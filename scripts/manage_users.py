"""Provision browser users without exposing passwords as command arguments."""
import argparse
import getpass
import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'backend'))

from app.identity.public import BrowserAuth, PERMISSIONS, password_hash
from app.settings import Settings


def main():
    parser = argparse.ArgumentParser(description='Administrar usuarios del chat local.')
    parser.add_argument('--auth-path', help='Ruta de la base SQLite de autenticación.')
    commands = parser.add_subparsers(dest='command', required=True)
    create = commands.add_parser('create')
    create.add_argument('username')
    create.add_argument('--user-id', help='Identificador estable; usar el anterior al migrar un usuario.')
    create.add_argument('--display-name')
    create.add_argument('--permissions', nargs='+', choices=sorted(PERMISSIONS), default=['internal_data', 'tracking', 'offices', 'summary'])
    create.add_argument('--scope', nargs='*', choices=['global_internal'], default=['global_internal'])
    create.add_argument('--password-file', type=Path)
    commands.add_parser('list')
    reset = commands.add_parser('reset-password')
    reset.add_argument('username')
    reset.add_argument('--password-file', type=Path)
    args = parser.parse_args()
    settings = Settings()
    if args.auth_path:
        settings.auth_path = args.auth_path
    auth = BrowserAuth(settings)
    try:
        if args.command == 'list':
            for user in auth.store.users():
                print(json.dumps(user, ensure_ascii=False))
            return
        if args.password_file:
            password = args.password_file.read_text(encoding='utf-8').rstrip('\r\n')
        else:
            password = getpass.getpass('Contraseña: ')
            if password != getpass.getpass('Repetir contraseña: '):
                raise ValueError('Las contraseñas no coinciden.')
        if args.command == 'create':
            auth.create_user(args.username, password, user_id=args.user_id,
                             display_name=args.display_name, permissions=args.permissions, scope=args.scope)
            print('Usuario creado: ' + args.username.strip().lower())
        else:
            auth.store.reset_password(args.username.strip().lower(), password_hash(password))
            print('Contraseña actualizada; sesiones anteriores revocadas.')
    except (ValueError, sqlite3.IntegrityError, OSError) as exc:
        parser.exit(1, 'No se pudo completar la operación: ' + ('El usuario o identificador ya existe.' if isinstance(exc, sqlite3.IntegrityError) else str(exc)) + '\n')


if __name__ == '__main__':
    main()
