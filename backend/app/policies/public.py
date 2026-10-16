from app.contracts import AccessContext, ServiceError

OUTSIDE = 'Solo puedo ayudarte con información de Correos Bolivia disponible en esta base de datos. Por favor, haz una pregunta sobre Correos Bolivia.'
UNAVAILABLE = 'No dispongo de esa información en la base de datos de Correos Bolivia.'


def authorize_operation(context: AccessContext, operation: str):
    if operation not in context.permissions or 'internal_data' not in context.permissions or context.scope != ('global_internal',):
        raise ServiceError('forbidden', 'No tienes permiso para consultar esa información.', 403)


def authorize_details(context: AccessContext):
    if 'personal_data' not in context.permissions:
        raise ServiceError('forbidden', 'No tienes permiso para consultar fichas completas con datos personales.', 403)
