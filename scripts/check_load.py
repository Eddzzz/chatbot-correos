"""Small fixture-only load smoke test, not a capacity or latency acceptance benchmark."""
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import statistics
import time
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
BASE = 'http://127.0.0.1:8000'


def main():
    with urllib.request.urlopen(BASE + '/api/config', timeout=5) as response:
        config = json.load(response)
    if config.get('data_mode') != 'fixture' or config.get('inference_mode') != 'local':
        raise SystemExit('Solo se permite fixture sintético con inferencia local.')
    token = (ROOT / '.runtime/operator-token.txt').read_text().strip()

    def query(_):
        started = time.perf_counter()
        request = urllib.request.Request(BASE + '/api/chat',
            data=json.dumps({'message': 'Seguimiento DEMO-CERTI-001'}).encode(),
            headers={'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json'})
        try:
            with urllib.request.urlopen(request, timeout=100) as response:
                body = json.load(response)
                valid = body.get('status') == 'answer' and body.get('rows', [{}])[0].get('tracking_code') == 'DEMO-CERTI-001'
                state = 'answer' if valid else 'invalid_answer'
        except urllib.error.HTTPError as error:
            body = json.load(error)
            state = body.get('error', {}).get('code', f'http_{error.code}')
        return {'outcome': state, 'seconds': round(time.perf_counter() - started, 3)}

    report = []
    for concurrency in (1, 2, 5):
        with ThreadPoolExecutor(max_workers=concurrency) as executor:
            results = list(executor.map(query, range(concurrency)))
        row = {'concurrency': concurrency, 'samples': len(results),
               'p50_seconds': statistics.median(result['seconds'] for result in results),
               'p95_seconds': max(result['seconds'] for result in results),
               'results': results}
        report.append(row)
        print(json.dumps(row), flush=True)
    (ROOT / '.runtime/load-smoke.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    if any(result['outcome'] not in {'answer', 'queue_full', 'queue_timeout'} for row in report for result in row['results']):
        raise SystemExit(1)


if __name__ == '__main__':
    main()
