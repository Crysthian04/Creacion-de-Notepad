# MantPlan — Entregable A: `MantPlan.xlsx`

Planificador semanal de mantenimiento reimplementado limpio: **sin macros, sin
enlaces externos, agnóstico de empresa y de ERP**. Las 10 reglas de negocio
están implementadas dos veces y verificadas una contra la otra:

1. Como **fórmulas** dentro del libro (`XLOOKUP` + referencias estructuradas).
2. Como **funciones puras de Python** en `generar_mantplan.py`
   (`regla_1_clasificacion` … `regla_10_validacion`), que además generan los
   datos sintéticos de ejemplo.

> El entregable B (`mantplan-web/`, con `src/domain/rules.ts`) queda pendiente
> y se hará como paso separado.

## Contenido de esta carpeta

| Archivo | Qué es | Cuándo usarlo |
|---|---|---|
| `MantPlan.xlsx` | Libro principal: `XLOOKUP` + referencias estructuradas | **Excel 2021 / Microsoft 365** |
| `MantPlan_compatible.xlsx` | Mismo libro y mismos datos con `INDEX/MATCH` + rangos A1 acotados | **Excel 2016 o anterior, y LibreOffice** |
| `generar_mantplan.py` | Motor de reglas en Python + generador determinista de ambos libros | — |
| `README.md` | Este documento | — |

Ambos libros llevan las mismas 200 órdenes sintéticas ancladas al
**2026-07-20** y producen números idénticos (verificado, ver §1).

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

Las fórmulas de un Excel generado por script no se pueden dar por buenas "a
ojo". El proceso de verificación fue:

- El mismo generador emite el libro en dos modos a partir de **las mismas
  plantillas de fórmula**: `estructuradas` (XLOOKUP, entregable) y
  `compatibles` (INDEX/MATCH + rangos A1 acotados).
- La variante compatible se recalculó con LibreOffice: **9.841 fórmulas, 0
  errores** (`#REF!`, `#VALUE!`, `#NAME?`, etc.).
- Cada valor recalculado se comparó contra el motor Python: **4.979
  comparaciones automáticas, 0 desviaciones** — las 21 columnas calculadas de
  las 200 órdenes (incluidas HHA/HHD), las 336 filas de REGLA-5, todo
  PERFIL_HH (REGLA-6 y 9), los 6 bloques de ADHERENCIA (REGLA-7), BACKLOG por
  tramos (REGLA-3), COSTOS por mes (REGLA-8), EQUIPOS_CRITICOS, los 9 chequeos
  de VALIDACION (REGLA-10) y la zona de datos del gráfico de carga de
  PLAN_SEMANAL.

Como ambos modos salen del mismo motor de plantillas (`class Refs`), verificar
la variante compatible verifica la lógica de la entregable; la única
diferencia es la función de búsqueda usada.

### 2. `XLOOKUP` y compatibilidad

- Los lookups del libro usan `XLOOKUP` con `si_no_encontrado` explícito, nunca
  `VLOOKUP` dentro de `IFERROR`. En el XML se almacena como `_xlfn.XLOOKUP`,
  que es la forma canónica con la que Excel guarda las funciones
  posteriores a 2007 (la interfaz oculta el prefijo).
- **Requiere Excel 2021 o Microsoft 365.** Para Excel 2016 o anterior y para
  LibreOffice (< 24.8 no evalúa `XLOOKUP`) está **`MantPlan_compatible.xlsx`**,
  versionado en esta carpeta desde v1.2.0: mismo libro, mismos datos, cero
  `XLOOKUP` (solo `INDEX/MATCH` + rangos A1 acotados). La hoja
  `_COMPATIBILIDAD` del libro principal documenta además el equivalente
  `INDEX/MATCH` de cada lookup con un ejemplo vivo.

### 3. Cálculo automático y caché de resultados

El libro se entrega con `fullCalcOnLoad` activado: **Excel recalcula todo al
abrirlo** (cálculo automático, nunca manual). openpyxl escribe fórmulas sin
caché de resultados, así que un visor que no calcule (una vista previa web,
`pandas`) mostrará vacías las celdas calculadas; en Excel aparecen al abrir.

### 4. Sustitutos sin macros (y sin XML a mano)

