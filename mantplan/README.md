# MantPlan — Entregable A: `MantPlan.xlsx` (v2.7.0)

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
**2026-07-23**, sobre tablas provisionadas para **1.200 filas**, y producen
números idénticos (verificado, ver §1).

## Cómo regenerarlo

```bash
pip install openpyxl
python generar_mantplan.py                                        # MantPlan.xlsx (principal)
python generar_mantplan.py --salida MantPlan_compatible.xlsx --refs compatibles
python generar_mantplan.py --fecha-ancla 2026-07-23               # fija el "hoy" de los datos
python generar_mantplan.py --resumen                              # imprime los números esperados (incl. rotación)
```

## Decisiones técnicas

### 1. Verificación: doble implementación + recálculo real

- El generador emite el libro en dos modos desde **las mismas plantillas de
  fórmula** (`class Refs`): `estructuradas` (XLOOKUP, entregable principal) y
  `compatibles` (INDEX/MATCH + rangos A1 acotados).
- La variante compatible se recalculó con LibreOffice: **72.814 fórmulas, 0
  errores**.
- Cada valor recalculado se comparó contra el motor Python: **11.409
  comparaciones automáticas, 0 desviaciones**, incluidas la rotación derivada de
  turnos (cobertura, avance y turno efectivo de las 448 filas de ASIGNACIONES),
  el calendario laboral (es_habil, backlog_habiles, capacidad por día), los
  desgloses por sub-área y la reconciliación área = Σ sub-áreas.
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
  (sigue plana en 8 h por la jornada, REGLA-5); no hay aritmética de solape. Se
  verificó que la capacidad es idéntica a la de 6.1.
- La lista de validación (`lista_turnos`) se reapunta a `CAT_TURNOS`
  (+ `VAC`/`X`), de modo que no hay dos fuentes de la definición; el antiguo
  rango auxiliar de turnos en `PARAMETROS` se retiró.

### Rotación automática de turnos (6.3)

El turno ya no es un dato de entrada: se **deriva por aritmética modular** de la
posición del técnico en el anillo del ciclo. La entrada queda en dos campos de
`TECNICOS` (`rotativo` sí/no, `orden_rotacion` 1..N) y un parámetro
(`semana_referencia`, una **fecha**). El usuario normalmente no toca nada.

**El anillo.** Para una especialidad con `N` posiciones (banco = `N-3` puestos de
Banco), el orden de avance semanal es:

```
B(N-3), B(N-4), …, B1, T3, T2, T1  → y vuelve a B(N-3)
(ej. N=7:  B4, B3, B2, B1, T3, T2, T1 → B4)
```

Avanza **+1 posición por semana**. El relevo `B1→T3` y el cierre `T1→B(N-3)`
salen solos del avance, sin tratarse aparte.

**La derivación** (por fila de `ASIGNACIONES`, técnico rotativo):

```
N       = COUNTIFS(TECNICOS: rotativo=sí, especialidad=E, area=A)
semanas = (lunes de la semana de la fila − semana_referencia) / 7
pos     = MOD( (orden_rotacion − 1) + semanas , N )
posicion_ciclo = si pos<N-3 → "B"&(N-3-pos) ; si no → "T"&(N-pos)
banda   = si pos<N-3 → "B" ; si no → la etiqueta T
```

Se aplica de **lunes a sábado**; el **domingo** queda sin turno (fuera de la base
L-S, 6.1). `AUT` (no rotativo) es Banco fijo (`posicion_ciclo="B"`, L-S).

**Alcance por (especialidad, área).** `N` se cuenta con `COUNTIFS` filtrando por
especialidad **y** área, así una especialidad repartida en varias áreas tiene un
ciclo por área. El flag `rotativo` es **explícito** por técnico (no se hardcodea
a MEC/ELE).

**Columnas de `ASIGNACIONES`.**
- `n_ciclo` y `posicion_ciclo` (derivadas, auditoría): `N` y la etiqueta del
  anillo (`B4`..`B1`/`T3`/`T2`/`T1`) para rotativos L-S; `""` el domingo; `"B"`
  para AUT.
