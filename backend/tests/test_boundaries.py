import pytest
from fastapi.testclient import TestClient

from app.bootstrap import create_app
from app.settings import Settings
from app.data_access.public import QuerySpec, validate_query


def test_authentication_and_unknown_fields_fail_closed():
    with TestClient(create_app(Settings(demo_mode=True))) as client:
        assert client.post('/api/chat', json={'message': 'hola'}).status_code == 401


def test_sql_catalog_rejects_mutation_and_unknown_template():
    with pytest.raises(ValueError):
        validate_query(QuerySpec(template='arbitrary', parameters={}), 'DELETE FROM users')


def test_demo_greeting_and_session_ownership():
    config = Settings(demo_mode=True, identities_json='{"test-token-000001":{"user_id":"alice","permissions":["tracking","offices","summary","internal_data","diagnostics"],"scope":["global_internal"]},"other-token-00001":{"user_id":"bob","permissions":[],"scope":[]}}')
    with TestClient(create_app(config)) as client:
        response = client.post('/api/chat', headers={'Authorization': 'Bearer test-token-000001'}, json={'message': 'hola'})
        assert response.status_code == 200
        body = response.json()
        assert body['request_id'] and body['session_id']
        assert body['status'] == 'answer'
        denied = client.get(f"/api/sessions/{body['session_id']}/history", headers={'Authorization': 'Bearer other-token-00001'})
        assert denied.status_code == 404
        invalid = client.post('/api/chat', headers={'Authorization': 'Bearer test-token-000001'}, json={'message':'hola','role':'admin'})
        assert invalid.status_code == 422
