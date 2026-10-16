import json
from pathlib import Path
import unittest

from upgrade_details import copy_header


class DetailsCatalogTest(unittest.TestCase):
    def test_catalog_excludes_authentication_and_binary_content(self):
        catalog = json.loads((Path(__file__).resolve().parents[1] / 'config/details_catalog.json').read_text())
        forbidden = {'password', 'remember_token', 'api_token', 'imagen', 'mapa', 'foto'}
        for table, spec in catalog['tables'].items():
            self.assertFalse(forbidden.intersection(spec['columns']), table)
            self.assertFalse(set(spec['presence']).intersection(spec['columns']), table)
            self.assertIn('id', spec['columns'], table)

    def test_copy_header_only_selects_catalogued_tables(self):
        with self.assertRaises(ValueError):
            copy_header('COPY public.sessions (id, payload) FROM stdin;', {'users': {}})
        table, columns = copy_header('COPY public.users (id, name, password) FROM stdin;', {'users': {}})
        self.assertEqual((table, columns), ('users', ['id', 'name', 'password']))


if __name__ == '__main__':
    unittest.main()
