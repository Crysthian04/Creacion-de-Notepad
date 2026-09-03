"""Verificación de que cada modo de falla mueve las variables en la dirección
físicamente correcta.

Esta es la suite más importante del proyecto. Un simulador con firmas invertidas
produciría un clasificador con métricas excelentes sobre física equivocada, y
ese es el peor fallo posible aquí: nada en la matriz de confusión lo delataría.

Las pruebas se ejecutan SIN ruido de sensor, para que los signos sean
deterministas y el resultado no dependa de la semilla. Y se exige que el signo
se cumpla en TODAS las condiciones de contorno evaluadas, no en promedio: un
modo que invierte su firma a 36 °C y la respeta a 24 °C está mal modelado aunque
la mediana salga bien.

La tabla de referencia es `src.fallas.FIRMAS_ESPERADAS`, transcrita de la columna
«Firma esperada» de la sección 4 de la especificación, que a su vez proviene del
AMEF de la Fase 1.
"""

from __future__ import annotations

import itertools

import pytest

from config.params import ParametrosEquipo
from src.calibracion import aplicar_calibracion
from src.ciclo import CondicionContorno
from src.fallas import (CLASES, FIRMAS_ESPERADAS, NIVELES, RESIDUO_CARACTERISTICO)
from src.features import COLUMNAS_RESIDUOS
from src.generador import residuos_sin_ruido

P = aplicar_calibracion(ParametrosEquipo())

# Rejilla de condiciones que cubre el dominio completo del barrido (sección 2.1).
CONDICIONES = [
    CondicionContorno(t, hr, 24.0, q)
    for t, hr, q in itertools.product([24.0, 30.0, 36.0], [65.0, 90.0], [0.50, 1.00])
]

F_SEVERA = 0.70        # severidad a la que la firma debe ser inequívoca
F_INCIPIENTE = 0.25    # nivel que realmente importa para el mantenimiento predictivo

TOL_SIGNO = 1e-3       # margen mínimo para considerar que un residuo tiene signo
BANDA_CERO = 0.35      # K — ancho de la banda de "sin cambio" (≈ ruido del sensor)

FALLAS = [c for c in CLASES if c != "sano"]


def _residuos(clase: str, f: float, cond: CondicionContorno) -> dict:
    r = residuos_sin_ruido(cond, clase, f, P)
    assert r is not None, f"El ciclo no convergió para {clase} f={f} en {cond}"
    return r


# ---------------------------------------------------------------------------
# 1. Dirección de la firma, clase por clase y condición por condición
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("clase", FALLAS)
def test_firma_tiene_la_direccion_fisica_correcta(clase):
    esperado = FIRMAS_ESPERADAS[clase]
    fallos = []
    for cond in CONDICIONES:
        r = _residuos(clase, F_SEVERA, cond)
        for residuo, signo in esperado.items():
            v = r[residuo]
            if signo == +1 and not v > TOL_SIGNO:
                fallos.append(f"{cond}: {residuo}={v:+.4f} debía ser POSITIVO")
            elif signo == -1 and not v < -TOL_SIGNO:
                fallos.append(f"{cond}: {residuo}={v:+.4f} debía ser NEGATIVO")
            elif signo == 0 and abs(v) > BANDA_CERO:
                fallos.append(f"{cond}: {residuo}={v:+.4f} debía quedar en |·|<{BANDA_CERO}")
    assert not fallos, (
        f"\nFirma física INCORRECTA para `{clase}`:\n  " + "\n  ".join(fallos[:8]))


@pytest.mark.parametrize("clase", FALLAS)
def test_firma_ya_es_correcta_en_nivel_incipiente(clase):
    """El residuo característico ya apunta bien en el nivel incipiente.

    Si la firma solo aparece cuando la falla es severa, el sistema no aporta nada
    sobre la inspección visual (sección 4.2).
    """
    residuo = RESIDUO_CARACTERISTICO[clase]
    signo = FIRMAS_ESPERADAS[clase].get(residuo)
    if signo in (None, 0):
        pytest.skip(f"{clase}: el residuo característico no tiene signo declarado")
    for cond in CONDICIONES:
        v = _residuos(clase, F_INCIPIENTE, cond)[residuo]
        assert v * signo > TOL_SIGNO, (
            f"{clase} en nivel incipiente: {residuo}={v:+.4f} no respeta el signo {signo:+d} "
            f"en {cond}")


# ---------------------------------------------------------------------------
# 2. Monotonía en severidad
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("clase", FALLAS)
def test_residuo_caracteristico_crece_con_la_severidad(clase):
    """Una falla que no se agrava al agravarse el parámetro está mal inyectada."""
    residuo = RESIDUO_CARACTERISTICO[clase]
    for cond in CONDICIONES:
        magnitudes = [abs(_residuos(clase, f, cond)[residuo]) for f in (0.20, 0.50, 0.80)]
        assert magnitudes[0] < magnitudes[1] < magnitudes[2], (
            f"{clase}: |{residuo}| no crece con f en {cond}: "
            f"{[round(m, 4) for m in magnitudes]}")


