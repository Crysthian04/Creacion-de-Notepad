# Módulo de detección y diagnóstico de fallas (FDD)

**Material para el informe final** — Plan Integral de Mantenimiento, KFC San Francisco
Curso 0251, Mantenimiento de Sistemas de Refrigeración y A/A — UTP, Facultad de Ingeniería Mecánica
Fase 5, Monitoreo e Innovación

| | |
|---|---|
| Repositorio | `Crysthian04/Creacion-de-Notepad`, carpeta `proyecto-fdd/` |
| Rama | `claude/fdd-random-forest-audit-gjehhl` |
| Commit del código | `8764236` |
| Fecha de esta exportación | 15 de noviembre de 2026 |

> **Cómo leer las cifras de este documento.** Cada número lleva entre paréntesis el archivo, la
> función y el commit que lo producen. Los resultados de la sección (g) se volvieron a calcular el
> 15 de noviembre de 2026 reejecutando `python -m src.modelo --sin-informe` con la semilla
> declarada, y se compararon uno a uno contra el artefacto guardado. Donde algo no existe en el
> repositorio, se escribe **«no disponible»** en lugar de estimarlo.

> **Nota de procedencia sobre el sitio.** El nombre «KFC San Francisco» **no aparece en ningún
> archivo del módulo FDD**; procede del encargo, no del código ni de la documentación. Lo que el
> módulo sí documenta es el equipo modelado, y no es el del local: ver la sección (c).

---

## (a) Resumen para la sección 12

**Qué es.** El módulo FDD es un sistema que, a partir de las variables que un técnico ya mide en
campo —presiones de succión y descarga, temperaturas del circuito, caudal y potencia eléctrica—,
identifica **cuál** de once modos de falla está presente en un equipo de refrigeración, y no solo
que «algo va mal». Se compone de dos piezas: un **gemelo digital** del ciclo de compresión de vapor
que predice cómo debería comportarse la máquina sana en las condiciones del momento, y un
**clasificador Random Forest** que lee la diferencia entre lo medido y esa predicción.

**Para qué sirve.** Un mantenimiento basado en condición necesita saber qué hay que intervenir. La
diferencia entre «el consumo subió un 12 %» y «el condensador está sucio con severidad moderada» es
la diferencia entre programar una inspección y programar una limpieza con su repuesto y su ventana
de parada. El método es implementable con el inventario de instrumentos que la Fase 1 levantó: no
exige instrumentación nueva.

**Qué resultados da.** Sobre datos que el modelo nunca vio, con ruido de sensor y con un error de
calibración del gemelo digital del 5 %:

| Escenario | F1 macro | PR-AUC macro | n |
|---|---|---|---|
| Prueba balanceada (todas las fallas igual de frecuentes) | **0,7543** | 0,8074 | 1 997 |
| Prevalencia realista (68 % de las muestras son máquina sana) | **0,5835** | 0,7205 | 9 964 |

Lo que esas cifras significan en la práctica: de cada diez equipos con **condensador sucio**,
**incondensables**, **carga baja de refrigerante** o **caudal de agua bajo**, el sistema acierta el
modo de falla en ocho o nueve. En cambio **restricción de línea de líquido** y **válvula de
expansión restringida** se confunden entre sí y con la máquina sana, y en escenario realista la
mayoría de las alarmas de las fallas raras son falsas: en escenario realista, de cada ocho avisos
de `txv_restringida` solo uno lo es (precisión 0,12), y lo mismo con `sobrecarga` (0,13) y
`txv_sobrealimenta` (0,17). **El sistema sirve para orientar una inspección, no para autorizar un
repuesto sin verla.**

Tres condiciones que acotan el alcance y que el informe no debe omitir: los datos son
**simulados**, no medidos; el equipo modelado **no es el del local** (sección c); y los parámetros
del gemelo digital siguen marcados como **provisionales** a la espera de la hoja `Registro Campo`
de la Fase 1. Lo que la Fase 5 demuestra es que **el método funciona y es implementable**, no que
ya esté implantado.

---

## (b) Arquitectura

Tres capas, en `proyecto-fdd/src/`:

```
Capa 1  src/ciclo.py       Gemelo digital de caja gris del ciclo de compresión de vapor
Capa 2  src/fallas.py      Inyección de fallas: degrada parámetros físicos del modelo
Capa 3  src/features.py    Residuos  →  src/modelo.py  Clasificador
```

### Capa 1 — Modelo físico de caja gris

«Caja gris» significa que la estructura es física —balances de energía y de masa, propiedades
reales del refrigerante— pero algunos coeficientes se ajustan con datos (`UA_ev`, `UA_cd`) en lugar
de deducirse de la geometría. Las propiedades del R-134a salen de **CoolProp** (Bell et al., 2014),
no de tablas interpoladas a mano (`src/ciclo.py:98`–`126`).

El estado se resuelve cerrando **tres ecuaciones** simultáneas con `scipy.optimize.fsolve`: balance
del evaporador, balance del condensador y balance de flujo de la válvula de expansión. Las
incógnitas son la temperatura de evaporación, la de condensación y el sobrecalentamiento; bajo
control de capacidad, la fracción de capacidad `y` sustituye a una de ellas.

| Elemento | Ecuación | Origen |
|---|---|---|
| Intercambiadores | `ε = 1 − exp(−UA / C)`, con `C = ṁ·c_p` | `src/ciclo.py:267`, `src/ciclo.py:288`–`289` |
| Escalado del UA con el caudal | `UA ∝ ṁ^0,8` | `src/ciclo.py:261`–`262` |
| Área seca del evaporador | `UA_ev,ef = UA_ev · (1 − β_SH · mín(SH / SH_ref, 1))`, β = 0,45 | `src/ciclo.py:288` |
| Compresor, caudal másico | `ṁ_r = y · V_disp · N_rev · η_v / v_suc` | `src/ciclo.py:318` |
| Rendimiento volumétrico | `η_v = (η_v0 − k_v·(r_p − 1)) · f_ηv` | `src/ciclo.py:314` |
| Rendimiento isentrópico a carga parcial | `η_s = η_s0 · (1 − k_cp·(1 − y)) · f_ηs` | `src/ciclo.py:316` |
| Subenfriamiento acoplado a la presión | `SC = SC_nom + k_SC·(T_cond − T_cond,ref) + ΔSC_falla` | `src/ciclo.py:326` |
| Caída en la línea de líquido | `ΔP_línea = frac · (P_cond − P_suc)` | `src/ciclo.py:334` |
| Válvula de expansión como elemento de flujo | `ṁ_v = K_v · f_Kv · a(SH) · √(ρ_líq · ΔP_válvula)` | `src/ciclo.py:358` |
| Apertura de la válvula | `a = clip(a_nom + Δa + K_ctrl·f_Kctrl·(SH − SH_obj), a_mín, 1)` | `src/ciclo.py:355`–`357` |
| Potencia y corriente | `W_elec = W_comp/η_motor + W_aux`; `I = W_elec/(√3·V·cos φ)` | `src/ciclo.py:369`–`370` |

Función de entrada: `resolver_ciclo` (`src/ciclo.py:386`). **La convergencia siempre se devuelve
como dato y nunca se asume**: cada punto trae su residuo y su motivo de descarte.

### Capa 2 — Inyección de fallas

Una falla **no** se simula sumando un número a una medición: se simula **degradando el parámetro
físico que la falla degrada en la máquina real**, y dejando que el solver propague la consecuencia.
Un condensador sucio baja el `UA` del condensador y el caudal de aire; el resto —presión de
condensación, relación de presiones, COP, temperatura de descarga— sale del balance, no de una
regla. Catálogo completo en `src/fallas.py:88`–`210`, función `ajustes_de_falla`.

Eso tiene una consecuencia que conviene decir en la defensa: **las firmas no se programaron, se
verificaron**. La batería `tests/test_firmas.py` comprueba que cada falla mueve cada variable en la
dirección físicamente correcta en todo el dominio, y durante el desarrollo encontró siete errores
reales del modelo.

### Capa 3 — Residuos y clasificador

```
residuo  =  variable derivada MEDIDA (con falla y con ruido)
          − variable derivada PREDICHA por el gemelo sano, en las MISMAS condiciones de contorno
```

(`src/features.py:182`, función `calcular_residuos`.) Son once residuos:
`res_SH_evap`, `res_SH_total`, `res_SC`, `res_SH_des`, `res_rp`, `res_COP`, `res_kW_TR`,
`res_approach_ev`, `res_dT_agua_ev`, `res_split_cond`, `res_dT_air_cd`
(`src/features.py:87`, función `columnas_residuos`).

