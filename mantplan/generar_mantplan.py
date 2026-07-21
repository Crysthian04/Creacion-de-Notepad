#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generar_mantplan.py — Entregable A del proyecto MantPlan.

Genera `MantPlan.xlsx`: libro Excel sin macros, sin enlaces externos, con
tablas estructuradas y las 10 reglas de negocio implementadas dos veces:

  1. Como FÓRMULAS dentro del libro (XLOOKUP + referencias estructuradas).
  2. Como FUNCIONES PURAS de Python en este módulo (regla_1 … regla_10),
     usadas para construir los datos sintéticos y para verificar que las
     fórmulas del libro producen exactamente los mismos números.

Uso:
    python generar_mantplan.py                        # genera MantPlan.xlsx
    python generar_mantplan.py --salida otro.xlsx
    python generar_mantplan.py --fecha-ancla 2026-07-19
    python generar_mantplan.py --refs compatibles     # variante INDEX/MATCH + rangos A1
    python generar_mantplan.py --resumen              # imprime números esperados

`--refs compatibles` produce el mismo libro pero con INDEX/MATCH y rangos
A1 acotados en lugar de XLOOKUP y referencias estructuradas. Se usa para
verificar el libro con motores de cálculo que aún no implementan XLOOKUP
(p. ej. LibreOffice ≤ 24.2) y sirve también para entornos con Excel 2016.

Requiere: openpyxl  (pip install openpyxl)
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from datetime import date, timedelta

from openpyxl import Workbook
from openpyxl.chart import BarChart, LineChart, Reference, Series
from openpyxl.chart.label import DataLabelList
from openpyxl.chart.marker import Marker
from openpyxl.formatting.rule import CellIsRule, ColorScaleRule, FormulaRule
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from openpyxl.workbook.defined_name import DefinedName
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.worksheet.properties import PageSetupProperties
from openpyxl.worksheet.table import Table, TableStyleInfo

VERSION = "2.3.0"

# Capacidad de las tablas de datos: filas provisionadas con fórmulas para que
# una importación mensual grande no requiera tocar el libro.
CAP_FILAS = 1200

# ══════════════════════════════════════════════════════════════════════════
# 1. PARÁMETROS (Tabla 10) Y CATÁLOGOS SINTÉTICOS
#    Los catálogos son ficticios: el motor jamás depende de sus valores.
# ══════════════════════════════════════════════════════════════════════════

PARAMETROS = [
    # (parametro, valor, descripcion)
    ("nombre_empresa", "Empresa Ejemplo S.A.", "Editable. Solo informativo, no participa en cálculos."),
    ("nombre_planta", "Planta Ejemplo", "Editable. Solo informativo."),
    ("moneda", "USD", "Moneda de los costos."),
    ("horas_jornada", 7, "Horas de trabajo por técnico y día (REGLA-5)."),
    ("factor_productividad", 0.87, "Fracción productiva de la jornada (REGLA-6)."),
    ("turnos", "B1,T1,T2,T3", "Códigos de turno válidos (lista auxiliar a la derecha)."),
    ("codigos_no_disponible", "VAC,X", "Códigos que anulan la disponibilidad (REGLA-5)."),
    ("dias_backlog_max", 30, "Días hacia atrás que siguen siendo plan (REGLAS 3 y 4)."),
    ("dias_backlog_min", -92, "Días hacia adelante (negativo) que entran al plan (REGLA-4)."),
    ("meta_adherencia", 0.95, "Meta de adherencia semanal (REGLA-7)."),
    ("meta_ratio_prev_corr", 0.80, "Meta: fracción preventiva mínima de las HH (REGLA-9)."),
    ("primer_dia_semana", "lunes", "Inicio de semana. La semana ISO (REGLA-2) empieza en lunes."),
    ("ruta_base_checklists", "C:\\MANTPLAN\\checklists\\", "Base para los hipervínculos de la columna link_checklist."),
    ("top_tareas", 5, "Nº de tareas relevantes que lista el correo de EXPORTAR."),
]
# Fila de cada parámetro dentro de la hoja PARAMETROS (encabezado en fila 3).
FILA_PARAM = {p[0]: 4 + i for i, p in enumerate(PARAMETROS)}

HORAS_JORNADA = 7
FACTOR_PRODUCTIVIDAD = 0.87
DIAS_BACKLOG_MAX = 30
DIAS_BACKLOG_MIN = -92
CODIGOS_NO_DISPONIBLE = ("VAC", "X")
TURNOS = ("B1", "T1", "T2", "T3")
DIAS = ("lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo")
SIN_CATALOGO = "(sin catálogo)"

CENTROS_COSTO = [
    # codigo, descripcion, planta, area, sub_area, linea, coordinador
    # sub_area es el nivel jerárquico intermedio área → sub-área → CECO.
    # Vacía = el CECO no subdivide su área y hereda el nombre del área
    # (ver sub_area_efectiva). PRODUCCION y EMPAQUE se dejan SIN sub-área a
    # propósito (prueban la herencia); SERVICIOS se subdivide en 4 sub-áreas.
    ("CC-110", "Línea de producción 1", "PLANTA-1", "PRODUCCION", "", "L1", "Coordinador A"),
    ("CC-120", "Línea de producción 2", "PLANTA-1", "PRODUCCION", "", "L2", "Coordinador A"),
    ("CC-210", "Línea de empaque 3", "PLANTA-1", "EMPAQUE", "", "L3", "Coordinador B"),
    ("CC-220", "Línea de empaque 4", "PLANTA-1", "EMPAQUE", "", "L4", "Coordinador B"),
    ("CC-310", "Generación de vapor", "PLANTA-1", "SERVICIOS", "Vapor", "SG", "Coordinador C"),
    ("CC-311", "Distribución de vapor", "PLANTA-1", "SERVICIOS", "Vapor", "SG", "Coordinador C"),
    ("CC-320", "Torres de enfriamiento", "PLANTA-1", "SERVICIOS", "Refrigeración", "TC", "Coordinador C"),
    ("CC-321", "Chillers", "PLANTA-1", "SERVICIOS", "Refrigeración", "TC", "Coordinador C"),
    ("CC-330", "Planta de CO2", "PLANTA-1", "SERVICIOS", "CO2", "CO", "Coordinador C"),
    ("CC-340", "Aire comprimido", "PLANTA-1", "SERVICIOS", "Aire comprimido", "AC", "Coordinador C"),
]
# Índices dentro de la tupla de CENTROS_COSTO
CECO_AREA, CECO_SUBAREA, CECO_LINEA, CECO_COORD = 3, 4, 5, 6


def sub_area_efectiva(sub_area, area):
    """Herencia: si el CECO no tiene sub-área, hereda el NOMBRE del área
    (nunca el código del CECO). Espejo exacto de la columna calculada."""
    return sub_area if sub_area else area


# Sub-áreas efectivas, agrupadas por área en el orden del catálogo (para los
# desgloses jerárquicos de los reportes).
SUBAREAS_POR_AREA, SUBAREAS = {}, []
for _c in CENTROS_COSTO:
    _se = sub_area_efectiva(_c[CECO_SUBAREA], _c[CECO_AREA])
    SUBAREAS_POR_AREA.setdefault(_c[CECO_AREA], [])
    if _se not in SUBAREAS_POR_AREA[_c[CECO_AREA]]:
        SUBAREAS_POR_AREA[_c[CECO_AREA]].append(_se)
    if _se not in SUBAREAS:
        SUBAREAS.append(_se)

PUESTOS = [
    ("PU-MEC", "MEC", "Puesto mecánico"),
    ("PU-ELE", "ELE", "Puesto eléctrico"),
    ("PU-AUT", "AUT", "Puesto automatización"),
    ("PU-OP", "OP", "Puesto operaciones"),
    ("PU-TER", "TERCERO", "Contratista externo"),
]

ACTIVIDADES = [
    ("ACT-01", "Inspección de rutina", "preventivo"),
    ("ACT-02", "Lubricación programada", "preventivo"),
    ("ACT-03", "Reparación de falla", "correctivo"),
    ("ACT-04", "Análisis predictivo", "predictivo"),
    ("ACT-05", "Certificación legal", "legal"),
]

TIPOS_OT = [
    ("TIPO-P1", "Orden preventiva programada", "preventiva"),
    ("TIPO-P2", "Orden preventiva legal/predictiva", "preventiva"),
    ("TIPO-C1", "Orden correctiva planificada", "correctiva"),
    ("TIPO-C2", "Orden correctiva de emergencia", "correctiva"),
]

ESTADOS_ERP = [
    ("CERR", "Cerrada"),
    ("LIB", "Pendiente"),
    ("EJEC", "Pendiente"),
    ("ABIE", "Pendiente"),
]

TECNICOS = [
    # id, nombre, especialidad, area
    ("TEC-01", "Técnico 01", "MEC", "PRODUCCION"),
    ("TEC-02", "Técnico 02", "MEC", "PRODUCCION"),
    ("TEC-03", "Técnico 03", "MEC", "EMPAQUE"),
    ("TEC-04", "Técnico 04", "MEC", "SERVICIOS"),
    ("TEC-05", "Técnico 05", "ELE", "PRODUCCION"),
    ("TEC-06", "Técnico 06", "ELE", "PRODUCCION"),
    ("TEC-07", "Técnico 07", "ELE", "EMPAQUE"),
    ("TEC-08", "Técnico 08", "AUT", "PRODUCCION"),
    ("TEC-09", "Técnico 09", "AUT", "EMPAQUE"),
    ("TEC-10", "Técnico 10", "OP", "PRODUCCION"),
    ("TEC-11", "Técnico 11", "OP", "EMPAQUE"),
    ("TEC-12", "Técnico 12", "OP", "SERVICIOS"),
]
COORD_POR_AREA = {"PRODUCCION": "Coordinador A", "EMPAQUE": "Coordinador B", "SERVICIOS": "Coordinador C"}
TURNO_POR_TECNICO = {"TEC-02": "T2", "TEC-08": "T3", "TEC-10": "B1"}  # el resto: T1
EQUIPOS_POR_AREA = {
    "PRODUCCION": ["EQ-101", "EQ-102", "EQ-103", "EQ-104", "EQ-105"],
    "EMPAQUE": ["EQ-106", "EQ-107", "EQ-108", "EQ-109"],
    "SERVICIOS": ["EQ-110", "EQ-111", "EQ-112"],
}
ESPECIALIDADES = ("MEC", "ELE", "AUT", "OP", "TERCERO")

CAT_TIPOS = {c: cl for c, _, cl in TIPOS_OT}
CAT_ESTADOS = dict(ESTADOS_ERP)
CAT_CECO = {c[0]: c for c in CENTROS_COSTO}
CAT_PUESTOS = {c: e for c, e, _ in PUESTOS}
CAT_ACTIVIDADES = {c: d for c, d, _ in ACTIVIDADES}

# ══════════════════════════════════════════════════════════════════════════
# 2. LAS 10 REGLAS DE NEGOCIO COMO FUNCIONES PURAS
#    Espejo exacto de las fórmulas del libro. No cambian entre empresas.
# ══════════════════════════════════════════════════════════════════════════


def regla_1_clasificacion(tipo_ot, catalogo_tipos):
    """REGLA-1: clasificación por catálogo TIPOS_OT; jamás códigos hardcodeados."""
    return catalogo_tipos.get(tipo_ot, "sin_clasificar")


def regla_2_semana(fecha):
    """REGLA-2 (v2): 'AAAA-Snn' = año ISO + semana ISO, sin pliegue S53→S1.

    Se usa el AÑO ISO (el del jueves de esa semana), no YEAR(fecha): difieren
    exactamente en los días de cruce diciembre/enero, que es el error a
    evitar (2027-01-01 pertenece a 2026-S53). La semana 53 es legítima en los
    años ISO largos —2026 lo es— y se publica tal cual; el pliegue S53→S1 de
    la especificación original mezclaba fines de diciembre con eneros.
    El formato AAAA-Snn con semana a dos dígitos ordena cronológicamente
    incluso como texto.
    """
    if fecha is None:
        return ""
    iso = fecha.isocalendar()
    return f"{iso[0]}-S{iso[1]:02d}"


def regla_3_estado_backlog(backlog_dias, dias_backlog_max=DIAS_BACKLOG_MAX):
    """REGLA-3: FUTURO / MES CORRIENTE / BACKLOG."""
    if backlog_dias is None:
        return ""
    if backlog_dias < 0:
        return "FUTURO"
    if backlog_dias > dias_backlog_max:
        return "BACKLOG"
    return "MES CORRIENTE"


def regla_4_en_plan(backlog_dias, dias_min=DIAS_BACKLOG_MIN, dias_max=DIAS_BACKLOG_MAX):
    """REGLA-4: pertenencia al plan."""
    if backlog_dias is None:
        return False
    return dias_min < backlog_dias <= dias_max


def regla_5_horas_disponibles(turno, horas_jornada=HORAS_JORNADA, no_disponible=CODIGOS_NO_DISPONIBLE):
    """REGLA-5: horas por técnico y día según turno."""
    if not turno or turno in no_disponible:
        return 0
    return horas_jornada


def regla_6_perfil_hh(hh_disponible, hh_preventiva, hh_correctiva, factor=FACTOR_PRODUCTIVIDAD):
    """REGLA-6: perfil de HH de una celda especialidad × semana."""
    hh_productiva = hh_disponible * factor
    hh_planificada = hh_preventiva + hh_correctiva
    return {
        "hh_disponible": hh_disponible,
        "hh_productiva": hh_productiva,
        "hh_preventiva": hh_preventiva,
        "hh_correctiva": hh_correctiva,
        "hh_planificada": hh_planificada,
        "holgura": hh_productiva - hh_planificada,
        "pct_carga": (hh_planificada / hh_productiva) if hh_productiva else None,
    }


def regla_7_adherencia(ordenes):
    """REGLA-7: adherencia por conteo y por horas (efectivas) sobre órdenes."""
    total = len(ordenes)
    cerradas = sum(1 for o in ordenes if o["estado"] == "Cerrada")
    hh_total = sum(o["horas_efectivas"] or 0 for o in ordenes)
    hh_cerr = sum((o["horas_efectivas"] or 0) for o in ordenes if o["estado"] == "Cerrada")
    return {
        "total": total,
        "cerradas": cerradas,
        "adherencia_conteo": cerradas / total if total else None,
        "hh_total": hh_total,
        "hh_cerradas": hh_cerr,
        "adherencia_horas": hh_cerr / hh_total if hh_total else None,
    }


def regla_8_costos(precio, costo_plan_total):
    """REGLA-8: costo_servicio = precio; materiales = MAX(0, plan_total − precio)."""
    servicio = precio or 0
    materiales = max(0, (costo_plan_total or 0) - servicio)
    return servicio, materiales, servicio + materiales


def regla_9_ratio(hh_preventiva, hh_correctiva):
    """REGLA-9: ratio correctivo/preventivo y % correctivo del total."""
    ratio = hh_correctiva / hh_preventiva if hh_preventiva else None
    total = hh_preventiva + hh_correctiva
    pct_corr = hh_correctiva / total if total else None
    return ratio, pct_corr


def regla_10_validacion(ordenes, ejecucion):
    """REGLA-10: diagnóstico de importación. Reporta, nunca bloquea."""
    ids = [o["id_operacion"] for o in ordenes]
    vistos = {}
    for i in ids:
        vistos[i] = vistos.get(i, 0) + 1
    ids_ejec = {e["id_operacion"] for e in ejecucion}
    return {
        "duplicadas": sum(n for n in vistos.values() if n > 1),
        "sin_fecha": sum(1 for o in ordenes if o["fecha_inicio"] is None),
        "sin_horas": sum(1 for o in ordenes if o["horas_estimadas"] is None),
        "ceco_desconocido": sum(1 for o in ordenes if o["centro_costo"] not in CAT_CECO),
        "puesto_desconocido": sum(1 for o in ordenes if o["puesto_trabajo"] not in CAT_PUESTOS),
        "actividad_desconocida": sum(1 for o in ordenes if o["cod_actividad"] not in CAT_ACTIVIDADES),
        "tipo_ot_desconocido": sum(1 for o in ordenes if o["tipo_ot"] not in CAT_TIPOS),
        "ejecucion_sin_par": sum(1 for e in ejecucion if e["id_operacion"] not in set(ids)),
        "ordenes_sin_par": sum(1 for i in ids if i not in ids_ejec),
    }


# ══════════════════════════════════════════════════════════════════════════
# 3. DATOS SINTÉTICOS DETERMINISTAS (200 órdenes, 12 técnicos, 4 semanas)
#    Números redondos, pensados para verificarse a mano.
# ══════════════════════════════════════════════════════════════════════════

# Presupuesto de horas planificadas por especialidad y semana: (preventiva, correctiva)
PRESUPUESTO_PLAN = {
    "MEC": [(80, 20), (80, 25), (80, 20), (70, 14)],
    "ELE": [(60, 15), (65, 20), (60, 10), (50, 10)],
    "AUT": [(40, 10), (45, 10), (35, 7), (30, 6)],
    "OP": [(30, 8), (36, 9), (28, 7), (24, 6)],
}
PRESUPUESTO_TERCERO = {1: 16, 2: 12}  # semana → horas preventivas contratadas
TARIFA = {"preventiva": 25, "correctiva": 40}  # USD/hora → costo_plan redondo


def partir_horas(total):
    """Parte un total de horas en órdenes de tamaño 10/8/6 + resto (determinista)."""
    ciclo = (10, 8, 6)
    partes, s, i = [], 0, 0
    while total - s >= 12:
        partes.append(ciclo[i % 3])
        s += ciclo[i % 3]
        i += 1
    if total - s > 0:
        partes.append(total - s)
    return partes


def _tecnicos_de(esp):
    return [t for t in TECNICOS if t[2] == esp]


