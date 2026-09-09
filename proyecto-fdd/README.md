# Detección y diagnóstico de fallas (FDD) por simulación

**Fase 5 — Monitoreo e Innovación** · Plan Integral de Mantenimiento
Sistema de Refrigeración y Aire Acondicionado (0251) — UTP, Facultad de Ingeniería Mecánica

Generador de datos sintéticos a partir de un modelo termodinámico del ciclo de compresión de vapor,
y clasificador Random Forest que identifica el modo de falla a partir de lo que el equipo mide en
campo.

**Sistema de estudio:** enfriadora de agua de 100 TR que da servicio a un edificio de oficinas, con
distribución hidrónica. El modelo de expansión directa se conserva como topología de respaldo.

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
python -m src.exportador_web          # genera web/datos/*.js y resultados/malla_error.json
pytest tests/test_exportador.py       # equivalencia exacta JS <-> scikit-learn
# y abrir web/verificacion.html con doble clic
```

| Archivo | Constante | Tamaño |
|---|---|---|
| `web/datos/fdd_modelo.js` | `FDD_MODELO` | 3,61 MB — el bosque de 100 árboles, recorrible |
| `web/datos/fdd_malla.js` | `FDD_MALLA` | 1,58 MB — mapa de operación, 4 620 puntos |
| `web/datos/fdd_fisica.js` | `FDD_FISICA` | 0,01 MB — equipo, fallas, campana de saturación |
| `web/datos/fdd_metricas.js` | `FDD_METRICAS` | 0,03 MB — confusión y Wilson |

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

**Cómo debe usar el visualizador la zona de carga baja.** En ciclado, el estado almacenado es el del
**período de marcha a capacidad mínima**, no un promedio del ciclo. El campo `fraccion_marcha` da la
proporción de tiempo encendido, `Q_demandada / Q_L_entregada`. El arranque matutino se reconstruye
ciclando ese estado, que es lo que hace el equipo real, en lugar de interpolar un estado que no
existe.

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
├── tests/                      # 154 pruebas sobre las tres topologías
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
