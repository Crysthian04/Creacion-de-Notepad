"""
Sistema Predictivo de Refacciones — Flota KingLong BUSPORT
═══════════════════════════════════════════════════════════
Basado en el modelo Power BI de la flota (Consolidado_Payment,
Maestro_Vehiculos, Ralenti, Kilometraje, Encendido, Rutas).

Módulos:
  1. Generación / carga de datos reales de la flota
  2. Análisis Estadístico Avanzado
  3. Análisis de Weibull (refacciones y buses)
  4. Modelos ML: clasificación (quiebre/fallo) + regresión (demanda)
  5. Exportación completa a Word
"""

# ── Instalación (descomentar en Colab) ──────────────────────────────────────
# !pip install python-docx imbalanced-learn scipy reliability

import io
import warnings
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import seaborn as sns
from scipy import stats
from scipy.stats import weibull_min, kstest, shapiro, kruskal, spearmanr
from scipy.optimize import curve_fit

from imblearn.over_sampling import SMOTE
from sklearn.model_selection import train_test_split, GridSearchCV, cross_val_score
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score, classification_report, confusion_matrix,
    mean_absolute_error, mean_squared_error, r2_score, roc_auc_score,
)
from sklearn.preprocessing import LabelEncoder, StandardScaler

from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

warnings.filterwarnings("ignore")
np.random.seed(42)

# ════════════════════════════════════════════════════════════════════════════
# SECCIÓN 0 — CONFIGURACIÓN
# ════════════════════════════════════════════════════════════════════════════

# Umbrales de cambio de refacciones (en KM) — ajustar según manual KingLong
UMBRALES_KM = {
    "Filtro de Aceite":      5_000,
    "Filtro de Combustible": 15_000,
    "Pastillas de Freno":    30_000,
    "Filtro de Aire":        20_000,
    "Correa de Distribución":60_000,
    "Amortiguadores":        80_000,
    "Bujías":                40_000,
    "Llantas":              100_000,
}

BUSES = [f"BP-{str(i).zfill(3)}" for i in range(1, 26)]   # 25 buses KingLong
MODELOS = ["KingLong XMQ6127", "KingLong XMQ6112", "KingLong XMQ6900"]
N_TRANS = 2000   # transacciones de combustible a simular
N_REFAC = 800    # registros de refacciones

# ════════════════════════════════════════════════════════════════════════════
# SECCIÓN 1 — DATOS DE FLOTA (reemplazar con tus CSVs reales)
# ════════════════════════════════════════════════════════════════════════════
#
# Si tienes los CSV reales exportados de Power BI:
#   df_pago    = pd.read_csv("Consolidado_Payment.csv")
#   df_maestro = pd.read_csv("Maestro_Vehiculos.csv")
#   df_ralenti = pd.read_csv("Ralenti.csv")
#   df_refac   = pd.read_csv("Refacciones.csv")
#
# De lo contrario el bloque de abajo genera datos representativos:

print("=" * 65)
print("  GENERANDO DATOS DE FLOTA KINGLONG BUSPORT")
print("=" * 65)

# ── 1a. Maestro de vehículos ─────────────────────────────────────────────────
df_maestro = pd.DataFrame({
    "BUSPORT":            BUSES,
    "modelo":             np.random.choice(MODELOS, len(BUSES)),
    "año_fabricacion":    np.random.randint(2010, 2022, len(BUSES)),
    "capacidad_tanque":   np.random.choice([200, 220, 240], len(BUSES)),
    "litros_x_km":        np.round(np.random.uniform(0.28, 0.42, len(BUSES)), 4),
    "odometro_inicial":   np.random.randint(50_000, 300_000, len(BUSES)),
    "consumo_ralenti_lh": np.round(np.random.uniform(1.8, 2.5, len(BUSES)), 2),
})
df_maestro["vida_util_km"] = 500_000
df_maestro["km_acumulados"] = df_maestro["odometro_inicial"] + np.random.randint(20_000, 150_000, len(BUSES))
df_maestro["antiguedad_años"] = 2026 - df_maestro["año_fabricacion"]

# ── 1b. Transacciones de combustible (Consolidado_Payment) ───────────────────
fechas = pd.date_range("2024-01-01", "2026-05-31", periods=N_TRANS)
buses_trans = np.random.choice(BUSES, N_TRANS)

litros_teoricos = df_maestro.set_index("BUSPORT")["litros_x_km"]
km_recorrido = np.random.randint(80, 550, N_TRANS)
litros_real = np.array([
    km * litros_teoricos.get(b, 0.35) * np.random.uniform(0.85, 1.40)
    for km, b in zip(km_recorrido, buses_trans)
])

