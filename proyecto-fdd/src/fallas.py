"""Capa 2 — Inyección de los modos de falla (sección 4 de la especificación).

Cada modo proviene del AMEF de la Fase 1 y se implementa como la degradación de
un parámetro FÍSICO del modelo, con severidad f ∈ [0, 1]. Este módulo no conoce
el solver: solo construye el `AjustesCiclo` que `src.ciclo` aplica.

El catálogo de clases depende de la topología: una enfriadora no puede tener el
evaporador sucio de polvo, y un equipo de expansión directa no puede tener el
caudal de agua bajo.

CAMBIOS FRENTE A LA VERSIÓN ANTERIOR
------------------------------------
Las fallas de la válvula de expansión ya NO son un desplazamiento del setpoint
de sobrecalentamiento. Actúan sobre el COEFICIENTE DE FLUJO de la válvula, que
es lo que dice la sección 4, y el sobrecalentamiento sale como CONSECUENCIA de
la restricción. La versión anterior movía el sobrecalentamiento sin tocar el
flujo, así que `res_rp`, `res_COP` y `res_split_cond` quedaban en cero: la falla
no tenía consecuencia sobre el ciclo.

Lo mismo vale para `restriccion_linea_liquido`: la caída de presión de la
sección 4 entra ahora directamente en el balance de la válvula
(`ΔP_válvula = P_cond − ΔP_línea − P_suc`) en lugar de representarse por un mapa
empírico. Una de las tres aproximaciones empíricas declaradas desaparece.

APROXIMACIÓN EMPÍRICA QUE SE MANTIENE (sección 4.1)
---------------------------------------------------
El inventario de refrigerante (`carga_baja`, `sobrecarga`) no se puede modelar
con rigor en un modelo de ciclo concentrado: haría falta un modelo distribuido
de los intercambiadores. Se usa un mapa empírico que reproduce la firma
conocida. Debe declararse como tal en el informe.
"""

from __future__ import annotations

from .ciclo import AjustesCiclo
from .topologia import Topologia

# ---------------------------------------------------------------------------
# Catálogo de clases por topología. El índice de la tupla ES el `clase_id`.
# ---------------------------------------------------------------------------
_COMUNES_FINALES = (
    "carga_baja", "sobrecarga", "txv_restringida", "txv_sobrealimenta",
    "compresor_desgastado", "incondensables", "restriccion_linea_liquido",
)


def clases(topo: Topologia) -> tuple[str, ...]:
    if topo.evap_es_agua:
        lado_frio = ("incrustacion_evaporador", "caudal_agua_bajo")
    else:
        lado_frio = ("evaporador_sucio",)
    lado_caliente = ("incrustacion_condensador",) if topo.cond_es_agua else ("condensador_sucio",)
    return ("sano",) + lado_caliente + lado_frio + _COMUNES_FINALES


def clase_a_id(topo: Topologia) -> dict[str, int]:
    return {c: i for i, c in enumerate(clases(topo))}


def id_a_clase(topo: Topologia) -> dict[int, str]:
    return {i: c for i, c in enumerate(clases(topo))}


# ---------------------------------------------------------------------------
# Niveles de severidad (sección 4.2)
# ---------------------------------------------------------------------------
NIVELES: dict[str, tuple[float, float]] = {
    "incipiente": (0.15, 0.35),
    "moderada":   (0.35, 0.65),
    "severa":     (0.65, 0.95),
}


class ClaseDesconocida(ValueError):
    pass


