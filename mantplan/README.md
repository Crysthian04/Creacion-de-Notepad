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

| Archivo | Qué es |
|---|---|
| `MantPlan.xlsx` | El libro entregable, con 200 órdenes sintéticas ancladas al **2026-07-19** |
| `generar_mantplan.py` | Motor de reglas en Python + generador determinista del libro |
| `README.md` | Este documento |

## Cómo regenerarlo

```bash
pip install openpyxl
python generar_mantplan.py                       # MantPlan.xlsx (XLOOKUP + refs estructuradas)
python generar_mantplan.py --fecha-ancla 2026-07-19   # fija el "hoy" de los datos de ejemplo
python generar_mantplan.py --refs compatibles    # variante INDEX/MATCH + rangos A1
python generar_mantplan.py --resumen             # imprime todos los números esperados
```

## Decisiones técnicas

### 1. Verificación: doble implementación + recálculo real

Las fórmulas de un Excel generado por script no se pueden dar por buenas "a
ojo". El proceso de verificación fue:

- El mismo generador emite el libro en dos modos a partir de **las mismas
  plantillas de fórmula**: `estructuradas` (XLOOKUP, entregable) y
  `compatibles` (INDEX/MATCH + rangos A1 acotados).
- La variante compatible se recalculó con LibreOffice: **9.181 fórmulas, 0
  errores** (`#REF!`, `#VALUE!`, `#NAME?`, etc.).
- Cada valor recalculado se comparó contra el motor Python: **4.519
  comparaciones automáticas, 0 desviaciones** — las 19 columnas calculadas de
  las 200 órdenes, las 336 filas de REGLA-5, todo PERFIL_HH (REGLA-6 y 9),
  los 6 bloques de ADHERENCIA (REGLA-7), BACKLOG por tramos (REGLA-3),
  COSTOS por mes (REGLA-8), EQUIPOS_CRITICOS y los 9 chequeos de VALIDACION
  (REGLA-10).

Como ambos modos salen del mismo motor de plantillas (`class Refs`), verificar
la variante compatible verifica la lógica de la entregable; la única
diferencia es la función de búsqueda usada.

### 2. `XLOOKUP` y compatibilidad

- Los lookups del libro usan `XLOOKUP` con `si_no_encontrado` explícito, nunca
  `VLOOKUP` dentro de `IFERROR`. En el XML se almacena como `_xlfn.XLOOKUP`,
  que es la forma canónica con la que Excel guarda las funciones
  posteriores a 2007 (la interfaz oculta el prefijo).
- **Requiere Excel 2021 o Microsoft 365.** Para Excel 2016 o anterior: la hoja
  `_COMPATIBILIDAD` documenta el equivalente `INDEX/MATCH` de cada lookup con
  un ejemplo vivo, y `--refs compatibles` regenera el libro completo en esa
  variante. LibreOffice < 24.8 tampoco evalúa `XLOOKUP`; para esos entornos
  vale la misma variante.

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
anclados al **2026-07-19**; si los números relativos al día cambian, regenere
con `--fecha-ancla 2026-07-19` o verifique contra `--resumen` del mismo día.

### 8. Higiene de fórmulas

Prohibidos y ausentes (auditado por script sobre el archivo final): `OFFSET`,
`INDIRECT`, referencias de columna completa (`A:A`), enlaces externos, VBA y
nombres definidos huérfanos. Los 12 nombres definidos (`p_*` para parámetros,
`lista_*` para listas de validación) se usan todos en fórmulas o validaciones.

## Datos de ejemplo y verificación a mano

200 órdenes · 163 filas de ejecución (3 huérfanas a propósito) · 12 técnicos ·
336 asignaciones · 4 semanas de plan **S28–S31** (ancla 2026-07-19).

### PERFIL_HH esperado (REGLA-6) — jornada 7 h, productividad 0,87

Cuenta rápida de referencia: **MEC S28 = 4 técnicos × 5 días × 7 h = 140 h
disponibles; × 0,87 = 121,8 productivas; 82 prev + 20 corr = 102 planificadas;
holgura 19,8; carga 102/121,8 = 83,7 % → verde.**

