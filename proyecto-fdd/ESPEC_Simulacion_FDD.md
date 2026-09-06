# Especificación técnica — Simulación de detección y diagnóstico de fallas (FDD)

**Versión 2** — enfriadora de agua (chiller)
**Proyecto:** Plan Integral de Mantenimiento — Sistema de Refrigeración y Aire Acondicionado
**Curso:** Mantenimiento de Sistemas de Refrigeración y A/A (0251) — UTP, Facultad de Ingeniería Mecánica
**Fase:** Fase 5 — Monitoreo e Innovación
**Estado:** parámetros del equipo pendientes de la placa; tipo de condensador pendiente del levantamiento

> Esta especificación está bajo control de versiones junto al código que la implementa. La
> sección 13 registra los cambios respecto de la versión 1 y por qué se hicieron.

---

## 0. Qué se construye y qué NO se construye

**Se construye:** un generador de datos sintéticos a partir de un modelo termodinámico del ciclo
de compresión de vapor, y un clasificador que identifica el modo de falla presente a partir de las
variables que el equipo mide en campo.

**NO se construye:** un sistema entrenado con datos reales de la instalación. Lo que se demuestra
es que **el método funciona y es implementable**, no que ya esté implementado.

---

## 1. Sistema de estudio

Enfriadora de agua de 100 TR que da servicio a un edificio de oficinas, con distribución hidrónica
hacia manejadoras y fan-coils. El evaporador intercambia contra **agua helada**; el condensador
queda **configurable** entre enfriado por aire y enfriado por agua con torre, porque el dato se
resuelve en el levantamiento de campo.

El modelo de **expansión directa aire-aire se conserva** como topología seleccionable: si el acceso
a la enfriadora se complica, el proyecto cambia de equipo de estudio con una línea de configuración.

| `TIPO_SISTEMA` | Evaporador | Condensador | Clases | Residuos |
|---|---|---|---|---|
| `chiller_cond_aire` | agua | aire | 11 | 11 |
| `chiller_cond_agua` | agua | agua + torre | 11 | 12 |
| `expansion_directa` | aire | aire | 10 | 11 |

---

## 2. Arquitectura en tres capas

```
Capa 1 — MODELO FÍSICO (gemelo digital de caja gris)      src/ciclo.py
   Entradas: T ambiente, HR, fracción de carga del edificio
   Salidas:  estado esperado del ciclo en condición SANA
                    |
Capa 2 — INYECCIÓN DE FALLAS                              src/fallas.py
   Se degradan parámetros físicos (UA, eficiencias, coeficiente de la válvula…)
                    |
Capa 3 — CLASIFICADOR                                     src/modelo.py
   Entrada:  RESIDUOS = (medición degradada) − (predicción sana a igual contorno)
   Salida:   modo de falla + severidad estimada
```

**El clasificador NO opera sobre valores crudos, sino sobre residuos.** Un día a 36 °C produce
presiones de descarga altas sin que exista falla alguna; entrenado con valores crudos, el modelo
aprendería a confundir clima con avería.

### 2.1 Discrepancia entre modelo y planta

Los datos se generan con `theta_planta`; la predicción sana que se resta se calcula con
`theta_modelo = theta_planta·(1 + ε)`, con ε acotado por el nivel de discrepancia. Representa el
error de calibración del gemelo digital, que en una instalación real es la fuente de error
**dominante**, por encima del ruido de los instrumentos.

Sin esa discrepancia, el residuo de la condición sana es puro ruido de sensor y la separación entre
clases resulta trivial por construcción: métricas de 0,99 que no significan nada.

---

## 3. Variables del sistema

### 3.1 Condiciones de contorno

| Símbolo | Variable | Unidad | Rango |
|---|---|---|---|
| `T_amb` | Bulbo seco exterior | °C | 24 a 36 (clima de Panamá) |
| `HR_amb` | Humedad relativa exterior | % | 60 a 95 |
| `Q_load_frac` | Fracción de carga térmica del edificio | – | 0,40 a 1,00 |

