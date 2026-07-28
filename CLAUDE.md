# CLAUDE.md — estado y disciplina de trabajo del repositorio

Contexto para retomar el trabajo sin releer todo el historial.

## Qué hay aquí

| Carpeta | Qué es | Estado |
|---|---|---|
| `mantplan/` | **MantPlan** — planificador semanal de mantenimiento en Excel, sin macros. Entregable A. | **v3.6.0, cerrado** |
| `task-manager/` | Proyecto independiente, sin relación con MantPlan. | — |
| `asignacion-6-distribucion-planta/` | Proyecto independiente. | — |

## MantPlan — estado final del entregable A

**Un único generador** (`mantplan/generar_mantplan.py`, Python + openpyxl) produce
**seis libros**: plantilla, demo y banco, cada uno en variante principal
(`XLOOKUP` + referencias estructuradas) y `_compatible` (`INDEX/MATCH` + rangos
A1, para Excel 2016 y LibreOffice).

- **`MantPlan_plantilla.xlsx`** — para **trabajar con datos reales**. 8 órdenes de
  ejemplo marcadas y limpias; `VALIDACION` abre en cero.
- **`MantPlan.xlsx`** — **demo**, 200 órdenes con casos sucios sembrados a
  propósito. Para enseñar el tablero lleno, **no** para trabajar.
- **`MantPlan_banco.xlsx`** — **banco §7**, 1.000 órdenes de un año. Solo pruebas
  a volumen.

31 hojas (32 en el banco), 21 visibles. Orden: `DASHBOARD` · `INSTRUCTIVO` ·
presentación · trabajo diario · configuración. Ocultas (con `hidden`, nunca
`veryHidden`): los 8 catálogos `CAT_*`, `GUIA_IMPORTAR_ORDENES`,
`_COMPATIBILIDAD` y `_BANCO_PRUEBA`.

### Arquitectura

- **Motor**: las 10 reglas de negocio, implementadas **dos veces** —como fórmulas
  del libro y como funciones puras de Python— y comparadas celda a celda. Las
  reglas no se renumeran ni se amplían: lo nuevo son hojas **derivadas**.
- **Catálogos**: lo que cambia entre empresas (`CAT_*`). **Parámetros**: lo que se
  ajusta (`PARAMETROS`). Ni un código de empresa dentro de una fórmula.
- **Prohibido en fórmulas**: `OFFSET`, `INDIRECT`, columnas completas (`A:A`),
  funciones de derrame (`SORT`, `FILTER`), `LET`. `TEXTJOIN` lleva `_xlfn.`.
  `INDEX` sí se usa para acotar rangos con nombre: no es volátil.
- **Sin macros**: navegación con `HYPERLINK`, avisos con formato condicional.

### Decisiones cerradas (el detalle y el porqué, en `mantplan/MANUAL.md`)

1. La **mano de obra propia no es costo**: es nómina fija, se mide en capacidad.
2. Base de **48 h (L–S)**; el domingo del relevo es superávit, se registra pero
   **no se planifica** sobre él.
3. **Rotación derivada** 1:1 por especialidad, con `turno_manual` como override.
4. **Vacaciones = hueco visible** (Modelo A): la posición queda vacía a propósito;
   cubrirla es decisión del supervisor.
5. La **adherencia excluye del denominador** los días no laborables.
6. El **dashboard no muestra datos por técnico**: en una reunión se leen como
   culpa individual. El detalle sigue en `SEGUIMIENTO_HH`.
7. **Clase** (mix, partición que suma 100: predictivo · preventivo ·
   correctivo_programado · emergencia, en `CAT_TIPOS_OT`) vs **rubro** (etiqueta
   transversal, puede ir vacía: calibracion · lubricacion, en `CAT_ACTIVIDADES`).
   Una calibración es preventivo **y** calibración a la vez.
8. Las **metas de mix (60/25/10/5) son convención de industria, NO norma**: no
   están en EN 15341 ni VDI 2893. Editables en `PARAMETROS`. El libro no cita
   códigos de indicador de ninguna norma.
9. El mix se mide **en horas**; el % por conteo se muestra al lado.
10. **Lubricación sin meta configurable**: es cumplimiento, el objetivo es 100 %.
11. **`VALIDACION` reporta y nunca bloquea.** Las validaciones de celda son
    ayudas, no barreras: no rechazan lo que se pega.
12. **Listas por calendario y por catálogo, nunca congeladas**: los selectores de
    mes (18) y semana (año ISO completo) se generan siempre igual, y las listas de
    catálogo son fórmulas con holgura y compactación.

### Convención de color (dos códigos, no tres)

- **AZUL** = celda editable, la escribe el usuario.
- **ROJO MUY CLARO** (relleno `#FDF3F3`, encabezado en rojo claro sobre la banda
  azul) = columna **calculada**, no escribir encima.
- Las hojas **no se protegen**: la señal es visual. Bloquear rompería el pegado
  masivo y contradiría «avisa, nunca bloquea».
- El formato condicional (semáforos, cuadres, alertas) se pinta **por encima**.

## Disciplina de trabajo (cómo se ha llevado y cómo seguir)

1. **Un cambio estructural por prompt.** Se implementa, se verifica, se
   documenta, se hace commit y **se para**. No se encadena con el siguiente.
2. **Regenerar SIEMPRE todas las variantes**, sin excepción: los seis libros.
3. **Verificar de verdad, no por inspección.** Recálculo real con LibreOffice
   (`/root/.claude/skills/xlsx/scripts/recalc.py <archivo> <timeout>`, máx. 595 s)
   y comparación celda a celda contra el motor Python. LibreOffice **no** evalúa
   `XLOOKUP`: solo se recalculan las variantes `_compatible`.
4. **`VERIFICACION.md` en cada tirada**: qué se verificó, con números, y qué
   **no** se verificó, con los supuestos declarados. Las secciones viejas se
   conservan como historia (`0-bis`, `0-ter`, …).
5. **El usuario corre su propio recálculo independiente.** El reporte propio no
   basta: no se declara nada como verificado sin haberlo ejecutado.
6. **Las pruebas se hacen editando el libro y recalculando**, no leyendo el
   código. Toda prueba de crecimiento (catálogos, meses) lleva un **control**:
   comprobar que el caso contrario sí se detecta.
7. Rama de trabajo: `claude/planning-maintenance-scheduler-fnawl5`.
8. Los `git tag` no se pueden empujar (el proxy de salida devuelve 403). Se
   reporta, no se rodea.

## Lo que la herramienta NO puede calcular

MTBF, MTTR, disponibilidad, OEE e indicadores de repuestos. No hay eventos de
parada, tiempos de operación, producción ni movimientos de almacén. Está dicho en
la hoja `INSTRUCTIVO` y en `MANUAL.md` para que nadie los pida esperando un número
que sería inventado.

## Pendiente

- **Entregable B**: aplicación web React (`mantplan-web/`), con las 10 reglas en
  `src/domain/rules.ts`. **No empezado.**
- Versión para SAP.
- Herramienta de análisis Weibull, como **proyecto independiente**.

Ver `TRASPASO_MantPlan.md` para el detalle del traspaso.