def generar_datos(hoy):
    """Construye ORDENES, EJECUCION, TECNICOS y ASIGNACIONES sintéticos."""
    lunes = hoy - timedelta(days=hoy.weekday())
    lunes_sem = [lunes + timedelta(weeks=k) for k in (-1, 0, 1, 2)]
    semanas = [regla_2_semana(d) for d in lunes_sem]

    # --- ASIGNACIONES: 4 semanas × 12 técnicos × 7 días = 336 filas -------
    asignaciones = []
    for si, sem in enumerate(semanas):
        for tid, nombre, esp, area in TECNICOS:
            for di, dia in enumerate(DIAS):
                if di >= 5:
                    turno = ""  # fin de semana sin programar
                elif tid == "TEC-04" and si == 2:
                    turno = "VAC"  # vacaciones toda la semana (demo REGLA-5)
                elif tid == "TEC-07" and si == 1 and dia == "viernes":
                    turno = "X"  # ausencia puntual (demo REGLA-5)
                else:
                    turno = TURNO_POR_TECNICO.get(tid, "T1")
                asignaciones.append({"semana": sem, "dia": dia, "tecnico": nombre,
                                     "area": area, "especialidad": esp, "turno": turno})

    # --- ORDENES ----------------------------------------------------------
    ordenes = []
    consecutivo = [0]

    def nueva(fecha, horas, esp, clasif, grupo, si=None, dia_idx=None, tecnico=None,
              ceco=None, tipo=None, act=None, orden_id=None, operacion="0010",
              desc_op=None):
        consecutivo[0] += 1
        oid = orden_id or f"OT-{consecutivo[0]:06d}"
        ceco = ceco or "CC-110"
        area = CAT_CECO[ceco][3] if ceco in CAT_CECO else "PRODUCCION"
        equipos = EQUIPOS_POR_AREA[area]
        equipo = equipos[consecutivo[0] % len(equipos)]
        if tipo is None:
            tipo = ("TIPO-P1", "TIPO-P2")[consecutivo[0] % 2] if clasif == "preventiva" \
                else ("TIPO-C1", "TIPO-C2")[consecutivo[0] % 2]
        if act is None:
            act = ("ACT-01", "ACT-02", "ACT-04")[consecutivo[0] % 3] if clasif == "preventiva" else "ACT-03"
        tarifa = TARIFA["preventiva" if clasif == "preventiva" else "correctiva"]
        o = {
            "orden": oid, "operacion": operacion,
            "descripcion_general": f"{CAT_ACTIVIDADES.get(act, 'Actividad')} — {equipo}",
            "descripcion_operacion": desc_op or f"{CAT_ACTIVIDADES.get(act, 'Actividad')} en {equipo}",
            "equipo": equipo, "centro_costo": ceco,
            "puesto_trabajo": {"MEC": "PU-MEC", "ELE": "PU-ELE", "AUT": "PU-AUT",
                               "OP": "PU-OP", "TERCERO": "PU-TER"}.get(esp, esp),
            "cod_actividad": act, "tipo_ot": tipo,
            "fecha_inicio": fecha, "horas_estimadas": horas,
            "costo_plan": (horas or 0) * tarifa,
            "tecnico_asignado": tecnico or "",
            "permiso_requerido": "", "bloqueo_energia": "", "link_checklist": "",
            "observaciones": "",
            "_grupo": grupo, "_si": si, "_clasif": clasif,
        }
        if clasif == "preventiva" and grupo == "plan":
            o["link_checklist"] = f"{act}.pdf"
        if clasif == "correctiva" and grupo == "plan" and consecutivo[0] % 4 == 0:
            o["permiso_requerido"] = "PT-CALIENTE"
            o["bloqueo_energia"] = "LOTO"
        ordenes.append(o)
        return o

    # Órdenes del plan (semanas S-1 … S+2)
    cecos_por_esp = {"MEC": ["CC-110", "CC-210", "CC-310"], "ELE": ["CC-120", "CC-220"],
                     "AUT": ["CC-110", "CC-220"], "OP": ["CC-120", "CC-210", "CC-320"]}
    idx_plan = 0
    for esp, filas in PRESUPUESTO_PLAN.items():
        tecs = _tecnicos_de(esp)
        for si, (hh_prev, hh_corr) in enumerate(filas):
            disponibles = [t for t in tecs if not (t[0] == "TEC-04" and si == 2)]
            for clasif, total in (("preventiva", hh_prev), ("correctiva", hh_corr)):
                for h in partir_horas(total):
                    dia_idx = idx_plan % 5
                    tec = disponibles[idx_plan % len(disponibles)]
                    if tec[0] == "TEC-07" and si == 1 and dia_idx == 4:
                        dia_idx = 3  # evitar el día de ausencia 'X'
                    nombre_tec = "" if idx_plan % 12 == 11 else tec[1]  # algunas sin técnico
                    nueva(lunes_sem[si] + timedelta(days=dia_idx), h, esp, clasif, "plan",
                          si=si, dia_idx=dia_idx, tecnico=nombre_tec,
                          ceco=cecos_por_esp[esp][idx_plan % len(cecos_por_esp[esp])])
                    idx_plan += 1
    # Trabajos de terceros (sin técnico interno)
    for si, horas in PRESUPUESTO_TERCERO.items():
        for j, h in enumerate(partir_horas(horas)):
            nueva(lunes_sem[si] + timedelta(days=j % 5), h, "TERCERO", "preventiva",
                  "plan_tercero", si=si, ceco="CC-310", act="ACT-05", tipo="TIPO-P2")

    # Conflicto deliberado: una orden MEC de la semana en que TEC-04 está de
    # vacaciones queda asignada a él → HHD = −HHA (demo de indisponibilidad)
    for o in ordenes:
        if (o["_grupo"] == "plan" and o["_si"] == 2
                and o["puesto_trabajo"] == "PU-MEC" and o["tecnico_asignado"]):
            o["tecnico_asignado"] = "Técnico 04"
            o["observaciones"] = "Demo: asignada a técnico de vacaciones (HHD = −HHA)"
            break

    # Ajustes manuales de horas (v2.1: viven en tblAjustes, con clave).
    # Aquí solo se eligen las órdenes; la lista de ajustes se arma al final,
    # cuando ya existen los id_operacion.
    aj1 = next(o for o in ordenes if o["_grupo"] == "plan" and o["_si"] == 1
               and o["tecnico_asignado"] == "Técnico 01" and o["horas_estimadas"] == 8)
    aj1["observaciones"] = "Ajuste 8 → 12 h en hoja AJUSTES"
    aj2 = next(o for o in ordenes if o["_grupo"] == "plan" and o["_si"] == 1
               and o["puesto_trabajo"] == "PU-ELE" and o["horas_estimadas"] == 6)
    aj2["observaciones"] = "Ajuste 6 → 4 h en hoja AJUSTES"

    # Segunda operación 0020 para 4 órdenes del plan (demo de operaciones)
    for o in [x for x in ordenes if x["_grupo"] == "plan"][::40][:4]:
        consecutivo[0] += 1
        extra = dict(o)
        extra.update({"operacion": "0020", "horas_estimadas": 2, "horas_ajustadas": None,
                      "costo_plan": 2 * TARIFA[o["_clasif"] if o["_clasif"] in TARIFA else "preventiva"],
                      "descripcion_operacion": f"Segunda operación — {o['equipo']}",
                      "link_checklist": "", "permiso_requerido": "", "bloqueo_energia": "",
                      "observaciones": ""})
        ordenes.append(extra)

    # Backlog pendiente (envejecimiento por tramos)
    esp_ciclo = ["MEC", "ELE", "AUT", "OP"]
    for k, (dias_atras, cuantas) in enumerate([(45, 8), (75, 6), (100, 6), (120, 4), (150, 4)]):
        for j in range(cuantas):
            esp = esp_ciclo[(k + j) % 4]
            clasif = "preventiva" if j % 4 == 3 else "correctiva"
            nueva(hoy - timedelta(days=dias_atras), (4, 6, 8)[j % 3], esp, clasif, "backlog",
                  ceco=CENTROS_COSTO[(k + j) % len(CENTROS_COSTO)][0])

    # Histórico cerrado (alimenta COSTOS y EQUIPOS_CRITICOS). Recorre los 10
    # CECOs para dar datos a todas las sub-áreas de SERVICIOS.
    for j in range(15):
        esp = esp_ciclo[j % 4]
        clasif = "preventiva" if j % 2 == 0 else "correctiva"
        nueva(hoy - timedelta(days=40 + j * 7), (4, 6, 8)[j % 3], esp, clasif, "historico",
              ceco=CENTROS_COSTO[j % len(CENTROS_COSTO)][0])

    # Futuras lejanas (REGLA-3 FUTURO y límite dias_backlog_min de REGLA-4)
    for j in range(3):
        nueva(hoy + timedelta(days=40), 6, "MEC", "preventiva", "futuro")
    for j in range(2):
        nueva(hoy + timedelta(days=100), 6, "ELE", "preventiva", "futuro")
    # Cruce de fin de año (REGLA-2 v2): tres órdenes que deben caer en semanas
    # DISTINTAS y con año ISO correcto. 2026 es un año ISO de 53 semanas:
    #   29-dic-2026 → 2026-S53 · 1-ene-2027 → 2026-S53 (año ISO ≠ YEAR)
    #   5-ene-2027  → 2027-S01
    nueva(date(hoy.year, 12, 29), 4, "AUT", "preventiva", "futuro")
    nueva(date(hoy.year + 1, 1, 1), 4, "MEC", "preventiva", "futuro")
    nueva(date(hoy.year + 1, 1, 5), 4, "ELE", "preventiva", "futuro")

    # Casos borde para VALIDACION (REGLA-10) — se importan igual, solo se reportan
    dup = nueva(hoy - timedelta(days=50), 6, "MEC", "correctiva", "edge", orden_id="OT-000900")
    ordenes.append({**dup})  # id_operacion duplicado (2 filas)
    consecutivo[0] += 1
    nueva(None, 4, "ELE", "correctiva", "edge", orden_id="OT-000901")          # sin fecha
    nueva(None, 6, "MEC", "preventiva", "edge", orden_id="OT-000902")          # sin fecha
    nueva(hoy - timedelta(days=55), None, "AUT", "correctiva", "edge", orden_id="OT-000903")   # sin horas
    nueva(hoy - timedelta(days=55), None, "OP", "correctiva", "edge", orden_id="OT-000904")    # sin horas
    nueva(hoy - timedelta(days=60), 4, "MEC", "correctiva", "edge", orden_id="OT-000905", tipo="TIPO-X9")
    nueva(hoy - timedelta(days=60), 4, "ELE", "correctiva", "edge", orden_id="OT-000906", tipo="TIPO-X9")
    nueva(hoy - timedelta(days=62), 4, "MEC", "correctiva", "edge", orden_id="OT-000907", ceco="CC-999")
    o908 = nueva(hoy - timedelta(days=62), 4, "ELE", "correctiva", "edge", orden_id="OT-000908")
    o908["puesto_trabajo"] = "PU-XXX"
    o909 = nueva(hoy - timedelta(days=64), 4, "AUT", "correctiva", "edge", orden_id="OT-000909")
    o909["cod_actividad"] = "ACT-99"

    # Relleno determinista hasta exactamente 200 órdenes
    k = 0
    while len(ordenes) < 200:
        nueva(hoy - timedelta(days=35 + k), 2, "ELE", "correctiva", "backlog", ceco="CC-220")
        k += 1
    assert len(ordenes) == 200, f"se generaron {len(ordenes)} órdenes, no 200"

    for o in ordenes:
        o["id_operacion"] = o["orden"] + (o["operacion"] or "0010")

    # tblAjustes de ejemplo: 2 aplicados + 1 duplicado + 1 huérfano (demos de
    # los chequeos de VALIDACION; ante duplicados gana la primera fila).
    ajustes = [
        {"id_operacion": aj1["id_operacion"], "horas_ajustadas": 12,
         "motivo": "Alcance real mayor al estándar del ERP", "fecha_ajuste": hoy},
        {"id_operacion": aj2["id_operacion"], "horas_ajustadas": 4,
         "motivo": "Alcance menor: tarea parcial", "fecha_ajuste": hoy},
        {"id_operacion": aj1["id_operacion"], "horas_ajustadas": 14,
         "motivo": "Duplicado (demo): se ignora, gana la primera fila",
         "fecha_ajuste": hoy},
        {"id_operacion": "OT-0009990010", "horas_ajustadas": 6,
         "motivo": "Huérfano (demo): la orden no existe en ORDENES",
         "fecha_ajuste": hoy},
    ]

    # --- EJECUCION --------------------------------------------------------
    ejecucion = []
    prioridades = ("1-ALTA", "2-MEDIA", "3-BAJA")
    instalacion = ("OPERATIVO", "PARADO")
    usuario = {"CERR": "CERRADA", "LIB": "LIBERADA", "EJEC": "EN EJECUCION", "ABIE": "ABIERTA"}
    ya = set()
    edge_regla8 = []  # órdenes con precio > costo_plan_total (materiales = 0)

    for j, o in enumerate(ordenes):
        if o["id_operacion"] in ya:
            continue  # el duplicado comparte una sola fila de ejecución
        g, si = o["_grupo"], o["_si"]
        if g in ("plan", "plan_tercero"):
            if si == 0:
                estado = "LIB" if j % 12 == 0 else "CERR"
            elif si == 1:
                estado = "CERR" if j % 2 == 0 else "EJEC"
            else:
                estado = "LIB" if j % 2 == 0 else None
        elif g == "backlog":
            estado = ("EJEC", "ABIE")[j % 2]
        elif g == "historico":
            estado = "CERR"
        elif g == "edge" and o["fecha_inicio"] is not None:
            estado = "EJEC"
        else:
            estado = None  # futuras y órdenes sin fecha quedan sin par → "Pendiente"
        if estado is None:
            continue
        plan = o["costo_plan"] or 0
        precio = plan * 2 // 5  # 40 % servicio, 60 % materiales — números redondos
        if g == "historico" and j % 7 == 0 and len(edge_regla8) < 2:
            precio = plan + 100  # demo REGLA-8: MAX(0, plan − precio) = 0
            edge_regla8.append(o["id_operacion"])
        ejecucion.append({
            "orden": o["orden"], "operacion": o["operacion"],
            "id_operacion": o["id_operacion"],
            "estado_sistema": estado, "prioridad": prioridades[j % 3],
            "estado_instalacion": instalacion[j % 2],
            "precio": precio, "costo_real": plan if estado == "CERR" else 0,
            "costo_plan_total": plan, "estado_usuario": usuario[estado],
        })
        ya.add(o["id_operacion"])

    # Registros de EJECUCION sin par en ORDENES (demo REGLA-10)
    for n in ("OT-000990", "OT-000991", "OT-000992"):
        ejecucion.append({"orden": n, "operacion": "0010", "id_operacion": n + "0010",
                          "estado_sistema": "LIB", "prioridad": "2-MEDIA",
                          "estado_instalacion": "OPERATIVO", "precio": 50,
                          "costo_real": 0, "costo_plan_total": 150, "estado_usuario": "LIBERADA"})

    return {"hoy": hoy, "lunes_sem": lunes_sem, "semanas": semanas,
            "ordenes": ordenes, "ejecucion": ejecucion, "asignaciones": asignaciones,
            "ajustes": ajustes, "edge_regla8": edge_regla8}


# ══════════════════════════════════════════════════════════════════════════
# 4. VALORES ESPERADOS (motor Python aplicado a los datos)
#    Es lo que las fórmulas del libro DEBEN producir.
# ══════════════════════════════════════════════════════════════════════════


