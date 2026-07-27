# VERIFICACION.md — MantPlan v3.0.0 (cierre del entregable A)

Reporte de verificación del entregable A. Esta versión añade **§7 — banco de
prueba**: volumen de un año en crudo + una ventana programada, como OPCIÓN del
generador. Sobre 6.5/6.6 (seguimiento y supervisor), 6.4 (VAC), 6.3 (rotación),
6.2 (CAT_TURNOS), 6.1 (jornada 8 h), v2.4 (calendario), v2.3 (sub_area), v2.2
(EXPORTAR), v2.1 y v2.0. Corridas: dataset por defecto con ancla **2026-07-27**;
banco con ancla FIJA **2026-11-02**.

## 0. §7 — Banco de prueba: un año en crudo + ventana programada

Cambio de **datos y de opciones del generador**: no toca las 10 reglas, ni la
rotación, ni VAC, ni el seguimiento, ni la capacidad. Se activa con
`--anio-completo`; **sin flags el generador produce exactamente el dataset de 4
semanas de siempre** (verificado, punto 17). Ancla FIJA (2026): el banco nunca
depende de `date.today()`.

### Volumen y agilidad (puntos 3, 4 y 16 — medidos)

| Métrica | Dataset por defecto | Banco §7 |
|---|---:|---:|
| Órdenes (`1_IMPORTAR_ORDENES`) | 200 | **1.000** |
| Notificaciones (`2_IMPORTAR_EJECUCION`) | 162 | **851** |
| Filas de ASIGNACIONES | 448 | **5.936** (53 semanas ISO × 16 técnicos × 7 días) |
| Hojas | 27 | **28** (añade `_BANCO_PRUEBA`) |
| Fórmulas recalculadas | 74.182 | **145.546** |
| Errores de fórmula | **0** | **0** |
| Tiempo de generación | 2,6 s | **29,6 s** |
| Tiempo de recálculo (LibreOffice) | ~10 s | **26,5 s** |
| Tamaño (variante compatible) | 0,99 MB | **2,19 MB** |

**El recálculo NO se vuelve impracticable**: 26,5 s para 145.546 fórmulas, muy
por debajo del límite de 595 s. No hizo falta recortar volumen. Los tipos de
trabajo salen de los catálogos (`CAT_TIPOS_OT` × `CAT_ACTIVIDADES`, con
`ACT-06 Overhaul mayor` añadido **al catálogo**), nunca hardcodeados.

**Determinismo (punto 2)**: dos generaciones con la misma semilla dan la misma
huella SHA-256 de las 1.000 órdenes (`7f7a0c1f9707f87f`); con `--semilla 777`
cambia (`31a7ac4cc2f5c554`). Los flags `--n-ordenes` y `--semanas-programadas`
responden (400 órdenes / ventana de 2 semanas, comprobado).

### (12) CONTRASTE VALIDACION ↔ MANIFIESTO — caso por caso

Leído del **libro recalculado** contra la hoja `_BANCO_PRUEBA`. REGLA-10
**reporta, nunca bloquea**: las 1.000 órdenes se importan igual.

| chequeo de VALIDACION | libro | manifiesto | |
|---|---:|---:|---|
| Órdenes duplicadas por `id_operacion` | 6 | 6 | OK |
| Órdenes sin fecha de inicio | 4 | 4 | OK |
| Órdenes sin horas estimadas | 4 | 4 | OK |
| Centros de costo fuera de catálogo | 3 | 3 | OK |
| Puestos de trabajo fuera de catálogo | 3 | 3 | OK |
| Actividades fuera de catálogo | 3 | 3 | OK |
| Tipos de OT fuera de catálogo | 3 | 3 | OK |
| EJECUCION sin par en ORDENES | 5 | 5 | OK |
| ORDENES sin par en EJECUCION | 151 | 151 | OK |
| Órdenes con ajuste manual | 5 | 5 | OK |
| Desviación total de horas | +4 | +4 | OK |
| Ajustes huérfanos | 2 | 2 | OK |
| `id_operacion` duplicados en tblAjustes | 4 | 4 | OK |
| Órdenes en día NO laborable | 13 | 13 | OK |
| Excepciones con área desconocida | 1 | 1 | OK |
| Excepciones con sub-área desconocida | 1 | 1 | OK |

Los 13 del día no laborable se descomponen en **6 domingos + 4 feriados + 3 del
paro de la sub-área Vapor**, sembrados a propósito.

### (13) Ventana programada coherente

Ventana **2026-S45 … 2026-S48** (2026-11-02 → 2026-11-29), leída del libro
recalculado:

- **190 órdenes programadas** y **75 de remanente sin técnico** (remanente
  deliberado: hay picos tipo parada que no caben en la jornada productiva).
- **0** órdenes con especialidad equivocada.
- **0** órdenes asignadas a técnico en VAC, en domingo o en día no hábil.
- **0** técnico-día por encima de la capacidad productiva (**6,96 h**).

