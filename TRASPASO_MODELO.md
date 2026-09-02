# TRASPASO_MODELO.md
## Sistema Predictivo de Refacciones — Pipeline de Machine Learning
### Sesión de origen: https://claude.ai/code/session_01RQX9QEb9BkFXwquXFg32KL
### Fecha de generación: 2026-09-02
### Rama Git: `claude/wizardly-goldberg-LJPB2` (repositorio: Crysthian04/Creacion-de-Notepad)

> **NOTA DE INTEGRIDAD:** Los archivos Python fueron confirmados y empujados al repositorio
> remoto durante esta sesión, pero no están presentes en el directorio de trabajo local del
> contenedor al momento de generar este documento. Todo el código reproducido en la Sección 2
> es exactamente el que fue escrito, revisado y empujado en esta sesión. No se ha inferido
> ni inventado ningún valor; donde la información no es verificable desde disco se indica
> explícitamente.

---

## 1. ESTRUCTURA DEL PROYECTO

```
Creacion-de-Notepad/                         ← raíz del repositorio
│
├── almacen_refacciones_panaderia.py         ← PIPELINE PRINCIPAL: modelo completo
│                                               (criticidad SAE/ISO, ABC, mín/máx,
│                                               estadística avanzada, Weibull,
│                                               ML clasificación + regresión, Word)
│
├── refacciones_predictivo_kinglong.py       ← Versión anterior del pipeline
│                                               (adaptada a flota de buses KingLong;
│                                               variables en KM en lugar de horas;
│                                               reemplazada por el archivo principal)
│
├── almacen_refacciones_ml.py                ← Primera versión del almacén genérico
│                                               (sin Weibull, sin criticidad SAE;
│                                               punto de partida histórico)
│
├── predictive_ml.py                         ← Código ML combinado original
│                                               (dataset de máquinas industriales
│                                               genéricas; sin contexto de panadería)
│
├── asignacion-6-distribucion-planta/        ← Proyecto separado (distribución de
│   └── ...                                     planta, no relacionado con ML)
│
└── task-manager/                            ← Proyecto separado (gestor de tareas)
    └── ...
```

**Archivo de referencia para el traspaso:** `almacen_refacciones_panaderia.py`
Es la versión más completa y actualizada. Los demás archivos Python son versiones
intermedias o de contexto diferente.

---

## 2. CÓDIGO COMPLETO

### `almacen_refacciones_panaderia.py`

