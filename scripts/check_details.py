"""Exercise full-details conversations without printing personal fields or responses."""
import json
from pathlib import Path
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[1]


def main():
    runtime = ROOT / '.runtime'
    token = (runtime / 'operator-token.txt').read_text().strip()
    session = None
    results = []
    code = json.loads((runtime / 'institutional-check-input.json').read_text())['tracking_code']
    for name, message, expected in (
        ('unspecified_latest', 'dame el ultimo dato guardado', 'needs_clarification'),
        ('office_summary', 'dame los atos e la sucursal e la paz', 'answer'),
        ('office_complete_typo_followup', 'dame compelto lo datos completos', 'answer'),
        ('office_complete_followup', 'muestrame todos sus datos asociados', 'answer'),
        ('shipment_summary', f'Consulta el seguimiento de {code}', 'answer'),
        ('shipment_complete_followup', 'dame los datos completos', 'answer'),
    ):
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
        if 'complete' in name:
            passed = passed and bool(rows) and all('details' in row for row in rows)
            if name.startswith('office') and rows:
                detail = rows[0]['details']
                passed = passed and len(detail['campos']) == 8 and 'usuarios' in detail['relaciones']
            if rows:
                history = urllib.request.Request(f'http://127.0.0.1:8000/api/sessions/{session}', headers={'Authorization': 'Bearer ' + token})
                with urllib.request.urlopen(history, timeout=5) as response:
                    stored = json.load(response)
                last_answer = stored['messages'][-1]
                passed = passed and last_answer.get('rows') == rows and last_answer['content'] == body['answer']
        result = {'case': name, 'status': body.get('status', 'unknown'), 'passed': bool(passed)}
        results.append(result)
        print(json.dumps(result), flush=True)
    (runtime / 'details-api-validation.json').write_text(json.dumps(results, indent=2), encoding='utf-8')
    if not all(result['passed'] for result in results):
        raise SystemExit(1)


if __name__ == '__main__':
    main()
