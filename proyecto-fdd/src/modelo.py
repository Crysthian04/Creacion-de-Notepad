"""Entrenamiento, evaluación y análisis del clasificador FDD.

REGLA VINCULANTE (Regla 3 de la auditoría, defecto D7)
------------------------------------------------------
La comparación entre el clasificador base y el Random Forest, y la elección de
hiperparámetros, se resuelven EXCLUSIVAMENTE con el conjunto de validación. El
conjunto de prueba se toca UNA SOLA VEZ, al final, para reportar. Y esa regla la
impone la estructura del código:

  * `ConjuntoSellado` cuenta cada apertura y registra el motivo.
  * `seleccionar_modelo()` recibe solo (X_tr, y_tr, grupos_tr, X_val, y_val): no
    tiene acceso léxico a los conjuntos de prueba.
  * Si algún conjunto sellado registra más de una apertura, `metricas.json`
    marca `corrida_valida: false`.

Otras reglas heredadas:
  * Regla 1 — X se construye por lista blanca `res_*` derivada de la topología.
  * Regla 2 — sin SMOTE: el conjunto balanceado nace balanceado del simulador y
    el desbalance de campo se trata con `class_weight='balanced'`.
  * GridSearchCV optimiza F1 MACRO, nunca exactitud (defecto D4).
"""

from __future__ import annotations

import json
import math
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

from config.params import (NIVELES_DISCREPANCIA_BARRIDO, NIVEL_DISCREPANCIA,
                           N_REPETICIONES_POR_CORRIDA, SEMILLA_MAESTRA,
                           SOPORTE_MINIMO_SIN_INTERVALO)
from .fallas import clases, firmas_esperadas, residuo_caracteristico
from .features import columnas_residuos, construir_matriz_X

RAIZ = Path(__file__).resolve().parents[1]
DIR_FIGURAS = RAIZ / "figuras"
DIR_RESULTADOS = RAIZ / "resultados"
DPI = 300

sns.set_theme(style="whitegrid", context="paper")


# ===========================================================================
# Intervalo de confianza de Wilson
# ===========================================================================
def intervalo_wilson(exitos: int, ensayos: int, z: float = 1.96) -> tuple[float, float]:
    """Intervalo de Wilson al 95 % para una proporción.

    Con soportes pequeños —la clase más rara del conjunto de prevalencia deja
    unas decenas de muestras— una precisión de 0,69 sin intervalo no significa
    nada. Wilson se prefiere al intervalo normal porque no se sale de [0, 1] ni
    colapsa cuando la proporción se acerca a 0 o a 1.
    """
    if ensayos <= 0:
        return (float("nan"), float("nan"))
    p = exitos / ensayos
    z2 = z * z
    denom = 1.0 + z2 / ensayos
    centro = (p + z2 / (2 * ensayos)) / denom
    margen = (z / denom) * math.sqrt(p * (1 - p) / ensayos + z2 / (4 * ensayos * ensayos))
    return (max(0.0, centro - margen), min(1.0, centro + margen))