Las 3 órdenes sembradas **mal asignadas a técnicos de vacaciones** están
**fuera** de la ventana a propósito: la ventana debe quedar coherente (§13) y ese
caso documenta el error humano que VALIDACION expone.

### (14) Año ISO: 2026-S53 y 2027-S01 no se pliegan

Del libro recalculado: `2026-12-29 → 2026-S53 (anio 2026)`, `2027-01-01 →
2026-S53 (anio 2027)`, `2027-01-05 → 2027-S01 (anio 2027)`. Las dos etiquetas
aparecen como semanas **distintas** en la serie de PERFIL_HH/ADHERENCIA.

### (15) Rotación, superávit y adherencia a volumen de año

- **Cobertura** 1 T1 / 1 T2 / 1 T3 / N−3 en Banco por posición derivada en las
  **53 semanas ISO × 2 ciclos** (MEC y ELE en PRODUCCION), con **13 huecos por
  VAC** (técnico-semana) que caen exactamente donde el técnico está de vacaciones.
- **Superávit/déficit** coherente: `horas_reales − 48` en todas las filas de
  `SEGUIMIENTO_HH`.
- **Adherencia** excluye del denominador las 13 órdenes en día no hábil, y da un
  número creíble: **88,2 % de media** en las semanas vencidas, con variación
  semanal de **71 % a 100 %** (ni 0 % ni 100 % plano).
- **Semanas sobrecargadas** sembradas: MEC 2026-S13 al **117 %** y ELE 2026-S34
  al **119 %** de carga; más 2 semanas casi vacías.

### (11) Comparación motor Python ↔ Excel recalculado (banco)

**59.553 comparaciones, 0 desviaciones**: las columnas calculadas de las 1.000
órdenes, las 5.936 filas de ASIGNACIONES (posición de ciclo, VAC, turno efectivo,
REGLA-5, supervisor, domingo trabajado), PERFIL_HH y ADHERENCIA de las 54 semanas
de la serie, `SEGUIMIENTO_HH`/`SEGUIMIENTO_MENSUAL`, los 16 chequeos de
VALIDACION y el manifiesto `_BANCO_PRUEBA`.

**Salvedad honesta (envejecimiento con `HOY()`)**: `backlog_dias`,
`backlog_habiles`, `estado_backlog` y `en_plan` usan `HOY()` en el libro **por
diseño** (REGLA-3/REGLA-4), así que en un banco de ancla FIJA no pueden coincidir
con el ancla salvo que se abra el archivo ese mismo día. Se verificaron contra el
**día real del recálculo**, inferido del propio libro (`fecha + backlog_dias`) y
exigiendo que sea **el mismo para las 1.000 órdenes**: así se verifica la fórmula
y queda documentado el desfase (el recálculo corrió con `HOY() = 2026-07-27`,
−98 días respecto del ancla del banco). El resto de columnas es independiente del día.

### (17) El dataset por defecto no cambió

Sin flags, el generador sigue produciendo el dataset de 4 semanas: **74.182
fórmulas, 0 errores** y **14.178 comparaciones, 0 desviaciones**, idéntico a
6.5+6.6. El refactor que comparte el bucle de ASIGNACIONES entre ambos modos y la
derivación del lunes desde la etiqueta ISO no alteraron ningún valor.

**Qué NO verifiqué / supuestos.** (i) No recalculé los libros principales
(`XLOOKUP`): LibreOffice no los evalúa; corrección heredada del modo compatible.
(ii) Las **851 notificaciones** no llegan a 1.000 porque la regla realista del
punto 8 manda: solo se emparejan con órdenes ya vencidas o de la ventana en curso
(nunca de semanas futuras sin programar) y se deja una proporción de vencidas sin
ejecución para que la adherencia sea creíble. Preferí respetar esa regla antes
que rellenar hasta el número redondo. (iii) El banco se acota al **año natural**
(no siembra en los días de dic-2025 que pertenecen a la semana ISO 1 de 2026)
para no rozar la limitación conocida del grid del calendario, que arranca el
1-ene del año del ancla. (iv) El recálculo independiente lo corre el usuario.

---

## 0-bis. Cambio 6.5 + 6.6 — horas reales de seguimiento y supervisor fijo

**Ninguno toca la rotación, la capacidad de planificación (REGLA-5 / PERFIL_HH
siguen en 48 h) ni el motor de VAC.** 6.5 añade una capa de **horas reales**
(cumplimiento individual / base de bono y déficit por VAC) — es reporte, no
motor. 6.6 marca un **supervisor fijo** por técnico. Verificado sobre el libro
recalculado, ancla 2026-07-24:

- **Ambas variantes se generan sin excepción** (`--refs estructuradas` y
  `--refs compatibles`).
