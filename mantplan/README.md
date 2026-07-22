# MantPlan — Entregable A: `MantPlan.xlsx` (v2.6.0)

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
| `VERIFICACION.md` | Reporte de verificación (recálculo + comparación + casos) | — |
| `README.md` | Este documento | — |

Ambos libros llevan las mismas 200 órdenes sintéticas ancladas al
**2026-07-22**, sobre tablas provisionadas para **1.200 filas**, y producen
números idénticos (verificado, ver §1).

## Cómo regenerarlo

```bash
pip install openpyxl
python generar_mantplan.py                                        # MantPlan.xlsx (principal)
python generar_mantplan.py --salida MantPlan_compatible.xlsx --refs compatibles
python generar_mantplan.py --fecha-ancla 2026-07-22               # fija el "hoy" de los datos
python generar_mantplan.py --resumen                              # imprime los números esperados
```

## Decisiones técnicas

### 1. Verificación: doble implementación + recálculo real

- El generador emite el libro en dos modos desde **las mismas plantillas de
  fórmula** (`class Refs`): `estructuradas` (XLOOKUP, entregable principal) y
  `compatibles` (INDEX/MATCH + rangos A1 acotados).
- La variante compatible se recalculó con LibreOffice: **71.014 fórmulas, 0
  errores**.
- Cada valor recalculado se comparó contra el motor Python: **9.486
  comparaciones automáticas, 0 desviaciones**, incluidos el calendario laboral
  (es_habil, backlog_habiles, capacidad por día), los desgloses por sub-área y
  la reconciliación área = Σ sub-áreas.
- Caso de reordenamiento (VERIFICACION.md §3.4): un libro con las 200 filas de
  ORDENES invertidas recalcula con los ajustes aplicados a las mismas órdenes.
- Caso de bloque condicional (VERIFICACION.md §3.5): con una semana sin
  técnicos sobreasignados, la alerta de capacidad del correo desaparece sin
  encabezado ni líneas en blanco huérfanas.

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

### 3. Ajustes de duración por clave: hoja `AJUSTES` (`tblAjustes`, v2.1)

Flujo real mensual: se pega la exportación del ERP **en un solo bloque** sobre
`ORDENES!A4` (columnas A:L) y los ajustes registrados en `AJUSTES` **se
re-aplican solos por `id_operacion`, sin importar el orden de las filas** del
nuevo export. (En v2.0 el ajuste vivía como columna de `tblOrdenes`, anclado a
la posición de la fila: un export reordenado lo aplicaba a la orden
equivocada sin error visible. Resuelto aquí.)

- **`tblAjustes`** (300 filas): `id_operacion` (clave, editable),
  `horas_ajustadas`, `motivo`, `fecha_ajuste` (editables) y tres columnas
  calculadas: **`descripcion`** (trae la descripción de la orden desde
  `tblOrdenes` para confirmar visualmente que se ajustó la orden correcta),
  `estado_ajuste` (aplicado / huérfano / duplicado-se-ignora, con resaltado) y
  `desviacion_h` (ajustadas − estándar ERP de esa orden). Las dos últimas son
  adiciones sobre lo pedido: alimentan los chequeos de VALIDACION sin
  fórmulas matriciales frágiles y dan feedback inmediato al usuario.
- **`horas_efectivas`** en `tblOrdenes` (columna M, calculada) se resuelve por
  búsqueda en ambos modos: `XLOOKUP(id_operacion; tblAjustes[id_operacion];
  tblAjustes[horas_ajustadas]; horas_estimadas)` en el principal, y
  `IFERROR(INDEX(…MATCH(…)); horas_estimadas)` en el compatible. Ante
  `id_operacion` duplicado en AJUSTES gana la primera fila (semántica de
  primera coincidencia de ambas funciones, replicada en el motor Python).
- **Todos los cálculos de horas usan `horas_efectivas`**: HHA, HHD,
  PERFIL_HH (REGLA-6), adherencia por horas (REGLA-7), REGLA-9, gráfico de
  carga, BACKLOG y EXPORTAR. `horas_estimadas` queda como referencia del ERP.
