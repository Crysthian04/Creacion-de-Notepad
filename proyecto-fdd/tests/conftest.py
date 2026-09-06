"""Parámetros por topología, compartidos por todas las suites."""

from __future__ import annotations

import pytest

from config.params import ParametrosEquipo, parametros_expansion_directa
from src.calibracion import aplicar_calibracion
from src.topologia import TOPOLOGIAS


def params_de(nombre: str) -> ParametrosEquipo:
    if nombre == "expansion_directa":
        return parametros_expansion_directa()
    if nombre == "chiller_cond_aire":
        # Topología base: usa los UA calibrados por `src.calibracion`.
        return aplicar_calibracion(ParametrosEquipo())
    return ParametrosEquipo(topologia=TOPOLOGIAS[nombre])


TOPOLOGIAS_PROBADAS = ("chiller_cond_aire", "chiller_cond_agua", "expansion_directa")


@pytest.fixture(params=TOPOLOGIAS_PROBADAS)
def parametros(request):
    return params_de(request.param)


@pytest.fixture
def parametros_base():
    return params_de("chiller_cond_aire")
