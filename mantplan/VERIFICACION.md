# VERIFICACION.md — MantPlan v2.2.0

Reporte de verificación del entregable A. Cubre el cambio v2.2 (hoja
`EXPORTAR` que redacta el correo del programa semanal) sobre v2.1 (ajustes en
`tblAjustes` con clave) y v2.0 (REGLA-2 con año ISO, `horas_efectivas`, hojas
dimensionadas por datos, tablas a 1.200 filas).
Fecha de la corrida: **2026-07-21** (ancla de los datos sintéticos).

## 1. Recálculo con motor de cálculo real

La variante `MantPlan_compatible.xlsx` (mismas plantillas de fórmula que el
principal, con `INDEX/MATCH` + rangos A1 en lugar de `XLOOKUP` + referencias
estructuradas) se recalculó por completo con LibreOffice Calc 24.2:

| Métrica | Valor |
|---|---:|
| Fórmulas recalculadas | **64.053** |
| Errores de fórmula (`#REF!`, `#VALUE!`, `#NAME?`, `#DIV/0!`, `#N/A`, …) | **0** |

## 2. Comparación motor Python ↔ Excel recalculado

Cada valor del libro recalculado se comparó contra el motor Python
(`generar_mantplan.py`), tolerancia 1e-6:

| Métrica | Valor |
|---|---:|
| Comparaciones automáticas | **7.648** |
| Desviaciones | **0** |

Cobertura: las 22 columnas calculadas de las 200 órdenes (incluida
`horas_efectivas` resuelta por búsqueda en `tblAjustes`); muestreo de filas
provisionadas vacías (250, 700, 1.203) en blanco; `id_operacion` de las 161
filas de EJECUCION; las 336 filas de REGLA-5; la hoja AJUSTES (descripcion,
estado_ajuste y desviacion_h de las 4 filas demo + fila vacía); PERFIL_HH
completo (serie de 60 posiciones, REGLA-6 por semana × especialidad,
REGLA-9); ADHERENCIA (bloque semanal dinámico + 5 desgloses); BACKLOG por
tramos; COSTOS por mes; EQUIPOS_CRITICOS; zona de datos del gráfico de carga;
los 13 chequeos de VALIDACION; y **EXPORTAR** (los escalares del resumen
AJ8–AJ16, el bloque por técnico AC/AD/AE de los 12, más 18 fragmentos del
texto del correo y el conteo de líneas del programa).

## 3. Casos de prueba

### 3.1 Cruce de fin de año (REGLA-2 v2)

| orden | fecha_inicio | semana | anio (`YEAR`) |
|---|---|---|---|
| OT-000182 | 2026-12-29 | **2026-S53** | 2026 |
| OT-000183 | 2027-01-01 | **2026-S53** | **2027** ← año ISO ≠ YEAR |
| OT-000184 | 2027-01-05 | **2027-S01** | 2027 |

`2026-S53` y `2027-S01` aparecen como semanas distintas en la serie.

### 3.2 Ajuste manual por clave (`tblAjustes` → `horas_efectivas`)

Filas demo de `tblAjustes` y su estado calculado (verificado):

| id_operacion | horas_ajustadas | estado_ajuste | desviacion_h |
|---|---:|---|---:|
| OT-0000170010 | 12 | aplicado | **+4** |
| OT-0000610010 | 4 | aplicado | **−2** |
| OT-0000170010 | 14 | duplicado (se ignora) | — |
| OT-0009990010 | 6 | huérfano | — |

Efectos verificados del ajuste 8 → 12 en OT-000017 (Técnico 01, martes
2026-S30): `horas_efectivas` 12 · PERFIL_HH MEC 2026-S30 prev **84** / carga
**89,5 %** · barra del gráfico Técnico 01 = **35** (30,45 verde + 4,55 rojo) ·
HHA martes 12 / HHD **−5,91**. VALIDACION: órdenes ajustadas **2**, desviación
total **+2 h**, huérfanos **1**, duplicados en tblAjustes **2**.

### 3.3 Recálculo de la variante compatible

**0 errores en 64.053 fórmulas** (§1), mismos números que el motor Python en
las 7.648 comparaciones (§2).

### 3.4 Reordenamiento deliberado de `tblOrdenes`

Se construyó un libro con las **200 filas de ORDENES en orden inverso**, se
recalculó con LibreOffice (0 errores) y se comprobó que los ajustes siguen
aplicados a las órdenes correctas por `id_operacion`:

| id_operacion | fila (orden normal) | fila (invertido) | horas_efectivas |
|---|---:|---:|---:|
| OT-0000170010 (ajustada a 12) | 20 | **187** | **12** ✓ |
| OT-0000610010 (ajustada a 4) | 64 | **143** | **4** ✓ |
| OT-0000010010 (control, sin ajuste) | 4 | 203 | 10 = estimadas ✓ |

Barrido completo del libro reordenado: `horas_efectivas` y `HHA` de las 200
filas contra el motor Python, **0 fallos**, y PERFIL_HH con números idénticos
a los del orden normal. Esto es exactamente lo que la v2.0 no garantizaba
(ajuste anclado a la posición de fila); la inconsistencia señalada en la
sección 6 del reporte anterior queda **resuelta**.

### 3.5 EXPORTAR — correo redactado y bloque condicional que desaparece

Con el filtro por defecto (semana 2026-S30, turno y coordinador "(todos)") el
correo recalculado en `EXPORTAR!A6` contiene, verificado por comparación de
escalares y por presencia de fragmentos:

- Contexto con planta/empresa (de `PARAMETROS`) y rango "del 20/07/2026 al
  26/07/2026" (fechas derivadas del rótulo ISO `2026-S30`).
- Resumen: **37** órdenes, **308 h** (prev **244** = 79 %, corr **64** = 21 %),
  **12** técnicos.
- Alerta de capacidad: Técnico 01 (35,0 vs 30,5) y Técnico 06 (40,0 vs 30,5).
- Top 5 tareas por `horas_efectivas`, con marca de permiso/LOTO donde aplica.
- Programa completo con **exactamente 37 líneas** (conteo de `· OT-`),
  agrupado por día y ordenado por turno y técnico.

**Bloque condicional:** al cambiar el selector a la semana **2026-S32** (sin
técnicos sobreasignados) y recalcular, el escalar de sobreasignados es **0**,
el encabezado "Alerta de capacidad" **no aparece**, no hay triple salto de
línea (bloque vacío sin residuo) y el correo pasa directo del resumen a las
tareas relevantes. Confirma que los bloques condicionales desaparecen limpios.

## 4. Qué NO se verificó (y por qué)

- **El archivo principal (`MantPlan.xlsx`) no se puede recalcular
  localmente**: LibreOffice 24.2 no evalúa `XLOOKUP` ni referencias
  estructuradas. Su corrección se infiere de que ambos modos salen de las
  mismas plantillas (`class Refs`) más auditoría sintáctica del XML
  (XLOOKUP canónico `_xlfn.`, cero OFFSET/INDIRECT/columnas completas, cero
  enlaces externos, cero VBA). Falta el humo final en Excel real.
- **Renderizado visual** (gráficos, formato condicional, resaltados de
  AJUSTES): verificado por inspección del XML/objetos, no por captura.
- **El texto exacto del correo de EXPORTAR** no se compara carácter a
  carácter contra un esperado generado por Python: se verifican los escalares
  numéricos (exactos) y la presencia de 18 fragmentos clave + el conteo de
  líneas del programa. El orden interno de líneas dentro de un mismo día se
  revisó por inspección visual del texto recalculado, no por aserción.
- **Re-importación real con datos nuevos** no se simuló como flujo de usuario
  (el caso 3.4 cubre el mecanismo crítico: ajustes por clave ante
  reordenamiento).
- **Límite de 32.767 caracteres** de una celda de Excel: un programa con
  cientos de órdenes en el filtro truncaría el correo. La zona de emisión se
  provisiona a 200 líneas de programa y 20 de top; un filtro semanal normal
  queda muy por debajo. No verificado en el límite.

## 5. Supuestos tomados donde la instrucción era ambigua

1. **Columnas extra en `tblAjustes`**: el pedido definía 5 columnas; se
   añadieron `estado_ajuste` y `desviacion_h` (calculadas) porque los
   chequeos de VALIDACION las necesitan sin recurrir a fórmulas matriciales
   frágiles, y dan el feedback visual que la columna `descripcion` inicia.
2. **Duplicados en `tblAjustes`**: se aplica la primera fila (semántica de
   primera coincidencia de XLOOKUP/MATCH, replicada en Python) y las demás se
   marcan "duplicado (se ignora)".
3. **Ajuste con `horas_ajustadas` vacía**: si se escribe el `id_operacion`
   pero no las horas, la búsqueda devuelve 0 y la orden queda con 0 horas
   efectivas. Visible en `desviacion_h`; documentado como limitación.
4. **`fecha_ajuste` es editable e informativa**: no participa de ningún
   cálculo (no hay regla que la use).
5. **EXPORTAR** (v2.2): (a) `LET` se omite — `_xlfn.LET` no lo evalúa
   LibreOffice y rompería la verificación; la legibilidad se logra con la zona
   auxiliar. (b) "Órdenes programadas" = en alcance de los filtros **y**
   `en_plan = TRUE`; el top de tareas añade `estado = "Pendiente"`. (c) La
   capacidad del técnico se toma de la semana seleccionada; con
   turno/coordinador filtrados la carga se reduce pero la capacidad no, así
   que la alerta es más significativa con turno/coordinador en "(todos)".
   (d) Con semana "(todos)" el rango de fechas usa MIN/MAX de las órdenes en
   alcance en lugar del lunes–domingo ISO. (e) Se añade un parámetro
   `top_tareas` (default 5) y una firma implícita con planta/empresa en el
   saludo.
6. Se mantienen los supuestos de v2.0/v2.1: ocultamiento de filas decidido al
   generar; ventana de 4 semanas solo en desplegables; `costo_plan` sin
   recálculo (reforzado por la nota de diseño del README §3: `horas_efectivas`
   nunca alimenta costo); área de impresión estática; nombre de hoja
   `PLAN_SEMANAL`; duplicados en tblAjustes resueltos por primera coincidencia.

## 6. Inconsistencias abiertas

- ~~`horas_ajustadas` anclada a la fila~~ — **resuelta en v2.1** (caso 3.4).
- **`anio` (= `YEAR`) convive con el año ISO de `semana`**: en los días de
  cruce difieren (OT-000183: anio 2027, semana 2026-S53). Correcto para
  costos mensuales vs. planificación semanal; no cruzar ambos campos en un
  mismo reporte.
- **Capacidad de la serie: 60 semanas** (los datos de ejemplo ocupan 47);
  `tblAjustes`: 300 filas. Un histórico mayor trunca; subir `CAP_SEM` /
  `CAP_AJUSTES` en el generador si el caso real lo pide.
