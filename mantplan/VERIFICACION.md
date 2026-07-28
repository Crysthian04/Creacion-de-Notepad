# VERIFICACION.md — MantPlan v3.6.0

## 0. Listas robustas, señalización de columnas calculadas y cierre

Última tirada del entregable A. **No toca** las 10 reglas, el motor, el dashboard
ni el banco (punto g).

### El defecto de fondo, y por qué era bloqueante

Las listas de los desplegables se escribían **al generar el archivo**, con los
valores del dataset de ejemplo, o dimensionadas al tamaño de los datos de ese
momento. No crecían nunca. En la plantilla —8 órdenes de ejemplo— el selector de
meses tenía **2 entradas** y el de semanas **4**: al pegar un año real, el usuario
**no podía seleccionar sus propios meses** y el tablero quedaba inservible justo
al empezar a usarse. En 7.2 estos desplegables pasaron de literales a rangos, pero
varios de esos rangos eran **copias estáticas**: el problema se había movido, no
eliminado.

### (1) Meses y semanas: ventana de calendario completa

Dejan de depender de los datos.

| lista | contenido | entradas |
|---|---|---:|
| `lista_meses_dash` | 3 últimos meses del año anterior + los 12 del año de la fecha de datos + 3 primeros del siguiente | **18**, siempre |
| `lista_semanas_plan` | `(todos)` + 2 últimas semanas ISO del año anterior + el año ISO completo + 2 primeras del siguiente | **58** (año de 53 semanas) |

Contiguas, ordenadas, sin huecos, en texto `AAAA-MM` y `AAAA-Snn` — nunca fechas
reales, porque el `MATCH` compara texto.

Los bloques mensuales de `ADHERENCIA`, `PERFIL_HH` y `BACKLOG` pasan a cubrir la
**misma** ventana de 18 meses. Sin eso, el arreglo habría quedado a medias: el mes
sería seleccionable pero no tendría fila que leer.

### (2) Auditoría completa de listas

Barrido de **todas** las listas del libro, no solo las señaladas:

| lista | origen | antes | ahora | holgura |
|---|---|---|---|---:|
| `lista_areas` | `CAT_CENTROS_COSTO.area` (distintos) | **texto fijo** | fórmula | 25 |
| `lista_subareas` | `CAT_CENTROS_COSTO`, sub-área **efectiva** | **texto fijo** | fórmula | 25 |
| `lista_f_area` | ídem + `(todos)` | **texto fijo** | fórmula | 26 |
| `lista_f_subarea` | ídem + `(todos)` | **texto fijo** | fórmula | 26 |
| `lista_f_coordinador` | `CAT_CENTROS_COSTO.coordinador` | **texto fijo** | fórmula | 26 |
| `lista_f_especialidad` | `CAT_PUESTOS.especialidad` | **texto fijo** | fórmula | 21 |
| `lista_esp_propias` | `CAT_PUESTOS` filtrando `es_especialidad_propia` | **texto fijo** | fórmula | 20 |
| `lista_ceco` | `CAT_CENTROS_COSTO.codigo` | fórmula, tamaño fijo | fórmula | 25 |
| `lista_puestos` | `CAT_PUESTOS.codigo` | fórmula, tamaño fijo | fórmula | 20 |
| `lista_actividades` | `CAT_ACTIVIDADES.codigo` | fórmula, tamaño fijo | fórmula | 23 |
| `lista_tipos_ot` | `CAT_TIPOS_OT.codigo` | fórmula, tamaño fijo | fórmula | 20 |
| `lista_supervisores` | `CAT_SUPERVISORES.nombre` | fórmula, tamaño fijo | fórmula | 18 |
| `lista_motivos_ausencia` | `CAT_MOTIVOS_AUSENCIA.motivo` | fórmula, tamaño fijo | fórmula | 18 |
| `lista_f_turno` | `CAT_TURNOS.turno` + `(todos)` | fórmula, tamaño fijo | fórmula | 20 |
| `lista_turnos` | `CAT_TURNOS` + códigos no disponibles | fórmula (ya correcta) | sin cambios | — |
| `lista_tecnicos` | `TECNICOS`, activos compactados | fórmula (ya correcta) | sin cambios | 16 |
| `lista_meses_dash` | **calendario** (18 meses) | datos | calendario | fija |
| `lista_semanas_plan` | **calendario** (año ISO) | datos | calendario | fija |
| `lista_dias` | dominio fijo | texto | **texto (correcto)** | — |
| `lista_no_disponible` | dominio fijo | texto | **texto (correcto)** | — |

Cada lista derivada de catálogo tiene tres piezas: una **columna de orden** en la
hoja del catálogo, que numera los valores **distintos** que entran (aplicando el
filtro si lo hay); una columna en `PARAMETROS` que los **compacta** con
`INDEX`/`MATCH` sin dejar huecos; y un **rango con nombre acotado con `INDEX`** al
número real de entradas, para que el desplegable no muestre opciones en blanco.
`INDEX` no es volátil y no está entre las funciones prohibidas —a diferencia de
`OFFSET`, que sí lo está—, así que el rango es dinámico sin romper la higiene.

Los catálogos llevan **15 filas vacías de holgura** dentro de su tabla.

### (a) La plantilla ofrece el calendario completo pese a no tener datos

Es la prueba clave del arreglo, sobre el libro entregado:

```
PLANTILLA con 8 órdenes en 2 meses:
  el selector ofrece 18 meses (2025-10 … 2027-03) y 58 semanas (2025-S51 … 2027-S02)
```

Nueve veces más meses que meses con datos.

### (b) Caso real simulado: un mes que no estaba en los datos

Se toma **2026-09**, que no tiene ninguna orden de ejemplo, y se comprueba en dos
tiempos sobre el libro recalculado:

1. **Antes de cargar nada**: el mes **ya era seleccionable** (está en la ventana),
   y el tablero lo muestra con los KPI **en blanco**, con 0 errores de fórmula.
2. Se pegan **3 órdenes** de ese mes en `ORDENES`, como haría el usuario, y se
   recalcula: 0 errores, `ADHERENCIA` cuenta las **3** órdenes en la fila del mes,
   y el KPI del tablero deja de estar en blanco y **coincide con su hoja de
   origen**.

Antes de este cambio, ese mes ni siquiera habría aparecido en el desplegable.

### (c) Prueba real de catálogos, no por inspección

Se abre el libro entregado, se añade **una fila a `CAT_CENTROS_COSTO`** (`CC-999`,
área `TALLER`, sub-área `Banco de pruebas`, coordinador `Coordinador Z`) y **una
especialidad propia a `CAT_PUESTOS`** (`PU-INS` / `INSTRUM`, marcada como propia),
y se **recalcula**:

| lista | antes | después | incluye el valor nuevo | huecos |
|---|---:|---:|---|---|
| `lista_ceco` | 10 | **11** | `CC-999` | no |
| `lista_areas` | 3 | **4** | `TALLER` | no |
| `lista_f_area` | 4 | **5** | `TALLER` | no |
| `lista_f_coordinador` | 4 | **5** | `Coordinador Z` | no |
| `lista_subareas` | 6 | **7** | `Banco de pruebas` | no |
| `lista_f_subarea` | 7 | **8** | `Banco de pruebas` | no |
| `lista_puestos` | 5 | **6** | `PU-INS` | no |
| `lista_f_especialidad` | 6 | **7** | `INSTRUM` | no |
| `lista_esp_propias` | 3 | **4** | `INSTRUM` | no |

**0 errores** en el recálculo. Ninguna lista muestra opciones en blanco, y el
valor nuevo no contamina las listas que no le corresponden. La sub-área efectiva
funciona con la herencia: `Banco de pruebas` aparece porque el CECO la declara; si
se hubiera dejado vacía, aparecería `TALLER`.

### (d) Los rangos coinciden con las entradas escritas

`lista_meses_dash` → `DASHBOARD!$X$3:$X$20` (18 celdas, 18 entradas).
`lista_semanas_plan` → `PLAN_SEMANAL!$X$3:$X$60` (58 celdas, 58 entradas).
Las 9 listas de catálogo de la prueba (c) cubren **exactamente** sus celdas
escritas: ni cortas —entradas invisibles— ni con celdas fuera del rango.

### (e) Un mes sin datos: blanco, no error

Mes `2026-09` sin órdenes, recalculado: **0 errores**; adherencia, carga,
lubricación y calibración **en blanco**. Las fórmulas ya usaban `IFERROR(…;"")` y
se confirma que siguen haciéndolo tras el cambio.

**Blanco = no hay dato; cero = hubo trabajo y no se cumplió.** La distinción se
mantiene: en el mismo mes vacío, backlog y ejecución OPEX **sí** muestran número,
y es correcto — el backlog es acumulado hasta el corte y el OPEX es una
acumulación anual, así que no dependen de que ese mes tenga órdenes.

La nota está en pantalla, en el `DASHBOARD` y en el `INSTRUCTIVO`.

### (f) Señalización de columnas calculadas

**Criterio:** una celda es calculada si **contiene una fórmula**. No hay lista de
columnas que mantener ni que pueda quedar desfasada; si una columna deja de
calcularse, deja de marcarse sola.

| hoja | celdas marcadas | encabezados en rojo | reglas de formato condicional |
|---|---:|---:|---:|
| `ORDENES` | 35.760 | 30 | 3 |
| `PLAN_SEMANAL` | 16.882 | 5 | 0 |
| `ASIGNACIONES` | 5.824 | 13 | 0 |
| `PERFIL_HH` | 2.898 | 11 | 3 |
| `ADHERENCIA` | 1.518 | 8 | 25 |
| `PRESUPUESTO` | 692 | 17 | 3 |
| `SEGUIMIENTO_HH` | 344 | 5 | 0 |
| `BACKLOG` | 150 | 6 | 4 |
| `SEGUIMIENTO_MENSUAL` | 128 | 4 | 0 |
| `COSTOS` | 91 | 3 | 0 |
| `TECNICOS` | 32 | 0 | 0 |
| `VALIDACION` | 16 | 1 | 1 |

- El **azul** de lo editable sigue intacto: las 5 columnas editables de `ORDENES`
  lo conservan, y `turno_manual` de `ASIGNACIONES` **no** aparece marcada como
  calculada, que es lo correcto.
- El **formato condicional previo sigue vivo** (25 reglas en `ADHERENCIA`, 4 en
  `BACKLOG`, 3 en `PERFIL_HH`, `ORDENES` y `PRESUPUESTO`) y se pinta **por
  encima** del relleno estático, así que donde hay conflicto gana el semáforo.