- `turno_manual` (**entrada**, desplegable = `CAT_TURNOS` + `VAC`/`X`, vacío por
  defecto): override de excepción. El desplegable se movió aquí desde `turno`.
- `turno` pasa a **derivado (efectivo)**:
  `=SI(turno_manual<>""; turno_manual; banda_de(posicion_ciclo))`. Es lo que leen
  REGLA-5 y los lookups de franja (6.2).

**UX.** Normalmente la rotación llena `turno` sola. Para una excepción puntual (o
`VAC`/`X` hasta que 6.4 lo automatice) se escribe en `turno_manual` y **solo esa
celda** se sobrescribe; vaciarla devuelve la rotación (verificado, VERIFICACION.md
§0-d).

**Capacidad sin cambios.** REGLA-5 lee el `turno` efectivo sin tocar su lógica:
cada técnico rotativo/AUT sigue sumando **48 h/semana** (L-S, domingo 0). La banda
cambia *qué* turno, no *cuántas* horas.

**Doble implementación.** La derivación existe como función pura
(`turno_derivado`, con `posicion_ciclo_de` y `etiqueta_anillo`) y como fórmula del
libro en ambas variantes; coinciden celda a celda (las 448 filas).

### 10. Higiene de fórmulas

Auditado sobre los archivos finales: sin `OFFSET`, sin `INDIRECT`, sin
columnas completas (`A:A`), sin enlaces externos, sin VBA, sin nombres
definidos huérfanos.

## Datos de ejemplo y verificación a mano (ancla 2026-07-23)

200 órdenes (tablas con capacidad 1.200) · 162 filas de ejecución (3
huérfanas) · 4 ajustes (2 aplicados + 2 demos de error) · **16 técnicos**
(7 MEC + 7 ELE rotativos en PRODUCCION + 2 AUT fijos) · **448 asignaciones**
· semanas del plan **2026-S29 … 2026-S32** · semana de referencia de la
rotación (lunes) **2026-07-13** · serie completa de reportes: 2026-S09 …
2027-S01.

### Caso 1 — cruce de fin de año (REGLA-2 v2)

| orden | fecha | semana | anio (YEAR) |
|---|---|---|---|
| OT-000165 | 2026-12-29 | **2026-S53** | 2026 |
| OT-000166 | 2027-01-01 | **2026-S53** | **2027** ← año ISO ≠ YEAR |
| OT-000167 | 2027-01-05 | **2027-S01** | 2027 |

`2026-S53` y `2027-S01` aparecen como semanas distintas en la serie de
PERFIL_HH/ADHERENCIA (las dos últimas filas visibles), sin mezcla.

### Caso 2 — ajuste manual de horas (hoja `AJUSTES` → `horas_efectivas`)

`tblAjustes` trae 4 filas demo: dos aplicadas, un duplicado (se ignora, gana
la primera) y un huérfano (id `OT-0009990010`, inexistente).

- **OT-000013** (MEC, preventiva, Técnico 01, 2026-S30): ajuste por clave
  `OT-0000130010` con `horas_ajustadas` **12** (estimadas 8) →
  `horas_efectivas` 12.
  - PERFIL_HH MEC 2026-S30: prev **82** (80 + 4 del ajuste − 2 del reparto),
    carga **41,4 %**.
  - Gráfico de carga (selector 2026-S30): barra de Técnico 01 = **32**, dentro
    de la capacidad semanal **41,76 h** (sin rojo).
  - HHA del día del ajuste = **12**, HHD = 6,96 − 12 = **−5,04** (rojo por día,
    aunque la carga semanal no supere la capacidad).
- **OT-000059** (ELE, preventiva, Técnico 08): 6 → **4** → ELE 2026-S30 prev
  59, carga 28,4 %.
- `VALIDACION`: **2** órdenes con ajuste, desviación total **+2 h**,
  **1** huérfano, **2** duplicados en tblAjustes.
