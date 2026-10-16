import unittest

from office_relation_paths import describe_paths


class PathsTest(unittest.TestCase):
    def test_paths_include_indirect_children_and_terminal_reference(self):
        tables = {name: {} for name in ['sucursales', 'users', 'paquetes_ems', 'estados']}
        edges = [{'child': child, 'child_columns': [column], 'parent': parent, 'parent_columns': ['id']}
                 for child, column, parent in [('users', 'sucursal_id', 'sucursales'),
                     ('paquetes_ems', 'user_id', 'users'), ('paquetes_ems', 'estado_id', 'estados')]]
        paths = describe_paths({'tables': tables, 'foreign_keys': edges})
        self.assertIn('users.sucursal_id', paths['paquetes_ems'])
        self.assertIn('paquetes_ems.user_id', paths['paquetes_ems'])
        self.assertIn('→ estados.id', paths['estados'])
        self.assertTrue(all('todos los caminos' in text for text in paths.values()))


if __name__ == '__main__':
    unittest.main()