### Por qué residuos y no valores crudos

Es la decisión central del módulo, y hay tres razones:

1. **Un valor crudo no distingue clima de falla.** Una presión de descarga de 180 psig es normal a
   35 °C de ambiente y es una alarma a 24 °C. Entrenado con valores crudos, el clasificador
   aprendería a leer el termómetro exterior: alcanzaría métricas excelentes aprendiendo la
   estación del año en lugar de la avería. El residuo resta la dependencia del contorno porque la
   predicción sana se calcula **en las mismas condiciones** que la medición.
2. **El residuo tiene signo y el signo es interpretable.** `res_split_cond > 0` significa que el
   condensador está más caliente respecto del aire de lo que debería. Eso se puede contrastar con
   la física, y el proyecto lo contrasta: el residuo que la teoría señala como dominante está
   entre los tres primeros por importancia en **10 de 10** clases, y es el primero en **7 de 10**
   (`resultados/metricas.json` → `contraste_con_la_fisica`, función
   `src.modelo.contrastar_con_fisica`, commit `d6d9628`).
3. **La exclusión es trazable.** La matriz de entrada se construye por **lista blanca** de columnas
   `res_*`, nunca descartando columnas no deseadas (`src/features.py:197`,
   `construir_matriz_X`). `T_amb`, `HR_amb`, `Q_load_frac`, las presiones crudas, la etiqueta, la
   severidad, el identificador de condición y las banderas del control están excluidas **con su
   motivo escrito** en `EXCLUIDAS_Y_MOTIVO` (`src/features.py:94`). Si mañana aparece una columna
   nueva, no entra sola al modelo: hay que añadirla a la lista blanca a propósito.

---

## (c) Equipo modelado, y por qué no es el del local

**Lo que el módulo modela:** una **enfriadora de agua (chiller) de 100 TR = 351 685 W**, con
compresor de tornillo, **refrigerante R-134a** y **condensador enfriado por aire**, que da servicio
a un edificio de oficinas con distribución hidrónica. El evaporador intercambia contra agua helada.
(`config/params.py:29` `TIPO_SISTEMA = "chiller_cond_aire"`; `config/params.py:103`
`refrigerante = "R134a"`; `Q_nom = 351685.0` W; commit `cd5f1db`.)

**Por qué no es el equipo del KFC.** El sitio de estudio del proyecto es un **congelador de
expansión directa** —condensadora Heatcraft MOH019L63CF, **R-404A**, baja temperatura de **−40 a
0 °F** (−40 a −17,8 °C), evaporador de aire con **desescarche eléctrico**—. Son dos máquinas
distintas en refrigerante, en nivel de temperatura, en fluido secundario del evaporador y en la
existencia misma de un ciclo de desescarche. El módulo FDD se construyó antes de ese cambio de
sitio y conserva la enfriadora, **declarado explícitamente** en `README.md:13`–`21`.

**Por qué no se adaptó: está medido, no estimado.** La auditoría del 10 de noviembre
(`AUDITORIA_FDD_10NOV.md`, sección 6) ejecutó el solver con el preset de expansión directa y
R-404A:

| `T_espacio` | ¿Converge? | Observación |
|---|---|---|
| +24 °C | sí | temperaturas de aire acondicionado |
| 0 °C | sí | |
| −18 °C | sí | |
| **−25 °C** | **no** | residuo 6,47e-01 |
| **−30 °C** | **no** | residuo 7,21e-01 |

La causa está localizada: `src/ciclo.py:417` fija `te_min = máx(T_triple + 5, −25,0)`. Para el
R-404A manda el literal **−25,0 °C**, de modo que con el espacio a −25 °C el intervalo de búsqueda
queda invertido (`te_max = −25,5 < te_min = −25,0`) y **no existe solución posible**. Es decir: con
el código actual, **la mitad inferior del rango declarado del equipo nuevo es inalcanzable por
construcción**.

Y bajar ese piso **no basta**. Una segunda sonda cargó el módulo en memoria con el literal en
−60 °C: a −40 °C el modelo converge, pero entrega **817 W de un serpentín nominal de 17 584 W**,
con 0,22 K de sobrecalentamiento y en régimen hambriento. No es un modelo de congelador: es un
modelo de aire acondicionado de 5 TR operando muy fuera de su diseño.

Faltan cuatro piezas de física que el módulo no tiene:

| Pieza ausente | Por qué importa en un congelador |
|---|---|
| **Calor latente y escarcha** | el intercambio es sensible puro (`src/ciclo.py:43`–`45`); por debajo de 0 °C el vapor de agua no condensa, escarcha, y la escarcha degrada `UA` y caudal de aire |
| **Ciclo de desescarche eléctrico** | es intrínsecamente transitorio y el modelo es estacionario |
| **Marcha y parada por termostato** | el preset DX tiene `y_min = 1,0` (sin modulación); toda la maquinaria `controlado / saturado / ciclado` es de válvula deslizante de enfriadora |
| **Clase de falla «evaporador escarchado / desescarche fallido»** | es la avería característica del equipo nuevo y **no existe en el catálogo** |

**Esfuerzo estimado: 59 a 118 horas** (`AUDITORIA_FDD_10NOV.md`, sección 6.4), repartidas en
6–10 h de parámetros, 43–90 h de reescritura de física y 10–18 h de regenerar, reentrenar y
reexportar. Incertidumbre declarada ±35–50 %, sesgada hacia arriba. **Decisión del proyecto del
10 de noviembre de 2026: no adaptar; conservar la enfriadora y declararlo** (`README.md:13`–`21`,
`ESPEC_Simulacion_FDD.md:35`–`57`, commit `2ba4c99`).

Lo que esto significa para el informe, dicho sin rodeos: **el módulo FDD demuestra un método, no
diagnostica el equipo del local.** Esa frase debe aparecer en la sección 12.

---

## (d) Datos de entrenamiento

### Las once clases

| # | Clase | Qué se degrada en el modelo | Origen |
|---|---|---|---|
| 0 | `sano` | nada | `src/fallas.py:88`–`91` |
| 1 | `condensador_sucio` | `UA_cd ·(1 − 0,45f)` y caudal de aire `·(1 − 0,25f)` | `src/fallas.py:99` |
| 2 | `incrustacion_evaporador` | `UA_ev ·(1 − 0,40f)` | `src/fallas.py:110` |
| 3 | `caudal_agua_bajo` | caudal de agua `·(1 − 0,40f)` | `src/fallas.py:115` |
| 4 | `carga_baja` | `K_v ·(1 − 0,35f)` y `ΔSC = −0,85·f·SC_nom` | `src/fallas.py:130` |
| 5 | `sobrecarga` | `ΔSC = +2,0f` y `UA_cd ·(1 − 0,20f)` | `src/fallas.py:146` |
| 6 | `txv_restringida` | `K_v ·(1 − 0,20f)` | `src/fallas.py:174` |
| 7 | `txv_sobrealimenta` | apertura base sube, ganancia del lazo cae a cero | `src/fallas.py:180` |
| 8 | `compresor_desgastado` | `η_v ·(1 − 0,30f)` y `η_s ·(1 − 0,25f)` | `src/fallas.py:184` |
| 9 | `incondensables` | presión de descarga `·(1 + 0,15f)` | `src/fallas.py:190` |
| 10 | `restriccion_linea_liquido` | `ΔP_línea = 0,45f·(P_cond − P_suc)`, con flasheo | `src/fallas.py:210` |

### Las tres severidades

`f ∈ [0, 1]` es continua; los tres **niveles** son tramos de muestreo
(`src/fallas.py:67`–`70`, commit `cd5f1db`):

| Nivel | Tramo de `f` |
|---|---|
| incipiente | 0,15 – 0,35 |
| moderada | 0,35 – 0,65 |
| severa | 0,65 – 0,95 |

Cada condición de contorno genera **una muestra por clase y por nivel**, con `f` sorteada
uniformemente dentro del tramo. De ahí 11 clases × 3 niveles × n condiciones.

### El muestreo de condiciones de contorno

Hipercubo latino sobre tres variables (`src/generador.py:105`, `muestrear_condiciones`;
`scipy.stats.qmc.LatinHypercube`):

| Variable | Rango | Origen |
|---|---|---|
| Temperatura del aire al condensador | 24,0 – 36,0 °C | `config/params.py:204`–`205` |
| Humedad relativa ambiente | 60 – 95 % | `config/params.py:206`–`207` |
| **Fracción de carga `Q_load_frac`** | **0,40 – 1,00** | `config/params.py:208`–`209` |