- **Reordenamiento** (VERIFICACION.md §3.4): el ajuste va por `id_operacion`, no
  por posición; con las 200 filas de ORDENES invertidas ambas órdenes conservan
  sus horas efectivas (12 y 4).

### PERFIL_HH esperado (REGLA-6, semanas del plan)

Cuenta rápida: **MEC 2026-S29 = 7 técnicos × 6 días × 8 h = 336; × 0,87 =
292,32; 82 prev + 20 corr = 102; carga 34,9 % → verde.**

Con la dotación de 7 rotativos por especialidad (6.3) y la base de 48 h (L-S,
6.1), la capacidad disponible es amplia y el plan de muestra cabe con holgura:
ninguna especialidad queda en amarillo ni rojo. En **2026-S31** el feriado
general del miércoles reduce la capacidad (MEC de 336 a **280 h** = 7 × 5 × 8),
y las órdenes de fin de semana suman correctivas en 2026-S30.

| esp | semana | disp | prod | prev | corr | plan | holgura | % carga |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| MEC | 2026-S29 | 336 | 292,32 | 82 | 20 | 102 | 190,32 | 34,9 % 🟢 |
| MEC | 2026-S30 | 336 | 292,32 | 82 | 39 | 121 | 171,32 | 41,4 % 🟢 |
| MEC | 2026-S31 | 280 | 243,60 | 80 | 20 | 100 | 143,60 | 41,1 % 🟢 |
| MEC | 2026-S32 | 336 | 292,32 | 72 | 14 | 86 | 206,32 | 29,4 % 🟢 |
| ELE | 2026-S29 | 336 | 292,32 | 60 | 15 | 75 | 217,32 | 25,7 % 🟢 |
| ELE | 2026-S30 | 336 | 292,32 | 59 | 24 | 83 | 209,32 | 28,4 % 🟢 |
| ELE | 2026-S31 | 280 | 243,60 | 60 | 10 | 70 | 173,60 | 28,7 % 🟢 |
| ELE | 2026-S32 | 336 | 292,32 | 52 | 10 | 62 | 230,32 | 21,2 % 🟢 |
| AUT | 2026-S29 | 96 | 83,52 | 40 | 10 | 50 | 33,52 | 59,9 % 🟢 |
| AUT | 2026-S30 | 96 | 83,52 | 45 | 10 | 55 | 28,52 | 65,9 % 🟢 |
| AUT | 2026-S31 | 80 | 69,60 | 35 | 7 | 42 | 27,60 | 60,3 % 🟢 |
| AUT | 2026-S32 | 96 | 83,52 | 30 | 6 | 36 | 47,52 | 43,1 % 🟢 |
| TERCERO | 2026-S30 | 0 | 0 | 16 | 0 | 16 | −16,00 | — |
| TERCERO | 2026-S31 | 0 | 0 | 12 | 0 | 12 | −12,00 | — |

`AUT` (2 técnicos de Banco fijo) sigue con la carga más alta relativa (una
dotación pequeña), pero dentro de capacidad. `TERCERO` es trabajo contratado
sin capacidad interna (% carga vacío). Casos preparados: feriado general el
miércoles de 2026-S31 (todas las especialidades caen) · rotación con cobertura
completa cada semana (ver §Rotación arriba y la sección ROTACIÓN de `--resumen`).

### ADHERENCIA esperada (REGLA-7, solo días hábiles)

2026-S29: 26/29 = 89,7 % (HH 197/227 = 86,8 %) · 2026-S30: 16/32 = 50,0 %
(HH 134/259 = 51,7 %) · 2026-S31 y S32: 0 %. Los conteos excluyen las órdenes
en día no laborable (se reportan en VALIDACION); el sábado es hábil (6.1).

### REGLA-9 esperada (meta: correctivo ≤ 20 %)

