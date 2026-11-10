# Cambios del módulo FDD — 10 de noviembre de 2026

**Rama:** `claude/fdd-random-forest-audit-gjehhl`
**Origen:** decisiones del proyecto sobre `AUDITORIA_FDD_10NOV.md`
**Commits:** `b59b089` (§7.3) · `2619317` (§7.1) · `a8e842c` (§7.2) · `2ba4c99` (documentación)

| Decisión | Estado |
|---|---|
| 1. No adaptar al congelador; conservar la enfriadora y declararlo | **hecho** (documentación) |
| 2a. §7.3 — rechazar los puntos sin estado estacionario | **hecho** |
| 2b. §7.1 — marcar y rechazar fuera de la malla | **hecho** |
| 2c. §7.2 opción B — bloque `res_ruidoso_*` | **hecho**, con una limitación declarada |
| 3. Corregir README (C5, C6) y ESPEC (C3) | **hecho** |
| 4. Suite completa y `verificacion.html` en Chromium | **hecho** (sección 6) |

**Lo que NO se tocó, como se pidió:** `src/ciclo.py`, `data/*.parquet`,
`resultados/*` (incluidos `metricas.json` y `malla_error.json`) y
`config/params.py`. No se reentrenó nada. Comprobado:
`git log -1 -- data/` sigue en `cd5f1db` y `git log -1 -- resultados/` en
`d6d9628`, ambos anteriores a este trabajo.

---

## 1. §7.3 — Los puntos sin estado estacionario se rechazan

Commit `b59b089`.

**El defecto.** `Math.fround(null)` vale `0`. Los 189 nodos de la malla con
`convergio = 0` llevan todos sus residuos en `null`, así que entraban al bosque
como un vector de once ceros —una máquina perfectamente sana— y el bosque
respondía con aire de certeza. Verificado contra el código anterior:

```
ANTES, nodo convergio=0 -> {clase: 'sano', conf: 0.3475356759901422}
ANTES, residuo null     -> {max: 0.3475356759901422}
```

| Cambio | Archivo:línea |
|---|---|
| `probabilidades()` valida cada característica y lanza si no es un número finito, en lugar de dejar que `null` se convierta en cero | `web/js/fdd_inferencia.js:53`–`67` |
| `diagnosticar()` comprueba `estado.convergio` antes de clasificar y devuelve `{residuos: null, diagnostico: null, motivo: …}` | `web/js/fdd_inferencia.js:286`–`289` |

**Por qué no basta con avisar de la banda de carga baja:** de los 189 nodos, 18
están a **carga plena** y 15 a carga 0,95. El reparto por clase es
`carga_baja` 132, `restriccion_linea_liquido` 38, `txv_restringida` 19.

**Pruebas** (`tests/test_inferencia_js.py`): una recorre los **189 nodos reales**
y exige que ninguno reciba clase; cuatro casos parametrizados cubren `null`,
`undefined`, `NaN` e `Infinity`; una comprueba el complemento —una fila legítima
de once ceros **sí** se clasifica—, para que la validación no se convierta en un
rechazo indiscriminado.

---

## 2. §7.1 — Fuera de la malla: borde marcado dentro de un paso, `null` más allá

Commit `2619317`.

**El defecto.** `buscarCelda` colapsaba cualquier valor fuera del dominio sobre
el nodo del borde y devolvía exactamente la misma estructura que un punto
interior. `FDD.consultar(50, 2.0, 'sano', 0)` —50 °C y carga del 200 %— devolvía
un estado completo con `T4_C = 4,5046` y ninguna marca.

| Cambio | Archivo:línea |
|---|---|
| `buscarCelda` devuelve `{i, t, fuera, distancia, rechazado}` | `web/js/fdd_inferencia.js:110`–`130` |
| `margenes()` exige que la malla declare el contrato, y falla con el comando de regeneración si no | `web/js/fdd_inferencia.js:142`–`149` |
| `consultar` rechaza con `null` más allá de un paso de nodo | `web/js/fdd_inferencia.js:201` |
| `consultar` adjunta `_extrapolado` y `_fuera_de_malla: {ejes, distancia_max}`, **presentes también dentro del dominio** | `web/js/fdd_inferencia.js:248`–`249` |
| `diagnosticar` propaga el rechazo con su motivo | `web/js/fdd_inferencia.js:282`–`285` |
| El margen lo calcula el exportador y viaja como dato | `src/exportador_web.py:619`–`658`, emitido en `:699` |