Con condensador de agua, `HR_amb` **interviene físicamente**: la torre trabaja contra el bulbo
húmedo, `T_agua_in_cd = T_bulbo_húmedo + approach_torre`. Con condensador de aire se registra pero
no entra al ciclo.

La carga del edificio fija la temperatura de retorno del agua helada:
`T_retorno = T_suministro_sp + Q_load / (ṁ_agua · cp)`, bajo el supuesto de **caudal primario
constante** (ver sección 12).

### 3.2 Variables medidas

Comunes a las tres topologías: `P_suc`, `P_des`, `T_ev_out`, `T_suc`, `T_des`, `T_liq`, `I_avg`,
`W_elec`.

| Lado | `chiller_cond_aire` | `chiller_cond_agua` | `expansion_directa` |
|---|---|---|---|
| Evaporador | `T_agua_in_ev`, `T_agua_out_ev`, `V_agua_ev` | ídem | `T_air_in_ev`, `T_air_out_ev`, `V_air_ev` |
| Condensador | `T_air_in_cd`, `T_air_out_cd` | `T_agua_in_cd`, `T_agua_out_cd`, `V_agua_cd` | `T_air_in_cd`, `T_air_out_cd` |

**Restricción de diseño:** el clasificador no puede depender de nada que el equipo no mida en campo.

### 3.3 Variables derivadas (características)

Comunes: `SH_evap`, `SH_total`, `SC`, `SH_des`, `rp`, `COP_sist`, `kW_TR`, `split_cond`.

| Característica | Definición | Topología |
|---|---|---|
| `approach_ev` | `T_agua_out_ev − T_rocío(P_suc)` | enfriadora |
| `dT_agua_ev` | `T_agua_in_ev − T_agua_out_ev` | enfriadora |
| `approach_cd` | `T_burbuja(P_des) − T_agua_out_cd` | condensador de agua |
| `approach_evap` | `T_air_in_ev − T_rocío(P_suc)` | expansión directa |

`approach_ev` es de las variables más informativas en diagnóstico de enfriadoras y no existe en un
equipo de expansión directa.

Todas las temperaturas de saturación con **CoolProp**, rocío para sobrecalentamiento y burbuja para
subenfriamiento.

---

## 4. Modelo físico

### 4.1 Intercambiadores (efectividad-NTU)

```
NTU = UA / (ṁ_secundario · cp)         eps = 1 − exp(−NTU)
Q_L = ṁ_w·cp_w·eps_ev·(T_agua_in_ev − T_evap)
Q_H = ṁ_sec·cp·eps_cd·(T_cond − T_entrada_cd)
```

Con refrigerante cambiando de fase a temperatura constante, `eps = 1 − exp(−NTU)` es exacta tanto
para agua como para aire. `UA` escala con el caudal según `UA ∝ ṁ^0.8`.

**Acoplamiento adicional:** el UA efectivo del evaporador se penaliza con el sobrecalentamiento,
`UA_ef = UA·(1 − β·min(SH/SH_ref, 1))`, porque la zona ya evaporada tiene un coeficiente de
transferencia muy inferior. Sin este acoplamiento el sobrecalentamiento no tendría **ninguna**
consecuencia sobre la evaporación y las fallas de válvula no moverían ni la presión de succión ni
el COP.

### 4.2 Válvula de expansión como elemento de flujo

```
ṁ_válvula = K_v · a(SH) · sqrt(ρ_líq · ΔP_válvula)
a(SH)     = clip(a_nom + K_ctrl·(SH − SH_objetivo), a_min, 1)
ΔP_válvula = P_cond − ΔP_línea − P_suc
```

**El sobrecalentamiento es RESULTADO, no entrada.** Una válvula restringida hambrea el evaporador:
cae el flujo, cae la presión de succión, cae la capacidad, y el sobrecalentamiento sube como
consecuencia.

### 4.3 Compresor y control de capacidad

```
eta_v  = eta_v0 − k_v·(rp − 1)
eta_s  = eta_s0·(1 − k_carga_parcial·(1 − y))
ṁ_r    = y · V_disp · N · eta_v / v_suc
```

