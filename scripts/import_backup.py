"""Build a local read model from a custom backup, retaining only approved columns.

Stream COPY values through pg_restore; never execute source SQL/functions or store
personal columns, images, users, passwords or source-table credentials.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import secrets
import subprocess
import tempfile

from inspect_backup import find_pg_restore

ROOT = Path(__file__).resolve().parents[1]
DATABASE = 'correos_sandbox_institutional'
ROLE = 'chatbot_institutional'
TABLES = {
    'estados': {'id': 'bigint', 'nombre_estado': 'text'},
    'sucursales': {'id': 'bigint', 'codigoSucursal': 'integer', 'municipio': 'text', 'departamento': 'text', 'telefono': 'text'},
}
for name, state, destination, origin in (
    ('certi', 'fk_estado', 'cuidad', False), ('ordi', 'fk_estado', 'ciudad', False),
    ('ems', 'estado_id', 'ciudad', True), ('contrato', 'estados_id', 'destino', True),
    ('int', 'estado_id', 'destino', True),
):
    columns = {'id': 'bigint', 'codigo': 'text', state: 'bigint', destination: 'text',
               'created_at': 'timestamp', 'updated_at': 'timestamp', 'peso': 'numeric', 'precio': 'numeric'}
    if origin:
        columns['origen'] = 'text'
    TABLES['paquetes_' + name] = columns


def parse_copy_header(line):
    match = re.fullmatch(r'COPY public\.([a-z_]+) \(([^;]+)\) FROM stdin;\s*', line)
    if not match or match[1] not in TABLES:
        raise ValueError('COPY fuera de las tablas aprobadas.')
    columns = [value.strip().strip('"') for value in match[2].split(',')]
    if len(columns) != len(set(columns)) or not all(re.fullmatch(r'[A-Za-z_][A-Za-z_0-9]*', value) for value in columns):
        raise ValueError('Columnas COPY inválidas.')
    return match[1], columns


def project_copy_row(row, indexes, expected_columns):
    fields = row.rstrip(b'\r\n').split(b'\t')
    if len(fields) != expected_columns:
        raise ValueError('Fila COPY inválida; no se importará.')
    return b'\t'.join(fields[index] for index in indexes) + b'\n'


def stream_projection(connection, backup):
    from psycopg import sql
    command = [find_pg_restore(), '--data-only', '--no-owner', '--no-privileges', '--file=-', '--schema=public']
    command += ['--table=' + table for table in TABLES]
    counts = Counter()
    with tempfile.TemporaryFile() as errors:
        process = subprocess.Popen(command + [str(backup)], stdout=subprocess.PIPE, stderr=errors)
        try:
            for line in process.stdout:
                if not line.startswith(b'COPY '):
                    continue
                table, source_columns = parse_copy_header(line.decode('utf-8'))
                if table in counts:
                    raise ValueError('Tabla COPY duplicada.')
                approved = list(TABLES[table])
                indexes = [source_columns.index(column) for column in approved]
                statement = sql.SQL('COPY public.{} ({}) FROM STDIN').format(
                    sql.Identifier(table), sql.SQL(',').join(map(sql.Identifier, approved)))
                counts[table] = 0
                with connection.cursor().copy(statement) as target:
                    batch = bytearray()
                    for row in process.stdout:
                        if row.rstrip(b'\r\n') == b'\\.':
                            break
                        batch.extend(project_copy_row(row, indexes, len(source_columns)))
                        counts[table] += 1
                        if len(batch) >= 256 * 1024:
                            target.write(batch)
                            batch.clear()
                    else:
                        raise ValueError('COPY incompleto.')
                    if batch:
                        target.write(batch)
                print(json.dumps({'table': table, 'imported_rows': counts[table]}), flush=True)
            if process.wait() != 0 or set(counts) != set(TABLES):
                raise RuntimeError('Extracción incompleta. La transacción será revertida.')
        finally:
            process.stdout.close()
            if process.poll() is None:
                process.terminate()
            process.wait()
    return counts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('backup', type=Path)
    args = parser.parse_args()
    with args.backup.open('rb') as source:
        if source.read(5) != b'PGDMP':
            raise SystemExit('Se requiere un respaldo custom de PostgreSQL.')
    import psycopg
    from psycopg import sql
    runtime = ROOT / '.runtime'
    password = (runtime / 'initdb-password').read_text().strip()
    # Fixed project-owned local cluster only; never take a production DSN.
    admin_options = dict(host='127.0.0.1', port=55432, user='fixture_admin', password=password)
    with psycopg.connect(**admin_options, dbname='postgres', autocommit=True) as admin:
        if admin.execute('SELECT 1 FROM pg_database WHERE datname=%s', (DATABASE,)).fetchone():
            raise SystemExit('El destino ya existe. No se sobrescribió; revisar estado antes de reintentar.')
        admin.execute(sql.SQL('CREATE DATABASE {}').format(sql.Identifier(DATABASE)))
    reader_secret = secrets.token_hex(32)
    with psycopg.connect(**admin_options, dbname=DATABASE) as connection:
        for table, columns in TABLES.items():
            definitions = [sql.SQL('{} {}').format(sql.Identifier(name), sql.SQL(kind)) for name, kind in columns.items()]
            connection.execute(sql.SQL('CREATE TABLE public.{} ({})').format(sql.Identifier(table), sql.SQL(',').join(definitions)))
        counts = stream_projection(connection, args.backup)
        for table in TABLES:
            connection.execute(sql.SQL('CREATE UNIQUE INDEX ON public.{} (id)').format(sql.Identifier(table)))
            if table.startswith('paquetes_'):
                connection.execute(sql.SQL('CREATE INDEX ON public.{} (codigo)').format(sql.Identifier(table)))
                connection.execute(sql.SQL('CREATE INDEX ON public.{} (created_at)').format(sql.Identifier(table)))
            connection.execute(sql.SQL('ANALYZE public.{}').format(sql.Identifier(table)))
        # Keep data, indexes, views and reader provisioning in one transaction.
        # These repository-owned scripts include standalone transaction wrappers.
        for relative in ('database/views/001_projection.sql', 'database/policies/002_reader_role.sql'):
            body = (ROOT / relative).read_text(encoding='utf-8')
            connection.execute(re.sub(r'(?m)^(?:BEGIN|COMMIT);[ \t]*$', '', body))
        connection.execute(sql.SQL('CREATE ROLE {} LOGIN PASSWORD {} NOSUPERUSER NOCREATEDB NOCREATEROLE INHERIT NOBYPASSRLS').format(sql.Identifier(ROLE), sql.Literal(reader_secret)))
        connection.execute(sql.SQL('GRANT chatbot_reader TO {}').format(sql.Identifier(ROLE)))
        connection.execute(sql.SQL('ALTER ROLE {} SET default_transaction_read_only=on').format(sql.Identifier(ROLE)))
        connection.execute(sql.SQL("ALTER ROLE {} SET lock_timeout='1s'").format(sql.Identifier(ROLE)))
        connection.execute(sql.SQL("ALTER ROLE {} SET idle_in_transaction_session_timeout='10s'").format(sql.Identifier(ROLE)))
        connection.execute('REVOKE CONNECT ON DATABASE ' + DATABASE + ' FROM PUBLIC')
        connection.execute(sql.SQL('GRANT CONNECT ON DATABASE {} TO {}').format(sql.Identifier(DATABASE), sql.Identifier(ROLE)))
        connection.commit()
    dsn = f'postgresql://{ROLE}:{reader_secret}@127.0.0.1:55432/{DATABASE}'
    (runtime / 'institutional-dsn.txt').write_text(dsn, encoding='utf-8')
    report = {'status': 'imported', 'source': str(args.backup), 'source_bytes': args.backup.stat().st_size,
              'imported_at': datetime.now(timezone.utc).isoformat(), 'database': DATABASE,
              'rows': dict(counts), 'personal_columns_retained': False,
              'note': 'Copia local del respaldo, sin actualizaciones en vivo. Semántica de tarifas no validada.'}
    (runtime / 'institutional-import.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print('Importación completa. DSN privado en .runtime/institutional-dsn.txt; API todavía sin cambiar.', flush=True)


if __name__ == '__main__':
    main()
