import json
from dataclasses import replace
from datetime import datetime, timezone

from fastapi.testclient import TestClient

from app.bootstrap import create_app
from app.contracts import IntentDecision
from app.contracts import AccessContext, ServiceError
from app.data_access.public import QueryResult
from app.settings import Settings
import pytest
from app.conversation.public import Conversation
from types import SimpleNamespace
from app.analytics.public import describe_period


@pytest.mark.parametrize('message,dimension', [
    ('¿Puedes desglosarlo por cada departamento?', 'department'),
    ('muéstrame la cantidad en cada oficina', 'office'),
    ('y eso separado por sucursal', 'office'),
    ('quiero el mismo resumen distribuido entre todas las sucursales', 'office'),
    ('cuánto corresponde a cada departamento', 'department'),
    ('ahora agrúpalo por destino', 'destination'),
    ('dame el detalle de carga para cada departamento', 'department'),
    ('me lo puedes mostrar agrupado por oficinas', 'office'),
    ('por tipo de envío', 'source'),
    ('separalo segun los estados', 'status'),
    ('distribución por sucursles', 'office'),
])
def test_similar_breakdown_requests(message, dimension):
    assert Conversation.summary_dimension_followup(message) == dimension


@pytest.mark.parametrize('message', [
    'teléfono de todas las oficinas', 'personal por departamentos',
    'por oficinas solo entregados', 'por departamentos en julio',
    'por oficinas de La Paz', 'por departamentos y oficinas',
])
def test_breakdown_does_not_swallow_new_topics_or_filters(message):
    assert Conversation.summary_dimension_followup(message) is None


def setup():
    class Model:
        async def interpret(self, message, context=None):
            return IntentDecision(operation='summary')

    class Reader:
        def __init__(self): self.queries = []
        async def run_read(self, query, context):
            self.queries.append(query)
            rows = ([{'office_id': 1, 'municipality': 'LA PAZ', 'department': 'LA PAZ'}]
                    if query.template == 'offices' else
                    [{'destination': 'La Paz', 'total': 7}, {'destination': 'Desconocido', 'total': 2}]
                    if query.template == 'summary_destination' else [{'status': 'ENTREGADO', 'total': 9}])
            return QueryResult(rows, 'Datos sintéticos', datetime.now(timezone.utc))

    token = 'context-edit-test-token-00001'
    settings = Settings(demo_mode=True, identities_json=json.dumps({token: {
        'user_id': 'editor', 'permissions': ['internal_data', 'summary', 'offices'], 'scope': ['global_internal']}}))
    reader = Reader()
    return create_app(settings, reader=reader, model=Model()), reader, {'Authorization': 'Bearer '+token}


def test_geographic_followups_keep_period_after_reload():
    app, reader, headers = setup()
    with TestClient(app) as client:
        first = client.post('/api/chat', headers=headers, json={'message': 'volumen de carga nacional en agosto de 2026'}).json()
        for text, column in [('dame por departamentos', 'department'), ('dame por oficinas', 'office'), ('todas las sucursale', 'office')]:
            app.state.conversation.sessions.clear()
            result = client.post('/api/chat', headers=headers, json={'message': text, 'session_id': first['session_id']}).json()
            assert result['status'] == 'answer'
            assert column in result['columns']
            assert sum(row['total'] for row in result['rows']) == 9
            assert 'agosto de 2026' in result['answer']
            assert 'destino' in result['answer']
            assert str(next(q for q in reversed(reader.queries) if q.template.startswith('summary')).parameters['start_date']) == '2026-08-01'


def test_edit_replaces_tail_and_restores_context_after_reload():
    app, reader, headers = setup()
    with TestClient(app) as client:
        first = client.post('/api/chat', headers=headers, json={'message': 'carga de agosto de 2026'}).json()
        sid = first['session_id']
        client.post('/api/chat', headers=headers, json={'message': 'septiembre de 2026', 'session_id': sid})
        app.state.conversation.sessions.clear()
        result = client.post('/api/chat', headers=headers, json={'message': 'por departamentos', 'session_id': sid, 'edit_message_index': 2})
        assert result.status_code == 200
        assert 'agosto de 2026' in result.json()['answer']
        history = client.get(f'/api/sessions/{sid}', headers=headers).json()['messages']
        assert len(history) == 4
        assert history[2]['content'] == 'por departamentos'
        invalid = client.post('/api/chat', headers=headers, json={'message': 'julio', 'session_id': sid, 'edit_message_index': 1})
        assert invalid.status_code == 422
        assert client.get(f'/api/sessions/{sid}', headers=headers).json()['messages'] == history


