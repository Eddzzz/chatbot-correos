import asyncio
import json
import time
import re
import unicodedata
from difflib import get_close_matches
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from uuid import uuid4
from pathlib import Path
from app.answers.public import compose_answer
from app.analytics.public import MONTHS, resolve_period, is_period_followup, describe_period
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
    contexts: dict[str, dict] = field(default_factory=dict)


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
                        messages=payload['messages'], filters=payload['filters'], contexts=payload.get('contexts', {}),
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

    def delete_session(self, session_id, principal):
        self.session(session_id, principal)
        if any(active_id == session_id for active_id, _ in self.active_sessions.values()):
            raise ServiceError('session_busy', 'Espera a que termine la respuesta antes de eliminar esta conversación.', 409)
        self.store.delete(session_id, principal.user_id)
        self.sessions.pop(session_id, None)
        return {'deleted': True}

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

    async def postal_records(self,start_date,end_date,family,offset,limit,principal):
        started=time.monotonic()
        status='error'
        try:
            result=await self.tools.postal_records(start_date,end_date,family,offset,limit,principal)
            status='answer'
            return result
        finally:
            self.audit.record(str(uuid4()),status,int((time.monotonic()-started)*1000),user_id=principal.user_id,operation='summary_records',model_version=self.settings.model_version)

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
        if request.edit_message_index is not None:
            index = request.edit_message_index
            if index >= len(session.messages) or session.messages[index]['role'] != 'user':
                raise ServiceError('invalid_edit', 'Selecciona una consulta enviada para editarla.', 422)
            context = session.contexts.get(str(index))
            if context is None:
                context = self.recover_edit_context(session, index)
            context = context or {}
            session.filters = dict(context.get('filters', {}))
            session.last_intent = IntentDecision.model_validate(context['intent']) if context.get('intent') else None
            session.messages = session.messages[:index]
            session.contexts = {key: value for key, value in session.contexts.items() if int(key) < index}
            if index == 0:
                session.title = 'Nueva conversación'
        session.contexts[str(len(session.messages))] = {'filters': dict(session.filters), 'intent': session.last_intent.model_dump(mode='json') if session.last_intent else None}
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
                answer = ChatResponse(request_id=request_id, session_id=session_id, status='answer', answer='Hola. Puedo ayudarte con seguimiento, oficinas, resúmenes y registros de movimientos, cobros y facturación de Correos Bolivia, según tus permisos. Indica tu consulta.')
            elif request.message.strip().lower().strip('¡!¿?. ') in {'qué consultas puedes responder', 'que consultas puedes responder', 'ayuda'}:
                operation = 'capabilities'
                answer = ChatResponse(request_id=request_id, session_id=session_id, status='answer', answer='Según tus permisos, puedo consultar seguimiento por código, oficinas por departamento, contar registros postales por estado, familia o destino y consultar movimientos, cobros y registros de facturación. Puedes indicar «todo octubre», «octubre de 2025», «el mes pasado» o un intervalo de hasta 366 días. Si no indicas año, usaré el actual y lo mostraré en la respuesta. Las tarifas no están habilitadas. Los conteos postales representan registros, no envíos únicos.')
            else:
                async with asyncio.timeout(self.settings.inference_timeout + self.settings.queue_timeout + 15):
                    operation = 'interpretation'
                    session = self.sessions[session_id]
                    confirmed = dict(session.filters)
                    followup = request.message.casefold().strip('¡!¿?. ')
                    categories = self.accounting_categories(request.message)
                    accounting_request = bool(re.search(r'\b(contab\w*|cobros?|cobranzas?|factur\w*)\b',request.message.casefold()))
                    if not session.last_intent and is_period_followup(request.message):
                        previous_topic=next((item['content'] for item in reversed(session.messages[:-1]) if item['role']=='user' and not is_period_followup(item['content'])), '')
                        if re.search(r'\b(contab\w*|cobros?|cobranzas?|factur\w*)\b',previous_topic.casefold()):
                            session.last_intent=IntentDecision(operation='accounting',accounting_categories=self.accounting_categories(previous_topic) or ['movimientos','cobros','facturacion'])
                    family=self.shipment_family(request.message)
                    personnel = self.office_personnel_intent(request.message, session.last_intent)
                    department_followup = self.office_department_followup(request.message, session.last_intent)
                    if department_followup and not department_followup.office_personnel:
                        # Recover the topic in saved chats affected by the previous classifier bug.
                        for item in reversed(session.messages[:-1]):
                            if item['role'] != 'user':
                                continue
                            try:
                                if self.office_department_followup(item['content'], session.last_intent):
                                    continue
                                previous_personnel = self.office_personnel_intent(item['content'], None)
                            except ServiceError:
                                break
                            if previous_personnel and previous_personnel.department:
                                department_followup = department_followup.model_copy(update={'detail': True, 'office_personnel': True})
                            break
                    dimension = self.summary_dimension_followup(request.message)
                    if dimension and session.last_intent and session.last_intent.operation == 'summary':
                        intent = session.last_intent.model_copy(update={'dimension': dimension, 'list_records': False})
                    elif personnel:
                        intent = personnel
                    elif department_followup:
                        intent = department_followup
                    elif self.is_family_followup(request.message):
                        intent=(session.last_intent.model_copy(update={'family':family,'list_records':True}) if session.last_intent and session.last_intent.operation=='summary' else IntentDecision(operation='summary',family=family,list_records=True))
                    elif accounting_request or (categories and session.last_intent and session.last_intent.operation=='accounting'):
                        intent = IntentDecision(operation='accounting',accounting_categories=categories or ['movimientos','cobros','facturacion'])
                        if session.last_intent and session.last_intent.operation=='accounting' and self.is_accounting_followup(request.message):
                            intent=session.last_intent.model_copy(update={'accounting_categories':categories or session.last_intent.accounting_categories})
                    elif is_period_followup(request.message) and session.last_intent and session.last_intent.operation in {'summary','accounting'}:
                        intent = session.last_intent.model_copy()
                    elif self.is_detail_followup(request.message):
                        intent = (session.last_intent.model_copy(update={'detail': True, 'office_personnel': False, 'latest_personnel': False})
                                  if session.last_intent and session.last_intent.operation in {'offices', 'tracking'}
                                  else session.last_intent.model_copy(update={'list_records':True}) if session.last_intent and session.last_intent.operation=='summary'
                                  else IntentDecision(operation='clarify'))
                    elif self.is_unspecified_data_request(request.message):
                        intent = IntentDecision(operation='clarify')
                    elif self.is_bare_postal_request(request.message):
                        intent = IntentDecision(operation='clarify')
                    elif confirmed.get('tracking_code') and followup in {'y su estado', 'su estado', 'el estado de ese envío', 'el estado de ese envio'}:
                        intent = IntentDecision(operation='tracking', tracking_code=confirmed['tracking_code'])
                    else:
                        intent = await self.model.interpret(request.message, context={**confirmed, 'last_operation': session.last_intent.operation if session.last_intent else None, 'last_office_personnel': bool(session.last_intent and session.last_intent.office_personnel), 'last_detail': bool(session.last_intent and session.last_intent.detail)})
                        if intent.operation in {'tracking', 'offices'} and self.requests_details(request.message):
                            intent = intent.model_copy(update={'detail': True})
                    if intent.operation=='summary' and not dimension and re.search(r'\b(registros?|envios?|envíos?|paquetes?)\b',request.message.casefold()) and not re.search(r'\b(cuenta|contar|cuantos|cuántos|conteo|resumen|total)\b',request.message.casefold()):
                        intent=intent.model_copy(update={'list_records':True})
                    operation = intent.operation + ('_details' if intent.detail or intent.office_personnel else '')
                    intent = self.validate_filters(intent, request.message, confirmed)
                    if intent.operation in {'summary','accounting'} and (not intent.start_date or not intent.end_date):
                        session.last_intent=intent
                        answer=ChatResponse(request_id=request_id,session_id=session_id,status='needs_clarification',answer='¿De qué mes o periodo necesitas los registros? Puedes decir «todo octubre», «octubre de 2025» o «el mes pasado».')
                    elif intent.operation in self.tools.supported:
                        result = await self.tools.execute(intent, principal)
                        answer = compose_answer(request_id, session_id, result)
                        session.last_intent = intent if result.rows or intent.operation in {'offices','summary','accounting'} else None
                        session.filters = {key: value for key, value in intent.model_dump().items() if key in {'tracking_code', 'start_date', 'end_date', 'department','family'} and value is not None}
                        session.required_permissions.update({'internal_data', 'summary' if intent.operation=='accounting' else intent.operation})
                        if intent.operation == 'summary' and intent.dimension in {'department', 'office'}:
                            session.required_permissions.add('offices')
                            answer.answer += ' Desglose por destino registrado y su correspondencia exacta con el municipio del directorio; no identifica la oficina responsable del envío. Los destinos sin coincidencia única figuran como «Sin correspondencia».'
                        if ((intent.detail or intent.office_personnel) and intent.operation in {'tracking','offices'}) or intent.operation=='accounting':
                            session.required_permissions.add('personal_data')
                        if intent.operation in {'summary','accounting'}:
                            answer.answer = 'Periodo consultado: '+describe_period(intent.start_date,intent.end_date)+'. '+answer.answer
                            if intent.operation=='summary' and intent.family:
                                labels={'ems':'EMS','certi':'Certificados','ordi':'Ordinarios','contrato':'Contratos','int':'Internacionales'}
                                answer.answer='Familia consultada: '+labels[intent.family]+'. '+answer.answer
                            if intent.operation=='summary' and intent.list_records:
                                answer.record_browser={'start_date':intent.start_date,'end_date':intent.end_date,'family':intent.family}
                                answer.answer+=' Los registros individuales están disponibles más abajo, con botones para recorrer todas las páginas.'
                            if self.settings.data_snapshot and intent.end_date>self.settings.data_snapshot[:10]:
                                answer.answer += ' El respaldo disponible llega al '+self.settings.data_snapshot[:10]+'; no permite confirmar los días posteriores.'
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
            if exc.code in {'period_ambiguous','family_ambiguous'}:
                if 'intent' in locals():
                    session.last_intent=intent
                status='needs_clarification'
                answer=ChatResponse(request_id=request_id,session_id=session_id,status=status,answer=exc.message)
                return answer
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
    def office_departments(message):
        text=' '.join(Conversation.normalized_words(message))
        return [name for name in ('Beni','Chuquisaca','Cochabamba','La Paz','Oruro','Pando','Potosí','Santa Cruz','Tarija') if re.search(r'\b'+re.escape(' '.join(Conversation.normalized_words(name)))+r'\b',text)]

    @staticmethod
    def office_department_followup(message, previous):
        if not previous or previous.operation!='offices':
            return None
        departments=Conversation.office_departments(message)
        if not departments:
            return None
        text=' '.join(Conversation.normalized_words(message))
        for department in departments:
            text=re.sub(r'\b'+re.escape(' '.join(Conversation.normalized_words(department)))+r'\b','',text)
        allowed={'y','de','del','en','el','la','los','las','ahora','ahorita','ahorta','tambien','solo','solamente','dame','muestra','muestrame','quiero','ver','tabla','tablas','lista','listado','por','favor'}
        if not set(text.split())<=allowed:
            return None
        if len(departments)>1:
            raise ServiceError('clarify','Indica un departamento a la vez para continuar la consulta.',422)
        return previous.model_copy(update={'department':departments[0]})

    @staticmethod
    def is_personnel_followup(message):
        words=set(Conversation.normalized_words(message))
        return bool(words & {'personal','empleados','funcionarios','trabajadores','usuarios','ultimo','ultima','reciente','recientes'}) and words <= {'personal','empleados','funcionarios','trabajadores','usuarios','dame','que','hay','en','la','el','los','las','de','del','y','su','sus','esa','ese','esta','este','sucursal','oficina','sucursales','oficinas','muestra','muestrame','lista','listar','quiero','ver','tabla','tablas','por','favor','asignados','asignado','ultimo','ultima','reciente','recientes','registrado','registrada','registrao','datos'}

    @staticmethod
    def office_personnel_intent(message, previous):
        words=set(Conversation.normalized_words(message))
        latest=bool(words & {'ultimo','ultima','reciente','recientes'})
        followup=Conversation.is_personnel_followup(message)
        if not words & {'personal','empleados','funcionarios','trabajadores','usuarios'} and not (latest and followup and previous and previous.office_personnel):
            return None
        departments=Conversation.office_departments(message)
        if not departments and not words & {'sucursal','sucursales','oficina','oficinas'} and not followup:
            return None
        if len(departments)>1:
            raise ServiceError('clarify','Indica un departamento a la vez para consultar el personal de sus sucursales.',422)
        department=departments[0] if departments else previous.department if followup and previous and previous.operation=='offices' else None
        return IntentDecision(operation='offices',department=department,detail=True,office_personnel=True,latest_personnel=latest)

    @staticmethod
    def recover_edit_context(session, index):
        """Recover old turns from saved answers, never from the discarded future."""
        filters, previous, user = {}, None, ''
        for position, message in enumerate(session.messages[:index]):
            if message['role'] == 'user':
                snapshot = session.contexts.get(str(position))
                if snapshot is not None:
                    filters = dict(snapshot.get('filters', {}))
                    previous = IntentDecision.model_validate(snapshot['intent']) if snapshot.get('intent') else None
                user = message['content']
                continue
            if message.get('status') not in {'answer', 'no_results'}:
                continue
            text = message.get('content', '')
            rows = message.get('rows') or []
            columns = set(message.get('columns') or (rows[0] if rows else {}))
            period_label = text.partition('Periodo consultado: ')[2].split('. ', 1)[0]
            browser = message.get('record_browser')
            intent = None
            if period_label or browser:
                period = None
                if browser:
                    period = browser['start_date'], browser['end_date']
                else:
                    # These are the exact calendar labels emitted by describe_period.
                    days = re.findall(r'\b(\d{1,2}) de ([a-z]+) de (\d{4})', period_label)
                    try:
                        if days:
                            dates = [date(int(year), MONTHS.index(month)+1, int(day)) for day, month, year in days]
                            period = dates[0].isoformat(), (dates[-1]+timedelta(days=1)).isoformat()
                        else:
                            period = resolve_period(period_label.split(' (', 1)[0])
                    except (ValueError, ServiceError):
                        pass
                accounting = 'category' in columns or 'Movimientos y cobros' in (message.get('source') or '')
                dimension = next((key for key in ('department', 'office', 'source', 'destination', 'status') if key in columns), 'status')
                family_label = text.partition('Familia consultada: ')[2].split('.', 1)[0]
                intent = IntentDecision(operation='accounting' if accounting else 'summary',
                    start_date=period[0] if period else None, end_date=period[1] if period else None,
                    dimension=dimension, family=browser.get('family') if browser else Conversation.shipment_family(family_label),
                    list_records=bool(browser), accounting_categories=Conversation.accounting_categories(user) or
                    (previous.accounting_categories if previous and previous.operation=='accounting' and Conversation.is_accounting_followup(user) else ['movimientos','cobros','facturacion']))
            elif 'office_id' in columns or {'nombre', 'sucursal'} <= columns or 'Directorio de sucursales' in (message.get('source') or ''):
                departments = Conversation.office_departments(user)
                intent = Conversation.office_personnel_intent(user, previous)
                if intent is None:
                    intent = IntentDecision(operation='offices', department=departments[0] if len(departments)==1 else
                        previous.department if previous and previous.operation=='offices' and Conversation.is_detail_followup(user) else None,
                        detail='details' in columns, office_personnel={'nombre','sucursal'} <= columns)
            elif 'tracking_code' in columns:
                codes = {row.get('tracking_code') for row in rows if row.get('tracking_code')}
                if len(codes)==1:
                    intent = IntentDecision(operation='tracking', tracking_code=next(iter(codes)), detail='details' in columns)
            if intent:
                previous = intent
                filters = {key: value for key, value in intent.model_dump().items() if key in {'tracking_code','start_date','end_date','department','family'} and value is not None}
        return {'filters': filters, 'intent': previous.model_dump(mode='json') if previous else None}

    @staticmethod
    def summary_dimension_followup(message):
        words = set(Conversation.normalized_words(message))
        dimensions = {'departamento': 'department', 'departamentos': 'department', 'oficina': 'office', 'oficinas': 'office', 'sucursal': 'office', 'sucursales': 'office', 'sucursale': 'office', 'estado': 'status', 'estados': 'status', 'destino': 'destination', 'destinos': 'destination', 'familia': 'source', 'familias': 'source', 'tipo': 'source', 'tipos': 'source'}
        # Correct dimension words only; never discard unknown filters or places.
        words = {get_close_matches(word, dimensions, n=1, cutoff=.88)[0] if word not in dimensions and len(word) >= 7 and get_close_matches(word, dimensions, n=1, cutoff=.88) else word for word in words}
        allowed = set(dimensions) | set(('dame por de del el la los las y ahora todas todos toda todo muestra muestrame quiero ver favor '
            'puedes puede podrias podria mostrar mostrarme necesito quisiera saber me lo eso esto esa ese esas esos esta este estas estos '
            'a en entre para segun cada mismo misma mismos mismas tambien solo solamente cuanto cuanta cuantos cuantas corresponde corresponden '
            'desglosa desglosalo desglosar desglosarlo desglosado desglosada desglose detalle detalles detallado detallada '
            'agrupa agrupalo agrupar agruparlo agrupado agrupada agrupacion separa separalo separar separado separada '
            'distribuye distribuyelo distribuido distribuida distribucion divide dividelo dividido dividida '
            'resumen resultado resultados consulta datos cantidad cantidades total totales volumen carga registros envio envios paquete paquetes').split())
        found = {value for word, value in dimensions.items() if word in words}
        return next(iter(found)) if len(found) == 1 and words <= allowed else None

    @staticmethod
    def shipment_family(message):
        words=set(Conversation.normalized_words(message))
        matches=[]
        for family,aliases in [('ems',{'ems'}),('certi',{'certi','certificado','certificados'}),('ordi',{'ordi','ordinario','ordinarios'}),('contrato',{'contrato','contratos'}),('int',{'int','internacional','internacionales'})]:
            if words & aliases:
                matches.append(family)
        if len(matches)>1:
            raise ServiceError('family_ambiguous','Indica una familia a la vez: EMS, certificados, ordinarios, contratos o internacionales.',422)
        return matches[0] if matches else None

    @staticmethod
    def is_family_followup(message):
        words=set(Conversation.normalized_words(message))
        allowed={'de','del','el','la','los','las','y','solo','solamente','tambien','ahora','dame','muestra','muestrame','quiero','ver','datos','registros','envios','paquetes','por','favor','ems','certi','certificado','certificados','ordi','ordinario','ordinarios','contrato','contratos','int','internacional','internacionales'}
        return Conversation.shipment_family(message) is not None and words<=allowed

    @staticmethod
    def accounting_categories(message):
        text=message.casefold()
        return [category for category,pattern in [('movimientos',r'\bmovimientos?\b'),('cobros',r'\b(cobros?|cobranzas?)\b'),('facturacion',r'\bfactur\w*\b')] if re.search(pattern,text)]

    @staticmethod
    def is_accounting_followup(message):
        words=set(Conversation.normalized_words(message))
        return bool(Conversation.accounting_categories(message)) and words <= {'y','los','las','el','la','solo','solamente','movimiento','movimientos','cobro','cobros','cobranzas','facturacion','facturas','datos','de','por','favor'}

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
        words = set(Conversation.normalized_words(message))
        return bool(words & {'completo', 'completos', 'completa', 'completas', 'compelto', 'detalles', 'asociados', 'asociadas'}) or {'todos', 'datos'} <= words or {'toda', 'informacion'} <= words

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
        continuation = Conversation.is_detail_followup(message) or (intent.operation == "summary" and bool(Conversation.summary_dimension_followup(message))) or bool(re.search(r'\b(su estado|ese envío|ese envio|mismo envío|mismo envio|ese código|ese codigo|mismo código|mismo codigo|ese periodo|ese período|mismo periodo|mismo período|esas fechas|mismas fechas)\b', text))
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
        if intent.operation in {'summary','accounting'}:
            period=resolve_period(message,confirmed)
            explicit_dates = re.findall(r'\b\d{4}-\d{2}-\d{2}\b', message)
            new_period = bool(re.search(r'\b(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre|hoy|ayer|semana|mes|año|\d{4})\b', text))
            may_reuse = (continuation or (intent.operation=='accounting' and Conversation.is_accounting_followup(message)) or (intent.operation=='summary' and Conversation.is_family_followup(message))) and not explicit_dates and not new_period
            if intent.operation=='summary':
                explicit_family=Conversation.shipment_family(message)
                if explicit_family and intent.family and intent.family!=explicit_family:
                    raise ServiceError('clarify','Confirma la familia de envíos que necesitas consultar.',422)
                updates['family']=explicit_family or (confirmed.get('family') if continuation or is_period_followup(message) else None)
            for key in ('start_date', 'end_date'):
                if period:
                    updates[key]=period[0 if key=='start_date' else 1]
                    continue
                value = getattr(intent, key) or (confirmed.get(key) if may_reuse else None)
                if value and value not in explicit_dates and not (may_reuse and value == confirmed.get(key)):
                    raise ServiceError('clarify', 'Indica ambas fechas explícitas AAAA-MM-DD, incluida la fecha final exclusiva.', 422)
                updates[key] = value
        if intent.operation == 'offices':
            office_followup = (Conversation.is_detail_followup(message) or (intent.office_personnel and Conversation.is_personnel_followup(message))) and intent.department == confirmed.get('department')
            department_text=' '.join(Conversation.normalized_words(intent.department or ''))
            explicit_department=bool(department_text and re.search(r'\b'+re.escape(department_text)+r'\b',' '.join(Conversation.normalized_words(message))))
            if intent.department and not explicit_department and not office_followup:
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
