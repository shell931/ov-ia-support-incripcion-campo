"""Puerto de persistencia de sesiones y sus dos adaptadores.

- `SesionesPostgres`: el real (demo, piloto y local).
- `SesionesEnMemoria`: para tests; no necesita base de datos.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from psycopg.types.json import Jsonb

from core import db
from core.engine import Estado


@dataclass(frozen=True)
class Sesion:
    id: str
    telefono: str
    estado: Estado
    cedula_enmascarada: str | None = None


class Sesiones(Protocol):
    def obtener(self, sesion_id: str) -> Sesion | None: ...

    def guardar(self, sesion: Sesion) -> None: ...

    def evento(self, sesion_id: str, tipo: str, datos: dict[str, Any]) -> None: ...


class SesionesEnMemoria:
    def __init__(self) -> None:
        self.sesiones: dict[str, Sesion] = {}
        self.eventos: list[tuple[str, str, dict[str, Any]]] = []

    def obtener(self, sesion_id: str) -> Sesion | None:
        return self.sesiones.get(sesion_id)

    def guardar(self, sesion: Sesion) -> None:
        self.sesiones[sesion.id] = sesion

    def evento(self, sesion_id: str, tipo: str, datos: dict[str, Any]) -> None:
        self.eventos.append((sesion_id, tipo, datos))


class SesionesPostgres:
    def obtener(self, sesion_id: str) -> Sesion | None:
        with db.conectar() as conn:
            fila = conn.execute(
                "select telefono, estado, cedula_enmascarada from sesiones where id = %s",
                (sesion_id,),
            ).fetchone()
        if fila is None:
            return None
        telefono, estado, cedula = fila
        return Sesion(sesion_id, telefono, Estado.desde_dict(estado), cedula)

    def guardar(self, sesion: Sesion) -> None:
        with db.conectar() as conn:
            conn.execute(
                """
                insert into sesiones (id, telefono, estado, cedula_enmascarada)
                values (%s, %s, %s, %s)
                on conflict (id) do update set
                    telefono = excluded.telefono,
                    estado = excluded.estado,
                    cedula_enmascarada = excluded.cedula_enmascarada,
                    actualizada_en = now()
                """,
                (sesion.id, sesion.telefono, Jsonb(sesion.estado.a_dict()), sesion.cedula_enmascarada),
            )

    def evento(self, sesion_id: str, tipo: str, datos: dict[str, Any]) -> None:
        with db.conectar() as conn:
            conn.execute(
                "insert into eventos (sesion_id, tipo, datos) values (%s, %s, %s)",
                (sesion_id, tipo, Jsonb(datos)),
            )