def test_edit_first_query_clears_future_period():
    app, reader, headers = setup()
    with TestClient(app) as client:
        sid = client.post('/api/chat', headers=headers, json={'message': 'carga de agosto de 2026'}).json()['session_id']
        result = client.post('/api/chat', headers=headers, json={'message': 'carga de julio de 2026', 'session_id': sid, 'edit_message_index': 0}).json()
        assert 'julio de 2026' in result['answer']
        assert len(client.get(f'/api/sessions/{sid}', headers=headers).json()['messages']) == 2


@pytest.mark.parametrize('stream', [False, True])
def test_legacy_edit_recovers_only_context_before_edited_query(stream):
    app, reader, headers = setup()
    with TestClient(app) as client:
        sid = client.post('/api/chat', headers=headers, json={'message': 'carga EMS de agosto de 2026'}).json()['session_id']
        client.post('/api/chat', headers=headers, json={'message': 'septiembre de 2026', 'session_id': sid})
        conversation = app.state.conversation
        session = conversation.sessions[sid]
        session.contexts.clear()
        conversation.store.save(sid, session)
        conversation.sessions.clear()
        result = client.post('/api/chat/stream' if stream else '/api/chat', headers=headers,
                             json={'message': 'por departamentos', 'session_id': sid, 'edit_message_index': 2})
        assert result.status_code == 200
        if stream:
            assert 'event: completed' in result.text and 'event: error' not in result.text
        else:
            assert result.json()['status'] == 'answer'
        history = client.get('/api/sessions/'+sid, headers=headers).json()['messages']
        assert len(history) == 4
        assert 'agosto de 2026' in history[-1]['content']
        assert 'EMS' in history[-1]['content']
        query = next(q for q in reversed(reader.queries) if q.template == 'summary_destination')
        assert query.parameters['family'] == 'ems'
        assert str(query.parameters['start_date']) == '2026-08-01'


def test_legacy_edit_can_replace_query_after_greetings():
    app, reader, headers = setup()
    with TestClient(app) as client:
        sid = client.post('/api/chat', headers=headers, json={'message': 'hola'}).json()['session_id']
        client.post('/api/chat', headers=headers, json={'message': 'buenas', 'session_id': sid})
        conversation = app.state.conversation
        conversation.sessions[sid].contexts.clear()
        conversation.store.save(sid, conversation.sessions[sid])
        conversation.sessions.clear()
        result = client.post('/api/chat', headers=headers, json={'message': 'carga de julio de 2026', 'session_id': sid, 'edit_message_index': 2})
        assert result.status_code == 200
        assert 'julio de 2026' in result.json()['answer']


@pytest.mark.parametrize('start,end', [
    ('2026-08-01', '2026-09-01'), ('2026-08-05', '2026-08-06'),
    ('2026-08-05', '2026-08-13'), ('2025-12-20', '2026-01-11'),
])
def test_legacy_recovery_uses_exact_saved_calendar_period(start, end):
    session = SimpleNamespace(contexts={}, messages=[
        {'role': 'user', 'content': 'el mes pasado'},
        {'role': 'assistant', 'status': 'answer', 'content': 'Periodo consultado: '+describe_period(start,end)+'. Resultado.',
         'columns': ['status', 'total'], 'rows': [{'status': 'ENTREGADO', 'total': 1}]},
        {'role': 'user', 'content': 'por oficinas'},
    ])
    context = Conversation.recover_edit_context(session, 2)
    assert context['filters'] == {'start_date': start, 'end_date': end}


def test_legacy_recovery_ignores_failed_turn_and_future_office_filter():
    session = SimpleNamespace(contexts={}, messages=[
        {'role': 'user', 'content': 'oficinas de La Paz'},
        {'role': 'assistant', 'status': 'answer', 'content': 'Oficinas', 'columns': ['office_id'], 'rows': [{'office_id': 1}]},
        {'role': 'user', 'content': 'oficinas de Beni'},
        {'role': 'assistant', 'status': 'error', 'content': 'Error'},
        {'role': 'user', 'content': 'oficinas de Pando'},
        {'role': 'assistant', 'status': 'answer', 'content': 'Oficinas', 'columns': ['office_id'], 'rows': [{'office_id': 2}]},
    ])
    context = Conversation.recover_edit_context(session, 4)
    assert context['filters']['department'].casefold() == 'la paz'


