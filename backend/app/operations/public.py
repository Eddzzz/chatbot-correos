from app.analytics.public import plan_analysis
from dataclasses import replace
from datetime import datetime, timezone
from app.contracts import AccessContext, IntentDecision, ServiceError
from app.data_access.public import QuerySpec, ReadPort
from app.policies.public import authorize_operation, authorize_details


class ToolRegistry:
    supported = frozenset({'tracking', 'offices', 'summary', 'accounting'})

    def __init__(self, reader: ReadPort):
        self.reader = reader

    async def execute(self, intent: IntentDecision, context: AccessContext):
        authorize_operation(context, 'summary' if intent.operation=='accounting' else intent.operation)
        detail = intent.detail or intent.office_personnel
        if (detail and intent.operation in {'tracking','offices'}) or intent.operation=='accounting':
            authorize_details(context)
        if intent.operation == 'tracking':
            if not intent.tracking_code:
                raise ServiceError('clarify', 'Indica el código de seguimiento del envío.', 422)
            query = QuerySpec(template='tracking', parameters={'tracking_code': intent.tracking_code.upper()})
        elif intent.operation == 'offices':
            query = QuerySpec(template='offices', parameters={'department': intent.department})
        elif intent.operation in {'summary','accounting'}:
            query = plan_analysis(intent)
            if intent.operation == 'summary' and intent.dimension in {'department', 'office'}:
                authorize_operation(context, 'offices')
                destinations = await self.reader.run_read(query.model_copy(update={'template': 'summary_destination'}), context)
                offices = await self.reader.run_read(QuerySpec(template='offices', parameters={'department': None}), context)
                if destinations.truncated or offices.truncated:
                    raise ServiceError('clarify', 'El desglose por destino o el directorio está limitado. Acota el periodo o consulta por destino para ver los resultados parciales.', 422)
                def normalized(value):
                    import unicodedata
                    return ' '.join(''.join(c for c in unicodedata.normalize('NFD', value or '') if not unicodedata.combining(c)).casefold().split())
                totals = {}
                for row in destinations.rows:
                    matches = [office for office in offices.rows if normalized(office.get('municipality')) and normalized(office.get('municipality')) == normalized(row.get('destination'))]
                    label = (matches[0].get('department') if intent.dimension == 'department' else matches[0].get('municipality')) if len(matches) == 1 else None
                    label = label or 'Sin correspondencia'
                    totals[label] = totals.get(label, 0) + row['total']
                return replace(destinations, rows=[{intent.dimension: label, 'total': total} for label, total in sorted(totals.items(), key=lambda item: (-item[1], item[0]))], source=destinations.source+' · correspondencia con '+offices.source)
        else:
            raise ServiceError('unsupported', 'Esta operación no está disponible.', 422)
        if detail and intent.operation in {'tracking', 'offices'}:
            query = query.model_copy(update={'template': query.template + '_details'})
        if intent.operation=='accounting':
            counts = await self.reader.run_read(QuerySpec(template='summary_accounting_counts_details',parameters=query.parameters),context)
            if counts.truncated:
                raise ServiceError('accounting_counts_limited','No se pudo completar el conteo de estas categorías.',503)
            result = await self.reader.run_read(query,context)
            totals = {category:0 for category in intent.accounting_categories}
            totals.update({row['category']:row['total'] for row in counts.rows})
            return replace(result,totals=totals)
        result = await self.reader.run_read(query, context)
        if intent.operation=='offices' and intent.office_personnel:
            rows=[]
            dates=[]
            limited=result.truncated
            for office in result.rows:
                details=office.get('details',{})
                fields=details.get('campos',{})
                personnel=details.get('relaciones',{}).get('usuarios',{})
                limited=limited or personnel.get('truncado',False)
                for person in personnel.get('registros',[]):
                    data=person.get('campos',{})
                    rows.append({'nombre':data.get('name'),'correo_electronico':data.get('email'),'documento_identidad':data.get('ci'),'ciudad':data.get('ciudad'),'sucursal':fields.get('municipio'),'departamento':office.get('department')})
                    if intent.latest_personnel:
                        rows[-1]['fecha_registro']=data.get('created_at')
                        dates.append(data.get('created_at'))
            if intent.latest_personnel:
                if limited:
                    raise ServiceError('clarify','La lista disponible está limitada; no puedo confirmar cuál es la última persona registrada con estos resultados parciales.',422)
                if rows:
                    try:
                        timestamps=[datetime.fromisoformat(str(value)) for value in dates]
                        timestamps=[value.astimezone(timezone.utc) if value.tzinfo else value for value in timestamps]
                        latest=max(timestamps)
                    except (ValueError,TypeError):
                        raise ServiceError('clarify','Faltan fechas de registro válidas o comparables en el personal consultado; no puedo confirmar cuál fue la última persona registrada.',422) from None
                    rows=[row for row,registered in zip(rows,timestamps) if registered==latest]
            return replace(result,rows=rows,truncated=limited)
        return result

    async def postal_records(self,start_date,end_date,family,offset,limit,context):
        authorize_operation(context,'summary')
        if offset<0 or offset>10000000 or not 1<=limit<=20:
            raise ServiceError('invalid_page','La página solicitada no es válida.',422)
        query=plan_analysis(IntentDecision(operation='summary',start_date=start_date,end_date=end_date,family=family))
        result=await self.reader.run_read(QuerySpec(template='summary_records',parameters={**query.parameters,'offset':offset,'page_limit':limit+1}),context)
        rows=result.rows[:limit]
        more=result.truncated or len(result.rows)>limit
        if not rows and result.truncated:
            raise ServiceError('record_too_large','Un registro supera el límite de respuesta.',422)
        return {'rows':rows,'offset':offset,'next_offset':offset+len(rows) if more else None,'source':result.source,'queried_at':result.queried_at,'truncated':more}

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