- `VALIDACION` reporta: órdenes con ajuste, desviación total en horas,
  **ajustes huérfanos** (id inexistente en ORDENES — típicamente órdenes ya
  cerradas/purgadas) y **duplicados dentro de tblAjustes**.

#### Nota de diseño: `horas_efectivas` nunca alimenta costo

`horas_efectivas` alimenta exclusivamente **capacidad, carga y utilización**
(HHA, HHD, PERFIL_HH, gráfico de carga). **Nunca alimenta costo.** La mano de
obra propia es costo fijo de nómina, ya contabilizado fuera de la orden;
ajustar las horas de una tarea cambia la utilización del técnico, no el
gasto. El costo variable (materiales y servicios de terceros) vive en
`costo_plan`, tomado del ERP sin recálculo. La mano de obra con desembolso
incremental —horas extra, recargos, contratistas— se rastrea por separado y
no se imputa al costo de la orden.

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
| Correo Outlook | Hoja `EXPORTAR`: correo redactado completo en una celda (§11) |
| Checklists | `HYPERLINK(ruta_base & link_checklist)` |

### 9. HHA / HHD

- `HHA` = `SUMIFS(horas_efectivas; tecnico; semana; dia)` — total del técnico
  ese día, repetido en sus filas.
- `HHD` = `factor_productividad × horas_disponibles − HHA`, con
  `horas_disponibles` buscada en `tblAsignaciones` (REGLA-5): con turno
  normal la capacidad diaria es 8 × 0,87 = **6,96 h**; con `VAC`/`X` es 0 y
  **HHD = −HHA**. HHD < 0 en rojo = sobreasignación.

### 11. EXPORTAR: correo del programa semanal (v2.2)

`EXPORTAR` ya no emite una línea seca + listado: arma un **correo redactado,
listo para enviar sin editar**, en una sola celda (`A6`, para copiar y pegar),
con seis secciones que respetan los tres filtros de la hoja (semana, turno,
coordinador) — texto y totales reflejan el subconjunto filtrado:

1. **Saludo y contexto** con planta y empresa (desde `PARAMETROS`, nunca en la
   fórmula) y el rango de fechas de la semana, calculado del rótulo `AAAA-Snn`
   por aritmética ISO (`DATE(año,1,4) − WEEKDAY(...) + 1 + (semana−1)·7`).
2. **Resumen de carga**: órdenes programadas, HH planificadas (sobre
   `horas_efectivas`), desglose preventiva/correctiva en horas y %, y técnicos
   involucrados.
3. **Alerta de capacidad**, condicional: lista los técnicos con carga semanal
   > capacidad (factor × horas disponibles de `tblAsignaciones`). Si no hay
   ninguno, el bloque **desaparece entero** — sin encabezado ni línea en
   blanco huérfana (verificado, §3.5 de VERIFICACION.md).
4. **Tareas relevantes**: las `p_top_tareas` (nuevo parámetro, default 5) de
   mayor `horas_efectivas` entre las pendientes y dentro del plan, con equipo,
   descripción, horas y técnico, marcando permiso de trabajo y bloqueo de
   energía (LOTO).
5. **Programa completo**, agrupado por día y, dentro del día, ordenado por
   turno y técnico.
6. **Cierre** con la frase de coordinación.

**Cómo, sin macros:** todo vive en una **zona auxiliar a la derecha (marcada
"no editar")**, una columna por magnitud. El orden del programa y el "top N"
se resuelven con **clave numérica + `SUMPRODUCT` (rango) + `INDEX/MATCH`
(emisión por posición)** — nunca `SORT`/`FILTER`, que son funciones de derrame
y openpyxl no puede escribir su metadato de spill. Los bloques condicionales
desaparecen limpios porque el ensamblado final es
`TEXTJOIN(CHAR(10)&CHAR(10); VERDADERO; sección1…sección6)`: `TEXTJOIN` con
"ignorar vacíos" omite una sección `""` sin dejar separador.

