from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Protocol
from pydantic import Field
import sqlglot
from sqlglot import exp
from app.contracts import AccessContext, StrictModel

TEMPLATES = {
    'tracking': 'SELECT source, tracking_code, status, origin, destination, registered_at, updated_at FROM chatbot.v_tracking WHERE tracking_code = %(tracking_code)s AND %(access_scope)s = \'global_internal\' ORDER BY registered_at DESC LIMIT %(limit)s',
    'offices': 'SELECT office_id, codigo_sucursal, municipality, department, phone FROM chatbot.v_offices WHERE (CAST(%(department)s AS TEXT) IS NULL OR department = %(department)s) AND %(access_scope)s = \'global_internal\' ORDER BY department, municipality, office_id LIMIT %(limit)s',
}
for dimension in ('source', 'status', 'destination'):
    TEMPLATES['summary_' + dimension] = f'SELECT {dimension}, COUNT(*) AS total FROM chatbot.v_tracking WHERE registered_at >= %(start_date)s AND registered_at < %(end_date)s AND %(access_scope)s = \'global_internal\' GROUP BY {dimension} ORDER BY total DESC LIMIT %(limit)s'


class QuerySpec(StrictModel):
    template: str
    parameters: dict = Field(default_factory=dict)


@dataclass
class QueryResult:
    rows: list[dict]
    source: str
    queried_at: datetime
    truncated: bool = False


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
        if table.db != 'chatbot' or table.name not in {'v_tracking', 'v_offices'}:
            raise ValueError('Fuente no autorizada.')
    if any(isinstance(node, (exp.Insert, exp.Update, exp.Delete, exp.Command, exp.Subquery, exp.Union)) for node in statements[0].walk()):
        raise ValueError('Estructura SQL no autorizada.')
