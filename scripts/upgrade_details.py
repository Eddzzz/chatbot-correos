"""Import reviewed full postal records into the project-owned local database only.

Never executes backup SQL. Authentication columns are excluded; attachments are
replaced by boolean presence flags. All changes commit atomically.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import subprocess
import tempfile

from import_backup import DATABASE, ROOT, find_pg_restore, project_copy_row

SCHEMA = 'chatbot_details_source'
CATALOG = ROOT / 'config/details_catalog.json'


def copy_header(line, tables):
    match = re.fullmatch(r'COPY public\.([a-z_]+) \(([^;]+)\) FROM stdin;\s*', line)
    if not match or match[1] not in tables:
        raise ValueError('Unapproved COPY table')
    columns = [part.strip().strip('"') for part in match[2].split(',')]
    if len(columns) != len(set(columns)) or any(not re.fullmatch(r'[A-Za-z_][A-Za-z_0-9]*', c) for c in columns):
        raise ValueError('Invalid COPY columns')
    return match[1], columns


def stream_details(connection, backup, catalog):
    from psycopg import sql
    tables = catalog['tables']
    command = [find_pg_restore(), '--data-only', '--no-owner', '--no-privileges', '--file=-', '--schema=public']
    command += ['--table=' + name for name in tables]
    counts = Counter()
    with tempfile.TemporaryFile() as errors:
        process = subprocess.Popen(command + [str(backup)], stdout=subprocess.PIPE, stderr=errors)
        try:
            for line in process.stdout:
                if not line.startswith(b'COPY '):
                    continue
                name, source_columns = copy_header(line.decode('utf-8'), tables)
                if name in counts:
                    raise ValueError('Duplicate COPY table')
                spec = tables[name]
                approved = list(spec['columns'])
                indexes = [source_columns.index(col) for col in approved]
                presence = [source_columns.index(col) for col in spec['presence']]
                output_columns = approved + [col + '_presente' for col in spec['presence']]
                statement = sql.SQL('COPY {}.{} ({}) FROM STDIN').format(
                    sql.Identifier(SCHEMA), sql.Identifier(name), sql.SQL(',').join(map(sql.Identifier, output_columns)))
                counts[name] = 0
                with connection.cursor().copy(statement) as target:
                    batch = bytearray()
                    for row in process.stdout:
                        if row.rstrip(b'\r\n') == b'\\.':
                            break
                        projected = project_copy_row(row, indexes, len(source_columns))
                        if presence:
                            fields = row.rstrip(b'\r\n').split(b'\t')
                            flags = [b'f' if fields[i] in (b'\\N', b'') else b't' for i in presence]
                            projected = projected[:-1] + b'\t' + b'\t'.join(flags) + b'\n'
                        batch.extend(projected)
                        counts[name] += 1
                        if len(batch) >= 256 * 1024:
                            target.write(batch)
                            batch.clear()
                    else:
                        raise ValueError('Incomplete COPY')
                    if batch:
                        target.write(batch)
                print(json.dumps({'table': name, 'rows': counts[name]}), flush=True)
            if process.wait() != 0 or set(counts) != set(tables):
                raise RuntimeError('Incomplete extraction; transaction rolled back')
        finally:
            process.stdout.close()
            if process.poll() is None:
                process.terminate()
            process.wait()
    return dict(counts)


def main():
    import psycopg
    from psycopg import sql
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('backup', type=Path)
    args = parser.parse_args()
    with args.backup.open('rb') as source:
        if source.read(5) != b'PGDMP':
            raise SystemExit('Custom PostgreSQL backup required')
    catalog = json.loads(CATALOG.read_text(encoding='utf-8'))
    password = (ROOT / '.runtime/initdb-password').read_text().strip()
    with psycopg.connect(host='127.0.0.1', port=55432, dbname=DATABASE, user='fixture_admin', password=password) as connection:
        if connection.execute('SELECT 1 FROM pg_namespace WHERE nspname=%s', (SCHEMA,)).fetchone():
            raise SystemExit('Details schema already exists; nothing overwritten')
        connection.execute(sql.SQL('CREATE SCHEMA {}').format(sql.Identifier(SCHEMA)))
        connection.execute(sql.SQL('REVOKE ALL ON SCHEMA {} FROM PUBLIC, chatbot_reader, chatbot_institutional').format(sql.Identifier(SCHEMA)))
        for name, spec in catalog['tables'].items():
            columns = dict(spec['columns']) | {c + '_presente': 'boolean' for c in spec['presence']}
            definitions = [sql.SQL('{} {}').format(sql.Identifier(col), sql.SQL(kind)) for col, kind in columns.items()]
            connection.execute(sql.SQL('CREATE TABLE {}.{} ({})').format(sql.Identifier(SCHEMA), sql.Identifier(name), sql.SQL(',').join(definitions)))
        counts = stream_details(connection, args.backup, catalog)
        for name, spec in catalog['tables'].items():
            indexes = {'id'} | {c for c in spec['columns'] if c.endswith('_id') or c.startswith('id_') or c.startswith('fk_')}
            indexes |= {'codigo'} & spec['columns'].keys()
            for column in sorted(indexes & spec['columns'].keys()):
                connection.execute(sql.SQL('CREATE INDEX ON {}.{} ({})').format(sql.Identifier(SCHEMA), sql.Identifier(name), sql.Identifier(column)))
            connection.execute(sql.SQL('ANALYZE {}.{}').format(sql.Identifier(SCHEMA), sql.Identifier(name)))
        connection.execute((ROOT / 'database/views/003_details.sql').read_text(encoding='utf-8'))
    report = {'status': 'imported', 'database': DATABASE, 'schema': SCHEMA,
              'imported_at': datetime.now(timezone.utc).isoformat(), 'rows': counts,
              'omitted': {name: {'authentication': spec['excluded'], 'attachment_presence_only': spec['presence']}
                          for name, spec in catalog['tables'].items() if spec['excluded'] or spec['presence']},
              'related_record_limit': 50, 'events_join': 'codigo equality, no source FK; explicit in JSON',
              'source_backup_unchanged': True}
    (ROOT / '.runtime/details-import.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print('Details imported atomically; count-only report in .runtime/details-import.json', flush=True)


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        # COPY diagnostics can contain the rejected private source row.
        raise SystemExit(f'Details import failed ({type(error).__name__}); transaction rolled back. No source rows logged.') from None