df_pago = pd.DataFrame({
    "BUSPORT":             buses_trans,
    "fecha_transaccion":   fechas,
    "km_recorrido":        km_recorrido,
    "litros_dispensados":  np.round(litros_real, 2),
    "litros_teoricos":     np.round([km * litros_teoricos.get(b, 0.35)
                                     for km, b in zip(km_recorrido, buses_trans)], 2),
    "odometro":            np.random.randint(50_000, 450_000, N_TRANS),
    "costo_combustible":   np.round(litros_real * np.random.uniform(0.85, 0.92, N_TRANS), 2),
})
df_pago["km_x_litro_real"]    = np.round(df_pago["km_recorrido"] / df_pago["litros_dispensados"], 3)
df_pago["km_x_litro_teorico"] = np.round(1 / df_maestro.set_index("BUSPORT")["litros_x_km"]
                                          .reindex(buses_trans).values, 3)
df_pago["pct_desviacion"]     = np.round(
    (df_pago["km_x_litro_real"] - df_pago["km_x_litro_teorico"]) / df_pago["km_x_litro_teorico"], 4)
df_pago["anomalia_galonaje"]  = np.where(
    df_pago["litros_dispensados"] > df_pago["litros_teoricos"] * 1.5, "Alerta Posible Robo", "Normal")
df_pago["estado_eficiencia"] = pd.cut(
    df_pago["pct_desviacion"],
    bins=[-np.inf, -0.30, -0.20, 0.20, 0.30, np.inf],
    labels=["Alerta–", "Precaución–", "Bien", "Precaución+", "Alerta+"])

# ── 1c. Ralentí ───────────────────────────────────────────────────────────────
N_RAL = 1200
df_ralenti = pd.DataFrame({
    "BUSPORT":        np.random.choice(BUSES, N_RAL),
    "fecha_inicio":   pd.date_range("2024-01-01", periods=N_RAL, freq="10h"),
    "horas_ralenti":  np.round(np.abs(np.random.normal(0.5, 0.4, N_RAL)), 2),
})
df_ralenti["excede_limite"] = (df_ralenti["horas_ralenti"] > 0.25).astype(int)

# ── 1d. Registro de refacciones ───────────────────────────────────────────────
tipos = list(UMBRALES_KM.keys())
df_refac = pd.DataFrame({
    "BUSPORT":         np.random.choice(BUSES, N_REFAC),
    "tipo_refaccion":  np.random.choice(tipos, N_REFAC),
    "fecha_cambio":    pd.date_range("2022-01-01", periods=N_REFAC, freq="16h"),
    "km_al_cambio":    np.random.randint(5_000, 450_000, N_REFAC),
    "costo_pieza":     np.round(np.random.uniform(50, 3500, N_REFAC), 2),
    "proveedor":       np.random.choice(["AutoPartes SA", "Refac Plus", "KingLong OEM"], N_REFAC),
})
# Duración real antes del cambio (variable clave para Weibull)
df_refac["km_vida_real"] = np.array([
    np.random.normal(UMBRALES_KM[t] * np.random.uniform(0.7, 1.3), UMBRALES_KM[t] * 0.15)
    for t in df_refac["tipo_refaccion"]
]).clip(1000)

print(f"  Buses:          {len(BUSES)}")
print(f"  Transacciones:  {len(df_pago)}")
print(f"  Eventos ralentí:{len(df_ralenti)}")
print(f"  Cambios refac:  {len(df_refac)}")


# ════════════════════════════════════════════════════════════════════════════
# SECCIÓN 2 — DATASET MAESTRO PARA ML
# ════════════════════════════════════════════════════════════════════════════

print("\n" + "=" * 65)
print("  CONSTRUYENDO DATASET MAESTRO")
print("=" * 65)

# Agregados por bus
agg_pago = df_pago.groupby("BUSPORT").agg(
    km_total=("km_recorrido", "sum"),
    litros_total=("litros_dispensados", "sum"),
    recargas=("litros_dispensados", "count"),
    km_x_litro_prom=("km_x_litro_real", "mean"),
    pct_desv_prom=("pct_desviacion", "mean"),
    pct_desv_std=("pct_desviacion", "std"),
    anomalias=("anomalia_galonaje", lambda x: (x == "Alerta Posible Robo").sum()),
    costo_combustible_total=("costo_combustible", "sum"),
).reset_index()

agg_ralenti = df_ralenti.groupby("BUSPORT").agg(
    horas_ralenti_total=("horas_ralenti", "sum"),
    eventos_ralenti=("horas_ralenti", "count"),
    ralenti_prom=("horas_ralenti", "mean"),
    eventos_sobre_limite=("excede_limite", "sum"),
).reset_index()

# Dataset principal
df_ml = (df_maestro
         .merge(agg_pago,   on="BUSPORT", how="left")
         .merge(agg_ralenti, on="BUSPORT", how="left")
         .fillna(0))

# Variables derivadas
df_ml["costo_x_km"]         = np.round(df_ml["costo_combustible_total"] / df_ml["km_total"].clip(1), 4)
df_ml["eficiencia_ratio"]   = np.round(df_ml["km_x_litro_prom"] / (1 / df_ml["litros_x_km"].clip(0.01)), 4)
df_ml["ralenti_pct"]        = np.round(df_ml["horas_ralenti_total"] / (df_ml["km_total"].clip(1) / 40), 4)
df_ml["desgaste_acumulado"] = np.round(df_ml["km_acumulados"] / df_ml["vida_util_km"], 4)