**Sobre `LET`:** se omite a propósito. `_xlfn.LET` no lo evalúa LibreOffice
24.2, así que romperia la verificación de la variante compatible; la
legibilidad se obtiene con la zona auxiliar (una fórmula corta por celda) en
vez de una fórmula gigante con `LET`. Es la única desviación respecto de las
funciones sugeridas, y es conforme ("`LET` si ayuda").

### 12. Dimensión `sub_area` (jerarquía área → sub-área → CECO, v2.3)

Nivel jerárquico intermedio entre área y CECO, **hermano de área** — no toca
ninguna de las 10 reglas del motor, es una dimensión de agrupamiento.

- **Catálogo**: `CAT_CENTROS_COSTO` gana la columna `sub_area`, entre `area`
  y `linea`. Un área (p. ej. SERVICIOS) puede subdividirse en sub-áreas
  (Vapor, Refrigeración, CO2, Aire comprimido), y cada sub-área agrupa uno o
  varios CECOs.
- **Herencia**: `sub_area_efectiva = IF(sub_area<>"", sub_area, area)`. Si un
  CECO no tiene sub-área definida, hereda el **nombre del área** (nunca el
  código del CECO), así los reportes siempre muestran nombres de proceso y un
  área sin subdividir se ve idéntica en el nivel área y sub-área. Implementada
  en Python (`sub_area_efectiva`) y en la columna calculada de ORDENES en
  ambos modos: `XLOOKUP`/`INDEX-MATCH` de la sub-área del CECO, con la celda
  `area` ya calculada como valor de herencia.
- **Columna en ORDENES**: `sub_area` calculada, **adyacente a `area`**.
- **Dimensión de reporte**: nuevo desglose por sub-área en **ADHERENCIA**
  (jerárquico, con el área madre en una columna auxiliar), **COSTOS** (matriz
  por sub-área, además de por área) y **BACKLOG** (tramos por sub-área), y
  como **selector** en PLAN_SEMANAL (7.º filtro) y EXPORTAR (4.º filtro).
  PERFIL_HH se mantiene por especialidad (la sub-área no aporta ahí).
- **Reconciliación**: la suma de las sub-áreas de un área = el total del área
  (verificado, VERIFICACION.md §3.6). Con los datos de muestra, SERVICIOS =
  Vapor + Refrigeración + CO2 + Aire comprimido; PRODUCCION y EMPAQUE quedan
  sin subdividir (heredan su nombre) y conviven con SERVICIOS en el mismo
  reporte.

### 13. Calendario laboral (hoja `CALENDARIO`, v2.4)

Distingue días **hábiles** de **no laborables** (fines de semana, feriados,
paros): un día no hábil no aporta capacidad y no penaliza los indicadores. Es
un cambio transversal que toca REGLA-5, backlog (REGLA-3/4), ADHERENCIA y
EXPORTAR — sin alterar la definición de las reglas, solo su insumo de días.

- **Parte A — patrón semanal**: 7 filas lunes…domingo con indicador hábil/no.
  Default L-V hábil, S-D no. Se marca una vez y aplica a todo el año sin
  listar fechas (rango con nombre `patronHabil`).
- **Parte B — `tblExcepciones`** (200 filas): solo las fechas que rompen el
  patrón. `fecha`, `tipo` (feriado / paro / día especial laborable), `habil`
  (sí/no), `area` (vacío = toda la planta), `sub_area` (vacío = toda el área),
  `motivo`, y una `clave` calculada `fecha|area|sub_area`. Aquí van los ~12-15
  feriados del año.
- **Parte C — grid del calendario** (760 días, nivel planta): fechas
  consecutivas con su `habil` (patrón + feriados generales), rangos con nombre
  `cal_fechas`/`cal_habil`. Es la base para contar días hábiles del backlog.

**`es_habil(fecha, area, sub_area)`** resuelve por **especificidad**, de más
específico a más general (la primera que aplica manda): (a) excepción fecha +
área + sub-área; (b) fecha + área; (c) excepción general de la fecha; (d)
patrón semanal. En fórmula esto es un `XLOOKUP` (o `INDEX/MATCH`) anidado
donde el argumento *si_no_encontrado* de cada nivel encadena al siguiente y,
al final, a `INDEX(patronHabil, WEEKDAY(fecha))`. Existe en Python
(`es_habil`) y en ambos modos de referencia.

