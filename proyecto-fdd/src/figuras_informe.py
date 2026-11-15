"""Figuras y JSON de métricas para el informe final (export_informe/).

Qué hace y qué NO hace
----------------------
NO vuelve a entrenar ni a decidir nada. Lee el modelo serializado y los datasets
que ya existen, rehace la MISMA partición con la MISMA semilla y vuelve a
evaluar, de modo que todo número que sale de aquí es el que produjo
`src/modelo.py`. Cada valor se contrasta contra `resultados/metricas.json` y, si
difiere, la corrida FALLA en lugar de publicar una figura que no cuadre con el
informe.

Uso:
    python -m src.figuras_informe          # tras `python -m src.modelo`

Salidas:
    export_informe/figuras/*.png   (300 dpi)
    export_informe/metricas.json   (cada número con su origen)
"""

from __future__ import annotations

import json
import platform
import subprocess
from datetime import date
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.metrics import precision_recall_curve
from sklearn.preprocessing import label_binarize

RAIZ = Path(__file__).resolve().parents[1]
DIR_SALIDA = RAIZ / "export_informe"
DIR_FIGURAS = DIR_SALIDA / "figuras"
DIR_RESULTADOS = RAIZ / "resultados"
DPI = 300

TOLERANCIA = 1e-12   # los números deben COINCIDIR, no parecerse


def _commit(ruta: str | None = None) -> str:
    """Commit del repositorio, o el último que tocó un archivo."""
    cmd = ["git", "log", "-1", "--format=%h"] + ([ "--", ruta] if ruta else [])
    try:
        return subprocess.run(cmd, cwd=RAIZ, capture_output=True, text=True,
                              check=True).stdout.strip()
    except Exception:
        return "no disponible"


def _rama() -> str:
    try:
        return subprocess.run(["git", "branch", "--show-current"], cwd=RAIZ,
                              capture_output=True, text=True, check=True).stdout.strip()
    except Exception:
        return "no disponible"


def _arbol_limpio() -> bool:
    try:
        salida = subprocess.run(["git", "status", "--porcelain"], cwd=RAIZ,
                                capture_output=True, text=True, check=True).stdout
        return salida.strip() == ""
    except Exception:
        return False