# Targets
df_ml["riesgo_fallo_mayor"]  = (
    (df_ml["pct_desv_prom"] < -0.20) |
    (df_ml["horas_ralenti_total"] > df_ml["horas_ralenti_total"].quantile(0.75)) |
    (df_ml["antiguedad_años"] > 10)
).astype(int)

df_ml["alerta_refaccion"] = (
    (df_ml["km_acumulados"] % 15_000 < 3_000) |  # próximo cambio de filtro
    (df_ml["eficiencia_ratio"] < 0.85)
).astype(int)

df_ml["demanda_refac_mes"] = (
    df_ml["km_total"] / 5_000 * np.random.uniform(0.8, 1.2, len(df_ml))
).round().astype(int).clip(0)

print(df_ml[["BUSPORT", "km_total", "eficiencia_ratio", "desgaste_acumulado",
              "riesgo_fallo_mayor", "alerta_refaccion", "demanda_refac_mes"]].to_string(index=False))


# ════════════════════════════════════════════════════════════════════════════
# SECCIÓN 3 — ANÁLISIS ESTADÍSTICO AVANZADO
# ════════════════════════════════════════════════════════════════════════════

print("\n" + "=" * 65)
print("  ANÁLISIS ESTADÍSTICO AVANZADO")
print("=" * 65)

NUM_COLS = ["km_total", "litros_total", "km_x_litro_prom", "pct_desv_prom",
            "horas_ralenti_total", "eficiencia_ratio", "desgaste_acumulado", "costo_x_km"]

desc = df_ml[NUM_COLS].describe().T
desc["skewness"] = df_ml[NUM_COLS].skew()
desc["kurtosis"] = df_ml[NUM_COLS].kurt()
desc["cv_%"]     = (df_ml[NUM_COLS].std() / df_ml[NUM_COLS].mean() * 100).round(2)

print("\nEstadísticas descriptivas avanzadas:")
print(desc.round(4))

# Test de normalidad (Shapiro-Wilk)
print("\nTest de normalidad Shapiro-Wilk:")
normalidad = {}
for col in NUM_COLS:
    stat, p = shapiro(df_ml[col].dropna())
    es_normal = "Sí" if p > 0.05 else "No"
    normalidad[col] = {"W": round(stat, 4), "p-valor": round(p, 4), "Normal": es_normal}
    print(f"  {col:<30} W={stat:.4f}  p={p:.4f}  Normal: {es_normal}")

# Correlación de Spearman (robusta para no-normales)
corr_sp = df_ml[NUM_COLS].corr(method="spearman")
print("\nCorrelación de Spearman calculada.")

# IQR y detección de outliers por bus
q1 = df_ml["km_x_litro_prom"].quantile(0.25)
q3 = df_ml["km_x_litro_prom"].quantile(0.75)
iqr = q3 - q1
outliers_efic = df_ml[(df_ml["km_x_litro_prom"] < q1 - 1.5*iqr) |
                       (df_ml["km_x_litro_prom"] > q3 + 1.5*iqr)]["BUSPORT"].tolist()
print(f"\nBuses con eficiencia atípica (IQR): {outliers_efic if outliers_efic else 'Ninguno'}")

# Test Kruskal-Wallis: diferencia de eficiencia entre modelos de bus
grupos = [grp["km_x_litro_prom"].values for _, grp in df_ml.merge(
    df_maestro[["BUSPORT", "modelo"]], on="BUSPORT").groupby("modelo")]
if len(grupos) > 1:
    h_stat, p_kw = kruskal(*grupos)
    print(f"\nKruskal-Wallis KM/L entre modelos: H={h_stat:.3f}  p={p_kw:.4f}")
    print(f"  → {'Diferencia significativa entre modelos' if p_kw < 0.05 else 'Sin diferencia significativa'}")

# ── Figuras de análisis estadístico ──────────────────────────────────────────

fig, axes = plt.subplots(2, 3, figsize=(16, 9))
fig.suptitle("Análisis Estadístico Avanzado — Flota KingLong BUSPORT", fontsize=14, fontweight="bold")

# Histograma + KDE eficiencia
ax = axes[0, 0]
df_ml["km_x_litro_prom"].hist(bins=10, ax=ax, color="steelblue", edgecolor="white", density=True)
df_ml["km_x_litro_prom"].plot(kind="kde", ax=ax, color="red", linewidth=2)
ax.set_title("Distribución KM/Litro Real")
ax.set_xlabel("KM/Litro")

# Boxplot por estado de riesgo
ax = axes[0, 1]
df_ml.boxplot(column="eficiencia_ratio", by="riesgo_fallo_mayor", ax=ax, patch_artist=True)
ax.set_title("Eficiencia vs Riesgo de Fallo")
ax.set_xlabel("Riesgo de Fallo Mayor (0=No, 1=Sí)")
ax.set_ylabel("Ratio de Eficiencia")
plt.sca(ax)
plt.title("Eficiencia vs Riesgo de Fallo")