**El margen, y por qué no es un número único.** El paso se toma de la celda del
**borde de cada lado**, porque el eje de cargas no es uniforme: vale 0,03 abajo
(0,28 → 0,31) y 0,05 arriba (0,95 → 1,00). De ahí:

```
FDD_MALLA.margen_extrapolacion = {
  temperaturas_C: [22, 38],
  cargas:         [0.25, 1.05],
  severidades:    [0.15, 0.95],
  regla:          "..."
}
```

**El eje de severidad se marca pero no se rechaza**, porque es vecino más
próximo por diseño —la malla solo trae cinco niveles y así está declarado—. Una
severidad fuera de `[0, 1]` sí falla ruidosamente: no es una severidad.

**Pruebas:** 16, entre ellas el caso exacto de la auditoría `(50, 2.0)`, cuatro
que comprueban que dentro de un paso se sirve **exactamente** el valor del nodo
del borde y queda marcado, y una que compara el margen exportado contra
`margenes_extrapolacion()` para que el `.js` y Python no puedan separarse.

**Desviación declarada respecto del plan de §7.1 de la auditoría.** El plan decía
que `validar_malla` ganaría un caso que comprobase la bandera. No se hizo así:
la comprobación es una prueba de pytest. Motivo: una afirmación de corrección
metida dentro de una validación que tarda entre 30 y 60 minutos solo se
comprueba cuando alguien corre el camino lento; como prueba se comprueba en cada
corrida de la suite. Es un cambio de mi propio plan, no del encargo, y se
registra aquí para que quede a la vista.

---

## 3. §7.2 opción B — El visualizador clasifica los residuos **con ruido**

Commit `a8e842c`.

**El defecto.** La malla se generaba sin ruido de sensor y sin discrepancia
modelo-planta; el clasificador se entrenó con ambos. El desacuerdo estaba
declarado como dato en `FDD_FISICA.nota_ruido`, pero `diagnosticar()` seguía
clasificando los residuos limpios, sin aplicar el ruido y sin marcar nada.

**La magnitud, ahora medida y no estimada.** Sobre los **4 431 nodos
utilizables** de la malla (los 4 620 menos los 189 sin estado estacionario):

| Qué se clasifica | Acierto |
|---|---|
| bloque limpio `res_*` | **0,7364** |
| bloque ruidoso `res_ruidoso_*` | **0,6752** |

**6,1 puntos de optimismo** que el visualizador ya no muestra. Es del mismo
orden que la cota que daba la auditoría a partir del barrido de discrepancia
(F1 macro 0,8198 con discrepancia nula frente a 0,7572 en el caso base).

### Cómo se calcula

Replica `src.generador._fila` paso por paso: el estado degradado se resuelve con
los parámetros de la **planta**, la referencia sana con
`theta_modelo = theta_planta·(1 + epsilon)`, y el ruido se suma a las
**mediciones** —no a los residuos— antes de derivarlas.

| Pieza | Archivo:línea |
|---|---|
| Constantes: `SEMILLA_MALLA = 20261110`, `FACTOR_RUIDO_MALLA = 1.0`, `PREFIJO_RUIDOSO`, `DECIMALES_RUIDOSO = 6` | `src/exportador_web.py:78`–`81` |
| `columnas_ruidosas()` y `mapa_residuo_ruidoso()` | `src/exportador_web.py:367`–`380` |
| Cálculo del bloque en `_estado_punto` | `src/exportador_web.py:449`–`464` |
| Derivación de semillas y epsilon en `generar_malla` | `src/exportador_web.py:494`–`521` |
| Seis decimales para el bloque que alimenta al clasificador | `src/exportador_web.py:663` |
| Emisión de `campos_siempre_vecino`, `residuo_ruidoso` y `ruido_malla` | `src/exportador_web.py:700`–`716` |
| `consultar` no interpola el bloque ruidoso | `web/js/fdd_inferencia.js:132`–`140`, `254` |
| `diagnosticar` clasifica el ruidoso y declara con qué | `web/js/fdd_inferencia.js:290`–`319` |

