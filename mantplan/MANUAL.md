# MANUAL.md — por qué MantPlan está hecho así

Este documento no explica **cómo** se usa la herramienta (eso está en la hoja
`INSTRUCTIVO`, dentro del propio libro). Explica **por qué** toma las decisiones
que toma, para poder defenderlas cuando alguien las cuestione en una reunión.

Cada sección tiene lo mismo: la decisión, el motivo y la consecuencia práctica —
incluido lo que se pierde, cuando se pierde algo.

---

## 1. La mano de obra propia NO es costo

**Decisión.** El costo de una orden son materiales, servicios y terceros. Las
horas de los técnicos de planta no se imputan a la orden ni aparecen en
`COSTOS` ni en `PRESUPUESTO`.

**Motivo.** La nómina de mantenimiento es un costo **fijo** que se paga esté la
orden hecha o no. Imputarla a la orden produce dos efectos perversos: hace que
una semana con mucha carga "cueste más" cuando en realidad se gastó lo mismo, y
convierte cualquier comparación entre meses en una comparación de horas
imputadas, no de dinero salido de caja. La mano de obra propia es un problema de
**capacidad**, no de costo.

**Consecuencia.** Las horas se miden donde importan: `PERFIL_HH` (¿cabe el
trabajo?), `SEGUIMIENTO_HH` (¿cuántas horas hizo cada técnico?) y el KPI de carga
del tablero. Y el presupuesto mide dinero real contra dinero planificado, sin
ruido. Si alguien necesita un costo "totalmente cargado" para un análisis de
inversión, ese cálculo se hace fuera, con la tarifa que corresponda: aquí no se
inventa.

---

## 2. Base de 48 h (L–S), y el domingo del relevo no se planifica

**Decisión.** La capacidad base de un técnico es **48 h semanales**: 6 días
(lunes a sábado) × 8 h. El domingo en que un técnico entra de relevo se registra
como horas reales (56 h esa semana) pero **no se planifica trabajo sobre él**.

**Motivo.** El domingo del relevo es un superávit que ocurre por cómo rota el
turno, no capacidad disponible para programar. Si se sumara a la base, el
planificador acabaría llenando domingos de forma sistemática — que es exactamente
lo que el esquema de turnos intenta evitar — y la capacidad "disponible"
dependería de en qué punto del ciclo está cada persona.

**Consecuencia.** La planificación es estable: todas las semanas tienen la misma
base y el reparto no se deforma por la rotación. El domingo trabajado se ve en
`SEGUIMIENTO_HH` y `SEGUIMIENTO_MENSUAL` — sirve para el bono y para el control
de horas — pero nunca infla el `% de carga`.

---

## 3. Rotación derivada, con override manual

**Decisión.** El turno de cada técnico se **calcula** a partir de su
`orden_rotacion` y de la semana: el anillo avanza una posición por semana y
garantiza 1 técnico en T1, 1 en T2, 1 en T3 y el resto en Banco, por especialidad
y área. Para una excepción puntual existe `turno_manual`, que manda sobre lo
derivado; al vaciarlo, vuelve la rotación.

**Motivo.** Un cuadro de turnos escrito a mano se desincroniza en cuanto alguien
falta, entra o cambia de posición, y nadie se entera hasta que hay un turno sin
cubrir. Derivarlo hace imposible ese error: la cobertura es una propiedad de la
fórmula, no de la disciplina de quien llena la tabla.

**Consecuencia.** Añadir o quitar un técnico recalcula el ciclo entero solo. Las
excepciones reales (un cambio pactado, una cobertura puntual) siguen siendo
posibles en una celda, y quedan **visibles** como lo que son: una excepción, no
la norma.

---

## 4. Vacaciones = hueco visible (Modelo A)

**Decisión.** Cuando un técnico está de vacaciones, su posición del ciclo **queda
vacía**. El sistema no reasigna automáticamente a nadie para taparla.

**Motivo.** Se evaluó la alternativa —recalcular el anillo con N−1 y repartir— y
se descartó a propósito. Tapar el hueco automáticamente esconde la decisión más
importante de la semana: *alguien tiene que cubrir ese turno, y hay que decidir
quién*. Un cuadro que siempre se ve completo transmite que no hay problema, y el
problema aparece el lunes a las seis de la mañana.

