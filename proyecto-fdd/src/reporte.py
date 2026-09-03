"""Exportación del informe a Word con python-docx.

Adaptado del módulo de exportación de `Codigo de AI 2.0.txt` (líneas 12-14,
41-69 y 84-133), que es lo único de aquella versión que la auditoría de la
Etapa 1 recomendó conservar. Cambios respecto al original:

  * `capture_df_info` se reescribe con `contextlib.redirect_stdout`, que es a
    prueba de excepciones (defecto D11: el original dejaba `sys.stdout`
    apuntando al StringIO si `df.info()` lanzaba).
  * Ya no se rotulan como «mejores parámetros» los parámetros por defecto
    (defecto D9): aquí solo se escriben los que salieron de una búsqueda real.
  * El informe NO encabeza con la exactitud (sección 7.3): abre con recall y F1
    por clase, y la exactitud aparece al final acompañada de la proporción de
    clases.
  * Se incluyen las cuatro declaraciones obligatorias de la sección 11.
"""

from __future__ import annotations

import io
from contextlib import redirect_stdout
from datetime import date
from pathlib import Path

import pandas as pd
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt

from .fallas import CLASES

RAIZ = Path(__file__).resolve().parents[1]
DIR_RESULTADOS = RAIZ / "resultados"


def capturar_info(df: pd.DataFrame) -> str:
    """Captura la salida de `df.info()` sin dejar `stdout` redirigido."""
    buffer = io.StringIO()
    with redirect_stdout(buffer):
        df.info()
    return buffer.getvalue()


def _tabla(doc: Document, filas: list[list[str]], encabezado: bool = True):
    tabla = doc.add_table(rows=len(filas), cols=len(filas[0]))
    tabla.style = "Light Grid Accent 1"
    for i, fila in enumerate(filas):
        for j, celda in enumerate(fila):
            parrafo = tabla.cell(i, j).paragraphs[0]
            run = parrafo.add_run(str(celda))
            run.font.size = Pt(8)
            if i == 0 and encabezado:
                run.bold = True
    return tabla


def _seccion_metricas(doc: Document, met: dict, titulo: str) -> None:
    doc.add_heading(titulo, level=2)
    doc.add_paragraph(f"Muestras evaluadas: {met['n_muestras']}")

    doc.add_heading("Recall y F1 por clase", level=3)
    doc.add_paragraph(
        "Métricas principales del informe. Se reportan por clase y nunca solo "
        "como promedio: un promedio alto puede esconder una clase con recall nulo.")
    filas = [["Clase", "Recall", "F1", "Precisión", "PR-AUC", "Soporte"]]
    for c in CLASES:
        pr = met["pr_auc_por_clase"].get(c)
        filas.append([c,
                      f"{met['recall_por_clase'][c]:.3f}",
                      f"{met['f1_por_clase'][c]:.3f}",
                      f"{met['precision_por_clase'][c]:.3f}",
                      "—" if pr is None else f"{pr:.3f}",
                      str(met["soporte_por_clase"][c])])
    _tabla(doc, filas)

    doc.add_paragraph()
    doc.add_paragraph(f"F1 macro: {met['f1_macro']:.4f}    "
                      f"F1 ponderado: {met['f1_ponderado']:.4f}    "
                      f"PR-AUC macro: {met['pr_auc_macro']:.4f}")

    doc.add_heading("Reporte de clasificación", level=3)
    parrafo = doc.add_paragraph(met["texto_reporte"])
    parrafo.runs[0].font.name = "Consolas"
    parrafo.runs[0].font.size = Pt(7)

    doc.add_heading("Exactitud global y proporción de clases", level=3)
    proporciones = ", ".join(f"{k} {v:.1%}" for k, v in
                             sorted(met["proporcion_de_clases"].items(),
                                    key=lambda kv: -kv[1]))
    doc.add_paragraph(f"Exactitud global: {met['exactitud_global']:.4f}")
    doc.add_paragraph(f"Proporción de clases del conjunto: {proporciones}")
    doc.add_paragraph(
        "La exactitud se reporta al final y acompañada de la proporción de clases. "
        "Con 70 % de muestras sanas, un modelo que prediga siempre «sano» obtiene "
        "70 % de exactitud y cero utilidad diagnóstica (Saito y Rehmsmeier, 2015).")


