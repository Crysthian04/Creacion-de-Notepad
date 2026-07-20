# MantPlan — Entregable A: `MantPlan.xlsx` (v2.0.0)

Planificador semanal de mantenimiento reimplementado limpio: **sin macros, sin
enlaces externos, agnóstico de empresa y de ERP**. Las 10 reglas de negocio
están implementadas dos veces y verificadas una contra la otra:

1. Como **fórmulas** dentro del libro (`XLOOKUP` + referencias estructuradas).
2. Como **funciones puras de Python** en `generar_mantplan.py`
   (`regla_1_clasificacion` … `regla_10_validacion`), que además generan los
   datos sintéticos de ejemplo.

> El entregable B (`mantplan-web/`, con `src/domain/rules.ts`) queda pendiente
> y se hará como paso separado. Los resultados de la verificación de esta
> versión están en [`VERIFICACION.md`](VERIFICACION.md).

## Contenido de esta carpeta

| Archivo | Qué es | Cuándo usarlo |
|---|---|---|
| `MantPlan.xlsx` | Libro principal: `XLOOKUP` + referencias estructuradas | **Excel 2021 / Microsoft 365** |
| `MantPlan_compatible.xlsx` | Mismo libro y mismos datos con `INDEX/MATCH` + rangos A1 acotados | **Excel 2016 o anterior, y LibreOffice** |
| `generar_mantplan.py` | Motor de reglas en Python + generador determinista de ambos libros | — |
| `VERIFICACION.md` | Reporte de verificación de v2.0.0 (recálculo + comparación + casos) | — |
| `README.md` | Este documento | — |

Ambos libros llevan las mismas 200 órdenes sintéticas ancladas al
**2026-07-20**, sobre tablas provisionadas para **1.200 filas**, y producen
números idénticos (verificado, ver §1).

## Cómo regenerarlo

```bash
pip install openpyxl
python generar_mantplan.py                                        # MantPlan.xlsx (principal)
python generar_mantplan.py --salida MantPlan_compatible.xlsx --refs compatibles
python generar_mantplan.py --fecha-ancla 2026-07-20               # fija el "hoy" de los datos
python generar_mantplan.py --resumen                              # imprime los números esperados
```

## Decisiones técnicas

### 1. Verificación: doble implementación + recálculo real

- El generador emite el libro en dos modos desde **las mismas plantillas de
  fórmula** (`class Refs`): `estructuradas` (XLOOKUP, entregable principal) y
  `compatibles` (INDEX/MATCH + rangos A1 acotados).
- La variante compatible se recalculó con LibreOffice: **51.623 fórmulas, 0
  errores**.
- Cada valor recalculado se comparó contra el motor Python: **7.587
  comparaciones automáticas, 0 desviaciones**. Detalle en `VERIFICACION.md`.

### 2. REGLA-2 v2: semana con año ISO, sin pliegue S53→S1

Esta versión **reemplaza la REGLA-2 del enunciado original**:

- `semana` = **`AAAA-Snn`**: año ISO + "-S" + semana ISO a dos dígitos
  (`2026-S28`). El año es el **ISO** (el del jueves de esa semana), no
  `YEAR(fecha)`: difieren exactamente en los días de cruce diciembre/enero.
  En Excel: `YEAR(fecha + 4 − WEEKDAY(fecha, 2)) & "-S" &
  TEXT(ISOWEEKNUM(fecha), "00")`.
- **Se eliminó el pliegue S53 → S1** de la especificación original. Los años
  ISO tienen 52 o 53 semanas; la 53 es legítima (2026 la tiene) y el pliegue
  mezclaba órdenes de fines de diciembre con las de principios de enero — con
  el agravante de que sin año en la clave también se mezclaban semanas
  homónimas de años distintos en PERFIL_HH y ADHERENCIA.
- Bonus del formato: `AAAA-Snn` con semana a dos dígitos **ordena
  cronológicamente incluso como texto**.
