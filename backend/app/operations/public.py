from app.analytics.public import plan_analysis
from dataclasses import replace
from app.contracts import AccessContext, IntentDecision, ServiceError
from app.data_access.public import QuerySpec, ReadPort
from app.policies.public import authorize_operation, authorize_details


class ToolRegistry:
    supported = frozenset({'tracking', 'offices', 'summary', 'accounting'})

    def __init__(self, reader: ReadPort):
        self.reader = reader

    async def execute(self, intent: IntentDecision, context: AccessContext):
        authorize_operation(context, 'summary' if intent.operation=='accounting' else intent.operation)
        if intent.detail or intent.operation=='accounting':
            authorize_details(context)
        if intent.operation == 'tracking':
            if not intent.tracking_code:
                raise ServiceError('clarify', 'Indica el código de seguimiento del envío.', 422)
            query = QuerySpec(template='tracking', parameters={'tracking_code': intent.tracking_code.upper()})
        elif intent.operation == 'offices':
            query = QuerySpec(template='offices', parameters={'department': intent.department})
        elif intent.operation in {'summary','accounting'}:
            query = plan_analysis(intent)
        else:
            raise ServiceError('unsupported', 'Esta operación no está disponible.', 422)
        if intent.detail and intent.operation in {'tracking', 'offices'}:
            query = query.model_copy(update={'template': query.template + '_details'})
        if intent.operation=='accounting':
            counts = await self.reader.run_read(QuerySpec(template='summary_accounting_counts_details',parameters=query.parameters),context)
            if counts.truncated:
                raise ServiceError('accounting_counts_limited','No se pudo completar el conteo de estas categorías.',503)
            result = await self.reader.run_read(query,context)
            totals = {category:0 for category in intent.accounting_categories}
            totals.update({row['category']:row['total'] for row in counts.rows})
            return replace(result,totals=totals)
        return await self.reader.run_read(query, context)

    async def related_tables(self, office_id: int, context: AccessContext):
        authorize_operation(context, 'offices')
        authorize_details(context)
        return await self.reader.run_read(QuerySpec(template='offices_related_details', parameters={'office_id': office_id}), context)

    async def related_records(self, office_id: int, table_name: str, offset: int, limit: int, context: AccessContext):
        if office_id < 1 or offset < 0 or offset > 10000000 or not 1 <= limit <= 20:
            raise ServiceError('invalid_page', 'La página solicitada no es válida.', 422)
        authorize_operation(context, 'offices')
        authorize_details(context)
        tables = await self.reader.run_read(QuerySpec(template='offices_table_details', parameters={'office_id': office_id, 'table_name': table_name}), context)
        table = next((row for row in tables.rows if row['table_name'] == table_name), None)
        if table is None:
            raise ServiceError('relation_not_found', 'La tabla no pertenece al catálogo de relaciones de esta sucursal.', 404)
        result = await self.reader.run_read(QuerySpec(template='offices_records_details', parameters={
            'office_id': office_id, 'table_name': table_name, 'offset': offset, 'page_limit': limit + 1}), context)
        has_more = result.truncated or len(result.rows) > limit
        rows = result.rows[:limit]
        if not rows and result.truncated:
            raise ServiceError('record_too_large', 'Un registro supera el límite de respuesta y no puede mostrarse completo.', 422)
        return {'rows': rows, 'total_count': table['total_count'], 'offset': offset,
                'next_offset': offset + len(rows) if has_more else None,
                'source': result.source, 'queried_at': result.queried_at, 'truncated': has_more}