# ===========================================================================
# Conjunto sellado
# ===========================================================================
class ConjuntoSellado:
    """Contenedor que solo se abre explícitamente y lleva la cuenta.

    Convierte «no mirar el test todavía» de intención en control verificable.
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
                f"El conjunto sellado `{self._nombre}` se abrió {len(self._aperturas)} "
                f"veces. La corrida quedará marcada como NO VÁLIDA. Motivos: "
                f"{self._aperturas}", stacklevel=2)
        return self._X, self._y, self._extra

    def __repr__(self) -> str:
        return (f"<ConjuntoSellado {self._nombre}: {self.n_filas} filas, "
                f"{self.n_aperturas} aperturas>")


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


COLUMNAS_EXTRA = ["clase", "severidad_f", "nivel", "cond_id"]


def particionar(df: pd.DataFrame, topo, semilla: int, prop_tr: float = 0.70,
                prop_val: float = 0.15) -> Particion:
    """Partición 70/15/15 POR GRUPOS de `cond_id` (sección 7.1).

    Una condición genera tantas filas como clases × niveles. Partir por fila
    metería la misma condición en entrenamiento y en prueba, que es la fuga
    entre conjuntos que la especificación prohíbe.
    """
    X = construir_matriz_X(df, topo)          # LISTA BLANCA
    y = df["clase_id"]
    g = df["cond_id"]

    gss1 = GroupShuffleSplit(n_splits=1, train_size=prop_tr, random_state=semilla)
    idx_tr, idx_resto = next(gss1.split(X, y, groups=g))
    resto_frac_val = prop_val / (1.0 - prop_tr)
    gss2 = GroupShuffleSplit(n_splits=1, train_size=resto_frac_val, random_state=semilla + 1)
    idx_val_rel, idx_test_rel = next(
        gss2.split(X.iloc[idx_resto], y.iloc[idx_resto], groups=g.iloc[idx_resto]))
    idx_val, idx_test = idx_resto[idx_val_rel], idx_resto[idx_test_rel]

    sellado = ConjuntoSellado("prueba_balanceada", X.iloc[idx_test], y.iloc[idx_test],
                              df.iloc[idx_test][COLUMNAS_EXTRA])
    return Particion(
        X_tr=X.iloc[idx_tr], y_tr=y.iloc[idx_tr], g_tr=g.iloc[idx_tr],
        X_val=X.iloc[idx_val], y_val=y.iloc[idx_val],
        extra_val=df.iloc[idx_val][COLUMNAS_EXTRA], sellado=sellado,
        conds={"train": set(g.iloc[idx_tr]), "val": set(g.iloc[idx_val]),
               "test": set(g.iloc[idx_test])})


# ===========================================================================
# Selección de modelo — SIN acceso al conjunto de prueba
# ===========================================================================
REJILLA_RF = {"n_estimators": [300], "max_depth": [None, 16],
              "min_samples_leaf": [1, 2, 4], "max_features": ["sqrt", 0.5]}
REJILLA_DT = {"max_depth": [8, 16, None], "min_samples_leaf": [1, 2, 4],
              "min_samples_split": [2, 10]}


def seleccionar_modelo(X_tr, y_tr, g_tr, X_val, y_val, semilla: int, verbose: bool = True):
    """Busca hiperparámetros y elige entre Árbol y Random Forest.

    La firma es deliberadamente estrecha: recibe entrenamiento y validación, y
    nada más. No puede tocar el conjunto de prueba.
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
        gs = GridSearchCV(estimador, rejilla, cv=cv, scoring="f1_macro", n_jobs=-1, refit=True)
        gs.fit(X_tr, y_tr, groups=g_tr)
        f1_val = f1_score(y_val, gs.best_estimator_.predict(X_val), average="macro")
        resultados[nombre] = {"mejores_parametros": gs.best_params_,
                              "f1_macro_cv": float(gs.best_score_),
                              "f1_macro_validacion": float(f1_val),
                              "estimador": gs.best_estimator_}
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
def evaluar(modelo, X, y, nombre_conjunto: str, nombres_clases) -> dict:
    """Métricas en el orden de la sección 7.3: la exactitud va al final."""
    y = np.asarray(y)
    y_pred = modelo.predict(X)
    y_proba = modelo.predict_proba(X)
    etiquetas = list(range(len(nombres_clases)))
    presentes = sorted(set(y.tolist()) | set(y_pred.tolist()))

    mc = confusion_matrix(y, y_pred, labels=etiquetas)
    with np.errstate(invalid="ignore"):
        mc_norm = mc / np.maximum(mc.sum(axis=1, keepdims=True), 1)
    reporte = classification_report(y, y_pred, labels=etiquetas,
                                    target_names=list(nombres_clases),
                                    output_dict=True, zero_division=0)

    y_bin = label_binarize(y, classes=etiquetas)
    pr_auc = {}
    for i, c in enumerate(nombres_clases):
        pr_auc[c] = (None if y_bin[:, i].sum() == 0
                     else float(average_precision_score(y_bin[:, i], y_proba[:, i])))

    # Intervalos de Wilson para las clases con soporte pequeño: una precisión
    # puntual sobre 20 o 30 muestras no dice nada sin su intervalo.
    intervalos = {}
    for i, c in enumerate(nombres_clases):
        soporte = int((y == i).sum())
        predichos = int((y_pred == i).sum())
        aciertos = int(((y_pred == i) & (y == i)).sum())
        intervalos[c] = {
            "soporte": soporte, "predichos": predichos,
            "recall_ic95": intervalo_wilson(aciertos, soporte),
            "precision_ic95": intervalo_wilson(aciertos, predichos),
            "soporte_pequeno": bool(0 < soporte < SOPORTE_MINIMO_SIN_INTERVALO),
        }

    proporciones = pd.Series(y).map(dict(enumerate(nombres_clases))).value_counts(normalize=True)
    return {
        "conjunto": nombre_conjunto, "n_muestras": int(len(y)),
        "matriz_confusion": mc.tolist(),
        "matriz_confusion_normalizada": np.nan_to_num(mc_norm).tolist(),
        "recall_por_clase": {c: float(reporte[c]["recall"]) for c in nombres_clases},
        "f1_por_clase": {c: float(reporte[c]["f1-score"]) for c in nombres_clases},
        "precision_por_clase": {c: float(reporte[c]["precision"]) for c in nombres_clases},
        "soporte_por_clase": {c: int(reporte[c]["support"]) for c in nombres_clases},
        "intervalos_wilson": intervalos,
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
                                               target_names=list(nombres_clases),
                                               zero_division=0),
        "_y": y, "_y_pred": y_pred, "_y_proba": y_proba,
    }


def tasa_deteccion(y_true, y_pred) -> float:
    """Detección = distinguir sano de no-sano, con independencia del diagnóstico."""
    return float(np.mean((np.asarray(y_true) == 0) == (np.asarray(y_pred) == 0)))