- Nota consciente: la columna `anio` sigue siendo `YEAR(fecha_inicio)` (Tabla
  1 del modelo), así que una orden del 2027-01-01 muestra `anio = 2027` y
  `semana = 2026-S53`. Es la distinción correcta: `anio/mes` alimentan los
  reportes mensuales de costos; `semana` es la clave de planificación.

### 3. `horas_ajustadas` / `horas_efectivas`: los ajustes sobreviven a la re-importación

Flujo real: cada mes se pega la exportación del ERP y el planificador ajusta
a mano la duración de algunas tareas.

- **`horas_ajustadas`** (columna M): editable, vacía por defecto, en azul.
- **`horas_efectivas`** (columna N): calculada —
  `IF(horas_ajustadas<>"", horas_ajustadas, IF(horas_estimadas="", "",
  horas_estimadas))`. (El `IF` interno es un refinamiento sobre la fórmula
  pedida: conserva el vacío cuando ambas están vacías en vez de mostrar 0.)
- **Todos los cálculos de horas usan `horas_efectivas`**: HHA, HHD,
  PERFIL_HH (REGLA-6), adherencia por horas (REGLA-7), REGLA-9, gráfico de
  carga, BACKLOG y EXPORTAR. `horas_estimadas` queda solo como referencia del
  estándar del ERP.
- `VALIDACION` reporta cuántas órdenes tienen ajuste manual y la desviación
  total en horas contra el estándar (`Σ efectivas − Σ estimadas` sobre las
  ajustadas).
- **Por qué sobreviven:** la re-importación pega un solo bloque en A:L (§5) y
  la columna M queda fuera del bloque.
- **Limitación honesta:** el ajuste queda anclado a la **fila**, no al
  `id_operacion`. Si el próximo export llega con las filas en otro orden, el
  ajuste quedará sobre otra orden. La solución robusta (tabla de ajustes por
  `id_operacion` que se re-aplica sola) necesita el entregable B o una
  columna de lookup adicional; quedó fuera de este cambio y está señalada en
  `VERIFICACION.md`.

### 4. Hojas de reporte dimensionadas por los datos (capacidad 60 semanas)

- `PERFIL_HH` deriva por fórmula una **serie de semanas** (columnas N/O):
  lunes consecutivos desde `MIN(tblOrdenes[fecha_inicio])` hasta
  `MAX(...)`, con etiqueta REGLA-2. Capacidad: 60 semanas.
- La tabla plana de REGLA-6 (60 semanas × 5 especialidades), la matriz de
  % de carga (transpuesta: semanas en filas), el bloque REGLA-9 y el bloque
  semanal de `ADHERENCIA` (incluidas las categorías de su gráfico) recorren
  la serie completa; **las filas de semanas sin órdenes están ocultas** y el
  gráfico solo traza las visibles.
- El ocultamiento se decide **al generar el archivo** (Excel sin macros no
  puede ocultar filas por fórmula): tras re-importar con semanas nuevas, esas
  filas calculan solas pero pueden requerir "Mostrar filas" para verse.
- Los **desplegables** de `PLAN_SEMANAL` y `EXPORTAR` mantienen la ventana
  operativa de 4 semanas del plan (más "(todos)"), que es donde la ventana
  corta tiene sentido.

### 5. Pegado en un solo bloque y capacidad mensual (1.200 filas)

- Las 12 columnas importadas de `tblOrdenes` quedan **contiguas en A:L** e
  **`id_operacion` pasó al final** (columna AO) — desviación deliberada del
  orden de la Tabla 1, al servicio del pegado en un paso. En `tblEjecucion`,
  `id_operacion` también va al final por la misma razón.
- `1_IMPORTAR_ORDENES` documenta el paso único: ordenar el export con esas 12
  cabeceras y pegarlo en `ORDENES!A4`. `2_IMPORTAR_EJECUCION` ya era la
  propia tabla.