- **(a) horas_reales**: **56 h** para un técnico en turno una semana completa
  (48 L-S + 8 del domingo), **48 h** en banco, **0 h** en VAC (semana normal; un
  feriado resta: banco 40, turno 48). El **+8 corresponde al domingo** (relevo
  22:00, 7.º día) y **NO aparece en PERFIL_HH**: la capacidad de planificación
  sigue en 48 h (verificado: PERFIL_HH idéntico a 6.4 — MEC 2026-S30 288 h). El
  domingo no se vuelve planificable.
- **(b) superavit_deficit** (= horas_reales − 48): **+8** en turno, **0** en
  banco, **−48** en VAC, por técnico × semana (recalculado en `SEGUIMIENTO_HH`).
- **(c) SEGUIMIENTO_MENSUAL**: `horas_reales_mes` (acumula `SEGUIMIENTO_HH`) y
  `horas_requeridas_mes` (nº de semanas del mes × 48; cada semana a un mes por su
  lunes) **cuadran**; `cumple` = `reales ≥ requeridas − tolerancia_horas_bono`
  (parámetro nuevo, default 0) es correcto; un técnico con VAC en el mes queda
  **por debajo** (Técnico 05, julio: 56 de 144 h → no cumple).
- **(d) Déficit de capacidad por VAC** (esp × semana) = nº de técnicos en VAC ×
  48 h (MEC 2026-S30/S31/S32 = 48 h; resto 0); **PERFIL_HH base sin cambios**.
- **(e) Supervisor fijo** correcto por especialidad (MEC → Supervisor Mecánico,
  ELE → Supervisor Eléctrico, AUT → Jefe de Automatización), en las 448 filas de
  ASIGNACIONES; **no cambia con VAC ni rotación** (es atributo del técnico).
- **(f) Rotación / capacidad / VAC idénticas a 6.4**: turno efectivo, posiciones
  y `horas_disponibles` sin cambios (comprobado celda a celda). Recálculo:
  **74.182 fórmulas, 0 errores**; comparación motor Python ↔ Excel **14.178
  comparaciones, 0 desviaciones** (incluye `SEGUIMIENTO_HH`, déficit VAC,
  `SEGUIMIENTO_MENSUAL`, la columna `supervisor` y `trabaja_domingo`).

**Inputs/columnas/hojas nuevos.** `TECNICOS.supervisor` (6.6, fuente única).
ASIGNACIONES: `trabaja_domingo` (6.5, helper) y `coordinador`→`supervisor` (6.6,
búsqueda a TECNICOS). Hojas `SEGUIMIENTO_HH` (técnico × semana + bloque déficit
VAC) y `SEGUIMIENTO_MENSUAL` (técnico × mes). Parámetro `tolerancia_horas_bono`.
Doble implementación (`trabaja_domingo_de`/`horas_reales_semana` en Python +
fórmula del libro), coincide celda a celda.

**Qué NO verifiqué / supuestos.** (i) No recalculé el principal `MantPlan.xlsx`
(XLOOKUP); corrección heredada del modo compatible. (ii) El domingo del relevo es
una **medición de seguimiento**, no capacidad planificable. (iii) El `motivo` de
PLAN_VACACIONES distingue vacaciones de día libre pagado pero **no** cambia la
lógica de capacidad. (iv) Sin suplencia de supervisor (a mano). (v) §7 no se
implementó. (vi) El recálculo independiente lo corre el usuario.

---

## 0-ter. Cambio 6.4 — vacaciones que arrastran (VAC automático, posición vacía)

El plan de vacaciones marca **VAC automáticamente** en ASIGNACIONES y saca al
técnico de la rotación esas semanas, dejando su **posición VACÍA** (hueco
visible). No se cierra ninguna fila ni se recalcula N: **la rotación de los demás
no se toca** (se preserva la derivación cerrada de 6.3). Modelo A: cubrir un
turno vacío es acción **manual** del supervisor vía `turno_manual`. Verificado
sobre el libro recalculado, ancla 2026-07-23. Demo: **Técnico 05** (MEC, orden 5)
de vacaciones ~4 semanas (dos periodos), que solapan S30 (estaría en T2), S31
(T1) y S32 (Banco):

- **Ambas variantes se generan sin excepción** (`--refs estructuradas` y
  `--refs compatibles`).
- **(a) Filas del técnico de VAC**: dentro del rango, `turno` = **"VAC"**,
  `horas_disponibles` = **0** (REGLA-5, VAC está en `codigos_no_disponible`) y
  `posicion_ciclo` sigue mostrando la **posición derivada** (T2/T1/B4). Verificado
  celda a celda: Técnico 05 en 2026-S30 lunes → posición T2, en_vacaciones sí,
  turno VAC, 0 h.
- **(b) COBERTURA**: por **posición derivada** cada semana sigue 1 T1 / 1 T2 / 1
  T3 / N-3 Banco (rotación intacta); el **hueco** (turno efectivo VAC) aparece
  EXACTAMENTE en la posición del técnico de VAC —S30→T2, S31→T1, S32→Banco— y en
  **ninguna otra**. El ciclo ELE (sin VAC) mantiene turnos llenos las 4 semanas.