2026-S29: 0,25 (19,8 % → SI) · 2026-S30: 0,36 (26,5 % → NO, subió por las
correctivas de fin de semana) · 2026-S31: 0,20 (16,5 % → SI) · 2026-S32: 0,19
(16,3 % → SI).

### BACKLOG esperado (pendientes por tramo, al 2026-07-23)

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
| ORDENES sin par en EJECUCION (quedan `Pendiente`) | 40 |
| Órdenes con ajuste manual de horas (tblAjustes) | 2 |
| Desviación total de horas (ajustadas − ERP) | +2 |
| **Ajustes huérfanos (id no existe en ORDENES)** | **1** |
| **id_operacion duplicados dentro de tblAjustes** | **2** |

### Carga por técnico (gráfico, selector 2026-S30)

Capacidad semanal de cada técnico = 6,96 h/día × 6 días = **41,76 h** (48 h ×
0,87). HHA de la semana: Técnico 01 **32** (incluye el ajuste +4 h y la orden
del sábado) · 02: 20 · 03: 8 · 04: 13 · 05: 10 · 06: 8 · 07: 14 (MEC) · 08: 10 ·
09: 10 · 10: 11 · 11: 10 · 12: 16 · 13: 10 · 14: 8 (ELE) · 15: 27 · 16: 18
(AUT). **Ningún técnico supera su capacidad**, así que ninguna barra tiene tramo
rojo. El detalle diario de HHD sí puede quedar en rojo (p. ej. Técnico 01 el
día del ajuste: HHA 12, HHD 6,96 − 12 = **−5,04**): la capacidad es semanal, el
HHD es por día.

### Correo generado por EXPORTAR (filtro por defecto: semana 2026-S30)

Texto real producido en `EXPORTAR!A6` con los datos de muestra (recalculado):

```
Buenos días.
A continuación el programa de mantenimiento de Planta Ejemplo — Empresa Ejemplo S.A. para la semana 2026-S30, del 20/07/2026 al 26/07/2026.

Resumen de carga:
• Órdenes programadas: 34
• HH planificadas: 275 h
• Preventiva: 202 h (73%)
• Correctiva: 73 h (27%)
• Técnicos involucrados: 16

Tareas relevantes (top 5 por horas):
   • EQ-102 — Lubricación programada en EQ-102 · 10 h · Técnico 02
   • EQ-108 — Análisis predictivo en EQ-108 · 10 h · Técnico 13
   • EQ-106 — Reparación de falla en EQ-106 · 10 h · Técnico 12 · permiso de trabajo · bloqueo de energía (LOTO)
   … 

Programa completo:

Lunes:
   B · Técnico 02 · OT-0000160010 — Lubricación programada en EQ-102 (10 h)
   B · Técnico 07 · OT-0000210010 — Inspección de rutina en EQ-110 (6 h)
   T2 · Técnico 12 · OT-0000610010 — Lubricación programada en EQ-102 (6 h)
   …
Sábado:
   … (orden correctiva de fin de semana) …
Domingo:
   … (orden correctiva de fin de semana) …

Cualquier ajuste, favor comunicarlo antes del inicio del turno.
```

El turno que muestra cada línea del programa (`B`, `T2`, …) es el **turno
efectivo derivado de la rotación** (6.3), no un dato tecleado.

Números verificables a mano: **34** órdenes programadas (incluye 3 de fin de
semana → el programa recorre los 7 días), **275 h** = 202 preventiva (73 %) +
73 correctiva (27 %). Con la capacidad semanal en **41,76 h** ningún técnico
queda sobreasignado en 2026-S30, así que el **bloque de alerta condicional no
aparece** en el correo; se sigue verificando que desaparece limpio, sin
encabezado ni línea en blanco huérfana
(VERIFICACION.md §3.5).

### Calendario laboral: casos verificables a mano (v2.4)

Excepciones de muestra (además de 12 feriados generales del año): feriado de
planta el miércoles de 2026-S31 (2026-07-29), domingo laborable solo para
SERVICIOS (2026-08-02), paro de la sub-área Vapor el jueves de 2026-S30
(2026-07-23), y dos excepciones con área/sub-área fuera de catálogo.

