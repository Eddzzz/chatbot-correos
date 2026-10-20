"""Integration proof of all-path membership; synthetic rows only, rolled back."""
import unittest
import uuid
import json
import re

from import_backup import ROOT
import upgrade_office_relations as upgrade


class CatalogTest(unittest.TestCase):
    def test_fk_graph_is_complete_and_security_fields_are_not_imported(self):
        catalog = json.loads(upgrade.CATALOG.read_text(encoding='utf-8'))
        tables = catalog['tables']
        for table,spec in tables.items():
            self.assertFalse(re.search(r'password|token|secret|credential|session_reference|device_id|device_name',
                                       ' '.join(spec['columns']), re.I), table)
        for fk in catalog['foreign_keys']:
            self.assertLessEqual(set(fk['child_columns']), set(tables[fk['child']]['columns']))
            self.assertLessEqual(set(fk['parent_columns']), set(tables[fk['parent']]['columns']))
        # The source has misleading legacy constraint names; table ownership comes from ALTER TABLE.
        self.assertTrue(any(fk['child']=='paquetes_contrato' and fk['parent']=='users'
                            for fk in catalog['foreign_keys']))
        self.assertNotIn('external_api_tokens', tables)
        self.assertNotIn('user_login_logs', tables)
        self.assertIn('eventos_auditoria', tables)
        self.assertIn('roles', tables)


class ClosureTest(unittest.TestCase):
    @unittest.skipUnless((ROOT/'.runtime/initdb-password').exists(), 'Requires project-owned local PostgreSQL fixture')
    def test_all_fk_paths_and_lookup_without_reverse_expansion(self):
        import psycopg
        schema = 'test_relations_' + uuid.uuid4().hex
        password = (ROOT/'.runtime/initdb-password').read_text().strip()
        original = upgrade.SCHEMA
        try:
            upgrade.SCHEMA = schema
            with psycopg.connect(host='127.0.0.1',port=55432,dbname='correos_sandbox_fixture',
                                 user='fixture_admin',password=password) as connection:
                connection.execute(f'''CREATE SCHEMA {schema};
                    CREATE TABLE {schema}.sucursales(id bigint);
                    CREATE TABLE {schema}.users(id bigint,sucursal_id bigint,state_id bigint);
                    CREATE TABLE {schema}.moves(id bigint,created_by bigint,updated_by bigint);
                    CREATE TABLE {schema}.states(id bigint);
                    INSERT INTO {schema}.sucursales VALUES (1),(2);
                    INSERT INTO {schema}.states VALUES (9);
                    INSERT INTO {schema}.users VALUES (10,1,9),(20,2,9),(30,2,9);
                    INSERT INTO {schema}.moves VALUES (100,10,20),(101,20,10);''')
                columns = {'sucursales':['id'],'users':['id','sucursal_id','state_id'],
                           'moves':['id','created_by','updated_by'],'states':['id']}
                tables = {name:{'columns':{c:'bigint' for c in cols},'presence':[],
                                'excluded':[],'source_schema':schema} for name,cols in columns.items()}
                foreign_keys = [{'child':c,'parent':p,'child_columns':[cc],'parent_columns':['id']}
                                for c,p,cc in [('users','sucursales','sucursal_id'),
                                ('users','states','state_id'),('moves','users','created_by'),
                                ('moves','users','updated_by')]]
                upgrade.build_graph(connection, {'tables':tables,'foreign_keys':foreign_keys})
                rows = connection.execute(f'SELECT office_id,table_name,record_key,relation_kind FROM {schema}.members').fetchall()
                office1 = {(table,key):kind for office,table,key,kind in rows if office==1}
                self.assertEqual(office1[('moves','100')], 'descendant')
                self.assertEqual(office1[('moves','101')], 'descendant')
                self.assertEqual(office1[('users','20')], 'lookup')
                self.assertEqual(office1[('states','9')], 'lookup')
                # Outgoing lookups can reach another office, but never reverse-expand its unrelated rows.
                self.assertEqual(office1[('sucursales','2')], 'lookup')
                self.assertNotIn(('users','30'), office1)
                connection.rollback()
        finally:
            upgrade.SCHEMA = original


if __name__ == '__main__':
    unittest.main()
