"""Enmascarado de datos personales (Ley 1581 de 2012).

La cédula entra por teclado y nunca se guarda completa: solo los últimos 3 dígitos.
"""

from __future__ import annotations

import re

_SOLO_DIGITOS = re.compile(r"\D")
_CEDULA = re.compile(r"^\d{6,10}$")  # cédula de ciudadanía colombiana: 6 a 10 dígitos


def normalizar_cedula(dtmf: str) -> str | None:
    """Devuelve solo los dígitos si parece una cédula válida; si no, None.

    El operador termina con '#', que se descarta junto con cualquier otro símbolo.
    """
    digitos = _SOLO_DIGITOS.sub("", dtmf or "")
    return digitos if _CEDULA.match(digitos) else None


def enmascarar_cedula(cedula: str) -> str:
    digitos = _SOLO_DIGITOS.sub("", cedula or "")
    if len(digitos) <= 3:
        return "*" * len(digitos)
    return "*" * (len(digitos) - 3) + digitos[-3:]
