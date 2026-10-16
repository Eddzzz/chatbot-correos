from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.api import register_routes
from app.audit.public import AuditSink
from app.conversation.public import Conversation
from app.data_access.infrastructure import DemoReader, PostgresReader, UnconfiguredReader
from app.identity.public import IdentityResolver
from app.inference.public import DemoInterpreter, LocalLanguageModel
from app.operations.public import ToolRegistry
from app.settings import Settings


def create_app(settings: Settings | None = None, *, reader=None, model=None):
    settings = settings or Settings()
    identity = IdentityResolver(settings.identities_json)
    reader = reader or (DemoReader() if settings.demo_mode else PostgresReader(settings) if settings.database_url else UnconfiguredReader())
    model = model or (DemoInterpreter() if settings.demo_mode else LocalLanguageModel(settings))
    audit = AuditSink()
    conversation = Conversation(settings, model, ToolRegistry(reader), audit)

    @asynccontextmanager
    async def lifespan(app):
        if hasattr(reader, 'open'):
            await reader.open()
        yield
        if hasattr(reader, 'close'):
            await reader.close()
        if hasattr(model, 'close'):
            await model.close()

    app = FastAPI(title='Correos Bolivia · consulta interna', lifespan=lifespan, docs_url=None, redoc_url=None)
    app.state.conversation = conversation
    register_routes(app, settings, identity, conversation, audit)
    return app