**Impacto en las reglas:**

- **REGLA-5**: un día no hábil da 0 horas disponibles sin importar el turno
  (la fórmula de `horas_disponibles` de ASIGNACIONES multiplica por
  `es_habil(fecha, área, "") = "sí"`). La capacidad de PERFIL_HH baja en
  consecuencia. ASIGNACIONES gana una columna `fecha` (lunes ISO de la semana
  + día) para consultar el calendario.
- **Backlog**: nueva columna `backlog_habiles` = días hábiles (nivel planta,
  vía `COUNTIFS` sobre el grid) entre `fecha_inicio` y hoy, con signo. **Ambos
  coexisten**: `backlog_habiles` alimenta REGLA-3 y REGLA-4 (gestión interna),
  y `backlog_dias` (calendario) se conserva para los indicadores contractuales
  en días corridos (el envejecimiento por tramos de BACKLOG sigue en días
  calendario). *Decisión: `backlog_habiles` usa el calendario a nivel planta
  (patrón + feriados generales), no las excepciones por área/sub-área — el
  conteo de aging es de planta; las excepciones por área afectan capacidad y
  el flag `es_habil` por orden.*
- **ADHERENCIA**: las órdenes cuya fecha cae en día no hábil **no penalizan el
  denominador** — se excluyen del cálculo (criterio `es_habil = "sí"` en todos
  los COUNTIFS/SUMIFS) y se reportan aparte en VALIDACION. *Decisión: no tiene
  sentido penalizar por no ejecutar una orden un día no laborable.*
- **EXPORTAR**: el programa completo recorre los **siete días** (ya ordenaba
  por día; la siembra de datos ahora incluye sábado y domingo). Un día no
  laborable con órdenes (p. ej. el domingo especial de SERVICIOS) sí se lista.
- **VALIDACION** suma tres chequeos: órdenes programadas en día no laborable,
  y excepciones cuya área o sub-área no existe en catálogo.

### Turnos con franja horaria (CAT_TURNOS, 6.2)

Los turnos pasan de ser una simple lista de códigos a un **catálogo con
significado horario**. `CAT_TURNOS` es la **fuente única** de la definición:
cada turno tiene `nombre`, `hora_inicio`, `hora_fin` y `tipo` (`banco` o
`rotativo`).

| turno | nombre | inicio | fin | tipo |
|---|---|---|---|---|
| `B` | Banco | 07:00 | 16:00 | banco |
| `T1` | Turno 1 | 06:00 | 15:00 | rotativo |
| `T2` | Turno 2 | 15:00 | 22:00 | rotativo |
| `T3` | Turno 3 | 22:00 | 06:00 | rotativo |

- `ASIGNACIONES` gana dos columnas calculadas, `hora_inicio` y `hora_fin`, que
  se traen del turno de la fila por búsqueda en `CAT_TURNOS` (quedan en blanco
  para `VAC`, `X` o turno vacío).
- La **franja es metadato de horario**: la capacidad **no** se deriva de ella
  (sigue plana en 8 h por la jornada, REGLA-5); no hay aritmética de solape ni
  rotación —la rotación/derivación queda fuera de este bloque—. Se verificó que
  la capacidad es idéntica a la de 6.1.
- La lista de validación de la columna `turno` (`lista_turnos`) se reapunta a
  `CAT_TURNOS` (+ `VAC`/`X`), de modo que no hay dos fuentes de la definición;
  el antiguo rango auxiliar de turnos en `PARAMETROS` se retiró.
- Convención de códigos: cualquier `B1` de Banco pasa a `B`; el área AUT usa
  `B`.

### 10. Higiene de fórmulas

Auditado sobre los archivos finales: sin `OFFSET`, sin `INDIRECT`, sin
columnas completas (`A:A`), sin enlaces externos, sin VBA, sin nombres
definidos huérfanos.

## Datos de ejemplo y verificación a mano (ancla 2026-07-22)

