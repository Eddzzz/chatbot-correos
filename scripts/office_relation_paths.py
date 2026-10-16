"""Add human-readable example FK paths to the offline office relation catalog."""
from collections import deque
import json

from import_backup import DATABASE, ROOT


def describe_paths(catalog):
    edges = catalog['foreign_keys']
    paths = {'sucursales': 'sucursales (registro solicitado)'}
    pending = deque(['sucursales'])
    # These are example paths for display, never membership or authorization rules.
    while pending:
        parent = pending.popleft()
        for edge in edges:
            child = edge['child']
            if edge['parent'] == parent and child not in paths:
                paths[child] = paths[parent] + ' ← ' + child + '.' + ','.join(edge['child_columns'])
                pending.append(child)
    pending.extend(paths)
    while pending:
        child = pending.popleft()
        for edge in edges:
            parent = edge['parent']
            if edge['child'] == child and parent not in paths:
                paths[parent] = paths[child] + ' → ' + parent + '.' + ','.join(edge['parent_columns'])
                pending.append(parent)
    return {name: paths.get(name, 'Sin ruta declarada desde sucursales') + '. Ruta de ejemplo; la consulta reúne todos los caminos FK válidos.' for name in catalog['tables']}


def main():
    import psycopg
    path = ROOT / 'config/office_relations_catalog.json'
    catalog = json.loads(path.read_text(encoding='utf-8'))
    descriptions = describe_paths(catalog)
    with psycopg.connect(host='127.0.0.1', port=55432, dbname=DATABASE, user='fixture_admin',
                         password=(ROOT / '.runtime/initdb-password').read_text().strip()) as connection:
        for table, description in descriptions.items():
            connection.execute('UPDATE chatbot_relations_source.catalog SET path_info=%s WHERE table_name=%s', (description, table))
            connection.execute('UPDATE chatbot_relations_source.counts SET path_info=%s WHERE table_name=%s', (description, table))
            catalog['tables'][table]['path_info'] = description
    path.write_text(json.dumps(catalog, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'Rutas de ejemplo actualizadas para {len(descriptions)} tablas; no se modificó la pertenencia de registros.')


if __name__ == '__main__':
    main()