def calcular_esperado(datos):
    hoy = datos["hoy"]
    ejec_por_id = {}
    for e in datos["ejecucion"]:
        ejec_por_id.setdefault(e["id_operacion"], e)  # primera coincidencia, como XLOOKUP
    asig_por_clave = {}
    for a in datos["asignaciones"]:
        asig_por_clave.setdefault((a["semana"], a["dia"], a["tecnico"]), a)
        a["horas_disponibles"] = regla_5_horas_disponibles(a["turno"])
        a["coordinador"] = COORD_POR_AREA[a["area"]]
    aj_por_id = {}
    for a in datos["ajustes"]:
        aj_por_id.setdefault(a["id_operacion"], a["horas_ajustadas"])  # gana la primera

    enriquecidas = []
    for o in datos["ordenes"]:
        f = o["fecha_inicio"]
        e = ejec_por_id.get(o["id_operacion"])
        backlog = (hoy - f).days if f else None
        ceco = CAT_CECO.get(o["centro_costo"])
        servicio, materiales, total = regla_8_costos(
            e["precio"] if e else 0, e["costo_plan_total"] if e else 0)
        semana = regla_2_semana(f)
        dia = DIAS[f.weekday()] if f else ""
        tec = o["tecnico_asignado"]
        asig = asig_por_clave.get((semana, dia, tec)) if tec else None
        aj = aj_por_id.get(o["id_operacion"])
        efectivas = aj if aj is not None else (
            o["horas_estimadas"] if o["horas_estimadas"] is not None else "")
        enriquecidas.append({**o,
            "horas_efectivas": efectivas,
            "estado": CAT_ESTADOS.get(e["estado_sistema"], "Pendiente") if e else "Pendiente",
            "semana": semana, "anio": f.year if f else "", "mes": f.month if f else "",
            "dia_semana": dia,
            "clasificacion": regla_1_clasificacion(o["tipo_ot"], CAT_TIPOS),
            "linea": ceco[CECO_LINEA] if ceco else SIN_CATALOGO,
            "area": ceco[CECO_AREA] if ceco else SIN_CATALOGO,
            "sub_area": sub_area_efectiva(ceco[CECO_SUBAREA], ceco[CECO_AREA])
            if ceco else SIN_CATALOGO,
            "coordinador": ceco[CECO_COORD] if ceco else SIN_CATALOGO,
            "especialidad": CAT_PUESTOS.get(o["puesto_trabajo"], SIN_CATALOGO),
            "actividad": CAT_ACTIVIDADES.get(o["cod_actividad"], SIN_CATALOGO),
            "backlog_dias": backlog if backlog is not None else "",
            "estado_backlog": regla_3_estado_backlog(backlog),
            "en_plan": regla_4_en_plan(backlog),
            "turno_asignado": (asig["turno"] if asig else "") if tec else "",
            "costo_servicio": servicio, "costo_materiales": materiales, "costo_total": total,
        })

    # HHA/HHD: agregado por técnico × semana × día, repetido en cada fila
    hha_por_dia = {}
    for o in enriquecidas:
        if o["tecnico_asignado"]:
            k = (o["tecnico_asignado"], o["semana"], o["dia_semana"])
            hha_por_dia[k] = hha_por_dia.get(k, 0) + (o["horas_efectivas"] or 0)
    for o in enriquecidas:
        if o["tecnico_asignado"]:
            o["HHA"] = hha_por_dia[(o["tecnico_asignado"], o["semana"], o["dia_semana"])]
            # HHD contra la disponibilidad real del técnico ese día (REGLA-5):
            # sin asignación o con VAC/X la disponibilidad es 0 y HHD = −HHA.
            asig = asig_por_clave.get((o["semana"], o["dia_semana"], o["tecnico_asignado"]))
            disp = asig["horas_disponibles"] if asig else 0
            o["HHD"] = FACTOR_PRODUCTIVIDAD * disp - o["HHA"]
        else:
            o["HHA"] = ""
            o["HHD"] = ""

    # Serie cronológica de semanas presentes en los datos (capacidad: 60).
    # Las etiquetas AAAA-Snn ordenan igual como texto que como fecha.
    fechas = [o["fecha_inicio"] for o in datos["ordenes"] if o["fecha_inicio"]]
    lunes_ini = min(fechas) - timedelta(days=min(fechas).weekday())
    lunes_fin = max(fechas) - timedelta(days=max(fechas).weekday())
    serie_semanas, lun = [], lunes_ini
    while lun <= lunes_fin and len(serie_semanas) < 60:
        serie_semanas.append(regla_2_semana(lun))
        lun += timedelta(weeks=1)
    semanas_con_datos = {o["semana"] for o in enriquecidas if o["semana"]}

    perfil = {}
    for esp in ESPECIALIDADES:
        for sem in serie_semanas:
            hh_disp = sum(a["horas_disponibles"] for a in datos["asignaciones"]
                          if a["especialidad"] == esp and a["semana"] == sem)
            hh_prev = sum(o["horas_efectivas"] or 0 for o in enriquecidas
                          if o["especialidad"] == esp and o["semana"] == sem
                          and o["clasificacion"] == "preventiva")
            hh_corr = sum(o["horas_efectivas"] or 0 for o in enriquecidas
                          if o["especialidad"] == esp and o["semana"] == sem
                          and o["clasificacion"] == "correctiva")
            perfil[(esp, sem)] = regla_6_perfil_hh(hh_disp, hh_prev, hh_corr)

    adherencia = {}
    for dim, valores in (("semana", serie_semanas),
                         ("area", [a for a in COORD_POR_AREA]),
                         ("sub_area", SUBAREAS),
                         ("especialidad", list(ESPECIALIDADES)),
                         ("coordinador", sorted(set(COORD_POR_AREA.values()))),
                         ("tecnico_asignado", [t[1] for t in TECNICOS]),
                         ("clasificacion", ["preventiva", "correctiva", "sin_clasificar"])):
        for v in valores:
            adherencia[(dim, v)] = regla_7_adherencia([o for o in enriquecidas if o[dim] == v])

    ratio9 = {}
    for sem in serie_semanas:
        prev = sum(o["horas_efectivas"] or 0 for o in enriquecidas
                   if o["semana"] == sem and o["clasificacion"] == "preventiva")
        corr = sum(o["horas_efectivas"] or 0 for o in enriquecidas
                   if o["semana"] == sem and o["clasificacion"] == "correctiva")
        ratio9[sem] = (prev, corr, *regla_9_ratio(prev, corr))

    tramos = [("0-30", 0, 30), ("31-60", 31, 60), ("61-90", 61, 90), (">90", 91, 10**6)]
    backlog_aging = {}
    for nombre, a, b in tramos:
        filas = [o for o in enriquecidas if o["estado"] == "Pendiente"
                 and o["backlog_dias"] != "" and a <= o["backlog_dias"] <= b]
        backlog_aging[nombre] = (len(filas), sum(o["horas_efectivas"] or 0 for o in filas))

    meses = sorted({(o["anio"], o["mes"]) for o in enriquecidas if o["mes"] != ""})
    costos = {}
    for anio, mes in meses:
        for area in COORD_POR_AREA:
            filas = [o for o in enriquecidas if o["anio"] == anio and o["mes"] == mes and o["area"] == area]
            costos[(anio, mes, area)] = (sum(o["costo_plan"] or 0 for o in filas),
                                         sum(o["costo_total"] for o in filas))
    costos_sub = {}       # costo_total real por (anio, mes, sub_area)
    for anio, mes in meses:
        for sa in SUBAREAS:
            filas = [o for o in enriquecidas if o["anio"] == anio and o["mes"] == mes
                     and o["sub_area"] == sa]
            costos_sub[(anio, mes, sa)] = sum(o["costo_total"] for o in filas)
    # Backlog (nº órdenes pendientes) por sub-área × tramo, para verificar
    backlog_sub = {}
    for sa in SUBAREAS:
        for nombre, a, b in tramos:
            backlog_sub[(sa, nombre)] = sum(
                1 for o in enriquecidas if o["sub_area"] == sa and o["estado"] == "Pendiente"
                and o["backlog_dias"] != "" and a <= o["backlog_dias"] <= b)

    equipos_tot = {}
    for o in enriquecidas:
        equipos_tot[o["equipo"]] = equipos_tot.get(o["equipo"], 0) + o["costo_total"]
    equipos_orden = sorted(equipos_tot, key=lambda q: -equipos_tot[q])

    # Carga y capacidad semanal por técnico (zona de datos del gráfico de carga)
    carga_tecnicos, capacidad_tecnicos = {}, {}
    for sem in datos["semanas"]:
        for _tid, nombre, _esp, _area in TECNICOS:
            carga_tecnicos[(sem, nombre)] = sum(
                o["horas_efectivas"] or 0 for o in enriquecidas
                if o["tecnico_asignado"] == nombre and o["semana"] == sem)
            capacidad_tecnicos[(sem, nombre)] = FACTOR_PRODUCTIVIDAD * sum(
                a["horas_disponibles"] for a in datos["asignaciones"]
                if a["tecnico"] == nombre and a["semana"] == sem)

    # Estado esperado de cada fila de tblAjustes (aplicado/duplicado/huérfano)
    ids_ordenes = {o["id_operacion"] for o in datos["ordenes"]}
    est_por_id = {}
    for o in datos["ordenes"]:
        est_por_id.setdefault(o["id_operacion"], o["horas_estimadas"])
    desc_por_id = {}
    for o in datos["ordenes"]:
        desc_por_id.setdefault(o["id_operacion"], o["descripcion_operacion"])
    ajustes_esperado, aplicados = [], set()
    for a in datos["ajustes"]:
        i = a["id_operacion"]
        if i not in ids_ordenes:
            estado_a, desv = "huérfano", ""
        elif i in aplicados:
            estado_a, desv = "duplicado (se ignora)", ""
        else:
            aplicados.add(i)
            est = est_por_id[i]
            estado_a = "aplicado"
            desv = a["horas_ajustadas"] - est if est is not None else ""
        ajustes_esperado.append({
            "estado_ajuste": estado_a, "desviacion_h": desv,
            "descripcion": desc_por_id.get(i, "(no encontrada)")})
    validacion_extra = {
        "ajustadas": sum(1 for o in datos["ordenes"] if o["id_operacion"] in aj_por_id),
        "desviacion_horas": sum(x["desviacion_h"] for x in ajustes_esperado
                                if x["desviacion_h"] != ""),
        "huerfanos": sum(1 for a in datos["ajustes"]
                         if a["id_operacion"] not in ids_ordenes),
        "duplicados_ajustes": sum(1 for a in datos["ajustes"]
                                  if sum(1 for b in datos["ajustes"]
                                         if b["id_operacion"] == a["id_operacion"]) > 1),
    }

    # --- Correo esperado de EXPORTAR (filtro por defecto: semana=semanas[1],
    #     turno y coordinador = "(todos)") --------------------------------
    def exportar_esperado(sem, top=5):
        scope = [o for o in enriquecidas if o["semana"] == sem and o["en_plan"] is True]
        hh_total = sum(o["horas_efectivas"] or 0 for o in scope)
        hh_prev = sum(o["horas_efectivas"] or 0 for o in scope if o["clasificacion"] == "preventiva")
        hh_corr = sum(o["horas_efectivas"] or 0 for o in scope if o["clasificacion"] == "correctiva")
        tecs = {t[1] for t in TECNICOS}
        n_tec = len({o["tecnico_asignado"] for o in scope
                     if o["tecnico_asignado"] in tecs})
        por_tec = {}
        for _tid, nombre, _e, _a in TECNICOS:
            hha = sum(o["horas_efectivas"] or 0 for o in scope if o["tecnico_asignado"] == nombre)
            cap = FACTOR_PRODUCTIVIDAD * sum(a["horas_disponibles"] for a in datos["asignaciones"]
                                             if a["tecnico"] == nombre and a["semana"] == sem)
            por_tec[nombre] = (hha, cap, hha > cap + 1e-4)
        sobre = [n for n, (h, c, ov) in por_tec.items() if ov]
        pend = [o for o in scope if o["estado"] == "Pendiente"]
        pend_orden = sorted(enumerate(pend), key=lambda kv: (-(kv[1]["horas_efectivas"] or 0), kv[0]))
        top_list = [o for _, o in pend_orden[:top]]
        return {"semana": sem, "n_ord": len(scope), "hh_total": hh_total,
                "hh_prev": hh_prev, "hh_corr": hh_corr, "n_tec": n_tec,
                "por_tec": por_tec, "sobreasignados": sobre, "n_top": len(pend),
                "top": top_list}

    exportar = exportar_esperado(datos["semanas"][1])

    return {"ordenes": enriquecidas, "perfil": perfil, "adherencia": adherencia,
            "ratio9": ratio9, "backlog_aging": backlog_aging, "meses": meses,
            "costos": costos, "equipos_orden": equipos_orden, "equipos_tot": equipos_tot,
            "carga_tecnicos": carga_tecnicos, "capacidad_tecnicos": capacidad_tecnicos,
            "serie_semanas": serie_semanas, "semanas_con_datos": semanas_con_datos,
            "validacion_extra": validacion_extra, "ajustes_esperado": ajustes_esperado,
            "exportar": exportar, "exportar_fn": exportar_esperado,
            "costos_sub": costos_sub, "backlog_sub": backlog_sub,
            "validacion": regla_10_validacion(datos["ordenes"], datos["ejecucion"])}


# ══════════════════════════════════════════════════════════════════════════
# 5. MOTOR DE REFERENCIAS: estructuradas (Excel) o A1 acotadas (verificación)
# ══════════════════════════════════════════════════════════════════════════


@dataclass
class Tabla:
    nombre: str
    hoja: str
    fila_enc: int
    campos: list
    n: int = 0

    @property
    def fila_ini(self):
        return self.fila_enc + 1

    @property
    def fila_fin(self):
        return self.fila_enc + self.n

    def letra(self, campo):
        return get_column_letter(self.campos.index(campo) + 1)

    @property
    def ref(self):
        return f"A{self.fila_enc}:{get_column_letter(len(self.campos))}{self.fila_fin}"


class Refs:
    """Traduce (tabla, campo) a referencias estructuradas o a rangos A1 acotados.

    Prohibido en ambos modos: OFFSET, INDIRECT y columnas completas (A:A).
    """

    def __init__(self, modo, tablas):
        self.modo = modo
        self.t = tablas

    def col(self, tabla, campo):
        tb = self.t[tabla]
        if self.modo == "estructuradas":
            return f"{tabla}[{campo}]"
        letra = tb.letra(campo)
        return f"'{tb.hoja}'!${letra}${tb.fila_ini}:${letra}${tb.fila_fin}"

    def this(self, tabla, campo, fila):
        if self.modo == "estructuradas":
            return f"{tabla}[[#This Row],[{campo}]]"
        return f"${self.t[tabla].letra(campo)}{fila}"

    def busca(self, expr, tabla, campo_clave, campo_valor, defecto):
        """XLOOKUP con si_no_encontrado, o su equivalente INDEX/MATCH."""
        if self.modo == "estructuradas":
            return (f"_xlfn.XLOOKUP({expr},{self.col(tabla, campo_clave)},"
                    f"{self.col(tabla, campo_valor)},{defecto})")
        return self.busca_im(expr, tabla, campo_clave, campo_valor, defecto)

    def busca_im(self, expr, tabla, campo_clave, campo_valor, defecto):
        """Variante INDEX/MATCH (hoja _COMPATIBILIDAD y modo compatibles)."""
        return (f"IFERROR(INDEX({self.col(tabla, campo_valor)},"
                f"MATCH({expr},{self.col(tabla, campo_clave)},0)),{defecto})")


# v2: las 12 columnas importadas quedan contiguas desde A (pegado en un solo
# bloque) e id_operacion pasa al final de la tabla.
CAMPOS_ORDENES = [
    "orden", "operacion", "descripcion_general", "descripcion_operacion",
    "equipo", "centro_costo", "puesto_trabajo", "cod_actividad", "tipo_ot",
    "fecha_inicio", "horas_estimadas", "costo_plan",
    "horas_efectivas",
    "estado", "semana", "anio", "mes", "dia_semana", "clasificacion",
    "linea", "area", "sub_area", "coordinador", "especialidad", "actividad",
    "backlog_dias", "estado_backlog", "en_plan",
    "tecnico_asignado", "turno_asignado", "HHA", "HHD",
    "costo_servicio", "costo_materiales", "costo_total",
    "permiso_requerido", "bloqueo_energia", "link_checklist", "abrir_checklist",
    "observaciones", "id_operacion",
]
CAMPOS_EDITABLES = {"tecnico_asignado", "permiso_requerido",
                    "bloqueo_energia", "link_checklist", "observaciones"}
# v2.1: los ajustes de duración viven en su propia tabla con clave, para que
# sobrevivan a re-importaciones aunque cambie el orden de las filas.
CAMPOS_AJUSTES = ["id_operacion", "horas_ajustadas", "motivo", "fecha_ajuste",
                  "descripcion", "estado_ajuste", "desviacion_h"]
CAP_AJUSTES = 300
CAMPOS_EJECUCION = ["orden", "operacion", "estado_sistema", "prioridad",
                    "estado_instalacion", "precio", "costo_real", "costo_plan_total",
                    "estado_usuario", "id_operacion"]
CAMPOS_ASIGNACIONES = ["semana", "dia", "tecnico", "area", "especialidad", "turno",
                       "coordinador", "horas_disponibles", "clave"]
CAMPOS_IMPORT_ORDENES = ["orden", "operacion", "descripcion_general", "descripcion_operacion",
                         "equipo", "centro_costo", "puesto_trabajo", "cod_actividad",
                         "tipo_ot", "fecha_inicio", "horas_estimadas", "costo_plan"]


def formulas_ordenes(R):
    """Fórmulas por columna calculada de tblOrdenes (REGLAS 1, 2, 3, 4 y 8)."""
    T = "tblOrdenes"

    def f(campo, fila):
        return R.this(T, campo, fila)

    def hecho(campo):
        def _g(fila):
            fe = f("fecha_inicio", fila)
            vacia = f'{f("orden", fila)}=""'  # fila provisionada sin datos aún
            if campo == "id_operacion":
                return (f'=IF({vacia},"",{f("orden", fila)}&'
                        f'IF({f("operacion", fila)}="","0010",{f("operacion", fila)}))')
            if campo == "horas_efectivas":
                # v2.1: el ajuste se busca por clave en tblAjustes; si no hay
                # ajuste, cae al estándar del ERP. XLOOKUP usa horas_estimadas
                # como si_no_encontrado; el modo compatible usa IFERROR.
                he = f("horas_estimadas", fila)
                ajuste = R.busca(f("id_operacion", fila), "tblAjustes",
                                 "id_operacion", "horas_ajustadas",
                                 f'IF({he}="","",{he})')
                return f'=IF({vacia},"",{ajuste})'
            if campo == "estado":
                interna = R.busca(f("id_operacion", fila), "tblEjecucion",
                                  "id_operacion", "estado_sistema", '""')
                return f'=IF({vacia},"",' + R.busca(interna, "tblEstados", "estado_sistema",
                                                    "estado_normalizado", '"Pendiente"') + ")"
            if campo == "semana":
                # REGLA-2 v2: año ISO (el del jueves de la semana) + "-S" +
                # semana ISO a dos dígitos. Sin pliegue S53→S1.
                return (f'=IF({fe}="","",YEAR({fe}+4-WEEKDAY({fe},2))&"-S"&'
                        f'TEXT(_xlfn.ISOWEEKNUM({fe}),"00"))')
            if campo == "anio":
                return f'=IF({fe}="","",YEAR({fe}))'
            if campo == "mes":
                return f'=IF({fe}="","",MONTH({fe}))'
            if campo == "dia_semana":
                return f'=IF({fe}="","",INDEX(lista_dias,WEEKDAY({fe},2)))'
            if campo == "clasificacion":
                return f'=IF({f("tipo_ot", fila)}="","",' + \
                    R.busca(f("tipo_ot", fila), "tblTiposOT", "codigo",
                            "clasificacion", '"sin_clasificar"') + ")"
            if campo in ("linea", "area", "coordinador"):
                return f'=IF({f("centro_costo", fila)}="","",' + \
                    R.busca(f("centro_costo", fila), "tblCECO", "codigo",
                            campo, f'"{SIN_CATALOGO}"') + ")"
            if campo == "sub_area":
                # Herencia: sub-área del CECO; si está vacía hereda el NOMBRE
                # del área (celda area ya calculada), nunca el código del CECO.
                sub = R.busca(f("centro_costo", fila), "tblCECO", "codigo",
                              "sub_area", '""')
                return (f'=IF({f("centro_costo", fila)}="","",'
                        f'IF(({sub})<>"",{sub},{f("area", fila)}))')
            if campo == "especialidad":
                return f'=IF({f("puesto_trabajo", fila)}="","",' + \
                    R.busca(f("puesto_trabajo", fila), "tblPuestos", "codigo",
                            "especialidad", f'"{SIN_CATALOGO}"') + ")"
            if campo == "actividad":
                return f'=IF({f("cod_actividad", fila)}="","",' + \
                    R.busca(f("cod_actividad", fila), "tblActividades", "codigo",
                            "descripcion", f'"{SIN_CATALOGO}"') + ")"
            if campo == "backlog_dias":
                return f'=IF({fe}="","",TODAY()-{fe})'
            if campo == "estado_backlog":
                b = f("backlog_dias", fila)
                return (f'=IF({b}="","",IF({b}<0,"FUTURO",IF({b}>p_dias_backlog_max,'
                        f'"BACKLOG","MES CORRIENTE")))')
            if campo == "en_plan":
                b = f("backlog_dias", fila)
                return (f'=IF({b}="",FALSE,AND({b}>p_dias_backlog_min,'
                        f'{b}<=p_dias_backlog_max))')
            if campo == "turno_asignado":
                clave = (f'{f("semana", fila)}&"|"&{f("dia_semana", fila)}&"|"&'
                         f'{f("tecnico_asignado", fila)}')
                return (f'=IF({f("tecnico_asignado", fila)}="","",'
                        + R.busca(clave, "tblAsignaciones", "clave", "turno", '""') + ")")
            if campo == "HHA":
                # Horas Hombre Asignadas: total del técnico en ese día de esa
                # semana, repetido en todas sus filas (agregado por SUMIFS).
                # v2: suma horas_efectivas (ajuste manual manda sobre el ERP).
                t = f("tecnico_asignado", fila)
                return (f'=IF({t}="","",SUMIFS({R.col("tblOrdenes", "horas_efectivas")},'
                        f'{R.col("tblOrdenes", "tecnico_asignado")},{t},'
                        f'{R.col("tblOrdenes", "semana")},{f("semana", fila)},'
                        f'{R.col("tblOrdenes", "dia_semana")},{f("dia_semana", fila)}))')
            if campo == "HHD":
                # Horas Hombre Disponibles del día contra la disponibilidad
                # REAL del técnico (tblAsignaciones vía REGLA-5): un técnico
                # de vacaciones/ausente aporta 0 y su HHD queda en −HHA.
                # Negativo = sobreasignación (misma fuente que la línea de
                # capacidad del gráfico de PLAN_SEMANAL).
                h = f("HHA", fila)
                clave = (f'{f("semana", fila)}&"|"&{f("dia_semana", fila)}&"|"&'
                         f'{f("tecnico_asignado", fila)}')
                disp = R.busca(clave, "tblAsignaciones", "clave", "horas_disponibles", "0")
                return f'=IF({h}="","",p_factor_productividad*{disp}-{h})'
            if campo == "costo_servicio":
                return f'=IF({vacia},"",' + R.busca(f("id_operacion", fila), "tblEjecucion",
                                                    "id_operacion", "precio", "0") + ")"
            if campo == "costo_materiales":
                plan_total = R.busca(f("id_operacion", fila), "tblEjecucion",
                                     "id_operacion", "costo_plan_total", "0")
                return f'=IF({vacia},"",MAX(0,{plan_total}-{f("costo_servicio", fila)}))'
            if campo == "costo_total":
                return (f'=IF({vacia},"",{f("costo_servicio", fila)}+'
                        f'{f("costo_materiales", fila)})')
            if campo == "abrir_checklist":
                lc = f("link_checklist", fila)
                return f'=IF({lc}="","",HYPERLINK(p_ruta_base_checklists&{lc},"abrir"))'
            raise KeyError(campo)
        return _g

    calculadas = [c for c in CAMPOS_ORDENES
                  if c not in CAMPOS_EDITABLES and c not in CAMPOS_IMPORT_ORDENES]
    return {c: hecho(c) for c in calculadas}