- **Leyenda**: completa en `INSTRUCTIVO` y corta al final de la fila de título de
  las siete hojas mixtas.
- Las hojas **no se protegen** y no se bloquea ninguna celda.
- El encabezado usa **rojo claro** (`#FFC7CE`) y no rojo puro: los encabezados van
  sobre una banda azul oscuro, donde el rojo puro sería ilegible. El relleno de
  celda (`#FDF3F3`) queda como un gris muy tenue al imprimir en blanco y negro:
  se distingue del blanco sin estorbar la lectura.
- `TECNICOS` marca sus 32 celdas calculadas pero **0 encabezados**: sus dos
  columnas auxiliares no llevan la banda azul, sino el estilo de nota. Es
  coherente y queda declarado.

### (g) Recálculo y motor ↔ Excel, en los tres datasets

| | fórmulas | errores | comparaciones | fallos |
|---|---:|---:|---:|---:|
| Plantilla (compatible) | 81.253 | **0** | — | — |
| Demo (compatible, ancla 2026-07-27) | 81.664 | **0** | 15.643 | **0** |
| Banco §7 (compatible, 1.000 órdenes) | 153.028 | **0** | 63.177 | **0** |
| Ventana de calendario (a)(b)(d)(e)(f) | — | **0** | 32 | **0** |
| Crecimiento de catálogos (c) | — | **0** | 38 | **0** |
| Plantilla (a)–(e) de la tirada anterior | — | **0** | 40 | **0** |
| DASHBOARD sobre el demo | — | **0** | 67 | **0** |

Las pruebas de regresión —`activo`, override de turno, presupuesto— pasan sin
cambios. **Nada más del motor cambió de valor**: los bloques mensuales cubren más
meses, pero cada fila calcula lo mismo que antes; las 15.643 y 63.177
comparaciones motor↔Excel siguen en cero desviaciones.

> **Dos fallos encontrados durante esta tirada, ambos por la verificación y no por
> lectura del código.** (1) La columna de orden de `lista_f_turno` cayó sobre la
> columna auxiliar que `CAT_TURNOS` ya usaba para `lista_turnos`, y la
> sobreescribió: el filtro de turno quedó con una sola entrada. Se corrigió
> calculando la primera columna libre **real** de cada hoja y moviendo el bloque
> de listas a después de que `CAT_TURNOS` escriba la suya. (2) Antes de eso, el
> bloque se había insertado en un punto donde los catálogos todavía no existían.
> Ninguno de los dos se ve leyendo el generador; los dos aparecen al mirar el
> libro recalculado.

### Qué NO se verificó / supuestos

(i) Solo se recalculan las variantes **compatibles**: LibreOffice no evalúa
`XLOOKUP`. (ii) **Lo que no se puede comprobar por programa es el render del
desplegable**: se verifica que el rango con nombre resuelve al número exacto de
entradas no vacías, no que Excel dibuje la lista sin líneas en blanco. El rango
acotado con `INDEX` es la técnica estándar para eso, pero su comportamiento
visual en cada versión de Excel y de LibreOffice queda fuera de lo verificable
aquí. (iii) La holgura es de 15 filas por catálogo: si alguien necesita más de 15
centros de costo nuevos de golpe, hay que ampliar la tabla —el `INSTRUCTIVO` no lo
menciona, y es una limitación real. (iv) El contraste al imprimir en blanco y
negro se razona sobre el valor del color (`#FDF3F3` ≈ gris 98 %), no se ha
impreso. (v) La ventana de 18 meses se ancla al **año** de la fecha de datos: un
libro cuya fecha de datos sea de enero ofrece 3 meses del año anterior, que puede
ser poco si se quiere mirar más atrás; se amplía cambiando dos constantes.
(vi) El recálculo independiente lo corre el usuario.

---

## 0-bis. Plantilla de producción e instructivo de uso

Última tirada del entregable A. **No toca** las 10 reglas, el motor, el dashboard
ni el banco: los tres datasets salen del mismo código y se verifican por separado
(punto f).

### Modo `--plantilla`: el archivo con el que se empieza a trabajar

El dataset de demo siembra casos sucios **a propósito** para ejercitar REGLA-10.
Eso es justo lo que no debe llevar el archivo que alguien abre para trabajar: se
hereda basura y el primer hallazgo que ve el usuario no es suyo. `--plantilla`
genera un tercer dataset, limpio, con ocho órdenes de ejemplo inconfundibles.

| | plantilla | demo | banco §7 |
|---|---:|---:|---:|
| Órdenes | **8** | 200 | 1.000 |
| Filas de EJECUCION | **8** | 162 | 851 |
| Casos sucios sembrados | **0** | 21 | 16 contadores |
| Ajustes manuales | 0 | 4 | 9 |
| Excepciones de calendario | **12** (solo feriados reales) | 17 | 17 |
| Hallazgos de VALIDACION al abrir | **0** | varios | varios |

### (a) La plantilla abre con VALIDACION en CERO

Los **16 chequeos** en cero, comprobado sobre el libro recalculado:

```
0  Órdenes duplicadas por id_operacion        0  Órdenes con ajuste manual de horas
0  Órdenes sin fecha de inicio                0  Desviación total de horas
0  Órdenes sin horas estimadas                0  Ajustes huérfanos
0  Centros de costo fuera de catálogo         0  id_operacion duplicados en tblAjustes
0  Puestos de trabajo fuera de catálogo       0  Órdenes en día NO laborable
0  Actividades fuera de catálogo              0  Excepciones con área fuera de catálogo
0  Tipos de OT fuera de catálogo              0  Excepciones con sub-área fuera de catálogo
0  Registros de EJECUCION sin par en ORDENES  0  Órdenes sin par en EJECUCION
```

> **Desviación consciente de lo pedido, y por qué.** El encargo decía «~8 órdenes
> y ~6 de ejecución». Se generan **8 filas de EJECUCION, no 6**: con seis, el
> chequeo «Órdenes sin par en EJECUCION» abriría en **2** y el requisito de cero
> hallazgos —que es el que tiene una razón detrás— quedaría incumplido. La
> variedad se conserva igual: **6 órdenes cerradas y 2 pendientes** (estado `LIB`),
> que es el reparto realista y da una adherencia de ejemplo del 75 %.

### (b) Las filas de ejemplo son inconfundibles

Ocho órdenes, `OT-EJEMPLO-001` … `OT-EJEMPLO-008`, todas con:

- **id** con el prefijo `OT-EJEMPLO-`
- **equipo** `EQ-EJEMPLO`
- **descripción** que empieza por `EJEMPLO — BORRAR ANTES DE USAR`
- **relleno ámbar** (`FFF2CC`) en toda la fila, en `ORDENES` y en
  `2_IMPORTAR_EJECUCION`

Verificado además que el relleno **no se derrama** a la primera fila vacía: el
aviso marca exactamente las filas que hay que borrar, ni una más.

`PLAN_VACACIONES` trae **1 fila** de ejemplo, también resaltada, y `PRESUPUESTO`
llega con **41 celdas** de monto, para que el formato esperado se vea en vez de
una hoja en blanco.

Cubren, con ocho órdenes, las **cuatro clases** del mix, los **dos rubros**
(calibración y lubricación), las tres especialidades propias y un trabajo de
tercero: suficiente para que el tablero se vea vivo sin ensuciar nada.

### (c) INSTRUCTIVO: una sola guía, visible y en el puesto #2

**La antigua hoja `INICIO` desaparece.** Estaba oculta y decía cosas parecidas
pero no idénticas al futuro instructivo; mantener dos guías —una visible y otra
no— es garantía de que acaben divergiendo. Su contenido útil (el principio de
diseño motor/catálogos/parámetros) se absorbió en la sección final del
`INSTRUCTIVO`.

Comprobado en los **seis libros** (plantilla ×2, demo ×2, banco ×2):

| comprobación | resultado |
|---|---|
| `INSTRUCTIVO` existe | sí, en los 6 |
| Puesto en el libro | **#2**, justo detrás de `DASHBOARD`, en los 6 |
| Estado | **visible** en los 6 |
| `INICIO` presente | **no**, en ninguno |
| Secciones A–G completas | sí, las 7 |
| Menciona MTBF · MTTR · OEE · disponibilidad | sí |
| Advertencia de borrar las filas de ejemplo | sí, destacada en rojo |

La sección **G** no solo lista lo que no se puede calcular: da el motivo de cada
uno (no hay eventos de parada, ni tiempos de operación, ni producción, ni
movimientos de almacén) y cierra diciendo dónde sí se calculan. Es el punto que
evita que alguien pida esos indicadores y se acabe fabricando un número.

### (d) Botón de vuelta también en INSTRUCTIVO

Presente en `INSTRUCTIVO!A2` de los seis libros, apuntando a `DASHBOARD!A1`,
dentro de la zona visible y sin pisar contenido. Con el `INSTRUCTIVO` sumado, el
botón está ahora en **20 hojas visibles** (19 antes).

### (e) La plantilla no arrastra ningún caso sucio

Se comprueban **14 categorías** de suciedad, una por cada cosa que el demo o el
banco siembran a propósito, y todas dan **0** en la plantilla:

ids duplicados · órdenes sin fecha · sin horas · centro de costo fuera de
catálogo · actividad fuera de catálogo · tipo de OT fuera de catálogo · ejecución
huérfana · orden sin ejecución · ajustes manuales · órdenes en día no laborable ·
excepción con área fuera de catálogo · excepción con sub-área fuera de catálogo ·
casos borde de REGLA-8 · órdenes que caen en `SIN CLASIFICAR`.

**Control de la prueba:** el mismo recuento sobre el dataset de demo da **21**
casos. Sin ese contraste, un «0» podría significar que la comprobación no mira
donde debe.

El calendario de la plantilla se queda con los **12 feriados generales** y pierde
las cinco excepciones de demostración —incluidas las dos que están fuera de
catálogo a propósito, de donde salían los dos últimos chequeos—. Para conseguirlo
se separó `feriados_del_anio()` de `construir_excepciones()`: un primer filtro por
tipo dejaba pasar el «Feriado de planta (demo capacidad)», que es andamio de
demostración y no tenía nada que hacer en un archivo de producción.

### (f) Recálculo y motor ↔ Excel, en los tres datasets

