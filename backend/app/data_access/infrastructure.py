import json
from datetime import datetime, timezone
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool
from app.contracts import AccessContext, ServiceError
from app.data_access.public import QueryResult, QuerySpec, TEMPLATES, validate_query
from app.policies.public import authorize_operation, authorize_details


class PostgresReader:
    def __init__(self, settings):
        self.settings = settings
        self.pool = AsyncConnectionPool(settings.database_url, min_size=0, max_size=3, open=False, kwargs={'row_factory': dict_row}, timeout=5)

    async def open(self):
        await self.pool.open()

    async def close(self):
        await self.pool.close()

    async def run_read(self, query: QuerySpec, context: AccessContext):
        authorize_operation(context, query.template.split('_')[0])
        if query.template.endswith('_details'):
            authorize_details(context)
        sql = TEMPLATES.get(query.template, '')
        validate_query(query, sql)
        # The metadata inventory is a separate bounded contract (at most 128 tables).
        # Operational record limits do not hide tables from that inventory.
        row_limit = 128 if query.template == 'offices_related_details' else 3 if query.template == 'summary_accounting_counts_details' else self.settings.max_rows
        byte_limit = 65536 if query.template == 'offices_related_details' else self.settings.max_result_bytes
        params = {'family':None,**query.parameters, 'access_scope': 'global_internal', 'limit': row_limit + 1}
        try:
            async with self.pool.connection() as conn:
                async with conn.transaction():
                    await conn.execute('SET TRANSACTION READ ONLY')
                    await conn.execute("SELECT set_config('statement_timeout', %s, true), set_config('chatbot.access_scope', %s, true), set_config('chatbot.personal_access', %s, true)", (str(self.settings.statement_timeout_ms), 'global_internal', 'allowed' if 'personal_data' in context.permissions else 'denied'))
                    role = await (await conn.execute("SELECT rolsuper, rolbypassrls, rolcreaterole, rolcreatedb FROM pg_roles WHERE rolname = current_user")).fetchone()
                    if not role or any(role.values()):
                        raise ServiceError('unsafe_database_role', 'La cuenta de lectura requiere una configuración segura.')
                    owned = await (await conn.execute("SELECT EXISTS (SELECT 1 FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE c.relowner=(SELECT oid FROM pg_roles WHERE rolname=current_user) AND n.nspname NOT IN ('pg_catalog','information_schema')) AS owns_objects")).fetchone()
                    raw_access = await (await conn.execute("SELECT EXISTS (SELECT 1 FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='public' AND c.relkind IN ('r','v','m','p') AND has_table_privilege(current_user,c.oid,'SELECT')) AS raw_access")).fetchone()
                    if owned['owns_objects'] or raw_access['raw_access']:
                        raise ServiceError('unsafe_database_role', 'La cuenta debe consultar únicamente las vistas aprobadas.')
                    cursor = await conn.execute(sql, params)
                    rows, size, truncated = [], 0, False
                    async for row in cursor:
                        size += len(json.dumps(row, default=str).encode())
                        if len(rows) >= row_limit or size > byte_limit:
                            truncated = True
                            break
                        rows.append(row)
            source = ('DEMOSTRACIÓN · datos ficticios · ' if self.settings.fixture_data else '') + ('Directorio de sucursales' if query.template.startswith('offices') else 'Registros de seguimiento postal')
            if query.template.startswith('summary_accounting'):
                source = ('DEMOSTRACIÓN · datos ficticios · ' if self.settings.fixture_data else '') + 'Movimientos y cobros de cuentas por cobrar · registros de facturas'
            if self.settings.data_snapshot and not self.settings.fixture_data:
                source += ' · respaldo local del ' + self.settings.data_snapshot
            return QueryResult(rows, source, datetime.now(timezone.utc), truncated)
        except ServiceError:
            raise
        except Exception:
            raise ServiceError('database_unavailable', 'Hay un problema temporal al consultar la base de datos. Intenta nuevamente.') from None


class UnconfiguredReader:
    async def run_read(self, query, context):
        raise ServiceError('database_unconfigured', 'La conexión PostgreSQL aún no está configurada.')


class DemoReader:
    async def run_read(self, query, context):
        authorize_operation(context, query.template.split('_')[0])
        if query.template.endswith('_details'):
            authorize_details(context)
        validate_query(query, TEMPLATES.get(query.template, ''))
        if query.template in {'offices_related_details', 'offices_table_details', 'offices_records_details'}:
            return QueryResult([], 'DEMOSTRACIÓN · relaciones sin registros asociados', datetime.now(timezone.utc))
        rows = []
        if query.template.startswith('tracking') and query.parameters['tracking_code'] == 'DEMO123BO':
            rows = [{'source': 'demo', 'tracking_code': 'DEMO123BO', 'status': 'En tránsito (ficticio)', 'origin': 'La Paz', 'destination': 'Cochabamba', 'registered_at': '2026-01-15', 'updated_at': '2026-01-16'}]
        if query.template.startswith('offices') and query.parameters.get('department') in (None, 'La Paz'):
            rows = [{'office_id': 1, 'codigo_sucursal': 'DEMO-LP', 'municipality': 'La Paz', 'department': 'La Paz', 'phone': 'Dato ficticio'}]
        if query.template=='summary_records':
            rows=[{'source':query.parameters.get('family') or 'ems','tracking_code':'DEMO123BO','status':'En tránsito (ficticio)','origin':'La Paz','destination':'Cochabamba','registered_at':str(query.parameters['start_date']),'updated_at':str(query.parameters['start_date'])}] if query.parameters['offset']==0 else []
        elif query.template.startswith('summary_') and not query.template.startswith('summary_accounting'):
            rows = [{query.template[8:]: 'Dato ficticio', 'total': 1}]
        if query.template=='summary_accounting_counts_details':
            rows = [{'category':category,'total':1} for category in query.parameters['categories']]
        elif query.template=='summary_accounting_details':
            rows = [{'category':category,'record_id':index,'occurred_at':str(query.parameters['start_date']),'service':'Servicio ficticio','active':True,'details':{'tabla':'demostracion','campos':{'id':index,'descripcion':'Registro ficticio'},'omitidos':[]}} for index,category in enumerate(query.parameters['categories'],1)]
        if query.template.endswith('_details') and not query.template.startswith('summary_accounting'):
            rows = [{**{key: value for key, value in row.items() if key in {'office_id', 'department', 'source', 'tracking_code'}}, 'details': {'tabla': 'demostracion', 'campos': row, 'relaciones': {}, 'omitidos': []}} for row in rows]
        return QueryResult(rows, 'DEMOSTRACIÓN · datos ficticios', datetime.now(timezone.utc))