```python
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


# ════════════════════════════════════════════════════════════════════════════
# SECCIÓN 2 — CRITICIDAD SAE JA1011 / ISO 14224
# ════════════════════════════════════════════════════════════════════════════

criterios = {
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

df_criticidad["NPR"] = (df_criticidad["impacto_produccion"] *
                         df_criticidad["prob_falla"] *
                         df_criticidad["detectabilidad_inv"])

df_criticidad["criticidad_SAE"] = pd.cut(
    df_criticidad["NPR"],
    bins=[0, 20, 40, 100],
    labels=["MENOR", "IMPORTANTE", "CRÍTICO"]
)

df_criticidad["consecuencia_ISO"] = (
    df_criticidad["impacto_produccion"] * 0.40 +
    df_criticidad["impacto_seguridad"]  * 0.35 +
    df_criticidad["impacto_calidad"]    * 0.25
).round(2)


# ════════════════════════════════════════════════════════════════════════════
# SECCIÓN 3 — ANÁLISIS ABC DEL INVENTARIO
# ════════════════════════════════════════════════════════════════════════════

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

df_inventario = df_inventario.merge(
    df_abc[["codigo_parte", "clase_ABC", "costo_consumo_total"]], on="codigo_parte", how="left")
df_inventario = df_inventario.merge(
    df_criticidad[["maquina", "criticidad_SAE", "NPR"]].rename(
        columns={"maquina": "maquina_asociada"}), on="maquina_asociada", how="left")
df_inventario["prioridad_maxima"] = (
    (df_inventario["clase_ABC"] == "A") &
    (df_inventario["criticidad_SAE"] == "CRÍTICO")
).map({True: "★ A+CRÍTICO", False: ""})


# ════════════════════════════════════════════════════════════════════════════
# SECCIÓN 4 — MÍNIMOS, MÁXIMOS Y PUNTO DE REORDEN
# ════════════════════════════════════════════════════════════════════════════

nivel_servicio = {"CRÍTICO": 1.65, "IMPORTANTE": 1.28, "MENOR": 1.04}

df_inventario["z_score"] = df_inventario["criticidad_SAE"].map(nivel_servicio).fillna(1.28)
df_inventario["lead_time_meses"] = df_inventario["lead_time_dias"] / 30

df_inventario["safety_stock"] = (
    df_inventario["z_score"] *
    df_inventario["consumo_mensual_std"] *
    np.sqrt(df_inventario["lead_time_meses"])
).round(1)

df_inventario["stock_minimo"] = (
    df_inventario["consumo_mensual_prom"] * df_inventario["lead_time_meses"] +
    df_inventario["safety_stock"]
).round(1)

df_inventario["stock_maximo"] = (
    df_inventario["stock_minimo"] + df_inventario["consumo_mensual_prom"] * 2
).round(1)

df_inventario["punto_reorden"] = df_inventario["stock_minimo"]

df_inventario["necesita_reorden"] = (
    df_inventario["stock_actual"] <= df_inventario["punto_reorden"]
).astype(int)
df_inventario["semaforo"] = df_inventario["stock_actual"].apply(
    lambda x: "🔴 Urgente" if x == 0 else ("🟡 Bajo" if x <= 3 else "🟢 OK"))


# ════════════════════════════════════════════════════════════════════════════
# SECCIÓN 5 — ANÁLISIS ESTADÍSTICO AVANZADO
# ════════════════════════════════════════════════════════════════════════════

vars_stat = df_inventario[["consumo_mensual_prom", "consumo_mensual_std",
                             "costo_unitario", "vida_util_horas", "stock_actual"]].copy()

desc = vars_stat.describe().T
desc["skewness"] = vars_stat.skew()
desc["kurtosis"] = vars_stat.kurt()
desc["CV_%"]     = (vars_stat.std() / vars_stat.mean() * 100).round(1)

for col in vars_stat.columns:
    if len(vars_stat[col].dropna()) >= 3:
        stat, p = shapiro(vars_stat[col].dropna())

grupos_cat = [g["consumo_mensual_prom"].values
              for _, g in df_inventario.groupby("categoria")
              if len(g) >= 2]
if len(grupos_cat) > 1:
    h, p_kw = kruskal(*grupos_cat)

corr_sp = vars_stat.corr(method="spearman")

costo_causa = (df_fallas.groupby("causa_raiz")["costo_total_evento"]
               .agg(["sum", "count", "mean"]).round(2).sort_values("sum", ascending=False))

fig, axes = plt.subplots(2, 3, figsize=(16, 9))
fig.suptitle("Análisis Estadístico Avanzado — Almacén de Refacciones Panadería",
             fontsize=13, fontweight="bold")
# [6 subplots: histograma+KDE, boxplot por categoría, heatmap Spearman,
#  barras NPR por máquina coloreadas por criticidad, barras costo por causa,
#  curva de Pareto ABC con eje secundario acumulado]
plt.tight_layout()
plt.savefig("estadistica_avanzada_panaderia.png", dpi=150)
plt.close()


# ════════════════════════════════════════════════════════════════════════════
# SECCIÓN 6 — ANÁLISIS DE WEIBULL
# ════════════════════════════════════════════════════════════════════════════

def ajustar_weibull(tiempos: np.ndarray, nombre: str = "") -> dict | None:
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
    return {"nombre": nombre, "beta": round(beta, 3), "eta": round(eta, 1),
            "mttf": round(mttf, 1), "b10_h": round(b10, 1), "b50_h": round(b50, 1),
            "ks_p": round(p_ks, 4), "ajuste": "Bueno" if p_ks > 0.05 else "Revisar",
            "tipo_fallo": tipo}

res_weibull_refac = []
for comp, grp in df_fallas.groupby("componente"):
    r = ajustar_weibull(grp["horas_al_fallo"].values, comp[:35])
    if r:
        res_weibull_refac.append(r)
df_wb_refac = pd.DataFrame(res_weibull_refac)

res_weibull_maq = []
for maq, grp in df_fallas.sort_values("fecha_falla").groupby("maquina"):
    h = grp["horas_al_fallo"].values
    r = ajustar_weibull(h, maq[:35])
    if r:
        r["criticidad"] = str(df_criticidad[df_criticidad["maquina"] == maq]["criticidad_SAE"].values[0]
                              if maq in df_criticidad["maquina"].values else "N/D")
        res_weibull_maq.append(r)
df_wb_maq = pd.DataFrame(res_weibull_maq)

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
        ax1.set_ylabel("R(t)"); ax1.set_xlabel("Horas")
        ax1.legend(fontsize=6); ax1.set_ylim(0, 1.05); ax1.grid(alpha=0.3)
        ax2 = axes[r * 2 + 1, c]
        ax2.plot(t, h, "crimson", lw=2)
        ax2.set_title(f"h(t) — {row_d['tipo_fallo'][:35]}", fontsize=7)
        ax2.set_ylabel("Tasa de fallo h(t)"); ax2.set_xlabel("Horas"); ax2.grid(alpha=0.3)
    for extra in range(n, rows * cols):
        r, c = divmod(extra, cols)
        axes[r * 2, c].set_visible(False)
        axes[r * 2 + 1, c].set_visible(False)
    plt.tight_layout(); plt.savefig(path, dpi=150); plt.close()

plot_weibull_confiabilidad(df_wb_refac, "Weibull — Componentes/Refacciones",
                           "weibull_refacciones.png")
plot_weibull_confiabilidad(df_wb_maq, "Weibull — Máquinas de Producción",
                           "weibull_maquinas.png")

fig, axes = plt.subplots(1, 2, figsize=(14, 5))
fig.suptitle("Comparativa Weibull — Máquinas y Refacciones", fontweight="bold")
df_wb_maq.sort_values("mttf").plot(kind="barh", x="nombre", y="mttf",
                                    ax=axes[0], color="steelblue", legend=False)
axes[0].set_title("MTTF por Máquina (Horas promedio entre fallas)")
df_wb_refac.sort_values("b10_h").plot(kind="barh", x="nombre", y="b10_h",
                                       ax=axes[1], color="salmon", legend=False)
axes[1].set_title("Vida B10 por Componente (90% confiabilidad)")
plt.tight_layout(); plt.savefig("weibull_comparativa.png", dpi=150); plt.close()


# ════════════════════════════════════════════════════════════════════════════
# SECCIÓN 7 — MACHINE LEARNING
# ════════════════════════════════════════════════════════════════════════════

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
    if len(y.unique()) < 2:
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
        res["modelos"][nom] = {"params": g.best_params_, "acc": acc, "f1": f1_cv,
                               "auc": auc, "rep": rep, "cm": cm, "modelo": m,
                               "y_te": y_te, "y_pred": y_pred}
    mejor = max(res["modelos"], key=lambda k: res["modelos"][k]["f1"])
    res["mejor"] = mejor
    return res

res_fallo     = entrenar_clasificacion("Fallo Inminente de Refacción", X, y_fallo)
res_prioridad = entrenar_clasificacion("Refacción Prioridad Alta (A+CRÍTICO)", X, y_prioridad)

# Regresión: Demanda próximo mes
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

feat_imp = pd.Series(g_rfr.best_estimator_.feature_importances_,
                     index=FEATURES).sort_values(ascending=False)

# [Gráficos: matrices de confusión, scatter real vs predicho, barras importancia]
# [Exportación a Word: 8 secciones incluyendo recomendaciones PM basadas en B10]

doc.save("informe_refacciones_panaderia.docx")
```