| | fórmulas | errores | comparaciones | fallos |
|---|---:|---:|---:|---:|
| **Plantilla** (compatible, 8 órdenes) | 79.933 | **0** | — | — |
| Demo (compatible, ancla 2026-07-27) | 80.731 | **0** | 15.643 | **0** |
| Banco §7 (compatible, 1.000 órdenes) | 152.181 | **0** | 63.177 | **0** |
| DASHBOARD sobre la plantilla | — | **0** | 50 | **0** |
| DASHBOARD sobre el demo | — | **0** | 135 | **0** |
| Verificador de plantilla (a)–(e) | — | — | 108 | **0** |

El tablero funciona igual sobre la plantilla: los KPI siguen coincidiendo con su
hoja de origen y con el motor, con solo ocho órdenes. Las pruebas de regresión
—`activo`, override de turno, presupuesto— pasan sin cambios.

> **Fallo encontrado y corregido durante la verificación.** El `INSTRUCTIVO`
> explicaba el error de Excel 2016 escribiendo el literal `#NAME?` dentro de una
> celda de texto. Cualquier auditoría de errores del libro —incluida la del
> propio recálculo— lo contaba como un **error real**: la plantilla reportaba
> «1 error» que no existía. Se reformuló a «errores de nombre de función (NOMBRE
> en Excel español, NAME en inglés)»: se entiende igual y no ensucia ninguna
> auditoría, ni la mía ni la de quien reciba el archivo.

### Qué NO se verificó / supuestos

(i) Solo se recalculan las variantes **compatibles**. (ii) La plantilla se
verifica con el ancla `2026-07-27`; sin `--fecha-ancla` toma el día de
generación, y las fechas de las 8 órdenes se recolocan al primer día hábil
disponible — el generador las desplaza para que ninguna caiga en domingo o
feriado, así que la garantía de «cero hallazgos» se mantiene con cualquier ancla,
pero eso solo se ha comprobado con una. (iii) La legibilidad del `INSTRUCTIVO`
—que un jefe que nunca vio la herramienta lo entienda— no es verificable por
programa: se comprueba que las siete secciones y los conceptos clave estén, no
que se entiendan. (iv) `MANUAL.md` es un documento de criterio: no tiene nada que
verificar automáticamente. (v) La plantilla conserva los 16 técnicos y los
códigos de catálogo de ejemplo **a propósito** —la rotación necesita al menos
cuatro por especialidad y los códigos son el andamio del mapeo—, y el
`INSTRUCTIVO` dice explícitamente que ambos se reemplazan. (vi) El recálculo
independiente lo corre el usuario.

---

## 0-ter. Ajustes de tablero — rubro, mix por horas y navegación de vuelta

Tirada de ajustes sobre el DASHBOARD. **No toca** las 10 reglas, la rotación,
VAC, el seguimiento, la capacidad ni el banco (comprobado en el punto f).

### 1) CLASE y RUBRO ya son dos dimensiones distintas

`clase_mantenimiento` mezclaba dos cosas. Ahora son dos atributos independientes,
cada uno en el catálogo que de verdad lo determina:

| | CLASE (`CAT_TIPOS_OT`) | RUBRO (`CAT_ACTIVIDADES`) |
|---|---|---|
| Qué es | la **estrategia** con la que se ataca la falla | una **etiqueta transversal** del trabajo |
| Valores | predictivo · preventivo · correctivo_programado · emergencia | calibracion · lubricacion |
| ¿Partición? | **sí**: sus porcentajes suman 100 | **no**: puede ir vacía, y lo normal es que lo esté |
| Vacío | cae en `SIN CLASIFICAR`, visible en el mix | en blanco, y eso **no** es «sin clasificar» |

**`legal` desaparece como clase.** Una calibración obligatoria es mantenimiento
**preventivo** hecho por exigencia normativa, no una estrategia aparte: tenerla
como quinta clase deformaba el mix hacia abajo el preventivo y mezclaba «cómo
ataco la falla» con «de qué trabajo se trata». `TIPO-P3` se remapea a
`preventivo` y conserva su descripción («Orden de calibración / verificación
legal»), así que ningún dato de entrada cambia de código.

El rubro va en la **actividad** porque es la actividad la que dice qué trabajo se
hace: el tipo de OT no distingue una lubricación de una inspección. Misma regla
que se viene aplicando: cada atributo en el catálogo que lo determina.

**Metas de mix actualizadas** en `PARAMETROS`, editables: 60 predictivo · 25
preventivo · 10 correctivo programado · 5 emergencia. `meta_pct_legal` se
elimina. El indicador de cuadre se conserva y ahora suma cuatro:
`cuadra: 100 %` en el libro entregado.

> Siguen sin ser normativos: no están en EN 15341 ni en VDI 2893. Son convención
> de industria, por eso son parámetros y no constantes.

### 2) Tarjeta 5: fuera el mix, entra lubricación

Se quitó «5 · MIX DE MANTENIMIENTO». Un número único —el desvío máximo— no era
accionable: decía *cuánto* te desvías pero no *qué hacer*, y la distribución ya
se ve en su gráfico. En su lugar, «5 · CUMPLIMIENTO DE LUBRICACIÓN» con
**exactamente el mismo patrón** que la tarjeta 6: cerradas ÷ programadas del mes,
celda de apoyo con las vencidas al corte y rojo forzado si hay alguna. Las seis
tarjetas quedan: adherencia · carga · backlog · OPEX · **lubricación** ·
**calibraciones**.

La tarjeta 6 pasa de medir la clase `legal` a medir el **rubro `calibracion`**,
que es lo que siempre quiso decir.

### 3) El mix se mide por HORAS, con la lectura por conteo al lado

Coherente con una herramienta de capacidad, y es a lo que se refieren los
benchmarks. La **tabla del mix va al lado del gráfico C** (celda `J34`), con una
fila por clase:

`clase · % real (horas) · % meta · desviación (pp) · % real (conteo) · horas · órdenes`

La comparación con la meta se hace **siempre contra el % por horas**; el % por
conteo va como dato secundario y no es decorativo: en el default de julio, el
predictivo es el **27,6 %** de las órdenes pero el **24,7 %** de las horas, y en
el banco de marzo la emergencia es el **29,8 %** de las órdenes y el **37,8 %**
de las horas. Una ruta de predictivo son muchas órdenes cortas; un overhaul es
una sola orden larga. Ver las dos lecturas juntas evita concluir de más.

Semáforo por formato condicional sobre la desviación en puntos porcentuales
(verde ≤ 5 pp, amarillo ≤ 10, rojo > 10), y el signo se conserva (`+`/`−`) para
que se lea si sobra o falta.

### 4) Gráfico nuevo: lubricación por semana

Barras por semana ISO del mes: **programadas vs cerradas**. Sin florituras: se
trata de ver si el plan se cumple o se va postergando. Se alimenta de un bloque
nuevo `SEMANA × RUBRO` de `ADHERENCIA` y reutiliza **las mismas semanas** que el
gráfico A, así que hay una sola definición de «semanas del mes» en todo el
tablero.

Para hacerle sitio sin reorganizar nada, el gráfico D se movió de `J34` a `S34` y
el E se ancló en `S18`. Es el único movimiento de layout, y era necesario: la
tabla del mix tenía que quedar pegada al gráfico C.

### 5) Botón de vuelta al tablero en todas las hojas

Problema real detectado presentando: se navegaba del tablero a una hoja y para
volver había que buscar la pestaña. Ahora **las 19 hojas visibles** (todas menos
el propio `DASHBOARD`) llevan el mismo enlace, con el mismo estilo:

```
=HYPERLINK("#DASHBOARD!A1","◂ VOLVER AL TABLERO")
```

Colocación: **columna A**, en la primera fila libre de la zona congelada, así
queda a la vista sin desplazarse. En 18 hojas cae en `A2`; en `PRESUPUESTO`, cuyo
encabezado ocupa las filas 2–4 con notas, cae en `A5` — también dentro de sus
paneles inmovilizados (`C7`). El generador **no adivina**: busca una fila con `A`
y `B` libres dentro de la zona congelada y, si no la encontrara, aborta la
generación con el nombre de la hoja en vez de pisar una celda.

---

### (a) Reconciliación intacta tras quitar `legal`

Las 4 clases + `SIN CLASIFICAR` siguen sumando el 100 % del mes, y ahora se
comprueba **por partida doble**: en conteo y en horas, en cuatro sitios (las dos
columnas DIFERENCIA del bloque de `ADHERENCIA` y las dos de la tabla del tablero,
todas en 0). Ejemplo del banco, 2026-03: 28 + 87 + 234 + 219 + 12 = **580 HH** =
horas del mes; y 84 órdenes por el otro lado. Los `SIN CLASIFICAR` (12 HH) siguen
visibles, no se disuelven.

### (b) Doble dimensión: la calibración es preventivo Y calibración

Verificado en todos los meses probados: **cero** órdenes de rubro `calibracion`
con una clase distinta de `preventivo`, y el preventivo del mix siempre contiene
al menos esas órdenes. El caso con datos es el banco 2026-12: **10 calibraciones**
que cuentan dentro del preventivo del mix (150 HH) y a la vez alimentan la
tarjeta 6, que marca 0 % con 10 vencidas → **rojo**. Las dos dimensiones
conviven sin contarse dos veces en el mix.

### (c) La tarjeta de lubricación coincide con su origen y responde al mes

| | mes | lubricación | calibración |
|---|---|---:|---:|
| Default | 2026-02 | — (sin órdenes) | — |
| Default | 2026-07 (corte 26) | **70 %** · 3 vencidas | — |
| Default | 2026-08 | **0 %** · 14 vencidas | **0 %** · 2 vencidas |
| Banco | 2026-03 | **87,5 %** | **75 %** · 1 vencida |
| Banco | 2026-11 (corte día 1) | — | — |
| Banco | 2026-12 | **0 %** · 10 vencidas | **0 %** · 10 vencidas |

Cada valor se compara contra la celda de `ADHERENCIA` de la que sale **y** contra
el motor Python, junto con programadas, cerradas y vencidas, incluida la celda de
apoyo del semáforo.

### (d) La tabla del mix cuadra en las dos lecturas

Por cada mes y cada clase se verifican: horas, órdenes, % por horas, % por conteo
y desviación en pp contra las metas de `PARAMETROS`. Los totales dan **100 %** en
las dos columnas de porcentaje, las metas suman **100 %**, y las cuatro celdas de
DIFERENCIA quedan en **0**.

### (e) Botón de vuelta

19 / 19 hojas visibles, todas apuntando a `DASHBOARD!A1`, todas dentro de su zona
congelada y **ninguna pisando contenido** (se comprueba que la celda vecina siga
libre). Comprobado en los dos datasets.