### Cuatro decisiones de diseño que conviene mirar

1. **El ruido se calcula en Python, no en el navegador** (la opción B que se
   aprobó). Los residuos son funciones no lineales de las mediciones: pasan por
   temperaturas de saturación de CoolProp. Sumar ruido a un residuo no equivale
   a sumar ruido a la medición.
2. **El bloque ruidoso NUNCA se interpola.** Esto no estaba en el plan y es
   indispensable: el ruido de dos nodos vecinos es independiente, así que una
   bilineal de cuatro nodos reduciría la desviación típica a la mitad y
   desharía en silencio justo el efecto que el bloque existe para representar.
   La lista viaja en `FDD_MALLA.campos_siempre_vecino` y hay una prueba que
   comprueba, en el centro de una celda interpolable, que el campo limpio sí se
   interpoló y el ruidoso es exactamente el del vecino más próximo.
3. **Semilla propia, no derivada de `SEMILLA_MAESTRA`.** Añadir un flujo al
   árbol de semillas del generador habría cambiado las semillas con las que se
   generaron los datasets ya reportados. Esta malla tiene su propio árbol.
4. **Un epsilon por condición `(T_amb, carga)`** —como en el dataset, donde
   todas las clases y severidades de una condición comparten el gemelo
   desafinado— y **una semilla de ruido por nodo derivada del índice**, no del
   orden de ejecución, para que la malla no dependa del número de núcleos. Es
   la única diferencia declarada respecto del dataset, donde las muestras de una
   condición consumen un solo generador en secuencia. Los sorteos son i.i.d. en
   ambos casos.

### Respuesta a la pregunta sobre C6

Se preguntó, antes de implementar, si la verificación contra scikit-learn queda
bloqueada por el `.joblib` ausente. **Queda bloqueada en parte.** Hay que separar
tres cosas:

| Qué se verifica | ¿Bloqueado? | Cómo |
|---|---|---|
| Que los residuos ruidosos son los que el pipeline de entrenamiento habría calculado | **No** | `test_el_bloque_ruidoso_coincide_con_el_pipeline_de_entrenamiento` los reconstruye con las primitivas de `src.generador` (`aplicar_discrepancia`, `_referencia_sana`, `aplicar_ruido`) y no con el propio exportador |
| Que los números llegan de Python a JavaScript sin perderse | **No** | `test_el_bloque_ruidoso_es_reproducible` compara el `.js` contra una reejecución |
| Que el bosque de JavaScript y el de scikit-learn dan la misma clase **sobre el bloque ruidoso** | **Sí** | Necesita el objeto `rf` del `.joblib`, igual que las cinco pruebas de `test_exportador.py` |

No se reentrenó para resolverlo, como se indicó. La limitación está declarada en
el commit, en el README y en el pie de `verificacion.html`.

**Además se añadió `--solo-malla`** (`src/exportador_web.py:847`–`864`, `:900`).
Sin esa vía, `python -m src.exportador_web` carga el `.joblib` antes de nada y
**esta corrección no se podría reproducir en un clon limpio sin reentrenar
primero**. La malla depende del solver y de los parámetros, no del modelo.

### Coste y comprobación de que nada más se movió

- `web/datos/fdd_malla.js`: **1 584 913 → 2 052 176 B** (+467 263 B, +0,47 MB,
  +29 %). Son 11 arreglos de 4 620 valores a seis decimales.
