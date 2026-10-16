import asyncio
import json
import time
import re
import unicodedata
from difflib import get_close_matches
from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4
from pathlib import Path
from app.answers.public import compose_answer
from app.contracts import AccessContext, ChatRequest, ChatResponse, IntentDecision, ServiceError
from app.policies.public import OUTSIDE, UNAVAILABLE
from app.data_access.public import HistoryStore


@dataclass
class Session:
    owner: str
    touched: float
    messages: list[dict] = field(default_factory=list)
    filters: dict[str, str] = field(default_factory=dict)
    last_intent: IntentDecision | None = None
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    title: str = 'Nueva conversación'
    required_permissions: set[str] = field(default_factory=set)
    scope: tuple[str, ...] = ()


class Conversation:
    def __init__(self, settings, model, tools, audit):
        self.settings, self.model, self.tools, self.audit = settings, model, tools, audit
        filename = 'chat-history-fixture.sqlite3' if settings.fixture_data or settings.demo_mode else 'chat-history.sqlite3'
        history_path = settings.history_path or str(Path(__file__).resolve().parents[3] / '.runtime' / filename)
        self.store = HistoryStore(history_path)
        # TTL applies only to the context cache; saved chats remain on disk.
        self.sessions: dict[str, Session] = {}
        self.running: dict[str, tuple[str, asyncio.Task]] = {}
        self.active_sessions: dict[str, tuple[str, asyncio.Task]] = {}

    def prune(self):
        now = time.monotonic()
        active = {session_id for session_id, _ in self.active_sessions.values()}
        self.sessions = {key: value for key, value in self.sessions.items() if key in active or now - value.touched < self.settings.session_ttl}

    def session(self, session_id: str | None, principal: AccessContext):
        self.prune()
        if session_id:
            session = self.sessions.get(session_id)
            if not session:
                row = self.store.load(session_id, principal.user_id)
                if row:
                    payload = json.loads(row['payload'])
                    session = Session(owner=row['owner'], touched=time.monotonic(),
                        messages=payload['messages'], filters=payload['filters'],
                        last_intent=IntentDecision.model_validate(payload['last_intent']) if payload['last_intent'] else None,
                        updated_at=row['updated_at'], title=row['title'],
                        required_permissions=set(json.loads(row['permissions'])), scope=tuple(json.loads(row['scope'])))
                    self.sessions[session_id] = session
            if not session or session.owner != principal.user_id:
                raise ServiceError('session_not_found', 'Conversación no encontrada.', 404)
            if not session.required_permissions <= principal.permissions or session.scope != principal.scope:
                raise ServiceError('forbidden', 'Tus permisos actuales no permiten abrir esta conversación.', 403)
        else:
            if self.store.count(principal.user_id) >= self.settings.max_sessions:
                raise ServiceError('sessions_full', 'Alcanzaste el límite de conversaciones guardadas. Puedes continuar una existente.', 429)
            if len(self.sessions) >= 5000:
                raise ServiceError('sessions_full', 'Capacidad de sesiones alcanzada.', 429)
            session_id = str(uuid4())
            session = self.sessions[session_id] = Session(principal.user_id, time.monotonic(), scope=principal.scope)
            self.store.save(session_id, session)
        session.touched = time.monotonic()
        return session_id, session

    def list_sessions(self, principal):
        self.prune()
        return {'sessions': self.store.list(principal)}

    def history(self, session_id, principal):
        _, session = self.session(session_id, principal)
        return {'messages': session.messages}

    async def office_related_tables(self, office_id, principal):
        started = time.monotonic()
        status = 'error'
        try:
            result = await self.tools.related_tables(office_id, principal)
            status = 'answer'
            return {'rows': result.rows, 'truncated': result.truncated, 'source': result.source, 'queried_at': result.queried_at}
        except ServiceError as error:
            status = 'forbidden' if error.status_code == 403 else 'error'
            raise
        finally:
            self.audit.record(str(uuid4()), status, int((time.monotonic() - started) * 1000), user_id=principal.user_id, operation='offices_related_details', model_version=self.settings.model_version)

    async def office_related_records(self, office_id, table_name, offset, limit, principal):
        started = time.monotonic()
        status = 'error'
        try:
            result = await self.tools.related_records(office_id, table_name, offset, limit, principal)
            status = 'answer'
            return result
        except ServiceError as error:
            status = 'forbidden' if error.status_code == 403 else 'error'
            raise
        finally:
            self.audit.record(str(uuid4()), status, int((time.monotonic() - started) * 1000), user_id=principal.user_id, operation='offices_records_details', model_version=self.settings.model_version)

    async def handle(self, request: ChatRequest, principal: AccessContext, request_id: str, session_id: str):
        started = time.monotonic()
        status = 'error'
        operation = 'greeting'
        task = asyncio.current_task()
        session = self.sessions[session_id]
        if any(active_id == session_id for active_id, _ in self.active_sessions.values()):
            raise ServiceError('session_busy', 'Esta conversación ya está respondiendo una consulta.', 409)
        self.active_sessions[request_id] = (session_id, task)
        self.running[request_id] = (principal.user_id, task)
        answer = None
        session.messages.append({'role': 'user', 'content': request.message, 'request_id': request_id})
        if session.title == 'Nueva conversación':
            session.title = ' '.join(request.message.split())[:80]
        session.updated_at = datetime.now(timezone.utc).isoformat()
        try:
            self.store.save(session_id, session)
            if request.message.strip().lower().strip('¡!¿?. ') in {'hola', 'buenos días', 'buenas tardes', 'buenas noches', 'buenas'}:
                answer = ChatResponse(request_id=request_id, session_id=session_id, status='answer', answer='Hola. Puedo ayudarte con seguimiento, oficinas y resúmenes de Correos Bolivia. Indica tu consulta.')
            elif request.message.strip().lower().strip('¡!¿?. ') in {'qué consultas puedes responder', 'que consultas puedes responder', 'ayuda'}:
                operation = 'capabilities'
                answer = ChatResponse(request_id=request_id, session_id=session_id, status='answer', answer='Según tus permisos, puedo consultar seguimiento por código, oficinas por departamento y contar registros por estado, familia o destino para un periodo de hasta 366 días. Indica ambas fechas AAAA-MM-DD; la fecha final es exclusiva. Las tarifas no están habilitadas. Los conteos son de registros, no garantizan envíos únicos.')
            else:
                async with asyncio.timeout(self.settings.inference_timeout + self.settings.queue_timeout + 15):
                    operation = 'interpretation'
                    session = self.sessions[session_id]
                    confirmed = dict(session.filters)
                    followup = request.message.casefold().strip('¡!¿?. ')
                    if self.is_detail_followup(request.message):
                        intent = (session.last_intent.model_copy(update={'detail': True})
                                  if session.last_intent and session.last_intent.operation in {'offices', 'tracking'}
                                  else IntentDecision(operation='clarify'))
                    elif self.is_unspecified_data_request(request.message):
                        intent = IntentDecision(operation='clarify')
                    elif self.is_bare_postal_request(request.message):
                        intent = IntentDecision(operation='clarify')
                    elif confirmed.get('tracking_code') and followup in {'y su estado', 'su estado', 'el estado de ese envío', 'el estado de ese envio'}:
                        intent = IntentDecision(operation='tracking', tracking_code=confirmed['tracking_code'])
                    else:
                        intent = await self.model.interpret(request.message, context={**confirmed, 'last_operation': session.last_intent.operation if session.last_intent else None})
                        if intent.operation in {'tracking', 'offices'} and self.requests_details(request.message):
                            intent = intent.model_copy(update={'detail': True})
                    operation = intent.operation + ('_details' if intent.detail else '')
                    intent = self.validate_filters(intent, request.message, confirmed)
                    if intent.operation in self.tools.supported:
                        result = await self.tools.execute(intent, principal)
                        answer = compose_answer(request_id, session_id, result)
                        session.last_intent = intent if result.rows else None
                        session.filters = {key: value for key, value in intent.model_dump().items() if key in {'tracking_code', 'start_date', 'end_date', 'department'} and value is not None}
                        session.required_permissions.update({'internal_data', intent.operation})
                        if intent.detail:
                            session.required_permissions.add('personal_data')
                    else:
                        text = {'outside': OUTSIDE, 'rates': UNAVAILABLE, 'clarify': self.clarification(request.message, session)}[intent.operation]
                        answer = ChatResponse(request_id=request_id, session_id=session_id, status={'outside': 'out_of_scope', 'rates': 'unsupported', 'clarify': 'needs_clarification'}[intent.operation], answer=text)
            status = answer.status
            return answer
        except TimeoutError:
            raise ServiceError('request_timeout', 'La consulta superó su tiempo máximo. Intenta nuevamente.') from None
        except asyncio.CancelledError:
            status = 'cancelled'
            raise
        except ServiceError as exc:
            status = {'clarify': 'needs_clarification', 'forbidden': 'forbidden'}.get(exc.code, 'error')
            raise
        finally:
            if answer:
                session.messages.append({**answer.model_dump(mode='json'), 'role': 'assistant', 'content': answer.answer})
            else:
                session.messages.append({'role': 'assistant', 'content': 'Consulta detenida.' if status == 'cancelled' else 'No se pudo completar la consulta. Puedes intentarlo nuevamente.', 'request_id': request_id, 'status': 'error'})
            session.updated_at = datetime.now(timezone.utc).isoformat()
            session.touched = time.monotonic()
            try:
                self.store.save(session_id, session)
            finally:
                self.active_sessions.pop(request_id, None)
                self.running.pop(request_id, None)
                self.audit.record(request_id, status, int((time.monotonic() - started) * 1000), user_id=principal.user_id, operation=operation, model_version='demo-rules-v1' if self.settings.demo_mode else self.settings.model_version)

    @staticmethod
    def normalized_words(message):
        words = re.findall(r'[a-z0-9]+', ''.join(char for char in unicodedata.normalize('NFD', message.casefold()) if not unicodedata.combining(char)))
        # Correct only presentation words; never rewrite identifiers, dates or places.
        vocabulary = ('completo', 'completos', 'completa', 'completas', 'detalles', 'informacion', 'datos')
        return [get_close_matches(word, vocabulary, n=1, cutoff=.86)[0]
                if len(word) >= 5 and word not in vocabulary and get_close_matches(word, vocabulary, n=1, cutoff=.86)
                else word for word in words]

    @staticmethod
    def is_bare_postal_request(message):
        words = set(Conversation.normalized_words(message))
        resources = {'sucursal', 'sucursales', 'oficina', 'oficinas', 'envio', 'envios', 'paquete', 'paquetes'}
        return bool(words & resources) and words <= resources | {'dame', 'muestra', 'muestrame', 'quiero', 'ver', 'datos', 'de', 'la', 'el', 'las', 'los', 'y', 'tambien', 'ambos', 'por', 'favor'}

    @staticmethod
    def clarification(message, session):
        words = set(Conversation.normalized_words(message))
        offices = bool(words & {'sucursal', 'sucursales', 'oficina', 'oficinas'})
        shipments = bool(words & {'envio', 'envios', 'paquete', 'paquetes'})
        previous = session.last_intent
        if offices and shipments:
            if previous and previous.operation == 'offices':
                known = f' de {previous.department}' if previous.department else ' ya consultadas'
                return f'Puedo ampliar los datos de las sucursales{known}. Para consultar un envío, indica su código de seguimiento. ¿Quieres la ficha completa de la sucursal o consultar un código? No puedo deducir los envíos de una sucursal solo por su departamento.'
            return 'Puedo consultar ambos: indica el departamento de las sucursales y el código de seguimiento del envío. No hay una relación confirmada que permita listar los envíos de una sucursal solo por su ciudad.'
        if Conversation.is_detail_followup(message):
            return '¿De qué recurso necesitas la ficha completa? Indica una sucursal y su departamento, o el código de un envío.'
        if offices:
            return '¿De qué departamento necesitas las sucursales? También puedes pedir «todas las sucursales».'
        if shipments:
            return 'Indica el código de seguimiento del envío que quieres consultar.'
        return '¿De qué información necesitas los datos: una sucursal o un envío? Indica el departamento o el código. Para el último registro, especifica la tabla o el tipo de dato.'

    @staticmethod
    def requests_details(message):
        return bool(set(Conversation.normalized_words(message)) & {'completo', 'completos', 'completa', 'completas', 'compelto', 'detalles', 'asociados', 'asociadas'})

    @staticmethod
    def is_detail_followup(message):
        words = set(Conversation.normalized_words(message))
        allowed = {'dame', 'da', 'me', 'danos', 'muestra', 'muestrame', 'mostrar', 'quiero', 'necesito', 'ver', 'amplia', 'ampliar', 'mas', 'y', 'por', 'favor', 'completo', 'completos', 'completa', 'completas', 'compelto', 'datos', 'dato', 'atos', 'los', 'lo', 'las', 'la', 'el', 'de', 'del', 'su', 'sus', 'esos', 'esas', 'estos', 'estas', 'todos', 'todo', 'todas', 'toda', 'detalles', 'detalle', 'informacion', 'asociados', 'asociadas', 'relaciones', 'tambien'}
        return bool(words) and words <= allowed and (Conversation.requests_details(message) or {'todos', 'datos'} <= words or {'toda', 'informacion'} <= words)

    @staticmethod
    def is_unspecified_data_request(message):
        words = set(Conversation.normalized_words(message))
        return bool(words & {'dato', 'datos', 'registro', 'registros'}) and words <= {'dame', 'el', 'la', 'los', 'las', 'ultimo', 'ultima', 'dato', 'datos', 'registro', 'registros', 'guardado', 'guardados', 'guardada', 'guardadas', 'muestra', 'muestrame', 'ver', 'quiero', 'necesito', 'por', 'favor'}

    @staticmethod
    def validate_filters(intent, message, confirmed):
        updates = {}
        text = message.casefold()
        continuation = Conversation.is_detail_followup(message) or bool(re.search(r'\b(su estado|ese envío|ese envio|mismo envío|mismo envio|ese código|ese codigo|mismo código|mismo codigo|ese periodo|ese período|mismo periodo|mismo período|esas fechas|mismas fechas)\b', text))
        if intent.operation == 'tracking':
            candidates = re.findall(r'\b[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*\b', message)
            new_codes = [value for value in candidates if any(char.isdigit() for char in value) and value.casefold() != confirmed.get('tracking_code', '').casefold()]
            may_reuse = continuation and not new_codes
            code = intent.tracking_code or (confirmed.get('tracking_code') if may_reuse else None)
            if code and code.casefold() not in text and not (may_reuse and code == confirmed.get('tracking_code')):
                raise ServiceError('clarify', 'Confirma el código de seguimiento exacto; no aparece en tu consulta.', 422)
            if new_codes and code and code.casefold() not in {value.casefold() for value in new_codes}:
                raise ServiceError('clarify', 'Indica y confirma el nuevo código de seguimiento; no reutilizaré el anterior.', 422)
            updates['tracking_code'] = code
        if intent.operation == 'summary':
            explicit_dates = re.findall(r'\b\d{4}-\d{2}-\d{2}\b', message)
            new_period = bool(re.search(r'\b(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre|hoy|ayer|semana|mes|año|\d{4})\b', text))
            may_reuse = continuation and not explicit_dates and not new_period
            for key in ('start_date', 'end_date'):
                value = getattr(intent, key) or (confirmed.get(key) if may_reuse else None)
                if value and value not in explicit_dates and not (may_reuse and value == confirmed.get(key)):
                    raise ServiceError('clarify', 'Indica ambas fechas explícitas AAAA-MM-DD, incluida la fecha final exclusiva.', 422)
                updates[key] = value
        if intent.operation == 'offices':
            office_followup = Conversation.is_detail_followup(message) and intent.department == confirmed.get('department')
            if intent.department and intent.department.casefold() not in text and not office_followup:
                raise ServiceError('clarify', 'Confirma el departamento de las oficinas que deseas consultar.', 422)
            if not intent.department and not any(word in text for word in ('todas', 'todos', 'nacional')) and not Conversation.is_detail_followup(message):
                raise ServiceError('clarify', 'Indica el departamento para consultar oficinas, o escribe «todas las oficinas».', 422)
        return intent.model_copy(update=updates)

    def cancel(self, request_id, principal):
        entry = self.running.get(request_id)
        if not entry or entry[0] != principal.user_id:
            raise ServiceError('request_not_found', 'Solicitud no encontrada.', 404)
        entry[1].cancel()
        return {'request_id': request_id, 'status': 'cancelled'}
