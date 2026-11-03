"""Postgres access. Plain Postgres: works the same against Supabase (demo, cloud)
and a self-hosted Postgres (on-premise). Only DATABASE_URL changes.

A connection pool is used because every voice turn hits the database several
times; opening a new TLS connection per request would add audible latency.
"""

from __future__ import annotations

import os
import threading
from contextlib import contextmanager
from typing import Iterator

import psycopg
from psycopg_pool import ConnectionPool

_pool: ConnectionPool | None = None
_lock = threading.Lock()


def database_url() -> str:
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL is not set")
    return url


def pool() -> ConnectionPool:
    global _pool
    with _lock:
        if _pool is None:
            _pool = ConnectionPool(
                database_url(),
                min_size=1,
                max_size=int(os.environ.get("DB_POOL_MAX", "5")),
                # Supabase's transaction pooler (Supavisor) does not support
                # server-side prepared statements; disabling them is harmless elsewhere.
                kwargs={"prepare_threshold": None, "connect_timeout": 5},
                open=True,
            )
        return _pool


@contextmanager
def connect() -> Iterator[psycopg.Connection]:
    with pool().connection() as conn:
        yield conn


def is_healthy() -> bool:
    try:
        with pool().connection(timeout=3) as conn:
            conn.execute("select 1")
        return True
    except Exception:  # pool timeout, network or auth error: the service is degraded either way
        return False
