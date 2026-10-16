from datetime import datetime, timezone
import json

from fastapi.testclient import TestClient
import pytest

from app.bootstrap import create_app
from app.contracts import AccessContext, IntentDecision
from app.data_access.public import QueryResult
from app.operations.public import ToolRegistry
from app.settings import Settings

PRINCIPAL = AccessContext(user_id='operator', permissions=frozenset({'internal_data', 'offices', 'personal_data'}), scope=('global_internal',))
TOKEN = 'relations-test-token-0001'


class Reader:
    async def run_read(self, query, context):
        if query.template in {'offices_related_details', 'offices_table_details'}:
            rows = [{'office_id': 2, 'table_name': 'paquetes_ems', 'total_count': 37, 'relation_kind': 'descendant', 'path_info': 'sucursales → users → paquetes_ems', 'descendant_count': 30, 'lookup_count': 7}]
        elif query.template == 'offices_records_details':
            assert query.parameters['table_name'] == 'paquetes_ems'
            rows = [{'record_key': str(i), 'record': {'id': i, 'codigo': 'FICTICIO'}, 'relation_kind': 'descendant' if i < 30 else 'lookup'} for i in range(query.parameters['offset'], min(37, query.parameters['offset'] + query.parameters['page_limit']))]
        else:
            rows = [{'office_id': 2, 'department': 'SANTA CRUZ', 'details': {'campos': {'id': 2}, 'relaciones': {}}}]
        return QueryResult(rows, 'Fixture', datetime.now(timezone.utc))


async def test_office_inventory_includes_table_counts_without_dumping_records():
    result = await ToolRegistry(Reader()).related_tables(2, PRINCIPAL)
    tables = result.rows
    assert tables[0]['table_name'] == 'paquetes_ems' and tables[0]['total_count'] == 37
    assert tables[0]['descendant_count'] == 30 and tables[0]['lookup_count'] == 7
    assert 'record' not in tables[0]


def test_related_records_are_authenticated_and_page_without_silent_loss():
    config = Settings(demo_mode=True, identities_json=json.dumps({TOKEN: PRINCIPAL.model_dump(mode='json')}))
    with TestClient(create_app(config, reader=Reader())) as client:
        url = '/api/offices/2/relations/paquetes_ems'
        assert client.get(url).status_code == 401
        headers = {'Authorization': 'Bearer ' + TOKEN}
        first = client.get(url + '?limit=20&offset=0', headers=headers).json()
        second = client.get(url + '?limit=20&offset=20', headers=headers).json()
        assert len(first['rows']) == 20 and first['next_offset'] == 20
        assert len(second['rows']) == 17 and second['next_offset'] is None
        assert first['total_count'] == 37
        assert second['rows'][-1]['relation_kind'] == 'lookup'
        assert set(row['record_key'] for row in first['rows']).isdisjoint(row['record_key'] for row in second['rows'])
        assert client.get(url + '?limit=1000', headers=headers).status_code == 422
        assert client.get('/api/offices/2/relations/users%3Bselect', headers=headers).status_code == 422


def test_related_records_need_personal_permission_even_with_office_permission():
    principal = PRINCIPAL.model_copy(update={'permissions': frozenset({'internal_data', 'offices'})})
    config = Settings(demo_mode=True, identities_json=json.dumps({TOKEN: principal.model_dump(mode='json')}))
    with TestClient(create_app(config, reader=Reader())) as client:
        assert client.get('/api/offices/2/relations/paquetes_ems', headers={'Authorization': 'Bearer ' + TOKEN}).status_code == 403
        assert client.get('/api/offices/2/relations', headers={'Authorization': 'Bearer ' + TOKEN}).status_code == 403