def ajustes_de_falla(clase: str, f: float, p) -> AjustesCiclo:
    """Ajustes del ciclo para un modo de falla y una severidad."""
    topo = p.topologia
    if clase not in clases(topo):
        raise ClaseDesconocida(
            f"Clase {clase!r} no pertenece a la topología {topo.nombre}. "
            f"Válidas: {clases(topo)}")
    if not (0.0 <= f <= 1.0):
        raise ValueError(f"La severidad debe estar en [0, 1]; se recibió f={f}")

    if clase == "sano":
        if f != 0.0:
            raise ValueError("La clase `sano` exige f = 0.")
        return AjustesCiclo()

    # --- lado caliente -----------------------------------------------------
    if clase == "condensador_sucio":
        # Ensuciamiento de aletas: cae el UA y también el caudal de aire, porque
        # la suciedad obstruye el paso entre aletas. La sección 4 solo degrada
        # UA_cd; sin la caída de caudal, el salto de aire del condensador no se
        # mueve y la firma distintiva de los incondensables no es verificable.
        return AjustesCiclo(f_UA_cd=1.0 - 0.45 * f, f_m_sec_cd=1.0 - 0.25 * f)

    if clase == "incrustacion_condensador":
        # Incrustación del lado agua: cae el UA a caudal constante.
        return AjustesCiclo(f_UA_cd=1.0 - 0.40 * f)

    # --- lado frío ---------------------------------------------------------
    if clase == "incrustacion_evaporador":
        # Incrustación del lado agua del evaporador: solo cae el UA. El caudal
        # no cambia, así que el salto de temperatura del agua tampoco: la firma
        # se concentra en el approach.
        return AjustesCiclo(f_UA_ev=1.0 - 0.40 * f)

    if clase == "caudal_agua_bajo":
        # Bomba degradada, filtro obstruido o válvula mal posicionada. Con
        # caudal primario constante por diseño, un caudal reducido es avería.
        return AjustesCiclo(f_m_sec_ev=1.0 - 0.40 * f)

    if clase == "evaporador_sucio":       # solo expansión directa
        return AjustesCiclo(f_UA_ev=1.0 - 0.40 * f, f_m_sec_ev=1.0 - 0.35 * f)

    # --- inventario de refrigerante (mapa empírico) ------------------------
    if clase == "carga_baja":
        # Menos inventario: el líquido llega a la válvula con burbujas, así que
        # la válvula pierde capacidad de alimentación (el sobrecalentamiento
        # sube SOLO como consecuencia), cae el subenfriamiento y hay menos área
        # mojada en el evaporador.
        # No se añade una caída explícita de UA_ev: el acoplamiento entre
        # sobrecalentamiento y área seca de `src.ciclo` ya la produce a partir
        # del SH que resulta de la válvula subalimentada. Imponerla además
        # contaría dos veces el mismo efecto físico.
        return AjustesCiclo(f_K_v=1.0 - 0.35 * f, d_SC=-0.85 * f * p.SC_nom)

    if clase == "sobrecarga":
        # El líquido inunda parte del condensador. El subenfriamiento sube por
        # DOS caminos: el inventario (este término) y el acoplamiento con la
        # presión de condensación que `src.ciclo` aplica a todas las clases. El
        # término de inventario se mantiene moderado justamente para no contar
        # dos veces el mismo efecto físico (ver A3 en el README).
        # El término de inventario se fija en 2,0·f y NO en los 12·f de la
        # sección 4: el subenfriamiento sube además por el acoplamiento con la
        # presión de condensación que `src.ciclo` aplica a todas las clases, y
        # sumar ambos contaba dos veces el mismo efecto físico. Con 12·f la
        # ganancia artificial de capacidad por subenfriamiento superaba la
        # penalización de área inundada y el COP SUBÍA con la sobrecarga, que es
        # físicamente falso. Con 2,0·f el COP baja en todas las condiciones y el
        # subenfriamiento sigue subiendo ~1,5 K, muy por encima del ruido.
        return AjustesCiclo(d_SC=+2.0 * f, f_UA_cd=1.0 - 0.20 * f)

    # --- válvula de expansión ---------------------------------------------
    if clase == "txv_restringida":
        # Coeficiente de flujo degradado: filtro de la válvula obstruido,
        # orificio parcialmente bloqueado o válvula subdimensionada. El
        # evaporador queda hambriento.
        # LÍMITE DE VALIDEZ DEL MODELO, declarado. El coeficiente baja hasta
        # 0,20·f, muy por debajo de lo que admitiría un equipo de expansión
        # directa, y el motivo es físico: EN UNA ENFRIADORA EL EVAPORADOR NO
        # PUEDE DESARROLLAR MUCHO SOBRECALENTAMIENTO. El agua entra entre 9 y
        # 12 °C y evapora entre 4 y 6 °C, así que el refrigerante no puede
        # salir más caliente que unos pocos kelvin por encima de la evaporación
        # —no puede calentarse por encima de su fuente—. La válvula termostática
        # necesita ese sobrecalentamiento para abrir; si no puede desarrollarlo,
        # no hay punto de operación estable y el equipo real responde ciclando.
        # Un modelo estacionario no puede representar ese ciclado.
        #
        # Consecuencia de ingeniería, que el informe debe declarar: en una
        # enfriadora, una restricción de válvula superior a ~20 % del
        # coeficiente de flujo saca al equipo del régimen estacionario a carga
        # parcial. Es una falla que se detecta temprano o no se detecta: no hay
        # un régimen degradado estable y prolongado en el que observarla.
        #
        # La válvula tiene además reserva de apertura, así que una restricción
        # incipiente la absorbe abriendo más. Que las restricciones incipientes
        # sean poco detectables NO es un defecto del modelo: es el resultado que
        # debe leerse en la curva de detección frente a severidad.
        return AjustesCiclo(f_K_v=1.0 - 0.20 * f)

    if clase == "txv_sobrealimenta":
        # Bulbo sin carga o elemento de potencia averiado: el lazo de control
        # deja de modular y la válvula queda abierta, sobrealimentando el
        # evaporador. Riesgo de retorno de líquido al compresor.
        return AjustesCiclo(d_a_nom=(1.0 - p.a_nom) * f, f_K_ctrl=1.0 - f)

    # --- compresor ---------------------------------------------------------
    if clase == "compresor_desgastado":
        return AjustesCiclo(f_eta_v=1.0 - 0.30 * f, f_eta_s=1.0 - 0.25 * f)

    # --- incondensables ----------------------------------------------------
    if clase == "incondensables":
        # Aire en el condensador: presión parcial adicional. NO altera T_cond,
        # que sigue gobernada por el balance del lado secundario.
        return AjustesCiclo(frac_P_des_extra=0.15 * f)

    # --- línea de líquido --------------------------------------------------
    if clase == "restriccion_linea_liquido":
        # Filtro deshidratador obstruido o línea estrangulada: la caída de
        # presión adicional reduce el ΔP disponible en la válvula y con ello el
        # flujo que puede alimentar. Primeros principios, no mapa empírico.
        #
        # DESVIACIÓN DECLARADA: el coeficiente es 0,45 y no el 0,20 de la
        # sección 4. Con 0,20 y un subenfriamiento nominal de 6 K, la caída de
        # presión máxima (≈ 154 kPa a f = 0,95) equivale a unos 4,6 K de
        # temperatura de saturación, por debajo del subenfriamiento: el líquido
        # NUNCA llega a flashear. Es decir, bajo el propio coeficiente de la
        # especificación, la firma de «burbujas en el visor» que esa misma
        # sección atribuye a esta falla no puede producirse, y la falla queda
        # con la misma firma de signos que `txv_restringida`. Con 0,45 el
        # flasheo aparece en los niveles moderado y severo —cuando la caída de
        # presión supera el subenfriamiento— y la línea de líquido se enfría por
        # debajo de la saturación, que es el «filtro frío» que el técnico
        # detecta en campo y lo que separa las dos fallas.
        return AjustesCiclo(frac_dP_liquido=0.45 * f)

    raise ClaseDesconocida(clase)  # pragma: no cover


