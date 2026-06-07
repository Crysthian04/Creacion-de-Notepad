"""
Sistema Predictivo de Refacciones — Línea de Producción de Panadería Industrial
════════════════════════════════════════════════════════════════════════════════
Fases 4 y 5 del Plan de Trabajo de 16 Semanas
Metodología: SAE JA1011 · ISO 14224 · RCM · Weibull · Machine Learning

Módulos:
  1.  Datos de máquinas, refacciones e historial (reemplazar con datos reales de Oracle)
  2.  Análisis de Criticidad SAE JA1011 / ISO 14224
  3.  Análisis ABC del inventario
  4.  Cálculo de Mínimos, Máximos y Punto de Reorden
  5.  Análisis Estadístico Avanzado
  6.  Análisis de Weibull (refacciones y máquinas)
  7.  Modelos de Machine Learning
  8.  Exportación completa a Word
"""

# ── Instalación (descomentar en Colab / primer uso) ──────────────────────────
# !pip install python-docx imbalanced-learn scipy

import io
import warnings
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from scipy.stats import weibull_min, kstest, shapiro, kruskal
from imblearn.over_sampling import SMOTE
from sklearn.model_selection import train_test_split, GridSearchCV, cross_val_score
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import (RandomForestClassifier, RandomForestRegressor,
                              GradientBoostingClassifier)
from sklearn.metrics import (accuracy_score, classification_report,
                              confusion_matrix, mean_absolute_error,
                              mean_squared_error, r2_score, roc_auc_score)
from sklearn.preprocessing import LabelEncoder, StandardScaler
from docx import Document
from docx.shared import Inches, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH

warnings.filterwarnings("ignore")
np.random.seed(42)


# ════════════════════════════════════════════════════════════════════════════
# SECCIÓN 0 — CONFIGURACIÓN DE LA PLANTA
# ════════════════════════════════════════════════════════════════════════════

# Máquinas de la línea de producción de panadería
MAQUINAS = {
    "Amasadora-01":          {"linea": "Producción A", "turno_horas": 16, "pm_intervalo_h": 720},
    "Amasadora-02":          {"linea": "Producción A", "turno_horas": 16, "pm_intervalo_h": 720},
    "Divisora-01":           {"linea": "Producción A", "turno_horas": 16, "pm_intervalo_h": 500},
    "Boleadora-01":          {"linea": "Producción A", "turno_horas": 16, "pm_intervalo_h": 500},
    "Cámara Fermentación-01":{"linea": "Producción A", "turno_horas": 24, "pm_intervalo_h": 1000},
    "Cámara Fermentación-02":{"linea": "Producción B", "turno_horas": 24, "pm_intervalo_h": 1000},
    "Horno Rotativo-01":     {"linea": "Producción A", "turno_horas": 20, "pm_intervalo_h": 600},
    "Horno Rotativo-02":     {"linea": "Producción B", "turno_horas": 20, "pm_intervalo_h": 600},
    "Laminadora-01":         {"linea": "Producción B", "turno_horas": 16, "pm_intervalo_h": 800},
    "Cortadora-01":          {"linea": "Producción B", "turno_horas": 16, "pm_intervalo_h": 400},
    "Empacadora-01":         {"linea": "Producción A", "turno_horas": 16, "pm_intervalo_h": 350},
    "Empacadora-02":         {"linea": "Producción B", "turno_horas": 16, "pm_intervalo_h": 350},
    "Compresor-01":          {"linea": "Servicios",    "turno_horas": 24, "pm_intervalo_h": 500},
    "Banda Transportadora-01":{"linea": "Producción A","turno_horas": 16, "pm_intervalo_h": 600},
    "Banda Transportadora-02":{"linea": "Producción B","turno_horas": 16, "pm_intervalo_h": 600},
}

# Tipos de refacciones con vida útil esperada en horas
REFACCIONES_CONFIG = {
    "Rodamiento SKF 6205":        {"vida_h": 4000,  "costo": 45.00,  "categoria": "Mecánica"},
    "Rodamiento SKF 6308":        {"vida_h": 5000,  "costo": 78.00,  "categoria": "Mecánica"},
    "Correa en V A-62":           {"vida_h": 2000,  "costo": 22.00,  "categoria": "Transmisión"},
    "Correa en V B-75":           {"vida_h": 2500,  "costo": 35.00,  "categoria": "Transmisión"},
    "Sello Mecánico 25mm":        {"vida_h": 3000,  "costo": 120.00, "categoria": "Neumática"},
    "Empaque Silicón 10mm":       {"vida_h": 1500,  "costo": 8.50,   "categoria": "Sellado"},
    "Resistencia Horno 2500W":    {"vida_h": 6000,  "costo": 280.00, "categoria": "Eléctrica"},
    "Filtro de Aceite HF6553":    {"vida_h": 500,   "costo": 18.00,  "categoria": "Lubricación"},
    "Filtro de Aire AF25708":     {"vida_h": 1000,  "costo": 32.00,  "categoria": "Lubricación"},
    "Cuchilla Acero Inox 300mm":  {"vida_h": 800,   "costo": 65.00,  "categoria": "Corte"},
    "Sensor Temperatura PT100":   {"vida_h": 8000,  "costo": 95.00,  "categoria": "Instrumentación"},
    "Contactor Siemens 3RT2025":  {"vida_h": 10000, "costo": 145.00, "categoria": "Eléctrica"},
    "Banda Transportadora PVC":   {"vida_h": 3500,  "costo": 380.00, "categoria": "Transmisión"},
    "Rasqueta Teflón 200mm":      {"vida_h": 600,   "costo": 12.00,  "categoria": "Limpieza"},
    "Válvula Solenoide 1/2\"":    {"vida_h": 5000,  "costo": 55.00,  "categoria": "Neumática"},
}

PROVEEDORES = {
    "SKF México":       {"lead_time_dias": 5,  "confiabilidad": 0.95},
    "Grainger":         {"lead_time_dias": 3,  "confiabilidad": 0.98},
    "Fastenal":         {"lead_time_dias": 2,  "confiabilidad": 0.97},
    "Distribuidor Local":{"lead_time_dias": 1, "confiabilidad": 0.85},
    "Import Directo":   {"lead_time_dias": 21, "confiabilidad": 0.80},
}