# ══════════════════════════════════════════════════════════════════════════
# 6. ESTILOS
# ══════════════════════════════════════════════════════════════════════════

F_TXT = Font(name="Arial", size=10)
F_TIT = Font(name="Arial", size=14, bold=True, color="1F4E78")
F_SEC = Font(name="Arial", size=11, bold=True, color="1F4E78")
F_HDR = Font(name="Arial", size=10, bold=True, color="FFFFFF")
F_EDIT = Font(name="Arial", size=10, color="0000FF")
F_NOTA = Font(name="Arial", size=9, italic=True, color="595959")
FILL_HDR = PatternFill("solid", fgColor="1F4E78")
FILL_GRIS = PatternFill("solid", fgColor="F2F2F2")
FILL_VERDE = PatternFill("solid", fgColor="C6EFCE")
FILL_AMAR = PatternFill("solid", fgColor="FFEB9C")
FILL_ROJO = PatternFill("solid", fgColor="FFC7CE")
FMT_FECHA = "yyyy-mm-dd"
FMT_DINERO = "#,##0"
FMT_PCT = "0.0%"
FMT_HH = "0.0"
ESTILO_TABLA = TableStyleInfo(name="TableStyleMedium2", showRowStripes=True,
                              showFirstColumn=False, showLastColumn=False,
                              showColumnStripes=False)


def celda(ws, fila, col, valor=None, font=F_TXT, fmt=None, fill=None, wrap=False, alinear=None):
    c = ws.cell(row=fila, column=col, value=valor)
    c.font = font
    if fmt:
        c.number_format = fmt
    if fill:
        c.fill = fill
    if wrap or alinear:
        c.alignment = Alignment(wrap_text=wrap, horizontal=alinear, vertical="top" if wrap else None)
    return c


def encabezados(ws, fila, nombres, col_ini=1):
    for i, n in enumerate(nombres):
        celda(ws, fila, col_ini + i, n, font=F_HDR, fill=FILL_HDR)


def agregar_tabla(ws, tb):
    t = Table(displayName=tb.nombre, ref=tb.ref)
    t.tableStyleInfo = ESTILO_TABLA
    ws.add_table(t)


def semaforo_carga(ws, rango):
    """Semáforo REGLA-6: verde < 85 %, amarillo 85–100 %, rojo > 100 %."""
    ws.conditional_formatting.add(rango, CellIsRule(
        operator="lessThan", formula=["0.85"], fill=FILL_VERDE))
    ws.conditional_formatting.add(rango, CellIsRule(
        operator="between", formula=["0.85", "1"], fill=FILL_AMAR))
    ws.conditional_formatting.add(rango, CellIsRule(
        operator="greaterThan", formula=["1"], fill=FILL_ROJO))
def escala_adherencia(ws, rango):
    """Escala REGLA-7: rojo < 90 %, amarillo 90–95 %, verde > 95 %."""
    ws.conditional_formatting.add(rango, CellIsRule(
        operator="lessThan", formula=["0.9"], fill=FILL_ROJO))
    ws.conditional_formatting.add(rango, CellIsRule(
        operator="between", formula=["0.9", "0.95"], fill=FILL_AMAR))
    ws.conditional_formatting.add(rango, CellIsRule(
        operator="greaterThan", formula=["0.95"], fill=FILL_VERDE))


# ══════════════════════════════════════════════════════════════════════════
# 7. CONSTRUCCIÓN DEL LIBRO
# ══════════════════════════════════════════════════════════════════════════


