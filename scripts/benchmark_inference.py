"""Measure CPU server generation; compare candidates with identical options."""
import argparse
import json
from pathlib import Path
import statistics
import time
import urllib.request


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url', default='http://127.0.0.1:8081/v1/chat/completions')
    parser.add_argument('--runs', type=int, default=3)
    parser.add_argument('--output', type=Path, default=Path('.runtime/inference-benchmark.json'))
    args = parser.parse_args()
    if not 1 <= args.runs <= 20:
        raise SystemExit('runs debe estar entre 1 y 20')
    results = []
    for index in range(args.runs):
        payload = {'model': 'local', 'temperature': 0, 'max_tokens': 128,
            'chat_template_kwargs': {'enable_thinking': False},
            'messages': [{'role': 'system', 'content': 'Responde brevemente en español.'},
                         {'role': 'user', 'content': 'Explica cómo pedir el código de seguimiento para consultar un envío postal. No inventes estados ni datos.'}]}
        request = urllib.request.Request(args.url, data=json.dumps(payload).encode(),
            headers={'Content-Type': 'application/json'})
        started = time.perf_counter()
        with urllib.request.urlopen(request, timeout=180) as response:
            result = json.load(response)
        duration = time.perf_counter() - started
        tokens = result.get('usage', {}).get('completion_tokens', 0)
        timings = result.get('timings', {})
        results.append({'run': index + 1, 'seconds': round(duration, 3), 'tokens': tokens,
            'end_to_end_tokens_per_second': round(tokens / duration, 3),
            'generation_tokens_per_second': timings.get('predicted_per_second')})
    output = {'note': 'Primera ejecución incluye calentamiento; no mide exactitud de negocio.',
        'model_manifest': 'config/model-manifest.json', 'runs': results,
        'p50_seconds': statistics.median(row['seconds'] for row in results)}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2), encoding='utf-8')
    print(json.dumps(output, indent=2))


if __name__ == '__main__':
    main()