**Consecuencia.** El hueco se ve y obliga a decidir. La cobertura la elige el
supervisor y la escribe en `turno_manual`, que además deja registro de quién
cubrió y cuándo. El coste de esta decisión es que el archivo no "resuelve" solo
las vacaciones; el beneficio es que nadie descubre la brecha tarde.

---

## 5. La adherencia excluye los días no laborables del denominador

**Decisión.** `REGLA-7` mide órdenes cerradas ÷ órdenes programadas, contando
**solo** las que caen en día hábil según `CALENDARIO`.

**Motivo.** Una orden programada un domingo o un feriado no se incumplió: se
programó mal. Dejarla en el denominador castiga al equipo por un error de
programación y, peor, hace que la métrica baje cuando el planificador se
equivoca, en vez de cuando el trabajo no se hace.

**Consecuencia.** La adherencia mide lo que dice medir. Las órdenes en día no
laborable no desaparecen: `VALIDACION` las reporta como «Órdenes programadas en
día NO laborable», que es donde deben corregirse.

---

## 6. El tablero NO muestra datos por técnico

**Decisión.** El `DASHBOARD` no tiene ni un solo indicador por persona. Todo lo
que muestra está agregado por especialidad o por área.

**Motivo.** Es una decisión sobre cómo se leen los números en una sala, no sobre
qué se puede calcular. Proyectado en una reunión, un ranking por técnico se lee
como culpa individual — cuando en la inmensa mayoría de los casos la causa es
falta de horas, una reprogramación, un permiso que no salió o un repuesto que no
llegó. El dato individual pierde su contexto justo en el momento en que más
gente lo está mirando.

**Consecuencia.** El detalle por persona **existe y no se ha quitado**: está en
`SEGUIMIENTO_HH` y `SEGUIMIENTO_MENSUAL`, donde el supervisor lo usa para lo que
sirve — conversaciones uno a uno, control de horas, bono. Lo que cambia es la
audiencia, no la disponibilidad del dato.

---

## 7. Clase (mix) y rubro (transversal) son dimensiones distintas

**Decisión.** **Clase** es la estrategia con la que se ataca la falla —
`predictivo`, `preventivo`, `correctivo_programado`, `emergencia` — y es una
partición: sus porcentajes suman 100. **Rubro** es una etiqueta transversal del
trabajo — `calibracion`, `lubricacion` — que puede estar vacía y no suma con las
clases.

**Motivo.** Son preguntas diferentes. «¿Cómo reparto mi esfuerzo entre estrategias?»
y «¿estoy cumpliendo el plan de lubricación?» no se responden con la misma lista.
Al principio `legal` estaba como quinta clase, y estaba mal: una calibración
obligatoria **es mantenimiento preventivo** hecho por exigencia normativa. Tenerla
aparte desinflaba artificialmente el preventivo y mezclaba el *cómo* con el *qué*.

**Consecuencia.** Una calibración cuenta dentro del preventivo del mix **y**
alimenta su propia tarjeta de cumplimiento, sin contarse dos veces. Cada atributo
vive en el catálogo que de verdad lo determina: la clase en `CAT_TIPOS_OT` —el
único que distingue un correctivo programado de una emergencia, porque la
actividad es la misma en ambos— y el rubro en `CAT_ACTIVIDADES`, porque es la
actividad la que dice qué trabajo se hace.

---

## 8. Las metas de mix (60/25/10/5) son convención, no norma

**Decisión.** Las metas por defecto son 60 % predictivo, 25 % preventivo, 10 %
correctivo programado y 5 % emergencia, y viven en `PARAMETROS` como parámetros
editables, con un indicador que avisa si no suman 100.

**Motivo.** **No están en EN 15341 ni en VDI 2893.** Son convención de industria.
Presentarlas como si fueran normativas sería falso y, además, contraproducente: la
mezcla correcta depende de la criticidad de los activos, su edad, la
instrumentación disponible y la estrategia de la planta. Una planta nueva con
sensores y una planta de 30 años no deberían tener el mismo objetivo.