### (f) Recálculo y motor ↔ Excel

| | fórmulas | errores | comparaciones | fallos |
|---|---:|---:|---:|---:|
| Default (compatible, ancla 2026-07-27) | 80.730 | **0** | 15.643 | **0** |
| Banco §7 (compatible, 1.000 órdenes) | 152.180 | **0** | 63.177 | **0** |
| DASHBOARD, default (3 meses × recálculo) | — | **0** | 202 | **0** |
| DASHBOARD, banco (3 meses × recálculo) | — | **0** | 186 | **0** |

**Nada del motor previo cambió de valor.** Comparado con el commit anterior
(`47e804f`), en las 200 órdenes del default solo se mueven dos campos: `rubro`
(columna **nueva**) y `clase_mantenimiento` en **exactamente 4 órdenes** — las
cuatro calibraciones que pasan de `legal` a `preventivo`, que es el cambio
pedido. En `adherencia`, la única novedad es la dimensión `rubro`: **todas** las
claves preexistentes conservan su valor. La prueba obligatoria de `activo` (28
bloques) sigue en 0 diferencias, y los tests de override de turno, precedencia
VAC y presupuesto pasan sin cambios.

Los 16 contadores de `VALIDACION` del banco siguen cuadrando con el manifiesto y
la reconciliación del presupuesto sigue en 12/12 meses.

### Restricciones duras, otra vez sobre los archivos finales

0 VBA · 0 `OFFSET` · 0 `INDIRECT` · 0 referencias de columna completa · **8
marcos de gráfico y 0 formas, conectores o imágenes** (las tarjetas y la tabla
del mix son celdas) · 31 hojas, 20 visibles (32 en el banco) · los 5 gráficos con
autoescala y ambos ejes visibles.

### Qué NO se verificó / supuestos

(i) Solo se recalculan las variantes **compatibles**. (ii) El aspecto visual no
se verifica por programa: se comprueba la estructura (celdas, combinaciones,
reglas de formato condicional, anclaje de gráficos), no el render; el usuario
ajustará tamaños y estética. (iii) El botón de vuelta se comprueba por su
fórmula, su fila y que no pise la celda vecina, no haciendo clic. (iv) Los
rubros del dataset son de demostración: `calibracion` sale de «Certificación
legal» y `lubricacion` de «Lubricación programada»; en una planta real se mapea
en el catálogo. (v) Un rubro vacío es lo normal y no se reporta como incidencia
en ningún sitio. (vi) El recálculo independiente lo corre el usuario.

---

## 0-quater. DASHBOARD — capstone del entregable A

Hoja de presentación en el **puesto #1**, activa al abrir, con paneles
inmovilizados. Es capa **visual y de solo lectura**: no implementa ninguna
regla, no guarda una segunda fuente de verdad y no recalcula nada que ya exista.
**No se tocaron** las 10 reglas, la rotación, VAC, el seguimiento, la capacidad,
el presupuesto ni la generación del banco (comprobado en el punto g).

### Cómo se garantiza que el tablero no tiene números propios

Cada tarjeta KPI es **un `INDEX`/`MATCH` a la fila del mes** en una hoja fuente,
o una **acumulación de celdas que ya calcula `PRESUPUESTO`**. Para que eso fuera
posible sin duplicar lógica, las hojas fuente publican su propio bloque mensual:

| bloque nuevo | hoja | qué publica |
|---|---|---|
| `MES A MES — corte del tablero` | `ADHERENCIA` | corte, adherencia del mes, cumplimiento legal, conteo por clase y su reconciliación |
| `MES A MES — carga vs capacidad productiva` | `PERFIL_HH` | HH planificadas y capacidad productiva por especialidad y mes |
| `AL CORTE DEL TABLERO` | `BACKLOG` | pendientes y HH acumuladas al corte, capacidad semanal y semanas de backlog |

Los tres usan el **mismo criterio** que el bloque semanal que ya tenían (la
adherencia sigue contando solo días hábiles, REGLA-7; la capacidad sigue saliendo
de `horas_disponibles` de `ASIGNACIONES`, REGLA-5). El tablero solo los lee.

### 0) Dato nuevo: `clase_mantenimiento`

Vive en **`CAT_TIPOS_OT`**, no en `CAT_ACTIVIDADES`. La razón es concreta: el
corte que hoy no se podía hacer —correctivo **programado** vs **emergencia**— lo
da únicamente el tipo de OT, porque la actividad («Reparación de falla») es la
misma en ambos casos. Poner la clase en las actividades habría duplicado su
columna `tipo`, que ya dice preventivo/correctivo/predictivo/legal. Es la
decisión **inversa** a la del presupuesto —allí la categoría sí vive en la
actividad, porque describe *qué* se gasta— y responde al mismo criterio: cada
atributo en el catálogo que realmente lo determina.

El catálogo pasa de 4 a 5 tipos para que las cinco clases existan (`TIPO-P3`,
orden legal / calibración). Cada orden **hereda** su clase; si el tipo no está en
catálogo o no trae clase, la orden cae en **`SIN CLASIFICAR`**, visible en el mix
— mismo criterio que el presupuesto. Reparto del default:

| clase | órdenes |
|---|---:|
| preventivo | 75 |
| correctivo_programado | 43 |
| predictivo | 38 |
| emergencia | 38 |
| legal | 4 |
| **SIN CLASIFICAR** | **2** (las dos órdenes sembradas con `TIPO-X9`, fuera de catálogo) |

`ORDENES` gana dos columnas derivadas: `clase_mantenimiento` y `mes_clave`
(`AAAA-MM`, armada con `anio` y `mes` ya calculados para no depender del formato
regional). `ADHERENCIA` gana además un desglose «POR CLASE DE MANTENIMIENTO»,
igual que los que ya tenía por área, sub-área, especialidad y coordinador.

**Metas de mix en `PARAMETROS`, editables:** 25 predictivo · 40 preventivo · 20
correctivo programado · 5 emergencia · 10 legal, más un **indicador de cuadre**
derivado (mismo patrón que el cuadre anual del presupuesto) que avisa si no suman
100. En el libro entregado: `cuadra: 100 %`.

> **Estos porcentajes NO son normativos.** No están en EN 15341 ni en VDI 2893:
> son convención de industria. Por eso son parámetros editables y por eso el
> tablero no cita códigos de indicador de ninguna norma.

### (a) Cada KPI coincide EXACTAMENTE con su hoja de origen

El verificador escribe el mes en `DASHBOARD!B3`, **recalcula el libro** y compara
tres cosas para cada tarjeta: el valor del tablero, la celda de la hoja fuente y
el valor calculado de cero por el motor Python.

| KPI | fórmula del tablero | celda de origen comparada |
|---|---|---|
| 1 · Adherencia | `INDEX`/`MATCH` | `ADHERENCIA!E`(fila del mes) |
| 2 · % carga de capacidad | `INDEX`/`MATCH` | `PERFIL_HH!L`(fila del mes) |
| 3 · Semanas de backlog | `INDEX`/`MATCH` | `BACKLOG!F`(fila del mes) |
| 4 · Ejecución OPEX | `SUMPRODUCT` sobre las celdas mensuales | `PRESUPUESTO`, filas `TOTAL GENERAL` de PRESUPUESTO y REAL |
| 5 · Mix (desvío máximo) | `MAX` sobre el bloque C | conteos de `ADHERENCIA!K:P`(fila del mes) |
| 6 · Cumplimiento legal | `INDEX`/`MATCH` | `ADHERENCIA!I`(fila del mes) |

**Resultado: 0 desviaciones** en las tres vías, en los meses probados. Ningún
KPI tiene un número propio.

### (b) Al cambiar de mes se mueve todo, de forma coherente

Cada fila de esta tabla es **un recálculo completo del libro** con ese mes en el
selector (0 errores de fórmula en todos):

**Default** (fecha de datos 2026-07-27):

| mes | corte aplicado | órdenes | adherencia | % carga | semanas backlog | OPEX acum. | mix (desvío máx.) | legal |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| 2026-02 | 2026-02-28 | 4 | 0 % | — | 0,03 | 25,2 % | 45 pp | — |
| 2026-07 | **2026-07-26** | **29** (31 quedan fuera) | 89,7 % | 34,0 % | 0,40 | 70,6 % | 15,2 pp | — |
| 2026-08 | 2026-08-31 | 56 | 0 % | 36,1 % | 1,22 | 73,5 % | 11,8 pp | **0 % · 2 vencidas** |
| 2027-01 | 2027-01-31 | 2 | 0 % | — | 1,29 | — | 25 pp | — |

**Banco §7** (fecha de datos 2026-11-02):

| mes | corte aplicado | órdenes | adherencia | % carga | semanas backlog | OPEX acum. | mix (desvío máx.) | legal |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| 2026-03 | 2026-03-31 | 84 | 84,5 % | 19,9 % | 0,23 | 102,5 % | 24,8 pp | **75 % · 1 vencida** |
| 2026-11 | **2026-11-01** | **0** (271 quedan fuera) | — | — | 0,69 | 94,6 % | — | — |
| 2026-12 | 2026-12-31 | 60 | 0 % | 10,8 % | 1,96 | 94,1 % | 6,7 pp | **0 % · 10 vencidas** |

Los cuatro gráficos se alimentan de bloques que dependen del mismo selector, así
que se mueven con él: el semanal muestra las semanas ISO del mes elegido, el de
especialidad y el de mix leen la fila de ese mes, y el de OPEX deja en blanco los
meses posteriores al elegido.

Tres celdas en blanco que **son correctas y no fallos**: `% carga` está vacío en
los meses sin filas de `ASIGNACIONES` (el default solo programa 4 semanas, así
que fuera de julio y agosto no hay capacidad que medir); `OPEX` está vacío cuando
el mes no pertenece al año presupuestado (2027-01); y `legal` está vacío cuando
el mes no tiene ninguna orden de esa clase. La adherencia sale 0 % en varios
meses porque el dataset solo tiene cierres (`EJECUCION`) dentro de la ventana
programada.

### (c) El mes en curso corta el DÍA ANTERIOR a la fecha de datos

El corte se ancla a **`p_fecha_datos`** (parámetro nuevo, se inyecta al generar
con el ancla del libro) y **nunca a `HOY()`**: así el tablero es la misma foto
cada vez que se abre. REGLA-3/REGLA-4 siguen usando `HOY()` por diseño — son el
envejecimiento vivo del backlog, no la foto del tablero.

