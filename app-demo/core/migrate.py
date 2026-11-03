"""Minimal migration runner: applies migrations/*.sql in name order, once each.

Works the same against Supabase and a self-hosted Postgres.
Usage: python -m core.migrate
"""

from __future__ import annotations

import sys
from pathlib import Path

import psycopg

from core.db import database_url

MIGRATIONS_DIR = Path(__file__).resolve().parent.parent / "migrations"

# Serializes concurrent runs (e.g. two containers booting at once).
_LOCK_ID = 727_001


def pending(applied: set[str], directory: Path = MIGRATIONS_DIR) -> list[Path]:
    return [p for p in sorted(directory.glob("*.sql")) if p.name not in applied]


def run(directory: Path = MIGRATIONS_DIR) -> list[str]:
    done: list[str] = []
    with psycopg.connect(database_url(), prepare_threshold=None, autocommit=True) as conn:
        conn.execute("select pg_advisory_lock(%s)", (_LOCK_ID,))
        try:
            conn.execute(
                "create table if not exists schema_migrations ("
                " name text primary key, applied_at timestamptz not null default now())"
            )
            conn.execute("alter table schema_migrations enable row level security")
            applied = {row[0] for row in conn.execute("select name from schema_migrations")}
            for path in pending(applied, directory):
                with conn.transaction():
                    conn.execute(path.read_text(encoding="utf-8"))
                    conn.execute("insert into schema_migrations (name) values (%s)", (path.name,))
                done.append(path.name)
        finally:
            conn.execute("select pg_advisory_unlock(%s)", (_LOCK_ID,))
    return done


if __name__ == "__main__":
    applied_now = run()
    print("migrations applied:", ", ".join(applied_now) if applied_now else "none (up to date)")
    sys.exit(0)