**Consecuencia.** Se ajustan sin tocar código, y el libro **no cita códigos de
indicador de ninguna norma** (E11, O19 y similares): usa el nombre del indicador.
Si alguien pregunta «¿de dónde sale el 60 %?», la respuesta honesta es «es la
meta que nos pusimos, y se cambia aquí».

---

## 9. El mix se mide en horas; el conteo va al lado

**Decisión.** El porcentaje que se compara contra la meta es el de **horas de
mano de obra**. El porcentaje por conteo de órdenes se muestra al lado, como dato
secundario.

**Motivo.** Es una herramienta de capacidad: lo que se reparte son horas. Y las
dos lecturas difieren de verdad — una ruta de predictivo son muchas órdenes
cortas, un overhaul es una sola orden larga. En los datos de ejemplo, la
emergencia llega a ser el 29,8 % de las órdenes y el 37,8 % de las horas.

**Consecuencia.** Se decide sobre horas, que es donde duele, y al tener las dos
columnas juntas nadie concluye de más a partir de un conteo.

---

## 10. Lubricación no tiene meta configurable

**Decisión.** La tarjeta de lubricación (y la de calibraciones) mide
**cumplimiento**: cerradas ÷ programadas del mes. No hay un parámetro de meta.

**Motivo.** El objetivo de un plan de lubricación es hacerlo entero: el 100 %.
Poner una meta configurable invitaría a bajarla cuando no se cumple, que es
exactamente el comportamiento que la métrica debería impedir. Es distinto del
mix, donde la meta sí es una decisión de estrategia.

**Consecuencia.** El semáforo se dispara con cualquier orden vencida al corte,
aunque el porcentaje sea alto. Si algún día hace falta un umbral de tolerancia,
se añade como parámetro — pero será una decisión explícita, no un hueco que ya
estaba ahí.

---

## 11. VALIDACION reporta y nunca bloquea

**Decisión.** `REGLA-10` cuenta y muestra los problemas de la importación, pero
no impide pegar nada. Las validaciones de las celdas son desplegables de ayuda,
no barreras: no rechazan lo que se pega.

**Motivo.** Un libro que rechaza un pegado masivo del ERP es un libro que el
planificador deja de usar a la tercera vez. Y el dato "malo" también es
información: una orden con un centro de costo que el catálogo no conoce sigue
siendo trabajo real que hay que programar.

**Consecuencia.** Todo entra y nada se pierde; lo que no cuadra queda listado en
`VALIDACION` para corregirlo en el catálogo o en el origen. El archivo de
plantilla abre con los **16 chequeos en cero**, precisamente para que el primer
hallazgo que alguien vea sea suyo y no ruido de fábrica.

---

## 12. Sin macros

**Decisión.** El libro es un `.xlsx` sin una sola línea de VBA. La navegación se
resuelve con `HYPERLINK` y los avisos con formato condicional.

**Motivo.** Un archivo con macros se bloquea al llegar por correo, lo frena la
política de seguridad de medio mundo, no abre en la versión web y obliga a
explicar por qué hay que habilitar contenido. Una herramienta de gestión que no
se puede compartir sin fricción no se comparte.

**Consecuencia.** Se envía, se abre y funciona en cualquier entorno. El precio es
que algunas cosas cuestan más de construir (las tarjetas del tablero son celdas
combinadas con relleno y bordes, no formas) y que no hay automatismos de un clic.
Compensa.

---

## 13. Dos variantes: principal y compatible

**Decisión.** Cada libro se genera dos veces: la variante principal usa `XLOOKUP`
y referencias estructuradas; la `_compatible` hace exactamente lo mismo con
`INDEX/MATCH` y rangos A1 acotados.

**Motivo.** `XLOOKUP` necesita Excel 2021 o 365. Excel 2016 y LibreOffice no lo
conocen y muestran un error de nombre de función en cientos de celdas. En vez de
renunciar a las fórmulas modernas o dejar fuera a media plantilla, se generan las
dos desde el **mismo código**, así no pueden divergir.

**Consecuencia.** Use la principal si tiene Excel 2021/365; la `_compatible` si
tiene Excel 2016 o LibreOffice. Los números son idénticos —se verifican uno
contra otro—, y de hecho la hoja `DASHBOARD` es idéntica celda a celda en ambas.

---

