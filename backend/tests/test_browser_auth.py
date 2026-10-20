import json
import secrets
import sqlite3
import time

from fastapi.testclient import TestClient
from app.bootstrap import create_app
from app.identity.public import BrowserAuth, COOKIE_NAME, password_hash, token_hash
from app.settings import Settings

PASSWORD = secrets.token_urlsafe(24)
NEW_PASSWORD = secrets.token_urlsafe(24)
ORIGIN = {'Origin': 'http://testserver'}
PERMISSIONS = ['internal_data', 'tracking', 'offices', 'summary', 'personal_data']


def configured(tmp_path, **updates):
    return Settings(demo_mode=True, history_path=str(tmp_path / 'history.sqlite3'),
                    auth_path=str(tmp_path / 'auth.sqlite3'), **updates)


def provision(settings):
    auth = BrowserAuth(settings)
    auth.create_user('alice', PASSWORD, user_id='operador-local', display_name='Alice', permissions=PERMISSIONS, scope=['global_internal'])
    auth.create_user('bob', PASSWORD, permissions=PERMISSIONS, scope=['global_internal'])
    return auth


def login(client, username='alice'):
    return client.post('/api/auth/login', headers=ORIGIN, json={'username': username, 'password': PASSWORD})


def test_login_persists_restarts_expires_and_logout_revokes(tmp_path):
    settings = configured(tmp_path)
    auth = provision(settings)
    with TestClient(create_app(settings)) as client:
        assert client.get('/api/auth/me').status_code == 401
        result = login(client)
        assert result.json() == {'user': {'user_id': 'operador-local', 'username': 'alice', 'display_name': 'Alice'}}
        cookie = result.headers['set-cookie'].lower()
        assert 'httponly' in cookie and 'samesite=strict' in cookie and 'path=/api' in cookie
        assert result.headers['cache-control'] == 'no-store'
        token = client.cookies.get(COOKIE_NAME)
        assert client.get('/api/auth/me').json() == result.json()
    with sqlite3.connect(settings.auth_path) as db:
        row = db.execute('SELECT token_hash FROM auth_sessions').fetchone()
        assert row[0] == token_hash(token) and token not in row[0]
        assert PASSWORD not in db.execute('SELECT password_hash FROM auth_users WHERE username="alice"').fetchone()[0]
    with TestClient(create_app(settings)) as client:
        client.cookies.set(COOKIE_NAME, token, path='/api')
        assert client.get('/api/auth/me').status_code == 200
        assert client.post('/api/auth/logout', headers=ORIGIN).status_code == 200
        assert client.get('/api/auth/me').status_code == 401
        client.cookies.set(COOKIE_NAME, token, path='/api')
        assert client.get('/api/auth/me').status_code == 401
        token, _ = auth.login('alice', PASSWORD, 'expiry-test')
        with auth.store.connect() as db:
            db.execute('UPDATE auth_sessions SET expires_at=? WHERE token_hash=?', (time.time()-1, token_hash(token)))
        client.cookies.set(COOKIE_NAME, token, path='/api')
        assert client.get('/api/sessions').status_code == 401


def test_cookie_chat_ownership_edit_delete_cancel_and_stream(tmp_path):
    settings = configured(tmp_path)
    provision(settings)
    app = create_app(settings)
    with TestClient(app) as alice, TestClient(app) as bob:
        assert login(alice).status_code == 200
        assert login(bob, 'bob').status_code == 200
        saved = alice.post('/api/chat', headers=ORIGIN, json={'message': 'hola'}).json()['session_id']
        assert len(alice.get('/api/sessions').json()['sessions']) == 1
        assert bob.get('/api/sessions').json()['sessions'] == []
        url = '/api/sessions/' + saved
        assert bob.get(url).status_code == 404
        assert bob.delete(url, headers=ORIGIN).status_code == 404
        for endpoint in ['/api/chat', '/api/chat/stream']:
            assert bob.post(endpoint, headers=ORIGIN, json={'message': 'otro', 'session_id': saved, 'edit_message_index': 0}).status_code == 404
        class ProtectedTask:
            def cancel(self):
                raise AssertionError('No debe cancelarse una consulta ajena.')

        app.state.conversation.running['alice-request'] = ('operador-local', ProtectedTask())
        assert bob.post('/api/requests/alice-request/cancel', headers=ORIGIN).status_code == 404
        app.state.conversation.running.clear()
        streamed = alice.post('/api/chat/stream', headers=ORIGIN, json={'message': 'hola', 'session_id': saved})
        assert streamed.status_code == 200 and 'event: completed' in streamed.text
        assert alice.delete(url, headers=ORIGIN).json() == {'deleted': True}


