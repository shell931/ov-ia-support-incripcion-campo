"""Motor de flujos guiados.

Lee los árboles YAML y decide el siguiente paso a partir de una etiqueta
(sí / no / no_entendí / persona / esperar). Es determinista: el texto que
se le dice al operador sale siempre del YAML, nunca de un LLM.

Regla de arquitectura: este módulo no importa nada de LiveKit ni de ningún
proveedor. Es el corazón del núcleo hexagonal.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any

import yaml

ETIQUETAS = frozenset({"inicio", "si", "no", "no_entendi", "persona", "esperar"})

# Respaldo por teclado cuando el reconocimiento de voz falla.
DTMF_A_ETIQUETA = {"1": "si", "2": "no", "0": "persona"}

FLOWS_DIR = Path(__file__).parent / "flows"


class FlujoInvalido(ValueError):
    """El YAML de un flujo no cumple el contrato."""


class TransicionInvalida(ValueError):
    """Se pidió avanzar con una etiqueta que no aplica al estado actual."""


@dataclass(frozen=True)
class Paso:
    id: str
    texto: str
    si: str | None = None
    no: str | None = None
    espera_activa: bool = False
    pide_dtmf: bool = False
    fin: bool = False
    accion: str | None = None  # "crear_caso"
    destino: str | None = None  # "mesa" | "direccion_censo" | "logistica"
    prioridad: str | None = None  # "normal" | "alta"


@dataclass(frozen=True)
class Flujo:
    id: str
    descripcion: str
    inicio: str
    escalar: str
    max_intentos_no_entendi: int
    pasos: dict[str, Paso]


@dataclass(frozen=True)
class Estado:
    """Estado de una sesión dentro de un flujo. Inmutable: cada avance devuelve uno nuevo."""

    flujo_id: str
    paso_id: str
    intentos_no_entendi: int = 0
    historial: tuple[str, ...] = field(default_factory=tuple)

    def a_dict(self) -> dict[str, Any]:
        return {
            "flujo_id": self.flujo_id,
            "paso_id": self.paso_id,
            "intentos_no_entendi": self.intentos_no_entendi,
            "historial": list(self.historial),
        }

    @classmethod
    def desde_dict(cls, d: dict[str, Any]) -> "Estado":
        return cls(
            flujo_id=d["flujo_id"],
            paso_id=d["paso_id"],
            intentos_no_entendi=d.get("intentos_no_entendi", 0),
            historial=tuple(d.get("historial", ())),
        )


@dataclass(frozen=True)
class Resultado:
    estado: Estado
    paso: Paso
    modo_teclado: bool  # el agente debe ofrecer "1 sí, 2 no, 0 persona"
    crear_caso: bool  # el agente debe llamar a crear_caso()

    @property
    def fin(self) -> bool:
        return self.paso.fin


# --------------------------------------------------------------------------- carga


def _paso_desde_dict(d: dict[str, Any], flujo_id: str) -> Paso:
    # YAML 1.1 ("problema de Noruega"): la clave `no:` sin comillas se lee como el
    # booleano False. Se acepta igual para que procesos escriba el YAML natural.
    no = d.get("no", d.get(False))
    try:
        return Paso(
            id=d["id"],
            texto=str(d["texto"]).strip(),
            si=d.get("si"),
            no=no,
            espera_activa=bool(d.get("espera_activa", False)),
            pide_dtmf=bool(d.get("pide_dtmf", False)),
            fin=bool(d.get("fin", False)),
            accion=d.get("accion"),
            destino=d.get("destino"),
            prioridad=d.get("prioridad"),
        )
    except KeyError as e:
        raise FlujoInvalido(f"{flujo_id}: paso sin campo obligatorio {e}") from e


def _validar(flujo: Flujo) -> None:
    ids = flujo.pasos
    if flujo.inicio not in ids:
        raise FlujoInvalido(f"{flujo.id}: el paso de inicio '{flujo.inicio}' no existe")
    if flujo.escalar not in ids:
        raise FlujoInvalido(f"{flujo.id}: el paso de escalamiento '{flujo.escalar}' no existe")
    if flujo.max_intentos_no_entendi < 1:
        raise FlujoInvalido(f"{flujo.id}: max_intentos_no_entendi debe ser >= 1")
    for paso in ids.values():
        if not paso.texto:
            raise FlujoInvalido(f"{flujo.id}/{paso.id}: texto vacío")
        if paso.fin:
            if paso.si or paso.no:
                raise FlujoInvalido(f"{flujo.id}/{paso.id}: un paso final no tiene transiciones")
            continue
        if not paso.si or not paso.no:
            raise FlujoInvalido(f"{flujo.id}/{paso.id}: un paso intermedio necesita 'si' y 'no'")
        for destino in (paso.si, paso.no):
            if destino not in ids:
                raise FlujoInvalido(f"{flujo.id}/{paso.id}: apunta a '{destino}', que no existe")
        if paso.accion is not None:
            raise FlujoInvalido(f"{flujo.id}/{paso.id}: solo los pasos finales llevan acción")
    if not ids[flujo.escalar].fin or ids[flujo.escalar].accion != "crear_caso":
        raise FlujoInvalido(f"{flujo.id}: el paso de escalamiento debe ser final y crear caso")


def flujo_desde_dict(d: dict[str, Any]) -> Flujo:
    flujo_id = d.get("id") or "<sin id>"
    pasos_lista = d.get("pasos") or []
    if not pasos_lista:
        raise FlujoInvalido(f"{flujo_id}: no tiene pasos")
    pasos: dict[str, Paso] = {}
    for raw in pasos_lista:
        paso = _paso_desde_dict(raw, flujo_id)
        if paso.id in pasos:
            raise FlujoInvalido(f"{flujo_id}: id de paso repetido '{paso.id}'")
        pasos[paso.id] = paso
    flujo = Flujo(
        id=flujo_id,
        descripcion=str(d.get("descripcion", "")).strip(),
        inicio=d.get("inicio") or pasos_lista[0]["id"],
        escalar=d.get("escalar", "escalar"),
        max_intentos_no_entendi=int(d.get("max_intentos_no_entendi", 2)),
        pasos=pasos,
    )
    _validar(flujo)
    return flujo


def cargar_flujos(directorio: Path = FLOWS_DIR) -> dict[str, Flujo]:
    flujos: dict[str, Flujo] = {}
    for archivo in sorted(directorio.glob("*.yaml")):
        flujo = flujo_desde_dict(yaml.safe_load(archivo.read_text(encoding="utf-8")))
        if flujo.id in flujos:
            raise FlujoInvalido(f"flujo repetido '{flujo.id}' en {archivo.name}")
        flujos[flujo.id] = flujo
    if not flujos:
        raise FlujoInvalido(f"no hay flujos en {directorio}")
    return flujos


# --------------------------------------------------------------------------- motor


def etiqueta_desde_dtmf(tecla: str) -> str:
    """Traduce una tecla del respaldo por teclado a etiqueta. Otra tecla = no entendí."""
    return DTMF_A_ETIQUETA.get(tecla.strip(), "no_entendi")


class Motor:
    def __init__(self, flujos: dict[str, Flujo]):
        self._flujos = flujos

    @property
    def flujos(self) -> dict[str, Flujo]:
        return self._flujos

    def _flujo(self, flujo_id: str) -> Flujo:
        try:
            return self._flujos[flujo_id]
        except KeyError as e:
            raise TransicionInvalida(f"flujo desconocido '{flujo_id}'") from e

    def _resultado(self, flujo: Flujo, estado: Estado, modo_teclado: bool = False) -> Resultado:
        paso = flujo.pasos[estado.paso_id]
        return Resultado(
            estado=estado,
            paso=paso,
            modo_teclado=modo_teclado,
            crear_caso=paso.accion == "crear_caso",
        )

    def iniciar(self, flujo_id: str) -> Resultado:
        flujo = self._flujo(flujo_id)
        estado = Estado(flujo_id=flujo.id, paso_id=flujo.inicio, historial=(flujo.inicio,))
        return self._resultado(flujo, estado)

    def actual(self, estado: Estado) -> Resultado:
        return self._resultado(self._flujo(estado.flujo_id), estado)

    def avanzar(self, estado: Estado, etiqueta: str) -> Resultado:
        if etiqueta not in ETIQUETAS or etiqueta == "inicio":
            raise TransicionInvalida(f"etiqueta inválida '{etiqueta}'")
        flujo = self._flujo(estado.flujo_id)
        paso = flujo.pasos[estado.paso_id]
        if paso.fin:
            raise TransicionInvalida(f"el flujo ya terminó en '{paso.id}'")

        if etiqueta == "esperar":
            # Espera activa: el operador está haciendo algo; no cuenta como fallo.
            return self._resultado(flujo, estado)

        if etiqueta == "no_entendi":
            intentos = estado.intentos_no_entendi + 1
            nuevo = replace(estado, intentos_no_entendi=intentos)
            return self._resultado(flujo, nuevo, modo_teclado=intentos >= flujo.max_intentos_no_entendi)

        destino = flujo.escalar if etiqueta == "persona" else (paso.si if etiqueta == "si" else paso.no)
        nuevo = Estado(
            flujo_id=flujo.id,
            paso_id=destino,
            intentos_no_entendi=0,
            historial=estado.historial + (destino,),
        )
        return self._resultado(flujo, nuevo)