| Requisito original | Implementación |
|---|---|
| Tabla dinámica en ADHERENCIA | Matrices de `COUNTIFS`/`SUMIFS` + gráfico de línea contra la meta. openpyxl no puede construir cachés de pivote; las fórmulas dan el mismo resultado, se recalculan solas y no dependen de "actualizar" |
| Segmentaciones (slicers) | Autofiltro en cada tabla + selectores desplegables con criterio `"(todos)"` en `PLAN_SEMANAL` y `EXPORTAR`. openpyxl no genera `slicerCache` |
| Impresión por turno/coordinador | Área de impresión definida en `PLAN_SEMANAL` (horizontal, ajustada a ancho) sobre la vista filtrada |
| Correo Outlook | Hoja `EXPORTAR`: arma el texto del plan con `TEXTJOIN` listo para copiar |
| Abrir checklist con doble clic | Columna `abrir_checklist` con `HYPERLINK(ruta_base & link_checklist)` |

### 5. Ajustes al modelo de datos (todos aditivos, documentados)

- **`clave` en `tblAsignaciones`** (`semana|dia|tecnico`): columna calculada
  auxiliar porque Excel no tiene lookup multi-criterio limpio sin fórmulas
  matriciales. Es la clave compuesta que el propio modelo define.
- **`abrir_checklist` en `tblOrdenes`**: separa el dato editable
  (`link_checklist`, ruta relativa) del hipervínculo calculado.
- **`linea` en `tblCECO`**: la Tabla 1 exige `ORDENES.linea` por lookup a
  CENTROS_COSTO, pero la Tabla 5 no traía ese campo; se añadió al catálogo.
- **`id_operacion` = `orden & operacion`** con default `"0010"` si la
  operación viene vacía. El `LPAD(operacion, 2)` del enunciado se descartó por
  inconsistente con operaciones de 4 caracteres (`"0010"`); truncaría la clave.
- **`costo_servicio` = `precio` de EJECUCION.** El enunciado solo dice "lookup
  EJECUCION"; se deriva de REGLA-8: si `materiales = plan_total − precio`,
  el componente servicio es `precio`.
- **`coordinador`** se resuelve por centro de costo (cada CECO tiene
  coordinador en el catálogo). El "+ puesto" del enunciado implicaría una
  matriz CECO × especialidad que el modelo no define; queda para B si se
  especifica.

### 6. Semana ISO y primer día de semana

`ISOWEEKNUM` implementa REGLA-2 (con el pliegue S53 → S1) y asume semana ISO
que empieza en lunes; `WEEKDAY(fecha, 2)` alinea `1 = lunes` con la lista
`lista_dias`. El parámetro `primer_dia_semana` queda declarado con default
`lunes`; cambiarlo a otro convenio es lógica del entregable B (en Excel
implicaría sustituir la pareja ISOWEEKNUM/WEEKDAY).

### 7. `backlog_dias` usa `HOY()`

Tal como exige el modelo. Consecuencia: FUTURO / MES CORRIENTE / BACKLOG se
mueven con la fecha real en que se abra el archivo. Los datos de ejemplo están
anclados al **2026-07-20**; si los números relativos al día cambian, regenere
con `--fecha-ancla 2026-07-20` o verifique contra `--resumen` del mismo día.

### 8. v1.1.0 / v1.2.0 — HHA/HHD y gráfico de carga por técnico

**Columnas `HHA` y `HHD` en `tblOrdenes`** (calculadas, mismo valor repetido
en todas las filas del mismo técnico/semana/día):

- `HHA` = `SUMIFS(horas_estimadas; tecnico_asignado; semana; dia_semana)` con
  referencias estructuradas — total de horas asignadas al técnico ese día.
- `HHD` = `factor_productividad × horas_disponibles − HHA`, donde
  `horas_disponibles` se busca en `tblAsignaciones` por la clave
  `semana|dia|tecnico` (con 0 si no hay asignación). Es la **misma fuente que
  la línea de capacidad del gráfico**, así que HHD respeta la disponibilidad
  real del técnico (REGLA-5): con turno normal la capacidad diaria es 7 ×
  0,87 = **6,09 h**; con `VAC`/`X` o sin asignación es 0 y **HHD = −HHA**.
  Puede ser negativa: **HHD < 0 se marca en rojo** con formato condicional =
  técnico sobreasignado ese día. *(Corregido en v1.2.0: antes usaba
  `horas_jornada × factor` fijo e ignoraba vacaciones y ausencias.)*
- Ambas quedan vacías en órdenes sin técnico asignado.
- Los datos de ejemplo incluyen un conflicto deliberado para probarlo:
  **OT-000026** está asignada al Técnico 04 en su semana de vacaciones
  (S31, turno "VAC") → HHA 10, **HHD = −10,00**.

**Gráfico de carga en `PLAN_SEMANAL`**, fijo en la parte superior de la hoja
(paneles inmovilizados en la fila de datos de la grilla: selectores, gráfico y
encabezados no se mueven al desplazarse):