# Correlación Spearman
ax = axes[0, 2]
mask = np.triu(np.ones_like(corr_sp, dtype=bool))
sns.heatmap(corr_sp, mask=mask, annot=True, cmap="coolwarm", fmt=".2f", ax=ax,
            annot_kws={"size": 6})
ax.set_title("Correlación Spearman")
ax.tick_params(axis="x", labelsize=6)
ax.tick_params(axis="y", labelsize=6)

# Scatter KM total vs Horas ralentí
ax = axes[1, 0]
sc = ax.scatter(df_ml["km_total"], df_ml["horas_ralenti_total"],
                c=df_ml["eficiencia_ratio"], cmap="RdYlGn", s=80, edgecolors="k", linewidths=0.5)
plt.colorbar(sc, ax=ax, label="Ratio Eficiencia")
ax.set_xlabel("KM Total")
ax.set_ylabel("Horas Ralentí Total")
ax.set_title("KM vs Ralentí (color=Eficiencia)")

# Barras costo x km por bus (top 10)
ax = axes[1, 1]
top10 = df_ml.nlargest(10, "costo_x_km")[["BUSPORT", "costo_x_km"]]
ax.barh(top10["BUSPORT"], top10["costo_x_km"], color="salmon")
ax.set_title("Top 10 Buses: Mayor Costo/KM")
ax.set_xlabel("B/. por KM")

# QQ-plot eficiencia
ax = axes[1, 2]
stats.probplot(df_ml["km_x_litro_prom"], dist="norm", plot=ax)
ax.set_title("Q-Q Plot KM/Litro vs Normal")

plt.tight_layout()
plt.savefig("estadistica_avanzada.png", dpi=150)
plt.close()
print("\nGráfico de estadística avanzada guardado.")


# ════════════════════════════════════════════════════════════════════════════
# SECCIÓN 4 — ANÁLISIS DE WEIBULL
# ════════════════════════════════════════════════════════════════════════════

print("\n" + "=" * 65)
print("  ANÁLISIS DE WEIBULL — REFACCIONES Y BUSES")
print("=" * 65)

def weibull_fit(tiempos: np.ndarray, nombre: str = "") -> dict:
    """Ajusta distribución Weibull de 2 parámetros y retorna métricas."""
    tiempos = tiempos[tiempos > 0]
    beta, loc, eta = weibull_min.fit(tiempos, floc=0)  # loc=0 → Weibull puro
    mttf = eta * stats.gamma(1 + 1/beta)
    b10  = eta * (-np.log(0.90)) ** (1/beta)   # vida B10 (10% probabilidad fallo)
    b50  = eta * (-np.log(0.50)) ** (1/beta)   # vida B50 (mediana)
    stat_ks, p_ks = kstest(tiempos, "weibull_min", args=(beta, 0, eta))
    resultado = {
        "nombre": nombre, "beta": round(beta, 4), "eta": round(eta, 2),
        "mttf": round(mttf, 2), "b10_km": round(b10, 2), "b50_km": round(b50, 2),
        "ks_stat": round(stat_ks, 4), "ks_p": round(p_ks, 4),
        "ajuste": "Bueno" if p_ks > 0.05 else "Revisar",
        "tipo_fallo": ("Mortalidad infantil" if beta < 1
                       else "Fallo aleatorio" if abs(beta - 1) < 0.2
                       else "Desgaste/Envejecimiento"),
    }
    print(f"  {nombre:<28} β={beta:.3f}  η={eta:>10.1f}  MTTF={mttf:>10.1f}  "
          f"B10={b10:>9.1f}  Tipo: {resultado['tipo_fallo']}")
    return resultado

# ── 4a. Weibull por tipo de refacción ────────────────────────────────────────
print("\nWeibull por tipo de refacción (KM de vida real):")
resultados_weibull_refac = []
for tipo, grp in df_refac.groupby("tipo_refaccion"):
    if len(grp) >= 10:
        res = weibull_fit(grp["km_vida_real"].values, tipo)
        resultados_weibull_refac.append(res)

df_weibull_refac = pd.DataFrame(resultados_weibull_refac)

# ── 4b. Weibull por bus (desgaste acumulado como proxy de tiempo) ─────────────
print("\nWeibull por modelo de bus (KM acumulados):")
df_buses_km = df_ml.merge(df_maestro[["BUSPORT", "modelo"]], on="BUSPORT")
resultados_weibull_bus = []
for modelo, grp in df_buses_km.groupby("modelo"):
    if len(grp) >= 5:
        res = weibull_fit(grp["km_acumulados"].values, modelo)
        resultados_weibull_bus.append(res)

df_weibull_bus = pd.DataFrame(resultados_weibull_bus)

# ── 4c. Gráficos Weibull ─────────────────────────────────────────────────────