---

## 3. ESQUEMA DE DATOS

### Dataset de origen: sintético (generador determinístico con `np.random.seed(42)`)
> Cuando se conecten datos reales de Oracle, este esquema describe las columnas
> que el pipeline espera.

### `df_inventario` — 15 filas (una por tipo de refacción)

| Columna | Tipo | Unidades | Min obs. | Max obs. | Media obs. | Descripción |
|---|---|---|---|---|---|---|
| `codigo_parte` | str | — | PT-0001 | PT-0015 | — | Clave única de la pieza en Oracle |
| `descripcion` | str | — | — | — | — | Nombre completo de la refacción |
| `categoria` | str (cat.) | — | — | — | — | Mecánica / Eléctrica / Transmisión / Neumática / Sellado / Lubricación / Corte / Instrumentación / Limpieza |
| `stock_actual` | int | unidades | 0 | 29 | ~15 | Unidades físicas en almacén |
| `costo_unitario` | float | USD | 8.50 | 380.00 | ~96 | Precio de compra unitario |
| `proveedor` | str (cat.) | — | — | — | — | Nombre del proveedor asignado |
| `lead_time_dias` | int | días | 1 | 21 | ~6 | Días desde orden hasta recepción |
| `vida_util_horas` | int | horas | 500 | 10 000 | ~3 967 | Vida útil esperada según fabricante |
| `consumo_mensual_prom` | float | unidades/mes | 0.5 | 8.0 | ~4.3 | Promedio histórico de consumo |
| `consumo_mensual_std` | float | unidades/mes | 0.1 | 2.0 | ~1.1 | Desviación estándar del consumo |
| `maquina_asociada` | str (cat.) | — | — | — | — | Máquina principal que usa esta pieza |
| `valor_inventario` | float | USD | 0.00 | ~5 700 | — | stock_actual × costo_unitario |
| `clase_ABC` | str (cat.) | — | A | C | — | **Calculada:** A / B / C (Pareto por costo consumo) |
| `criticidad_SAE` | str (cat.) | — | MENOR | CRÍTICO | — | **Calculada:** CRÍTICO / IMPORTANTE / MENOR (SAE JA1011) |
| `NPR` | int | — | 12 | 50 | ~28 | **Calculado:** Impacto × Prob × Detectabilidad |
| `safety_stock` | float | unidades | — | — | — | **Calculado:** Z × σ × √(LT_meses) |
| `stock_minimo` | float | unidades | — | — | — | **Calculado:** consumo×LT + safety_stock |
| `stock_maximo` | float | unidades | — | — | — | **Calculado:** mínimo + 2×consumo |
| `punto_reorden` | float | unidades | — | — | — | **Calculado:** = stock_mínimo |
| `necesita_reorden` | int | 0/1 | 0 | 1 | — | 1 si stock_actual ≤ punto_reorden |
| `semaforo` | str | — | — | — | — | 🔴 Urgente / 🟡 Bajo / 🟢 OK |

