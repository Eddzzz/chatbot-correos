"""Local accounting-view integration proof; synthetic records always rolled back."""
import unittest
import uuid

from import_backup import DATABASE, ROOT


@unittest.skipUnless((ROOT / '.runtime/initdb-password').exists(),
                     'Requires project-owned local PostgreSQL fixture')
class AccountingViewTest(unittest.TestCase):
    def test_categories_month_bounds_scope_guards_and_private_sources(self):
        import psycopg
        from psycopg import sql

        password = (ROOT / '.runtime/initdb-password').read_text().strip()
        connection = psycopg.connect(host='127.0.0.1', port=55432, dbname=DATABASE,
                                      user='fixture_admin', password=password)
        sources = [
            ('chatbot_relations_source', 'cashier_flow_receivable_movements', 'cobrado_at'),
            ('chatbot_relations_source', 'cashier_flow_receivable_collections', 'cobrado_at'),
            ('chatbot_accounting_source', 'facturas', 'created_at'),
        ]
        try:
            connection.execute('SAVEPOINT accounting_test')
            # Random negative bigint identifiers cannot collide silently: check all
            # three copied sources before inserting, and never delete source rows.
            first_id = -(uuid.uuid4().int % (2**61) + 10)
            identifiers = [first_id, first_id - 1, first_id - 2]
            for schema, table, column in sources:
                source = sql.Identifier(schema, table)
                collision = connection.execute(sql.SQL(
                    'SELECT count(*) FROM {} WHERE id=ANY(%s)').format(source),
                    (identifiers,)).fetchone()[0]
                self.assertEqual(collision, 0, 'Synthetic identifier collision; no rows replaced')
                connection.execute(sql.SQL('''INSERT INTO {} (id,{}) VALUES
                    (%s,'2026-10-01 00:00:00'),
                    (%s,'2026-10-31 23:59:59'),
                    (%s,'2026-11-01 00:00:00')''').format(
                        source, sql.Identifier(column)), identifiers)

            exact_amount = '99999999999999.99'
            connection.execute('''UPDATE chatbot_relations_source.cashier_flow_receivable_movements
                SET monto=%s,cantidad_paquetes=%s WHERE id=ANY(%s)''',
                (exact_amount, exact_amount, identifiers))
            connection.execute('''UPDATE chatbot_relations_source.cashier_flow_receivable_collections
                SET monto_cobrado=%s WHERE id=ANY(%s)''', (exact_amount, identifiers))

            connection.execute('SET LOCAL ROLE chatbot_institutional')
            for role in ('chatbot_institutional', 'chatbot_reader'):
                for schema in ('chatbot_accounting_source', 'chatbot_relations_source'):
                    accessible = connection.execute(
                        "SELECT has_schema_privilege(%s,%s,'USAGE')", (role, schema)).fetchone()[0]
                    self.assertFalse(accessible)

            # Explicitly reset both GUCs so a session default cannot affect proof.
            for scope, personal, expected in [
                ('', '', 0), ('global_internal', '', 0),
                ('', 'allowed', 0), ('regional', 'allowed', 0),
                ('global_internal', 'denied', 0),
                ('global_internal', 'allowed', 9),
            ]:
                connection.execute("SELECT set_config('chatbot.access_scope',%s,true)", (scope,))
                connection.execute("SELECT set_config('chatbot.personal_access',%s,true)", (personal,))
                count = connection.execute('''SELECT count(*) FROM chatbot.v_accounting_records
                    WHERE record_id=ANY(%s)''', (identifiers,)).fetchone()[0]
                self.assertEqual(count, expected, 'Accounting authorization guard mismatch')

            records = connection.execute('''SELECT category,record FROM chatbot.v_accounting_records
                WHERE record_id=%s''', (first_id,)).fetchall()
            for category, record in records:
                if category == 'movimientos':
                    self.assertEqual(record['campos']['monto'], exact_amount)
                    self.assertEqual(record['campos']['cantidad_paquetes'], exact_amount)
                elif category == 'cobros':
                    self.assertEqual(record['campos']['monto_cobrado'], exact_amount)

            rows = connection.execute('''SELECT category,count(*)
                FROM chatbot.v_accounting_records WHERE record_id=ANY(%s)
                  AND occurred_at >= '2026-10-01' AND occurred_at < '2026-11-01'
                GROUP BY category ORDER BY category''', (identifiers,)).fetchall()
            self.assertEqual(dict(rows), {'cobros': 2, 'facturacion': 2, 'movimientos': 2})
            rows = connection.execute('''SELECT category,count(*)
                FROM chatbot.v_accounting_records WHERE record_id=ANY(%s)
                  AND occurred_at >= '2026-11-01' AND occurred_at < '2026-12-01'
                GROUP BY category ORDER BY category''', (identifiers,)).fetchall()
            self.assertEqual(dict(rows), {'cobros': 1, 'facturacion': 1, 'movimientos': 1})

            connection.execute('ROLLBACK TO SAVEPOINT accounting_test')
            for schema, table, column in sources:
                count = connection.execute(sql.SQL('SELECT count(*) FROM {} WHERE id=ANY(%s)')
                    .format(sql.Identifier(schema, table)), (identifiers,)).fetchone()[0]
                self.assertEqual(count, 0, 'Synthetic test rows survived savepoint rollback')
        finally:
            # Never commit, including when an assertion or source query fails.
            connection.rollback()
            connection.close()


if __name__ == '__main__':
    unittest.main()