- Barras verticales **apiladas** por técnico: porción **verde** = dentro de
  capacidad (`MIN(HHA_sel, capacidad)`), porción **roja** = sobreasignación
  (`MAX(0, HHA_sel − capacidad)`). Etiquetas de datos visibles en ambas
  series, ceros incluidos (un técnico sin carga muestra "0" de inmediato).
- **Serie de línea de capacidad** = `factor_productividad × Σ
  horas_disponibles` del técnico en la selección (REGLA-5). Con un día
  concreto seleccionado eso es exactamente `horas_jornada ×
  factor_productividad` (6,09) salvo vacaciones/ausencia (0); con día
  "(todos)" escala a la semana completa (30,45 h con 5 días), manteniendo la
  línea comparable con las barras. *(v1.2.0: la línea va combinada sobre el
  **mismo eje de valores** que las barras apiladas — `bar += line` en
  openpyxl con ejes compartidos —, con marcador circular visible y sin
  etiquetas de datos; en v1.1.0 iba a un eje secundario oculto y Excel no la
  dibujaba.)*
- Eje de categorías: técnicos **ordenados por especialidad** (MEC → ELE → AUT
  → OP); la etiqueta añade el turno (`Técnico 01 (T1)`) cuando hay semana y
  día concretos seleccionados, porque el turno depende del día.
- **Conectado a los mismos selectores que filtran la grilla** (semana, día,
  turno, coordinador, área y especialidad — este último se añadió en v1.1.0
  también a la grilla): la zona de datos `P3:V15` recalcula con `SUMIFS` al
  cambiar cualquier selector y el gráfico se redibuja. Al filtrar por
  especialidad, los técnicos de otras especialidades se excluyen con `NA()`
  (sin barra ni etiqueta, como haría un pivote).

**Por qué no es un PivotChart OOXML:** openpyxl no puede construir
`pivotCacheDefinition`, `pivotCacheRecords` ni `slicerCache` (§4). Escribir
ese XML a mano sería frágil e inverificable con las herramientas de este
repositorio. El gráfico por fórmulas entrega el mismo comportamiento
(actualización con cada filtro) con el mismo mecanismo sin macros del resto
del libro, y sí es verificable: sus celdas se comparan contra el motor Python.
Nota: los "slicers" de este libro son los selectores desplegables de la fila 3
(el sustituto documentado desde v1.0.0).

### 9. Higiene de fórmulas

Prohibidos y ausentes (auditado por script sobre el archivo final): `OFFSET`,
`INDIRECT`, referencias de columna completa (`A:A`), enlaces externos, VBA y
nombres definidos huérfanos. Los 12 nombres definidos (`p_*` para parámetros,
`lista_*` para listas de validación) se usan todos en fórmulas o validaciones.

## Datos de ejemplo y verificación a mano

200 órdenes · 163 filas de ejecución (3 huérfanas a propósito) · 12 técnicos ·
336 asignaciones · 4 semanas de plan **S29–S32** (ancla 2026-07-20).

### PERFIL_HH esperado (REGLA-6) — jornada 7 h, productividad 0,87

Cuenta rápida de referencia: **MEC S29 = 4 técnicos × 5 días × 7 h = 140 h
disponibles; × 0,87 = 121,8 productivas; 82 prev + 20 corr = 102 planificadas;
holgura 19,8; carga 102/121,8 = 83,7 % → verde.**

| esp | semana | disp | prod | prev | corr | plan | holgura | % carga |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| MEC | S29 | 140 | 121,80 | 82 | 20 | 102 | 19,80 | 83,7 % 🟢 |
| MEC | S30 | 140 | 121,80 | 80 | 25 | 105 | 16,80 | 86,2 % 🟡 |
| MEC | S31 | 105 | 91,35 | 80 | 20 | 100 | −8,65 | **109,5 % 🔴** |
| MEC | S32 | 140 | 121,80 | 72 | 14 | 86 | 35,80 | 70,6 % 🟢 |
| ELE | S29 | 105 | 91,35 | 60 | 15 | 75 | 16,35 | 82,1 % 🟢 |
| ELE | S30 | 98 | 85,26 | 65 | 20 | 85 | 0,26 | 99,7 % 🟡 |
| ELE | S31 | 105 | 91,35 | 60 | 10 | 70 | 21,35 | 76,6 % 🟢 |
| ELE | S32 | 105 | 91,35 | 52 | 10 | 62 | 29,35 | 67,9 % 🟢 |
| AUT | S29 | 70 | 60,90 | 40 | 10 | 50 | 10,90 | 82,1 % 🟢 |
| AUT | S30 | 70 | 60,90 | 45 | 10 | 55 | 5,90 | 90,3 % 🟡 |
| AUT | S31 | 70 | 60,90 | 35 | 7 | 42 | 18,90 | 69,0 % 🟢 |
| AUT | S32 | 70 | 60,90 | 30 | 6 | 36 | 24,90 | 59,1 % 🟢 |
| OP | S29 | 105 | 91,35 | 30 | 8 | 38 | 53,35 | 41,6 % 🟢 |
| OP | S30 | 105 | 91,35 | 36 | 9 | 45 | 46,35 | 49,3 % 🟢 |
| OP | S31 | 105 | 91,35 | 28 | 9 | 37 | 54,35 | 40,5 % 🟢 |
| OP | S32 | 105 | 91,35 | 24 | 6 | 30 | 61,35 | 32,8 % 🟢 |
| TERCERO | S30 | 0 | 0 | 16 | 0 | 16 | −16,00 | — |
| TERCERO | S31 | 0 | 0 | 12 | 0 | 12 | −12,00 | — |

