# TRASPASO — MantPlan

Documento de traspaso: qué está terminado, qué contiene y qué queda por hacer.

---

## Estado: entregable A CERRADO (v3.7.0)

El planificador semanal de mantenimiento en Excel está terminado y verificado.
Se entrega listo para usar, sin trabajo pendiente dentro de su alcance.

### Qué se entrega

Todo vive en `mantplan/`. Un único generador Python produce **seis libros**:

| Archivo | Para qué | Cuándo |
|---|---|---|
| `MantPlan_plantilla.xlsx` | **Trabajar con datos reales** | Excel 2021 / 365 |
| `MantPlan_plantilla_compatible.xlsx` | Lo mismo | Excel 2016 / LibreOffice |
| `MantPlan.xlsx` | **Demo**: enseñar el tablero lleno | Excel 2021 / 365 |
| `MantPlan_compatible.xlsx` | Lo mismo | Excel 2016 / LibreOffice |
| `MantPlan_banco.xlsx` | **Banco §7**: probar a volumen (1.000 órdenes) | Excel 2021 / 365 |
| `MantPlan_banco_compatible.xlsx` | Lo mismo | Excel 2016 / LibreOffice |

**Para empezar a trabajar se usa la PLANTILLA**, no el demo: el demo lleva casos
sucios sembrados a propósito para ejercitar las validaciones.

Documentación:

- **`mantplan/README.md`** — decisiones técnicas y números verificables a mano.
- **`mantplan/MANUAL.md`** — el **porqué** de cada decisión de diseño, con su
  motivo y su consecuencia. Escrito para defenderlo ante quien lo cuestione.
- **`mantplan/VERIFICACION.md`** — reporte de verificación de cada tirada, con lo
  que se comprobó, lo que no, y los supuestos.
- **Hoja `INSTRUCTIVO`, dentro del libro** — el **cómo se usa**, en lenguaje
  llano. Es la única guía; no hay una segunda que pueda divergir.
- **`CLAUDE.md`** (raíz) — estado y disciplina de trabajo.

### Qué hace

Programa y controla la semana de mantenimiento: reparte el trabajo entre los
técnicos, comprueba si la carga cabe en las horas disponibles, mide si se cumplió
lo programado, sigue el gasto contra el presupuesto y redacta el correo semanal.

Contenido: 10 reglas de negocio implementadas dos veces y verificadas una contra
otra · rotación de turnos derivada con cobertura garantizada · vacaciones que
dejan hueco visible · calendario laboral · presupuesto OPEX mensual · tablero con
6 KPI y 5 gráficos · exportación del correo semanal · validación de importación
que reporta y nunca bloquea.

### Qué NO hace, y no es una omisión

No genera órdenes (salen del ERP/CMMS), no sustituye al ERP, no gestiona almacén
y **no calcula MTBF, MTTR, disponibilidad, OEE ni indicadores de repuestos**:
harían falta eventos de parada, tiempos de operación, producción y movimientos de
almacén, y ninguno de esos datos entra en el libro. Está dicho en el `INSTRUCTIVO`
para que nadie los pida esperando un número que sería inventado.

### Cómo se pone en marcha en otra planta

Mapear catálogos. Cero código. En orden: `PARAMETROS` → catálogos `CAT_*`
(centros de costo, puestos, actividades, tipos de OT, estados del ERP,
supervisores, turnos) → `TECNICOS` → `CALENDARIO` → `PLAN_VACACIONES` →
`PRESUPUESTO`. El `INSTRUCTIVO` lo detalla paso a paso, con la advertencia de
borrar las filas de ejemplo antes de cargar datos reales.

### Cómo se regenera

```bash
pip install openpyxl
cd mantplan
python generar_mantplan.py --plantilla --fecha-ancla 2026-07-27 --salida MantPlan_plantilla.xlsx
python generar_mantplan.py --plantilla --fecha-ancla 2026-07-27 --salida MantPlan_plantilla_compatible.xlsx --refs compatibles
python generar_mantplan.py --fecha-ancla 2026-07-27 --salida MantPlan.xlsx
python generar_mantplan.py --fecha-ancla 2026-07-27 --salida MantPlan_compatible.xlsx --refs compatibles
python generar_mantplan.py --anio-completo --salida MantPlan_banco.xlsx
python generar_mantplan.py --anio-completo --salida MantPlan_banco_compatible.xlsx --refs compatibles

# Y SIEMPRE, sobre los seis: comprobación estructural del XML de los nombres.
python verificar_nombres.py MantPlan*.xlsx
```