- **(c) Rotación de los demás idéntica a 6.3**: en toda fila sin VAC ni override,
  el `turno` efectivo recalculado iguala a `turno_derivado` (la banda de 6.3); y
  `posicion_ciclo` iguala a `posicion_ciclo_de` en las 448 filas (las posiciones
  no se desplazan).
- **(d) PRECEDENCIA (manual > VAC)**: fijar `turno_manual` = "T1" en una celda VAC
  (Técnico 05, S30, martes) la sobrescribe → `turno` = **T1**, franja 06:00–15:00,
  capacidad **8 h**; `en_vacaciones` (el plan) no cambia. Al **vaciar**
  `turno_manual`, vuelve **"VAC"**. **VAC nunca aparece en domingo** (la posición
  vacía del domingo gana antes que VAC): Técnico 05 el domingo de S30 tiene
  `en_vacaciones` = sí pero `turno` = "". Recalculado con LibreOffice en cada paso.
- **(e) CAPACIDAD**: cada técnico **sin** VAC sigue en **48 h/semana** (16/16
  comprobados en S30 dan 48 h salvo Técnico 05, que da **0 h** por estar de VAC
  toda la semana). La capacidad de MEC baja en consecuencia (S30 de 336 a 288 h),
  sin tocar REGLA-5.
- **(f) Recálculo y comparación**: **73.262 fórmulas, 0 errores**; comparación
  celda a celda motor Python ↔ Excel **12.350 comparaciones, 0 desviaciones**
  (incluye la columna `en_vacaciones`, `PLAN_VACACIONES`, y las comprobaciones
  directas de cobertura/hueco-VAC/avance/capacidad sobre el libro recalculado).

**Inputs/columnas nuevos.** Hoja `PLAN_VACACIONES` (`tblVacaciones`: tecnico,
fecha_inicio, fecha_fin, motivo; varias filas por técnico; `tecnico` validado
contra `lista_tecnicos`). Columna derivada `en_vacaciones` en ASIGNACIONES
(COUNTIFS tecnico + inicio<=fecha + fin>=fecha > 0). `turno` efectivo con
precedencia manual > (domingo) > VAC > rotación. Doble implementación
(`en_vacaciones_de` / `turno_efectivo` en Python + fórmula), coincide celda a celda.

**Qué NO verifiqué / supuestos.** (i) No recalculé el principal `MantPlan.xlsx`
(XLOOKUP); corrección heredada del modo compatible. (ii) Modelo A: la cobertura
de un hueco es manual (no hay reemplazo automático — sería otro bloque). (iii)
6.5 (domingo 22:00 / superávit) y 6.6 (coordinador auto) NO se implementaron.
(iv) El recálculo independiente lo corre el usuario.

---

## 0-quater. Cambio 6.3 — rotación automática derivada por especialidad

El turno pasa de ser un dato a **derivarse por aritmética modular** de la
posición del técnico en el anillo del ciclo. Anillo (orden de avance semanal,
N posiciones, banco = N-3): **B(N-3), …, B1, T3, T2, T1** → y vuelve a B(N-3);
avance **+1 posición/semana**. Dotación que lo ejercita: **7 MEC + 7 ELE**
rotativos en una sola área (N=7 en cada ciclo) + **2 AUT** de Banco fijo, sin
OP. Verificado sobre el libro recalculado (`MantPlan_compatible.xlsx`), ancla
2026-07-23, semana de referencia (lunes) **2026-07-13**:

- **Ambas variantes se generan sin excepción** (`--refs estructuradas` y
  `--refs compatibles`).
- **(a) COBERTURA**: en cada ciclo (especialidad × área) y **cada** semana, en
  día hábil, los N técnicos ocupan las N posiciones distintas — **exactamente 1
  en T1, 1 en T2, 1 en T3 y N-3 = 4 en Banco**; ningún turno vacío ni
  duplicado. Comprobado leyendo la columna `turno` recalculada de MEC·PRODUCCION
  y ELE·PRODUCCION en las 4 semanas del plan (8 comprobaciones, todas OK).
- **(b) AVANCE**: cada técnico avanza **exactamente una posición por semana** en
  el sentido del anillo (incluido el relevo **B1→T3** y el cierre **T1→B(N-3)**).
  Ej. Técnico 04 (orden 4): B1(S29)→T3(S30)→T2→T1; Técnico 05 (orden 5):
  T3→T2→T1(S31)→B4(S32). Comprobado sobre `posicion_ciclo` recalculada de los
  14 rotativos.
- **(c) La fórmula del libro coincide con `turno_derivado`** en **todas** las
  filas: las 448 celdas `posicion_ciclo`, `turno_manual` y `turno` (efectivo)
  recalculadas por LibreOffice igualan a la función pura Python, celda a celda,
  cero desviaciones. (El modo estructurado usa la misma lógica con referencias
  XLOOKUP; se genera sin error y comparte el motor.)
