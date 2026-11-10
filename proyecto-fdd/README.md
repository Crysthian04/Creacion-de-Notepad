# Detección y diagnóstico de fallas (FDD) por simulación

**Fase 5 — Monitoreo e Innovación** · Plan Integral de Mantenimiento
Sistema de Refrigeración y Aire Acondicionado (0251) — UTP, Facultad de Ingeniería Mecánica

Generador de datos sintéticos a partir de un modelo termodinámico del ciclo de compresión de vapor,
y clasificador Random Forest que identifica el modo de falla a partir de lo que el equipo mide en
campo.

**Sistema de estudio:** enfriadora de agua de 100 TR que da servicio a un edificio de oficinas, con
distribución hidrónica. El modelo de expansión directa se conserva como topología de respaldo.

> **Decisión del proyecto, 10 de noviembre de 2026.** El sitio de estudio de las otras fases pasó a
> ser un congelador de expansión directa (condensadora Heatcraft MOH019L63CF, R-404A, −40 a 0 °F,
> evaporador de aire con desescarche eléctrico). **El módulo FDD NO se adapta a ese equipo: conserva
> la enfriadora de agua como sistema de estudio.** El motivo está medido en
> `AUDITORIA_FDD_10NOV.md`, sección 6: no es un cambio de parámetros. A −25 °C el solver no
> converge, porque `src/ciclo.py:417` fija un piso de −25,0 °C a la temperatura de evaporación; y
> bajando ese piso a mano el modelo converge entregando 817 W de un serpentín de 17 584 W, con
> 0,22 K de sobrecalentamiento. Adaptarlo cuesta entre 59 y 118 horas, porque faltan el calor
> latente, la escarcha, el ciclo de desescarche y el régimen de marcha y parada por termostato.

**Lo que se demuestra es que el método funciona y es implementable, no que ya esté implementado.**

---

## 1. Topologías seleccionables

Una sola línea de `config/params.py` (`TIPO_SISTEMA`) cambia el sistema modelado. La topología
viaja dentro de `ParametrosEquipo`, y de ella se derivan las variables medidas, las características
del clasificador y el catálogo de fallas.

| `TIPO_SISTEMA` | Evaporador | Condensador | Clases | Residuos |
|---|---|---|---|---|
| `chiller_cond_aire` | agua | aire | 11 | 11 |
| `chiller_cond_agua` | agua | agua + torre | 11 | 12 |
| `expansion_directa` | aire | aire | 10 | 11 |

El tipo de condensador se resuelve en el levantamiento: la presencia de torre se ve desde la azotea.
Mientras tanto el caso base es **condensador de aire**, que exige menos supuestos inventados.

---

## 2. Arquitectura

```
Capa 1 — MODELO FÍSICO        src/ciclo.py     T_amb, HR, carga -> estado SANO
Capa 2 — INYECCIÓN DE FALLAS  src/fallas.py    degrada parámetros físicos
Capa 3 — CLASIFICADOR         src/modelo.py    RESIDUOS -> modo de falla + severidad
```

El clasificador **no opera sobre valores crudos, sino sobre residuos**: `(medición degradada) −
(predicción sana a las mismas condiciones)`. Así la variabilidad del clima y de la carga se cancela
y queda solo la firma de la degradación.

### Discrepancia entre modelo y planta

Los datos se generan con `theta_planta` y la referencia sana se calcula con
`theta_modelo = theta_planta·(1+ε)`. Sin esa discrepancia el residuo de la condición sana es puro
ruido de sensor y la separación entre clases es trivial por construcción. Es la diferencia entre un
F1 de 0,99 que no significa nada y una estimación defendible.

---

## 3. Instalación

