"""Recorre los tres árboles sin voz: si el motor está bien, la voz es solo un adaptador."""

from __future__ import annotations

import pytest

from core.engine import (
    Estado,
    FlujoInvalido,
    Motor,
    TransicionInvalida,
    cargar_flujos,
    etiqueta_desde_dtmf,
    flujo_desde_dict,
)


@pytest.fixture(scope="module")
def motor() -> Motor:
    return Motor(cargar_flujos())


def recorrer(motor: Motor, flujo_id: str, etiquetas: list[str]):
    r = motor.iniciar(flujo_id)
    for e in etiquetas:
        r = motor.avanzar(r.estado, e)
    return r


# --------------------------------------------------------------------------- carga


def test_cargan_los_tres_flujos(motor: Motor):
    assert set(motor.flujos) == {"sin_internet", "primer_logueo", "tableta_no_enciende"}


@pytest.mark.parametrize("flujo_id", ["sin_internet", "primer_logueo", "tableta_no_enciende"])
def test_todo_paso_es_alcanzable(motor: Motor, flujo_id: str):
    flujo = motor.flujos[flujo_id]
    vistos, pendientes = set(), [flujo.inicio]
    while pendientes:
        pid = pendientes.pop()
        if pid in vistos:
            continue
        vistos.add(pid)
        paso = flujo.pasos[pid]
        pendientes += [d for d in (paso.si, paso.no) if d]
    vistos.add(flujo.escalar)  # alcanzable siempre con "persona"
    assert vistos == set(flujo.pasos), f"pasos huérfanos: {set(flujo.pasos) - vistos}"


# --------------------------------------------------------------------------- sin internet


@pytest.mark.parametrize(
    "etiquetas, final",
    [
        (["si", "si"], "resuelto"),  # datos activos, modo avión ok
        (["si", "no", "si"], "resuelto"),  # reinicio resuelve
        (["si", "no", "no"], "escalar"),  # reinicio no resuelve
        (["no", "si", "si"], "resuelto"),  # activa datos
        (["no", "no"], "escalar"),  # no logra activar datos
        (["no", "si", "no", "si"], "resuelto"),
        (["no", "si", "no", "no"], "escalar"),
    ],
)
def test_sin_internet_todas_las_ramas(motor: Motor, etiquetas, final):
    r = recorrer(motor, "sin_internet", etiquetas)
    assert r.paso.id == final
    assert r.fin
    assert r.crear_caso == (final == "escalar")


def test_historial_registra_pasos_intentados(motor: Motor):
    r = recorrer(motor, "sin_internet", ["si", "no", "no"])
    assert r.estado.historial == ("datos_moviles", "modo_avion", "reiniciar", "escalar")


# --------------------------------------------------------------------------- tableta


def test_tableta_no_disponible_va_a_logistica(motor: Motor):
    r = recorrer(motor, "tableta_no_enciende", ["no"])
    assert r.paso.id == "no_disponible"
    assert r.crear_caso and r.paso.destino == "logistica" and r.paso.prioridad == "alta"


def test_tableta_agota_los_cuatro_pasos_y_escala(motor: Motor):
    r = recorrer(motor, "tableta_no_enciende", ["si", "no", "no", "no", "no"])
    assert r.paso.id == "escalar"
    assert r.estado.historial[1:5] == ("mover_cable", "cable_tipo_c", "otra_toma", "otro_adaptador")


@pytest.mark.parametrize("n_no", [0, 1, 2, 3])
def test_tableta_resuelve_en_cualquier_paso(motor: Motor, n_no: int):
    r = recorrer(motor, "tableta_no_enciende", ["si"] + ["no"] * n_no + ["si"])
    assert r.paso.id == "resuelto"


# --------------------------------------------------------------------------- primer logueo


def test_logueo_empieza_pidiendo_cedula_por_teclado(motor: Motor):
    r = motor.iniciar("primer_logueo")
    assert r.paso.pide_dtmf


def test_logueo_sin_correo_va_a_censo(motor: Motor):
    r = recorrer(motor, "primer_logueo", ["si", "no"])
    assert r.paso.id == "sin_credenciales" and r.paso.destino == "direccion_censo"


def test_logueo_dos_fallos_de_credenciales_escala(motor: Motor):
    r = recorrer(motor, "primer_logueo", ["si", "si", "no", "no"])
    assert r.paso.id == "escalar"