# ════════════════════════════════════════════════════════════════════════════
# SECCIÓN 1 — GENERACIÓN DE DATOS
# ════════════════════════════════════════════════════════════════════════════
#
# ── DATOS REALES: reemplaza este bloque con tus exportaciones de Oracle ──────
#
#   df_inventario = pd.read_excel("Oracle_Inventario.xlsx")
#   df_consumos   = pd.read_excel("Oracle_Consumos_Historicos.xlsx")
#   df_fallas     = pd.read_excel("Historial_Fallas.xlsx")
#   df_ordenes    = pd.read_excel("Ordenes_de_Trabajo.xlsx")
#
#   Columnas esperadas en df_fallas:
#     maquina | componente | fecha_falla | horas_al_fallo | tiempo_reparacion_h
#     causa_raiz | tipo_mantenimiento | costo_paro
#
# ─────────────────────────────────────────────────────────────────────────────

print("=" * 68)
print("  SISTEMA PREDICTIVO DE REFACCIONES — PANADERÍA INDUSTRIAL")
print("=" * 68)

maquinas_list   = list(MAQUINAS.keys())
refacciones_list = list(REFACCIONES_CONFIG.keys())
N_INVENTARIO     = len(refacciones_list)
N_CONSUMOS       = 1200
N_FALLAS         = 600
N_OT             = 500

# ── 1a. Inventario actual (como en Oracle) ────────────────────────────────────
proveedor_asignado = np.random.choice(list(PROVEEDORES.keys()), N_INVENTARIO)
df_inventario = pd.DataFrame({
    "codigo_parte":    [f"PT-{str(i).zfill(4)}" for i in range(1, N_INVENTARIO + 1)],
    "descripcion":     refacciones_list,
    "categoria":       [REFACCIONES_CONFIG[r]["categoria"] for r in refacciones_list],
    "stock_actual":    np.random.randint(0, 30, N_INVENTARIO),
    "costo_unitario":  [REFACCIONES_CONFIG[r]["costo"] for r in refacciones_list],
    "proveedor":       proveedor_asignado,
    "lead_time_dias":  [PROVEEDORES[p]["lead_time_dias"] for p in proveedor_asignado],
    "vida_util_horas": [REFACCIONES_CONFIG[r]["vida_h"] for r in refacciones_list],
    "consumo_mensual_prom": np.random.uniform(0.5, 8, N_INVENTARIO).round(1),
    "consumo_mensual_std":  np.random.uniform(0.1, 2, N_INVENTARIO).round(2),
    "maquina_asociada": np.random.choice(maquinas_list, N_INVENTARIO),
})
df_inventario["valor_inventario"] = (df_inventario["stock_actual"] *
                                      df_inventario["costo_unitario"]).round(2)

# ── 1b. Historial de consumos mensuales (8 meses) ─────────────────────────────
meses = pd.date_range("2024-09-01", periods=8, freq="MS")
consumo_rows = []
for _, row in df_inventario.iterrows():
    for mes in meses:
        cant = max(0, np.random.normal(row["consumo_mensual_prom"],
                                        row["consumo_mensual_std"]))
        consumo_rows.append({
            "codigo_parte": row["codigo_parte"],
            "descripcion":  row["descripcion"],
            "mes":          mes,
            "cantidad_consumida": round(cant, 0),
            "costo_consumo": round(cant * row["costo_unitario"], 2),
        })
df_consumos = pd.DataFrame(consumo_rows)

# ── 1c. Historial de fallas (Oracle / OT manuales) ────────────────────────────
df_fallas = pd.DataFrame({
    "id_falla":          range(1, N_FALLAS + 1),
    "maquina":           np.random.choice(maquinas_list, N_FALLAS),
    "componente":        np.random.choice(refacciones_list, N_FALLAS),
    "fecha_falla":       pd.date_range("2023-01-01", periods=N_FALLAS, freq="10h"),
    "horas_al_fallo":    np.abs(np.array([
        np.random.normal(REFACCIONES_CONFIG[r]["vida_h"] * np.random.uniform(0.5, 1.2),
                         REFACCIONES_CONFIG[r]["vida_h"] * 0.20)
        for r in np.random.choice(refacciones_list, N_FALLAS)
    ])).clip(50),
    "tiempo_reparacion_h": np.abs(np.random.normal(4, 2, N_FALLAS)).clip(0.5),
    "tipo_mantenimiento":  np.random.choice(
        ["Correctivo", "Preventivo", "Predictivo"], N_FALLAS, p=[0.55, 0.35, 0.10]),
    "causa_raiz":          np.random.choice(
        ["Desgaste normal", "Falta de lubricación", "Sobrecarga",
         "Error operativo", "Fin de vida útil", "Falla de proveedor"], N_FALLAS),
    "costo_paro_hrs":      np.random.uniform(500, 8000, N_FALLAS).round(2),
})
df_fallas["costo_total_evento"] = (df_fallas["costo_paro_hrs"] *
                                    df_fallas["tiempo_reparacion_h"]).round(2)

print(f"\n  Máquinas en planta:      {len(MAQUINAS)}")
print(f"  Tipos de refacciones:    {len(REFACCIONES_CONFIG)}")
print(f"  Registros de consumo:    {len(df_consumos)}")
print(f"  Eventos de falla:        {len(df_fallas)}")


# ════════════════════════════════════════════════════════════════════════════
# SECCIÓN 2 — CRITICIDAD SAE JA1011 / ISO 14224
# ════════════════════════════════════════════════════════════════════════════

print("\n" + "=" * 68)
print("  ANÁLISIS DE CRITICIDAD — SAE JA1011 / ISO 14224 / RCM")
print("=" * 68)