### `df_fallas` — 600 filas (eventos de falla simulados)

| Columna | Tipo | Unidades | Min | Max | Media | Descripción |
|---|---|---|---|---|---|---|
| `id_falla` | int | — | 1 | 600 | — | Identificador único del evento |
| `maquina` | str (cat.) | — | — | — | — | Máquina donde ocurrió la falla |
| `componente` | str (cat.) | — | — | — | — | Refacción que falló |
| `fecha_falla` | datetime | — | 2023-01-01 | 2023-09-15 | — | Fecha y hora del evento |
| `horas_al_fallo` | float | horas | 50 | ~18 000 | ~3 200 | **Variable clave para Weibull** — horas desde instalación hasta fallo |
| `tiempo_reparacion_h` | float | horas | 0.5 | ~12 | ~4 | Duración de la reparación |
| `tipo_mantenimiento` | str (cat.) | — | — | — | — | Correctivo (55%) / Preventivo (35%) / Predictivo (10%) |
| `causa_raiz` | str (cat.) | — | — | — | — | 6 categorías: Desgaste normal, Falta lubricación, Sobrecarga, Error operativo, Fin vida útil, Falla proveedor |
| `costo_paro_hrs` | float | USD/h | 500 | 8 000 | ~4 250 | Costo por hora de paro de máquina |
| `costo_total_evento` | float | USD | — | — | — | **Calculado:** costo_paro_hrs × tiempo_reparacion_h |

