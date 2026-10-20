"""Durable credentials, opaque sessions and login throttling for browser users."""
import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path


class AuthStore:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.executescript('''
                CREATE TABLE IF NOT EXISTS auth_users (
                    user_id TEXT PRIMARY KEY, username TEXT NOT NULL UNIQUE,
                    display_name TEXT NOT NULL, password_hash TEXT NOT NULL,
                    permissions TEXT NOT NULL, scope TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS auth_sessions (
                    token_hash TEXT PRIMARY KEY, user_id TEXT NOT NULL,
                    expires_at REAL NOT NULL,
                    FOREIGN KEY(user_id) REFERENCES auth_users(user_id) ON DELETE CASCADE);
                CREATE INDEX IF NOT EXISTS auth_sessions_expiry ON auth_sessions(expires_at);
                CREATE TABLE IF NOT EXISTS auth_attempts (
                    key TEXT PRIMARY KEY, started_at REAL NOT NULL, attempts INTEGER NOT NULL);
            ''')

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=10)
        db.row_factory = sqlite3.Row
        db.execute('PRAGMA foreign_keys=ON')
        try:
            with db:
                yield db
        finally:
            db.close()

    def create_user(self, user_id, username, display_name, password_hash, permissions, scope):
        with self.connect() as db:
            db.execute('INSERT INTO auth_users VALUES (?,?,?,?,?,?)',
                       (user_id, username, display_name, password_hash, json.dumps(sorted(permissions)), json.dumps(scope)))

    def user(self, username):
        with self.connect() as db:
            row = db.execute('SELECT * FROM auth_users WHERE username=?', (username,)).fetchone()
        return dict(row) if row else None

    def users(self):
        with self.connect() as db:
            return [dict(row) for row in db.execute('SELECT user_id,username,display_name,permissions,scope FROM auth_users ORDER BY username')]

    def reset_password(self, username, password_hash):
        with self.connect() as db:
            row = db.execute('SELECT user_id FROM auth_users WHERE username=?', (username,)).fetchone()
            if not row:
                raise ValueError('El usuario no existe.')
            db.execute('UPDATE auth_users SET password_hash=? WHERE user_id=?', (password_hash, row['user_id']))
            db.execute('DELETE FROM auth_sessions WHERE user_id=?', (row['user_id'],))

    def consume_attempt(self, keys, now, window, maximum):
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            db.execute('DELETE FROM auth_attempts WHERE started_at<=?', (now - window,))
            for key in keys:
                row = db.execute('SELECT attempts FROM auth_attempts WHERE key=?', (key,)).fetchone()
                if row and row['attempts'] >= maximum:
                    return False
            for key in keys:
                db.execute('''INSERT INTO auth_attempts VALUES (?,?,1)
                    ON CONFLICT(key) DO UPDATE SET attempts=attempts+1''', (key, now))
        return True

    def create_session(self, token_hash, user_id, expires_at, now, expected_password_hash):
        with self.connect() as db:
            db.execute('DELETE FROM auth_sessions WHERE expires_at<=?', (now,))
            inserted = db.execute('''INSERT INTO auth_sessions (token_hash,user_id,expires_at)
                SELECT ?,user_id,? FROM auth_users WHERE user_id=? AND password_hash=?''',
                (token_hash, expires_at, user_id, expected_password_hash)).rowcount
        return inserted == 1

    def session_user(self, token_hash, now):
        with self.connect() as db:
            row = db.execute('''SELECT u.* FROM auth_users u JOIN auth_sessions s ON u.user_id=s.user_id
                WHERE s.token_hash=? AND s.expires_at>?''', (token_hash, now)).fetchone()
        return dict(row) if row else None

    def revoke(self, token_hash):
        with self.connect() as db:
            db.execute('DELETE FROM auth_sessions WHERE token_hash=?', (token_hash,))
