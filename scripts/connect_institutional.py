"""Verify imported real read model and prepare private API configuration."""
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import subprocess

from import_backup import DATABASE, ROLE, ROOT, TABLES
from inspect_backup import find_pg_restore


def main():
    import psycopg
    from psycopg import sql
    runtime = ROOT / '.runtime'
    report = json.loads((runtime / 'institutional-import.json').read_text())
    if report['status'] != 'imported' or report['database'] != DATABASE:
        raise SystemExit('La importación no está completa.')
    admin_options = dict(host='127.0.0.1', port=55432, user='fixture_admin',
                         password=(runtime / 'initdb-password').read_text().strip(), dbname=DATABASE)
    with psycopg.connect(**admin_options) as admin:
        # Login settings are not inherited from a group role at session startup.
        admin.execute(sql.SQL("ALTER ROLE {} SET lock_timeout='1s'").format(sql.Identifier(ROLE)))
        admin.execute(sql.SQL("ALTER ROLE {} SET idle_in_transaction_session_timeout='10s'").format(sql.Identifier(ROLE)))
        admin_counts = {name: admin.execute(sql.SQL('SELECT count(*) FROM public.{}').format(sql.Identifier(name))).fetchone()[0] for name in TABLES}
        if admin_counts != report['rows']:
            raise RuntimeError('Los conteos almacenados no coinciden con la importación.')
        for table, columns in TABLES.items():
            actual = admin.execute('SELECT column_name FROM information_schema.columns WHERE table_schema=%s AND table_name=%s ORDER BY ordinal_position', ('public', table)).fetchall()
            assert [row[0] for row in actual] == list(columns), 'Columnas fuera del catálogo.'
    dsn = (runtime / 'institutional-dsn.txt').read_text().strip()
    with psycopg.connect(dsn) as reader:
        reader.execute('SET TRANSACTION READ ONLY')
        assert reader.execute('SELECT count(*) FROM chatbot.v_tracking').fetchone()[0] == 0
        reader.execute("SELECT set_config('chatbot.access_scope','global_internal',true)")
        tracking = reader.execute('SELECT source,count(*) FROM chatbot.v_tracking GROUP BY source').fetchall()
        counts = dict(tracking)
        assert counts == {key.removeprefix('paquetes_'): value for key, value in admin_counts.items() if key.startswith('paquetes_')}
        assert reader.execute('SELECT count(*) FROM chatbot.v_offices').fetchone()[0] == admin_counts['sucursales']
        missing, no_date, duplicates = reader.execute('SELECT count(*) FILTER (WHERE status IS NULL), count(*) FILTER (WHERE registered_at IS NULL), count(*)-count(DISTINCT tracking_code) FROM chatbot.v_tracking').fetchone()
        reference = reader.execute("SELECT tracking_code FROM chatbot.v_tracking WHERE tracking_code ~ '^[A-Z0-9-]{5,40}$' GROUP BY tracking_code HAVING count(*)=1 ORDER BY tracking_code LIMIT 1").fetchone()
        assert reference, 'Se requiere al menos un código consultable.'
        year = reader.execute('SELECT extract(year from max(registered_at))::int FROM chatbot.v_tracking').fetchone()[0]
        roles = reader.execute('SELECT rolsuper,rolbypassrls,rolcreatedb,rolcreaterole FROM pg_roles WHERE rolname=current_user').fetchone()
        assert not any(roles), 'Rol privilegiado.'
        reader.commit()
        assert reader.execute('SELECT count(*) FROM chatbot.v_tracking').fetchone()[0] == 0
        reader.rollback()
        try:
            reader.execute('SELECT * FROM public.paquetes_certi LIMIT 1')
        except psycopg.errors.InsufficientPrivilege:
            reader.rollback()
        else:
            raise RuntimeError('La cuenta tiene acceso a tablas originales.')
        try:
            reader.execute("INSERT INTO public.estados(id,nombre_estado) VALUES (-1,'forbidden')")
        except (psycopg.errors.InsufficientPrivilege, psycopg.errors.ReadOnlySqlTransaction):
            reader.rollback()
        else:
            reader.rollback()
            raise RuntimeError('La cuenta permite escritura.')
    listing = subprocess.check_output([find_pg_restore(), '--list', report['source']], text=True, encoding='utf-8')
    match = re.search(r'^; Archive created at (.+)$', listing, re.M)
    snapshot = match[1].strip() if match else 'fecha no disponible'
    environment = json.loads((runtime / 'local-env.json').read_text())
    environment.update({'CHATBOT_DATABASE_URL': dsn, 'CHATBOT_DEMO_MODE': 'false',
                        'CHATBOT_FIXTURE_DATA': 'false', 'CHATBOT_DATA_SNAPSHOT': snapshot})
    (runtime / 'institutional-env.json').write_text(json.dumps(environment), encoding='utf-8')
    # Functional reference remains private; stdout/report contain only aggregate counts.
    (runtime / 'institutional-check-input.json').write_text(json.dumps({'tracking_code': reference[0], 'year': year}), encoding='utf-8')
    validation = {'verified_at': datetime.now(timezone.utc).isoformat(), 'snapshot': snapshot,
                  'tracking_records': sum(counts.values()), 'records_by_family': counts,
                  'offices': admin_counts['sucursales'], 'missing_status': missing,
                  'missing_registration_date': no_date, 'duplicate_or_null_tracking_codes': duplicates,
                  'scope_cleanup': True, 'raw_table_denied': True, 'write_denied': True,
                  'personal_columns_retained': False}
    (runtime / 'institutional-validation.json').write_text(json.dumps(validation, indent=2), encoding='utf-8')
    print(json.dumps(validation, ensure_ascii=False, indent=2))
    print('Configuración lista; reiniciar scripts/start_backend.ps1 sin -Fixture.')


if __name__ == '__main__':
    main()