# ---------------------------------------------------------------------------
# 3. Unicidad de las firmas
# ---------------------------------------------------------------------------
def _vector_de_signos(clase: str, cond: CondicionContorno, f: float = F_SEVERA) -> tuple:
    r = _residuos(clase, f, cond)
    return tuple(0 if abs(r[c]) <= BANDA_CERO * 0.5 else (1 if r[c] > 0 else -1)
                 for c in COLUMNAS_RESIDUOS)


def test_cada_clase_deja_una_firma_distinta():
    """Dos clases con la misma firma solo se separarían por magnitud.

    Si eso ocurriera, la confusión entre ambas sería estructural —del simulador,
    no del entrenamiento— y es mejor descubrirlo aquí que en la matriz de
    confusión.
    """
    cond = CondicionContorno(30.0, 80.0, 24.0, 0.80)
    firmas = {clase: _vector_de_signos(clase, cond) for clase in FALLAS}
    repetidas = {}
    for clase, v in firmas.items():
        repetidas.setdefault(v, []).append(clase)
    colisiones = {v: cs for v, cs in repetidas.items() if len(cs) > 1}
    assert not colisiones, (
        "Clases con firma de signos idéntica: "
        + "; ".join(" == ".join(cs) for cs in colisiones.values()))


def test_incondensables_se_distingue_de_condensador_sucio():
    """La firma distintiva de la sección 4, verificada explícitamente.

    Ambos suben el split de condensación aparente. Los separa el salto de aire
    del condensador: con incondensables T_cond real no cambió, así que dT_air_cd
    se mantiene normal.
    """
    for cond in CONDICIONES:
        inc = _residuos("incondensables", F_SEVERA, cond)
        suc = _residuos("condensador_sucio", F_SEVERA, cond)
        assert inc["res_split_cond"] > TOL_SIGNO
        assert suc["res_split_cond"] > TOL_SIGNO
        assert abs(inc["res_dT_air_cd"]) < abs(suc["res_dT_air_cd"]), (
            f"En {cond} los incondensables movieron dT_air_cd tanto como el "
            f"ensuciamiento: {inc['res_dT_air_cd']:+.3f} vs {suc['res_dT_air_cd']:+.3f}")


def test_txv_restringida_y_sobrealimenta_van_en_sentidos_opuestos():
    for cond in CONDICIONES:
        r_res = _residuos("txv_restringida", F_SEVERA, cond)["res_SH_evap"]
        r_sob = _residuos("txv_sobrealimenta", F_SEVERA, cond)["res_SH_evap"]
        assert r_res > 0 > r_sob, (
            f"En {cond} las dos fallas de válvula no se oponen: "
            f"restringida={r_res:+.3f}, sobrealimenta={r_sob:+.3f}")


def test_carga_baja_y_sobrecarga_van_en_sentidos_opuestos():
    for cond in CONDICIONES:
        r_baja = _residuos("carga_baja", F_SEVERA, cond)["res_SC"]
        r_sobre = _residuos("sobrecarga", F_SEVERA, cond)["res_SC"]
        assert r_baja < 0 < r_sobre, (
            f"En {cond} carga baja y sobrecarga no se oponen en SC: "
            f"{r_baja:+.3f} vs {r_sobre:+.3f}")


# ---------------------------------------------------------------------------
# 4. La clase sana no deja firma
# ---------------------------------------------------------------------------
def test_sano_no_deja_residuo_sin_ruido():
    """Sin ruido, el equipo sano debe dar residuos exactamente nulos.

    Con ruido, la clase `sano` es ruido puro: es lo que fija la sección 4.
    """
    for cond in CONDICIONES:
        r = residuos_sin_ruido(cond, "sano", 0.0, P)
        assert r is not None
        for nombre, v in r.items():
            assert abs(v) < 1e-9, f"El equipo sano dejó residuo en {nombre}: {v}"


def test_severidad_cero_equivale_a_sano():
    """f = 0 en cualquier clase debe reproducir el estado sano."""
    cond = CondicionContorno(30.0, 80.0, 24.0, 0.80)
    for clase in FALLAS:
        r = residuos_sin_ruido(cond, clase, 0.0, P)
        assert r is not None
        assert max(abs(v) for v in r.values()) < 1e-9, (
            f"{clase} con f=0 no equivale al equipo sano")


# ---------------------------------------------------------------------------
# 5. Coherencia de las tablas declarativas
# ---------------------------------------------------------------------------
def test_las_tablas_de_firmas_cubren_todas_las_fallas():
    assert set(FIRMAS_ESPERADAS) == set(FALLAS)
    assert set(RESIDUO_CARACTERISTICO) == set(FALLAS)
    for clase, esperado in FIRMAS_ESPERADAS.items():
        for residuo in esperado:
            assert residuo in COLUMNAS_RESIDUOS, f"{clase}: {residuo} no es un residuo válido"
    for clase, residuo in RESIDUO_CARACTERISTICO.items():
        assert residuo in COLUMNAS_RESIDUOS


def test_niveles_de_severidad_cubren_el_intervalo_pf():
    assert set(NIVELES) == {"incipiente", "moderada", "severa"}
    assert NIVELES["incipiente"][0] > 0.0
    assert NIVELES["severa"][1] <= 1.0