# Matriz de criticidad: Consecuencia × Probabilidad × Detectabilidad
# Escala 1-5 para cada criterio (basado en SAE JA1011 / ISO 14224)
criterios = {
    # maquina: [impacto_produccion, impacto_seguridad, impacto_calidad,
    #           prob_falla, detectabilidad_inversa]
    # Detectabilidad inversa: 5=muy difícil detectar, 1=fácil detectar
    "Amasadora-01":           [5, 3, 5, 3, 2],
    "Amasadora-02":           [5, 3, 5, 3, 2],
    "Divisora-01":            [4, 2, 4, 3, 3],
    "Boleadora-01":           [4, 2, 3, 3, 3],
    "Cámara Fermentación-01": [5, 2, 5, 2, 4],
    "Cámara Fermentación-02": [5, 2, 5, 2, 4],
    "Horno Rotativo-01":      [5, 5, 5, 2, 2],
    "Horno Rotativo-02":      [5, 5, 5, 2, 2],
    "Laminadora-01":          [3, 2, 4, 4, 3],
    "Cortadora-01":           [3, 4, 3, 4, 2],
    "Empacadora-01":          [3, 1, 3, 4, 3],
    "Empacadora-02":          [3, 1, 3, 4, 3],
    "Compresor-01":           [4, 3, 2, 2, 4],
    "Banda Transportadora-01":[3, 2, 2, 3, 3],
    "Banda Transportadora-02":[3, 2, 2, 3, 3],
}

df_criticidad = pd.DataFrame(criterios,
    index=["impacto_produccion", "impacto_seguridad", "impacto_calidad",
           "prob_falla", "detectabilidad_inv"]).T.reset_index()
df_criticidad.rename(columns={"index": "maquina"}, inplace=True)

# NPR (Número de Prioridad de Riesgo) — metodología RCM/FMEA
df_criticidad["NPR"] = (df_criticidad["impacto_produccion"] *
                         df_criticidad["prob_falla"] *
                         df_criticidad["detectabilidad_inv"])

df_criticidad["criticidad_SAE"] = pd.cut(
    df_criticidad["NPR"],
    bins=[0, 20, 40, 100],
    labels=["MENOR", "IMPORTANTE", "CRÍTICO"]
)

# Puntaje de consecuencia compuesto (ISO 14224)
df_criticidad["consecuencia_ISO"] = (
    df_criticidad["impacto_produccion"] * 0.40 +
    df_criticidad["impacto_seguridad"]  * 0.35 +
    df_criticidad["impacto_calidad"]    * 0.25
).round(2)

print("\nClasificación de criticidad (SAE JA1011 / ISO 14224):")
print(df_criticidad[["maquina", "NPR", "criticidad_SAE", "consecuencia_ISO",
                      "impacto_seguridad"]].sort_values("NPR", ascending=False).to_string(index=False))


# ════════════════════════════════════════════════════════════════════════════
# SECCIÓN 3 — ANÁLISIS ABC DEL INVENTARIO
# ════════════════════════════════════════════════════════════════════════════

print("\n" + "=" * 68)
print("  ANÁLISIS ABC DEL INVENTARIO")
print("=" * 68)

consumo_total = (df_consumos.groupby("codigo_parte")["costo_consumo"]
                 .sum().reset_index().rename(columns={"costo_consumo": "costo_consumo_total"}))

df_abc = df_inventario.merge(consumo_total, on="codigo_parte", how="left").fillna(0)
df_abc = df_abc.sort_values("costo_consumo_total", ascending=False)
df_abc["costo_acumulado_pct"] = (df_abc["costo_consumo_total"].cumsum() /
                                  df_abc["costo_consumo_total"].sum() * 100)
df_abc["clase_ABC"] = pd.cut(
    df_abc["costo_acumulado_pct"],
    bins=[0, 80, 95, 100],
    labels=["A", "B", "C"],
    include_lowest=True
)

# Cruce criticidad + ABC (las A+CRÍTICO son las de máxima prioridad)
df_inventario = df_inventario.merge(
    df_abc[["codigo_parte", "clase_ABC", "costo_consumo_total"]], on="codigo_parte", how="left")
df_inventario = df_inventario.merge(
    df_criticidad[["maquina", "criticidad_SAE", "NPR"]].rename(
        columns={"maquina": "maquina_asociada"}), on="maquina_asociada", how="left")
df_inventario["prioridad_maxima"] = (
    (df_inventario["clase_ABC"] == "A") &
    (df_inventario["criticidad_SAE"] == "CRÍTICO")
).map({True: "★ A+CRÍTICO", False: ""})

resumen_abc = df_abc.groupby("clase_ABC").agg(
    partes=("codigo_parte", "count"),
    costo_total=("costo_consumo_total", "sum"),
    pct_partes=("codigo_parte", lambda x: f"{len(x)/len(df_abc)*100:.1f}%"),
).reset_index()
print("\nResumen Análisis ABC:")
print(resumen_abc.to_string(index=False))


# ════════════════════════════════════════════════════════════════════════════
# SECCIÓN 4 — MÍNIMOS, MÁXIMOS Y PUNTO DE REORDEN
# ════════════════════════════════════════════════════════════════════════════

print("\n" + "=" * 68)
print("  CÁLCULO DE MÍNIMOS, MÁXIMOS Y PUNTO DE REORDEN")
print("=" * 68)

# Nivel de servicio según criticidad SAE
nivel_servicio = {"CRÍTICO": 1.65, "IMPORTANTE": 1.28, "MENOR": 1.04}  # Z-score

df_inventario["z_score"] = df_inventario["criticidad_SAE"].map(nivel_servicio).fillna(1.28)
df_inventario["lead_time_meses"] = df_inventario["lead_time_dias"] / 30

# Stock de seguridad = Z × σ_demanda × √(Lead Time en meses)
df_inventario["safety_stock"] = (
    df_inventario["z_score"] *
    df_inventario["consumo_mensual_std"] *
    np.sqrt(df_inventario["lead_time_meses"])
).round(1)

# Stock mínimo = (Consumo promedio × Lead Time) + Safety Stock
df_inventario["stock_minimo"] = (
    df_inventario["consumo_mensual_prom"] * df_inventario["lead_time_meses"] +
    df_inventario["safety_stock"]
).round(1)

# Stock máximo = Mínimo + consumo de 2 meses (ciclo de compra mensual)
df_inventario["stock_maximo"] = (
    df_inventario["stock_minimo"] + df_inventario["consumo_mensual_prom"] * 2
).round(1)

# Punto de reorden = stock mínimo
df_inventario["punto_reorden"] = df_inventario["stock_minimo"]