def plot_weibull_panel(df_w: pd.DataFrame, tiempos_dict: dict,
                       titulo: str, path: str, unidad: str = "KM"):
    """Genera panel con curvas de confiabilidad y tasa de fallo."""
    n = len(df_w)
    cols = min(3, n)
    rows = (n + cols - 1) // cols
    fig, axes = plt.subplots(rows * 2, cols, figsize=(5 * cols, 4 * rows * 2))
    fig.suptitle(titulo, fontsize=13, fontweight="bold")
    axes = np.array(axes).reshape(rows * 2, cols)

    for idx, row in df_w.iterrows():
        r, c = divmod(idx, cols)
        beta, eta = row["beta"], row["eta"]
        t = np.linspace(0.01, eta * 3, 500)

        R_t   = np.exp(-(t / eta) ** beta)            # Confiabilidad
        h_t   = (beta / eta) * (t / eta) ** (beta-1)  # Tasa de fallo (hazard)
        F_t   = 1 - R_t                               # Probabilidad acumulada de fallo

        # Confiabilidad
        ax1 = axes[r * 2, c]
        ax1.plot(t, R_t, "steelblue", lw=2, label="R(t)")
        ax1.axhline(0.9, color="g", ls="--", lw=1, label="90%")
        ax1.axhline(0.5, color="orange", ls="--", lw=1, label="50%")
        ax1.axvline(row["b10_km"], color="g", ls=":", lw=1)
        ax1.axvline(row["b50_km"], color="orange", ls=":", lw=1)
        ax1.set_title(f"{row['nombre']}\nβ={beta:.2f}  η={eta:,.0f}", fontsize=8)
        ax1.set_ylabel("Confiabilidad R(t)")
        ax1.set_xlabel(unidad)
        ax1.legend(fontsize=7)
        ax1.set_ylim(0, 1.05)
        ax1.grid(alpha=0.3)

        # Tasa de fallo
        ax2 = axes[r * 2 + 1, c]
        ax2.plot(t, h_t, "crimson", lw=2)
        ax2.set_title(f"Tasa de Fallo — {row['tipo_fallo']}", fontsize=8)
        ax2.set_ylabel("h(t)")
        ax2.set_xlabel(unidad)
        ax2.grid(alpha=0.3)

    # Ocultar ejes vacíos
    total = rows * cols
    for extra in range(n, total):
        r, c = divmod(extra, cols)
        axes[r * 2, c].set_visible(False)
        axes[r * 2 + 1, c].set_visible(False)

    plt.tight_layout()
    plt.savefig(path, dpi=150)
    plt.close()
    print(f"  Gráfico guardado: {path}")

plot_weibull_panel(
    df_weibull_refac, {},
    "Análisis Weibull — Refacciones KingLong BUSPORT",
    "weibull_refacciones.png", "KM de Vida"
)

if len(df_weibull_bus) > 0:
    plot_weibull_panel(
        df_weibull_bus, {},
        "Análisis Weibull — Buses por Modelo",
        "weibull_buses.png", "KM Acumulados"
    )

# ── 4d. Gráfico comparativo B10/MTTF ─────────────────────────────────────────
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
fig.suptitle("Comparativa Weibull — Refacciones", fontweight="bold")

df_weibull_refac.sort_values("mttf").plot(
    kind="barh", x="nombre", y="mttf", ax=ax1, color="steelblue", legend=False)
ax1.set_title("MTTF por Refacción (KM Promedio hasta Fallo)")
ax1.set_xlabel("MTTF (KM)")

df_weibull_refac.sort_values("b10_km").plot(
    kind="barh", x="nombre", y="b10_km", ax=ax2, color="salmon", legend=False)
ax2.set_title("Vida B10 (KM con 90% confiabilidad)")
ax2.set_xlabel("B10 (KM)")

plt.tight_layout()
plt.savefig("weibull_comparativa.png", dpi=150)
plt.close()


# ════════════════════════════════════════════════════════════════════════════
# SECCIÓN 5 — MODELOS DE MACHINE LEARNING
# ════════════════════════════════════════════════════════════════════════════

print("\n" + "=" * 65)
print("  MODELOS DE MACHINE LEARNING")
print("=" * 65)

# Codificar modelo de bus
df_ml_enc = df_ml.copy()
le = LabelEncoder()
df_ml_enc["modelo_enc"] = le.fit_transform(
    df_ml.merge(df_maestro[["BUSPORT", "modelo"]], on="BUSPORT")["modelo"])

FEATURES = [
    "km_total", "litros_total", "km_x_litro_prom", "pct_desv_prom", "pct_desv_std",
    "horas_ralenti_total", "eventos_sobre_limite", "ralenti_pct",
    "eficiencia_ratio", "desgaste_acumulado", "costo_x_km", "antiguedad_años",
    "modelo_enc",
]

PARAM_TREE = {"max_depth": [3, 5, 10, None], "min_samples_split": [2, 5], "min_samples_leaf": [1, 2]}
PARAM_RF   = {"n_estimators": [100, 200], "max_depth": [5, 10, None], "min_samples_split": [2, 5]}
PARAM_GB   = {"n_estimators": [100, 200], "max_depth": [3, 5], "learning_rate": [0.05, 0.1]}