La enfriadora **modula capacidad** (`y ∈ [y_min, 1]`) para sostener la temperatura de salida del
agua en el setpoint. Bajo control, la carga queda prescrita y la ecuación del evaporador se vuelve
explícita para `T_evap`, así que `y` ocupa su lugar como incógnita: el sistema sigue siendo de tres
ecuaciones.

**Regímenes de capacidad:** `controlado`, `saturado` (y = 1 y no alcanza el setpoint) y `ciclado`
(la carga cae por debajo de la capacidad mínima). Los dos últimos quedan registrados como banderas
en el dataset: que el equipo no alcance el setpoint es información valiosa, no un error.

**Regímenes de la válvula:** `balance`, `inundado` (sobrealimenta incluso con el sobrecalentamiento
en su mínimo) y `hambriento` (no alimenta ni con el sobrecalentamiento en su máximo físico). En los
dos extremos el balance de la válvula se viola a propósito y el desbalance se reporta como medida
del fenómeno.

**Tope físico del sobrecalentamiento:** el refrigerante no puede salir del evaporador más caliente
que el fluido que lo calienta. En una enfriadora ese tope es estrecho —el agua entra a 9-12 °C y
evapora a 4-6 °C— y limita cuánto puede degradarse una válvula antes de que el equipo salga del
régimen estacionario.

### 4.4 Subenfriamiento

```
SC = SC_nom + k_SC·(T_cond − T_cond_ref) + d_SC_falla
```

El acoplamiento con la presión de condensación es una aproximación empírica declarada: al subir la
presión se acumula líquido y crece el área inundada. Sin él, `res_SC` solo llevaría información
sobre el inventario de refrigerante.

### 4.5 Solución

Tres incógnitas resueltas con `scipy.optimize.fsolve`, tolerancia 1e-4 en los balances, arranque
multiarranque determinista. **La convergencia se verifica en cada punto y los descartes se cuentan.**

---

## 5. Modos de falla

| Clase | Parámetro degradado | Topologías |
|---|---|---|
| `sano` | ninguno | todas |
| `condensador_sucio` | `UA_cd·(1−0,45f)` y `ṁ_a_cd·(1−0,25f)` | cond. de aire |
| `incrustacion_condensador` | `UA_cd·(1−0,40f)` | cond. de agua |
| `incrustacion_evaporador` | `UA_ev·(1−0,40f)` | enfriadora |
| `caudal_agua_bajo` | `ṁ_w_ev·(1−0,40f)` | enfriadora |
| `evaporador_sucio` | `UA_ev·(1−0,40f)` y `ṁ_a_ev·(1−0,35f)` | expansión directa |
| `carga_baja` | `K_v·(1−0,35f)`, `SC → SC_nom(1−0,85f)` | todas |
| `sobrecarga` | `d_SC = +2,0f`, `UA_cd·(1−0,20f)` | todas |
| `txv_restringida` | `K_v·(1−0,20f)` | todas |
| `txv_sobrealimenta` | apertura base ↑, ganancia del lazo ↓ | todas |
| `compresor_desgastado` | `eta_v·(1−0,30f)`, `eta_s·(1−0,25f)` | todas |
| `incondensables` | `P_des·(1+0,15f)` sin alterar `T_cond` | todas |
| `restriccion_linea_liquido` | `ΔP_línea = 0,45f·(P_des − P_suc)` | todas |

Niveles de severidad (intervalo P-F): incipiente 0,15-0,35; moderada 0,35-0,65; severa 0,65-0,95.

**Aproximación empírica declarada:** el inventario de refrigerante (`carga_baja`, `sobrecarga`) no
se puede modelar con rigor en un modelo concentrado. Es una simplificación aceptada en la
literatura de FDD y no debe presentarse como modelo de primeros principios.

---

## 6. Ruido de sensor

`sigma = exactitud/2`, tomada de la hoja `Instrumentos`.

| Variable | Exactitud | sigma |
|---|---|---|
| `P_suc`, `P_des` | ± 0,5 % del fondo de escala | 0,25 % FS |
| Temperaturas de tubería | ± 0,5 K | 0,25 K |
| Temperaturas de agua (RTD en pozo) | ± 0,2 K | 0,10 K |
| Temperaturas de aire | ± 0,3 K | 0,15 K |
| Corriente | ± 1,5 % de la lectura | 0,75 % |
| Potencia | ± 1 % de la lectura | 0,5 % |
| Caudal de agua (ultrasónico) | ± 2 % de la lectura | 1 % |

