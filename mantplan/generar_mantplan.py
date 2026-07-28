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
    python generar_mantplan.py --anio-completo        # §7: banco de prueba de un año

`--refs compatibles` produce el mismo libro pero con INDEX/MATCH y rangos
A1 acotados en lugar de XLOOKUP y referencias estructuradas. Se usa para
verificar el libro con motores de cálculo que aún no implementan XLOOKUP
(p. ej. LibreOffice ≤ 24.2) y sirve también para entornos con Excel 2016.

Requiere: openpyxl  (pip install openpyxl)
"""

from __future__ import annotations

import argparse
import random
import time
from dataclasses import dataclass, field
from datetime import date, timedelta

from openpyxl import Workbook
from openpyxl.chart import BarChart, LineChart, Reference, Series
from openpyxl.chart.label import DataLabelList
from openpyxl.chart.marker import Marker
from openpyxl.formatting.rule import CellIsRule, ColorScaleRule, FormulaRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.workbook.defined_name import DefinedName
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.worksheet.properties import PageSetupProperties
from openpyxl.worksheet.table import Table, TableStyleInfo

VERSION = "3.3.0"

# Capacidad de las tablas de datos: filas provisionadas con fórmulas para que
# una importación mensual grande no requiera tocar el libro.
CAP_FILAS = 1200

# 7.2: dominio sí/no UNIFICADO en minúsculas y con tilde ("sí"/"no"), que es lo
# que ya producían es_habil, en_vacaciones, trabaja_domingo y el patrón semanal.
SI, NO = "sí", "no"

# ══════════════════════════════════════════════════════════════════════════
# 1. PARÁMETROS (Tabla 10) Y CATÁLOGOS SINTÉTICOS
#    Los catálogos son ficticios: el motor jamás depende de sus valores.
# ══════════════════════════════════════════════════════════════════════════

PARAMETROS = [
    # (parametro, valor, descripcion)
    ("nombre_empresa", "Empresa Ejemplo S.A.", "Editable. Solo informativo, no participa en cálculos."),
    ("nombre_planta", "Planta Ejemplo", "Editable. Solo informativo."),
    ("moneda", "USD", "Moneda de los costos."),
    ("horas_jornada", 8, "Horas de trabajo por técnico y día (REGLA-5)."),
    ("factor_productividad", 0.87, "Fracción productiva de la jornada (REGLA-6)."),
    ("turnos", "B,T1,T2,T3", "Códigos de turno válidos. La definición manda en CAT_TURNOS."),
    ("codigos_no_disponible", "VAC,X", "Códigos que anulan la disponibilidad (REGLA-5)."),
    ("dias_backlog_max", 30, "Días hacia atrás que siguen siendo plan (REGLAS 3 y 4)."),
    ("dias_backlog_min", -92, "Días hacia adelante (negativo) que entran al plan (REGLA-4)."),
    ("meta_adherencia", 0.95, "Meta de adherencia semanal (REGLA-7)."),
    ("meta_ratio_prev_corr", 0.80, "Meta: fracción preventiva mínima de las HH (REGLA-9)."),
    ("primer_dia_semana", "lunes", "Inicio de semana. La semana ISO (REGLA-2) empieza en lunes."),
    ("ruta_base_checklists", "C:\\MANTPLAN\\checklists\\", "Base para los hipervínculos de la columna link_checklist."),
    ("top_tareas", 5, "Nº de tareas relevantes que lista el correo de EXPORTAR."),
    ("dias_laborables_base", 6,
     "Días laborables base por semana (lunes a sábado). Base de REGLA-5 / 48 h."),
    # base_semanal_horas es DERIVADO: su celda B se escribe como fórmula
    # (=p_horas_jornada*p_dias_laborables_base), fuente única de verdad.
    ("base_semanal_horas", "=p_horas_jornada*p_dias_laborables_base",
     "Base obligatoria por técnico y semana = horas_jornada × dias_laborables_base."),
    # 6.3: semana de referencia de la rotación de turnos. Es una FECHA (el lunes
    # de esa semana). En ella, orden_rotacion 1..N mapea directo a la posición
    # del anillo. Su valor se escribe al generar el libro (depende del ancla).
    ("semana_referencia", None,
     "FECHA (lunes) de la semana de referencia de la rotación de turnos (6.3)."),
    # 6.5: tolerancia del cumplimiento mensual de horas reales (base del bono).
    ("tolerancia_horas_bono", 0,
     "Horas de tolerancia para 'cumple' del seguimiento mensual (6.5). No toca capacidad."),
    # PRESUPUESTO OPEX: año presupuestado (se inyecta = año del ancla) y
    # tolerancia del semáforo de desviación. Ninguno toca el motor.
    ("anio_presupuesto", None,
     "Año del presupuesto OPEX de la hoja PRESUPUESTO (por defecto, el año del ancla)."),
    ("tolerancia_desviacion_presupuesto", 0.10,
     "Desviación relativa tolerada antes de marcar sobre/bajo presupuesto (semáforo)."),
    # DASHBOARD: fecha a la que están los datos del libro. El tablero corta con
    # ella y NUNCA con HOY(), para que la foto sea estable y reproducible. Se
    # inyecta al generar (= el ancla). REGLA-3/REGLA-4 siguen usando HOY() por
    # diseño: son el envejecimiento vivo del backlog, no la foto del tablero.
    ("fecha_datos", None,
     "FECHA de los datos del libro. El DASHBOARD corta con ella (mes en curso: hasta el día anterior)."),
    # DASHBOARD — metas de distribución del mix de mantenimiento. NO son
    # normativas: no salen de EN 15341 ni de VDI 2893, son convención de
    # industria y cada planta ajusta las suyas. Por eso son editables.
    ("meta_pct_predictivo", 25, "Meta de mix: % de órdenes predictivas. Convención, NO norma."),
    ("meta_pct_preventivo", 40, "Meta de mix: % de órdenes preventivas. Convención, NO norma."),
    ("meta_pct_correctivo_programado", 20,
     "Meta de mix: % de correctivos programados. Convención, NO norma."),
    ("meta_pct_emergencia", 5, "Meta de mix: % de emergencias. Convención, NO norma."),
    ("meta_pct_legal", 10, "Meta de mix: % de órdenes legales. Convención, NO norma."),
    # Cuadre DERIVADO de las metas (mismo patrón que el cuadre anual del
    # presupuesto): avisa si los cinco porcentajes no suman 100.
    ("cuadre_metas_mix",
     '=IF(p_meta_pct_predictivo+p_meta_pct_preventivo+p_meta_pct_correctivo_programado'
     '+p_meta_pct_emergencia+p_meta_pct_legal=100,"cuadra: 100 %","DESCUADRE: suman "'
     '&(p_meta_pct_predictivo+p_meta_pct_preventivo+p_meta_pct_correctivo_programado'
     '+p_meta_pct_emergencia+p_meta_pct_legal)&" %, deben sumar 100")',
     "Cuadre de las metas de mix. Derivado: avisa si los cinco porcentajes no suman 100."),
]
# Fila de cada parámetro dentro de la hoja PARAMETROS (encabezado en fila 3).
FILA_PARAM = {p[0]: 4 + i for i, p in enumerate(PARAMETROS)}

HORAS_JORNADA = 8
FACTOR_PRODUCTIVIDAD = 0.87
DIAS_LABORABLES_BASE = 6
BASE_SEMANAL_HORAS = HORAS_JORNADA * DIAS_LABORABLES_BASE
DIAS_BACKLOG_MAX = 30
DIAS_BACKLOG_MIN = -92
CODIGOS_NO_DISPONIBLE = ("VAC", "X")
# 6.2: catálogo de turnos con franja horaria. CAT_TURNOS es la fuente única de
# la definición de turnos. La franja es metadato de horario; la capacidad NO se
# deriva de ella (REGLA-5 sigue plana en horas_jornada). T3 cruza medianoche:
# es solo rótulo, no se calcula duración.
TURNOS_CAT = [
    # turno, nombre, hora_inicio, hora_fin, tipo (horas como texto "HH:MM")
    ("B", "Banco", "07:00", "16:00", "banco"),
    ("T1", "Turno 1", "06:00", "15:00", "rotativo"),
    ("T2", "Turno 2", "15:00", "22:00", "rotativo"),
    ("T3", "Turno 3", "22:00", "06:00", "rotativo"),
]
TURNOS = tuple(t[0] for t in TURNOS_CAT)   # ("B", "T1", "T2", "T3")
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

# ── Calendario laboral (v2.4) ─────────────────────────────────────────────
# Parte A: patrón semanal (lunes..domingo). Default L-V hábil, S-D no hábil.
PATRON_SEMANAL = [("lunes", "sí"), ("martes", "sí"), ("miércoles", "sí"),
                  ("jueves", "sí"), ("viernes", "sí"), ("sábado", "sí"),
                  ("domingo", "no")]
PATRON_HABIL = [h for _, h in PATRON_SEMANAL]   # índice 0=lunes … 6=domingo


def _fecha_ancla_year(hoy):
    return hoy.year


# Parte B: excepciones que rompen el patrón. area vacía = toda la planta;
# sub_area vacía = toda el área. Las fechas se fijan al año del ancla.
def construir_excepciones(hoy):
    y = hoy.year
    exc = [
        # ~12 feriados generales del año (area y sub_area vacías)
        (date(y, 1, 1), "feriado", "no", "", "", "Año Nuevo"),
        (date(y, 1, 6), "feriado", "no", "", "", "Día de Reyes"),
        (date(y, 4, 3), "feriado", "no", "", "", "Viernes Santo"),
        (date(y, 5, 1), "feriado", "no", "", "", "Día del Trabajo"),
        (date(y, 5, 25), "feriado", "no", "", "", "Feriado nacional"),
        (date(y, 6, 29), "feriado", "no", "", "", "San Pedro y San Pablo"),
        (date(y, 8, 15), "feriado", "no", "", "", "Asunción"),
        (date(y, 10, 12), "feriado", "no", "", "", "Día de la Raza"),
        (date(y, 11, 1), "feriado", "no", "", "", "Todos los Santos"),
        (date(y, 11, 21), "feriado", "no", "", "", "Feriado regional"),
        (date(y, 12, 8), "feriado", "no", "", "", "Inmaculada Concepción"),
        (date(y, 12, 25), "feriado", "no", "", "", "Navidad"),
    ]
    # Excepciones dentro de las semanas del plan (para verificación):
    lunes = hoy - timedelta(days=hoy.weekday())
    s31_mie = lunes + timedelta(weeks=1, days=2)   # miércoles de la 2.ª semana futura
    s31_dom = lunes + timedelta(weeks=1, days=6)   # domingo de esa semana
    s30_jue = lunes + timedelta(days=3)            # jueves de la semana corriente
    exc += [
        (s31_mie, "feriado", "no", "", "", "Feriado de planta (demo capacidad)"),
        (s31_dom, "día especial laborable", "sí", "SERVICIOS", "",
         "Turno especial de mantenimiento (solo SERVICIOS)"),
        (s30_jue, "paro", "no", "SERVICIOS", "Vapor", "Paro planta de vapor"),
        # Excepciones con área / sub-área fuera de catálogo (para VALIDACION):
        (date(y, 9, 15), "feriado", "no", "ZONA-X", "", "Área inexistente (demo validación)"),
        (date(y, 9, 16), "paro", "no", "SERVICIOS", "Nitrógeno", "Sub-área inexistente (demo)"),
    ]
    return [{"fecha": f, "tipo": t, "habil": h, "area": a, "sub_area": s, "motivo": m}
            for f, t, h, a, s, m in exc]

# 7.2: `es_especialidad_propia` marca qué especialidades son de personal propio.
# OP y TERCERO existen en las órdenes del ERP pero NO son técnicos propios: no
# deben poder entrar al ciclo de rotación ni a la capacidad. La restricción queda
# EXPLÍCITA y editable en el catálogo, no escondida en una lista hardcodeada.
PUESTOS = [
    ("PU-MEC", "MEC", "Puesto mecánico", SI),
    ("PU-ELE", "ELE", "Puesto eléctrico", SI),
    ("PU-AUT", "AUT", "Puesto automatización", SI),
    ("PU-OP", "OP", "Puesto operaciones", NO),
    ("PU-TER", "TERCERO", "Contratista externo", NO),
]
# Especialidades de personal propio, derivadas del catálogo (fuente única).
ESPECIALIDADES_PROPIAS = [e for _c, e, _d, propia in PUESTOS if propia == SI]

# PRESUPUESTO OPEX: la categoría de presupuesto y su clasificación (fijo/variable)
# son ATRIBUTOS DE CATÁLOGO de la actividad — se eligió ACTIVIDADES y no TIPOS_OT
# porque la actividad describe QUÉ se gasta (repuesto, servicio, overhaul) mientras
# que el tipo de OT solo separa preventiva/correctiva, demasiado grueso para las 6
# categorías. Onboardear otra empresa = editar este catálogo, cero código.
ACTIVIDADES = [
    # codigo, descripcion, tipo, categoria_presupuesto, clasificacion
    ("ACT-01", "Inspección de rutina", "preventivo", "Repuestos mandatorios", "fijo"),
    ("ACT-02", "Lubricación programada", "preventivo", "Repuestos mandatorios", "fijo"),
    ("ACT-03", "Reparación de falla", "correctivo", "Correctivos - materiales", "variable"),
    ("ACT-04", "Análisis predictivo", "predictivo", "Servicios contratados", "fijo"),
    ("ACT-05", "Certificación legal", "legal", "Servicios contratados", "fijo"),
    # §7: el banco de prueba necesita variedad de tipos de trabajo; el overhaul
    # se añade al CATÁLOGO (no se hardcodea en la lógica). El dataset por
    # defecto no lo usa: sus órdenes siguen saliendo de ACT-01…ACT-04.
    ("ACT-06", "Overhaul mayor", "correctivo", "Overhauls programados", "fijo"),
    ("ACT-07", "Servicio externo no contratado", "correctivo", "Servicios requeridos", "variable"),
    ("ACT-08", "Refacción / mejora menor", "correctivo", "Refacciones nuevas", "variable"),
]
# Categorías OPEX en orden de presentación: primero las FIJAS, luego las VARIABLES,
# dentro de cada grupo en el orden del catálogo. Se DERIVAN del catálogo (si el
# usuario añade una categoría a una actividad, aparece sola en PRESUPUESTO).
def _categorias_presupuesto():
    vistas = []
    for clas in ("fijo", "variable"):
        for a in ACTIVIDADES:
            cat, cl = a[3], a[4]
            if cat and cl == clas and (cat, cl) not in vistas:
                vistas.append((cat, cl))
    return vistas


CATEGORIAS_PRESUPUESTO = _categorias_presupuesto()
SIN_CLASIFICAR_PPTO = "SIN CLASIFICAR"

# DASHBOARD: la CLASE DE MANTENIMIENTO es atributo del TIPO DE OT y no de la
# actividad. Razón: es el tipo de OT —y solo él— el que distingue un correctivo
# PROGRAMADO de una EMERGENCIA (la actividad "Reparación de falla" es la misma en
# los dos casos), y ese corte es justo el que hoy no se podía hacer. Poner la
# clase en CAT_ACTIVIDADES habría duplicado su columna `tipo`, que ya dice
# preventivo/correctivo/predictivo/legal. Es la decisión inversa a la del
# presupuesto (allí la categoría SÍ vive en la actividad, porque describe QUÉ se
# gasta) y por el mismo criterio: cada atributo en el catálogo que lo determina.
# Onboardear otra empresa = mapear sus tipos de OT a estas 5 clases.
CLASES_MANTENIMIENTO = ["predictivo", "preventivo", "correctivo_programado",
                        "emergencia", "legal"]
SIN_CLASIFICAR_CLASE = "SIN CLASIFICAR"
TIPOS_OT = [
    ("TIPO-P1", "Orden preventiva programada", "preventiva", "preventivo"),
    ("TIPO-P2", "Orden predictiva (análisis de condición)", "preventiva", "predictivo"),
    ("TIPO-P3", "Orden legal / calibración obligatoria", "preventiva", "legal"),
    ("TIPO-C1", "Orden correctiva planificada", "correctiva", "correctivo_programado"),
    ("TIPO-C2", "Orden correctiva de emergencia", "correctiva", "emergencia"),
]
# tipo_ot → clase. Un tipo sin clase (o fuera de catálogo) cae en SIN CLASIFICAR:
# el mismo criterio que el presupuesto, la orden nunca desaparece del mix.
CAT_CLASE = {t[0]: t[3] for t in TIPOS_OT}
# Naturaleza de cada actividad (columna `tipo` de CAT_ACTIVIDADES) y tipo de OT
# preventivo que le corresponde. Solo se usan para SEMBRAR datos sintéticos
# coherentes; el libro no depende de ellos.
TIPO_ACTIVIDAD = {a[0]: a[2] for a in ACTIVIDADES}
TIPO_OT_PREVENTIVO = {"preventivo": "TIPO-P1", "predictivo": "TIPO-P2", "legal": "TIPO-P3"}

ESTADOS_ERP = [
    ("CERR", "Cerrada"),
    ("LIB", "Pendiente"),
    ("EJEC", "Pendiente"),
    ("ABIE", "Pendiente"),
]

# 6.3: dotación que EJERCITA la rotación. Especialidades rotativas MEC y ELE con
# 7 técnicos cada una en UNA sola área (→ N=7 en cada ciclo); 2 AUT de Banco fijo
# (no rotativo). El flag `rotativo` es explícito por técnico (no se hardcodea a
# MEC/ELE); orden_rotacion 1..N es único por especialidad×área entre rotativos y
# fija la posición de arranque en la semana de referencia.
# 6.6: supervisor FIJO por técnico (atributo del técnico; no rota, no cambia con
# VAC, no crea ni consume capacidad). Tres supervisores por especialidad; sin
# suplencia (se hace a mano). Fuente única del supervisor de ASIGNACIONES.
# 7.2: los supervisores dejan de ser cadenas sueltas y pasan a CATÁLOGO.
SUPERVISORES = [
    # codigo, nombre, especialidad
    ("SUP-MEC", "Supervisor Mecánico", "MEC"),
    ("SUP-ELE", "Supervisor Eléctrico", "ELE"),
    ("SUP-AUT", "Jefe de Automatización", "AUT"),
]
SUPERVISOR_POR_ESP = {e: n for _c, n, e in SUPERVISORES}
# 7.2: motivos de ausencia como catálogo editable (no hardcode en la fórmula).
MOTIVOS_AUSENCIA = [("Vacaciones anuales",), ("Día libre pagado",), ("Permiso",)]
# 7.2: roster REAL (id numérico de 8 dígitos). El orden 1..7 por especialidad es
# el mismo que había, así la rotación y la cobertura no cambian.
_TECNICOS_BASE = [
    # id, nombre, especialidad, area, rotativo, orden_rotacion, activo
    (80205524, "Carlos Pérez", "MEC", "PRODUCCION", SI, 1, SI),
    (80205525, "María Gómez", "MEC", "PRODUCCION", SI, 2, SI),
    (80205526, "Luis Rodríguez", "MEC", "PRODUCCION", SI, 3, SI),
    (80205527, "Miguel Martínez", "MEC", "PRODUCCION", SI, 4, SI),
    (80205528, "Ana Sánchez", "MEC", "PRODUCCION", SI, 5, SI),
    (80205529, "David Torres", "MEC", "PRODUCCION", SI, 6, SI),
    (80205530, "Francisco Ramírez", "MEC", "PRODUCCION", SI, 7, SI),
    (80205531, "Jorge Díaz", "ELE", "PRODUCCION", SI, 1, SI),
    (80205532, "Roberto Castro", "ELE", "PRODUCCION", SI, 2, SI),
    (80205533, "Laura Morales", "ELE", "PRODUCCION", SI, 3, SI),
    (80205534, "Ricardo Ortiz", "ELE", "PRODUCCION", SI, 4, SI),
    (80205535, "Eduardo Silva", "ELE", "PRODUCCION", SI, 5, SI),
    (80205536, "Gabriela Rojas", "ELE", "PRODUCCION", SI, 6, SI),
    (80205537, "Fernando Mendoza", "ELE", "PRODUCCION", SI, 7, SI),
    (80205538, "Alberto Vargas", "AUT", "PRODUCCION", NO, "", SI),
    (80205539, "Daniela Medina", "AUT", "PRODUCCION", NO, "", SI),
]
# El supervisor es atributo del técnico y sale del catálogo por su especialidad.
TECNICOS = [t[:4] + (SUPERVISOR_POR_ESP[t[2]],) + t[4:] for t in _TECNICOS_BASE]
# Índices dentro de la tupla de TECNICOS:
#   0 id · 1 nombre · 2 especialidad · 3 area · 4 supervisor · 5 rotativo
#   6 orden_rotacion · 7 activo
TEC_ESP, TEC_AREA, TEC_SUP, TEC_ROT, TEC_ORDROT, TEC_ACT = 2, 3, 4, 5, 6, 7
# 7.2: `activo` deja de ser decorativo. Solo los técnicos activos entran en las
# listas, en ASIGNACIONES, en el N de la rotación, en la capacidad y en el
# seguimiento. TECNICOS_ACTIVOS es la fuente única de "quién cuenta".
TECNICOS_ACTIVOS = [t for t in TECNICOS if t[TEC_ACT] == SI]
COORD_POR_AREA = {"PRODUCCION": "Coordinador A", "EMPAQUE": "Coordinador B", "SERVICIOS": "Coordinador C"}
EQUIPOS_POR_AREA = {
    "PRODUCCION": ["EQ-101", "EQ-102", "EQ-103", "EQ-104", "EQ-105"],
    "EMPAQUE": ["EQ-106", "EQ-107", "EQ-108", "EQ-109"],
    "SERVICIOS": ["EQ-110", "EQ-111", "EQ-112"],
}
ESPECIALIDADES = ("MEC", "ELE", "AUT", "TERCERO")

CAT_TIPOS = {t[0]: t[2] for t in TIPOS_OT}
CAT_ESTADOS = dict(ESTADOS_ERP)
CAT_CECO = {c[0]: c for c in CENTROS_COSTO}
CAT_PUESTOS = {c: e for c, e, *_ in PUESTOS}
CAT_ACTIVIDADES = {c: d for c, d, *_ in ACTIVIDADES}
# actividad → (categoria_presupuesto, clasificacion); "" si el catálogo no la asigna
CAT_CATEGORIA_PPTO = {a[0]: (a[3], a[4]) for a in ACTIVIDADES}

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


def es_habil(fecha, area, sub_area, excepciones, patron_habil=PATRON_HABIL):
    """Calendario laboral (v2.4): resuelve hábil/no hábil por especificidad, de
    más específico a más general. La primera que aplica manda:
      (a) excepción fecha + área + sub-área
      (b) excepción fecha + área (sub-área vacía)
      (c) excepción general de la fecha (área vacía)
      (d) patrón semanal del día
    Devuelve "sí"/"no". Espejo exacto de la fórmula del libro.
    """
    if fecha is None:
        return ""
    a, s = area or "", sub_area or ""
    for ea, es in ((a, s), (a, ""), ("", "")):
        for ex in excepciones:
            if ex["fecha"] == fecha and (ex["area"] or "") == ea and (ex["sub_area"] or "") == es:
                return ex["habil"]
    return patron_habil[fecha.weekday()]     # weekday(): lunes=0 … domingo=6


def backlog_habiles(fecha_inicio, hoy, excepciones):
    """Días HÁBILES (nivel planta) entre fecha_inicio y hoy, con signo. Excluye
    no laborables. Coexiste con backlog_dias (calendario). El nivel planta usa
    es_habil(fecha, "", "")."""
    if fecha_inicio is None:
        return ""
    if fecha_inicio <= hoy:
        d0, d1, signo = fecha_inicio, hoy, 1
    else:
        d0, d1, signo = hoy, fecha_inicio, -1
    cnt, d = 0, d0
    while d < d1:
        if es_habil(d, "", "", excepciones) == "sí":
            cnt += 1
        d += timedelta(days=1)
    return signo * cnt


def regla_3_estado_backlog(backlog, dias_backlog_max=DIAS_BACKLOG_MAX):
    """REGLA-3: FUTURO / MES CORRIENTE / BACKLOG. v2.4: sobre días hábiles."""
    if backlog is None or backlog == "":
        return ""
    if backlog < 0:
        return "FUTURO"
    if backlog > dias_backlog_max:
        return "BACKLOG"
    return "MES CORRIENTE"


def regla_4_en_plan(backlog, dias_min=DIAS_BACKLOG_MIN, dias_max=DIAS_BACKLOG_MAX):
    """REGLA-4: pertenencia al plan. v2.4: sobre días hábiles."""
    if backlog is None or backlog == "":
        return False
    return dias_min < backlog <= dias_max


def regla_5_horas_disponibles(turno, habil=True, horas_jornada=HORAS_JORNADA,
                              no_disponible=CODIGOS_NO_DISPONIBLE):
    """REGLA-5: horas por técnico y día. v2.4: un día NO hábil da 0 horas,
    sin importar el turno."""
    if habil is False or habil == "no":
        return 0
    if not turno or turno in no_disponible:
        return 0
    return horas_jornada


# ── Rotación automática de turnos (6.3) ────────────────────────────────────
# Anillo determinista, en orden de AVANCE semanal, para una especialidad con N
# posiciones (banco = N-3 puestos de Banco):
#     B(N-3), B(N-4), …, B1, T3, T2, T1  → y vuelve a B(N-3).
# (Ej. N=7: B4, B3, B2, B1, T3, T2, T1 → B4.)
# Avance: +1 posición por semana. El relevo B1→T3 sale solo del avance +1.
def etiqueta_anillo(pos, n):
    """Etiqueta de la posición pos (0..n-1) del anillo. banco = n-3."""
    banco = n - 3
    if pos < banco:
        return f"B{banco - pos}"      # pos0→B(n-3) … pos(banco-1)→B1
    return f"T{n - pos}"              # pos=banco→T3, +1→T2, +2→T1


def posicion_ciclo_de(rotativo, orden_rotacion, n, semanas_desde_ref, es_domingo):
    """Posición del anillo (texto) de un técnico en una semana. '' el domingo
    (fuera de la base L-S); 'B' fijo para no rotativos. Espejo de la fórmula."""
    if es_domingo:
        return ""
    if not rotativo:
        return "B"
    pos = ((orden_rotacion - 1) + semanas_desde_ref) % n
    return etiqueta_anillo(pos, n)


def banda_de(posicion):
    """Banda de turno (B/T1/T2/T3) a partir de la posición del anillo. La banda
    NO cambia la capacidad (REGLA-5 sigue plana): cambia QUÉ turno, no cuántas horas."""
    if not posicion:
        return ""
    return "B" if posicion[0] == "B" else posicion


def turno_derivado(turno_manual, posicion):
    """Turno de rotación 6.3 (sin vacaciones): el override manual manda; si no,
    la banda del anillo. Se conserva para verificar que 6.4 no mueve la rotación."""
    return turno_manual if turno_manual else banda_de(posicion)


# ── Vacaciones que arrastran (6.4) ─────────────────────────────────────────
# El plan de vacaciones marca VAC automáticamente y saca al técnico de la
# rotación esas semanas, dejando su POSICIÓN VACÍA (hueco visible). No se cierra
# ninguna fila ni se recalcula N: la derivación cerrada de 6.3 no se toca.
def en_vacaciones_de(tecnico, fecha, plan_vacaciones):
    """True si la fecha cae dentro de algún periodo [inicio, fin] de ese técnico
    (soporta varios periodos por técnico). Espejo del COUNTIFS del libro."""
    return any(v["tecnico"] == tecnico and v["fecha_inicio"] <= fecha <= v["fecha_fin"]
               for v in plan_vacaciones)


def turno_efectivo(turno_manual, posicion, en_vacaciones):
    """Turno efectivo (6.4) por precedencia:
      1) turno_manual <> ""     → turno_manual   (manual manda siempre)
      2) sin posición de ciclo  → ""             (domingo/sin turno; VAC no aplica)
      3) en_vacaciones          → "VAC"          (arrastra, solo L-S)
      4) si no                  → banda del anillo (rotación de 6.3)."""
    if turno_manual:
        return turno_manual
    if not posicion:
        return ""
    if en_vacaciones:
        return "VAC"
    return banda_de(posicion)


# ── Horas reales de seguimiento (6.5) ──────────────────────────────────────
# Capa de SEGUIMIENTO (cumplimiento individual / base de bono), NO de
# planificación: la base de 48 h (6.1) y la capacidad de PERFIL_HH NO se tocan.
# Un técnico en TURNO trabaja también el domingo (relevo 22:00, 7.º día) → 56 h
# reales = 48 + 8 de SUPERÁVIT; en BANCO = 48; en VAC = 0. El domingo NO se
# vuelve planificable.
def trabaja_domingo_de(posicion, en_vacaciones):
    """¿El técnico trabaja el domingo de esa semana? Sí si su posición es de
    turno (T1/T2/T3) y no está de vacaciones. Helper por fila (como en_vacaciones)."""
    return bool(posicion) and posicion[0] == "T" and not en_vacaciones


def horas_reales_semana(horas_disponibles_ls, trabaja_domingo):
    """Horas reales de la semana (seguimiento) = horas disponibles L-S (REGLA-5)
    + 8 h si trabaja el domingo. 56 turno / 48 banco / 0 VAC en semana normal;
    el +8 es superávit y NO entra en PERFIL_HH (la capacidad sigue en 48 h)."""
    return horas_disponibles_ls + (8 if trabaja_domingo else 0)


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


def lunes_iso(anio, n):
    """Lunes de la semana ISO n de ese año (misma aritmética que el libro)."""
    j4 = date(anio, 1, 4)
    return j4 - timedelta(days=j4.weekday()) + timedelta(weeks=n - 1)


def lunes_de_semana(etiqueta):
    """Lunes ISO de una etiqueta AAAA-Snn (inversa de regla_2_semana)."""
    return lunes_iso(int(etiqueta[:4]), int(etiqueta[6:8]))


def semanas_iso_del_anio(anio):
    """Nº de semanas ISO del año: 52 o 53."""
    return 53 if regla_2_semana(date(anio, 12, 28)).endswith("S53") else 52


def _n_por_ciclo():
    """N (nº de posiciones del anillo) por (especialidad, área) entre rotativos
    ACTIVOS. 7.2: un técnico con activo=no no cuenta para el ciclo."""
    n = {}
    for t in TECNICOS_ACTIVOS:
        if t[TEC_ROT] == SI:
            n[(t[TEC_ESP], t[TEC_AREA])] = n.get((t[TEC_ESP], t[TEC_AREA]), 0) + 1
    return n


def _asignaciones_de(lunes_list, semanas_list, semana_referencia, plan_vacaciones):
    """Filas de ASIGNACIONES para las semanas dadas: turno DERIVADO de la
    rotación (6.3), arrastrado a VAC por el plan de vacaciones (6.4), con el
    supervisor fijo (6.6) y el helper de domingo trabajado (6.5)."""
    n_por_ciclo = _n_por_ciclo()
    asignaciones = []
    for si, sem in enumerate(semanas_list):
        semanas_desde = (lunes_list[si] - semana_referencia).days // 7
        for tid, nombre, esp, area, sup, rot, ordrot, _act in TECNICOS_ACTIVOS:
            n = n_por_ciclo.get((esp, area), 0)
            for di, dia in enumerate(DIAS):
                fecha = lunes_list[si] + timedelta(days=di)
                pc = posicion_ciclo_de(rot == SI, ordrot or 0, n,
                                       semanas_desde, di == 6)
                en_vac = en_vacaciones_de(nombre, fecha, plan_vacaciones)
                turno_manual = ""            # sin excepciones manuales en el sintético
                turno = turno_efectivo(turno_manual, pc, en_vac)
                # 6.5: ¿trabaja el domingo? (turno y no VAC) — helper de seguimiento.
                trab_dom = trabaja_domingo_de(pc, en_vac)
                asignaciones.append({"semana": sem, "dia": dia, "tecnico": nombre,
                                     "area": area, "especialidad": esp,
                                     "n_ciclo": n, "posicion_ciclo": pc,
                                     "en_vacaciones": "sí" if en_vac else "no",
                                     "turno_manual": turno_manual, "turno": turno,
                                     "supervisor": sup,
                                     "trabaja_domingo": "sí" if trab_dom else "no"})
    return asignaciones


def _tec(esp, orden):
    """Nombre del técnico ACTIVO de esa especialidad con ese orden_rotacion (1..N),
    o el n-ésimo si no es rotativo. Evita hardcodear nombres del roster."""
    de_esp = [t for t in TECNICOS_ACTIVOS if t[TEC_ESP] == esp]
    for t in de_esp:
        if t[TEC_ORDROT] == orden:
            return t[1]
    return de_esp[min(orden - 1, len(de_esp) - 1)][1]


def generar_datos(hoy):
    """Construye ORDENES, EJECUCION, TECNICOS y ASIGNACIONES sintéticos."""
    lunes = hoy - timedelta(days=hoy.weekday())
    lunes_sem = [lunes + timedelta(weeks=k) for k in (-1, 0, 1, 2)]
    semanas = [regla_2_semana(d) for d in lunes_sem]
    excepciones = construir_excepciones(hoy)

    # 6.3: semana de referencia de la rotación = lunes de la 1.ª semana del plan
    # (así todas las semanas del plan quedan a +0..+3 de la referencia, sin
    # negativos). En ella orden_rotacion 1..N mapea directo a la posición.
    semana_referencia = lunes_sem[0]
    # N = nº de posiciones del ciclo por (especialidad, área) entre rotativos.
    n_por_ciclo = _n_por_ciclo()

    # 6.4: plan de vacaciones. Demo: el 5.º mecánico de la rotación, ~4 semanas que
    # SOLAPAN semanas en las que estaría en turno (S30→T2, S31→T1) → hueco de
    # cobertura visible en un turno; en S32 estaría en Banco (hueco en banco).
    # Dos periodos (varias filas por técnico) para ejercitar el COUNTIFS.
    plan_vacaciones = [
        {"tecnico": _tec("MEC", 5), "fecha_inicio": lunes_sem[1],
         "fecha_fin": lunes_sem[3] + timedelta(days=13), "motivo": "Vacaciones anuales"},
        {"tecnico": _tec("MEC", 5), "fecha_inicio": lunes_sem[3] + timedelta(days=35),
         "fecha_fin": lunes_sem[3] + timedelta(days=41), "motivo": "Permiso"},
    ]

    # --- ASIGNACIONES: 4 semanas × 16 técnicos × 7 días = 448 filas -------
    # El turno se DERIVA de la rotación (6.3) y, si el técnico está de VAC en esa
    # fecha (6.4), arrastra a "VAC" dejando su posición vacía (hueco). La rotación
    # de los DEMÁS no se toca. Sin overrides manuales en el sintético.
    asignaciones = _asignaciones_de(lunes_sem, semanas, semana_referencia, plan_vacaciones)

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
        if act is None:
            act = ("ACT-01", "ACT-02", "ACT-04")[consecutivo[0] % 3] if clasif == "preventiva" else "ACT-03"
        if tipo is None:
            # El tipo de OT preventivo se deriva de la NATURALEZA de la actividad
            # (columna `tipo` de CAT_ACTIVIDADES), para que la clase de
            # mantenimiento del mix sea coherente con el trabajo descrito: un
            # "Análisis predictivo" no puede quedar como preventivo. Los
            # correctivos alternan planificada/emergencia, que es justo el corte
            # que el tipo de OT aporta y la actividad no puede dar.
            tipo = (TIPO_OT_PREVENTIVO[TIPO_ACTIVIDAD.get(act, "preventivo")]
                    if clasif == "preventiva"
                    else ("TIPO-C1", "TIPO-C2")[consecutivo[0] % 2])
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
                     "AUT": ["CC-110", "CC-220"]}
    idx_plan = 0
    for esp, filas in PRESUPUESTO_PLAN.items():
        tecs = _tecnicos_de(esp)
        for si, (hh_prev, hh_corr) in enumerate(filas):
            # Dos huecos deliberados del sintético (heredados, se mantienen tal
            # cual): el 4.º mecánico no recibe carga en la 3.ª semana y el 7.º no
            # trabaja el viernes de la 2.ª. Antes iban clavados al código
            # "TEC-04"/"TEC-07"; con el roster real se expresan por rotación.
            disponibles = [t for t in tecs if not (t[1] == _tec("MEC", 4) and si == 2)]
            for clasif, total in (("preventiva", hh_prev), ("correctiva", hh_corr)):
                for h in partir_horas(total):
                    dia_idx = idx_plan % 5
                    tec = disponibles[idx_plan % len(disponibles)]
                    if tec[1] == _tec("MEC", 7) and si == 1 and dia_idx == 4:
                        dia_idx = 3
                    nombre_tec = "" if idx_plan % 12 == 11 else tec[1]  # algunas sin técnico
                    nueva(lunes_sem[si] + timedelta(days=dia_idx), h, esp, clasif, "plan",
                          si=si, dia_idx=dia_idx, tecnico=nombre_tec,
                          ceco=cecos_por_esp[esp][idx_plan % len(cecos_por_esp[esp])])
                    idx_plan += 1
    # Trabajos de terceros (sin técnico interno)
    for si, horas in PRESUPUESTO_TERCERO.items():
        for j, h in enumerate(partir_horas(horas)):
            nueva(lunes_sem[si] + timedelta(days=j % 5), h, "TERCERO", "preventiva",
                  "plan_tercero", si=si, ceco="CC-310", act="ACT-05", tipo="TIPO-P3")

    # Órdenes de fin de semana (6.1: base L-S). El SÁBADO es hábil (consume
    # capacidad y cuenta en adherencia); el DOMINGO es el día normal no hábil
    # (prueba VALIDACION y que EXPORTAR recorre los 7 días). Los casos ad-hoc
    # viejos (vacaciones ad-hoc, domingo especial de SERVICIOS) se retiran del sintético
    # y se reservan para §7 (la rotación exige cobertura limpia cada semana).
    s30_sab = lunes_sem[1] + timedelta(days=5)   # sábado de la semana corriente (hábil)
    s30_dom = lunes_sem[1] + timedelta(days=6)   # domingo (no hábil)
    nueva(s30_sab, 6, "MEC", "correctiva", "finde", tecnico=_tec("MEC", 1), ceco="CC-110")
    nueva(s30_sab, 4, "ELE", "correctiva", "finde", tecnico=_tec("ELE", 1), ceco="CC-120")
    nueva(s30_dom, 8, "MEC", "correctiva", "finde", tecnico="", ceco="CC-210")

    # Ajustes manuales de horas (v2.1: viven en tblAjustes, con clave). Se fijan
    # dos órdenes del plan (horas estimadas 8 y 6) para dar desviaciones
    # demostrables (+4 y −2); la lista de ajustes se arma al final con los id.
    def _fijar_horas(o, h):
        o["horas_estimadas"] = h
        o["costo_plan"] = h * TARIFA["preventiva" if o["_clasif"] == "preventiva" else "correctiva"]
    aj1 = next(o for o in ordenes if o["_grupo"] == "plan" and o["_si"] == 1
               and o["puesto_trabajo"] == "PU-MEC" and o["_clasif"] == "preventiva")
    aj1["tecnico_asignado"] = _tec("MEC", 1)
    _fijar_horas(aj1, 8)
    aj1["observaciones"] = "Ajuste 8 → 12 h en hoja AJUSTES"
    aj2 = next(o for o in ordenes if o["_grupo"] == "plan" and o["_si"] == 1
               and o["puesto_trabajo"] == "PU-ELE" and o["_clasif"] == "preventiva"
               and o is not aj1)
    if not aj2["tecnico_asignado"]:
        aj2["tecnico_asignado"] = _tec("ELE", 1)
    _fijar_horas(aj2, 6)
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
    esp_ciclo = ["MEC", "ELE", "AUT"]
    for k, (dias_atras, cuantas) in enumerate([(45, 8), (75, 6), (100, 6), (120, 4), (150, 4)]):
        for j in range(cuantas):
            esp = esp_ciclo[(k + j) % len(esp_ciclo)]
            clasif = "preventiva" if j % 4 == 3 else "correctiva"
            nueva(hoy - timedelta(days=dias_atras), (4, 6, 8)[j % 3], esp, clasif, "backlog",
                  ceco=CENTROS_COSTO[(k + j) % len(CENTROS_COSTO)][0])

    # Histórico cerrado (alimenta COSTOS y EQUIPOS_CRITICOS). Recorre los 10
    # CECOs para dar datos a todas las sub-áreas de SERVICIOS.
    for j in range(15):
        esp = esp_ciclo[j % len(esp_ciclo)]
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

    # 6.4: una orden planificada para un técnico que ESE día está de vacaciones
    # se queda sin técnico (el supervisor la reasignará): así el técnico de VAC
    # no aparece sobreasignado (0 h de capacidad) y el hueco es solo de cobertura.
    for o in ordenes:
        if o["tecnico_asignado"] and o["fecha_inicio"] \
                and en_vacaciones_de(o["tecnico_asignado"], o["fecha_inicio"], plan_vacaciones):
            o["tecnico_asignado"] = ""

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
            "semana_referencia": semana_referencia, "n_por_ciclo": n_por_ciclo,
            "plan_vacaciones": plan_vacaciones, "anio_presupuesto": hoy.year,
            "ordenes": ordenes, "ejecucion": ejecucion, "asignaciones": asignaciones,
            "ajustes": ajustes, "excepciones": excepciones, "edge_regla8": edge_regla8}


# ══════════════════════════════════════════════════════════════════════════
# 3-bis. §7 — BANCO DE PRUEBA: un año en crudo + ventana programada
#    Es OPCIÓN del generador (--anio-completo). El dataset por defecto (4
#    semanas ancladas a HOY) NO cambia: es el que se usa a diario.
#    Ancla FIJA (año 2026): el banco nunca depende de date.today().
#    No toca ninguna de las 10 reglas, ni la rotación, ni VAC, ni seguimiento.
# ══════════════════════════════════════════════════════════════════════════

ANIO_BANCO = 2026
SEMANA_VENTANA = 45          # semana ISO donde arranca la ventana programada
SEMILLA_BANCO = 20260101
EQUIPOS_CRITICOS_BANCO = ("EQ-101", "EQ-106", "EQ-110")
# Tareas de la ventana: cortas, para que quepan en la jornada productiva
# (8 × 0,87 = 6,96 h/día). Fuera de la ventana el volumen es crudo.
HORAS_VENTANA = (2, 3, 4)
HORAS_CRUDO = (2, 3, 4, 6, 8, 10)
# Combinaciones (actividad, tipo_ot) tomadas de los CATÁLOGOS, no hardcodeadas.
COMBOS_PREV = [("ACT-01", "TIPO-P1"), ("ACT-02", "TIPO-P1"),
               ("ACT-04", "TIPO-P2"), ("ACT-05", "TIPO-P3")]
COMBOS_CORR = [("ACT-03", "TIPO-C1"), ("ACT-03", "TIPO-C2"), ("ACT-06", "TIPO-C1")]


def generar_datos_banco(n_ordenes=1000, semanas_programadas=4, semilla=SEMILLA_BANCO):
    """§7: banco de prueba. Volumen de un año (n_ordenes órdenes repartidas de
    forma NO uniforme por las semanas ISO de 2026) + una ventana de
    `semanas_programadas` semanas realmente programada (técnico asignado por
    especialidad, disponibilidad y capacidad). Determinista por `semilla`."""
    rnd = random.Random(semilla)
    anio = ANIO_BANCO
    n_sem = semanas_iso_del_anio(anio)
    lunes_anio = [lunes_iso(anio, k + 1) for k in range(n_sem)]
    sem_anio = [regla_2_semana(d) for d in lunes_anio]

    i0 = SEMANA_VENTANA - 1
    i1 = min(i0 + semanas_programadas, n_sem)
    lunes_sem, semanas = lunes_anio[i0:i1], sem_anio[i0:i1]
    hoy = lunes_sem[0]                       # "hoy" = lunes de la ventana
    v_ini, v_fin = lunes_sem[0], lunes_sem[-1] + timedelta(days=6)

    excepciones = construir_excepciones(hoy)
    semana_referencia = lunes_anio[0]

    # --- Vacaciones del año (7 periodos; 2 solapan la ventana programada) ----
    plan_vacaciones = []
    for nombre, sini, nsemv, motivo in [
            (_tec("MEC", 3), 8, 3, "Vacaciones anuales"),
            (_tec("MEC", 6), 20, 2, "Vacaciones anuales"),
            (TECNICOS_ACTIVOS[-2][1], 27, 2, "Vacaciones anuales"),
            (_tec("ELE", 2), 31, 3, "Vacaciones anuales"),
            (_tec("ELE", 5), 38, 2, "Vacaciones anuales"),
            (_tec("MEC", 2), SEMANA_VENTANA, 2, "Vacaciones anuales"),
            (_tec("ELE", 4), SEMANA_VENTANA + 2, 1, "Día libre pagado")]:
        ini = lunes_iso(anio, sini)
        plan_vacaciones.append({"tecnico": nombre, "fecha_inicio": ini,
                                "fecha_fin": ini + timedelta(days=7 * nsemv - 1),
                                "motivo": motivo})

    # ASIGNACIONES: el AÑO COMPLETO para el roster actual (rotación 6.3 + VAC 6.4).
    asignaciones = _asignaciones_de(lunes_anio, sem_anio, semana_referencia, plan_vacaciones)
    disp_h, turno_de = {}, {}
    for a in asignaciones:
        f = lunes_de_semana(a["semana"]) + timedelta(days=DIAS.index(a["dia"]))
        hab = es_habil(f, a["area"], "", excepciones)
        disp_h[(a["tecnico"], f)] = regla_5_horas_disponibles(a["turno"], hab)
        turno_de[(a["tecnico"], f)] = a["turno"]

    # --- Fábrica de órdenes -------------------------------------------------
    ordenes, cons = [], [0]
    cecos_esp = {"MEC": ["CC-110", "CC-210", "CC-310"],
                 "ELE": ["CC-120", "CC-220", "CC-320"],
                 "AUT": ["CC-110", "CC-220", "CC-340"]}
    puesto_esp = {"MEC": "PU-MEC", "ELE": "PU-ELE", "AUT": "PU-AUT"}

    def nueva(fecha, horas, esp, clasif, grupo, ceco=None, act=None, tipo=None,
              puesto=None, orden_id=None, tecnico="", obs=""):
        cons[0] += 1
        oid = orden_id or f"OT-{cons[0]:06d}"
        ceco = ceco or cecos_esp[esp][cons[0] % len(cecos_esp[esp])]
        info = CAT_CECO.get(ceco)
        area = info[CECO_AREA] if info else "PRODUCCION"
        equipos = EQUIPOS_POR_AREA.get(area, EQUIPOS_POR_AREA["PRODUCCION"])
        equipo = equipos[cons[0] % len(equipos)]
        if act is None or tipo is None:
            a2, t2 = rnd.choice(COMBOS_PREV if clasif == "preventiva" else COMBOS_CORR)
            act, tipo = act or a2, tipo or t2
        tarifa = TARIFA["preventiva" if clasif == "preventiva" else "correctiva"]
        o = {"orden": oid, "operacion": "0010",
             "descripcion_general": f"{CAT_ACTIVIDADES.get(act, 'Actividad')} — {equipo}",
             "descripcion_operacion": f"{CAT_ACTIVIDADES.get(act, 'Actividad')} en {equipo}",
             "equipo": equipo, "centro_costo": ceco,
             "puesto_trabajo": puesto or puesto_esp[esp],
             "cod_actividad": act, "tipo_ot": tipo,
             "fecha_inicio": fecha, "horas_estimadas": horas,
             "costo_plan": (horas or 0) * tarifa,
             "tecnico_asignado": tecnico, "permiso_requerido": "",
             "bloqueo_energia": "", "link_checklist": "", "observaciones": obs,
             "_grupo": grupo, "_si": None, "_clasif": clasif}
        if clasif == "preventiva" and act in ("ACT-01", "ACT-02"):
            o["link_checklist"] = f"{act}.pdf"        # fecha comprometida (prioridad)
        if clasif == "correctiva" and equipo in EQUIPOS_CRITICOS_BANCO:
            o["permiso_requerido"], o["bloqueo_energia"] = "PT-CALIENTE", "LOTO"
        ordenes.append(o)
        return o

    # El grid del calendario cubre 760 días desde el 1-ene del año del ancla, y
    # la semana ISO 1 de 2026 arranca el 29-dic-2025: las fechas anteriores al
    # 1-ene quedarían fuera del grid y `backlog_habiles` contaría de menos
    # (limitación conocida del libro). El banco se acota al año natural.
    ini_grid = date(anio, 1, 1)

    def dia_habil_de(lunes, esp, ceco=None):
        """Un día L-S de esa semana que sea HÁBIL para el área de la orden, para
        que el volumen crudo no contamine los casos borde sembrados."""
        info = CAT_CECO.get(ceco) if ceco else None
        ar = info[CECO_AREA] if info else "PRODUCCION"
        sa = sub_area_efectiva(info[CECO_SUBAREA], info[CECO_AREA]) if info else ar
        for _ in range(12):
            f = lunes + timedelta(days=rnd.randrange(6))
            if f >= ini_grid and es_habil(f, ar, sa, excepciones) == "sí":
                return f
        return None

    # --- Casos borde sembrados: cantidades EXACTAS conocidas ----------------
    S = {"dup_ids": 3, "sin_fecha": 4, "sin_horas": 4, "ceco_desconocido": 3,
         "puesto_desconocido": 3, "actividad_desconocida": 3, "tipo_desconocido": 3,
         "domingo": 6, "feriado": 4, "paro_subarea": 3, "cruce_anio": 3,
         "vac_mal_asignadas": 3, "ejec_sin_orden": 5, "sobrecargadas": 2,
         "casi_vacias": 2, "ajustes_aplicados": 5, "ajustes_duplicados": 2,
         "ajustes_huerfanos": 2, "regla8_precio_mayor": 2}

    # Semanas sobrecargadas (>100 % de carga) y casi vacías: fuera de la ventana.
    sem_sobrecarga = [12, 33]          # índices 0-based de semana ISO
    sem_vacia = [5, 27]
    n_reservadas = (S["dup_ids"] + S["sin_fecha"] + S["sin_horas"] + S["ceco_desconocido"]
                    + S["puesto_desconocido"] + S["actividad_desconocida"]
                    + S["tipo_desconocido"] + S["domingo"] + S["feriado"]
                    + S["paro_subarea"] + S["cruce_anio"] + S["vac_mal_asignadas"])
    n_sobre = 68                       # 34 órdenes de 10 h en cada semana sobrecargada
    picos = ((0, "MEC", 34), (1, "ELE", 30), (2, "MEC", 26))   # parada dentro de la ventana
    n_bulk = n_ordenes - n_reservadas - n_sobre - sum(p[2] for p in picos)
    if n_bulk < 100:
        raise ValueError("n_ordenes demasiado pequeño para el banco (mínimo ~300)")

    # Reparto NO uniforme por semana: ondulación determinista + zona rica
    # alrededor de la ventana + dos semanas casi vacías.
    pesos = []
    for k in range(n_sem):
        w = rnd.uniform(0.55, 1.45)
        if i0 - 3 <= k < i1 + 1:
            w *= 3.4                   # zona rica: la ventana y su entorno
        if k in sem_vacia:
            w = 0.03
        if k in sem_sobrecarga:
            w *= 0.4                   # su volumen llega por las órdenes de 10 h
        pesos.append(w)
    total_peso = sum(pesos)
    por_semana = [max(0, round(n_bulk * w / total_peso)) for w in pesos]
    # Ajuste fino para cuadrar exactamente n_bulk
    while sum(por_semana) > n_bulk:
        por_semana[max(range(n_sem), key=lambda k: por_semana[k])] -= 1
    while sum(por_semana) < n_bulk:
        por_semana[i0] += 1

    # Volumen crudo, semana a semana
    mezcla_esp = ["MEC"] * 5 + ["ELE"] * 4 + ["AUT"] * 2
    for k in range(n_sem):
        en_ventana_k = i0 <= k < i1
        for _ in range(por_semana[k]):
            esp = rnd.choice(mezcla_esp)
            ceco = cecos_esp[esp][rnd.randrange(len(cecos_esp[esp]))]
            f = dia_habil_de(lunes_anio[k], esp, ceco)
            if f is None:
                continue
            clasif = "preventiva" if rnd.random() < 0.68 else "correctiva"
            horas = rnd.choice(HORAS_VENTANA if en_ventana_k else HORAS_CRUDO)
            nueva(f, horas, esp, clasif, "ventana" if en_ventana_k else "anio", ceco=ceco)
    # Picos de carga dentro de la ventana (parada de planta): generan el
    # REMANENTE deliberado, porque no caben en la jornada productiva del día.
    for off_sem, esp, cuantas in picos:
        lun = lunes_sem[min(off_sem, len(lunes_sem) - 1)]
        f = dia_habil_de(lun, esp) or (lun + timedelta(days=1))
        for _ in range(cuantas):
            nueva(f, rnd.choice((3, 4)), esp, "correctiva", "ventana_pico")

    # Semanas sobrecargadas (>100 % de carga): 34 órdenes de 10 h cada una
    for k, esp in zip(sem_sobrecarga, ("MEC", "ELE")):
        for _ in range(34):
            f = dia_habil_de(lunes_anio[k], esp) or lunes_anio[k]
            nueva(f, 10, esp, "correctiva", "sobrecarga")

    # ---- Casos borde (cantidades exactas del manifiesto) -------------------
    f_ok = dia_habil_de(lunes_anio[10], "MEC") or lunes_anio[10]
    for _ in range(S["sin_fecha"]):
        nueva(None, 4, "MEC", "correctiva", "edge")
    for _ in range(S["sin_horas"]):
        nueva(dia_habil_de(lunes_anio[11], "ELE") or f_ok, None, "ELE", "correctiva", "edge")
    for _ in range(S["ceco_desconocido"]):
        nueva(f_ok, 4, "MEC", "correctiva", "edge", ceco="CC-999")
    for _ in range(S["puesto_desconocido"]):
        nueva(f_ok, 4, "ELE", "correctiva", "edge", puesto="PU-XXX")
    for _ in range(S["actividad_desconocida"]):
        nueva(f_ok, 4, "AUT", "correctiva", "edge", act="ACT-99", tipo="TIPO-C1")
    for _ in range(S["tipo_desconocido"]):
        nueva(f_ok, 4, "MEC", "correctiva", "edge", act="ACT-03", tipo="TIPO-X9")
    # Domingos NO laborables (evita el domingo especial laborable de SERVICIOS)
    dom_especial = lunes_sem[1] + timedelta(days=6)
    doms = [lunes_anio[k] + timedelta(days=6) for k in (14, 18, 22, 26, 30, 34)]
    for f in doms[:S["domingo"]]:
        assert f != dom_especial
        nueva(f, 4, "MEC", "correctiva", "edge_domingo", ceco="CC-110")
    # Feriados generales del año
    for f in [date(anio, 5, 1), date(anio, 8, 15), date(anio, 10, 12), date(anio, 12, 25)][:S["feriado"]]:
        nueva(f, 4, "ELE", "correctiva", "edge_feriado", ceco="CC-120")
    # Paro de la sub-área Vapor (excepción por sub-área), dentro de la ventana
    f_paro = lunes_sem[0] + timedelta(days=3)
    for _ in range(S["paro_subarea"]):
        nueva(f_paro, 4, "MEC", "correctiva", "edge_paro", ceco="CC-310")
    # Cruce de fin de año: 2026-S53 y 2027-S01 (no se pliegan)
    nueva(date(anio, 12, 29), 4, "AUT", "preventiva", "cruce")
    nueva(date(anio + 1, 1, 1), 4, "MEC", "preventiva", "cruce")
    nueva(date(anio + 1, 1, 5), 4, "ELE", "preventiva", "cruce")
    # Órdenes mal asignadas a técnicos que están de VACACIONES esas fechas.
    # Van FUERA de la ventana programada a propósito: la ventana debe quedar
    # coherente (§13) y este caso documenta el error humano que VALIDACION expone.
    vac_mal = []
    for v in plan_vacaciones[:S["vac_mal_asignadas"]]:
        f = v["fecha_inicio"] + timedelta(days=1)
        esp = next(t[TEC_ESP] for t in TECNICOS if t[1] == v["tecnico"])
        o = nueva(f, 4, esp, "correctiva", "edge_vac", tecnico=v["tecnico"],
                  obs="Demo: asignada a técnico de vacaciones (HHD = −HHA)")
        vac_mal.append(o)

    # Relleno determinista hasta exactamente n_ordenes (antes de duplicar ids)
    k_rel = 0
    while len(ordenes) < n_ordenes - S["dup_ids"]:
        esp = mezcla_esp[k_rel % len(mezcla_esp)]
        f = dia_habil_de(lunes_anio[(k_rel * 7) % n_sem], esp) or f_ok
        nueva(f, rnd.choice(HORAS_CRUDO), esp, "preventiva", "anio")
        k_rel += 1
    # id_operacion duplicados (2 filas por id): se copian filas ya existentes
    for j in range(S["dup_ids"]):
        ordenes.append({**ordenes[40 + j * 7]})
    assert len(ordenes) == n_ordenes, f"{len(ordenes)} órdenes, esperadas {n_ordenes}"

    for o in ordenes:
        o["id_operacion"] = o["orden"] + o["operacion"]

    # --- Programación REAL de la ventana ------------------------------------
    # Precedencia: (a) especialidad · (b) disponibilidad · (c) capacidad ·
    # (d) prioridad. Si no cabe, la orden queda SIN TÉCNICO (remanente real).
    cap_dia = HORAS_JORNADA * FACTOR_PRODUCTIVIDAD          # 6,96 h productivas
    usado = {}

    def prioridad(o):
        if o["_clasif"] == "preventiva" and o["link_checklist"]:
            return 0                                        # preventivo comprometido
        if o["_clasif"] == "correctiva" and o["equipo"] in EQUIPOS_CRITICOS_BANCO:
            return 1                                        # correctivo de equipo crítico
        return 2

    en_ventana = [o for o in ordenes
                  if o["fecha_inicio"] and v_ini <= o["fecha_inicio"] <= v_fin
                  and o["horas_estimadas"] and not o["tecnico_asignado"]]
    en_ventana.sort(key=lambda o: (o["fecha_inicio"], prioridad(o), o["orden"]))
    n_programadas = n_remanente = 0
    for o in en_ventana:
        info = CAT_CECO.get(o["centro_costo"])
        ar = info[CECO_AREA] if info else SIN_CATALOGO
        sa = sub_area_efectiva(info[CECO_SUBAREA], info[CECO_AREA]) if info else SIN_CATALOGO
        if es_habil(o["fecha_inicio"], ar, sa, excepciones) != "sí":
            continue                                        # día no laborable: no se programa
        esp = CAT_PUESTOS.get(o["puesto_trabajo"])
        if esp not in cecos_esp:
            continue                                        # puesto fuera de catálogo
        f = o["fecha_inicio"]
        cands = sorted([t[1] for t in TECNICOS if t[TEC_ESP] == esp],
                       key=lambda nb: usado.get((nb, f), 0))
        for nb in cands:
            if disp_h.get((nb, f), 0) <= 0:
                continue                                    # domingo / VAC / no hábil
            if usado.get((nb, f), 0) + o["horas_estimadas"] <= cap_dia + 1e-9:
                o["tecnico_asignado"] = nb
                usado[(nb, f)] = usado.get((nb, f), 0) + o["horas_estimadas"]
                n_programadas += 1
                break
        else:
            n_remanente += 1                                # remanente deliberado

    # --- EJECUCION: notificaciones realistas --------------------------------
    # Solo de órdenes ya vencidas o de la ventana en curso (nunca de semanas
    # futuras sin programar), y se deja una proporción sin ejecución → la
    # adherencia queda en un rango creíble en vez de 0 % o 100 %.
    ejecucion, ya = [], set()
    prioridades = ("1-ALTA", "2-MEDIA", "3-BAJA")
    usuario = {"CERR": "CERRADA", "LIB": "LIBERADA", "EJEC": "EN EJECUCION", "ABIE": "ABIERTA"}
    edge_regla8, n_cerradas = [], 0
    for j, o in enumerate(ordenes):
        f = o["fecha_inicio"]
        if f is None or f > v_fin or o["id_operacion"] in ya:
            continue
        pasada = f < v_ini
        if rnd.random() > (0.95 if pasada else 0.75):
            continue                                        # vencida SIN ejecución
        if pasada:
            estado = "CERR" if rnd.random() < 0.92 else rnd.choice(("EJEC", "ABIE"))
        else:
            estado = rnd.choice(("CERR", "CERR", "EJEC", "LIB"))
        plan = o["costo_plan"] or 0
        precio = plan * 2 // 5
        if len(edge_regla8) < S["regla8_precio_mayor"] and estado == "CERR" and j % 97 == 0:
            precio = plan + 100                             # REGLA-8: materiales = 0
            edge_regla8.append(o["id_operacion"])
        ejecucion.append({"orden": o["orden"], "operacion": o["operacion"],
                          "id_operacion": o["id_operacion"], "estado_sistema": estado,
                          "prioridad": prioridades[j % 3],
                          "estado_instalacion": ("OPERATIVO", "PARADO")[j % 2],
                          "precio": precio, "costo_real": plan if estado == "CERR" else 0,
                          "costo_plan_total": plan, "estado_usuario": usuario[estado]})
        ya.add(o["id_operacion"])
        n_cerradas += estado == "CERR"
    # Ejecuciones huérfanas (sin orden en ORDENES)
    for n in range(S["ejec_sin_orden"]):
        oid = f"OT-99{n:04d}"
        ejecucion.append({"orden": oid, "operacion": "0010", "id_operacion": oid + "0010",
                          "estado_sistema": "LIB", "prioridad": "2-MEDIA",
                          "estado_instalacion": "OPERATIVO", "precio": 50,
                          "costo_real": 0, "costo_plan_total": 150,
                          "estado_usuario": "LIBERADA"})

    # --- tblAjustes: aplicados + duplicados + huérfanos ---------------------
    con_horas = [o for o in ordenes if o["horas_estimadas"] and o["fecha_inicio"]
                 and o["id_operacion"] not in {x["id_operacion"] for x in ordenes
                                               if ordenes.count(x) > 1}]
    elegidas = con_horas[:: max(1, len(con_horas) // (S["ajustes_aplicados"] + 3))][:S["ajustes_aplicados"]]
    ajustes, desviacion_total = [], 0
    for i, o in enumerate(elegidas):
        nuevas_h = o["horas_estimadas"] + (2 if i % 2 == 0 else -1)
        desviacion_total += nuevas_h - o["horas_estimadas"]
        ajustes.append({"id_operacion": o["id_operacion"], "horas_ajustadas": nuevas_h,
                        "motivo": "Alcance real distinto al estándar del ERP",
                        "fecha_ajuste": hoy})
    for i in range(S["ajustes_duplicados"]):                # duplicados dentro de tblAjustes
        ajustes.append({"id_operacion": elegidas[i]["id_operacion"],
                        "horas_ajustadas": elegidas[i]["horas_estimadas"] + 5,
                        "motivo": "Duplicado (demo): se ignora, gana la primera fila",
                        "fecha_ajuste": hoy})
    for i in range(S["ajustes_huerfanos"]):                 # huérfanos (id inexistente)
        ajustes.append({"id_operacion": f"OT-9999{i:02d}0010", "horas_ajustadas": 6,
                        "motivo": "Huérfano (demo): la orden no existe en ORDENES",
                        "fecha_ajuste": hoy})

    # --- MANIFIESTO DE SIEMBRA (contraste contra VALIDACION, sin contar a ojo)
    ids = [o["id_operacion"] for o in ordenes]
    ids_ejec = {e["id_operacion"] for e in ejecucion}
    manifiesto = {
        "ventana_programada": f"{semanas[0]} … {semanas[-1]}  ({v_ini} → {v_fin})",
        "ancla_hoy": hoy.isoformat(),
        "semilla": semilla,
        "ordenes": len(ordenes),
        "ejecuciones": len(ejecucion),
        "asignaciones": len(asignaciones),
        "semanas_iso_cubiertas": n_sem,
        # — Contraste directo contra VALIDACION (REGLA-10 + ajustes + calendario) —
        "val_duplicadas": S["dup_ids"] * 2,
        "val_sin_fecha": S["sin_fecha"],
        "val_sin_horas": S["sin_horas"],
        "val_ceco_desconocido": S["ceco_desconocido"],
        "val_puesto_desconocido": S["puesto_desconocido"],
        "val_actividad_desconocida": S["actividad_desconocida"],
        "val_tipo_ot_desconocido": S["tipo_desconocido"],
        "val_ejecucion_sin_par": S["ejec_sin_orden"],
        "val_ordenes_sin_par": sum(1 for i in ids if i not in ids_ejec),
        "val_ordenes_ajustadas": S["ajustes_aplicados"],
        "val_desviacion_horas": desviacion_total,
        "val_ajustes_huerfanos": S["ajustes_huerfanos"],
        "val_ajustes_duplicados": S["ajustes_duplicados"] * 2,
        "val_en_dia_no_habil": S["domingo"] + S["feriado"] + S["paro_subarea"],
        "val_exc_area_desconocida": 1,
        "val_exc_sub_desconocida": 1,
        # — Casos sembrados que no son chequeos de VALIDACION —
        "semanas_sobrecargadas": S["sobrecargadas"],
        "semanas_casi_vacias": S["casi_vacias"],
        "ordenes_asignadas_a_tecnico_en_vac": S["vac_mal_asignadas"],
        "ordenes_cruce_de_anio": S["cruce_anio"],
        "periodos_de_vacaciones": len(plan_vacaciones),
        "ordenes_regla8_precio_mayor": len(edge_regla8),
        # — Ventana programada —
        "ventana_ordenes_programadas": n_programadas,
        "ventana_remanente_sin_tecnico": n_remanente,
        "ventana_capacidad_dia_h": round(cap_dia, 2),
    }

    return {"hoy": hoy, "lunes_sem": lunes_sem, "semanas": semanas,
            "semana_referencia": semana_referencia, "n_por_ciclo": _n_por_ciclo(),
            "plan_vacaciones": plan_vacaciones, "anio_presupuesto": hoy.year,
            "ordenes": ordenes, "ejecucion": ejecucion, "asignaciones": asignaciones,
            "ajustes": ajustes, "excepciones": excepciones, "edge_regla8": edge_regla8,
            "manifiesto": manifiesto, "banco": True}


# ══════════════════════════════════════════════════════════════════════════
# 3-ter. PRESUPUESTO OPEX (plan manual por mes vs gasto real)
#    Hoja DERIVADA, no una regla del motor: no renumera ni amplía las 10 reglas.
#    Alcance OPEX: materiales, servicios y terceros. La mano de obra propia NO es
#    costo (decisión cerrada) y no entra ni en el plan ni en el real. Nada de CAPEX.
#    El REAL sale del MISMO campo que usa COSTOS (`costo_total`, REGLA-8) y con la
#    MISMA convención de mes (anio/mes de la orden): no hay una segunda forma de
#    sumar costos.
# ══════════════════════════════════════════════════════════════════════════

# Factores usados para sembrar el plan a partir del gasto real, elegidos para que
# el semáforo quede EJERCITADO: ~1,00 → dentro; <1 → sobre; >1,15 → bajo.
TOLERANCIA_PPTO = 0.10         # espejo de p_tolerancia_desviacion_presupuesto
FACTORES_PPTO = [1.00, 1.05, 0.85, 1.30, 0.95, 1.00, 1.15, 0.90, 1.02, 1.25, 0.80, 1.00]
PPTO_BASE_SIN_GASTO = 400      # categoría presupuestada que todavía no gastó


def presupuesto_sintetico(real_cat_mes):
    """Plan mensual sintético por categoría, calibrado sobre el gasto real para
    que haya meses dentro de tolerancia, alguno por encima y alguno por debajo.
    El anual solicitado se siembra cuadrando con la distribución mensual."""
    mensual, anual = {}, {}
    for cat, _clas in CATEGORIAS_PRESUPUESTO:
        total = sum(real_cat_mes.get((cat, m), 0) for m in range(1, 13))
        base = 0 if total else PPTO_BASE_SIN_GASTO
        vals = [round((real_cat_mes.get((cat, m), 0) * FACTORES_PPTO[m - 1] + base) / 10) * 10
                for m in range(1, 13)]
        mensual[cat], anual[cat] = vals, sum(vals)
    return mensual, anual


def mes_corte_ytd(hoy, anio_ppto):
    """Mes hasta el que acumula el YTD: el de la fecha de datos si el año en curso
    es el presupuestado; 12 si ya pasó; 0 si aún no empieza. Espejo de la fórmula."""
    if hoy.year > anio_ppto:
        return 12
    if hoy.year < anio_ppto:
        return 0
    return hoy.month


def calcular_presupuesto(ordenes, mensual, anual, anio, tolerancia, mes_ytd):
    """Bloque de comparación: presupuesto/real/desviación/%/estado por categoría ×
    mes, con SIN CLASIFICAR, subtotales fijo/variable, total y YTD."""
    cats = [c for c, _ in CATEGORIAS_PRESUPUESTO]
    filas = cats + [SIN_CLASIFICAR_PPTO]
    real = {(f, m): 0.0 for f in filas for m in range(1, 13)}
    total_mes = {m: 0.0 for m in range(1, 13)}          # control: total de COSTOS
    for o in ordenes:
        if o["anio"] != anio or o["mes"] == "":
            continue
        cat = o["categoria_presupuesto"]
        if cat not in filas:                             # defensivo: categoría desconocida
            cat = SIN_CLASIFICAR_PPTO
        real[(cat, o["mes"])] += o["costo_total"]
        total_mes[o["mes"]] += o["costo_total"]

    ppto = {(c, m): mensual[c][m - 1] for c in cats for m in range(1, 13)}
    for m in range(1, 13):
        ppto[(SIN_CLASIFICAR_PPTO, m)] = 0              # lo no clasificado no se presupuesta

    def estado(p, r):
        if p == 0 and abs(r) < 1e-9:
            return ""
        if p == 0:
            return "sobre"
        d = (r - p) / p
        return "dentro" if abs(d) <= tolerancia + 1e-12 else ("sobre" if d > 0 else "bajo")

    out = {}
    for f in filas:
        for m in range(1, 13):
            p, r = ppto[(f, m)], real[(f, m)]
            out[(f, m)] = {"presupuesto": p, "real": r, "desviacion": r - p,
                           "desviacion_pct": ((r - p) / p) if p else "",
                           "estado": estado(p, r)}
    # Subtotales por clasificación, total general y control del mes
    clas_de = dict(CATEGORIAS_PRESUPUESTO)
    for etiqueta, miembros in (("Subtotal FIJO", [c for c in cats if clas_de[c] == "fijo"]),
                               ("Subtotal VARIABLE", [c for c in cats if clas_de[c] == "variable"]),
                               ("TOTAL GENERAL", filas)):
        for m in range(1, 13):
            p = sum(out[(c, m)]["presupuesto"] for c in miembros)
            r = sum(out[(c, m)]["real"] for c in miembros)
            out[(etiqueta, m)] = {"presupuesto": p, "real": r, "desviacion": r - p,
                                  "desviacion_pct": ((r - p) / p) if p else "",
                                  "estado": estado(p, r)}
    ytd = {}
    for f in filas + ["Subtotal FIJO", "Subtotal VARIABLE", "TOTAL GENERAL"]:
        ytd[f] = {k: sum(out[(f, m)][k] for m in range(1, mes_ytd + 1))
                  for k in ("presupuesto", "real", "desviacion")}
    return {"filas": filas, "celdas": out, "ytd": ytd, "total_mes": total_mes,
            "mensual": mensual, "anual": anual, "anio": anio,
            "tolerancia": tolerancia, "mes_ytd": mes_ytd}


# ══════════════════════════════════════════════════════════════════════════
# 4. VALORES ESPERADOS (motor Python aplicado a los datos)
#    Es lo que las fórmulas del libro DEBEN producir.
# ══════════════════════════════════════════════════════════════════════════


def calcular_esperado(datos):
    hoy = datos["hoy"]
    ejec_por_id = {}
    for e in datos["ejecucion"]:
        ejec_por_id.setdefault(e["id_operacion"], e)  # primera coincidencia, como XLOOKUP
    exc = datos["excepciones"]
    # 6.2: franja horaria por turno (espejo de CAT_TURNOS). "" si no es un turno
    # del catálogo (VAC/X/vacío). La franja NO alimenta capacidad.
    franja_turno = {t[0]: (t[2], t[3]) for t in TURNOS_CAT}
    asig_por_clave = {}
    for a in datos["asignaciones"]:
        asig_por_clave.setdefault((a["semana"], a["dia"], a["tecnico"]), a)
        # Fecha real de la celda (semana + día) para consultar el calendario.
        # El lunes se deriva de la etiqueta ISO (igual que la fórmula del libro),
        # así ASIGNACIONES puede cubrir más semanas que las del plan (§7 banco).
        a["fecha"] = lunes_de_semana(a["semana"]) + timedelta(days=DIAS.index(a["dia"]))
        a["habil"] = es_habil(a["fecha"], a["area"], "", exc)   # capacidad: nivel área
        a["horas_disponibles"] = regla_5_horas_disponibles(a["turno"], a["habil"])
        # 6.6: supervisor fijo del técnico (ya viene de generar_datos, por esp).
        a["hora_inicio"], a["hora_fin"] = franja_turno.get(a["turno"], ("", ""))
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
        area_o = ceco[CECO_AREA] if ceco else SIN_CATALOGO
        sub_o = sub_area_efectiva(ceco[CECO_SUBAREA], ceco[CECO_AREA]) if ceco else SIN_CATALOGO
        habil_o = es_habil(f, area_o, sub_o, exc)             # nivel orden (área+sub)
        bh = backlog_habiles(f, hoy, exc)                     # días hábiles con signo
        enriquecidas.append({**o,
            "horas_efectivas": efectivas,
            "estado": CAT_ESTADOS.get(e["estado_sistema"], "Pendiente") if e else "Pendiente",
            "semana": semana, "anio": f.year if f else "", "mes": f.month if f else "",
            # DASHBOARD: clave de mes AAAA-MM y clase de mantenimiento heredada
            # del catálogo de tipos de OT (SIN CLASIFICAR si el tipo no la trae).
            "mes_clave": f"{f.year}-{f.month:02d}" if f else "",
            "dia_semana": dia,
            "clasificacion": regla_1_clasificacion(o["tipo_ot"], CAT_TIPOS),
            "clase_mantenimiento": (CAT_CLASE.get(o["tipo_ot"], "") or SIN_CLASIFICAR_CLASE)
                                   if o["tipo_ot"] else "",
            "linea": ceco[CECO_LINEA] if ceco else SIN_CATALOGO,
            "area": area_o, "sub_area": sub_o,
            "coordinador": ceco[CECO_COORD] if ceco else SIN_CATALOGO,
            "especialidad": CAT_PUESTOS.get(o["puesto_trabajo"], SIN_CATALOGO),
            "actividad": CAT_ACTIVIDADES.get(o["cod_actividad"], SIN_CATALOGO),
            # PRESUPUESTO OPEX: "" si la actividad no está en catálogo o no tiene
            # categoría asignada → su costo cae en SIN CLASIFICAR.
            "categoria_presupuesto": (CAT_CATEGORIA_PPTO.get(o["cod_actividad"], ("", ""))[0]
                                      or SIN_CLASIFICAR_PPTO),
            "es_habil": habil_o,
            "backlog_dias": backlog if backlog is not None else "",
            "backlog_habiles": bh,
            "estado_backlog": regla_3_estado_backlog(bh if bh != "" else None),
            "en_plan": regla_4_en_plan(bh if bh != "" else None),
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

    # ADHERENCIA (v2.4): las órdenes en día NO hábil no penalizan el
    # denominador — se excluyen del cálculo y se reportan aparte (VALIDACION).
    habiles = [o for o in enriquecidas if o["es_habil"] == "sí"]
    adherencia = {}
    for dim, valores in (("semana", serie_semanas),
                         ("area", [a for a in COORD_POR_AREA]),
                         ("sub_area", SUBAREAS),
                         ("especialidad", list(ESPECIALIDADES)),
                         ("coordinador", sorted(set(COORD_POR_AREA.values()))),
                         ("tecnico_asignado", [t[1] for t in TECNICOS_ACTIVOS]),
                         ("clasificacion", ["preventiva", "correctiva", "sin_clasificar"]),
                         ("clase_mantenimiento",
                          CLASES_MANTENIMIENTO + [SIN_CLASIFICAR_CLASE])):
        for v in valores:
            adherencia[(dim, v)] = regla_7_adherencia([o for o in habiles if o[dim] == v])

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
        for _tid, nombre, *_ in TECNICOS_ACTIVOS:
            carga_tecnicos[(sem, nombre)] = sum(
                o["horas_efectivas"] or 0 for o in enriquecidas
                if o["tecnico_asignado"] == nombre and o["semana"] == sem)
            capacidad_tecnicos[(sem, nombre)] = FACTOR_PRODUCTIVIDAD * sum(
                a["horas_disponibles"] for a in datos["asignaciones"]
                if a["tecnico"] == nombre and a["semana"] == sem)

    # ── 6.5: SEGUIMIENTO de horas reales (capa de cumplimiento, NO de capacidad;
    #    la base de 48 h y PERFIL_HH no se tocan). horas_reales = disp L-S + 8 si
    #    trabaja el domingo (turno). 56 turno / 48 banco / 0 VAC en semana normal.
    base_sem, tol = BASE_SEMANAL_HORAS, 0     # 48 h; tolerancia_horas_bono (default 0)
    disp_ls_por, posicion_por, trab_dom_por = {}, {}, {}
    for a in datos["asignaciones"]:
        k = (a["tecnico"], a["semana"])
        if a["dia"] != "domingo":
            disp_ls_por[k] = disp_ls_por.get(k, 0) + a["horas_disponibles"]
        if a["dia"] == "lunes":
            posicion_por[k] = a["posicion_ciclo"]
            trab_dom_por[k] = a["trabaja_domingo"]
    esp_por_tec = {t[1]: t[TEC_ESP] for t in TECNICOS_ACTIVOS}
    seguimiento_hh = []
    for _tid, nombre, *_ in TECNICOS_ACTIVOS:
        for sem in datos["semanas"]:
            k = (nombre, sem)
            hr = horas_reales_semana(disp_ls_por.get(k, 0), trab_dom_por.get(k) == "sí")
            seguimiento_hh.append({
                "tecnico": nombre, "semana": sem, "especialidad": esp_por_tec[nombre],
                "posicion": posicion_por.get(k, ""), "horas_reales": hr,
                "base_semanal": base_sem, "superavit_deficit": hr - base_sem})
    hr_por = {(s["tecnico"], s["semana"]): s["horas_reales"] for s in seguimiento_hh}
    # Cada semana del plan se asigna a un mes por su LUNES (clave "AAAA-MM").
    mes_de_sem = {datos["semanas"][i]: f"{d.year}-{d.month:02d}"
                  for i, d in enumerate(datos["lunes_sem"])}
    meses_seg = sorted(set(mes_de_sem.values()))
    semanas_de_mes = {m: [s for s in datos["semanas"] if mes_de_sem[s] == m] for m in meses_seg}
    seguimiento_mensual = []
    for _tid, nombre, *_ in TECNICOS_ACTIVOS:
        for m in meses_seg:
            ws_mes = semanas_de_mes[m]
            reales = sum(hr_por[(nombre, s)] for s in ws_mes)
            req = len(ws_mes) * base_sem
            seguimiento_mensual.append({
                "tecnico": nombre, "mes": m, "horas_reales_mes": reales,
                "horas_requeridas_mes": req, "brecha": reales - req,
                "cumple": "sí" if reales >= req - tol else "no"})
    # Déficit de capacidad por VAC (esp × semana): técnicos en VAC × base 48 h.
    # Informativo (para decidir contratar externo); NO cambia la capacidad base.
    esps_con_tec = [e for e in ESPECIALIDADES if any(t[TEC_ESP] == e for t in TECNICOS_ACTIVOS)]
    deficit_vac = {}
    for e in esps_con_tec:
        for sem in datos["semanas"]:
            nvac = sum(1 for a in datos["asignaciones"]
                       if a["especialidad"] == e and a["semana"] == sem
                       and a["dia"] == "lunes" and a["en_vacaciones"] == "sí")
            deficit_vac[(e, sem)] = nvac * base_sem

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
        # Calendario (v2.4)
        "en_dia_no_habil": sum(1 for o in enriquecidas
                               if o["orden"] and o["es_habil"] == "no"),
        "exc_area_desconocida": sum(1 for x in exc
                                    if x["area"] and x["area"] not in COORD_POR_AREA),
        "exc_sub_desconocida": sum(1 for x in exc
                                   if x["sub_area"] and x["sub_area"] not in SUBAREAS),
    }

    # --- Correo esperado de EXPORTAR (filtro por defecto: semana=semanas[1],
    #     turno y coordinador = "(todos)") --------------------------------
    def exportar_esperado(sem, top=5):
        scope = [o for o in enriquecidas if o["semana"] == sem and o["en_plan"] is True]
        hh_total = sum(o["horas_efectivas"] or 0 for o in scope)
        hh_prev = sum(o["horas_efectivas"] or 0 for o in scope if o["clasificacion"] == "preventiva")
        hh_corr = sum(o["horas_efectivas"] or 0 for o in scope if o["clasificacion"] == "correctiva")
        tecs = {t[1] for t in TECNICOS_ACTIVOS}
        n_tec = len({o["tecnico_asignado"] for o in scope
                     if o["tecnico_asignado"] in tecs})
        por_tec = {}
        for _tid, nombre, *_ in TECNICOS_ACTIVOS:
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

    # --- PRESUPUESTO OPEX: real por categoría × mes desde el MISMO campo que
    #     COSTOS (costo_total) y la MISMA convención de mes (anio/mes).
    anio_ppto = datos["anio_presupuesto"]
    real_cat_mes = {}
    for o in enriquecidas:
        if o["anio"] == anio_ppto and o["mes"] != "":
            k = (o["categoria_presupuesto"], o["mes"])
            real_cat_mes[k] = real_cat_mes.get(k, 0) + o["costo_total"]
    ppto_mensual, ppto_anual = presupuesto_sintetico(real_cat_mes)
    presupuesto = calcular_presupuesto(enriquecidas, ppto_mensual, ppto_anual, anio_ppto,
                                       TOLERANCIA_PPTO,
                                       mes_corte_ytd(datos["hoy"], anio_ppto))

    return {"ordenes": enriquecidas, "perfil": perfil, "adherencia": adherencia,
            "presupuesto": presupuesto,
            "ratio9": ratio9, "backlog_aging": backlog_aging, "meses": meses,
            "costos": costos, "equipos_orden": equipos_orden, "equipos_tot": equipos_tot,
            "carga_tecnicos": carga_tecnicos, "capacidad_tecnicos": capacidad_tecnicos,
            "serie_semanas": serie_semanas, "semanas_con_datos": semanas_con_datos,
            "validacion_extra": validacion_extra, "ajustes_esperado": ajustes_esperado,
            "exportar": exportar, "exportar_fn": exportar_esperado,
            "costos_sub": costos_sub, "backlog_sub": backlog_sub,
            "asignaciones": datos["asignaciones"], "excepciones": exc,
            "seguimiento_hh": seguimiento_hh, "seguimiento_mensual": seguimiento_mensual,
            "deficit_vac": deficit_vac, "meses_seg": meses_seg,
            "semanas_de_mes": semanas_de_mes, "esps_con_tec": esps_con_tec,
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
    "estado", "semana", "anio", "mes", "mes_clave", "dia_semana", "es_habil",
    "clasificacion", "clase_mantenimiento",
    "linea", "area", "sub_area", "coordinador", "especialidad", "actividad",
    "backlog_dias", "backlog_habiles", "estado_backlog", "en_plan",
    "tecnico_asignado", "turno_asignado", "HHA", "HHD",
    "costo_servicio", "costo_materiales", "costo_total", "categoria_presupuesto",
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
# 6.3: turno pasa a DERIVADO (efectivo). Entradas nuevas: turno_manual (override
# de excepción). Derivadas de auditoría: n_ciclo (N del ciclo) y posicion_ciclo
# (etiqueta del anillo). REGLA-5 y los lookups de franja (6.2) leen `turno`.
# 6.4: en_vacaciones (derivada, helper) — sí si la fecha cae en un periodo de
# PLAN_VACACIONES del técnico; el turno efectivo arrastra a "VAC".
# 6.6: coordinador → supervisor (fijo del técnico). 6.5: trabaja_domingo (helper).
CAMPOS_ASIGNACIONES = ["semana", "dia", "tecnico", "area", "especialidad",
                       "n_ciclo", "posicion_ciclo", "en_vacaciones",
                       "turno_manual", "turno",
                       "supervisor", "fecha", "horas_disponibles", "clave",
                       "hora_inicio", "hora_fin", "trabaja_domingo"]
CAMPOS_VACACIONES = ["tecnico", "fecha_inicio", "fecha_fin", "motivo"]
CAP_VACACIONES = 100         # filas provisionadas de tblVacaciones
# 6.5: seguimiento de horas reales (capa de cumplimiento, no de planificación).
CAMPOS_SEG_HH = ["tecnico", "semana", "especialidad", "posicion", "horas_reales",
                 "base_semanal", "superavit_deficit"]
CAMPOS_SEG_MES = ["tecnico", "mes", "horas_reales_mes", "horas_requeridas_mes",
                  "cumple", "brecha"]
CAMPOS_EXCEPCIONES = ["fecha", "tipo", "habil", "area", "sub_area", "motivo", "clave"]
CAP_EXCEPCIONES = 200        # filas provisionadas de tblExcepciones
CAP_CAL_DIAS = 760           # días del grid del calendario (nivel planta)
CAMPOS_IMPORT_ORDENES = ["orden", "operacion", "descripcion_general", "descripcion_operacion",
                         "equipo", "centro_costo", "puesto_trabajo", "cod_actividad",
                         "tipo_ot", "fecha_inicio", "horas_estimadas", "costo_plan"]


def formula_es_habil(R, fecha, area, sub):
    """Calendario (v2.4): resuelve hábil/no por especificidad, más específico
    primero. Devuelve la expresión (sin '=' inicial), en cualquier modo. La
    clave es TEXT(fecha,"yyyy-mm-dd")&"|"&area&"|"&sub; el argumento
    si_no_encontrado de cada nivel encadena al siguiente y, al final, al
    patrón semanal INDEX(patronHabil, WEEKDAY(fecha,2))."""
    fk = f'TEXT({fecha},"yyyy-mm-dd")'
    kA = f'{fk}&"|"&{area}&"|"&{sub}'
    kB = f'{fk}&"|"&{area}&"|"'
    kC = f'{fk}&"||"'
    patron = f'INDEX(patronHabil,WEEKDAY({fecha},2))'
    inner = R.busca(kC, "tblExcepciones", "clave", "habil", patron)
    midd = R.busca(kB, "tblExcepciones", "clave", "habil", inner)
    return R.busca(kA, "tblExcepciones", "clave", "habil", midd)


def formulas_ordenes(R):
    """Fórmulas por columna calculada de tblOrdenes (REGLAS 1, 2, 3, 4, 8 y
    calendario laboral)."""
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
            if campo == "mes_clave":
                # DASHBOARD: clave de mes AAAA-MM. Se arma con anio y mes ya
                # calculados (no con TEXT sobre la fecha) para no depender del
                # formato regional. Es la clave del selector y de los bloques
                # mensuales de ADHERENCIA / PERFIL_HH / BACKLOG.
                return (f'=IF({fe}="","",{f("anio", fila)}&"-"&'
                        f'TEXT({f("mes", fila)},"00"))')
            if campo == "dia_semana":
                return f'=IF({fe}="","",INDEX(lista_dias,WEEKDAY({fe},2)))'
            if campo == "es_habil":
                # Calendario laboral con el área y sub-área de la propia orden.
                return (f'=IF({fe}="","",'
                        + formula_es_habil(R, fe, f("area", fila), f("sub_area", fila)) + ")")
            if campo == "clase_mantenimiento":
                # DASHBOARD: la clase se HEREDA del catálogo de tipos de OT. Si el
                # tipo no está o no tiene clase, la orden cae en SIN CLASIFICAR
                # (visible en el mix), nunca desaparece.
                cl = R.busca(f("tipo_ot", fila), "tblTiposOT", "codigo",
                             "clase_mantenimiento", f'"{SIN_CLASIFICAR_CLASE}"')
                return (f'=IF({f("tipo_ot", fila)}="","",'
                        f'IF({cl}="","{SIN_CLASIFICAR_CLASE}",{cl}))')
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
            if campo == "categoria_presupuesto":
                # PRESUPUESTO OPEX: categoría heredada del CATÁLOGO de actividades.
                # Si la actividad no está en catálogo, o está pero sin categoría,
                # queda "" y su gasto cae en la fila SIN CLASIFICAR (nunca se pierde).
                cat = R.busca(f("cod_actividad", fila), "tblActividades", "codigo",
                              "categoria_presupuesto", '""')
                return (f'=IF({vacia},"",IF(OR(({cat})=0,({cat})=""),'
                        f'"{SIN_CLASIFICAR_PPTO}",{cat}))')
            if campo == "backlog_dias":
                return f'=IF({fe}="","",TODAY()-{fe})'
            if campo == "backlog_habiles":
                # Días HÁBILES (nivel planta) con signo, contados en el grid del
                # CALENDARIO. Coexiste con backlog_dias (calendario).
                return (f'=IF({fe}="","",IF({fe}<=TODAY(),'
                        f'COUNTIFS(cal_fechas,">="&{fe},cal_fechas,"<"&TODAY(),cal_habil,"sí"),'
                        f'-COUNTIFS(cal_fechas,">="&TODAY(),cal_fechas,"<"&{fe},cal_habil,"sí")))')
            if campo == "estado_backlog":
                # REGLA-3 v2.4: sobre días hábiles.
                b = f("backlog_habiles", fila)
                return (f'=IF({b}="","",IF({b}<0,"FUTURO",IF({b}>p_dias_backlog_max,'
                        f'"BACKLOG","MES CORRIENTE")))')
            if campo == "en_plan":
                # REGLA-4 v2.4: sobre días hábiles.
                b = f("backlog_habiles", fila)
                return (f'=IF({b}="",FALSE,AND({b}>p_dias_backlog_min,'
                        f'{b}<=p_dias_backlog_max))')
            if campo == "turno_asignado":
                clave = (f'{f("semana", fila)}&"|"&{f("dia_semana", fila)}&"|"&'
                         f'{f("tecnico_asignado", fila)}')
                # Una celda de turno vacía (p. ej. fin de semana) devuelve 0 al
                # buscarla; se coacciona a "" para no mostrar "0".
                lu = R.busca(clave, "tblAsignaciones", "clave", "turno", '""')
                return (f'=IF({f("tecnico_asignado", fila)}="","",'
                        f'IF(({lu})=0,"",{lu}))')
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
# DASHBOARD: las tarjetas se dibujan con CELDAS (combinadas, relleno y bordes),
# nunca con formas ni objetos de dibujo, para que se vean igual en Excel 2016 y
# en LibreOffice y para que el libro siga siendo un .xlsx sin objetos.
FILL_TARJETA = PatternFill("solid", fgColor="F7F9FC")
FILL_BANDA = PatternFill("solid", fgColor="1F4E78")
F_KPI = Font(name="Arial", size=26, bold=True, color="1F4E78")
F_KPI_TIT = Font(name="Arial", size=10, bold=True, color="FFFFFF")
F_KPI_META = Font(name="Arial", size=9, color="595959")
F_BOTON = Font(name="Arial", size=10, bold=True, color="1F4E78", underline="single")
_LADO = Side(style="thin", color="BFBFBF")
BORDE_TARJETA = Border(left=_LADO, right=_LADO, top=_LADO, bottom=_LADO)
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


# ── DASHBOARD: fechas derivadas de una clave de mes "AAAA-MM" ──────────────
# El corte NUNCA usa HOY(): se ancla a p_fecha_datos (la fecha de los datos del
# libro). Si el mes de la clave es el mes de esa fecha, el corte es el DÍA
# ANTERIOR (mes en curso parcial); en cualquier otro mes, el último día del mes.
def _mes_ini(c):
    return f'DATE(VALUE(LEFT({c},4)),VALUE(RIGHT({c},2)),1)'


def _mes_fin(c):
    return f'DATE(VALUE(LEFT({c},4)),VALUE(RIGHT({c},2))+1,0)'


MES_DE_FECHA_DATOS = 'YEAR(p_fecha_datos)&"-"&TEXT(MONTH(p_fecha_datos),"00")'


def _mes_corte(c):
    return f'IF({c}="","",IF({c}={MES_DE_FECHA_DATOS},p_fecha_datos-1,{_mes_fin(c)}))'


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
    # Anclas de los bloques mensuales que alimentan el DASHBOARD. Las hojas
    # fuente las publican al construirse y el tablero las lee: así el tablero
    # referencia celdas concretas en vez de recalcular nada.
    ANC = {}
    hoy = datos["hoy"]
    semanas = datos["semanas"]
    n_ord, n_ejec, n_asig = len(datos["ordenes"]), len(datos["ejecucion"]), len(datos["asignaciones"])

    TAB = {
        "tblOrdenes": Tabla("tblOrdenes", "ORDENES", 3, CAMPOS_ORDENES, CAP_FILAS),
        "tblEjecucion": Tabla("tblEjecucion", "2_IMPORTAR_EJECUCION", 8, CAMPOS_EJECUCION, CAP_FILAS),
        "tblAjustes": Tabla("tblAjustes", "AJUSTES", 3, CAMPOS_AJUSTES, CAP_AJUSTES),
        "tblTecnicos": Tabla("tblTecnicos", "TECNICOS", 3,
                             ["id", "nombre", "especialidad", "area", "supervisor",
                              "rotativo", "orden_rotacion", "activo"], len(TECNICOS)),
        "tblAsignaciones": Tabla("tblAsignaciones", "ASIGNACIONES", 3, CAMPOS_ASIGNACIONES, n_asig),
        "tblVacaciones": Tabla("tblVacaciones", "PLAN_VACACIONES", 3, CAMPOS_VACACIONES, CAP_VACACIONES),
        "tblSegHH": Tabla("tblSegHH", "SEGUIMIENTO_HH", 3, CAMPOS_SEG_HH,
                          len(TECNICOS) * len(semanas)),
        "tblSegMes": Tabla("tblSegMes", "SEGUIMIENTO_MENSUAL", 3, CAMPOS_SEG_MES,
                           len(TECNICOS) * len(esperado["meses_seg"])),
        "tblExcepciones": Tabla("tblExcepciones", "CALENDARIO", 14, CAMPOS_EXCEPCIONES, CAP_EXCEPCIONES),
        "tblCECO": Tabla("tblCECO", "CAT_CENTROS_COSTO", 3,
                         ["codigo", "descripcion", "planta", "area", "sub_area", "linea", "coordinador"],
                         len(CENTROS_COSTO)),
        "tblPuestos": Tabla("tblPuestos", "CAT_PUESTOS", 3,
                            ["codigo", "especialidad", "descripcion",
                             "es_especialidad_propia"], len(PUESTOS)),
        "tblActividades": Tabla("tblActividades", "CAT_ACTIVIDADES", 3,
                                ["codigo", "descripcion", "tipo",
                                 "categoria_presupuesto", "clasificacion"], len(ACTIVIDADES)),
        "tblTiposOT": Tabla("tblTiposOT", "CAT_TIPOS_OT", 3,
                            ["codigo", "descripcion", "clasificacion",
                             "clase_mantenimiento"], len(TIPOS_OT)),
        "tblEstados": Tabla("tblEstados", "CAT_ESTADOS_ERP", 3,
                            ["estado_sistema", "estado_normalizado"], len(ESTADOS_ERP)),
        "tblTurnos": Tabla("tblTurnos", "CAT_TURNOS", 3,
                           ["turno", "nombre", "hora_inicio", "hora_fin", "tipo"], len(TURNOS_CAT)),
        # 7.2: supervisores y motivos de ausencia pasan a catálogo
        "tblSupervisores": Tabla("tblSupervisores", "CAT_SUPERVISORES", 3,
                                 ["codigo", "nombre", "especialidad"], len(SUPERVISORES)),
        "tblMotivos": Tabla("tblMotivos", "CAT_MOTIVOS_AUSENCIA", 3,
                            ["motivo"], len(MOTIVOS_AUSENCIA)),
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
        "  4. Complete TECNICOS (incl. rotativo y orden_rotacion) y fije semana_referencia en",
        "     PARAMETROS: el turno de ASIGNACIONES se DERIVA solo de la rotación. Para una",
        "     excepción puntual escriba en turno_manual. Asigne técnicos en ORDENES. Los ajustes",
        "     de duración van en AJUSTES por id_operacion: se re-aplican solos tras re-importar.",
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
        # 6.3: semana_referencia es una FECHA que depende del ancla; su valor se
        # inyecta aquí (input azul con formato fecha).
        if p == "semana_referencia":
            v = datos["semana_referencia"]
        if p == "anio_presupuesto":
            v = datos["anio_presupuesto"]
        # DASHBOARD: la fecha de datos es el ancla del libro, no HOY().
        if p == "fecha_datos":
            v = datos["hoy"]
        # Un valor que empieza por "=" es una celda DERIVADA (fórmula): se
        # muestra con estilo de celda calculada (negro), no de input (azul),
        # y no lleva validación de entrada.
        es_formula = isinstance(v, str) and v.startswith("=")
        fmt = FMT_FECHA if isinstance(v, date) else ("0.00" if isinstance(v, float) else None)
        celda(ws, 4 + i, 2, v, font=F_TXT if es_formula else F_EDIT, fmt=fmt)
        celda(ws, 4 + i, 3, d, font=F_NOTA)
    celda(ws, 3, 5, "listas auxiliares", font=F_SEC)
    # 6.2: los turnos ya no viven aquí — su fuente única es CAT_TURNOS y la
    # lista de validación (lista_turnos) se arma en esa hoja. Aquí solo quedan
    # los códigos de no disponible y los días de la semana.
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
    dv3.add(f"B{FILA_PARAM['dias_laborables_base']}")   # entero positivo, como horas_jornada
    # base_semanal_horas es DERIVADA (fórmula): sin validación de entrada.
    dv4 = DataValidation(type="whole", operator="between", formula1="1", formula2="20")
    ws.add_data_validation(dv4)
    dv4.add(f"B{FILA_PARAM['top_tareas']}")
    # Metas de mix: enteros 0..100 (no bloquean; el cuadre es el que avisa).
    dv5 = DataValidation(type="whole", operator="between", formula1="0", formula2="100",
                         showErrorMessage=False)
    ws.add_data_validation(dv5)
    for _m in ("predictivo", "preventivo", "correctivo_programado", "emergencia", "legal"):
        dv5.add(f"B{FILA_PARAM['meta_pct_' + _m]}")
    ws.conditional_formatting.add(
        f"B{FILA_PARAM['cuadre_metas_mix']}",
        FormulaRule(formula=[f'LEFT($B${FILA_PARAM["cuadre_metas_mix"]},9)="DESCUADRE"'],
                    fill=FILL_ROJO))

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
        "p_dias_laborables_base": FILA_PARAM["dias_laborables_base"],
        "p_base_semanal_horas": FILA_PARAM["base_semanal_horas"],
        "p_semana_referencia": FILA_PARAM["semana_referencia"],
        "p_tolerancia_horas_bono": FILA_PARAM["tolerancia_horas_bono"],
        "p_anio_presupuesto": FILA_PARAM["anio_presupuesto"],
        "p_tolerancia_desviacion_presupuesto": FILA_PARAM["tolerancia_desviacion_presupuesto"],
        "p_fecha_datos": FILA_PARAM["fecha_datos"],
        "p_meta_pct_predictivo": FILA_PARAM["meta_pct_predictivo"],
        "p_meta_pct_preventivo": FILA_PARAM["meta_pct_preventivo"],
        "p_meta_pct_correctivo_programado": FILA_PARAM["meta_pct_correctivo_programado"],
        "p_meta_pct_emergencia": FILA_PARAM["meta_pct_emergencia"],
        "p_meta_pct_legal": FILA_PARAM["meta_pct_legal"],
    }
    for nom, fila in nombres.items():
        wb.defined_names.add(DefinedName(nom, attr_text=f"PARAMETROS!$B${fila}"))
    # lista_turnos (nombre) se define en CAT_TURNOS (6.2), fuente única.
    wb.defined_names.add(DefinedName("lista_no_disponible", attr_text="PARAMETROS!$G$5:$G$6"))
    wb.defined_names.add(DefinedName("lista_dias", attr_text="PARAMETROS!$I$5:$I$11"))

    # 7.2: BLOQUE DE LISTAS DE VALIDACIÓN. Toda lista cuyo contenido dependa de un
    # catálogo o de los datos vive aquí como RANGO (no como literal dentro de la
    # validación): así se puede editar sin tocar código y no hay dos fuentes que
    # puedan divergir. Las 1:1 con un catálogo se escriben como FÓRMULA (siguen
    # las ediciones del catálogo en vivo); las derivadas (valores distintos,
    # filtradas) se escriben como valores y se refrescan al regenerar.
    celda(ws, 3, 11, "listas de validación (rangos con nombre) — no editar salvo para "
                     "añadir valores", font=F_SEC)
    col_aux = [11]                       # K en adelante

    def lista_aux(nombre, titulo, valores, formulas=None):
        """Escribe una lista en una columna libre y registra su nombre definido."""
        c = col_aux[0]
        celda(ws, 4, c, titulo, font=F_NOTA)
        for i, v in enumerate(valores):
            celda(ws, 5 + i, c, formulas[i] if formulas else v)
        L_ = get_column_letter(c)
        wb.defined_names.add(DefinedName(
            nombre, attr_text=f"PARAMETROS!${L_}$5:${L_}${4 + len(valores)}"))
        ws.column_dimensions[L_].width = 22
        col_aux[0] += 1
        return nombre

    TODOS = "(todos)"
    ct = TAB["tblTurnos"]
    lista_aux("lista_f_turno", "filtro turno", [TODOS] + list(TURNOS),
              formulas=[f'="{TODOS}"'] + [f"=CAT_TURNOS!$A${ct.fila_ini + i}"
                                          for i in range(len(TURNOS_CAT))])
    areas_cat = list(dict.fromkeys(c[CECO_AREA] for c in CENTROS_COSTO))
    coords_cat = list(dict.fromkeys(c[CECO_COORD] for c in CENTROS_COSTO))
    lista_aux("lista_f_area", "filtro área", [TODOS] + areas_cat)
    lista_aux("lista_areas", "áreas (CAT_CENTROS_COSTO)", areas_cat)
    lista_aux("lista_f_coordinador", "filtro coordinador", [TODOS] + coords_cat)
    lista_aux("lista_f_subarea", "filtro sub-área", [TODOS] + SUBAREAS)
    lista_aux("lista_subareas", "sub-áreas (CAT_SUBAREAS)", SUBAREAS)
    lista_aux("lista_f_especialidad", "filtro especialidad", [TODOS] + list(ESPECIALIDADES))
    # Especialidades de PERSONAL PROPIO: derivadas del atributo del catálogo
    # (es_especialidad_propia), no de una lista paralela hardcodeada.
    lista_aux("lista_esp_propias", "especialidad propia (CAT_PUESTOS)", ESPECIALIDADES_PROPIAS)
    cc = TAB["tblCECO"]
    lista_aux("lista_ceco", "centros de costo", [c[0] for c in CENTROS_COSTO],
              formulas=[f"=CAT_CENTROS_COSTO!$A${cc.fila_ini + i}"
                        for i in range(len(CENTROS_COSTO))])
    cp = TAB["tblPuestos"]
    lista_aux("lista_puestos", "puestos de trabajo", [p[0] for p in PUESTOS],
              formulas=[f"=CAT_PUESTOS!$A${cp.fila_ini + i}" for i in range(len(PUESTOS))])
    ca = TAB["tblActividades"]
    lista_aux("lista_actividades", "actividades", [a[0] for a in ACTIVIDADES],
              formulas=[f"=CAT_ACTIVIDADES!$A${ca.fila_ini + i}" for i in range(len(ACTIVIDADES))])
    cti = TAB["tblTiposOT"]
    lista_aux("lista_tipos_ot", "tipos de OT", [t[0] for t in TIPOS_OT],
              formulas=[f"=CAT_TIPOS_OT!$A${cti.fila_ini + i}" for i in range(len(TIPOS_OT))])
    cs = TAB["tblSupervisores"]
    lista_aux("lista_supervisores", "supervisores", [s[1] for s in SUPERVISORES],
              formulas=[f"=CAT_SUPERVISORES!$B${cs.fila_ini + i}" for i in range(len(SUPERVISORES))])
    cmo = TAB["tblMotivos"]
    lista_aux("lista_motivos_ausencia", "motivos de ausencia", [m[0] for m in MOTIVOS_AUSENCIA],
              formulas=[f"=CAT_MOTIVOS_AUSENCIA!$A${cmo.fila_ini + i}"
                        for i in range(len(MOTIVOS_AUSENCIA))])
    # 7.2: lista_tecnicos = columna K de TECNICOS (activos compactados), no la
    # columna de nombres: un técnico con activo=no no aparece en los desplegables.
    _T = TAB["tblTecnicos"]
    wb.defined_names.add(DefinedName(
        "lista_tecnicos", attr_text=f"TECNICOS!$K${_T.fila_ini}:$K${_T.fila_fin}"))

    # --------------------------------------------- GUIA_IMPORTAR_ORDENES
    # 7.1: era `1_IMPORTAR_ORDENES` y PARECÍA zona de pegado (nombre numerado +
    # fila de cabeceras + filas de ejemplo), lo que confundía: las órdenes se
    # pegan en ORDENES!A4. Ahora es una GUÍA sin rejilla horizontal: el layout se
    # muestra en VERTICAL (una fila por columna esperada), así no invita a pegar.
    ws = wb.create_sheet("GUIA_IMPORTAR_ORDENES")
    ws.sheet_properties.tabColor = "A6A6A6"          # gris de guía, no naranja de pegado
    celda(ws, 1, 1, "⚠ ESTA HOJA NO RECIBE DATOS — es solo una guía de formato.", font=F_TIT)
    celda(ws, 2, 1, "Las órdenes se pegan en  ORDENES!A4  (columnas A:L, en un solo bloque).",
          font=F_SEC)
    notas = [
        "Ordene la exportación de su ERP con las 12 columnas de abajo, en ESE orden, y péguela",
        "EN UN SOLO PASO en ORDENES!A4 (o desde la primera fila libre). Nada más que hacer: las",
        "columnas calculadas ya están escritas en las 1.200 filas provisionadas de la tabla.",
        "«operacion» es opcional: si su ERP no maneja operaciones, déjela vacía y se asume \"0010\".",
        "Los ajustes de duración NO van aquí: se registran en AJUSTES por id_operacion y se",
        "re-aplican solos tras re-importar, aunque cambie el orden de las filas.",
        "REGLA-10 (hoja VALIDACION) reporta problemas pero nunca bloquea la importación.",
    ]
    for i, t in enumerate(notas, start=4):
        celda(ws, i, 1, t, font=F_NOTA)
    fila_g = 4 + len(notas) + 1
    celda(ws, fila_g, 1, "Layout esperado (vertical: una fila por columna a pegar)", font=F_SEC)
    encabezados(ws, fila_g + 1, ["col.", "nombre de la columna", "EJEMPLO (no pegar)",
                                 "EJEMPLO (no pegar)"])
    ejemplos = datos["ordenes"][:2]
    for j, campo in enumerate(CAMPOS_IMPORT_ORDENES):
        fr = fila_g + 2 + j
        celda(ws, fr, 1, f"{get_column_letter(j + 1)}")
        celda(ws, fr, 2, campo)
        for k, o in enumerate(ejemplos):
            celda(ws, fr, 3 + k, o[campo], font=F_NOTA, fill=FILL_GRIS,
                  fmt=FMT_FECHA if campo == "fecha_inicio" else None)
    for colw, w in (("A", 7), ("B", 26), ("C", 34), ("D", 34)):
        ws.column_dimensions[colw].width = w

    # ----------------------------------------------- 2_IMPORTAR_EJECUCION
    ws = wb.create_sheet("2_IMPORTAR_EJECUCION")
    ws.sheet_properties.tabColor = "ED7D31"
    celda(ws, 1, 1, "✔ ZONA DE PEGADO REAL — aquí SÍ se pegan datos: estados y costos (tblEjecucion)",
          font=F_TIT)
    notas = [
        "Pegue aquí los estados y costos reales del ERP, con estas cabeceras exactas, desde la primera fila vacía.",
        "(Las ÓRDENES no se pegan aquí ni en la hoja de guía: van en ORDENES!A4.)",
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
            elif campo in ("backlog_dias", "backlog_habiles"):
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
    # 7.2: campos importados que antes eran texto plano ahora tienen su lista de
    # catálogo. La validación de Excel NO impide pegar: el pegado en ORDENES!A4
    # sigue funcionando igual y el guardián real sigue siendo REGLA-10
    # (hoja VALIDACION), que reporta lo que quede fuera de catálogo.
    for campo, rango in (("centro_costo", "lista_ceco"),
                         ("puesto_trabajo", "lista_puestos"),
                         ("cod_actividad", "lista_actividades"),
                         ("tipo_ot", "lista_tipos_ot")):
        dvc = DataValidation(type="list", formula1=rango, allow_blank=True,
                             showErrorMessage=False)
        ws.add_data_validation(dvc)
        dvc.add(f"{let(campo)}{O.fila_ini}:{let(campo)}{O.fila_fin}")
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
    celda(ws, 1, 1, "TECNICOS (tblTecnicos) — catálogo editable de personal propio. "
                    "6.3: rotativo (sí/no) y orden_rotacion (1..N por especialidad×área "
                    "entre rotativos) alimentan la rotación. 6.6: supervisor fijo del técnico.",
          font=F_SEC)
    encabezados(ws, T.fila_enc, T.campos)
    for i, fila_t in enumerate(TECNICOS):
        fila = T.fila_ini + i
        for j, v in enumerate(fila_t, start=1):
            celda(ws, fila, j, v, font=F_EDIT)
    agregar_tabla(ws, T)
    # 7.2: especialidad desde el CATÁLOGO, filtrada por es_especialidad_propia
    # (OP y TERCERO no pueden ser técnicos propios). Sin lista paralela hardcodeada.
    dv = DataValidation(type="list", formula1="lista_esp_propias", allow_blank=False)
    ws.add_data_validation(dv)
    dv.add(f"C{T.fila_ini}:C{T.fila_fin}")
    dv = DataValidation(type="list", formula1="lista_areas", allow_blank=False)
    ws.add_data_validation(dv)
    dv.add(f"D{T.fila_ini}:D{T.fila_fin}")
    dv = DataValidation(type="list", formula1="lista_supervisores", allow_blank=True)
    ws.add_data_validation(dv)
    dv.add(f"E{T.fila_ini}:E{T.fila_fin}")
    # rotativo (F) y activo (H): dominio fijo sí/no, unificado con el resto del libro
    dv = DataValidation(type="list", formula1=f'"{SI},{NO}"', allow_blank=False)
    ws.add_data_validation(dv)
    dv.add(f"F{T.fila_ini}:F{T.fila_fin}")
    dv.add(f"H{T.fila_ini}:H{T.fila_fin}")
    # orden_rotacion (G): entero 1..N; vacío para no rotativos
    dv = DataValidation(type="whole", operator="between", formula1="1", formula2="30",
                        allow_blank=True)
    ws.add_data_validation(dv)
    dv.add(f"G{T.fila_ini}:G{T.fila_fin}")
    # 7.2: `activo` conectado. Columnas auxiliares que COMPACTAN los técnicos
    # activos: J numera los activos y K los lista sin huecos. `lista_tecnicos`
    # apunta a K, así un técnico con activo=no desaparece de los desplegables.
    celda(ws, T.fila_enc, 10, "nº activo", font=F_NOTA)
    celda(ws, T.fila_enc, 11, "técnicos activos (lista_tecnicos) — no editar", font=F_NOTA)
    for i in range(len(TECNICOS)):
        fr = T.fila_ini + i
        celda(ws, fr, 10, f'=IF($H{fr}="{SI}",COUNTIFS($H${T.fila_ini}:$H{fr},"{SI}"),"")')
        celda(ws, fr, 11, f'=IFERROR(INDEX($B${T.fila_ini}:$B${T.fila_fin},'
                          f'MATCH(ROW()-{T.fila_enc},$J${T.fila_ini}:$J${T.fila_fin},0)),"")')
    for colw, w in (("A", 12), ("B", 20), ("C", 12), ("D", 14), ("E", 22),
                    ("F", 9), ("G", 14), ("H", 8), ("J", 10), ("K", 24)):
        ws.column_dimensions[colw].width = w

    # ------------------------------------------------------- ASIGNACIONES
    ws = wb.create_sheet("ASIGNACIONES")
    ws.sheet_properties.tabColor = "4472C4"
    A = TAB["tblAsignaciones"]
    celda(ws, 1, 1, "ASIGNACIONES — el turno se DERIVA de la rotación (6.3) y arrastra a \"VAC\" si el "
                    "técnico está en PLAN_VACACIONES esa fecha (6.4), dejando su posición vacía "
                    "(hueco). Precedencia: turno_manual > (domingo) > VAC > rotación. REGLA-5 lee el "
                    "turno efectivo. Para cubrir un hueco, el supervisor escribe en turno_manual.",
          font=F_SEC)
    encabezados(ws, A.fila_enc, A.campos)
    rot_col = R.col("tblTecnicos", "rotativo")
    esp_col = R.col("tblTecnicos", "especialidad")
    area_col = R.col("tblTecnicos", "area")
    act_col = R.col("tblTecnicos", "activo")
    vt_col = R.col("tblVacaciones", "tecnico")
    vi_col = R.col("tblVacaciones", "fecha_inicio")
    vf_col = R.col("tblVacaciones", "fecha_fin")
    for i, a in enumerate(datos["asignaciones"]):
        fila = A.fila_ini + i
        nb = R.this("tblAsignaciones", "tecnico", fila)
        sm = R.this("tblAsignaciones", "semana", fila)
        dia_c = R.this("tblAsignaciones", "dia", fila)
        area_c = R.this("tblAsignaciones", "area", fila)
        esp_c = R.this("tblAsignaciones", "especialidad", fila)
        ncell = R.this("tblAsignaciones", "n_ciclo", fila)
        pccell = R.this("tblAsignaciones", "posicion_ciclo", fila)
        evcell = R.this("tblAsignaciones", "en_vacaciones", fila)
        tmcell = R.this("tblAsignaciones", "turno_manual", fila)
        tu = R.this("tblAsignaciones", "turno", fila)
        fe = R.this("tblAsignaciones", "fecha", fila)
        celda(ws, fila, 1, a["semana"])
        celda(ws, fila, 2, a["dia"])
        celda(ws, fila, 3, a["tecnico"])
        celda(ws, fila, 4, "=" + R.busca(nb, "tblTecnicos", "nombre", "area", '""'))
        celda(ws, fila, 5, "=" + R.busca(nb, "tblTecnicos", "nombre", "especialidad", '""'))
        # 6.3 n_ciclo: nº de posiciones del ciclo = rotativos de la MISMA
        # especialidad y área (soporta una especialidad repartida en varias
        # áreas: cada área su propio ciclo). 0 para no rotativos (Banco fijo).
        # 7.2: solo los técnicos ACTIVOS cuentan para el N del ciclo.
        celda(ws, fila, 6, f'=COUNTIFS({rot_col},"{SI}",{esp_col},{esp_c},{area_col},{area_c},'
                           f'{act_col},"{SI}")')
        # 6.3 posicion_ciclo (auditoría): etiqueta del anillo B(N-3)..B1/T3/T2/T1.
        # Anillo: pos<banco → "B"&(banco-pos); si no → "T"&(N-pos). banco=N-3.
        # "" el domingo (fuera de la base L-S) o sin técnico/semana; "B" si no rotativo.
        # NO cambia con VAC: el hueco se lee "iba a T2, está VAC".
        yy = f"VALUE(LEFT({sm},4))"
        lunes_iso = f'DATE({yy},1,4)-WEEKDAY(DATE({yy},1,4),2)+1+(VALUE(MID({sm},7,2))-1)*7'
        rot_lu = R.busca(nb, "tblTecnicos", "nombre", "rotativo", f'"{NO}"')
        act_lu = R.busca(nb, "tblTecnicos", "nombre", "activo", f'"{NO}"')
        ord_lu = R.busca(nb, "tblTecnicos", "nombre", "orden_rotacion", "0")
        semanas_expr = f'(({lunes_iso})-p_semana_referencia)/7'
        pos = f'MOD(({ord_lu}-1)+{semanas_expr},{ncell})'
        banco = f'({ncell}-3)'
        label = f'IF({pos}<{banco},"B"&({banco}-{pos}),"T"&({ncell}-{pos}))'
        # 7.2: un técnico con activo=no queda sin posición → sin turno → 0 h.
        celda(ws, fila, 7, f'=IF(OR({nb}="",{sm}="",{dia_c}="domingo",{act_lu}<>"{SI}"),"",'
                           f'IF({rot_lu}<>"{SI}","B",{label}))')
        # 6.4 en_vacaciones (helper): sí si la fecha cae en algún periodo de
        # PLAN_VACACIONES del técnico (COUNTIFS soporta varios periodos por técnico).
        celda(ws, fila, 8, f'=IF(COUNTIFS({vt_col},{nb},{vi_col},"<="&{fe},'
                           f'{vf_col},">="&{fe})>0,"sí","no")')
        # 6.3 turno_manual: override de excepción (desplegable = CAT_TURNOS + VAC/X).
        celda(ws, fila, 9, a["turno_manual"] or None, font=F_EDIT)
        # 6.4 turno EFECTIVO por precedencia: manual > (domingo "") > VAC > banda.
        celda(ws, fila, 10, f'=IF({tmcell}<>"",{tmcell},'
                            f'IF({pccell}="","",'
                            f'IF({evcell}="sí","VAC",'
                            f'IF(LEFT({pccell},1)="B","B",{pccell}))))')
        # 6.6: supervisor FIJO del técnico (búsqueda a TECNICOS; no rota, no
        # cambia con VAC; fuente única). Reemplaza al antiguo coordinador de área.
        celda(ws, fila, 11, "=" + R.busca(nb, "tblTecnicos", "nombre", "supervisor", '""'))
        # fecha real de la celda (para consultar el calendario): lunes ISO + día.
        celda(ws, fila, 12, f'=IF({sm}="","",{lunes_iso}+MATCH({dia_c},lista_dias,0)-1)',
              fmt=FMT_FECHA)
        habil = formula_es_habil(R, fe, area_c, '""')
        # REGLA-5 v2.4: 0 si turno (efectivo) no disponible/vacío O día no hábil.
        # SIN CAMBIOS: lee el turno efectivo; VAC ya da 0 (está en no disponible).
        celda(ws, fila, 13, f'=IF(OR({tu}="",ISNUMBER(MATCH({tu},lista_no_disponible,0)),'
                            f'({habil})<>"sí"),0,p_horas_jornada)')
        celda(ws, fila, 14, f'={sm}&"|"&{dia_c}&"|"&{nb}')
        # 6.2: franja horaria del turno efectivo desde CAT_TURNOS (metadato; NO
        # alimenta capacidad). En blanco si el turno es VAC/X/vacío.
        celda(ws, fila, 15, "=" + R.busca(tu, "tblTurnos", "turno", "hora_inicio", '""'))
        celda(ws, fila, 16, "=" + R.busca(tu, "tblTurnos", "turno", "hora_fin", '""'))
        # 6.5 trabaja_domingo (helper de seguimiento): sí si la posición es de
        # turno (T*) y no está de vacaciones. El domingo (posición "") da "no".
        celda(ws, fila, 17, f'=IF(AND(LEFT({pccell},1)="T",{evcell}="no"),"sí","no")')
    agregar_tabla(ws, A)
    ws.freeze_panes = "A4"
    # 6.3: el desplegable se MUEVE de turno a turno_manual (I); turno es derivado.
    dv = DataValidation(type="list", formula1="lista_turnos", allow_blank=True)
    ws.add_data_validation(dv)
    dv.add(f"I{A.fila_ini}:I{A.fila_fin}")
    for colw, w in (("A", 9), ("B", 11), ("C", 13), ("D", 13), ("E", 12), ("F", 8),
                    ("G", 14), ("H", 13), ("I", 13), ("J", 8), ("K", 18), ("L", 12),
                    ("M", 16), ("N", 26), ("O", 11), ("P", 11), ("Q", 14)):
        ws.column_dimensions[colw].width = w

    # --------------------------------------------------- PLAN_VACACIONES
    # 6.4: hoja de entrada (catálogo editable). Varias filas por técnico
    # (varios periodos). ASIGNACIONES marca VAC automáticamente cuando la fecha
    # de la fila cae dentro de algún periodo del técnico.
    ws = wb.create_sheet("PLAN_VACACIONES")
    ws.sheet_properties.tabColor = "4472C4"
    V = TAB["tblVacaciones"]
    celda(ws, 1, 1, "PLAN_VACACIONES (tblVacaciones) — periodos de vacaciones/permiso. Azul = "
                    "editable. El técnico de VAC sale de la rotación esas semanas (turno \"VAC\", "
                    "0 h) dejando su posición VACÍA; cubrir el hueco es acción manual (turno_manual).",
          font=F_SEC)
    encabezados(ws, V.fila_enc, V.campos)
    for i in range(CAP_VACACIONES):
        v = datos["plan_vacaciones"][i] if i < len(datos["plan_vacaciones"]) else {}
        fila = V.fila_ini + i
        celda(ws, fila, 1, v.get("tecnico"), font=F_EDIT)
        celda(ws, fila, 2, v.get("fecha_inicio"), font=F_EDIT, fmt=FMT_FECHA)
        celda(ws, fila, 3, v.get("fecha_fin"), font=F_EDIT, fmt=FMT_FECHA)
        celda(ws, fila, 4, v.get("motivo"), font=F_EDIT)
    agregar_tabla(ws, V)
    ws.freeze_panes = "A4"
    dv = DataValidation(type="list", formula1="lista_tecnicos", allow_blank=True)
    ws.add_data_validation(dv)
    dv.add(f"A{V.fila_ini}:A{V.fila_fin}")
    # 7.2: motivo desde CAT_MOTIVOS_AUSENCIA (catálogo editable, no hardcode)
    dvm = DataValidation(type="list", formula1="lista_motivos_ausencia", allow_blank=True,
                         showErrorMessage=False)
    ws.add_data_validation(dvm)
    dvm.add(f"D{V.fila_ini}:D{V.fila_fin}")
    for colw, w in (("A", 14), ("B", 13), ("C", 13), ("D", 26)):
        ws.column_dimensions[colw].width = w

    # ------------------------------------------------------- PRESUPUESTO
    # Presupuesto OPEX: plan manual por mes (entrada) vs gasto real (derivado del
    # MISMO campo que COSTOS, REGLA-8, y la MISMA convención de mes). No es una
    # regla del motor: es una hoja derivada.
    P = esperado["presupuesto"]
    ws = wb.create_sheet("PRESUPUESTO")
    ws.sheet_properties.tabColor = "7030A0"
    MESES_AB = ["ene", "feb", "mar", "abr", "may", "jun",
                "jul", "ago", "sep", "oct", "nov", "dic"]
    C0 = 3                                     # primera columna de mes (C)
    cm = lambda m: get_column_letter(C0 + m - 1)          # letra de la columna del mes
    RANGO_MESES = f"$C:$N"                                # solo documental
    ARR12 = "{1,2,3,4,5,6,7,8,9,10,11,12}"
    celda(ws, 1, 1, '="PRESUPUESTO OPEX "&p_anio_presupuesto&" — plan mensual vs gasto real ("&p_moneda&")"',
          font=F_TIT)
    for i, t in enumerate([
            "Alcance OPEX: materiales, servicios y terceros. La mano de obra propia NO es costo "
            "y no entra ni en el plan ni en el real. Nada de CAPEX ni de costo de ciclo de vida.",
            "La categoría de cada orden se hereda del CATÁLOGO de actividades (CAT_ACTIVIDADES: "
            "categoria_presupuesto + clasificacion). Onboardear otra empresa = editar el catálogo.",
            "El gasto real sale del mismo campo que COSTOS (costo_total, REGLA-8). Lo que no tenga "
            "categoría en catálogo cae en la fila SIN CLASIFICAR: el gasto nunca desaparece."], start=2):
        celda(ws, i, 1, t, font=F_NOTA)

    # ---- BLOQUE DE ENTRADA (manual) ----
    fe0 = 6
    celda(ws, fe0, 1, "BLOQUE DE ENTRADA — plan manual del año (azul = editable)", font=F_SEC)
    encabezados(ws, fe0 + 1, ["categoria", "clasificacion"] + MESES_AB
                + ["presupuesto_anual", "suma_12_meses", "cuadre"])
    fila_cat = {}
    for i, (cat, clas) in enumerate(CATEGORIAS_PRESUPUESTO):
        fr = fe0 + 2 + i
        fila_cat[cat] = fr
        celda(ws, fr, 1, cat)
        celda(ws, fr, 2, clas)
        for m in range(1, 13):
            celda(ws, fr, C0 + m - 1, P["mensual"][cat][m - 1], font=F_EDIT, fmt=FMT_DINERO)
        celda(ws, fr, 15, P["anual"][cat], font=F_EDIT, fmt=FMT_DINERO)
        celda(ws, fr, 16, f"=SUM($C{fr}:$N{fr})", fmt=FMT_DINERO)
        celda(ws, fr, 17, f'=IF(ROUND($P{fr}-$O{fr},2)=0,"cuadra",'
                          f'"DESCUADRE: "&TEXT($P{fr}-$O{fr},"+#,##0;-#,##0")&" vs anual")')
    fe1 = fe0 + 1 + len(CATEGORIAS_PRESUPUESTO)
    celda(ws, fe1 + 1, 1, "TOTAL", font=F_SEC)
    for col in list(range(C0, C0 + 12)) + [15, 16]:
        L_ = get_column_letter(col)
        celda(ws, fe1 + 1, col, f"=SUM({L_}{fe0 + 2}:{L_}{fe1})", fmt=FMT_DINERO)
    dvp = DataValidation(type="decimal", operator="greaterThanOrEqual", formula1="0",
                         allow_blank=True)
    ws.add_data_validation(dvp)
    dvp.add(f"C{fe0 + 2}:O{fe1}")
    ws.conditional_formatting.add(
        f"Q{fe0 + 2}:Q{fe1}",
        FormulaRule(formula=[f'LEFT($Q{fe0 + 2},9)="DESCUADRE"'], fill=FILL_ROJO))

    # ---- BLOQUE DE COMPARACIÓN (derivado) ----
    fc0 = fe1 + 3
    celda(ws, fc0, 1, "BLOQUE DE COMPARACIÓN — presupuesto vs real por categoría y mes", font=F_SEC)
    celda(ws, fc0 + 1, 1, "mes de corte del YTD:", font=F_NOTA)
    # YTD acumula hasta el mes de la fecha de datos; 12 si el año ya pasó, 0 si no empezó.
    celda(ws, fc0 + 1, 2, "=IF(YEAR(TODAY())>p_anio_presupuesto,12,"
                          "IF(YEAR(TODAY())<p_anio_presupuesto,0,MONTH(TODAY())))")
    cel_ytd = f"$B${fc0 + 1}"
    filas_comp = ([c for c, _ in CATEGORIAS_PRESUPUESTO] + [SIN_CLASIFICAR_PPTO]
                  + ["Subtotal FIJO", "Subtotal VARIABLE", "TOTAL GENERAL"])
    clas_de = dict(CATEGORIAS_PRESUPUESTO)
    miembros = {"Subtotal FIJO": [c for c, k in CATEGORIAS_PRESUPUESTO if k == "fijo"],
                "Subtotal VARIABLE": [c for c, k in CATEGORIAS_PRESUPUESTO if k == "variable"],
                "TOTAL GENERAL": [c for c, _ in CATEGORIAS_PRESUPUESTO] + [SIN_CLASIFICAR_PPTO]}
    o_col = R.col("tblOrdenes", "costo_total")
    o_anio = R.col("tblOrdenes", "anio")
    o_mes = R.col("tblOrdenes", "mes")
    o_cat = R.col("tblOrdenes", "categoria_presupuesto")
    bloques, fb = {}, fc0 + 3

    def matriz(fila0, titulo, fmt, celda_fn, extra=(), ytd_fn=None):
        """Emite una matriz categorías × 12 meses + YTD. Las filas se conocen ANTES
        de escribir (son deterministas), así los subtotales pueden referenciar a
        sus propias filas dentro del mismo bloque."""
        celda(ws, fila0, 1, titulo, font=F_SEC)
        encabezados(ws, fila0 + 1, ["categoria", "clasificacion"] + MESES_AB + ["YTD"])
        filas = {f: fila0 + 2 + i for i, f in enumerate(filas_comp)}
        for i, (etiqueta, _fn) in enumerate(extra):
            filas[etiqueta] = fila0 + 2 + len(filas_comp) + i
        for f in filas_comp:
            fr = filas[f]
            celda(ws, fr, 1, f, font=F_SEC if f.startswith(("Subtotal", "TOTAL")) else F_TXT)
            celda(ws, fr, 2, clas_de.get(f, ""))
            for m in range(1, 13):
                celda(ws, fr, C0 + m - 1, celda_fn(f, m, filas), fmt=fmt)
            # El YTD de las matrices numéricas acumula los meses hasta el corte;
            # las de % y estado no se pueden sumar: llevan su propia fórmula sobre
            # los YTD ya acumulados (SUMPRODUCT sobre texto daría #VALUE!).
            celda(ws, fr, 15,
                  ytd_fn(f) if ytd_fn else f"=SUMPRODUCT(({ARR12}<={cel_ytd})*($C{fr}:$N{fr}))",
                  fmt=fmt)
        for etiqueta, fn in extra:
            fr = filas[etiqueta]
            celda(ws, fr, 1, etiqueta, font=F_NOTA)
            for m in range(1, 13):
                celda(ws, fr, C0 + m - 1, fn(m, filas), fmt=fmt)
            celda(ws, fr, 15, f"=SUMPRODUCT(({ARR12}<={cel_ytd})*($C{fr}:$N{fr}))", fmt=fmt)
        return filas, fila0 + 3 + len(filas_comp) + len(extra)

    def suma_de(fs, m, miembros_f):
        return "=" + "+".join(f"{cm(m)}{fs[c]}" for c in miembros_f)

    def f_ppto(f, m, fs):
        if f in miembros:
            return suma_de(fs, m, miembros[f])
        if f == SIN_CLASIFICAR_PPTO:
            return 0                     # lo no clasificado no se presupuesta
        return f"={cm(m)}{fila_cat[f]}"   # referencia al bloque de entrada

    bloques["ppto"], fb = matriz(fb, "PRESUPUESTO (del bloque de entrada)",
                                 FMT_DINERO, f_ppto)

    def f_real(f, m, fs):
        if f in miembros:
            return suma_de(fs, m, miembros[f])
        return (f'=SUMIFS({o_col},{o_anio},p_anio_presupuesto,{o_mes},{m},'
                f'{o_cat},$A{fs[f]})')

    bloques["real"], fb = matriz(
        fb, "REAL (gasto del mes; mismo campo y misma convención de mes que COSTOS)",
        FMT_DINERO, f_real,
        extra=[("CONTROL — total de COSTOS del mes",
                lambda m, fs: f'=SUMIFS({o_col},{o_anio},p_anio_presupuesto,{o_mes},{m})'),
               ("DIFERENCIA (debe ser 0)",
                lambda m, fs: f'=ROUND({cm(m)}{fs["TOTAL GENERAL"]}-'
                              f'{cm(m)}{fs["CONTROL — total de COSTOS del mes"]},2)')])

    bloques["desv"], fb = matriz(
        fb, "DESVIACIÓN (real − presupuesto)", FMT_DINERO,
        lambda f, m, fs: f"={cm(m)}{bloques['real'][f]}-{cm(m)}{bloques['ppto'][f]}")

    bloques["pct"], fb = matriz(
        fb, "DESVIACIÓN %", "0.0%",
        lambda f, m, fs: (f'=IF({cm(m)}{bloques["ppto"][f]}=0,"",'
                          f'{cm(m)}{bloques["desv"][f]}/{cm(m)}{bloques["ppto"][f]})'),
        ytd_fn=lambda f: (f'=IF($O${bloques["ppto"][f]}=0,"",'
                          f'$O${bloques["desv"][f]}/$O${bloques["ppto"][f]})'))

    bloques["estado"], fb = matriz(
        fb, "ESTADO (semáforo · tolerancia = p_tolerancia_desviacion_presupuesto)", None,
        lambda f, m, fs: (
            f'=IF(AND({cm(m)}{bloques["ppto"][f]}=0,{cm(m)}{bloques["real"][f]}=0),"",'
            f'IF({cm(m)}{bloques["ppto"][f]}=0,"sobre",'
            f'IF(ABS({cm(m)}{bloques["desv"][f]}/{cm(m)}{bloques["ppto"][f]})'
            f'<=p_tolerancia_desviacion_presupuesto,"dentro",'
            f'IF({cm(m)}{bloques["desv"][f]}>0,"sobre","bajo"))))'),
        ytd_fn=lambda f: (
            f'=IF(AND($O${bloques["ppto"][f]}=0,$O${bloques["real"][f]}=0),"",'
            f'IF($O${bloques["ppto"][f]}=0,"sobre",'
            f'IF(ABS($O${bloques["desv"][f]}/$O${bloques["ppto"][f]})'
            f'<=p_tolerancia_desviacion_presupuesto,"dentro",'
            f'IF($O${bloques["desv"][f]}>0,"sobre","bajo"))))'))

    # El DASHBOARD lee estas filas tal cual (KPI 4 y gráfico D): no recalcula el
    # presupuesto, solo acumula las celdas mensuales que ya están aquí.
    for _k in ("ppto", "real"):
        for _f in ("TOTAL GENERAL", "Subtotal FIJO", "Subtotal VARIABLE"):
            ANC[f"ppto_{_k}_{_f.split()[-1].lower()}"] = bloques[_k][_f]

    # Reconciliación visible: la fila DIFERENCIA debe quedar en 0 los 12 meses.
    fr_dif = bloques["real"]["DIFERENCIA (debe ser 0)"]
    ws.conditional_formatting.add(
        f"C{fr_dif}:O{fr_dif}",
        CellIsRule(operator="notEqual", formula=["0"], fill=FILL_ROJO))

    # Semáforo del bloque ESTADO
    fe_ini, fe_fin = min(bloques["estado"].values()), max(bloques["estado"].values())
    for texto, relleno in (("dentro", FILL_VERDE), ("sobre", FILL_ROJO), ("bajo", FILL_AMAR)):
        ws.conditional_formatting.add(
            f"C{fe_ini}:O{fe_fin}",
            CellIsRule(operator="equal", formula=[f'"{texto}"'], fill=relleno))

    ws.freeze_panes = "C7"
    for colw, w in ([("A", 26), ("B", 13)] + [(cm(m), 11) for m in range(1, 13)]
                    + [("O", 13), ("P", 14), ("Q", 30)]):
        ws.column_dimensions[colw].width = w

    # --------------------------------------------------- SEGUIMIENTO_HH
    # 6.5: horas REALES por técnico × semana (capa de seguimiento; NO cambia la
    # base de 48 h ni PERFIL_HH). horas_reales = disp L-S (REGLA-5, suma domingo=0)
    # + 8 si trabaja el domingo. superavit_deficit = horas_reales − 48.
    ws = wb.create_sheet("SEGUIMIENTO_HH")
    ws.sheet_properties.tabColor = "70AD47"
    SH = TAB["tblSegHH"]
    celda(ws, 1, 1, "SEGUIMIENTO DE HORAS REALES (6.5) — capa de cumplimiento individual. 56 h en "
                    "turno (48 + domingo), 48 en banco, 0 en VAC. El +8 del domingo es superávit y "
                    "NO entra en PERFIL_HH (la capacidad de planificación sigue en 48 h).", font=F_SEC)
    encabezados(ws, SH.fila_enc, SH.campos)
    ah_disp = R.col("tblAsignaciones", "horas_disponibles")
    ah_tec = R.col("tblAsignaciones", "tecnico")
    ah_sem = R.col("tblAsignaciones", "semana")
    ah_dom = R.col("tblAsignaciones", "trabaja_domingo")
    for i, s in enumerate(esperado["seguimiento_hh"]):
        fila = SH.fila_ini + i
        tc = R.this("tblSegHH", "tecnico", fila)
        sc = R.this("tblSegHH", "semana", fila)
        hrc = R.this("tblSegHH", "horas_reales", fila)
        bsc = R.this("tblSegHH", "base_semanal", fila)
        celda(ws, fila, 1, s["tecnico"])
        celda(ws, fila, 2, s["semana"])
        celda(ws, fila, 3, "=" + R.busca(tc, "tblTecnicos", "nombre", "especialidad", '""'))
        # posición derivada de la semana (lunes) — muestra la posición aunque VAC.
        celda(ws, fila, 4, "=" + R.busca(f'{sc}&"|lunes|"&{tc}', "tblAsignaciones",
                                         "clave", "posicion_ciclo", '""'))
        # horas_reales = SUMIFS(disp L-S) + 8 si algún día de turno trabaja el domingo.
        celda(ws, fila, 5, f'=SUMIFS({ah_disp},{ah_tec},{tc},{ah_sem},{sc})'
                           f'+IF(COUNTIFS({ah_tec},{tc},{ah_sem},{sc},{ah_dom},"sí")>0,8,0)')
        celda(ws, fila, 6, "=p_base_semanal_horas")
        celda(ws, fila, 7, f"={hrc}-{bsc}")
    agregar_tabla(ws, SH)
    ws.freeze_panes = "A4"
    # Déficit de capacidad por VAC (esp × semana) — informativo (contratar externo);
    # NO cambia la capacidad base. = técnicos en VAC esa semana × base 48 h.
    fdef = SH.fila_fin + 3
    celda(ws, fdef, 1, "DÉFICIT DE CAPACIDAD POR VACACIONES (esp × semana) — informativo, "
                       "no cambia la capacidad base", font=F_SEC)
    encabezados(ws, fdef + 1, ["especialidad", "semana", "tecnicos_vac", "deficit_horas"])
    ah_esp = R.col("tblAsignaciones", "especialidad")
    ah_dia = R.col("tblAsignaciones", "dia")
    ah_vac = R.col("tblAsignaciones", "en_vacaciones")
    r = fdef + 2
    for e in esperado["esps_con_tec"]:
        for sem in semanas:
            celda(ws, r, 1, e)
            celda(ws, r, 2, sem)
            celda(ws, r, 3, f'=COUNTIFS({ah_esp},"{e}",{ah_sem},"{sem}",'
                            f'{ah_dia},"lunes",{ah_vac},"sí")')
            celda(ws, r, 4, f'=C{r}*p_base_semanal_horas')
            r += 1
    for colw, w in (("A", 14), ("B", 11), ("C", 13), ("D", 10), ("E", 14), ("F", 13), ("G", 16)):
        ws.column_dimensions[colw].width = w

    # ----------------------------------------------- SEGUIMIENTO_MENSUAL
    # 6.5: acumulado por técnico × mes (base del bono). Cada semana se asigna a un
    # mes por su lunes. horas_requeridas_mes = nº de semanas × 48. cumple con
    # tolerancia p_tolerancia_horas_bono. NO cambia la capacidad ni PERFIL_HH.
    ws = wb.create_sheet("SEGUIMIENTO_MENSUAL")
    ws.sheet_properties.tabColor = "70AD47"
    SM = TAB["tblSegMes"]
    celda(ws, 1, 1, "SEGUIMIENTO MENSUAL (6.5) — base del bono. horas_reales_mes acumula el "
                    "SEGUIMIENTO_HH; requeridas = nº de semanas del mes × 48. cumple usa la "
                    "tolerancia p_tolerancia_horas_bono. Un técnico con VAC en el mes queda por debajo.",
          font=F_SEC)
    encabezados(ws, SM.fila_enc, SM.campos)
    sh_hr = R.col("tblSegHH", "horas_reales")
    sh_tec = R.col("tblSegHH", "tecnico")
    sh_sem = R.col("tblSegHH", "semana")
    for i, s in enumerate(esperado["seguimiento_mensual"]):
        fila = SM.fila_ini + i
        tc = R.this("tblSegMes", "tecnico", fila)
        hrm = R.this("tblSegMes", "horas_reales_mes", fila)
        reqm = R.this("tblSegMes", "horas_requeridas_mes", fila)
        semanas_mes = esperado["semanas_de_mes"][s["mes"]]
        celda(ws, fila, 1, s["tecnico"])
        celda(ws, fila, 2, s["mes"])
        suma = "+".join(f'SUMIFS({sh_hr},{sh_tec},{tc},{sh_sem},"{w}")' for w in semanas_mes)
        celda(ws, fila, 3, "=" + suma)
        celda(ws, fila, 4, f"={len(semanas_mes)}*p_base_semanal_horas")
        celda(ws, fila, 5, f'=IF({hrm}>={reqm}-p_tolerancia_horas_bono,"sí","no")')
        celda(ws, fila, 6, f"={hrm}-{reqm}")
    agregar_tabla(ws, SM)
    ws.freeze_panes = "A4"
    for colw, w in (("A", 14), ("B", 10), ("C", 16), ("D", 18), ("E", 9), ("F", 10)):
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

    # ---------------------------------------------------------- CALENDARIO
    ws = wb.create_sheet("CALENDARIO")
    ws.sheet_properties.tabColor = "70AD47"
    celda(ws, 1, 1, "CALENDARIO LABORAL — un día no hábil no aporta capacidad ni penaliza los "
                    "indicadores. es_habil resuelve por especificidad: excepción fecha+área+sub-área "
                    "→ fecha+área → fecha → patrón semanal.", font=F_TIT)
    # Parte A: patrón semanal (default L-V hábil, S-D no hábil). Editable.
    celda(ws, 3, 1, "Parte A — patrón semanal (marcar una sola vez, aplica todo el año)", font=F_SEC)
    encabezados(ws, 4, ["dia", "habil"])
    for i, (dia, hab) in enumerate(PATRON_SEMANAL):
        celda(ws, 5 + i, 1, dia)
        celda(ws, 5 + i, 2, hab, font=F_EDIT)
    dvp = DataValidation(type="list", formula1='"sí,no"', allow_blank=False)
    ws.add_data_validation(dvp)
    dvp.add("B5:B11")
    # Parte B: excepciones (tblExcepciones). Solo fechas que rompen el patrón.
    EX = TAB["tblExcepciones"]
    celda(ws, 13, 1, "Parte B — excepciones que rompen el patrón (feriados, paros, días "
                     "especiales). área vacía = toda la planta; sub-área vacía = toda el área.",
          font=F_SEC)
    encabezados(ws, EX.fila_enc, EX.campos)
    for i in range(CAP_EXCEPCIONES):
        x = datos["excepciones"][i] if i < len(datos["excepciones"]) else {}
        fila = EX.fila_ini + i
        celda(ws, fila, 1, x.get("fecha"), font=F_EDIT, fmt=FMT_FECHA)
        celda(ws, fila, 2, x.get("tipo"), font=F_EDIT)
        celda(ws, fila, 3, x.get("habil"), font=F_EDIT)
        celda(ws, fila, 4, x.get("area"), font=F_EDIT)
        celda(ws, fila, 5, x.get("sub_area"), font=F_EDIT)
        celda(ws, fila, 6, x.get("motivo"), font=F_EDIT)
        fx = R.this("tblExcepciones", "fecha", fila)
        celda(ws, fila, 7, f'=IF({fx}="","",TEXT({fx},"yyyy-mm-dd")&"|"&'
                           f'{R.this("tblExcepciones", "area", fila)}&"|"&'
                           f'{R.this("tblExcepciones", "sub_area", fila)})')
    agregar_tabla(ws, EX)
    dvx = DataValidation(type="list", formula1='"sí,no"', allow_blank=False)
    ws.add_data_validation(dvx)
    dvx.add(f"C{EX.fila_ini}:C{EX.fila_fin}")
    # 7.2 (hallazgo del barrido): área y sub-área de las excepciones son
    # editables y salen de catálogo — REGLA-10 ya las audita, pero faltaba el
    # desplegable. En blanco = toda la planta / toda el área, así que se admite
    # vacío y no se bloquea el pegado.
    dva = DataValidation(type="list", formula1="lista_areas", allow_blank=True,
                         showErrorMessage=False)
    ws.add_data_validation(dva)
    dva.add(f"D{EX.fila_ini}:D{EX.fila_fin}")
    dvs = DataValidation(type="list", formula1="lista_subareas", allow_blank=True,
                         showErrorMessage=False)
    ws.add_data_validation(dvs)
    dvs.add(f"E{EX.fila_ini}:E{EX.fila_fin}")
    ws.conditional_formatting.add(
        f"C{EX.fila_ini}:C{EX.fila_fin}",
        CellIsRule(operator="equal", formula=['"no"'], fill=FILL_ROJO))
    # Parte C: grid de fechas (nivel planta) para contar días hábiles del backlog.
    celda(ws, 3, 9, "Parte C — grid del calendario (nivel planta) — no editar", font=F_NOTA)
    encabezados(ws, 4, ["fecha", "habil_planta"], col_ini=9)
    ini_cal = date(datos["hoy"].year, 1, 1)
    for i in range(CAP_CAL_DIAS):
        fila = 5 + i
        celda(ws, fila, 9, ini_cal + timedelta(days=i), fmt=FMT_FECHA)
        fc = f"$I{fila}"
        celda(ws, fila, 10, "=" + formula_es_habil(R, fc, '""', '""'))
    for colw, w in (("A", 12), ("B", 8), ("C", 22), ("D", 8), ("E", 16), ("F", 40),
                    ("G", 26), ("I", 12), ("J", 12)):
        ws.column_dimensions[colw].width = w
    wb.defined_names.add(DefinedName("patronHabil", attr_text="CALENDARIO!$B$5:$B$11"))
    wb.defined_names.add(DefinedName("cal_fechas",
                                     attr_text=f"CALENDARIO!$I$5:$I${4 + CAP_CAL_DIAS}"))
    wb.defined_names.add(DefinedName("cal_habil",
                                     attr_text=f"CALENDARIO!$J$5:$J${4 + CAP_CAL_DIAS}"))

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
    # ── MES A MES (fuente del DASHBOARD) ───────────────────────────────────
    # Carga y capacidad PRODUCTIVA por especialidad y mes, con el mismo corte que
    # ADHERENCIA. La capacidad sale de las MISMAS horas_disponibles de
    # ASIGNACIONES que usa el bloque semanal, multiplicadas por el factor de
    # productividad: es capacidad productiva, no tiempo nominal de presencia.
    fpm = fila_r9 + CAP_SEM + 3
    ANC["perfil_mes"] = fpm
    celda(ws, fpm - 1, 1, "MES A MES — carga vs capacidad PRODUCTIVA por especialidad "
                          "(fuente del DASHBOARD; no editar). Capacidad productiva = horas "
                          "disponibles (REGLA-5) × p_factor_productividad. Nunca se exige el "
                          "100 % del tiempo de presencia.", font=F_SEC)
    esp_mes = ESPECIALIDADES_PROPIAS
    cab_pm = ["mes", "corte", "inicio_mes"]
    for e_ in esp_mes:
        cab_pm += [f"planificada_{e_}", f"productiva_{e_}"]
    cab_pm += ["planificada_TOTAL", "productiva_TOTAL", "pct_carga"]
    encabezados(ws, fpm, cab_pm)
    o_mesk = R.col("tblOrdenes", "mes_clave")
    o_fecha = R.col("tblOrdenes", "fecha_inicio")
    a_fecha = R.col("tblAsignaciones", "fecha")
    a_esp = R.col("tblAsignaciones", "especialidad")
    a_disp = R.col("tblAsignaciones", "horas_disponibles")
    for i, (anio_m, mes_m) in enumerate(esperado["meses"]):
        fr = fpm + 1 + i
        celda(ws, fr, 1, f"{anio_m}-{mes_m:02d}")
        celda(ws, fr, 2, "=" + _mes_corte(f"$A{fr}"), fmt=FMT_FECHA)
        celda(ws, fr, 3, "=" + _mes_ini(f"$A{fr}"), fmt=FMT_FECHA)
        for j, e_ in enumerate(esp_mes):
            cp, cc = 4 + 2 * j, 5 + 2 * j
            celda(ws, fr, cp,
                  f'=SUMIFS({R.col("tblOrdenes", "horas_efectivas")},'
                  f'{R.col("tblOrdenes", "especialidad")},"{e_}",'
                  f'{o_mesk},$A{fr},{o_fecha},"<="&$B{fr})', fmt=FMT_HH)
            celda(ws, fr, cc,
                  f'=SUMIFS({a_disp},{a_esp},"{e_}",{a_fecha},">="&$C{fr},'
                  f'{a_fecha},"<="&$B{fr})*p_factor_productividad', fmt=FMT_HH)
        ctp, ctc = 4 + 2 * len(esp_mes), 5 + 2 * len(esp_mes)
        Lp = [get_column_letter(4 + 2 * j) + str(fr) for j in range(len(esp_mes))]
        Lc = [get_column_letter(5 + 2 * j) + str(fr) for j in range(len(esp_mes))]
        celda(ws, fr, ctp, "=" + "+".join(Lp), fmt=FMT_HH)
        celda(ws, fr, ctc, "=" + "+".join(Lc), fmt=FMT_HH)
        celda(ws, fr, ctc + 1,
              f"=IF({get_column_letter(ctc)}{fr}=0,\"\","
              f"{get_column_letter(ctp)}{fr}/{get_column_letter(ctc)}{fr})", fmt=FMT_PCT)
    col_pct = get_column_letter(6 + 2 * len(esp_mes))
    semaforo_carga(ws, f"{col_pct}{fpm + 1}:{col_pct}{fpm + len(esperado['meses'])}")

    for colw, w in (("A", 13), ("B", 13), ("C", 13), ("D", 14), ("E", 14), ("F", 14),
                    ("G", 14), ("H", 12), ("I", 11), ("N", 13), ("O", 18)):
        ws.column_dimensions[colw].width = w

    # ------------------------------------------------------- PLAN_SEMANAL
    ws = wb.create_sheet("PLAN_SEMANAL")
    ws.sheet_properties.tabColor = "7030A0"
    celda(ws, 1, 1, "PLAN SEMANAL — el gráfico de carga y la grilla responden a los mismos "
                    "selectores. \"(todos)\" desactiva un criterio; \"-\" significa vacío.", font=F_SEC)
    # 7.1: el selector de SEMANA debe listar TODAS las semanas presentes en los
    # datos (ORDENES + ASIGNACIONES), no solo las de la ventana del plan; si no,
    # no se puede filtrar por semanas que sí tienen filas en la grilla. Como la
    # lista supera el límite de ~255 caracteres de una validación literal, se
    # escribe en un rango auxiliar (columna X, oculta) y la validación apunta
    # ahí por nombre definido. El resto de selectores salen de catálogo (turno de
    # CAT_TURNOS, área/sub-área/coordinador de CAT_CENTROS_COSTO, especialidad de
    # CAT_PUESTOS) o de un dominio fijo (día), así que siguen como lista literal.
    semanas_datos = sorted(set(esperado["serie_semanas"])
                           | {a["semana"] for a in datos["asignaciones"]})
    COL_AUX = 24                                      # columna X
    celda(ws, 2, COL_AUX, "semanas con datos (validación) — no editar", font=F_NOTA)
    celda(ws, 3, COL_AUX, "(todos)")
    for i, sem in enumerate(semanas_datos):
        celda(ws, 4 + i, COL_AUX, sem)
    fila_aux_fin = 3 + len(semanas_datos)
    ws.column_dimensions[get_column_letter(COL_AUX)].hidden = True
    wb.defined_names.add(DefinedName(
        "lista_semanas_plan",
        attr_text=f"PLAN_SEMANAL!${get_column_letter(COL_AUX)}$3:"
                  f"${get_column_letter(COL_AUX)}${fila_aux_fin}"))

    # 7.2: solo "día" sigue siendo literal (dominio fijo); el resto sale de su
    # catálogo o de los datos a través de un rango con nombre.
    criterios = [("semana", 2, "lista_semanas_plan", semanas[1]),
                 ("día", 4, ["(todos)"] + list(DIAS), "(todos)"),
                 ("turno", 6, "lista_f_turno", "(todos)"),
                 ("coordinador", 8, "lista_f_coordinador", "(todos)"),
                 ("área", 10, "lista_f_area", "(todos)"),
                 ("especialidad", 12, "lista_f_especialidad", "(todos)"),
                 ("sub-área", 14, "lista_f_subarea", "(todos)")]
    for nombre, colc, lista, defecto in criterios:
        celda(ws, 3, colc - 1, nombre + ":", font=F_SEC)
        celda(ws, 3, colc, defecto, font=F_EDIT, fill=FILL_GRIS)
        f1 = lista if isinstance(lista, str) else '"' + ",".join(lista) + '"'
        dv = DataValidation(type="list", formula1=f1, allow_blank=False)
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
    for i, (_tid, nombre, esp_t, *_) in enumerate(TECNICOS_ACTIVOS):
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
    # 7.1 (c): con 16 técnicos, 32 etiquetas apiladas se encimaban. Se dejan SOLO
    # en la serie de sobreasignación —la que hay que ver— y el resto se lee por
    # el eje, ahora visible.
    barras.series[1].dLbls = DataLabelList(showVal=True)
    # 7.1 (a): SIN máximo fijo. El eje se autoescala en cada cambio de selector
    # (antes estaba clavado en 46,76, dimensionado para una sola semana, y al
    # filtrar "(todos)" las barras del año quedaban aplastadas).
    barras.y_axis.scaling.min = 0
    barras.y_axis.title = "HH"
    # 7.1 (b): ejes VISIBLES con su escala. `delete=None` dejaba que el
    # consumidor los ocultara; se fuerza a False. El eje de categorías además
    # iba con axPos="l" (izquierda) por defecto de openpyxl: va abajo.
    barras.y_axis.delete = False
    barras.x_axis.delete = False
    barras.x_axis.axPos = "b"
    barras.x_axis.title = "Técnico"
    barras.y_axis.majorTickMark = "out"
    barras.x_axis.majorTickMark = "out"
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
    celda(ws, 1, 1, "ADHERENCIA (REGLA-7) — rojo < 90 %, amarillo 90–95 %, verde > 95 %. "
                    "Solo días hábiles: las órdenes en día no laborable no penalizan (se reportan "
                    "en VALIDACION).", font=F_TIT)

    def bloque_adh(fila0, titulo, campo, valores, con_meta=False, ocultar=()):
        """valores: literales o fórmulas '=...' (etiquetas dinámicas de semana);
        ocultar: offsets (0-based) de filas de datos que quedan ocultas."""
        celda(ws, fila0, 1, titulo, font=F_SEC)
        cabb = ["valor", "total_ot", "cerradas", "adherencia_conteo", "hh_total",
                "hh_cerradas", "adherencia_horas"] + (["meta"] if con_meta else [])
        encabezados(ws, fila0 + 1, cabb)
        # v2.4: solo días hábiles — las órdenes en día no hábil no penalizan.
        hab = f'{R.col("tblOrdenes", "es_habil")},"sí"'
        for i, v in enumerate(valores):
            fr = fila0 + 2 + i
            celda(ws, fr, 1, v)
            celda(ws, fr, 2, f'=COUNTIFS({R.col("tblOrdenes", campo)},$A{fr},{hab})')
            celda(ws, fr, 3, f'=COUNTIFS({R.col("tblOrdenes", campo)},$A{fr},'
                             f'{R.col("tblOrdenes", "estado")},"Cerrada",{hab})')
            celda(ws, fr, 4, f'=IF(B{fr}=0,"",C{fr}/B{fr})', fmt=FMT_PCT)
            celda(ws, fr, 5, f'=SUMIFS({R.col("tblOrdenes", "horas_efectivas")},'
                             f'{R.col("tblOrdenes", campo)},$A{fr},{hab})', fmt=FMT_HH)
            celda(ws, fr, 6, f'=SUMIFS({R.col("tblOrdenes", "horas_efectivas")},'
                             f'{R.col("tblOrdenes", campo)},$A{fr},'
                             f'{R.col("tblOrdenes", "estado")},"Cerrada",{hab})', fmt=FMT_HH)
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
    f5 = bloque_adh(f4, "POR CLASE DE MANTENIMIENTO (mix; la clase la hereda la orden de "
                    "CAT_TIPOS_OT)", "clase_mantenimiento",
                    CLASES_MANTENIMIENTO + [SIN_CLASIFICAR_CLASE])
    f6 = bloque_adh(f5, "POR TÉCNICO", "tecnico_asignado", [t[1] for t in TECNICOS_ACTIVOS])

    # ── MES A MES (fuente del DASHBOARD) ───────────────────────────────────
    # El tablero NO calcula: lee estas filas. Aquí vive el corte (mes en curso
    # hasta el día ANTERIOR a p_fecha_datos), la adherencia del mes, el
    # cumplimiento legal y el mix por clase con su reconciliación.
    fm = f6 + 1
    ANC["adh_mes"] = fm          # fila de encabezados; los datos empiezan en fm+1
    celda(ws, fm - 1, 1, "MES A MES — corte del tablero (fuente del DASHBOARD; no editar). "
                         "El mes de la fecha de datos se corta el DÍA ANTERIOR a ella; el resto, "
                         "a fin de mes. El mix cuenta TODAS las órdenes del mes (la adherencia, "
                         "solo días hábiles, como REGLA-7).", font=F_SEC)
    cab_mes = (["mes", "corte", "total_ot", "cerradas", "adherencia", "meta",
                "legal_programadas", "legal_cerradas", "legal_adherencia", "legal_vencidas"]
               + CLASES_MANTENIMIENTO + [SIN_CLASIFICAR_CLASE,
                                         "CONTROL — órdenes del mes", "DIFERENCIA (debe ser 0)"])
    encabezados(ws, fm, cab_mes)
    o_mesk = R.col("tblOrdenes", "mes_clave")
    o_fecha = R.col("tblOrdenes", "fecha_inicio")
    o_est = R.col("tblOrdenes", "estado")
    o_clase = R.col("tblOrdenes", "clase_mantenimiento")
    for i, (anio_m, mes_m) in enumerate(esperado["meses"]):
        fr = fm + 1 + i
        celda(ws, fr, 1, f"{anio_m}-{mes_m:02d}")
        celda(ws, fr, 2, "=" + _mes_corte(f"$A{fr}"), fmt=FMT_FECHA)
        base = f'{o_mesk},$A{fr},{o_fecha},"<="&$B{fr}'
        hab = f'{R.col("tblOrdenes", "es_habil")},"sí"'
        celda(ws, fr, 3, f"=COUNTIFS({base},{hab})")
        celda(ws, fr, 4, f'=COUNTIFS({base},{hab},{o_est},"Cerrada")')
        celda(ws, fr, 5, f'=IF($C{fr}=0,"",$D{fr}/$C{fr})', fmt=FMT_PCT)
        celda(ws, fr, 6, "=p_meta_adherencia", fmt="0%")
        # Cumplimiento legal: se mide sobre TODAS las órdenes legales del mes
        # (también las de día no hábil): un vencimiento normativo no se excusa
        # porque cayera en domingo.
        leg = f'{base},{o_clase},"legal"'
        celda(ws, fr, 7, f"=COUNTIFS({leg})")
        celda(ws, fr, 8, f'=COUNTIFS({leg},{o_est},"Cerrada")')
        celda(ws, fr, 9, f'=IF($G{fr}=0,"",$H{fr}/$G{fr})', fmt=FMT_PCT)
        celda(ws, fr, 10, f'=COUNTIFS({leg},{o_est},"Pendiente")')
        for j, cl in enumerate(CLASES_MANTENIMIENTO + [SIN_CLASIFICAR_CLASE]):
            celda(ws, fr, 11 + j, f'=COUNTIFS({base},{o_clase},"{cl}")')
        c_ini = get_column_letter(11)
        c_fin = get_column_letter(10 + len(CLASES_MANTENIMIENTO) + 1)
        col_ctrl = 11 + len(CLASES_MANTENIMIENTO) + 1
        celda(ws, fr, col_ctrl, f"=COUNTIFS({base})")
        celda(ws, fr, col_ctrl + 1,
              f"=SUM({c_ini}{fr}:{c_fin}{fr})-{get_column_letter(col_ctrl)}{fr}")
    ult_mes = fm + len(esperado["meses"])
    escala_adherencia(ws, f"E{fm + 1}:E{ult_mes}")
    escala_adherencia(ws, f"I{fm + 1}:I{ult_mes}")
    ws.conditional_formatting.add(f"J{fm + 1}:J{ult_mes}",
                                  CellIsRule(operator="greaterThan", formula=["0"], fill=FILL_ROJO))
    col_dif = get_column_letter(12 + len(CLASES_MANTENIMIENTO) + 1)
    ws.conditional_formatting.add(f"{col_dif}{fm + 1}:{col_dif}{ult_mes}",
                                  CellIsRule(operator="notEqual", formula=["0"], fill=FILL_ROJO))
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
    f2 = matriz_backlog(f1, "POR SUB-ÁREA (herencia: área sin subdividir con su propio nombre)",
                        "sub_area", SUBAREAS)

    # ── AL CORTE DEL TABLERO (fuente del DASHBOARD) ────────────────────────
    # Semanas de backlog = horas pendientes acumuladas hasta el corte ÷ capacidad
    # productiva de una semana. Es una AGREGACIÓN nueva sobre datos que ya
    # existen (estado, horas_efectivas, fecha): el detalle por tramos sigue
    # siendo el de arriba, y el tablero enlaza a él.
    fbm = f2 + 1
    ANC["backlog_mes"] = fbm
    celda(ws, fbm - 1, 1, "AL CORTE DEL TABLERO (fuente del DASHBOARD; no editar) — el backlog "
                          "es ACUMULADO: cuenta todo lo pendiente con fecha hasta el corte del "
                          "mes, no solo lo del mes.", font=F_SEC)
    encabezados(ws, fbm, ["mes", "corte", "ordenes_pendientes", "hh_pendientes",
                          "capacidad_productiva_semanal", "semanas_de_backlog"])
    o_fecha = R.col("tblOrdenes", "fecha_inicio")
    o_est = R.col("tblOrdenes", "estado")
    for i, (anio_m, mes_m) in enumerate(esperado["meses"]):
        fr = fbm + 1 + i
        celda(ws, fr, 1, f"{anio_m}-{mes_m:02d}")
        celda(ws, fr, 2, "=" + _mes_corte(f"$A{fr}"), fmt=FMT_FECHA)
        pend = f'{o_est},"Pendiente",{o_fecha},"<="&$B{fr}'
        celda(ws, fr, 3, f"=COUNTIFS({pend})")
        celda(ws, fr, 4, f'=SUMIFS({R.col("tblOrdenes", "horas_efectivas")},{pend})', fmt=FMT_HH)
        celda(ws, fr, 5,
              f'=p_base_semanal_horas*p_factor_productividad*'
              f'COUNTIFS({R.col("tblTecnicos", "activo")},"{SI}")', fmt=FMT_HH)
        celda(ws, fr, 6, f'=IF($E{fr}=0,"",$D{fr}/$E{fr})', fmt="0.0")
    for colw, w in (("F", 20), ("E", 26), ("D", 15), ("C", 19)):
        ws.column_dimensions[colw].width = w
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
        # Calendario (v2.4)
        ("Órdenes programadas en día NO laborable",
         f'=SUMPRODUCT(--({oid}<>""),--({R.col("tblOrdenes", "es_habil")}="no"))',
         "Posible error de programación; o una excepción laborable que falta cargar."),
        ("Excepciones con área fuera de catálogo",
         f'=SUMPRODUCT(--({R.col("tblExcepciones", "area")}<>""),'
         f'--ISNA(MATCH({R.col("tblExcepciones", "area")},{R.col("tblCECO", "area")},0)))',
         "Revisar la columna area de CALENDARIO contra CAT_CENTROS_COSTO."),
        ("Excepciones con sub-área fuera de catálogo",
         f'=SUMPRODUCT(--({R.col("tblExcepciones", "sub_area")}<>""),'
         f'--ISNA(MATCH({R.col("tblExcepciones", "sub_area")},{R.col("tblCECO", "sub_area")},0)))',
         "Revisar la columna sub_area de CALENDARIO contra CAT_CENTROS_COSTO."),
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
         "Catálogo de puestos de trabajo → especialidad. es_especialidad_propia marca "
         "quién puede ser técnico propio (rotación y capacidad)",
         [("B", '"ELE,MEC,AUT,OP,TERCERO"'), ("D", f'"{SI},{NO}"')]),
        ("CAT_ACTIVIDADES", "tblActividades", ACTIVIDADES,
         "Catálogo de actividades", ("C", '"correctivo,preventivo,predictivo,legal"')),
        ("CAT_TIPOS_OT", "tblTiposOT", TIPOS_OT,
         "Traducción de tipos de OT del ERP → preventiva/correctiva (REGLA-1) y → clase "
         "de mantenimiento (mix del DASHBOARD). Un tipo sin clase cae en SIN CLASIFICAR",
         [("C", '"preventiva,correctiva"'),
          ("D", '"' + ",".join(CLASES_MANTENIMIENTO) + '"')]),
        ("CAT_ESTADOS_ERP", "tblEstados", ESTADOS_ERP,
         "Traducción de estados del ERP → Cerrada/Pendiente", ("B", '"Cerrada,Pendiente"')),
        # 6.2: catálogo de turnos con franja horaria (fuente única).
        ("CAT_TURNOS", "tblTurnos", TURNOS_CAT,
         "Turnos con su franja horaria (metadato; la capacidad no se deriva de ella)",
         ("E", '"banco,rotativo"')),
        # 7.2: los supervisores dejan de ser cadenas sueltas; TECNICOS.supervisor
        # los toma de aquí. Los motivos de ausencia, igual, para PLAN_VACACIONES.
        ("CAT_SUPERVISORES", "tblSupervisores", SUPERVISORES,
         "Supervisores por especialidad — TECNICOS.supervisor sale de aquí",
         ("C", "lista_esp_propias")),
        ("CAT_MOTIVOS_AUSENCIA", "tblMotivos", MOTIVOS_AUSENCIA,
         "Motivos de ausencia — PLAN_VACACIONES.motivo sale de aquí", None),
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
        for colv, lista in ([val] if isinstance(val, tuple) else (val or [])):
            dv = DataValidation(type="list", formula1=lista, allow_blank=False)
            ws.add_data_validation(dv)
            dv.add(f"{colv}{tb.fila_ini}:{colv}{tb.fila_fin}")
        for j in range(len(tb.campos)):
            ws.column_dimensions[get_column_letter(j + 1)].width = 22

    # 6.2: lista de validación del turno en ASIGNACIONES = bandas de CAT_TURNOS
    # (espejadas por fórmula, fuente única) + los códigos de no disponible.
    # Repunta el nombre lista_turnos aquí; el rango auxiliar de PARAMETROS se
    # retiró para no dejar dos fuentes.
    tt = TAB["tblTurnos"]
    wsT = wb["CAT_TURNOS"]
    celda(wsT, 1, 7, "lista de validación (turnos + no disponible) — no editar", font=F_NOTA)
    for i in range(len(TURNOS_CAT)):
        celda(wsT, tt.fila_ini + i, 7, f"=A{tt.fila_ini + i}")     # espejo de la banda
    celda(wsT, tt.fila_ini + len(TURNOS_CAT), 7, "=PARAMETROS!$G$5")   # VAC
    celda(wsT, tt.fila_ini + len(TURNOS_CAT) + 1, 7, "=PARAMETROS!$G$6")  # X
    wsT.column_dimensions["G"].width = 26
    ult_val = tt.fila_ini + len(TURNOS_CAT) + 1
    if "lista_turnos" in wb.defined_names:
        del wb.defined_names["lista_turnos"]
    wb.defined_names.add(DefinedName(
        "lista_turnos", attr_text=f"CAT_TURNOS!$G${tt.fila_ini}:$G${ult_val}"))

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
    # 7.2: mismo criterio que PLAN_SEMANAL — los cuatro selectores salen de un
    # rango con nombre. B3 usa `lista_semanas_plan` (TODAS las semanas con datos),
    # que era el mismo bug de 7.1: antes listaba solo las 4 de la ventana.
    for etiqueta, colc, lista, defecto in [("semana", 2, "lista_semanas_plan", semanas[1]),
                                           ("turno", 4, "lista_f_turno", "(todos)"),
                                           ("coordinador", 6, "lista_f_coordinador", "(todos)"),
                                           ("sub-área", 8, "lista_f_subarea", "(todos)")]:
        celda(ws, 3, colc - 1, etiqueta + ":", font=F_SEC)
        celda(ws, 3, colc, defecto, font=F_EDIT, fill=FILL_GRIS)
        dv = DataValidation(type="list", formula1=lista, allow_blank=False)
        ws.add_data_validation(dv)
        dv.add(f"{get_column_letter(colc)}3")

    MAXPROG, MAXTOP, NT = 200, 20, len(TECNICOS_ACTIVOS)
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
        if campo == "es_habil":
            Rim = Refs("compatibles", TAB)   # fuerza INDEX/MATCH en el ejemplo
            return f'=IF({a1("fecha_inicio")}="","",' + \
                formula_es_habil(Rim, a1("fecha_inicio"), a1("area"), a1("sub_area")) + ")"
        raise KeyError(campo)

    campos_comp = ["estado", "clasificacion", "linea", "area", "sub_area", "coordinador",
                   "especialidad", "actividad", "es_habil", "horas_efectivas", "turno_asignado",
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

    # ------------------------------------------------------ _BANCO_PRUEBA
    # §7: manifiesto de siembra del banco. Solo existe en el libro del banco
    # (--anio-completo). Sirve para contrastar VALIDACION contra lo sembrado
    # sin contar a ojo: cada fila "val_*" debe coincidir con su chequeo.
    man = datos.get("manifiesto")
    if man:
        ws = wb.create_sheet("_BANCO_PRUEBA")
        ws.sheet_properties.tabColor = "A6A6A6"
        celda(ws, 1, 1, "§7 BANCO DE PRUEBA — manifiesto de siembra", font=F_TIT)
        celda(ws, 2, 1, "Cantidades EXACTAS sembradas a propósito. Las filas 'val_*' se "
                        "contrastan una a una contra la hoja VALIDACION (REGLA-10 reporta, "
                        "nunca bloquea). Datos deterministas: misma semilla → mismos valores.",
              font=F_NOTA)
        encabezados(ws, 4, ["concepto", "valor sembrado"])
        for i, (k, v) in enumerate(man.items()):
            fr = 5 + i
            celda(ws, fr, 1, k)
            celda(ws, fr, 2, v, fmt=FMT_FECHA if isinstance(v, date) else None)
        for colw, w in (("A", 38), ("B", 46)):
            ws.column_dimensions[colw].width = w

    # ═══════════════════════════════════════════════════════════ DASHBOARD
    # Capa VISUAL y de SOLO LECTURA. No implementa ninguna regla ni guarda una
    # segunda fuente de verdad: cada KPI es un INDEX/MATCH a la fila del mes en
    # ADHERENCIA / PERFIL_HH / BACKLOG, o una acumulación de celdas que ya
    # calcula PRESUPUESTO. Se dibuja con CELDAS (combinadas + relleno + bordes)
    # y formato condicional: sin formas, sin objetos de dibujo y sin macros.
    ws = wb.create_sheet("DASHBOARD")
    ws.sheet_properties.tabColor = "1F4E78"
    NM = len(esperado["meses"])
    fa0, fa1 = ANC["adh_mes"] + 1, ANC["adh_mes"] + NM
    fp0, fp1 = ANC["perfil_mes"] + 1, ANC["perfil_mes"] + NM
    fb0, fb1 = ANC["backlog_mes"] + 1, ANC["backlog_mes"] + NM

    def r_adh(col):
        return f"ADHERENCIA!${col}${fa0}:${col}${fa1}"

    def r_per(col):
        return f"PERFIL_HH!${col}${fp0}:${col}${fp1}"

    def r_bkl(col):
        return f"BACKLOG!${col}${fb0}:${col}${fb1}"

    SEL = "$B$3"

    def del_mes(rango, rango_mes):
        """Lee la celda del mes seleccionado en una hoja fuente. El tablero no
        recalcula: localiza la fila del mes y la lee tal cual."""
        return f'IFERROR(INDEX({rango},MATCH({SEL},{rango_mes},0)),"")'

    col_carga = get_column_letter(6 + 2 * len(ESPECIALIDADES_PROPIAS))
    col_mix0 = 11                                   # 1.ª columna de mix en ADHERENCIA

    # ---- encabezado ------------------------------------------------------
    celda(ws, 1, 1, '="TABLERO DE MANTENIMIENTO — "&p_nombre_planta&" · "&p_nombre_empresa',
          font=F_TIT)
    ws.merge_cells("A1:R1")
    celda(ws, 2, 1, "Solo lectura: cada indicador se lee de su hoja de origen (botonera de abajo). "
                    "Las metas de mix son convención de industria, NO una norma; se ajustan en "
                    "PARAMETROS.", font=F_NOTA)
    ws.merge_cells("A2:R2")
    celda(ws, 3, 1, "Mes:", font=F_SEC)
    # Al abrir, el tablero muestra el mes de la fecha de datos (la vista natural);
    # si ese mes no tiene órdenes, cae al último mes con datos.
    _mes_hoy = f"{datos['hoy'].year}-{datos['hoy'].month:02d}"
    _meses_txt = [f"{a_}-{m_:02d}" for a_, m_ in esperado["meses"]]
    celda(ws, 3, 2, _mes_hoy if _mes_hoy in _meses_txt else _meses_txt[-1], font=F_EDIT)
    # El corte se declara SIEMPRE en pantalla, y se ancla a p_fecha_datos: nunca
    # a HOY(), para que el tablero sea la misma foto cada vez que se abre.
    celda(ws, 3, 4,
          f'="Fecha de datos: "&TEXT(p_fecha_datos,"yyyy-mm-dd")&"   ·   "&'
          f'IF({SEL}={MES_DE_FECHA_DATOS},'
          f'"MES EN CURSO: incluye hasta el "&TEXT(p_fecha_datos-1,"yyyy-mm-dd")&'
          f'" (ni el día de la fecha de datos ni los posteriores entran)",'
          f'IF({SEL}<{MES_DE_FECHA_DATOS},"mes cerrado: incluye el mes completo",'
          f'"mes futuro: muestra lo PLANIFICADO del mes completo"))', font=F_SEC)
    ws.merge_cells("D3:R3")

    # ---- botonera de navegación (HYPERLINK; sin macros) ------------------
    for i, (hoja, rot) in enumerate([
            ("PLAN_SEMANAL", "PLAN SEMANAL"), ("ADHERENCIA", "ADHERENCIA"),
            ("PERFIL_HH", "PERFIL HH"), ("BACKLOG", "BACKLOG"),
            ("PRESUPUESTO", "PRESUPUESTO"), ("ORDENES", "ORDENES"),
            ("VALIDACION", "VALIDACION")]):
        c0 = 1 + i * 2
        celda(ws, 4, c0, f'=HYPERLINK("#{hoja}!A1","▸ {rot}")', font=F_BOTON,
              fill=FILL_GRIS, alinear="center")
        ws.merge_cells(start_row=4, start_column=c0, end_row=4, end_column=c0 + 1)
    # El encabezado (título + selector + botonera) queda fijo al desplazarse.
    ws.freeze_panes = "A6"

    # ---- 6 tarjetas KPI --------------------------------------------------
    def tarjeta(fila, col, titulo, formula, fmt, meta, nota, semaforo=None):
        """Tarjeta hecha con celdas: banda de título, número grande combinado,
        línea de meta y línea de origen. El semáforo es formato condicional."""
        c1, c2 = col, col + 4
        L1, L2 = get_column_letter(c1), get_column_letter(c2)
        celda(ws, fila, c1, titulo, font=F_KPI_TIT, fill=FILL_BANDA, alinear="center")
        ws.merge_cells(start_row=fila, start_column=c1, end_row=fila, end_column=c2)
        celda(ws, fila + 1, c1, formula, font=F_KPI, fmt=fmt, fill=FILL_TARJETA,
              alinear="center")
        ws.merge_cells(start_row=fila + 1, start_column=c1, end_row=fila + 2, end_column=c2)
        celda(ws, fila + 3, c1, meta, font=F_KPI_META, fill=FILL_TARJETA, alinear="center")
        ws.merge_cells(start_row=fila + 3, start_column=c1, end_row=fila + 3, end_column=c2)
        celda(ws, fila + 4, c1, nota, font=F_NOTA, fill=FILL_TARJETA, alinear="center")
        ws.merge_cells(start_row=fila + 4, start_column=c1, end_row=fila + 4, end_column=c2)
        for f_ in range(fila, fila + 5):
            for c_ in range(c1, c2 + 1):
                ws.cell(row=f_, column=c_).border = BORDE_TARJETA
        ws.row_dimensions[fila + 1].height = 26
        ws.row_dimensions[fila + 2].height = 12
        if semaforo:
            semaforo(f"{L1}{fila + 1}:{L2}{fila + 1}", f"{L1}{fila + 1}")

    def sem_num(rango, ref, cortes):
        """Semáforo numérico que ignora la celda vacía: sin el ISNUMBER, Excel
        compara texto contra número y pintaría de rojo una tarjeta en blanco."""
        for expr, fill in cortes:
            ws.conditional_formatting.add(rango, FormulaRule(
                formula=[f"AND(ISNUMBER({ref}),{expr.format(c=ref)})"], fill=fill))

    F1, F2 = 6, 12
    tarjeta(F1, 1, "1 · ADHERENCIA AL PROGRAMA",
            "=" + del_mes(r_adh("E"), r_adh("A")), "0.0%",
            '="meta "&TEXT(p_meta_adherencia,"0%")&"  ·  REGLA-7, solo días hábiles"',
            "origen: ADHERENCIA › MES A MES",
            lambda r, ref: escala_adherencia(ws, r))
    tarjeta(F1, 7, "2 · % CARGA DE CAPACIDAD",
            "=" + del_mes(r_per(col_carga), r_per("A")), "0.0%",
            '="capacidad PRODUCTIVA = disponible × "&TEXT(p_factor_productividad,"0%")&'
            '"  ·  no es el 100 % del tiempo de presencia"',
            "origen: PERFIL_HH › MES A MES",
            lambda r, ref: semaforo_carga(ws, r))
    tarjeta(F1, 13, "3 · SEMANAS DE BACKLOG",
            "=" + del_mes(r_bkl("F"), r_bkl("A")), "0.0",
            "HH pendientes al corte ÷ capacidad productiva de una semana",
            "origen: BACKLOG › AL CORTE (el detalle por tramos, en la hoja)",
            lambda r, ref: sem_num(r, ref, [("{c}<4", FILL_VERDE),
                                            ("AND({c}>=4,{c}<=8)", FILL_AMAR),
                                            ("{c}>8", FILL_ROJO)]))

    # KPI 4 — ejecución OPEX acumulada (enero → mes elegido). Acumula las celdas
    # mensuales que YA calcula PRESUPUESTO; no vuelve a sumar costos de órdenes.
    ARR12D = "{1,2,3,4,5,6,7,8,9,10,11,12}"
    mes_num = f"VALUE(RIGHT({SEL},2))"

    def acum(fila):
        return f"SUMPRODUCT(({ARR12D}<={mes_num})*(PRESUPUESTO!$C${fila}:$N${fila}))"

    tarjeta(F2, 1, "4 · EJECUCIÓN OPEX (acumulada)",
            f'=IF(VALUE(LEFT({SEL},4))<>p_anio_presupuesto,"",'
            f'IF({acum(ANC["ppto_ppto_general"])}=0,"",'
            f'{acum(ANC["ppto_real_general"])}/{acum(ANC["ppto_ppto_general"])}))', "0.0%",
            '="real ÷ presupuesto, enero → mes elegido  ·  tolerancia "&'
            'TEXT(p_tolerancia_desviacion_presupuesto,"0%")',
            "origen: PRESUPUESTO › filas TOTAL GENERAL",
            lambda r, ref: sem_num(r, ref, [
                ("ABS({c}-1)<=p_tolerancia_desviacion_presupuesto", FILL_VERDE),
                ("{c}>1+p_tolerancia_desviacion_presupuesto", FILL_ROJO),
                ("{c}<1-p_tolerancia_desviacion_presupuesto", FILL_AMAR)]))

    # KPI 5 — MIX. Criterio elegido, por legibilidad: el DESVÍO MÁXIMO en puntos
    # porcentuales entre el mix real del mes y su meta, y la clase que lo causa.
    # Un solo número dice "cuán lejos estoy del mix objetivo" y, al lado, de qué
    # clase se trata; un % de "cumplimiento compuesto" escondería la causa.
    FG_C = 68                                  # bloque de datos del gráfico C
    rng_pp = f"$E${FG_C + 1}:$E${FG_C + len(CLASES_MANTENIMIENTO) + 1}"
    rng_cl = f"$A${FG_C + 1}:$A${FG_C + len(CLASES_MANTENIMIENTO) + 1}"
    tarjeta(F2, 7, "5 · MIX DE MANTENIMIENTO",
            f'=IF(COUNT({rng_pp})=0,"",MAX({rng_pp}))', '0.0" pp"',
            f'=IF(COUNT({rng_pp})=0,"",'
            f'"desvío máximo vs meta · clase: "&INDEX({rng_cl},MATCH(MAX({rng_pp}),{rng_pp},0)))',
            "origen: ADHERENCIA › MES A MES (conteo por clase) vs metas de PARAMETROS",
            lambda r, ref: sem_num(r, ref, [("{c}<=5", FILL_VERDE),
                                            ("AND({c}>5,{c}<=10)", FILL_AMAR),
                                            ("{c}>10", FILL_ROJO)]))

    # KPI 6 — cumplimiento legal. Es normativo: si queda alguna orden legal
    # vencida al corte, la tarjeta va en ROJO aunque el porcentaje sea alto.
    celda(ws, F2 + 5, 7, "=" + del_mes(r_adh("J"), r_adh("A")), font=F_NOTA)
    ws.cell(row=F2 + 5, column=7).number_format = "0"
    celda(ws, F2 + 5, 8, "← órdenes legales vencidas al corte (celda de apoyo del semáforo)",
          font=F_NOTA)
    ref_venc = f"$G${F2 + 5}"
    tarjeta(F2, 13, "6 · CUMPLIMIENTO LEGAL / CALIBRACIONES",
            "=" + del_mes(r_adh("I"), r_adh("A")), "0.0%",
            f'="legales cerradas ÷ programadas del mes  ·  vencidas: "&{ref_venc}',
            "origen: ADHERENCIA › MES A MES (clase legal)",
            lambda r, ref: [
                ws.conditional_formatting.add(r, FormulaRule(
                    formula=[f"AND(ISNUMBER({ref_venc}),{ref_venc}>0)"], fill=FILL_ROJO)),
                ws.conditional_formatting.add(r, FormulaRule(
                    formula=[f"AND(ISNUMBER({ref}),{ref}>=1)"], fill=FILL_VERDE)),
                ws.conditional_formatting.add(r, FormulaRule(
                    formula=[f"AND(ISNUMBER({ref}),{ref}<1)"], fill=FILL_AMAR))])

    # ---- bloques de datos de los gráficos --------------------------------
    # Viven en la propia hoja, debajo y a la vista (no ocultos): son la fuente
    # de los cuatro gráficos y hacen auditable de dónde sale cada barra. Todos
    # LEEN de las hojas fuente; ninguno vuelve a agregar órdenes.
    celda(ws, 51, 1, "BLOQUES DE DATOS DE LOS GRÁFICOS — se leen de las hojas fuente y responden "
                     "al mes seleccionado. No editar.", font=F_SEC)

    # A) cumplimiento semanal del mes: hasta 6 semanas ISO cuyo lunes cae en el
    #    mes. La adherencia de cada semana se LEE del bloque semanal de
    #    ADHERENCIA (columna D), no se recalcula.
    FG_A = 53
    celda(ws, FG_A - 1, 1, "A · cumplimiento semanal del mes elegido", font=F_NOTA)
    encabezados(ws, FG_A, ["semana", "adherencia", "meta"])
    ini_mes_sel = _mes_ini(SEL)
    fin_mes_sel = _mes_fin(SEL)
    # El bloque semanal de ADHERENCIA arranca en la fila 5 (título 3, cabecera 4).
    adh_sem_val = f"ADHERENCIA!$D$5:$D${4 + CAP_SEM}"
    adh_sem_lbl = f"ADHERENCIA!$A$5:$A${4 + CAP_SEM}"
    for k in range(6):
        fr = FG_A + 1 + k
        lun = f"({ini_mes_sel}-WEEKDAY({ini_mes_sel},2)+1+{7 * k})"
        celda(ws, fr, 1, f'=IF({lun}>{fin_mes_sel},"",'
                         f'YEAR({lun}+4-WEEKDAY({lun},2))&"-S"&'
                         f'TEXT(_xlfn.ISOWEEKNUM({lun}),"00"))')
        celda(ws, fr, 2, f'=IF($A{fr}="","",IFERROR(INDEX({adh_sem_val},'
                         f'MATCH($A{fr},{adh_sem_lbl},0)),""))', fmt=FMT_PCT)
        celda(ws, fr, 3, f'=IF($A{fr}="","",p_meta_adherencia)', fmt=FMT_PCT)

    # B) carga vs capacidad productiva por especialidad (nunca por técnico).
    FG_B = 61
    celda(ws, FG_B - 1, 1, "B · carga vs capacidad productiva por especialidad "
                           "(agregado; el detalle individual vive en SEGUIMIENTO_HH)",
          font=F_NOTA)
    encabezados(ws, FG_B, ["especialidad", "planificada", "capacidad productiva"])
    for j, e_ in enumerate(ESPECIALIDADES_PROPIAS):
        fr = FG_B + 1 + j
        celda(ws, fr, 1, e_)
        celda(ws, fr, 2, "=" + del_mes(r_per(get_column_letter(4 + 2 * j)), r_per("A")),
              fmt=FMT_HH)
        celda(ws, fr, 3, "=" + del_mes(r_per(get_column_letter(5 + 2 * j)), r_per("A")),
              fmt=FMT_HH)

    # C) mix real vs meta por clase. El % real sale de los conteos por clase del
    #    bloque MES A MES de ADHERENCIA; la meta, de PARAMETROS.
    celda(ws, FG_C - 1, 1, "C · mix de mantenimiento: real vs meta (en % de las órdenes del mes)",
          font=F_NOTA)
    encabezados(ws, FG_C, ["clase", "real %", "meta %", "órdenes", "desvío |pp|"])
    metas_clase = {"predictivo": "p_meta_pct_predictivo", "preventivo": "p_meta_pct_preventivo",
                   "correctivo_programado": "p_meta_pct_correctivo_programado",
                   "emergencia": "p_meta_pct_emergencia", "legal": "p_meta_pct_legal"}
    tot_mix = del_mes(r_adh(get_column_letter(col_mix0 + len(CLASES_MANTENIMIENTO) + 1)),
                      r_adh("A"))
    for j, cl in enumerate(CLASES_MANTENIMIENTO + [SIN_CLASIFICAR_CLASE]):
        fr = FG_C + 1 + j
        celda(ws, fr, 1, cl)
        celda(ws, fr, 4, "=" + del_mes(r_adh(get_column_letter(col_mix0 + j)), r_adh("A")))
        celda(ws, fr, 2, f'=IF(N({tot_mix})=0,"",$D{fr}/{tot_mix})', fmt=FMT_PCT)
        # SIN CLASIFICAR no tiene meta: su objetivo es 0 (no debería haber nada).
        celda(ws, fr, 3, f"={metas_clase[cl]}/100" if cl in metas_clase else "=0", fmt=FMT_PCT)
        celda(ws, fr, 5, f'=IF($B{fr}="","",ABS($B{fr}-$C{fr})*100)', fmt="0.0")
    fmix = FG_C + 1 + len(CLASES_MANTENIMIENTO) + 1
    celda(ws, fmix, 1, "TOTAL (control)", font=F_SEC)
    celda(ws, fmix, 2, f'=IF(N({tot_mix})=0,"",SUM($B${FG_C + 1}:$B${fmix - 1}))', fmt=FMT_PCT)
    celda(ws, fmix, 4, f'=SUM($D${FG_C + 1}:$D${fmix - 1})')
    celda(ws, fmix + 1, 1, "DIFERENCIA vs órdenes del mes (debe ser 0)", font=F_NOTA)
    celda(ws, fmix + 1, 4, f'=$D{fmix}-N({tot_mix})')
    ws.conditional_formatting.add(f"D{fmix + 1}", CellIsRule(
        operator="notEqual", formula=["0"], fill=FILL_ROJO))
    celda(ws, fmix + 2, 1,
          f"=PARAMETROS!$B${FILA_PARAM['cuadre_metas_mix']}", font=F_NOTA)

    # D) OPEX plan vs real por mes, separando fijo y variable. Lee las filas de
    #    subtotales de PRESUPUESTO; los meses posteriores al elegido se dejan en
    #    blanco, así el gráfico acompaña al selector.
    FG_D = 80
    celda(ws, FG_D - 1, 1, "D · OPEX plan vs real por mes (fijo y variable) — hasta el mes elegido",
          font=F_NOTA)
    encabezados(ws, FG_D, ["mes", "plan fijo", "plan variable", "real fijo", "real variable"])
    MESES_AB_D = ["ene", "feb", "mar", "abr", "may", "jun",
                  "jul", "ago", "sep", "oct", "nov", "dic"]
    for m in range(1, 13):
        fr = FG_D + m
        cl_m = get_column_letter(2 + m)          # C..N en PRESUPUESTO
        celda(ws, fr, 1, MESES_AB_D[m - 1])
        for j, clave in enumerate(("ppto_ppto_fijo", "ppto_ppto_variable",
                                   "ppto_real_fijo", "ppto_real_variable")):
            celda(ws, fr, 2 + j,
                  f'=IF({m}>{mes_num},"",PRESUPUESTO!${cl_m}${ANC[clave]})', fmt=FMT_DINERO)

    # ---- 4 gráficos ------------------------------------------------------
    # Ninguno lleva máximo de eje fijo (autoescala al cambiar de mes) y los dos
    # ejes van visibles con su escala.
    def ejes(ch, tit_x, tit_y, minimo=0):
        ch.y_axis.scaling.min = minimo
        ch.y_axis.delete = False
        ch.x_axis.delete = False
        ch.x_axis.axPos = "b"
        ch.x_axis.title = tit_x
        ch.y_axis.title = tit_y
        ch.y_axis.majorTickMark = "out"
        ch.x_axis.majorTickMark = "out"
        ch.legend.position = "b"

    gA = BarChart()
    gA.type, gA.gapWidth = "col", 60
    gA.title = "A · Cumplimiento semanal del mes vs meta"
    gA.height, gA.width = 8, 15
    gA.add_data(Reference(ws, min_col=2, min_row=FG_A, max_row=FG_A + 6), titles_from_data=True)
    cats_a = Reference(ws, min_col=1, min_row=FG_A + 1, max_row=FG_A + 6)
    gA.set_categories(cats_a)
    gA.series[0].graphicalProperties.solidFill = "4472C4"
    gA.series[0].dLbls = DataLabelList(showVal=True)
    metaA = LineChart()
    metaA.add_data(Reference(ws, min_col=3, min_row=FG_A, max_row=FG_A + 6), titles_from_data=True)
    metaA.set_categories(cats_a)
    sA = metaA.series[0]
    sA.graphicalProperties.line.solidFill = "C00000"
    sA.graphicalProperties.line.width = 25000
    sA.smooth = False
    sA.marker = Marker(symbol="none")
    gA += metaA
    ejes(gA, "Semana ISO", "Adherencia")
    ws.add_chart(gA, "A18")

    gB = BarChart()
    gB.type, gB.gapWidth = "col", 60
    gB.title = "B · Carga vs capacidad productiva por especialidad"
    gB.height, gB.width = 8, 15
    gB.add_data(Reference(ws, min_col=2, max_col=3, min_row=FG_B,
                          max_row=FG_B + len(ESPECIALIDADES_PROPIAS)), titles_from_data=True)
    gB.set_categories(Reference(ws, min_col=1, min_row=FG_B + 1,
                                max_row=FG_B + len(ESPECIALIDADES_PROPIAS)))
    gB.series[0].graphicalProperties.solidFill = "4472C4"
    gB.series[1].graphicalProperties.solidFill = "A9C4E8"
    ejes(gB, "Especialidad", "HH")
    ws.add_chart(gB, "J18")

    gC = BarChart()
    gC.type, gC.gapWidth = "col", 60
    gC.title = "C · Mix de mantenimiento: real vs meta"
    gC.height, gC.width = 8, 15
    gC.add_data(Reference(ws, min_col=2, max_col=3, min_row=FG_C,
                          max_row=FG_C + len(CLASES_MANTENIMIENTO) + 1), titles_from_data=True)
    gC.set_categories(Reference(ws, min_col=1, min_row=FG_C + 1,
                                max_row=FG_C + len(CLASES_MANTENIMIENTO) + 1))
    gC.series[0].graphicalProperties.solidFill = "4472C4"
    gC.series[1].graphicalProperties.solidFill = "ED7D31"
    ejes(gC, "Clase de mantenimiento", "% de las órdenes del mes")
    ws.add_chart(gC, "A34")

    gD = BarChart()
    gD.type, gD.gapWidth = "col", 40
    gD.title = "D · OPEX plan vs real por mes (fijo y variable)"
    gD.height, gD.width = 8, 15
    gD.add_data(Reference(ws, min_col=2, max_col=5, min_row=FG_D, max_row=FG_D + 12),
                titles_from_data=True)
    gD.set_categories(Reference(ws, min_col=1, min_row=FG_D + 1, max_row=FG_D + 12))
    for si, color in enumerate(("1F4E78", "A9C4E8", "C55A11", "F4B183")):
        gD.series[si].graphicalProperties.solidFill = color
    ejes(gD, "Mes", '=p_moneda')
    ws.add_chart(gD, "J34")

    # ---- selector de mes: rango + nombre definido (misma técnica que 7.1) --
    COL_MES = 24                                   # columna X, fuera del tablero
    celda(ws, 2, COL_MES, "meses con datos (validación) — no editar", font=F_NOTA)
    for i, (anio_m, mes_m) in enumerate(esperado["meses"]):
        celda(ws, 3 + i, COL_MES, f"{anio_m}-{mes_m:02d}")
    LM = get_column_letter(COL_MES)
    wb.defined_names.add(DefinedName(
        "lista_meses_dash", attr_text=f"DASHBOARD!${LM}$3:${LM}${2 + NM}"))
    ws.column_dimensions[LM].hidden = True
    dvm = DataValidation(type="list", formula1="lista_meses_dash", allow_blank=False,
                         showErrorMessage=False)
    ws.add_data_validation(dvm)
    dvm.add("B3")

    for colw, w in ([("A", 22), ("B", 12), ("C", 12)]
                    + [(get_column_letter(c), 11) for c in range(4, 19)]):
        ws.column_dimensions[colw].width = w
    ws.row_dimensions[1].height = 24
    ws.sheet_view.showGridLines = False

    # ------------------------------------------------- ORDEN DE LAS HOJAS
    # 7.1: el libro se ordena por USO, no por historia. (A) lo que se muestra,
    # (B) el trabajo diario, (C) configuración, catálogos y guías al final.
    # El DASHBOARD ocupa el puesto #1 y es la hoja activa al abrir.
    # Reordenar no cambia fórmulas (referencian por nombre), pero se verifica.
    ORDEN_HOJAS = [
        # A. PRESENTACIÓN
        "DASHBOARD", "PLAN_SEMANAL", "ADHERENCIA", "PERFIL_HH", "BACKLOG", "COSTOS", "PRESUPUESTO",
        "EQUIPOS_CRITICOS", "SEGUIMIENTO_HH", "SEGUIMIENTO_MENSUAL", "EXPORTAR",
        # B. TRABAJO DIARIO
        "ORDENES", "ASIGNACIONES", "AJUSTES", "PLAN_VACACIONES",
        "2_IMPORTAR_EJECUCION", "TECNICOS", "CALENDARIO", "VALIDACION",
        # C. CONFIGURACIÓN, CATÁLOGOS Y GUÍAS
        "PARAMETROS", "CAT_CENTROS_COSTO", "CAT_PUESTOS", "CAT_ACTIVIDADES",
        "CAT_TIPOS_OT", "CAT_ESTADOS_ERP", "CAT_TURNOS", "CAT_SUPERVISORES",
        "CAT_MOTIVOS_AUSENCIA", "INICIO",
        "GUIA_IMPORTAR_ORDENES", "_COMPATIBILIDAD", "_BANCO_PRUEBA",
    ]
    pos = {n: i for i, n in enumerate(ORDEN_HOJAS)}
    # Cualquier hoja no listada queda al final, en su orden actual (nunca se pierde).
    wb._sheets.sort(key=lambda h: (pos.get(h.title, len(ORDEN_HOJAS)),))
    wb.active = 0

    # HIGIENE: las hojas que se consultan una vez al año se ocultan. `hidden`
    # (no `veryHidden`): el usuario las recupera con clic derecho en cualquier
    # pestaña → Mostrar. PARAMETROS queda VISIBLE porque se ajusta a menudo.
    OCULTAS = ([h for h in wb.sheetnames if h.startswith("CAT_")]
               + ["GUIA_IMPORTAR_ORDENES", "INICIO", "_COMPATIBILIDAD", "_BANCO_PRUEBA"])
    for nombre in OCULTAS:
        if nombre in wb.sheetnames:
            wb[nombre].sheet_state = "hidden"

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

    man = datos.get("manifiesto")
    if man:
        print("\n§7 BANCO DE PRUEBA — manifiesto de siembra:")
        for k, v in man.items():
            print(f"  {k:38} {v}")
        # Coherencia de la ventana programada (contraste independiente)
        v_ini = datos["lunes_sem"][0]
        v_fin = datos["lunes_sem"][-1] + timedelta(days=6)
        asig = {(a["tecnico"], a["fecha"]): a for a in esperado["asignaciones"]}
        prog = [o for o in esperado["ordenes"] if o["tecnico_asignado"]
                and o["fecha_inicio"] and v_ini <= o["fecha_inicio"] <= v_fin]
        mal_esp = [o for o in prog
                   if CAT_PUESTOS.get(o["puesto_trabajo"])
                   != next((t[TEC_ESP] for t in TECNICOS if t[1] == o["tecnico_asignado"]), None)]
        mal_disp = [o for o in prog
                    if (asig.get((o["tecnico_asignado"], o["fecha_inicio"])) or {}
                        ).get("horas_disponibles", 0) <= 0]
        carga = {}
        for o in prog:
            k = (o["tecnico_asignado"], o["fecha_inicio"])
            carga[k] = carga.get(k, 0) + (o["horas_efectivas"] or 0)
        cap = HORAS_JORNADA * FACTOR_PRODUCTIVIDAD
        mal_cap = {k: h for k, h in carga.items() if h > cap + 1e-9}
        print("  COHERENCIA DE LA VENTANA PROGRAMADA:")
        print(f"    órdenes con técnico: {len(prog)} · remanente sin técnico: "
              f"{man['ventana_remanente_sin_tecnico']}")
        print(f"    especialidad equivocada: {len(mal_esp)} (esperado 0)")
        print(f"    técnico en VAC/domingo/no hábil: {len(mal_disp)} (esperado 0)")
        print(f"    técnico-día sobre capacidad ({cap:.2f} h): {len(mal_cap)} (esperado 0)")

    print("\nROTACIÓN DE TURNOS (6.3, anillo B(N-3)…B1 → T3 → T2 → T1; +1 pos/semana):")
    print(f"  Semana de referencia (lunes): {datos['semana_referencia'].isoformat()}")
    pos_lunes = {}
    for a in datos["asignaciones"]:
        if a["dia"] == "lunes":
            pos_lunes[(a["especialidad"], a["area"], a["semana"])] = \
                pos_lunes.get((a["especialidad"], a["area"], a["semana"]), [])
            pos_lunes[(a["especialidad"], a["area"], a["semana"])].append(
                (a["tecnico"], a["posicion_ciclo"], a["turno"]))
    for (esp, area), n in datos["n_por_ciclo"].items():
        print(f"  Ciclo {esp} · {area} (N={n}) — posicion_ciclo por técnico y semana (lunes):")
        techs = sorted([t for t in TECNICOS_ACTIVOS if t[TEC_ESP] == esp
                        and t[TEC_AREA] == area and t[TEC_ROT] == SI],
                       key=lambda x: x[TEC_ORDROT])
        print("    " + "técnico(orden)".ljust(23) + "".join(s.rjust(10) for s in datos["semanas"]))
        for t in techs:
            fila = "".join(
                next(p for (nb, p, _tu) in pos_lunes[(esp, area, sem)] if nb == t[1]).rjust(10)
                for sem in datos["semanas"])
            print("    " + f"{t[1][:18]} (o{t[TEC_ORDROT]})".ljust(23) + fila)
        for sem in datos["semanas"]:
            # Cobertura por POSICIÓN derivada (rotación 6.3, intacta): siempre
            # 1/1/1/(N-3). Los huecos VAC (6.4) se listan aparte: el turno efectivo
            # de esa posición es "VAC", pero la posición sigue asignada al técnico.
            c = {b: 0 for b in ("B", "T1", "T2", "T3")}
            huecos = []
            for (_nb, pos, tu) in pos_lunes[(esp, area, sem)]:
                c[banda_de(pos)] += 1
                if tu == "VAC":
                    huecos.append(banda_de(pos))
            ok = c["T1"] == 1 and c["T2"] == 1 and c["T3"] == 1 and c["B"] == n - 3
            hueco_txt = f" · huecos VAC en: {', '.join(huecos)}" if huecos else ""
            print(f"      cobertura {sem} (por posición): B={c['B']} T1={c['T1']} "
                  f"T2={c['T2']} T3={c['T3']}  {'OK' if ok else 'FALLO'}{hueco_txt}")

    print("\nVACACIONES QUE ARRASTRAN (6.4, PLAN_VACACIONES → VAC automático):")
    for v in datos["plan_vacaciones"]:
        print(f"  {v['tecnico']}: {v['fecha_inicio']} … {v['fecha_fin']} ({v['motivo']})")
    tec_vac = datos["plan_vacaciones"][0]["tecnico"]
    print(f"  {tec_vac} — turno efectivo por semana (lunes) [posición derivada se conserva]:")
    for sem in datos["semanas"]:
        a = next(a for a in datos["asignaciones"] if a["tecnico"] == tec_vac
                 and a["semana"] == sem and a["dia"] == "lunes")
        disp = a["horas_disponibles"]
        print(f"    {sem}: posición {a['posicion_ciclo']:>2} · en_vacaciones={a['en_vacaciones']:>2} "
              f"· turno={a['turno']:>4} · {disp} h")
    cap_vac = FACTOR_PRODUCTIVIDAD * sum(
        a["horas_disponibles"] for a in datos["asignaciones"]
        if a["tecnico"] == tec_vac and a["semana"] == datos["semanas"][1])
    print(f"  Capacidad de {tec_vac} en {datos['semanas'][1]} (semana de VAC completa): "
          f"{cap_vac:.2f} h (0 h)")

    print("\nSEGUIMIENTO DE HORAS REALES (6.5, capa de cumplimiento; NO cambia PERFIL_HH):")
    print("  horas_reales por técnico × semana (56 turno / 48 banco / 0 VAC; feriado resta):")
    print("    " + "técnico".ljust(12) + "".join(s.rjust(11) for s in datos["semanas"]))
    seg = {(s["tecnico"], s["semana"]): s for s in esperado["seguimiento_hh"]}
    for _tid, nombre, *_ in TECNICOS_ACTIVOS:
        fila = "".join(f"{seg[(nombre, sem)]['posicion'] or '-':>3}:{seg[(nombre, sem)]['horas_reales']:>2.0f}h"
                       .rjust(11) for sem in datos["semanas"])
        print("    " + nombre[:11].ljust(12) + fila)
    print("  superavit_deficit (=reales−48): +8 turno · 0 banco · −48 VAC · −8 banco en feriado")
    print("  Déficit de capacidad por VAC (esp × semana, técnicos_vac × 48 h):")
    for (e, sem), d in esperado["deficit_vac"].items():
        if d:
            print(f"    {e} {sem}: {d:.0f} h ({d // 48:.0f} técnico(s) en VAC)")
    print("\nSEGUIMIENTO MENSUAL (6.5, base del bono; tolerancia p_tolerancia_horas_bono=0):")
    print("    " + "técnico".ljust(18) + "mes".ljust(9) + "reales".rjust(7)
          + "requer.".rjust(8) + "brecha".rjust(8) + "  cumple")
    for s in esperado["seguimiento_mensual"]:
        print("    " + s["tecnico"][:17].ljust(18) + s["mes"].ljust(9)
              + f"{s['horas_reales_mes']:>7.0f}{s['horas_requeridas_mes']:>8.0f}"
              + f"{s['brecha']:>+8.0f}  {s['cumple']}")

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
        if o["fecha_inicio"] and o["fecha_inicio"].month in (12, 1) and o["_grupo"] in ("futuro", "cruce"):
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
    for _tid, nombre, esp_t, *_ in TECNICOS_ACTIVOS:
        c = esperado["carga_tecnicos"][(sem1, nombre)]
        cap = esperado["capacidad_tecnicos"][(sem1, nombre)]
        print(f"  {nombre} ({esp_t}): HHA {c:>5.1f} · capacidad {cap:>6.2f} · "
              f"dentro {min(c, cap):>6.2f} · sobre {max(0, c - cap):>5.2f}")
    print(f"\nHHA/HHD por día — {_tec('MEC', 1)}, semana {sem1} "
          f"(disponibilidad normal = {HORAS_JORNADA} h × {FACTOR_PRODUCTIVIDAD} = "
          f"{HORAS_JORNADA * FACTOR_PRODUCTIVIDAD:.2f} h):")
    for dia in DIAS[:6]:
        ords = [o for o in esperado["ordenes"] if o["tecnico_asignado"] == _tec("MEC", 1)
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
    print("\nCALENDARIO LABORAL (v2.4):")
    exc = datos["excepciones"]
    print(f"  Excepciones: {len(exc)} (12 feriados generales + demos). Patrón: L-V hábil, S-D no.")
    casos_cal = [] if datos.get("banco") else [(date(hoy.year, 5, 1), "PRODUCCION", "", "no"),
                         (datos["lunes_sem"][2] + timedelta(days=6), "SERVICIOS", "", "sí"),
                         (datos["lunes_sem"][2] + timedelta(days=6), "PRODUCCION", "", "no"),
                         (datos["lunes_sem"][1] + timedelta(days=3), "SERVICIOS", "Vapor", "no"),
                         (datos["lunes_sem"][1] + timedelta(days=3), "SERVICIOS", "Refrigeración", "sí")]
    for f, a, s, exp in casos_cal:
        r = es_habil(f, a, s, exc)
        print(f"  es_habil({f}, {a}, {s or '—'}) = {r}  (esperado {exp})  "
              f"{'OK' if r == exp else 'FALLO'}")
    ve = esperado["validacion_extra"]
    print(f"  VALIDACION → en día no laborable: {ve['en_dia_no_habil']} · "
          f"área desconocida: {ve['exc_area_desconocida']} · sub desconocida: {ve['exc_sub_desconocida']}")
    print("  Capacidad PERFIL_HH (hh_disponible) por semana del plan:")
    for sem in datos["semanas"]:
        p = esperado["perfil"][("MEC", sem)]
        print(f"    MEC {sem}: disp {p['hh_disponible']:.0f} · %carga "
              f"{p['pct_carga']:.1%}" if p['pct_carga'] else f"    MEC {sem}: disp {p['hh_disponible']:.0f}")
    print("  Orden que cruza fin de semana (backlog_dias vs backlog_habiles):")
    for o in esperado["ordenes"]:
        if o["_grupo"] == "backlog" and o["backlog_dias"] != "" and \
                o["backlog_dias"] - abs(o["backlog_habiles"]) >= 4:
            print(f"    {o['id_operacion']}: fecha {o['fecha_inicio']} · dias {o['backlog_dias']} · "
                  f"hábiles {o['backlog_habiles']} · diferencia {o['backlog_dias'] - o['backlog_habiles']} no hábiles")
            break

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
    # §7 — banco de prueba (OPCIÓN; sin estos flags sale el dataset de 4 semanas)
    ap.add_argument("--anio-completo", action="store_true",
                    help="§7: banco de prueba de un año (ancla fija 2026) con ventana programada")
    ap.add_argument("--n-ordenes", type=int, default=1000,
                    help="§7: nº de órdenes del banco (default 1000)")
    ap.add_argument("--semanas-programadas", type=int, default=4,
                    help="§7: semanas de la ventana realmente programada (default 4)")
    ap.add_argument("--semilla", type=int, default=SEMILLA_BANCO,
                    help=f"§7: semilla determinista del banco (default {SEMILLA_BANCO})")
    args = ap.parse_args(argv)

    t0 = time.perf_counter()
    if args.anio_completo:
        datos = generar_datos_banco(args.n_ordenes, args.semanas_programadas, args.semilla)
        hoy = datos["hoy"]
    else:
        hoy = date.fromisoformat(args.fecha_ancla) if args.fecha_ancla else date.today()
        datos = generar_datos(hoy)
    esperado = calcular_esperado(datos)
    construir_libro(datos, esperado, args.salida, refs=args.refs)
    seg = time.perf_counter() - t0
    modo = "BANCO §7" if args.anio_completo else "default"
    print(f"Generado {args.salida} (refs {args.refs}, ancla {hoy.isoformat()}, "
          f"{modo}, {len(datos['ordenes'])} órdenes, {seg:.1f} s)")
    if args.resumen:
        print()
        imprimir_resumen(datos, esperado)


if __name__ == "__main__":
    main()