resultados_ml = {}

def clasificacion_completa(nombre: str, X: pd.DataFrame, y: pd.Series) -> dict:
    print(f"\n  ── {nombre} ──")
    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    # SMOTE solo si hay desbalance
    ratio = y_tr.mean()
    if ratio < 0.3 or ratio > 0.7:
        sm = SMOTE(random_state=42)
        X_tr, y_tr = sm.fit_resample(X_tr, y_tr)
        print(f"    SMOTE aplicado (ratio original: {ratio:.2f})")

    modelos_clf = {
        "Árbol de Decisión": GridSearchCV(DecisionTreeClassifier(random_state=42),
                                          PARAM_TREE, cv=5, scoring="f1", n_jobs=-1),
        "Random Forest":     GridSearchCV(RandomForestClassifier(random_state=42),
                                          PARAM_RF, cv=5, scoring="f1", n_jobs=-1),
        "Gradient Boosting": GridSearchCV(GradientBoostingClassifier(random_state=42),
                                          PARAM_GB, cv=5, scoring="f1", n_jobs=-1),
    }

    res = {"nombre": nombre, "modelos": {}}
    for nom_m, g in modelos_clf.items():
        g.fit(X_tr, y_tr)
        m = g.best_estimator_
        y_pred = m.predict(X_te)
        acc  = accuracy_score(y_te, y_pred)
        f1   = cross_val_score(m, X_te, y_te, cv=3, scoring="f1").mean()
        try:
            auc = roc_auc_score(y_te, m.predict_proba(X_te)[:, 1])
        except Exception:
            auc = np.nan
        rep  = classification_report(y_te, y_pred)
        cm   = confusion_matrix(y_te, y_pred)

        print(f"    {nom_m:<22} Acc={acc:.3f}  F1={f1:.3f}  AUC={auc:.3f}")
        res["modelos"][nom_m] = {
            "params": g.best_params_, "acc": acc, "f1": f1, "auc": auc,
            "rep": rep, "cm": cm, "y_te": y_te, "y_pred": y_pred, "modelo": m,
        }

    mejor = max(res["modelos"], key=lambda k: res["modelos"][k]["f1"])
    res["mejor"] = mejor
    print(f"    → Mejor modelo: {mejor}")
    return res


X_ml = df_ml_enc[FEATURES]

# Clasificación 1: Alerta de refacción (necesita pieza pronto)
res_alerta = clasificacion_completa("Alerta de Refacción", X_ml, df_ml_enc["alerta_refaccion"])

# Clasificación 2: Riesgo de fallo mayor del bus
res_fallo = clasificacion_completa("Riesgo de Fallo Mayor", X_ml, df_ml_enc["riesgo_fallo_mayor"])

# Regresión: Demanda de refacciones por mes
print("\n  ── Regresión: Demanda de Refacciones/Mes ──")
scaler = StandardScaler()
X_reg  = scaler.fit_transform(X_ml)
y_reg  = df_ml_enc["demanda_refac_mes"]
X_tr_r, X_te_r, y_tr_r, y_te_r = train_test_split(X_reg, y_reg, test_size=0.2, random_state=42)

param_rfr = {"n_estimators": [100, 200], "max_depth": [5, 10, None]}
g_rfr = GridSearchCV(RandomForestRegressor(random_state=42), param_rfr, cv=5,
                     scoring="neg_mean_absolute_error", n_jobs=-1)
g_rfr.fit(X_tr_r, y_tr_r)
best_rfr   = g_rfr.best_estimator_
y_pred_reg = best_rfr.predict(X_te_r)
mae  = mean_absolute_error(y_te_r, y_pred_reg)
rmse = np.sqrt(mean_squared_error(y_te_r, y_pred_reg))
r2   = r2_score(y_te_r, y_pred_reg)
print(f"    RandomForest Reg.  MAE={mae:.2f}  RMSE={rmse:.2f}  R²={r2:.4f}")

# Importancia de variables
feat_imp = pd.Series(best_rfr.feature_importances_, index=FEATURES).sort_values(ascending=False)

# ── Gráficos ML ──────────────────────────────────────────────────────────────

def plot_cm_triple(res: dict, path: str):
    modelos = list(res["modelos"].keys())
    fig, axes = plt.subplots(1, len(modelos), figsize=(5 * len(modelos), 4))
    fig.suptitle(f"Matrices de Confusión — {res['nombre']}", fontweight="bold")
    if len(modelos) == 1:
        axes = [axes]
    for ax, nom in zip(axes, modelos):
        cm = res["modelos"][nom]["cm"]
        sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", ax=ax,
                    xticklabels=["No", "Sí"], yticklabels=["No", "Sí"])
        ax.set_title(f"{nom}\nAcc={res['modelos'][nom]['acc']:.3f}  F1={res['modelos'][nom]['f1']:.3f}")
        ax.set_xlabel("Predicción")
        ax.set_ylabel("Real")
    plt.tight_layout()
    plt.savefig(path, dpi=150)
    plt.close()