# Alerta de reorden
df_inventario["necesita_reorden"] = (
    df_inventario["stock_actual"] <= df_inventario["punto_reorden"]
).astype(int)
df_inventario["semaforo"] = df_inventario["stock_actual"].apply(
    lambda x: "🔴 Urgente" if x == 0 else ("🟡 Bajo" if x <= 3 else "🟢 OK"))

alertas = df_inventario[df_inventario["necesita_reorden"] == 1]
print(f"\n  Refacciones que necesitan reorden: {len(alertas)} de {len(df_inventario)}")
print(df_inventario[["descripcion", "stock_actual", "stock_minimo",
                       "punto_reorden", "semaforo", "clase_ABC",
                       "criticidad_SAE"]].to_string(index=False))


# ════════════════════════════════════════════════════════════════════════════
# SECCIÓN 5 — ANÁLISIS ESTADÍSTICO AVANZADO
# ════════════════════════════════════════════════════════════════════════════

print("\n" + "=" * 68)
print("  ANÁLISIS ESTADÍSTICO AVANZADO")
print("=" * 68)

# Variables de análisis
consumo_pivot = (df_consumos.groupby(["codigo_parte", "mes"])["cantidad_consumida"]
                 .sum().reset_index())
consumo_pivot["mes_num"] = consumo_pivot.groupby("codigo_parte").cumcount() + 1

vars_stat = df_inventario[["consumo_mensual_prom", "consumo_mensual_std",
                             "costo_unitario", "vida_util_horas", "stock_actual"]].copy()

desc = vars_stat.describe().T
desc["skewness"] = vars_stat.skew()
desc["kurtosis"] = vars_stat.kurt()
desc["CV_%"]     = (vars_stat.std() / vars_stat.mean() * 100).round(1)
print("\nEstadísticas descriptivas:")
print(desc.round(3))

# Shapiro-Wilk
print("\nNormalidad (Shapiro-Wilk):")
for col in vars_stat.columns:
    if len(vars_stat[col].dropna()) >= 3:
        stat, p = shapiro(vars_stat[col].dropna())
        print(f"  {col:<28} W={stat:.4f}  p={p:.4f}  "
              f"{'Normal' if p > 0.05 else 'No normal'}")

# Kruskal-Wallis: diferencia de consumo entre categorías
grupos_cat = [g["consumo_mensual_prom"].values
              for _, g in df_inventario.groupby("categoria")
              if len(g) >= 2]
if len(grupos_cat) > 1:
    h, p_kw = kruskal(*grupos_cat)
    print(f"\nKruskal-Wallis consumo por categoría: H={h:.3f}  p={p_kw:.4f}")

# Correlación Spearman
corr_sp = vars_stat.corr(method="spearman")

# Costo total de paros por tipo de causa
costo_causa = (df_fallas.groupby("causa_raiz")["costo_total_evento"]
               .agg(["sum", "count", "mean"]).round(2).sort_values("sum", ascending=False))
print("\nCosto total de paros por causa raíz:")
print(costo_causa)

# ── Figuras de estadística ────────────────────────────────────────────────────
fig, axes = plt.subplots(2, 3, figsize=(16, 9))
fig.suptitle("Análisis Estadístico Avanzado — Almacén de Refacciones Panadería",
             fontsize=13, fontweight="bold")

# Distribución de consumo mensual
ax = axes[0, 0]
df_inventario["consumo_mensual_prom"].hist(bins=8, ax=ax, color="steelblue",
                                            edgecolor="white", density=True)
df_inventario["consumo_mensual_prom"].plot(kind="kde", ax=ax, color="red", lw=2)
ax.set_title("Distribución Consumo Mensual Promedio")
ax.set_xlabel("Unidades/mes")

# Boxplot consumo por categoría
ax = axes[0, 1]
cats = df_inventario["categoria"].unique()
data_box = [df_inventario[df_inventario["categoria"] == c]["consumo_mensual_prom"].values
            for c in cats]
ax.boxplot(data_box, labels=[c[:8] for c in cats], patch_artist=True)
ax.set_title("Consumo por Categoría de Refacción")
ax.set_ylabel("Unidades/mes")
ax.tick_params(axis="x", rotation=30, labelsize=7)

# Correlación Spearman
ax = axes[0, 2]
sns.heatmap(corr_sp, annot=True, cmap="coolwarm", fmt=".2f", ax=ax, annot_kws={"size": 7})
ax.set_title("Correlación Spearman")
ax.tick_params(labelsize=7)

# NPR por máquina (criticidad)
ax = axes[1, 0]
df_crit_sort = df_criticidad.sort_values("NPR", ascending=True)
colors = ["#e85d3a" if c == "CRÍTICO" else "#f0c040" if c == "IMPORTANTE" else "#3ae87a"
          for c in df_crit_sort["criticidad_SAE"]]
ax.barh(df_crit_sort["maquina"].str[:20], df_crit_sort["NPR"], color=colors)
ax.set_title("NPR por Máquina (SAE JA1011)")
ax.set_xlabel("NPR = Impacto × Prob × Detectabilidad")
ax.tick_params(axis="y", labelsize=7)
# Leyenda manual
from matplotlib.patches import Patch
ax.legend(handles=[Patch(color="#e85d3a", label="CRÍTICO"),
                   Patch(color="#f0c040", label="IMPORTANTE"),
                   Patch(color="#3ae87a", label="MENOR")], fontsize=7)

# Costo de paros por causa
ax = axes[1, 1]
costo_causa["sum"].sort_values().plot(kind="barh", ax=ax, color="salmon")
ax.set_title("Costo Total de Paros por Causa Raíz")
ax.set_xlabel("Costo Total ($)")
ax.tick_params(axis="y", labelsize=7)

# Pareto ABC
ax = axes[1, 2]
df_abc_sorted = df_abc.sort_values("costo_consumo_total", ascending=False).reset_index(drop=True)
colores_abc = df_abc_sorted["clase_ABC"].map({"A": "#e85d3a", "B": "#f0c040", "C": "#3ae87a"})
ax.bar(df_abc_sorted.index, df_abc_sorted["costo_consumo_total"],
       color=colores_abc, width=0.8)