| esp | semana | disp | prod | prev | corr | plan | holgura | % carga |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| MEC | S28 | 140 | 121,80 | 82 | 20 | 102 | 19,80 | 83,7 % 🟢 |
| MEC | S29 | 140 | 121,80 | 80 | 25 | 105 | 16,80 | 86,2 % 🟡 |
| MEC | S30 | 105 | 91,35 | 80 | 20 | 100 | −8,65 | **109,5 % 🔴** |
| MEC | S31 | 140 | 121,80 | 72 | 14 | 86 | 35,80 | 70,6 % 🟢 |
| ELE | S28 | 105 | 91,35 | 60 | 15 | 75 | 16,35 | 82,1 % 🟢 |
| ELE | S29 | 98 | 85,26 | 65 | 20 | 85 | 0,26 | 99,7 % 🟡 |
| ELE | S30 | 105 | 91,35 | 60 | 10 | 70 | 21,35 | 76,6 % 🟢 |
| ELE | S31 | 105 | 91,35 | 52 | 10 | 62 | 29,35 | 67,9 % 🟢 |
| AUT | S28 | 70 | 60,90 | 40 | 10 | 50 | 10,90 | 82,1 % 🟢 |
| AUT | S29 | 70 | 60,90 | 45 | 10 | 55 | 5,90 | 90,3 % 🟡 |
| AUT | S30 | 70 | 60,90 | 35 | 7 | 42 | 18,90 | 69,0 % 🟢 |
| AUT | S31 | 70 | 60,90 | 30 | 6 | 36 | 24,90 | 59,1 % 🟢 |
| OP | S28 | 105 | 91,35 | 30 | 8 | 38 | 53,35 | 41,6 % 🟢 |
| OP | S29 | 105 | 91,35 | 36 | 9 | 45 | 46,35 | 49,3 % 🟢 |
| OP | S30 | 105 | 91,35 | 28 | 9 | 37 | 54,35 | 40,5 % 🟢 |
| OP | S31 | 105 | 91,35 | 24 | 6 | 30 | 61,35 | 32,8 % 🟢 |
| TERCERO | S29 | 0 | 0 | 16 | 0 | 16 | −16,00 | — |
| TERCERO | S30 | 0 | 0 | 12 | 0 | 12 | −12,00 | — |

Casos preparados a propósito:

- **TEC-04 (MEC) de vacaciones toda la S30** (`VAC` → REGLA-5 = 0 h): MEC baja
  de 140 a 105 h disponibles y la carga se dispara a 109,5 % (rojo).
- **TEC-07 (ELE) ausente el viernes de S29** (`X`): ELE 98 h en vez de 105.
- **TERCERO** no tiene capacidad interna (sin filas en ASIGNACIONES): la
  columna `% carga` queda vacía (denominador 0 protegido).

### ADHERENCIA esperada por semana (REGLA-7)

| semana | cerradas/total | conteo | HH cerradas/total | horas |
|---|---|---:|---|---:|
| S28 | 30/34 | 88,2 % | 229/265 | 86,4 % |
| S29 | 19/37 | 51,4 % | 161/306 | 52,6 % |
| S30 | 0/33 | 0,0 % | 0/261 | 0,0 % |
| S31 | 0/29 | 0,0 % | 0/214 | 0,0 % |

### REGLA-9 esperada (meta: correctivo ≤ 20 %)

S28: ratio 0,25 (20,0 % → SI) · S29: 0,26 (20,9 % → NO) · S30: 0,21 (17,6 % →
SI) · S31: 0,20 (16,8 % → SI).

### BACKLOG esperado (pendientes por tramo, al 2026-07-19)

0–30: 22 órdenes / 181 h · 31–60: 21 / 80 h · 61–90: 9 / 48 h · **>90: 14 /
80 h** (resaltadas en rojo).

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
`ORDENES` (`tblOrdenes`, 37 columnas: 12 importadas, 5 editables en azul, 20
calculadas) · `TECNICOS` · `ASIGNACIONES` (turno por desplegable, REGLA-5) ·
`PERFIL_HH` (REGLA-6 + matriz semáforo + REGLA-9) · `PLAN_SEMANAL` (selectores
+ autofiltro + área de impresión) · `ADHERENCIA` (REGLA-7, 6 desgloses +
gráfico vs meta) · `COSTOS` (REGLA-8, plan/real/desvío por área y línea, por
mes + gráfico) · `BACKLOG` (REGLA-3, tramos 0-30/31-60/61-90/>90) ·
`EQUIPOS_CRITICOS` (equipo × mes) · `VALIDACION` (REGLA-10) · 5 catálogos
`CAT_*` · `EXPORTAR` · `_COMPATIBILIDAD`.

Formato condicional obligatorio implementado: semáforo de carga en PERFIL_HH,
escala <90/90–95/>95 en ADHERENCIA, backlog > 90 días en rojo (ORDENES y
BACKLOG) y órdenes del plan sin técnico en amarillo (ORDENES).

## Limitaciones conocidas

- `XLOOKUP` exige Excel 2021/365 (mitigado con `_COMPATIBILIDAD` y
  `--refs compatibles`).
- Sin caché de resultados hasta el primer abrir-y-guardar en Excel (§3).
- Slicers y tablas dinámicas nativas quedan fuera del alcance de un libro
  generado sin macros (§4); la web (entregable B) cubre esa interactividad.