200 órdenes (tablas con capacidad 1.200) · 157 filas de ejecución (3
huérfanas) · 4 ajustes (2 aplicados + 2 demos de error) · 12 técnicos · 336
asignaciones · semanas del plan **2026-S29 … 2026-S32** · serie completa de
reportes: 2026-S08 … 2027-S01.

### Caso 1 — cruce de fin de año (REGLA-2 v2)

| orden | fecha | semana | anio (YEAR) |
|---|---|---|---|
| OT-000182 | 2026-12-29 | **2026-S53** | 2026 |
| OT-000183 | 2027-01-01 | **2026-S53** | **2027** ← año ISO ≠ YEAR |
| OT-000184 | 2027-01-05 | **2027-S01** | 2027 |

`2026-S53` y `2027-S01` aparecen como semanas distintas en la serie de
PERFIL_HH/ADHERENCIA (las dos últimas filas visibles), sin mezcla.

### Caso 2 — ajuste manual de horas (hoja `AJUSTES` → `horas_efectivas`)

`tblAjustes` trae 4 filas demo: dos aplicadas, un duplicado (se ignora, gana
la primera) y un huérfano (id `OT-0009990010`, inexistente).

- **OT-000017** (MEC, preventiva, Técnico 01, martes 2026-S30): ajuste por
  clave `OT-0000170010` con `horas_ajustadas` **12** (estimadas 8) →
  `horas_efectivas` 12.
  - PERFIL_HH MEC 2026-S30: prev **84** (80 + 4 del ajuste), carga **68,8 %**.
  - Gráfico de carga (selector 2026-S30): barra de Técnico 01 = **41** =
    6+12+10+7 (L-V) + 6 (sábado correctivo) → **dentro de la capacidad
    semanal 41,76 h** (sin rojo).
  - HHA del martes = **12**, HHD = 6,96 − 12 = **−5,04** (rojo).
- **OT-000061** (ELE, preventiva, Técnico 05): 6 → **4** → ELE 2026-S30 prev
  63, carga 73,5 %.
- `VALIDACION`: **2** órdenes con ajuste, desviación total **+2 h**,
  **1** huérfano, **2** duplicados en tblAjustes.
- **Reordenamiento** (VERIFICACION.md §3.4): con las 200 filas de ORDENES
  invertidas, OT-000017 pasó de la fila 20 a la 187 y OT-000061 de la 64 a
  la 143, y ambas conservaron sus horas efectivas (12 y 4).

### PERFIL_HH esperado (REGLA-6, semanas del plan)

Cuenta rápida: **MEC 2026-S29 = 4 técnicos × 6 días × 8 h = 192; × 0,87 =
167,04; 82 prev + 20 corr = 102; carga 61,1 % → verde.**

Con la jornada de 8 h y la base semanal de 48 h (L-S, 6.1) la capacidad
disponible subió respecto de la base anterior de 7 h × 5 días, así que el
plan de muestra ahora cabe con holgura: ninguna especialidad queda en rojo.
Los números de S30/S31 siguen reflejando el calendario laboral (v2.4): en
2026-S31 el feriado del miércoles reduce la capacidad de todas las
especialidades (MEC de 192 a 120 h), y las órdenes de fin de semana sumaron
horas correctivas en 2026-S30.