ax2b = ax.twinx()
ax2b.plot(df_abc_sorted.index, df_abc_sorted["costo_acumulado_pct"], "k-", lw=2)
ax2b.axhline(80, color="red", ls="--", lw=1)
ax2b.set_ylabel("% Acumulado")
ax.set_title("Curva de Pareto — Análisis ABC")
ax.set_xlabel("Refacciones (ordenadas por costo)")
ax.set_ylabel("Costo de Consumo ($)")
ax.tick_params(axis="x", labelbottom=False)

plt.tight_layout()
plt.savefig("estadistica_avanzada_panaderia.png", dpi=150)
plt.close()
print("\n  Gráfico estadístico guardado.")


# ════════════════════════════════════════════════════════════════════════════
# SECCIÓN 6 — ANÁLISIS DE WEIBULL
# ════════════════════════════════════════════════════════════════════════════

print("\n" + "=" * 68)
print("  ANÁLISIS DE WEIBULL — REFACCIONES Y MÁQUINAS")
print("=" * 68)

def ajustar_weibull(tiempos: np.ndarray, nombre: str = "") -> dict | None:
    """Ajusta Weibull de 2 parámetros y retorna métricas de confiabilidad."""
    tiempos = np.array(tiempos)[np.array(tiempos) > 0]
    if len(tiempos) < 5:
        return None
    beta, _, eta = weibull_min.fit(tiempos, floc=0)
    mttf = eta * stats.gamma(1 + 1 / beta)
    b10  = eta * (-np.log(0.90)) ** (1 / beta)
    b50  = eta * (-np.log(0.50)) ** (1 / beta)
    _, p_ks = kstest(tiempos, "weibull_min", args=(beta, 0, eta))

    tipo = ("Mortalidad infantil (β<1) → revisar instalación/proveedor" if beta < 0.9
            else "Fallo aleatorio (β≈1) → fallo independiente del tiempo" if abs(beta - 1) < 0.2
            else "Desgaste/Envejecimiento (β>1) → mantenimiento preventivo ideal")

    print(f"  {nombre:<35} β={beta:.3f}  η={eta:>8.1f}h  "
          f"MTTF={mttf:>8.1f}h  B10={b10:>7.1f}h  {tipo[:30]}")
    return {"nombre": nombre, "beta": round(beta, 3), "eta": round(eta, 1),
            "mttf": round(mttf, 1), "b10_h": round(b10, 1), "b50_h": round(b50, 1),
            "ks_p": round(p_ks, 4), "ajuste": "Bueno" if p_ks > 0.05 else "Revisar",
            "tipo_fallo": tipo}

# ── 6a. Weibull por tipo de refacción ─────────────────────────────────────────
print("\nWeibull por componente (horas al fallo):")
res_weibull_refac = []
for comp, grp in df_fallas.groupby("componente"):
    r = ajustar_weibull(grp["horas_al_fallo"].values, comp[:35])
    if r:
        res_weibull_refac.append(r)
df_wb_refac = pd.DataFrame(res_weibull_refac)

# ── 6b. Weibull por máquina (MTBF operativo) ──────────────────────────────────
print("\nWeibull por máquina (horas entre fallas):")
res_weibull_maq = []
for maq, grp in df_fallas.sort_values("fecha_falla").groupby("maquina"):
    h = grp["horas_al_fallo"].values
    r = ajustar_weibull(h, maq[:35])
    if r:
        r["criticidad"] = str(df_criticidad[df_criticidad["maquina"] == maq]["criticidad_SAE"].values[0]
                              if maq in df_criticidad["maquina"].values else "N/D")
        res_weibull_maq.append(r)
df_wb_maq = pd.DataFrame(res_weibull_maq)

# ── 6c. Curvas de confiabilidad ───────────────────────────────────────────────
def plot_weibull_confiabilidad(df_w: pd.DataFrame, titulo: str, path: str,
                                col_color: str = None):
    n = min(len(df_w), 9)
    cols = 3
    rows = (n + 2) // 3
    fig, axes = plt.subplots(rows * 2, cols, figsize=(5 * cols, 4 * rows * 2))
    fig.suptitle(titulo, fontsize=12, fontweight="bold")
    axes = np.array(axes).reshape(rows * 2, cols)

    for idx in range(n):
        row_d = df_w.iloc[idx]
        beta, eta = row_d["beta"], row_d["eta"]
        t = np.linspace(0.01, eta * 2.5, 400)
        R = np.exp(-(t / eta) ** beta)
        h = (beta / eta) * (t / eta) ** (beta - 1)
        r, c = divmod(idx, cols)

        ax1 = axes[r * 2, c]
        ax1.plot(t, R, "steelblue", lw=2)
        ax1.axhline(0.90, color="green",  ls="--", lw=1, label=f"B10={row_d['b10_h']:.0f}h")
        ax1.axhline(0.50, color="orange", ls="--", lw=1, label=f"B50={row_d['b50_h']:.0f}h")
        ax1.axvline(row_d["b10_h"], color="green",  ls=":", lw=1)
        ax1.axvline(row_d["b50_h"], color="orange", ls=":", lw=1)
        ax1.set_title(f"{row_d['nombre'][:28]}\nβ={beta:.2f}  η={eta:.0f}h  "
                      f"MTTF={row_d['mttf']:.0f}h", fontsize=7)
        ax1.set_ylabel("R(t)")
        ax1.set_xlabel("Horas")
        ax1.legend(fontsize=6)
        ax1.set_ylim(0, 1.05)
        ax1.grid(alpha=0.3)

        ax2 = axes[r * 2 + 1, c]
        ax2.plot(t, h, "crimson", lw=2)
        ax2.set_title(f"h(t) — {row_d['tipo_fallo'][:35]}", fontsize=7)
        ax2.set_ylabel("Tasa de fallo h(t)")
        ax2.set_xlabel("Horas")
        ax2.grid(alpha=0.3)

    for extra in range(n, rows * cols):
        r, c = divmod(extra, cols)
        axes[r * 2, c].set_visible(False)
        axes[r * 2 + 1, c].set_visible(False)

    plt.tight_layout()
    plt.savefig(path, dpi=150)
    plt.close()
    print(f"  Gráfico guardado: {path}")

plot_weibull_confiabilidad(df_wb_refac, "Weibull — Componentes/Refacciones",
                           "weibull_refacciones.png")