Casos preparados a propósito:

- **TEC-04 (MEC) de vacaciones toda la S31** (`VAC` → REGLA-5 = 0 h): MEC baja
  de 140 a 105 h disponibles y la carga se dispara a 109,5 % (rojo).
- **TEC-07 (ELE) ausente el viernes de S30** (`X`): ELE 98 h en vez de 105.
- **TERCERO** no tiene capacidad interna (sin filas en ASIGNACIONES): la
  columna `% carga` queda vacía (denominador 0 protegido).

### ADHERENCIA esperada por semana (REGLA-7)

| semana | cerradas/total | conteo | HH cerradas/total | horas |
|---|---|---:|---|---:|
| S29 | 30/34 | 88,2 % | 229/265 | 86,4 % |
| S30 | 19/37 | 51,4 % | 161/306 | 52,6 % |
| S31 | 0/33 | 0,0 % | 0/261 | 0,0 % |
| S32 | 0/29 | 0,0 % | 0/214 | 0,0 % |

### REGLA-9 esperada (meta: correctivo ≤ 20 %)

S29: ratio 0,25 (20,0 % → SI) · S30: 0,26 (20,9 % → NO) · S31: 0,21 (17,6 % →
SI) · S32: 0,20 (16,8 % → SI).

### BACKLOG esperado (pendientes por tramo, al 2026-07-20)

0–30: 9 órdenes / 75 h · 31–60: 21 / 80 h · 61–90: 9 / 48 h · **>90: 14 /
80 h** (resaltadas en rojo). El tramo 0–30 depende del día en que se abra el
libro (`HOY()`, §7): con el ancla en lunes solo la semana pasada aporta
pendientes recientes.

### VALIDACION esperada (REGLA-10)

| chequeo | resultado |
|---|---:|
| Duplicadas por `id_operacion` (OT-000900) | 2 |
| Sin fecha de inicio (OT-000901/902) | 2 |
| Sin horas estimadas (OT-000903/904) | 2 |
| Centro de costo fuera de catálogo (CC-999) | 1 |
| Puesto fuera de catálogo (PU-XXX) | 1 |
| Actividad fuera de catálogo (ACT-99) | 1 |
| Tipo de OT fuera de catálogo (TIPO-X9 → `sin_clasificar`) | 2 |
| EJECUCION sin par en ORDENES (OT-000990/991/992) | 3 |
| ORDENES sin par en EJECUCION (quedan `Pendiente`) | 39 |

### Caso manual de HHA/HHD y del gráfico de carga (v1.1.0/v1.2.0)

**Técnico 01 (MEC), semana S30** — capacidad diaria con turno normal =
7 × 0,87 = **6,09 h**:

| día | órdenes asignadas | HHA | HHD | color |
|---|---|---:|---:|---|
| lunes | 6 h | 6 | **+0,09** | — |
| martes | 8 h | 8 | **−1,91** | 🔴 |
| miércoles | 10 h | 10 | **−3,91** | 🔴 |
| jueves | (sin órdenes) | — | — | — |
| viernes | 7 h | 7 | **−0,91** | 🔴 |

Compruébelo filtrando `ORDENES` por `tecnico_asignado = Técnico 01` y
`semana = S30`: todas las filas del martes repiten HHA = 8 y HHD = −1,91 en
rojo. El caso extremo es **OT-000026** (Técnico 04, S31 lunes, turno "VAC"):
disponibilidad 0 → HHA 10 y **HHD = −10,00** — la sobreasignación es la orden
completa porque el técnico está de vacaciones.

