"""Entrenamiento, evaluación y análisis del clasificador FDD.

REGLA VINCULANTE DEL PROYECTO (Regla 3 de la auditoría, defecto D7)
------------------------------------------------------------------
La comparación entre el clasificador base y el Random Forest, y la elección de
hiperparámetros, se resuelven EXCLUSIVAMENTE con el conjunto de validación. El
conjunto de prueba se toca UNA SOLA VEZ, al final, para reportar.

Y esa regla la impone la estructura del código, no la disciplina de quien lo
corra:

  * `ConjuntoSellado` cuenta cada apertura y registra el motivo.
  * `seleccionar_modelo()` recibe en su firma únicamente
    (X_tr, y_tr, grupos_tr, X_val, y_val): no tiene acceso léxico a los
    conjuntos de prueba, así que no puede evaluarlos aunque alguien modifique
    el cuerpo de la función por descuido.
  * Si al terminar la corrida algún conjunto sellado registra más de una
    apertura, `metricas.json` marca `corrida_valida: false`.

Otras reglas heredadas de la auditoría:
  * Regla 1 — la matriz X se construye por lista blanca `res_*` (src.features).
  * Regla 2 — sin SMOTE: el conjunto balanceado ya nace balanceado del simulador
    y el desbalance de campo se trata con `class_weight='balanced'`.
  * GridSearchCV optimiza F1 MACRO, nunca exactitud (defecto D4).
"""

from __future__ import annotations

import json
import warnings
from dataclasses import dataclass, field
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.inspection import permutation_importance
from sklearn.metrics import (accuracy_score, average_precision_score,
                             classification_report, confusion_matrix, f1_score,
                             mean_absolute_error, precision_recall_curve, r2_score,
                             recall_score)
from sklearn.model_selection import GridSearchCV, GroupKFold, GroupShuffleSplit
from sklearn.preprocessing import label_binarize
from sklearn.tree import DecisionTreeClassifier

from config.params import SEMILLA_MAESTRA
from .fallas import CLASES, FIRMAS_ESPERADAS, RESIDUO_CARACTERISTICO
from .features import COLUMNAS_RESIDUOS, construir_matriz_X

RAIZ = Path(__file__).resolve().parents[1]
DIR_FIGURAS = RAIZ / "figuras"
DIR_RESULTADOS = RAIZ / "resultados"
DPI = 300

sns.set_theme(style="whitegrid", context="paper")


# ===========================================================================
# Conjunto sellado: control estructural del acceso al conjunto de prueba
# ===========================================================================
class ConjuntoSellado:
    """Contenedor que solo se abre explícitamente y lleva la cuenta.

    No es un adorno: es el mecanismo que convierte «no mirar el test todavía»
    de intención en control verificable.
    """

    def __init__(self, nombre: str, X: pd.DataFrame, y: pd.Series, extra: pd.DataFrame):
        self._nombre = nombre
        self._X, self._y, self._extra = X, y, extra
        self._aperturas: list[str] = []

    @property
    def nombre(self) -> str:
        return self._nombre

    @property
    def n_aperturas(self) -> int:
        return len(self._aperturas)

    @property
    def aperturas(self) -> list[str]:
        return list(self._aperturas)

    @property
    def n_filas(self) -> int:
        return len(self._y)

    def abrir(self, motivo: str):
        self._aperturas.append(motivo)
        if len(self._aperturas) > 1:
            warnings.warn(
                f"El conjunto sellado `{self._nombre}` se abrió {len(self._aperturas)} veces. "
                f"La corrida quedará marcada como NO VÁLIDA. Motivos: {self._aperturas}",
                stacklevel=2)
        return self._X, self._y, self._extra

    def __repr__(self) -> str:
        return f"<ConjuntoSellado {self._nombre}: {self.n_filas} filas, {self.n_aperturas} aperturas>"


# ===========================================================================
# Partición por GRUPOS de condición de contorno
# ===========================================================================
@dataclass
class Particion:
    X_tr: pd.DataFrame
    y_tr: pd.Series
    g_tr: pd.Series
    X_val: pd.DataFrame
    y_val: pd.Series
    extra_val: pd.DataFrame
    sellado: ConjuntoSellado
    conds: dict[str, set] = field(default_factory=dict)


