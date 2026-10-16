"""Build the reviewed office FK closure in the project-owned local database.

Only COPY values are read from the backup. Source DDL is never executed.
All imports, graph memberships and public read views commit together.
"""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re

from import_backup import DATABASE, ROOT
import upgrade_details

SCHEMA = 'chatbot_relations_source'
CATALOG = ROOT / 'config/office_relations_catalog.json'


def generate_catalog():
    """Derive only structural FK associations; source SQL is read as text."""
    schema = (ROOT/'docs/source-schema.sql').read_text(encoding='utf-8')
    definitions = dict(re.findall(r'CREATE TABLE public\.(\w+) \(\n(.*?)\n\);', schema, re.S))
    fks = [{'child':c,'parent':p,'child_columns':[v.strip().strip('"') for v in cc.split(',')],
            'parent_columns':[v.strip().strip('"') for v in pc.split(',')]}
           for c,cc,p,pc in re.findall(r'ALTER TABLE ONLY public\.(\w+)\s+ADD CONSTRAINT [^\n]+? FOREIGN KEY \(([^)]+)\) REFERENCES public\.(\w+)\(([^)]+)\)',schema)]
    excluded = {name:'Metadatos de autenticación, seguridad o snapshots; no se exponen datos operativos de esta tabla.'
                for name in ['activity_logs','external_api_tokens','mobile_db_snapshots','user_ips_links','user_login_logs']}
    reached = {'sucursales'}
    while True:
        new = {fk['child'] for fk in fks if fk['parent'] in reached} - excluded.keys()
        if new <= reached:
            break
        reached |= new
    descendants = set(reached)
    while True:
        new = {fk['parent'] for fk in fks if fk['child'] in reached} - excluded.keys()
        if new <= reached:
            break
        reached |= new
    details = json.loads((ROOT/'config/details_catalog.json').read_text(encoding='utf-8'))['tables']
    tables = {}
    for name in sorted(reached):
        kind = 'descendant' if name in descendants else 'lookup'
        if name in details:
            spec = dict(details[name]) | {'source_schema':'chatbot_details_source'}
        else:
            columns, presence, omitted = {}, [], []
            for line in definitions[name].splitlines():
                match = re.match(r'\s*"?(\w+)"?\s+(.+?)(?:,)?$',line)
                if not match:
                    raise ValueError('Unparsed column definition')
                col, raw_type = match.groups()
                if re.search(r'password|token|secret|credential|api_key|verification|email_verified|session_reference|^device_id$|^device_name$',col,re.I):
                    omitted.append(col)
                elif re.search(r'image|imagen|photo|foto|_path$|^archivo|^pdf$|^mapa$|^qr_|_url$|firma_digital|documentacion_legal|^recibo$|^comprobante$|payload|meta_json|snapshot|evidence_json|datos_completos|old_values|new_values|changed_fields',col,re.I) or re.match(r'jsonb?\b|bytea\b',raw_type):
                    presence.append(col)
                else:
                    typename = raw_type.split()[0]
                    if typename.startswith('numeric') or typename in ('real','double'):
                        typename = 'numeric'
                    elif typename.startswith('timestamp'):
                        typename = 'timestamp'
                    elif typename not in ('bigint','integer','smallint','boolean','date','uuid'):
                        typename = 'text'
                    columns[col] = typename
            spec = {'columns':columns,'presence':presence,'excluded':omitted,'source_schema':SCHEMA}
        spec['path_info'] = ('Descendencia por FK desde sucursales; unión de todos los caminos.' if kind=='descendant'
                            else 'Referencia saliente por FK de registros asociados; no implica pertenencia a la sucursal.')
        tables[name] = spec
    catalog = {'tables':tables,'foreign_keys':[fk for fk in fks if fk['child'] in reached and fk['parent'] in reached],
               'excluded_tables':excluded,'method':'All incoming FK paths; then outgoing lookup closure, without reverse lookup expansion.'}
    CATALOG.write_text(json.dumps(catalog,indent=2,ensure_ascii=False),encoding='utf-8')
    return catalog


def source_name(table, spec):
    return spec.get('source_schema', SCHEMA), table


