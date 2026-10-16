import json
from fastapi.testclient import TestClient
from app.bootstrap import create_app
from app.settings import Settings

TOKEN = 'saved-chat-token-00001'
OTHER = 'other-chat-token-00001'


def config(path, permissions=None):
    identity = {'user_id': 'saved-alice', 'permissions': permissions if permissions is not None else ['internal_data', 'tracking', 'offices', 'summary', 'personal_data'], 'scope': ['global_internal']}
    return Settings(demo_mode=True, history_path=str(path), identities_json=json.dumps({TOKEN: identity, OTHER: {**identity, 'user_id': 'saved-bob'}}))


def test_history_survives_restart_and_keeps_full_results_and_context(tmp_path):
    settings = config(tmp_path / 'chats.sqlite3')
    headers = {'Authorization': 'Bearer ' + TOKEN}
    with TestClient(create_app(settings)) as client:
        answer = client.post('/api/chat', headers=headers, json={'message': 'seguimiento DEMO123BO'}).json()
        chat_id = answer['session_id']
    with TestClient(create_app(settings)) as client:
        sessions = client.get('/api/sessions', headers=headers).json()['sessions']
        assert sessions[0]['session_id'] == chat_id
        assert sessions[0]['title'] == 'seguimiento DEMO123BO'
        response = client.get('/api/sessions/' + chat_id, headers=headers)
        assert response.headers['cache-control'] == 'no-store'
        history = response.json()['messages']
        assert history[0]['content'] == 'seguimiento DEMO123BO'
        assert history[1]['content'] == answer['answer']
        assert history[1]['rows'] == answer['rows']
        followup = client.post('/api/chat', headers=headers, json={'message': '¿Y su estado?', 'session_id': chat_id}).json()
        assert followup['rows'][0]['tracking_code'] == 'DEMO123BO'
        assert client.get('/api/sessions/' + chat_id, headers={'Authorization': 'Bearer ' + OTHER}).status_code == 404
        assert client.get('/api/sessions', headers={'Authorization': 'Bearer ' + OTHER}).json()['sessions'] == []
    with TestClient(create_app(config(tmp_path / 'chats.sqlite3', ['internal_data', 'offices']))) as client:
        assert client.get('/api/sessions/' + chat_id, headers=headers).status_code == 403
        assert client.get('/api/sessions', headers=headers).json()['sessions'] == []


def test_cache_expiry_does_not_delete_saved_chats_and_limit_does_not_erase(tmp_path):
    settings = config(tmp_path / 'chats.sqlite3').model_copy(update={'max_sessions': 1})
    headers = {'Authorization': 'Bearer ' + TOKEN}
    app = create_app(settings)
    with TestClient(app) as client:
        result = client.post('/api/chat', headers=headers, json={'message': 'hola'}).json()
        app.state.conversation.sessions[result['session_id']].touched = 0
        assert client.get('/api/sessions/' + result['session_id'], headers=headers).json()['messages'][0]['content'] == 'hola'
        assert client.post('/api/chat', headers=headers, json={'message': 'hola'}).status_code == 429
        assert len(client.get('/api/sessions', headers=headers).json()['sessions']) == 1


def test_saved_history_keeps_more_than_forty_messages_and_records_failed_turn(tmp_path):
    settings = config(tmp_path / 'chats.sqlite3')
    headers = {'Authorization': 'Bearer ' + TOKEN}
    with TestClient(create_app(settings)) as client:
        chat_id = None
        for _ in range(21):
            chat_id = client.post('/api/chat', headers=headers, json={'message': 'hola', 'session_id': chat_id}).json()['session_id']
        assert client.post('/api/chat', headers=headers, json={'message': 'resumen 2026-02-30 2026-03-02', 'session_id': chat_id}).status_code == 422
    with TestClient(create_app(settings)) as client:
        messages = client.get('/api/sessions/' + chat_id, headers=headers).json()['messages']
        assert len(messages) == 44
        assert messages[0]['content'] == 'hola'
        assert messages[-2]['content'] == 'resumen 2026-02-30 2026-03-02'
        assert messages[-1]['status'] == 'error'
