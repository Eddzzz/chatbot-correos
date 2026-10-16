"""Create ignored local configuration for synthetic PostgreSQL + real CPU inference."""
import json
from pathlib import Path
import secrets

ROOT = Path(__file__).resolve().parents[1]


def main():
    runtime = ROOT / '.runtime'
    dsn_path = runtime / 'fixture-dsn.txt'
    if not dsn_path.exists():
        raise SystemExit('Ejecuta scripts/init_fixture.ps1 primero.')
    token_path = runtime / 'operator-token.txt'
    if not token_path.exists():
        token_path.write_text(secrets.token_urlsafe(32), encoding='utf-8')
    identities = {token_path.read_text().strip(): {'user_id': 'operador-local',
        'permissions': ['internal_data', 'tracking', 'offices', 'summary', 'diagnostics'],
        'scope': ['global_internal']}}
    environment = {'CHATBOT_IDENTITIES_JSON': json.dumps(identities),
        'CHATBOT_DATABASE_URL': dsn_path.read_text().strip(),
        'CHATBOT_LLAMA_URL': 'http://127.0.0.1:8081/v1',
        'CHATBOT_LLAMA_MODEL': 'local', 'CHATBOT_DEMO_MODE': 'false',
        'CHATBOT_FIXTURE_DATA': 'true',
        'CHATBOT_MODEL_VERSION': 'sha256:' + json.loads((ROOT / 'config/model-manifest.json').read_text())['model']['sha256']}
    (runtime / 'local-env.json').write_text(json.dumps(environment), encoding='utf-8')
    print('Configuración ficticia creada en .runtime/local-env.json. Credencial en .runtime/operator-token.txt; no compartir.')


if __name__ == '__main__':
    main()