- `tblOrdenes` y `tblEjecucion` están provisionadas a **1.200 filas** con
  todas las columnas calculadas ya escritas y **blindadas**: una fila sin
  `orden` produce vacío en todas las calculadas (nada de ids `"0010"`
  fantasma) y los chequeos de `VALIDACION` ignoran las filas vacías.
- El área de impresión de `PLAN_SEMANAL` cubre las filas con datos de
  ejemplo; tras una importación mayor hay que reajustarla (no puede ser
  dinámica sin `OFFSET`, que está prohibido).

### 6. `XLOOKUP` y compatibilidad

Los lookups usan `XLOOKUP` con `si_no_encontrado` (almacenado `_xlfn.XLOOKUP`,
forma canónica OOXML). **Requiere Excel 2021/365**; para Excel 2016 o anterior
y LibreOffice < 24.8 está `MantPlan_compatible.xlsx` (cero `XLOOKUP`, solo
`INDEX/MATCH` + rangos A1). La hoja `_COMPATIBILIDAD` documenta los
equivalentes con ejemplos vivos.

### 7. Cálculo automático y caché

`fullCalcOnLoad` activado: Excel recalcula al abrir. openpyxl no escribe caché
de resultados, así que visores sin motor de cálculo muestran vacías las
celdas calculadas hasta abrir el archivo en Excel/LibreOffice.

### 8. Sustitutos sin macros

| Requisito original | Implementación |
|---|---|
| Tabla dinámica en ADHERENCIA | Matrices `COUNTIFS`/`SUMIFS` + gráfico contra meta |
| Segmentaciones (slicers) | Autofiltro por tabla + selectores desplegables "(todos)" en PLAN_SEMANAL/EXPORTAR |
| PivotChart de carga | Zona de datos `SUMIFS` (P3:V15 de PLAN_SEMANAL) conectada a los mismos selectores; barras apiladas verde/rojo + línea de capacidad (REGLA-5 × factor) en el mismo eje, con marcador |
| Impresión por turno/coordinador | Área de impresión + vista filtrable |
| Correo Outlook | Hoja `EXPORTAR` con `TEXTJOIN` |
| Checklists | `HYPERLINK(ruta_base & link_checklist)` |

### 9. HHA / HHD

- `HHA` = `SUMIFS(horas_efectivas; tecnico; semana; dia)` — total del técnico
  ese día, repetido en sus filas.
- `HHD` = `factor_productividad × horas_disponibles − HHA`, con
  `horas_disponibles` buscada en `tblAsignaciones` (REGLA-5): con turno
  normal la capacidad diaria es 7 × 0,87 = **6,09 h**; con `VAC`/`X` es 0 y
  **HHD = −HHA**. HHD < 0 en rojo = sobreasignación.

### 10. Higiene de fórmulas

Auditado sobre los archivos finales: sin `OFFSET`, sin `INDIRECT`, sin
columnas completas (`A:A`), sin enlaces externos, sin VBA, sin nombres
definidos huérfanos.

## Datos de ejemplo y verificación a mano (ancla 2026-07-20)

200 órdenes (tablas con capacidad 1.200) · 163 filas de ejecución (3
huérfanas) · 12 técnicos · 336 asignaciones · semanas del plan
**2026-S29 … 2026-S32** · serie completa de reportes: 2026-S08 … 2027-S01.

### Caso 1 — cruce de fin de año (REGLA-2 v2)

| orden | fecha | semana | anio (YEAR) |
|---|---|---|---|
| OT-000182 | 2026-12-29 | **2026-S53** | 2026 |
| OT-000183 | 2027-01-01 | **2026-S53** | **2027** ← año ISO ≠ YEAR |
| OT-000184 | 2027-01-05 | **2027-S01** | 2027 |

`2026-S53` y `2027-S01` aparecen como semanas distintas en la serie de
PERFIL_HH/ADHERENCIA (las dos últimas filas visibles), sin mezcla.

### Caso 2 — ajuste manual de horas (`horas_efectivas`)

