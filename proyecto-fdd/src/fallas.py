"""Capa 2 — Inyección de los 9 modos de falla (sección 4 de la especificación).

Cada modo proviene del AMEF de la Fase 1 y se implementa como la degradación de
un parámetro físico del modelo, con un factor de severidad f ∈ [0, 1]. Este
módulo NO conoce el solver: solo construye el objeto `AjustesCiclo` que
`src.ciclo` aplica. Así la física y la degradación quedan separadas.

FIRMAS_ESPERADAS es la fuente única de verdad sobre el efecto físico de cada
modo. La usa `tests/test_firmas.py` para verificar que el simulador mueve las
variables en la dirección correcta, y `src.modelo` para contrastar la
importancia de características aprendida contra la expectativa física.

APROXIMACIÓN EMPÍRICA DECLARADA (sección 4.1)
---------------------------------------------
El inventario de refrigerante (`carga_baja`, `sobrecarga`) y la restricción de
la línea de líquido no se pueden modelar rigurosamente con un modelo de ciclo
concentrado: harían falta modelos distribuidos de los intercambiadores. Se usa
un mapa empírico que reproduce la firma conocida. Es una simplificación aceptada
en la literatura de FDD, y debe declararse como tal en el informe: NO es un
modelo de primeros principios.
"""

from __future__ import annotations

from .ciclo import AjustesCiclo

# ---------------------------------------------------------------------------
# Catálogo de clases. El índice de la tupla ES el `clase_id` (0-9).
# ---------------------------------------------------------------------------
CLASES: tuple[str, ...] = (
    "sano",                        # 0
    "condensador_sucio",           # 1
    "evaporador_sucio",            # 2
    "carga_baja",                  # 3
    "sobrecarga",                  # 4
    "txv_restringida",             # 5
    "txv_sobrealimenta",           # 6
    "compresor_desgastado",        # 7
    "incondensables",              # 8
    "restriccion_linea_liquido",   # 9
)

CLASE_A_ID = {c: i for i, c in enumerate(CLASES)}
ID_A_CLASE = {i: c for i, c in enumerate(CLASES)}

# ---------------------------------------------------------------------------
# Niveles de severidad (sección 4.2). El incipiente es el que importa: si el
# clasificador solo detecta fallas severas, no aporta nada sobre la inspección
# visual.
# ---------------------------------------------------------------------------
NIVELES: dict[str, tuple[float, float]] = {
    "incipiente": (0.15, 0.35),
    "moderada":   (0.35, 0.65),
    "severa":     (0.65, 0.95),
}

# ---------------------------------------------------------------------------
# Firmas físicas esperadas (columna «Firma esperada» de la sección 4).
#   +1 -> el residuo debe ser POSITIVO
#   -1 -> el residuo debe ser NEGATIVO
#    0 -> el residuo debe permanecer en una banda estrecha alrededor de cero
# Solo se listan los residuos con dirección inequívoca; los demás quedan libres.
# ---------------------------------------------------------------------------
FIRMAS_ESPERADAS: dict[str, dict[str, int]] = {
    "condensador_sucio": {
        "res_split_cond": +1, "res_COP": -1, "res_kW_TR": +1, "res_dT_air_cd": +1,
    },
    "evaporador_sucio": {
        "res_approach_evap": +1, "res_COP": -1,
    },
    "carga_baja": {
        "res_SC": -1, "res_SH_evap": +1, "res_COP": -1,
    },
    "sobrecarga": {
        "res_SC": +1, "res_split_cond": +1,
    },
    "txv_restringida": {
        "res_SH_evap": +1, "res_SH_total": +1, "res_COP": -1,
    },
    "txv_sobrealimenta": {
        "res_SH_evap": -1, "res_SH_total": -1,
    },
    "compresor_desgastado": {
        "res_SH_des": +1, "res_COP": -1, "res_dT_air_ev": -1,
    },
    "incondensables": {
        # Firma distintiva: el split de condensación APARENTE sube porque la
        # presión de descarga sube, pero el salto de aire en el condensador se
        # mantiene normal porque T_cond real no cambió.
        "res_split_cond": +1, "res_dT_air_cd": 0, "res_rp": +1,
    },
    "restriccion_linea_liquido": {
        "res_SC": +1, "res_SH_evap": +1, "res_COP": -1,
    },
}

# Residuo que define a cada clase: el que debe crecer en magnitud con la
# severidad (prueba de monotonía en tests/test_firmas.py).
RESIDUO_CARACTERISTICO: dict[str, str] = {
    "condensador_sucio": "res_split_cond",
    "evaporador_sucio": "res_approach_evap",
    "carga_baja": "res_SC",
    "sobrecarga": "res_SC",
    "txv_restringida": "res_SH_evap",
    "txv_sobrealimenta": "res_SH_evap",
    "compresor_desgastado": "res_SH_des",
    "incondensables": "res_rp",
    "restriccion_linea_liquido": "res_SC",
}


class ClaseDesconocida(ValueError):
    pass


