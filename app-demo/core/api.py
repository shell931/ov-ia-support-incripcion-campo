"""Puertos HTTP del núcleo. El voice-agent y la consola solo conocen esto."""

from __future__ import annotations

from typing import Literal

from fastapi import Depends, FastAPI, HTTPException, Response
from pydantic import BaseModel, Field

from core import db
from core.engine import Motor, Resultado, TransicionInvalida, cargar_flujos, etiqueta_desde_dtmf
from core.masking import enmascarar_cedula, normalizar_cedula
from core.sesiones import Sesion, Sesiones, SesionesPostgres

app = FastAPI(title="Núcleo — soporte inscripción en campo")
motor = Motor(cargar_flujos())  # falla al arrancar si un YAML es inválido: mejor que fallar en una llamada

_sesiones_postgres = SesionesPostgres()


def obtener_sesiones() -> Sesiones:
    """Inyección del adaptador de persistencia; los tests lo reemplazan por uno en memoria."""
    return _sesiones_postgres


Etiqueta = Literal["inicio", "si", "no", "no_entendi", "persona", "esperar"]


class PedidoPaso(BaseModel):
    sesion_id: str = Field(min_length=1, max_length=128)
    telefono: str = Field(min_length=1, max_length=32)
    etiqueta: Etiqueta
    flujo: str | None = None  # obligatorio con etiqueta "inicio"
    dtmf: str | None = Field(default=None, max_length=32)  # teclas marcadas; tiene prioridad sobre la etiqueta


class RespuestaPaso(BaseModel):
    paso_id: str
    texto: str
    espera_activa: bool
    pide_dtmf: bool
    modo_teclado: bool
    fin: bool
    crear_caso: bool
    destino: str | None
    prioridad: str | None
    pasos_intentados: list[str]


def _respuesta(r: Resultado) -> RespuestaPaso:
    return RespuestaPaso(
        paso_id=r.paso.id,
        texto=r.paso.texto,
        espera_activa=r.paso.espera_activa,
        pide_dtmf=r.paso.pide_dtmf,
        modo_teclado=r.modo_teclado,
        fin=r.fin,
        crear_caso=r.crear_caso,
        destino=r.paso.destino,
        prioridad=r.paso.prioridad,
        pasos_intentados=list(r.estado.historial),
    )


@app.get("/salud")
def salud(response: Response) -> dict:
    base_ok = db.salud()
    if not base_ok:
        response.status_code = 503
    return {"estado": "ok" if base_ok else "degradado", "postgres": base_ok, "flujos": sorted(motor.flujos)}


@app.post("/siguiente-paso", response_model=RespuestaPaso)
def siguiente_paso(pedido: PedidoPaso, sesiones: Sesiones = Depends(obtener_sesiones)) -> RespuestaPaso:
    if pedido.etiqueta == "inicio":
        if not pedido.flujo:
            raise HTTPException(422, "etiqueta 'inicio' requiere 'flujo'")
        if pedido.flujo not in motor.flujos:
            raise HTTPException(422, f"flujo desconocido '{pedido.flujo}'")
        r = motor.iniciar(pedido.flujo)
        sesiones.guardar(Sesion(pedido.sesion_id, pedido.telefono, r.estado))
        sesiones.evento(pedido.sesion_id, "inicio", {"flujo": pedido.flujo, "paso": r.paso.id})
        return _respuesta(r)

    sesion = sesiones.obtener(pedido.sesion_id)
    if sesion is None:
        raise HTTPException(404, "sesión inexistente; empezar con etiqueta 'inicio'")

    actual = motor.actual(sesion.estado)
    etiqueta: str = pedido.etiqueta
    cedula = sesion.cedula_enmascarada
    datos_evento: dict = {"paso": actual.paso.id, "etiqueta": pedido.etiqueta}

    if pedido.dtmf is not None:
        if actual.paso.pide_dtmf:
            # Paso que pide la cédula: si es válida se guarda ENMASCARADA y se avanza.
            digitos = normalizar_cedula(pedido.dtmf)
            etiqueta = "si" if digitos else "no_entendi"
            if digitos:
                cedula = enmascarar_cedula(digitos)
            datos_evento["dtmf"] = "cedula_valida" if digitos else "cedula_invalida"  # nunca la cédula
        else:
            etiqueta = etiqueta_desde_dtmf(pedido.dtmf)
            datos_evento["dtmf"] = pedido.dtmf[:1]
    elif actual.paso.pide_dtmf and etiqueta == "si":
        # La cédula solo entra por teclado: un "sí" hablado no la reemplaza.
        etiqueta = "no_entendi"

    try:
        r = motor.avanzar(sesion.estado, etiqueta)
    except TransicionInvalida as e:
        raise HTTPException(409, str(e)) from e

    sesiones.guardar(Sesion(sesion.id, sesion.telefono, r.estado, cedula))
    datos_evento.update(etiqueta_aplicada=etiqueta, siguiente=r.paso.id)
    sesiones.evento(sesion.id, "turno", datos_evento)
    return _respuesta(r)
