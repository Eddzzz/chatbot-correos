from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix='CHATBOT_', env_file='.env', extra='ignore')
    database_url: str = ''
    identities_json: str = '{}'
    demo_mode: bool = False
    fixture_data: bool = False
    data_snapshot: str = Field(default='', max_length=40)
    llama_url: str = 'http://127.0.0.1:8081/v1'
    llama_model: str = 'local'
    model_version: str = 'unverified'
    inference_timeout: float = Field(default=60, gt=0, le=300)
    queue_timeout: float = Field(default=15, gt=0, le=60)
    queue_size: int = Field(default=4, ge=0, le=32)
    session_ttl: int = Field(default=1800, ge=60, le=86400)
    max_sessions: int = Field(default=100, ge=1, le=1000)
    history_path: str = ''
    auth_path: str = ''
    auth_session_ttl: int = Field(default=43200, ge=60, le=2592000)
    auth_cookie_secure: bool = False
    auth_allowed_origins: list[str] = []
    auth_login_max_attempts: int = Field(default=10, ge=1, le=100)
    auth_login_window: int = Field(default=300, ge=10, le=3600)
    statement_timeout_ms: int = Field(default=3000, ge=100, le=10000)
    max_rows: int = Field(default=100, ge=1, le=500)
    max_result_bytes: int = Field(default=65536, ge=1024, le=262144)
