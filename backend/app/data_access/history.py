"""Local durable history; authentication and ownership remain server-side."""
import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path


class HistoryStore:
    def __init__(self, path: str):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as connection:
            connection.execute('''CREATE TABLE IF NOT EXISTS chats (
                id TEXT PRIMARY KEY, owner TEXT NOT NULL, title TEXT NOT NULL,
                updated_at TEXT NOT NULL, permissions TEXT NOT NULL, scope TEXT NOT NULL,
                payload TEXT NOT NULL)''')
            connection.execute('CREATE INDEX IF NOT EXISTS chats_owner_updated ON chats(owner, updated_at DESC)')

    @contextmanager
    def connect(self):
        connection = sqlite3.connect(self.path, timeout=10)
        connection.row_factory = sqlite3.Row
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def save(self, chat_id, session):
        payload = {'messages': session.messages, 'filters': session.filters,
                   'last_intent': session.last_intent.model_dump(mode='json') if session.last_intent else None}
        with self.connect() as connection:
            connection.execute('''INSERT INTO chats VALUES (?,?,?,?,?,?,?)
                ON CONFLICT(id) DO UPDATE SET title=excluded.title, updated_at=excluded.updated_at,
                permissions=excluded.permissions, scope=excluded.scope, payload=excluded.payload
                WHERE chats.owner=excluded.owner''',
                (chat_id, session.owner, session.title, session.updated_at,
                 json.dumps(sorted(session.required_permissions)), json.dumps(session.scope),
                 json.dumps(payload, ensure_ascii=False)))

    def load(self, chat_id, owner):
        with self.connect() as connection:
            row = connection.execute('SELECT * FROM chats WHERE id=? AND owner=?', (chat_id, owner)).fetchone()
        return dict(row) if row else None

    def list(self, principal):
        with self.connect() as connection:
            rows = connection.execute('SELECT id,title,updated_at,permissions,scope FROM chats WHERE owner=? ORDER BY updated_at DESC,id', (principal.user_id,)).fetchall()
        return [{'session_id': row['id'], 'title': row['title'], 'updated_at': row['updated_at']}
                for row in rows if set(json.loads(row['permissions'])) <= principal.permissions
                and tuple(json.loads(row['scope'])) == principal.scope]

    def count(self, owner):
        with self.connect() as connection:
            return connection.execute('SELECT count(*) FROM chats WHERE owner=?', (owner,)).fetchone()[0]
