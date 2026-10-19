import json
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from app.bootstrap import create_app
from app.contracts import IntentDecision
from app.data_access.public import QueryResult
from app.settings import Settings

TOKEN = 'personnel-test-token-0001'


class WrongModel:
    async def interpret(self, message, context=None):
        return IntentDecision(operation='outside')


class Reader:
    def __init__(self, empty=False, limited=False):
        self.queries = []
        self.empty, self.limited = empty, limited

    async def run_read(self, query, context):
        self.queries.append(query)
        assert query.template == 'offices_details'
        department = query.parameters['department']
        users = [] if self.empty else [{'tabla':'users','campos':{'id':43,'sucursal_id':2,'name':'Persona de prueba','email':'persona@example.test','ci':'123456','ciudad':'Trinidad'}}]
        return QueryResult([{'office_id':2,'department':department,'details':{'tabla':'sucursales','campos':{'municipio':'TRINIDAD','departamento':department},'relaciones':{'usuarios':{'registros':users,'truncado':self.limited,'limite':50}}}}], 'Respaldo de prueba', datetime.now(timezone.utc))


def client(reader, permissions=None):
    settings = Settings(identities_json=json.dumps({TOKEN:{'user_id':'personnel-test','permissions':permissions if permissions is not None else ['internal_data','offices','personal_data'],'scope':['global_internal']}}))
    return TestClient(create_app(settings, reader=reader, model=WrongModel()))


@pytest.mark.parametrize('message,department', [
    ('dame que personal hay en la sucursal de beni en tablas','Beni'),
    ('¿Qué empleados hay en la oficina de La Paz?','La Paz'),
    ('Lista los funcionarios de la sucursal de Pando','Pando'),
    ('personal de la oficina de potosi en tabla','Potosí'),
])
def test_personnel_is_in_scope_and_returns_a_readable_table(message, department):
    reader = Reader()
    with client(reader) as api:
        response = api.post('/api/chat', headers={'Authorization':'Bearer '+TOKEN},json={'message':message})
        assert response.status_code == 200
        body = response.json()
        assert body['status'] == 'answer'
        assert reader.queries[-1].parameters['department'] == department
        assert body['rows'][0]['nombre'] == 'Persona de prueba'
        assert body['rows'][0]['sucursal'] == 'TRINIDAD'
        assert 'details' not in body['columns'] and 'id' not in body['columns']
        assert 'personal' in body['answer'].lower()
        history = api.get('/api/sessions/'+body['session_id'],headers={'Authorization':'Bearer '+TOKEN}).json()
        assert history['messages'][-1]['rows'] == body['rows']
        followup=api.post('/api/chat',headers={'Authorization':'Bearer '+TOKEN},json={'message':'y el personal en tablas','session_id':body['session_id']}).json()
        assert followup['status']=='answer'
        assert reader.queries[-1].parameters['department']==department
        new=api.post('/api/chat',headers={'Authorization':'Bearer '+TOKEN},json={'message':'personal de la sucursal de Tarija','session_id':body['session_id']}).json()
        assert new['status']=='answer'
        assert reader.queries[-1].parameters['department']=='Tarija'


def test_personnel_keeps_permission_checks_and_asks_for_missing_department():
    reader = Reader()
    with client(reader, ['internal_data','offices']) as api:
        headers={'Authorization':'Bearer '+TOKEN}
        denied=api.post('/api/chat',headers=headers,json={'message':'personal de la sucursal de Beni en tablas'})
        assert denied.status_code == 403
        assert not reader.queries
    with client(reader) as api:
        missing=api.post('/api/chat',headers=headers,json={'message':'personal de la sucursal en tablas'})
        assert missing.json()['status'] == 'needs_clarification'
        assert not reader.queries


@pytest.mark.parametrize('empty,limited,status',[(True,False,'no_results'),(False,True,'answer'),(True,True,'needs_clarification')])
def test_empty_and_partial_personnel_are_not_reported_as_complete(empty,limited,status):
    with client(Reader(empty,limited)) as api:
        body=api.post('/api/chat',headers={'Authorization':'Bearer '+TOKEN},json={'message':'personal de la sucursal de Beni'}).json()
        assert body['status'] == status
        assert body['evidence'][0]['truncated'] is limited


