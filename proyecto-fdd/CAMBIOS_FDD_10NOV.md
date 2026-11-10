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

---

# Adenda — dominio de entrenamiento

Añadida después de la primera entrega, sobre el mismo trabajo y la misma fecha,
por lo que no se abre un archivo nuevo.

## A.1 El problema

El dataset se muestreó con `Q_load_frac ≥ 0,40` (`config/params.py:208`), y la
malla se extendió hasta 0,28 para poder dibujar la zona de ciclado. El
clasificador **no vio ni un solo punto de esa banda**: el dataset tiene cero
filas con carga por debajo de 0,40 y cero filas en ciclado. Pedirle un
diagnóstico ahí es pedirle que extrapole, y un bosque aleatorio extrapola
devolviendo la hoja más parecida con toda la confianza del mundo.

**1 540 de los 4 620 nodos de la malla (33,3 %) están fuera del dominio de
entrenamiento**: los cuatro nodos de carga 0,28, 0,31, 0,34 y 0,37, en las siete
temperaturas, once clases y cinco severidades.

## A.2 Qué se implementó

| Cambio | Archivo:línea |
|---|---|
| `dominio_entrenamiento()` lee los rangos de `config.params.RangosContorno` —la misma configuración que usó el hipercubo latino— y los exporta | `src/exportador_web.py:619`–`655`, emitido en `:738` |
| `dominioEntrenamiento()` exige el dato y falla con el comando de regeneración si falta | `web/js/fdd_inferencia.js:147`–`160` |
| `consultar` calcula la marca y la adjunta como `_fuera_de_entrenamiento` (booleano) y `_fuera_de_entrenamiento_ejes` (detalle: eje, valor, rango, lado) | `web/js/fdd_inferencia.js:244`–`262`, `280`–`281` |
| `diagnosticar` **no clasifica** fuera del dominio: devuelve el estado, `diagnostico: null`, `fuera_de_entrenamiento: true` y un motivo legible | `web/js/fdd_inferencia.js:330`–`343` |
| Dentro del dominio, el objeto también lo declara (`fuera_de_entrenamiento: false` y los rangos) | `web/js/fdd_inferencia.js:355`–`359` |
| Fila nueva en la autoprueba | `web/verificacion.html:99`–`108` |

**Los rangos viajan como dato, no escritos en el JS.** `FDD_MALLA.dominio_entrenamiento`
trae `T_amb_C: [24, 36]`, `Q_load_frac: [0.4, 1]`, `HR_amb_pct: [60, 95]`, la
lista `ejes_comprobados` y la fuente. Hay una prueba que compara el dato
exportado contra `RangosContorno()` y **otra que lo compara contra los mínimos y
máximos que de verdad hay en los `.parquet`**, para que una configuración que
dejara de describir los datos no pase desapercibida.

### Dos decisiones que van más allá de la letra del encargo

1. **Se comprueba el rango completo en los dos ejes, no solo el piso de carga.**
   El encargo decía «la carga por debajo del piso de entrenamiento, o la
   temperatura ambiente fuera de su rango». Una consulta a carga 1,03 —que el
   margen de extrapolación admite— está tan fuera del dominio del dataset como
   una a 0,28, así que se marca igual. Si se prefiere la lectura literal, es un
   `||` menos en `web/js/fdd_inferencia.js:252`.
2. **La marca va en el estado que devuelve `consultar`, no solo en el resultado
   de `diagnosticar`.** El encargo nombraba `diagnosticar()`. Ponerla en el
   estado hace que cualquier consumidor la vea —la página de demostración la
   necesita para pintar la bandera— y `diagnosticar` la lee de ahí. Es
   consistente con `_extrapolado`, que ya funcionaba así.

### `HR_amb_pct` se exporta pero NO se comprueba

Está en el dato por completitud. La malla fija la humedad en 80 %, dentro del
rango, y con condensador de aire la humedad no interviene en el ciclo:
`consultar` ni la recibe como argumento. `ejes_comprobados` lo dice
explícitamente para que nadie suponga que sí se valida.

## A.3 Acierto dentro y fuera del dominio

Medido con `FDD.consultar()` —la superficie que el visualizador expone—, no
leyendo las matrices crudas.

| Conjunto de nodos | n | Acierto **ruidoso** | Acierto **limpio** | Recall macro ruidoso / limpio |
|---|---|---|---|---|
| **Todos** (lo reportado antes) | 4 431 | **0,6752** | **0,7364** | 0,6759 / 0,7322 |
| **Dentro** del dominio de entrenamiento | 3 010 | **0,7156** | **0,7920** | 0,7172 / 0,7903 |
| Fuera del dominio | 1 421 | 0,5897 | 0,6186 | 0,5860 / 0,6043 |

Dos lecturas:

- **La banda fuera del dominio estaba arrastrando la cifra hacia abajo.**
  Restringido a donde el modelo fue entrenado, el acierto con el bloque ruidoso
  sube de 0,6752 a **0,7156**. Esa es la cifra defendible: la otra mezclaba
  puntos sobre los que el clasificador no tenía nada que decir.
- **La brecha limpio-ruidoso es MAYOR dentro del dominio**, no menor: 7,6 puntos
  (0,7920 frente a 0,7156) contra 6,1 en el conjunto completo. Es decir, el
  optimismo de clasificar residuos limpios es todavía más grande justo donde el
  visualizador va a usarse.

Recall por clase dentro del dominio (ruidoso / limpio):

