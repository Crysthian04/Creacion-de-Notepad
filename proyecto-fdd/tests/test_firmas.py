"""Verificación de que cada modo de falla mueve las variables en la dirección
físicamente correcta.

Es la suite más importante del proyecto. Un simulador con firmas invertidas
produciría un clasificador con métricas excelentes sobre física equivocada, y
ese es el peor fallo posible aquí: nada en la matriz de confusión lo delataría.

Se ejecuta SIN ruido de sensor y SIN discrepancia modelo-planta, para que los
signos sean deterministas. Y se exige que el signo se cumpla en TODAS las
condiciones de contorno evaluadas, no en promedio: un modo que invierte su firma
a 36 °C y la respeta a 24 °C está mal modelado aunque la mediana salga bien.

La tabla de referencia es `src.fallas.firmas_esperadas`, transcrita de la
columna «Firma esperada» de la sección 4, que proviene del AMEF de la Fase 1.
"""

from __future__ import annotations

import itertools

import pytest

from src.ciclo import CondicionContorno, resolver_ciclo, AjustesCiclo
from src.fallas import (NIVELES, ajustes_de_falla, clases, firmas_esperadas,
                        residuo_caracteristico)
from src.features import columnas_residuos
from src.generador import residuos_sin_ruido

from .conftest import TOPOLOGIAS_PROBADAS, params_de

CONDICIONES = [CondicionContorno(t, hr, q)
               for t, hr, q in itertools.product([24.0, 30.0, 36.0], [65.0, 90.0],
                                                 [0.50, 0.85])]

F_SEVERA = 0.70
F_INCIPIENTE = 0.35
TOL_SIGNO = 1e-3
BANDA_CERO = 0.35     # K — ancho de la banda de «sin cambio» (≈ ruido del sensor)


# Fracción de condiciones sin estado estacionario que se tolera por clase. No
# es una válvula de escape: es el reconocimiento de que ciertas combinaciones de
# falla y carga NO tienen punto de operación estable —una válvula muy
# restringida a carga parcial exige un sobrecalentamiento que el evaporador no
# puede desarrollar, porque el refrigerante no puede salir más caliente que el
# agua que lo calienta— y el equipo real respondería ciclando. El modelo
# estacionario no puede representar ese ciclado, así que descarta esos puntos y
# los cuenta. `test_los_descartes_se_mantienen_acotados` vigila que no crezcan.
MAX_FRACCION_SIN_ESTADO_ESTACIONARIO = 0.35


def _residuos(p, clase: str, f: float, cond: CondicionContorno) -> dict | None:
    """Residuos del punto, o None si no tiene estado estacionario."""
    return residuos_sin_ruido(cond, clase, f, p)


def _residuos_convergidos(p, clase: str, f: float) -> list[dict]:
    """Residuos de todas las condiciones que sí tienen estado estacionario."""
    salida = [(c, _residuos(p, clase, f, c)) for c in CONDICIONES]
    convergidos = [(c, r) for c, r in salida if r is not None]
    assert len(convergidos) >= 4, (
        f"{clase} f={f}: solo {len(convergidos)} de {len(CONDICIONES)} condiciones "
        f"tienen estado estacionario; la firma no se puede verificar")
    return convergidos


def _fallas(p):
    return [c for c in clases(p.topologia) if c != "sano"]


# ---------------------------------------------------------------------------
# 1. Dirección de la firma, clase por clase y condición por condición
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("topo_nombre", TOPOLOGIAS_PROBADAS)
def test_firma_tiene_la_direccion_fisica_correcta(topo_nombre):
    p = params_de(topo_nombre)
    tabla = firmas_esperadas(p.topologia)
    fallos = []
    for clase in _fallas(p):
        for cond, r in _residuos_convergidos(p, clase, F_SEVERA):
            for residuo, signo in tabla[clase].items():
                v = r[residuo]
                if signo == +1 and not v > TOL_SIGNO:
                    fallos.append(f"{clase} @ {cond}: {residuo}={v:+.4f} debía ser POSITIVO")
                elif signo == -1 and not v < -TOL_SIGNO:
                    fallos.append(f"{clase} @ {cond}: {residuo}={v:+.4f} debía ser NEGATIVO")
                elif signo == 0 and abs(v) > BANDA_CERO:
                    fallos.append(f"{clase} @ {cond}: {residuo}={v:+.4f} debía quedar "
                                  f"en |·| < {BANDA_CERO}")
    assert not fallos, (f"\nFirma física INCORRECTA en {topo_nombre}:\n  "
                        + "\n  ".join(fallos[:10]))