**El gráfico refleja los mismos números.** Con los selectores por defecto
(semana = S30, resto "(todos)") la barra de cada técnico suma su HHA semanal
contra la capacidad de la semana (30,45 h = 5 días × 7 h × 0,87), y la línea
de capacidad con marcadores pasa por esos mismos valores:

| técnico | HHA S30 | capacidad | verde (dentro) | rojo (sobre) |
|---|---:|---:|---:|---:|
| Técnico 01 (MEC) | **31** = 6+8+10+7 | 30,45 | 30,45 | **0,55** |
| Técnico 02 (MEC) | 22 | 30,45 | 22 | 0 |
| Técnico 03 (MEC) | 26 | 30,45 | 26 | 0 |
| Técnico 04 (MEC) | 18 | 30,45 | 18 | 0 |
| Técnico 05 (ELE) | 22 | 30,45 | 22 | 0 |
| Técnico 06 (ELE) | **40** | 30,45 | 30,45 | **9,55** |
| Técnico 07 (ELE) | 15 | **24,36** | 15 | 0 |
| Técnico 08 (AUT) | 27 | 30,45 | 27 | 0 |
| Técnico 09 (AUT) | 18 | 30,45 | 18 | 0 |
| Técnico 10 (OP) | 20 | 30,45 | 20 | 0 |
| Técnico 11 (OP) | 10 | 30,45 | 10 | 0 |
| Técnico 12 (OP) | 15 | 30,45 | 15 | 0 |

Detalles que amarran el caso: Técnico 06 es el sobreasignado visible de la
semana (porción roja de 9,55); Técnico 07 tiene capacidad 24,36 = 4 días ×
6,09 por su ausencia "X" del viernes (REGLA-5); las etiquetas muestran la
porción de cada serie (Técnico 01: "30,45" en verde y "0,55" en rojo — la
altura total de la barra es su HHA = 31). Si además selecciona día = lunes,
la línea de capacidad baja a 6,09 y la barra de Técnico 01 marca 6.

### Otros números verificables

- **Costos redondos:** `costo_plan` = horas × 25 USD (preventiva) o × 40 USD
  (correctiva). En EJECUCION, `precio` (servicio) = 40 % del plan ⇒ REGLA-8 da
  materiales = 60 % del plan. Dos órdenes históricas tienen `precio >
  costo_plan_total` para probar el `MAX(0, …)` (ids impresos por `--resumen`).
- **REGLA-2, pliegue S53 → S1:** hay una orden preventiva el 2026-12-29
  (semana ISO 53) que el libro publica como `S1`.
- **Equipo de mayor gasto:** EQ-110 con 5.070 USD de `costo_total`.

## Estructura del libro (21 hojas)

`INICIO` · `PARAMETROS` (Tabla 10 + listas de validación + nombres `p_*`) ·
`1_IMPORTAR_ORDENES` · `2_IMPORTAR_EJECUCION` (aloja `tblEjecucion`) ·
`ORDENES` (`tblOrdenes`, 39 columnas: 12 importadas, 5 editables en azul, 22
calculadas incl. HHA/HHD) · `TECNICOS` · `ASIGNACIONES` (turno por
desplegable, REGLA-5) · `PERFIL_HH` (REGLA-6 + matriz semáforo + REGLA-9) ·
`PLAN_SEMANAL` (6 selectores + gráfico de carga fijo + autofiltro + área de
impresión) · `ADHERENCIA` (REGLA-7, 6 desgloses +
gráfico vs meta) · `COSTOS` (REGLA-8, plan/real/desvío por área y línea, por
mes + gráfico) · `BACKLOG` (REGLA-3, tramos 0-30/31-60/61-90/>90) ·
`EQUIPOS_CRITICOS` (equipo × mes) · `VALIDACION` (REGLA-10) · 5 catálogos
`CAT_*` · `EXPORTAR` · `_COMPATIBILIDAD`.

Formato condicional obligatorio implementado: semáforo de carga en PERFIL_HH,
escala <90/90–95/>95 en ADHERENCIA, backlog > 90 días en rojo (ORDENES y
BACKLOG), órdenes del plan sin técnico en amarillo (ORDENES) y HHD negativa
en rojo (ORDENES, sobreasignación).

## Limitaciones conocidas

- `XLOOKUP` exige Excel 2021/365 en el libro principal; para Excel 2016 y
  LibreOffice use `MantPlan_compatible.xlsx` (versionado en esta carpeta).
- Sin caché de resultados hasta el primer abrir-y-guardar en Excel (§3).
- Slicers y tablas dinámicas nativas quedan fuera del alcance de un libro
  generado sin macros (§4); la web (entregable B) cubre esa interactividad.
