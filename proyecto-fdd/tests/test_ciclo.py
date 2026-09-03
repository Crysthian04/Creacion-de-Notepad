"""Pruebas del solver del ciclo — se ejecutan ANTES de generar el dataset.

El generador se niega a correr si esta suite falla (ver README): un dataset
construido sobre un solver equivocado produciría un clasificador con métricas
excelentes sobre física incorrecta.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

import CoolProp.CoolProp as CP
from config.params import OBJETIVO_CALIBRACION, PUNTO_DISENO, ParametrosEquipo
from src.calibracion import (Medicion, aplicar_calibracion, calibrar_UA,
                             mediciones_provisionales)
from src.ciclo import (CERO_C_EN_K, PSI_A_PA, AjustesCiclo, CondicionContorno,
                       c_a_k, cop_carnot, k_a_c, pa_abs_a_psig, psig_a_pa_abs,
                       resolver_ciclo, t_burbuja, t_rocio)

RAIZ = Path(__file__).resolve().parents[1]
GOLDEN = RAIZ / "tests" / "puntos_referencia.json"

P_BASE = ParametrosEquipo()
P = aplicar_calibracion(P_BASE)

ESQUINAS = [
    CondicionContorno(24.0, 60.0, 24.0, 0.40),
    CondicionContorno(24.0, 95.0, 24.0, 1.00),
    CondicionContorno(36.0, 60.0, 24.0, 0.40),
    CondicionContorno(36.0, 95.0, 24.0, 1.00),
]


# ---------------------------------------------------------------------------
# 1. Unidades — el error más silencioso del proyecto
# ---------------------------------------------------------------------------
def test_unidades_presion_ida_y_vuelta():
    for psig in [0.0, 55.5, 137.0, 415.0, 800.0]:
        pa = psig_a_pa_abs(psig, P.P_atm)
        assert pa_abs_a_psig(pa, P.P_atm) == pytest.approx(psig, abs=1e-9)
    # Una presión manométrica de 0 psig es exactamente la atmosférica.
    assert psig_a_pa_abs(0.0, P.P_atm) == pytest.approx(P.P_atm)
    # 1 psi = 6894,757 Pa (definición).
    assert PSI_A_PA == pytest.approx(6894.757, abs=1e-3)


def test_unidades_temperatura_ida_y_vuelta():
    for t in [-40.0, 0.0, 24.0, 50.0, 120.0]:
        assert k_a_c(c_a_k(t)) == pytest.approx(t, abs=1e-12)
    assert CERO_C_EN_K == 273.15


# ---------------------------------------------------------------------------
# 2. Propiedades contra referencia publicada (no contra el propio CoolProp)
# ---------------------------------------------------------------------------
def test_propiedades_refrigerante_contra_valores_publicados():
    """Verifica la identidad del fluido, no la aritmética de CoolProp.

    Valores de referencia para el R-410A (ASHRAE / NIST REFPROP):
      punto de burbuja a 101,325 kPa  ≈ −51,4 °C
      temperatura crítica              ≈  71,3 °C
      presión crítica                  ≈   4,90 MPa
    """
    ref = P.refrigerante
    assert t_burbuja(101325.0, ref) == pytest.approx(-51.4, abs=0.5)
    assert k_a_c(CP.PropsSI("Tcrit", ref)) == pytest.approx(71.3, abs=0.5)
    assert CP.PropsSI("Pcrit", ref) == pytest.approx(4.90e6, rel=0.02)


def test_deslizamiento_pequeno_pero_presente():
    """El R-410A es casi azeotrópico: el deslizamiento existe y es < 0,5 K.

    Justifica usar rocío para el sobrecalentamiento y burbuja para el
    subenfriamiento, que es lo que hace `src.features`.
    """
    for p_pa in [8.0e5, 1.2e6, 3.0e6]:
        deslizamiento = t_rocio(p_pa, P.refrigerante) - t_burbuja(p_pa, P.refrigerante)
        assert 0.0 <= deslizamiento < 0.5


# ---------------------------------------------------------------------------
# 3. Cierre del balance de energía
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("cond", ESQUINAS)
def test_cierre_balance_energia(cond):
    """Q_H = Q_L + W_comp + Q_linea.

    El término de línea de succión es la ganancia de calor del ambiente al
    refrigerante entre el evaporador y el compresor: no procede del espacio
    acondicionado, así que aparece en Q_H sin estar en Q_L.
    """
    e = resolver_ciclo(cond, P)
    assert e.convergio, f"no convergió en {cond}: {e.motivo}"
    desbalance = abs(e.Q_H - (e.Q_L + e.W_comp + e.Q_linea))
    assert desbalance / P.Q_nom < 1e-3


@pytest.mark.parametrize("cond", ESQUINAS)
def test_residuo_por_debajo_de_la_tolerancia(cond):
    e = resolver_ciclo(cond, P, tol=1e-4)
    assert e.convergio
    assert e.residuo < 1e-4


# ---------------------------------------------------------------------------
# 4. Coherencia termodinámica
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("cond", ESQUINAS)
def test_coherencia_termodinamica(cond):
    e = resolver_ciclo(cond, P)
    assert e.convergio
    assert e.T_evap < e.T_air_in_ev, "el evaporador debe estar más frío que el aire de retorno"
    assert e.T_cond > e.T_air_in_cd, "el condensador debe estar más caliente que el aire exterior"
    assert e.rp > 1.0, "la relación de presiones debe ser mayor que 1"
    assert e.T_ev_out >= e.T_evap, "sobrecalentamiento negativo"
    assert e.T_liq <= e.T_cond, "subenfriamiento negativo"
    assert e.T_des > e.T_cond, "la descarga debe salir sobrecalentada"
    assert e.m_r > 0 and e.W_comp > 0 and e.Q_L > 0
    assert e.T_air_out_ev < e.T_air_in_ev, "el aire debe enfriarse al pasar por el evaporador"
    assert e.T_air_out_cd > e.T_air_in_cd, "el aire debe calentarse al pasar por el condensador"


@pytest.mark.parametrize("cond", ESQUINAS)
def test_cota_de_segunda_ley(cond):
    """COP del sistema por debajo del COP de Carnot entre T_evap y T_cond.

    Si esta prueba falla hay un signo invertido en el balance de energía.
    """
    e = resolver_ciclo(cond, P)
    assert e.convergio
    cop = e.Q_L / e.W_elec
    assert 0.0 < cop < cop_carnot(e.T_evap, e.T_cond)


# ---------------------------------------------------------------------------
# 5. Sensibilidades de signo conocido
# ---------------------------------------------------------------------------
def _base():
    return CondicionContorno(30.0, 80.0, 24.0, 0.80)


def test_sensibilidad_temperatura_ambiente():
    """Más calor exterior: sube la condensación y la potencia, cae el COP."""
    frio = resolver_ciclo(CondicionContorno(26.0, 80.0, 24.0, 0.80), P)
    calor = resolver_ciclo(CondicionContorno(35.0, 80.0, 24.0, 0.80), P)
    assert frio.convergio and calor.convergio
    assert calor.T_cond > frio.T_cond
    assert calor.P_des > frio.P_des
    assert calor.W_elec > frio.W_elec
    assert (calor.Q_L / calor.W_elec) < (frio.Q_L / frio.W_elec)


def test_sensibilidad_carga_termica():
    """Más carga: sube la evaporación, la presión de succión y la capacidad."""
    baja = resolver_ciclo(CondicionContorno(30.0, 80.0, 24.0, 0.45), P)
    alta = resolver_ciclo(CondicionContorno(30.0, 80.0, 24.0, 1.00), P)
    assert baja.convergio and alta.convergio
    assert alta.T_evap > baja.T_evap
    assert alta.P_suc > baja.P_suc
    assert alta.Q_L > baja.Q_L


def test_sensibilidad_ua_condensador():
    """Más UA en el condensador: menor split de condensación."""
    e_bajo = resolver_ciclo(_base(), P.con(UA_cd=P.UA_cd * 0.7))
    e_alto = resolver_ciclo(_base(), P.con(UA_cd=P.UA_cd * 1.3))
    assert e_bajo.convergio and e_alto.convergio
    split_bajo = e_bajo.T_cond - e_bajo.T_air_in_cd
    split_alto = e_alto.T_cond - e_alto.T_air_in_cd
    assert split_alto < split_bajo


# ---------------------------------------------------------------------------
# 6. Robustez y determinismo
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("cond", ESQUINAS)
def test_esquinas_del_dominio_convergen(cond):
    assert resolver_ciclo(cond, P).convergio, f"esquina no convergida: {cond}"


def test_determinismo_del_solver():
    """La misma entrada devuelve exactamente la misma salida: sin estado oculto."""
    c = _base()
    a = resolver_ciclo(c, P)
    b = resolver_ciclo(c, P)
    for campo in ("T_evap", "T_cond", "P_suc", "P_des", "Q_L", "W_elec", "m_r"):
        assert getattr(a, campo) == getattr(b, campo)


def test_ajustes_neutros_equivalen_a_sano():
    c = _base()
    assert resolver_ciclo(c, P, AjustesCiclo()).T_evap == resolver_ciclo(c, P).T_evap


# ---------------------------------------------------------------------------
# 7. Punto nominal y calibración
# ---------------------------------------------------------------------------
def test_punto_nominal_tras_calibracion():
    """Calibrado, el modelo reproduce el punto de diseño y ~la capacidad de placa."""
    e = resolver_ciclo(CondicionContorno(**PUNTO_DISENO), P)
    assert e.convergio
    assert e.T_evap == pytest.approx(OBJETIVO_CALIBRACION["T_evap"], abs=0.2)
    assert e.T_cond == pytest.approx(OBJETIVO_CALIBRACION["T_cond"], abs=0.2)
    assert e.Q_L == pytest.approx(P.Q_nom, rel=0.10)


def test_identificabilidad_de_la_calibracion():
    """Con UA conocidos, la calibración los recupera desde otro punto inicial.

    Si no los recuperara, el ajuste estaría mal condicionado y habría que
    saberlo ANTES de que lleguen las mediciones de campo, no después.
    """
    ua_ev_verdadero, ua_cd_verdadero = 1650.0, 2500.0
    p_verdadero = P_BASE.con(UA_ev=ua_ev_verdadero, UA_cd=ua_cd_verdadero)
    cond = CondicionContorno(**PUNTO_DISENO)
    estado = resolver_ciclo(cond, p_verdadero)
    assert estado.convergio

    med = [Medicion(cond=cond, objetivo={"T_evap": estado.T_evap, "T_cond": estado.T_cond})]
    res = calibrar_UA(med, P_BASE.con(UA_ev=1100.0, UA_cd=3600.0),
                      origen_datos="prueba de identificabilidad", provisional=True)
    assert res.convergio
    assert res.UA_ev == pytest.approx(ua_ev_verdadero, rel=0.01)
    assert res.UA_cd == pytest.approx(ua_cd_verdadero, rel=0.01)


def test_calibracion_provisional_alcanza_su_objetivo():
    res = calibrar_UA(mediciones_provisionales(P_BASE), P_BASE)
    assert res.convergio and res.rmse_relativo < 1e-3


# ---------------------------------------------------------------------------
# 8. Regresión: diez puntos congelados
# ---------------------------------------------------------------------------
PUNTOS_REGRESION = [
    (24.0, 65.0, 0.45), (24.0, 90.0, 1.00), (27.0, 70.0, 0.60),
    (28.5, 85.0, 0.75), (30.0, 60.0, 0.50), (30.0, 95.0, 0.90),
    (32.0, 75.0, 0.65), (33.5, 80.0, 1.00), (36.0, 62.0, 0.40),
    (36.0, 93.0, 0.85),
]


def _estados_regresion():
    salida = {}
    for t_amb, hr, q in PUNTOS_REGRESION:
        e = resolver_ciclo(CondicionContorno(t_amb, hr, 24.0, q), P)
        salida[f"{t_amb}_{hr}_{q}"] = {
            "T_evap": e.T_evap, "T_cond": e.T_cond, "P_suc": e.P_suc,
            "P_des": e.P_des, "Q_L": e.Q_L, "W_elec": e.W_elec, "m_r": e.m_r,
        }
    return salida


def test_regresion_contra_puntos_congelados():
    """Cualquier cambio futuro que altere los resultados se detecta aquí.

    Para regenerar el archivo a propósito (tras un cambio de modelo justificado):
        python -m tests.test_ciclo --regenerar
    """
    actuales = _estados_regresion()
    assert GOLDEN.exists(), (
        f"Falta {GOLDEN}. Genéralo con `python -m tests.test_ciclo --regenerar`.")
    esperados = json.loads(GOLDEN.read_text(encoding="utf-8"))
    assert set(actuales) == set(esperados), "cambió el conjunto de puntos de referencia"
    for clave, vals in esperados.items():
        for campo, v in vals.items():
            assert actuales[clave][campo] == pytest.approx(v, rel=1e-6), (
                f"El punto {clave} cambió en {campo}: "
                f"{actuales[clave][campo]} != {v}")


if __name__ == "__main__":
    import sys
    if "--regenerar" in sys.argv:
        GOLDEN.write_text(json.dumps(_estados_regresion(), indent=2), encoding="utf-8")
        print(f"Puntos de referencia regenerados -> {GOLDEN}")