| esp | semana | disp | prod | prev | corr | plan | holgura | % carga |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| MEC | 2026-S29 | 192 | 167,04 | 82 | 20 | 102 | 65,04 | 61,1 % 🟢 |
| MEC | 2026-S30 | 192 | 167,04 | 84 | 31 | 115 | 52,04 | 68,8 % 🟢 |
| MEC | 2026-S31 | 120 | 104,40 | 80 | 20 | 100 | 4,40 | 95,8 % 🟡 |
| MEC | 2026-S32 | 192 | 167,04 | 72 | 14 | 86 | 81,04 | 51,5 % 🟢 |
| ELE | 2026-S29 | 144 | 125,28 | 60 | 15 | 75 | 50,28 | 59,9 % 🟢 |
| ELE | 2026-S30 | 136 | 118,32 | 63 | 24 | 87 | 31,32 | 73,5 % 🟢 |
| ELE | 2026-S31 | 120 | 104,40 | 60 | 10 | 70 | 34,40 | 67,0 % 🟢 |
| ELE | 2026-S32 | 144 | 125,28 | 52 | 10 | 62 | 63,28 | 49,5 % 🟢 |
| AUT | 2026-S29 | 96 | 83,52 | 40 | 10 | 50 | 33,52 | 59,9 % 🟢 |
| AUT | 2026-S30 | 96 | 83,52 | 45 | 10 | 55 | 28,52 | 65,9 % 🟢 |
| AUT | 2026-S31 | 80 | 69,60 | 35 | 7 | 42 | 27,60 | 60,3 % 🟢 |
| AUT | 2026-S32 | 96 | 83,52 | 30 | 6 | 36 | 47,52 | 43,1 % 🟢 |
| OP | 2026-S29 | 144 | 125,28 | 30 | 8 | 38 | 87,28 | 30,3 % 🟢 |
| OP | 2026-S30 | 144 | 125,28 | 36 | 17 | 53 | 72,28 | 42,3 % 🟢 |
| OP | 2026-S31 | 128 | 111,36 | 34 | 9 | 43 | 68,36 | 38,6 % 🟢 |
| OP | 2026-S32 | 144 | 125,28 | 24 | 6 | 30 | 95,28 | 23,9 % 🟢 |
| TERCERO | 2026-S30 | 0 | 0 | 16 | 0 | 16 | −16,00 | — |
| TERCERO | 2026-S31 | 0 | 0 | 12 | 0 | 12 | −12,00 | — |

Casos preparados: TEC-04 de vacaciones toda 2026-S31 · feriado el miércoles de
2026-S31 (MEC de 192 a **120 h**) · domingo laborable de SERVICIOS en 2026-S31
(OP recupera 8 h vía TEC-12 → 128 h) · TEC-07 ausente el viernes de 2026-S30
(`X`, ELE 136 h) · TERCERO sin capacidad interna (% carga vacío).

### ADHERENCIA esperada (REGLA-7, solo días hábiles)

2026-S29: 30/34 = 88,2 % (HH 229/265 = 86,4 %) · 2026-S30: 19/38 = 50,0 %
(HH 163/310 = 52,6 %) · 2026-S31 y S32: 0 %. Los conteos excluyen las órdenes
en día no laborable (se reportan en VALIDACION); con el sábado hábil (6.1) el
denominador de S30 incluye más OT que antes.

### REGLA-9 esperada (meta: correctivo ≤ 20 %)

2026-S29: 0,25 (20,0 % → SI) · 2026-S30: 0,34 (25,2 % → NO, subió por las
correctivas de fin de semana) · 2026-S31: 0,21 (17,2 % → SI) · 2026-S32: 0,20
(16,8 % → SI).

### BACKLOG esperado (pendientes por tramo, al 2026-07-22)

Envejecimiento en días **calendario** (`backlog_dias`, contractual): el tramo
0–30 depende del día de apertura (`HOY()`). REGLA-3/REGLA-4 usan en cambio los
días **hábiles** (`backlog_habiles`).

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
| ORDENES sin par en EJECUCION (quedan `Pendiente`) | 45 |
| Órdenes con ajuste manual de horas (tblAjustes) | 2 |
| Desviación total de horas (ajustadas − ERP) | +2 |
| **Ajustes huérfanos (id no existe en ORDENES)** | **1** |
| **id_operacion duplicados dentro de tblAjustes** | **2** |

### Carga por técnico (gráfico, selector 2026-S30)

Técnico 01: **41** (dentro de la capacidad semanal 41,76 h; incluye el ajuste
+4 h y la orden del sábado) · 02: 22 · 03: 26 · 04: 18 · 05: 24 · 06: **40** ·
07: 15 (capacidad 34,80 por ausencia "X") · 08: 27 · 09: 18 · 10: 20 · 11: 10 ·
12: 15. Con la base de 48 h/semana (6,96 h/día × 6 días = 41,76 h) **ningún
técnico supera su capacidad semanal**, así que ninguna barra tiene tramo rojo.
Conflicto demo: **OT-000026** asignada a Técnico 04 en su semana de
vacaciones (2026-S31, turno "VAC") → HHA 10, **HHD −10,00** (la disponibilidad
diaria del turno VAC es 0, así que el rojo de HHD persiste aunque la carga
semanal no supere la capacidad).