- **(d) OVERRIDE**: al fijar `turno_manual` en una celda (p. ej. Técnico 01,
  2026-S30, martes, cuya rotación da "B") a **"T2"**, **solo esa celda** cambia:
  `turno`→T2 y su franja→15:00–22:00; `posicion_ciclo` sigue en **"B3"**
  (auditoría, no cambia), la capacidad sigue en **8 h** (REGLA-5 intacta) y el
  vecino Técnico 02 mantiene su rotación ("B"). Al **vaciar** `turno_manual`, el
  `turno` vuelve a "B" (la rotación). Recalculado con LibreOffice en cada paso.
- **(e) CAPACIDAD SIN CAMBIOS**: cada técnico (rotativo o AUT) suma **48 h/semana**
  (L-S, domingo 0) en una semana sin feriado. Comprobado sobre las 16 columnas
  `horas_disponibles` recalculadas de 2026-S30 (16/16 = 48 h). La banda cambia
  QUÉ turno, no cuántas horas: REGLA-5 lee el `turno` efectivo sin tocar su lógica.
- **(f) Recálculo completo y comparación**: **72.814 fórmulas, 0 errores**;
  comparación celda a celda motor Python ↔ Excel recalculado **11.409
  comparaciones, 0 desviaciones** (11.371 celda a celda de todas las hojas +
  38 comprobaciones directas de cobertura/avance/capacidad sobre el libro
  recalculado).

**Inputs nuevos.** `TECNICOS.rotativo` (sí/no, flag explícito — no se hardcodea
a MEC/ELE) y `TECNICOS.orden_rotacion` (1..N, único por especialidad×área entre
rotativos); `PARAMETROS.semana_referencia` como **FECHA** (el lunes de la semana
de referencia, no un rótulo). Columnas nuevas en ASIGNACIONES: `posicion_ciclo`
(derivada, auditoría), `turno_manual` (entrada, override) y `n_ciclo` (derivada,
auditoría = N del ciclo); `turno` pasa a **derivado** (efectivo) y el desplegable
se mueve de `turno` a `turno_manual`.

**Qué NO verifiqué / supuestos.** (i) No recalculé el principal `MantPlan.xlsx`
(XLOOKUP): LibreOffice no lo evalúa; corrección heredada del modo compatible
(misma lógica, otra sintaxis de referencia) y auditoría sintáctica. (ii) El
alcance del ciclo es por (especialidad, área): el motor soporta una especialidad
repartida en varias áreas (cada área su propio ciclo, N por COUNTIFS con filtro
de área), pero la muestra usa **una sola área** (PRODUCCION). (iii) Los casos
ad-hoc viejos (TEC-04 VAC, domingo especial de SERVICIOS) se retiraron del
sintético — la rotación exige cobertura limpia cada semana — y quedan reservados
para §7. (iv) 6.4 (VAC automático), 6.5 (domingo 22:00 / superávit) y 6.6
(coordinador auto) NO se implementaron. (v) El recálculo independiente lo corre
el usuario.

---

## 0-quinquies. Cambio 6.2 — catálogo de turnos con franja horaria (CAT_TURNOS)

Los turnos pasan de etiquetas sueltas a un catálogo con banda horaria. **La
franja es metadato de horario; la capacidad NO se deriva de ella** (REGLA-5
sigue plana en `horas_jornada`). Sin rotación ni derivación (eso es 6.3).
Verificado sobre el libro recalculado (`MantPlan_compatible.xlsx`):

- **Ambas variantes se generan sin excepción** (`--refs estructuradas` y
  `--refs compatibles`).
- **(a) CAT_TURNOS con las 4 bandas y franjas correctas**: B 07:00–16:00
  (banco); T1 06:00–15:00, T2 15:00–22:00, T3 22:00–06:00 (rotativos). T3
  cruza medianoche: solo rótulo, no se calcula duración. Es la fuente única.
- **(b) El desplegable de `turno` en ASIGNACIONES toma de CAT_TURNOS + VAC/X**:
  el nombre `lista_turnos` apunta a `CAT_TURNOS!$G$4:$G$9`, cuyas 4 primeras
  celdas espejan por fórmula las bandas del catálogo y las 2 últimas
  referencian los códigos de no disponible (`PARAMETROS!$G$5:$G$6`). El rango
  auxiliar de turnos de PARAMETROS se retiró (sin dos fuentes; `E5` vacío).
- **(c) Los lookups `hora_inicio`/`hora_fin` resuelven la franja correcta y
  quedan en blanco en VAC/X**: comprobado en las 336 celdas recalculadas —
  B→07:00/16:00, T1→06:00/15:00, T2→15:00/22:00; VAC, X y turno vacío
  (domingo) → en blanco (el turno no está en el catálogo → si_no_encontrado "").
- **(d) La CAPACIDAD NO CAMBIÓ**: las 336 celdas de `horas_disponibles` de 6.2
  son **idénticas** a las de 6.1 (0 diferencias, total 2168 h en ambas,
  comparación directa entre los dos generadores). Un técnico normal sigue
  sumando **48 h/semana** (TEC-01 2026-S29 = 8×6). La migración de bandas
  (B1→B, AUT→B) no mueve capacidad porque todo turno de trabajo da igual 8 h.
