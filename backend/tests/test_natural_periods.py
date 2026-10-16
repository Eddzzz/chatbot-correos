import json
from datetime import date
import pytest
from fastapi.testclient import TestClient
from app.analytics.public import resolve_period
from app.bootstrap import create_app
from app.contracts import IntentDecision, ServiceError
from app.contracts import AccessContext
from app.conversation.public import Conversation
from app.settings import Settings


@pytest.mark.parametrize('message,start,end', [
    ('de todo el mes de octubre','2026-10-01','2026-11-01'),
    ('octubre de 2025','2025-10-01','2025-11-01'),
    ('resumen de diciembre 2026','2026-12-01','2027-01-01'),
    ('febrero de 2024','2024-02-01','2024-03-01'),
    ('octubre del año pasado','2025-10-01','2025-11-01'),
    ('este mes','2026-10-01','2026-11-01'),
    ('el mes pasado','2026-09-01','2026-10-01'),
    ('hoy','2026-10-16','2026-10-17'),
    ('ayer','2026-10-15','2026-10-16'),
    ('del 1 al 31 de octubre de 2026','2026-10-01','2026-11-01'),
])
def test_periods_are_resolved_without_model_dates(message,start,end):
    assert resolve_period(message,today=date(2026,10,16)) == (start,end)


def test_month_followup_preserves_confirmed_year_but_explicit_year_wins():
    assert resolve_period('de todo octubre', {'start_date':'2024-09-01'}, today=date(2026,10,16)) == ('2024-10-01','2024-11-01')
    assert resolve_period('octubre de 2025', {'start_date':'2024-09-01'}, today=date(2026,10,16)) == ('2025-10-01','2025-11-01')
    assert resolve_period('octubre de este año', {'start_date':'2024-09-01'}, today=date(2026,10,16)) == ('2026-10-01','2026-11-01')
    with pytest.raises(ServiceError):
        resolve_period('del 31 al 1 de octubre de 2026',today=date(2026,10,16))
    with pytest.raises(ServiceError):
        resolve_period('octubre y noviembre de 2026',today=date(2026,10,16))
    # Model dates without evidence are still refused.
    with pytest.raises(ServiceError):
        Conversation.validate_filters(IntentDecision(operation='summary',start_date='2026-10-01',end_date='2026-11-01'),'resumen urgente',{})


def test_accounting_and_date_followup_never_become_shipment_counts(tmp_path):
    token='natural-period-token-001'
    identity={'user_id':'period-user','permissions':['internal_data','summary','offices','personal_data'],'scope':['global_internal']}
    settings=Settings(demo_mode=True,history_path=str(tmp_path/'chats.sqlite3'),identities_json=json.dumps({token:identity}))
    headers={'Authorization':'Bearer '+token}
    with TestClient(create_app(settings)) as client:
        first=client.post('/api/chat',headers=headers,json={'message':'dame el registro contable del mes de octubre'}).json()
        assert first['status']=='answer'
        assert 'octubre' in first['answer'] and 'facturación' in first['answer']
        assert {row['category'] for row in first['rows']}=={'movimientos','cobros','facturacion'}
    with TestClient(create_app(settings)) as client:
        second=client.post('/api/chat',headers=headers,json={'message':'de todo el mes de octubre','session_id':first['session_id']}).json()
        assert second['status']=='answer'
        assert 'facturación' in second['answer'] and 'AAAA-MM-DD' not in second['answer']
        only=client.post('/api/chat',headers=headers,json={'message':'solo cobros','session_id':first['session_id']}).json()
        assert only['status']=='answer' and {row['category'] for row in only['rows']}=={'cobros'}
        assert 'octubre' in only['answer']


def test_accounting_needs_personal_access_and_missing_period_is_a_question():
    token='period-access-token-001'
    settings=Settings(demo_mode=True,identities_json=json.dumps({token:{'user_id':'period-access-user','permissions':['internal_data','summary'],'scope':['global_internal']}}))
    with TestClient(create_app(settings)) as client:
        headers={'Authorization':'Bearer '+token}
        question=client.post('/api/chat',headers=headers,json={'message':'dame los cobros'}).json()
        assert question['status']=='needs_clarification'
        denied=client.post('/api/chat',headers=headers,json={'message':'todo octubre','session_id':question['session_id']})
        assert denied.status_code==403


def test_date_followup_recovers_accounting_topic_from_previously_failed_chat():
    token='period-legacy-token-001'
    principal=AccessContext(user_id='legacy-period-user',permissions=frozenset({'internal_data','summary','personal_data'}),scope=('global_internal',))
    settings=Settings(demo_mode=True,identities_json=json.dumps({token:principal.model_dump(mode='json')}))
    app=create_app(settings)
    chat_id,session=app.state.conversation.session(None,principal)
    session.messages=[{'role':'user','content':'dame el registro contable del mes de octubre'},{'role':'assistant','content':'No se pudo completar la consulta.','status':'error'}]
    with TestClient(app) as client:
        response=client.post('/api/chat',headers={'Authorization':'Bearer '+token},json={'message':'de todo el mes de octubre','session_id':chat_id}).json()
        assert response['status']=='answer'
        assert {row['category'] for row in response['rows']}=={'movimientos','cobros','facturacion'}


def test_monthly_counts_show_period_and_backup_cutoff():
    token='natural-period-token-002'
    settings=Settings(demo_mode=True,identities_json=json.dumps({token:{'user_id':'monthly-user','permissions':['internal_data','summary'],'scope':['global_internal']}}),data_snapshot='2026-10-08 14:59:32')
    with TestClient(create_app(settings)) as client:
        body=client.post('/api/chat',headers={'Authorization':'Bearer '+token},json={'message':'Cuenta registros por estado en octubre de 2026'}).json()
        assert body['status']=='answer'
        assert 'octubre de 2026' in body['answer'] and '2026-10-08' in body['answer']