plot_cm_triple(res_alerta, "cm_alerta_refaccion.png")
plot_cm_triple(res_fallo,  "cm_riesgo_fallo.png")

# Scatter regresión
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))
ax1.scatter(y_te_r, y_pred_reg, alpha=0.6, color="steelblue")
mn, mx = min(y_te_r.min(), y_pred_reg.min()), max(y_te_r.max(), y_pred_reg.max())
ax1.plot([mn, mx], [mn, mx], "r--")
ax1.set_xlabel("Demanda Real")
ax1.set_ylabel("Demanda Predicha")
ax1.set_title(f"Demanda Refacciones/Mes\nMAE={mae:.2f}  R²={r2:.4f}")

feat_imp.plot(kind="bar", ax=ax2, color="steelblue")
ax2.set_title("Importancia de Variables — Demanda")
ax2.set_ylabel("Importancia")
ax2.tick_params(axis="x", rotation=45, labelsize=8)

plt.tight_layout()
plt.savefig("ml_regresion.png", dpi=150)
plt.close()

# Resumen comparativo de modelos
rows_comp = []
for res in [res_alerta, res_fallo]:
    for nom_m, d in res["modelos"].items():
        rows_comp.append({
            "Análisis": res["nombre"], "Modelo": nom_m,
            "Exactitud": f"{d['acc']:.4f}", "F1": f"{d['f1']:.4f}",
            "AUC-ROC": f"{d['auc']:.4f}" if not np.isnan(d["auc"]) else "N/A",
            "Mejor": "★" if nom_m == res["mejor"] else "",
        })
rows_comp.append({
    "Análisis": "Demanda Refacciones/Mes", "Modelo": "Random Forest Regressor",
    "Exactitud": f"R²={r2:.4f}", "F1": f"MAE={mae:.2f}", "AUC-ROC": f"RMSE={rmse:.2f}", "Mejor": "★",
})
df_comp = pd.DataFrame(rows_comp)
print("\nResumen comparativo de modelos:")
print(df_comp.to_string(index=False))


# ════════════════════════════════════════════════════════════════════════════
# SECCIÓN 6 — EXPORTACIÓN A WORD
# ════════════════════════════════════════════════════════════════════════════

print("\n" + "=" * 65)
print("  GENERANDO INFORME WORD")
print("=" * 65)

def capture_info(df):
    buf = io.StringIO()
    df.info(buf=buf)
    return buf.getvalue()

def df_to_word_table(doc, df, font_size=8):
    table = doc.add_table(rows=1, cols=len(df.columns))
    table.style = "Table Grid"
    hdr = table.rows[0].cells
    for i, col in enumerate(df.columns):
        hdr[i].text = str(col)
        hdr[i].paragraphs[0].runs[0].bold = True
    for _, row in df.iterrows():
        cells = table.add_row().cells
        for i, val in enumerate(row):
            cells[i].text = str(round(val, 4) if isinstance(val, float) else val)

doc = Document()
style = doc.styles["Normal"]
style.font.name = "Calibri"
style.font.size = Pt(10)

# Portada
doc.add_heading("Sistema Predictivo de Refacciones", 0)
doc.add_heading("Flota KingLong BUSPORT — Análisis Estadístico, Weibull y Machine Learning", 1)
p = doc.add_paragraph(f"Fecha de generación: {pd.Timestamp.now().strftime('%d/%m/%Y %H:%M')}")
p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
doc.add_page_break()

# ── Sección 1: Resumen de flota ───────────────────────────────────────────────
doc.add_heading("1. Resumen de la Flota", level=1)
doc.add_paragraph(f"• Total de buses activos: {len(BUSES)}")
doc.add_paragraph(f"• Transacciones de combustible analizadas: {N_TRANS}")
doc.add_paragraph(f"• Cambios de refacciones registrados: {N_REFAC}")
doc.add_paragraph(f"• Tipos de refacciones: {len(UMBRALES_KM)}")
doc.add_heading("Dataset Maestro por Bus (muestra)", level=2)
df_to_word_table(doc, df_ml[["BUSPORT", "km_total", "litros_total", "eficiencia_ratio",
                               "desgaste_acumulado", "riesgo_fallo_mayor", "alerta_refaccion"]].round(4))

# ── Sección 2: Estadística avanzada ──────────────────────────────────────────
doc.add_page_break()
doc.add_heading("2. Análisis Estadístico Avanzado", level=1)

doc.add_heading("Estadísticas Descriptivas", level=2)
df_to_word_table(doc, desc.reset_index().round(4))

doc.add_heading("Prueba de Normalidad — Shapiro-Wilk", level=2)
df_to_word_table(doc, pd.DataFrame(normalidad).T.reset_index().rename(columns={"index": "Variable"}))

doc.add_heading("Kruskal-Wallis: Diferencia KM/L entre Modelos de Bus", level=2)
doc.add_paragraph(f"H = {h_stat:.3f}  |  p-valor = {p_kw:.4f}")
doc.add_paragraph(f"Conclusión: {'Diferencia estadísticamente significativa (p < 0.05)' if p_kw < 0.05 else 'Sin diferencia significativa'}")

