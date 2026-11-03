"""Postgres access. Plain Postgres: no vendor-specific services."""

from __future__ import annotations

import os

import psycopg


def database_url() -> str:
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL is not set")
    return url


def connect() -> psycopg.Connection:
    return psycopg.connect(database_url(), connect_timeout=3)


def is_healthy() -> bool:
    try:
        with connect() as conn:
            conn.execute("select 1")
        return True
    except (psycopg.Error, RuntimeError):
        return False
