"""Pruebas del solver del ciclo — se ejecutan ANTES de generar el dataset.

El generador no debe correr si esta suite falla: un dataset construido sobre un
solver equivocado produciría un clasificador con métricas excelentes sobre
física incorrecta.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

import CoolProp.CoolProp as CP
from config.params import (OBJETIVO_CALIBRACION, PUNTO_DISENO, ParametrosEquipo,
                           parametros_expansion_directa)
from src.calibracion import (Medicion, aplicar_calibracion, calibrar_UA,
                             mediciones_provisionales)
from src.ciclo import (CERO_C_EN_K, PSI_A_PA, AjustesCiclo, CondicionContorno,
                       c_a_k, cop_carnot, k_a_c, pa_abs_a_psig, psig_a_pa_abs,
                       resolver_ciclo, t_burbuja, t_rocio, temperatura_bulbo_humedo)

from .conftest import params_de

RAIZ = Path(__file__).resolve().parents[1]
GOLDEN = RAIZ / "tests" / "puntos_referencia.json"

ESQUINAS = [CondicionContorno(24.0, 60.0, 0.40), CondicionContorno(24.0, 95.0, 1.00),
            CondicionContorno(36.0, 60.0, 0.40), CondicionContorno(36.0, 95.0, 1.00)]


# ---------------------------------------------------------------------------
# 1. Unidades — el error más silencioso del proyecto
# ---------------------------------------------------------------------------
def test_unidades_presion_ida_y_vuelta(parametros_base):
    p = parametros_base
    for psig in [0.0, 55.5, 137.0, 415.0, 800.0]:
        assert pa_abs_a_psig(psig_a_pa_abs(psig, p.P_atm), p.P_atm) == pytest.approx(psig, abs=1e-9)
    assert psig_a_pa_abs(0.0, p.P_atm) == pytest.approx(p.P_atm)
    assert PSI_A_PA == pytest.approx(6894.757, abs=1e-3)


def test_unidades_temperatura_ida_y_vuelta():
    for t in [-40.0, 0.0, 24.0, 50.0, 120.0]:
        assert k_a_c(c_a_k(t)) == pytest.approx(t, abs=1e-12)
    assert CERO_C_EN_K == 273.15


# ---------------------------------------------------------------------------
# 2. Propiedades contra referencia publicada (no contra el propio CoolProp)
# ---------------------------------------------------------------------------
def test_propiedades_r134a_contra_valores_publicados():
    """R-134a (ASHRAE / NIST): ebullición normal −26,1 °C, crítico 101,1 °C / 4,06 MPa."""
    assert t_burbuja(101325.0, "R134a") == pytest.approx(-26.1, abs=0.5)
    assert k_a_c(CP.PropsSI("Tcrit", "R134a")) == pytest.approx(101.1, abs=0.5)
    assert CP.PropsSI("Pcrit", "R134a") == pytest.approx(4.06e6, rel=0.02)


def test_propiedades_r410a_contra_valores_publicados():
    """R-410A: burbuja a 1 atm ≈ −51,4 °C, crítico ≈ 71,3 °C."""
    assert t_burbuja(101325.0, "R410A") == pytest.approx(-51.4, abs=0.5)
    assert k_a_c(CP.PropsSI("Tcrit", "R410A")) == pytest.approx(71.3, abs=0.5)


def test_bulbo_humedo_contra_valores_psicrometricos():
    """Carta psicrométrica: 30 °C y 50 % HR -> bulbo húmedo ≈ 22,0 °C.

    Gobierna la temperatura del agua de la torre en la topología de condensador
    de agua, y es lo que hace que `HR_amb` intervenga físicamente.
    """
    assert temperatura_bulbo_humedo(30.0, 50.0, 101325.0) == pytest.approx(22.0, abs=0.4)
    assert temperatura_bulbo_humedo(35.0, 80.0, 101325.0) == pytest.approx(31.5, abs=0.6)
    # Saturado: bulbo húmedo = bulbo seco.
    assert temperatura_bulbo_humedo(28.0, 100.0, 101325.0) == pytest.approx(28.0, abs=0.2)


# ---------------------------------------------------------------------------
# 3. Balance de energía y coherencia termodinámica, en las TRES topologías
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("cond", ESQUINAS)
def test_cierre_balance_energia(parametros, cond):
    """Q_H = Q_L + W_comp + Q_linea, sobre el lado refrigerante."""
    e = resolver_ciclo(cond, parametros)
    assert e.convergio, f"no convergió en {cond}: {e.motivo}"
    desbalance = abs(e.Q_H - (e.Q_L + e.W_comp + e.Q_linea))
    assert desbalance / parametros.Q_nom < 5e-3


@pytest.mark.parametrize("cond", ESQUINAS)
def test_coherencia_termodinamica(parametros, cond):
    e = resolver_ciclo(cond, parametros)
    assert e.convergio
    assert e.T_evap < e.T_sec_in_ev, "el evaporador debe estar más frío que el fluido que enfría"
    assert e.T_cond > e.T_air_in_cd if not parametros.topologia.cond_es_agua \
        else e.T_cond > e.T_agua_in_cd
    assert e.rp > 1.0
    assert e.SH_evap >= 0.0 and e.SC >= 0.0
    assert e.T_des > e.T_cond, "la descarga debe salir sobrecalentada"
    assert e.m_r > 0 and e.W_comp > 0 and e.Q_L > 0
    assert 0.0 < e.apertura_valvula <= 1.0
    assert e.T_sec_out_ev < e.T_sec_in_ev


@pytest.mark.parametrize("cond", ESQUINAS)
def test_cota_de_segunda_ley(parametros, cond):
    """COP del sistema por debajo del de Carnot. Si falla, hay un signo invertido."""
    e = resolver_ciclo(cond, parametros)
    assert e.convergio
    assert 0.0 < e.Q_L / e.W_elec < cop_carnot(e.T_evap, e.T_cond)


@pytest.mark.parametrize("cond", ESQUINAS)
def test_esquinas_del_dominio_convergen(parametros, cond):
    assert resolver_ciclo(cond, parametros).convergio, f"esquina no convergida: {cond}"


def test_sobrecalentamiento_no_supera_su_tope_fisico(parametros):
    """El refrigerante no puede salir del evaporador más caliente que su fuente."""
    for cond in ESQUINAS:
        e = resolver_ciclo(cond, parametros)
        assert e.convergio
        assert e.T_ev_out <= e.T_sec_in_ev + 1e-6, (
            f"T_ev_out={e.T_ev_out:.2f} por encima del fluido de entrada "
            f"{e.T_sec_in_ev:.2f} en {cond}")


# ---------------------------------------------------------------------------
# 4. Control de capacidad (solo enfriadora)
# ---------------------------------------------------------------------------
def test_el_chiller_sostiene_el_setpoint_a_carga_parcial(parametros_base):
    """Un chiller modula para sostener la salida de agua en el setpoint.

    Sin control de capacidad, a carga parcial el equipo sobre-enfriaría el agua
    muy por debajo del setpoint: un estado que en la instalación real no existe.
    """
    for carga in (0.45, 0.60, 0.80, 1.00):
        e = resolver_ciclo(CondicionContorno(30.0, 80.0, carga), parametros_base)
        assert e.convergio
        assert e.regimen.startswith("controlado")
        assert abs(e.desviacion_setpoint) < 0.05, (
            f"a carga {carga:.0%} el agua sale a {e.T_agua_out_ev:.2f} °C, "
            f"desviada {e.desviacion_setpoint:+.2f} K del setpoint")
        assert parametros_base.y_min <= e.y_capacidad <= 1.0


def test_la_capacidad_modula_con_la_carga(parametros_base):
    ys = [resolver_ciclo(CondicionContorno(30.0, 80.0, q), parametros_base).y_capacidad
          for q in (0.45, 0.70, 0.95)]
    assert ys[0] < ys[1] < ys[2], f"la fracción de capacidad no sigue a la carga: {ys}"


def test_la_saturacion_de_capacidad_queda_registrada(parametros_base):
    """Con el compresor degradado en un día caluroso, el equipo no alcanza el
    setpoint y eso debe quedar registrado, no perdido."""
    e = resolver_ciclo(CondicionContorno(36.0, 85.0, 1.00), parametros_base,
                       AjustesCiclo(f_eta_v=0.60, f_eta_s=0.70))
    assert e.convergio
    assert e.capacidad_saturada
    assert e.y_capacidad == pytest.approx(1.0)
    assert e.desviacion_setpoint > 0.0, "si satura, el agua debe salir por encima del setpoint"


# ---------------------------------------------------------------------------
# 5. Sensibilidades de signo conocido
# ---------------------------------------------------------------------------
def test_sensibilidad_temperatura_ambiente(parametros_base):
    frio = resolver_ciclo(CondicionContorno(26.0, 80.0, 0.80), parametros_base)
    calor = resolver_ciclo(CondicionContorno(35.0, 80.0, 0.80), parametros_base)
    assert frio.convergio and calor.convergio
    assert calor.T_cond > frio.T_cond
    assert calor.P_des > frio.P_des
    assert calor.W_elec > frio.W_elec
    assert (calor.Q_L / calor.W_elec) < (frio.Q_L / frio.W_elec)


def test_sensibilidad_carga_termica(parametros_base):
    baja = resolver_ciclo(CondicionContorno(30.0, 80.0, 0.45), parametros_base)
    alta = resolver_ciclo(CondicionContorno(30.0, 80.0, 1.00), parametros_base)
    assert baja.convergio and alta.convergio
    assert alta.Q_L > baja.Q_L
    assert alta.T_evap < baja.T_evap, "más carga exige evaporar más frío"
    assert alta.W_elec > baja.W_elec


def test_sensibilidad_ua_condensador(parametros_base):
    base = CondicionContorno(30.0, 80.0, 0.80)
    bajo = resolver_ciclo(base, parametros_base.con(UA_cd=parametros_base.UA_cd * 0.7))
    alto = resolver_ciclo(base, parametros_base.con(UA_cd=parametros_base.UA_cd * 1.3))
    assert bajo.convergio and alto.convergio
    assert (alto.T_cond - alto.T_air_in_cd) < (bajo.T_cond - bajo.T_air_in_cd)


def test_la_humedad_solo_interviene_con_torre(parametros_base):
    """Con condensador de aire, HR_amb se mide pero no interviene en el ciclo.

    Con condensador de agua sí interviene, porque la torre trabaja contra el
    bulbo húmedo. Es la diferencia que elimina una de las simplificaciones
    declaradas.
    """
    seco = resolver_ciclo(CondicionContorno(32.0, 60.0, 0.80), parametros_base)
    humedo = resolver_ciclo(CondicionContorno(32.0, 95.0, 0.80), parametros_base)
    assert seco.T_cond == pytest.approx(humedo.T_cond, abs=1e-9)

    p_agua = params_de("chiller_cond_agua")
    seco_t = resolver_ciclo(CondicionContorno(32.0, 60.0, 0.80), p_agua)
    humedo_t = resolver_ciclo(CondicionContorno(32.0, 95.0, 0.80), p_agua)
    assert seco_t.convergio and humedo_t.convergio
    assert humedo_t.T_cond > seco_t.T_cond + 1.0, (
        "con torre, más humedad significa mayor bulbo húmedo y mayor condensación")


# ---------------------------------------------------------------------------
# 6. Determinismo y reproducibilidad
# ---------------------------------------------------------------------------
def test_determinismo_del_solver(parametros):
    c = CondicionContorno(30.0, 80.0, 0.80)
    a, b = resolver_ciclo(c, parametros), resolver_ciclo(c, parametros)
    for campo in ("T_evap", "T_cond", "SH_evap", "y_capacidad", "Q_L", "W_elec", "m_r"):
        assert getattr(a, campo) == getattr(b, campo)


def test_ajustes_neutros_equivalen_a_sano(parametros):
    c = CondicionContorno(30.0, 80.0, 0.80)
    assert resolver_ciclo(c, parametros, AjustesCiclo()).T_evap == \
           resolver_ciclo(c, parametros).T_evap


# ---------------------------------------------------------------------------
# 7. Punto nominal y calibración
# ---------------------------------------------------------------------------
def test_punto_nominal_tras_calibracion(parametros_base):
    e = resolver_ciclo(CondicionContorno(**PUNTO_DISENO), parametros_base)
    assert e.convergio
    assert e.T_evap == pytest.approx(OBJETIVO_CALIBRACION["T_evap"], abs=0.3)
    assert e.T_cond == pytest.approx(OBJETIVO_CALIBRACION["T_cond"], abs=0.3)
    assert e.Q_L == pytest.approx(parametros_base.Q_nom, rel=0.05)


def test_identificabilidad_de_la_calibracion():
    """Con UA conocidos, la calibración los recupera desde otro punto inicial.

    Si no los recuperara, el ajuste estaría mal condicionado y habría que
    saberlo ANTES de que lleguen los datos de campo, no después.
    """
    base = ParametrosEquipo()
    ua_ev_v, ua_cd_v = 82000.0, 60000.0
    cond = CondicionContorno(**PUNTO_DISENO)
    estado = resolver_ciclo(cond, base.con(UA_ev=ua_ev_v, UA_cd=ua_cd_v))
    assert estado.convergio

    med = [Medicion(cond=cond, objetivo={"T_evap": estado.T_evap, "T_cond": estado.T_cond})]
    res = calibrar_UA(med, base.con(UA_ev=65000.0, UA_cd=80000.0),
                      origen_datos="prueba de identificabilidad")
    assert res.convergio
    assert res.UA_ev == pytest.approx(ua_ev_v, rel=0.02)
    assert res.UA_cd == pytest.approx(ua_cd_v, rel=0.02)


def test_calibracion_provisional_alcanza_su_objetivo():
    base = ParametrosEquipo()
    res = calibrar_UA(mediciones_provisionales(base), base)
    assert res.convergio and res.rmse_relativo < 1e-3


# ---------------------------------------------------------------------------
# 8. Regresión: diez puntos congelados
# ---------------------------------------------------------------------------
PUNTOS_REGRESION = [(24.0, 65.0, 0.45), (24.0, 90.0, 1.00), (27.0, 70.0, 0.60),
                    (28.5, 85.0, 0.75), (30.0, 60.0, 0.50), (30.0, 95.0, 0.90),
                    (32.0, 75.0, 0.65), (33.5, 80.0, 1.00), (36.0, 62.0, 0.40),
                    (36.0, 93.0, 0.85)]


def _estados_regresion():
    p = params_de("chiller_cond_aire")
    salida = {}
    for t_amb, hr, q in PUNTOS_REGRESION:
        e = resolver_ciclo(CondicionContorno(t_amb, hr, q), p)
        salida[f"{t_amb}_{hr}_{q}"] = {
            "T_evap": e.T_evap, "T_cond": e.T_cond, "SH_evap": e.SH_evap,
            "y_capacidad": e.y_capacidad, "P_suc": e.P_suc, "P_des": e.P_des,
            "Q_L": e.Q_L, "W_elec": e.W_elec, "m_r": e.m_r}
    return salida


def test_regresion_contra_puntos_congelados():
    """Cualquier cambio futuro que altere los resultados se detecta aquí.

    Para regenerar el archivo tras un cambio de modelo justificado:
        python -m tests.test_ciclo --regenerar
    """
    actuales = _estados_regresion()
    assert GOLDEN.exists(), f"Falta {GOLDEN}. Genéralo con `python -m tests.test_ciclo --regenerar`."
    esperados = json.loads(GOLDEN.read_text(encoding="utf-8"))
    assert set(actuales) == set(esperados), "cambió el conjunto de puntos de referencia"
    for clave, vals in esperados.items():
        for campo, v in vals.items():
            assert actuales[clave][campo] == pytest.approx(v, rel=1e-6), (
                f"El punto {clave} cambió en {campo}: {actuales[clave][campo]} != {v}")


if __name__ == "__main__":
    import sys
    if "--regenerar" in sys.argv:
        GOLDEN.write_text(json.dumps(_estados_regresion(), indent=2), encoding="utf-8")
        print(f"Puntos de referencia regenerados -> {GOLDEN}")
