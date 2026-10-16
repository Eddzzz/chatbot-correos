import asyncio
import json
from uuid import uuid4
from fastapi import FastAPI, Header, Request
from fastapi.responses import JSONResponse, StreamingResponse
from app.contracts import ChatRequest, ServiceError


def register_routes(app: FastAPI, settings, identity, conversation, audit):
    def principal(authorization):
        return identity.resolve(authorization)

    @app.exception_handler(ServiceError)
    async def service_error(request: Request, exc: ServiceError):
        status = {'clarify': 'needs_clarification', 'forbidden': 'forbidden'}.get(exc.code, 'error')
        return JSONResponse(status_code=exc.status_code, content={'status': status, 'error': {'code': exc.code, 'message': exc.message}, 'request_id': str(uuid4())})

    @app.get('/health')
    async def health():
        return {'status': 'ok'}

    @app.get('/api/config')
    async def config():
        return {'data_mode': 'demo' if settings.demo_mode else 'fixture' if settings.fixture_data else ('postgres' if settings.database_url else 'unconfigured'), 'inference_mode': 'rules' if settings.demo_mode else 'local'}

    @app.get('/api/health')
    async def diagnostic(authorization: str | None = Header(default=None)):
        context = principal(authorization)
        if 'diagnostics' not in context.permissions:
            raise ServiceError('forbidden', 'No tienes permiso para consultar esa información.', 403)
        return {'status': 'ok', 'database_configured': bool(settings.database_url), 'demo': settings.demo_mode, 'inference': 'rules' if settings.demo_mode else 'local', 'dependencies_verified': False}

    @app.get('/api/metrics')
    async def metrics(authorization: str | None = Header(default=None)):
        context = principal(authorization)
        if 'diagnostics' not in context.permissions:
            raise ServiceError('forbidden', 'No tienes permiso para consultar esa información.', 403)
        return {'requests': dict(audit.counts)}

    @app.get('/api/sessions')
    async def sessions(authorization: str | None = Header(default=None)):
        return conversation.list_sessions(principal(authorization))

    @app.get('/api/sessions/{session_id}')
    @app.get('/api/sessions/{session_id}/history')
    async def history(session_id: str, authorization: str | None = Header(default=None)):
        return conversation.history(session_id, principal(authorization))

    @app.post('/api/requests/{request_id}/cancel')
    async def cancel(request_id: str, authorization: str | None = Header(default=None)):
        return conversation.cancel(request_id, principal(authorization))

    @app.post('/api/chat')
    async def chat(body: ChatRequest, authorization: str | None = Header(default=None)):
        context = principal(authorization)
        session_id, _ = conversation.session(body.session_id, context)
        request_id = str(uuid4())
        try:
            return await conversation.handle(body, context, request_id, session_id)
        except asyncio.CancelledError:
            return JSONResponse(status_code=409, content={'request_id': request_id, 'error': {'code': 'cancelled', 'message': 'Consulta cancelada.'}})

    @app.post('/api/chat/stream')
    async def stream(body: ChatRequest, request: Request, authorization: str | None = Header(default=None)):
        context = principal(authorization)
        session_id, _ = conversation.session(body.session_id, context)
        request_id = str(uuid4())

        def event(name, data):
            return 'event: ' + name + '\ndata: ' + json.dumps({'request_id': request_id, **data}, ensure_ascii=False, default=str) + '\n\n'

        async def events():
            task = None
            try:
                yield event('request_started', {'session_id': session_id})
                yield event('status', {'message': 'Interpretando la consulta y comprobando permisos.'})
                task = asyncio.create_task(conversation.handle(body, context, request_id, session_id))
                while not task.done():
                    done, _ = await asyncio.wait({task}, timeout=1)
                    if await request.is_disconnected():
                        task.cancel()
                        return
                    if not done:
                        yield ': keepalive\n\n'
                response = task.result()
                yield event('status', {'message': 'Respuesta verificada.'})
                for offset in range(0, len(response.answer), 160):
                    yield event('answer_chunk', {'text': response.answer[offset:offset + 160]})
                yield event('completed', response.model_dump(mode='json'))
            except asyncio.CancelledError:
                if task and not task.done():
                    task.cancel()
                yield event('error', {'code': 'cancelled', 'message': 'Consulta cancelada.'})
            except ServiceError as exc:
                yield event('error', {'code': exc.code, 'message': exc.message})
            except Exception:
                yield event('error', {'code': 'internal_error', 'message': 'No fue posible completar la consulta.'})
            finally:
                if task and not task.done():
                    task.cancel()
                if task:
                    await asyncio.gather(task, return_exceptions=True)

        return StreamingResponse(events(), media_type='text/event-stream', headers={'Cache-Control': 'no-store', 'X-Accel-Buffering': 'no'})