---

## 7. Estructura del dataset

- **Conjunto balanceado:** clases × 3 niveles × 400 condiciones (hipercubo latino).
- **Conjunto de prevalencia realista:** 10 000 muestras de un barrido **independiente** (pool B).
  El tamaño subió de 3 000 porque con 0,3 % de `txv_sobrealimenta` quedaban nueve casos, y con
  nueve casos la precisión de esa clase es ruido estadístico.

Prevalencia de campo declarada (plausible, no medida): sano 68 %, ensuciamiento de condensador 8 %,
incrustación de evaporador 6 %, caudal de agua bajo 5 %, carga baja 4 %, TXV restringida 3 %,
compresor desgastado 2,5 %, restricción de línea de líquido 1,5 %, incondensables 1 %, sobrecarga
0,7 %, TXV sobrealimenta 0,3 %.

---

## 8. Clasificador

- `RandomForestClassifier`; entradas **únicamente** las columnas `res_*` por lista blanca.
- Partición 70/15/15 **por grupos de condición de contorno**.
- `GridSearchCV` optimizando **F1 macro**, nunca exactitud, con `GroupKFold`.
- `class_weight='balanced'` en el modelo evaluado sobre prevalencia realista.
- Semilla fija y declarada; el conjunto de prueba se abre **una sola vez**.
- Modelo secundario de severidad: `RandomForestRegressor` sobre las muestras con falla.

### 8.1 Métricas obligatorias, en este orden

1. Matriz de confusión normalizada por fila, en ambos conjuntos.
2. Recall y F1 por clase, con **intervalo de Wilson** al 95 % en las clases con soporte < 50.
3. F1 macro y F1 ponderado.
4. Curvas precisión-recall y PR-AUC por clase.
5. Exactitud global — al final, acompañada de la proporción de clases.

### 8.2 Análisis adicionales

6. Importancia por permutación, contrastada contra la expectativa física.
7. Curva de detección frente a severidad.
8. Estudio de sensibilidad al ruido (0,5×, 1×, 2×).
9. **Barrido de discrepancia modelo-planta** (0 %, 3 %, 5 %, 8 %, 15 %) y **cinco repeticiones**
   con error de calibración por corrida, para separar el efecto promedio del nivel de discrepancia
   de la dispersión entre implantaciones concretas.

---

## 9. Parámetros pendientes

Refrigerante, capacidad nominal, desplazamiento y velocidad del compresor, eficiencias,
coeficiente de flujo de la válvula, caudales de agua y aire, setpoint y salto nominal del agua
helada, y los `UA` —que **se calibran, no se asumen**—. Valores provisionales en `config/params.py`,
declarados en pantalla y en `metricas.json` en cada corrida.

---

## 10. Entregables

```
proyecto-fdd/
├── config/params.py            # parámetros, semilla, ruido, discrepancia
├── src/topologia.py            # topologías seleccionables            [añadido]
├── src/ciclo.py                # modelo físico (CoolProp)
├── src/calibracion.py          # ajuste de los UA, parametrizable      [añadido]
├── src/fallas.py               # inyección de fallas y tabla de firmas
├── src/generador.py            # barrido, ruido, discrepancia, dataset
├── src/features.py             # residuos y lista blanca
├── src/modelo.py               # entrenamiento, evaluación, análisis
├── src/reporte.py              # exportación a Word                    [añadido]
├── tests/                      # verificación física                   [añadido]
├── data/, figuras/, resultados/
├── requirements.txt, README.md
```

Figuras: P-h sano vs degradado; matrices de confusión de ambos conjuntos; curvas PR; importancia por
permutación; detección vs severidad; sensibilidad al ruido; **sensibilidad a la discrepancia**;
mapa de firmas.

---

## 11. Declaraciones obligatorias en el informe

