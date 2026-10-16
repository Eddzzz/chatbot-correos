import json
import pytest

from fastapi.testclient import TestClient

from app.bootstrap import create_app
from app.contracts import AccessContext, IntentDecision, ServiceError
from app.settings import Settings
from app.conversation.public import Conversation


TOKEN = 'details-test-token-0001'


def test_complete_followup_keeps_the_previously_confirmed_office_and_uses_detail_tool():
    class Model:
        async def interpret(self, message, context=None):
            return IntentDecision(operation='offices', department='La Paz') if 'sucursal' in message else IntentDecision(operation='outside')

    class Reader:
        async def run_read(self, query, context):
            from app.data_access.public import QueryResult
            from datetime import datetime, timezone
            assert query.parameters['department'] == 'La Paz'
            rows = [{'office_id': 1, 'department': 'LA PAZ', 'details': {'puntoVenta': 7, 'usuarios_asignados': [{'name': 'Persona ficticia'}]}}] if query.template == 'offices_details' else [{'office_id': 1, 'department': 'LA PAZ'}]
            return QueryResult(rows, 'Datos ficticios', datetime.now(timezone.utc))

    principal = AccessContext(user_id='operator', permissions=frozenset({'internal_data', 'offices', 'personal_data'}), scope=('global_internal',))
    settings = Settings(identities_json=json.dumps({TOKEN: principal.model_dump(mode='json')}))
    with TestClient(create_app(settings, reader=Reader(), model=Model())) as client:
        headers = {'Authorization': 'Bearer ' + TOKEN}
        first = client.post('/api/chat', headers=headers, json={'message': 'dame los datos e la sucursal e la paz'}).json()
        followup = client.post('/api/chat', headers=headers, json={'message': 'dame compelto lo datos completos', 'session_id': first['session_id']})
        assert followup.status_code == 200
        assert followup.json()['status'] == 'answer'
        assert followup.json()['rows'][0]['details']['puntoVenta'] == 7


def test_details_without_context_ask_which_resource_instead_of_outside():
    class Model:
        async def interpret(self, message, context=None):
            return IntentDecision(operation='outside')
    with TestClient(create_app(Settings(demo_mode=True, identities_json=json.dumps({TOKEN: {'user_id': 'operator'}})), model=Model())) as client:
        response = client.post('/api/chat', headers={'Authorization': 'Bearer ' + TOKEN}, json={'message': 'dame los datos completos'})
        assert response.json()['status'] == 'needs_clarification'


def test_detail_request_never_extends_to_a_new_named_resource():
    assert not Conversation.is_detail_followup('dame datos completos de la sucursal de Cochabamba')
    assert not Conversation.is_detail_followup('datos completos de usuarios y contraseñas')


def test_full_details_require_an_explicit_personal_permission():
    settings = Settings(demo_mode=True, identities_json=json.dumps({TOKEN: {'user_id': 'operator', 'permissions': ['internal_data', 'offices'], 'scope': ['global_internal']}}))
    with TestClient(create_app(settings)) as client:
        headers = {'Authorization': 'Bearer ' + TOKEN}
        first = client.post('/api/chat', headers=headers, json={'message': 'oficinas de La Paz'}).json()
        response = client.post('/api/chat', headers=headers, json={'message': 'datos completos', 'session_id': first['session_id']})
        assert response.status_code == 403
        assert response.json()['status'] == 'forbidden'


def test_last_data_without_a_table_asks_for_clarification():
    settings = Settings(demo_mode=True, identities_json=json.dumps({TOKEN: {'user_id': 'operator'}}))
    with TestClient(create_app(settings)) as client:
        response = client.post('/api/chat', headers={'Authorization': 'Bearer ' + TOKEN}, json={'message': 'dame el ultimo dato guardado'})
        assert response.json()['status'] == 'needs_clarification'


def test_full_detail_that_exceeds_the_limit_is_not_reported_as_no_results():
    from datetime import datetime, timezone
    from app.answers.public import compose_answer
    from app.data_access.public import QueryResult
    response = compose_answer('r', 's', QueryResult([], 'fixture', datetime.now(timezone.utc), True))
    assert response.status == 'needs_clarification'
    assert 'supera' in response.answer


async def test_data_access_also_denies_personal_details_before_opening_a_connection():
    from app.data_access.infrastructure import PostgresReader
    from app.data_access.public import QuerySpec
    reader = PostgresReader(Settings())
    principal = AccessContext(user_id='operator', permissions=frozenset({'internal_data', 'offices'}), scope=('global_internal',))
    with pytest.raises(ServiceError) as caught:
        await reader.run_read(QuerySpec(template='offices_details', parameters={'department': 'La Paz'}), principal)
    assert caught.value.status_code == 403