def test_geography_preserves_family_and_does_not_invent_period():
    app, reader, headers = setup()
    with TestClient(app) as client:
        missing = client.post('/api/chat', headers=headers, json={'message': 'por departamentos'}).json()
        assert missing['status'] == 'needs_clarification'
        assert not reader.queries
        first = client.post('/api/chat', headers=headers, json={'message': 'carga EMS en agosto de 2026'}).json()
        result = client.post('/api/chat', headers=headers, json={'message': 'por oficinas', 'session_id': first['session_id']}).json()
        assert result['status'] == 'answer'
        assert next(q for q in reversed(reader.queries) if q.template == 'summary_destination').parameters['family'] == 'ems'


@pytest.mark.parametrize('message,template', [
    ('puedes desglosarlo por cada departamento', 'summary_destination'),
    ('muestrame la cantidad en cada oficina', 'summary_destination'),
    ('dame el detalle de carga para cada departamento', 'summary_destination'),
    ('por tipo de envio', 'summary_source'),
    ('separalo segun los estados', 'summary_status'),
])
def test_natural_breakdown_keeps_confirmed_filters(message, template):
    app, reader, headers = setup()
    with TestClient(app) as client:
        sid = client.post('/api/chat', headers=headers, json={'message': 'carga EMS de agosto de 2026'}).json()['session_id']
        result = client.post('/api/chat', headers=headers, json={'message': message, 'session_id': sid}).json()
        assert result['status'] == 'answer'
        assert result['record_browser'] is None
        query = next(q for q in reversed(reader.queries) if q.template.startswith('summary'))
        assert query.template == template
        assert query.parameters['family'] == 'ems'
        assert str(query.parameters['start_date']) == '2026-08-01'


def test_ambiguous_municipality_does_not_duplicate_counts():
    app, reader, headers = setup()
    original = reader.run_read
    async def duplicate(query, context):
        result = await original(query, context)
        return replace(result, rows=result.rows * 2) if query.template == 'offices' else result
    reader.run_read = duplicate
    with TestClient(app) as client:
        sid = client.post('/api/chat', headers=headers, json={'message': 'carga de agosto de 2026'}).json()['session_id']
        result = client.post('/api/chat', headers=headers, json={'message': 'por oficinas', 'session_id': sid}).json()
        assert result['rows'] == [{'office': 'Sin correspondencia', 'total': 9}]


def test_geography_rejects_incomplete_source():
    app, reader, headers = setup()
    original = reader.run_read
    async def truncated(query, context):
        result = await original(query, context)
        return replace(result, truncated=True) if query.template == 'summary_destination' else result
    reader.run_read = truncated
    with TestClient(app) as client:
        sid = client.post('/api/chat', headers=headers, json={'message': 'carga de agosto de 2026'}).json()['session_id']
        result = client.post('/api/chat', headers=headers, json={'message': 'por departamentos', 'session_id': sid})
        assert result.status_code == 422
        assert 'limitado' in result.json()['error']['message']


def test_edit_stream_updates_durable_history():
    app, reader, headers = setup()
    with TestClient(app) as client:
        sid = client.post('/api/chat', headers=headers, json={'message': 'carga de agosto de 2026'}).json()['session_id']
        result = client.post('/api/chat/stream', headers=headers, json={'message': 'carga de julio de 2026', 'session_id': sid, 'edit_message_index': 0})
        assert 'event: completed' in result.text
        app.state.conversation.sessions.clear()
        history = client.get(f'/api/sessions/{sid}', headers=headers).json()['messages']
        assert len(history) == 2
        assert history[0]['content'] == 'carga de julio de 2026'
        assert 'julio de 2026' in history[1]['content']


@pytest.mark.asyncio
async def test_geography_requires_directory_permission_before_reading():
    app, reader, _ = setup()
    with pytest.raises(ServiceError) as error:
        await app.state.conversation.tools.execute(
            IntentDecision(operation='summary', dimension='department', start_date='2026-08-01', end_date='2026-09-01'),
            AccessContext(user_id='restricted', permissions=frozenset({'summary', 'internal_data'}), scope=('global_internal',)))
    assert error.value.status_code == 403
    assert not reader.queries