> ⚠ **Corrección a la premisa del encargo.** El encargo habla de «el hipercubo latino de **120**
> puntos de operación». Ese número existe en el proyecto, pero **es otra cosa**: 120 es el número
> de condiciones de los **estudios de sensibilidad** al ruido y a la discrepancia
> (`src/modelo.py:517`, `:538`, `:566`, `n_cond=120`). El conjunto de entrenamiento usa
> **400 condiciones** (`config/params.py:279`, `N_COND_ENTRENAMIENTO = 400`) y el de prevalencia
> **10 000 muestras independientes** (`config/params.py:280`). Las cifras verificadas son:

| Conjunto | Condiciones (hipercubo) | Intentos | Convergidos | Descartados |
|---|---|---|---|---|
| Balanceado | 400 | 13 200 | **13 077** | 123 (0,93 %) |
| Prevalencia realista | 10 000 (una por muestra) | 10 000 | **9 964** | 36 (0,36 %) |

(`resultados/metricas.json` → `generacion`, función `src.generador.generar_todo`, commit
`d6d9628`.) **Cero condiciones descartadas por completo**, así que la partición por grupos no
perdió ningún grupo.

### El ruido inyectado

El ruido se suma a las **mediciones**, no a los residuos, antes de derivar nada
(`src/generador.py:160`, `aplicar_ruido`). Cada σ se trazó a la hoja `Instrumentos` del
levantamiento y vale **exactitud / 2**, asumiendo que la exactitud declarada es un intervalo del
95 % (`config/params.py:225`–`255`, commit `cd5f1db`):

| Variable | σ | Instrumento |
|---|---|---|
| `P_suc` | 0,75 psig (0,25 % de 300 FS) | manifold digital |
| `P_des` | 1,25 psig (0,25 % de 500 FS) | manifold digital |
| `T_ev_out`, `T_suc`, `T_des`, `T_liq` | 0,25 K | termopar tipo K |
| `T_agua_in_ev`, `T_agua_out_ev` | 0,10 K | RTD Pt100 en pozo |
| `T_air_in_cd`, `T_air_out_cd` | 0,15 K | sonda T-HR |
| `I_avg` | 0,75 % de la lectura | pinza True RMS |
| `W_elec` | 0,50 % de la lectura | analizador de redes |
| `V_agua_ev` | 1,0 % de la lectura | caudalímetro ultrasónico |

**Hay una segunda fuente de error, más grande que el ruido, y es deliberada.** Los datos se generan
con los parámetros de la planta, pero la referencia sana que se resta se calcula con
`θ_modelo = θ_planta·(1 + ε)`, con `|ε| ≤ 5 %` sorteado por condición
(`config/params.py:264`, `src/generador.py:122` `muestrear_discrepancia`). Representa el error de
calibración del gemelo digital, que en campo es el error **dominante**. Sin él, el residuo de una
máquina sana sería ruido puro y la separación entre clases sería trivial por construcción: el F1
macro subiría de 0,757 a 0,820 (sección g).

### ¿Hubo fracciones de carga menores de 0,34?

**No. Cero.** Contado sobre los `.parquet` que alimentaron el entrenamiento:

| Conjunto | Filas | `Q_load_frac < 0,40` | `< 0,34` | Mínimo observado |
|---|---|---|---|---|
| `data/dataset_balanceado.parquet` | 13 077 | **0** | **0** | 0,4011 |
| `data/dataset_prevalencia.parquet` | 9 964 | **0** | **0** | 0,4000 |

El piso está en la configuración (`config/params.py:208`, `Q_load_frac_min = 0.40`) y el muestreo
no lo cruza nunca. Dos consecuencias que importan:

- **Cero filas en régimen de ciclado** (`resultados/metricas.json` → `generacion.banderas.ciclado`
  = 0). El clasificador nunca vio la máquina arrancando y parando.
- Donde **sí** hay cargas por debajo de 0,34 es en la **malla de operación exportada al
  visualizador**, que llega hasta 0,28 para poder dibujar la zona de ciclado. Esa malla **no es
  dato de entrenamiento**. Desde el 10 de noviembre el visualizador marca esos puntos con
  `_fuera_de_entrenamiento` y **se niega a diagnosticarlos** (sección h).

---

## (e) Clasificador

**Familia ganadora: Random Forest**, elegido contra un árbol de decisión único por **F1 macro sobre
el conjunto de validación** (`src/modelo.py:183`, `seleccionar_modelo`):

| Candidato | F1 macro (validación cruzada) | F1 macro (validación) |
|---|---|---|
| Árbol de decisión | 0,6962 | 0,7239 |
| **Random Forest** | **0,7470** | **0,7608** |

**Hiperparámetros elegidos** (`GridSearchCV`, `scoring='f1_macro'`, `GroupKFold(4)`):

| Parámetro | Valor | Rejilla explorada |
|---|---|---|
| `n_estimators` | 100 | `[100]` |
| `max_depth` | 16 | `[None, 16]` |
| `min_samples_leaf` | 1 | `[1, 2, 4]` |
| `max_features` | 0,5 | `['sqrt', 0.5]` |

(`src/modelo.py:177`–`178`, `REJILLA_RF`; resultado en `resultados/metricas.json` →
`seleccion_de_modelo`.)

**La optimización es por F1 macro y nunca por exactitud.** Con once clases y una de ellas al 68 %
en el escenario realista, optimizar exactitud premiaría a un modelo que dijera «sano» casi siempre.

**Semilla.** `SEMILLA_MAESTRA = 20260902` (`config/params.py:35`), propagada a la partición, al
`random_state` de los dos estimadores, al ruido, a la severidad y a la discrepancia mediante un
árbol de `SeedSequence` (`src/generador.py:97`, `semillas_derivadas`).

**Separación entre entrenamiento y prueba — por grupos, no por fila.** Una condición de contorno
genera 33 filas (11 clases × 3 niveles). Partir por fila metería la misma condición en
entrenamiento y en prueba, que es fuga. La partición es `GroupShuffleSplit` sobre `cond_id`
(`src/modelo.py:144`, `particionar`):

| Partición | Filas | Condiciones |
|---|---|---|
| Entrenamiento | 9 151 | 280 |
| Validación | 1 929 | 59 |
| **Prueba (sellada)** | **1 997** | **61** |

**Condiciones compartidas entre particiones: 0.** Verificado con un `assert` que aborta la corrida
(`src/modelo.py:660`–`662`), no con una comprobación opcional.

**El conjunto de prueba está sellado por construcción.** La clase `ConjuntoSellado`
(`src/modelo.py:85`) lleva la cuenta de cuántas veces se abre y por qué motivo; si se abre más de
una vez, emite un aviso y la corrida queda marcada `corrida_valida = False`. En la corrida
reportada: **una apertura por conjunto**, motivo «evaluación final del informe»,
`corrida_valida = true`.

**Dos modelos, no uno.** El modelo principal se evalúa en la prueba balanceada. Para el escenario
de prevalencia realista se entrena un segundo Random Forest con los mismos hiperparámetros y
`class_weight='balanced'` (`src/modelo.py:674`–`679`), porque con 68 % de clase sana un modelo sin
ponderar ignora las clases raras. Se reportan ambos: con ponderación (F1 macro 0,5835) y sin ella
(0,5851).

**Modelo auxiliar de severidad.** Un regresor estima `f` a partir de los mismos residuos:
MAE 0,1030 y R² 0,652 en prueba (`resultados/metricas.json` → `modelo_de_severidad`).

---

## (f) Métricas: qué es cada una y por qué se usa

Todas se calculan en `src/modelo.py:218`, función `evaluar`.