def generar_informe(metricas: dict, ruta_salida: Path | None = None) -> Path:
    """Construye el informe Word a partir del diccionario de métricas."""
    ruta_salida = ruta_salida or (DIR_RESULTADOS / "informe_fdd.docx")
    ruta_salida.parent.mkdir(parents=True, exist_ok=True)
    figuras = metricas.get("figuras", {})

    doc = Document()
    doc.add_heading("Detección y diagnóstico de fallas por simulación — Resultados", 0)
    sub = doc.add_paragraph(
        "Fase 5 — Monitoreo e Innovación · Plan Integral de Mantenimiento\n"
        "Sistema de Refrigeración y Aire Acondicionado (0251) — UTP\n"
        f"Generado automáticamente el {date.today().isoformat()}")
    sub.alignment = WD_ALIGN_PARAGRAPH.LEFT

    # --- Declaraciones obligatorias (sección 11) --------------------------
    doc.add_heading("Declaraciones", level=1)
    doc.add_paragraph(
        "Estas cuatro declaraciones no debilitan el trabajo: lo blindan. Una "
        "limitación declarada y analizada es criterio; una no declarada es un error.")
    for texto in [
        "El modelo fue entrenado con datos sintéticos generados a partir de un modelo "
        "termodinámico del ciclo de compresión de vapor, no con datos históricos de la "
        "instalación.",
        "El modelado del inventario de refrigerante (carga baja, sobrecarga) y de la "
        "restricción de la línea de líquido es una aproximación empírica, no un modelo "
        "de primeros principios.",
        "Lo que se demuestra es la viabilidad del método; la implementación en la "
        "instalación real requeriría un periodo de recolección de datos y una "
        "recalibración de los coeficientes UA con mediciones de campo.",
        "Las métricas principales son recall y F1 por clase; la exactitud global se "
        "reporta acompañada de la proporción de clases.",
    ]:
        doc.add_paragraph(texto, style="List Number")

    doc.add_paragraph(
        "Limitación adicional, sobre la interpretación de las métricas: los residuos se "
        "calculan contra el MISMO modelo que generó los datos, de modo que no existe "
        "discrepancia entre modelo y planta. En una instalación real, esa discrepancia —el "
        "error del gemelo digital frente al equipo físico— sería la fuente de error "
        "dominante, por encima del ruido de los instrumentos. Las métricas de este informe "
        "deben leerse como una COTA SUPERIOR del desempeño alcanzable, no como el desempeño "
        "esperado en campo.")

    provisionales = metricas.get("parametros_provisionales", [])
    if provisionales:
        doc.add_paragraph(
            f"AVISO: {len(provisionales)} parámetros del equipo siguen marcados como "
            f"PROVISIONALES a la espera de confirmar el sitio de estudio: "
            f"{', '.join(provisionales)}.")

    # --- Configuración ----------------------------------------------------
    doc.add_heading("1. Configuración del experimento", level=1)
    doc.add_paragraph(f"Semilla maestra: {metricas.get('semilla_maestra')}")
    part = metricas.get("particion", {})
    doc.add_paragraph(
        f"Partición por grupos de condición de contorno — filas: {part.get('filas')}; "
        f"condiciones: {part.get('condiciones')}. Ninguna condición aparece en más de "
        f"una partición.")
    doc.add_paragraph(
        "Entradas del clasificador (lista blanca): "
        + ", ".join(metricas.get("columnas_de_entrada", [])))
    doc.add_paragraph(
        "No se usan mediciones crudas ni condiciones de contorno: el clasificador "
        "opera solo sobre residuos, para que no pueda aprender clima en lugar de falla.")

    cal = metricas.get("calibracion_ua") or {}
    if cal:
        doc.add_paragraph(
            f"Coeficientes UA calibrados: UA_ev = {cal.get('UA_ev', float('nan')):.1f} W/K, "
            f"UA_cd = {cal.get('UA_cd', float('nan')):.1f} W/K "
            f"(origen: {cal.get('origen_datos')}).")

    sel = metricas.get("seleccion_de_modelo", {})
    doc.add_heading("Selección de modelo", level=2)
    doc.add_paragraph(f"Criterio: {sel.get('criterio')}. Modelo elegido: {sel.get('ganador')}.")
    filas = [["Candidato", "F1 macro (CV)", "F1 macro (validación)", "Hiperparámetros"]]
    for nombre, datos in sel.get("candidatos", {}).items():
        filas.append([nombre, f"{datos['f1_macro_cv']:.4f}",
                      f"{datos['f1_macro_validacion']:.4f}",
                      str(datos["mejores_parametros"])])
    _tabla(doc, filas)
    doc.add_paragraph(
        "Los hiperparámetros provienen de una búsqueda real con GridSearchCV "
        "optimizando F1 macro sobre GroupKFold; el conjunto de prueba no participó "
        "en ninguna decisión.")

    aperturas = metricas.get("aperturas_del_conjunto_de_prueba", {})
    doc.add_paragraph(
        f"Control de integridad: aperturas del conjunto de prueba {aperturas}; "
        f"corrida válida: {metricas.get('corrida_valida')}.")

    # --- Métricas ---------------------------------------------------------
    doc.add_heading("2. Resultados", level=1)
    m = metricas.get("metricas", {})
    if "prueba_balanceada" in m:
        _seccion_metricas(doc, m["prueba_balanceada"],
                          "2.1 Conjunto de prueba balanceado")
    if "prevalencia_realista" in m:
        _seccion_metricas(doc, m["prevalencia_realista"],
                          "2.2 Conjunto de prevalencia realista de campo")
        doc.add_paragraph(
            "La caída de precisión entre un conjunto y otro es el fenómeno documentado "
            "por Saito y Rehmsmeier (2015): con clases desbalanceadas, la exactitud "
            "global y la curva ROC producen una impresión optimista del desempeño, "
            "mientras que la curva precisión-recall revela el comportamiento real. "
            "Reportar ambos conjuntos permite cuantificar ese efecto en lugar de padecerlo.")

    # --- Figuras ----------------------------------------------------------
    doc.add_heading("3. Figuras", level=1)
    titulos = {
        "fig1_diagrama_ph": "Figura 1. Diagrama P-h: ciclo sano frente a ciclo degradado",
        "fig2a_matriz_confusion_balanceado": "Figura 2a. Matriz de confusión — conjunto balanceado",
        "fig2b_matriz_confusion_prevalencia": "Figura 2b. Matriz de confusión — prevalencia realista",
        "fig3a_curvas_pr_balanceado": "Figura 3a. Curvas precisión-recall — conjunto balanceado",
        "fig3b_curvas_pr_prevalencia": "Figura 3b. Curvas precisión-recall — prevalencia realista",
        "fig4_importancia_permutacion": "Figura 4. Importancia de características por permutación",
        "fig5_deteccion_vs_severidad": "Figura 5. Curva de detección frente a severidad",
        "fig6_sensibilidad_ruido": "Figura 6. Sensibilidad al ruido de los instrumentos",
        "fig7_mapa_firmas": "Figura 7. Mapa de firmas: residuo medio por clase",
    }
    for clave, titulo in titulos.items():
        ruta = figuras.get(clave)
        if ruta and Path(ruta).exists():
            doc.add_heading(titulo, level=2)
            doc.add_picture(ruta, width=Inches(6.0))

    # --- Análisis ---------------------------------------------------------
    doc.add_heading("4. Contraste con la expectativa física", level=1)
    doc.add_paragraph(
        "Para cada clase se compara el residuo que más la separa de la condición sana "
        "contra el residuo característico que predice la física del modo de falla. El "
        "contraste se hace por dos vías: el tamaño de efecto en los datos "
        "—|media(clase) − media(sano)| / desviación(sano)— y el residuo que un árbol de "
        "decisión uno-contra-sano elige en su raíz.")
    contraste = metricas.get("contraste_con_la_fisica", {})
    if contraste:
        filas = [["Clase", "Esperado por física", "Dominante en los datos",
                  "Puesto del esperado", "Raíz del árbol"]]
        for clase, datos in contraste.items():
            filas.append([clase,
                          datos["residuo_caracteristico_esperado"],
                          datos["residuo_dominante_en_los_datos"],
                          str(datos["puesto_del_esperado_en_los_datos"]),
                          datos["residuo_raiz_del_arbol"]])
        _tabla(doc, filas)
        doc.add_paragraph(
            "No se usó la importancia por permutación para este contraste: con un bosque "
            "de 300 árboles y once residuos correlacionados entre sí, permutar una sola "
            "característica apenas mueve la predicción porque el modelo se apoya en las "
            "demás, y el ranking queda dominado por el ruido. La figura 4 conserva la "
            "importancia por permutación global, que es la que pide la especificación.")

    ruido = metricas.get("sensibilidad_al_ruido", {})
    if ruido:
        doc.add_heading("5. Sensibilidad al ruido de los instrumentos", level=1)
        doc.add_paragraph(
            "Responde a la pregunta «¿qué exactitud de instrumento hace falta para que "
            "esto funcione?», que es una pregunta de ingeniería, no de ciencia de datos. "
            "El factor 1,0 corresponde a la exactitud declarada de los instrumentos "
            "usados en campo en la Fase 1.")
        filas = [["Factor de ruido", "F1 macro", "Diagnóstico incipiente",
                  "Detección incipiente"]]
        for factor in sorted(ruido, key=float):
            d = ruido[factor]
            filas.append([f"×{float(factor):.1f}", f"{d['f1_macro']:.4f}",
                          f"{d['diagnostico_incipiente']:.4f}",
                          f"{d['deteccion_incipiente']:.4f}"])
        _tabla(doc, filas)

    sev = metricas.get("modelo_de_severidad", {})
    if sev:
        doc.add_heading("6. Modelo secundario de severidad", level=1)
        doc.add_paragraph(
            f"RandomForestRegressor entrenado solo con muestras con falla "
            f"({sev.get('n_entrenamiento')} muestras). "
            f"MAE en validación: {sev.get('mae_validacion', float('nan')):.4f}; "
            f"R²: {sev.get('r2_validacion', float('nan')):.4f}. "
            f"MAE en prueba: {sev.get('mae_prueba', float('nan')):.4f}; "
            f"R²: {sev.get('r2_prueba', float('nan')):.4f}.")
        doc.add_paragraph(
            "Sirve para priorizar la orden de trabajo: no es lo mismo un condensador "
            "con ensuciamiento incipiente que uno severo.")

    doc.add_heading("7. Referencias", level=1)
    for r in [
        "Bell, I. H., Wronski, J., Quoilin, S., & Lemort, V. (2014). Pure and pseudo-pure "
        "fluid thermophysical property evaluation and the open-source thermophysical "
        "property library CoolProp. Industrial & Engineering Chemistry Research, 53(6), "
        "2498–2508.",
        "Breiman, L. (2001). Random forests. Machine Learning, 45(1), 5–32.",
        "Katipamula, S., & Brambley, M. R. (2005). Methods for fault detection, "
        "diagnostics, and prognostics for building systems — A review, Part I y Part II. "
        "HVAC&R Research, 11(1), 3–25 y 11(2), 169–187.",
        "Pedregosa, F., et al. (2011). Scikit-learn: Machine learning in Python. Journal "
        "of Machine Learning Research, 12, 2825–2830.",
        "Saito, T., & Rehmsmeier, M. (2015). The precision-recall plot is more informative "
        "than the ROC plot when evaluating binary classifiers on imbalanced datasets. "
        "PLOS ONE, 10(3), e0118432.",
        "Çengel, Y. A., & Boles, M. A. Termodinámica. McGraw-Hill.",
        "Çengel, Y. A., & Ghajar, A. J. Transferencia de calor y masa. McGraw-Hill.",
    ]:
        doc.add_paragraph(r, style="List Bullet")

    doc.save(ruta_salida)
    return ruta_salida


if __name__ == "__main__":
    import json
    metricas = json.loads((DIR_RESULTADOS / "metricas.json").read_text(encoding="utf-8"))
    print(f"Informe -> {generar_informe(metricas)}")