def construir_libro(datos, esperado, ruta, refs="estructuradas"):
    hoy = datos["hoy"]
    semanas = datos["semanas"]
    n_ord, n_ejec, n_asig = len(datos["ordenes"]), len(datos["ejecucion"]), len(datos["asignaciones"])

    TAB = {
        "tblOrdenes": Tabla("tblOrdenes", "ORDENES", 3, CAMPOS_ORDENES, CAP_FILAS),
        "tblEjecucion": Tabla("tblEjecucion", "2_IMPORTAR_EJECUCION", 8, CAMPOS_EJECUCION, CAP_FILAS),
        "tblAjustes": Tabla("tblAjustes", "AJUSTES", 3, CAMPOS_AJUSTES, CAP_AJUSTES),
        "tblTecnicos": Tabla("tblTecnicos", "TECNICOS", 3,
                             ["id", "nombre", "especialidad", "area", "coordinador", "activo"], len(TECNICOS)),
        "tblAsignaciones": Tabla("tblAsignaciones", "ASIGNACIONES", 3, CAMPOS_ASIGNACIONES, n_asig),
        "tblCECO": Tabla("tblCECO", "CAT_CENTROS_COSTO", 3,
                         ["codigo", "descripcion", "planta", "area", "sub_area", "linea", "coordinador"],
                         len(CENTROS_COSTO)),
        "tblPuestos": Tabla("tblPuestos", "CAT_PUESTOS", 3,
                            ["codigo", "especialidad", "descripcion"], len(PUESTOS)),
        "tblActividades": Tabla("tblActividades", "CAT_ACTIVIDADES", 3,
                                ["codigo", "descripcion", "tipo"], len(ACTIVIDADES)),
        "tblTiposOT": Tabla("tblTiposOT", "CAT_TIPOS_OT", 3,
                            ["codigo", "descripcion", "clasificacion"], len(TIPOS_OT)),
        "tblEstados": Tabla("tblEstados", "CAT_ESTADOS_ERP", 3,
                            ["estado_sistema", "estado_normalizado"], len(ESTADOS_ERP)),
    }
    R = Refs(refs, TAB)
    O = TAB["tblOrdenes"]

    wb = Workbook()
    wb.calculation.fullCalcOnLoad = True  # cálculo automático al abrir, nunca manual

    # ------------------------------------------------------------- INICIO
    ws = wb.active
    ws.title = "INICIO"
    ws.sheet_properties.tabColor = "1F4E78"
    celda(ws, 1, 1, "MantPlan — Planificador semanal de mantenimiento", font=F_TIT)
    celda(ws, 2, 1, f"Versión {VERSION} · generado {hoy.isoformat()} · datos 100 % sintéticos de ejemplo", font=F_NOTA)
    filas_ini = [
        "",
        "PRINCIPIO RECTOR — separación entre lógica y datos:",
        "  · MOTOR: las 10 reglas de negocio viven en las fórmulas de este libro y nunca cambian.",
        "  · CATÁLOGOS: centros de costo, puestos, actividades, tipos de OT y estados se cargan por empresa.",
        "  · PARÁMETROS: jornada, productividad, ventanas de backlog y metas se ajustan en PARAMETROS.",
        "  · No hay macros, ni enlaces externos, ni códigos de empresa dentro de ninguna fórmula.",
        "",
        "FLUJO DE USO EN 5 PASOS:",
        "  1. Ajuste PARAMETROS y cargue los catálogos de su empresa (hojas CAT_*).",
        "  2. Pegue la exportación de órdenes (12 columnas, en este orden) directamente en ORDENES!A4:",
        "     un solo bloque contiguo A:L. Hay 1.200 filas provisionadas con las fórmulas ya escritas.",
        "  3. Pegue la segunda exportación (estados y costos) en 2_IMPORTAR_EJECUCION.",
        "  4. Complete TECNICOS y los turnos de ASIGNACIONES; asigne técnicos en ORDENES.",
        "     Los ajustes de duración van en AJUSTES por id_operacion: se re-aplican solos",
        "     tras cada re-importación, sin importar el orden de las filas.",
        "  5. Revise VALIDACION y trabaje con PERFIL_HH, PLAN_SEMANAL, ADHERENCIA, COSTOS y BACKLOG.",
        "",
        "CONVENCIONES:",
        "  · Celdas de texto azul = editables por el usuario. El resto se calcula solo.",
        "  · El libro recalcula automáticamente al abrir (sin macros).",
        "  · Las fórmulas usan XLOOKUP (Excel 2021/365). Para Excel 2016 vea la hoja _COMPATIBILIDAD.",
        "  · Los filtros se hacen con los autofiltros de cada tabla y con los selectores de PLAN_SEMANAL.",
        "  · ORDENES: HHA/HHD agregan las horas del técnico en ese día; HHD negativo (rojo) = sobreasignado.",
        "  · PLAN_SEMANAL: el gráfico de carga por técnico responde a los mismos selectores que la grilla.",
    ]
    for i, txt in enumerate(filas_ini, start=3):
        celda(ws, i, 1, txt, font=F_SEC if txt.endswith(":") else F_TXT)
    ws.column_dimensions["A"].width = 110

    # --------------------------------------------------------- PARAMETROS
    ws = wb.create_sheet("PARAMETROS")
    ws.sheet_properties.tabColor = "70AD47"
    celda(ws, 1, 1, "PARÁMETROS DEL MOTOR (Tabla 10)", font=F_TIT)
    encabezados(ws, 3, ["parametro", "valor", "descripcion"])
    for i, (p, v, d) in enumerate(PARAMETROS):
        celda(ws, 4 + i, 1, p)
        celda(ws, 4 + i, 2, v, font=F_EDIT,
              fmt="0.00" if isinstance(v, float) else None)
        celda(ws, 4 + i, 3, d, font=F_NOTA)
    celda(ws, 3, 5, "listas auxiliares", font=F_SEC)
    celda(ws, 4, 5, "turnos y códigos de ausencia:", font=F_NOTA)
    for i, t in enumerate(list(TURNOS) + list(CODIGOS_NO_DISPONIBLE)):
        celda(ws, 5 + i, 5, t)
    celda(ws, 4, 7, "no disponible:", font=F_NOTA)
    for i, t in enumerate(CODIGOS_NO_DISPONIBLE):
        celda(ws, 5 + i, 7, t)
    celda(ws, 4, 9, "días (1 = lunes):", font=F_NOTA)
    for i, d in enumerate(DIAS):
        celda(ws, 5 + i, 9, d)
    for colw, w in (("A", 24), ("B", 26), ("C", 66), ("E", 26), ("G", 14), ("I", 14)):
        ws.column_dimensions[colw].width = w
    dv = DataValidation(type="list", formula1='"lunes,domingo"', allow_blank=False)
    ws.add_data_validation(dv)
    dv.add(f"B{FILA_PARAM['primer_dia_semana']}")
    dv2 = DataValidation(type="decimal", operator="between", formula1="0", formula2="1")
    ws.add_data_validation(dv2)
    dv2.add(f"B{FILA_PARAM['factor_productividad']}")
    dv2.add(f"B{FILA_PARAM['meta_adherencia']}")
    dv2.add(f"B{FILA_PARAM['meta_ratio_prev_corr']}")
    dv3 = DataValidation(type="decimal", operator="between", formula1="1", formula2="24")
    ws.add_data_validation(dv3)
    dv3.add(f"B{FILA_PARAM['horas_jornada']}")
    dv4 = DataValidation(type="whole", operator="between", formula1="1", formula2="20")
    ws.add_data_validation(dv4)
    dv4.add(f"B{FILA_PARAM['top_tareas']}")

    nombres = {
        "p_moneda": FILA_PARAM["moneda"], "p_horas_jornada": FILA_PARAM["horas_jornada"],
        "p_factor_productividad": FILA_PARAM["factor_productividad"],
        "p_dias_backlog_max": FILA_PARAM["dias_backlog_max"],
        "p_dias_backlog_min": FILA_PARAM["dias_backlog_min"],
        "p_meta_adherencia": FILA_PARAM["meta_adherencia"],
        "p_meta_ratio_prev_corr": FILA_PARAM["meta_ratio_prev_corr"],
        "p_ruta_base_checklists": FILA_PARAM["ruta_base_checklists"],
        "p_top_tareas": FILA_PARAM["top_tareas"],
        "p_nombre_empresa": FILA_PARAM["nombre_empresa"],
        "p_nombre_planta": FILA_PARAM["nombre_planta"],
    }
    for nom, fila in nombres.items():
        wb.defined_names.add(DefinedName(nom, attr_text=f"PARAMETROS!$B${fila}"))
    wb.defined_names.add(DefinedName("lista_turnos", attr_text="PARAMETROS!$E$5:$E$10"))
    wb.defined_names.add(DefinedName("lista_no_disponible", attr_text="PARAMETROS!$G$5:$G$6"))
    wb.defined_names.add(DefinedName("lista_dias", attr_text="PARAMETROS!$I$5:$I$11"))
    wb.defined_names.add(DefinedName("lista_tecnicos", attr_text="TECNICOS!$B$4:$B$15"))

    # ------------------------------------------------- 1_IMPORTAR_ORDENES
    ws = wb.create_sheet("1_IMPORTAR_ORDENES")
    ws.sheet_properties.tabColor = "ED7D31"
    celda(ws, 1, 1, "ZONA DE PEGADO — exportación de órdenes del ERP", font=F_TIT)
    notas = [
        "Ordene la exportación de su ERP con estas 12 cabeceras exactas (misma disposición que ORDENES!A:L)",
        "y péguela EN UN SOLO PASO en ORDENES!A4 (o desde la primera fila libre). Nada más que hacer:",
        "las columnas calculadas ya están escritas en las 1.200 filas provisionadas de la tabla.",
        "operacion es opcional: si su ERP no maneja operaciones, déjela vacía y el sistema asume \"0010\".",
        "Los ajustes de duración NO van aquí: se registran en la hoja AJUSTES por id_operacion",
        "y se re-aplican solos tras re-importar, aunque cambie el orden de las filas.",
        "La validación de REGLA-10 (hoja VALIDACION) reporta problemas pero nunca bloquea la importación.",
        "Puede usar esta hoja como borrador para reordenar columnas antes de pegar.",
    ]
    for i, t in enumerate(notas, start=3):
        celda(ws, i, 1, t, font=F_NOTA)
    encabezados(ws, 8, CAMPOS_IMPORT_ORDENES)
    for i, o in enumerate(datos["ordenes"][:2]):  # dos filas de ejemplo del formato esperado
        for j, campo in enumerate(CAMPOS_IMPORT_ORDENES):
            v = o[campo]
            celda(ws, 9 + i, 1 + j, v, font=F_NOTA, fill=FILL_GRIS,
                  fmt=FMT_FECHA if campo == "fecha_inicio" else None)
    for j in range(len(CAMPOS_IMPORT_ORDENES)):
        ws.column_dimensions[get_column_letter(j + 1)].width = 18

    # ----------------------------------------------- 2_IMPORTAR_EJECUCION
    ws = wb.create_sheet("2_IMPORTAR_EJECUCION")
    ws.sheet_properties.tabColor = "ED7D31"
    celda(ws, 1, 1, "ZONA DE PEGADO — segunda exportación: estados y costos (tblEjecucion)", font=F_TIT)
    notas = [
        "Pegue aquí los estados y costos reales del ERP, con estas cabeceras exactas, desde la primera fila vacía.",
        "id_operacion se calcula solo. El catálogo CAT_ESTADOS_ERP traduce estado_sistema a Cerrada/Pendiente.",
        "Las órdenes sin par en esta tabla quedan como \"Pendiente\" (REGLA-10).",
    ]
    for i, t in enumerate(notas, start=3):
        celda(ws, i, 1, t, font=F_NOTA)
    E = TAB["tblEjecucion"]
    encabezados(ws, E.fila_enc, CAMPOS_EJECUCION)
    for i in range(CAP_FILAS):
        e = datos["ejecucion"][i] if i < n_ejec else {}
        fila = E.fila_ini + i
        for j, campo in enumerate(CAMPOS_EJECUCION[:-1], start=1):
            celda(ws, fila, j, e.get(campo),
                  fmt=FMT_DINERO if campo in ("precio", "costo_real", "costo_plan_total") else None)
        ord_ref = R.this("tblEjecucion", "orden", fila)
        op_ref = R.this("tblEjecucion", "operacion", fila)
        celda(ws, fila, len(CAMPOS_EJECUCION),
              f'=IF({ord_ref}="","",{ord_ref}&IF({op_ref}="","0010",{op_ref}))')
    agregar_tabla(ws, E)
    for j, wdt in enumerate([12, 10, 14, 11, 16, 10, 10, 15, 14, 16]):
        ws.column_dimensions[get_column_letter(j + 1)].width = wdt

    # ------------------------------------------------------------ ORDENES
    ws = wb.create_sheet("ORDENES")
    ws.sheet_properties.tabColor = "4472C4"
    celda(ws, 1, 1, "ORDENES — tabla madre (tblOrdenes). Azul = editable; el resto se calcula solo.", font=F_SEC)
    encabezados(ws, O.fila_enc, CAMPOS_ORDENES)
    F_ORD = formulas_ordenes(R)
    for i in range(CAP_FILAS):  # capacidad completa: fórmulas listas para importar
        o = datos["ordenes"][i] if i < n_ord else {}
        fila = O.fila_ini + i
        for j, campo in enumerate(CAMPOS_ORDENES, start=1):
            if campo in F_ORD:
                v = F_ORD[campo](fila)
                fnt = F_TXT
            else:
                v = o.get(campo)
                fnt = F_EDIT if campo in CAMPOS_EDITABLES else F_TXT
            fmt = None
            if campo == "fecha_inicio":
                fmt = FMT_FECHA
            elif campo in ("costo_plan", "costo_servicio", "costo_materiales", "costo_total"):
                fmt = FMT_DINERO
            elif campo == "backlog_dias":
                fmt = "0"
            elif campo in ("HHA", "HHD"):
                fmt = "0.00"
            celda(ws, fila, j, v, font=fnt, fmt=fmt)
    agregar_tabla(ws, O)
    ws.freeze_panes = "D4"
    let = O.letra
    dv = DataValidation(type="list", formula1="lista_tecnicos", allow_blank=True)
    ws.add_data_validation(dv)
    dv.add(f"{let('tecnico_asignado')}{O.fila_ini}:{let('tecnico_asignado')}{O.fila_fin}")
    # Resaltados obligatorios: backlog > 90 días y órdenes del plan sin técnico
    ws.conditional_formatting.add(
        f"{let('backlog_dias')}{O.fila_ini}:{let('backlog_dias')}{O.fila_fin}",
        CellIsRule(operator="greaterThan", formula=["90"], fill=FILL_ROJO))
    col_tec, col_plan = let("tecnico_asignado"), let("en_plan")
    ws.conditional_formatting.add(
        f"{col_tec}{O.fila_ini}:{col_tec}{O.fila_fin}",
        FormulaRule(formula=[f'AND(${col_plan}{O.fila_ini}=TRUE,${col_tec}{O.fila_ini}="")'],
                    fill=FILL_AMAR))
    # HHD negativo = técnico sobreasignado ese día
    col_hhd = let("HHD")
    ws.conditional_formatting.add(
        f"{col_hhd}{O.fila_ini}:{col_hhd}{O.fila_fin}",
        CellIsRule(operator="lessThan", formula=["0"], fill=FILL_ROJO))
    anchos = {"descripcion_general": 30, "descripcion_operacion": 30, "fecha_inicio": 12,
              "id_operacion": 15, "tecnico_asignado": 14, "estado_backlog": 14}
    for campo in CAMPOS_ORDENES:
        ws.column_dimensions[let(campo)].width = anchos.get(campo, 12)

    # ----------------------------------------------------------- TECNICOS
    ws = wb.create_sheet("TECNICOS")
    ws.sheet_properties.tabColor = "4472C4"
    T = TAB["tblTecnicos"]
    celda(ws, 1, 1, "TECNICOS (tblTecnicos) — catálogo editable de personal propio", font=F_SEC)
    encabezados(ws, T.fila_enc, T.campos)
    for i, (tid, nombre, esp, area) in enumerate(TECNICOS):
        fila = T.fila_ini + i
        for j, v in enumerate([tid, nombre, esp, area, COORD_POR_AREA[area], "SI"], start=1):
            celda(ws, fila, j, v, font=F_EDIT)
    agregar_tabla(ws, T)
    dv = DataValidation(type="list", formula1='"ELE,MEC,AUT,OP"', allow_blank=False)
    ws.add_data_validation(dv)
    dv.add(f"C{T.fila_ini}:C{T.fila_fin}")
    dv = DataValidation(type="list", formula1='"SI,NO"', allow_blank=False)
    ws.add_data_validation(dv)
    dv.add(f"F{T.fila_ini}:F{T.fila_fin}")
    for colw, w in (("A", 10), ("B", 14), ("C", 12), ("D", 14), ("E", 16), ("F", 8)):
        ws.column_dimensions[colw].width = w

    # ------------------------------------------------------- ASIGNACIONES
    ws = wb.create_sheet("ASIGNACIONES")
    ws.sheet_properties.tabColor = "4472C4"
    A = TAB["tblAsignaciones"]
    celda(ws, 1, 1, "ASIGNACIONES — turno por técnico, día y semana. El turno se elige de la lista "
                    "desplegable; REGLA-5 calcula las horas.", font=F_SEC)
    encabezados(ws, A.fila_enc, A.campos)
    for i, a in enumerate(datos["asignaciones"]):
        fila = A.fila_ini + i
        celda(ws, fila, 1, a["semana"])
        celda(ws, fila, 2, a["dia"])
        celda(ws, fila, 3, a["tecnico"])
        celda(ws, fila, 4, "=" + R.busca(R.this("tblAsignaciones", "tecnico", fila),
                                         "tblTecnicos", "nombre", "area", '""'))
        celda(ws, fila, 5, "=" + R.busca(R.this("tblAsignaciones", "tecnico", fila),
                                         "tblTecnicos", "nombre", "especialidad", '""'))
        celda(ws, fila, 6, a["turno"], font=F_EDIT)
        celda(ws, fila, 7, "=" + R.busca(R.this("tblAsignaciones", "tecnico", fila),
                                         "tblTecnicos", "nombre", "coordinador", '""'))
        tu = R.this("tblAsignaciones", "turno", fila)
        celda(ws, fila, 8, f'=IF(OR({tu}="",ISNUMBER(MATCH({tu},lista_no_disponible,0))),0,p_horas_jornada)')
        celda(ws, fila, 9, f'={R.this("tblAsignaciones", "semana", fila)}&"|"&'
                           f'{R.this("tblAsignaciones", "dia", fila)}&"|"&'
                           f'{R.this("tblAsignaciones", "tecnico", fila)}')
    agregar_tabla(ws, A)
    ws.freeze_panes = "A4"
    dv = DataValidation(type="list", formula1="lista_turnos", allow_blank=True)
    ws.add_data_validation(dv)
    dv.add(f"F{A.fila_ini}:F{A.fila_fin}")
    for colw, w in (("A", 9), ("B", 11), ("C", 13), ("D", 13), ("E", 12), ("F", 8),
                    ("G", 15), ("H", 16), ("I", 26)):
        ws.column_dimensions[colw].width = w

    # ------------------------------------------------------------ AJUSTES
    # v2.1: los ajustes de duración van por id_operacion, no por posición de
    # fila, para sobrevivir a re-importaciones con otro orden de filas.
    ws = wb.create_sheet("AJUSTES")
    ws.sheet_properties.tabColor = "4472C4"
    AJ = TAB["tblAjustes"]
    celda(ws, 1, 1, "AJUSTES DE DURACIÓN (tblAjustes) — por id_operacion. Se re-aplican solos "
                    "tras cada re-importación, sin importar el orden de las filas. Ante "
                    "duplicados gana la primera fila. Azul = editable.", font=F_SEC)
    encabezados(ws, AJ.fila_enc, AJ.campos)
    for i in range(CAP_AJUSTES):
        a = datos["ajustes"][i] if i < len(datos["ajustes"]) else {}
        fila = AJ.fila_ini + i
        celda(ws, fila, 1, a.get("id_operacion"), font=F_EDIT)
        celda(ws, fila, 2, a.get("horas_ajustadas"), font=F_EDIT, fmt="0.0")
        celda(ws, fila, 3, a.get("motivo"), font=F_EDIT)
        celda(ws, fila, 4, a.get("fecha_ajuste"), font=F_EDIT, fmt=FMT_FECHA)
        idr = R.this("tblAjustes", "id_operacion", fila)
        celda(ws, fila, 5, f'=IF({idr}="","",'
              + R.busca(idr, "tblOrdenes", "id_operacion", "descripcion_operacion",
                        '"(no encontrada)"') + ")")
        celda(ws, fila, 6,
              f'=IF({idr}="","",IF(ISNA(MATCH({idr},{R.col("tblOrdenes", "id_operacion")},0)),'
              f'"huérfano",IF(COUNTIF($A$4:$A{fila},{idr})>1,"duplicado (se ignora)",'
              f'"aplicado")))')
        est_lu = R.busca(idr, "tblOrdenes", "id_operacion", "horas_estimadas", '""')
        celda(ws, fila, 7,
              f'=IF({R.this("tblAjustes", "estado_ajuste", fila)}<>"aplicado","",'
              f'IF({est_lu}="","",{R.this("tblAjustes", "horas_ajustadas", fila)}-{est_lu}))',
              fmt="+0.0;-0.0;0")
    agregar_tabla(ws, AJ)
    ws.conditional_formatting.add(
        f"F{AJ.fila_ini}:F{AJ.fila_fin}",
        CellIsRule(operator="equal", formula=['"huérfano"'], fill=FILL_AMAR))
    ws.conditional_formatting.add(
        f"F{AJ.fila_ini}:F{AJ.fila_fin}",
        CellIsRule(operator="equal", formula=['"duplicado (se ignora)"'], fill=FILL_ROJO))
    ws.freeze_panes = "A4"
    for colw, w in (("A", 16), ("B", 15), ("C", 46), ("D", 13), ("E", 34), ("F", 20), ("G", 12)):
        ws.column_dimensions[colw].width = w

    # ---------------------------------------------------------- PERFIL_HH
    # v2: dimensionado por los datos. Una serie de hasta 60 semanas se deriva
    # por fórmula de MIN/MAX de tblOrdenes[fecha_inicio]; las filas/columnas
    # de semanas sin órdenes se generan igual pero quedan ocultas.
    CAP_SEM = 60
    serie = esperado["serie_semanas"]
    con_datos = esperado["semanas_con_datos"]
    ocultas_k = {k for k in range(CAP_SEM)
                 if k >= len(serie) or serie[k] not in con_datos}

    ws = wb.create_sheet("PERFIL_HH")
    ws.sheet_properties.tabColor = "7030A0"
    celda(ws, 1, 1, "PERFIL DE HH (REGLA-6) — especialidad × semana. La serie de semanas se deriva "
                    "de los datos (capacidad 60); las semanas sin órdenes están ocultas.", font=F_TIT)
    # Serie de semanas (columnas N/O): lunes consecutivos desde la primera
    # fecha presente hasta la última, y su etiqueta REGLA-2 (AAAA-Snn).
    celda(ws, 3, 14, "lunes_semana", font=F_HDR, fill=FILL_HDR)
    celda(ws, 3, 15, "semana (serie auto)", font=F_HDR, fill=FILL_HDR)
    col_fecha = R.col("tblOrdenes", "fecha_inicio")
    FILA_SERIE = 4
    for k in range(CAP_SEM):
        fr = FILA_SERIE + k
        if k == 0:
            celda(ws, fr, 14, f'=IF(COUNT({col_fecha})=0,"",MIN({col_fecha})'
                              f'-WEEKDAY(MIN({col_fecha}),2)+1)', fmt=FMT_FECHA)
        else:
            celda(ws, fr, 14, f'=IF(N{fr - 1}="","",IF(N{fr - 1}+7>MAX({col_fecha}),"",'
                              f'N{fr - 1}+7))', fmt=FMT_FECHA)
        celda(ws, fr, 15, f'=IF(N{fr}="","",YEAR(N{fr}+4-WEEKDAY(N{fr},2))&"-S"&'
                          f'TEXT(_xlfn.ISOWEEKNUM(N{fr}),"00"))')

    cab = ["especialidad", "semana", "hh_disponible", "hh_productiva", "hh_preventiva",
           "hh_correctiva", "hh_planificada", "holgura", "pct_carga"]
    encabezados(ws, 3, cab)
    filas_flat = {}
    for k in range(CAP_SEM):
        for ei, esp_f in enumerate(ESPECIALIDADES):
            fila = 4 + k * len(ESPECIALIDADES) + ei
            filas_flat[(esp_f, k)] = fila
            celda(ws, fila, 1, esp_f)
            celda(ws, fila, 2, f"=$O${FILA_SERIE + k}")
            celda(ws, fila, 3, f'=SUMIFS({R.col("tblAsignaciones", "horas_disponibles")},'
                               f'{R.col("tblAsignaciones", "especialidad")},$A{fila},'
                               f'{R.col("tblAsignaciones", "semana")},$B{fila})', fmt=FMT_HH)
            celda(ws, fila, 4, f"=C{fila}*p_factor_productividad", fmt=FMT_HH)
            celda(ws, fila, 5, f'=SUMIFS({R.col("tblOrdenes", "horas_efectivas")},'
                               f'{R.col("tblOrdenes", "especialidad")},$A{fila},'
                               f'{R.col("tblOrdenes", "semana")},$B{fila},'
                               f'{R.col("tblOrdenes", "clasificacion")},"preventiva")', fmt=FMT_HH)
            celda(ws, fila, 6, f'=SUMIFS({R.col("tblOrdenes", "horas_efectivas")},'
                               f'{R.col("tblOrdenes", "especialidad")},$A{fila},'
                               f'{R.col("tblOrdenes", "semana")},$B{fila},'
                               f'{R.col("tblOrdenes", "clasificacion")},"correctiva")', fmt=FMT_HH)
            celda(ws, fila, 7, f"=E{fila}+F{fila}", fmt=FMT_HH)
            celda(ws, fila, 8, f"=D{fila}-G{fila}", fmt=FMT_HH)
            celda(ws, fila, 9, f'=IF(D{fila}=0,"",G{fila}/D{fila})', fmt=FMT_PCT)
    ult_flat = 3 + CAP_SEM * len(ESPECIALIDADES)
    semaforo_carga(ws, f"I4:I{ult_flat}")
    for k in ocultas_k:  # bloques de semanas sin datos, ocultos
        for ei in range(len(ESPECIALIDADES)):
            ws.row_dimensions[4 + k * len(ESPECIALIDADES) + ei].hidden = True

    fila_mat = ult_flat + 3
    celda(ws, fila_mat - 1, 1, "MATRIZ % CARGA — semana × especialidad. Semáforo: verde < 85 %, "
                               "amarillo 85–100 %, rojo > 100 %. Semanas sin datos ocultas.", font=F_SEC)
    celda(ws, fila_mat, 1, "semana", font=F_HDR, fill=FILL_HDR)
    for i, esp_f in enumerate(ESPECIALIDADES):
        celda(ws, fila_mat, 2 + i, esp_f, font=F_HDR, fill=FILL_HDR)
    for k in range(CAP_SEM):
        fr = fila_mat + 1 + k
        celda(ws, fr, 1, f"=$O${FILA_SERIE + k}")
        for i, esp_f in enumerate(ESPECIALIDADES):
            celda(ws, fr, 2 + i, f"=$I${filas_flat[(esp_f, k)]}", fmt=FMT_PCT)
        if k in ocultas_k:
            ws.row_dimensions[fr].hidden = True
    semaforo_carga(ws, f"B{fila_mat + 1}:{get_column_letter(1 + len(ESPECIALIDADES))}{fila_mat + CAP_SEM}")

    fila_r9 = fila_mat + CAP_SEM + 3
    celda(ws, fila_r9 - 1, 1, "RATIO CORRECTIVO/PREVENTIVO POR SEMANA (REGLA-9) — meta: correctivo ≤ 20 % de las HH",
          font=F_SEC)
    encabezados(ws, fila_r9, ["semana", "hh_preventiva", "hh_correctiva", "ratio_corr_prev",
                              "pct_correctivo", "cumple_meta"])
    for k in range(CAP_SEM):
        fr = fila_r9 + 1 + k
        celda(ws, fr, 1, f"=$O${FILA_SERIE + k}")
        celda(ws, fr, 2, f'=SUMIFS({R.col("tblOrdenes", "horas_efectivas")},'
                         f'{R.col("tblOrdenes", "semana")},$A{fr},'
                         f'{R.col("tblOrdenes", "clasificacion")},"preventiva")', fmt=FMT_HH)
        celda(ws, fr, 3, f'=SUMIFS({R.col("tblOrdenes", "horas_efectivas")},'
                         f'{R.col("tblOrdenes", "semana")},$A{fr},'
                         f'{R.col("tblOrdenes", "clasificacion")},"correctiva")', fmt=FMT_HH)
        celda(ws, fr, 4, f'=IF(B{fr}=0,"",C{fr}/B{fr})', fmt=FMT_PCT)
        celda(ws, fr, 5, f'=IF(B{fr}+C{fr}=0,"",C{fr}/(B{fr}+C{fr}))', fmt=FMT_PCT)
        celda(ws, fr, 6, f'=IF(E{fr}="","",IF(E{fr}<=1-p_meta_ratio_prev_corr,"SI","NO"))')
        if k in ocultas_k:
            ws.row_dimensions[fr].hidden = True
    for colw, w in (("A", 13), ("B", 13), ("C", 13), ("D", 14), ("E", 14), ("F", 14),
                    ("G", 14), ("H", 12), ("I", 11), ("N", 13), ("O", 18)):
        ws.column_dimensions[colw].width = w

    # ------------------------------------------------------- PLAN_SEMANAL
    ws = wb.create_sheet("PLAN_SEMANAL")
    ws.sheet_properties.tabColor = "7030A0"
    celda(ws, 1, 1, "PLAN SEMANAL — el gráfico de carga y la grilla responden a los mismos "
                    "selectores. \"(todos)\" desactiva un criterio; \"-\" significa vacío.", font=F_SEC)
    criterios = [("semana", 2, ["(todos)"] + semanas, semanas[1]),
                 ("día", 4, ["(todos)"] + list(DIAS), "(todos)"),
                 ("turno", 6, ["(todos)"] + list(TURNOS), "(todos)"),
                 ("coordinador", 8, ["(todos)"] + sorted(set(COORD_POR_AREA.values())), "(todos)"),
                 ("área", 10, ["(todos)"] + list(COORD_POR_AREA), "(todos)"),
                 ("especialidad", 12, ["(todos)"] + list(ESPECIALIDADES), "(todos)"),
                 ("sub-área", 14, ["(todos)"] + SUBAREAS, "(todos)")]
    for nombre, colc, lista, defecto in criterios:
        celda(ws, 3, colc - 1, nombre + ":", font=F_SEC)
        celda(ws, 3, colc, defecto, font=F_EDIT, fill=FILL_GRIS)
        dv = DataValidation(type="list", formula1='"' + ",".join(lista) + '"', allow_blank=False)
        ws.add_data_validation(dv)
        dv.add(f"{get_column_letter(colc)}3")
    FILA_GRILLA = 25  # encabezado de la grilla; el gráfico vive arriba, en la zona fija
    fila_ini_esp, fila_fin_esp = FILA_GRILLA + 1, FILA_GRILLA + CAP_FILAS
    # grilla A..G = 7 dimensiones de filtro; H..N = datos. Los selectores están
    # en B3,D3,F3,H3,J3,L3,N3 (semana, día, turno, coordinador, área,
    # especialidad, sub-área).
    crit = (f'$A${fila_ini_esp}:$A${fila_fin_esp},IF($B$3="(todos)","*",$B$3),'
            f'$B${fila_ini_esp}:$B${fila_fin_esp},IF($D$3="(todos)","*",$D$3),'
            f'$C${fila_ini_esp}:$C${fila_fin_esp},IF($F$3="(todos)","*",$F$3),'
            f'$D${fila_ini_esp}:$D${fila_fin_esp},IF($H$3="(todos)","*",$H$3),'
            f'$E${fila_ini_esp}:$E${fila_fin_esp},IF($J$3="(todos)","*",$J$3),'
            f'$F${fila_ini_esp}:$F${fila_fin_esp},IF($L$3="(todos)","*",$L$3),'
            f'$G${fila_ini_esp}:$G${fila_fin_esp},IF($N$3="(todos)","*",$N$3)')
    celda(ws, 5, 1, "órdenes:", font=F_SEC)
    celda(ws, 5, 2, f"=COUNTIFS({crit})")
    celda(ws, 5, 3, "HH:", font=F_SEC)
    celda(ws, 5, 4, f"=SUMIFS($L${fila_ini_esp}:$L${fila_fin_esp},{crit})", fmt=FMT_HH)

    # Zona de datos del gráfico (columnas P:V, dentro de la zona fija).
    # Es el sustituto sin macros del PivotChart: SUMIFS contra tblOrdenes
    # gobernados por los mismos selectores que filtran la grilla.
    celda(ws, 2, 16, "datos del gráfico de carga — no editar", font=F_NOTA)
    encabezados(ws, 3, ["tecnico", "especialidad", "etiqueta", "hha_seleccion",
                        "dentro_capacidad", "sobreasignacion", "capacidad"], col_ini=16)
    fila_tec0 = 4
    for i, (_tid, nombre, esp_t, _area) in enumerate(TECNICOS):
        fr = fila_tec0 + i
        celda(ws, fr, 16, nombre)
        celda(ws, fr, 17, esp_t)
        turno_sel = R.busca(f'$B$3&"|"&$D$3&"|"&$P{fr}', "tblAsignaciones", "clave", "turno", '""')
        celda(ws, fr, 18, f'=IF(OR($B$3="(todos)",$D$3="(todos)"),$P{fr},'
                          f'$P{fr}&" ("&{turno_sel}&")")')
        celda(ws, fr, 19,
              f'=IF(AND($L$3<>"(todos)",$Q{fr}<>$L$3),NA(),'
              f'SUMIFS({R.col("tblOrdenes", "horas_efectivas")},'
              f'{R.col("tblOrdenes", "tecnico_asignado")},$P{fr},'
              f'{R.col("tblOrdenes", "semana")},IF($B$3="(todos)","*",$B$3),'
              f'{R.col("tblOrdenes", "dia_semana")},IF($D$3="(todos)","*",$D$3),'
              f'{R.col("tblOrdenes", "turno_asignado")},IF($F$3="(todos)","*",$F$3),'
              f'{R.col("tblOrdenes", "coordinador")},IF($H$3="(todos)","*",$H$3),'
              f'{R.col("tblOrdenes", "area")},IF($J$3="(todos)","*",$J$3),'
              f'{R.col("tblOrdenes", "sub_area")},IF($N$3="(todos)","*",$N$3)))', fmt=FMT_HH)
        celda(ws, fr, 20, f"=IF(ISNA($S{fr}),NA(),MIN($S{fr},$V{fr}))", fmt=FMT_HH)
        celda(ws, fr, 21, f"=IF(ISNA($S{fr}),NA(),MAX(0,$S{fr}-$V{fr}))", fmt=FMT_HH)
        celda(ws, fr, 22,
              f'=IF(AND($L$3<>"(todos)",$Q{fr}<>$L$3),NA(),'
              f'p_factor_productividad*SUMIFS({R.col("tblAsignaciones", "horas_disponibles")},'
              f'{R.col("tblAsignaciones", "tecnico")},$P{fr},'
              f'{R.col("tblAsignaciones", "semana")},IF($B$3="(todos)","*",$B$3),'
              f'{R.col("tblAsignaciones", "dia")},IF($D$3="(todos)","*",$D$3)))', fmt=FMT_HH)
    fila_tec1 = fila_tec0 + len(TECNICOS) - 1

    # Gráfico: barras apiladas (verde dentro de capacidad, rojo sobreasignado)
    # + serie de línea con la capacidad productiva (REGLA-5 × factor).
    y_max = max([v for v in esperado["carga_tecnicos"].values()]
                + [v for v in esperado["capacidad_tecnicos"].values()]) + 5
    barras = BarChart()
    barras.type = "col"
    barras.grouping = "stacked"
    barras.overlap = 100
    barras.gapWidth = 60
    barras.title = "Carga por técnico vs capacidad (según selectores)"
    barras.add_data(Reference(ws, min_col=20, min_row=3, max_row=fila_tec1), titles_from_data=True)
    barras.add_data(Reference(ws, min_col=21, min_row=3, max_row=fila_tec1), titles_from_data=True)
    cats_tec = Reference(ws, min_col=18, min_row=fila_tec0, max_row=fila_tec1)
    barras.set_categories(cats_tec)
    barras.series[0].graphicalProperties.solidFill = "63BE7B"   # dentro de capacidad
    barras.series[1].graphicalProperties.solidFill = "F8696B"   # sobreasignación
    for s in barras.series:
        s.dLbls = DataLabelList(showVal=True)  # etiquetas visibles, ceros incluidos
    barras.y_axis.scaling.min = 0
    barras.y_axis.scaling.max = y_max
    barras.y_axis.title = "HH"
    # Serie de capacidad como línea combinada SOBRE EL MISMO eje de valores
    # que las barras (mismos axId por defecto → ejes compartidos), con
    # marcador visible y sin etiquetas de datos.
    capacidad = LineChart()
    capacidad.add_data(Reference(ws, min_col=22, min_row=3, max_row=fila_tec1), titles_from_data=True)
    capacidad.set_categories(cats_tec)
    s_cap = capacidad.series[0]
    s_cap.graphicalProperties.line.solidFill = "1F4E78"
    s_cap.graphicalProperties.line.width = 25000
    s_cap.smooth = False
    s_cap.marker = Marker(symbol="circle", size=6)
    barras += capacidad
    barras.legend.position = "b"
    barras.height, barras.width = 8.5, 30
    ws.add_chart(barras, "A7")

    cab_plan = ["semana", "dia", "turno", "coordinador", "area", "especialidad", "sub_area",
                "tecnico", "id_operacion", "descripcion_operacion", "equipo", "horas",
                "estado", "en_plan"]
    encabezados(ws, FILA_GRILLA, cab_plan)
    origen = {"semana": "semana", "dia": "dia_semana", "turno": "turno_asignado",
              "coordinador": "coordinador", "area": "area", "especialidad": "especialidad",
              "sub_area": "sub_area", "tecnico": "tecnico_asignado", "id_operacion": "id_operacion",
              "descripcion_operacion": "descripcion_operacion", "equipo": "equipo",
              "horas": "horas_efectivas", "estado": "estado", "en_plan": "en_plan"}
    for i in range(CAP_FILAS):
        fo = O.fila_ini + i
        fe = fila_ini_esp + i
        vacia = f"'ORDENES'!${O.letra('orden')}{fo}=\"\""
        for j, c in enumerate(cab_plan, start=1):
            ref = f"'ORDENES'!${O.letra(origen[c])}{fo}"
            if c == "horas":
                celda(ws, fe, j, f'=IF({vacia},"",IF({ref}="",0,{ref}))', fmt="0")
            elif c == "en_plan":
                celda(ws, fe, j, f'=IF({vacia},"",{ref})')
            else:
                celda(ws, fe, j, f'=IF({vacia},"",IF({ref}="","-",{ref}))')
    ws.auto_filter.ref = f"A{FILA_GRILLA}:N{fila_fin_esp}"
    # Paneles inmovilizados: selectores, gráfico y encabezados quedan fijos
    ws.freeze_panes = f"A{fila_ini_esp}"
    # El área de impresión cubre las filas con datos de ejemplo; ajústela tras
    # una importación mayor (no puede ser dinámica sin OFFSET, que está prohibido).
    ws.print_area = f"A1:N{FILA_GRILLA + n_ord}"
    ws.page_setup.orientation = "landscape"
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 0
    ws.sheet_properties.pageSetUpPr = PageSetupProperties(fitToPage=True)
    for j, wdt in enumerate([9, 11, 8, 14, 13, 12, 14, 13, 15, 30, 9, 7, 11, 9]):
        ws.column_dimensions[get_column_letter(j + 1)].width = wdt
    for j, wdt in enumerate([13, 12, 20, 13, 15, 15, 11]):
        ws.column_dimensions[get_column_letter(16 + j)].width = wdt

    # --------------------------------------------------------- ADHERENCIA
    ws = wb.create_sheet("ADHERENCIA")
    ws.sheet_properties.tabColor = "7030A0"
    celda(ws, 1, 1, "ADHERENCIA (REGLA-7) — rojo < 90 %, amarillo 90–95 %, verde > 95 %", font=F_TIT)

    def bloque_adh(fila0, titulo, campo, valores, con_meta=False, ocultar=()):
        """valores: literales o fórmulas '=...' (etiquetas dinámicas de semana);
        ocultar: offsets (0-based) de filas de datos que quedan ocultas."""
        celda(ws, fila0, 1, titulo, font=F_SEC)
        cabb = ["valor", "total_ot", "cerradas", "adherencia_conteo", "hh_total",
                "hh_cerradas", "adherencia_horas"] + (["meta"] if con_meta else [])
        encabezados(ws, fila0 + 1, cabb)
        for i, v in enumerate(valores):
            fr = fila0 + 2 + i
            celda(ws, fr, 1, v)
            celda(ws, fr, 2, f'=COUNTIFS({R.col("tblOrdenes", campo)},$A{fr})')
            celda(ws, fr, 3, f'=COUNTIFS({R.col("tblOrdenes", campo)},$A{fr},'
                             f'{R.col("tblOrdenes", "estado")},"Cerrada")')
            celda(ws, fr, 4, f'=IF(B{fr}=0,"",C{fr}/B{fr})', fmt=FMT_PCT)
            celda(ws, fr, 5, f'=SUMIFS({R.col("tblOrdenes", "horas_efectivas")},'
                             f'{R.col("tblOrdenes", campo)},$A{fr})', fmt=FMT_HH)
            celda(ws, fr, 6, f'=SUMIFS({R.col("tblOrdenes", "horas_efectivas")},'
                             f'{R.col("tblOrdenes", campo)},$A{fr},'
                             f'{R.col("tblOrdenes", "estado")},"Cerrada")', fmt=FMT_HH)
            celda(ws, fr, 7, f'=IF(E{fr}=0,"",F{fr}/E{fr})', fmt=FMT_PCT)
            if con_meta:
                celda(ws, fr, 8, "=p_meta_adherencia", fmt="0%")
            if i in ocultar:
                ws.row_dimensions[fr].hidden = True
        ult = fila0 + 1 + len(valores)
        escala_adherencia(ws, f"D{fila0 + 2}:D{ult}")
        escala_adherencia(ws, f"G{fila0 + 2}:G{ult}")
        return ult + 2

    # Bloque semanal dinámico: 60 etiquetas derivadas de la serie de PERFIL_HH;
    # las semanas sin órdenes quedan ocultas (el gráfico solo traza visibles).
    etiquetas_sem = [f"='PERFIL_HH'!$O${FILA_SERIE + k}" for k in range(CAP_SEM)]
    f0 = bloque_adh(3, "POR SEMANA (serie derivada de los datos, hasta 60)", "semana",
                    etiquetas_sem, con_meta=True, ocultar=ocultas_k)
    fa = bloque_adh(f0, "POR ÁREA", "area", list(COORD_POR_AREA))
    # POR SUB-ÁREA — jerárquico: las sub-áreas van agrupadas por su área madre
    # (indicada en la columna I). Herencia mediante: un área sin subdividir
    # aparece con su propio nombre como sub-área (fila idéntica al nivel área).
    parent_of = {se: ar for ar, ses in SUBAREAS_POR_AREA.items() for se in ses}
    f1 = bloque_adh(fa, "POR SUB-ÁREA (agrupada bajo su área madre — col. I)", "sub_area", SUBAREAS)
    celda(ws, fa + 1, 9, "área madre", font=F_HDR, fill=FILL_HDR)
    for i, sa in enumerate(SUBAREAS):
        celda(ws, fa + 2 + i, 9, parent_of[sa], font=F_NOTA)
    f2 = bloque_adh(f1, "POR ESPECIALIDAD", "especialidad", list(ESPECIALIDADES))
    f3 = bloque_adh(f2, "POR COORDINADOR", "coordinador", sorted(set(COORD_POR_AREA.values())))
    f4 = bloque_adh(f3, "POR CLASIFICACIÓN", "clasificacion",
                    ["preventiva", "correctiva", "sin_clasificar"])
    bloque_adh(f4, "POR TÉCNICO", "tecnico_asignado", [t[1] for t in TECNICOS])
    grafico = LineChart()
    grafico.title = "Adherencia semanal vs meta"
    grafico.height, grafico.width = 8, 16
    datos_ref = Reference(ws, min_col=4, min_row=4, max_row=4 + CAP_SEM)
    meta_ref = Reference(ws, min_col=8, min_row=4, max_row=4 + CAP_SEM)
    cats = Reference(ws, min_col=1, min_row=5, max_row=4 + CAP_SEM)
    grafico.add_data(datos_ref, titles_from_data=True)
    grafico.add_data(meta_ref, titles_from_data=True)
    grafico.set_categories(cats)
    grafico.y_axis.number_format = "0%"
    grafico.y_axis.scaling.min = 0
    ws.add_chart(grafico, "J3")
    for colw, w in (("A", 18), ("B", 9), ("C", 9), ("D", 17), ("E", 9), ("F", 11),
                    ("G", 16), ("H", 7), ("I", 14)):
        ws.column_dimensions[colw].width = w

    # ------------------------------------------------------------- COSTOS
    ws = wb.create_sheet("COSTOS")
    ws.sheet_properties.tabColor = "7030A0"
    celda(ws, 1, 1, '="COSTOS ("&p_moneda&") — REGLA-8: real (servicio + materiales) contra plan"', font=F_TIT)
    meses = esperado["meses"]
    areas = list(COORD_POR_AREA)
    lineas = [c[CECO_LINEA] for c in CENTROS_COSTO]

    def matriz_costos(fila0, titulo, campo_dim, valores, campo_valor):
        celda(ws, fila0, 1, titulo, font=F_SEC)
        celda(ws, fila0 + 1, 1, "anio", font=F_NOTA)
        celda(ws, fila0 + 2, 1, "mes", font=F_NOTA)
        for j, (anio, mes) in enumerate(meses):
            celda(ws, fila0 + 1, 2 + j, anio, font=F_NOTA)
            celda(ws, fila0 + 2, 2 + j, mes, font=F_HDR, fill=FILL_HDR)
        celda(ws, fila0 + 2, 2 + len(meses), "TOTAL", font=F_HDR, fill=FILL_HDR)
        for i, v in enumerate(valores):
            fr = fila0 + 3 + i
            celda(ws, fr, 1, v)
            for j in range(len(meses)):
                cl = get_column_letter(2 + j)
                celda(ws, fr, 2 + j,
                      f'=SUMIFS({R.col("tblOrdenes", campo_valor)},'
                      f'{R.col("tblOrdenes", campo_dim)},$A{fr},'
                      f'{R.col("tblOrdenes", "anio")},{cl}${fila0 + 1},'
                      f'{R.col("tblOrdenes", "mes")},{cl}${fila0 + 2})', fmt=FMT_DINERO)
            celda(ws, fr, 2 + len(meses),
                  f"=SUM(B{fr}:{get_column_letter(1 + len(meses))}{fr})", fmt=FMT_DINERO)
        fr_tot = fila0 + 3 + len(valores)
        celda(ws, fr_tot, 1, "TOTAL", font=F_SEC)
        for j in range(len(meses) + 1):
            cl = get_column_letter(2 + j)
            celda(ws, fr_tot, 2 + j, f"=SUM({cl}{fila0 + 3}:{cl}{fr_tot - 1})", fmt=FMT_DINERO)
        return fr_tot

    tot_plan = matriz_costos(3, "PLAN por área (costo_plan)", "area", areas, "costo_plan")
    tot_real = matriz_costos(tot_plan + 2, "REAL por área (costo_total = servicio + materiales)",
                             "area", areas, "costo_total")
    fila0_desv = tot_real + 2
    celda(ws, fila0_desv, 1, "DESVÍO por área (real − plan)", font=F_SEC)
    for i, v in enumerate(areas + ["TOTAL"]):
        fr = fila0_desv + 1 + i
        celda(ws, fr, 1, v, font=F_SEC if v == "TOTAL" else F_TXT)
        for j in range(len(meses) + 1):
            cl = get_column_letter(2 + j)
            celda(ws, fr, 2 + j,
                  f"={cl}{(tot_real - len(areas)) + i}-{cl}{(tot_plan - len(areas)) + i}",
                  fmt=FMT_DINERO)
    ult_desv = fila0_desv + 1 + len(areas)
    tot_sub = matriz_costos(ult_desv + 2,
                            "REAL por sub-área (herencia: un área sin subdividir aparece con su "
                            "propio nombre; el TOTAL coincide con el de por área)",
                            "sub_area", SUBAREAS, "costo_total")
    tot_lin = matriz_costos(tot_sub + 2, "REAL por línea", "linea", lineas, "costo_total")
    grafico = BarChart()
    grafico.title = "Plan vs real por mes (todas las áreas)"
    grafico.height, grafico.width = 8, 18
    s1 = Series(Reference(ws, min_col=2, max_col=1 + len(meses), min_row=tot_plan, max_row=tot_plan),
                title="Plan")
    s2 = Series(Reference(ws, min_col=2, max_col=1 + len(meses), min_row=tot_real, max_row=tot_real),
                title="Real")
    grafico.append(s1)
    grafico.append(s2)
    grafico.set_categories(Reference(ws, min_col=2, max_col=1 + len(meses), min_row=5, max_row=5))
    ws.add_chart(grafico, f"A{tot_lin + 3}")
    ws.column_dimensions["A"].width = 16

    # ------------------------------------------------------------ BACKLOG
    ws = wb.create_sheet("BACKLOG")
    ws.sheet_properties.tabColor = "7030A0"
    celda(ws, 1, 1, "BACKLOG (REGLA-3) — envejecimiento de órdenes pendientes", font=F_TIT)
    tramos = [("0-30", ">=0", "<=30"), ("31-60", ">=31", "<=60"),
              ("61-90", ">=61", "<=90"), (">90", ">90", None)]

    def criterios_tramo(c1, c2):
        base = (f'{R.col("tblOrdenes", "estado")},"Pendiente",'
                f'{R.col("tblOrdenes", "backlog_dias")},"{c1}"')
        if c2:
            base += f',{R.col("tblOrdenes", "backlog_dias")},"{c2}"'
        return base

    encabezados(ws, 3, ["tramo (días)", "ordenes", "hh_estimadas"])
    for i, (nombre, c1, c2) in enumerate(tramos):
        fr = 4 + i
        celda(ws, fr, 1, nombre)
        celda(ws, fr, 2, f"=COUNTIFS({criterios_tramo(c1, c2)})")
        celda(ws, fr, 3, f'=SUMIFS({R.col("tblOrdenes", "horas_efectivas")},{criterios_tramo(c1, c2)})',
              fmt=FMT_HH)
    ws.conditional_formatting.add("B7:C7", CellIsRule(operator="greaterThan", formula=["0"],
                                                      fill=FILL_ROJO))

    def matriz_backlog(fila0, titulo, campo, valores):
        celda(ws, fila0, 1, titulo, font=F_SEC)
        encabezados(ws, fila0 + 1, [campo] + [t[0] for t in tramos])
        for i, v in enumerate(valores):
            fr = fila0 + 2 + i
            celda(ws, fr, 1, v)
            for j, (nombre, c1, c2) in enumerate(tramos):
                celda(ws, fr, 2 + j,
                      f'=COUNTIFS({criterios_tramo(c1, c2)},{R.col("tblOrdenes", campo)},$A{fr})')
        ncol = get_column_letter(1 + len(tramos))
        ws.conditional_formatting.add(
            f"{ncol}{fila0 + 2}:{ncol}{fila0 + 1 + len(valores)}",
            CellIsRule(operator="greaterThan", formula=["0"], fill=FILL_ROJO))
        return fila0 + 2 + len(valores) + 1

    f0 = matriz_backlog(10, "POR ESPECIALIDAD", "especialidad", list(ESPECIALIDADES))
    f1 = matriz_backlog(f0, "POR ÁREA", "area", areas)
    matriz_backlog(f1, "POR SUB-ÁREA (herencia: área sin subdividir con su propio nombre)",
                   "sub_area", SUBAREAS)
    for colw, w in (("A", 22), ("B", 10), ("C", 13), ("D", 10), ("E", 10)):
        ws.column_dimensions[colw].width = w

    # --------------------------------------------------- EQUIPOS_CRITICOS
    ws = wb.create_sheet("EQUIPOS_CRITICOS")
    ws.sheet_properties.tabColor = "7030A0"
    celda(ws, 1, 1, '="EQUIPOS CRÍTICOS — costo total de mantenimiento ("&p_moneda&") por equipo y mes"',
          font=F_TIT)
    celda(ws, 3, 1, "anio", font=F_NOTA)
    celda(ws, 4, 1, "equipo \\ mes", font=F_HDR, fill=FILL_HDR)
    for j, (anio, mes) in enumerate(meses):
        celda(ws, 3, 2 + j, anio, font=F_NOTA)
        celda(ws, 4, 2 + j, mes, font=F_HDR, fill=FILL_HDR)
    celda(ws, 4, 2 + len(meses), "TOTAL", font=F_HDR, fill=FILL_HDR)
    equipos = esperado["equipos_orden"]
    for i, eq in enumerate(equipos):
        fr = 5 + i
        celda(ws, fr, 1, eq)
        for j in range(len(meses)):
            cl = get_column_letter(2 + j)
            celda(ws, fr, 2 + j,
                  f'=SUMIFS({R.col("tblOrdenes", "costo_total")},'
                  f'{R.col("tblOrdenes", "equipo")},$A{fr},'
                  f'{R.col("tblOrdenes", "anio")},{cl}$3,'
                  f'{R.col("tblOrdenes", "mes")},{cl}$4)', fmt=FMT_DINERO)
        celda(ws, fr, 2 + len(meses), f"=SUM(B{fr}:{get_column_letter(1 + len(meses))}{fr})",
              fmt=FMT_DINERO)
    ult_eq = 4 + len(equipos)
    ws.conditional_formatting.add(
        f"B5:{get_column_letter(1 + len(meses))}{ult_eq}",
        ColorScaleRule(start_type="min", start_color="FFFFFF",
                       end_type="max", end_color="F8696B"))
    celda(ws, ult_eq + 2, 1, "Ordenado de mayor a menor gasto total (con los datos de ejemplo).", font=F_NOTA)
    ws.column_dimensions["A"].width = 14

    # --------------------------------------------------------- VALIDACION
    ws = wb.create_sheet("VALIDACION")
    ws.sheet_properties.tabColor = "C00000"
    celda(ws, 1, 1, "VALIDACIÓN DE IMPORTACIÓN (REGLA-10) — reporta, nunca bloquea", font=F_TIT)
    encabezados(ws, 3, ["chequeo", "resultado", "detalle"])
    oid, eid = R.col("tblOrdenes", "id_operacion"), R.col("tblEjecucion", "id_operacion")
    orden_c = R.col("tblOrdenes", "orden")
    ajid = R.col("tblAjustes", "id_operacion")
    # Todos los chequeos ignoran las filas provisionadas vacías (orden = "").
    chequeos = [
        ("Órdenes duplicadas por id_operacion",
         f"=SUMPRODUCT(--({oid}<>\"\"),--(COUNTIF({oid},{oid})>1))",
         "Filas de ORDENES cuyo id_operacion aparece más de una vez."),
        ("Órdenes sin fecha de inicio",
         f'=SUMPRODUCT(--({orden_c}<>""),--({R.col("tblOrdenes", "fecha_inicio")}=""))',
         "Sin fecha no hay semana, backlog ni plan."),
        ("Órdenes sin horas estimadas",
         f'=SUMPRODUCT(--({orden_c}<>""),--({R.col("tblOrdenes", "horas_estimadas")}=""))',
         "No cargan el perfil de HH (REGLA-6)."),
        ("Centros de costo fuera de catálogo",
         f'=SUMPRODUCT(--({R.col("tblOrdenes", "centro_costo")}<>""),'
         f'--ISNA(MATCH({R.col("tblOrdenes", "centro_costo")},{R.col("tblCECO", "codigo")},0)))',
         "Revisar CAT_CENTROS_COSTO."),
        ("Puestos de trabajo fuera de catálogo",
         f'=SUMPRODUCT(--({R.col("tblOrdenes", "puesto_trabajo")}<>""),'
         f'--ISNA(MATCH({R.col("tblOrdenes", "puesto_trabajo")},{R.col("tblPuestos", "codigo")},0)))',
         "Revisar CAT_PUESTOS."),
        ("Actividades fuera de catálogo",
         f'=SUMPRODUCT(--({R.col("tblOrdenes", "cod_actividad")}<>""),'
         f'--ISNA(MATCH({R.col("tblOrdenes", "cod_actividad")},{R.col("tblActividades", "codigo")},0)))',
         "Revisar CAT_ACTIVIDADES."),
        ("Tipos de OT fuera de catálogo (sin_clasificar)",
         f'=SUMPRODUCT(--({R.col("tblOrdenes", "tipo_ot")}<>""),'
         f'--ISNA(MATCH({R.col("tblOrdenes", "tipo_ot")},{R.col("tblTiposOT", "codigo")},0)))',
         "REGLA-1 las marca sin_clasificar; agregar el código a CAT_TIPOS_OT."),
        ("Registros de EJECUCION sin par en ORDENES",
         f"=SUMPRODUCT(--({eid}<>\"\"),--ISNA(MATCH({eid},{oid},0)))",
         "Estados/costos que no encuentran su orden."),
        ("Órdenes sin par en EJECUCION",
         f"=SUMPRODUCT(--({oid}<>\"\"),--ISNA(MATCH({oid},{eid},0)))",
         "Quedan como \"Pendiente\" (comportamiento esperado)."),
        ("Órdenes con ajuste manual de horas (tblAjustes)",
         f"=SUMPRODUCT(--({oid}<>\"\"),--ISNUMBER(MATCH({oid},{ajid},0)))",
         "Órdenes cuyo id_operacion tiene ajuste en la hoja AJUSTES."),
        ("Desviación total de horas (ajustadas − estándar ERP)",
         f'=SUM({R.col("tblAjustes", "desviacion_h")})',
         "Suma de desviacion_h de AJUSTES (solo filas aplicadas)."),
        ("Ajustes huérfanos (id_operacion no existe en ORDENES)",
         f"=SUMPRODUCT(--({ajid}<>\"\"),--ISNA(MATCH({ajid},{oid},0)))",
         "Típicamente órdenes ya cerradas o purgadas; el ajuste no se aplica."),
        ("id_operacion duplicados dentro de tblAjustes",
         f"=SUMPRODUCT(--({ajid}<>\"\"),--(COUNTIF({ajid},{ajid})>1))",
         "Se aplica la primera fila; las demás se ignoran (ver estado_ajuste)."),
    ]
    for i, (nombre, formula, detalle) in enumerate(chequeos):
        fr = 4 + i
        celda(ws, fr, 1, nombre)
        celda(ws, fr, 2, formula)
        celda(ws, fr, 3, detalle, font=F_NOTA)
    ws.conditional_formatting.add(f"B4:B{3 + len(chequeos)}",
                                  CellIsRule(operator="greaterThan", formula=["0"], fill=FILL_AMAR))
    celda(ws, 5 + len(chequeos), 1,
          "La validación no bloquea: todo se importa y aquí se reporta (REGLA-10).", font=F_NOTA)
    for colw, w in (("A", 44), ("B", 11), ("C", 62)):
        ws.column_dimensions[colw].width = w

    # ---------------------------------------------------------- CATÁLOGOS
    catalogos = [
        ("CAT_CENTROS_COSTO", "tblCECO", CENTROS_COSTO,
         "Catálogo de centros de costo — se carga por empresa", None),
        ("CAT_PUESTOS", "tblPuestos", PUESTOS,
         "Catálogo de puestos de trabajo → especialidad", ("B", '"ELE,MEC,AUT,OP,TERCERO"')),
        ("CAT_ACTIVIDADES", "tblActividades", ACTIVIDADES,
         "Catálogo de actividades", ("C", '"correctivo,preventivo,predictivo,legal"')),
        ("CAT_TIPOS_OT", "tblTiposOT", TIPOS_OT,
         "Traducción de tipos de OT del ERP → preventiva/correctiva (REGLA-1)",
         ("C", '"preventiva,correctiva"')),
        ("CAT_ESTADOS_ERP", "tblEstados", ESTADOS_ERP,
         "Traducción de estados del ERP → Cerrada/Pendiente", ("B", '"Cerrada,Pendiente"')),
    ]
    for hoja, tnombre, filas_cat, titulo, val in catalogos:
        ws = wb.create_sheet(hoja)
        ws.sheet_properties.tabColor = "808080"
        tb = TAB[tnombre]
        celda(ws, 1, 1, titulo + " — editable", font=F_SEC)
        encabezados(ws, tb.fila_enc, tb.campos)
        for i, fila_cat in enumerate(filas_cat):
            for j, v in enumerate(fila_cat, start=1):
                celda(ws, tb.fila_ini + i, j, v, font=F_EDIT)
        agregar_tabla(ws, tb)
        if val:
            colv, lista = val
            dv = DataValidation(type="list", formula1=lista, allow_blank=False)
            ws.add_data_validation(dv)
            dv.add(f"{colv}{tb.fila_ini}:{colv}{tb.fila_fin}")
        for j in range(len(tb.campos)):
            ws.column_dimensions[get_column_letter(j + 1)].width = 22

    # ----------------------------------------------------------- EXPORTAR
    # Correo redactado en una sola celda (A6), armado desde una zona auxiliar
    # a la derecha (no editable). Sin macros y sin LET (LibreOffice no evalúa
    # _xlfn.LET, lo que rompería la verificación de la variante compatible):
    # la legibilidad se logra con una columna por magnitud. El ordenamiento y
    # el "top N" se resuelven con clave numérica + SUMPRODUCT/INDEX/MATCH,
    # nunca con SORT/FILTER (funciones de derrame, prohibidas).
    ws = wb.create_sheet("EXPORTAR")
    ws.sheet_properties.tabColor = "ED7D31"
    celda(ws, 1, 1, "EXPORTAR — correo del programa semanal, listo para copiar y enviar. "
                    "Elija los filtros y copie la celda A6.", font=F_TIT)
    for etiqueta, colc, lista, defecto in [("semana", 2, ["(todos)"] + semanas, semanas[1]),
                                           ("turno", 4, ["(todos)"] + list(TURNOS), "(todos)"),
                                           ("coordinador", 6,
                                            ["(todos)"] + sorted(set(COORD_POR_AREA.values())), "(todos)"),
                                           ("sub-área", 8, ["(todos)"] + SUBAREAS, "(todos)")]:
        celda(ws, 3, colc - 1, etiqueta + ":", font=F_SEC)
        celda(ws, 3, colc, defecto, font=F_EDIT, fill=FILL_GRIS)
        dv = DataValidation(type="list", formula1='"' + ",".join(lista) + '"', allow_blank=False)
        ws.add_data_validation(dv)
        dv.add(f"{get_column_letter(colc)}3")

    MAXPROG, MAXTOP, NT = 200, 20, len(TECNICOS)
    F0 = 8                       # primera fila de todas las zonas auxiliares
    FN = 7 + CAP_FILAS           # última fila de la zona por-orden (1:1 tblOrdenes)
    # columnas auxiliares
    cK, cL, cM, cN, cO, cP, cQ, cR, cS, cT = 11, 12, 13, 14, 15, 16, 17, 18, 19, 20
    cU, cV, cW = 21, 22, 23      # emisión del programa (ordenado)
    cY, cZ = 25, 26              # emisión del top de tareas
    cAB, cAC, cAD, cAE, cAF, cAG = 28, 29, 30, 31, 32, 33   # por técnico
    cAJ, cAL = 36, 38            # escalares / textos de sección
    L = get_column_letter

    def rng(col, hasta=FN):
        return f"${L(col)}${F0}:${L(col)}${hasta}"

    def oc(campo):               # columna entera de tblOrdenes (para INDEX/SUMIFS)
        return R.col("tblOrdenes", campo)

    celda(ws, 6, cU, "zona auxiliar de cálculo — no editar", font=F_NOTA)

    # --- Zona por-orden (1:1 con tblOrdenes) --------------------------------
    for i in range(CAP_FILAS):
        r = F0 + i
        fo = O.fila_ini + i
        ridx = i + 1

        def rr(campo):
            return f"'ORDENES'!${O.letra(campo)}{fo}"
        scope = (f'AND(IF($B$3="(todos)",TRUE,{rr("semana")}=$B$3),'
                 f'IF($D$3="(todos)",TRUE,{rr("turno_asignado")}=$D$3),'
                 f'IF($F$3="(todos)",TRUE,{rr("coordinador")}=$F$3),'
                 f'IF($H$3="(todos)",TRUE,{rr("sub_area")}=$H$3),'
                 f'{rr("en_plan")}=TRUE,{rr("orden")}<>"")')
        celda(ws, r, cK, f"=IF({scope},1,0)")
        di = f'IFERROR(MATCH({rr("dia_semana")},lista_dias,0),9)'
        ti = f'IFERROR(MATCH({rr("turno_asignado")},lista_turnos,0),9)'
        ci = f'IFERROR(MATCH({rr("tecnico_asignado")},{R.col("tblTecnicos", "nombre")},0),99)'
        celda(ws, r, cL, f'=IF({L(cK)}{r}=1,{di}*1000000000+{ti}*10000000+{ci}*100000+{ridx},'
                         f'9000000000000+{ridx})')
        # posición solo para filas en alcance; en blanco fuera de alcance para
        # que el emisor se detenga en la última (MATCH falla → "").
        celda(ws, r, cM, f'=IF({L(cK)}{r}=1,SUMPRODUCT(--({rng(cL)}<{L(cL)}{r}))+1,"")')
        celda(ws, r, cN, f'=IF({L(cK)}{r}=1,N({rr("horas_efectivas")}),0)', fmt=FMT_HH)
        celda(ws, r, cO, f'=IF({rr("clasificacion")}="preventiva",{L(cN)}{r},0)', fmt=FMT_HH)
        celda(ws, r, cP, f'=IF({rr("clasificacion")}="correctiva",{L(cN)}{r},0)', fmt=FMT_HH)
        celda(ws, r, cT, f'=IF({L(cK)}{r}=1,{rr("fecha_inicio")},"")', fmt=FMT_FECHA)
        celda(ws, r, cQ, f'=IF(AND({L(cK)}{r}=1,{rr("estado")}="Pendiente"),1,0)')
        celda(ws, r, cR, f'=IF({L(cQ)}{r}=1,100000-{L(cN)}{r}*1000+{ridx}*0.01,'
                         f'9000000000000+{ridx})')
        celda(ws, r, cS, f'=IF({L(cQ)}{r}=1,SUMPRODUCT(--({rng(cR)}<{L(cR)}{r}))+1,"")')

    # --- Emisión del programa completo (ordenado por día, turno, técnico) ---
    def idx(campo, kcell):
        return f"INDEX({oc(campo)},{kcell})"
    for p in range(1, MAXPROG + 1):
        r = F0 + p - 1
        k = f"{L(cU)}{r}"
        celda(ws, r, cU, f"=IFERROR(MATCH({p},{rng(cM)},0),\"\")")
        celda(ws, r, cV, f'=IF({k}="","",{idx("dia_semana", k)})')
        cab_dia = (f'IF({L(cV)}{r}<>{L(cV)}{r - 1},CHAR(10)&UPPER(LEFT({L(cV)}{r},1))&'
                   f'MID({L(cV)}{r},2,20)&":"&CHAR(10),"")')
        linea = (f'"   "&IF({idx("turno_asignado", k)}="","(s/t)",{idx("turno_asignado", k)})&'
                 f'" · "&IF({idx("tecnico_asignado", k)}="","(sin técnico)",{idx("tecnico_asignado", k)})&'
                 f'" · "&{idx("id_operacion", k)}&" — "&{idx("descripcion_operacion", k)}&'
                 f'" ("&TEXT({idx("horas_efectivas", k)},"0.#")&" h)"')
        celda(ws, r, cW, f'=IF({k}="","",{cab_dia}&{linea})')

    # --- Emisión del top de tareas relevantes -------------------------------
    for j in range(1, MAXTOP + 1):
        r = F0 + j - 1
        k = f"{L(cY)}{r}"
        celda(ws, r, cY, f"=IFERROR(MATCH({j},{rng(cS)},0),\"\")")
        linea = (f'"   • "&{idx("equipo", k)}&" — "&{idx("descripcion_operacion", k)}&'
                 f'" · "&TEXT({idx("horas_efectivas", k)},"0.#")&" h · "&'
                 f'IF({idx("tecnico_asignado", k)}="","(sin técnico)",{idx("tecnico_asignado", k)})&'
                 f'IF({idx("permiso_requerido", k)}<>""," · permiso de trabajo","")&'
                 f'IF({idx("bloqueo_energia", k)}<>""," · bloqueo de energía (LOTO)","")')
        celda(ws, r, cZ, f'=IF(OR({k}="",{j}>p_top_tareas),"",{linea})')

    # --- Bloque por técnico (carga vs capacidad en el filtro) ---------------
    for t in range(NT):
        r = F0 + t
        tn = f"{L(cAB)}{r}"
        celda(ws, r, cAB, f"='TECNICOS'!$B${TAB['tblTecnicos'].fila_ini + t}")
        celda(ws, r, cAC, f"=SUMPRODUCT({rng(cN)},--({oc('tecnico_asignado')}={tn}))", fmt=FMT_HH)
        celda(ws, r, cAD, f'=p_factor_productividad*SUMIFS({R.col("tblAsignaciones", "horas_disponibles")},'
                          f'{R.col("tblAsignaciones", "tecnico")},{tn},'
                          f'{R.col("tblAsignaciones", "semana")},IF($B$3="(todos)","*",$B$3))', fmt=FMT_HH)
        celda(ws, r, cAE, f"=IF({L(cAC)}{r}>{L(cAD)}{r}+0.0001,1,0)")
        celda(ws, r, cAF, f'=IF({L(cAE)}{r}=1,"   • "&{tn}&": "&TEXT({L(cAC)}{r},"0.0")&'
                          f'" h asignadas vs "&TEXT({L(cAD)}{r},"0.0")&" h de capacidad","")')
        celda(ws, r, cAG, f"=IF(SUMPRODUCT({rng(cK)},--({oc('tecnico_asignado')}={tn}))>0,1,0)")

    # --- Escalares del resumen ---------------------------------------------
    esc = [("órdenes programadas", f"=SUM({rng(cK)})"),
           ("hh_total", f"=SUM({rng(cN)})"),
           ("hh_preventiva", f"=SUM({rng(cO)})"),
           ("hh_correctiva", f"=SUM({rng(cP)})"),
           ("técnicos involucrados", f"=SUM({rng(cAG, F0 + NT - 1)})"),
           ("técnicos sobreasignados", f"=SUM({rng(cAE, F0 + NT - 1)})"),
           ("lunes_sel", None), ("domingo_sel", None),
           ("órdenes pendientes en plan", f"=SUM({rng(cQ)})")]
    yy = f"VALUE(LEFT($B$3,4))"
    lun = (f'DATE({yy},1,4)-WEEKDAY(DATE({yy},1,4),2)+1+(VALUE(MID($B$3,7,2))-1)*7')
    esc[6] = ("lunes_sel",
              f'=IF($B$3="(todos)",IF({L(cAJ)}{F0}=0,"",MIN({rng(cT)})),{lun})')
    esc[7] = ("domingo_sel",
              f'=IF($B$3="(todos)",IF({L(cAJ)}{F0}=0,"",MAX({rng(cT)})),{L(cAJ)}{F0 + 6}+6)')
    for m, (lab, formula) in enumerate(esc):
        r = F0 + m
        celda(ws, r, cAJ - 1, lab, font=F_NOTA)
        fmt = FMT_FECHA if lab in ("lunes_sel", "domingo_sel") else None
        celda(ws, r, cAJ, formula, fmt=fmt)
    A = lambda m: f"${L(cAJ)}${F0 + m}"   # ancla a un escalar por su índice

    # --- Textos de sección (bloques condicionales que desaparecen limpios) --
    s1 = (f'="Buenos días."&CHAR(10)&"A continuación el programa de mantenimiento de "&'
          f'p_nombre_planta&" — "&p_nombre_empresa&'
          f'IF($B$3="(todos)"," para las semanas seleccionadas."," para la semana "&$B$3&'
          f'", del "&TEXT({A(6)},"dd/mm/yyyy")&" al "&TEXT({A(7)},"dd/mm/yyyy")&".")&'
          f'IF(AND($D$3="(todos)",$F$3="(todos)",$H$3="(todos)"),"",CHAR(10)&'
          f'"(Filtro aplicado — turno: "&$D$3&", coordinador: "&$F$3&", sub-área: "&$H$3&")")')
    s2 = (f'="Resumen de carga:"&CHAR(10)&'
          f'"• Órdenes programadas: "&{A(0)}&CHAR(10)&'
          f'"• HH planificadas: "&TEXT({A(1)},"0.#")&" h"&CHAR(10)&'
          f'"• Preventiva: "&TEXT({A(2)},"0.#")&" h ("&TEXT(IF({A(1)}=0,0,{A(2)}/{A(1)}),"0%")&")"&CHAR(10)&'
          f'"• Correctiva: "&TEXT({A(3)},"0.#")&" h ("&TEXT(IF({A(1)}=0,0,{A(3)}/{A(1)}),"0%")&")"&CHAR(10)&'
          f'"• Técnicos involucrados: "&{A(4)}')
    s3 = (f'=IF({A(5)}=0,"","Alerta de capacidad — técnicos sobreasignados:"&CHAR(10)&'
          f'_xlfn.TEXTJOIN(CHAR(10),TRUE,{rng(cAF, F0 + NT - 1)}))')
    s4 = (f'=IF({A(8)}=0,"","Tareas relevantes (top "&MIN(p_top_tareas,{A(8)})&" por horas):"&CHAR(10)&'
          f'_xlfn.TEXTJOIN(CHAR(10),TRUE,{rng(cZ, F0 + MAXTOP - 1)}))')
    s5 = (f'=IF({A(0)}=0,"(Sin órdenes en el filtro seleccionado.)","Programa completo:"&CHAR(10)&'
          f'_xlfn.TEXTJOIN(CHAR(10),TRUE,{rng(cW, F0 + MAXPROG - 1)}))')
    s6 = '="Cualquier ajuste, favor comunicarlo antes del inicio del turno."'
    for m, sec in enumerate([s1, s2, s3, s4, s5, s6]):
        celda(ws, F0 + m, cAL, sec)

    celda(ws, 5, 1, "correo (seleccione A6, copie y pegue en el cuerpo del mensaje):", font=F_SEC)
    master = (f'=_xlfn.TEXTJOIN(CHAR(10)&CHAR(10),TRUE,'
              + ",".join(f"${L(cAL)}${F0 + m}" for m in range(6)) + ")")
    celda(ws, 6, 1, master, wrap=True)
    ws.merge_cells(start_row=6, start_column=1, end_row=110, end_column=8)
    for colw, w in (("A", 20), ("B", 16), ("C", 14), ("D", 14), ("E", 14), ("F", 16), ("G", 14), ("H", 14)):
        ws.column_dimensions[colw].width = w

    # ---------------------------------------------------- _COMPATIBILIDAD
    ws = wb.create_sheet("_COMPATIBILIDAD")
    ws.sheet_properties.tabColor = "808080"
    celda(ws, 1, 1, "_COMPATIBILIDAD — equivalentes INDEX/MATCH para Excel 2016 o anterior", font=F_TIT)
    celda(ws, 2, 1, "Las columnas calculadas de ORDENES usan XLOOKUP (Excel 2021/365). Si su Excel no lo tiene, "
                    "reemplace cada fórmula por su equivalente de la columna C. El ejemplo vivo de la columna D "
                    "calcula la primera fila de ORDENES con INDEX/MATCH.", font=F_NOTA, wrap=True)
    ws.merge_cells("A2:F2")
    encabezados(ws, 4, ["campo", "fórmula con XLOOKUP (como en tblOrdenes)",
                        "equivalente INDEX/MATCH", "ejemplo vivo (fila 1 de ORDENES)"])
    Rx = Refs("estructuradas", TAB)
    fila_o1 = O.fila_ini

    def ejemplo(campo):
        def a1(c):
            return f"'ORDENES'!${O.letra(c)}${fila_o1}"
        if campo == "estado":
            interna = R.busca_im(a1("id_operacion"), "tblEjecucion", "id_operacion",
                                 "estado_sistema", '""')
            return "=" + R.busca_im(interna, "tblEstados", "estado_sistema",
                                    "estado_normalizado", '"Pendiente"')
        if campo == "clasificacion":
            return "=" + R.busca_im(a1("tipo_ot"), "tblTiposOT", "codigo", "clasificacion",
                                    '"sin_clasificar"')
        if campo in ("linea", "area", "coordinador"):
            return "=" + R.busca_im(a1("centro_costo"), "tblCECO", "codigo", campo,
                                    f'"{SIN_CATALOGO}"')
        if campo == "sub_area":
            sub = R.busca_im(a1("centro_costo"), "tblCECO", "codigo", "sub_area", '""')
            area = R.busca_im(a1("centro_costo"), "tblCECO", "codigo", "area", f'"{SIN_CATALOGO}"')
            return f'=IF({a1("centro_costo")}="","",IF(({sub})<>"",{sub},{area}))'
        if campo == "especialidad":
            return "=" + R.busca_im(a1("puesto_trabajo"), "tblPuestos", "codigo",
                                    "especialidad", f'"{SIN_CATALOGO}"')
        if campo == "actividad":
            return "=" + R.busca_im(a1("cod_actividad"), "tblActividades", "codigo",
                                    "descripcion", f'"{SIN_CATALOGO}"')
        if campo == "horas_efectivas":
            est = a1("horas_estimadas")
            return "=" + R.busca_im(a1("id_operacion"), "tblAjustes", "id_operacion",
                                    "horas_ajustadas", f'IF({est}="","",{est})')
        if campo == "turno_asignado":
            clave = f'{a1("semana")}&"|"&{a1("dia_semana")}&"|"&{a1("tecnico_asignado")}'
            return f'=IF({a1("tecnico_asignado")}="","",' + \
                R.busca_im(clave, "tblAsignaciones", "clave", "turno", '""') + ")"
        if campo == "costo_servicio":
            return "=" + R.busca_im(a1("id_operacion"), "tblEjecucion", "id_operacion",
                                    "precio", "0")
        if campo == "costo_materiales":
            pt = R.busca_im(a1("id_operacion"), "tblEjecucion", "id_operacion",
                            "costo_plan_total", "0")
            return f'=MAX(0,{pt}-{a1("costo_servicio")})'
        raise KeyError(campo)

    campos_comp = ["estado", "clasificacion", "linea", "area", "sub_area", "coordinador",
                   "especialidad", "actividad", "horas_efectivas", "turno_asignado",
                   "costo_servicio", "costo_materiales"]
    FX = formulas_ordenes(Rx)
    for i, campo in enumerate(campos_comp):
        fr = 5 + i
        celda(ws, fr, 1, campo)
        # Los textos de las columnas B y C se escriben sin el "=" inicial para
        # que queden como texto documental y no como fórmula.
        celda(ws, fr, 2, FX[campo](fila_o1).replace("_xlfn.", "").lstrip("="),
              font=F_NOTA, wrap=True)
        im = ejemplo(campo)
        celda(ws, fr, 3, im.lstrip("="), font=F_NOTA, wrap=True)
        celda(ws, fr, 4, im)
    for colw, w in (("A", 18), ("B", 64), ("C", 64), ("D", 22)):
        ws.column_dimensions[colw].width = w

    # Orden final de hojas: EXPORTAR y _COMPATIBILIDAD ya quedan al final tras los catálogos.
    wb.save(ruta)
    return ruta


