"""Single-worker launcher: Psycopg async requires a selector loop on Windows."""
import asyncio
from pathlib import Path
import uvicorn


def selector_loop():
    return asyncio.SelectorEventLoop()


def main():
    uvicorn.run('app.main:app', host='127.0.0.1', port=8000, workers=1, loop='app.run:selector_loop',
                log_config=str(Path(__file__).resolve().parents[2] / 'config/logging.json'))


if __name__ == '__main__':
    main()