### Correo generado por EXPORTAR (filtro por defecto: semana 2026-S30)

Texto real producido en `EXPORTAR!A6` con los datos de muestra (recalculado):

```
Buenos días.
A continuación el programa de mantenimiento de Planta Ejemplo — Empresa Ejemplo S.A. para la semana 2026-S30, del 20/07/2026 al 26/07/2026.

Resumen de carga:
• Órdenes programadas: 40
• HH planificadas: 326 h
• Preventiva: 244 h (75%)
• Correctiva: 82 h (25%)
• Técnicos involucrados: 12

Tareas relevantes (top 5 por horas):
   • EQ-102 — Lubricación programada en EQ-102 · 10 h · Técnico 04
   • EQ-108 — Análisis predictivo en EQ-108 · 10 h · Técnico 06
   • EQ-106 — Reparación de falla en EQ-106 · 10 h · Técnico 06 · permiso de trabajo · bloqueo de energía (LOTO)
   … 

Programa completo:

Lunes:
   T1 · Técnico 01 · OT-0000210010 — Inspección de rutina en EQ-110 (6 h)
   …
Sábado:
   … (orden correctiva de fin de semana) …
Domingo:
   … (orden correctiva de fin de semana) …

Cualquier ajuste, favor comunicarlo antes del inicio del turno.
```

Números verificables a mano: **40** órdenes programadas (incluye 3 de fin de
semana → el programa ahora recorre los 7 días), **326 h** = 244 preventiva
(75 %) + 82 correctiva (25 %). Con la capacidad semanal en **41,76 h** (jornada
8 h × base 48 h L-S, 6.1) ningún técnico queda sobreasignado en 2026-S30
—Técnico 01 con 41 h y Técnico 06 con 40 h quedan por debajo—, así que el
**bloque de alerta condicional no aparece** en el correo; se sigue verificando
que desaparece limpio, sin encabezado ni línea en blanco huérfana
(VERIFICACION.md §3.5).

### Calendario laboral: casos verificables a mano (v2.4)

Excepciones de muestra (además de 12 feriados generales del año): feriado de
planta el miércoles de 2026-S31 (2026-07-29), domingo laborable solo para
SERVICIOS (2026-08-02), paro de la sub-área Vapor el jueves de 2026-S30
(2026-07-23), y dos excepciones con área/sub-área fuera de catálogo.

| Caso | Resultado |
|---|---|
| **Feriado general** (mié 2026-07-29) | `horas_disponibles = 0` para TEC-01, TEC-05, TEC-12 (todas las áreas). PERFIL_HH **MEC 2026-S31 cae de 192 a 120 h** disponibles (3 técnicos activos × 5 días × 8). |
| **Domingo laborable SERVICIOS** (2026-08-02) | TEC-12 (SERVICIOS) = **8 h**; TEC-01 (PRODUCCION) = **0**. La excepción por área da capacidad solo a SERVICIOS. |
| **Paro sub-área Vapor** (jue 2026-07-23) | `es_habil` = **no** para órdenes de Vapor; **sí** para PRODUCCION, EMPAQUE y Refrigeración. La excepción por sub-área no afecta a las demás sub-áreas. |
| **Orden que cruza fines de semana** (OT-000138, 2026-06-07) | `backlog_dias` = **45**, `backlog_habiles` = **37**, diferencia **8** días no hábiles en medio (solo domingos, con el sábado hábil de 6.1). |
| **VALIDACION** | 21 órdenes en día no laborable · 1 excepción con área desconocida · 1 con sub-área desconocida. |

Los totales por área siguen cuadrando: la reconciliación COSTOS área = Σ
sub-áreas se mantiene (verificada dentro de las 9.486 comparaciones).

