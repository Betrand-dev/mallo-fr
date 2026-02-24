"""
Database support for Mallo using SQLAlchemy Core.
"""

from contextlib import contextmanager

try:
    from sqlalchemy import create_engine, text
except Exception:  # pragma: no cover - handled at runtime
    create_engine = None
    text = None


class Database:
    """
    Minimal SQLAlchemy Core database wrapper.
    """

    def __init__(self, url: str, **engine_kwargs):
        if create_engine is None:
            raise RuntimeError(
                "SQLAlchemy is required for database support. "
                "Install it with: pip install sqlalchemy"
            )
        self.url = url
        self.engine = create_engine(url, future=True, **engine_kwargs)

    def execute(self, sql: str, params=None):
        """
        Execute write or generic SQL in a transaction.
        """
        params = params or {}
        with self.engine.begin() as conn:
            return conn.execute(text(sql), params)

    def fetchone(self, sql: str, params=None):
        """
        Execute a SELECT and return one row as dict (or None).
        """
        params = params or {}
        with self.engine.connect() as conn:
            result = conn.execute(text(sql), params)
            row = result.mappings().first()
            return dict(row) if row else None

    def fetchall(self, sql: str, params=None):
        """
        Execute a SELECT and return all rows as dict list.
        """
        params = params or {}
        with self.engine.connect() as conn:
            result = conn.execute(text(sql), params)
            return [dict(row) for row in result.mappings().all()]

    @contextmanager
    def transaction(self):
        """
        Transaction context manager.
        """
        with self.engine.begin() as conn:
            yield conn

    def close(self):
        """
        Dispose underlying SQLAlchemy engine.
        """
        self.engine.dispose()