plot_weibull_confiabilidad(df_wb_maq, "Weibull — Máquinas de Producción",
                           "weibull_maquinas.png")

# Comparativa MTTF y B10
fig, axes = plt.subplots(1, 2, figsize=(14, 5))
fig.suptitle("Comparativa Weibull — Máquinas y Refacciones", fontweight="bold")

df_wb_maq.sort_values("mttf").plot(kind="barh", x="nombre", y="mttf",
                                    ax=axes[0], color="steelblue", legend=False)
axes[0].set_title("MTTF por Máquina (Horas promedio entre fallas)")
axes[0].set_xlabel("MTTF (Horas)")
axes[0].tick_params(axis="y", labelsize=7)

df_wb_refac.sort_values("b10_h").plot(kind="barh", x="nombre", y="b10_h",
                                       ax=axes[1], color="salmon", legend=False)
axes[1].set_title("Vida B10 por Componente (90% confiabilidad)")
axes[1].set_xlabel("B10 (Horas)")
axes[1].tick_params(axis="y", labelsize=7)

plt.tight_layout()
plt.savefig("weibull_comparativa.png", dpi=150)
plt.close()


# ════════════════════════════════════════════════════════════════════════════
# SECCIÓN 7 — MACHINE LEARNING
# ════════════════════════════════════════════════════════════════════════════

print("\n" + "=" * 68)
print("  MODELOS DE MACHINE LEARNING")
print("=" * 68)

# ── 7a. Dataset maestro para ML ───────────────────────────────────────────────
# Agregados de fallas por refacción
agg_fallas = df_fallas.groupby("componente").agg(
    total_fallas=("id_falla", "count"),
    horas_promedio_fallo=("horas_al_fallo", "mean"),
    horas_std_fallo=("horas_al_fallo", "std"),
    tiempo_rep_prom=("tiempo_reparacion_h", "mean"),
    costo_paro_total=("costo_total_evento", "sum"),
    pct_correctivo=("tipo_mantenimiento", lambda x: (x == "Correctivo").mean()),
).reset_index().rename(columns={"componente": "descripcion"}).fillna(0)

df_ml = (df_inventario
         .merge(agg_fallas, on="descripcion", how="left")
         .fillna(0))

# Codificación de variables categóricas
le_cat    = LabelEncoder()
le_crit   = LabelEncoder()
le_abc    = LabelEncoder()
le_maq    = LabelEncoder()
df_ml["categoria_enc"]   = le_cat.fit_transform(df_ml["categoria"].fillna("Desconocido"))
df_ml["criticidad_enc"]  = le_crit.fit_transform(df_ml["criticidad_SAE"].astype(str))
df_ml["abc_enc"]         = le_abc.fit_transform(df_ml["clase_ABC"].astype(str))
df_ml["maquina_enc"]     = le_maq.fit_transform(df_ml["maquina_asociada"].fillna("Sin máquina"))

FEATURES = [
    "consumo_mensual_prom", "consumo_mensual_std", "costo_unitario",
    "vida_util_horas", "stock_actual", "lead_time_dias",
    "safety_stock", "stock_minimo", "NPR",
    "total_fallas", "horas_promedio_fallo", "horas_std_fallo",
    "tiempo_rep_prom", "costo_paro_total", "pct_correctivo",
    "categoria_enc", "criticidad_enc", "abc_enc", "maquina_enc",
]

# Targets
df_ml["fallo_inminente"]  = (
    (df_ml["stock_actual"] <= df_ml["stock_minimo"]) &
    (df_ml["horas_promedio_fallo"] < df_ml["vida_util_horas"] * 0.8)
).astype(int)

df_ml["es_prioridad_alta"] = (
    (df_ml["clase_ABC"] == "A") &
    (df_ml["criticidad_SAE"] == "CRÍTICO") &
    (df_ml["pct_correctivo"] > 0.5)
).astype(int)

X = df_ml[FEATURES].fillna(0)
y_fallo    = df_ml["fallo_inminente"]
y_prioridad = df_ml["es_prioridad_alta"]

PARAM_TREE = {"max_depth": [3, 5, None], "min_samples_split": [2, 5], "min_samples_leaf": [1, 2]}
PARAM_RF   = {"n_estimators": [100, 200], "max_depth": [5, 10, None], "min_samples_split": [2, 5]}
PARAM_GB   = {"n_estimators": [100, 200], "max_depth": [3, 5], "learning_rate": [0.05, 0.1]}

def entrenar_clasificacion(nombre, X, y):
    print(f"\n  ── {nombre} ──")
    if len(y.unique()) < 2:
        print("    Sin varianza suficiente en target, omitiendo.")
        return None
    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.25,
                                                random_state=42, stratify=y)
    if y_tr.mean() < 0.3 or y_tr.mean() > 0.7:
        try:
            sm = SMOTE(random_state=42, k_neighbors=min(3, y_tr.sum() - 1))
            X_tr, y_tr = sm.fit_resample(X_tr, y_tr)
        except Exception:
            pass

    modelos = {
        "Árbol de Decisión": GridSearchCV(DecisionTreeClassifier(random_state=42),
                                          PARAM_TREE, cv=3, scoring="f1", n_jobs=-1),
        "Random Forest":     GridSearchCV(RandomForestClassifier(random_state=42),
                                          PARAM_RF, cv=3, scoring="f1", n_jobs=-1),
        "Gradient Boosting": GridSearchCV(GradientBoostingClassifier(random_state=42),
                                          PARAM_GB, cv=3, scoring="f1", n_jobs=-1),
    }
    res = {"nombre": nombre, "modelos": {}}
    for nom, g in modelos.items():
        g.fit(X_tr, y_tr)
        m = g.best_estimator_
        y_pred = m.predict(X_te)
        acc = accuracy_score(y_te, y_pred)
        rep = classification_report(y_te, y_pred, zero_division=0)
        cm  = confusion_matrix(y_te, y_pred)
        try:
            auc = roc_auc_score(y_te, m.predict_proba(X_te)[:, 1])
        except Exception:
            auc = np.nan
        f1_cv = cross_val_score(m, X_te, y_te, cv=3, scoring="f1",
                                error_score=0).mean()
        print(f"    {nom:<22} Acc={acc:.3f}  F1={f1_cv:.3f}  AUC={auc:.3f}")
        res["modelos"][nom] = {"params": g.best_params_, "acc": acc, "f1": f1_cv,
                               "auc": auc, "rep": rep, "cm": cm, "modelo": m,
                               "y_te": y_te, "y_pred": y_pred}
    mejor = max(res["modelos"], key=lambda k: res["modelos"][k]["f1"])
    res["mejor"] = mejor
    return res