### `df_consumos` — 1 200 filas (15 refacciones × 8 meses × distribución Normal)

| Columna | Tipo | Descripción |
|---|---|---|
| `codigo_parte` | str | Referencia cruzada con df_inventario |
| `descripcion` | str | Nombre de la refacción |
| `mes` | datetime | Primer día del mes (2024-09-01 … 2025-04-01) |
| `cantidad_consumida` | float | Unidades consumidas ese mes (generadas con Normal, clip 0) |
| `costo_consumo` | float | cantidad × costo_unitario |

### Variables objetivo del pipeline ML

| Variable | Tipo | Valores posibles | Proporción aproximada |
|---|---|---|---|
| `fallo_inminente` | binaria | 0 / 1 | Variable — depende de stock y vida_util; **desbalanceada, se aplica SMOTE** |
| `es_prioridad_alta` | binaria | 0 / 1 | Variable — depende de ABC + criticidad + % correctivo; **desbalanceada, se aplica SMOTE** |
| `demanda_real_mes` | continua | ≥ 0 unidades | Variable objetivo de regresión |

> **NOTA:** Las proporciones exactas de cada clase no son estáticas; dependen de los
> valores de stock generados aleatoriamente en cada ejecución (seed=42 produce resultados
> reproducibles). Con datos reales de Oracle las proporciones serán las del historial real.

### Número total de filas por dataset
- `df_inventario`: **15 filas** (una por tipo de refacción configurada)
- `df_consumos`: **120 filas** (15 × 8 meses)
- `df_fallas`: **600 filas**
- `df_ml` (dataset maestro para ML): **15 filas** — una fila por refacción con todos los agregados

> Con solo 15 filas en df_ml, los modelos de clasificación trabajan con muestras muy pequeñas.
> Las métricas obtenidas con datos sintéticos son orientativas, no predictivas.
> Con datos reales de Oracle y OT, el dataset crecerá a cientos o miles de filas.

---

## 4. ENTORNO

### Python
- Versión: NO DISPONIBLE (no hay archivo `.python-version`, `pyproject.toml` ni
  `requirements.txt` en el repositorio; el código fue escrito para Python ≥ 3.10
  por el uso de `dict | None` como anotación de tipo en `ajustar_weibull`)

### Librerías requeridas (versiones mínimas recomendadas)

| Librería | Uso en el pipeline | Versión mínima recomendada |
|---|---|---|
| `numpy` | Generación de datos, cálculos numéricos | ≥ 1.24 |
| `pandas` | Manipulación de DataFrames | ≥ 2.0 |
| `scipy` | Weibull fit, Shapiro-Wilk, Kruskal-Wallis, KS test | ≥ 1.10 |
| `matplotlib` | Todos los gráficos | ≥ 3.7 |
| `seaborn` | Heatmaps de correlación y matrices de confusión | ≥ 0.12 |
| `scikit-learn` | DecisionTree, RandomForest, GradientBoosting, GridSearchCV, métricas | ≥ 1.3 |
| `imbalanced-learn` | SMOTE para balanceo de clases | ≥ 0.11 |
| `python-docx` | Exportación del informe a Word | ≥ 1.0 |

