import unittest

from import_backup import TABLES, project_copy_row, parse_copy_header


class ProjectionTest(unittest.TestCase):
    def test_copy_projection_preserves_postgres_escaping_without_personal_columns(self):
        row = b'7\tCP123\tNombre privado\tLa\\tPaz\t\\N\n'
        self.assertEqual(project_copy_row(row, [0, 1, 3, 4], 5), b'7\tCP123\tLa\\tPaz\t\\N\n')

    def test_invalid_copy_shape_fails_closed(self):
        with self.assertRaises(ValueError):
            project_copy_row(b'1\t2\n', [0], 3)
        with self.assertRaises(ValueError):
            parse_copy_header('COPY public.users (id, password) FROM stdin;')

    def test_only_expected_plain_copy_headers_are_accepted(self):
        table, columns = parse_copy_header('COPY public.sucursales (id, "codigoSucursal", municipio) FROM stdin;')
        self.assertEqual((table, columns), ('sucursales', ['id', 'codigoSucursal', 'municipio']))
        personal = {'destinatario', 'nombre_r', 'nombre_d', 'telefono_r', 'telefono_d',
                    'direccion', 'direccion_r', 'direccion_d', 'imagen', 'carnet', 'contenido', 'password'}
        self.assertTrue(all(not personal.intersection(columns) for columns in TABLES.values()))


if __name__ == '__main__':
    unittest.main()