res_fallo    = entrenar_clasificacion("Fallo Inminente de Refacción", X, y_fallo)
res_prioridad = entrenar_clasificacion("Refacción Prioridad Alta (A+CRÍTICO)", X, y_prioridad)

# ── Regresión: Demanda próximo mes ─────────────────────────────────────────────
print("\n  ── Regresión: Demanda de Refacciones Próximo Mes ──")
consumo_prox = (df_consumos[df_consumos["mes"] == df_consumos["mes"].max()]
                .groupby("codigo_parte")["cantidad_consumida"].sum().reset_index()
                .rename(columns={"cantidad_consumida": "demanda_real_mes"}))
df_reg = df_ml.merge(consumo_prox, on="codigo_parte", how="left").fillna(0)

X_reg = StandardScaler().fit_transform(df_reg[FEATURES].fillna(0))
y_reg = df_reg["demanda_real_mes"]
X_tr_r, X_te_r, y_tr_r, y_te_r = train_test_split(X_reg, y_reg, test_size=0.25, random_state=42)

g_rfr = GridSearchCV(RandomForestRegressor(random_state=42),
                     {"n_estimators": [100, 200], "max_depth": [5, 10, None]},
                     cv=3, scoring="neg_mean_absolute_error", n_jobs=-1)
g_rfr.fit(X_tr_r, y_tr_r)
y_pred_reg = g_rfr.best_estimator_.predict(X_te_r)
mae  = mean_absolute_error(y_te_r, y_pred_reg)
rmse = np.sqrt(mean_squared_error(y_te_r, y_pred_reg))
r2   = r2_score(y_te_r, y_pred_reg)
print(f"    Random Forest Reg.  MAE={mae:.2f}  RMSE={rmse:.2f}  R²={r2:.4f}")

feat_imp = pd.Series(g_rfr.best_estimator_.feature_importances_,
                     index=FEATURES).sort_values(ascending=False)

# ── Gráficos ML ───────────────────────────────────────────────────────────────
def guardar_cms(res, path):
    if not res:
        return
    mods = list(res["modelos"].keys())
    fig, axes = plt.subplots(1, len(mods), figsize=(5 * len(mods), 4))
    fig.suptitle(f"Matrices de Confusión — {res['nombre']}", fontweight="bold")
    if len(mods) == 1:
        axes = [axes]
    for ax, nom in zip(axes, mods):
        d = res["modelos"][nom]
        sns.heatmap(d["cm"], annot=True, fmt="d", cmap="Blues", ax=ax,
                    xticklabels=["No", "Sí"], yticklabels=["No", "Sí"])
        ax.set_title(f"{nom}\nAcc={d['acc']:.3f}  F1={d['f1']:.3f}")
        ax.set_xlabel("Predicción")
        ax.set_ylabel("Real")
    plt.tight_layout()
    plt.savefig(path, dpi=150)
    plt.close()

if res_fallo:
    guardar_cms(res_fallo,     "cm_fallo_inminente.png")
if res_prioridad:
    guardar_cms(res_prioridad, "cm_prioridad_alta.png")

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 4))
ax1.scatter(y_te_r, y_pred_reg, alpha=0.6, color="steelblue")
mn, mx = min(y_te_r.min(), y_pred_reg.min()), max(y_te_r.max(), y_pred_reg.max())
ax1.plot([mn, mx], [mn, mx], "r--")
ax1.set_xlabel("Demanda Real")
ax1.set_ylabel("Demanda Predicha")
ax1.set_title(f"Demanda Próximo Mes  MAE={mae:.2f}  R²={r2:.4f}")

feat_imp.head(10).plot(kind="bar", ax=ax2, color="steelblue")
ax2.set_title("Top 10 Variables Más Importantes")
ax2.set_ylabel("Importancia")
ax2.tick_params(axis="x", rotation=45, labelsize=8)
plt.tight_layout()
plt.savefig("ml_regresion_demanda.png", dpi=150)
plt.close()


# ════════════════════════════════════════════════════════════════════════════
# SECCIÓN 8 — EXPORTACIÓN A WORD
# ════════════════════════════════════════════════════════════════════════════

print("\n" + "=" * 68)
print("  GENERANDO INFORME WORD")
print("=" * 68)

def df_to_word_table(doc, df, max_rows=None):
    df_show = df.head(max_rows) if max_rows else df
    table = doc.add_table(rows=1, cols=len(df_show.columns))
    table.style = "Table Grid"
    hdr = table.rows[0].cells
    for i, col in enumerate(df_show.columns):
        hdr[i].text = str(col)
        hdr[i].paragraphs[0].runs[0].bold = True
    for _, row in df_show.iterrows():
        cells = table.add_row().cells
        for i, val in enumerate(row):
            cells[i].text = str(round(val, 3) if isinstance(val, float) else val)

doc = Document()
doc.styles["Normal"].font.name = "Calibri"
doc.styles["Normal"].font.size = Pt(10)

doc.add_heading("Sistema Predictivo de Refacciones", 0)
doc.add_heading("Línea de Producción — Panadería Industrial", 1)
doc.add_heading("Fases 4 y 5: Weibull + Machine Learning", 2)
p = doc.add_paragraph(f"Generado: {pd.Timestamp.now().strftime('%d/%m/%Y %H:%M')}  |  "
                       f"Metodología: SAE JA1011 · ISO 14224 · RCM · Weibull · ML")
p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
doc.add_page_break()

# Sección 1: Inventario
doc.add_heading("1. Inventario con Mínimos, Máximos y Semáforo de Stock", level=1)
df_to_word_table(doc, df_inventario[["descripcion", "categoria", "stock_actual",
    "stock_minimo", "stock_maximo", "punto_reorden", "semaforo",
    "clase_ABC", "criticidad_SAE", "prioridad_maxima"]].round(1))