# ===========================================================================
# Figuras
# ===========================================================================
def _guardar(fig, nombre: str) -> Path:
    DIR_FIGURAS.mkdir(parents=True, exist_ok=True)
    ruta = DIR_FIGURAS / nombre
    fig.savefig(ruta, dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    return ruta


def fig_matriz_confusion(res, titulo, nombre_archivo, nombres_clases) -> Path:
    mc = np.array(res["matriz_confusion_normalizada"])
    fig, ax = plt.subplots(figsize=(9.5, 8))
    sns.heatmap(mc, annot=True, fmt=".2f", cmap="Blues", cbar=True, vmin=0, vmax=1,
                xticklabels=nombres_clases, yticklabels=nombres_clases, ax=ax,
                annot_kws={"size": 7})
    ax.set_title(f"{titulo}\n(normalizada por fila; n = {res['n_muestras']})")
    ax.set_xlabel("Predicción"); ax.set_ylabel("Realidad")
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
    return _guardar(fig, nombre_archivo)


def fig_curvas_pr(res, titulo, nombre_archivo, nombres_clases) -> Path:
    y, proba = res["_y"], res["_y_proba"]
    y_bin = label_binarize(y, classes=list(range(len(nombres_clases))))
    fig, ax = plt.subplots(figsize=(8, 6))
    colores = sns.color_palette("tab20", len(nombres_clases))
    for i, c in enumerate(nombres_clases):
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


def fig_importancia_permutacion(modelo, X_val, y_val, semilla, topo):
    imp = permutation_importance(modelo, X_val, y_val, n_repeats=10,
                                 random_state=semilla, scoring="f1_macro", n_jobs=-1)
    cols = np.array(columnas_residuos(topo))
    orden = np.argsort(imp.importances_mean)
    fig, ax = plt.subplots(figsize=(8, 5.5))
    ax.barh(cols[orden], imp.importances_mean[orden], xerr=imp.importances_std[orden],
            color=sns.color_palette("crest", 1)[0])
    ax.set_xlabel("Caída de F1 macro al permutar la característica")
    ax.set_title("Importancia por permutación (conjunto de validación)")
    ruta = _guardar(fig, "fig4_importancia_permutacion.png")
    tabla = {c: {"media": float(m), "desv": float(s)}
             for c, m, s in zip(cols, imp.importances_mean, imp.importances_std)}
    return ruta, tabla


def fig_deteccion_vs_severidad(res, extra):
    d = extra.copy()
    d["acierto"] = (res["_y"] == res["_y_pred"])
    d = d[d["clase"] != "sano"]
    bins = np.arange(0.15, 1.01, 0.10)
    d["bin"] = pd.cut(d["severidad_f"], bins=bins)
    tabla = d.groupby(["clase", "bin"], observed=True)["acierto"].mean().unstack()
    fig, ax = plt.subplots(figsize=(8.5, 5.5))
    centros = [iv.mid for iv in tabla.columns]
    colores = sns.color_palette("tab20", len(tabla.index))
    for (clase, fila), color in zip(tabla.iterrows(), colores):
        ax.plot(centros, fila.values, marker="o", ms=4, lw=1.5, label=clase, color=color)
    ax.axvspan(0.15, 0.35, alpha=0.10, color="grey")
    ax.text(0.25, 0.02, "incipiente", ha="center", fontsize=8, color="dimgrey")
    ax.set_xlabel("Severidad f"); ax.set_ylabel("Exactitud de diagnóstico")
    ax.set_title("Curva de detección frente a severidad")
    ax.set_ylim(-0.02, 1.05); ax.legend(fontsize=7, ncol=2)
    ruta = _guardar(fig, "fig5_deteccion_vs_severidad.png")
    return ruta, {c: {str(k): (None if pd.isna(v) else float(v)) for k, v in f.items()}
                  for c, f in tabla.iterrows()}


def fig_mapa_firmas(df, topo) -> Path:
    """Heatmap de residuo medio por clase: cada falla deja una huella distinta."""
    cols = list(columnas_residuos(topo))
    sub = df[df["nivel"].isin(["severa", "sano"])]
    medias = sub.groupby("clase")[cols].mean()
    z = (medias - medias.mean()) / medias.std(ddof=0).replace(0, 1)
    orden = [c for c in clases(topo) if c in z.index]
    z, medias = z.reindex(orden), medias.reindex(orden)
    fig, ax = plt.subplots(figsize=(11, 6))
    sns.heatmap(z, cmap="RdBu_r", center=0, annot=medias.values, fmt=".2f",
                annot_kws={"size": 6}, ax=ax,
                cbar_kws={"label": "residuo medio estandarizado"})
    ax.set_title("Mapa de firmas: residuo medio por clase (nivel severo)\n"
                 "color = valor estandarizado por columna; número = residuo medio "
                 "en unidades físicas")
    ax.set_xlabel(""); ax.set_ylabel("")
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
    return _guardar(fig, "fig7_mapa_firmas.png")


def fig_diagrama_ph(p, clase_degradada: str = "condensador_sucio", f: float = 0.8) -> Path:
    import CoolProp.CoolProp as CP
    from .ciclo import AjustesCiclo, CondicionContorno, resolver_ciclo
    from .fallas import ajustes_de_falla

    cond = CondicionContorno(32.0, 80.0, 0.90)
    sano = resolver_ciclo(cond, p, AjustesCiclo())
    degr = resolver_ciclo(cond, p, ajustes_de_falla(clase_degradada, f, p))
    fig, ax = plt.subplots(figsize=(8, 6))
    t_crit = CP.PropsSI("Tcrit", p.refrigerante) - 273.15
    temps = np.linspace(-25.0, t_crit - 0.5, 220)
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
                label=f"{etiqueta}: T_ev={estado.T_evap:.1f} °C, T_cd={estado.T_cond:.1f} °C, "
                      f"y={estado.y_capacidad:.2f}")
    ax.set_yscale("log")
    ax.set_xlabel("Entalpía específica h [kJ/kg]"); ax.set_ylabel("Presión [kPa]")
    ax.set_title(f"Diagrama P-h — {p.refrigerante}\n"
                 f"T_amb={cond.T_amb:.0f} °C, carga={cond.Q_load_frac:.0%}")
    ax.legend(fontsize=8, loc="upper left")
    return _guardar(fig, "fig1_diagrama_ph.png")


