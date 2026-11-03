"""Puerto POST /siguiente-paso, con persistencia en memoria (sin Postgres)."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from core.api import app, obtener_sesiones
from core.masking import enmascarar_cedula, normalizar_cedula
from core.sesiones import SesionesEnMemoria


@pytest.fixture
def sesiones() -> SesionesEnMemoria:
    return SesionesEnMemoria()


@pytest.fixture
def cliente(sesiones: SesionesEnMemoria):
    app.dependency_overrides[obtener_sesiones] = lambda: sesiones
    yield TestClient(app)
    app.dependency_overrides.clear()


def turno(cliente, etiqueta, sid="s1", **extra):
    r = cliente.post("/siguiente-paso", json={"sesion_id": sid, "telefono": "+573001112233", "etiqueta": etiqueta, **extra})
    return r


def test_inicio_devuelve_primer_paso(cliente):
    r = turno(cliente, "inicio", flujo="sin_internet")
    assert r.status_code == 200
    body = r.json()
    assert body["paso_id"] == "datos_moviles"
    assert "datos móviles" in body["texto"]
    assert body["pasos_intentados"] == ["datos_moviles"]


def test_recorrido_completo_por_http_hasta_escalar(cliente):
    turno(cliente, "inicio", flujo="sin_internet")
    for e in ["si", "no"]:
        assert turno(cliente, e).status_code == 200
    body = turno(cliente, "no").json()
    assert body["paso_id"] == "escalar"
    assert body["fin"] and body["crear_caso"]
    assert body["destino"] == "mesa"
    assert body["pasos_intentados"] == ["datos_moviles", "modo_avion", "reiniciar", "escalar"]


def test_inicio_sin_flujo_es_422(cliente):
    assert turno(cliente, "inicio").status_code == 422


def test_flujo_desconocido_es_422(cliente):
    assert turno(cliente, "inicio", flujo="no_existe").status_code == 422


def test_etiqueta_fuera_del_contrato_es_422(cliente):
    turno(cliente, "inicio", flujo="sin_internet")
    assert turno(cliente, "tal_vez").status_code == 422


def test_sesion_inexistente_es_404(cliente):
    assert turno(cliente, "si", sid="nadie").status_code == 404


def test_avanzar_flujo_terminado_es_409(cliente):
    turno(cliente, "inicio", flujo="sin_internet")
    turno(cliente, "si")
    turno(cliente, "si")  # resuelto
    assert turno(cliente, "si").status_code == 409


def test_dos_no_entendi_activan_teclado(cliente):
    turno(cliente, "inicio", flujo="sin_internet")
    assert turno(cliente, "no_entendi").json()["modo_teclado"] is False
    assert turno(cliente, "no_entendi").json()["modo_teclado"] is True


def test_teclado_como_respaldo(cliente):
    turno(cliente, "inicio", flujo="sin_internet")
    body = turno(cliente, "no_entendi", dtmf="1").json()  # 1 = sí
    assert body["paso_id"] == "modo_avion"


def test_cedula_valida_avanza_y_se_guarda_enmascarada(cliente, sesiones):
    turno(cliente, "inicio", flujo="primer_logueo")
    body = turno(cliente, "no_entendi", dtmf="1012345678#").json()
    assert body["paso_id"] == "correo_recibido"
    assert sesiones.sesiones["s1"].cedula_enmascarada == "*******678"


def test_cedula_nunca_aparece_completa_en_eventos(cliente, sesiones):
    turno(cliente, "inicio", flujo="primer_logueo")
    turno(cliente, "no_entendi", dtmf="1012345678#")
    assert "1012345678" not in repr(sesiones.eventos)


def test_cedula_invalida_cuenta_como_no_entendi(cliente):
    turno(cliente, "inicio", flujo="primer_logueo")
    body = turno(cliente, "no_entendi", dtmf="12#").json()
    assert body["paso_id"] == "pedir_cedula"


def test_si_hablado_no_reemplaza_la_cedula(cliente):
    turno(cliente, "inicio", flujo="primer_logueo")
    assert turno(cliente, "si").json()["paso_id"] == "pedir_cedula"


def test_persona_escala_desde_cualquier_punto(cliente):
    turno(cliente, "inicio", flujo="tableta_no_enciende")
    body = turno(cliente, "persona").json()
    assert body["crear_caso"] and body["destino"] == "logistica"


def test_sesiones_independientes(cliente):
    turno(cliente, "inicio", sid="a", flujo="sin_internet")
    turno(cliente, "inicio", sid="b", flujo="primer_logueo")
    assert turno(cliente, "si", sid="a").json()["paso_id"] == "modo_avion"


def test_cada_turno_queda_registrado(cliente, sesiones):
    turno(cliente, "inicio", flujo="sin_internet")
    turno(cliente, "si")
    tipos = [t for _, t, _ in sesiones.eventos]
    assert tipos == ["inicio", "turno"]


# --------------------------------------------------------------------------- masking


@pytest.mark.parametrize("entrada, esperado", [("1012345678#", "1012345678"), ("123456", "123456"), ("12#", None), ("", None), ("12345678901", None)])
def test_normalizar_cedula(entrada, esperado):
    assert normalizar_cedula(entrada) == esperado


@pytest.mark.parametrize("entrada, esperado", [("1012345678", "*******678"), ("123", "***"), ("", "")])
def test_enmascarar_cedula(entrada, esperado):
    assert enmascarar_cedula(entrada) == esperado