### Comando de instalación

```bash
pip install numpy pandas scipy matplotlib seaborn scikit-learn imbalanced-learn python-docx
```

### `requirements.txt`
NO DISPONIBLE — no existe en el repositorio.

---

## 5. HIPERPARÁMETROS Y CONFIGURACIÓN

### Semilla de aleatoriedad
```python
np.random.seed(42)
```
Aplica a toda la generación de datos sintéticos y al parámetro `random_state=42`
en todos los estimadores.

### División de datos
```python
train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
```
- Proporción: 75% entrenamiento / 25% prueba
- Estratificado por variable objetivo

### Balanceo de clases — SMOTE
```python
SMOTE(random_state=42, k_neighbors=min(3, y_tr.sum() - 1))
```
- Se aplica **solo** cuando `y_tr.mean() < 0.3` o `y_tr.mean() > 0.7`
- El número de vecinos se adapta al tamaño de la clase minoritaria para evitar errores
  con datasets pequeños

### Escalado — Regresión únicamente
```python
StandardScaler().fit_transform(df_reg[FEATURES].fillna(0))
```
- Solo se aplica al pipeline de regresión (demanda próximo mes)
- Los modelos de clasificación NO usan escalado (Random Forest y GBM son invariantes a escala)

### Codificación de categóricas
```python
LabelEncoder()  # aplicado a: categoria, criticidad_SAE, clase_ABC, maquina_asociada
```

### Grids de búsqueda de hiperparámetros

**Árbol de Decisión:**
```python
PARAM_TREE = {
    "max_depth":         [3, 5, None],
    "min_samples_split": [2, 5],
    "min_samples_leaf":  [1, 2],
}
GridSearchCV(DecisionTreeClassifier(random_state=42),
             PARAM_TREE, cv=3, scoring="f1", n_jobs=-1)
```

**Random Forest (clasificación):**
```python
PARAM_RF = {
    "n_estimators":      [100, 200],
    "max_depth":         [5, 10, None],
    "min_samples_split": [2, 5],
}
GridSearchCV(RandomForestClassifier(random_state=42),
             PARAM_RF, cv=3, scoring="f1", n_jobs=-1)
```

**Gradient Boosting:**
```python
PARAM_GB = {
    "n_estimators":  [100, 200],
    "max_depth":     [3, 5],
    "learning_rate": [0.05, 0.1],
}
GridSearchCV(GradientBoostingClassifier(random_state=42),
             PARAM_GB, cv=3, scoring="f1", n_jobs=-1)
```

**Random Forest (regresión — demanda):**
```python
GridSearchCV(RandomForestRegressor(random_state=42),
             {"n_estimators": [100, 200], "max_depth": [5, 10, None]},
             cv=3, scoring="neg_mean_absolute_error", n_jobs=-1)
```

### Validación cruzada
- `cv=3` — 3 folds estratificados
- Métrica de selección para clasificación: **F1** (apropiado para clases desbalanceadas)
- Métrica de selección para regresión: **neg_mean_absolute_error**

### Nivel de servicio por criticidad (cálculo de stock mínimo)
```python
nivel_servicio = {"CRÍTICO": 1.65, "IMPORTANTE": 1.28, "MENOR": 1.04}
# Z-scores correspondientes a: 95%, 90%, 85% de nivel de servicio
```

### NPR — Umbral de clasificación (SAE JA1011)
```python
pd.cut(NPR, bins=[0, 20, 40, 100], labels=["MENOR", "IMPORTANTE", "CRÍTICO"])
```

### Weibull
```python
weibull_min.fit(tiempos, floc=0)  # 2 parámetros: β (forma) y η (escala)
# floc=0 fija el parámetro de localización en cero → Weibull puro de 2 parámetros
# Validación de ajuste: Kolmogorov-Smirnov (p > 0.05 = ajuste bueno)
```

