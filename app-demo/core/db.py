"""Acceso a Postgres. Postgres plano: nada de servicios propietarios de un proveedor."""

from __future__ import annotations

import os

import psycopg


def database_url() -> str:
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError("Falta DATABASE_URL")
    return url


def conectar() -> psycopg.Connection:
    return psycopg.connect(database_url(), connect_timeout=3)


def salud() -> bool:
    try:
        with conectar() as conn:
            conn.execute("select 1")
        return True
    except psycopg.Error:
        return False