def build_graph(connection, catalog):
    from psycopg import sql
    tables = catalog['tables']
    connection.execute(f'''CREATE TABLE {SCHEMA}.nodes (
        table_name text NOT NULL, record_key text NOT NULL, record jsonb NOT NULL,
        PRIMARY KEY(table_name, record_key));
        CREATE TABLE {SCHEMA}.edges (
        child_table text NOT NULL, child_key text NOT NULL,
        parent_table text NOT NULL, parent_key text NOT NULL);
        CREATE TABLE {SCHEMA}.members (
        office_id bigint NOT NULL, table_name text NOT NULL, record_key text NOT NULL,
        relation_kind text NOT NULL, PRIMARY KEY(office_id, table_name, record_key));
        CREATE INDEX ON {SCHEMA}.members(table_name, record_key);''')
    for table, spec in tables.items():
        source = sql.Identifier(*source_name(table, spec))
        key = sql.Identifier('id' if 'id' in spec['columns'] else '__row_id')
        omitted = spec.get('excluded', []) + spec.get('presence', [])
        connection.execute(sql.SQL('''INSERT INTO {}.nodes
            SELECT %s, {}::text, jsonb_build_object('tabla', %s::text, 'campos',
              to_jsonb(s) - '__row_id', 'omitidos', %s::jsonb) FROM {} s''').format(
                sql.Identifier(SCHEMA), key, source), (table, table, json.dumps(omitted)))
    for fk in catalog['foreign_keys']:
        child, parent = fk['child'], fk['parent']
        ckey = sql.Identifier('id' if 'id' in tables[child]['columns'] else '__row_id')
        pkey = sql.Identifier('id' if 'id' in tables[parent]['columns'] else '__row_id')
        pairs = zip(fk['child_columns'], fk['parent_columns'])
        match = sql.SQL(' AND ').join(sql.SQL('c.{} = p.{}').format(sql.Identifier(c), sql.Identifier(p)) for c, p in pairs)
        connection.execute(sql.SQL('''INSERT INTO {}.edges SELECT %s,c.{}::text,%s,p.{}::text
            FROM {} c JOIN {} p ON {}''').format(sql.Identifier(SCHEMA), ckey, pkey,
                sql.Identifier(*source_name(child, tables[child])),
                sql.Identifier(*source_name(parent, tables[parent])), match), (child, parent))
    connection.execute(f'''CREATE INDEX ON {SCHEMA}.edges(parent_table,parent_key);
        CREATE INDEX ON {SCHEMA}.edges(child_table,child_key);
        ANALYZE {SCHEMA}.edges;
        INSERT INTO {SCHEMA}.members SELECT record_key::bigint,table_name,record_key,'descendant'
        FROM {SCHEMA}.nodes WHERE table_name='sucursales';''')
    iterations = {}
    # Descendants first: every declared incoming FK participates, including alternate user FKs.
    # Lookups never trigger reverse expansion into unrelated branches.
    for mode in ('descendant', 'lookup'):
        steps = 0
        while True:
            direction = ('e.parent_table=m.table_name AND e.parent_key=m.record_key' if mode == 'descendant'
                         else 'e.child_table=m.table_name AND e.child_key=m.record_key')
            selected = ('e.child_table,e.child_key' if mode == 'descendant' else 'e.parent_table,e.parent_key')
            result = connection.execute(f'''INSERT INTO {SCHEMA}.members
                SELECT DISTINCT m.office_id,{selected},%s FROM {SCHEMA}.members m
                JOIN {SCHEMA}.edges e ON {direction}
                ON CONFLICT DO NOTHING''', (mode,))
            steps += 1
            print(json.dumps({'closure':mode,'iteration':steps,'new_members':result.rowcount}),flush=True)
            if result.rowcount == 0:
                break
        iterations[mode] = steps
    connection.execute(f'ANALYZE {SCHEMA}.members')
    return iterations