def particionar(df: pd.DataFrame, semilla: int, prop_tr: float = 0.70,
                prop_val: float = 0.15) -> Particion:
    """Partición 70/15/15 POR GRUPOS de `cond_id` (sección 7.1).

    Una condición de contorno genera 30 filas (10 clases × 3 niveles). Partir
    por fila metería la misma condición en entrenamiento y en prueba, que es
    exactamente la fuga entre conjuntos que la especificación prohíbe.

    La estratificación por clase sale sola: cada condición aporta el mismo
    número de filas de cada clase, así que un corte por condiciones preserva el
    balance. `test_particion.py` lo verifica en lugar de suponerlo.
    """
    X = construir_matriz_X(df)          # LISTA BLANCA
    y = df["clase_id"]
    g = df["cond_id"]

    gss1 = GroupShuffleSplit(n_splits=1, train_size=prop_tr, random_state=semilla)
    idx_tr, idx_resto = next(gss1.split(X, y, groups=g))

    resto_frac_val = prop_val / (1.0 - prop_tr)
    gss2 = GroupShuffleSplit(n_splits=1, train_size=resto_frac_val, random_state=semilla + 1)
    idx_val_rel, idx_test_rel = next(
        gss2.split(X.iloc[idx_resto], y.iloc[idx_resto], groups=g.iloc[idx_resto]))
    idx_val = idx_resto[idx_val_rel]
    idx_test = idx_resto[idx_test_rel]

    extra_cols = ["clase", "severidad_f", "nivel", "cond_id"]
    sellado = ConjuntoSellado("prueba_balanceada", X.iloc[idx_test], y.iloc[idx_test],
                              df.iloc[idx_test][extra_cols])
    return Particion(
        X_tr=X.iloc[idx_tr], y_tr=y.iloc[idx_tr], g_tr=g.iloc[idx_tr],
        X_val=X.iloc[idx_val], y_val=y.iloc[idx_val],
        extra_val=df.iloc[idx_val][extra_cols],
        sellado=sellado,
        conds={"train": set(g.iloc[idx_tr]), "val": set(g.iloc[idx_val]),
               "test": set(g.iloc[idx_test])},
    )


# ===========================================================================
# Selección de modelo — SIN acceso al conjunto de prueba
# ===========================================================================
REJILLA_RF = {
    "n_estimators": [300],
    "max_depth": [None, 16],
    "min_samples_leaf": [1, 2, 4],
    "max_features": ["sqrt", 0.5],
}
REJILLA_DT = {
    "max_depth": [8, 16, None],
    "min_samples_leaf": [1, 2, 4],
    "min_samples_split": [2, 10],
}


def seleccionar_modelo(X_tr, y_tr, g_tr, X_val, y_val, semilla: int, verbose: bool = True):
    """Busca hiperparámetros y elige entre Árbol y Random Forest.

    La firma de esta función es deliberadamente estrecha: recibe entrenamiento y
    validación, y nada más. No puede tocar el conjunto de prueba.

    GridSearchCV optimiza F1 MACRO (defecto D4 de la auditoría) y usa GroupKFold
    sobre `cond_id`, para que tampoco haya fuga de condiciones entre pliegues.
    """
    cv = GroupKFold(n_splits=4)
    resultados = {}

    candidatos = {
        "arbol_decision": (DecisionTreeClassifier(random_state=semilla), REJILLA_DT),
        "random_forest": (RandomForestClassifier(random_state=semilla, n_jobs=-1), REJILLA_RF),
    }
    for nombre, (estimador, rejilla) in candidatos.items():
        if verbose:
            print(f"  GridSearchCV [{nombre}] — scoring='f1_macro', GroupKFold(4)")
        gs = GridSearchCV(estimator=estimador, param_grid=rejilla, cv=cv,
                          scoring="f1_macro", n_jobs=-1, refit=True)
        gs.fit(X_tr, y_tr, groups=g_tr)
        # La decisión se toma con VALIDACIÓN, no con el CV interno ni con prueba.
        f1_val = f1_score(y_val, gs.best_estimator_.predict(X_val), average="macro")
        resultados[nombre] = {
            "mejores_parametros": gs.best_params_,
            "f1_macro_cv": float(gs.best_score_),
            "f1_macro_validacion": float(f1_val),
            "estimador": gs.best_estimator_,
        }
        if verbose:
            print(f"    mejores parámetros : {gs.best_params_}")
            print(f"    F1 macro (CV)      : {gs.best_score_:.4f}")
            print(f"    F1 macro (VALID.)  : {f1_val:.4f}")

    ganador = max(resultados, key=lambda k: resultados[k]["f1_macro_validacion"])
    if verbose:
        print(f"  -> modelo elegido con el conjunto de VALIDACIÓN: {ganador}")
    return ganador, resultados