- **OT-000017** (MEC, preventiva, Técnico 01, martes 2026-S30):
  `horas_estimadas` 8, `horas_ajustadas` **12** → `horas_efectivas` 12.
  - PERFIL_HH MEC 2026-S30: prev **84** (80 + 4), planificada 109, carga
    **89,5 %** (con 8 h sería 86,2 %).
  - Gráfico de carga (selector 2026-S30): barra de Técnico 01 = **35** =
    6+12+10+7 (30,45 verde + **4,55 rojo**).
  - HHA del martes = **12**, HHD = 6,09 − 12 = **−5,91** (rojo).
- **OT-000061** (ELE, preventiva, Técnico 05): 6 → **4** → ELE 2026-S30 prev
  63, carga 97,3 %.
- `VALIDACION`: **2** órdenes con ajuste manual, desviación total **+2 h**.

### PERFIL_HH esperado (REGLA-6, semanas del plan)

Cuenta rápida: **MEC 2026-S29 = 4 técnicos × 5 días × 7 h = 140; × 0,87 =
121,8; 82 prev + 20 corr = 102; carga 83,7 % → verde.**

| esp | semana | disp | prod | prev | corr | plan | holgura | % carga |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| MEC | 2026-S29 | 140 | 121,80 | 82 | 20 | 102 | 19,80 | 83,7 % 🟢 |
| MEC | 2026-S30 | 140 | 121,80 | 84 | 25 | 109 | 12,80 | 89,5 % 🟡 |
| MEC | 2026-S31 | 105 | 91,35 | 80 | 20 | 100 | −8,65 | **109,5 % 🔴** |
| MEC | 2026-S32 | 140 | 121,80 | 72 | 14 | 86 | 35,80 | 70,6 % 🟢 |
| ELE | 2026-S29 | 105 | 91,35 | 60 | 15 | 75 | 16,35 | 82,1 % 🟢 |
| ELE | 2026-S30 | 98 | 85,26 | 63 | 20 | 83 | 2,26 | 97,3 % 🟡 |
| ELE | 2026-S31 | 105 | 91,35 | 60 | 10 | 70 | 21,35 | 76,6 % 🟢 |
| ELE | 2026-S32 | 105 | 91,35 | 52 | 10 | 62 | 29,35 | 67,9 % 🟢 |
| AUT | 2026-S29 | 70 | 60,90 | 40 | 10 | 50 | 10,90 | 82,1 % 🟢 |
| AUT | 2026-S30 | 70 | 60,90 | 45 | 10 | 55 | 5,90 | 90,3 % 🟡 |
| AUT | 2026-S31 | 70 | 60,90 | 35 | 7 | 42 | 18,90 | 69,0 % 🟢 |
| AUT | 2026-S32 | 70 | 60,90 | 30 | 6 | 36 | 24,90 | 59,1 % 🟢 |
| OP | 2026-S29 | 105 | 91,35 | 30 | 8 | 38 | 53,35 | 41,6 % 🟢 |
| OP | 2026-S30 | 105 | 91,35 | 36 | 9 | 45 | 46,35 | 49,3 % 🟢 |
| OP | 2026-S31 | 105 | 91,35 | 28 | 9 | 37 | 54,35 | 40,5 % 🟢 |
| OP | 2026-S32 | 105 | 91,35 | 24 | 6 | 30 | 61,35 | 32,8 % 🟢 |
| TERCERO | 2026-S30 | 0 | 0 | 16 | 0 | 16 | −16,00 | — |
| TERCERO | 2026-S31 | 0 | 0 | 12 | 0 | 12 | −12,00 | — |

Casos preparados: TEC-04 de vacaciones toda 2026-S31 (MEC 105 h → 109,5 %
rojo) · TEC-07 ausente el viernes de 2026-S30 (`X`, ELE 98 h) · TERCERO sin
capacidad interna (% carga vacío, denominador protegido).

### ADHERENCIA esperada (REGLA-7, sobre horas efectivas)

2026-S29: 30/34 = 88,2 % (HH 229/265 = 86,4 %) · 2026-S30: 19/37 = 51,4 %
(HH 163/308 = 52,9 %) · 2026-S31 y S32: 0 %.