def test_personnel_does_not_reuse_a_department_for_an_unknown_place_or_unrelated_topic():
    from app.conversation.public import Conversation
    previous=IntentDecision(operation='offices',department='La Paz',detail=True,office_personnel=True)
    intent=Conversation.office_personnel_intent('personal de la sucursal de Cobija',previous)
    assert intent.department is None
    assert Conversation.office_personnel_intent('ayuda con mi vida personal',previous) is None


@pytest.mark.parametrize('followup', ['ahorta las de santa cruz','ahorita las de Santa Cruz','ahora los de Santa Cruz','y de Santa Cruz','Santa Cruz','las de Santa Cruz en tablas'])
def test_department_followup_keeps_personnel_after_context_cache_is_cleared(followup):
    reader=Reader()
    with client(reader) as api:
        headers={'Authorization':'Bearer '+TOKEN}
        first=api.post('/api/chat',headers=headers,json={'message':'personal de la sucursal de Beni en tablas'}).json()
        session_id=first['session_id']
        api.app.state.conversation.sessions.clear()
        response=api.post('/api/chat',headers=headers,json={'message':followup,'session_id':session_id})
        assert response.status_code==200
        body=response.json()
        assert body['status']=='answer'
        assert body['columns']==first['columns']
        assert reader.queries[-1].parameters['department']=='Santa Cruz'
        assert body['rows'][0]['departamento']=='Santa Cruz'
        again=api.post('/api/chat',headers=headers,json={'message':'y de Pando','session_id':session_id}).json()
        assert again['status']=='answer'
        assert again['columns']==first['columns']
        assert reader.queries[-1].parameters['department']=='Pando'


def test_department_followup_does_not_assume_personnel_without_that_topic():
    from app.conversation.public import Conversation
    previous=IntentDecision(operation='offices',department='Beni')
    intent=Conversation.office_department_followup('y de Santa Cruz',previous)
    assert intent.department=='Santa Cruz' and not intent.office_personnel and not intent.detail
    assert Conversation.office_department_followup('oficinas de Santa Cruz',previous) is None
    assert Conversation.office_department_followup('seguimiento CP123456789BO de Santa Cruz',previous) is None
    assert Conversation.office_department_followup('y de Santa Cruz',None) is None


def test_saved_chat_recovers_personnel_after_an_old_department_followup_lost_it():
    reader=Reader()
    with client(reader) as api:
        headers={'Authorization':'Bearer '+TOKEN}
        first=api.post('/api/chat',headers=headers,json={'message':'personal de la sucursal de Beni en tablas'}).json()
        conversation=api.app.state.conversation
        session=conversation.sessions[first['session_id']]
        # Reproduce the persisted state created by the old classifier.
        session.messages.append({'role':'user','content':'ahorta las de santa cruz'})
        session.last_intent=IntentDecision(operation='offices',department='Santa Cruz')
        conversation.store.save(first['session_id'],session)
        conversation.sessions.clear()
        body=api.post('/api/chat',headers=headers,json={'message':'y de Pando','session_id':first['session_id']}).json()
        assert body['status']=='answer'
        assert body['columns']==first['columns']
        assert reader.queries[-1].parameters['department']=='Pando'


def test_no_results_does_not_clear_the_personnel_topic():
    reader=Reader(empty=True)
    with client(reader) as api:
        headers={'Authorization':'Bearer '+TOKEN}
        first=api.post('/api/chat',headers=headers,json={'message':'personal de la sucursal de Beni'}).json()
        assert first['status']=='no_results'
        reader.empty=False
        body=api.post('/api/chat',headers=headers,json={'message':'y de Santa Cruz','session_id':first['session_id']}).json()
        assert body['status']=='answer' and body['rows'][0]['nombre']=='Persona de prueba'
        assert reader.queries[-1].parameters['department']=='Santa Cruz'


