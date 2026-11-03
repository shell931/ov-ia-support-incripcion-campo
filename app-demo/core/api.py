"""Puertos HTTP del núcleo. El voice-agent y la consola solo conocen esto."""

from __future__ import annotations

from fastapi import FastAPI, Response

from core import db
from core.engine import Motor, cargar_flujos

app = FastAPI(title="Núcleo — soporte inscripción en campo")
motor = Motor(cargar_flujos())  # falla al arrancar si un YAML es inválido: mejor que fallar en una llamada


@app.get("/salud")
def salud(response: Response) -> dict:
    base_ok = db.salud()
    if not base_ok:
        response.status_code = 503
    return {"estado": "ok" if base_ok else "degradado", "postgres": base_ok, "flujos": sorted(motor.flujos)}