| Métrica | En lenguaje sencillo | Por qué se usa aquí |
|---|---|---|
| **Matriz de confusión** | Una tabla: en la fila va lo que la máquina tenía de verdad, en la columna lo que el sistema dijo. La diagonal son los aciertos. | Es la única métrica que dice **con qué se confunde** cada falla. Saber que `txv_restringida` se confunde con `sano` y con `restriccion_linea_liquido` orienta qué medición adicional desempataría en campo. |
| **Precisión** | De todas las veces que el sistema dijo «condensador sucio», ¿qué fracción lo era de verdad? | Es el coste de las **falsas alarmas**: una precisión de 0,13 significa que siete de cada ocho órdenes de trabajo emitidas por esa alarma serían en vano. |
| **Sensibilidad (recall)** | De todos los equipos que de verdad tenían condensador sucio, ¿a qué fracción se la detectó? | Es el coste de las **fallas que se escapan**. En mantenimiento pesa más que la precisión: una falla no detectada degrada el equipo. |
| **F1 por clase** | La media armónica de precisión y sensibilidad de esa clase: un solo número que castiga si cualquiera de las dos es mala. | Permite ver **qué fallas el método diagnostica bien y cuáles no**, que es lo que el informe debe declarar en lugar de un promedio que lo esconda. |
| **F1 macro** | El promedio simple de los F1 de las once clases: **todas pesan igual**, la rara y la frecuente. | Es el criterio de optimización del proyecto. Con una clase al 68 %, cualquier métrica ponderada por frecuencia se dejaría dominar por ella. |
| **Prevalencia realista** | Evaluar sobre un conjunto donde las clases aparecen con la frecuencia que tienen **en una instalación real**: 68 % sano y las averías repartidas según su frecuencia esperada. | La prueba balanceada mide la **capacidad de discriminar**; la de prevalencia mide **lo que pasaría al conectarlo**. Reportar solo la primera sería optimista. |
| **PR-AUC** | Área bajo la curva precisión-sensibilidad: resume, en un número, el compromiso en **todos** los umbrales de decisión posibles, no solo en el que el modelo usa. | Con clases muy desbalanceadas, la curva ROC es engañosamente optimista porque los verdaderos negativos la inflan. La PR-AUC no (Saito y Rehmsmeier, 2015). |
| **Detección por severidad** | La fracción de aciertos **separada por cuán grave es la falla**, de incipiente a severa. | Es la métrica que contesta la pregunta de mantenimiento: ¿con cuánta antelación avisa? Un sistema que solo acierta cuando la falla ya es severa no sirve para mantenimiento predictivo. |

### Por qué no se reporta la exactitud como resultado

La **exactitud global** es la fracción de aciertos sobre el total. Con once clases y una de ellas al
68 %, un modelo que respondiera siempre «sano» obtendría **68 % de exactitud sin diagnosticar
nada**. Es decir: la exactitud puede ser alta precisamente cuando el sistema es inútil. Por eso el
proyecto la impone en último lugar y por escrito en la función que calcula las métricas —«las
métricas en el orden de la sección 7.3: la exactitud va al final», `src/modelo.py:219`— y optimiza
F1 macro en su lugar.

Se **calcula y se publica** de todos modos, por dos razones: es la métrica que un lector no técnico
espera, y sirve de **alarma**. Si la exactitud sobre datos no vistos subiera por encima de 0,95,
eso no sería un buen resultado sino la señal de que hay fuga de datos. Ver la sección (g).

---

## (g) Resultados

### Cómo se obtuvieron estos números

El **15 de noviembre de 2026** se volvió a ejecutar el entrenamiento completo desde cero, en un
contenedor recién construido, con la semilla declarada:

```bash
python -m src.modelo --sin-informe     # entrena, evalúa y escribe resultados/metricas.json
python -m src.figuras_informe          # figuras a 300 dpi + export_informe/metricas.json
```

El resultado se comparó, **clave por clave y valor por valor**, contra el artefacto
`resultados/metricas.json` que quedó commiteado el 10 de noviembre (commit `d6d9628`):

> **0 claves distintas, 0 valores distintos.** La corrida es bit a bit reproducible cinco días
> después, en otra máquina, con el entorno reinstalado desde `requirements.txt`.

Además, `src/figuras_informe.py` recalcula las métricas desde el modelo serializado y **aborta la
generación** si alguna difiere de `resultados/metricas.json` en más de 1e-12. No abortó.

### Resultados principales

| Métrica | Prueba balanceada | Prevalencia realista |
|---|---|---|
| n de muestras | 1 997 | 9 964 |
| **F1 macro** | **0,7543** | **0,5835** |
| **PR-AUC macro** | **0,8074** | 0,7205 |
| F1 ponderado | 0,7527 | 0,7293 |
| Sensibilidad macro | 0,7391 | 0,7269 |
| Exactitud global | 0,7376 | 0,6827 |

Origen: `resultados/metricas.json` → `metricas.prueba_balanceada` y `metricas.prevalencia_realista`,
función `src.modelo.evaluar`, commit `d6d9628` del artefacto, commit `8764236` del código.

### Comparación con los valores citados en el encargo

> ⚠ **Los tres valores que el encargo da como «anteriores» no son los de este proyecto.**

| | Encargo | Repositorio (10 nov) | Recalculado (15 nov) | Diferencia |
|---|---|---|---|---|
| F1 macro balanceado | 0,7554 | **0,7543** | **0,7543** | −0,0011 |
| F1 macro prevalencia | 0,5866 | **0,5835** | **0,5835** | −0,0031 |
| PR-AUC macro | 0,8076 | **0,8074** | **0,8074** | −0,0002 |

**La diferencia no es de redondeo ni de versión de librería.** Se buscaron los tres valores en todos
los artefactos del repositorio y **no aparecen en ninguno**: ni en `resultados/metricas.json`, ni en
`metricas_sin_discrepancia.json`, ni en los `.js` exportados, ni en la documentación. Las cifras del
proyecto son 0,7543 / 0,5835 / 0,8074 y hoy se han vuelto a obtener idénticas.

**No sé de dónde salen 0,7554 / 0,5866 / 0,8076.** Las hipótesis que pude descartar: no son la
corrida sin discrepancia (esa da 0,8270 / 0,6566 / 0,8618), no son el modelo sin `class_weight`
(0,5851 en prevalencia), no son la validación (0,7608) ni el bosque de 300 árboles (0,7611). Lo que
no puedo descartar leyendo el repositorio es que procedan de un borrador anterior del informe o de
una corrida que no quedó versionada. **Recomendación: usar 0,7543 / 0,5835 / 0,8074, que son
reproducibles y trazables, y corregir el borrador que lleve los otros.**

### F1 y PR-AUC por clase

| Clase | F1 balanceada | F1 prevalencia | PR-AUC balanceada |
|---|---|---|---|
| `carga_baja` | **0,9477** | 0,8934 | 0,9905 |
| `condensador_sucio` | **0,9248** | 0,8869 | 0,9684 |
| `incondensables` | **0,9157** | 0,8397 | 0,9592 |
| `txv_sobrealimenta` | 0,8844 | 0,2685 | 0,9577 |
| `caudal_agua_bajo` | 0,8688 | 0,8356 | 0,9360 |
| `compresor_desgastado` | 0,8218 | 0,5158 | 0,8879 |
| `incrustacion_evaporador` | 0,7322 | 0,5741 | 0,8310 |
| `sobrecarga` | 0,6533 | 0,2246 | 0,7381 |
| `restriccion_linea_liquido` | 0,5986 | 0,4286 | 0,6901 |
| `txv_restringida` | 0,5165 | 0,1983 | 0,5653 |
| **`sano`** | **0,4333** | 0,7536 | **0,3576** |

Tres lecturas que el informe debe hacer y no esconder:

1. **Hay dos grupos claros.** Las fallas que alteran el lado de alta presión o el inventario de
   refrigerante —condensador sucio, incondensables, carga baja, caudal de agua bajo— se diagnostican
   bien (F1 ≥ 0,87). Las dos que hambrean el evaporador —`txv_restringida` y
   `restriccion_linea_liquido`— se confunden entre sí y con la máquina sana (F1 0,52 y 0,60).
2. **La clase `sano` es la peor de la prueba balanceada** (F1 0,4333, PR-AUC 0,3576). El modelo
   declara avería en máquinas sanas con frecuencia: precisión 0,33 con sensibilidad 0,64. Está
   regulado para no perder fallas, a costa de falsas alarmas. En un plan de mantenimiento eso es
   preferible al error contrario, pero hay que dimensionar la carga de inspecciones en vano.
3. **El salto entre escenarios castiga a las clases raras.** `txv_sobrealimenta` pasa de F1 0,8844
   a 0,2685 sin que el modelo empeore: lo que cambia es que en prevalencia realista esa clase es el
   0,3 % de las muestras, así que cada falso positivo pesa muchísimo en la precisión.

### Detección frente a severidad

Fracción diagnosticada correctamente, por tramo de severidad `f`, en la prueba balanceada:

| Clase | 0,15–0,25 | 0,25–0,35 | 0,35–0,45 | 0,45–0,55 | 0,55–0,65 | 0,65–0,75 | 0,75–0,85 | 0,85–0,95 |
|---|---|---|---|---|---|---|---|---|
| `carga_baja` | 0,75 | 0,82 | 1,00 | 1,00 | 1,00 | 1,00 | 1,00 | 1,00 |
| `condensador_sucio` | 0,55 | 0,90 | 1,00 | 1,00 | 1,00 | 1,00 | 1,00 | 1,00 |
| `incondensables` | 0,45 | 0,90 | 1,00 | 1,00 | 1,00 | 1,00 | 1,00 | 1,00 |
| `caudal_agua_bajo` | 0,44 | 0,62 | 0,91 | 0,90 | 0,95 | 1,00 | 1,00 | 1,00 |
| `txv_sobrealimenta` | 0,35 | 0,74 | 0,84 | 0,94 | 1,00 | 1,00 | 1,00 | 1,00 |
| `compresor_desgastado` | 0,24 | 0,47 | 0,76 | 0,92 | 0,94 | 1,00 | 1,00 | 1,00 |
| `incrustacion_evaporador` | 0,44 | 0,55 | 0,45 | 0,83 | 0,96 | 0,84 | 1,00 | 1,00 |
| `sobrecarga` | 0,12 | 0,41 | 0,47 | 0,92 | 0,80 | 0,85 | 0,85 | 0,90 |
| `txv_restringida` | 0,30 | 0,43 | 0,55 | 0,39 | 0,65 | 0,72 | 0,71 | **0,89** |
| `restriccion_linea_liquido` | **0,03** | 0,03 | **0,00** | 0,32 | 0,89 | 1,00 | 1,00 | 1,00 |

**Esta es la tabla que decide si el método sirve para mantenimiento predictivo**, y la respuesta es
matizada:

- **Seis clases avisan temprano.** `carga_baja`, `condensador_sucio` e `incondensables` superan el
  90 % de acierto ya en severidad moderada baja (0,25–0,35). Para esas fallas el sistema sí da
  antelación útil.
- **`restriccion_linea_liquido` es prácticamente indetectable por debajo de f ≈ 0,45** (0,03, 0,03 y
  0,00 en los tres primeros tramos) y salta a 1,00 desde 0,65. No es un defecto del clasificador:
  por debajo de ese umbral la caída de presión en la línea no basta para que el líquido flashee, y
  sin flasheo la falla deja la misma firma de signos que `txv_restringida`. Está razonado en
  `src/fallas.py:194`–`209`.
- **`txv_restringida` no llega a 0,90 en ningún tramo.** Tiene una explicación física declarada: en
  una enfriadora el agua entra entre 9 y 12 °C y evapora entre 4 y 6 °C, así que el refrigerante no
  puede desarrollar mucho sobrecalentamiento —no puede calentarse por encima de su fuente—, que es
  precisamente lo que la válvula necesita para abrir. Una restricción fuerte saca al equipo del
  régimen estacionario, y un modelo estacionario no puede representarlo (`src/fallas.py:149`–`173`).
  **Consecuencia de ingeniería que el informe debe declarar: esta falla se detecta temprano o no se
  detecta; no hay un régimen degradado estable y prolongado en el que observarla.**

### Robustez: qué pasa si el ruido o la calibración empeoran

| Factor de ruido de instrumentos | F1 macro | Diagnóstico de fallas incipientes |
|---|---|---|
| ×0,5 | 0,8172 | 0,6235 |
| **×1,0 (caso base)** | **0,7572** | **0,4824** |
| ×2,0 | 0,6460 | 0,3647 |

| Discrepancia modelo–planta | F1 macro | Diagnóstico de fallas incipientes |
|---|---|---|
| 0 % | 0,8198 | 0,6412 |
| 3 % | 0,7700 | 0,5294 |
| **5 % (caso base)** | **0,7572** | **0,4824** |
| 8 % | 0,7491 | 0,5118 |
| 15 % | 0,6638 | 0,3941 |

Cinco repeticiones con un error de calibración distinto por corrida: **F1 macro 0,7950 ± 0,0076**
(mínimo 0,7867, máximo 0,8024). Es decir: la variabilidad entre instalaciones es pequeña comparada
con el efecto del nivel de calibración.

(`resultados/metricas.json` → `sensibilidad_al_ruido`, `sensibilidad_a_la_discrepancia`,
`repeticiones_por_corrida`; funciones `src.modelo.estudio_ruido`, `estudio_discrepancia`,
`repeticiones_por_corrida`, commit `d6d9628`.)

### Alarma de fuga de datos: NO disparada

El encargo pide tratar como alarma cualquier métrica demasiado buena. Se comprobó explícitamente
(`src/figuras_informe.py`, bloque `alarma_de_fuga`, y queda registrado en
`export_informe/metricas.json`):

| Comprobación | Umbral | Valor | ¿Alarma? |
|---|---|---|---|
| Exactitud, prueba balanceada | > 0,95 | 0,7376 | no |
| Exactitud, prevalencia realista | > 0,95 | 0,6827 | no |
| F1 macro, prueba balanceada | > 0,95 | 0,7543 | no |
| F1 macro, prevalencia realista | > 0,95 | 0,5835 | no |

Ninguna métrica se acerca al umbral. Además, las tres defensas estructurales contra la fuga están
activas y verificadas en esta corrida:

1. **Lista blanca de columnas** (`src/features.py:197`): la matriz de entrada solo admite columnas
   `res_*`; la etiqueta, la severidad y el identificador de condición no pueden entrar por descuido.
2. **Partición por grupos** (`src/modelo.py:144`): condiciones compartidas entre particiones = **0**,
   verificado con un `assert` que aborta la corrida.
3. **Conjunto de prueba sellado** (`src/modelo.py:85`): **1 apertura** por conjunto, motivo
   registrado, `corrida_valida = true`.

**Contexto histórico que conviene recordar en la defensa.** Una versión anterior de este módulo,
anterior a introducir la discrepancia modelo–planta, daba F1 macro **0,9956**. Eso no se celebró: se
trató como la señal de que el problema estaba mal planteado. Sin error de calibración, el residuo de
una máquina sana es ruido puro y las clases se separan trivialmente. El 0,7543 de hoy es peor y es
mejor: mide algo.

---

## Figuras

Seis archivos PNG a **300 dpi** en `export_informe/figuras/`, generados por
`python -m src.figuras_informe` (commit `8764236`) a partir de
`resultados/modelo_rf.joblib` y los `.parquet` de `data/`. Todas se recalcularon el 15 de noviembre
de 2026 con la semilla 20260902 y se contrastaron contra `resultados/metricas.json` con tolerancia
1e-12 antes de dibujarse.

### Figura 1 — `fig1_matriz_confusion_balanceada.png`

> **Figura 1.** Matriz de confusión del clasificador sobre el conjunto de prueba balanceado
> (n = 1 997), normalizada por fila. Las filas son la falla realmente presente y las columnas el
> diagnóstico emitido; la diagonal son los aciertos. Se lee de izquierda a derecha en cada fila para
> ver **con qué se confunde** cada falla. Tres filas concentran el problema: `sano` tiene 0,64 en la
> diagonal y deriva 0,16 a `txv_restringida`; `txv_restringida` tiene 0,56 y deriva **0,36 a
> `sano`**; y `restriccion_linea_liquido` tiene 0,46 y reparte 0,23 a `txv_restringida` y 0,21 a
> `sano`. Es decir: las dos fallas que hambrean el evaporador se confunden entre sí **y con la
> máquina sana**, en los tres sentidos.
>
> *Origen:* `resultados/metricas.json` → `metricas.prueba_balanceada.matriz_confusion_normalizada`;
> función `src.modelo.evaluar`; dibujada por `src.figuras_informe.fig_matriz`; commit `8764236`.

### Figura 2 — `fig2_matriz_confusion_prevalencia.png`

> **Figura 2.** Matriz de confusión sobre el conjunto de prevalencia realista (n = 9 964), donde el
> 67,67 % de las muestras son máquina sana, normalizada por fila. Comparada con la Figura 1, la
> diagonal se mantiene —el modelo no empeora— pero la interpretación cambia: con una clase
> dominante, los pocos falsos positivos de las clases raras destruyen su precisión. Es la figura que
> hay que mirar para estimar la carga de órdenes de trabajo en vano.
>
> *Origen:* `resultados/metricas.json` → `metricas.prevalencia_realista.matriz_confusion_normalizada`;
> modelo con `class_weight='balanced'` (`src/modelo.py:674`–`679`); función `src.modelo.evaluar`;
> dibujada por `src.figuras_informe.fig_matriz`; commit `8764236`.