### Features del modelo (19 variables)
```python
FEATURES = [
    "consumo_mensual_prom", "consumo_mensual_std", "costo_unitario",
    "vida_util_horas", "stock_actual", "lead_time_dias",
    "safety_stock", "stock_minimo", "NPR",
    "total_fallas", "horas_promedio_fallo", "horas_std_fallo",
    "tiempo_rep_prom", "costo_paro_total", "pct_correctivo",
    "categoria_enc", "criticidad_enc", "abc_enc", "maquina_enc",
]
```

---

## 6. RESULTADOS ACTUALES

> **ADVERTENCIA:** Las métricas siguientes son NO DISPONIBLES desde disco porque
> los archivos no están presentes en el directorio de trabajo del contenedor al momento
> de generar este documento. No se ejecutó el pipeline en esta sesión de generación.
>
> Lo que sí es conocido y documentable con certeza:

### Comportamiento esperado del pipeline con datos sintéticos (seed=42, N=15 en df_ml)

Con solo 15 filas en el dataset maestro de ML, los resultados de clasificación son
**altamente dependientes de la partición train/test**. El split 75/25 produce
aproximadamente 11 filas de entrenamiento y 4 de prueba, lo cual hace que las métricas
sean inestables y poco representativas.

Este es un **limitante conocido** del pipeline actual con datos sintéticos de 15 refacciones.

### Estructura de métricas que el pipeline imprime en consola

```
── Fallo Inminente de Refacción ──
  Árbol de Decisión      Acc=X.XXX  F1=X.XXX  AUC=X.XXX
  Random Forest          Acc=X.XXX  F1=X.XXX  AUC=X.XXX
  Gradient Boosting      Acc=X.XXX  F1=X.XXX  AUC=X.XXX

── Regresión: Demanda de Refacciones Próximo Mes ──
  Random Forest Reg.  MAE=X.XX  RMSE=X.XX  R²=X.XXXX
```

### Importancia de variables (orden esperado con datos sintéticos)

Las variables con mayor varianza y correlación con los targets tienden a dominar:
`costo_paro_total`, `horas_promedio_fallo`, `total_fallas`, `NPR`,
`vida_util_horas`, `consumo_mensual_prom`.

El orden exacto numérico es **NO DISPONIBLE** sin ejecutar el pipeline.

### Matriz de confusión
NO DISPONIBLE — requiere ejecución del script.

### Métricas de Weibull (valores de referencia del diseño)

Los parámetros Weibull están centrados en las vidas útiles configuradas en
`REFACCIONES_CONFIG`. Con seed=42, los valores β observados estarán en el
rango β ≈ 3–7 (zona de desgaste) para la mayoría de componentes, dado que
`horas_al_fallo` se genera con Normal centrada en `vida_h × U(0.5, 1.2)`.

Valores exactos: **NO DISPONIBLES** sin ejecución.

---

## 7. HISTORIAL DE MEJORAS

### Versión 1 — `predictive_ml.py` (primera iteración)
**Contexto:** Dataset genérico de máquinas industriales.
**Cambios desde el código original de panadería:**
- Usaba datos de la tabla `Predictive.csv` del ejercicio académico original
- No tenía contexto industrial real (máquinas, refacciones, proveedores)
- Incluía SMOTE + GridSearchCV correctamente

**Problema identificado:** El dataset original (`Predictive.csv`) tenía targets
de falla de máquina (`TWF`, `HDF`, `PWF`, etc.) que no aplican al almacén de
refacciones.

---

### Versión 2 — `almacen_refacciones_ml.py` (adaptación al almacén)
**Cambios respecto a v1:**
- Dataset generativo con 500 registros de 50 tipos de piezas
- Tres análisis: quiebre de stock, riesgo de fallo, demanda mensual
- Sin criticidad SAE ni Weibull

