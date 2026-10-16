import json
import secrets
from app.contracts import AccessContext, ServiceError


class IdentityResolver:
    def __init__(self, config: str):
        self.identities = {token: AccessContext.model_validate(value) for token, value in json.loads(config).items()}
        if any(len(token) < 16 for token in self.identities):
            raise ValueError('Los tokens deben tener al menos 16 caracteres.')

    def resolve(self, authorization: str | None) -> AccessContext:
        if authorization and authorization.startswith('Bearer '):
            token = authorization[7:]
            for expected, principal in self.identities.items():
                if secrets.compare_digest(token, expected):
                    return principal
        raise ServiceError('unauthenticated', 'Autenticación requerida.', 401)
