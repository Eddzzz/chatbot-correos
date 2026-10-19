from datetime import date, datetime, timedelta, timezone
import re
import unicodedata
from app.contracts import IntentDecision, ServiceError
from app.data_access.public import QuerySpec

MONTHS = ('enero','febrero','marzo','abril','mayo','junio','julio','agosto','septiembre','octubre','noviembre','diciembre')


def period_text(message):
    return ''.join(c for c in unicodedata.normalize('NFD',message.casefold()) if not unicodedata.combining(c))


def is_period_followup(message):
    words = set(re.findall(r'[a-z]+',period_text(message)))
    return bool(words) and words <= set(MONTHS) | {'de','del','el','la','los','las','todo','toda','todos','todas','mes','ano','este','esta','pasado','anterior','hoy','ayer','al','a','desde','hasta','en','completo','completa','y','dame','muestra','muestrame','quiero','necesito','por','favor','ahora','solo'}


def resolve_period(message, confirmed=None, *, today=None):
    """Resolve calendar expressions deterministically; model-generated dates are not evidence."""
    text = period_text(message)
    today = today or datetime.now(timezone(timedelta(hours=-4))).date()
    if re.search(r'\b\d{4}-\d{2}-\d{2}\b',text):
        return None  # ISO endpoints retain their existing exclusive-end contract.
    found = [month for month in MONTHS if re.search(r'\b'+month+r'\b',text)]
    if len(found)>1:
        raise ServiceError('period_ambiguous','¿Quieres un mes concreto o un intervalo entre esos meses? Indica, por ejemplo, «todo octubre de 2026».',422)
    if re.search(r'\b(hoy|ayer)\b',text):
        if found or ('hoy' in text and 'ayer' in text):
            raise ServiceError('period_ambiguous','Indica un solo periodo para la consulta.',422)
        start=today-timedelta(days=1 if re.search(r'\bayer\b',text) else 0)
        return start.isoformat(),(start+timedelta(days=1)).isoformat()
    relative = re.search(r'\b(este mes|mes (?:pasado|anterior))\b',text)
    if not found and not relative:
        return None
    years = set(re.findall(r'\b\d{4}\b',text))
    if len(years)>1 or (relative and (found or years)):
        raise ServiceError('period_ambiguous','Indica un solo mes y año para la consulta.',422)
    inherited = (confirmed or {}).get('start_date') if is_period_followup(message) else None
    year=int(next(iter(years))) if years else int(inherited[:4]) if inherited else today.year
    if re.search(r'\bano (?:pasado|anterior)\b',text) and not years:
        year=today.year-1
    elif re.search(r'\beste ano\b',text) and not years:
        year=today.year
    if not 1<=year<=9998:
        raise ServiceError('period_ambiguous','Indica un año válido para el periodo solicitado.',422)
    month=MONTHS.index(found[0])+1 if found else today.month
    if relative:
        year=today.year
        if relative.group()!='este mes':
            year,month=(year-1,12) if month==1 else (year,month-1)
    start=date(year,month,1)
    end=date(year+1,1,1) if month==12 else date(year,month+1,1)
    days = re.search(r'\b(?:del?|desde el)\s+(\d{1,2})\s+(?:al|hasta el)\s+(\d{1,2})\s+(?:de\s+)?'+(found[0] if found else r'\b$'),text)
    if days:
        try:
            start=date(year,month,int(days[1])); last=date(year,month,int(days[2]))
            if last<start: raise ValueError()
            end=last+timedelta(days=1)
        except ValueError:
            raise ServiceError('period_ambiguous','Ese intervalo no es válido. Indica los días inicial y final del mes.',422) from None
    elif re.search(r'\b\d{1,2}\b',re.sub(r'\b\d{4}\b','',text)):
        raise ServiceError('period_ambiguous','¿Qué días del mes necesitas? Puedes indicar «del 1 al 31 de octubre de 2026».',422)
    return start.isoformat(),end.isoformat()


def describe_period(start,end):
    start,end=date.fromisoformat(start),date.fromisoformat(end)
    last=end-timedelta(days=1)
    if start.day==1 and end.day==1 and (end-start).days<=31:
        return f'{MONTHS[start.month-1]} de {start.year} (del 1 al {last.day})'
    label=lambda day:f'{day.day} de {MONTHS[day.month-1]} de {day.year}'
    return label(start) if start==last else f'del {label(start)} al {label(last)}'


def plan_analysis(intent: IntentDecision) -> QuerySpec:
    if not intent.start_date or not intent.end_date:
        raise ServiceError('clarify', '¿De qué mes o periodo necesitas los registros? Por ejemplo, «todo octubre de 2026».', 422)
    try:
        start, end = date.fromisoformat(intent.start_date), date.fromisoformat(intent.end_date)
    except ValueError:
        raise ServiceError('clarify', 'Indica fechas válidas en formato AAAA-MM-DD.', 422) from None
    if not 0 < (end - start).days <= 366:
        raise ServiceError('clarify', 'El periodo debe tener entre 1 y 366 días; la fecha final es exclusiva.', 422)
    if intent.operation=='accounting':
        return QuerySpec(template='summary_accounting_details',parameters={'start_date':start,'end_date':end,'categories':intent.accounting_categories})
    return QuerySpec(template='summary_' + intent.dimension, parameters={'start_date': start, 'end_date': end,'family':intent.family})