- **Los 47 campos limpios y los 5 discretos salieron bit a bit idénticos** a los
  de antes de este trabajo, y `celda_bilineal` también. Comprobado valor por
  valor: **0 diferencias**. Por eso `resultados/malla_error.json` sigue siendo
  válido y **no se repitió** la validación por muestreo dirigido (30–60 min).
- **189 nodos quedan sin bloque ruidoso: exactamente los mismos 189** que no
  tienen estado estacionario. La referencia sana del gemelo desafinado convergió
  en todos los demás, así que no se pierde ningún punto adicional.

---

## 4. Documentación

Commit `2ba4c99`.

| Punto | Qué decía | Qué dice | Archivo:línea |
|---|---|---|---|
| Sistema de estudio | «el modelo de expansión directa se conserva como topología de respaldo» | Añade la decisión del proyecto: el módulo FDD **conserva la enfriadora**, con el motivo medido (piso de −25 °C, 817 W de un serpentín de 17 584 W, 59–118 h) | `README.md:13`–`21` |
| **C5** | «El resto de la malla (carga ≥ 0,34) no está afectado» — falso en la frontera | «`carga > 0,34` no está afectado; `carga = 0,34` sí lo está marginalmente», con el reparto exacto: 519 estados imposibles, 490 por debajo de 0,34 y **29 en 0,34 justo**, con `y_capacidad` entre 0,2431 y 0,2500 | `README.md:341`–`363` |
| **C6** | nada | Tabla de qué corre y qué no en un clon limpio, el conteo esperado de la suite (189 pasan, 5 errores de 194) y el comando para desbloquear las cinco | `README.md:81`–`84`, `233`–`253` |
| **C3** | «el proyecto cambia de equipo de estudio con una línea de configuración» | Acota el alcance: vale para A/C aire-aire; **no** para un congelador de baja temperatura con desescarche, con las cuatro piezas de física que faltan | `ESPEC_Simulacion_FDD.md:35`–`57` |

También: contrato de extrapolación, rechazo de los puntos sin estado
estacionario y los dos bloques de residuos documentados con sus números
(`README.md:270`–`324`); tamaños y estructura al día; registro de cambios
`13 bis` en la especificación con cinco entradas nuevas
(`ESPEC_Simulacion_FDD.md:378`–`389`).

---

## 5. `verificacion.html`: tres comprobaciones nuevas

De 8 a **11** comprobaciones, todas correctas:

| Nueva comprobación | Qué muestra |
|---|---|
| Clasifica los residuos CON ruido | `semilla 20261110, factor de ruido 1, discrepancia 0.05 (por_condicion)` |
| Fuera de la malla: marca y rechazo | `a 37 °C se sirve el borde marcado (temperaturas_C, distancia 1.00); a 50 °C y carga 2,0 se rechaza` |
| Sin estado estacionario: se rechaza | `189 nodos sin solución física; el primero devuelve null` |

El pie de la página ahora advierte de que la equivalencia con scikit-learn **no
es reproducible desde un clon limpio** y remite a `tests/test_inferencia_js.py`,
que sí lo es.

---

## 6. Verificación final

### Suite completa

| | Antes | Después |
|---|---|---|
| Recogidas | 161 | **194** |
| Pasan | 156 | **189** |
| Errores | 5 | **5** |
| Tiempo | 171 s | 186 s |

Los **5 errores son los mismos de antes**, ninguno nuevo: todos de
`tests/test_exportador.py`, todos `FileNotFoundError` de
`resultados/modelo_rf.joblib`. Las **33 pruebas nuevas** están en
`tests/test_inferencia_js.py` y **ninguna depende de ese artefacto**: corren en
un clon limpio.

### `verificacion.html` en Chromium bajo `file://`

```
pageerrors = []        console = []        11/11 comprobaciones correctas
```

Cargada desde `file:///…/proyecto-fdd/web/verificacion.html` en Chromium
headless. Cero errores de página, cero mensajes de consola.

### Tamaño final de `web/`

