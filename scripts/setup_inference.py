"""Download pinned CPU runtime and text model; verify SHA-256 before use."""
import argparse
import hashlib
import json
from pathlib import Path
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    with path.open('rb') as source:
        return hashlib.file_digest(source, 'sha256').hexdigest()


def download(url, target, expected):
    if target.exists() and digest(target) == expected:
        print(f'Verificado: {target.name}', flush=True)
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    partial = target.with_suffix(target.suffix + '.partial')
    print(f'Descargando: {target.name}', flush=True)
    request = urllib.request.Request(url, headers={'User-Agent': 'correos-chatbot-local/0.1'})
    with urllib.request.urlopen(request, timeout=90) as source, partial.open('wb') as output:
        while chunk := source.read(1024 * 1024):
            output.write(chunk)
    if digest(partial) != expected:
        raise RuntimeError(f'SHA-256 incorrecto: {target.name}; no se utilizará')
    partial.replace(target)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime-only', action='store_true')
    args = parser.parse_args()
    manifest = json.loads((ROOT / 'config/model-manifest.json').read_text())
    runtime = manifest['runtime']
    archive = ROOT / '.runtime/downloads' / runtime['filename']
    download(runtime['url'], archive, runtime['sha256'])
    destination = ROOT / '.runtime/llama-cpu'
    destination.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive) as package:
        for entry in package.infolist():
            path = (destination / entry.filename).resolve()
            if not path.is_relative_to(destination.resolve()):
                raise RuntimeError('Ruta inválida en paquete del runtime')
        package.extractall(destination)
    if not args.runtime_only:
        model = manifest['model']
        url = f"https://huggingface.co/{model['repository']}/resolve/{model['revision']}/{model['filename']}"
        download(url, ROOT / 'models' / model['filename'], model['sha256'])
        license_path = ROOT / 'models/LICENSE-model.txt'
        with urllib.request.urlopen(model['license_url'].replace('/blob/', '/resolve/'), timeout=30) as source:
            license_path.write_bytes(source.read())
    print('Runtime CPU listo. Ejecutar scripts/start_inference.ps1.', flush=True)


if __name__ == '__main__':
    main()