- **(e) Recálculo completo y comparación**: 71.014 fórmulas, **0 errores**;
  comparación celda a celda motor Python ↔ Excel recalculado **9.486
  comparaciones, 0 desviaciones** (incluidas las 336×2 celdas de franja y las
  20 de CAT_TURNOS).

**Qué NO verifiqué / supuestos.** (i) No recalculé el principal `MantPlan.xlsx`
(XLOOKUP): LibreOffice no lo evalúa; corrección heredada de las plantillas
compartidas y auditoría sintáctica. (ii) **Sí actualicé el README** (era la
higiene pendiente de 6.1, edición 8 de este bloque): título a v2.6.0, cifras
de capacidad de 7 h → 8 h, inventario con CAT_TURNOS y línea de "turnos con
franja". (iii) Supuestos: `hora_inicio`/`hora_fin` se **añadieron al final** de
ASIGNACIONES (columnas K/L) para no correr `fecha`/`horas_disponibles`/`clave`
ni la verificación; T3 queda sin técnico en la muestra (AUT migró a B), pero
la banda existe en el catálogo y se verifica su franja. (iv) El recálculo
independiente lo corre el usuario.

---

## 0-sexies. Cambio 6.1 — jornada 8 h y base semanal 48 h (L-S)

Cambio de parámetro + patrón, sin tocar el modelo de turnos ni la rotación
(eso es 6.3) ni ninguna otra hoja/regla. Verificado sobre el libro
recalculado (`MantPlan_compatible.xlsx`):

- **Ambas variantes se generan sin excepción** (`--refs estructuradas` y
  `--refs compatibles`).
- **REGLA-5 devuelve 8 h en día hábil (L-S) y 0 en domingo / VAC / X.**
  Comprobado en la función pura (`regla_5_horas_disponibles`) y en las 336
  celdas `horas_disponibles` de ASIGNACIONES recalculadas: TEC-01 en 2026-S29
  da 8 h de lunes a sábado y 0 el domingo.
- **Un técnico normal suma 48 h en la semana** (6 días × 8 h). Verificado:
  TEC-01 2026-S29 = 8+8+8+8+8+8+0 = **48 h**.
- **Los dos parámetros nuevos existen con sus rangos nombrados**:
  `dias_laborables_base` (B18, valor 6, rango `p_dias_laborables_base`) y
  `base_semanal_horas` (B19, rango `p_base_semanal_horas`).
- **`base_semanal_horas` evalúa a 48 vía fórmula**: su celda B19 contiene
  `=p_horas_jornada*p_dias_laborables_base` y LibreOffice la recalculó a **48**
  (celda derivada, estilo de fórmula, sin validación de entrada ni marca de
  editable). Es la fuente única de verdad: cambiar jornada o días la actualiza.
- **`horas_jornada` = 8** (B7) y **`PATRON_HABIL[5]` (sábado) = "sí"**; el
  patrón semanal marca L-S hábil y domingo no hábil.
- **Recálculo completo**: 71.014 fórmulas, **0 errores**; y la comparación
  celda a celda motor Python ↔ Excel recalculado dio **9.486 comparaciones,
  0 desviaciones** con la jornada de 8 h (todo el efecto aguas abajo —
  PERFIL_HH, ADHERENCIA, gráfico de carga, EXPORTAR — coincide con el motor).

**Qué NO verifiqué en este cambio.** (a) No recalculé el archivo principal
`MantPlan.xlsx` (XLOOKUP): LibreOffice no lo evalúa; su corrección se hereda
de las plantillas compartidas y de la auditoría sintáctica, como en versiones
previas. (b) **No actualicé el README ni las cifras absolutas de las secciones
§3.2–§3.7 de más abajo**, que se tabularon bajo jornada 7 h (v2.4): con 6.1
esas capacidades escalan (día = 8 × 0,87 = 6,96 h; MEC 2026-S29 pasa de 140 a
192 h disponibles, etc.). El verificador celda a celda (8.794/0) revalidó
todas esas magnitudes bajo 8 h, pero los ejemplos narrados abajo conservan los
números de v2.4 y deben leerse como históricos. (c) El recálculo independiente
lo hace el usuario en el chat.

**Supuestos donde algo fue ambiguo.** (1) `base_semanal_horas` se escribe como
fórmula en su celda B (no como literal), por indicación explícita, y recibe
estilo de celda calculada. (2) A `dias_laborables_base` se le aplicó la misma
validación que a `horas_jornada` (`dv3`, entero 1–24), tal como se pidió, aun
cuando 24 sea un techo amplio para "días". (3) Los parámetros nuevos se
apéndieron al final de la lista para no correr las filas existentes; los
rangos nombrados y `FILA_PARAM` se recalculan solos.

---