doc.add_heading("Gráficos de Análisis Estadístico", level=2)
doc.add_picture("estadistica_avanzada.png", width=Inches(6.2))

# ── Sección 3: Weibull refacciones ───────────────────────────────────────────
doc.add_page_break()
doc.add_heading("3. Análisis de Weibull — Refacciones", level=1)
doc.add_paragraph(
    "El análisis de Weibull permite estimar la confiabilidad de cada refacción "
    "en función del kilometraje, identificar el tipo de fallo (β<1: mortalidad "
    "infantil, β≈1: fallo aleatorio, β>1: desgaste) y definir intervalos óptimos "
    "de mantenimiento preventivo (vida B10 = 90% confiabilidad)."
)
doc.add_heading("Parámetros Weibull por Tipo de Refacción", level=2)
df_to_word_table(doc, df_weibull_refac.drop(columns=["nombre"]).rename(
    index=df_weibull_refac["nombre"]).assign(Refaccion=df_weibull_refac["nombre"].values)
    [["Refaccion", "beta", "eta", "mttf", "b10_km", "b50_km", "tipo_fallo", "ajuste"]].round(2))

doc.add_heading("Curvas de Confiabilidad y Tasa de Fallo", level=2)
doc.add_picture("weibull_refacciones.png", width=Inches(6.2))

doc.add_heading("Comparativa MTTF y Vida B10", level=2)
doc.add_picture("weibull_comparativa.png", width=Inches(6.2))

# ── Sección 4: Weibull buses ─────────────────────────────────────────────────
doc.add_page_break()
doc.add_heading("4. Análisis de Weibull — Buses por Modelo", level=1)
if len(df_weibull_bus) > 0:
    df_to_word_table(doc, df_weibull_bus[
        ["nombre", "beta", "eta", "mttf", "b10_km", "tipo_fallo", "ajuste"]].round(2))
    doc.add_picture("weibull_buses.png", width=Inches(6.2))

# ── Sección 5: Modelos ML ─────────────────────────────────────────────────────
doc.add_page_break()
doc.add_heading("5. Modelos de Machine Learning", level=1)

for res in [res_alerta, res_fallo]:
    doc.add_heading(f"5.{list([res_alerta,res_fallo]).index(res)+1}. {res['nombre']}", level=2)
    for nom_m, d in res["modelos"].items():
        doc.add_paragraph(f"{'★ ' if nom_m == res['mejor'] else '  '}{nom_m}: "
                          f"Exactitud={d['acc']:.4f}  F1={d['f1']:.4f}  AUC={d['auc']:.4f}")
        doc.add_paragraph(f"  Mejores hiperparámetros: {d['params']}")
    doc.add_paragraph(f"Reporte detallado del mejor modelo ({res['mejor']}):")
    doc.add_paragraph(res["modelos"][res["mejor"]]["rep"])

tag_alerta = "alerta_refaccion"
tag_fallo  = "riesgo_fallo_mayor"
doc.add_heading("Matrices de Confusión — Alerta de Refacción", level=2)
doc.add_picture("cm_alerta_refaccion.png", width=Inches(6))

doc.add_heading("Matrices de Confusión — Riesgo de Fallo", level=2)
doc.add_picture("cm_riesgo_fallo.png", width=Inches(6))

doc.add_heading("5.3. Predicción de Demanda de Refacciones/Mes", level=2)
doc.add_paragraph(f"Modelo: Random Forest Regressor  |  Parámetros: {g_rfr.best_params_}")
doc.add_paragraph(f"MAE = {mae:.2f} piezas  |  RMSE = {rmse:.2f}  |  R² = {r2:.4f}")
doc.add_picture("ml_regresion.png", width=Inches(6.2))

# ── Sección 6: Comparativa final ─────────────────────────────────────────────
doc.add_page_break()
doc.add_heading("6. Resumen Comparativo de Modelos", level=1)
df_to_word_table(doc, df_comp)

# ── Sección 7: Recomendaciones ───────────────────────────────────────────────
doc.add_page_break()
doc.add_heading("7. Recomendaciones de Mantenimiento Preventivo", level=1)
doc.add_paragraph("Con base en el análisis Weibull, se recomiendan los siguientes "
                  "intervalos de cambio preventivo (al 90% de confiabilidad — Vida B10):")
for _, row in df_weibull_refac.sort_values("b10_km").iterrows():
    doc.add_paragraph(
        f"• {row['nombre']}: cambio preventivo cada {row['b10_km']:,.0f} KM  "
        f"(MTTF={row['mttf']:,.0f} KM  |  β={row['beta']:.2f} → {row['tipo_fallo']})",
        style="List Bullet"
    )

doc.save("informe_refacciones_kinglong.docx")
print("  Informe guardado: informe_refacciones_kinglong.docx")
print("\n" + "=" * 65)
print("  PROCESO COMPLETADO")
print("=" * 65)