def test_logueo_huella_no_reconocida_es_prioridad_alta(motor: Motor):
    r = recorrer(motor, "primer_logueo", ["si", "si", "si", "no", "no"])
    assert r.paso.id == "huella_no_reconocida"
    assert r.paso.destino == "direccion_censo" and r.paso.prioridad == "alta"


def test_logueo_camino_feliz(motor: Motor):
    assert recorrer(motor, "primer_logueo", ["si", "si", "si", "si"]).paso.id == "resuelto"


# --------------------------------------------------------------------------- reglas transversales


def test_persona_escala_desde_cualquier_paso(motor: Motor):
    r = recorrer(motor, "sin_internet", ["si", "persona"])
    assert r.paso.id == "escalar" and r.crear_caso


def test_esperar_no_avanza_ni_cuenta_fallo(motor: Motor):
    r = recorrer(motor, "sin_internet", ["si", "no"])  # en "reiniciar"
    r2 = motor.avanzar(r.estado, "esperar")
    assert r2.paso.id == "reiniciar"
    assert r2.estado.intentos_no_entendi == 0


def test_no_entendi_repite_y_pasa_a_teclado(motor: Motor):
    r = motor.iniciar("sin_internet")
    r = motor.avanzar(r.estado, "no_entendi")
    assert r.paso.id == "datos_moviles" and not r.modo_teclado
    r = motor.avanzar(r.estado, "no_entendi")
    assert r.paso.id == "datos_moviles" and r.modo_teclado


def test_respuesta_valida_reinicia_contador(motor: Motor):
    r = motor.iniciar("sin_internet")
    r = motor.avanzar(r.estado, "no_entendi")
    r = motor.avanzar(r.estado, "si")
    assert r.estado.intentos_no_entendi == 0


def test_no_se_avanza_un_flujo_terminado(motor: Motor):
    r = recorrer(motor, "sin_internet", ["si", "si"])
    with pytest.raises(TransicionInvalida):
        motor.avanzar(r.estado, "si")


@pytest.mark.parametrize("etiqueta", ["inicio", "quizas", ""])
def test_etiqueta_invalida(motor: Motor, etiqueta: str):
    with pytest.raises(TransicionInvalida):
        motor.avanzar(motor.iniciar("sin_internet").estado, etiqueta)


def test_flujo_desconocido(motor: Motor):
    with pytest.raises(TransicionInvalida):
        motor.iniciar("no_existe")


def test_estado_se_serializa_ida_y_vuelta(motor: Motor):
    r = recorrer(motor, "sin_internet", ["no", "no_entendi"])
    assert Estado.desde_dict(r.estado.a_dict()) == r.estado


@pytest.mark.parametrize("tecla, etiqueta", [("1", "si"), ("2", "no"), ("0", "persona"), ("9", "no_entendi")])
def test_dtmf(tecla: str, etiqueta: str):
    assert etiqueta_desde_dtmf(tecla) == etiqueta


# --------------------------------------------------------------------------- validación del YAML


def _base(**extra):
    d = {
        "id": "x",
        "pasos": [
            {"id": "a", "texto": "¿Sí?", "si": "fin", "no": "escalar"},
            {"id": "fin", "texto": "Listo.", "fin": True},
            {"id": "escalar", "texto": "Caso.", "fin": True, "accion": "crear_caso"},
        ],
    }
    d.update(extra)
    return d


def test_flujo_minimo_valido():
    assert flujo_desde_dict(_base()).inicio == "a"


def test_rechaza_transicion_a_paso_inexistente():
    d = _base()
    d["pasos"][0]["si"] = "fantasma"
    with pytest.raises(FlujoInvalido):
        flujo_desde_dict(d)


def test_rechaza_paso_intermedio_sin_no():
    d = _base()
    del d["pasos"][0]["no"]
    with pytest.raises(FlujoInvalido):
        flujo_desde_dict(d)


def test_rechaza_escalar_que_no_crea_caso():
    d = _base()
    del d["pasos"][2]["accion"]
    with pytest.raises(FlujoInvalido):
        flujo_desde_dict(d)


def test_rechaza_ids_repetidos():
    d = _base()
    d["pasos"].append({"id": "a", "texto": "dup", "fin": True})
    with pytest.raises(FlujoInvalido):
        flujo_desde_dict(d)