def _guardar(fig, nombre: str) -> Path:
    DIR_FIGURAS.mkdir(parents=True, exist_ok=True)
    ruta = DIR_FIGURAS / nombre
    fig.savefig(ruta, dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    return ruta


def _versiones() -> dict:
    import CoolProp, joblib, scipy, sklearn
    return {
        "python": platform.python_version(),
        "numpy": np.__version__,
        "scipy": scipy.__version__,
        "pandas": pd.__version__,
        "scikit-learn": sklearn.__version__,
        "matplotlib": matplotlib.__version__,
        "seaborn": sns.__version__,
        "joblib": joblib.__version__,
        "CoolProp": CoolProp.__version__,
    }


# ---------------------------------------------------------------------------
# Reevaluación: mismos datos, misma partición, misma semilla
# ---------------------------------------------------------------------------
def reevaluar() -> dict:
    import joblib

    from config.params import SEMILLA_MAESTRA, ParametrosEquipo
    from src.calibracion import aplicar_calibracion
    from src.fallas import clases
    from src.features import construir_matriz_X
    from src.modelo import COLUMNAS_EXTRA, evaluar, particionar

    ruta_modelo = DIR_RESULTADOS / "modelo_rf.joblib"
    if not ruta_modelo.exists():
        raise SystemExit(
            f"Falta {ruta_modelo.relative_to(RAIZ)}. Está excluido del repositorio "
            "por tamaño: regenéralo con `python -m src.modelo --sin-informe`.")

    p = aplicar_calibracion(ParametrosEquipo())
    topo = p.topologia
    nombres = list(clases(topo))
    paquete = joblib.load(ruta_modelo)
    # OJO: son DOS modelos. El escenario de prevalencia se evalúa con el que
    # lleva `class_weight="balanced"` (src/modelo.py:674-679, :706); usar el
    # principal daría las cifras de `prevalencia_sin_class_weight`, que son otra
    # fila del informe. La comprobación contra metricas.json lo detectaría, pero
    # es mejor no equivocarse de modelo a propósito.
    modelo = paquete["modelo"]
    modelo_prev = paquete["modelo_balanceado"]

    df_bal = pd.read_parquet(RAIZ / "data" / "dataset_balanceado.parquet")
    df_prev = pd.read_parquet(RAIZ / "data" / "dataset_prevalencia.parquet")
    part = particionar(df_bal, topo, SEMILLA_MAESTRA)

    # El conjunto sellado ya se abrió en la corrida de `src.modelo`; aquí solo se
    # vuelve a LEER para dibujar. No hay decisión que tomar con estos datos.
    X_te, y_te = part.sellado._X, np.asarray(part.sellado._y)
    extra_te = part.sellado._extra
    res_bal = evaluar(modelo, X_te, y_te, "prueba_balanceada", nombres)

    X_prev = construir_matriz_X(df_prev, topo)
    res_prev = evaluar(modelo_prev, X_prev, np.asarray(df_prev["clase_id"]),
                       "prevalencia_realista", nombres)
    return {"res_bal": res_bal, "res_prev": res_prev, "extra_te": extra_te,
            "nombres": nombres, "modelo": modelo, "modelo_prev": modelo_prev,
            "paquete": paquete}


def comprobar_contra_metricas(res_bal, res_prev, guardadas: dict) -> list[str]:
    """Las figuras deben contar lo mismo que `resultados/metricas.json`."""
    fallos = []
    pares = [("prueba_balanceada", res_bal), ("prevalencia_realista", res_prev)]
    for clave, res in pares:
        ref = guardadas["metricas"][clave]
        for campo in ("f1_macro", "pr_auc_macro", "exactitud_global", "n_muestras"):
            if abs(float(res[campo]) - float(ref[campo])) > TOLERANCIA:
                fallos.append(f"{clave}.{campo}: recalculado {res[campo]!r} "
                              f"frente a {ref[campo]!r} en metricas.json")
        for c, v in res["f1_por_clase"].items():
            if abs(float(v) - float(ref["f1_por_clase"][c])) > TOLERANCIA:
                fallos.append(f"{clave}.f1_por_clase[{c}]: {v!r} vs "
                              f"{ref['f1_por_clase'][c]!r}")
    return fallos


# ---------------------------------------------------------------------------
# Figuras
# ---------------------------------------------------------------------------
def fig_matriz(res, titulo, archivo, nombres) -> Path:
    mc = np.array(res["matriz_confusion_normalizada"])
    fig, ax = plt.subplots(figsize=(9.5, 8))
    sns.heatmap(mc, annot=True, fmt=".2f", cmap="Blues", cbar=True, vmin=0, vmax=1,
                xticklabels=nombres, yticklabels=nombres, ax=ax,
                annot_kws={"size": 7})
    ax.set_title(f"{titulo}\n(normalizada por fila; n = {res['n_muestras']})")
    ax.set_xlabel("Predicción"); ax.set_ylabel("Realidad")
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
    return _guardar(fig, archivo)


def fig_pr(res, titulo, archivo, nombres) -> Path:
    y, proba = res["_y"], res["_y_proba"]
    y_bin = label_binarize(y, classes=list(range(len(nombres))))
    fig, ax = plt.subplots(figsize=(8, 6))
    colores = sns.color_palette("tab20", len(nombres))
    for i, c in enumerate(nombres):
        if y_bin[:, i].sum() == 0:
            continue
        prec, rec, _ = precision_recall_curve(y_bin[:, i], proba[:, i])
        ax.plot(rec, prec, color=colores[i], lw=1.6,
                label=f"{c} (AP={res['pr_auc_por_clase'][c]:.3f})")
    ax.set_xlabel("Sensibilidad (recall)"); ax.set_ylabel("Precisión")
    ax.set_title(f"Curvas precisión-sensibilidad por clase — {titulo}\n"
                 f"PR-AUC macro = {res['pr_auc_macro']:.4f}")
    ax.legend(fontsize=7, loc="lower left")
    ax.set_xlim(0, 1); ax.set_ylim(0, 1.02)
    return _guardar(fig, archivo)


def fig_f1_por_clase(res_bal, res_prev, nombres) -> Path:
    """Figura que el pipeline no producía: F1 por clase en los dos escenarios."""
    orden = sorted(nombres, key=lambda c: res_bal["f1_por_clase"][c])
    y = np.arange(len(orden))
    bal = [res_bal["f1_por_clase"][c] for c in orden]
    prev = [res_prev["f1_por_clase"][c] for c in orden]
    fig, ax = plt.subplots(figsize=(9, 6))
    h = 0.4
    ax.barh(y + h / 2, bal, height=h, label=f"Prueba balanceada (macro {res_bal['f1_macro']:.4f})",
            color=sns.color_palette("Blues", 3)[2])
    ax.barh(y - h / 2, prev, height=h,
            label=f"Prevalencia realista (macro {res_prev['f1_macro']:.4f})",
            color=sns.color_palette("Oranges", 3)[1])
    ax.axvline(res_bal["f1_macro"], color="#1b5fa8", ls="--", lw=1)
    ax.axvline(res_prev["f1_macro"], color="#b8651b", ls="--", lw=1)
    ax.set_yticks(y, orden, fontsize=9)
    ax.set_xlim(0, 1)
    ax.set_xlabel("F1 por clase")
    ax.set_title("F1 por clase en los dos conjuntos de prueba\n"
                 "(líneas discontinuas: F1 macro de cada escenario)")
    # La leyenda va FUERA del área de trazado: dentro tapaba la barra de `sano`,
    # que es justo la clase cuyo contraste entre escenarios hay que ver.
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.09), ncols=2, fontsize=9,
              frameon=False)
    ax.grid(axis="x", alpha=.25)
    return _guardar(fig, "fig4_f1_por_clase.png")


