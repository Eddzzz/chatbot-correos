from app.analytics.public import plan_analysis
from app.contracts import AccessContext, IntentDecision, ServiceError
from app.data_access.public import QuerySpec, ReadPort
from app.policies.public import authorize_operation, authorize_details


class ToolRegistry:
    supported = frozenset({'tracking', 'offices', 'summary'})

    def __init__(self, reader: ReadPort):
        self.reader = reader

    async def execute(self, intent: IntentDecision, context: AccessContext):
        authorize_operation(context, intent.operation)
        if intent.detail:
            authorize_details(context)
        if intent.operation == 'tracking':
            if not intent.tracking_code:
                raise ServiceError('clarify', 'Indica el código de seguimiento del envío.', 422)
            query = QuerySpec(template='tracking', parameters={'tracking_code': intent.tracking_code.upper()})
        elif intent.operation == 'offices':
            query = QuerySpec(template='offices', parameters={'department': intent.department})
        elif intent.operation == 'summary':
            query = plan_analysis(intent)
        else:
            raise ServiceError('unsupported', 'Esta operación no está disponible.', 422)
        if intent.detail and intent.operation in {'tracking', 'offices'}:
            query = query.model_copy(update={'template': query.template + '_details'})
        return await self.reader.run_read(query, context)
