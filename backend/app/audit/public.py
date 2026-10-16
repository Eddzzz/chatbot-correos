import json
import logging
from collections import Counter


class AuditSink:
    def __init__(self):
        self.counts = Counter()
        self.logger = logging.getLogger('chatbot.audit')

    def record(self, request_id: str, outcome: str, duration_ms: int, *, user_id: str, operation: str, model_version: str):
        self.counts[outcome] += 1
        self.logger.info(json.dumps({'event': 'chat_completed', 'request_id': request_id, 'user_id': user_id, 'operation': operation, 'model_version': model_version, 'outcome': outcome, 'duration_ms': duration_ms}))