def fig_deteccion(res_bal, extra_te) -> tuple[Path, dict]:
    d = extra_te.copy()
    d["acierto"] = (res_bal["_y"] == res_bal["_y_pred"])
    d = d[d["clase"] != "sano"]
    bins = np.arange(0.15, 1.01, 0.10)
    d["tramo"] = pd.cut(d["severidad_f"], bins=bins, include_lowest=True)
    tabla = {}
    fig, ax = plt.subplots(figsize=(9, 6))
    colores = sns.color_palette("tab20", d["clase"].nunique())
    for i, (clase, g) in enumerate(d.groupby("clase", observed=True)):
        serie = g.groupby("tramo", observed=True)["acierto"].mean()
        centros = [iv.mid for iv in serie.index]
        ax.plot(centros, serie.values, marker="o", ms=4, lw=1.5,
                color=colores[i], label=clase)
        tabla[clase] = {str(k): (None if pd.isna(v) else float(v))
                        for k, v in serie.items()}
    ax.set_xlabel("Severidad de la falla  f")
    ax.set_ylabel("Fracción diagnosticada correctamente")
    ax.set_title("Detección frente a severidad — conjunto de prueba balanceado\n"
                 "(solo clases con falla; la clase sana no tiene severidad)")
    ax.set_ylim(-0.02, 1.05)
    ax.grid(alpha=.25)
    ax.legend(fontsize=8, ncols=5, loc="upper center", bbox_to_anchor=(0.5, -0.1),
              frameon=False)
    return _guardar(fig, "fig5_deteccion_por_severidad.png"), tabla


