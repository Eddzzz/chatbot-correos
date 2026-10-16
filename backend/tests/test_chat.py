import asyncio
import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from app.bootstrap import create_app
from app.contracts import AccessContext, IntentDecision, ServiceError
from app.data_access.infrastructure import PostgresReader
from app.data_access.public import QuerySpec, TEMPLATES, validate_query
from app.inference.public import LocalLanguageModel
from app.settings import Settings
from app.conversation.public import Conversation
from app.audit.public import AuditSink
from app.operations.public import ToolRegistry
from app.answers.public import compose_answer
from app.data_access.public import QueryResult
from datetime import datetime, timezone

TOKEN = 'test-token-000001'
PRINCIPAL = AccessContext(user_id='alice', permissions=frozenset({'internal_data', 'tracking', 'summary', 'offices'}), scope=('global_internal',))


def settings(**kwargs):
    return Settings(identities_json=json.dumps({TOKEN: PRINCIPAL.model_dump(mode='json')}), **kwargs)


def test_tracking_evidence_and_sse():
    with TestClient(create_app(settings(demo_mode=True))) as client:
        result = client.post('/api/chat', headers={'Authorization': 'Bearer ' + TOKEN}, json={'message': 'seguimiento DEMO123BO'}).json()
        assert 'ficticios' in result['answer']
        assert result['rows'][0]['tracking_code'] == 'DEMO123BO'
        assert result['evidence'][0]['row_count'] == 1
        history = client.get('/api/sessions/' + result['session_id'], headers={'Authorization': 'Bearer ' + TOKEN}).json()
        assert 'DEMO123BO' not in json.dumps(history)
        stream = client.post('/api/chat/stream', headers={'Authorization': 'Bearer ' + TOKEN}, json={'message': 'hola'}).text
        events = [json.loads(line[6:]) for line in stream.splitlines() if line.startswith('data: ')]
        assert len({event['request_id'] for event in events}) == 1
        assert 'event: request_started' in stream and 'event: completed' in stream


def test_permission_scope_and_dates():
    denied = AccessContext(user_id='alice', permissions=frozenset({'tracking'}), scope=('global_internal',))
    config = Settings(demo_mode=True, identities_json=json.dumps({TOKEN: denied.model_dump(mode='json')}))
    with TestClient(create_app(config)) as client:
        result = client.post('/api/chat', headers={'Authorization': 'Bearer ' + TOKEN}, json={'message': 'seguimiento DEMO123BO'})
        assert result.status_code == 403
    with TestClient(create_app(settings(demo_mode=True))) as client:
        result = client.post('/api/chat', headers={'Authorization': 'Bearer ' + TOKEN}, json={'message': 'resumen 2026-02-30 2026-03-02'})
        assert result.status_code == 422


def test_all_catalog_statements_parse_and_no_model_sql():
    for template, sql in TEMPLATES.items():
        validate_query(QuerySpec(template=template), sql)
        with pytest.raises(ValueError):
            validate_query(QuerySpec(template=template), sql + '; SELECT 1')


async def test_inference_queue_bound_and_cancellation():
    model = LocalLanguageModel(Settings(queue_size=0))
    await model.lock.acquire()
    model.pending = 1
    with pytest.raises(ServiceError) as error:
        await model.interpret('hola')
    assert error.value.code == 'queue_full'
    model.pending = 0
    task = asyncio.create_task(model.interpret('oficinas'))
    await asyncio.sleep(0)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert model.pending == 0
    model.lock.release()
    await model.close()


def test_hallucinated_filters_fail_and_followup_uses_confirmed_code():
    with pytest.raises(ServiceError):
        Conversation.validate_filters(IntentDecision(operation='summary', start_date='2026-03-01', end_date='2026-04-01'), 'Resumen de marzo', {})
    with pytest.raises(ServiceError):
        Conversation.validate_filters(IntentDecision(operation='tracking', tracking_code='DEMO123BO'), 'Consulta un envío', {})
    with pytest.raises(ServiceError):
        Conversation.validate_filters(IntentDecision(operation='offices'), 'Oficinas de Cochabamba', {})
    intent = Conversation.validate_filters(IntentDecision(operation='tracking'), '¿Y su estado?', {'tracking_code':'DEMO123BO'})
    assert intent.tracking_code == 'DEMO123BO'


def test_new_tracking_and_period_never_reuse_stale_filters():
    confirmed = {'tracking_code':'DEMO-CERTI-001'}
    for output in (None, 'DEMO-CERTI-001'):
        intent = IntentDecision(operation='tracking', tracking_code=output)
        if output:
            with pytest.raises(ServiceError):
                Conversation.validate_filters(intent, 'Consulta seguimiento DEMO-NUEVO-002', confirmed)
        else:
            assert Conversation.validate_filters(intent, 'Consulta seguimiento DEMO-NUEVO-002', confirmed).tracking_code is None
    assert Conversation.validate_filters(IntentDecision(operation='tracking'), 'Consulta otro envío', confirmed).tracking_code is None
    with pytest.raises(ServiceError):
        Conversation.validate_filters(IntentDecision(operation='tracking', tracking_code='DEMO-CERTI-001'), 'Consulta otro envío', confirmed)
    period = {'start_date':'2026-01-01','end_date':'2026-02-01'}
    with pytest.raises(ServiceError):
        Conversation.validate_filters(IntentDecision(operation='summary', **period), 'Resumen de marzo', period)
    intent = Conversation.validate_filters(IntentDecision(operation='summary'), 'Cuenta por destino en ese periodo', period)
    assert intent.start_date == period['start_date'] and intent.end_date == period['end_date']
    intent = Conversation.validate_filters(IntentDecision(operation='summary'), 'Resumen de marzo', period)
    assert intent.start_date is None and intent.end_date is None


