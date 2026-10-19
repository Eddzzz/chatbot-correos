import json
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from app.bootstrap import create_app
from app.contracts import AccessContext, IntentDecision, ServiceError
from app.conversation.public import Conversation
from app.data_access.public import QueryResult
from app.settings import Settings
import pytest


class PostalReader:
    def __init__(self): self.queries=[]
    async def run_read(self,query,context):
        self.queries.append(query)
        family=query.parameters.get('family')
        if query.template=='summary_records':
            offset=query.parameters['offset']
            rows=[{'source':family or 'ems','tracking_code':f'SYNTH-{i}','status':'En tránsito','registered_at':'2026-06-15'} for i in range(offset,min(13,offset+query.parameters['page_limit']))]
        else:
            rows=[{'source':family or 'ems','total':13}]
        return QueryResult(rows,'Datos sintéticos',datetime.now(timezone.utc))


def setup():
    token='family-followup-token-00001'
    identity={'user_id':'family-user','permissions':['internal_data','summary'],'scope':['global_internal']}
    reader=PostalReader()
    settings=Settings(demo_mode=True,identities_json=json.dumps({token:identity,'no-summary-token-00001':{**identity,'permissions':['internal_data','tracking']}}))
    class SummaryModel:
        async def interpret(self,message,context=None):
            assert 'registros' in message
            return IntentDecision(operation='summary',dimension='source')
    return create_app(settings,reader=reader,model=SummaryModel()),reader,{'Authorization':'Bearer '+token}


def test_followup_retains_june_and_selects_ems_after_restart():
    app,reader,headers=setup()
    with TestClient(app) as client:
        first=client.post('/api/chat',headers=headers,json={'message':'dame todos los registros de cartes del mes e junio'}).json()
        chat_id=first['session_id']
        # Cache eviction exercises the saved intent, not frontend-only context.
        app.state.conversation.sessions.clear()
        for text,family in [('de ems','ems'),('y de certificados','certi'),('solo contratos','contrato')]:
            response=client.post('/api/chat',headers=headers,json={'message':text,'session_id':chat_id}).json()
            assert response['status']=='answer'
            assert reader.queries[-1].parameters['family']==family
            assert str(reader.queries[-1].parameters['start_date'])=='2026-06-01'
            assert str(reader.queries[-1].parameters['end_date'])=='2026-07-01'
            assert response['record_browser']['family']==family
            assert 'junio' in response['answer']


def test_family_without_period_asks_for_month_and_pages_are_bounded_and_authorized():
    app,reader,headers=setup()
    with TestClient(app) as client:
        missing=client.post('/api/chat',headers=headers,json={'message':'de EMS'}).json()
        assert missing['status']=='needs_clarification'
        path='/api/postal-records?start_date=2026-06-01&end_date=2026-07-01&family=ems&limit=10'
        assert client.get(path).status_code==401
        assert client.get(path,headers={'Authorization':'Bearer no-summary-token-00001'}).status_code==403
        first=client.get(path,headers=headers).json()
        second=client.get(path+'&offset=10',headers=headers).json()
        assert len(first['rows'])==10 and first['next_offset']==10
        assert len(second['rows'])==3 and second['next_offset'] is None
        assert {row['tracking_code'] for row in first['rows']}.isdisjoint(row['tracking_code'] for row in second['rows'])
        assert client.get(path.replace('family=ems','family=unknown'),headers=headers).status_code==422
        assert client.get(path.replace('limit=10','limit=1000'),headers=headers).status_code==422
        assert client.get(path.replace('2026-06-01','2026-02-30'),headers=headers).status_code==422
        ambiguous=client.post('/api/chat',headers=headers,json={'message':'EMS y certificados'}).json()
        assert ambiguous['status']=='needs_clarification'


def test_new_summary_clears_previous_family_and_rejects_model_invented_family():
    previous={'start_date':'2026-06-01','end_date':'2026-07-01','family':'ems'}
    new=Conversation.validate_filters(IntentDecision(operation='summary',family='ems'),'Cuenta registros de julio de 2026',previous)
    assert new.family is None
    with pytest.raises(ServiceError):
        Conversation.validate_filters(IntentDecision(operation='summary',family='contrato'),'de EMS',previous)
