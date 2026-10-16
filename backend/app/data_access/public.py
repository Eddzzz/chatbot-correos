from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Protocol
from pydantic import Field
import sqlglot
from sqlglot import exp
from app.contracts import AccessContext, StrictModel
from app.data_access.history import HistoryStore

TEMPLATES = {
    'tracking': 'SELECT source, tracking_code, status, origin, destination, registered_at, updated_at FROM chatbot.v_tracking WHERE tracking_code = %(tracking_code)s AND %(access_scope)s = \'global_internal\' ORDER BY registered_at DESC LIMIT %(limit)s',
    'offices': 'SELECT office_id, codigo_sucursal, municipality, department, phone FROM chatbot.v_offices WHERE (CAST(%(department)s AS TEXT) IS NULL OR lower(translate(department, \'ÁÉÍÓÚÜáéíóúü\', \'AEIOUUaeiouu\')) = lower(translate(CAST(%(department)s AS TEXT), \'ÁÉÍÓÚÜáéíóúü\', \'AEIOUUaeiouu\'))) AND %(access_scope)s = \'global_internal\' ORDER BY department, municipality, office_id LIMIT %(limit)s',
}
for dimension in ('source', 'status', 'destination'):
    TEMPLATES['summary_' + dimension] = f'SELECT {dimension}, COUNT(*) AS total FROM chatbot.v_tracking WHERE registered_at >= %(start_date)s AND registered_at < %(end_date)s AND %(access_scope)s = \'global_internal\' GROUP BY {dimension} ORDER BY total DESC LIMIT %(limit)s'

TEMPLATES['tracking_details'] = TEMPLATES['tracking'].replace('source, tracking_code, status, origin, destination, registered_at, updated_at', 'source, tracking_code, details').replace('chatbot.v_tracking ', 'chatbot.v_tracking_details ').replace('registered_at DESC', 'source, tracking_code')
TEMPLATES['offices_details'] = TEMPLATES['offices'].replace('office_id, codigo_sucursal, municipality, department, phone', 'office_id, department, details').replace('chatbot.v_offices ', 'chatbot.v_office_details ').replace('department, municipality, office_id', 'department, office_id')
TEMPLATES['offices_related_details'] = "SELECT office_id, table_name, total_count, relation_kind, path_info, descendant_count, lookup_count FROM chatbot.v_office_related_counts WHERE office_id = %(office_id)s AND %(access_scope)s = 'global_internal' ORDER BY table_name LIMIT %(limit)s"
TEMPLATES['offices_table_details'] = TEMPLATES['offices_related_details'].replace('WHERE office_id', 'WHERE table_name = %(table_name)s AND office_id')
TEMPLATES['offices_records_details'] = "SELECT record_key, record, relation_kind FROM chatbot.v_office_related_records WHERE office_id = %(office_id)s AND table_name = %(table_name)s AND %(access_scope)s = 'global_internal' ORDER BY record_key LIMIT %(page_limit)s OFFSET %(offset)s"
TEMPLATES['summary_accounting_details'] = "SELECT category, record_id, occurred_at, service, active, record AS details FROM chatbot.v_accounting_records WHERE occurred_at >= %(start_date)s AND occurred_at < %(end_date)s AND category = ANY(%(categories)s) AND %(access_scope)s = 'global_internal' ORDER BY occurred_at DESC, category, record_id LIMIT %(limit)s"
TEMPLATES['summary_accounting_counts_details'] = "SELECT category, COUNT(*) AS total FROM chatbot.v_accounting_records WHERE occurred_at >= %(start_date)s AND occurred_at < %(end_date)s AND category = ANY(%(categories)s) AND %(access_scope)s = 'global_internal' GROUP BY category ORDER BY category LIMIT %(limit)s"


class QuerySpec(StrictModel):
    template: str
    parameters: dict = Field(default_factory=dict)


@dataclass
class QueryResult:
    rows: list[dict]
    source: str
    queried_at: datetime
    truncated: bool = False
    totals: dict[str,int] | None = None


class ReadPort(Protocol):
    async def run_read(self, query: QuerySpec, context: AccessContext) -> QueryResult: ...


def validate_query(query: QuerySpec, sql: str):
    if query.template not in TEMPLATES or sql != TEMPLATES[query.template]:
        raise ValueError('Consulta fuera del catálogo aprobado.')
    # Parse a structurally identical statement with literals in place of driver placeholders.
    import re
    statements = sqlglot.parse(re.sub(r'%\([a-z_]+\)s', 'NULL', sql), read='postgres')
    if len(statements) != 1 or not isinstance(statements[0], exp.Select):
        raise ValueError('Solo SELECT.')
    for table in statements[0].find_all(exp.Table):
        if table.db != 'chatbot' or table.name not in {'v_tracking', 'v_offices', 'v_tracking_details', 'v_office_details', 'v_office_related_counts', 'v_office_related_records','v_accounting_records'}:
            raise ValueError('Fuente no autorizada.')
    if any(isinstance(node, (exp.Insert, exp.Update, exp.Delete, exp.Command, exp.Subquery, exp.Union)) for node in statements[0].walk()):
        raise ValueError('Estructura SQL no autorizada.')