# ===========================================================================
# Evaluación
# ===========================================================================
def evaluar(modelo, X, y, nombre_conjunto: str, clases=CLASES) -> dict:
    """Métricas en el orden que fija la sección 7.3: la exactitud va al final."""
    y_pred = modelo.predict(X)
    y_proba = modelo.predict_proba(X)
    etiquetas = list(range(len(clases)))
    presentes = sorted(set(y) | set(y_pred))

    mc = confusion_matrix(y, y_pred, labels=etiquetas)
    with np.errstate(invalid="ignore"):
        mc_norm = mc / np.maximum(mc.sum(axis=1, keepdims=True), 1)

    reporte = classification_report(y, y_pred, labels=etiquetas,
                                    target_names=list(clases), output_dict=True,
                                    zero_division=0)
    # PR-AUC por clase (Saito y Rehmsmeier, 2015)
    y_bin = label_binarize(y, classes=etiquetas)
    pr_auc = {}
    for i, c in enumerate(clases):
        if y_bin[:, i].sum() == 0:
            pr_auc[c] = None
            continue
        pr_auc[c] = float(average_precision_score(y_bin[:, i], y_proba[:, i]))

    proporciones = pd.Series(y).map(dict(enumerate(clases))).value_counts(normalize=True)

    return {
        "conjunto": nombre_conjunto,
        "n_muestras": int(len(y)),
        "matriz_confusion": mc.tolist(),
        "matriz_confusion_normalizada": np.nan_to_num(mc_norm).tolist(),
        "recall_por_clase": {c: float(reporte[c]["recall"]) for c in clases},
        "f1_por_clase": {c: float(reporte[c]["f1-score"]) for c in clases},
        "precision_por_clase": {c: float(reporte[c]["precision"]) for c in clases},
        "soporte_por_clase": {c: int(reporte[c]["support"]) for c in clases},
        "f1_macro": float(f1_score(y, y_pred, average="macro", labels=presentes,
                                   zero_division=0)),
        "f1_ponderado": float(f1_score(y, y_pred, average="weighted", zero_division=0)),
        "recall_macro": float(recall_score(y, y_pred, average="macro", labels=presentes,
                                           zero_division=0)),
        "pr_auc_por_clase": pr_auc,
        "pr_auc_macro": float(np.mean([v for v in pr_auc.values() if v is not None])),
        "exactitud_global": float(accuracy_score(y, y_pred)),
        "proporcion_de_clases": proporciones.to_dict(),
        "texto_reporte": classification_report(y, y_pred, labels=etiquetas,
                                               target_names=list(clases), zero_division=0),
        "_y": np.asarray(y), "_y_pred": y_pred, "_y_proba": y_proba,
    }


def tasa_deteccion(y_true, y_pred) -> float:
    """Detección = distinguir sano de no-sano, con independencia del diagnóstico."""
    sano = 0
    return float(np.mean((np.asarray(y_true) == sano) == (np.asarray(y_pred) == sano)))


