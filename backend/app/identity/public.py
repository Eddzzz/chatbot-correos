import json
import secrets
import hashlib
import re
import time
from pathlib import Path
from uuid import uuid4
from app.contracts import AccessContext, ServiceError
from app.data_access.public import AuthStore


COOKIE_NAME = 'chatbot_session'
PERMISSIONS = frozenset({'internal_data', 'tracking', 'offices', 'summary', 'diagnostics', 'personal_data', 'accounting', 'rates'})


def auth_path(settings):
    if settings.auth_path:
        return settings.auth_path
    if settings.history_path:
        history = Path(settings.history_path)
        return str(history.with_name(history.stem + '-auth.sqlite3'))
    filename = 'auth-fixture.sqlite3' if settings.fixture_data or settings.demo_mode else 'auth.sqlite3'
    return str(Path(__file__).resolve().parents[3] / '.runtime' / filename)


def password_hash(password, salt=None):
    if not 12 <= len(password) <= 1024:
        raise ValueError('La contraseña debe tener entre 12 y 1024 caracteres.')
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode('utf-8'), salt=salt, n=32768, r=8, p=1, maxmem=67108864)
    return 'scrypt$' + salt.hex() + '$' + digest.hex()


def token_hash(token):
    return hashlib.sha256(token.encode('utf-8')).hexdigest()


class BrowserAuth:
    def __init__(self, settings):
        self.settings = settings
        self.store = AuthStore(auth_path(settings))
        self.dummy_hash = password_hash(secrets.token_urlsafe(32))

    def create_user(self, username, password, *, user_id=None, display_name=None, permissions=(), scope=()):
        username = username.strip().lower()
        if not re.fullmatch(r'[a-z0-9][a-z0-9_.-]{2,63}', username):
            raise ValueError('El usuario debe tener entre 3 y 64 letras, números, puntos, guiones o guiones bajos.')
        if not set(permissions) <= PERMISSIONS or not set(scope) <= {'global_internal'}:
            raise ValueError('Permisos o alcance no válidos.')
        user_id = user_id or str(uuid4())
        if not re.fullmatch(r'[A-Za-z0-9_.-]{1,128}', user_id):
            raise ValueError('Identificador de usuario no válido.')
        display_name = (display_name or username).strip()
        if not 1 <= len(display_name) <= 100:
            raise ValueError('El nombre debe tener entre 1 y 100 caracteres.')
        self.store.create_user(user_id, username, display_name, password_hash(password), permissions, scope)

    @staticmethod
    def public_user(user):
        return {field: user[field] for field in ('user_id', 'username', 'display_name')}

    @staticmethod
    def context(user):
        return AccessContext(user_id=user['user_id'], permissions=json.loads(user['permissions']), scope=json.loads(user['scope']))

    def login(self, username, password, remote):
        username = username.strip().lower()
        now = time.time()
        keys = ['ip:' + token_hash(remote), 'user:' + token_hash(username)]
        if not self.store.consume_attempt(keys, now, self.settings.auth_login_window, self.settings.auth_login_max_attempts):
            raise ServiceError('rate_limited', 'Demasiados intentos. Espera unos minutos antes de volver a intentar.', 429)
        user = self.store.user(username)
        encoded = user['password_hash'] if user else self.dummy_hash
        _, salt, expected = encoded.split('$')
        digest = hashlib.scrypt(password.encode('utf-8'), salt=bytes.fromhex(salt), n=32768, r=8, p=1, maxmem=67108864).hex()
        if not secrets.compare_digest(digest, expected) or not user:
            raise ServiceError('unauthenticated', 'Usuario o contraseña incorrectos.', 401)
        token = secrets.token_urlsafe(32)
        if not self.store.create_session(token_hash(token), user['user_id'], now + self.settings.auth_session_ttl, now, encoded):
            raise ServiceError('unauthenticated', 'Usuario o contraseña incorrectos.', 401)
        return token, self.public_user(user)

    def user(self, token):
        user = self.store.session_user(token_hash(token), time.time()) if token and len(token) <= 128 else None
        if not user:
            raise ServiceError('unauthenticated', 'Autenticación requerida.', 401)
        return user

    def logout(self, token):
        if token and len(token) <= 128:
            self.store.revoke(token_hash(token))

    def check_origin(self, request):
        origin = request.headers.get('origin')
        allowed = {str(request.base_url).rstrip('/'), *self.settings.auth_allowed_origins}
        if not origin or origin not in allowed:
            raise ServiceError('forbidden', 'Origen de la solicitud no permitido.', 403)


class IdentityResolver:
    def __init__(self, config: str, browser_auth=None):
        self.browser_auth = browser_auth
        self.identities = {token: AccessContext.model_validate(value) for token, value in json.loads(config).items()}
        if any(len(token) < 16 for token in self.identities):
            raise ValueError('Los tokens deben tener al menos 16 caracteres.')

    def resolve(self, authorization: str | None, request=None) -> AccessContext:
        if authorization and authorization.startswith('Bearer '):
            token = authorization[7:]
            for expected, principal in self.identities.items():
                if secrets.compare_digest(token, expected):
                    return principal
            raise ServiceError('unauthenticated', 'Autenticación requerida.', 401)
        if request is not None and self.browser_auth:
            token = request.cookies.get(COOKIE_NAME)
            if token:
                if request.method not in {'GET', 'HEAD', 'OPTIONS'}:
                    self.browser_auth.check_origin(request)
                return self.browser_auth.context(self.browser_auth.user(token))
        raise ServiceError('unauthenticated', 'Autenticación requerida.', 401)
