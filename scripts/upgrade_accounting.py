"""Atomically expose reviewed accounting records in the project-owned copy.

The backup is read only. Invoice records contain only an id and timestamps;
they do not establish invoice issuance, amounts, currency or tax status.
"""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path

from import_backup import DATABASE, ROOT
import upgrade_details

SCHEMA = 'chatbot_accounting_source'
CATALOG = {'tables': {'facturas': {
    'columns': {'id': 'bigint', 'created_at': 'timestamp', 'updated_at': 'timestamp'},
    'presence': [], 'excluded': [],
}}}


def main():
    import psycopg
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('backup', type=Path)
    args = parser.parse_args()
    with args.backup.open('rb') as handle:
        if handle.read(5) != b'PGDMP':
            raise ValueError('Custom PostgreSQL backup required')
    password = (ROOT / '.runtime/initdb-password').read_text().strip()
    with psycopg.connect(host='127.0.0.1', port=55432, dbname=DATABASE,
                         user='fixture_admin', password=password) as connection:
        if connection.execute('SELECT 1 FROM pg_namespace WHERE nspname=%s', (SCHEMA,)).fetchone():
            raise ValueError('Accounting schema exists; nothing overwritten')
        connection.execute('''CREATE SCHEMA chatbot_accounting_source;
            REVOKE ALL ON SCHEMA chatbot_accounting_source
              FROM PUBLIC,chatbot_reader,chatbot_institutional;
            CREATE TABLE chatbot_accounting_source.facturas (
              id bigint PRIMARY KEY, created_at timestamp, updated_at timestamp);''')
        previous_schema = upgrade_details.SCHEMA
        try:
            upgrade_details.SCHEMA = SCHEMA
            counts = upgrade_details.stream_details(connection, args.backup, CATALOG)
        finally:
            upgrade_details.SCHEMA = previous_schema
        actual = connection.execute('SELECT count(*) FROM chatbot_accounting_source.facturas').fetchone()[0]
        if actual != counts['facturas']:
            raise ValueError('Backup COPY count and imported count differ')
        connection.execute('''CREATE INDEX ON chatbot_accounting_source.facturas(created_at,id);
            CREATE INDEX IF NOT EXISTS cashier_movement_accounting_date_idx
              ON chatbot_relations_source.cashier_flow_receivable_movements(cobrado_at,id);
            CREATE INDEX IF NOT EXISTS cashier_collection_accounting_date_idx
              ON chatbot_relations_source.cashier_flow_receivable_collections(cobrado_at,id);
            ANALYZE chatbot_accounting_source.facturas;''')
        connection.execute((ROOT / 'database/views/005_accounting.sql').read_text(encoding='utf-8'))
        connection.execute('SET LOCAL ROLE chatbot_institutional')
        if connection.execute('SELECT count(*) FROM chatbot.v_accounting_records').fetchone()[0] != 0:
            raise ValueError('Guarded view returned data without scope')
        connection.execute("SET LOCAL chatbot.access_scope='global_internal'")
        if connection.execute('SELECT count(*) FROM chatbot.v_accounting_records').fetchone()[0] != 0:
            raise ValueError('Guarded view returned data without personal scope')
        connection.execute("SET LOCAL chatbot.personal_access='allowed'")
        rows = connection.execute('''SELECT categories.category,count(records.record_id),
            min(records.occurred_at),max(records.occurred_at),
            count(records.record_id) FILTER (WHERE records.occurred_at IS NULL)
            FROM (VALUES ('movimientos'),('cobros'),('facturacion')) categories(category)
            LEFT JOIN chatbot.v_accounting_records records USING (category)
            GROUP BY categories.category ORDER BY categories.category''').fetchall()
        connection.execute('RESET ROLE')
        for role in ('chatbot_institutional', 'chatbot_reader'):
            if connection.execute('SELECT has_schema_privilege(%s,%s,\'USAGE\')', (role, SCHEMA)).fetchone()[0]:
                raise ValueError('Reader can access private accounting schema')
    report = {'status': 'imported', 'database': DATABASE, 'schema': SCHEMA,
              'imported_at': datetime.now(timezone.utc).isoformat(), 'backup_copy_rows': counts,
              'source_backup_unchanged': True, 'reader_guards_verified': True,
              'categories': [{'category': r[0], 'rows': r[1], 'first_date': str(r[2]),
                              'last_date': str(r[3]), 'undated_rows': r[4]} for r in rows],
              'semantics': 'Movements and collections filtered by cobrado_at; facturas by created_at. No totals or currency inferred.'}
    (ROOT / '.runtime/accounting-import.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report), flush=True)


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        # COPY diagnostics can contain private records: report only the type.
        raise SystemExit(f'Accounting import failed ({type(error).__name__}); transaction rolled back. No source rows logged.') from None