### Figura 3a — `fig3a_curvas_pr_balanceada.png`

> **Figura 3a.** Curvas precisión–sensibilidad por clase sobre el conjunto de prueba balanceado.
> Cada curva recorre todos los umbrales de decisión posibles, no solo el que el modelo usa; el valor
> AP de la leyenda es el área bajo cada curva. **PR-AUC macro = 0,8074.** Se usa curva PR y no ROC
> porque con clases desbalanceadas la ROC es engañosamente optimista: los verdaderos negativos la
> inflan. Se aprecian los dos grupos: `carga_baja` (0,991), `condensador_sucio` (0,968) e
> `incondensables` (0,959) arriba; `txv_restringida` (0,565) y `sano` (0,358) abajo.
>
> *Origen:* probabilidades del modelo sobre el conjunto sellado; `sklearn.metrics.precision_recall_curve`;
> AP por clase en `resultados/metricas.json` → `metricas.prueba_balanceada.pr_auc_por_clase`;
> dibujada por `src.figuras_informe.fig_pr`; commit `8764236`.

### Figura 3b — `fig3b_curvas_pr_prevalencia.png`

> **Figura 3b.** Las mismas curvas sobre el conjunto de prevalencia realista.
> **PR-AUC macro = 0,7205.** La caída respecto de la Figura 3a no se debe a que el modelo empeore,
> sino a que la línea base de cada clase es su propia prevalencia: una clase que aparece el 0,3 % de
> las veces parte de una precisión base de 0,003.
>
> *Origen:* igual que la Figura 3a, sobre `data/dataset_prevalencia.parquet` y el modelo con
> `class_weight='balanced'`; commit `8764236`.

### Figura 4 — `fig4_f1_por_clase.png`

> **Figura 4.** F1 por clase en los dos escenarios, ordenado de menor a mayor según la prueba
> balanceada. Las líneas discontinuas marcan el F1 macro de cada escenario (0,7543 y 0,5835). La
> figura resume el resultado del módulo en una imagen: cuatro fallas por encima de 0,87, dos por
> debajo de 0,60, y la clase `sano` como la peor de la prueba balanceada. El contraste entre barras
> de la misma clase mide cuánto castiga la prevalencia realista a las clases raras: `txv_sobrealimenta`
> cae de 0,8844 a 0,2685.
>
> *Origen:* `resultados/metricas.json` → `metricas.*.f1_por_clase`; función `src.modelo.evaluar`;
> dibujada por `src.figuras_informe.fig_f1_por_clase`; commit `8764236`. **Esta figura no existía en
> el pipeline; se añadió para este informe.**

### Figura 5 — `fig5_deteccion_por_severidad.png`

> **Figura 5.** Fracción diagnosticada correctamente frente a la severidad de la falla `f`, por
> clase, sobre el conjunto de prueba balanceado. Solo clases con falla: la clase sana no tiene
> severidad. Es la figura que decide si el método sirve para mantenimiento **predictivo**: una curva
> que solo sube al final significa que la falla se detecta cuando ya es grave.
> `restriccion_linea_liquido` es el caso extremo —0,03 / 0,03 / 0,00 en los tres primeros tramos y
> 1,00 desde 0,65—, con explicación física declarada: por debajo de ese umbral la caída de presión
> no basta para que el líquido flashee. `carga_baja`, `condensador_sucio` e `incondensables`, en
> cambio, superan el 90 % ya en severidad 0,25–0,35.
>
> *Origen:* aciertos del conjunto sellado cruzados con `severidad_f`; equivale a
> `resultados/metricas.json` → `deteccion_vs_severidad` (función
> `src.modelo.fig_deteccion_vs_severidad`); recalculada y dibujada por
> `src.figuras_informe.fig_deteccion`; commit `8764236`.

### Inventario

| Archivo | Píxeles | Tamaño | dpi |
|---|---|---|---|
| `fig1_matriz_confusion_balanceada.png` | 2666×2455 | 480 kB | 300 |
| `fig2_matriz_confusion_prevalencia.png` | 2666×2455 | 488 kB | 300 |
| `fig3a_curvas_pr_balanceada.png` | 2100×1682 | 353 kB | 300 |
| `fig3b_curvas_pr_prevalencia.png` | 2100×1682 | 367 kB | 300 |
| `fig4_f1_por_clase.png` | 2679×1765 | 204 kB | 300 |
| `fig5_deteccion_por_severidad.png` | 2625×1820 | 409 kB | 300 |

> **Figuras que NO se incluyen y existen en el proyecto**, por si el informe las necesita:
> diagrama P-h del ciclo, importancia por permutación, mapa de firmas y los dos barridos de
> sensibilidad, todas en `proyecto-fdd/figuras/` a 300 dpi
> (`resultados/metricas.json` → `figuras`).

---

## (h) Auditoría: hallazgos, correcciones y defectos abiertos

El 10 de noviembre de 2026 se hizo una **auditoría de solo lectura** del módulo
(`AUDITORIA_FDD_10NOV.md`, commit `9690b71`). Encontró tres defectos en el visualizador y uno en el
solver, y planteó un plan de corrección en su sección 7. Las correcciones se implementaron el mismo
día y están registradas en `CAMBIOS_FDD_10NOV.md`.

### §7.3 — Los puntos sin estado estacionario se clasificaban como «sano»  ✅ CORREGIDO

**El hallazgo.** En JavaScript, `Math.fround(null)` vale `0`. Los 189 nodos de la malla de operación
sin solución física llevan todos sus residuos en `null`, así que entraban al bosque como un vector
de once ceros —es decir, **como una máquina perfectamente sana**— y el clasificador respondía
`sano` con confianza 0,348. Verificado contra el código anterior antes de corregirlo. Dieciocho de
esos 189 nodos están a carga plena, así que no era un problema de una banda de carga.

**La corrección** (commit `b59b089`): `probabilidades()` falla ruidosamente ante cualquier
característica no finita (`web/js/fdd_inferencia.js:53`–`67`) y `diagnosticar()` comprueba
`estado.convergio` antes de clasificar (`:323`). Prueba que recorre **los 189 nodos reales** y exige
que ninguno reciba clase.

### §7.1 — `buscarCelda` saturaba sin aviso de extrapolación  ✅ CORREGIDO

> ⚠ **Corrección a la premisa del encargo.** El encargo lista este punto como defecto conocido
> **abierto**. No lo está: se corrigió el 10 de noviembre.

**El hallazgo.** Cualquier consulta fuera del dominio de la malla se colapsaba sobre el nodo del
borde y devolvía **exactamente la misma estructura** que un punto interior, sin bandera ni
centinela. `FDD.consultar(50, 2.0, 'sano', 0)` —50 °C de ambiente y carga del 200 %— devolvía un
estado completo con `T4_C = 4,5046` y ninguna marca. La búsqueda de la cadena `extrapol` en todo
`web/` devolvía cero resultados.

**La corrección** (commit `2619317`): `buscarCelda` devuelve ahora `{i, t, fuera, distancia,
rechazado}` (`web/js/fdd_inferencia.js:110`–`130`); todo estado lleva `_extrapolado` y
`_fuera_de_malla: {ejes, distancia_max}`, presentes también dentro del dominio; y **más allá de un
paso de nodo `consultar()` devuelve `null`** (`:215`). El margen lo calcula el exportador y viaja
como dato en `FDD_MALLA.margen_extrapolacion` —`[22, 38] °C` y carga `[0,25, 1,05]`—, no está
escrito en el JavaScript. 16 pruebas, incluido el caso exacto de la auditoría.

### §7.2 — `diagnosticar()` usaba residuos deterministas  ✅ CORREGIDO

> ⚠ **Corrección a la premisa del encargo.** También figura como abierto y tampoco lo está.

**El hallazgo.** La malla se generaba **sin ruido de sensor y sin discrepancia modelo–planta**,
mientras el clasificador se entrenó con ambos. El desacuerdo estaba declarado como dato en
`FDD_FISICA.nota_ruido`, pero `diagnosticar()` seguía clasificando los residuos limpios: el
visualizador acertaba más de lo que dice el informe, y nadie lo veía.