def _fig_barrido(tabla, etiqueta_x, titulo, nombre_archivo, marca_x=None,
                 texto_marca=None) -> Path:
    xs = sorted(tabla, key=float)
    fig, ax = plt.subplots(figsize=(7.5, 5))
    series = {
        "F1 macro (todas las severidades)": [tabla[x]["f1_macro"] for x in xs],
        "Exactitud de diagnóstico, nivel incipiente": [tabla[x]["diagnostico_incipiente"]
                                                       for x in xs],
        "Tasa de detección sano/no-sano, incipiente": [tabla[x]["deteccion_incipiente"]
                                                       for x in xs],
    }
    for (etiqueta, valores), marca in zip(series.items(), ["o", "s", "^"]):
        ax.plot([float(x) for x in xs], valores, marker=marca, lw=1.8, label=etiqueta)
    if marca_x is not None:
        ax.axvline(marca_x, color="grey", ls="--", lw=1)
        if texto_marca:
            ax.text(marca_x, 0.02, f"  {texto_marca}", fontsize=8, color="dimgrey")
    ax.set_xlabel(etiqueta_x); ax.set_ylabel("Desempeño")
    ax.set_title(titulo); ax.set_ylim(0, 1.05); ax.legend(fontsize=8)
    return _guardar(fig, nombre_archivo)


# ===========================================================================
# Contraste con la expectativa física
# ===========================================================================
def contrastar_con_fisica(X, y, topo, semilla: int) -> dict:
    """¿Aparece la firma física en los datos, y la usa un modelo interpretable?

    Dos vías independientes:
      1. Tamaño de efecto entre la clase y la condición sana,
         |media(clase) − media(sano)| / desviación(sano). Propiedad de los DATOS.
      2. Árbol uno-contra-sano de profundidad 3: el residuo de la raíz es el que
         mejor separa la falla del equipo sano, y es interpretable ante un
         ingeniero de mantenimiento.

    NO se usa la importancia por permutación del bosque para este contraste: con
    cientos de árboles y residuos correlacionados entre sí, permutar una
    característica apenas mueve la predicción porque el modelo se apoya en las
    demás, y el ranking queda dominado por el ruido.
    """
    nombres = clases(topo)
    cols = list(columnas_residuos(topo))
    caracteristico = residuo_caracteristico(topo)
    firmas = firmas_esperadas(topo)
    y = np.asarray(y)
    salida = {}
    for clase_id, clase in enumerate(nombres):
        if clase == "sano":
            continue
        mask_c, mask_s = y == clase_id, y == 0
        if mask_c.sum() < 20 or mask_s.sum() < 20:
            continue
        Xc, Xs = X[mask_c], X[mask_s]
        sigma = Xs.std(ddof=0).replace(0, np.nan)
        efecto = ((Xc.mean() - Xs.mean()).abs() / sigma).fillna(0.0)
        ranking = list(efecto.sort_values(ascending=False).index)

        X_bin = pd.concat([Xc, Xs])
        y_bin = np.r_[np.ones(len(Xc), dtype=int), np.zeros(len(Xs), dtype=int)]
        arbol = DecisionTreeClassifier(max_depth=3, random_state=semilla).fit(X_bin, y_bin)
        raiz = cols[arbol.tree_.feature[0]]

        esperado = caracteristico[clase]
        puesto = ranking.index(esperado) + 1
        salida[clase] = {
            "residuo_caracteristico_esperado": esperado,
            "residuo_dominante_en_los_datos": ranking[0],
            "puesto_del_esperado_en_los_datos": puesto,
            "residuo_raiz_del_arbol": raiz,
            "coincide_en_los_datos": bool(ranking[0] == esperado),
            "coincide_en_el_arbol": bool(raiz == esperado),
            "entre_los_tres_primeros": bool(puesto <= 3),
            "esta_entre_los_declarados": bool(ranking[0] in firmas[clase]),
            "exactitud_del_arbol": float(arbol.score(X_bin, y_bin)),
            "tamano_de_efecto": {c: float(efecto[c]) for c in cols},
        }
    return salida