@pytest.mark.parametrize("topo_nombre", TOPOLOGIAS_PROBADAS)
def test_firma_ya_apunta_bien_en_nivel_incipiente(topo_nombre):
    """El residuo característico ya apunta bien en el nivel incipiente.

    Se exige la MEDIANA y no todas las condiciones: en el nivel incipiente la
    señal es del orden del ruido del instrumento en algunos puntos del dominio,
    y esa es justamente la información que la curva de detección frente a
    severidad debe reportar en lugar de esconder.
    """
    p = params_de(topo_nombre)
    tabla = firmas_esperadas(p.topologia)
    caracteristico = residuo_caracteristico(p.topologia)
    for clase in _fallas(p):
        residuo = caracteristico[clase]
        signo = tabla[clase].get(residuo)
        if signo in (None, 0):
            continue
        valores = [r[residuo] for _, r in _residuos_convergidos(p, clase, F_INCIPIENTE)]
        mediana = sorted(valores)[len(valores) // 2]
        assert mediana * signo > TOL_SIGNO, (
            f"{topo_nombre}/{clase} incipiente: mediana de {residuo} = {mediana:+.4f} "
            f"no respeta el signo {signo:+d}")


# ---------------------------------------------------------------------------
# 2. Monotonía en severidad
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("topo_nombre", TOPOLOGIAS_PROBADAS)
def test_residuo_caracteristico_crece_con_la_severidad(topo_nombre):
    """Una falla que no se agrava al agravarse el parámetro está mal inyectada."""
    p = params_de(topo_nombre)
    caracteristico = residuo_caracteristico(p.topologia)
    for clase in _fallas(p):
        residuo = caracteristico[clase]
        for cond in CONDICIONES:
            serie = [_residuos(p, clase, f, cond) for f in (0.20, 0.45, 0.70)]
            if any(r is None for r in serie):
                continue          # sin estado estacionario: se cuenta aparte
            magnitudes = [abs(r[residuo]) for r in serie]
            # Crecimiento estricto en el primer tramo y no decreciente después.
            # El tramo alto admite saturación porque hay observables que se
            # topan con un límite físico: una vez que el evaporador se inunda,
            # el sobrecalentamiento medido ya no puede bajar más, por mucho que
            # empeore la falla. La severidad más allá de ese umbral existe pero
            # NO es observable con el inventario de instrumentos, y eso es un
            # resultado que el informe debe declarar, no un defecto que ocultar.
            assert magnitudes[0] < magnitudes[1], (
                f"{topo_nombre}/{clase}: |{residuo}| no crece con f en {cond}: "
                f"{[round(m, 4) for m in magnitudes]}")
            assert magnitudes[1] <= magnitudes[2] * (1 + 1e-9), (
                f"{topo_nombre}/{clase}: |{residuo}| DECRECE con f en {cond}: "
                f"{[round(m, 4) for m in magnitudes]}")


# ---------------------------------------------------------------------------
# 3. Unicidad y pares que deben oponerse
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("topo_nombre", TOPOLOGIAS_PROBADAS)
def test_cada_clase_deja_una_firma_distinta(topo_nombre):
    """Dos clases con la misma firma solo se separarían por magnitud.

    Si eso ocurriera, la confusión entre ambas sería estructural —del simulador,
    no del entrenamiento— y es mejor descubrirlo aquí que en la matriz de
    confusión.
    """
    p = params_de(topo_nombre)
    cols = columnas_residuos(p.topologia)
    cond = CondicionContorno(30.0, 80.0, 0.80)
    firmas = {}
    for clase in _fallas(p):
        r = _residuos(p, clase, F_SEVERA, cond)
        if r is None:
            continue
        firmas[clase] = tuple(0 if abs(r[c]) <= BANDA_CERO * 0.5 else (1 if r[c] > 0 else -1)
                              for c in cols)
    repetidas: dict[tuple, list[str]] = {}
    for clase, v in firmas.items():
        repetidas.setdefault(v, []).append(clase)
    colisiones = {v: cs for v, cs in repetidas.items() if len(cs) > 1}
    assert not colisiones, ("Clases con firma de signos idéntica en "
                            f"{topo_nombre}: "
                            + "; ".join(" == ".join(cs) for cs in colisiones.values()))


def test_las_dos_fallas_del_lado_agua_se_separan():
    """Incrustación y caudal bajo: el canal que las distingue es el salto del agua.

    A caudal constante, la incrustación NO mueve el salto de temperatura del
    agua —la carga y el caudal no cambian— y sí aleja el agua de la temperatura
    de evaporación. Un caudal reducido hace lo contrario en el canal del salto.
    """
    p = params_de("chiller_cond_aire")
    for cond in CONDICIONES:
        inc = _residuos(p, "incrustacion_evaporador", F_SEVERA, cond)
        cau = _residuos(p, "caudal_agua_bajo", F_SEVERA, cond)
        if inc is None or cau is None:
            continue
        assert abs(inc["res_dT_agua_ev"]) < BANDA_CERO, (
            f"la incrustación movió el salto del agua en {cond}: "
            f"{inc['res_dT_agua_ev']:+.3f}")
        assert cau["res_dT_agua_ev"] > TOL_SIGNO
        assert cau["res_dT_agua_ev"] > inc["res_dT_agua_ev"] + BANDA_CERO
        assert inc["res_approach_ev"] > cau["res_approach_ev"], (
            "la incrustación debe alejar más el agua de la evaporación que el caudal bajo")


def test_incondensables_se_distingue_del_ensuciamiento_del_condensador():
    """Firma distintiva de la sección 4, verificada explícitamente.

    Ambos suben el split de condensación aparente. Los separa el salto de aire
    del condensador: con incondensables T_cond real no cambió.
    """
    p = params_de("chiller_cond_aire")
    for cond in CONDICIONES:
        inc = _residuos(p, "incondensables", F_SEVERA, cond)
        suc = _residuos(p, "condensador_sucio", F_SEVERA, cond)
        if inc is None or suc is None:
            continue
        assert inc["res_split_cond"] > TOL_SIGNO and suc["res_split_cond"] > TOL_SIGNO
        assert abs(inc["res_dT_air_cd"]) < BANDA_CERO
        assert suc["res_dT_air_cd"] > abs(inc["res_dT_air_cd"]), (
            f"en {cond} los incondensables movieron dT_air_cd tanto como el ensuciamiento")


@pytest.mark.parametrize("topo_nombre", TOPOLOGIAS_PROBADAS)
def test_las_dos_fallas_de_valvula_van_en_sentidos_opuestos(topo_nombre):
    p = params_de(topo_nombre)
    for cond in CONDICIONES:
        a = _residuos(p, "txv_restringida", F_SEVERA, cond)
        b = _residuos(p, "txv_sobrealimenta", F_SEVERA, cond)
        if a is None or b is None:
            continue
        r_res, r_sob = a["res_SH_evap"], b["res_SH_evap"]
        assert r_res > 0 > r_sob, (f"en {cond} las fallas de válvula no se oponen: "
                                   f"restringida={r_res:+.3f}, sobrealimenta={r_sob:+.3f}")


@pytest.mark.parametrize("topo_nombre", TOPOLOGIAS_PROBADAS)
def test_las_dos_restricciones_de_flujo_se_separan_por_el_subenfriamiento(topo_nombre):
    """`txv_restringida` y `restriccion_linea_liquido` hambrean ambas el evaporador.

    Lo que las separa es dónde está la restricción: si está aguas arriba de la
    válvula y la caída de presión supera el subenfriamiento, el líquido flashea
    y la línea se enfría hasta la saturación a la presión reducida. Es el
    «filtro deshidratador frío» que el técnico detecta en campo, y en el modelo
    aparece como un salto del subenfriamiento medido que la válvula restringida
    no produce.
    """
    p = params_de(topo_nombre)
    sc_valvula, sc_linea = [], []
    for cond in CONDICIONES:
        a = _residuos(p, "txv_restringida", 0.85, cond)
        b = _residuos(p, "restriccion_linea_liquido", 0.85, cond)
        if a is None or b is None:
            continue
        sc_valvula.append(a["res_SC"])
        sc_linea.append(b["res_SC"])
    assert sc_linea, "sin condiciones convergidas para comparar"
    assert min(sc_linea) > max(sc_valvula) + 0.5, (
        f"{topo_nombre}: el subenfriamiento no separa las dos restricciones. "
        f"línea={min(sc_linea):+.2f}..{max(sc_linea):+.2f}, "
        f"válvula={min(sc_valvula):+.2f}..{max(sc_valvula):+.2f}")
    assert max(abs(v) for v in sc_valvula) < BANDA_CERO, (
        "una válvula restringida no debe mover el subenfriamiento medido")


@pytest.mark.parametrize("topo_nombre", TOPOLOGIAS_PROBADAS)
def test_carga_baja_y_sobrecarga_van_en_sentidos_opuestos(topo_nombre):
    p = params_de(topo_nombre)
    for cond in CONDICIONES:
        a = _residuos(p, "carga_baja", F_SEVERA, cond)
        b = _residuos(p, "sobrecarga", F_SEVERA, cond)
        if a is None or b is None:
            continue
        baja, sobre = a["res_SC"], b["res_SC"]
        assert baja < 0 < sobre, (f"en {cond} carga baja y sobrecarga no se oponen en SC: "
                                  f"{baja:+.3f} vs {sobre:+.3f}")


# ---------------------------------------------------------------------------
# 4. Régimen de la válvula y banderas del control
# ---------------------------------------------------------------------------
def test_la_valvula_restringida_hambrea_el_evaporador():
    """Cae la presión de succión, sube la relación de presiones y cae el COP."""
    p = params_de("chiller_cond_aire")
    for cond in CONDICIONES:
        sano = resolver_ciclo(cond, p, AjustesCiclo())
        deg = resolver_ciclo(cond, p, ajustes_de_falla("txv_restringida", F_SEVERA, p))
        if not (sano.convergio and deg.convergio):
            continue
        assert deg.P_suc < sano.P_suc, f"la succión no cayó en {cond}"
        # NO se compara el flujo másico contra el estado sano: al no alcanzar el
        # setpoint, el control sube la fracción de capacidad, y un compresor a
        # plena carga con la válvula restringida puede mover MÁS masa que uno
        # modulado al 30 % en estado sano. La comparación con sentido físico es
        # a igual fracción de capacidad.
        assert deg.y_capacidad >= sano.y_capacidad - 1e-9, (
            "ante una válvula restringida el control debe subir la capacidad")
        r = _residuos(p, "txv_restringida", F_SEVERA, cond)
        assert r is not None
        assert r["res_COP"] < -TOL_SIGNO and r["res_rp"] > TOL_SIGNO


def test_la_valvula_sobrealimentada_sube_la_succion_e_inunda():
    """Sube la presión de succión, colapsa el sobrecalentamiento y aparece
    riesgo de retorno de líquido."""
    p = params_de("chiller_cond_aire")
    inundados = 0
    for cond in CONDICIONES:
        sano = resolver_ciclo(cond, p, AjustesCiclo())
        deg = resolver_ciclo(cond, p, ajustes_de_falla("txv_sobrealimenta", 0.90, p))
        if not (sano.convergio and deg.convergio):
            continue
        assert deg.P_suc > sano.P_suc, f"la succión no subió en {cond}"
        assert deg.SH_evap < sano.SH_evap
        inundados += deg.retorno_liquido
    assert inundados > 0, "a severidad alta debe aparecer retorno de líquido en algún punto"


def test_el_exceso_de_alimentacion_crece_con_la_severidad():
    """La severidad de la sobrealimentación se mide por el líquido que retorna,
    no por el sobrecalentamiento: una vez inundado, el SH medido ya no baja más."""
    p = params_de("chiller_cond_aire")
    cond = CondicionContorno(30.0, 80.0, 0.85)
    excesos = [resolver_ciclo(cond, p, ajustes_de_falla("txv_sobrealimenta", f, p)
                              ).exceso_alimentacion for f in (0.30, 0.60, 0.90)]
    # Por debajo del umbral de inundación no hay exceso: la válvula abre de más
    # pero el lazo todavía compensa bajando el sobrecalentamiento. El exceso
    # aparece cuando el sobrecalentamiento ya no puede bajar más, y desde ahí
    # crece con la severidad. Es el relevo entre los dos observables.
    assert excesos[2] > 0.05, f"a severidad alta debe haber retorno de líquido: {excesos}"
    assert excesos[2] > excesos[1] and excesos[1] >= excesos[0] - 1e-6, excesos


# ---------------------------------------------------------------------------
# 5. La clase sana no deja firma
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("topo_nombre", TOPOLOGIAS_PROBADAS)
def test_sano_no_deja_residuo_sin_ruido_ni_discrepancia(topo_nombre):
    p = params_de(topo_nombre)
    for cond in CONDICIONES:
        r = residuos_sin_ruido(cond, "sano", 0.0, p)
        assert r is not None
        for nombre, v in r.items():
            assert abs(v) < 1e-9, f"El equipo sano dejó residuo en {nombre}: {v}"


@pytest.mark.parametrize("topo_nombre", TOPOLOGIAS_PROBADAS)
def test_severidad_cero_equivale_a_sano(topo_nombre):
    p = params_de(topo_nombre)
    cond = CondicionContorno(30.0, 80.0, 0.80)
    for clase in _fallas(p):
        r = residuos_sin_ruido(cond, clase, 0.0, p)
        assert r is not None
        assert max(abs(v) for v in r.values()) < 1e-9, (
            f"{clase} con f=0 no equivale al equipo sano")


# ---------------------------------------------------------------------------
# 6. Coherencia de las tablas declarativas
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("topo_nombre", TOPOLOGIAS_PROBADAS)
def test_las_tablas_de_firmas_cubren_todas_las_fallas(topo_nombre):
    p = params_de(topo_nombre)
    topo = p.topologia
    fallas = set(_fallas(p))
    assert set(firmas_esperadas(topo)) == fallas
    assert set(residuo_caracteristico(topo)) == fallas
    cols = set(columnas_residuos(topo))
    for clase, esperado in firmas_esperadas(topo).items():
        for residuo in esperado:
            assert residuo in cols, f"{topo.nombre}/{clase}: {residuo} no es un residuo válido"
    for clase, residuo in residuo_caracteristico(topo).items():
        assert residuo in cols


def test_niveles_de_severidad_cubren_el_intervalo_pf():
    assert set(NIVELES) == {"incipiente", "moderada", "severa"}
    assert NIVELES["incipiente"][0] > 0.0 and NIVELES["severa"][1] <= 1.0


# ---------------------------------------------------------------------------
# 7. Los descartes por ausencia de estado estacionario quedan acotados
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("topo_nombre", TOPOLOGIAS_PROBADAS)
def test_los_descartes_se_mantienen_acotados(topo_nombre):
    """Cuenta las combinaciones de falla y carga sin estado estacionario.

    No se ocultan: se cuentan y se acotan. Si esta prueba empieza a fallar, el
    modelo se está saliendo de su rango de validez y hay que revisar los
    coeficientes de severidad, no relajar el umbral.
    """
    p = params_de(topo_nombre)
    informe = {}
    for clase in _fallas(p):
        sin_estado = sum(1 for c in CONDICIONES
                         if _residuos(p, clase, F_SEVERA, c) is None)
        fraccion = sin_estado / len(CONDICIONES)
        if sin_estado:
            informe[clase] = f"{sin_estado}/{len(CONDICIONES)} ({fraccion:.0%})"
        assert fraccion <= MAX_FRACCION_SIN_ESTADO_ESTACIONARIO, (
            f"{topo_nombre}/{clase}: {sin_estado} de {len(CONDICIONES)} condiciones "
            f"sin estado estacionario, por encima del "
            f"{MAX_FRACCION_SIN_ESTADO_ESTACIONARIO:.0%} tolerado")
    if informe:
        print(f"\n  [{topo_nombre}] condiciones sin estado estacionario: {informe}")
