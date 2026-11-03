"""Guards on the SQL migrations (no database needed)."""

from __future__ import annotations

import re
from pathlib import Path

from core.migrate import MIGRATIONS_DIR, pending

SQL = "\n".join(p.read_text(encoding="utf-8") for p in sorted(MIGRATIONS_DIR.glob("*.sql")))


def test_every_table_has_row_level_security():
    # On Supabase, a table in "public" without RLS is readable through its REST API.
    tables = set(re.findall(r"create table if not exists (\w+)", SQL))
    secured = set(re.findall(r"alter table (\w+)\s+enable row level security", SQL))
    assert tables, "no tables found"
    assert tables <= secured, f"tables without RLS: {tables - secured}"


def test_no_column_stores_a_raw_id_number():
    columns = set(re.findall(r"^\s+(\w*id_number\w*)\s", SQL, re.MULTILINE))
    assert columns == {"masked_id_number"}


def test_pending_skips_applied_and_keeps_order(tmp_path: Path):
    for name in ["002_b.sql", "001_a.sql", "003_c.sql"]:
        (tmp_path / name).write_text("select 1;")
    assert [p.name for p in pending({"002_b.sql"}, tmp_path)] == ["001_a.sql", "003_c.sql"]