| Clase | n | Ruidoso | Limpio |
|---|---|---|---|
| `sano` | 280 | 0,625 | **1,000** |
| `condensador_sucio` | 280 | 0,871 | 0,911 |
| `incrustacion_evaporador` | 280 | 0,729 | 0,693 |
| `caudal_agua_bajo` | 280 | 0,821 | 0,875 |
| `carga_baja` | 219 | 0,826 | 0,744 |
| `sobrecarga` | 280 | 0,586 | 0,789 |
| `txv_restringida` | 279 | 0,541 | 0,688 |
| `txv_sobrealimenta` | 280 | 0,796 | 0,757 |
| `compresor_desgastado` | 280 | 0,750 | 0,800 |
| `incondensables` | 280 | 0,857 | 0,925 |
| `restriccion_linea_liquido` | 272 | 0,485 | 0,511 |

La fila que conviene mirar es la primera: **con residuos limpios, `sano` se
reconoce el 100 % de las veces**. Es el artefacto que justifica todo el bloque
ruidoso — un residuo limpio de una máquina sana es casi exactamente cero y el
bosque lo reconoce sin esfuerzo. Con ruido y discrepancia baja a 0,625, que es
del orden del 0,64 de recall que el informe reporta para `sano` en el conjunto
de prueba.

## A.4 Cobertura del defecto 1

**Los 519 estados imposibles del defecto 1 quedan cubiertos por la marca: 519 de
519, el 100 %.** Reparto por carga: **262** en 0,28, **228** en 0,31 y **29** en
0,34 — los tres por debajo del piso de 0,40.

Y es más amplio que eso: **los 623 nodos marcados como `ciclado` están fuera del
dominio de entrenamiento**, no solo los 519 imposibles. No es casualidad —la
máquina solo cicla por debajo de la carga mínima que sostiene el compresor, y el
dataset nunca bajó hasta ahí— pero hay una prueba que lo comprueba en lugar de
suponerlo, y que fallaría si alguien ampliara la malla o el barrido.

**Las dos marcas no son redundantes.** De los 189 nodos sin estado estacionario,
**119 están fuera del dominio y 70 están dentro**. Esos 70 solo los atrapa la
comprobación de `convergio` de §7.3. Hay una prueba que lo afirma, para que
nadie retire una de las dos creyéndola cubierta por la otra.

## A.5 Hallazgo: `sano` guarda cinco realizaciones de ruido y solo una es alcanzable

Salió al cuadrar los números y no estaba buscado.

La malla guarda cinco ranuras de severidad por clase. Para `sano` las cinco
corresponden a `f = 0`, así que el bloque **limpio** es idéntico en las cinco
—mismo cálculo determinista—. El bloque **ruidoso**, en cambio, tiene una
semilla por nodo, de modo que **las cinco ranuras llevan cinco sorteos de ruido
independientes**. Pero `consultar` fuerza `iS = 0` cuando la clase es `sano`
(`web/js/fdd_inferencia.js:234`), que es correcto —`sano` ignora la severidad por
construcción—, así que **cuatro de cada cinco realizaciones de `sano` no son
alcanzables por la API**: 336 nodos con 11 valores cada uno.

Consecuencias:

- **Ninguna sobre la corrección.** Lo que el visualizador sirve es siempre la
  ranura 0, de forma determinista y reproducible.
- **Una sobre la medición**, y por eso se reporta: leyendo las matrices crudas el
  acierto sale 0,6741, y por `consultar()` sale 0,6752. La diferencia son esas
  realizaciones que nadie puede ver. **Las cifras de A.3 están medidas por
  `consultar()`**, que es lo único reproducible desde el navegador.
- Si se cuenta `sano` una sola vez por condición, para que no pese cinco veces,
  el acierto dentro del dominio es **0,7229 ruidoso frente a 0,7753 limpio**
  (n = 2 786). El recall macro no cambia, porque promedia por clase.

**No lo corregí**, porque sembrar las cinco ranuras de `sano` con una sola
semilla es un cambio de diseño que nadie pidió y que obligaría a regenerar la
malla otra vez. Queda anotado. Cuesta del orden de media hora más una
regeneración de siete minutos, y ahorraría unos 30 kB.

## A.6 Verificación de la adenda

- **Malla regenerada por completo** (`python -m src.exportador_web --solo-malla
  --sin-validar`, 11 min con la suite compitiendo por los núcleos) y comparada
  contra el archivo que yo había parcheado a mano insertando solo la línea
  nueva: **idéntico byte a byte**. Los campos siguen intactos, así que
  `resultados/malla_error.json` continúa siendo válido.
- **Suite completa: 202 pasan, 5 errores de 207.** Los 5 errores son los mismos
  de siempre, del `.joblib` ausente. Las 13 pruebas nuevas de esta adenda no
  dependen de ese artefacto.
- **`verificacion.html` en Chromium bajo `file://`: 12 de 12 correctas, cero
  errores de página, cero mensajes de consola.** La fila nueva informa: «entrenado
  en carga [0.4, 1] y 24–36 °C; a carga 0,30 se devuelve el estado del ciclo pero
  no un diagnóstico».
- `web/`: **5 727 188 B (5,73 MB)**. El dato del dominio añade 712 B a la malla.
- `src/ciclo.py`, `data/` y `resultados/` siguen sin tocar; no se reentrenó nada.

### Conteo de pruebas a lo largo del trabajo

| | Recogidas | Pasan | Errores |
|---|---|---|---|
| Antes de todo | 161 | 156 | 5 |
| Tras §7.3 + §7.1 + §7.2 | 194 | 189 | 5 |
| Tras la adenda | **207** | **202** | **5** |