def main():
    import psycopg
    from psycopg import sql
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('backup', type=Path)
    args = parser.parse_args()
    with args.backup.open('rb') as handle:
        if handle.read(5) != b'PGDMP':
            raise ValueError('Custom PostgreSQL backup required')
    catalog = json.loads(CATALOG.read_text(encoding='utf-8'))
    password = (ROOT / '.runtime/initdb-password').read_text().strip()
    with psycopg.connect(host='127.0.0.1', port=55432, dbname=DATABASE,
                         user='fixture_admin', password=password) as connection:
        if connection.execute('SELECT 1 FROM pg_namespace WHERE nspname=%s', (SCHEMA,)).fetchone():
            raise ValueError('Relations schema exists; nothing overwritten')
        connection.execute(sql.SQL('CREATE SCHEMA {}').format(sql.Identifier(SCHEMA)))
        connection.execute(sql.SQL('REVOKE ALL ON SCHEMA {} FROM PUBLIC,chatbot_reader,chatbot_institutional').format(sql.Identifier(SCHEMA)))
        fresh = {name: spec for name, spec in catalog['tables'].items() if spec.get('source_schema', SCHEMA) == SCHEMA}
        for name, spec in fresh.items():
            columns = dict(spec['columns']) | {c + '_presente': 'boolean' for c in spec['presence']}
            definitions = [sql.SQL('{} {}').format(sql.Identifier(c), sql.SQL(t)) for c,t in columns.items()]
            if 'id' not in columns:
                definitions.append(sql.SQL('__row_id bigint GENERATED ALWAYS AS IDENTITY'))
            connection.execute(sql.SQL('CREATE TABLE {}.{} ({})').format(sql.Identifier(SCHEMA),sql.Identifier(name),sql.SQL(',').join(definitions)))
        upgrade_details.SCHEMA = SCHEMA
        counts = upgrade_details.stream_details(connection, args.backup, {'tables': fresh})
        for name, spec in fresh.items():
            indexes = {'id'} | {c for c in spec['columns'] if c.endswith('_id') or c.startswith('id_') or c.startswith('fk_')}
            for column in sorted(indexes & spec['columns'].keys()):
                connection.execute(sql.SQL('CREATE INDEX ON {}.{} ({})').format(sql.Identifier(SCHEMA), sql.Identifier(name), sql.Identifier(column)))
            connection.execute(sql.SQL('ANALYZE {}.{}').format(sql.Identifier(SCHEMA), sql.Identifier(name)))
        print('Source extraction complete; computing all FK paths.', flush=True)
        iterations = build_graph(connection, catalog)
        connection.execute(f'''CREATE TABLE {SCHEMA}.catalog (
            table_name text PRIMARY KEY, path_info text NOT NULL);
            CREATE TABLE {SCHEMA}.counts (office_id bigint NOT NULL, table_name text NOT NULL,
            total_count bigint NOT NULL, relation_kind text NOT NULL, path_info text NOT NULL,
            descendant_count bigint NOT NULL, lookup_count bigint NOT NULL,
            PRIMARY KEY(office_id,table_name));''')
        for name, spec in catalog['tables'].items():
            path = spec.get('path_info', 'Asociación por claves foráneas; no acredita pertenencia operativa a la sucursal.')
            if not isinstance(path, str):
                path = json.dumps(path, ensure_ascii=False)
            connection.execute(f'INSERT INTO {SCHEMA}.catalog VALUES (%s,%s)', (name,path))
        connection.execute(f'''INSERT INTO {SCHEMA}.counts
            SELECT o.id,c.table_name,count(m.record_key),
            CASE WHEN bool_or(m.relation_kind='descendant') THEN 'descendant' ELSE 'lookup' END,c.path_info,
            count(m.record_key) FILTER (WHERE m.relation_kind='descendant'),
            count(m.record_key) FILTER (WHERE m.relation_kind='lookup')
            FROM chatbot_details_source.sucursales o CROSS JOIN {SCHEMA}.catalog c
            LEFT JOIN {SCHEMA}.members m ON m.office_id=o.id AND m.table_name=c.table_name
            GROUP BY o.id,c.table_name,c.path_info''')
        connection.execute((ROOT/'database/views/004_office_relations.sql').read_text(encoding='utf-8'))
        totals = connection.execute(f'SELECT office_id,sum(total_count)::bigint FROM {SCHEMA}.counts GROUP BY office_id ORDER BY office_id').fetchall()
        max_record = connection.execute(f'SELECT max(octet_length(record::text)) FROM {SCHEMA}.nodes').fetchone()[0]
        node_count = connection.execute(f'SELECT count(*) FROM {SCHEMA}.nodes').fetchone()[0]
        source_counts = dict(connection.execute(f'SELECT table_name,count(*) FROM {SCHEMA}.nodes GROUP BY table_name').fetchall())
        if any(source_counts.get(table,0) != count for table,count in counts.items()):
            raise ValueError('Imported source completeness mismatch')
    report = {'status':'imported','database':DATABASE,'imported_at':datetime.now(timezone.utc).isoformat(),
        'new_rows':counts,'table_count':len(catalog['tables']),'node_count':node_count,
        'all_source_counts':source_counts,
        'office_related_counts':dict(totals),'max_record_bytes':max_record,'iterations':iterations,
        'excluded_tables':catalog.get('excluded_tables',{}),'source_backup_unchanged':True,
        'semantics':'Declared FK descendants (all paths), followed by outgoing FK lookup closure only.'}
    (ROOT/'.runtime/office-relations-import.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps({'status':'imported','table_count':len(catalog['tables']),'node_count':node_count,'max_record_bytes':max_record}),flush=True)


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        raise SystemExit(f'Office relations import failed ({type(error).__name__}); transaction rolled back; no private rows logged.') from None
