from app.audit.public import AuditSink
from app.contracts import AccessContext, ChatRequest, IntentDecision
from app.conversation.public import Conversation
from app.data_access.infrastructure import DemoReader
from app.operations.public import ToolRegistry
from app.settings import Settings


async def test_explicit_status_followup_uses_authorized_confirmed_tracking():
    class UncertainModel:
        async def interpret(self, message, context=None):
            return IntentDecision(operation='outside')

    principal = AccessContext(user_id='operator', permissions=frozenset({'internal_data', 'tracking'}), scope=('global_internal',))
    conversation = Conversation(Settings(), UncertainModel(), ToolRegistry(DemoReader()), AuditSink())
    session_id, session = conversation.session(None, principal)
    session.filters['tracking_code'] = 'DEMO123BO'
    answer = await conversation.handle(ChatRequest(message='¿Y su estado?'), principal, 'r', session_id)
    assert answer.status == 'answer'
    assert answer.rows[0]['tracking_code'] == 'DEMO123BO'