## 14. Agnóstico de empresa y de ERP

**Decisión.** No hay ni un código de empresa, ni un nombre de planta, ni un
código de ERP dentro de una fórmula. Todo lo específico vive en los catálogos
`CAT_*` y en `PARAMETROS`.

**Motivo.** Es lo que separa una herramienta de una plantilla desechable. Si los
códigos están dentro de las fórmulas, adaptarla a otra planta es reescribirla, y
cada copia acaba siendo una versión distinta que nadie sabe mantener.

**Consecuencia.** Poner en marcha la herramienta en otra planta es **mapear
catálogos**: traducir los tipos de OT, los estados, los centros de costo, los
puestos y las actividades del ERP de esa planta. Cero código. Ese mapeo es el
trabajo real de implantación, y es exactamente donde debe estar.

---

## 15. Tres archivos, tres propósitos

**Decisión.** El repositorio produce tres pares de archivos: **demo** (200
órdenes sintéticas), **plantilla** (8 órdenes de ejemplo, limpias) y **banco**
(1.000 órdenes de un año).

**Motivo.** Cada uno responde a una necesidad distinta y mezclarlos causa daño.
El demo enseña el tablero lleno —sirve para presentar—, pero sus datos incluyen
casos sucios sembrados a propósito para ejercitar las validaciones: empezar a
trabajar sobre él significa heredar basura. La plantilla arranca limpia. El banco
existe para probar la herramienta a volumen real y **no** para trabajar.

**Consecuencia.** Para trabajar con datos reales se usa **siempre**
`MantPlan_plantilla.xlsx` (o su variante compatible). El demo es para enseñar; el
banco, para probar. Están claramente etiquetados dentro del propio libro, en la
hoja `INSTRUCTIVO`.

---

## 16. Lo generado se marca aunque no lleve fórmula

**Decisión.** En las hojas de **resultado**, todas las columnas van marcadas como
calculadas —relleno rojo muy claro y encabezado en rojo—, tengan fórmula o un
valor escrito por el generador. En las hojas **mixtas** sigue marcándose la celda
con fórmula.

**Motivo.** El primer criterio («la celda contiene una fórmula») era elegante y
se mantenía solo, pero describía mal la realidad: `SEGUIMIENTO_HH` escribe
`tecnico` y `semana` como texto, `SEGUIMIENTO_MENSUAL` escribe `tecnico` y `mes`,
y todas las matrices escriben sus etiquetas de fila. Nada de eso lleva fórmula y
nada de eso lo debe tocar el usuario. Con el criterio viejo se veían editables,
y el usuario intentó editarlas. Lo que escribiera se perdería en la siguiente
regeneración, en silencio, y descuadraría los cruces contra las hojas fuente.

**Consecuencia.** El color deja de significar «aquí hay una fórmula» y pasa a
significar **«esto lo genera el libro»**, que es lo que el usuario necesita saber.
Esas columnas tampoco llevan desplegable: una lista invitaría a editar justo lo
que el color dice que no se toca.

---

## 17. Todo lo que crezca lleva holgura, incluido el presupuesto

**Decisión.** El bloque de `PRESUPUESTO` tiene 12 ranuras de categoría en el
bloque de entrada y en cada matriz del bloque de comparación, con las etiquetas
derivadas de `CAT_ACTIVIDADES`. Los subtotales se calculan por `SUMIF` sobre la
clasificación, no enumerando categorías.

**Motivo.** Es el mismo defecto que ya había aparecido tres veces en este proyecto
con las listas: algo dimensionado a los datos del momento de generar el archivo.
El bloque tenía seis filas porque había seis categorías. La séptima categoría que
alguien definiera en el catálogo no tendría fila, y su gasto **desaparecería** del
bloque de comparación sin decir nada.

**Consecuencia.** Añadir una categoría es escribirla en el catálogo. Y el límite,
cuando se alcance, **se ve**: un rótulo cuenta las categorías activas y se pone en
rojo, y la fila `DIFERENCIA` deja de ser 0. Se prefirió eso a hacer que
`DIFERENCIA` cuadrase siempre por construcción —absorbiendo el residuo en una fila
comodín—, porque eso habría eliminado el único indicador que detecta el problema.

---

