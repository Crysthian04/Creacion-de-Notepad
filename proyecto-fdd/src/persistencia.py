"""Estudio de persistencia: ¿cuánto ayuda exigir N lecturas coincidentes?

PREGUNTA. Una política de mantenimiento no tiene por qué actuar con la primera
lectura. Si se exige que N lecturas consecutivas den el mismo diagnóstico antes
de emitir una orden de trabajo, ¿cuántas falsas alarmas se evitan y cuántas
fallas se pierden?

QUÉ SE SIMULA, Y QUÉ NO. Entre dos lecturas de la MISMA máquina en el MISMO
punto de operación, lo único que cambia es el ruido de los instrumentos. Eso es
exactamente lo que aquí se repite: se resuelve el ciclo una vez por condición y
se sortean N vectores de ruido independientes sobre el mismo estado.

Lo que NO cambia entre lecturas, a propósito:

  * la discrepancia modelo-planta `epsilon`, que es un error de CALIBRACIÓN del
    gemelo digital y está fijo por condición. No se promedia al repetir la
    lectura: si el gemelo está desafinado en ese punto, lo está en las N;
  * las condiciones de contorno y la severidad de la falla.

Esa es la diferencia con un cálculo binomial ingenuo. Si los errores fueran
independientes entre lecturas, la tasa de falsa alarma caería como p^N. Aquí no
cae tanto, porque una parte del error es sistemática. El módulo reporta las dos
cosas para que la diferencia se vea.

SUPUESTOS DECLARADOS:
  1. Las N lecturas se toman en el mismo punto de operación. En campo, la carga
     y el ambiente se mueven entre lecturas; eso no se modela.
  2. El ruido de instrumento es independiente entre lecturas, gaussiano y con
     las sigmas de `config.params.SIGMA_RUIDO`. Un sesgo de instrumento, que
     sería sistemático, no se modela.
  3. La falla no progresa entre lecturas.

NO reentrena nada: usa `resultados/modelo_rf.joblib` tal cual.

Uso:
    python -m src.persistencia [--n-muestras 10000] [--n-lecturas 5]
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from joblib import Parallel, delayed

RAIZ = Path(__file__).resolve().parents[1]
DIR_RESULTADOS = RAIZ / "resultados"
N_LECTURAS = 5
POLITICAS = (1, 2, 3, 5)


def _lecturas_de_una_condicion(cond_row, eps, semilla_ruido, semilla_sorteo, p,
                               factor_ruido, prevalencia, n_lecturas):
    """Réplica de `_procesar_condicion_prevalencia` con N sorteos de ruido.

    Todo lo demás —condición, epsilon, clase, severidad, estado resuelto— es
    idéntico, y el PRIMER sorteo consume el mismo generador que el dataset
    publicado, de modo que la lectura 0 lo reproduce fila a fila.
    """
    from src.ciclo import AjustesCiclo, CondicionContorno, resolver_ciclo
    from src.fallas import NIVELES, ajustes_de_falla
    from src.generador import (TOL_BALANCE, _referencia_sana, aplicar_discrepancia,
                               aplicar_ruido)
    from src.features import calcular_residuos, derivadas_desde_medicion

    cond = CondicionContorno(T_amb=cond_row["T_amb"], HR_amb=cond_row["HR_amb"],
                             Q_load_frac=cond_row["Q_load_frac"])
    p_modelo = aplicar_discrepancia(p, eps)
    estado_ref, _, derivadas_ref = _referencia_sana(cond, p_modelo)
    if estado_ref is None:
        return []
    estado_sano = resolver_ciclo(cond, p, AjustesCiclo(), tol=TOL_BALANCE)
    if not estado_sano.convergio:
        return []

    rng_sorteo = np.random.default_rng(semilla_sorteo)
    nombres = list(prevalencia)
    clase = str(rng_sorteo.choice(nombres, p=np.array([prevalencia[c] for c in nombres])))
    if clase == "sano":
        f, nivel, estado_deg = 0.0, "sano", estado_sano
    else:
        nivel = str(rng_sorteo.choice(list(NIVELES)))
        lo, hi = NIVELES[nivel]
        f = float(rng_sorteo.uniform(lo, hi))
        estado_deg = resolver_ciclo(cond, p, ajustes_de_falla(clase, f, p), tol=TOL_BALANCE)
    if not estado_deg.convergio:
        return []

    medible = estado_deg.dict_medible()
    rng_ruido = np.random.default_rng(semilla_ruido)   # el MISMO del dataset
    filas = []
    for k in range(n_lecturas):
        medido = aplicar_ruido(medible, rng_ruido, factor_ruido)
        res = calcular_residuos(derivadas_desde_medicion(medido, p),
                                derivadas_ref, p.topologia)
        fila = {"cond_id": cond_row["cond_id"], "lectura": k,
                "clase": clase, "nivel": nivel, "severidad_f": f}
        fila.update(res)
        filas.append(fila)
    return filas


def generar_lecturas(p, semilla_maestra: int, n_muestras: int, n_lecturas: int,
                     verbose: bool = True) -> pd.DataFrame:
    from config.params import MODO_DISCREPANCIA, NIVEL_DISCREPANCIA
    from src.generador import (muestrear_condiciones, muestrear_discrepancia,
                               prevalencia_campo, semillas_derivadas, semillas_hijas)

    from config.params import N_MUESTRAS_PREVALENCIA
    if n_muestras != N_MUESTRAS_PREVALENCIA:
        # El hipercubo latino de n puntos NO contiene los n primeros de uno de
        # N puntos: es un diseño distinto. Con otro n, la reconstrucción no
        # reproduce el dataset publicado y `comprobar_lectura_cero` fallará.
        print(f"  AVISO: n_muestras={n_muestras} != {N_MUESTRAS_PREVALENCIA}; el "
              f"hipercubo latino será OTRO diseño y no reproducirá el dataset.")
    sem = semillas_derivadas(semilla_maestra)
    conds = muestrear_condiciones(n_muestras, sem["lhs_prevalencia"], p, prefijo="B")
    hijas_ruido = semillas_hijas(sem["ruido"], n_muestras, marca=(99,))
    hijas_sorteo = semillas_hijas(sem["severidad"], n_muestras, marca=(99,))
    eps = muestrear_discrepancia(p, semillas_hijas(sem["discrepancia"], 1, (99,))[0],
                                 n_muestras, NIVEL_DISCREPANCIA, MODO_DISCREPANCIA)
    prev = prevalencia_campo(p.topologia)
    if verbose:
        print(f"  {n_muestras} condiciones × {n_lecturas} lecturas "
              f"(discrepancia {NIVEL_DISCREPANCIA:.0%} {MODO_DISCREPANCIA}, fija por condición)")

    salida = Parallel(n_jobs=-1, verbose=5 if verbose else 0)(
        delayed(_lecturas_de_una_condicion)(
            conds.iloc[i], eps[i], hijas_ruido[i], hijas_sorteo[i], p, 1.0, prev,
            n_lecturas)
        for i in range(n_muestras))
    return pd.DataFrame([f for grupo in salida for f in grupo])


def comprobar_lectura_cero(df: pd.DataFrame, topo) -> dict:
    """La lectura 0 debe reproducir el dataset publicado fila a fila.

    Es la validación de que la reconstrucción no se desvía del pipeline. Si
    fallara, el estudio entero sería sobre otros datos y no valdría nada.
    """
    from src.features import columnas_residuos

    ref = pd.read_parquet(RAIZ / "data" / "dataset_prevalencia.parquet")
    cero = df[df["lectura"] == 0].set_index("cond_id")
    ref = ref.set_index("cond_id")
    comunes = cero.index.intersection(ref.index)
    cols = list(columnas_residuos(topo))
    dif = (cero.loc[comunes, cols].to_numpy() - ref.loc[comunes, cols].to_numpy())
    clases_ok = bool((cero.loc[comunes, "clase"] == ref.loc[comunes, "clase"]).all())
    return {"n_comunes": int(len(comunes)), "n_dataset": int(len(ref)),
            "n_reconstruido": int(len(cero)),
            "max_abs_dif_residuos": float(np.abs(dif).max()),
            "clases_identicas": clases_ok}


def evaluar_politicas(df: pd.DataFrame, modelo, topo, politicas=POLITICAS) -> dict:
    """Política: actuar solo si las N primeras lecturas coinciden."""
    from src.features import columnas_residuos
    from src.fallas import clase_a_id

    cols = list(columnas_residuos(topo))
    ids = clase_a_id(topo)
    df = df.sort_values(["cond_id", "lectura"]).reset_index(drop=True)
    df["pred"] = modelo.predict(df[cols])
    df["pred_no_sano"] = df["pred"] != ids["sano"]

    verdad = df.groupby("cond_id").first()
    verdad_no_sano = (verdad["clase"] != "sano").to_numpy()
    verdad_id = verdad["clase"].map(ids).to_numpy()
    n_sanas = int((~verdad_no_sano).sum())
    n_fallas = int(verdad_no_sano.sum())

    pivot_pred = df.pivot(index="cond_id", columns="lectura", values="pred").loc[verdad.index]
    pivot_alarma = df.pivot(index="cond_id", columns="lectura",
                            values="pred_no_sano").loc[verdad.index]

    tabla = {}
    for N in politicas:
        a = pivot_alarma.to_numpy()[:, :N]
        p_ = pivot_pred.to_numpy()[:, :N]
        # DETECCIÓN: se avisa solo si las N lecturas dicen «no sano».
        dispara = a.all(axis=1)
        falsas = int((dispara & ~verdad_no_sano).sum())
        perdidas = int((~dispara & verdad_no_sano).sum())
        # DIAGNÓSTICO: se emite clase solo si las N coinciden en la MISMA clase.
        coinciden = (p_ == p_[:, [0]]).all(axis=1)
        emite = coinciden & dispara
        acierta = int((emite & (p_[:, 0] == verdad_id) & verdad_no_sano).sum())
        tabla[str(N)] = {
            "n_condiciones": int(len(verdad)),
            "deteccion": {
                "falsas_alarmas": falsas,
                "tasa_falsa_alarma": falsas / n_sanas,
                "fallas_perdidas": perdidas,
                "tasa_falla_perdida": perdidas / n_fallas,
                "avisos_emitidos": int(dispara.sum()),
                "precision_del_aviso": float((dispara & verdad_no_sano).sum() / max(int(dispara.sum()), 1)),
            },
            "diagnostico": {
                "ordenes_emitidas": int(emite.sum()),
                "con_clase_correcta": acierta,
                "precision_de_la_orden": acierta / max(int(emite.sum()), 1),
                "cobertura_sobre_fallas": acierta / n_fallas,
            },
        }
    # Predicción binomial, SOLO para contrastar: supone independencia total.
    p1 = tabla["1"]["deteccion"]["tasa_falsa_alarma"]
    for N in politicas:
        tabla[str(N)]["deteccion"]["tasa_falsa_alarma_si_fuera_independiente"] = p1 ** N
    return {"n_condiciones_sanas": n_sanas, "n_condiciones_con_falla": n_fallas,
            "politicas": tabla}


def _umbrales_de_coste(res: dict) -> dict:
    """¿A partir de qué razón de costos conviene cada N?

    Coste esperado por condición, en unidades de «una inspección en vano»:

        C(N) = falsas_alarmas(N)  +  r · fallas_perdidas(N)

    con r = coste de una falla no detectada / coste de una inspección en vano.
    Entre dos políticas consecutivas, el N mayor gana mientras r esté por debajo
    del umbral donde las dos se igualan. NO se recomienda un N: el que convenga
    depende de r, y r lo fija el plan de mantenimiento, no este módulo.
    """
    pol = res["politicas"]
    ns = sorted(pol, key=int)
    umbrales = []
    for a, b in zip(ns, ns[1:]):
        fa_a, fn_a = pol[a]["deteccion"]["falsas_alarmas"], pol[a]["deteccion"]["fallas_perdidas"]
        fa_b, fn_b = pol[b]["deteccion"]["falsas_alarmas"], pol[b]["deteccion"]["fallas_perdidas"]
        d_fn = fn_b - fn_a
        umbrales.append({
            "de_N": int(a), "a_N": int(b),
            "r_umbral": (fa_a - fa_b) / d_fn if d_fn else None,
            "lectura": f"N={b} cuesta menos que N={a} mientras r sea MENOR que el umbral",
        })
    return {
        "definicion_de_r": "coste de una falla no detectada / coste de una inspección en vano",
        "formula": "C(N) = falsas_alarmas(N) + r · fallas_perdidas(N)",
        "umbrales": umbrales,
        "nota": "Este módulo no recomienda un N. El óptimo depende de r, que es una "
                "decisión del plan de mantenimiento.",
    }


def ejecutar(n_muestras: int = 10000, n_lecturas: int = N_LECTURAS,
             verbose: bool = True) -> dict:
    import joblib

    from config.params import SEMILLA_MAESTRA, ParametrosEquipo
    from src.calibracion import aplicar_calibracion

    p = aplicar_calibracion(ParametrosEquipo())
    ruta = DIR_RESULTADOS / "modelo_rf.joblib"
    if not ruta.exists():
        raise SystemExit(f"Falta {ruta.relative_to(RAIZ)}: `python -m src.modelo --sin-informe`.")
    # El conjunto de prevalencia se evalúa con el modelo que lleva
    # `class_weight='balanced'` (src/modelo.py:674-679, :706), no con el
    # principal. Usar el otro daría las cifras de `prevalencia_sin_class_weight`,
    # que son otra fila del informe.
    modelo = joblib.load(ruta)["modelo_balanceado"]

    if verbose:
        print("[1] Generando lecturas repetidas")
    df = generar_lecturas(p, SEMILLA_MAESTRA, n_muestras, n_lecturas, verbose)

    if verbose:
        print("[2] Comprobando que la lectura 0 reproduce el dataset publicado")
    chequeo = comprobar_lectura_cero(df, p.topologia)
    if chequeo["max_abs_dif_residuos"] > 1e-12 or not chequeo["clases_identicas"]:
        raise SystemExit(f"La reconstrucción NO reproduce el dataset: {chequeo}")
    if verbose:
        print(f"    {chequeo['n_comunes']} condiciones comunes, "
              f"diferencia máxima {chequeo['max_abs_dif_residuos']:.2e}")

    if verbose:
        print("[3] Evaluando políticas de persistencia")
    res = evaluar_politicas(df, modelo, p.topologia)
    res["validacion_lectura_cero"] = chequeo
    res["n_lecturas_simuladas"] = n_lecturas
    res["modelo_usado"] = {
        "clave_en_el_joblib": "modelo_balanceado",
        "descripcion": "Random Forest con class_weight='balanced', el mismo que "
                       "evalúa el escenario de prevalencia realista en el informe",
        "origen": "resultados/modelo_rf.joblib, entrenado por src.modelo (src/modelo.py:674-679)",
        "conjunto": "conjunto de prevalencia realista reconstruido con la misma semilla",
    }
    res["umbrales_de_decision"] = _umbrales_de_coste(res)
    res["supuestos"] = [
        "Las N lecturas se toman en el mismo punto de operación; en campo la "
        "carga y el ambiente se mueven entre lecturas y eso no se modela.",
        "El ruido de instrumento es independiente entre lecturas, gaussiano y "
        "con las sigmas de config.params.SIGMA_RUIDO; un sesgo de instrumento "
        "sería sistemático y no se modela.",
        "La discrepancia modelo-planta epsilon es FIJA por condición y no se "
        "promedia al repetir la lectura: es un error de calibración, no ruido.",
        "La falla no progresa entre lecturas.",
    ]
    ruta_json = DIR_RESULTADOS / "persistencia.json"
    ruta_json.write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    if verbose:
        print(f"[4] {ruta_json.relative_to(RAIZ)}")
        for N, t in res["politicas"].items():
            d = t["deteccion"]
            print(f"    N={N}: falsa alarma {d['tasa_falsa_alarma']:.4f} "
                  f"(binomial {d['tasa_falsa_alarma_si_fuera_independiente']:.4f}) | "
                  f"falla perdida {d['tasa_falla_perdida']:.4f}")
    return res


if __name__ == "__main__":
    import argparse, sys
    sys.path.insert(0, str(RAIZ))
    ap = argparse.ArgumentParser(description="Estudio de persistencia del diagnóstico.")
    ap.add_argument("--n-muestras", type=int, default=10000)
    ap.add_argument("--n-lecturas", type=int, default=N_LECTURAS)
    args = ap.parse_args()
    ejecutar(args.n_muestras, args.n_lecturas)