def test_origin_checks_validation_credentials_throttling_and_secure_cookie(tmp_path):
    settings = configured(tmp_path, auth_login_max_attempts=2, auth_cookie_secure=True)
    provision(settings)
    with TestClient(create_app(settings), base_url='https://testserver') as client:
        body = {'username': 'alice', 'password': PASSWORD}
        assert client.post('/api/auth/login', json=body).status_code == 403
        assert client.post('/api/auth/login', headers={'Origin': 'https://evil.example'}, json=body).status_code == 403
        headers = {'Origin': 'https://testserver'}
        invalid = client.post('/api/auth/login', headers=headers, json={**body, 'permissions': PERMISSIONS})
        assert invalid.status_code == 422 and PASSWORD not in invalid.text
        result = client.post('/api/auth/login', headers=headers, json=body)
        assert result.status_code == 200 and '; Secure' in result.headers['set-cookie']
        assert client.cookies.get(COOKIE_NAME)
        assert client.post('/api/chat', json={'message': 'hola'}).status_code == 403
        assert client.post('/api/auth/logout', headers={'Origin': 'https://evil.example'}).status_code == 403
        assert client.get('/api/auth/me').status_code == 200
        assert client.post('/api/auth/login', headers=headers, json={**body, 'password': 'wrong'}).status_code == 401
        assert client.post('/api/auth/login', headers=headers, json=body).status_code == 429


def test_password_reset_revokes_sessions_and_bearer_can_see_migrated_history(tmp_path):
    legacy = {'user_id': 'operador-local', 'permissions': PERMISSIONS, 'scope': ['global_internal']}
    settings = configured(tmp_path, identities_json=json.dumps({'legacy-token-123456789': legacy}))
    auth = provision(settings)
    with TestClient(create_app(settings)) as client:
        saved = client.post('/api/chat', headers={'Authorization': 'Bearer legacy-token-123456789'}, json={'message': 'hola'}).json()['session_id']
        assert login(client).status_code == 200
        assert client.get('/api/sessions').json()['sessions'][0]['session_id'] == saved
        auth.store.reset_password('alice', password_hash(NEW_PASSWORD))
        assert client.get('/api/auth/me').status_code == 401
        assert login(client).status_code == 401
        assert client.post('/api/auth/login', headers=ORIGIN, json={'username': 'alice', 'password': NEW_PASSWORD}).status_code == 200


def test_throttle_survives_restart_and_missing_user_errors_match(tmp_path):
    settings = configured(tmp_path, auth_login_max_attempts=2)
    provision(settings)
    for name in ['alice', 'unknown']:
        with TestClient(create_app(settings)) as client:
            result = client.post('/api/auth/login', headers=ORIGIN, json={'username': name, 'password': 'wrong'})
            assert result.status_code == 401
            assert result.json()['error']['message'] == 'Usuario o contraseña incorrectos.'
    with TestClient(create_app(settings)) as client:
        assert login(client).status_code == 429


def test_revoked_cookie_stops_running_stream(tmp_path):
    from app.contracts import IntentDecision

    settings = configured(tmp_path)
    provision(settings)
    app = create_app(settings)

    class RevokingModel:
        async def interpret(self, message, context):
            with app.state.browser_auth.store.connect() as db:
                db.execute('DELETE FROM auth_sessions')
            return IntentDecision(operation='outside')

    app.state.conversation.model = RevokingModel()
    with TestClient(app) as client:
        assert login(client).status_code == 200
        stream = client.post('/api/chat/stream', headers=ORIGIN, json={'message': 'consulta de prueba'})
        assert 'unauthenticated' in stream.text
        assert 'event: completed' not in stream.text
        assert 'event: answer_chunk' not in stream.text


def test_password_reset_during_login_cannot_create_session_with_old_password(tmp_path, monkeypatch):
    from app.contracts import ServiceError
    import pytest

    settings = configured(tmp_path)
    auth = provision(settings)
    original = auth.store.create_session

    def reset_then_create(*args):
        auth.store.reset_password('alice', password_hash(NEW_PASSWORD))
        return original(*args)

    monkeypatch.setattr(auth.store, 'create_session', reset_then_create)
    with pytest.raises(ServiceError) as error:
        auth.login('alice', PASSWORD, 'reset-race-test')
    assert error.value.status_code == 401
    with auth.store.connect() as db:
        assert db.execute('SELECT count(*) FROM auth_sessions').fetchone()[0] == 0