## 1. Recálculo con motor de cálculo real (contexto v2.4/v2.5)

La variante `MantPlan_compatible.xlsx` (mismas plantillas de fórmula que el
principal, con `INDEX/MATCH` + rangos A1 en lugar de `XLOOKUP` + referencias
estructuradas) se recalculó por completo con LibreOffice Calc 24.2:

| Métrica | Valor |
|---|---:|
| Fórmulas recalculadas | **74.182** |
| Errores de fórmula (`#REF!`, `#VALUE!`, `#NAME?`, `#DIV/0!`, `#N/A`, …) | **0** |

## 2. Comparación motor Python ↔ Excel recalculado

Cada valor del libro recalculado se comparó contra el motor Python
(`generar_mantplan.py`), tolerancia 1e-6:

| Métrica | Valor |
|---|---:|
| Comparaciones automáticas | **14.178** |
| Desviaciones | **0** |

Cobertura: las 24 columnas calculadas de las 200 órdenes (incluidas es_habil y backlog_habiles, y
`horas_efectivas` resuelta por búsqueda en `tblAjustes`); muestreo de filas
provisionadas vacías (250, 700, 1.203) en blanco; `id_operacion` de las
filas de EJECUCION; las **448 filas de ASIGNACIONES** (rotación derivada
`n_ciclo`/`posicion_ciclo`, `en_vacaciones`, `turno_manual`/`turno`, `supervisor`,
`trabaja_domingo`, fecha, REGLA-5 y franja horaria) + las comprobaciones directas
de cobertura/hueco-VAC/avance/capacidad sobre el libro recalculado (6.3/6.4);
`PLAN_VACACIONES`; **`SEGUIMIENTO_HH`** (horas reales, superávit/déficit y
déficit por VAC) y **`SEGUIMIENTO_MENSUAL`** (reales/requeridas/cumple/brecha,
6.5); la hoja AJUSTES (descripcion,
estado_ajuste y desviacion_h de las 4 filas demo + fila vacía); PERFIL_HH
completo (serie de 60 posiciones, REGLA-6 por semana × especialidad,
REGLA-9); ADHERENCIA (bloque semanal dinámico + 6 desgloses, solo días hábiles); BACKLOG por
tramos; COSTOS por mes; EQUIPOS_CRITICOS; zona de datos del gráfico de carga;
los 16 chequeos de VALIDACION; **EXPORTAR** (los escalares del resumen
AJ8–AJ16, el bloque por técnico AC/AD/AE de los 16, más fragmentos del
texto del correo y el conteo de líneas del programa); y la dimensión
**sub_area** (columna calculada de las 200 órdenes, desglose de ADHERENCIA,
matriz de COSTOS por sub-área con su reconciliación contra el área, y matriz
de BACKLOG por sub-área).

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

Efectos verificados del ajuste 8 → 12 en la orden de ajuste (Técnico 01,
2026-S30): `horas_efectivas` 12 · PERFIL_HH MEC 2026-S30 prev **82** / carga
**41,4 %** · barra del gráfico Técnico 01 = **32**, dentro de la capacidad
semanal 41,76 h (sin rojo) · HHA del día del ajuste 12 / HHD **−5,04**.
VALIDACION: órdenes ajustadas **2**, desviación
total **+2 h**, huérfanos **1**, duplicados en tblAjustes **2**.

### 3.3 Recálculo de la variante compatible

**0 errores en 74.182 fórmulas** (§1), mismos números que el motor Python en
las 14.178 comparaciones (§2).

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
- Resumen: **40** órdenes (incluye 3 de fin de semana), **326 h** (prev **244** =
  75 %, corr **82** = 25 %), **12** técnicos.
- Alerta de capacidad: Técnico 01 (41,0 vs 30,5) y Técnico 06 (40,0 vs 30,5).
- Top 5 tareas por `horas_efectivas`, con marca de permiso/LOTO donde aplica.
- Programa completo con **exactamente 40 líneas** (conteo de `· OT-`),
  agrupado por día y ordenado por turno y técnico, **incluyendo sábado y
  domingo** (7 días).

**Bloque condicional:** al cambiar el selector a la semana **2026-S32** (sin
técnicos sobreasignados) y recalcular, el escalar de sobreasignados es **0**,
el encabezado "Alerta de capacidad" **no aparece**, no hay triple salto de
línea (bloque vacío sin residuo) y el correo pasa directo del resumen a las
tareas relevantes. Confirma que los bloques condicionales desaparecen limpios.

### 3.6 Dimensión sub_area — agrupamiento con herencia

Jerarquía de muestra: SERVICIOS subdividido en 4 sub-áreas; PRODUCCION y
EMPAQUE sin subdividir (prueban la herencia). Verificado sobre el libro
recalculado (matriz REAL por sub-área de COSTOS):

- **Sub-área con 2 CECOs**: `Vapor` = CC-310 (4.280) + CC-311 (1.540) =
  **5.820** en una sola fila rotulada con el nombre de proceso "Vapor".