# ===========================================================================
# Estudios de sensibilidad
# ===========================================================================
def _entrenar_y_medir(df, topo, semilla, parametros_rf) -> dict:
    part = particionar(df, topo, semilla)
    modelo = RandomForestClassifier(random_state=semilla, n_jobs=-1, **parametros_rf)
    modelo.fit(part.X_tr, part.y_tr)
    y_pred = modelo.predict(part.X_val)
    inc = (part.extra_val["nivel"] == "incipiente").values
    return {
        "f1_macro": float(f1_score(part.y_val, y_pred, average="macro", zero_division=0)),
        "exactitud": float(accuracy_score(part.y_val, y_pred)),
        "diagnostico_incipiente": float(accuracy_score(part.y_val[inc], y_pred[inc])),
        "deteccion_incipiente": tasa_deteccion(part.y_val[inc], y_pred[inc]),
        "n_filas": int(len(df)),
    }


def estudio_ruido(p, semilla, factores=(0.5, 1.0, 2.0), n_cond=120,
                  parametros_rf=None, verbose=True) -> dict:
    """Reentrena con el ruido a la mitad, nominal y duplicado (sección 5)."""
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
        tabla[str(factor)] = _entrenar_y_medir(df, p.topologia, semilla, parametros_rf)
        if verbose:
            t = tabla[str(factor)]
            print(f"    F1 macro={t['f1_macro']:.4f}  "
                  f"diagnóstico incipiente={t['diagnostico_incipiente']:.4f}")
    return tabla


def estudio_discrepancia(p, semilla, niveles=NIVELES_DISCREPANCIA_BARRIDO, n_cond=120,
                         parametros_rf=None, verbose=True) -> dict:
    """Barrido del error de calibración del gemelo digital.

    Responde la pregunta de ingeniería que conecta esta fase con la calibración
    contra mediciones de campo: ¿con qué exactitud hay que calibrar el gemelo
    para que el diagnóstico siga siendo útil?
    """
    from .generador import generar_balanceado, semillas_derivadas
    parametros_rf = parametros_rf or {"n_estimators": 300, "min_samples_leaf": 1,
                                      "max_features": "sqrt", "max_depth": None}
    semillas = semillas_derivadas(semilla)
    tabla = {}
    for nivel in niveles:
        if verbose:
            print(f"  discrepancia {nivel:.0%} — generando {n_cond} condiciones…", flush=True)
        df, _ = generar_balanceado(p, semillas, n_cond=n_cond,
                                   nivel_discrepancia=nivel,
                                   modo_discrepancia="por_condicion", verbose=False)
        tabla[str(nivel)] = _entrenar_y_medir(df, p.topologia, semilla, parametros_rf)
        if verbose:
            t = tabla[str(nivel)]
            print(f"    F1 macro={t['f1_macro']:.4f}  "
                  f"diagnóstico incipiente={t['diagnostico_incipiente']:.4f}")
    return tabla


def repeticiones_por_corrida(p, semilla, nivel=NIVEL_DISCREPANCIA,
                             n_repeticiones=N_REPETICIONES_POR_CORRIDA, n_cond=120,
                             parametros_rf=None, verbose=True) -> dict:
    """Repite la corrida con un ÚNICO error de calibración por corrida.

    El barrido por condición mide el efecto PROMEDIO del nivel de discrepancia.
    Estas repeticiones miden otra cosa: cuán distinto le puede ir a UNA
    implantación concreta según cómo haya quedado calibrado su gemelo. Las dos
    cosas son información distinta y las dos hacen falta.
    """
    from .generador import generar_balanceado, semillas_derivadas
    parametros_rf = parametros_rf or {"n_estimators": 300, "min_samples_leaf": 1,
                                      "max_features": "sqrt", "max_depth": None}
    corridas = []
    for i in range(n_repeticiones):
        semilla_i = semilla + 1000 * (i + 1)
        if verbose:
            print(f"  repetición {i + 1}/{n_repeticiones} (semilla {semilla_i})…", flush=True)
        semillas = semillas_derivadas(semilla_i)
        df, _ = generar_balanceado(p, semillas, n_cond=n_cond, nivel_discrepancia=nivel,
                                   modo_discrepancia="por_corrida", verbose=False)
        m = _entrenar_y_medir(df, p.topologia, semilla_i, parametros_rf)
        m["semilla"] = semilla_i
        corridas.append(m)
        if verbose:
            print(f"    F1 macro={m['f1_macro']:.4f}")
    f1s = [c["f1_macro"] for c in corridas]
    inc = [c["diagnostico_incipiente"] for c in corridas]
    return {
        "nivel_discrepancia": nivel, "n_repeticiones": n_repeticiones,
        "modo": "por_corrida", "corridas": corridas,
        "f1_macro_media": float(np.mean(f1s)), "f1_macro_desv": float(np.std(f1s, ddof=1)),
        "f1_macro_min": float(np.min(f1s)), "f1_macro_max": float(np.max(f1s)),
        "diagnostico_incipiente_media": float(np.mean(inc)),
        "diagnostico_incipiente_desv": float(np.std(inc, ddof=1)),
    }