- Default, mes 2026-07 con fecha de datos 2026-07-27 → corte **2026-07-26**.
  Entran **29** órdenes; **31** órdenes de julio con fecha ≥ 27 quedan fuera.
  Ni el día de la fecha de datos ni los posteriores entran.
- Banco, mes 2026-11 con fecha de datos 2026-11-02 → corte **2026-11-01**.
  Entran **0** (la ventana programada arranca el día 2); **271** quedan fuera.
- Meses cerrados y futuros: corte = fin de mes, verificado celda a celda contra
  la columna `corte` de la hoja fuente en los 7 meses probados.

El tablero **lo dice en pantalla**, no solo en la documentación:
`MES EN CURSO: incluye hasta el 2026-07-26 (ni el día de la fecha de datos ni los
posteriores entran)`, y cambia el texto a «mes cerrado» o «mes futuro: muestra lo
PLANIFICADO» según corresponda.

### (d) Reconciliación del mix: nada se pierde

Por cada mes probado se comprobó que **las 5 clases + SIN CLASIFICAR = todas las
órdenes del mes** hasta el corte, en tres sitios a la vez: la columna DIFERENCIA
del bloque de `ADHERENCIA` (**0** en todos), la fila DIFERENCIA del bloque C del
tablero (**0** en todos) y la suma de porcentajes (**100 %** en todos los meses
con órdenes). Ejemplo del banco, 2026-03: predictivo 4 + preventivo 14 +
correctivo programado 34 + emergencia 25 + legal 4 + SIN CLASIFICAR 3 = **84** =
órdenes del mes.

El **cuadre de metas** se probó en los dos sentidos: con los defaults muestra
`cuadra: 100 %`; el indicador es derivado, así que cualquier edición que rompa la
suma lo pone en rojo con el total real.

### (e) Ejes: ninguno con máximo fijo

| gráfico | `y.max` | eje Y visible | eje X visible |
|---|---|---|---|
| A · Cumplimiento semanal del mes vs meta | `None` | sí | sí |
| B · Carga vs capacidad productiva por especialidad | `None` | sí | sí |
| C · Mix de mantenimiento: real vs meta | `None` | sí | sí |
| D · OPEX plan vs real por mes (fijo y variable) | `None` | sí | sí |

Autoescala en los cuatro, con `delete=False` explícito en ambos ejes (dejarlo en
`None` permitía que el consumidor los ocultara) y el eje de categorías forzado
abajo. Etiquetas de datos **solo** en la serie de barras del gráfico A, que es la
que se lee de un vistazo; en los demás manda el eje, ya visible.

### (f) Navegación

Los 7 hipervínculos (`PLAN_SEMANAL · ADHERENCIA · PERFIL_HH · BACKLOG ·
PRESUPUESTO · ORDENES · VALIDACION`) apuntan a hojas que **existen y están
visibles**; ninguno apunta a una hoja oculta. Son `HYPERLINK("#HOJA!A1", …)`:
sin macros, y funcionan igual en Excel y en LibreOffice.

### Higiene: hojas ocultas

**11 hojas ocultas** (12 en el banco) con `hidden`, **nunca `veryHidden`**: los 8
catálogos `CAT_*`, `GUIA_IMPORTAR_ORDENES`, `INICIO`, `_COMPATIBILIDAD` y
`_BANCO_PRUEBA`. Quedan **20 hojas visibles**, `PARAMETROS` entre ellas porque se
ajusta con frecuencia. Se recuperan con clic derecho en cualquier pestaña →
*Mostrar*.

### Restricciones duras: comprobadas sobre los archivos finales

| restricción | comprobación |
|---|---:|
| Sin macros / VBA | 0 `vbaProject` en los 4 archivos; siguen siendo `.xlsx` |
| Sin formas ni objetos de dibujo | 7 marcos de gráfico; **0** formas, **0** conectores, **0** imágenes. Las tarjetas son celdas combinadas con relleno, bordes y formato condicional |
| Sin `LET` ni funciones dinámicas | 0 `OFFSET`, 0 `INDIRECT`, 0 referencias de columna completa, 0 enlaces externos |
| Igual en ambas variantes | El `DASHBOARD` es **idéntico celda a celda** entre `MantPlan.xlsx` y `MantPlan_compatible.xlsx`: **194 celdas comparadas, 0 diferencias**, 4 gráficos en cada uno. Usa `INDEX`/`MATCH` directo, así que no depende del modo de referencias |

### Prohibiciones de presentación

Barrido automático sobre la hoja `DASHBOARD` de los dos libros: **0** apariciones
de un nombre de técnico, **0** menciones de «estimadas vs reales» y **0** códigos
de indicador de norma. El detalle individual sigue donde estaba, en
`SEGUIMIENTO_HH`, y el tablero solo agrega por especialidad.

### (g) Nada del motor previo cambió de valor

Comparación bloque a bloque del motor contra el commit anterior (`5d5df33`), con
la misma ancla: de los **29 bloques** de `calcular_esperado`, el único campo que
cambia es **`tipo_ot`**, y por una razón deliberada: la siembra sintética ahora
deriva el tipo de OT preventivo de la naturaleza de la actividad, para que un
«Análisis predictivo» no quede clasificado como preventivo y el mix signifique
algo. `clasificacion` (REGLA-1) es preventiva en los tipos afectados igual que
antes, así que **ningún agregado se mueve**: perfil, adherencia, presupuesto,
costos, backlog, seguimiento, capacidad, rotación y validación son idénticos.
(`exportar` figura como distinto solo porque incrusta órdenes completas y estas
llevan las dos columnas nuevas; sus cifras —34 órdenes, 275 HH, 202/73
preventiva/correctiva, 15 técnicos, top 5— son las mismas.)

| | fórmulas | errores | comparaciones | fallos |
|---|---:|---:|---:|---:|
| Default (compatible, ancla 2026-07-27) | 79.066 | **0** | 15.436 | **0** |
| Banco §7 (compatible, 1.000 órdenes) | 150.496 | **0** | 62.177 | **0** |
| DASHBOARD, default (4 meses × recálculo) | — | **0** | 150 | **0** |
| DASHBOARD, banco (3 meses × recálculo) | — | **0** | 88 | **0** |

Los 16 contadores de `VALIDACION` del banco siguen cuadrando uno a uno con el
manifiesto de siembra, la ventana programada mantiene 190 programadas / 75
remanente / 0 fuera de especialidad / 0 no disponible / 0 sobre capacidad, y la
reconciliación del presupuesto sigue en 12/12 meses en los dos datasets.

> **Mejora del verificador, de paso.** Ahora lee el ancla del propio libro
> (`PARAMETROS!fecha_datos`) en vez de usar `date.today()`, y mide las cuatro
> columnas de envejecimiento —y los tramos de `BACKLOG`— contra el día real del
> recálculo, inferido del libro y exigido único. Antes, ejecutar la verificación
> un día distinto al del ancla producía cientos de falsos fallos; ahora verifica
> el archivo que de verdad se entrega, se ejecute el día que se ejecute.

### Qué NO se verificó / supuestos

(i) Solo se recalculan las variantes **compatibles**: LibreOffice no evalúa
`XLOOKUP`. Para el tablero esto es menos relevante que nunca, porque sus celdas
son idénticas en las dos variantes (comprobado arriba). (ii) El aspecto visual
—que las tarjetas se vean como tarjetas, los colores, el ancho de columnas— no se
puede verificar por programa: se comprueba la estructura (celdas combinadas,
rellenos, bordes, reglas de formato condicional), no el render. (iii) Los
hipervínculos se verifican por su destino en la fórmula, no haciendo clic.
(iv) El criterio del KPI 5 (desvío máximo en puntos porcentuales, y la clase que
lo causa) es una **elección de legibilidad**, no un estándar; queda documentado
en el propio tablero y en el README. (v) Las metas de mix son convención, no
norma. (vi) `semanas_de_backlog` usa como denominador la capacidad productiva de
una semana con la **dotación activa actual**; no proyecta altas ni bajas.
(vii) El recálculo independiente lo corre el usuario.

---

## 0-quinquies. Correcciones 7.2 — listas dinámicas completas, roster real y `activo` funcional

Tirada de correcciones. **No toca las 10 reglas, el presupuesto, VAC, el
seguimiento ni el banco**: con los 16 técnicos activos el motor devuelve
*exactamente* lo mismo que la versión anterior (comprobado abajo, punto e).

### (a) `EXPORTAR!B3` usa el mismo rango dinámico que `PLAN_SEMANAL`

Era el único selector de semana que había quedado fuera de la corrección 7.1.
Ahora ambos apuntan al mismo nombre definido:

| hoja | celda | validación |
|---|---|---|
| `PLAN_SEMANAL` | `B3` | `lista_semanas_plan` → `PLAN_SEMANAL!$X$3:$X$49` |
| `EXPORTAR` | `B3` | `lista_semanas_plan` → `PLAN_SEMANAL!$X$3:$X$49` |

Una sola fuente: si aparecen semanas nuevas en los datos, las dos listas crecen a
la vez. **Default**: 47 entradas (`(todos)` + 2026-S09 … 2027-S01). **Banco**: 55.

### (b) BARRIDO COMPLETO de validaciones — tabla íntegra del libro

Criterio aplicado: **cualquier lista cuyo contenido cambie al editar un catálogo
o los datos apunta a un rango**; solo quedan literales los dominios
*estructuralmente fijos* (días de la semana, `sí/no`, `lunes/domingo`,
`banco/rotativo`, `preventiva/correctiva`) y los vocabularios propios de las
hojas `CAT_*`, que son la definición misma del dominio y no tienen catálogo
aguas arriba.