def test_audit_metadata_has_no_message_or_results(caplog):
    import logging
    with caplog.at_level(logging.INFO, logger='chatbot.audit'):
        AuditSink().record('request-1', 'answer', 12, user_id='operator1', operation='tracking', model_version='sha256:verified')
    record = json.loads(caplog.records[-1].message)
    assert record == {'event':'chat_completed','request_id':'request-1','user_id':'operator1','operation':'tracking','model_version':'sha256:verified','outcome':'answer','duration_ms':12}


def test_truncated_analytics_never_invents_grand_total():
    result = QueryResult([{'status':'A','total':3},{'status':'B','total':2}], 'fixture', datetime.now(timezone.utc), True)
    answer = compose_answer('r', 's', result)
    assert 'parcial' in answer.answer and 'no representan el total completo' in answer.answer
    assert answer.evidence[0].truncated
    assert '5' not in answer.answer


async def test_cancel_propagates_to_active_reader_and_owner_only():
    started, cancelled = asyncio.Event(), asyncio.Event()
    class FakeModel:
        async def interpret(self, message, context=None):
            return IntentDecision(operation='tracking', tracking_code='DEMO123BO')
    class SlowReader:
        async def run_read(self, query, context):
            started.set()
            try:
                await asyncio.Future()
            finally:
                cancelled.set()
    service = Conversation(Settings(), FakeModel(), ToolRegistry(SlowReader()), AuditSink())
    session_id, _ = service.session(None, PRINCIPAL)
    from app.contracts import ChatRequest
    task = asyncio.create_task(service.handle(ChatRequest(message='DEMO123BO'), PRINCIPAL, 'request-123', session_id))
    await started.wait()
    with pytest.raises(ServiceError):
        service.cancel('request-123', AccessContext(user_id='mallory'))
    service.cancel('request-123', PRINCIPAL)
    with pytest.raises(asyncio.CancelledError):
        await task
    assert cancelled.is_set() and not service.running


@pytest.mark.skipif(not Path('../.runtime/fixture-dsn.txt').exists(), reason='Requiere PostgreSQL fixture local aislado')
async def test_postgres_restricted_role_real_execution():
    reader = PostgresReader(Settings(database_url=Path('../.runtime/fixture-dsn.txt').read_text().strip()))
    await reader.open()
    try:
        result = await reader.run_read(QuerySpec(template='offices', parameters={'department': None}), PRINCIPAL)
        assert result.rows and set(result.rows[0]) == {'office_id', 'codigo_sucursal', 'municipality', 'department', 'phone'}
        result = await reader.run_read(QuerySpec(template='summary_status', parameters={'start_date': '2020-01-01', 'end_date': '2030-01-01'}), PRINCIPAL)
        assert sum(row['total'] for row in result.rows) == 5
    finally:
        await reader.close()


@pytest.mark.skipif(not Path('../.runtime/initdb-password').exists() or not Path('../.runtime/fixture-dsn.txt').exists(), reason='Requiere fixture aislado local con administrador de prueba')
async def test_real_postgres_cancellation_releases_pool():
    import psycopg
    from psycopg.conninfo import make_conninfo
    # Fixed fixture-only destination; never use application/production DATABASE_URL.
    admin = await psycopg.AsyncConnection.connect(host='127.0.0.1', port=55432, dbname='correos_sandbox_fixture', user='fixture_admin', password=Path('../.runtime/initdb-password').read_text().strip(), autocommit=True)
    dsn = make_conninfo(Path('../.runtime/fixture-dsn.txt').read_text().strip(), application_name='chatbot-cancel-proof')
    reader = PostgresReader(Settings(database_url=dsn, statement_timeout_ms=10000))
    await reader.open()
    task = None
    try:
        await admin.execute('BEGIN')
        await admin.execute('LOCK TABLE public.sucursales IN ACCESS EXCLUSIVE MODE')
        task = asyncio.create_task(reader.run_read(QuerySpec(template='offices', parameters={'department':None}), PRINCIPAL))
        blocked = False
        for _ in range(100):
            await admin.execute('SELECT pg_stat_clear_snapshot()')
            state = await (await admin.execute("SELECT EXISTS (SELECT 1 FROM pg_stat_activity WHERE application_name='chatbot-cancel-proof' AND wait_event_type='Lock')")).fetchone()
            if state[0]:
                blocked = True
                break
            await asyncio.sleep(0.02)
        assert blocked, 'La consulta real debe estar esperando el bloqueo del fixture antes de cancelar.'
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await asyncio.wait_for(task, timeout=5)
        await admin.execute('ROLLBACK')
        result = await reader.run_read(QuerySpec(template='offices', parameters={'department':None}), PRINCIPAL)
        assert result.rows, 'Pool reutilizable después de cancelar PostgreSQL.'
    finally:
        if task and not task.done():
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)
        await admin.execute('ROLLBACK')
        await admin.close()
        await reader.close()