# ══════════════════════════════════════════════════════════════════════════
# 8. RESUMEN PARA VERIFICACIÓN MANUAL
# ══════════════════════════════════════════════════════════════════════════


def imprimir_resumen(datos, esperado):
    hoy, semanas = datos["hoy"], datos["semanas"]
    print(f"MantPlan — datos sintéticos anclados a HOY = {hoy.isoformat()}")
    print(f"Órdenes: {len(datos['ordenes'])} · Ejecución: {len(datos['ejecucion'])} · "
          f"Asignaciones: {len(datos['asignaciones'])} · Semanas del plan: {', '.join(semanas)}")
    print(f"Serie de semanas con datos: {len(esperado['serie_semanas'])} "
          f"({esperado['serie_semanas'][0]} … {esperado['serie_semanas'][-1]}), "
          f"{len(esperado['semanas_con_datos'])} con órdenes")
    print("\nPERFIL_HH esperado (REGLA-6, solo semanas del plan; el libro genera hasta 60):")
    print(f"{'esp':8}{'semana':10}{'disp':>7}{'prod':>9}{'prev':>7}{'corr':>7}{'plan':>7}{'holgura':>9}{'%carga':>9}")
    for esp in ESPECIALIDADES:
        for sem in semanas:
            p = esperado["perfil"][(esp, sem)]
            pct = f"{p['pct_carga']:.1%}" if p["pct_carga"] is not None else "—"
            print(f"{esp:8}{sem:10}{p['hh_disponible']:>7.0f}{p['hh_productiva']:>9.2f}"
                  f"{p['hh_preventiva']:>7.0f}{p['hh_correctiva']:>7.0f}{p['hh_planificada']:>7.0f}"
                  f"{p['holgura']:>9.2f}{pct:>9}")
    print("\nADHERENCIA esperada por semana (REGLA-7):")
    for sem in semanas:
        a = esperado["adherencia"][("semana", sem)]
        ac = f"{a['adherencia_conteo']:.1%}" if a["adherencia_conteo"] is not None else "—"
        ah = f"{a['adherencia_horas']:.1%}" if a["adherencia_horas"] is not None else "—"
        print(f"  {sem}: {a['cerradas']}/{a['total']} OT cerradas = {ac} · "
              f"{a['hh_cerradas']:.0f}/{a['hh_total']:.0f} HH = {ah}")
    print("\nRATIO corr/prev esperado por semana (REGLA-9, semanas del plan):")
    for sem in semanas:
        prev, corr, ratio, pct = esperado["ratio9"][sem]
        print(f"  {sem}: prev {prev:.0f} h · corr {corr:.0f} h · ratio {ratio:.2f} · "
              f"correctivo {pct:.1%} del total")
    print("\nCruce de fin de año (REGLA-2 v2):")
    for o in esperado["ordenes"]:
        if o["fecha_inicio"] and o["fecha_inicio"].month in (12, 1) and o["_grupo"] == "futuro":
            print(f"  {o['id_operacion']}: fecha {o['fecha_inicio']} → semana {o['semana']} "
                  f"(anio YEAR = {o['anio']})")
    print("\nAjustes manuales (tblAjustes → horas_efectivas por id_operacion):")
    for a, ax in zip(datos["ajustes"], esperado["ajustes_esperado"]):
        extra = f" · desviación {ax['desviacion_h']:+}" if ax["desviacion_h"] != "" else ""
        print(f"  {a['id_operacion']}: {a['horas_ajustadas']} h → {ax['estado_ajuste']}{extra}")
    ve = esperado["validacion_extra"]
    print(f"  VALIDACION → órdenes ajustadas: {ve['ajustadas']} · desviación total: "
          f"{ve['desviacion_horas']:+.0f} h · huérfanos: {ve['huerfanos']} · "
          f"duplicados en tblAjustes: {ve['duplicados_ajustes']}")
    print("\nBACKLOG esperado (pendientes por tramo):")
    for tramo, (n, hh) in esperado["backlog_aging"].items():
        print(f"  {tramo:>6}: {n} órdenes · {hh:.0f} h")
    sem1 = semanas[1]
    print(f"\nCARGA SEMANAL POR TÉCNICO (gráfico de PLAN_SEMANAL, selector por defecto {sem1}):")
    for _tid, nombre, esp_t, _area in TECNICOS:
        c = esperado["carga_tecnicos"][(sem1, nombre)]
        cap = esperado["capacidad_tecnicos"][(sem1, nombre)]
        print(f"  {nombre} ({esp_t}): HHA {c:>5.1f} · capacidad {cap:>6.2f} · "
              f"dentro {min(c, cap):>6.2f} · sobre {max(0, c - cap):>5.2f}")
    print(f"\nHHA/HHD por día — Técnico 01, semana {sem1} "
          f"(disponibilidad normal = 7 h × 0,87 = {HORAS_JORNADA * FACTOR_PRODUCTIVIDAD:.2f} h):")
    for dia in DIAS[:5]:
        ords = [o for o in esperado["ordenes"] if o["tecnico_asignado"] == "Técnico 01"
                and o["semana"] == sem1 and o["dia_semana"] == dia]
        if not ords:
            print(f"  {dia:10}: sin órdenes")
            continue
        hha = ords[0]["HHA"]
        print(f"  {dia:10}: {' + '.join(str(o['horas_estimadas']) for o in ords)} h "
              f"→ HHA {hha} · HHD {ords[0]['HHD']:+.2f}")
    demo = next((o for o in esperado["ordenes"]
                 if str(o.get("observaciones", "")).startswith("Demo:")), None)
    if demo:
        print(f"  Conflicto demo: {demo['id_operacion']} asignada a {demo['tecnico_asignado']} "
              f"({demo['semana']} {demo['dia_semana']}, turno \"{demo['turno_asignado']}\") → "
              f"disponibilidad 0 → HHA {demo['HHA']} · HHD {demo['HHD']:+.2f}")
    print("\nSUB-ÁREAS (jerarquía área → sub-área → CECO; herencia si vacía):")
    for area, subs in SUBAREAS_POR_AREA.items():
        print(f"  {area}: {', '.join(subs)}")
    print("  COSTO_TOTAL real por sub-área (suma de sus CECOs) y control por área:")
    for area in COORD_POR_AREA:
        tot_area = sum(o["costo_total"] for o in esperado["ordenes"] if o["area"] == area)
        for sa in SUBAREAS_POR_AREA[area]:
            tot_sa = sum(o["costo_total"] for o in esperado["ordenes"] if o["sub_area"] == sa)
            print(f"    {area:11} · {sa:16}: {tot_sa:>8,.0f}")
        suma_subs = sum(o["costo_total"] for o in esperado["ordenes"]
                        if o["sub_area"] in SUBAREAS_POR_AREA[area])
        print(f"    {area:11} · {'TOTAL área':16}: {tot_area:>8,.0f}  "
              f"(Σ sub-áreas = {suma_subs:,.0f}; {'cuadra' if suma_subs == tot_area else 'DESCUADRE'})")

    ex = esperado["exportar"]
    print(f"\nCORREO (EXPORTAR) esperado — filtro por defecto semana {ex['semana']}, "
          f"turno/coordinador (todos):")
    print(f"  Órdenes programadas: {ex['n_ord']} · HH {ex['hh_total']:.0f} "
          f"(prev {ex['hh_prev']:.0f} / corr {ex['hh_corr']:.0f}) · técnicos {ex['n_tec']}")
    print(f"  Sobreasignados: {', '.join(ex['sobreasignados']) or '(ninguno)'}")
    for n in ex["sobreasignados"]:
        h, c, _ = ex["por_tec"][n]
        print(f"    {n}: {h:.1f} h asignadas vs {c:.2f} h de capacidad")
    print(f"  Top {min(5, ex['n_top'])} tareas (de {ex['n_top']} pendientes en plan):")
    for o in ex["top"]:
        marca = ("permiso" if o["permiso_requerido"] else "") + \
                ("+LOTO" if o["bloqueo_energia"] else "")
        print(f"    {o['equipo']} · {o['horas_efectivas']} h · "
              f"{o['tecnico_asignado'] or '(sin técnico)'}{' · ' + marca if marca else ''}")
    print("\nVALIDACION esperada (REGLA-10):")
    for k, v in esperado["validacion"].items():
        print(f"  {k}: {v}")
    print("\nEquipos con mayor gasto (costo_total):")
    for eq in esperado["equipos_orden"][:5]:
        print(f"  {eq}: {esperado['equipos_tot'][eq]:,.0f} USD")
    print(f"\nÓrdenes con precio > costo_plan_total (REGLA-8 → materiales 0): "
          f"{', '.join(datos['edge_regla8'])}")


def main(argv=None):
    ap = argparse.ArgumentParser(description="Genera MantPlan.xlsx (Entregable A)")
    ap.add_argument("--salida", default="MantPlan.xlsx")
    ap.add_argument("--fecha-ancla", default=None,
                    help="AAAA-MM-DD; por defecto la fecha de hoy (backlog usa HOY()).")
    ap.add_argument("--refs", choices=["estructuradas", "compatibles"], default="estructuradas",
                    help="compatibles = INDEX/MATCH + rangos A1 (verificación / Excel 2016)")
    ap.add_argument("--resumen", action="store_true", help="imprime los números esperados")
    args = ap.parse_args(argv)

    hoy = date.fromisoformat(args.fecha_ancla) if args.fecha_ancla else date.today()
    datos = generar_datos(hoy)
    esperado = calcular_esperado(datos)
    construir_libro(datos, esperado, args.salida, refs=args.refs)
    print(f"Generado {args.salida} (refs {args.refs}, ancla {hoy.isoformat()})")
    if args.resumen:
        print()
        imprimir_resumen(datos, esperado)


if __name__ == "__main__":
    main()