| hoja | celdas | clase | origen |
|---|---|---|---|
| `PLAN_SEMANAL` | `B3` | rango | `lista_semanas_plan` → `PLAN_SEMANAL!$X$3:$X$49` |
| `PLAN_SEMANAL` | `D3` | literal | `(todos),lunes,…,domingo` — dominio fijo |
| `PLAN_SEMANAL` | `F3` | rango | `lista_f_turno` → `PARAMETROS!$K$5:$K$9` |
| `PLAN_SEMANAL` | `H3` | rango | `lista_f_coordinador` → `PARAMETROS!$N$5:$N$8` |
| `PLAN_SEMANAL` | `J3` | rango | `lista_f_area` → `PARAMETROS!$L$5:$L$8` |
| `PLAN_SEMANAL` | `L3` | rango | `lista_f_especialidad` → `PARAMETROS!$Q$5:$Q$9` |
| `PLAN_SEMANAL` | `N3` | rango | `lista_f_subarea` → `PARAMETROS!$O$5:$O$11` |
| `PRESUPUESTO` | `C8:O13` | decimal | `>= 0` (no es lista) |
| `EXPORTAR` | `B3` | rango | `lista_semanas_plan` → `PLAN_SEMANAL!$X$3:$X$49` |
| `EXPORTAR` | `D3` | rango | `lista_f_turno` → `PARAMETROS!$K$5:$K$9` |
| `EXPORTAR` | `F3` | rango | `lista_f_coordinador` → `PARAMETROS!$N$5:$N$8` |
| `EXPORTAR` | `H3` | rango | `lista_f_subarea` → `PARAMETROS!$O$5:$O$11` |
| `ORDENES` | `F4:F1203` (centro_costo) | rango | `lista_ceco` → `PARAMETROS!$S$5:$S$14` |
| `ORDENES` | `G4:G1203` (puesto_trabajo) | rango | `lista_puestos` → `PARAMETROS!$T$5:$T$9` |
| `ORDENES` | `H4:H1203` (cod_actividad) | rango | `lista_actividades` → `PARAMETROS!$U$5:$U$12` |
| `ORDENES` | `I4:I1203` (tipo_ot) | rango | `lista_tipos_ot` → `PARAMETROS!$V$5:$V$8` |
| `ORDENES` | `AE4:AE1203` (tecnico_asignado) | rango | `lista_tecnicos` → `TECNICOS!$K$4:$K$19` |
| `ASIGNACIONES` | `I4:I451` (turno_manual) | rango | `lista_turnos` → `CAT_TURNOS!$G$4:$G$9` |
| `PLAN_VACACIONES` | `A4:A103` (tecnico) | rango | `lista_tecnicos` → `TECNICOS!$K$4:$K$19` |
| `PLAN_VACACIONES` | `D4:D103` (motivo) | rango | `lista_motivos_ausencia` → `PARAMETROS!$X$5:$X$7` |
| `TECNICOS` | `C4:C19` (especialidad) | rango | `lista_esp_propias` → `PARAMETROS!$R$5:$R$7` |
| `TECNICOS` | `D4:D19` (area) | rango | `lista_areas` → `PARAMETROS!$M$5:$M$7` |
| `TECNICOS` | `E4:E19` (supervisor) | rango | `lista_supervisores` → `PARAMETROS!$W$5:$W$7` |
| `TECNICOS` | `F4:F19` `H4:H19` (rotativo, activo) | literal | `sí,no` — dominio fijo |
| `TECNICOS` | `G4:G19` (orden_rotacion) | whole | `entre 1 y 30` (no es lista) |
| `CALENDARIO` | `B5:B11` (patrón hábil) | literal | `sí,no` — dominio fijo |
| `CALENDARIO` | `C15:C214` (excepción hábil) | literal | `sí,no` — dominio fijo |
| `CALENDARIO` | `D15:D214` (área) | rango | `lista_areas` → `PARAMETROS!$M$5:$M$7` |
| `CALENDARIO` | `E15:E214` (sub-área) | rango | `lista_subareas` → `PARAMETROS!$P$5:$P$10` |
| `PARAMETROS` | `B15` | literal | `lunes,domingo` — dominio fijo |
| `PARAMETROS` | `B7 B18` | decimal | `entre 1 y 24` (no es lista) |
| `PARAMETROS` | `B8 B13 B14` | decimal | `entre 0 y 1` (no es lista) |
| `PARAMETROS` | `B17` | whole | `entre 1 y 20` (no es lista) |
| `CAT_PUESTOS` | `B4:B8` | literal | `ELE,MEC,AUT,OP,TERCERO` — vocabulario propio |
| `CAT_PUESTOS` | `D4:D8` (es_especialidad_propia) | literal | `sí,no` — dominio fijo |
| `CAT_ACTIVIDADES` | `C4:C11` | literal | `correctivo,preventivo,predictivo,legal` — vocabulario propio |
| `CAT_TIPOS_OT` | `C4:C7` | literal | `preventiva,correctiva` — dominio fijo |
| `CAT_ESTADOS_ERP` | `B4:B7` | literal | `Cerrada,Pendiente` — dominio fijo |
| `CAT_TURNOS` | `E4:E7` | literal | `banco,rotativo` — dominio fijo |
| `CAT_SUPERVISORES` | `C4:C6` (especialidad) | rango | `lista_esp_propias` → `PARAMETROS!$R$5:$R$7` |

**Totales: 40 validaciones · 24 por rango · 11 literales · 5 no-lista**
(19 nombres definidos `lista_*`). Ninguno de los 11 literales depende de un
catálogo editable.

Dos hallazgos del barrido, corregidos aquí aunque no estaban en la lista de (c):
`CALENDARIO` **área** y **sub-área** de las excepciones eran editables y salen de
catálogo (REGLA-10 ya audita «Excepciones con área/sub-área fuera de catálogo»)
pero no tenían desplegable. Ahora apuntan a `lista_areas` y `lista_subareas`, con
blanco permitido porque *área vacía = toda la planta* y *sub-área vacía = toda el
área*.

**Decisión declarada:** `2_IMPORTAR_EJECUCION` (`estado_sistema`, `prioridad`) se
deja **sin** desplegable a propósito. Es una zona de pegado masivo de 1.200 filas
que viene del ERP; `CAT_ESTADOS_ERP` es la tabla de *traducción*, no un dominio
que el usuario elija a mano. Nada se pierde: REGLA-10 reporta los estados sin
traducción.

### El caso `especialidad` de TECNICOS, sin dos listas que puedan divergir

`OP` y `TERCERO` existen en `CAT_PUESTOS` pero **no son personal propio**: no
pueden entrar al ciclo de rotación ni sumar capacidad. La lista de `TECNICOS!C`
no puede, por tanto, apuntar al catálogo completo — y tampoco podía ser una
segunda lista escrita a mano, porque divergiría del catálogo en cuanto alguien
añada una especialidad.

Solución: `CAT_PUESTOS` gana la columna **`es_especialidad_propia` (`sí/no`)**.
`lista_esp_propias` se deriva de ese atributo (`MEC, ELE, AUT`), y la usan tanto
`TECNICOS!C` como `CAT_SUPERVISORES!C`. **Una sola fuente**: marcar `OP` como
propia en el catálogo la haría aparecer en las dos listas a la vez; no hay forma
de que se contradigan.

### (c) Listas nuevas sin bloquear el pegado

Las validaciones añadidas se crean con `showErrorMessage=False`: Excel muestra la
flecha del desplegable pero **no rechaza** lo que se pegue ni lo que se escriba a
mano. Verificado en el libro entregado: las **40** validaciones tienen
`showErrorMessage=false`. El guardián real sigue siendo `VALIDACION`/REGLA-10,
que **no se tocó** — sigue reportando «centros de costo / puestos / actividades /
tipos de OT fuera de catálogo» exactamente igual (los 16 contadores del banco
cuadran con el manifiesto, punto g).

`ORDENES!estado` **no** lleva lista porque no es editable: es una fórmula que
busca `estado_sistema` en `tblEjecucion` y lo traduce con `tblEstados`.

### (d) `CAT_SUPERVISORES`

Catálogo nuevo (`codigo · nombre · especialidad`) en el grupo C de catálogos,
entre `CAT_TURNOS` y `CAT_MOTIVOS_AUSENCIA`. Tres filas: `SUP-MEC` Supervisor
Mecánico (MEC), `SUP-ELE` Supervisor Eléctrico (ELE), `SUP-AUT` Jefe de
Automatización (AUT). El supervisor de cada técnico (6.6) se toma de aquí por su
especialidad, así que renombrar un supervisor en el catálogo se propaga solo.
`CAT_MOTIVOS_AUSENCIA` (Vacaciones anuales · Día libre pagado · Permiso) alimenta
`PLAN_VACACIONES!motivo`.

### (e) `activo` conectado — VERIFICACIÓN OBLIGATORIA

**Cómo funciona.** `lista_tecnicos` ya no apunta a `TECNICOS!B` (todos) sino a la
columna auxiliar `TECNICOS!K`, que **compacta los activos sin huecos**:

```
J4 = IF($H4="sí",COUNTIFS($H$4:$H4,"sí"),"")                 ← numera activos
K4 = IFERROR(INDEX($B$4:$B$19,MATCH(ROW()-3,$J$4:$J$19,0)),"")  ← lista sin huecos
```

Sin funciones de derrame ni `OFFSET`/`INDIRECT`, así que funciona en Excel 2016.
En `ASIGNACIONES`, `n_ciclo` añade `activo="sí"` al `COUNTIFS`, y `posicion_ciclo`
devuelve `""` si el técnico no está activo → sin turno → **0 h** por REGLA-5.

**Prueba 1 — con los 16 activos, cero cambios.** Se importan como módulos el
generador actual y el del commit anterior (`17d958a`), se ejecuta el motor con la
misma ancla `2026-07-27` y se comparan **los 28 bloques** de `calcular_esperado`
tras traducir los nombres del roster viejo al nuevo (correspondencia posicional):

```
A) 16 activos · bloques comparados: 28 · diferencias: 0
   asignaciones prev=448 actual=448 · N por ciclo prev={MEC:7, ELE:7} actual={MEC:7, ELE:7}
```

**Cero diferencias**: órdenes, perfil, adherencia, presupuesto, costos, backlog,
seguimiento, capacidad, rotación y validación son idénticos.

> Durante esta prueba salieron **3 diferencias reales** que hubo que corregir: el
> sintético llevaba dos huecos deliberados clavados a los códigos viejos
> (`TEC-04` sin carga en la 3.ª semana, `TEC-07` sin viernes en la 2.ª). Al
> cambiar el roster dejaron de aplicarse y el reparto de órdenes se movía. Se
> reexpresaron por rotación (`_tec("MEC", 4)` / `_tec("MEC", 7)`), no se
> eliminaron. Es exactamente el tipo de deriva que esta prueba existe para cazar.

**Prueba 2 — un técnico inactivo, sobre el LIBRO recalculado.** No se regenera
nada: se abre `MantPlan_compatible.xlsx` ya entregado, se escribe `no` en la celda
`activo` de **Ana Sánchez** (MEC · PRODUCCION · orden 5) y se recalcula:

| comprobación | resultado |
|---|---|
| Recálculo | 76.144 fórmulas · **0 errores** |
| `lista_tecnicos` | **16 → 15** nombres, sin Ana Sánchez, resto del orden intacto |
| `n_ciclo` en filas MEC·PRODUCCION | **7 → 6** |
| `n_ciclo` en filas ELE·PRODUCCION | **7** (sin cambio) |
| Filas de Ana Sánchez en `ASIGNACIONES` (28) | `posicion_ciclo=""`, `turno=""`, `horas_disponibles=0` en las 28 |
| Capacidad total de Ana Sánchez | **0 h** |
| Filas de otras especialidades/áreas alteradas | **0** |
| Filas MEC·PRODUCCION recalculadas por el anillo más corto | 168 |

El motor da lo mismo al marcarla inactiva en el roster: 15 activos, `N` MEC 7→6,
ELE intacto, **0** filas de `ASIGNACIONES`, y desaparece de `carga_tecnicos`,
`capacidad_tecnicos` y `seguimiento_hh`.

**Diferencia de comportamiento, declarada:** al *generar* el libro, un técnico
inactivo no produce filas de `ASIGNACIONES`; al *editar* el flag en un libro ya
entregado, las filas existen pero quedan neutralizadas (sin posición, sin turno,
0 h). El efecto sobre capacidad, cobertura y seguimiento es el mismo; lo que
cambia es que el libro editado conserva la fila como rastro visible.

### (f) Roster real de 16 técnicos

`Técnico 01…16` y los códigos `TEC-nn` desaparecen del libro y del generador.
Ahora hay 16 personas con **id numérico de 8 dígitos** (80205524 … 80205539) y
nombre real: 7 mecánicos (Carlos Pérez, María Gómez, Luis Rodríguez, Miguel
Martínez, Ana Sánchez, David Torres, Francisco Ramírez), 7 eléctricos (Jorge
Díaz, Roberto Castro, Laura Morales, Ricardo Ortiz, Eduardo Silva, Gabriela
Rojas, Fernando Mendoza) y 2 de automatización no rotativos (Alberto Vargas,
Daniela Medina).

Especialidad, área, rotativo y orden de rotación se mantienen posición por
posición, y por eso la rotación y la cobertura no cambian: **N = 7 MEC y 7 ELE**,
cobertura 1 T1 / 1 T2 / 1 T3 / (N−3) Banco en todas las semanas, los mismos
huecos de VAC. Ningún sitio del generador vuelve a nombrar a una persona a mano:
los casos sintéticos (vacaciones demo, órdenes de fin de semana, ajustes) usan
`_tec(especialidad, orden_rotacion)`.

### Unificación del dominio `sí/no`, con una excepción declarada

`TECNICOS!rotativo` y `TECNICOS!activo` usaban `SI/NO` en mayúscula mientras el
resto del libro (`es_habil`, `en_vacaciones`, `trabaja_domingo`, catálogos) usaba
`sí/no`. Ahora todo el libro habla el mismo dominio `sí,no`, definido una sola vez
en el generador (`SI, NO = "sí", "no"`).

Al hacerlo apareció un bug latente: `imprimir_resumen` filtraba los rotativos con
`t[TEC_ROT] == "SI"` y, tras la unificación, **la tabla de rotación de
`--resumen` salía vacía** (los encabezados y la cobertura sí, las filas por
técnico no). Corregido: filtra por `SI` y sobre `TECNICOS_ACTIVOS`, y la columna
de nombre se ensanchó para que quepa el nombre real completo.

**Excepción declarada:** `PERFIL_HH` conserva `"SI"/"NO"` en el indicador de
cumplimiento de la meta de REGLA-9. No es el atributo `sí/no` de un catálogo sino
la **salida de una regla**, y esta tirada tiene prohibido tocar las 10 reglas;
cambiar ese literal alteraría lo que la regla emite y lo que el verificador
compara.

### (g) Recálculo independiente y contraste motor ↔ Excel

| | fórmulas | errores | comparaciones | fallos |
|---|---:|---:|---:|---:|
| Default (compatible, ancla 2026-07-27) | 76.144 | **0** | 14.994 | **0** |
| Banco §7 (compatible, 1.000 órdenes) | 147.508 | **0** | 60.177 | **0** |

Los 16 contadores de `VALIDACION` del banco siguen cuadrando **uno a uno** con el
manifiesto de siembra, la ventana programada mantiene 190 programadas / 75
remanente / 0 fuera de especialidad / 0 no disponible / 0 sobre capacidad, y la
reconciliación del presupuesto sigue en 12/12 meses. Los tests de edición
anteriores (override de turno, precedencia VAC, las cinco pruebas del
presupuesto, EXPORTAR en semana vacía) se reejecutaron y pasan. Higiene de
fórmulas auditada sobre los **cuatro** archivos finales: 0 `OFFSET`, 0
`INDIRECT`, 0 referencias de columna completa, 0 enlaces externos.

### Qué NO se verificó / supuestos

(i) Solo se recalculan las variantes **compatibles**: LibreOffice no evalúa
`XLOOKUP`, así que las estructuradas se validan por construcción (mismo código,
misma tabla de campos). (ii) El comportamiento del desplegable *en Excel* —que
muestre la flecha y no bloquee el pegado— se comprueba leyendo la propiedad
`showErrorMessage=false` del XML, no abriendo Excel. (iii) `lista_tecnicos` tiene
16 celdas fijas: si algún día hay más de 16 técnicos hay que ampliar el rango de
`tblTecnicos` (es el mismo límite que ya tenía la tabla). (iv) Los nombres del
roster son datos de demostración: no hay validación de unicidad de nombre, y la
compactación de `K` asume nombres distintos entre sí. (v) Las secciones
históricas de más abajo conservan los nombres `Técnico nn` de la versión en
que se escribieron: son registro de lo verificado entonces, no del libro
actual. (vi) **No se implementó el
DASHBOARD.** (vii) El recálculo independiente lo corre el usuario.

---

## 0-sexies. PRESUPUESTO OPEX — plan mensual manual vs gasto real por categoría

Hoja **derivada** nueva (`PRESUPUESTO`), colocada en el grupo de presentación
justo después de `COSTOS`. **No toca las 10 reglas, la rotación, VAC, el
seguimiento, la capacidad ni la generación del banco** (comprobado en el punto g).
Alcance **solo OPEX**: materiales, servicios y terceros; la mano de obra propia no
es costo y no entra ni en el plan ni en el real. Nada de CAPEX.

Clasificación por **catálogo**: `CAT_ACTIVIDADES` gana `categoria_presupuesto` y
`clasificacion` (fijo/variable). Se eligió actividades y no tipos de OT porque la
actividad describe *qué* se gasta; el tipo de OT solo separa
preventiva/correctiva. Seis categorías: 3 fijas (Repuestos mandatorios, Servicios
contratados, Overhauls programados) y 3 variables (Correctivos - materiales,
Servicios requeridos, Refacciones nuevas).

### (a) RECONCILIACIÓN — obligatoria, verificada en los 12 meses

Por cada mes: **suma de reales por categoría + SIN CLASIFICAR = total de COSTOS
del mes**. La hoja lleva dos filas de control («CONTROL — total de COSTOS del
mes» y «DIFERENCIA (debe ser 0)», roja si no cuadra) y el verificador exige
ambas cosas leyendo el **libro recalculado**:

| | meses reconciliados | diferencia |
|---|---:|---:|
| Default | **12 / 12** | 0 en todos |
| Banco | **12 / 12** | 0 en todos |

Sin fugas ni doble conteo. El real usa el **mismo campo** que COSTOS
(`costo_total`, REGLA-8) y la **misma convención de mes** (`anio`/`mes` de la
orden): no se creó una segunda forma de sumar costos.

### (b) Gasto sin categoría → fila SIN CLASIFICAR (probado a propósito)

Dos caminos llevan a SIN CLASIFICAR y ambos se comprobaron:

1. **Actividad fuera de catálogo** (`ACT-99` ya sembrada): su costo aparece en
   SIN CLASIFICAR en el libro tal cual se entrega — **160** en el default y
   **480** en el banco.
2. **Actividad en catálogo pero sin categoría**: se borró a propósito la
   `categoria_presupuesto` de `ACT-01` en `CAT_ACTIVIDADES` y se recalculó. Su
   gasto **se movió íntegro**: «Repuestos mandatorios» 10.275 → 5.550 y
   «SIN CLASIFICAR» 160 → 4.885 (**4.725** movidos, exactamente lo que perdió la
   categoría), y la **reconciliación siguió en 0 los 12 meses**. El gasto no
   desaparece nunca.

### (c) Desviación, % y semáforo

`desviacion = real − presupuesto` y `desviacion_pct = desviacion / presupuesto`
(vacío si el presupuesto es 0) coinciden celda a celda con el motor en las 5
matrices × 10 filas × 12 meses. El semáforo responde al parámetro: al subir
`tolerancia_desviacion_presupuesto` de **0,10 a 0,50** y recalcular, **12 celdas
de estado cambian** y las marcadas «dentro» pasan de **7 a 19**. No hay ningún
umbral hardcodeado.

### (d) Cuadre de la distribución mensual

`suma_12_meses` vs `presupuesto_anual` con indicador propio. Probado: restando
500 a un mes de «Repuestos mandatorios» y recalculando, el indicador pasa de
**«cuadra»** a **«DESCUADRE: -500 vs anual»** (y se resalta en rojo).

### (e) YTD acumula hasta el mes de la fecha de datos y no más

Mes de corte = mes de la fecha de datos si el año en curso es el presupuestado;
12 si ya pasó, 0 si no ha empezado. Comprobado en el libro recalculado del
default: corte **mes 7**, YTD del total = **25.760**, que es exactamente la suma
de los meses 1..7 — y **no** los **31.590** del año completo. En el banco el
corte es el **mes 11**.

### (f) Subtotales y total general

Para los 12 meses y en las matrices de presupuesto y real se verificó que
**Subtotal FIJO**, **Subtotal VARIABLE** y **TOTAL GENERAL** son exactamente la
suma de sus filas miembro (el total incluye SIN CLASIFICAR, que es lo que cierra
la reconciliación).

### (g) Recálculo y comparación motor ↔ Excel

| | fórmulas | errores | comparaciones | desviaciones |
|---|---:|---:|---:|---:|
| Default (`MantPlan_compatible.xlsx`) | 76.074 | **0** | 14.994 | **0** |
| Banco (`MantPlan_banco_compatible.xlsx`) | 147.438 | **0** | 60.177 | **0** |