def ajustes_de_falla(clase: str, f: float, p) -> AjustesCiclo:
    """Construye los ajustes del ciclo para un modo de falla y una severidad.

    Parámetros
    ----------
    clase : nombre de la clase, de `CLASES`.
    f     : severidad en [0, 1]. Para `sano` debe ser 0.
    p     : `ParametrosEquipo` (necesario para el mapa empírico de carga, que
            se expresa como fracción del SC nominal).
    """
    if clase not in CLASE_A_ID:
        raise ClaseDesconocida(f"Clase desconocida: {clase!r}. Válidas: {CLASES}")
    if not (0.0 <= f <= 1.0):
        raise ValueError(f"La severidad debe estar en [0, 1]; se recibió f={f}")

    if clase == "sano":
        if f != 0.0:
            raise ValueError("La clase `sano` exige f = 0.")
        return AjustesCiclo()

    if clase == "condensador_sucio":
        # Ensuciamiento de aletas: cae el coeficiente global del condensador Y
        # el caudal de aire, porque la suciedad obstruye el paso entre aletas.
        #
        # DESVIACIÓN DECLARADA respecto a la sección 4, que solo degrada UA_cd:
        # sin la caída de caudal, el salto de aire del condensador no se mueve
        # (Q_H/(m·cp) queda casi constante) y entonces la «firma distintiva» de
        # los incondensables —split aparente alto CON dT_air_cd normal— no es
        # verificable, porque el ensuciamiento tampoco movería dT_air_cd. La
        # especificación ya degrada ambos parámetros en `evaporador_sucio`; se
        # aplica el mismo criterio al condensador por coherencia física.
        return AjustesCiclo(f_UA_cd=1.0 - 0.45 * f, f_m_a_cd=1.0 - 0.25 * f)

    if clase == "evaporador_sucio":
        # Filtro y aletas sucias: cae el UA y también el caudal de aire.
        return AjustesCiclo(f_UA_ev=1.0 - 0.40 * f, f_m_a_ev=1.0 - 0.35 * f)

    if clase == "carga_baja":
        # MAPA EMPÍRICO (sección 4.1): menos inventario -> menos subenfriamiento,
        # más sobrecalentamiento y menos área mojada en el evaporador.
        return AjustesCiclo(
            d_SC=-0.85 * f * p.SC_nom,
            d_SH=+10.0 * f,
            f_UA_ev=1.0 - 0.25 * f,
        )

    if clase == "sobrecarga":
        # MAPA EMPÍRICO (sección 4.1): el líquido inunda parte del condensador.
        return AjustesCiclo(d_SC=+12.0 * f, f_UA_cd=1.0 - 0.20 * f)

    if clase == "txv_restringida":
        # La válvula subalimenta: el sobrecalentamiento objetivo se dispara.
        return AjustesCiclo(d_SH=+12.0 * f)

    if clase == "txv_sobrealimenta":
        # La válvula sobrealimenta: el sobrecalentamiento cae hacia cero, con
        # riesgo de retorno de líquido al compresor.
        return AjustesCiclo(d_SH=-5.0 * f)

    if clase == "compresor_desgastado":
        # Desgaste de scroll/pistones: caen ambas eficiencias.
        return AjustesCiclo(f_eta_v=1.0 - 0.30 * f, f_eta_s=1.0 - 0.25 * f)

    if clase == "incondensables":
        # Aire en el condensador: presión parcial adicional. NO altera T_cond,
        # que sigue gobernada por el balance del lado aire.
        return AjustesCiclo(frac_P_des_extra=0.15 * f)

    if clase == "restriccion_linea_liquido":
        # MAPA EMPÍRICO: la caída de presión adicional en la línea de líquido
        # (ΔP = 0,20·f·(P_des − P_suc)) provoca flasheo aguas arriba de la
        # válvula, que pierde capacidad de alimentación. En un modelo
        # concentrado no hay camino directo desde ΔP, así que el efecto se
        # representa por su consecuencia medible: el evaporador queda
        # hambriento —parte de la superficie deja de estar mojada, de ahí la
        # caída de UA_ev efectivo—, sube el sobrecalentamiento y el líquido se
        # represa aguas arriba (SC↑).
        #
        # Se descartó representarlo como una reducción directa del flujo másico
        # (`f_m_r`): esa formulación sube T_evap y baja la potencia del
        # compresor a la vez, con lo que el COP SUBE. La batería de firmas lo
        # detectó (`res_COP` positivo donde debía ser negativo) y por eso el
        # modelo se cambió. Un evaporador hambriento baja la presión de
        # succión, no la sube.
        return AjustesCiclo(f_UA_ev=1.0 - 0.35 * f, d_SC=+3.0 * f, d_SH=+6.0 * f)

    raise ClaseDesconocida(clase)  # pragma: no cover


def nivel_de_severidad(f: float) -> str:
    """Nivel cualitativo (P-F) al que corresponde una severidad."""
    for nombre, (lo, hi) in NIVELES.items():
        if lo <= f <= hi:
            return nombre
    return "sano" if f == 0.0 else "fuera_de_rango"