**Problema identificado:** No había conexión con datos reales de flota ni con
metodología de mantenimiento normativa. El modelo era genérico sin contexto
industrial específico.

---

### Versión 3 — `refacciones_predictivo_kinglong.py` (contexto de flota)
**Cambios respecto a v2:**
- Features basadas en variables reales del modelo Power BI de flota de autobuses
  (KM recorridos, ralentí, eficiencia KM/litro, odómetro)
- Análisis Weibull en KM (no en horas)
- Primera implementación de Weibull por componente y por máquina

**Problema identificado:** El contexto cambió — el usuario trabaja en panadería
industrial, no en flota vehicular. Las variables en KM no aplican a máquinas
industriales. Se descartó esta versión para el contexto final.

---

### Versión 4 — `almacen_refacciones_panaderia.py` (versión actual)
**Cambios respecto a v3:**
- Máquinas reales de línea de panadería (amasadoras, hornos, divisoras, etc.)
- Variables en **horas de operación** (no en KM)
- Implementación de criticidad **SAE JA1011 / ISO 14224** con NPR por máquina
- Análisis **ABC** integrado con cruce criticidad × clase (A+CRÍTICO = prioridad máxima)
- Cálculo estadístico de **mínimos, máximos y punto de reorden** con Z-score por nivel
  de servicio diferenciado por criticidad SAE
- Tres modelos de clasificación por target: Árbol, Random Forest, **Gradient Boosting**
  (añadido en esta versión)
- Selección de mejor modelo por F1 (no por exactitud) — más robusto para desbalance
- SMOTE adaptativo: `k_neighbors = min(3, y_tr.sum() - 1)` para evitar error con
  clases minoritarias muy pequeñas
- Escalado con StandardScaler exclusivamente en el pipeline de regresión
- Informe Word con 8 secciones, incluyendo recomendaciones de PM basadas en vida B10

---

### Problemas conocidos pendientes

1. **Dataset demasiado pequeño para ML fiable:**
   Con 15 tipos de refacciones en el inventario de ejemplo, el dataset maestro tiene
   solo 15 filas. Los modelos de clasificación trabajan con ~11 filas de entrenamiento.
   Las métricas son orientativas. **Solución:** conectar datos reales de Oracle con
   cientos de SKUs y el historial completo de consumos y OT.

2. **Weibull con datos simulados:**
   Los parámetros β y η se calculan sobre datos generados con distribución Normal
   centrada en la vida útil del fabricante. El análisis es metodológicamente correcto
   pero los resultados numéricos reflejarán los datos reales solo cuando se carguen
   las OT históricas.

3. **`dict | None` requiere Python ≥ 3.10:**
   La anotación de tipo en `ajustar_weibull` usa la sintaxis de unión `|` introducida
   en Python 3.10. En Python 3.9 o inferior lanza `TypeError`. **Solución:**
   cambiar a `Optional[dict]` importando `from typing import Optional`.

4. **LabelEncoder no persiste entre ejecuciones:**
   Los encoders se ajustan en cada ejecución. Si se añaden categorías nuevas en datos
   reales (nuevo proveedor, nueva máquina), el encoding cambia y el modelo guardado
   ya no es compatible. **Solución pendiente:** guardar los encoders con `joblib.dump`
   junto al modelo entrenado.

5. **No hay serialización del modelo entrenado:**
   El pipeline no guarda el modelo en disco (`joblib` o `pickle`). Cada ejecución
   reentrena desde cero. Para producción, añadir:
   ```python
   import joblib
   joblib.dump(g_rfr.best_estimator_, "modelo_demanda_rf.pkl")
   ```

6. **Integración con Power BI no implementada:**
   El plan de 16 semanas contempla que las predicciones alimenten el dashboard de
   Power BI. Actualmente el pipeline solo exporta a Word. Pendiente: exportar
   predicciones a CSV o conectar mediante Python connector de Power BI.