Nada del motor previo cambió: rotación, VAC, seguimiento, capacidad, adherencia y
el manifiesto del banco dan los mismos valores que en v3.0.1 (las comparaciones
crecieron solo por las celdas nuevas del presupuesto: +816 en el default y +624 en
el banco).

**Datos sintéticos**: el plan se siembra calibrado sobre el gasto real con
factores por mes, y el semáforo queda ejercitado en ambos datasets —default:
7 «dentro», 6 «sobre», 42 «bajo»; banco: 20 «dentro», 12 «sobre», 36 «bajo».

**Qué NO verifiqué / supuestos.** (i) No recalculé los libros principales
(`XLOOKUP`): LibreOffice no los evalúa. (ii) En el banco hay gasto real en
**11 de 12 meses**: diciembre tiene órdenes pero ninguna notificación, porque la
regla realista de §7 solo empareja ejecuciones con órdenes vencidas o de la
ventana en curso — no toqué la generación del banco para forzarlo. El bloque de
comparación sí está poblado en los 12 meses (plan, desviación y estado se
calculan igual). (iii) El indicador de cuadre se entrega **cuadrando** en las 6
categorías; el descuadre se probó editando el libro, no dejándolo sembrado.
(iv) El YTD usa `HOY()` como fecha de datos, así que en el banco (ancla fija) se
mide contra el día de apertura, igual que las columnas de envejecimiento.
(v) No se implementó el DASHBOARD. (vi) El recálculo independiente lo corre el usuario.

---

## 0-septies. Correcciones 7.1 — selector de semanas, gráfico, hoja guía y orden de hojas

Tirada de correcciones sobre el entregable A. **No toca las 10 reglas, la
rotación, VAC, el seguimiento, la capacidad ni la generación del banco**: los
números de §7 y de 6.x quedan idénticos (verificado abajo, punto e).

### (a) Selector de semanas dinámico — bug corregido

El desplegable de `PLAN_SEMANAL!B3` era una lista **literal** con solo las
semanas de la ventana del plan (`"(todos),2026-S30,…,2026-S33"`), mientras que la
grilla mostraba filas de todo el año: no se podía filtrar por semanas que sí
tenían datos.

- Ahora la lista se construye desde **todas las semanas presentes en los datos**
  = unión de la serie de ORDENES y de las semanas de ASIGNACIONES.
- Como supera el límite de ~255 caracteres de una validación literal, va a un
  **rango auxiliar oculto** (`PLAN_SEMANAL!$X$3:$X$n`) y la validación apunta al
  nombre definido **`lista_semanas_plan`**. Comprobado en el libro generado:
  `DV(B3).formula1 = "lista_semanas_plan"`.
- **Default**: 47 entradas — `(todos)` + 2026-S09 … 2027-S01.
  **Banco**: 55 entradas — `(todos)` + 2026-S01 … 2027-S01.
- **Prueba funcional** (la que importa): con `B3 = 2026-S09` —una semana **fuera**
  de la ventana programada— el libro recalculado devuelve **4 órdenes · 22 HH**
  en los contadores B5/D5. Antes esa semana ni siquiera era seleccionable.
- Los demás selectores de esa fila salen de **catálogo** (turno de `CAT_TURNOS`;
  área, sub-área y coordinador de `CAT_CENTROS_COSTO`; especialidad de
  `CAT_PUESTOS`) o de un **dominio fijo** (día): se revisaron y se dejan como
  lista literal, que es correcto para ellos.

### (b) Gráfico de PLAN_SEMANAL — bug corregido

Diagnóstico confirmado sobre el XML del archivo anterior
(`xl/charts/chart1.xml`): `<max val="46.76"/>` fijo, sin elemento `<delete>` en
ninguno de los dos ejes, `axPos="l"` **también** en el eje de categorías, y
`showVal` en las **dos** series (16 técnicos × 2 = 32 etiquetas encimadas).

Estado tras la corrección, leído del XML regenerado:

| aspecto | antes | ahora |
|---|---|---|
| máximo del eje Y | `<max val="46.76"/>` | **ninguno** (autoescala) |
| `<delete>` de los ejes | ausente | `0` y `0` (**ambos visibles**) |
| `axPos` | `l`, `l` | **`b`** (categorías) y `l` (valores) |
| etiquetas de datos (`showVal`) | 2 series | **1** (solo sobreasignación) |
| combinado | barras + línea | **se mantiene**: 3 series, `<barChart>` + `<lineChart>` |

Títulos de eje: **HH** (valores) y **Técnico** (categorías); marcas de escala
hacia fuera. La línea de **capacidad** sigue sobre el mismo eje de valores. Como
los rangos T/U/V ya dependen de los selectores, al cambiar semana/día/técnico el
gráfico se recalcula y, sin máximo fijo, **se reescala solo**.

### (c) Hoja de importar órdenes — ya no invita a pegar

Se mantiene el diseño: las órdenes se pegan en `ORDENES!A4`; **no** se creó tabla
de staging ni se duplicó el pegado.

- **Antes de renombrar se comprobó** (no se asumió) que la hoja no estaba
  referenciada: barrido de todo el `.xlsx` (todos los `.xml` y `.rels`) →
  `1_IMPORTAR_ORDENES` aparecía **solo** en `<sheets>` de `xl/workbook.xml`, la
  entrada del propio libro. **Cero** menciones en fórmulas, `definedNames`,
  tablas o validaciones. El renombrado es seguro.
- `1_IMPORTAR_ORDENES` → **`GUIA_IMPORTAR_ORDENES`**, con pestaña **gris de
  guía** (antes naranja de zona de pegado).
- Encabezado inequívoco: «**⚠ ESTA HOJA NO RECIBE DATOS** — es solo una guía de
  formato» y debajo «Las órdenes se pegan en **ORDENES!A4** (columnas A:L, en un
  solo bloque)».
- Se **quitó la fila de cabeceras horizontal** que invitaba a pegar: el layout se
  muestra ahora **en vertical** (una fila por columna esperada: letra, nombre y
  dos ejemplos), con las columnas de ejemplo rotuladas «EJEMPLO (no pegar)».
- `2_IMPORTAR_EJECUCION` **no se tocó** en estructura; solo su encabezado dice
  ahora «**✔ ZONA DE PEGADO REAL** — aquí SÍ se pegan datos», más una línea que
  aclara que las órdenes no van ahí. El contraste entre ambas es obvio.

### (d) Orden de las hojas

Ordenadas por uso. Verificado que el orden es **exactamente** el pedido y el
**mismo en los cuatro libros** (comparación programática de `wb.sheetnames`):

- **A. Presentación**: PLAN_SEMANAL · ADHERENCIA · PERFIL_HH · BACKLOG · COSTOS ·
  EQUIPOS_CRITICOS · SEGUIMIENTO_HH · SEGUIMIENTO_MENSUAL · EXPORTAR
- **B. Trabajo diario**: ORDENES · ASIGNACIONES · AJUSTES · PLAN_VACACIONES ·
  2_IMPORTAR_EJECUCION · TECNICOS · CALENDARIO · VALIDACION
- **C. Configuración, catálogos y guías**: PARAMETROS · CAT_CENTROS_COSTO ·
  CAT_PUESTOS · CAT_ACTIVIDADES · CAT_TIPOS_OT · CAT_ESTADOS_ERP · CAT_TURNOS ·
  INICIO · GUIA_IMPORTAR_ORDENES · _COMPATIBILIDAD · _BANCO_PRUEBA (solo banco)

El **puesto #1 queda libre** para el DASHBOARD de la próxima tirada. La hoja
activa al abrir es `PLAN_SEMANAL`. Cualquier hoja no listada caería al final sin
perderse (salvaguarda del reordenador). 27 hojas en el default, 28 en el banco.

### (e) Recálculo y comparación: sin regresión

Reordenar hojas no cambia fórmulas (referencian por nombre), pero **se verificó**:

| | fórmulas | errores | comparaciones | desviaciones |
|---|---:|---:|---:|---:|
| Default (`MantPlan_compatible.xlsx`) | 74.182 | **0** | 14.178 | **0** |
| Banco (`MantPlan_banco_compatible.xlsx`) | 145.546 | **0** | 59.553 | **0** |

Cifras **idénticas** a las de v3.0.0: ninguna de las cuatro correcciones movió un
solo valor calculado.

**Qué NO verifiqué / supuestos.** (i) No recalculé los libros principales
(`XLOOKUP`): LibreOffice no los evalúa. (ii) El aspecto visual del gráfico
(reescalado y legibilidad al cambiar selectores) se verificó **estructuralmente**
sobre el XML —sin máximo fijo, ejes con `delete=0`, una sola serie con
etiquetas— y funcionalmente por el recálculo de los rangos que lo alimentan; el
juicio final de legibilidad es visual y lo hace el usuario al abrirlo. (iii) No
se implementó el DASHBOARD (queda para la próxima tirada). (iv) El recálculo
independiente lo corre el usuario.

---

# (histórico) VERIFICACION — MantPlan v3.0.0

Reporte de verificación del entregable A. Esta versión añade **§7 — banco de
prueba**: volumen de un año en crudo + una ventana programada, como OPCIÓN del
generador. Sobre 6.5/6.6 (seguimiento y supervisor), 6.4 (VAC), 6.3 (rotación),
6.2 (CAT_TURNOS), 6.1 (jornada 8 h), v2.4 (calendario), v2.3 (sub_area), v2.2
(EXPORTAR), v2.1 y v2.0. Corridas: dataset por defecto con ancla **2026-07-27**;
banco con ancla FIJA **2026-11-02**.

## §7 — Banco de prueba: un año en crudo + ventana programada

Cambio de **datos y de opciones del generador**: no toca las 10 reglas, ni la
rotación, ni VAC, ni el seguimiento, ni la capacidad. Se activa con
`--anio-completo`; **sin flags el generador produce exactamente el dataset de 4
semanas de siempre** (verificado, punto 17). Ancla FIJA (2026): el banco nunca
depende de `date.today()`.

### Volumen y agilidad (puntos 3, 4 y 16 — medidos)

| Métrica | Dataset por defecto | Banco §7 |
|---|---:|---:|
| Órdenes (`ORDENES`) | 200 | **1.000** |
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

## 6.5 + 6.6 — horas reales de seguimiento y supervisor fijo

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

## 6.4 — vacaciones que arrastran (VAC automático, posición vacía)

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

## 6.3 — rotación automática derivada por especialidad

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

## 6.2 — catálogo de turnos con franja horaria (CAT_TURNOS)

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

## 6.1 — jornada 8 h y base semanal 48 h (L-S)

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
