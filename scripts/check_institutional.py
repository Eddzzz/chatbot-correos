"""Compare authorized API answers with local imported PostgreSQL; report no row data."""
import json
import time
import urllib.error
import urllib.request

from import_backup import ROOT


def main():
    import psycopg
    runtime = ROOT / '.runtime'
    config = json.load(urllib.request.urlopen('http://127.0.0.1:8000/api/config', timeout=5))
    assert config['data_mode'] == 'postgres' and config.get('data_snapshot'), 'Requiere respaldo real configurado.'
    inputs = json.loads((runtime / 'institutional-check-input.json').read_text())
    token = (runtime / 'operator-token.txt').read_text().strip()
    year, code = inputs['year'], inputs['tracking_code']
    with psycopg.connect((runtime / 'institutional-dsn.txt').read_text().strip()) as connection:
        connection.execute("SELECT set_config('chatbot.access_scope','global_internal',true)")
        expected_count = connection.execute('SELECT count(*) FROM chatbot.v_tracking WHERE registered_at >= %s AND registered_at < %s', (f'{year}-01-01', f'{year+1}-01-01')).fetchone()[0]
        expected_offices = connection.execute('SELECT count(*) FROM chatbot.v_offices').fetchone()[0]
    results, session = [], None
    for name, message, expected in (
        ('tracking', f'Consulta el seguimiento de {code}', 'answer'),
        ('followup', '¿Y su estado?', 'answer'),
        ('offices_case_variants', 'Lista oficinas de La Paz', 'answer'),
        ('offices_all', 'Lista todas las oficinas', 'answer'),
        ('analytics_reference', f'Cuenta registros por estado desde {year}-01-01 hasta {year+1}-01-01', 'answer'),
        ('ambiguous_period', 'Resumen de marzo', 'needs_clarification'),
        ('unsupported_rates', 'Consulta las tarifas postales', 'unsupported'),
    ):
        start = time.perf_counter()
        request = urllib.request.Request('http://127.0.0.1:8000/api/chat',
            data=json.dumps({'message': message, 'session_id': session}).encode(),
            headers={'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json'})
        try:
            with urllib.request.urlopen(request, timeout=100) as response:
                body = json.load(response)
        except urllib.error.HTTPError as error:
            body = json.load(error)
        session = body.get('session_id', session)
        passed = body.get('status') == expected
        rows = body.get('rows', [])
        if name in {'tracking', 'followup'}:
            passed = passed and len(rows) == 1 and rows[0]['tracking_code'] == code
        elif name == 'offices_case_variants':
            passed = passed and len(rows) == 1 and rows[0]['department'] == 'LA PAZ'
        elif name == 'offices_all':
            passed = passed and len(rows) == expected_offices
        elif name == 'analytics_reference':
            passed = passed and sum(row['total'] for row in rows) == expected_count
        if rows:
            passed = passed and 'respaldo local del ' in body.get('source', '') and 'ficticios' not in body.get('answer', '')
            assert all(not any(key in row for key in ('destinatario', 'nombre_r', 'telefono_r', 'direccion', 'carnet', 'imagen')) for row in rows)
        result = {'case': name, 'status': body.get('status', 'unknown'), 'passed': passed,
                  'seconds': round(time.perf_counter() - start, 3)}
        results.append(result)
        print(json.dumps(result), flush=True)
    output = {'snapshot': config['data_snapshot'], 'reference_count': expected_count,
              'reference_offices': expected_offices, 'results': results}
    (runtime / 'institutional-api-validation.json').write_text(json.dumps(output, indent=2), encoding='utf-8')
    if not all(result['passed'] for result in results):
        raise SystemExit(1)


if __name__ == '__main__':
    main()