def nivel_de_severidad(f: float) -> str:
    for nombre, (lo, hi) in NIVELES.items():
        if lo <= f <= hi:
            return nombre
    return "sano" if f == 0.0 else "fuera_de_rango"


# ---------------------------------------------------------------------------
# Firmas físicas esperadas (columna «Firma esperada» de la sección 4)
# ---------------------------------------------------------------------------
#   +1 -> el residuo debe ser POSITIVO en TODAS las condiciones
#   -1 -> el residuo debe ser NEGATIVO en TODAS las condiciones
#    0 -> el residuo debe permanecer en una banda estrecha alrededor de cero
# Solo se declaran los canales cuyo signo el modelo sostiene en todo el dominio;
# los demás quedan libres. La tabla se verifica en tests/test_firmas.py.
_FIRMAS_BASE: dict[str, dict[str, int]] = {
    "condensador_sucio": {
        "res_split_cond": +1, "res_dT_air_cd": +1, "res_SC": +1,
        "res_rp": +1, "res_COP": -1, "res_kW_TR": +1,
    },
    "incrustacion_condensador": {
        "res_split_cond": +1, "res_SC": +1, "res_rp": +1, "res_COP": -1,
    },
    "incrustacion_evaporador": {
        # Incrustación a caudal constante: se aleja el agua de la evaporación
        # (approach ↑) SIN mover el salto de temperatura del agua, porque la
        # carga y el caudal no cambian.
        "res_approach_ev": +1, "res_rp": +1, "res_COP": -1, "res_dT_agua_ev": 0,
    },
    "caudal_agua_bajo": {
        # Menos caudal para el mismo calor: el salto del agua sube. Es el canal
        # que la distingue de la incrustación.
        "res_dT_agua_ev": +1,
    },
    "evaporador_sucio": {      # solo expansión directa
        "res_approach_evap": +1, "res_COP": -1,
    },
    "carga_baja": {
        "res_SC": -1, "res_SH_evap": +1, "res_SH_total": +1, "res_COP": -1,
    },
    "sobrecarga": {
        "res_SC": +1, "res_split_cond": +1, "res_COP": -1, "res_SH_evap": -1,
    },
    "txv_restringida": {
        # El evaporador queda hambriento: sube el sobrecalentamiento, cae la
        # presión de succión (sube rp) y cae el COP.
        "res_SH_evap": +1, "res_SH_total": +1, "res_SH_des": +1,
        "res_approach_ev": +1, "res_rp": +1, "res_COP": -1,
    },
    "txv_sobrealimenta": {
        # Sentido contrario en todos los canales de sobrecalentamiento.
        # res_COP es POSITIVO y no es un error: un sobrecalentamiento bajo
        # aprovecha mejor la superficie del evaporador y sube la temperatura de
        # evaporación, así que la eficiencia mejora. El peligro de esta falla no
        # es energético sino mecánico —retorno de líquido al compresor—, y por
        # eso el modelo lo reporta en `retorno_liquido` y `exceso_alimentacion`
        # en lugar de en el COP.
        "res_SH_evap": -1, "res_SH_total": -1, "res_SH_des": -1,
        "res_approach_ev": -1, "res_rp": -1, "res_COP": +1,
    },
    "compresor_desgastado": {
        "res_SH_des": +1, "res_COP": -1, "res_kW_TR": +1,
    },
    "incondensables": {
        # Firma distintiva: el split de condensación APARENTE sube porque la
        # presión de descarga sube, pero el salto del fluido del condensador se
        # mantiene normal porque T_cond real no cambió.
        "res_split_cond": +1, "res_SC": +1, "res_rp": +1, "res_COP": -1,
        "res_dT_air_cd": 0,
    },
    "restriccion_linea_liquido": {
        "res_SH_evap": +1, "res_SH_total": +1, "res_SH_des": +1,
        "res_approach_ev": +1,
    },
}

