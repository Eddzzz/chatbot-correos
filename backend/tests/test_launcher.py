import asyncio
import json
import subprocess
import sys

from uvicorn import Config
from app import run


def test_launcher_uses_psycopg_compatible_event_loop(monkeypatch):
    captured = {}
    monkeypatch.setattr(run.uvicorn, 'run', lambda app, **options: captured.update(options))
    run.main()
    loop = Config('app.main:app', loop=captured['loop']).get_loop_factory()()
    try:
        assert isinstance(loop, asyncio.SelectorEventLoop)
    finally:
        loop.close()


def test_deployment_logging_emits_audit_json():
    script = '''import json, logging.config
from pathlib import Path
from app.audit.public import AuditSink
logging.config.dictConfig(json.loads(Path('../config/logging.json').read_text()))
AuditSink().record('r', 'answer', 1, user_id='operator', operation='tracking', model_version='test')
'''
    result = subprocess.run([sys.executable, '-c', script], check=True, capture_output=True, text=True)
    record = json.loads(result.stderr.strip())
    assert record['event'] == 'chat_completed' and record['user_id'] == 'operator'
