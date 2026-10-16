from datetime import datetime
from typing import Any, Literal
from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    model_config = ConfigDict(extra='forbid')


class ChatRequest(StrictModel):
    message: str = Field(min_length=1, max_length=2000)
    session_id: str | None = Field(default=None, max_length=64, pattern=r'^[a-f0-9-]+$')


class AccessContext(StrictModel):
    user_id: str
    permissions: frozenset[str] = frozenset()
    scope: tuple[str, ...] = ()


class IntentDecision(StrictModel):
    operation: Literal['tracking', 'offices', 'summary', 'rates', 'outside', 'clarify']
    tracking_code: str | None = Field(default=None, max_length=40, pattern=r'^[A-Za-z0-9-]+$')
    department: str | None = Field(default=None, max_length=80)
    start_date: str | None = Field(default=None, pattern=r'^[0-9]{4}-[0-9]{2}-[0-9]{2}$')
    end_date: str | None = Field(default=None, pattern=r'^[0-9]{4}-[0-9]{2}-[0-9]{2}$')
    dimension: Literal['source', 'status', 'destination'] = 'status'
    detail: bool = False


class Evidence(StrictModel):
    source: str
    queried_at: datetime
    row_count: int
    truncated: bool = False


class ChatResponse(StrictModel):
    request_id: str
    session_id: str
    status: Literal['answer', 'out_of_scope', 'unsupported', 'needs_clarification', 'forbidden', 'no_results', 'error']
    answer: str
    evidence: list[Evidence] = []
    rows: list[dict[str, Any]] = []
    columns: list[str] = []
    source: str | None = None
    queried_at: datetime | None = None


class ServiceError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 503):
        self.code, self.message, self.status_code = code, message, status_code
        super().__init__(code)