# Residuo que define a cada clase: el que debe crecer en magnitud con la
# severidad (prueba de monotonía).
_CARACTERISTICO_BASE: dict[str, str] = {
    "condensador_sucio": "res_split_cond",
    "incrustacion_condensador": "res_split_cond",
    "incrustacion_evaporador": "res_approach_ev",
    "caudal_agua_bajo": "res_dT_agua_ev",
    "evaporador_sucio": "res_approach_evap",
    "carga_baja": "res_SC",
    "sobrecarga": "res_SC",
    "txv_restringida": "res_SH_evap",
    "txv_sobrealimenta": "res_SH_evap",
    "compresor_desgastado": "res_SH_des",
    "incondensables": "res_split_cond",
    "restriccion_linea_liquido": "res_SH_evap",
}

# Renombres de residuos entre topologías (el canal físico es el mismo).
_RENOMBRES_DX = {"res_approach_ev": "res_approach_evap", "res_dT_agua_ev": "res_dT_air_ev"}
_RENOMBRES_COND_AGUA = {"res_dT_air_cd": "res_dT_agua_cd"}


def _traducir(d: dict[str, int], topo: Topologia) -> dict[str, int]:
    renombres = {}
    if not topo.evap_es_agua:
        renombres.update(_RENOMBRES_DX)
    if topo.cond_es_agua:
        renombres.update(_RENOMBRES_COND_AGUA)
    return {renombres.get(k, k): v for k, v in d.items()}


def firmas_esperadas(topo: Topologia) -> dict[str, dict[str, int]]:
    """Firma física declarada de cada clase de la topología."""
    return {c: _traducir(_FIRMAS_BASE[c], topo) for c in clases(topo) if c != "sano"}


def residuo_caracteristico(topo: Topologia) -> dict[str, str]:
    return {c: _traducir({_CARACTERISTICO_BASE[c]: 1}, topo).popitem()[0]
            for c in clases(topo) if c != "sano"}