### REGLA-9 esperada (meta: correctivo ≤ 20 %)

2026-S29: 0,25 (20,0 % → SI) · 2026-S30: 0,26 (20,8 % → NO) · 2026-S31: 0,21
(17,6 % → SI) · 2026-S32: 0,20 (16,8 % → SI).

### BACKLOG esperado (pendientes por tramo, al 2026-07-20)

0–30: 9 órdenes / 75 h · 31–60: 19 / 76 h · 61–90: 9 / 48 h · **>90: 14 /
80 h** (rojo). El tramo 0–30 depende del día de apertura (`HOY()`).

### VALIDACION esperada

| chequeo | resultado |
|---|---:|
| Duplicadas por `id_operacion` (OT-000900) | 2 |
| Sin fecha de inicio | 2 |
| Sin horas estimadas | 2 |
| Centro de costo fuera de catálogo | 1 |
| Puesto fuera de catálogo | 1 |
| Actividad fuera de catálogo | 1 |
| Tipo de OT fuera de catálogo (`sin_clasificar`) | 2 |
| EJECUCION sin par en ORDENES | 3 |
| ORDENES sin par en EJECUCION (quedan `Pendiente`) | 41 |
| **Órdenes con ajuste manual de horas** | **2** |
| **Desviación total de horas (ajustadas − ERP)** | **+2** |

### Carga por técnico (gráfico, selector 2026-S30)

Técnico 01: **35** (30,45 + 4,55 rojo) · 02: 22 · 03: 26 · 04: 18 · 05: 20 ·
06: **40** (30,45 + 9,55 rojo) · 07: 15 (capacidad 24,36 por ausencia "X") ·
08: 27 · 09: 18 · 10: 20 · 11: 10 · 12: 15. Conflicto demo: **OT-000026**
asignada a Técnico 04 en su semana de vacaciones (2026-S31, turno "VAC") →
HHA 10, **HHD −10,00**.

### Otros números

Costos: `costo_plan` = horas **estimadas** × 25 (prev) / × 40 (corr) — el
costo plan es del ERP y no se recalcula con el ajuste manual; `precio` = 40 %
del plan (REGLA-8 → materiales 60 %); dos órdenes históricas con `precio >
plan` (materiales 0). Equipo de mayor gasto: EQ-110 (5.070 USD).

## Estructura del libro (21 hojas)

`INICIO` · `PARAMETROS` · `1_IMPORTAR_ORDENES` (paso único de pegado) ·
`2_IMPORTAR_EJECUCION` (`tblEjecucion`, 1.200 filas) · `ORDENES`
(`tblOrdenes`, 1.200 filas × 41 columnas: 12 importadas A:L, 6 editables en
azul, 23 calculadas; `id_operacion` al final) · `TECNICOS` · `ASIGNACIONES` ·
`PERFIL_HH` (serie dinámica de 60 semanas + matriz semáforo + REGLA-9) ·
`PLAN_SEMANAL` (6 selectores + gráfico de carga + grilla 1.200) ·
`ADHERENCIA` (bloque semanal dinámico + 5 desgloses + gráfico) · `COSTOS` ·
`BACKLOG` · `EQUIPOS_CRITICOS` · `VALIDACION` (9 chequeos REGLA-10 + 2 de
ajustes) · 5 catálogos `CAT_*` · `EXPORTAR` · `_COMPATIBILIDAD`.

## Limitaciones conocidas

- `XLOOKUP` exige Excel 2021/365 en el principal; use el compatible para
  Excel 2016/LibreOffice.
- Sin caché de resultados hasta el primer abrir-y-guardar (§7).
- Filas de semanas nuevas tras re-importar pueden requerir "Mostrar filas"
  (§4); capacidad máxima de la serie: 60 semanas.
- `horas_ajustadas` está anclada a la fila, no al `id_operacion` (§3).
- Área de impresión de PLAN_SEMANAL estática (§5).