### Sub-áreas: agrupamiento con herencia (COSTOS real, USD)

Jerarquía de muestra y `costo_total` real por sub-área (suma de sus CECOs):

| área | sub-área | CECOs | costo_total |
|---|---|---|---:|
| PRODUCCION | *PRODUCCION* (heredado) | CC-110, CC-120 | 13.185 |
| EMPAQUE | *EMPAQUE* (heredado) | CC-210, CC-220 | 10.385 |
| SERVICIOS | Vapor | CC-310 + CC-311 | **5.820** |
| SERVICIOS | Refrigeración | CC-320 + CC-321 | 3.280 |
| SERVICIOS | CO2 | CC-330 | 200 |
| SERVICIOS | Aire comprimido | CC-340 | 160 |

Números verificables a mano: **Vapor = CC-310 (4.280) + CC-311 (1.540) =
5.820** en una sola fila con el nombre de proceso. **SERVICIOS = 5.820 + 3.280
+ 200 + 160 = 9.460**, que es exactamente el total del área SERVICIOS
(reconciliación). PRODUCCION y EMPAQUE, sin sub-área, reportan bajo el **nombre
de su área**, no bajo `CC-110`/`CC-210`.

### Otros números

Costos: `costo_plan` = horas **estimadas** × 25 (prev) / × 40 (corr) — el
costo plan es del ERP y no se recalcula con el ajuste manual; `precio` = 40 %
del plan (REGLA-8 → materiales 60 %); dos órdenes históricas con `precio >
plan` (materiales 0). Equipo de mayor gasto: EQ-110 (5.810 USD).

## Estructura del libro (24 hojas)

`INICIO` · `PARAMETROS` · `1_IMPORTAR_ORDENES` (paso único de pegado) ·
`2_IMPORTAR_EJECUCION` (`tblEjecucion`, 1.200 filas) · `ORDENES`
(`tblOrdenes`, 1.200 filas × 42 columnas: 12 importadas A:L, 5 editables en
azul, 26 calculadas incl. `es_habil` y `backlog_habiles`; `id_operacion` al
final) · `TECNICOS` · `ASIGNACIONES` (con `fecha`, REGLA-5 sobre el
calendario y la franja horaria del turno `hora_inicio`/`hora_fin` traída de
`CAT_TURNOS`) · `AJUSTES` (`tblAjustes`, 300 filas) · `CALENDARIO` (patrón
semanal + `tblExcepciones` 200 filas + grid de 760 días) · `PERFIL_HH` (serie
dinámica de 60 semanas + matriz semáforo + REGLA-9) · `PLAN_SEMANAL` (7
selectores + gráfico de carga + grilla 1.200) · `ADHERENCIA` (bloque semanal
dinámico + 6 desgloses, solo días hábiles) · `COSTOS` (por área, sub-área y
línea) · `BACKLOG` (tramos por especialidad, área y sub-área) ·
`EQUIPOS_CRITICOS` · `VALIDACION` (9 chequeos REGLA-10 + 4 de ajustes + 3 de
calendario) · 6 catálogos `CAT_*` (incl. `CAT_TURNOS`, turnos con su franja
horaria) · `EXPORTAR` (correo semanal en una celda, 4 selectores) ·
`_COMPATIBILIDAD`.

## Limitaciones conocidas

- `XLOOKUP` exige Excel 2021/365 en el principal; use el compatible para
  Excel 2016/LibreOffice.
- Sin caché de resultados hasta el primer abrir-y-guardar (§7).
- Filas de semanas nuevas tras re-importar pueden requerir "Mostrar filas"
  (§4); capacidad máxima de la serie: 60 semanas.
- Área de impresión de PLAN_SEMANAL estática (§5).
- Un ajuste en AJUSTES con `id_operacion` informado pero `horas_ajustadas`
  vacía produce horas efectivas 0 en esa orden (visible en `desviacion_h`).
- `backlog_habiles` usa el calendario a nivel planta (no las excepciones por
  área/sub-área); el grid del calendario cubre 760 días desde el 1 de enero
  del año del ancla (una orden fuera de ese rango contaría de menos).