## 18. Un archivo cubre un SEMESTRE, no un año, y se rota

**Decisión.** El archivo cubre un semestre de calendario más el mes anterior
completo: 7 meses, ~31 semanas de grilla. Cerrado el semestre, se guarda con su
fecha en el nombre y se genera el siguiente.

**Motivo.** Las dos alternativas son peores. Dimensionar la grilla a los datos de
ejemplo —4 semanas— dejaba el archivo **inservible** pasada la cuarta: sin turnos,
sin capacidad, sin seguimiento. Y el año completo pesa de más para lo que se gana,
porque nadie pega doce meses de órdenes en enero: las fechas se mueven y se agregan
operaciones sobre la marcha. Rotar de archivo por periodos es, además, como se
trabajaba antes con hojas sueltas; lo que faltaba era que la rotación no perdiera la
continuidad.

**El mes anterior entra completo a propósito**: es el colchón. Al abrir el archivo
nuevo, la semana en curso y las anteriores ya tienen turnos y capacidad, y no hay
un día sin cubrir en la costura entre los dos archivos.

**Consecuencia.** Cambiar de semestre **es regenerar**, no editar un parámetro: las
filas de la grilla y de los bloques mensuales son filas escritas, no fórmulas. El
`INSTRUCTIVO` lleva el procedimiento de rotación en 7 pasos, y el archivo cerrado
queda como registro histórico consultable.

---

## 19. La semana de referencia de la rotación se fija UNA VEZ

**Decisión.** `semana_referencia` es una fecha fija, independiente del horizonte, y
no se toca nunca más — tampoco al cambiar de semestre.

**Motivo.** El turno de cada técnico sale de la **distancia en semanas** hasta esa
fecha (aritmética modular sobre el anillo). Antes era «el primer lunes de la
grilla», que con un horizonte móvil se habría movido en cada archivo nuevo: el
ciclo se reiniciaría y el técnico que venía de T3 volvería a Banco. Es el fallo más
silencioso posible — no da error, no descuadra ningún total, simplemente el turno
de todos está mal.

**Consecuencia.** Es el único parámetro del libro que puede romper la continuidad
sin avisar, así que se avisa por triplicado: su descripción empieza por «⚠ NO
MODIFICAR al cambiar de semestre», su fila va pintada en rojo en `PARAMETROS`, y el
`INSTRUCTIVO` explica el arranque inicial (poner los turnos reales de una semana en
`orden_rotacion`, fijar ese lunes, y no volver a tocarlo). La verificación lo
comprueba de las dos maneras: con la misma referencia, los 14 rotativos encadenan
+1 posición en la frontera entre semestres; con la referencia movida, los 14
cambian.

---

## 20. El acumulado del presupuesto dice si es parcial

**Decisión.** El gasto real acumulado del año se compone del **arrastre** (lo que
el usuario copia del archivo cerrado) más lo que hay en este archivo. Si el
arrastre está vacío, el encabezado del acumulado dice que cubre **solo este
archivo**.

**Motivo.** Con archivos semestrales, el real acumulado de un archivo de segundo
semestre empieza en junio. Presentar eso como «YTD» sería mentir en la única cifra
que alguien va a llevar a una reunión de presupuesto. El plan sí cubre los 12 meses
(es manual), así que la comparación solo es honesta si el real también.

**Consecuencia.** El arrastre entra **únicamente en el acumulado**, nunca en un
mes: así la reconciliación mensual (`CONTROL` y `DIFERENCIA`) sigue cuadrando y no
se puede usar el arrastre para tapar un descuadre. Y el rótulo es una fórmula, no
un texto fijo: no puede quedar desactualizado.

---

## Lo que esta herramienta no puede calcular

No es una omisión, es una consecuencia de qué datos entran: MTBF, MTTR,
disponibilidad, OEE e indicadores de repuestos **no se pueden calcular aquí**,
porque harían falta eventos de parada, tiempos de operación, producción real y
movimientos de almacén. Nada de eso entra en este libro.

Decirlo por adelantado evita la conversación en la que alguien pide esos
indicadores y se termina fabricando un número que parece bueno y no significa
nada. Se calculan donde están los datos: el ERP, el sistema de producción o el de
almacén.