**La corrección** (commit `a8e842c`): la malla trae ahora **dos** bloques de residuos. `res_*`
limpios, para el diagrama P-h; y `res_ruidoso_*`, calculados en Python replicando
`src.generador._fila` paso por paso —ruido sumado a las mediciones, referencia sana con
`θ_modelo = θ_planta·(1+ε)`— que son los que `diagnosticar()` clasifica
(`src/exportador_web.py:384`–`466`, `web/js/fdd_inferencia.js:342`–`371`). Semilla propia y
exportada, `SEMILLA_MALLA = 20261110`. El bloque ruidoso **nunca se interpola**: el ruido de dos
nodos vecinos es independiente y una bilineal de cuatro nodos reduciría la desviación típica a la
mitad.

**Magnitud del sesgo que se eliminó**, medida sobre los 4 431 nodos utilizables:

| Qué se clasifica | Acierto |
|---|---|
| Residuos limpios | 0,7364 |
| Residuos con ruido | 0,6752 |

**6,1 puntos de optimismo** que el visualizador ya no muestra.

### Dominio de entrenamiento  ✅ AÑADIDO (commit `be7fc76`)

Hallazgo posterior: la malla llega hasta carga 0,28 y **el dataset nunca bajó de 0,40**. Son **1 540
de los 4 620 nodos (33,3 %)** sobre los que el clasificador no vio ni un punto. `consultar()` los
marca con `_fuera_de_entrenamiento` y **`diagnosticar()` no los clasifica**: devuelve el estado del
ciclo, `diagnostico: null` y el motivo. Los rangos se leen de `config.params.RangosContorno` y
viajan en `FDD_MALLA.dominio_entrenamiento`.

Acierto recalculado restringiendo al dominio:

| Nodos | n | Con ruido | Limpios |
|---|---|---|---|
| Todos los utilizables | 4 431 | 0,6752 | 0,7364 |
| **Dentro del dominio de entrenamiento** | **3 010** | **0,7156** | 0,7920 |
| Fuera del dominio | 1 421 | 0,5897 | 0,6186 |

### No convergencia en carga baja  ❌ ABIERTO

Es el único de los tres defectos que el encargo lista que **sigue abierto**, y en realidad son dos
problemas distintos en la misma zona:

**(1) Puntos sin estado estacionario.** El solver no encuentra solución por debajo de cierta carga.
En el **dataset** esto se traduce en descartes, contabilizados y reportados: 123 de 13 200 intentos
en el balanceado (0,93 %, de los cuales 117 son `carga_baja`) y 36 de 10 000 en el de prevalencia
(0,36 %, todos `carga_baja`). **Cero condiciones descartadas por completo.** En la **malla** son 189
nodos de 4 620 (4,09 %). No contaminan las métricas: el dataset no tiene ninguna fila por debajo de
carga 0,40 (sección d).

**(2) La bandera `ciclado` no es fiable.** Más grave y peor documentado hasta la auditoría. En
`src/ciclo.py:571`–`581` la bandera se fija **antes** de reintentar a capacidad mínima, y si el
reintento no mejora el residuo se conserva la solución no acotada con la bandera ya puesta. Medido
sobre la malla: 623 nodos marcados como `ciclado`, de los cuales **519 son estados que la máquina no
puede tener** (`y_capacidad < y_min = 0,25` sosteniendo el setpoint). Reparto: 262 en carga 0,28,
228 en 0,31, **29 en 0,34**. Consecuencia: `fraccion_marcha` vale 1,000 en toda esa zona en lugar de
la proporción real de tiempo encendido, así que **el arranque matutino no se puede reconstruir con
la malla**.

**Mitigación actual, no corrección:** los 519 nodos quedan **todos** cubiertos por la marca de
dominio de entrenamiento —de hecho los 623 en ciclado lo están—, así que el visualizador no los
diagnostica. Pero el defecto sigue en el solver, y el solver es `src/ciclo.py`, que esta fase no
tocó. **Para el informe: declarar la zona de carga baja como no utilizable.**

### Dos defectos menores detectados y no corregidos

| Hallazgo | Estado |
|---|---|
| `V_agua_ev` se llama como caudal volumétrico y contiene **caudal másico en kg/s** (`src/ciclo.py:610`, consumido en `src/features.py:123`). Uso internamente consistente, **sin error numérico**, pero el nombre induce a anotar m³/h en campo. | Anotado, no corregido |
| La malla guarda **cinco sorteos de ruido** para la clase `sano`, uno por ranura de severidad, y `consultar()` solo alcanza el primero porque `sano` ignora la severidad por construcción. 336 nodos con valores inalcanzables. Sin efecto sobre lo que se muestra. | Anotado, no corregido (`CAMBIOS_FDD_10NOV.md` §A.5) |

---

## (i) Pruebas

### Suite completa

```bash
python -m pytest tests/ -q
```

**Resultado del 15 de noviembre de 2026: 213 pruebas, 213 pasan, 0 fallan** (145 s).

> ⚠ **Corrección a la premisa del encargo.** El encargo cita «213 pruebas, 208 pasan y 5 fallan por
> el `.joblib`». Ese era el estado del 10 de noviembre y **ya no lo es**. Las 5 que fallaban
> necesitaban `resultados/modelo_rf.joblib`, excluido del repositorio por tamaño (70 MB, frente al
> límite de 100 MB de GitHub tras compresión; sin comprimir eran 244 MB). Al reentrenar hoy para la
> sección (g), el artefacto existe y **las cinco pruebas corren y pasan**.

Esto importa para el informe: significa que **la equivalencia Python–JavaScript está verificada en
esta sesión**, no solo declarada en una corrida pasada.

| Archivo | Qué verifica |
|---|---|
| `tests/test_ciclo.py` | solver, unidades, dominio físico (23 funciones) |
| `tests/test_firmas.py` | batería de firmas físicas: cada falla mueve cada variable en la dirección correcta, en todo el dominio y sin ruido (17) |
| `tests/test_features.py` | lista blanca y construcción de residuos (9) |
| `tests/test_particion.py` | partición por grupos, intervalos de Wilson (17) |
| `tests/test_inferencia_js.py` | contrato del visualizador; **no necesita el `.joblib`** (52) |
| `tests/test_exportador.py` | equivalencia exacta JS ↔ scikit-learn; **necesita el `.joblib`** (7) |

### Equivalencia Python ↔ JavaScript

El visualizador reimplementa la inferencia del bosque en JavaScript plano. La prueba ejecuta
**node** contra los archivos realmente exportados y compara con scikit-learn sobre **las 1 997
muestras completas** del conjunto de prueba, con `n_jobs=1` para que el orden de acumulación sea
determinista:

| Comprobación | Resultado (15 nov 2026) |
|---|---|
| Clase predicha idéntica, **sin tolerancia** | **1 997 / 1 997** |
| Probabilidades idénticas **bit a bit** | **100,00 %** |
| Diferencia máxima de probabilidad | **0,000e+00** |
| Pares (muestra, umbral) a menos de 1e-9 | **0** |

Tres detalles del código fuente de scikit-learn gobiernan la implementación y se leyeron antes de
escribirla: el casteo de `X` a **float32** antes de recorrer los árboles (de ahí `Math.fround` en
JavaScript), el hecho de que `tree_.value` se devuelve **sin normalizar**, y que
`predict_proba` acumula con **suma lineal** árbol por árbol, no por pares.

**Regla de conducta que se siguió:** si la prueba divergía, se reportaba el número exacto de casos y
el diagnóstico; no se ajustaba la tolerancia hasta que pasara.

---

## (j) Limitaciones

Sin suavizar.

1. **Los datos son simulados, no medidos.** No hay ni una sola observación de un equipo real en el
   entrenamiento ni en la prueba. Lo que se demuestra es que el método funciona sobre un gemelo
   digital cuyas firmas se verificaron físicamente; **no** que funcione sobre la máquina del local.
   La validación con datos de campo está pendiente.

2. **El equipo modelado no es el del local.** Una enfriadora de agua de 100 TR con R-134a y
   condensador de aire, frente a un congelador de expansión directa con R-404A a −40/0 °F y
   desescarche eléctrico. Adaptarlo cuesta 59–118 h y requiere física que el módulo no tiene
   (sección c). **Ninguna cifra de este documento es un diagnóstico del equipo del KFC.**

3. **Los 29 parámetros del equipo siguen marcados como provisionales**, incluidos los dos `UA`
   calibrados, cuyo origen declarado es «punto de diseño de catálogo, sustituir por la hoja
   `Registro Campo` de la Fase 1» (`resultados/metricas.json` → `calibracion_ua.origen_datos`).
   Las métricas se moverán cuando lleguen los datos reales.