# ===========================================================================
# Modelo secundario de severidad (sección 7.2)
# ===========================================================================
def entrenar_regresor_severidad(X_tr, sev_tr, y_tr, X_val, val_extra, semilla: int):
    """RandomForestRegressor de `severidad_f`, entrenado SOLO con muestras con falla.

    Sirve para priorizar la orden de trabajo: no es lo mismo una incrustación
    incipiente que una severa.
    """
    con_falla = np.asarray(y_tr) != 0
    reg = RandomForestRegressor(n_estimators=300, random_state=semilla, n_jobs=-1)
    reg.fit(X_tr[con_falla], np.asarray(sev_tr)[con_falla])
    con_falla_val = (val_extra["clase"] != "sano").values
    pred = reg.predict(X_val[con_falla_val])
    real = val_extra["severidad_f"].values[con_falla_val]
    return reg, {"mae_validacion": float(mean_absolute_error(real, pred)),
                 "r2_validacion": float(r2_score(real, pred)),
                 "n_entrenamiento": int(con_falla.sum())}


# ===========================================================================
# Orquestación
# ===========================================================================
def ejecutar(semilla: int = SEMILLA_MAESTRA, sufijo: str = "", con_estudios: bool = True,
             n_cond_estudios: int = 120) -> dict:
    from config.params import (ParametrosEquipo, advertir_provisionales,
                               resumen_parametros)
    from .calibracion import aplicar_calibracion, cargar_calibracion
    from .generador import prevalencia_campo

    DIR_RESULTADOS.mkdir(parents=True, exist_ok=True)
    DIR_FIGURAS.mkdir(parents=True, exist_ok=True)
    provisionales = advertir_provisionales()
    p = aplicar_calibracion(ParametrosEquipo())
    topo = p.topologia
    nombres_clases = clases(topo)

    print(f"\n[1] Carga de los datasets — topología {topo.nombre}")
    df_bal = pd.read_parquet(RAIZ / "data" / f"dataset_balanceado{sufijo}.parquet")
    df_prev = pd.read_parquet(RAIZ / "data" / f"dataset_prevalencia{sufijo}.parquet")
    meta_gen = json.loads((RAIZ / "resultados" / f"generacion{sufijo}.json").read_text("utf-8"))
    assert meta_gen["topologia"] == topo.nombre, (
        f"El dataset se generó con la topología {meta_gen['topologia']} y se está "
        f"entrenando con {topo.nombre}")
    print(f"    balanceado : {len(df_bal)} filas, {df_bal['cond_id'].nunique()} condiciones")
    print(f"    prevalencia: {len(df_prev)} filas, {df_prev['cond_id'].nunique()} condiciones")
    print(f"    discrepancia modelo-planta: {meta_gen['nivel_discrepancia']:.0%} "
          f"({meta_gen['modo_discrepancia']})")

    print("\n[2] Partición 70/15/15 por grupos de condición de contorno")
    part = particionar(df_bal, topo, semilla)
    print(f"    entrenamiento {len(part.y_tr)} filas / {len(part.conds['train'])} condiciones")
    print(f"    validación    {len(part.y_val)} filas / {len(part.conds['val'])} condiciones")
    print(f"    prueba        {part.sellado.n_filas} filas / {len(part.conds['test'])} "
          f"condiciones [SELLADO]")
    solape = ((part.conds["train"] & part.conds["val"])
              | (part.conds["train"] & part.conds["test"])
              | (part.conds["val"] & part.conds["test"]))
    assert not solape, f"Fuga de condiciones entre particiones: {sorted(solape)[:5]}"

    sellado_prev = ConjuntoSellado("prevalencia_realista", construir_matriz_X(df_prev, topo),
                                   df_prev["clase_id"], df_prev[COLUMNAS_EXTRA])

    print("\n[3] Selección de modelo — SOLO con entrenamiento y validación")
    ganador, seleccion = seleccionar_modelo(part.X_tr, part.y_tr, part.g_tr,
                                            part.X_val, part.y_val, semilla)
    modelo = seleccion[ganador]["estimador"]
    mejores = dict(seleccion[ganador]["mejores_parametros"])

    print("\n[4] Modelo con class_weight='balanced' para el escenario de prevalencia")
    if ganador == "random_forest":
        modelo_bal = RandomForestClassifier(random_state=semilla, n_jobs=-1,
                                            class_weight="balanced", **mejores)
    else:
        modelo_bal = DecisionTreeClassifier(random_state=semilla,
                                            class_weight="balanced", **mejores)
    modelo_bal.fit(part.X_tr, part.y_tr)

    print("\n[5] Evaluación en VALIDACIÓN")
    res_val = evaluar(modelo, part.X_val, part.y_val, "validacion", nombres_clases)
    print(f"    F1 macro validación: {res_val['f1_macro']:.4f}")

    print("\n[6] Modelo de severidad")
    reg_sev, met_sev = entrenar_regresor_severidad(
        part.X_tr, df_bal.loc[part.X_tr.index, "severidad_f"], part.y_tr,
        part.X_val, part.extra_val, semilla)
    print(f"    MAE validación: {met_sev['mae_validacion']:.4f}   R²: {met_sev['r2_validacion']:.4f}")

    print("\n[7] Importancia por permutación y contraste con la física")
    ruta_imp, tabla_imp = fig_importancia_permutacion(modelo, part.X_val, part.y_val,
                                                      semilla, topo)
    contraste = contrastar_con_fisica(part.X_val, part.y_val, topo, semilla)
    c_datos = sum(v["coincide_en_los_datos"] for v in contraste.values())
    c_arbol = sum(v["coincide_en_el_arbol"] for v in contraste.values())
    top3 = sum(v["entre_los_tres_primeros"] for v in contraste.values())
    print(f"    residuo esperado dominante en los datos: {c_datos}/{len(contraste)}; "
          f"entre los tres primeros: {top3}/{len(contraste)}; "
          f"en la raíz del árbol: {c_arbol}/{len(contraste)}")

    print("\n[8] Apertura ÚNICA de los conjuntos de prueba (solo para reportar)")
    X_te, y_te, extra_te = part.sellado.abrir("evaluación final del informe")
    Xp, yp, extra_p = sellado_prev.abrir("evaluación final del informe")
    res_test_bal = evaluar(modelo, X_te, y_te, "prueba_balanceada", nombres_clases)
    res_test_prev = evaluar(modelo_bal, Xp, yp, "prevalencia_realista", nombres_clases)
    res_prev_sin_peso = evaluar(modelo, Xp, yp, "prevalencia_sin_class_weight", nombres_clases)
    for r in (res_test_bal, res_test_prev):
        print(f"    [{r['conjunto']}] F1 macro={r['f1_macro']:.4f}  "
              f"F1 ponderado={r['f1_ponderado']:.4f}  PR-AUC macro={r['pr_auc_macro']:.4f}  "
              f"exactitud={r['exactitud_global']:.4f}")

    mask_f = (extra_te["clase"] != "sano").values
    pred_sev = reg_sev.predict(X_te[mask_f])
    met_sev["mae_prueba"] = float(mean_absolute_error(
        extra_te["severidad_f"].values[mask_f], pred_sev))
    met_sev["r2_prueba"] = float(r2_score(extra_te["severidad_f"].values[mask_f], pred_sev))

    print("\n[9] Figuras")
    figuras = {
        "fig1_diagrama_ph": str(fig_diagrama_ph(p)),
        "fig2a_matriz_confusion_balanceado": str(fig_matriz_confusion(
            res_test_bal, "Matriz de confusión — conjunto de prueba balanceado",
            "fig2a_matriz_confusion_balanceado.png", nombres_clases)),
        "fig2b_matriz_confusion_prevalencia": str(fig_matriz_confusion(
            res_test_prev, "Matriz de confusión — prevalencia realista de campo",
            "fig2b_matriz_confusion_prevalencia.png", nombres_clases)),
        "fig3a_curvas_pr_balanceado": str(fig_curvas_pr(
            res_test_bal, "conjunto balanceado", "fig3a_curvas_pr_balanceado.png",
            nombres_clases)),
        "fig3b_curvas_pr_prevalencia": str(fig_curvas_pr(
            res_test_prev, "prevalencia realista", "fig3b_curvas_pr_prevalencia.png",
            nombres_clases)),
        "fig4_importancia_permutacion": str(ruta_imp),
        "fig7_mapa_firmas": str(fig_mapa_firmas(df_bal, topo)),
    }
    ruta_det, tabla_det = fig_deteccion_vs_severidad(res_test_bal, extra_te)
    figuras["fig5_deteccion_vs_severidad"] = str(ruta_det)

    tabla_ruido, tabla_disc, repeticiones = {}, {}, {}
    if con_estudios:
        params_rf = mejores if ganador == "random_forest" else None
        print("\n[10] Estudio de sensibilidad al ruido de los instrumentos")
        tabla_ruido = estudio_ruido(p, semilla, n_cond=n_cond_estudios,
                                    parametros_rf=params_rf)
        figuras["fig6_sensibilidad_ruido"] = str(_fig_barrido(
            tabla_ruido, "Factor multiplicador del ruido de los instrumentos",
            "Sensibilidad al ruido de los instrumentos", "fig6_sensibilidad_ruido.png",
            marca_x=1.0, texto_marca="instrumentos de la Fase 1"))

        print("\n[11] Barrido de discrepancia entre modelo y planta")
        tabla_disc = estudio_discrepancia(p, semilla, n_cond=n_cond_estudios,
                                          parametros_rf=params_rf)
        figuras["fig8_sensibilidad_discrepancia"] = str(_fig_barrido(
            tabla_disc, "Error de calibración del gemelo digital (δ)",
            "Sensibilidad a la discrepancia entre modelo y planta",
            "fig8_sensibilidad_discrepancia.png",
            marca_x=NIVEL_DISCREPANCIA, texto_marca="caso base"))

        print("\n[12] Repeticiones con error de calibración por corrida")
        repeticiones = repeticiones_por_corrida(p, semilla, n_cond=n_cond_estudios,
                                                parametros_rf=params_rf)
        print(f"    F1 macro: media={repeticiones['f1_macro_media']:.4f} "
              f"desv={repeticiones['f1_macro_desv']:.4f} "
              f"[{repeticiones['f1_macro_min']:.4f}, {repeticiones['f1_macro_max']:.4f}]")

    aperturas = {part.sellado.nombre: part.sellado.n_aperturas,
                 sellado_prev.nombre: sellado_prev.n_aperturas}
    corrida_valida = all(n == 1 for n in aperturas.values())

    metricas = {
        "corrida_valida": corrida_valida,
        "aperturas_del_conjunto_de_prueba": aperturas,
        "motivos_de_apertura": {part.sellado.nombre: part.sellado.aperturas,
                                sellado_prev.nombre: sellado_prev.aperturas},
        "topologia": topo.nombre,
        "descripcion_topologia": topo.descripcion,
        "semilla_maestra": semilla,
        "nivel_discrepancia": meta_gen["nivel_discrepancia"],
        "modo_discrepancia": meta_gen["modo_discrepancia"],
        "generacion": meta_gen,
        "parametros_provisionales": provisionales,
        "calibracion_ua": cargar_calibracion(),
        "parametros_equipo": resumen_parametros(p),
        "clases": list(nombres_clases),
        "particion": {"filas": {"entrenamiento": int(len(part.y_tr)),
                                "validacion": int(len(part.y_val)),
                                "prueba": int(part.sellado.n_filas)},
                      "condiciones": {k: len(v) for k, v in part.conds.items()},
                      "condiciones_compartidas_entre_particiones": 0},
        "seleccion_de_modelo": {
            "criterio": "F1 macro sobre el conjunto de VALIDACIÓN", "ganador": ganador,
            "candidatos": {k: {kk: vv for kk, vv in v.items() if kk != "estimador"}
                           for k, v in seleccion.items()}},
        "columnas_de_entrada": list(columnas_residuos(topo)),
        "metricas": {
            "validacion": {k: v for k, v in res_val.items() if not k.startswith("_")},
            "prueba_balanceada": {k: v for k, v in res_test_bal.items()
                                  if not k.startswith("_")},
            "prevalencia_realista": {k: v for k, v in res_test_prev.items()
                                     if not k.startswith("_")},
            "prevalencia_sin_class_weight": {k: v for k, v in res_prev_sin_peso.items()
                                             if not k.startswith("_")}},
        "modelo_de_severidad": met_sev,
        "importancia_permutacion": tabla_imp,
        "contraste_con_la_fisica": contraste,
        "deteccion_vs_severidad": tabla_det,
        "sensibilidad_al_ruido": tabla_ruido,
        "sensibilidad_a_la_discrepancia": tabla_disc,
        "repeticiones_por_corrida": repeticiones,
        "prevalencia_objetivo": prevalencia_campo(topo),
        "figuras": figuras,
    }
    ruta = DIR_RESULTADOS / f"metricas{sufijo}.json"
    ruta.write_text(json.dumps(metricas, indent=2, ensure_ascii=False, default=str),
                    encoding="utf-8")
    print(f"\n[13] Métricas -> {ruta}")
    print(f"     corrida_valida = {corrida_valida} (aperturas: {aperturas})")
    return metricas


if __name__ == "__main__":
    import argparse, sys
    sys.path.insert(0, str(RAIZ))
    ap = argparse.ArgumentParser(description="Entrena y evalúa el clasificador FDD.")
    ap.add_argument("--sufijo", default="")
    ap.add_argument("--semilla", type=int, default=SEMILLA_MAESTRA)
    ap.add_argument("--sin-estudios", action="store_true")
    ap.add_argument("--n-cond-estudios", type=int, default=120)
    ap.add_argument("--sin-informe", action="store_true")
    args = ap.parse_args()

    met = ejecutar(args.semilla, args.sufijo, not args.sin_estudios, args.n_cond_estudios)
    if not args.sin_informe:
        from .reporte import generar_informe
        print(f"[14] Informe Word -> {generar_informe(met)}")
