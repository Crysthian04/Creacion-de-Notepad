# Detección y diagnóstico de fallas (FDD) por simulación

**Fase 5 — Monitoreo e Innovación** · Plan Integral de Mantenimiento
Sistema de Refrigeración y Aire Acondicionado (0251) — UTP, Facultad de Ingeniería Mecánica

Generador de datos sintéticos a partir de un modelo termodinámico del ciclo de compresión de
vapor, y clasificador Random Forest que identifica el modo de falla presente a partir de las
variables que el equipo mide en campo.

**Lo que se demuestra es que el método funciona y es implementable, no que ya esté implementado.**
El modelo no fue entrenado con datos históricos de la instalación.

---

## 1. Arquitectura en tres capas

```
Capa 1 — MODELO FÍSICO (gemelo digital de caja gris)      src/ciclo.py
   entradas: T_amb, HR_amb, T_space, Q_load_frac
   salidas : estado del ciclo en condición SANA
                    |
Capa 2 — INYECCIÓN DE FALLAS                              src/fallas.py
   degrada parámetros físicos (UA, eficiencias, carga…)
   salidas : estado DEGRADADO + etiqueta del modo de falla
                    |
Capa 3 — CLASIFICADOR                                     src/modelo.py
   entrada : RESIDUOS = (medición degradada) − (predicción sana a igual contorno)
   salida  : modo de falla + severidad estimada
```

El clasificador **no opera sobre valores crudos, sino sobre residuos**. Un día a 36 °C produce
presiones de descarga altas sin que exista falla alguna; entrenado con valores crudos, el modelo
aprendería a confundir clima con avería. Al restar la predicción del modelo sano a las mismas
condiciones de contorno, la variabilidad operacional se cancela y queda solo la firma de la
degradación.

---

## 2. Instalación

```bash
cd proyecto-fdd
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Probado con Python 3.11. Las versiones están fijadas: la reproducibilidad exige controlar la
semilla **y** el entorno.

---

## 3. Cómo correr el pipeline completo

Ejecutar **en este orden**, desde la carpeta `proyecto-fdd`:

```bash
# 0. VERIFICACIÓN FÍSICA — obligatoria antes de generar nada
python -m pytest tests/ -v

# 1. Calibración de los coeficientes UA del gemelo digital
python -m src.calibracion

# 2. Generación de los dos datasets (~4 min)
python -m src.generador