```bash
cd proyecto-fdd
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Probado con Python 3.11. Versiones fijadas: la reproducibilidad exige controlar la semilla **y** el
entorno.

---

## 4. Cómo correr el pipeline completo

En un clon limpio, cinco pruebas de `tests/test_exportador.py` dan error porque
`resultados/modelo_rf.joblib` está excluido del repositorio. El paso 3 lo regenera; hasta
entonces el conteo esperado es **202 pasan, 5 errores** de 207. Ver «Qué se puede correr en un clon
limpio» en la sección 7 bis.

```bash
# 0. VERIFICACIÓN FÍSICA — obligatoria antes de generar nada (~4 min)
python -m pytest tests/ -v

# 1. Calibración de los coeficientes UA del gemelo digital
python -m src.calibracion

# 2. Datasets del caso base, con discrepancia del 5 %
python -m src.generador

# 3. Entrenamiento, evaluación, figuras e informe Word
python -m src.modelo

# 4. Cota superior teórica: los mismos datos sin discrepancia
python -m src.generador --discrepancia 0.0 --sufijo _sin_discrepancia
python -m src.modelo --sufijo _sin_discrepancia --sin-estudios --sin-informe
```

Salidas: `config/ua_calibrado.json`, `data/*.parquet`, `figuras/*.png` (300 dpi),
`resultados/metricas.json`, `resultados/informe_fdd.docx`.

### Por qué las pruebas van primero

`tests/test_firmas.py` verifica que cada modo de falla mueve las variables en la dirección
físicamente correcta, en **todas** las condiciones del dominio y sin ruido. Un simulador con firmas
invertidas produciría un clasificador con métricas excelentes sobre física equivocada, y nada en la
matriz de confusión lo delataría.

**Durante el desarrollo esta batería encontró siete errores reales del modelo**, todos documentados
en el código y en la sección 13 de `ESPEC_Simulacion_FDD.md`:

1. La falla de válvula era un desplazamiento del setpoint de sobrecalentamiento, **sin consecuencia
   sobre el flujo**: `res_rp`, `res_COP` y `res_split_cond` quedaban exactamente en cero.
2. Sin acoplar el sobrecalentamiento al área seca del evaporador, el SH no tiene **ninguna**
   consecuencia sobre la temperatura de evaporación.
3. `sobrecarga` subía el COP: el mapa de inventario y el acoplamiento del subenfriamiento contaban
   dos veces el mismo efecto físico.
4. `condensador_sucio` degradando solo `UA_cd` no movía el salto de aire, así que la firma
   distintiva de los incondensables no era verificable.
5. Los regímenes extremos de la válvula siempre convergen —sueltan una ecuación—, así que sin una
   condición de validez el **orden de prueba** decidía el resultado en lugar de la física.
6. Fijar la capacidad al máximo también admite siempre solución: una válvula ligeramente
   sobrealimentada salía declarada como «saturación de capacidad», entregando más frío que la carga.
7. Con el coeficiente de la especificación, la restricción de línea de líquido **nunca** hace
   flashear el líquido, así que su firma de «burbujas en el visor» no podía producirse y quedaba
   idéntica a la de una válvula restringida.

---

## 5. Reglas no negociables y dónde las impone el código

| Regla | Dónde |
|---|---|
| El clasificador se entrena **solo** con columnas `res_*` | `features.columnas_residuos(topo)` + `construir_matriz_X()`: lista blanca, nunca `drop` |
| Ninguna variable puede filtrar información sobre la etiqueta | `features.EXCLUIDAS_Y_MOTIVO` documenta cada exclusión, incluidas las banderas del control |
| Propiedades termodinámicas con CoolProp | `ciclo.py` y `features.py`; sin correlaciones ni tablas embebidas |
| Toda la aleatoriedad con semilla fija | `config.params.SEMILLA_MAESTRA`, un único literal; flujos con `SeedSequence.spawn()` |
| GridSearchCV optimiza **F1 macro** | `modelo.seleccionar_modelo()` |
| Se evalúan los **dos** conjuntos de prueba | `modelo.ejecutar()` |
| Parámetros del equipo separados y marcados como provisionales | `config/params.py` + `advertir_provisionales()` |
| Convergencia verificada y descartes reportados | `ciclo.resolver_ciclo()` devuelve `convergio`; `generador.ContabilidadSolver` los cuenta |
| El conjunto de prueba se toca **una sola vez** | `modelo.ConjuntoSellado`; `seleccionar_modelo()` no lo recibe en su firma; `metricas.json` marca `corrida_valida` |
| Partición sin fuga de condiciones | `modelo.particionar()` corta por grupos de `cond_id` |
| Las clases con soporte pequeño llevan intervalo | `modelo.intervalo_wilson()` en toda clase con soporte < 50 |

### Nota sobre reproducibilidad

`np.random.default_rng(seed_sequence)` **no** es reproducible entre llamadas en NumPy ≥ 2: deriva un
hijo nuevo cada vez. El proyecto usa `generador.rng_desde()`, que reconstruye el `SeedSequence`
desde su entropía. Lo detectó `test_muestreo_reproducible_con_la_misma_semilla`.

---

## 6. Simplificaciones declaradas

1. **Datos sintéticos.** El modelo no fue entrenado con históricos de la instalación.
2. **Inventario de refrigerante.** `carga_baja` y `sobrecarga` usan un mapa empírico, no un modelo
   de primeros principios.
3. **Intercambio sensible puro.** En el evaporador de agua es exacto; en la topología de expansión
   directa ignora la deshumidificación.
4. **Caudal primario constante** en el circuito de agua helada. Es un **supuesto, no un hecho**: se
   verifica en el cuarto de máquinas. Si la instalación resultara de caudal primario variable
   —válvulas de dos vías y variador en las bombas—, un caudal reducido a carga parcial sería
   operación normal y la clase `caudal_agua_bajo` dejaría de ser válida tal como está planteada.
5. **Acoplamientos empíricos declarados:** subenfriamiento con presión de condensación, y área seca
   del evaporador con sobrecalentamiento. Representan efectos de modelos distribuidos mediante un
   coeficiente.
6. **Rango de validez de las fallas de flujo.** Una restricción de válvula superior a ~20 % del
   coeficiente de flujo saca a la enfriadora del régimen estacionario a carga parcial: el evaporador
   no puede desarrollar el sobrecalentamiento que la válvula necesita para abrir, porque el
   refrigerante no puede salir más caliente que el agua que lo calienta. El equipo real respondería
   ciclando, y un modelo estacionario no puede representarlo. Los puntos sin estado estacionario se
   **descartan y se cuentan**; la suite los vigila con un tope declarado.
7. **La discrepancia modelo-planta es un parámetro barrido, no una limitación oculta.** Las métricas
   con discrepancia 0 % se reportan como **cota superior teórica**, inalcanzable en campo.
8. **Parámetros provisionales.** Todos los valores de `config/params.py` esperan la placa y la hoja
   `Ficha Tecnica`.

---

## 7. Cuando lleguen los datos de campo

1. **`config/params.py`** — sustituir placa y catálogo; bajar la marca `provisional`.
2. **`src/calibracion.py`** — sustituir `mediciones_provisionales()` por las corridas reales:

```python
mediciones = [
    Medicion(cond=CondicionContorno(T_amb=33.1, HR_amb=78, Q_load_frac=0.85),
             objetivo={"P_suc": 48.0, "P_des": 172.0}),      # hoja Registro Campo
    ...
]
res = calibrar_UA(mediciones, ParametrosEquipo(), origen_datos="Registro Campo, Fase 1",
                  provisional=False)
```

`test_identificabilidad_de_la_calibracion` verifica que el ajuste recupera coeficientes conocidos,
de modo que un problema mal condicionado se detecta antes y no después.

---

## 7 bis. Exportación al visualizador web

El módulo `src/exportador_web.py` genera cuatro archivos `.js` que un visualizador local puede
cargar con `<script src=...>` **sin servidor**: bajo `file://`, Chrome y Firefox tratan el origen
como `null` y bloquean `fetch()`, así que un `.json` haría que el visualizador no abra en la máquina
del evaluador.

```bash
python -m src.exportador_web               # los cuatro .js + resultados/malla_error.json
python -m src.exportador_web --solo-malla  # solo la malla; NO necesita el .joblib
pytest tests/test_inferencia_js.py         # contrato del visualizador (sin .joblib)
pytest tests/test_exportador.py            # equivalencia exacta JS <-> scikit-learn
# y abrir web/verificacion.html con doble clic
```

| Archivo | Constante | Tamaño |
|---|---|---|
| `web/datos/fdd_modelo.js` | `FDD_MODELO` | 3,61 MB — el bosque de 100 árboles, recorrible |
| `web/datos/fdd_malla.js` | `FDD_MALLA` | 2,05 MB — mapa de operación, 4 620 puntos, dos bloques de residuos |
| `web/datos/fdd_metricas.js` | `FDD_METRICAS` | 0,03 MB — confusión y Wilson |
| `web/datos/fdd_fisica.js` | `FDD_FISICA` | 0,01 MB — equipo, fallas, campana de saturación |
| `web/js/fdd_inferencia.js` | `FDD` | 0,02 MB — inferencia de referencia |
| `web/verificacion.html` | — | autoprueba de carga local, 12 comprobaciones |

Total: **5,73 MB (5,46 MiB) en 6 archivos, cero dependencias externas** — ningún CDN, ninguna fuente web,
ningún `fetch`, ningún módulo ES6.

### Qué se puede correr en un clon limpio, y qué no

`resultados/modelo_rf.joblib` **está excluido del repositorio** (`.gitignore`): el modelo
serializado pesaba 244 MB, por encima del límite de 100 MB de GitHub. Consecuencia práctica:

| | En un clon limpio |
|---|---|
| `pytest tests/` menos `test_exportador.py` | **corre** |
| `pytest tests/test_inferencia_js.py` | **corre** — el contrato del visualizador se verifica siempre |
| `pytest tests/test_exportador.py` (5 pruebas) | **NO corre**: `FileNotFoundError` del `.joblib` |
| `python -m src.exportador_web` | **NO corre**: carga el `.joblib` antes de nada |
| `python -m src.exportador_web --solo-malla` | **corre**: la malla depende del solver, no del modelo |

Las cinco pruebas que no corren son precisamente las que verifican la **equivalencia exacta entre el
JavaScript y scikit-learn**. Ese resultado se obtuvo y está declarado más abajo, pero **no es
reproducible desde el repositorio sin reentrenar primero**:

```bash
python -m src.modelo                  # regenera resultados/modelo_rf.joblib
pytest tests/test_exportador.py       # ahora sí
```

### Equivalencia exacta con scikit-learn

Tres detalles del código fuente de scikit-learn gobiernan la implementación en JavaScript, y se
verificaron leyendo el fuente antes de escribir la prueba:

1. `ForestClassifier._validate_X_predict` convierte X a **float32**; en JavaScript hay que aplicar
   `Math.fround` a cada característica antes de comparar contra el umbral.
2. `DecisionTreeClassifier.predict_proba` devuelve `tree_.value` **sin normalizar**, así que las
   hojas se exportan verbatim y no se renormalizan.
3. `ForestClassifier.predict_proba` acumula `out += prediccion` árbol por árbol: suma **lineal**, no
   por pares. Con `n_jobs=1` el orden es determinista y la igualdad es exacta.

Resultado sobre las 1 997 muestras del conjunto de prueba: **100 % de las probabilidades idénticas
bit a bit, diferencia máxima 0,000e+00**, y cero pares (muestra, umbral) a menos de 1e-9.

### Contrato de la malla

- **Entrada canónica: la fracción de carga.** `indicePorRetorno()` existe como conveniencia y lleva
  escrita su advertencia: la relación `T_ret = 7,0 + 5,0·Q_load_frac` es la SANA y no vale bajo
  `caudal_agua_bajo`, porque con caudal degradado la misma carga produce un retorno más alto. La
  temperatura de retorno real es el campo `T_sec_in_ev`.
- `FDD_FISICA.Q_nom_W` permite convertir una demanda en vatios a fracción de carga.
- **Interpolación:** la decide el exportador y viaja en `celda_bilineal`, para que Python y
  JavaScript no puedan divergir. Los campos discretos (`regimen_cod`, `ciclado`,
  `capacidad_saturada`, `retorno_liquido`) son **siempre** vecino más próximo: interpolar un código
  de régimen produce valores que no existen en ningún estado de la máquina.
- **Fuera del dominio:** `consultar()` devuelve el valor del borde **marcado** mientras la consulta
  no se salga más de un paso de nodo, y **`null`** más allá. El margen lo calcula el exportador y
  viaja en `FDD_MALLA.margen_extrapolacion`: `[22, 38] °C` y `[0,25, 1,05]` de carga. El paso se
  toma de la celda del borde de cada lado porque el eje de cargas no es uniforme —0,03 abajo y 0,05
  arriba—. Todo estado devuelto lleva `_extrapolado` y `_fuera_de_malla: {ejes, distancia_max}`,
  presentes también cuando la consulta está dentro del dominio. El eje de severidad se **marca pero
  no se rechaza**, porque es vecino más próximo por diseño; una severidad fuera de `[0, 1]` sí falla
  ruidosamente.
- **Dominio de entrenamiento:** la malla llega hasta carga **0,28** y el dataset nunca bajó de
  **0,40** (`config/params.py:208`). Esos 1 540 nodos —el 33,3 % de la malla— están fuera del
  dominio en el que el clasificador fue entrenado, así que `consultar()` los marca con
  `_fuera_de_entrenamiento` y **`diagnosticar()` NO los clasifica**: devuelve el estado del ciclo,
  `diagnostico: null` y el motivo. Lo que falta ahí es el mandato para diagnosticar, no el cálculo.
  Los rangos los lee el exportador de `config.params.RangosContorno` —la misma configuración del
  hipercubo latino— y viajan en `FDD_MALLA.dominio_entrenamiento`; no están escritos en el
  JavaScript. `HR_amb_pct` se exporta pero no se comprueba, y el dato lo dice en
  `ejes_comprobados`.
- **Puntos sin estado estacionario:** los 189 nodos con `convergio = 0` llevan sus residuos en
  `null` y **`diagnosticar()` los rechaza**. `Math.fround(null)` vale 0, así que sin esa
  comprobación entraban al bosque como un vector de once ceros —una máquina perfectamente sana— y
  devolvían `sano` con confianza 0,348. Dieciocho de los 189 están a carga plena, así que no es un
  problema de la banda de carga baja.

### Dos bloques de residuos: `res_*` y `res_ruidoso_*`

La malla trae los residuos **dos veces**, y no son intercambiables:

| Bloque | Cómo se calcula | Para qué |
|---|---|---|
| `res_*` | limpio: sin ruido de sensor y sin discrepancia modelo-planta | diagrama P-h, validación de la malla |
| `res_ruidoso_*` | con ruido de sensor y con `theta_modelo = theta_planta·(1+epsilon)`, igual que el dataset de entrenamiento | **lo que clasifica `diagnosticar()`** |

El clasificador se entrenó con ruido y con un gemelo desafinado al 5 %, así que alimentarlo con
residuos limpios lo hace parecer mejor de lo que es. Medido con `FDD.consultar()`:

| Nodos | n | Acierto ruidoso | Acierto limpio |
|---|---|---|---|
| Todos los utilizables | 4 431 | 0,6752 | 0,7364 |
| **Dentro del dominio de entrenamiento** | **3 010** | **0,7156** | **0,7920** |
| Fuera del dominio | 1 421 | 0,5897 | 0,6186 |

La cifra defendible es la del medio: **0,7156**. La primera mezcla puntos sobre los que el
clasificador no tenía nada que decir, y la banda fuera del dominio la arrastraba hacia abajo. La
brecha limpio-ruidoso es **mayor** dentro del dominio —7,6 puntos frente a 6,1—, es decir el
optimismo de clasificar residuos limpios es más grande justo donde el visualizador se va a usar. Del
mismo orden que la cota del barrido de discrepancia (F1 macro 0,8198 con discrepancia nula frente a
0,7572 en el caso base).

El caso que lo explica: con residuos **limpios**, `sano` se reconoce el **100 %** de las veces
dentro del dominio (280 nodos), porque el residuo limpio de una máquina sana es casi exactamente
cero. Con ruido y discrepancia baja a 0,625, del orden del 0,64 que el informe reporta para `sano`
en el conjunto de prueba.

- El ruido se calcula en **Python**, no en el navegador. Los residuos son funciones no lineales de
  las mediciones —pasan por temperaturas de saturación de CoolProp—, así que sumar ruido a un
  residuo no equivale a sumar ruido a la medición. Python sigue siendo el único lugar donde se
  calculan residuos.
- Semilla propia y exportada: `SEMILLA_MALLA = 20261110`, en `FDD_MALLA.ruido_malla` junto al factor
  de ruido y al nivel y modo de discrepancia. `diagnosticar()` los devuelve en cada respuesta. No se
  deriva de `SEMILLA_MAESTRA` para no tocar el árbol de semillas con el que se generaron los
  datasets ya reportados.
- Un epsilon por **condición** (T_amb, carga), como en el dataset; una semilla de ruido por **nodo**,
  derivada del índice y no del orden de ejecución, para que la malla no dependa del número de
  núcleos.
- **El bloque ruidoso NUNCA se interpola** (`FDD_MALLA.campos_siempre_vecino`). El ruido de dos
  nodos vecinos es independiente: una bilineal de cuatro nodos reduciría la desviación típica a la
  mitad y desharía en silencio justo el efecto que el bloque existe para representar.
- 189 nodos no tienen bloque ruidoso: exactamente los mismos que no tienen estado estacionario.

### Límites medidos de la malla

`resultados/malla_error.json` guarda el error contra el solver con **muestreo dirigido celda por
celda** —no aleatorio, porque un muestreo uniforme casi nunca cae cerca de una frontera de régimen y
el promedio escondería el error grande—.

- Fuera de la banda de carga baja, el error máximo queda **por debajo del ruido de los
  instrumentos**: 0,08 K en la temperatura de evaporación frente a 0,10 K del RTD.
- En la banda `carga 0,28–0,31`, donde la máquina entra en ciclado, el error máximo llega a
  **0,43–0,55 K** en la temperatura de evaporación, cuatro o cinco veces el ruido. **No baja al
  refinar**: se midió 0,55, 0,46 y 0,57 K con pasos de 0,06, 0,03 y 0,015. Es una discontinuidad del
  modelo en el umbral de ciclado, no una malla gruesa.
- Por debajo de carga ≈ 0,25 (a 24 °C) o ≈ 0,19 (a 36 °C) el modelo **no tiene estado
  estacionario**. Esos puntos se marcan con `convergio = 0` y no se extrapolan.

**Zona de carga baja: DEFECTO ABIERTO, no usar todavía.** La bandera `ciclado` de la malla no es
fiable en su estado actual. A carga 0,28 y 30 °C el solver marca `ciclado = 1` pero devuelve una
fracción de capacidad de **0,214, por debajo del mínimo del compresor (0,25)**, sosteniendo el
setpoint exactamente: un estado que la máquina no puede tener. Existe solución válida a capacidad
mínima —entrega unos 116 kW frente a 98,5 kW de demanda, es decir sobre-entrega, que es justamente
lo que hace ciclar— pero el solver la rechaza y conserva la solución no acotada.

Consecuencia: `fraccion_marcha` vale 1,000 en toda la zona de ciclado en lugar de la proporción real
de tiempo encendido, así que **el arranque matutino todavía no se puede reconstruir con la malla**.
La causa está localizada en la selección de régimen de `src/ciclo.py:571`–`581`: `ciclado` se fija
antes de reintentar a `y_min`, y si el reintento no mejora el residuo se conserva la solución no
acotada con la bandera ya puesta.

**Alcance exacto, contado sobre la malla exportada.** De los 4 620 nodos, 623 están marcados como
`ciclado` y **519 de ellos son estados imposibles** (`y_capacidad < y_min = 0,25` sosteniendo el
setpoint). De esos 519:

- **490 están en la banda `carga < 0,34`** (nodos 0,28 y 0,31);
- **29 están en `carga = 0,34` exactamente**, con `y_capacidad` entre 0,2431 y 0,2500 —hasta 0,007
  por debajo del mínimo— en 9 de las 11 clases y a 24 y 26 °C.

Es decir: **`carga > 0,34` no está afectado; `carga = 0,34` sí lo está marginalmente.** Una versión
anterior de esta nota decía «carga ≥ 0,34 no está afectado», que es falso en la frontera.

## 8. Estructura

```
proyecto-fdd/
├── config/params.py            # parámetros, semilla, ruido, discrepancia
├── src/topologia.py            # topologías seleccionables
├── src/ciclo.py                # modelo físico (CoolProp)
├── src/calibracion.py          # ajuste de los UA, parametrizable
├── src/fallas.py               # inyección de fallas + tabla de firmas
├── src/generador.py            # barrido LHS, ruido, discrepancia, dataset
├── src/features.py             # residuos y lista blanca
├── src/modelo.py               # entrenamiento, evaluación, análisis
├── src/reporte.py              # exportación a Word
├── src/exportador_web.py       # exportación a JavaScript plano
├── web/datos/*.js              # los cuatro archivos del visualizador
├── web/js/fdd_inferencia.js    # inferencia de referencia en JavaScript
├── web/verificacion.html       # autoprueba de carga local (no es el visualizador)
├── tests/                      # 207 pruebas sobre las tres topologías
│   ├── test_ciclo.py           #   solver, unidades, dominio físico
│   ├── test_firmas.py          #   batería de firmas físicas (va primero)
│   ├── test_features.py        #   lista blanca y residuos
│   ├── test_particion.py       #   partición por grupos, sin fuga
│   ├── test_inferencia_js.py   #   contrato del visualizador — SIN .joblib
│   └── test_exportador.py      #   equivalencia JS <-> sklearn — NECESITA el .joblib
├── data/  figuras/  resultados/
├── ESPEC_Simulacion_FDD.md     # especificación v2, con registro de cambios
├── requirements.txt  README.md
```

---

## 9. Referencias

- Bell, I. H., et al. (2014). CoolProp. *Industrial & Engineering Chemistry Research, 53*(6), 2498–2508.
- Breiman, L. (2001). Random forests. *Machine Learning, 45*(1), 5–32.
- Katipamula, S., & Brambley, M. R. (2005). Methods for fault detection, diagnostics, and
  prognostics for building systems, Part I y II. *HVAC&R Research, 11*(1) y *11*(2).
- Pedregosa, F., et al. (2011). Scikit-learn. *JMLR, 12*, 2825–2830.
- Saito, T., & Rehmsmeier, M. (2015). The precision-recall plot is more informative than the ROC
  plot. *PLOS ONE, 10*(3), e0118432.
- Wilson, E. B. (1927). Probable inference, the law of succession, and statistical inference.
  *JASA, 22*(158), 209–212.
- Çengel, Y. A., & Boles, M. A. *Termodinámica.* McGraw-Hill.
- Çengel, Y. A., & Ghajar, A. J. *Transferencia de calor y masa.* McGraw-Hill.
