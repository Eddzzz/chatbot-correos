import asyncio
import sys
import pytest


@pytest.fixture(autouse=True)
def isolated_chat_history(tmp_path, monkeypatch):
    monkeypatch.setenv('CHATBOT_HISTORY_PATH', str(tmp_path / 'history.sqlite3'))


@pytest.fixture(scope='session')
def event_loop_policy():
    return asyncio.WindowsSelectorEventLoopPolicy() if sys.platform == 'win32' else asyncio.DefaultEventLoopPolicy()