4. **Dos fallas no se diagnostican de forma utilizable.** `txv_restringida` (F1 0,52) y
   `restriccion_linea_liquido` (F1 0,60) se confunden entre sí y con la máquina sana. La segunda es
   indetectable por debajo de severidad 0,45. Ambas tienen explicación física declarada, pero el
   efecto práctico es el mismo: para esas dos averías el sistema no sustituye a la inspección.

5. **El sistema declara avería en máquinas sanas con frecuencia.** En la prueba balanceada, la
   clase `sano` tiene precisión 0,33 y sensibilidad 0,64: de cada tres veces que dice «sano», dos
   son equivocadas, y a la vez se le escapa un 36 % de las máquinas que sí estaban sanas,
   etiquetándolas como averiadas —sobre todo como `txv_restringida`, que recibe el 0,16 de esa
   fila—. En escenario realista la precisión de las clases raras cae a 0,12–0,17: **de cada siete u
   ocho avisos, uno es real.** Hay que dimensionar el coste de las inspecciones en vano antes de
   conectar esto a un flujo de órdenes de trabajo.

6. **La zona de carga baja no es utilizable.** Por debajo de carga 0,40 el clasificador no fue
   entrenado, y por debajo de 0,34 el modelo físico tiene además un defecto abierto en la bandera de
   ciclado (sección h). El arranque matutino **no** se puede reconstruir hoy.

7. **El modelo es estacionario.** No representa transitorios: ni arranques, ni ciclado, ni
   desescarches. Cualquier falla cuyo síntoma sea dinámico queda fuera por construcción.

8. **El intercambio es sensible puro.** No se modela deshumidificación ni escarcha
   (`src/ciclo.py:43`–`45`). Es exacto en el evaporador de agua de la enfriadora y sería un error
   grave en un evaporador de aire bajo cero.

9. **Dos supuestos de instalación sin verificar**: caudal primario constante en el circuito de agua
   helada, y que la carga del edificio fija la temperatura de retorno. Si la instalación resultara
   de caudal primario variable, la clase `caudal_agua_bajo` dejaría de ser válida tal como está
   planteada (`src/ciclo.py:46`–`54`).

10. **El `UA` se calibró con un único punto de diseño**, no con una curva. El RMSE relativo de
    1,67e-13 que reporta la calibración **no es una medida de bondad del modelo**: es el residuo
    numérico de ajustar dos parámetros a dos ecuaciones. No debe citarse como validación.

11. **El modelo serializado no está en el repositorio** (70 MB). Reproducir la sección (g) o las
    5 pruebas de equivalencia exige reentrenar primero, lo que lleva unos 20 minutos.

---

## (k) Reproducibilidad

### Entorno verificado el 15 de noviembre de 2026

Versiones **fijadas** en `requirements.txt` y comprobadas en la corrida:

| Paquete | Versión |
|---|---|
| Python | 3.11.18 |
| numpy | 2.4.6 |
| scipy | 1.17.1 |
| pandas | 3.0.5 |
| scikit-learn | 1.9.0 |
| matplotlib | 3.11.1 |
| seaborn | 0.13.2 |
| joblib | 1.6.0 |
| CoolProp | 8.0.0 |
| pyarrow | 25.0.1 |
| pytest | 9.1.1 |
| python-docx | 1.2.0 |

El encabezado de `requirements.txt` lo justifica: «la reproducibilidad exige que la semilla y el
entorno estén controlados a la vez».

### Semillas

| Semilla | Valor | Dónde |
|---|---|---|
| Maestra | **20260902** | `config/params.py:35` |
| Partición, estimadores, ruido, severidad, discrepancia | derivadas por `SeedSequence` | `src/generador.py:97`, `semillas_derivadas` |
| Repeticiones por corrida | 20261902 … 20265902 | `src.modelo.repeticiones_por_corrida` |
| Ruido de la malla del visualizador | **20261110** | `src/exportador_web.py:78` |

Nota técnica: no se usa `np.random.default_rng(seed_sequence)` directamente, porque en NumPy ≥ 2 esa
llamada deriva un hijo nuevo en cada invocación y dos llamadas con el mismo objeto dan secuencias
distintas. Se reconstruye el `SeedSequence` desde su entropía y su `spawn_key`
(`src/generador.py:79`, `rng_desde`).

### Comandos, en orden

```bash
cd proyecto-fdd
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

python -m pytest tests/ -q          # 0. verificación física — va PRIMERO (~2,5 min)
python -m src.calibracion           # 1. calibración de los UA
python -m src.generador             # 2. datasets del caso base, discrepancia 5 %
python -m src.modelo --sin-informe  # 3. entrenamiento, evaluación y figuras (~20 min)
python -m src.figuras_informe       # 4. figuras del informe + export_informe/metricas.json
python -m src.exportador_web        # 5. (opcional) visualizador web
```

Las pruebas van primero a propósito: un simulador con firmas invertidas produciría un clasificador
con métricas excelentes sobre física equivocada, y nada en la matriz de confusión lo delataría.

### Qué se reprodujo exactamente y qué no

**Reproducido al bit.** Se reejecutó `python -m src.modelo --sin-informe` el 15 de noviembre, en un
contenedor construido de cero, y se comparó el `resultados/metricas.json` resultante contra el que
quedó commiteado el 10 de noviembre: **0 claves distintas y 0 valores distintos**, sobre el árbol
completo del JSON. Incluye las métricas principales, las matrices de confusión, los intervalos de
Wilson, los barridos de ruido y de discrepancia y las cinco repeticiones.

**No reproducido al bit: los PNG.** Las figuras regeneradas difieren de las commiteadas a nivel de
píxel, y en algunos casos por unos pocos píxeles de tamaño total (2 671×2 458 → 2 666×2 455). **El
contenido numérico es idéntico**; la diferencia está en el renderizado —métricas de fuente y
`bbox_inches="tight"`—, no en el cálculo. Es una limitación conocida de matplotlib, no un fallo de
reproducibilidad del método, pero conviene saberlo antes de comparar imágenes byte a byte.

**Hueco de reproducibilidad detectado.** `resultados/metricas.json` **no registra las versiones de
las librerías** con las que se produjo. Están fijadas en `requirements.txt`, así que en la práctica
coinciden, pero la corrida no lo deja escrito. El `export_informe/metricas.json` que acompaña a este
documento **sí lo hace**, en la clave `entorno`. Recomendación: añadir ese bloque también a la
salida de `src/modelo.py`.

### Procedencia de los tres entregables

| Archivo | Cómo se produce |
|---|---|
| `export_informe/FDD_informe.md` | escrito a mano; cada cifra con su origen |
| `export_informe/figuras/*.png` | `python -m src.figuras_informe`, 300 dpi |
| `export_informe/metricas.json` | `python -m src.figuras_informe`, cada valor con `archivo`, `clave`, `función` y `commit` |

`src/figuras_informe.py` no entrena ni decide nada: lee el modelo serializado, rehace la misma
partición con la misma semilla, vuelve a evaluar y **contrasta cada número contra
`resultados/metricas.json` con tolerancia 1e-12**. Si alguno difiriera, aborta en lugar de publicar
una figura que no cuadre con el informe.

---

## Anexo — resumen de las correcciones a las premisas del encargo

| # | El encargo dice | Lo que hay en el repositorio |
|---|---|---|
| 1 | Valores anteriores 0,7554 / 0,5866 / 0,8076 | **0,7543 / 0,5835 / 0,8074**; los tres citados no aparecen en ningún artefacto |
| 2 | Hipercubo latino de **120** puntos de operación | **400** condiciones en el conjunto de entrenamiento; 120 es el tamaño de los **estudios de sensibilidad** |
| 3 | Prevalencia realista **70 %** sano | objetivo **68 %**, obtenido **67,67 %** |
| 4 | `buscarCelda` satura sin aviso — defecto conocido | **corregido** el 10 nov, commit `2619317` |
| 5 | `diagnosticar()` usa residuos deterministas — defecto conocido | **corregido** el 10 nov, commit `a8e842c` |
| 6 | No convergencia en carga baja — defecto conocido | **abierto**, confirmado; y hay un segundo defecto peor en la misma zona: la bandera `ciclado` |
| 7 | 213 pruebas, 208 pasan, 5 fallan | **213 pasan, 0 fallan** hoy: al reentrenar aparece el `.joblib` que faltaba |
| 8 | Sitio: KFC San Francisco | el nombre **no aparece en ningún archivo** del módulo; procede del encargo |

---

## Referencias

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
- Wilson, E. B. (1927). Probable inference, the law of succession, and statistical inference.
  *Journal of the American Statistical Association, 22*(158), 209–212.