def test_explicit_office_topic_is_preserved_instead_of_recovering_an_older_personnel_topic():
    class OfficeReader(Reader):
        async def run_read(self,query,context):
            if query.template=='offices':
                return QueryResult([{'office_id':2,'department':query.parameters['department'],'municipality':'Ciudad de prueba'}],'Prueba',datetime.now(timezone.utc))
            return await super().run_read(query,context)
    with client(OfficeReader()) as api:
        headers={'Authorization':'Bearer '+TOKEN}
        first=api.post('/api/chat',headers=headers,json={'message':'personal de la sucursal de Beni'}).json()
        conversation=api.app.state.conversation
        session=conversation.sessions[first['session_id']]
        session.messages.append({'role':'user','content':'muestra las oficinas de La Paz'})
        session.last_intent=IntentDecision(operation='offices',department='La Paz')
        body=api.post('/api/chat',headers=headers,json={'message':'y de Santa Cruz','session_id':first['session_id']}).json()
        assert body['status']=='answer'
        assert 'municipality' in body['columns'] and 'nombre' not in body['columns']


class DatedReader(Reader):
    def __init__(self,dates,limited=False):
        super().__init__(limited=limited)
        self.dates=dates

    async def run_read(self,query,context):
        result=await super().run_read(query,context)
        users=result.rows[0]['details']['relaciones']['usuarios']
        users['registros']=[{'campos':{'id':100-index,'name':f'Persona {index+1}','created_at':date}} for index,date in enumerate(self.dates)]
        return result


def test_latest_personnel_uses_registration_date_and_keeps_department_context():
    reader=DatedReader(['2026-06-25T15:00:00','2026-08-01T12:00:00','2026-07-31T23:00:00'])
    with client(reader) as api:
        headers={'Authorization':'Bearer '+TOKEN}
        first=api.post('/api/chat',headers=headers,json={'message':'el personal de oruro'}).json()
        body=api.post('/api/chat',headers=headers,json={'message':'ame los datos del ultimo personal registrao de la paz','session_id':first['session_id']}).json()
        assert body['status']=='answer'
        assert len(body['rows'])==1 and body['rows'][0]['nombre']=='Persona 2'
        assert body['rows'][0]['fecha_registro']=='2026-08-01T12:00:00'
        assert reader.queries[-1].parameters['department']=='La Paz'
        assert 'registro' in body['answer'].lower() and 'última' in body['answer'].lower()
        again=api.post('/api/chat',headers=headers,json={'message':'y de Santa Cruz','session_id':first['session_id']}).json()
        assert len(again['rows'])==1 and reader.queries[-1].parameters['department']=='Santa Cruz'


def test_latest_personnel_followup_does_not_require_repeating_the_department():
    with client(DatedReader(['2026-01-01T12:00:00','2026-08-01T12:00:00'])) as api:
        headers={'Authorization':'Bearer '+TOKEN}
        first=api.post('/api/chat',headers=headers,json={'message':'personal de la sucursal de La Paz'}).json()
        body=api.post('/api/chat',headers=headers,json={'message':'y el último registrado','session_id':first['session_id']}).json()
        assert body['status']=='answer' and len(body['rows'])==1
        assert body['rows'][0]['nombre']=='Persona 2'


@pytest.mark.parametrize('dates,limited', [([None,'2026-08-01T12:00:00'],False),(['fecha inválida'],False),(['2026-08-01T12:00:00'],True)])
def test_latest_personnel_does_not_guess_from_missing_dates_or_a_partial_list(dates,limited):
    with client(DatedReader(dates,limited)) as api:
        body=api.post('/api/chat',headers={'Authorization':'Bearer '+TOKEN},json={'message':'último personal registrado de La Paz'}).json()
        assert body['status']=='needs_clarification'
        assert not body.get('rows')


def test_latest_personnel_keeps_all_people_tied_on_the_latest_date():
    with client(DatedReader(['2026-01-01T12:00:00','2026-08-01T12:00:00','2026-08-01T12:00:00'])) as api:
        body=api.post('/api/chat',headers={'Authorization':'Bearer '+TOKEN},json={'message':'último personal registrado de La Paz'}).json()
        assert body['status']=='answer' and len(body['rows'])==2
        assert {row['nombre'] for row in body['rows']}=={'Persona 2','Persona 3'}
        assert 'misma' in body['answer'].lower()
