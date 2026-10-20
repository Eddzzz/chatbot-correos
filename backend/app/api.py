import asyncio
import json
from uuid import uuid4
from typing import Literal
from fastapi import FastAPI, Header, Request, Response, Path, Query
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.exceptions import RequestValidationError
from fastapi.exception_handlers import request_validation_exception_handler
from app.contracts import ChatRequest, ServiceError, StrictModel
from app.identity.public import COOKIE_NAME
from pydantic import Field


class LoginRequest(StrictModel):
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=1024)


def register_routes(app: FastAPI, settings, identity, conversation, audit):
    def principal(authorization, request):
        return identity.resolve(authorization, request)

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc: RequestValidationError):
        if request.url.path == '/api/auth/login':
            return JSONResponse(status_code=422, headers={'Cache-Control': 'no-store'}, content={
                'error': {'code': 'invalid_credentials', 'message': 'Introduce un usuario y una contraseña válidos.'}})
        return await request_validation_exception_handler(request, exc)

    @app.exception_handler(ServiceError)
    async def service_error(request: Request, exc: ServiceError):
        status = {'clarify': 'needs_clarification', 'forbidden': 'forbidden'}.get(exc.code, 'error')
        return JSONResponse(status_code=exc.status_code, headers={'Cache-Control': 'no-store'}, content={'status': status, 'error': {'code': exc.code, 'message': exc.message}, 'request_id': str(uuid4())})

    @app.post('/api/auth/login')
    async def login(body: LoginRequest, request: Request, response: Response):
        auth = identity.browser_auth
        auth.check_origin(request)
        token, user = await asyncio.to_thread(auth.login, body.username, body.password, request.client.host if request.client else 'unknown')
        auth.logout(request.cookies.get(COOKIE_NAME))
        response.set_cookie(COOKIE_NAME, token, max_age=settings.auth_session_ttl,
                            httponly=True, secure=settings.auth_cookie_secure, samesite='strict', path='/api')
        response.headers['Cache-Control'] = 'no-store'
        return {'user': user}

    @app.get('/api/auth/me')
    async def me(request: Request, response: Response):
        response.headers['Cache-Control'] = 'no-store'
        auth = identity.browser_auth
        return {'user': auth.public_user(auth.user(request.cookies.get(COOKIE_NAME)))}

    @app.post('/api/auth/logout')
    async def logout(request: Request, response: Response):
        auth = identity.browser_auth
        auth.check_origin(request)
        auth.logout(request.cookies.get(COOKIE_NAME))
        response.delete_cookie(COOKIE_NAME, path='/api', secure=settings.auth_cookie_secure, httponly=True, samesite='strict')
        response.headers['Cache-Control'] = 'no-store'
        return {'logged_out': True}

    @app.get('/health')
    async def health():
        return {'status': 'ok'}

    @app.get('/api/config')
    async def config():
        result = {'data_mode': 'demo' if settings.demo_mode else 'fixture' if settings.fixture_data else ('postgres' if settings.database_url else 'unconfigured'), 'inference_mode': 'rules' if settings.demo_mode else 'local'}
        if settings.data_snapshot and not settings.demo_mode and not settings.fixture_data:
            result['data_snapshot'] = settings.data_snapshot
        return result

    @app.get('/api/health')
    async def diagnostic(request: Request, authorization: str | None = Header(default=None)):
        context = principal(authorization, request)
        if 'diagnostics' not in context.permissions:
            raise ServiceError('forbidden', 'No tienes permiso para consultar esa información.', 403)
        return {'status': 'ok', 'database_configured': bool(settings.database_url), 'demo': settings.demo_mode, 'inference': 'rules' if settings.demo_mode else 'local', 'dependencies_verified': False}

    @app.get('/api/metrics')
    async def metrics(request: Request, authorization: str | None = Header(default=None)):
        context = principal(authorization, request)
        if 'diagnostics' not in context.permissions:
            raise ServiceError('forbidden', 'No tienes permiso para consultar esa información.', 403)
        return {'requests': dict(audit.counts)}

    @app.get('/api/sessions')
    async def sessions(request: Request, response: Response, authorization: str | None = Header(default=None)):
        response.headers['Cache-Control'] = 'no-store'
        return conversation.list_sessions(principal(authorization, request))

    @app.get('/api/offices/{office_id}/relations')
    async def office_tables(request: Request, office_id: int = Path(gt=0), authorization: str | None = Header(default=None)):
        return await conversation.office_related_tables(office_id, principal(authorization, request))

    @app.get('/api/postal-records')
    async def postal_records(request: Request, response:Response,start_date:str=Query(pattern=r'^\d{4}-\d{2}-\d{2}$'),end_date:str=Query(pattern=r'^\d{4}-\d{2}-\d{2}$'),family:Literal['ems','certi','ordi','contrato','int']|None=None,offset:int=Query(default=0,ge=0,le=10000000),limit:int=Query(default=10,ge=1,le=20),authorization:str|None=Header(default=None)):
        response.headers['Cache-Control']='no-store'
        return await conversation.postal_records(start_date,end_date,family,offset,limit,principal(authorization, request))

    @app.get('/api/offices/{office_id}/relations/{table_name}')
    async def office_records(request: Request, office_id: int = Path(gt=0), table_name: str = Path(pattern=r'^[a-z_]+$', max_length=80), offset: int = Query(default=0, ge=0, le=10000000), limit: int = Query(default=10, ge=1, le=20), authorization: str | None = Header(default=None)):
        return await conversation.office_related_records(office_id, table_name, offset, limit, principal(authorization, request))

    @app.get('/api/sessions/{session_id}')
    @app.get('/api/sessions/{session_id}/history')
    async def history(request: Request, session_id: str, response: Response, authorization: str | None = Header(default=None)):
        response.headers['Cache-Control'] = 'no-store'
        return conversation.history(session_id, principal(authorization, request))

    @app.delete('/api/sessions/{session_id}')
    async def delete_session(request: Request, session_id: str, response: Response, authorization: str | None = Header(default=None)):
        response.headers['Cache-Control'] = 'no-store'
        return conversation.delete_session(session_id, principal(authorization, request))

    @app.post('/api/requests/{request_id}/cancel')
    async def cancel(request: Request, request_id: str, authorization: str | None = Header(default=None)):
        return conversation.cancel(request_id, principal(authorization, request))

    @app.post('/api/chat')
    async def chat(request: Request, body: ChatRequest, authorization: str | None = Header(default=None)):
        context = principal(authorization, request)
        session_id, _ = conversation.session(body.session_id, context)
        request_id = str(uuid4())
        try:
            return await conversation.handle(body, context, request_id, session_id)
        except asyncio.CancelledError:
            return JSONResponse(status_code=409, content={'request_id': request_id, 'error': {'code': 'cancelled', 'message': 'Consulta cancelada.'}})

    @app.post('/api/chat/stream')
    async def stream(body: ChatRequest, request: Request, authorization: str | None = Header(default=None)):
        context = principal(authorization, request)
        session_id, _ = conversation.session(body.session_id, context)
        request_id = str(uuid4())

        def event(name, data):
            return 'event: ' + name + '\ndata: ' + json.dumps({'request_id': request_id, **data}, ensure_ascii=False, default=str) + '\n\n'

        async def events():
            task = None
            def validate_session():
                if not authorization or not authorization.startswith('Bearer '):
                    identity.browser_auth.user(request.cookies.get(COOKIE_NAME))
            try:
                validate_session()
                yield event('request_started', {'session_id': session_id})
                yield event('status', {'message': 'Interpretando la consulta y comprobando permisos.'})
                task = asyncio.create_task(conversation.handle(body, context, request_id, session_id))
                while not task.done():
                    done, _ = await asyncio.wait({task}, timeout=1)
                    validate_session()
                    if await request.is_disconnected():
                        task.cancel()
                        return
                    if not done:
                        yield ': keepalive\n\n'
                response = task.result()
                validate_session()
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