---

## Pendiente

### 1. Entregable B — aplicación web (React). No empezado

Carpeta prevista `mantplan-web/`, con las 10 reglas en `src/domain/rules.ts`.

Lo que ya está resuelto y se reutiliza: las 10 reglas están **especificadas y
verificadas** en `generar_mantplan.py` como funciones puras
(`regla_1_clasificacion` … `regla_10_validacion`), con un dataset sintético y un
banco de 1.000 órdenes que sirven de casos de prueba. Portarlas a TypeScript es
traducción, no diseño: el comportamiento esperado ya está fijado y verificado.

Decisiones pendientes de la app: dónde vive el dato (¿fichero, base, conexión al
ERP?), autenticación, y si el Excel sigue siendo el formato de intercambio.

### 2. Versión para SAP

Adaptar la importación a los formatos de exportación reales de SAP-PM y mapear
sus tipos de OT, estados y centros de costo. El diseño ya es agnóstico de ERP, así
que en principio es un mapeo de catálogos más el ajuste del layout de pegado.

### 3. Herramienta de análisis Weibull — proyecto INDEPENDIENTE

**No es parte de MantPlan y no debe integrarse en él.** Weibull necesita datos de
falla (tiempos hasta fallo, censurados incluidos) que este libro no tiene ni debe
tener: mezclarlos rompería el principio de que la herramienta no inventa
indicadores con datos que no posee. Va como proyecto aparte, con su propia fuente
de datos.

---

## Riesgos y avisos para quien retome

- **Los `git tag` no se pueden empujar** desde este entorno: el proxy de salida
  devuelve 403. Si hace falta etiquetar, se hace desde otra máquina.
- **LibreOffice no evalúa `XLOOKUP`**: solo se pueden recalcular y verificar las
  variantes `_compatible`. Las principales se validan por construcción, porque
  salen del mismo código.
- **REGLA-3 y REGLA-4 usan `HOY()` por diseño** (envejecimiento vivo del backlog).
  Eso hace que las cuatro columnas de envejecimiento cambien según el día del
  recálculo; el verificador lo tiene en cuenta e infiere el día del propio libro.
  El **tablero**, en cambio, se ancla a `p_fecha_datos` y nunca a `HOY()`.
- **Los rangos con nombre se escriben SIN `=` delante.** En `xl/workbook.xml` la
  definición va como expresión desnuda; con el `=` Excel avisa de «Registros
  quitados: Rango con nombre» y **borra los nombres al reparar**, dejando mudos los
  desplegables. LibreOffice lo tolera, así que **el recálculo no lo detecta**: por
  eso hay una comprobación estructural del XML (`verificar_nombres.py`) que se
  corre sobre los seis libros y falla si algún `definedName` empieza por `=`,
  contiene `#REF!`, está vacío o está duplicado. Es el tipo de defecto que solo se
  ve abriendo el archivo en Excel real.
- Si se añade una hoja o una columna, hay que decidir si es **derivada** (rojo
  claro) o **editable** (azul). No hay tercer color. En las hojas de **resultado**
  se marca todo, tenga fórmula o valor: el rojo significa «lo genera el libro», no
  «aquí hay una fórmula».
- Cualquier lista nueva que dependa de un catálogo o de los datos debe ser
  **fórmula con holgura y compactación**, nunca texto fijo. Es el defecto que más
  veces ha reaparecido en este proyecto — la última, en las **filas de categoría de
  `PRESUPUESTO`**, que estaban dimensionadas a las seis categorías existentes.
  Regla práctica: si algo puede crecer con el catálogo, dele ranuras y avise
  cuando se agoten; no lo haga cuadrar por construcción.
