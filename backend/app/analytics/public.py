from datetime import date
from app.contracts import IntentDecision, ServiceError
from app.data_access.public import QuerySpec


def plan_analysis(intent: IntentDecision) -> QuerySpec:
    if not intent.start_date or not intent.end_date:
        raise ServiceError('clarify', 'Indica fecha inicial y fecha final exclusiva (AAAA-MM-DD) para el resumen.', 422)
    try:
        start, end = date.fromisoformat(intent.start_date), date.fromisoformat(intent.end_date)
    except ValueError:
        raise ServiceError('clarify', 'Indica fechas válidas en formato AAAA-MM-DD.', 422) from None
    if not 0 < (end - start).days <= 366:
        raise ServiceError('clarify', 'El periodo debe tener entre 1 y 366 días; la fecha final es exclusiva.', 422)
    return QuerySpec(template='summary_' + intent.dimension, parameters={'start_date': start, 'end_date': end})
