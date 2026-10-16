import asyncio
import sys
import pytest


@pytest.fixture(scope='session')
def event_loop_policy():
    return asyncio.WindowsSelectorEventLoopPolicy() if sys.platform == 'win32' else asyncio.DefaultEventLoopPolicy()
