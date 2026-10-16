"""Exercise the real CPU model and isolated synthetic PostgreSQL through the API."""
import json
from pathlib import Path
import time
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
BASE = 'http://127.0.0.1:8000'


def main():
    with urllib.request.urlopen(BASE + '/api/config', timeout=5) as response:
        config = json.load(response)
    if config != {'data_mode': 'fixture', 'inference_mode': 'local'}:
        raise SystemExit('Esta prueba exige modo fixture con modelo local; no se ejecuta contra datos institucionales.')
    token = (ROOT / '.runtime/operator-token.txt').read_text().strip()
    session = None
    cases = [
        ('saludo', 'Hola', 'answer'),
        ('seguimiento', 'Seguimiento DEMO-CERTI-001', 'answer'),
        ('continuacion', '¿Y su estado?', 'answer'),
        ('oficinas', 'Lista oficinas de La Paz', 'answer'),
        ('analitica', 'Cuenta registros por estado desde 2026-01-01 hasta 2027-01-01', 'answer'),
        ('ambiguedad', 'Resumen de marzo', 'needs_clarification'),
        ('fuera_de_dominio', 'Dame una receta de pizza', 'out_of_scope'),
        ('tarifas', 'Consulta las tarifas de Correos Bolivia', 'unsupported'),
    ]
    results = []
    for name, message, expected in cases:
        started = time.perf_counter()
        request = urllib.request.Request(BASE + '/api/chat',
            data=json.dumps({'message': message, 'session_id': session}).encode(),
            headers={'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json'})
        try:
            with urllib.request.urlopen(request, timeout=100) as response:
                body = json.load(response)
        except urllib.error.HTTPError as error:
            body = json.load(error)
        session = body.get('session_id', session)
        passed = body.get('status') == expected
        if name in {'seguimiento', 'continuacion'}:
            passed = passed and body.get('rows', [{}])[0].get('tracking_code') == 'DEMO-CERTI-001'
        if name == 'analitica':
            passed = passed and sum(row.get('total', 0) for row in body.get('rows', [])) == 5
        if name in {'seguimiento', 'oficinas', 'analitica'}:
            passed = passed and 'ficticios' in body.get('answer', '')
        result = {'case': name, 'status': body.get('status', 'unknown'), 'passed': passed,
                  'seconds': round(time.perf_counter() - started, 3)}
        results.append(result)
        print(json.dumps(result), flush=True)
    (ROOT / '.runtime/api-real-model-smoke.json').write_text(json.dumps(results, indent=2), encoding='utf-8')
    if not all(result['passed'] for result in results):
        raise SystemExit(1)


if __name__ == '__main__':
    main()