# Sección 2: Criticidad
doc.add_page_break()
doc.add_heading("2. Análisis de Criticidad — SAE JA1011 / ISO 14224 / RCM", level=1)
doc.add_paragraph(
    "El NPR (Número de Prioridad de Riesgo) se calcula como:\n"
    "NPR = Impacto en Producción × Probabilidad de Falla × Detectabilidad inversa\n"
    "Clasificación: CRÍTICO (NPR > 40) · IMPORTANTE (21–40) · MENOR (≤ 20)")
df_to_word_table(doc, df_criticidad[["maquina", "NPR", "criticidad_SAE",
    "consecuencia_ISO", "impacto_produccion",
    "impacto_seguridad", "impacto_calidad"]].sort_values("NPR", ascending=False))

# Sección 3: ABC
doc.add_page_break()
doc.add_heading("3. Análisis ABC del Inventario", level=1)
doc.add_paragraph("Clase A = 80% del valor de consumo · B = 15% · C = 5%")
df_to_word_table(doc, resumen_abc)
doc.add_paragraph("\nRefacciones de Máxima Prioridad (Clase A + Máquina CRÍTICA):")
df_to_word_table(doc, df_inventario[df_inventario["prioridad_maxima"] != ""][
    ["descripcion", "clase_ABC", "criticidad_SAE", "stock_actual",
     "semaforo", "costo_unitario"]])

# Sección 4: Estadística
doc.add_page_break()
doc.add_heading("4. Análisis Estadístico Avanzado", level=1)
df_to_word_table(doc, desc.reset_index().round(3))
doc.add_paragraph(f"\nKruskal-Wallis (consumo por categoría): H={h:.3f}  p={p_kw:.4f}")
doc.add_paragraph(f"{'Diferencia significativa entre categorías' if p_kw < 0.05 else 'Sin diferencia significativa'}")
doc.add_heading("Gráficos de Análisis Estadístico", level=2)
doc.add_picture("estadistica_avanzada_panaderia.png", width=Inches(6.2))

# Sección 5: Weibull refacciones
doc.add_page_break()
doc.add_heading("5. Análisis de Weibull — Refacciones / Componentes", level=1)
doc.add_paragraph(
    "β < 1: Mortalidad infantil → revisar proveedor e instalación\n"
    "β ≈ 1: Fallo aleatorio → revisar causas externas / operativas\n"
    "β > 1: Desgaste → candidato ideal para mantenimiento preventivo programado\n\n"
    "Vida B10 = Horas en que el 10% de los componentes ya habrá fallado (90% confiabilidad)\n"
    "MTTF = Horas promedio hasta el fallo")
df_to_word_table(doc, df_wb_refac[["nombre", "beta", "eta", "mttf",
                                    "b10_h", "b50_h", "ajuste"]].round(2))
doc.add_picture("weibull_refacciones.png", width=Inches(6.2))

# Sección 6: Weibull máquinas
doc.add_page_break()
doc.add_heading("6. Análisis de Weibull — Máquinas de Producción", level=1)
df_to_word_table(doc, df_wb_maq[["nombre", "beta", "eta", "mttf",
                                  "b10_h", "criticidad"]].round(2))
doc.add_picture("weibull_maquinas.png", width=Inches(6.2))
doc.add_heading("Comparativa MTTF y Vida B10", level=2)
doc.add_picture("weibull_comparativa.png", width=Inches(6.2))

# Sección 7: ML
doc.add_page_break()
doc.add_heading("7. Modelos de Machine Learning", level=1)

for res in [r for r in [res_fallo, res_prioridad] if r]:
    doc.add_heading(f"7.x. {res['nombre']}", level=2)
    for nom, d in res["modelos"].items():
        doc.add_paragraph(
            f"{'★ ' if nom == res['mejor'] else '  '}{nom}: "
            f"Exactitud={d['acc']:.4f}  F1={d['f1']:.4f}  AUC={d['auc']:.4f}")
    doc.add_paragraph(f"Reporte del mejor modelo ({res['mejor']}):")
    doc.add_paragraph(res["modelos"][res["mejor"]]["rep"])

try:
    doc.add_heading("Matrices de Confusión — Fallo Inminente", level=2)
    doc.add_picture("cm_fallo_inminente.png", width=Inches(6))
    doc.add_heading("Matrices de Confusión — Prioridad Alta", level=2)
    doc.add_picture("cm_prioridad_alta.png", width=Inches(6))
except Exception:
    pass

doc.add_heading("7.3. Predicción de Demanda — Próximo Mes", level=2)
doc.add_paragraph(f"MAE = {mae:.2f} unidades  |  RMSE = {rmse:.2f}  |  R² = {r2:.4f}")
doc.add_picture("ml_regresion_demanda.png", width=Inches(6.2))

# Sección 8: Recomendaciones
doc.add_page_break()
doc.add_heading("8. Recomendaciones de Mantenimiento Preventivo (Weibull B10)", level=1)
doc.add_paragraph(
    "Intervalos recomendados de cambio preventivo al 90% de confiabilidad.\n"
    "Priorizar los componentes de máquinas CRÍTICAS (SAE JA1011):")

df_rec = df_wb_refac.sort_values("b10_h").merge(
    df_inventario[["descripcion", "criticidad_SAE", "costo_unitario"]].drop_duplicates(),
    left_on="nombre", right_on="descripcion", how="left")

for _, row in df_rec.iterrows():
    critica = row.get("criticidad_SAE", "N/D")
    costo   = row.get("costo_unitario", 0)
    doc.add_paragraph(
        f"• {row['nombre'][:40]}: cambio preventivo cada {row['b10_h']:,.0f} h  "
        f"| MTTF={row['mttf']:,.0f} h  | β={row['beta']:.2f}  "
        f"| Máquina: {critica}  | Costo: ${costo:.2f}",
        style="List Bullet"
    )

doc.save("informe_refacciones_panaderia.docx")
print("  Informe guardado: informe_refacciones_panaderia.docx")
print("\n" + "=" * 68)
print("  PROCESO COMPLETADO — Fases 4 y 5 del Plan de 16 Semanas")
print("=" * 68)