| Caso | Resultado |
|---|---|
| **Feriado general** (mié 2026-07-29) | `horas_disponibles = 0` el miércoles para todos los técnicos activos. PERFIL_HH **MEC 2026-S31 cae de 336 a 280 h** disponibles (7 técnicos × 5 días × 8). La rotación no altera este efecto (solo cambia qué turno). |
| **Excepción por área** (dom 2026-08-02) | `es_habil(SERVICIOS)` = **sí**, `es_habil(PRODUCCION)` = **no**. La excepción por área da capacidad solo a SERVICIOS. |
| **Paro sub-área Vapor** (jue 2026-07-23) | `es_habil` = **no** para órdenes de Vapor; **sí** para PRODUCCION, EMPAQUE y Refrigeración. La excepción por sub-área no afecta a las demás sub-áreas. |
| **Orden que cruza fines de semana** (2026-06-08) | `backlog_dias` = **45**, `backlog_habiles` = **38**, diferencia **7** domingos no hábiles en medio (el sábado es hábil, 6.1). |
| **VALIDACION** | 11 órdenes en día no laborable · 1 excepción con área desconocida · 1 con sub-área desconocida. |

Los totales por área siguen cuadrando: la reconciliación COSTOS área = Σ
sub-áreas se mantiene (verificada dentro de las 11.409 comparaciones).

### Sub-áreas: agrupamiento con herencia (COSTOS real, USD)

Jerarquía de muestra y `costo_total` real por sub-área (suma de sus CECOs):

| área | sub-área | CECOs | costo_total |
|---|---|---|---:|
| PRODUCCION | *PRODUCCION* (heredado) | CC-110, CC-120 | 12.025 |
| EMPAQUE | *EMPAQUE* (heredado) | CC-210, CC-220 | 10.975 |
| SERVICIOS | Vapor | CC-310 + CC-311 | **6.020** |
| SERVICIOS | Refrigeración | CC-320 + CC-321 | 2.050 |
| SERVICIOS | CO2 | CC-330 | 200 |
| SERVICIOS | Aire comprimido | CC-340 | 160 |

Números verificables a mano: **Vapor = CC-310 (4.480) + CC-311 (1.540) =
6.020** en una sola fila con el nombre de proceso. **SERVICIOS = 6.020 + 2.050
+ 200 + 160 = 8.430**, que es exactamente el total del área SERVICIOS
(reconciliación). PRODUCCION y EMPAQUE, sin sub-área, reportan bajo el **nombre
de su área**, no bajo `CC-110`/`CC-210`.

### Otros números

Costos: `costo_plan` = horas **estimadas** × 25 (prev) / × 40 (corr) — el
costo plan es del ERP y no se recalcula con el ajuste manual; `precio` = 40 %
del plan (REGLA-8 → materiales 60 %); dos órdenes históricas con `precio >
plan` (materiales 0). Equipo de mayor gasto: EQ-110 (4.430 USD).

## Estructura del libro (24 hojas)

`INICIO` · `PARAMETROS` · `1_IMPORTAR_ORDENES` (paso único de pegado) ·
`2_IMPORTAR_EJECUCION` (`tblEjecucion`, 1.200 filas) · `ORDENES`
(`tblOrdenes`, 1.200 filas × 42 columnas: 12 importadas A:L, 5 editables en
azul, 26 calculadas incl. `es_habil` y `backlog_habiles`; `id_operacion` al
final) · `TECNICOS` (con `rotativo` y `orden_rotacion` para la rotación) ·
`ASIGNACIONES` (448 filas; rotación derivada `n_ciclo`/`posicion_ciclo`/
`turno_manual`/`turno` efectivo, `fecha`, REGLA-5 sobre el calendario y la
franja horaria `hora_inicio`/`hora_fin` desde `CAT_TURNOS`) · `AJUSTES`
(`tblAjustes`, 300 filas) · `CALENDARIO` (patrón
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
