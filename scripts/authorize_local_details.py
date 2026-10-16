"""Grant/revoke full personal-detail access for the explicitly authorized local operator."""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--revoke', action='store_true')
    args = parser.parse_args()
    runtime = ROOT / '.runtime'
    if not args.revoke:
        report = json.loads((runtime / 'details-import.json').read_text())
        if report.get('status') != 'imported':
            raise SystemExit('Primero completar la importación de fichas autorizadas.')
    path = runtime / 'institutional-env.json'
    environment = json.loads(path.read_text())
    token = (runtime / 'operator-token.txt').read_text().strip()
    identities = json.loads(environment['CHATBOT_IDENTITIES_JSON'])
    operator = identities[token]
    if operator['user_id'] != 'operador-local' or operator['scope'] != ['global_internal']:
        raise SystemExit('Este comando solo modifica al operador local del proyecto.')
    permissions = set(operator['permissions'])
    if args.revoke:
        permissions.discard('personal_data')
    else:
        permissions.add('personal_data')
    operator['permissions'] = sorted(permissions)
    environment['CHATBOT_IDENTITIES_JSON'] = json.dumps(identities)
    path.write_text(json.dumps(environment), encoding='utf-8')
    print('Permiso personal_data ' + ('revocado' if args.revoke else 'habilitado') + ' para operador-local. Reiniciar API para aplicar.')


if __name__ == '__main__':
    main()
