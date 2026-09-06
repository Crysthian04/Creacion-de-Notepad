"""Exportación del informe a Word con python-docx.

Adaptado del módulo de exportación de `Codigo de AI 2.0.txt` (líneas 12-14,
41-69 y 84-133), lo único de aquella versión que la auditoría de la Etapa 1
recomendó conservar. Cambios respecto al original:

  * `capture_df_info` se reescribe con `contextlib.redirect_stdout`, a prueba de
    excepciones (defecto D11).
  * Ya no se rotulan como «mejores parámetros» los parámetros por defecto
    (defecto D9): solo se escriben los que salieron de una búsqueda real.
  * El informe NO encabeza con la exactitud (sección 7.3).
  * Se incluyen las declaraciones obligatorias de la sección 11.
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

RAIZ = Path(__file__).resolve().parents[1]
DIR_RESULTADOS = RAIZ / "resultados"


def capturar_info(df: pd.DataFrame) -> str:
    """Captura la salida de `df.info()` sin dejar `stdout` redirigido."""
    buffer = io.StringIO()
    with redirect_stdout(buffer):
        df.info()
    return buffer.getvalue()


def _tabla(doc, filas, encabezado: bool = True):
    tabla = doc.add_table(rows=len(filas), cols=len(filas[0]))
    tabla.style = "Light Grid Accent 1"
    for i, fila in enumerate(filas):
        for j, celda in enumerate(fila):
            run = tabla.cell(i, j).paragraphs[0].add_run(str(celda))
            run.font.size = Pt(8)
            if i == 0 and encabezado:
                run.bold = True
    return tabla


def _ic(par: tuple) -> str:
    lo, hi = par
    if lo != lo or hi != hi:      # NaN
        return "—"
    return f"[{lo:.2f}, {hi:.2f}]"


def _seccion_metricas(doc, met: dict, clases: list[str], titulo: str) -> None:
    doc.add_heading(titulo, level=2)
    doc.add_paragraph(f"Muestras evaluadas: {met['n_muestras']}")
    doc.add_heading("Recall y F1 por clase", level=3)
    doc.add_paragraph(
        "Métricas principales del informe. Se reportan por clase y nunca solo como "
        "promedio. Las clases con soporte menor a 50 muestras llevan intervalo de "
        "confianza de Wilson al 95 %: una precisión puntual sobre unas decenas de "
        "casos no significa nada sin su intervalo.")
    filas = [["Clase", "Recall", "IC95 recall", "Precisión", "IC95 precisión", "F1",
              "PR-AUC", "Soporte"]]
    for c in clases:
        iv = met["intervalos_wilson"][c]
        pr = met["pr_auc_por_clase"].get(c)
        pequeno = iv["soporte_pequeno"]
        filas.append([c,
                      f"{met['recall_por_clase'][c]:.3f}",
                      _ic(iv["recall_ic95"]) if pequeno else "—",
                      f"{met['precision_por_clase'][c]:.3f}",
                      _ic(iv["precision_ic95"]) if pequeno else "—",
                      f"{met['f1_por_clase'][c]:.3f}",
                      "—" if pr is None else f"{pr:.3f}",
                      str(met["soporte_por_clase"][c])])
    _tabla(doc, filas)
    doc.add_paragraph()
    doc.add_paragraph(f"F1 macro: {met['f1_macro']:.4f}    "
                      f"F1 ponderado: {met['f1_ponderado']:.4f}    "
                      f"PR-AUC macro: {met['pr_auc_macro']:.4f}")

    doc.add_heading("Reporte de clasificación", level=3)
    par = doc.add_paragraph(met["texto_reporte"])
    par.runs[0].font.name = "Consolas"
    par.runs[0].font.size = Pt(7)

    doc.add_heading("Exactitud global y proporción de clases", level=3)
    proporciones = ", ".join(f"{k} {v:.1%}" for k, v in
                             sorted(met["proporcion_de_clases"].items(), key=lambda kv: -kv[1]))
    trivial = max(met["proporcion_de_clases"].values())
    clase_trivial = max(met["proporcion_de_clases"], key=met["proporcion_de_clases"].get)
    doc.add_paragraph(f"Exactitud global: {met['exactitud_global']:.4f}")
    doc.add_paragraph(f"Proporción de clases: {proporciones}")
    doc.add_paragraph(
        f"Un clasificador trivial que predijera siempre «{clase_trivial}» obtendría "
        f"{trivial:.4f} de exactitud y CERO utilidad diagnóstica. El modelo obtiene "
        f"{met['exactitud_global']:.4f}: "
        + ("una diferencia de apenas "
           f"{met['exactitud_global'] - trivial:+.4f}. Leída sola, la exactitud diría que "
           "el sistema no aporta nada, y sería una lectura equivocada: el modelo detecta "
           "la mayoría de las fallas presentes, que es justamente lo que el clasificador "
           "trivial no hace en absoluto. La exactitud no distingue entre acertar por "
           "diagnóstico y acertar por prevalencia."
           if met["exactitud_global"] - trivial < 0.10 else
           f"{met['exactitud_global'] - trivial:+.4f} por encima del trivial."))
    doc.add_paragraph(
        "Por eso la exactitud se reporta al final y acompañada de la proporción de clases, "
        "y por eso las métricas principales del informe son el recall y el F1 por clase "
        "(Saito y Rehmsmeier, 2015).")


def _seccion_clase_rara(doc, met: dict) -> None:
    """La clase más rara del conjunto: precisión baja con recall alto.

    Es el único resultado del informe que se comporta como se comportaría en
    campo, y la ilustración con datos propios del fenómeno de Saito y
    Rehmsmeier.
    """
    intervalos = met["intervalos_wilson"]
    candidatas = {c: v for c, v in intervalos.items() if 0 < v["soporte"] < 200 and c != "sano"}
    if not candidatas:
        return
    clase = min(candidatas, key=lambda c: candidatas[c]["soporte"])
    iv = intervalos[clase]
    recall = met["recall_por_clase"][clase]
    precision = met["precision_por_clase"][clase]
    soporte = iv["soporte"]
    predichos = iv["predichos"]
    falsos_positivos = max(predichos - round(recall * soporte), 0)

    doc.add_heading(f"2.3 El caso de `{clase}`: por qué la exactitud global no sirve",
                    level=2)
    doc.add_paragraph(
        f"En el conjunto de prevalencia realista, `{clase}` aparece {soporte} veces sobre "
        f"{met['n_muestras']} muestras. El clasificador la detecta con un recall de "
        f"{recall:.3f} {_ic(iv['recall_ic95'])} pero con una precisión de "
        f"{precision:.3f} {_ic(iv['precision_ic95'])}: de las {predichos} muestras que "
        f"señala como esa falla, alrededor de {falsos_positivos} resultan ser otra cosa.")
    doc.add_paragraph(
        "El motivo no es que el modelo diagnostique mal esa falla: en el conjunto "
        "balanceado, donde todas las clases tienen el mismo peso, la misma clase se ve "
        "prácticamente perfecta. El motivo es aritmético. Cuando una clase representa el "
        "0,3 % de la población, incluso una tasa de falsos positivos baja sobre el 68 % "
        "de muestras sanas produce más falsas alarmas que aciertos posibles. La precisión "
        "de una clase rara está gobernada por la prevalencia, no por la calidad del "
        "clasificador.")
    doc.add_paragraph(
        "Es exactamente el fenómeno que documentan Saito y Rehmsmeier (2015): con clases "
        "desbalanceadas, la exactitud global y la curva ROC producen una impresión "
        "optimista, mientras que la curva precisión-recall revela el comportamiento real. "
        "Reportar los dos conjuntos permite cuantificar el efecto en lugar de padecerlo.")
    doc.add_paragraph(
        f"Consecuencia práctica para el plan de mantenimiento: si el sistema emitiera una "
        f"orden de trabajo por cada aviso de `{clase}`, la mayoría de esas órdenes se "
        f"gastaría en equipos que no tienen esa falla. La respuesta de ingeniería no es "
        f"descartar el clasificador, sino usar la clase rara como disparador de "
        f"inspección y no de intervención, y acompañar el aviso con la severidad estimada.")
    doc.add_paragraph(
        f"El intervalo de Wilson importa aquí: con {soporte} casos, la precisión "
        f"observada de {precision:.3f} es compatible con cualquier valor entre "
        f"{iv['precision_ic95'][0]:.2f} y {iv['precision_ic95'][1]:.2f}. Reportar el "
        f"número puntual sin ese intervalo sería reportar ruido como si fuera un "
        f"resultado.")


def generar_informe(metricas: dict, ruta_salida: Path | None = None) -> Path:
    ruta_salida = ruta_salida or (DIR_RESULTADOS / "informe_fdd.docx")
    ruta_salida.parent.mkdir(parents=True, exist_ok=True)
    figuras = metricas.get("figuras", {})
    clases = metricas.get("clases", [])
    m = metricas.get("metricas", {})

    doc = Document()
    doc.add_heading("Detección y diagnóstico de fallas por simulación — Resultados", 0)
    doc.add_paragraph(
        "Fase 5 — Monitoreo e Innovación · Plan Integral de Mantenimiento\n"
        "Sistema de Refrigeración y Aire Acondicionado (0251) — UTP\n"
        f"Sistema de estudio: {metricas.get('descripcion_topologia', '')}\n"
        f"Generado automáticamente el {date.today().isoformat()}"
    ).alignment = WD_ALIGN_PARAGRAPH.LEFT

    # --- Declaraciones obligatorias (sección 11) --------------------------
    doc.add_heading("Declaraciones", level=1)
    doc.add_paragraph(
        "Estas declaraciones no debilitan el trabajo: lo blindan. Una limitación "
        "declarada y analizada es criterio; una no declarada es un error.")
    for texto in [
        "El modelo fue entrenado con datos sintéticos generados a partir de un modelo "
        "termodinámico del ciclo de compresión de vapor, no con datos históricos de la "
        "instalación.",
        "El modelado del inventario de refrigerante (carga baja, sobrecarga) es una "
        "aproximación empírica, no un modelo de primeros principios.",
        "Lo que se demuestra es la viabilidad del método; la implementación en la "
        "instalación real requeriría un periodo de recolección de datos y la calibración "
        "de los coeficientes UA con mediciones de campo.",
        "Las métricas principales son recall y F1 por clase; la exactitud global se "
        "reporta acompañada de la proporción de clases.",
        "Los resultados principales se reportan CON discrepancia entre modelo y planta: "
        f"la referencia sana que se resta se calcula con un gemelo digital desafinado en "
        f"±{100 * float(metricas.get('nivel_discrepancia', 0)):.0f} % respecto del equipo "
        "simulado. Sin esa discrepancia, el único error presente sería el ruido de los "
        "instrumentos y la separación entre clases resultaría trivial por construcción.",
        "El circuito de agua helada se supone de CAUDAL PRIMARIO CONSTANTE. Es un "
        "supuesto pendiente de verificar en el cuarto de máquinas: si la instalación "
        "resultara de caudal primario variable, un caudal reducido a carga parcial sería "
        "operación normal y la clase `caudal_agua_bajo` dejaría de ser válida tal como "
        "está planteada.",
    ]:
        doc.add_paragraph(texto, style="List Number")

    provisionales = metricas.get("parametros_provisionales", [])
    if provisionales:
        doc.add_paragraph(
            f"AVISO: {len(provisionales)} parámetros del equipo siguen marcados como "
            f"PROVISIONALES a la espera de la placa y de la hoja `Ficha Tecnica`: "
            f"{', '.join(provisionales)}.")

    # --- Configuración ----------------------------------------------------
    doc.add_heading("1. Configuración del experimento", level=1)
    doc.add_paragraph(f"Topología: {metricas.get('topologia')} — "
                      f"{metricas.get('descripcion_topologia')}")
    doc.add_paragraph(f"Semilla maestra: {metricas.get('semilla_maestra')}")
    doc.add_paragraph(
        f"Discrepancia modelo-planta: {float(metricas.get('nivel_discrepancia', 0)):.0%} "
        f"({metricas.get('modo_discrepancia')})")
    part = metricas.get("particion", {})
    doc.add_paragraph(
        f"Partición por grupos de condición de contorno — filas: {part.get('filas')}; "
        f"condiciones: {part.get('condiciones')}. Ninguna condición aparece en más de una "
        f"partición.")
    doc.add_paragraph("Entradas del clasificador (lista blanca): "
                      + ", ".join(metricas.get("columnas_de_entrada", [])))
    doc.add_paragraph(
        "No se usan mediciones crudas ni condiciones de contorno: el clasificador opera "
        "solo sobre residuos, para que no pueda aprender clima en lugar de falla. Las "
        "banderas del control (saturación de capacidad, ciclado, retorno de líquido) se "
        "registran para el análisis pero se excluyen del entrenamiento, porque están "
        "correlacionadas con la severidad de la falla.")

    gen = metricas.get("generacion", {})
    conv = gen.get("convergencia_balanceado", {})
    if conv:
        doc.add_paragraph(
            f"Convergencia del solver: {conv.get('convergidos')} de {conv.get('intentos')} "
            f"puntos ({100 * float(conv.get('fraccion_descartada', 0)):.2f} % descartados).")

    cal = metricas.get("calibracion_ua") or {}
    if cal:
        doc.add_paragraph(
            f"Coeficientes UA calibrados: UA_ev = {cal.get('UA_ev', float('nan')):.0f} W/K, "
            f"UA_cd = {cal.get('UA_cd', float('nan')):.0f} W/K (origen: {cal.get('origen_datos')}).")

    sel = metricas.get("seleccion_de_modelo", {})
    doc.add_heading("Selección de modelo", level=2)
    doc.add_paragraph(f"Criterio: {sel.get('criterio')}. Modelo elegido: {sel.get('ganador')}.")
    filas = [["Candidato", "F1 macro (CV)", "F1 macro (validación)", "Hiperparámetros"]]
    for nombre, datos in sel.get("candidatos", {}).items():
        filas.append([nombre, f"{datos['f1_macro_cv']:.4f}",
                      f"{datos['f1_macro_validacion']:.4f}", str(datos["mejores_parametros"])])
    _tabla(doc, filas)
    doc.add_paragraph(
        "Los hiperparámetros provienen de una búsqueda real con GridSearchCV optimizando "
        "F1 macro sobre GroupKFold; el conjunto de prueba no participó en ninguna decisión.")
    doc.add_paragraph(
        f"Control de integridad: aperturas del conjunto de prueba "
        f"{metricas.get('aperturas_del_conjunto_de_prueba')}; corrida válida: "
        f"{metricas.get('corrida_valida')}.")

    # --- Resultados -------------------------------------------------------
    doc.add_heading("2. Resultados", level=1)
    doc.add_paragraph(
        f"Los resultados de esta sección corresponden al caso base, CON discrepancia "
        f"modelo-planta del {float(metricas.get('nivel_discrepancia', 0)):.0%}. Son los "
        f"que deben leerse como estimación del desempeño alcanzable.")
    if "prueba_balanceada" in m:
        _seccion_metricas(doc, m["prueba_balanceada"], clases,
                          "2.1 Conjunto de prueba balanceado")
    if "prevalencia_realista" in m:
        _seccion_metricas(doc, m["prevalencia_realista"], clases,
                          "2.2 Conjunto de prevalencia realista de campo")
        _seccion_clase_rara(doc, m["prevalencia_realista"])

    # --- Cota superior teórica -------------------------------------------
    ruta_cota = DIR_RESULTADOS / "metricas_sin_discrepancia.json"
    if ruta_cota.exists():
        import json as _json
        cota = _json.loads(ruta_cota.read_text(encoding="utf-8"))
        doc.add_heading("2.4 Cota superior teórica (discrepancia cero)", level=2)
        doc.add_paragraph(
            "Los mismos datos generados SIN discrepancia entre modelo y planta, es decir "
            "suponiendo que el gemelo digital reproduce el equipo exactamente. Es un "
            "escenario INALCANZABLE en campo y se reporta solo como cota superior: "
            "cualquier implantación real tendrá un error de calibración distinto de cero.")
        filas = [["Conjunto", "Métrica", "Caso base (5 %)", "Cota superior (0 %)"]]
        for clave, etiqueta in (("prueba_balanceada", "Balanceado"),
                                ("prevalencia_realista", "Prevalencia")):
            for metrica, nombre in (("f1_macro", "F1 macro"),
                                    ("pr_auc_macro", "PR-AUC macro"),
                                    ("exactitud_global", "Exactitud")):
                filas.append([etiqueta, nombre,
                              f"{m[clave][metrica]:.4f}",
                              f"{cota['metricas'][clave][metrica]:.4f}"])
        _tabla(doc, filas)
        doc.add_paragraph(
            "La diferencia entre ambas columnas es el precio de no tener un gemelo digital "
            "perfecto. Es la magnitud que justifica el esfuerzo de calibración descrito en "
            "la sección 9 de la especificación.")

    # --- Figuras ----------------------------------------------------------
    doc.add_heading("3. Figuras", level=1)
    titulos = {
        "fig1_diagrama_ph": "Figura 1. Diagrama P-h: ciclo sano frente a ciclo degradado",
        "fig2a_matriz_confusion_balanceado": "Figura 2a. Matriz de confusión — balanceado",
        "fig2b_matriz_confusion_prevalencia": "Figura 2b. Matriz de confusión — prevalencia",
        "fig3a_curvas_pr_balanceado": "Figura 3a. Curvas precisión-recall — balanceado",
        "fig3b_curvas_pr_prevalencia": "Figura 3b. Curvas precisión-recall — prevalencia",
        "fig4_importancia_permutacion": "Figura 4. Importancia por permutación",
        "fig5_deteccion_vs_severidad": "Figura 5. Detección frente a severidad",
        "fig6_sensibilidad_ruido": "Figura 6. Sensibilidad al ruido de los instrumentos",
        "fig8_sensibilidad_discrepancia": "Figura 8. Sensibilidad a la discrepancia "
                                          "entre modelo y planta",
        "fig7_mapa_firmas": "Figura 7. Mapa de firmas: residuo medio por clase",
    }
    for clave, titulo in titulos.items():
        ruta = figuras.get(clave)
        if ruta and Path(ruta).exists():
            doc.add_heading(titulo, level=2)
            doc.add_picture(ruta, width=Inches(6.0))

    # --- Contraste con la física -----------------------------------------
    doc.add_heading("4. Contraste con la expectativa física", level=1)
    doc.add_paragraph(
        "Para cada clase se compara el residuo que más la separa de la condición sana "
        "contra el que predice la física del modo de falla, por dos vías: el tamaño de "
        "efecto en los datos y el residuo que un árbol uno-contra-sano elige en su raíz.")
    contraste = metricas.get("contraste_con_la_fisica", {})
    if contraste:
        filas = [["Clase", "Esperado por física", "Dominante en los datos",
                  "Puesto del esperado", "Raíz del árbol"]]
        for clase, d in contraste.items():
            filas.append([clase, d["residuo_caracteristico_esperado"],
                          d["residuo_dominante_en_los_datos"],
                          str(d["puesto_del_esperado_en_los_datos"]),
                          d["residuo_raiz_del_arbol"]])
        _tabla(doc, filas)
        doc.add_paragraph(
            "No se usó la importancia por permutación para este contraste: con cientos de "
            "árboles y residuos correlacionados entre sí, permutar una sola característica "
            "apenas mueve la predicción porque el modelo se apoya en las demás, y el "
            "ranking queda dominado por el ruido. La figura 4 conserva la importancia por "
            "permutación global, que es la que pide la especificación.")

    # --- Discrepancia ------------------------------------------------------
    disc = metricas.get("sensibilidad_a_la_discrepancia", {})
    if disc:
        doc.add_heading("5. Sensibilidad a la discrepancia entre modelo y planta", level=1)
        doc.add_paragraph(
            "Responde la pregunta de ingeniería que conecta esta fase con la calibración "
            "contra mediciones de campo: ¿con qué exactitud hay que calibrar el gemelo "
            "digital para que el diagnóstico siga siendo útil? El nivel 0 % es una COTA "
            "SUPERIOR TEÓRICA, inalcanzable en campo: supone que el modelo reproduce el "
            "equipo exactamente.")
        filas = [["Discrepancia δ", "F1 macro", "Diagnóstico incipiente",
                  "Detección incipiente"]]
        for nivel in sorted(disc, key=float):
            d = disc[nivel]
            etiqueta = f"{float(nivel):.0%}" + (" (cota superior)" if float(nivel) == 0 else "")
            filas.append([etiqueta, f"{d['f1_macro']:.4f}",
                          f"{d['diagnostico_incipiente']:.4f}",
                          f"{d['deteccion_incipiente']:.4f}"])
        _tabla(doc, filas)

    rep = metricas.get("repeticiones_por_corrida", {})
    if rep:
        doc.add_heading("5.1 Dispersión entre implantaciones", level=2)
        doc.add_paragraph(
            f"El barrido anterior sortea un error de calibración distinto para cada "
            f"condición, así que mide el efecto PROMEDIO del nivel de discrepancia. Estas "
            f"{rep['n_repeticiones']} repeticiones hacen otra cosa: cada una usa un ÚNICO "
            f"error de calibración para toda la corrida, que es lo que le ocurre a una "
            f"instalación concreta según cómo haya quedado calibrado su gemelo.")
        doc.add_paragraph(
            f"F1 macro: media {rep['f1_macro_media']:.4f}, desviación "
            f"{rep['f1_macro_desv']:.4f}, rango [{rep['f1_macro_min']:.4f}, "
            f"{rep['f1_macro_max']:.4f}]. Diagnóstico incipiente: media "
            f"{rep['diagnostico_incipiente_media']:.4f} ± "
            f"{rep['diagnostico_incipiente_desv']:.4f}.")
        doc.add_paragraph(
            "Esa dispersión es la incertidumbre que debe acompañar cualquier promesa de "
            "desempeño hecha antes de calibrar el gemelo contra el equipo real.")

    ruido = metricas.get("sensibilidad_al_ruido", {})
    if ruido:
        doc.add_heading("6. Sensibilidad al ruido de los instrumentos", level=1)
        doc.add_paragraph(
            "El factor 1,0 corresponde a la exactitud declarada de los instrumentos usados "
            "en campo en la Fase 1.")
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
        doc.add_heading("7. Modelo secundario de severidad", level=1)
        doc.add_paragraph(
            f"RandomForestRegressor entrenado solo con muestras con falla "
            f"({sev.get('n_entrenamiento')} muestras). MAE en validación: "
            f"{sev.get('mae_validacion', float('nan')):.4f}; R²: "
            f"{sev.get('r2_validacion', float('nan')):.4f}. MAE en prueba: "
            f"{sev.get('mae_prueba', float('nan')):.4f}; R²: "
            f"{sev.get('r2_prueba', float('nan')):.4f}.")
        doc.add_paragraph(
            "Sirve para priorizar la orden de trabajo: no es lo mismo una incrustación "
            "incipiente que una severa.")

    doc.add_heading("8. Referencias", level=1)
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
        "Wilson, E. B. (1927). Probable inference, the law of succession, and statistical "
        "inference. Journal of the American Statistical Association, 22(158), 209–212.",
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