# ---------------------------------------------------------------------------
# Orquestación
# ---------------------------------------------------------------------------
def generar(verbose: bool = True) -> dict:
    ruta_met = DIR_RESULTADOS / "metricas.json"
    if not ruta_met.exists():
        raise SystemExit(f"Falta {ruta_met.relative_to(RAIZ)}: corre `python -m src.modelo`.")
    guardadas = json.loads(ruta_met.read_text("utf-8"))

    # El estado de git se captura ANTES de escribir nada: si se leyera después,
    # las propias figuras recién escritas ensuciarían el árbol y el campo diría
    # siempre `false`.
    git = {"rama": _rama(), "commit_codigo": _commit(),
           "arbol_git_limpio_al_generar": _arbol_limpio()}

    r = reevaluar()
    res_bal, res_prev, nombres = r["res_bal"], r["res_prev"], r["nombres"]

    fallos = comprobar_contra_metricas(res_bal, res_prev, guardadas)
    if fallos:
        raise SystemExit("Las figuras no cuadran con resultados/metricas.json:\n  "
                         + "\n  ".join(fallos))
    if verbose:
        print(f"[1] Reevaluación idéntica a resultados/metricas.json "
              f"(tolerancia {TOLERANCIA:g})")

    DIR_FIGURAS.mkdir(parents=True, exist_ok=True)
    figs = {}
    figs["fig1_matriz_confusion_balanceada"] = fig_matriz(
        res_bal, "Matriz de confusión — prueba balanceada",
        "fig1_matriz_confusion_balanceada.png", nombres)
    figs["fig2_matriz_confusion_prevalencia"] = fig_matriz(
        res_prev, "Matriz de confusión — prevalencia realista (68 % sano)",
        "fig2_matriz_confusion_prevalencia.png", nombres)
    figs["fig3a_curvas_pr_balanceada"] = fig_pr(
        res_bal, "prueba balanceada", "fig3a_curvas_pr_balanceada.png", nombres)
    figs["fig3b_curvas_pr_prevalencia"] = fig_pr(
        res_prev, "prevalencia realista", "fig3b_curvas_pr_prevalencia.png", nombres)
    figs["fig4_f1_por_clase"] = fig_f1_por_clase(res_bal, res_prev, nombres)
    ruta_det, tabla_det = fig_deteccion(res_bal, r["extra_te"])
    figs["fig5_deteccion_por_severidad"] = ruta_det
    if verbose:
        for k, v in figs.items():
            print(f"    {v.relative_to(RAIZ)}  ({v.stat().st_size/1000:.0f} kB)")

    # --- metricas.json del informe -----------------------------------------
    def origen(clave, funcion):
        return {"archivo": "resultados/metricas.json", "clave": clave,
                "funcion": funcion, "commit_codigo": _commit()}

    salida = {
        "_lee_esto_primero": (
            "Cada número lleva su origen: archivo, clave, función que lo calcula y "
            "commit del código. Los valores se recalcularon con `src.figuras_informe` "
            "a partir de `resultados/modelo_rf.joblib` y se comprobaron uno a uno "
            "contra `resultados/metricas.json`; si hubieran diferido, esta corrida "
            "habría fallado en lugar de publicar."),
        "generado": date.today().isoformat(),
        "procedencia": {
            **git,
            "commit_de_resultados_metricas_json": _commit("resultados/metricas.json"),
            "commit_de_los_datasets": _commit("data/dataset_balanceado.parquet"),
            "semilla_maestra": guardadas["semilla_maestra"],
            "comandos": [
                "python -m src.modelo --sin-informe",
                "python -m src.figuras_informe",
            ],
            "topologia": guardadas["topologia"],
            "nivel_discrepancia": guardadas["nivel_discrepancia"],
            "modo_discrepancia": guardadas["modo_discrepancia"],
            "factor_ruido": guardadas["generacion"]["factor_ruido"],
        },
        "entorno": _versiones(),
        "modelo": {
            "familia": guardadas["seleccion_de_modelo"]["ganador"],
            "criterio_de_seleccion": guardadas["seleccion_de_modelo"]["criterio"],
            "hiperparametros": guardadas["seleccion_de_modelo"]["candidatos"][
                guardadas["seleccion_de_modelo"]["ganador"]]["mejores_parametros"],
            "origen": origen("seleccion_de_modelo", "src.modelo.seleccionar_modelo"),
        },
        "particion": {"valores": guardadas["particion"],
                      "origen": origen("particion", "src.modelo.particionar")},
        "columnas_de_entrada": {
            "valores": guardadas["columnas_de_entrada"],
            "origen": {"archivo": "src/features.py",
                       "funcion": "columnas_residuos (lista blanca)",
                       "commit_codigo": _commit("src/features.py")}},
        "resultados": {},
        "deteccion_por_severidad": {
            "valores": tabla_det,
            "origen": {"archivo": "src/figuras_informe.py", "funcion": "fig_deteccion",
                       "commit_codigo": _commit(),
                       "nota": "equivale a `deteccion_vs_severidad` de "
                               "resultados/metricas.json, calculada por src.modelo."
                               "fig_deteccion_vs_severidad"}},
        "figuras": {k: str(v.relative_to(DIR_SALIDA)) for k, v in figs.items()},
    }

    for clave, res in (("prueba_balanceada", res_bal), ("prevalencia_realista", res_prev)):
        salida["resultados"][clave] = {
            "n_muestras": res["n_muestras"],
            "f1_macro": res["f1_macro"],
            "f1_ponderado": res["f1_ponderado"],
            "recall_macro": res["recall_macro"],
            "pr_auc_macro": res["pr_auc_macro"],
            "exactitud_global": res["exactitud_global"],
            "f1_por_clase": res["f1_por_clase"],
            "recall_por_clase": res["recall_por_clase"],
            "pr_auc_por_clase": res["pr_auc_por_clase"],
            "matriz_confusion": res["matriz_confusion"],
            "intervalos_wilson": res["intervalos_wilson"],
            "origen": origen(f"metricas.{clave}", "src.modelo.evaluar"),
        }

    # --- alarma de fuga de datos -------------------------------------------
    alarmas = []
    for clave, res in (("prueba_balanceada", res_bal), ("prevalencia_realista", res_prev)):
        if res["exactitud_global"] > 0.95:
            alarmas.append(f"{clave}: exactitud {res['exactitud_global']:.4f} > 0,95")
        if res["f1_macro"] > 0.95:
            alarmas.append(f"{clave}: F1 macro {res['f1_macro']:.4f} > 0,95")
    salida["alarma_de_fuga"] = {
        "umbral": 0.95,
        "criterio": "exactitud o F1 macro por encima de 0,95 en datos no vistos",
        "disparada": bool(alarmas),
        "detalle": alarmas or ["ninguna métrica supera el umbral"],
        "controles_estructurales": {
            "lista_blanca_de_columnas": "src/features.py::construir_matriz_X",
            "particion_por_grupos": "src/modelo.py::particionar (GroupShuffleSplit "
                                    "sobre cond_id)",
            "condiciones_compartidas_entre_particiones":
                guardadas["particion"]["condiciones_compartidas_entre_particiones"],
            "aperturas_del_conjunto_de_prueba":
                guardadas["aperturas_del_conjunto_de_prueba"],
            "corrida_valida": guardadas["corrida_valida"],
        },
    }

    DIR_SALIDA.mkdir(parents=True, exist_ok=True)
    ruta = DIR_SALIDA / "metricas.json"
    ruta.write_text(json.dumps(salida, indent=2, ensure_ascii=False), encoding="utf-8")
    if verbose:
        print(f"[2] {ruta.relative_to(RAIZ)}")
        print(f"[3] Alarma de fuga: {'SÍ' if alarmas else 'no'} — "
              f"{'; '.join(alarmas) if alarmas else 'ninguna métrica supera 0,95'}")
    return salida


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(RAIZ))
    generar()
