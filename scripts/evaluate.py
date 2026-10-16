"""Evaluate routing and latency; never persist messages or returned operational data."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
import math
import os
from pathlib import Path
import statistics
import time
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[1]


def percentile(values, fraction):
    ordered = sorted(values)
    return ordered[max(0, min(len(ordered) - 1, math.ceil(len(ordered) * fraction) - 1))]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url', default='http://127.0.0.1:8000')
    parser.add_argument('--cases', type=Path, default=ROOT / 'evaluation/questions.json')
    parser.add_argument('--limit', type=int, default=10)
    parser.add_argument('--concurrency', type=int, choices=[1, 2, 5], default=1)
    parser.add_argument('--output', type=Path, default=ROOT / '.runtime/evaluation.json')
    args = parser.parse_args()
    token = os.environ.get('CHATBOT_EVALUATION_TOKEN')
    if not token:
        raise SystemExit('Configura CHATBOT_EVALUATION_TOKEN desde una sesión autorizada.')
    corpus = json.loads(args.cases.read_text(encoding='utf-8'))
    cases = [case for case in corpus['cases'] if case.get('automated', False)][:args.limit]
    if not cases:
        raise SystemExit('No hay casos automatizables seleccionados.')

    def run(case):
        start = time.perf_counter()
        request = urllib.request.Request(args.url.rstrip('/') + '/api/chat',
            data=json.dumps({'message': case['message']}).encode(),
            headers={'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json'})
        try:
            with urllib.request.urlopen(request, timeout=90) as response:
                status = json.load(response)['status']
        except urllib.error.HTTPError as error:
            status = f'http_{error.code}'
        except (OSError, TimeoutError):
            status = 'transport_error'
        return {'id': case['id'], 'status': status,
                'passed': status in case['expected_status'],
                'seconds': round(time.perf_counter() - start, 3)}

    with ThreadPoolExecutor(max_workers=args.concurrency) as executor:
        results = list(executor.map(run, cases))
    durations = [result['seconds'] for result in results]
    report = {'corpus_business_reviewed': corpus['business_reviewed'],
        'concurrency': args.concurrency, 'total': len(results),
        'passed': sum(result['passed'] for result in results),
        'p50_seconds': round(statistics.median(durations), 3),
        'p95_seconds': percentile(durations, .95), 'results': results}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps({key: value for key, value in report.items() if key != 'results'}, indent=2))
    if not all(result['passed'] for result in results):
        raise SystemExit(1)


if __name__ == '__main__':
    main()
