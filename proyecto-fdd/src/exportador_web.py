"""Exportación del modelo FDD a JavaScript plano para un visualizador local.

REQUISITO QUE MANDA SOBRE EL FORMATO
------------------------------------
El visualizador debe abrirse con doble clic sobre un archivo local. Bajo el
protocolo `file://`, Chrome y Firefox tratan el origen como `null` y bloquean
`fetch()` por política de CORS, así que un `.json` leído con `fetch` haría que
el visualizador no abra en la máquina del evaluador. Por eso este módulo emite
`.js` con declaraciones `const`, cargables con `<script src=...>`: sin `fetch`,
sin `XMLHttpRequest`, sin módulos ES6.

CUATRO ARCHIVOS
---------------
  fdd_modelo.js    FDD_MODELO     bosque recorrible desde JavaScript
  fdd_fisica.js    FDD_FISICA     parámetros del equipo, fallas, ruido, P-h
  fdd_malla.js     FDD_MALLA      mapa de operación: estados del ciclo
  fdd_metricas.js  FDD_METRICAS   matriz de confusión y métricas con Wilson

TRES DETALLES DE LOS QUE DEPENDE LA EQUIVALENCIA EXACTA CON scikit-learn
------------------------------------------------------------------------
1. `ForestClassifier._validate_X_predict` convierte X a **float32** antes de
   recorrer los árboles. La comparación `x <= umbral` se hace, por tanto, sobre
   un float32 promovido a doble. En JavaScript hay que aplicar `Math.fround` a
   cada característica; sin eso, un residuo que difiera en el octavo dígito
   puede tomar la rama contraria.
2. En esta versión de scikit-learn, `DecisionTreeClassifier.predict_proba`
   devuelve `tree_.value` TAL CUAL, sin normalizar: los valores ya vienen como
   fracciones que suman 1 salvo error de redondeo (se midieron sumas entre
   0,99999999999999978 y 1,0000000000000002). Por eso las hojas se exportan
   verbatim y NO se renormalizan en JavaScript: renormalizar cambiaría los bits.
3. `ForestClassifier.predict_proba` acumula con `out[0] += prediction` árbol por
   árbol sobre un acumulador compartido y divide al final: es una suma LINEAL,
   no por pares. Sumando en JavaScript en el mismo orden de árboles, la igualdad
   es exacta bit a bit. La corrida de referencia debe hacerse con `n_jobs=1`,
   porque con varios hilos el orden de acumulación no es determinista.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
from joblib import Parallel, delayed

RAIZ = Path(__file__).resolve().parents[1]
DIR_DATOS = RAIZ / "web" / "datos"
DIR_RESULTADOS = RAIZ / "resultados"

# Severidades de la malla, una por nivel del intervalo P-F más los extremos.
SEVERIDADES = (0.15, 0.35, 0.55, 0.75, 0.95)

# Eje de carga: extendido por debajo de 0,40 hasta el suelo de convergencia del
# modelo y REFINADO en las dos bandas de transición de régimen (ver
# `validar_malla` y el README).
CARGAS = (0.28, 0.31, 0.34, 0.37, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90, 0.95, 1.00)
TEMPERATURAS = (24.0, 26.0, 28.0, 30.0, 32.0, 34.0, 36.0)
HR_FIJA = 80.0   # sin efecto con condensador de aire; ver README


# ---------------------------------------------------------------------------
# Serialización
# ---------------------------------------------------------------------------
def _num(x) -> str:
    """Número con repr completo: JavaScript y Python usan el mismo doble IEEE-754."""
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return "null"
    if isinstance(x, (bool, np.bool_)):
        return "true" if x else "false"
    if isinstance(x, (int, np.integer)):
        return str(int(x))
    return repr(float(x))


def _num_red(x, dec: int) -> str:
    """Número redondeado, para campos físicos donde no hace falta exactitud de bits."""
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return "null"
    if isinstance(x, (bool, np.bool_)):
        return "true" if x else "false"
    v = round(float(x), dec)
    return repr(int(v)) if v == int(v) and abs(v) < 1e15 else repr(v)


def _arr(xs, dec: int | None = None) -> str:
    f = _num if dec is None else (lambda v: _num_red(v, dec))
    return "[" + ",".join(f(x) for x in xs) + "]"


def _escribir(ruta: Path, constante: str, cuerpo: str, cabecera: str) -> Path:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    texto = (f"// {cabecera}\n"
             f"// Generado por src/exportador_web.py el {date.today().isoformat()}.\n"
             f"// NO editar a mano: se regenera con `python -m src.exportador_web`.\n"
             f"// Cargar con <script src=\"...\"></script>. No usa fetch ni módulos ES6.\n"
             f"const {constante} = {cuerpo};\n")
    ruta.write_text(texto, encoding="utf-8")
    return ruta


# ---------------------------------------------------------------------------
# 1. El bosque
# ---------------------------------------------------------------------------
def _arbol_a_dict(est) -> dict:
    """Un árbol en la codificación que recorre `fdd_inferencia.js`.

    Las hojas puras —una sola clase con valor 1,0— se guardan como el índice de
    esa clase, que es exacto y ocupa cuatro caracteres en vez de once números.
    Las impuras guardan el vector completo con repr, verbatim.
    """
    t = est.tree_
    es_hoja = t.children_left == -1
    v = t.value[:, 0, :]
    idx_hoja = np.where(es_hoja)[0]
    hoja_num = -np.ones(t.node_count, dtype=int)
    hoja_num[idx_hoja] = np.arange(len(idx_hoja))

    clase_pura, valores_impuros, tipo_hoja = [], [], []
    for n in idx_hoja:
        fila = v[n]
        nz = np.flatnonzero(fila)
        if len(nz) == 1 and fila[nz[0]] == 1.0:
            tipo_hoja.append(1)
            clase_pura.append(int(nz[0]))
            valores_impuros.append(None)
        else:
            tipo_hoja.append(0)
            clase_pura.append(-1)
            valores_impuros.append([float(x) for x in fila])

    return {
        "feature": [int(f) if not es_hoja[i] else -1 for i, f in enumerate(t.feature)],
        "umbral": [float(x) if not es_hoja[i] else 0.0 for i, x in enumerate(t.threshold)],
        "izq": [int(x) for x in t.children_left],
        "der": [int(x) for x in t.children_right],
        "hoja": [int(x) for x in hoja_num],
        "tipo_hoja": tipo_hoja,
        "clase_pura": clase_pura,
        "valores": [x for x in valores_impuros if x is not None],
        "indice_impura": [i for i, tp in enumerate(tipo_hoja) if tp == 0],
    }


def exportar_modelo(paquete: dict, ruta: Path | None = None) -> Path:
    ruta = ruta or (DIR_DATOS / "fdd_modelo.js")
    rf = paquete["modelo"]
    arboles = [_arbol_a_dict(e) for e in rf.estimators_]

    partes = []
    for a in arboles:
        impuras = []
        for i, vals in zip(a["indice_impura"], a["valores"]):
            impuras.append(f'{{"h":{i},"v":{_arr(vals)}}}')
        partes.append(
            "{"
            f'"feature":{_arr(a["feature"])},'
            f'"umbral":{_arr(a["umbral"])},'
            f'"izq":{_arr(a["izq"])},'
            f'"der":{_arr(a["der"])},'
            f'"hoja":{_arr(a["hoja"])},'
            f'"tipo_hoja":{_arr(a["tipo_hoja"])},'
            f'"clase_pura":{_arr(a["clase_pura"])},'
            f'"impuras":[{",".join(impuras)}]'
            "}")

    cuerpo = ("{\n"
              f'  "version_formato": 1,\n'
              f'  "topologia": {json.dumps(paquete["topologia"])},\n'
              f'  "semilla": {paquete["semilla"]},\n'
              f'  "hiperparametros": {json.dumps(paquete["hiperparametros"])},\n'
              f'  "n_arboles": {len(arboles)},\n'
              f'  "clases": {json.dumps(paquete["clases"], ensure_ascii=False)},\n'
              f'  "columnas_entrada": {json.dumps(paquete["columnas"])},\n'
              f'  "nota_float32": "scikit-learn convierte X a float32 antes de '
              f'recorrer los arboles: aplicar Math.fround a cada caracteristica.",\n'
              f'  "nota_hojas": "Los valores de hoja se guardan verbatim; NO renormalizar.",\n'
              f'  "arboles": [\n    ' + ",\n    ".join(partes) + "\n  ]\n}")
    return _escribir(ruta, "FDD_MODELO", cuerpo,
                     "Bosque aleatorio entrenado, recorrible desde JavaScript.")


# ---------------------------------------------------------------------------
# 2. La física
# ---------------------------------------------------------------------------
def exportar_fisica(p, ruta: Path | None = None) -> Path:
    import CoolProp.CoolProp as CP
    from config.params import SIGMA_RUIDO, resumen_parametros
    from src.fallas import NIVELES, clases, firmas_esperadas, residuo_caracteristico
    from src.features import columnas_derivadas, columnas_residuos
    from src.topologia import variables_medibles

    ruta = ruta or (DIR_DATOS / "fdd_fisica.js")
    topo = p.topologia

    # Campana de saturación muestreada, para dibujar el diagrama P-h sin CoolProp.
    t_crit = CP.PropsSI("Tcrit", p.refrigerante) - 273.15
    temps = np.linspace(-25.0, t_crit - 0.5, 160)
    campana = {"T": [], "P_kPa": [], "h_liq": [], "h_vap": []}
    for t in temps:
        try:
            campana["h_liq"].append(CP.PropsSI("H", "T", t + 273.15, "Q", 0, p.refrigerante) / 1000)
            campana["h_vap"].append(CP.PropsSI("H", "T", t + 273.15, "Q", 1, p.refrigerante) / 1000)
            campana["P_kPa"].append(CP.PropsSI("P", "T", t + 273.15, "Q", 0, p.refrigerante) / 1000)
            campana["T"].append(float(t))
        except Exception:
            pass

    equipo = {k: v["valor"] for k, v in resumen_parametros(p).items()
              if isinstance(v["valor"], (int, float, str))}
    provisionales = [k for k, v in resumen_parametros(p).items() if v["provisional"]]

    cuerpo = ("{\n"
              f'  "version_formato": 1,\n'
              f'  "topologia": {json.dumps(topo.nombre)},\n'
              f'  "descripcion": {json.dumps(topo.descripcion, ensure_ascii=False)},\n'
              f'  "refrigerante": {json.dumps(p.refrigerante)},\n'
              # --- el número que el acoplamiento con el edificio necesita ---
              f'  "Q_nom_W": {_num(p.Q_nom)},\n'
              f'  "Q_nom_TR": {_num_red(p.Q_nom / 3516.85, 3)},\n'
              f'  "nota_Q_nom": "El eje de la malla es FRACCION de carga. Para consultar '
              f'la malla con una demanda en vatios: Q_load_frac = W_demandados / Q_nom_W.",\n'
              f'  "setpoint_agua_C": {_num(p.T_agua_sup_sp)},\n'
              f'  "dT_agua_nominal_K": {_num(p.dT_agua_nom)},\n'
              f'  "caudal_agua_evaporador_kg_s": {_num(p.m_w_ev)},\n'
              f'  "capacidad_minima_compresor": {_num(p.y_min)},\n'
              f'  "equipo": {json.dumps(equipo, ensure_ascii=False)},\n'
              f'  "parametros_provisionales": {json.dumps(provisionales, ensure_ascii=False)},\n'
              f'  "clases": {json.dumps(list(clases(topo)), ensure_ascii=False)},\n'
              f'  "niveles_severidad": {json.dumps(NIVELES, ensure_ascii=False)},\n'
              f'  "firmas_esperadas": {json.dumps(firmas_esperadas(topo), ensure_ascii=False)},\n'
              f'  "residuo_caracteristico": {json.dumps(residuo_caracteristico(topo), ensure_ascii=False)},\n'
              f'  "variables_medidas": {json.dumps(list(variables_medibles(topo)))},\n'
              f'  "variables_derivadas": {json.dumps(list(columnas_derivadas(topo)))},\n'
              f'  "columnas_residuos": {json.dumps(list(columnas_residuos(topo)))},\n'
              f'  "sigma_ruido": {json.dumps({k: [v[0], v[1]] for k, v in SIGMA_RUIDO.items()})},\n'
              f'  "nota_ruido": "La malla se genera SIN ruido y SIN discrepancia '
              f'modelo-planta. El clasificador se entreno CON ambos, asi que alimentado '
              f'con residuos limpios acertara mas de lo que dice el informe. Para '
              f'reproducir el desempeno reportado hay que sumar ruido con estas sigmas.",\n'
              f'  "campana_saturacion": {{"T_C":{_arr(campana["T"], 3)},'
              f'"P_kPa":{_arr(campana["P_kPa"], 3)},'
              f'"h_liq_kJ_kg":{_arr(campana["h_liq"], 3)},'
              f'"h_vap_kJ_kg":{_arr(campana["h_vap"], 3)}}}\n'
              "}")
    return _escribir(ruta, "FDD_FISICA", cuerpo,
                     "Parametros del equipo, catalogo de fallas y campana de saturacion.")


# ---------------------------------------------------------------------------
# 3. Las métricas
# ---------------------------------------------------------------------------
def exportar_metricas(metricas: dict, ruta: Path | None = None,
                      desacuerdo: dict | None = None) -> Path:
    ruta = ruta or (DIR_DATOS / "fdd_metricas.js")
    m = metricas["metricas"]
    def bloque(clave):
        d = m[clave]
        return {k: d[k] for k in ("conjunto", "n_muestras", "matriz_confusion",
                                  "matriz_confusion_normalizada", "recall_por_clase",
                                  "precision_por_clase", "f1_por_clase",
                                  "soporte_por_clase", "intervalos_wilson",
                                  "pr_auc_por_clase", "f1_macro", "f1_ponderado",
                                  "pr_auc_macro", "exactitud_global",
                                  "proporcion_de_clases")}
    payload = {
        "version_formato": 1,
        "clases": metricas["clases"],
        "nivel_discrepancia": metricas["nivel_discrepancia"],
        "modo_discrepancia": metricas["modo_discrepancia"],
        "corrida_valida": metricas["corrida_valida"],
        "prueba_balanceada": bloque("prueba_balanceada"),
        "prevalencia_realista": bloque("prevalencia_realista"),
        "sensibilidad_al_ruido": metricas.get("sensibilidad_al_ruido", {}),
        "sensibilidad_a_la_discrepancia": metricas.get("sensibilidad_a_la_discrepancia", {}),
        "repeticiones_por_corrida": metricas.get("repeticiones_por_corrida", {}),
        "contraste_con_la_fisica": {k: {kk: vv for kk, vv in v.items()
                                        if kk != "tamano_de_efecto"}
                                    for k, v in metricas.get("contraste_con_la_fisica", {}).items()},
        "deteccion_vs_severidad": metricas.get("deteccion_vs_severidad", {}),
        "desacuerdo_100_vs_300": desacuerdo or {},
    }
    return _escribir(ruta, "FDD_METRICAS",
                     json.dumps(payload, indent=1, ensure_ascii=False),
                     "Matriz de confusion, metricas por clase con intervalos de Wilson.")


# ---------------------------------------------------------------------------
# Regla de interpolación: qué transiciones se pueden interpolar y cuáles no
# ---------------------------------------------------------------------------
def descomponer_regimen(nombre: str) -> tuple[str, str]:
    """Separa el régimen en (capacidad, válvula).

    `controlado_inundado` -> ("controlado", "inundado")
    `saturado`            -> ("saturado", "balance")
    """
    for v in ("inundado", "hambriento"):
        if nombre.endswith("_" + v):
            return nombre[: -len(v) - 1], v
    return nombre, "balance"


def se_puede_interpolar(regimenes: list[str], convergidos: list[int]) -> bool:
    """¿Se puede interpolar bilinealmente entre estos cuatro vértices?

    NO se interpola si algún vértice no converge, si alguno está en CICLADO, o
    si cambia el régimen de la VÁLVULA. Motivo, medido y no supuesto:

      * El paso controlado -> saturado es un CODO: la fracción de capacidad
        llega a su tope y la derivada cambia, pero el estado es continuo. Ahí
        interpolar es mejor que tomar el vecino (error máximo medido 0,063 K
        frente a 0,17 K en la banda de saturación).
      * El paso a CICLADO y los cambios de régimen de la válvula son
        DISCONTINUIDADES: el estado salta. Ahí interpolar produce estados que la
        máquina no tiene, y además el error no baja al refinar la malla —se
        midió 0,55, 0,46 y 0,57 K con pasos de 0,06, 0,03 y 0,015—, que es la
        firma de una discontinuidad y no de una malla gruesa.
    """
    if not all(convergidos):
        return False
    caps, valvs = zip(*(descomponer_regimen(r) for r in regimenes))
    if any(c == "ciclado" for c in caps):
        return False
    return len(set(valvs)) == 1


# ---------------------------------------------------------------------------
# 4. La malla: el mapa de operación
# ---------------------------------------------------------------------------
CAMPOS_ESTADO = (
    "y_capacidad", "m_r", "caudal_sec_ev", "caudal_sec_cd",
    "P1_kPa", "P2_kPa", "P3_kPa", "P4_kPa",
    "T1_C", "T2_C", "T3_C", "T4_C",
    "h1_kJkg", "h2_kJkg", "h3_kJkg", "h4_kJkg",
    "T_sec_in_ev", "T_sec_out_ev", "desviacion_setpoint",
    "W_elec_W", "Q_L_W", "COP", "fraccion_marcha",
)
CAMPOS_DISCRETOS = ("convergio", "regimen_cod", "ciclado", "capacidad_saturada",
                    "retorno_liquido")


def _estado_punto(t_amb: float, carga: float, clase: str, f: float, p) -> dict | None:
    """Estado completo del ciclo en un punto de la malla, sin ruido de sensor.

    Los residuos se calculan contra la predicción sana del MISMO juego de
    parámetros: la malla no lleva discrepancia modelo-planta ni ruido. Esa
    decisión está documentada en `FDD_FISICA.nota_ruido`.
    """
    from src.ciclo import AjustesCiclo, CondicionContorno, resolver_ciclo
    from src.fallas import ajustes_de_falla
    from src.features import calcular_residuos, derivadas_desde_medicion
    from src.topologia import variables_medibles

    topo = p.topologia
    cond = CondicionContorno(t_amb, HR_FIJA, carga)
    sano = resolver_ciclo(cond, p, AjustesCiclo())
    if not sano.convergio:
        return None
    deg = sano if clase == "sano" else resolver_ciclo(cond, p, ajustes_de_falla(clase, f, p))
    if not deg.convergio:
        return None

    med = deg.dict_medible()
    res = calcular_residuos(derivadas_desde_medicion(med, p),
                            derivadas_desde_medicion(sano.dict_medible(), p), topo)
    q_demandada = carga * p.Q_nom
    fila = {
        "regimen": deg.regimen,
        "convergio": 1, "ciclado": int(deg.ciclado),
        "capacidad_saturada": int(deg.capacidad_saturada),
        "retorno_liquido": int(deg.retorno_liquido),
        "y_capacidad": deg.y_capacidad, "m_r": deg.m_r,
        "caudal_sec_ev": med.get("V_agua_ev", med.get("V_air_ev")),
        "caudal_sec_cd": med.get("V_agua_cd", float("nan")),
        # Cuatro estados: 1 succión al compresor, 2 descarga, 3 líquido a la
        # salida del condensador, 4 entrada al evaporador tras la expansión.
        "P1_kPa": deg.P_suc_pa / 1000.0, "P2_kPa": deg.P_des_pa / 1000.0,
        "P3_kPa": deg.P_des_pa / 1000.0, "P4_kPa": deg.P_suc_pa / 1000.0,
        "T1_C": med["T_suc"], "T2_C": med["T_des"], "T3_C": med["T_liq"], "T4_C": deg.T_evap,
        "h1_kJkg": deg.h1 / 1000.0, "h2_kJkg": deg.h2a / 1000.0,
        "h3_kJkg": deg.h3 / 1000.0, "h4_kJkg": deg.h4 / 1000.0,
        "T_sec_in_ev": deg.T_sec_in_ev, "T_sec_out_ev": deg.T_sec_out_ev,
        "desviacion_setpoint": deg.desviacion_setpoint,
        "W_elec_W": deg.W_elec, "Q_L_W": deg.Q_L, "COP": deg.Q_L / deg.W_elec,
        # Fracción de marcha: en régimen controlado vale 1; en ciclado, la
        # máquina entrega más de lo que se le pide y el equipo real arranca y
        # para. Es lo que permite al visualizador reconstruir el arranque
        # matutino por ciclado en lugar de extrapolar un estado que no existe.
        "fraccion_marcha": min(1.0, q_demandada / deg.Q_L) if deg.Q_L > 0 else float("nan"),
    }
    fila.update({f"med_{k}": med[k] for k in variables_medibles(topo)})
    fila.update(res)
    return fila


def _fila_vacia(p) -> dict:
    from src.features import columnas_residuos
    from src.topologia import variables_medibles
    fila = {"regimen": "sin_estado_estacionario", "convergio": 0, "ciclado": 0,
            "capacidad_saturada": 0, "retorno_liquido": 0}
    fila.update({c: float("nan") for c in CAMPOS_ESTADO})
    fila.update({f"med_{k}": float("nan") for k in variables_medibles(p.topologia)})
    fila.update({c: float("nan") for c in columnas_residuos(p.topologia)})
    return fila


def generar_malla(p, temperaturas=TEMPERATURAS, cargas=CARGAS,
                  severidades=SEVERIDADES, verbose=True) -> dict:
    from src.fallas import clases
    from src.features import columnas_residuos
    from src.topologia import variables_medibles

    topo = p.topologia
    nombres = clases(topo)
    nT, nQ, nC, nS = len(temperaturas), len(cargas), len(nombres), len(severidades)
    tareas = [(i, j, c, s) for i in range(nT) for j in range(nQ)
              for c in range(nC) for s in range(nS)]
    if verbose:
        print(f"Malla: {nT} T_amb × {nQ} cargas × {nC} clases × {nS} severidades "
              f"= {len(tareas)} puntos")

    def calcular(i, j, c, s):
        clase = nombres[c]
        f = 0.0 if clase == "sano" else severidades[s]
        return _estado_punto(temperaturas[i], cargas[j], clase, f, p)

    crudo = Parallel(n_jobs=-1, verbose=5 if verbose else 0)(
        delayed(calcular)(*t) for t in tareas)

    campos = (list(CAMPOS_ESTADO)
              + [f"med_{k}" for k in variables_medibles(topo)]
              + list(columnas_residuos(topo)))
    datos = {c: np.full(len(tareas), np.nan) for c in campos}
    discretos = {c: np.zeros(len(tareas), dtype=int) for c in CAMPOS_DISCRETOS}
    regimenes: list[str] = []
    cod_reg: dict[str, int] = {}
    vacia = _fila_vacia(p)
    sin_estado = 0
    for k, fila in enumerate(crudo):
        if fila is None:
            fila = vacia
            sin_estado += 1
        reg = fila["regimen"]
        if reg not in cod_reg:
            cod_reg[reg] = len(regimenes)
            regimenes.append(reg)
        discretos["regimen_cod"][k] = cod_reg[reg]
        for c in ("convergio", "ciclado", "capacidad_saturada", "retorno_liquido"):
            discretos[c][k] = fila[c]
        for c in campos:
            datos[c][k] = fila.get(c, np.nan)

    if verbose:
        print(f"  puntos sin estado estacionario: {sin_estado} "
              f"({100 * sin_estado / len(tareas):.2f} %)")
        print(f"  puntos en ciclado: {int(discretos['ciclado'].sum())} "
              f"({100 * discretos['ciclado'].mean():.1f} %)")
    return {"temperaturas": list(temperaturas), "cargas": list(cargas),
            "severidades": list(severidades), "clases": list(nombres),
            "campos": campos, "datos": datos, "discretos": discretos,
            "regimenes": regimenes, "sin_estado": sin_estado, "n": len(tareas)}


def decidir_celdas(malla: dict) -> np.ndarray:
    """1 = la celda se interpola bilinealmente; 0 = vecino más próximo.

    La decisión se calcula UNA vez aquí y se exporta, en lugar de duplicar la
    regla en JavaScript. Tres motivos para marcar una celda como no interpolable:

      * algún vértice no converge;
      * algún vértice está en ciclado o cambia el régimen de la válvula;
      * la celda es VECINA de una celda en ciclado. Esta tercera condición es la
        que no se puede deducir de los vértices: la frontera de ciclado puede
        cruzar por dentro de una celda sin que ninguna de sus cuatro esquinas
        esté todavía en ciclado, y ahí la interpolación mezcla dos regímenes y
        devuelve un estado que la máquina no tiene. Se midió 0,43 K de error en
        `T_evap` en una celda así, cuatro veces el ruido del RTD.

    El paso controlado -> saturado SÍ se interpola: es un codo, no un salto.
    """
    nT, nQ = len(malla["temperaturas"]), len(malla["cargas"])
    nC, nS = len(malla["clases"]), len(malla["severidades"])
    reg, conv = malla["discretos"]["regimen_cod"], malla["discretos"]["convergio"]
    nombres = malla["regimenes"]

    def idx(i, j, c, s):
        return ((i * nQ + j) * nC + c) * nS + s

    celdas = np.zeros((nT - 1) * (nQ - 1) * nC * nS, dtype=int)
    for c in range(nC):
        for s in range(nS):
            # máscara de nodos "problemáticos": ciclado o sin estado estacionario
            malo = np.zeros((nT, nQ), dtype=bool)
            for i in range(nT):
                for j in range(nQ):
                    k = idx(i, j, c, s)
                    cap, _ = descomponer_regimen(nombres[reg[k]])
                    malo[i, j] = (not conv[k]) or cap == "ciclado"
            # dilatación: una celda vecina de un nodo problemático tampoco se interpola
            dil = malo.copy()
            dil[:-1, :] |= malo[1:, :]; dil[1:, :] |= malo[:-1, :]
            dil[:, :-1] |= malo[:, 1:]; dil[:, 1:] |= malo[:, :-1]
            for i in range(nT - 1):
                for j in range(nQ - 1):
                    esq = [idx(i, j, c, s), idx(i + 1, j, c, s),
                           idx(i, j + 1, c, s), idx(i + 1, j + 1, c, s)]
                    regs = [nombres[reg[k]] for k in esq]
                    convs = [conv[k] for k in esq]
                    vecina_mala = bool(dil[i, j] or dil[i + 1, j]
                                       or dil[i, j + 1] or dil[i + 1, j + 1])
                    ok = se_puede_interpolar(regs, convs) and not vecina_mala
                    celdas[((i * (nQ - 1) + j) * nC + c) * nS + s] = int(ok)
    return celdas


def exportar_malla(malla: dict, p, ruta: Path | None = None) -> Path:
    ruta = ruta or (DIR_DATOS / "fdd_malla.js")
    dec = {"m_r": 6, "y_capacidad": 6, "COP": 6, "fraccion_marcha": 6}
    celdas = malla.get("celda_bilineal")
    if celdas is None:
        celdas = decidir_celdas(malla)
        malla["celda_bilineal"] = celdas
    campos_js = ",".join(
        f'"{c}":{_arr(malla["datos"][c], dec.get(c, 4))}' for c in malla["campos"])
    disc_js = ",".join(f'"{c}":{_arr(malla["discretos"][c])}' for c in CAMPOS_DISCRETOS)
    t_sup, dt_nom = p.T_agua_sup_sp, p.dT_agua_nom

    cuerpo = ("{\n"
              f'  "version_formato": 1,\n'
              f'  "topologia": {json.dumps(p.topologia.nombre)},\n'
              f'  "temperaturas_C": {_arr(malla["temperaturas"], 3)},\n'
              f'  "cargas": {_arr(malla["cargas"], 4)},\n'
              f'  "severidades": {_arr(malla["severidades"], 3)},\n'
              f'  "clases": {json.dumps(malla["clases"], ensure_ascii=False)},\n'
              f'  "regimenes": {json.dumps(malla["regimenes"], ensure_ascii=False)},\n'
              f'  "regimenes_info": {json.dumps([{"nombre": r, "capacidad": descomponer_regimen(r)[0], "valvula": descomponer_regimen(r)[1]} for r in malla["regimenes"]], ensure_ascii=False)},\n'
              f'  "HR_fija_pct": {_num(HR_FIJA)},\n'
              f'  "nota_HR": "Con condensador de aire la humedad no interviene en el '
              f'ciclo, asi que la malla no la lleva como eje.",\n'
              f'  "indice": "idx = ((i_T * nCargas + i_carga) * nClases + i_clase) * nSeveridades + i_sev",\n'
              f'  "nCargas": {len(malla["cargas"])}, "nClases": {len(malla["clases"])}, '
              f'"nSeveridades": {len(malla["severidades"])},\n'
              f'  "entrada_canonica": "Q_load_frac",\n'
              f'  "retorno_sano_C": "T_ret = {t_sup} + {dt_nom} * Q_load_frac",\n'
              f'  "aviso_retorno": "indicePorRetorno() usa la relacion SANA y NO es valida '
              f'bajo falla de caudal de agua: con caudal degradado la misma carga produce '
              f'un retorno mas alto. La entrada canonica a la malla es la carga. La '
              f'temperatura de retorno REAL es el campo T_sec_in_ev.",\n'
              f'  "interpolacion": "Bilineal solo si las cuatro esquinas convergen, ninguna '
              f'esta en ciclado y todas comparten regimen de valvula. El paso '
              f'controlado->saturado SI se interpola: es un codo, no un salto. En los '
              f'demas casos, vecino mas proximo. Los campos discretos son SIEMPRE vecino.",\n'
              f'  "campos_discretos": {json.dumps(list(CAMPOS_DISCRETOS))},\n'
              f'  "celda_bilineal": {_arr(celdas)},\n'
              f'  "indice_celda": "idxCelda = ((i_T * (nCargas-1) + i_carga) * nClases + i_clase) * nSeveridades + i_sev",\n'
              f'  "discretos": {{{disc_js}}},\n'
              f'  "datos": {{{campos_js}}}\n'
              "}")
    return _escribir(ruta, "FDD_MALLA", cuerpo,
                     "Mapa de operacion: estados del ciclo por condicion, clase y severidad.")


# ---------------------------------------------------------------------------
# 5. Validación de la malla — cuánto se pierde al interpolar
# ---------------------------------------------------------------------------
def validar_malla(p, malla: dict, muestras_por_celda: int = 9, casos=None,
                  ruta: Path | None = None, verbose: bool = True) -> dict:
    """Compara la malla contra el solver en puntos FUERA de malla.

    MUESTREO DIRIGIDO, no aleatorio. Un muestreo aleatorio uniforme casi nunca
    cae cerca de una frontera de régimen, que es justo donde el mapa no es suave,
    y el promedio esconde el error grande. Aquí se recorren TODAS las celdas, se
    clasifican en régimen uniforme o mixto, y se muestrea dentro de cada una.

    Se reporta el MÁXIMO además del RMSE, separado por tipo de celda:
      * uniforme -> interpolación bilineal
      * mixta    -> vecino más próximo (interpolar entre regímenes distintos
                    produce estados que la máquina no tiene)
    """
    from src.fallas import clases
    ruta = ruta or (DIR_RESULTADOS / "malla_error.json")
    casos = casos or [("sano", 0.0), ("condensador_sucio", 0.75),
                      ("caudal_agua_bajo", 0.75), ("txv_restringida", 0.75),
                      ("incrustacion_evaporador", 0.75)]
    T = np.array(malla["temperaturas"]); Q = np.array(malla["cargas"])
    nQ, nC, nS = len(Q), len(malla["clases"]), len(malla["severidades"])
    campos = [c for c in ("T4_C", "T_sec_out_ev", "m_r", "W_elec_W", "res_SC",
                          "res_approach_ev", "res_COP", "res_dT_agua_ev")
              if c in malla["campos"]]
    RUIDO = {"T4_C": 0.10, "T_sec_out_ev": 0.10, "m_r": None, "W_elec_W": None,
             "res_SC": 0.35, "res_approach_ev": 0.40, "res_COP": 0.22,
             "res_dT_agua_ev": 0.14}

    def idx(i, j, c, s):
        return ((i * nQ + j) * nC + c) * nS + s

    lado = int(np.sqrt(muestras_por_celda))
    frac = np.linspace(0.15, 0.85, lado)
    salida = {"metodo": ("muestreo dirigido: se recorren todas las celdas y se muestrean "
                         f"{lado * lado} puntos interiores en cada una"),
              "leyenda": {
                  "bilineal": "celdas interpolables: sin ciclado y sin cambio de régimen "
                              "de válvula (el paso controlado->saturado es un codo, no un salto)",
                  "vecino": "celdas con ciclado, con cambio de régimen de válvula o con "
                            "algún vértice sin estado estacionario: vecino más próximo",
                  "ruido_instrumento": RUIDO},
              "casos": {}}

    celda_bil = malla.get("celda_bilineal")
    if celda_bil is None:
        celda_bil = decidir_celdas(malla)
        malla["celda_bilineal"] = celda_bil
    for clase, f in casos:
        if clase not in malla["clases"]:
            continue
        ic = malla["clases"].index(clase)
        isv = 0 if clase == "sano" else malla["severidades"].index(f)
        tareas, meta = [], []
        for i in range(len(T) - 1):
            for j in range(len(Q) - 1):
                esq = [idx(i, j, ic, isv), idx(i + 1, j, ic, isv),
                       idx(i, j + 1, ic, isv), idx(i + 1, j + 1, ic, isv)]
                if not all(malla["discretos"]["convergio"][k] for k in esq):
                    continue
                kc = ((i * (len(Q) - 1) + j) * nC + ic) * nS + isv
                tipo = "bilineal" if celda_bil[kc] else "vecino"
                for a in frac:
                    for b in frac:
                        tareas.append((float(T[i] + (T[i + 1] - T[i]) * a),
                                       float(Q[j] + (Q[j + 1] - Q[j]) * b)))
                        meta.append((i, j, float(a), float(b), tipo, esq))
        reales = Parallel(n_jobs=-1)(
            delayed(_estado_punto)(t, q, clase, f, p) for t, q in tareas)

        acum = {"bilineal": {c: [] for c in campos}, "vecino": {c: [] for c in campos}}
        celdas = {"bilineal": set(), "vecino": set()}
        peor = {"bilineal": {}, "vecino": {}}
        for (i, j, a, b, tipo, esq), real in zip(meta, reales):
            if real is None:
                continue
            celdas[tipo].add((i, j))
            vecino = esq[(0 if a < 0.5 else 1) + (0 if b < 0.5 else 2)]
            for c in campos:
                v = malla["datos"][c]
                if tipo == "bilineal":
                    est = ((1 - a) * (1 - b) * v[esq[0]] + a * (1 - b) * v[esq[1]]
                           + (1 - a) * b * v[esq[2]] + a * b * v[esq[3]])
                else:
                    est = v[vecino]
                if np.isnan(est) or np.isnan(real[c]):
                    continue
                err = abs(est - real[c])
                acum[tipo][c].append(err)
                if c not in peor[tipo] or err > peor[tipo][c][0]:
                    peor[tipo][c] = (err, f"T[{T[i]:.0f},{T[i+1]:.0f}] q[{Q[j]:.2f},{Q[j+1]:.2f}]")

        salida["casos"][f"{clase}_f{f}"] = {
            tipo: {"n_celdas": len(celdas[tipo]),
                   "campos": {c: {"n": len(v),
                                  "rmse": float(np.sqrt(np.mean(np.square(v)))) if v else None,
                                  "max": float(np.max(v)) if v else None,
                                  "celda_peor": peor[tipo].get(c, (None, None))[1],
                                  "supera_ruido": (bool(np.max(v) > RUIDO[c])
                                                   if v and RUIDO.get(c) else None)}
                              for c, v in acum[tipo].items()}}
            for tipo in ("bilineal", "vecino")}

    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(json.dumps(salida, indent=2, ensure_ascii=False), encoding="utf-8")
    if verbose:
        print(f"\nError de la malla, muestreo DIRIGIDO por celda -> {ruta}")
        print(f"{'caso':30s} {'celda':9s} {'campo':17s} {'rmse':>9s} {'max':>9s} "
              f"{'ruido':>6s}  celda peor")
        for caso, d in salida["casos"].items():
            for tipo in ("bilineal", "vecino"):
                for c, v in d[tipo]["campos"].items():
                    if v["rmse"] is None:
                        continue
                    rn = RUIDO.get(c)
                    marca = " !!" if v["supera_ruido"] else ""
                    print(f"{caso:30s} {tipo:9s} {c:17s} {v['rmse']:9.4f} {v['max']:9.4f} "
                          f"{(('%.2f' % rn) if rn else '—'):>6s}  {v['celda_peor'] or ''}{marca}")
    return salida


# ---------------------------------------------------------------------------
# Orquestación
# ---------------------------------------------------------------------------
def exportar_todo(sufijo: str = "", validar: bool = True, verbose: bool = True) -> dict:
    import joblib
    from config.params import ParametrosEquipo
    from src.calibracion import aplicar_calibracion

    p = aplicar_calibracion(ParametrosEquipo())
    paquete = joblib.load(DIR_RESULTADOS / f"modelo_rf{sufijo}.joblib")
    metricas = json.loads((DIR_RESULTADOS / f"metricas{sufijo}.json").read_text("utf-8"))
    ruta_des = DIR_RESULTADOS / "desacuerdo_100_vs_300.json"
    desacuerdo = json.loads(ruta_des.read_text("utf-8")) if ruta_des.exists() else None

    if paquete["topologia"] != p.topologia.nombre:
        raise SystemExit(f"El modelo se entrenó con la topología {paquete['topologia']} "
                         f"y la configuración activa es {p.topologia.nombre}")

    rutas = {"modelo": exportar_modelo(paquete),
             "fisica": exportar_fisica(p),
             "metricas": exportar_metricas(metricas, desacuerdo=desacuerdo)}
    malla = generar_malla(p, verbose=verbose)
    rutas["malla"] = exportar_malla(malla, p)
    if validar:
        validar_malla(p, malla, verbose=verbose)

    if verbose:
        print("\nArchivos generados:")
        total = 0
        for k, r in rutas.items():
            tam = r.stat().st_size
            total += tam
            print(f"  {k:10s} {r.relative_to(RAIZ)}  {tam/1e6:6.2f} MB")
        print(f"  {'TOTAL':10s} {'':40s}  {total/1e6:6.2f} MB")
    return rutas


if __name__ == "__main__":
    import argparse, sys
    sys.path.insert(0, str(RAIZ))
    ap = argparse.ArgumentParser(description="Exporta el modelo FDD a JavaScript plano.")
    ap.add_argument("--sufijo", default="")
    ap.add_argument("--sin-validar", action="store_true")
    args = ap.parse_args()
    exportar_todo(args.sufijo, not args.sin_validar)
