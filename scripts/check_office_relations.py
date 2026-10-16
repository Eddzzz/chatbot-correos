"""Verify real office relation inventory and pagination without printing private records."""
import json
import urllib.request

from import_backup import ROOT


def main():
    import psycopg
    runtime = ROOT / '.runtime'
    token = (runtime / 'operator-token.txt').read_text().strip()

    def get(path):
        request = urllib.request.Request('http://127.0.0.1:8000' + path, headers={'Authorization': 'Bearer ' + token})
        with urllib.request.urlopen(request, timeout=15) as response:
            return json.load(response)

    inventory = get('/api/offices/2/relations')
    catalog = json.loads((ROOT / 'config/office_relations_catalog.json').read_text(encoding='utf-8'))
    assert not inventory['truncated']
    assert {row['table_name'] for row in inventory['rows']} == set(catalog['tables'])
    assert not set(catalog['excluded_tables']).intersection(row['table_name'] for row in inventory['rows'])
    with psycopg.connect((runtime / 'institutional-dsn.txt').read_text().strip()) as connection:
        connection.execute("SELECT set_config('chatbot.access_scope','global_internal',true), set_config('chatbot.personal_access','allowed',true)")
        expected = dict(connection.execute('SELECT table_name,total_count FROM chatbot.v_office_related_counts WHERE office_id=2').fetchall())
    assert {row['table_name']: row['total_count'] for row in inventory['rows']} == expected
    assert all(row['descendant_count'] + row['lookup_count'] == row['total_count'] for row in inventory['rows'])
    users = next(row for row in inventory['rows'] if row['table_name'] == 'users')
    assert users['descendant_count'] == 2 and users['lookup_count'] == 40
    table = next(row['table_name'] for row in inventory['rows'] if row['table_name'] == 'paquetes_ems' and row['total_count'] > 20)
    first = get(f'/api/offices/2/relations/{table}?limit=10&offset=0')
    second = get(f'/api/offices/2/relations/{table}?limit=10&offset={first["next_offset"]}')
    assert len(first['rows']) == len(second['rows']) == 10
    assert first['total_count'] == expected[table] and second['offset'] == 10
    assert {row['record_key'] for row in first['rows']}.isdisjoint(row['record_key'] for row in second['rows'])
    forbidden = {'password', 'remember_token', 'session_reference', 'device_id', 'api_token'}
    for row in first['rows'] + second['rows']:
        assert not forbidden.intersection(row['record']['campos'])
        assert row['relation_kind'] in {'descendant', 'lookup'}
    report = {'inventory_tables': len(inventory['rows']), 'inventory_matches_postgres': True,
              'office': 2, 'related_records': sum(expected.values()), 'page_size': 10,
              'two_pages_without_duplicates': True, 'authentication_tables_excluded': True}
    (runtime / 'office-relations-api-validation.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