# ===========================================================================
# Figuras (300 dpi, listas para el informe)
# ===========================================================================
def _guardar(fig, nombre: str) -> Path:
    DIR_FIGURAS.mkdir(parents=True, exist_ok=True)
    ruta = DIR_FIGURAS / nombre
    fig.savefig(ruta, dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    return ruta


def fig_matriz_confusion(res: dict, titulo: str, nombre_archivo: str) -> Path:
    """Matriz de confusión NORMALIZADA POR FILA (sección 7.3, punto 1)."""
    mc = np.array(res["matriz_confusion_normalizada"])
    fig, ax = plt.subplots(figsize=(9, 7.5))
    sns.heatmap(mc, annot=True, fmt=".2f", cmap="Blues", cbar=True, vmin=0, vmax=1,
                xticklabels=CLASES, yticklabels=CLASES, ax=ax,
                annot_kws={"size": 7})
    ax.set_title(f"{titulo}\n(normalizada por fila; n = {res['n_muestras']})")
    ax.set_xlabel("Predicción")
    ax.set_ylabel("Realidad")
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
    return _guardar(fig, nombre_archivo)


def fig_curvas_pr(res: dict, titulo: str, nombre_archivo: str) -> Path:
    y, proba = res["_y"], res["_y_proba"]
    y_bin = label_binarize(y, classes=list(range(len(CLASES))))
    fig, ax = plt.subplots(figsize=(8, 6))
    colores = sns.color_palette("tab10", len(CLASES))
    for i, c in enumerate(CLASES):
        if y_bin[:, i].sum() == 0:
            continue
        prec, rec, _ = precision_recall_curve(y_bin[:, i], proba[:, i])
        ax.plot(rec, prec, color=colores[i], lw=1.6,
                label=f"{c} (AP={res['pr_auc_por_clase'][c]:.3f})")
    ax.set_xlabel("Recall"); ax.set_ylabel("Precisión")
    ax.set_title(f"Curvas precisión-recall por clase — {titulo}")
    ax.legend(fontsize=7, loc="lower left")
    ax.set_xlim(0, 1); ax.set_ylim(0, 1.02)
    return _guardar(fig, nombre_archivo)


def fig_importancia_permutacion(modelo, X_val, y_val, semilla: int) -> tuple[Path, dict]:
    imp = permutation_importance(modelo, X_val, y_val, n_repeats=10,
                                 random_state=semilla, scoring="f1_macro", n_jobs=-1)
    orden = np.argsort(imp.importances_mean)
    fig, ax = plt.subplots(figsize=(8, 5.5))
    ax.barh(np.array(COLUMNAS_RESIDUOS)[orden], imp.importances_mean[orden],
            xerr=imp.importances_std[orden], color=sns.color_palette("crest", 1)[0])
    ax.set_xlabel("Caída de F1 macro al permutar la característica")
    ax.set_title("Importancia por permutación (conjunto de validación)")
    ruta = _guardar(fig, "fig4_importancia_permutacion.png")
    tabla = {c: {"media": float(m), "desv": float(s)}
             for c, m, s in zip(COLUMNAS_RESIDUOS, imp.importances_mean, imp.importances_std)}
    return ruta, tabla


def fig_deteccion_vs_severidad(res: dict, extra: pd.DataFrame) -> tuple[Path, dict]:
    """¿Desde qué nivel de degradación se detecta cada falla? (sección 7.3, punto 7)"""
    d = extra.copy()
    d["acierto"] = (res["_y"] == res["_y_pred"])
    d = d[d["clase"] != "sano"]
    bins = np.arange(0.15, 1.01, 0.10)
    d["bin"] = pd.cut(d["severidad_f"], bins=bins)
    tabla = d.groupby(["clase", "bin"], observed=True)["acierto"].mean().unstack()

    fig, ax = plt.subplots(figsize=(8.5, 5.5))
    centros = [iv.mid for iv in tabla.columns]
    colores = sns.color_palette("tab10", len(tabla.index))
    for (clase, fila), color in zip(tabla.iterrows(), colores):
        ax.plot(centros, fila.values, marker="o", ms=4, lw=1.5, label=clase, color=color)
    ax.axvspan(0.15, 0.35, alpha=0.10, color="grey")
    ax.text(0.25, 0.02, "incipiente", ha="center", fontsize=8, color="dimgrey")
    ax.set_xlabel("Severidad f"); ax.set_ylabel("Exactitud de diagnóstico")
    ax.set_title("Curva de detección frente a severidad")
    ax.set_ylim(-0.02, 1.05)
    ax.legend(fontsize=7, ncol=2)
    ruta = _guardar(fig, "fig5_deteccion_vs_severidad.png")
    return ruta, {c: {str(k): (None if pd.isna(v) else float(v)) for k, v in f.items()}
                  for c, f in tabla.iterrows()}


def fig_mapa_firmas(df: pd.DataFrame) -> Path:
    """Figura 7: heatmap de residuo medio por clase (mapa de firmas).

    Es la figura que mejor comunica la idea en una defensa oral: se ve de un
    vistazo que cada modo de falla deja una huella distinta.
    """
    sub = df[df["nivel"].isin(["severa", "sano"])]
    medias = sub.groupby("clase")[list(COLUMNAS_RESIDUOS)].mean()
    # Estandarización por columna para que residuos de escalas distintas
    # (K, adimensional, kW/TR) sean comparables visualmente.
    z = (medias - medias.mean()) / medias.std(ddof=0).replace(0, 1)
    z = z.reindex(list(CLASES))
    fig, ax = plt.subplots(figsize=(10, 5.5))
    sns.heatmap(z, cmap="RdBu_r", center=0, annot=medias.reindex(list(CLASES)).values,
                fmt=".2f", annot_kws={"size": 6}, ax=ax,
                cbar_kws={"label": "residuo medio estandarizado"})
    ax.set_title("Mapa de firmas: residuo medio por clase (nivel severo)\n"
                 "color = valor estandarizado por columna; número = residuo medio en unidades físicas")
    ax.set_xlabel(""); ax.set_ylabel("")
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
    return _guardar(fig, "fig7_mapa_firmas.png")


def fig_diagrama_ph(p, clase_degradada: str = "condensador_sucio", f: float = 0.8) -> Path:
    """Figura 1: ciclo sano frente a ciclo degradado, superpuestos."""
    import CoolProp.CoolProp as CP
    from .ciclo import AjustesCiclo, CondicionContorno, resolver_ciclo
    from .fallas import ajustes_de_falla

    cond = CondicionContorno(32.0, 80.0, 24.0, 0.90)
    sano = resolver_ciclo(cond, p, AjustesCiclo())
    degr = resolver_ciclo(cond, p, ajustes_de_falla(clase_degradada, f, p))

    fig, ax = plt.subplots(figsize=(8, 6))
    # Campana de saturación
    t_min, t_crit = -30.0, CP.PropsSI("Tcrit", p.refrigerante) - 273.15
    temps = np.linspace(t_min, t_crit - 0.5, 220)
    h_liq, h_vap, p_sat = [], [], []
    for t in temps:
        try:
            h_liq.append(CP.PropsSI("H", "T", t + 273.15, "Q", 0, p.refrigerante) / 1000)
            h_vap.append(CP.PropsSI("H", "T", t + 273.15, "Q", 1, p.refrigerante) / 1000)
            p_sat.append(CP.PropsSI("P", "T", t + 273.15, "Q", 0, p.refrigerante) / 1000)
        except Exception:
            h_liq.append(np.nan); h_vap.append(np.nan); p_sat.append(np.nan)
    ax.plot(h_liq, p_sat, color="grey", lw=1)
    ax.plot(h_vap, p_sat, color="grey", lw=1, label="campana de saturación")

    for estado, color, etiqueta in ((sano, "tab:blue", "sano"),
                                    (degr, "tab:red", f"{clase_degradada} (f={f:.2f})")):
        h = np.array([estado.h1, estado.h2a, estado.h3, estado.h4, estado.h1]) / 1000
        pr = np.array([estado.P_suc_pa, estado.P_des_pa, estado.P_des_pa,
                       estado.P_suc_pa, estado.P_suc_pa]) / 1000
        ax.plot(h, pr, marker="o", ms=4, lw=1.8, color=color,
                label=f"{etiqueta}: T_ev={estado.T_evap:.1f} °C, T_cd={estado.T_cond:.1f} °C")
    ax.set_yscale("log")
    ax.set_xlabel("Entalpía específica h [kJ/kg]")
    ax.set_ylabel("Presión [kPa]")
    ax.set_title(f"Diagrama P-h — {p.refrigerante}\n"
                 f"T_amb={cond.T_amb:.0f} °C, carga={cond.Q_load_frac:.0%}")
    ax.legend(fontsize=8, loc="upper left")
    return _guardar(fig, "fig1_diagrama_ph.png")


def fig_sensibilidad_ruido(tabla: dict) -> Path:
    """Figura 6: ¿qué exactitud de instrumento hace falta para que esto funcione?"""
    factores = sorted(tabla)
    fig, ax = plt.subplots(figsize=(7.5, 5))
    series = {
        "F1 macro (todas las severidades)": [tabla[f]["f1_macro"] for f in factores],
        "Exactitud de diagnóstico, nivel incipiente": [tabla[f]["diagnostico_incipiente"] for f in factores],
        "Tasa de detección sano/no-sano, incipiente": [tabla[f]["deteccion_incipiente"] for f in factores],
    }
    for (etiqueta, valores), marca in zip(series.items(), ["o", "s", "^"]):
        ax.plot([float(f) for f in factores], valores, marker=marca, lw=1.8, label=etiqueta)
    ax.axvline(1.0, color="grey", ls="--", lw=1)
    ax.text(1.02, 0.02, "instrumentos de la Fase 1", fontsize=8, color="dimgrey")
    ax.set_xlabel("Factor multiplicador del ruido de los instrumentos")
    ax.set_ylabel("Desempeño")
    ax.set_title("Sensibilidad al ruido de los instrumentos")
    ax.set_ylim(0, 1.05)
    ax.legend(fontsize=8)
    return _guardar(fig, "fig6_sensibilidad_ruido.png")


# ===========================================================================
# Contraste de la importancia aprendida contra la expectativa física
# ===========================================================================
def contrastar_con_fisica(modelo, X, y, semilla: int) -> dict:
    """¿El modelo aprendió la física correcta? (sección 7.3, punto 6)

    El contraste se hace por DOS vías independientes, porque una sola no basta:

    1. `firma_en_los_datos` — tamaño de efecto de cada residuo entre la clase y
       la condición sana: |media(clase) − media(sano)| / desviación(sano). Es una
       propiedad de los DATOS, no del modelo: responde «¿aparece la firma física
       en los residuos?».
    2. `arbol_uno_contra_sano` — árbol de decisión de profundidad 3 entrenado
       solo con esa clase frente a `sano`. El residuo de la raíz es el que mejor
       separa la falla del equipo sano, y es directamente interpretable ante un
       ingeniero de mantenimiento.

    Se descartó usar la importancia por permutación del bosque completo para este
    contraste: con 300 árboles y once residuos correlacionados entre sí, permutar
    una característica casi no mueve la predicción —el bosque se apoya en las
    demás— y el ranking resultante queda dominado por el ruido. Es la limitación
    conocida de la permutación ante características redundantes. La figura 4 sí
    conserva la importancia por permutación global, que es lo que pide la
    especificación; aquí hace falta otra herramienta.
    """
    salida = {}
    y = np.asarray(y)
    for clase_id, clase in enumerate(CLASES):
        if clase == "sano":
            continue
        mask_clase = y == clase_id
        mask_sano = y == 0
        if mask_clase.sum() < 20 or mask_sano.sum() < 20:
            continue

        # --- vía 1: la firma en los datos ---------------------------------
        Xc, Xs = X[mask_clase], X[mask_sano]
        sigma_sano = Xs.std(ddof=0).replace(0, np.nan)
        efecto = ((Xc.mean() - Xs.mean()).abs() / sigma_sano).fillna(0.0)
        ranking_datos = list(efecto.sort_values(ascending=False).index)

        # --- vía 2: árbol de decisión uno-contra-sano ---------------------
        X_bin = pd.concat([Xc, Xs])
        y_bin = np.r_[np.ones(len(Xc), dtype=int), np.zeros(len(Xs), dtype=int)]
        arbol = DecisionTreeClassifier(max_depth=3, random_state=semilla)
        arbol.fit(X_bin, y_bin)
        raiz = COLUMNAS_RESIDUOS[arbol.tree_.feature[0]]
        importancias = dict(zip(COLUMNAS_RESIDUOS, arbol.feature_importances_))
        ranking_arbol = sorted(importancias, key=importancias.get, reverse=True)

        esperado = RESIDUO_CARACTERISTICO[clase]
        puesto_datos = ranking_datos.index(esperado) + 1
        salida[clase] = {
            "residuo_caracteristico_esperado": esperado,
            "residuo_dominante_en_los_datos": ranking_datos[0],
            "puesto_del_esperado_en_los_datos": puesto_datos,
            "residuo_raiz_del_arbol": raiz,
            "coincide_en_los_datos": bool(ranking_datos[0] == esperado),
            "coincide_en_el_arbol": bool(raiz == esperado),
            "entre_los_tres_primeros": bool(puesto_datos <= 3),
            "esta_entre_los_declarados": bool(ranking_datos[0] in FIRMAS_ESPERADAS[clase]),
            "exactitud_del_arbol": float(arbol.score(X_bin, y_bin)),
            "tamano_de_efecto": {c: float(efecto[c]) for c in COLUMNAS_RESIDUOS},
            "importancia_del_arbol": {c: float(v) for c, v in importancias.items()},
        }
    return salida


# ===========================================================================
# Estudio de sensibilidad al ruido (sección 5)
# ===========================================================================
def estudio_ruido(p, semilla: int, factores=(0.5, 1.0, 2.0), n_cond: int = 120,
                  parametros_rf: dict | None = None, verbose: bool = True) -> dict:
    """Reentrena con el ruido a la mitad, nominal y duplicado.

    Responde «¿qué exactitud de instrumento hace falta para que esto funcione?»,
    que es una pregunta de ingeniería, no de ciencia de datos. Se usa un barrido
    reducido (n_cond) porque lo que interesa es la TENDENCIA entre factores, no
    el valor absoluto: los tres puntos comparten tamaño y semilla.
    """
    from .generador import generar_balanceado, semillas_derivadas

    parametros_rf = parametros_rf or {"n_estimators": 300, "min_samples_leaf": 1,
                                      "max_features": "sqrt", "max_depth": None}
    semillas = semillas_derivadas(semilla)
    tabla = {}
    for factor in factores:
        if verbose:
            print(f"  ruido ×{factor:.1f} — generando {n_cond} condiciones…", flush=True)
        df, _ = generar_balanceado(p, semillas, n_cond=n_cond, factor_ruido=factor,
                                   verbose=False)
        part = particionar(df, semilla)
        modelo = RandomForestClassifier(random_state=semilla, n_jobs=-1, **parametros_rf)
        modelo.fit(part.X_tr, part.y_tr)
        y_pred = modelo.predict(part.X_val)
        inc = part.extra_val["nivel"] == "incipiente"
        tabla[str(factor)] = {
            "f1_macro": float(f1_score(part.y_val, y_pred, average="macro", zero_division=0)),
            "exactitud": float(accuracy_score(part.y_val, y_pred)),
            "diagnostico_incipiente": float(accuracy_score(part.y_val[inc], y_pred[inc])),
            "deteccion_incipiente": tasa_deteccion(part.y_val[inc], y_pred[inc]),
            "n_filas": int(len(df)),
        }
        if verbose:
            t = tabla[str(factor)]
            print(f"    F1 macro={t['f1_macro']:.4f}  "
                  f"diagnóstico incipiente={t['diagnostico_incipiente']:.4f}  "
                  f"detección incipiente={t['deteccion_incipiente']:.4f}")
    return tabla


# ===========================================================================
# Modelo secundario de severidad (sección 7.2)
# ===========================================================================
def entrenar_regresor_severidad(X_tr, sev_tr, y_tr, X_val, val_extra, semilla: int):
    """RandomForestRegressor de `severidad_f`, entrenado SOLO con muestras con falla.

    Sirve para priorizar la orden de trabajo: no es lo mismo un condensador con
    ensuciamiento incipiente que uno severo, y esa distinción es la que alimenta
    la orden de trabajo.

    `sev_tr` es la severidad real alineada con `X_tr`; `val_extra` trae las
    columnas de etiqueta del conjunto de validación.
    """
    con_falla_tr = np.asarray(y_tr) != 0
    reg = RandomForestRegressor(n_estimators=300, random_state=semilla, n_jobs=-1)
    reg.fit(X_tr[con_falla_tr], np.asarray(sev_tr)[con_falla_tr])

    con_falla_val = (val_extra["clase"] != "sano").values
    pred = reg.predict(X_val[con_falla_val])
    real = val_extra["severidad_f"].values[con_falla_val]
    return reg, {
        "mae_validacion": float(mean_absolute_error(real, pred)),
        "r2_validacion": float(r2_score(real, pred)),
        "n_entrenamiento": int(con_falla_tr.sum()),
    }


# ===========================================================================
# Orquestación
# ===========================================================================
def ejecutar(semilla: int = SEMILLA_MAESTRA, sufijo: str = "", con_estudio_ruido: bool = True,
             n_cond_ruido: int = 120) -> dict:
    from config.params import ParametrosEquipo, advertir_provisionales, resumen_parametros
    from .calibracion import aplicar_calibracion, cargar_calibracion
    from .generador import PREVALENCIA_CAMPO

    DIR_RESULTADOS.mkdir(parents=True, exist_ok=True)
    DIR_FIGURAS.mkdir(parents=True, exist_ok=True)

    provisionales = advertir_provisionales()
    p = aplicar_calibracion(ParametrosEquipo())

    print("\n[1] Carga de los datasets")
    df_bal = pd.read_parquet(RAIZ / "data" / f"dataset_balanceado{sufijo}.parquet")
    df_prev = pd.read_parquet(RAIZ / "data" / f"dataset_prevalencia{sufijo}.parquet")
    print(f"    balanceado : {len(df_bal)} filas, {df_bal['cond_id'].nunique()} condiciones")
    print(f"    prevalencia: {len(df_prev)} filas, {df_prev['cond_id'].nunique()} condiciones")

    print("\n[2] Partición 70/15/15 por grupos de condición de contorno")
    part = particionar(df_bal, semilla)
    print(f"    entrenamiento {len(part.y_tr)} filas / {len(part.conds['train'])} condiciones")
    print(f"    validación    {len(part.y_val)} filas / {len(part.conds['val'])} condiciones")
    print(f"    prueba        {part.sellado.n_filas} filas / {len(part.conds['test'])} condiciones "
          f"[SELLADO]")
    solape = (part.conds["train"] & part.conds["val"]) | (part.conds["train"] & part.conds["test"]) \
             | (part.conds["val"] & part.conds["test"])
    assert not solape, f"Fuga de condiciones entre particiones: {sorted(solape)[:5]}"

    # El conjunto de prevalencia también se sella: se abre una sola vez.
    sellado_prev = ConjuntoSellado("prevalencia_realista", construir_matriz_X(df_prev),
                                   df_prev["clase_id"],
                                   df_prev[["clase", "severidad_f", "nivel", "cond_id"]])

    print("\n[3] Selección de modelo — SOLO con entrenamiento y validación")
    ganador, resultados_seleccion = seleccionar_modelo(
        part.X_tr, part.y_tr, part.g_tr, part.X_val, part.y_val, semilla)
    modelo = resultados_seleccion[ganador]["estimador"]
    mejores_params = resultados_seleccion[ganador]["mejores_parametros"]

    print("\n[4] Modelo con class_weight='balanced' para el escenario de prevalencia")
    params_rf = {k: v for k, v in mejores_params.items()}
    if ganador == "random_forest":
        modelo_bal = RandomForestClassifier(random_state=semilla, n_jobs=-1,
                                            class_weight="balanced", **params_rf)
    else:
        modelo_bal = DecisionTreeClassifier(random_state=semilla,
                                            class_weight="balanced", **params_rf)
    modelo_bal.fit(part.X_tr, part.y_tr)

    print("\n[5] Evaluación en VALIDACIÓN (última mirada antes de sellar decisiones)")
    res_val = evaluar(modelo, part.X_val, part.y_val, "validacion")
    print(f"    F1 macro validación: {res_val['f1_macro']:.4f}")

    print("\n[6] Modelo de severidad")
    reg_sev, met_sev = entrenar_regresor_severidad(
        part.X_tr, df_bal.loc[part.X_tr.index, "severidad_f"], part.y_tr,
        part.X_val, part.extra_val, semilla)
    print(f"    MAE validación: {met_sev['mae_validacion']:.4f}   "
          f"R²: {met_sev['r2_validacion']:.4f}")

    print("\n[7] Importancia por permutación y contraste con la física")
    ruta_imp, tabla_imp = fig_importancia_permutacion(modelo, part.X_val, part.y_val, semilla)
    contraste = contrastar_con_fisica(modelo, part.X_val, part.y_val, semilla)
    c_datos = sum(v["coincide_en_los_datos"] for v in contraste.values())
    c_arbol = sum(v["coincide_en_el_arbol"] for v in contraste.values())
    en_top3 = sum(v["entre_los_tres_primeros"] for v in contraste.values())
    print(f"    residuo esperado = dominante en los datos: {c_datos}/{len(contraste)} clases; "
          f"entre los tres primeros: {en_top3}/{len(contraste)}")
    print(f"    residuo esperado en la raíz del árbol uno-contra-sano: "
          f"{c_arbol}/{len(contraste)} clases")

    # =======================================================================
    # APERTURA ÚNICA DE LOS CONJUNTOS DE PRUEBA
    # =======================================================================
    print("\n[8] Apertura ÚNICA de los conjuntos de prueba (solo para reportar)")
    X_te, y_te, extra_te = part.sellado.abrir("evaluación final del informe")
    Xp, yp, extra_p = sellado_prev.abrir("evaluación final del informe")

    res_test_bal = evaluar(modelo, X_te, y_te, "prueba_balanceada")
    res_test_prev = evaluar(modelo_bal, Xp, yp, "prevalencia_realista")
    res_test_prev_sin_peso = evaluar(modelo, Xp, yp, "prevalencia_realista_sin_class_weight")

    for r in (res_test_bal, res_test_prev):
        print(f"    [{r['conjunto']}] F1 macro={r['f1_macro']:.4f}  "
              f"F1 ponderado={r['f1_ponderado']:.4f}  "
              f"PR-AUC macro={r['pr_auc_macro']:.4f}  "
              f"exactitud={r['exactitud_global']:.4f}")

    mask_f = extra_te["clase"] != "sano"
    pred_sev = reg_sev.predict(X_te[mask_f.values])
    met_sev["mae_prueba"] = float(mean_absolute_error(
        extra_te.loc[mask_f, "severidad_f"], pred_sev))
    met_sev["r2_prueba"] = float(r2_score(extra_te.loc[mask_f, "severidad_f"], pred_sev))

    print("\n[9] Figuras")
    figuras = {
        "fig1_diagrama_ph": str(fig_diagrama_ph(p)),
        "fig2a_matriz_confusion_balanceado": str(fig_matriz_confusion(
            res_test_bal, "Matriz de confusión — conjunto de prueba balanceado",
            "fig2a_matriz_confusion_balanceado.png")),
        "fig2b_matriz_confusion_prevalencia": str(fig_matriz_confusion(
            res_test_prev, "Matriz de confusión — prevalencia realista de campo",
            "fig2b_matriz_confusion_prevalencia.png")),
        "fig3a_curvas_pr_balanceado": str(fig_curvas_pr(
            res_test_bal, "conjunto balanceado", "fig3a_curvas_pr_balanceado.png")),
        "fig3b_curvas_pr_prevalencia": str(fig_curvas_pr(
            res_test_prev, "prevalencia realista", "fig3b_curvas_pr_prevalencia.png")),
        "fig4_importancia_permutacion": str(ruta_imp),
        "fig7_mapa_firmas": str(fig_mapa_firmas(df_bal)),
    }
    ruta_det, tabla_det = fig_deteccion_vs_severidad(res_test_bal, extra_te)
    figuras["fig5_deteccion_vs_severidad"] = str(ruta_det)
    for k in figuras:
        print(f"    {k}")

    tabla_ruido = {}
    if con_estudio_ruido:
        print("\n[10] Estudio de sensibilidad al ruido de los instrumentos")
        params_rf_est = params_rf if ganador == "random_forest" else None
        tabla_ruido = estudio_ruido(p, semilla, n_cond=n_cond_ruido,
                                    parametros_rf=params_rf_est)
        figuras["fig6_sensibilidad_ruido"] = str(fig_sensibilidad_ruido(tabla_ruido))

    # --- validez de la corrida ------------------------------------------
    aperturas = {part.sellado.nombre: part.sellado.n_aperturas,
                 sellado_prev.nombre: sellado_prev.n_aperturas}
    corrida_valida = all(n == 1 for n in aperturas.values())

    metricas = {
        "corrida_valida": corrida_valida,
        "aperturas_del_conjunto_de_prueba": aperturas,
        "motivos_de_apertura": {part.sellado.nombre: part.sellado.aperturas,
                                sellado_prev.nombre: sellado_prev.aperturas},
        "semilla_maestra": semilla,
        "parametros_provisionales": provisionales,
        "calibracion_ua": cargar_calibracion(),
        "parametros_equipo": resumen_parametros(p),
        "particion": {
            "filas": {"entrenamiento": int(len(part.y_tr)), "validacion": int(len(part.y_val)),
                      "prueba": int(part.sellado.n_filas)},
            "condiciones": {k: len(v) for k, v in part.conds.items()},
            "condiciones_compartidas_entre_particiones": 0,
        },
        "seleccion_de_modelo": {
            "criterio": "F1 macro sobre el conjunto de VALIDACIÓN",
            "ganador": ganador,
            "candidatos": {k: {kk: vv for kk, vv in v.items() if kk != "estimador"}
                           for k, v in resultados_seleccion.items()},
        },
        "columnas_de_entrada": list(COLUMNAS_RESIDUOS),
        "metricas": {
            "validacion": {k: v for k, v in res_val.items() if not k.startswith("_")},
            "prueba_balanceada": {k: v for k, v in res_test_bal.items() if not k.startswith("_")},
            "prevalencia_realista": {k: v for k, v in res_test_prev.items()
                                     if not k.startswith("_")},
            "prevalencia_sin_class_weight": {k: v for k, v in res_test_prev_sin_peso.items()
                                             if not k.startswith("_")},
        },
        "modelo_de_severidad": met_sev,
        "importancia_permutacion": tabla_imp,
        "contraste_con_la_fisica": contraste,
        "deteccion_vs_severidad": tabla_det,
        "sensibilidad_al_ruido": tabla_ruido,
        "prevalencia_objetivo": PREVALENCIA_CAMPO,
        "figuras": figuras,
    }
    ruta = DIR_RESULTADOS / "metricas.json"
    ruta.write_text(json.dumps(metricas, indent=2, ensure_ascii=False, default=str),
                    encoding="utf-8")
    print(f"\n[11] Métricas -> {ruta}")
    print(f"     corrida_valida = {corrida_valida} "
          f"(aperturas del conjunto de prueba: {aperturas})")

    metricas["_objetos"] = {"modelo": modelo, "modelo_bal": modelo_bal,
                            "res_test_bal": res_test_bal, "res_test_prev": res_test_prev}
    return metricas


if __name__ == "__main__":
    import argparse, sys
    sys.path.insert(0, str(RAIZ))

    ap = argparse.ArgumentParser(description="Entrena y evalúa el clasificador FDD.")
    ap.add_argument("--sufijo", default="")
    ap.add_argument("--semilla", type=int, default=SEMILLA_MAESTRA)
    ap.add_argument("--sin-estudio-ruido", action="store_true")
    ap.add_argument("--n-cond-ruido", type=int, default=120)
    ap.add_argument("--sin-informe", action="store_true")
    args = ap.parse_args()

    met = ejecutar(args.semilla, args.sufijo, not args.sin_estudio_ruido, args.n_cond_ruido)

    if not args.sin_informe:
        from .reporte import generar_informe
        ruta = generar_informe(met)
        print(f"[12] Informe Word -> {ruta}")