- **CECO sin sub-área hereda el nombre del área**: las etiquetas del desglose
  son `PRODUCCION`, `EMPAQUE`, `Vapor`, `Refrigeración`, `CO2`,
  `Aire comprimido` — **ninguna es un código `CC-*`**. PRODUCCION y EMPAQUE
  reportan bajo el nombre de su área, no bajo `CC-110`/`CC-210`.
- **Reconciliación área = Σ sub-áreas**: SERVICIOS = 6.020 + 2.050 + 200 +
  160 = **8.430**, idéntico al total del área SERVICIOS; el gran total de la
  matriz por sub-área coincide con el de la matriz por área.

Todos los desgloses por sub-área (ADHERENCIA, COSTOS, BACKLOG) se
compararon celda a celda contra el motor Python dentro de las 14.178
comparaciones, con 0 desviaciones. La dimensión no toca ninguna de las 10
reglas del motor.

### 3.7 Calendario laboral — es_habil, capacidad y backlog hábil

Excepciones de muestra: 12 feriados generales + feriado de planta el miércoles
de 2026-S31 (2026-07-29) + domingo laborable de SERVICIOS (2026-08-02) + paro
de la sub-área Vapor (2026-07-23) + 2 excepciones con área/sub-área fuera de
catálogo. Verificado sobre el libro recalculado:

- **`es_habil` por especificidad**: en el paro de Vapor, `es_habil` = **no**
  para órdenes de Vapor y **sí** para PRODUCCION, EMPAQUE y Refrigeración (la
  excepción por sub-área no toca las demás sub-áreas).
- **Feriado general reduce capacidad** (REGLA-5): el miércoles 2026-07-29,
  `horas_disponibles` = 0 para todos los técnicos activos (feriado general).
  PERFIL_HH **MEC 2026-S31 baja de 336 a 280 h** disponibles (7 técnicos × 5
  días × 8) — la rotación no altera este efecto, solo cambia qué turno.
- **Excepción por área** (día especial laborable): el domingo 2026-08-02,
  `es_habil(SERVICIOS)` = **sí** y `es_habil(PRODUCCION)` = **no** (la excepción
  por área da capacidad solo a SERVICIOS).
- **`backlog_habiles` < `backlog_dias`** al cruzar fines de semana: la orden
  demo (fecha 2026-06-09) tiene `backlog_dias` **45** y `backlog_habiles` **38**
  — diferencia de **7** domingos no hábiles en medio (el sábado es hábil, 6.1).
- **VALIDACION**: 34 órdenes en día no laborable, 1 excepción con área
  desconocida (ZONA-X), 1 con sub-área desconocida (Nitrógeno).
- **Reconciliación**: los totales por área de COSTOS siguen cuadrando con la
  suma de sus sub-áreas tras el cambio (dentro de las 14.178 comparaciones).

Las 448 filas de REGLA-5 (con el turno derivado de la rotación, la fecha de
semana+día y el calendario) y las 26 columnas calculadas de las 200 órdenes
(incluidas `es_habil`, `backlog_habiles`, `estado_backlog` y `en_plan` sobre
días hábiles) se compararon celda a celda, con 0 desviaciones.

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
6. **sub_area** (v2.3): (a) las sub-áreas de los reportes se derivan del
   catálogo en orden, agrupadas por área madre; una sub-área nueva en el
   catálogo aparece sola tras regenerar. (b) La herencia usa la celda `area`
   ya calculada de la orden como valor por defecto, no un segundo lookup
   independiente. (c) PERFIL_HH se deja por especialidad (la sub-área no
   aporta un corte útil de capacidad). (d) En PLAN_SEMANAL la sub-área se
   añade como 7.ª columna de dimensión de la grilla (tras especialidad) por
   simplicidad del filtro; en ORDENES sí queda adyacente a `area`.
7. **Calendario** (v2.4): (a) `backlog_habiles` usa el calendario a **nivel
   planta** (patrón + feriados generales), no las excepciones por área/sub-área
   — el aging es un conteo de planta; las excepciones por área afectan
   capacidad (REGLA-5) y el flag `es_habil` por orden. (b) ADHERENCIA
   **excluye** las órdenes en día no hábil del denominador (no las "reporta
   aparte" dentro del mismo cálculo); el conteo de esas órdenes va a VALIDACION.
   (c) El grid del calendario cubre 760 días desde el 1-ene del año del ancla;
   una orden fuera de ese rango contaría de menos en `backlog_habiles`. (d) La
   capacidad de REGLA-5 se evalúa a nivel área (sub-área vacía): un paro de
   sub-área no reduce la capacidad del técnico (que no tiene sub-área), solo
   marca no hábiles las órdenes de esa sub-área. (e) BACKLOG (envejecimiento
   por tramos) se mantiene en días **calendario** (`backlog_dias`), como pide
   el enunciado para indicadores contractuales.
8. Se mantienen los supuestos de v2.0/v2.1: ocultamiento de filas decidido al
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