| Archivo | Antes | Después |
|---|---|---|
| `web/datos/fdd_modelo.js` | 3 608 614 | 3 608 614 |
| `web/datos/fdd_malla.js` | 1 584 913 | **2 052 176** |
| `web/datos/fdd_metricas.js` | 30 116 | 30 116 |
| `web/datos/fdd_fisica.js` | 10 262 | 10 262 |
| `web/js/fdd_inferencia.js` | 8 236 | **15 345** |
| `web/verificacion.html` | 3 804 | **6 475** |
| **Total** | **5 245 945 B (5,25 MB)** | **5 722 988 B (5,72 MB / 5,46 MiB)** |

Crecimiento: **+477 043 B (+9,1 %)**. Sigue con **cero dependencias externas**:
ningún CDN, ninguna fuente web, ningún `fetch`, ningún módulo ES6.

### Métricas mostradas en el visualizador: qué cambia y qué no

**No cambia nada de lo que ya se mostraba.** Comprobado una por una:

| Fila de `verificacion.html` | Antes | Después |
|---|---|---|
| `FDD_MODELO` | 100 árboles, 11 clases | igual |
| `FDD_FISICA` | R134a, 100 TR (351 685 W) | igual |
| `FDD_MALLA` | 7 × 12 × 11 × 5 | igual |
| `FDD_METRICAS` | F1 macro prevalencia = 0,5835 | igual |
| Consulta de la malla | ṁ = 1,9523 kg/s, W = 97,1 kW, controlado, bilineal | igual |
| Inferencia del bosque | `condensador_sucio`, confianza **1,000** | `condensador_sucio`, confianza **1,000** |
| Zona de ciclado | carga 0,30: ciclado = 1, fracción de marcha = 1,000 | igual |
| Vatios → fracción de carga | q = 0,6000 | igual |

**Dos matices que importan, y que la tabla de arriba no deja ver.**

1. La fila «Inferencia del bosque» **sigue en 1,000 por casualidad del punto
   elegido**: `(32 °C, carga 0,8, condensador_sucio, 0,75)` es un caso severo y
   fácil, y lo acierta con confianza plena tanto con el bloque limpio como con
   el ruidoso. En otros puntos sí cambia: en `(30 °C, carga 0,70,
   condensador_sucio, 0,75)` la confianza pasa de **1,000 a 0,950**. Lo que
   cambió de verdad es **de dónde sale el diagnóstico**, y eso ahora se declara
   en la fila nueva.
2. **El efecto agregado es el de la sección 3: el acierto sobre la malla baja de
   0,7364 a 0,6752.** Esa cifra no estaba en la página antes y sigue sin estar;
   si quieres que el visualizador la muestre, hay que decidir dónde, y no lo he
   hecho por mi cuenta.

Tercer cambio, menor pero visible para quien use la API: el objeto que devuelve
`consultar()` pasa de **55 a 68 claves** — 11 residuos ruidosos, `_extrapolado`
y `_fuera_de_malla`.

---

## 7. Lo que sigue abierto

- **Defecto 1** (la bandera `ciclado` no es fiable: 519 de 623 nodos son estados
  imposibles, 490 por debajo de carga 0,34 y 29 en 0,34 justo). Vive en
  `src/ciclo.py:571`–`581`, que el encargo excluyó expresamente. Sin tocar.
- **C6 de fondo**: la equivalencia exacta JavaScript ↔ scikit-learn no es
  reproducible desde el repositorio. Resolverlo de verdad pide o reentrenar en
  la máquina del evaluador, o publicar el modelo fuera del repositorio, o
  reducirlo —100 árboles a 16 de profundidad son 244 MB sin comprimir—. Las tres
  salidas son decisiones del proyecto; queda declarado, no resuelto.
- **C7** (`V_agua_ev` se llama como un caudal volumétrico y contiene kg/s) y
  **C8** (el caso del README que no pude reproducir desde los artefactos). No se
  pidió corregirlos; siguen anotados en `AUDITORIA_FDD_10NOV.md`.
- **Sin decidir, de la sección 3**: si el visualizador debe mostrar en alguna
  parte la caída de acierto de 0,7364 a 0,6752, y dónde.