# 3. Entrenamiento, evaluación, figuras e informe Word (~5 min)
python -m src.modelo
```

Salidas:

| Ruta | Contenido |
|---|---|
| `config/ua_calibrado.json` | UA ajustados, con su origen y marca de provisional |
| `data/dataset_balanceado.parquet` | 12 000 filas, 10 clases balanceadas |
| `data/dataset_prevalencia.parquet` | 3 000 filas con prevalencia de campo |
| `figuras/*.png` | Las 7 figuras del informe, a 300 dpi |
| `resultados/metricas.json` | Todas las métricas, la trazabilidad y el control de integridad |
| `resultados/informe_fdd.docx` | Informe Word listo para el documento de la fase |

### Por qué las pruebas van primero

`tests/test_firmas.py` verifica que cada modo de falla mueve las variables en la dirección
físicamente correcta: ensuciar el condensador **siempre** debe subir el split de condensación;
bajar la carga de refrigerante **siempre** debe bajar el subenfriamiento. Un simulador con firmas
invertidas produciría un clasificador con métricas excelentes sobre física equivocada, y ese es el
peor fallo posible en este proyecto porque nada en la matriz de confusión lo delataría.

Durante el desarrollo, esta batería detectó dos errores reales del modelo de fallas, documentados
en `src/fallas.py`:

1. **`restriccion_linea_liquido`** estaba modelada como una reducción del flujo másico. Esa
   formulación sube `T_evap` y baja la potencia del compresor a la vez, con lo que el COP **subía**
   en lugar de bajar. Se cambió por una caída del `UA_ev` efectivo: un evaporador hambriento baja la
   presión de succión, no la sube.
2. **`condensador_sucio`** degradaba solo `UA_cd`, con lo que el salto de aire del condensador
   apenas se movía y la «firma distintiva» de los incondensables no era verificable. Se añadió la
   caída de caudal de aire, que es lo que físicamente hace una aleta obstruida.

Opciones útiles:

```bash
python -m src.generador --n-cond 50 --n-prev 300 --sufijo _rapido   # corrida corta
python -m src.modelo --sufijo _rapido --sin-estudio-ruido           # entrenamiento rápido
python -m tests.test_ciclo --regenerar                              # recongelar los puntos de regresión
```

---

## 4. Reglas no negociables y dónde las impone el código

| Regla | Dónde se impone |
|---|---|
| El clasificador se entrena **solo** con columnas `res_*` | `features.COLUMNAS_RESIDUOS` + `construir_matriz_X()`: selección por lista blanca, nunca `drop`. Verificado en `tests/test_features.py` |
| Ninguna variable puede filtrar información sobre la etiqueta | `features.EXCLUIDAS_Y_MOTIVO` documenta cada exclusión y su razón |
| Propiedades termodinámicas con CoolProp | `ciclo.py` y `features.py`; sin correlaciones aproximadas ni tablas embebidas |
| Toda la aleatoriedad con semilla fija y declarada | `config.params.SEMILLA_MAESTRA`, un único literal; flujos derivados con `SeedSequence.spawn()` |
| GridSearchCV optimiza **F1 macro**, nunca exactitud | `modelo.seleccionar_modelo()`, `scoring="f1_macro"` |
| Se evalúan los **dos** conjuntos de prueba | `modelo.ejecutar()` reporta balanceado y prevalencia realista |
| Parámetros del equipo en configuración separada y marcados como provisionales | `config/params.py` + `advertir_provisionales()` al arrancar |
| Convergencia verificada en cada punto y descartes reportados | `ciclo.resolver_ciclo()` devuelve `convergio`; `generador.ContabilidadSolver` los cuenta |
| El conjunto de prueba se toca **una sola vez** | `modelo.ConjuntoSellado` cuenta cada apertura; `seleccionar_modelo()` no recibe el test en su firma; `metricas.json` marca `corrida_valida: false` si hubo más de una apertura |
| Partición sin fuga de condiciones entre conjuntos | `modelo.particionar()` corta por grupos de `cond_id`. Verificado en `tests/test_particion.py` |

### Nota sobre reproducibilidad

`np.random.default_rng(seed_sequence)` **no** es reproducible entre llamadas en NumPy ≥ 2: deriva un
hijo nuevo cada vez. El proyecto usa `generador.rng_desde()`, que reconstruye el `SeedSequence` a
partir de su entropía y su `spawn_key`. Lo detectó
`tests/test_particion.py::test_muestreo_reproducible_con_la_misma_semilla`, y es justo el tipo de
fallo silencioso que la auditoría previa anticipó: la semilla estaba puesta y aun así el resultado
no era reproducible.

---

## 5. Simplificaciones declaradas

Una limitación declarada y analizada es criterio; una no declarada es un error.

1. **Datos sintéticos.** El modelo no fue entrenado con datos históricos de la instalación.
2. **Inventario de refrigerante.** `carga_baja`, `sobrecarga` y `restriccion_linea_liquido` usan un
   mapa empírico (sección 4.1 de la especificación), no un modelo de primeros principios. Modelar
   el inventario con rigor exigiría intercambiadores distribuidos.
3. **Intercambio sensible puro.** Los intercambiadores se modelan como `m_a·cp_a·eps·ΔT`, tal como
   fija la especificación. No se modela la deshumidificación del evaporador; por eso `HR_amb` se
   registra como medición pero no interviene en el cierre del ciclo.
4. **Carga parcial.** `Q_load_frac` se implementa como fracción del caudal de aire nominal del
   evaporador: un proxy de la operación a carga parcial de un equipo de velocidad fija con control
   on/off. El modelo describe el estado cuasi-estacionario durante el periodo de marcha, no el
   ciclado. A carga baja y ambiente frío el modelo predice temperaturas de evaporación bajo cero;
   en el equipo real eso correspondería a formación de escarcha, que este modelo no representa.
5. **`condensador_sucio` degrada también el caudal de aire**, apartándose de la letra de la
   sección 4. La justificación está en `src/fallas.py`.
6. **No hay discrepancia entre modelo y planta.** Los residuos se calculan contra el mismo modelo
   que generó los datos, así que el único error presente es el ruido de los instrumentos. En una
   instalación real, el error del gemelo digital frente al equipo físico sería la fuente de error
   dominante. **Las métricas de este proyecto son una cota superior del desempeño alcanzable, no el
   desempeño esperado en campo.** Es la limitación más importante de las declaradas aquí.
7. **Parámetros del equipo provisionales.** Todos los valores de `config/params.py` esperan la hoja
   `Ficha Tecnica`. El pipeline los declara en pantalla y en `metricas.json` en cada corrida.

---

## 6. Cuando lleguen las mediciones de campo de la Fase 1

Dos cambios, ningún reescribir:

1. **`config/params.py`** — sustituir los valores de placa y catálogo, y bajar la marca
   `provisional` en `FUENTE_PARAMETROS`.
2. **`src/calibracion.py`** — sustituir `mediciones_provisionales()` por las corridas reales de la
   hoja `Registro Campo`:

```python
mediciones = [
    Medicion(cond=CondicionContorno(T_amb=33.1, HR_amb=78, T_space=24.5, Q_load_frac=1.0),
             objetivo={"P_suc": 132.0, "P_des": 405.0}),      # corrida 1
    ...                                                        # una por circuito
]
res = calibrar_UA(mediciones, ParametrosEquipo(), origen_datos="Registro Campo, Fase 1",
                  provisional=False)
```

Cualquier atributo de `EstadoCiclo` sirve como variable objetivo; se eligen las medidas con menor
incertidumbre. `tests/test_ciclo.py::test_identificabilidad_de_la_calibracion` verifica que el
ajuste recupera coeficientes conocidos, de modo que un problema mal condicionado se detecta antes
de que lleguen los datos y no después.

Para la validación contra el equipo real (sección 8 de la especificación): calcular los residuos de
esos puntos con el modelo sano calibrado, pasarlos por el clasificador y contrastar contra el
diagnóstico manual de la hoja `Desviaciones`. Si el modelo señala otra cosa, **también es un
resultado publicable**: se documenta la discrepancia y se discuten las causas.

---

## 7. Estructura del proyecto

```
proyecto-fdd/
├── config/
│   ├── params.py              # parámetros del equipo (provisionales) y semilla maestra
│   └── ua_calibrado.json      # salida de la calibración
├── src/
│   ├── ciclo.py               # modelo físico del ciclo (CoolProp)
│   ├── calibracion.py         # ajuste de los UA, parametrizable        [módulo añadido]
│   ├── fallas.py              # inyección de los 9 modos + tabla de firmas
│   ├── generador.py           # barrido LHS, ruido y construcción del dataset
│   ├── features.py            # variables derivadas y residuos (lista blanca)
│   ├── modelo.py              # entrenamiento, evaluación y análisis
│   └── reporte.py             # exportación a Word                      [módulo añadido]
├── tests/
│   ├── test_ciclo.py          # unidades, balance, 2.ª ley, regresión, identificabilidad
│   ├── test_firmas.py         # verificación física de los 9 modos de falla
│   ├── test_features.py       # lista blanca de características
│   └── test_particion.py      # independencia de barridos y partición sin fuga
├── data/                      # datasets generados (Parquet)
├── figuras/                   # 7 figuras a 300 dpi
├── resultados/                # metricas.json e informe_fdd.docx
├── requirements.txt
└── README.md
```

`calibracion.py` y `reporte.py` no aparecen en la sección 10 de la especificación. Se separaron a
propósito: la calibración se va a repetir con los datos de campo, y el informe debe poder
regenerarse sin reentrenar.

---

## 8. Referencias

- Bell, I. H., Wronski, J., Quoilin, S., & Lemort, V. (2014). Pure and pseudo-pure fluid
  thermophysical property evaluation and the open-source thermophysical property library CoolProp.
  *Industrial & Engineering Chemistry Research, 53*(6), 2498–2508.
- Breiman, L. (2001). Random forests. *Machine Learning, 45*(1), 5–32.
- Katipamula, S., & Brambley, M. R. (2005). Methods for fault detection, diagnostics, and
  prognostics for building systems — A review, Part I y Part II. *HVAC&R Research, 11*(1), 3–25 y
  *11*(2), 169–187.
- Pedregosa, F., et al. (2011). Scikit-learn: Machine learning in Python. *Journal of Machine
  Learning Research, 12*, 2825–2830.
- Saito, T., & Rehmsmeier, M. (2015). The precision-recall plot is more informative than the ROC
  plot when evaluating binary classifiers on imbalanced datasets. *PLOS ONE, 10*(3), e0118432.
- Çengel, Y. A., & Boles, M. A. *Termodinámica.* McGraw-Hill.
- Çengel, Y. A., & Ghajar, A. J. *Transferencia de calor y masa.* McGraw-Hill.