1. Entrenado con **datos sintéticos**, no con históricos de la instalación.
2. El inventario de refrigerante es una **aproximación empírica**.
3. Se demuestra **viabilidad del método**; implementar exige recolección y recalibración.
4. Métricas principales: **recall y F1 por clase**; la exactitud acompañada de la proporción.
5. Los resultados principales se reportan **con discrepancia modelo-planta**; los de discrepancia
   cero son cota superior teórica.
6. El circuito de agua helada se supone de **caudal primario constante** (sección 12).

---

## 12. Supuestos pendientes de verificar en campo

| Supuesto | Cómo se verifica | Consecuencia si es falso |
|---|---|---|
| Caudal primario **constante** | Visita al cuarto de máquinas: válvulas de dos vías y variadores en las bombas | Con caudal variable, un caudal reducido a carga parcial es operación normal y la clase `caudal_agua_bajo` deja de ser válida tal como está planteada |
| Condensador enfriado por **aire** | Inspección visual de la azotea: presencia de torre de enfriamiento | Cambia la topología a `chiller_cond_agua`: entra `approach_cd`, `HR_amb` pasa a intervenir físicamente y `condensador_sucio` se sustituye por `incrustacion_condensador` |
| Compresor de **tornillo** con modulación continua | Placa del equipo | Con compresor alternativo por escalones, la fracción de capacidad sería discreta |

---

## 13. Cambios respecto de la versión 1

| # | Cambio | Motivo |
|---|---|---|
| 1 | Evaporador de **agua** y topologías seleccionables | Se confirmó que el sistema de estudio es una enfriadora de un edificio de oficinas |
| 2 | **Control de capacidad** con sus tres regímenes y banderas | Un chiller de tornillo modula para sostener el setpoint; sin control, a carga parcial el modelo sobre-enfriaba el agua muy por debajo del setpoint, un estado que en la instalación no existe |
| 3 | **Válvula de expansión como elemento de flujo** | En la v1 la falla de válvula era un desplazamiento del setpoint de sobrecalentamiento, sin consecuencia sobre el flujo: `res_rp`, `res_COP` y `res_split_cond` quedaban en cero |
| 4 | **Acoplamiento sobrecalentamiento-área seca** del evaporador | Sin él, el sobrecalentamiento no tiene consecuencia sobre la evaporación y las fallas de válvula siguen sin mover el ciclo |
| 5 | **Acoplamiento subenfriamiento-presión de condensación** | En la v1 `res_SC` solo respondía al inventario de refrigerante |
| 6 | Término de inventario de `sobrecarga` reducido de 12·f a 2,0·f | Con el acoplamiento anterior, sumar ambos contaba dos veces el mismo efecto y el COP **subía** con la sobrecarga |
| 7 | `condensador_sucio` degrada también el **caudal de aire** | Sin esa caída, el salto de aire del condensador no se mueve y la firma distintiva de los incondensables no es verificable |
| 8 | `txv_restringida` acotada a 0,20·f | Por encima, el equipo no tiene estado estacionario a carga parcial: el evaporador de una enfriadora no puede desarrollar el sobrecalentamiento que la válvula necesita para abrir |
| 9 | `restriccion_linea_liquido` con coeficiente 0,45 y **flasheo** en la línea | Con el 0,20 de la v1 el líquido nunca flashea, así que la firma de «burbujas en el visor» que la propia v1 le atribuye no puede producirse, y la falla queda con la misma firma que `txv_restringida` |
| 10 | **Discrepancia modelo-planta** y su barrido | Sin ella el único error es el ruido de sensor y la separación entre clases es trivial por construcción |
| 11 | Conjunto de prevalencia de 3 000 a **10 000** muestras e **intervalos de Wilson** | Con 3 000 muestras la clase más rara dejaba nueve casos y su precisión era ruido estadístico |
| 12 | Clase nueva **`caudal_agua_bajo`** | Es una de las fallas más frecuentes en sistemas hidrónicos y no estaba contemplada |

---

## 14. Referencias (APA 7)

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
- Çengel, Y. A., & Boles, M. A. *Termodinámica.* McGraw-Hill.
- Çengel, Y. A., & Ghajar, A. J. *Transferencia de calor y masa.* McGraw-Hill.
