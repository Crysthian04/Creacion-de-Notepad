# Auditoría de solo lectura del módulo FDD — 10 de noviembre de 2026

**Proyecto:** Plan Integral de Mantenimiento — Fase 5 (Monitoreo e Innovación), UTP
**Rama auditada:** `claude/fdd-random-forest-audit-gjehhl`, commit `3a4b6f3`
**Motivo:** el sitio de estudio cambió a un congelador de expansión directa (condensadora
Heatcraft MOH019L63CF, R-404A, baja temperatura −40 a 0 °F, evaporador de aire con
desescarche eléctrico). Se audita el código tal como está para decidir qué se conserva.

## Alcance y método

- **No se modificó ningún archivo del proyecto.** `git status --porcelain` devuelve vacío
  antes y después de la auditoría. El único archivo nuevo es este documento.
- **No se reentrenó nada.** Las métricas que se citan se leen de los artefactos guardados
  (`resultados/metricas.json`, `resultados/generacion.json`, `resultados/malla_error.json`)
  y de los datasets ya generados (`data/*.parquet`).
- Sí se ejecutaron, porque el encargo lo permite: la batería de pruebas existente
  (`pytest tests`), lecturas de la malla exportada con `node`, carga del visualizador en
  Chromium bajo `file://`, y **sondas del solver** que importan el código tal como está y
  lo evalúan en condiciones nuevas. Las sondas viven en el directorio temporal de la
  sesión, no en el repositorio.
- Una sonda (§6) carga `src/ciclo.py` **en memoria** con un literal cambiado para medir si
  un solo valor explica la falta de convergencia en frío. El archivo en disco no se tocó.
- Donde algo no se puede determinar leyendo el código, se escribe **«no determinable»** y
  se dice qué haría falta.

---

## 1. Física que el modelo implementa hoy

### 1.1 Lo que es, en una frase

Un gemelo digital **estacionario** de ciclo de compresión de vapor, de caja gris, resuelto
por `scipy.optimize.fsolve` sobre tres ecuaciones (balance del evaporador, balance del
condensador, balance de flujo de la válvula), con propiedades del refrigerante tomadas de
CoolProp y con una capa de residuos encima.

| Elemento | Formulación | Archivo:línea |
|---|---|---|
| Propiedades del refrigerante | `CoolProp.PropsSI`, rocío para succión y burbuja para líquido | `src/ciclo.py:98`–`126`, `295`–`330` |
| Psicrometría (bulbo húmedo de torre) | `CoolProp.HAPropsSI("Twb", …)` | `src/ciclo.py:130`–`132` |
| Intercambiadores | Efectividad-NTU, **sensible puro**, `ε = 1 − exp(−UA/C)` | `src/ciclo.py:267` (cond.), `src/ciclo.py:270`–`289` (evap.) |
| Escalado de UA con caudal secundario | `UA ∝ ṁ^0.8` | `src/ciclo.py:261`–`262` |
| Acoplamiento SH → área seca | `UA_ev_ef = UA_ev·(1 − β_sh·min(SH/SH_ref, 1))`, β_sh = 0,45 | `src/ciclo.py:288`–`289`, `config/params.py` (`beta_sh_UA`) |
| Compresor | `ṁ_r = y·V_disp·N_rev·η_v/v_suc`, con `η_v = (η_v0 − k_v(rp−1))·f_ηv` | `src/ciclo.py:313`–`318` |
| Penalización a carga parcial (IPLV) | `η_s = η_s0·(1 − k_cp·(1 − y))·f_ηs` | `src/ciclo.py:316` |
| Subenfriamiento acoplado a la presión | `SC = SC_nom + k_SC·(T_cond − T_cond_ref) + d_SC_falla` | `src/ciclo.py:326`–`327` |
| Línea de líquido y flasheo | `ΔP_línea = frac·(P_cond − P_suc)`; `T_liq` medida se limita a la saturación aguas abajo | `src/ciclo.py:333`–`351` |
| Válvula de expansión como elemento de flujo | `ṁ_v = K_v·f_Kv·a(SH)·√(ρ_líq·ΔP_válvula)`, con `a = clip(a_nom + d_a + K_ctrl·f_Kctrl·(SH − SH_obj), a_min, 1)` | `src/ciclo.py:355`–`358` |
| Potencia eléctrica y corriente | `W_elec = W_comp/η_motor + W_aux`; `I = W_elec/(√3·V·fp)` | `src/ciclo.py:369`–`370` |
| Tope físico del sobrecalentamiento | `SH_max = t_in_ev − T_evap − 0,5` (el refrigerante no puede salir más caliente que su fuente) | `src/ciclo.py:423`–`427` |
| Cota inferior de la temperatura de evaporación | `te_min = max(T_triple + 5, −25,0)` | `src/ciclo.py:417` |
| Regímenes de capacidad y de válvula | selección por residuo con guardas de validez | `src/ciclo.py:515`–`527` (guarda), `569`–`585` (selección) |
| Residuo | `res_X = X(medición degradada) − X(predicción sana al mismo contorno)` | `src/features.py:95`–`166` |

### 1.2 Las tres topologías y la que está activa

`src/topologia.py` define tres sistemas seleccionables con una línea de configuración
(`config/params.py:29`):

| `TIPO_SISTEMA` | Evaporador | Condensador | Clases | Residuos |
|---|---|---|---|---|
| **`chiller_cond_aire`** (activo) | agua helada | aire | 11 | 11 |
| `chiller_cond_agua` | agua helada | agua + torre | 11 | 12 |
| `expansion_directa` | **aire** | aire | 10 | 11 |

El lado secundario se elige en `src/ciclo.py:235`–`267`:

- Evaporador de agua (`src/ciclo.py:240`–`244`): caudal primario constante,
  `T_ret = T_sup_sp + Q_load/(ṁ_w·cp)`.
- Evaporador de aire (`src/ciclo.py:246`–`249`):
  `ṁ_ev = m_a_ev·f_m_sec_ev·Q_load_frac`, `t_in_ev = T_space_sp`.
- Condensador de aire (`src/ciclo.py:258`–`259`): `t_in_cd = T_amb`.
- Condensador de agua (`src/ciclo.py:250`–`257`): `t_in_cd = T_bulbo_húmedo + approach_torre`.

### 1.3 Simplificaciones declaradas en el propio código

De `src/ciclo.py:41`–`55` y `README.md:144`–`170`:

| # | Simplificación | Dónde se declara |
|---|---|---|
| a | **Intercambio sensible puro.** Exacto en el evaporador de agua; en el de aire **ignora la deshumidificación** | `src/ciclo.py:43`–`45` |
| b | Caudal primario constante en el circuito de agua helada — **supuesto, no hecho verificado** | `src/ciclo.py:46`–`51` |
| c | La carga del edificio fija la temperatura de retorno; no se modela la pérdida de capacidad de las serpentinas | `src/ciclo.py:52`–`54` |
| d | `UA ∝ ṁ^0.8` | `src/ciclo.py:55` |
| e | El acoplamiento SH → área seca es «una aproximación empírica declarada» de un modelo distribuido de dos zonas | `src/ciclo.py:284`–`287` |
| f | El acoplamiento SC ↔ presión de condensación también es empírico declarado | `src/ciclo.py:33`–`39` |

### 1.4 Lo que NO existe en el modelo

Verificado por búsqueda sobre todo el proyecto (`.py`, `.md`, `.js`, `.html`):

- **R-404A: cero apariciones.** El refrigerante es un campo de dataclass
  (`config/params.py:103`, valor `"R134a"`); el preset de respaldo usa `"R410A"`
  (`config/params.py:188`–`190`). CoolProp sí conoce `R404A`.
- **Desescarche: cero apariciones.** Ni eléctrico, ni por gas caliente, ni por aire.
- **Escarcha / formación de hielo: cero apariciones.**
- **Calor latente y deshumidificación:** solo dos menciones, y ambas son la declaración de
  que **no se modela** (`src/ciclo.py:45`, `README.md:150`).
- **Baja temperatura:** `src/ciclo.py:417` fija un piso de **−25,0 °C** a la temperatura de
  evaporación. No es una propiedad del refrigerante; es un literal.
- **Mezclas zeotrópicas:** el código usa rocío para la succión y burbuja para el líquido
  (`src/ciclo.py:299`–`300`, `src/features.py:106`–`108`), que es la convención correcta
  para una mezcla con deslizamiento. El R-404A tiene 0,66 K de deslizamiento a −30 °C
  (medido con CoolProp en esta auditoría). El tratamiento es correcto de forma, pero
  **nunca se ha ejercitado con una mezcla**: el único refrigerante usado en una corrida
  completa es R-134a.

---

## 2. Catálogo de fallas y variables medidas

### 2.1 Catálogo (topología activa: 11 clases)

Severidad `f ∈ [0,1]`; niveles en `src/fallas.py:67`–`70`: incipiente 0,15–0,35,
moderada 0,35–0,65, severa 0,65–0,95.

| # | Clase | Mecanismo físico inyectado | Ajuste | Línea |
|---|---|---|---|---|
| 0 | `sano` | — | ninguno | `src/fallas.py:88`–`91` |
| 1 | `condensador_sucio` | aletas obstruidas: cae UA **y** caudal de aire | `f_UA_cd = 1−0,45f`, `f_m_sec_cd = 1−0,25f` | `src/fallas.py:99` |
| 2 | `incrustacion_evaporador` | incrustación lado agua: solo cae UA | `f_UA_ev = 1−0,40f` | `src/fallas.py:110` |
| 3 | `caudal_agua_bajo` | bomba degradada / filtro obstruido | `f_m_sec_ev = 1−0,40f` | `src/fallas.py:115` |
| 4 | `carga_baja` | menos inventario: válvula con burbujas y menos SC | `f_K_v = 1−0,35f`, `d_SC = −0,85f·SC_nom` | `src/fallas.py:130` |
| 5 | `sobrecarga` | líquido inunda el condensador | `d_SC = +2,0f`, `f_UA_cd = 1−0,20f` | `src/fallas.py:146` |
| 6 | `txv_restringida` | coeficiente de flujo degradado | `f_K_v = 1−0,20f` | `src/fallas.py:174` |
| 7 | `txv_sobrealimenta` | bulbo descargado: válvula abierta y sin control | `d_a_nom = (1−a_nom)f`, `f_K_ctrl = 1−f` | `src/fallas.py:180` |
| 8 | `compresor_desgastado` | fugas internas y pérdida isentrópica | `f_eta_v = 1−0,30f`, `f_eta_s = 1−0,25f` | `src/fallas.py:184` |
| 9 | `incondensables` | presión parcial de aire en el condensador | `frac_P_des_extra = 0,15f` | `src/fallas.py:190` |
| 10 | `restriccion_linea_liquido` | filtro deshidratador obstruido → ΔP y flasheo | `frac_dP_liquido = 0,45f` | `src/fallas.py:210` |

Clases que **solo existen en la topología de expansión directa**: `evaporador_sucio`
(`src/fallas.py:118`, `f_UA_ev = 1−0,40f` y `f_m_sec_ev = 1−0,35f`), que reemplaza a las
dos clases del lado agua. En esa topología hay 10 clases, no 11 (`src/fallas.py:47`–`53`).

Dos desviaciones respecto de la especificación quedan declaradas en el propio código y se
confirman aquí: el coeficiente de `restriccion_linea_liquido` es 0,45 y no 0,20 (con 0,20 el
flasheo nunca ocurre y la falla queda indistinguible de `txv_restringida`,
`src/fallas.py:194`–`209`), y `condensador_sucio` añade una caída de caudal de aire que la
sección 4 de la especificación no pide (`src/fallas.py:95`–`98`).

### 2.2 Las 13 variables medidas de la topología activa, con unidades

Definidas en `src/topologia.py:64`–`77`; el ruido de sensor, en
`config/params.py:230`–`255`. σ = exactitud/2 asumiendo que la exactitud declarada es un
intervalo de confianza del 95 % (`config/params.py:225`–`227`).

| # | Variable | Magnitud | Unidad | σ de ruido | Instrumento declarado |
|---|---|---|---|---|---|
| 1 | `P_suc` | presión de succión | **psig** (manométrica) | 0,75 psig (0,25 % de 300 FS) | manifold digital |
| 2 | `P_des` | presión de descarga | **psig** | 1,25 psig (0,25 % de 500 FS) | manifold digital |
| 3 | `T_ev_out` | temperatura a la salida del evaporador | °C | 0,25 K | termopar tipo K |
| 4 | `T_suc` | temperatura de succión al compresor | °C | 0,25 K | termopar tipo K |
| 5 | `T_des` | temperatura de descarga | °C | 0,25 K | termopar tipo K |
| 6 | `T_liq` | temperatura de la línea de líquido (aguas abajo del filtro) | °C | 0,25 K | termopar tipo K |
| 7 | `I_avg` | corriente media de línea | A | 0,75 % de la lectura | pinza True RMS |
| 8 | `W_elec` | potencia eléctrica activa | W | 0,5 % de la lectura | analizador de redes |
| 9 | `T_agua_in_ev` | agua de retorno al evaporador | °C | 0,10 K | RTD Pt100 en pozo |
| 10 | `T_agua_out_ev` | agua de suministro del evaporador | °C | 0,10 K | RTD Pt100 en pozo |
| 11 | `V_agua_ev` | caudal de agua del evaporador | **kg/s** (ver nota) | 1,0 % de la lectura | caudalímetro ultrasónico |
| 12 | `T_air_in_cd` | aire de entrada al condensador | °C | 0,15 K | sonda T-HR |
| 13 | `T_air_out_cd` | aire de salida del condensador | °C | 0,15 K | sonda T-HR |

**Nota sobre la unidad 11.** El nombre `V_agua_ev` sugiere caudal volumétrico, pero el
campo transporta el **caudal másico en kg/s**: se escribe desde `sec["m_ev"]`
(`src/ciclo.py:610`) y se consume multiplicado por `cp` sin conversión de densidad
(`src/features.py:119`–`123`). El uso es internamente consistente, así que **no hay error
numérico**, pero el nombre es engañoso y en campo invita a anotar m³/h en una casilla que
espera kg/s. Se registra como observación, no como defecto de cálculo.

`T_amb` y `HR_amb` también se miden, pero son condiciones de contorno y están excluidas del
clasificador por decisión trazable (`src/features.py:65`–`66`).

### 2.3 Los 11 residuos que ve el clasificador

`res_SH_evap`, `res_SH_total`, `res_SC`, `res_SH_des`, `res_rp`, `res_COP`, `res_kW_TR`,
`res_approach_ev`, `res_dT_agua_ev`, `res_split_cond`, `res_dT_air_cd`
(`resultados/metricas.json`, clave `columnas_de_entrada`; construidos por lista blanca en
`src/features.py:58`–`60`). La lista blanca es estructural: `construir_matriz_X` falla
ruidosamente si falta una columna, y nunca se construye por `drop`.

---

## 3. Rangos de los datos de entrenamiento y métricas actuales

### 3.1 Rangos realmente muestreados

Medidos sobre los `.parquet` guardados, no sobre la configuración:

| Variable | Rango configurado | Rango observado (balanceado) | Rango observado (prevalencia) |
|---|---|---|---|
| `T_amb` | 24–36 °C | 24,003 – 35,992 °C | 24,001 – 36,000 °C |
| `HR_amb` | 60–95 % | 60,07 – 94,93 % | 60,00 – 95,00 % |
| `Q_load_frac` | **0,40 – 1,00** | **0,4011 – 0,9986** | **0,4000 – 1,0000** |
| `severidad_f` | 0,15–0,95 por nivel | 0,0000 – 0,9500 | 0,0000 – 0,9499 |
| `y_capacidad` (resultado) | — | 0,2963 – 1,0338 | 0,2941 – 1,0000 |

Muestreo por hipercubo latino; el piso de carga está en `config/params.py:208`
(`Q_load_frac_min: float = 0.40`).

### 3.2 ¿Bajó el muestreo de carga 0,34? — **No, en los datos de entrenamiento.**

La pregunta se responde con conteos exactos:

| Conjunto | Filas | Filas con `Q_load_frac < 0,40` | Filas con `< 0,34` | Filas con `≤ 0,34` |
|---|---|---|---|---|
| `dataset_balanceado.parquet` | 13 077 | **0** | **0** | **0** |
| `dataset_prevalencia.parquet` | 9 964 | **0** | **0** | **0** |

Y en consecuencia:

| Bandera | Balanceado | Prevalencia |
|---|---|---|
| `ciclado = True` | **0** | **0** |
| `capacidad_saturada = True` | 153 | 46 |
| `retorno_liquido = True` | 461 | 6 |
| `y_capacidad < y_min (0,25)` | **0** | **0** |

Regímenes resueltos: balanceado `controlado` 12 464, `controlado_inundado` 461,
`saturado` 150, `saturado_hambriento` 2; prevalencia `controlado` 9 912, `saturado` 45,
`controlado_inundado` 6, `saturado_hambriento` 1.

**Conclusión operativa:** el clasificador nunca vio un punto en ciclado, y el defecto de la
zona de carga baja **no contamina las métricas reportadas**. Afecta exclusivamente a la
malla exportada al visualizador, que sí tiene nodos en 0,28 y 0,31
(`src/exportador_web.py:58`, `CARGAS`). El reparto en la malla es:

| Banda de carga | Nodos | `ciclado = 1` | de ellos con `y < y_min` | `convergio = 0` |
|---|---|---|---|---|
| `< 0,34` (0,28 y 0,31) | 770 | 586 | **490** | 83 |
| `≥ 0,34` | 3 850 | 37 | **29** | 106 |
| **Total** | **4 620** | **623** | **519** | **189** |

### 3.3 Convergencia y descartes de la generación

De `resultados/generacion.json`:

| Conjunto | Intentos | Convergidos | Descartados | Fracción |
|---|---|---|---|---|
| Balanceado | 13 200 | 13 077 | 123 | 0,932 % |
| Prevalencia | 10 000 | 9 964 | 36 | 0,360 % |

Descartes por clase (balanceado): `carga_baja` 117, `restriccion_linea_liquido` 4,
`txv_sobrealimenta` 2. En prevalencia, los 36 son todos `carga_baja`. **Cero condiciones de
contorno descartadas por completo**, así que la partición por grupos no perdió grupos.
El motivo se registra caso a caso con el residuo exacto («residuo 6,02e-02 por encima de la
tolerancia 1e-04», etc.).

### 3.4 Partición

Por grupos de condición de contorno (`cond_id`), sin fuga entre particiones:

| Partición | Filas | Condiciones |
|---|---|---|
| Entrenamiento | 9 151 | 280 |
| Validación | 1 929 | 59 |
| Prueba | 1 997 | 61 |

`condiciones_compartidas_entre_particiones = 0`. El conjunto de prueba se abrió **una vez**
por conjunto, con motivo registrado («evaluación final del informe»);
`corrida_valida = true`.

### 3.5 Métricas guardadas

Semilla maestra 20 260 902; discrepancia modelo-planta 5 % en modo `por_condicion`;
factor de ruido 1,0. Modelo ganador: `random_forest` con
`max_depth = 16`, `max_features = 0,5`, `min_samples_leaf = 1`, `n_estimators = 100`,
elegido por **F1 macro sobre validación** (0,7608 frente a 0,7239 del árbol único).

| Conjunto | n | **F1 macro** | F1 ponderado | Exactitud | Recall macro | PR-AUC macro |
|---|---|---|---|---|---|---|
| Validación | 1 929 | 0,7608 | 0,7591 | 0,7506 | 0,7522 | 0,8117 |
| **Prueba balanceada** | 1 997 | **0,7543** | 0,7527 | 0,7376 | 0,7391 | 0,8074 |
| **Prevalencia realista** | 9 964 | **0,5835** | 0,7293 | 0,6827 | 0,7269 | 0,7205 |
| Prevalencia sin `class_weight` | 9 964 | 0,5851 | 0,7254 | 0,6771 | 0,7307 | 0,7242 |

F1 por clase en la prueba balanceada: `carga_baja` 0,948, `condensador_sucio` 0,925,
`incondensables` 0,916, `txv_sobrealimenta` 0,884, `caudal_agua_bajo` 0,869,
`compresor_desgastado` 0,822, `incrustacion_evaporador` 0,732, `sobrecarga` 0,653,
`restriccion_linea_liquido` 0,599, `txv_restringida` 0,516, **`sano` 0,433**.

La clase `sano` tiene precisión 0,33 con recall 0,64: el modelo declara avería en máquinas
sanas con frecuencia. En prevalencia realista las clases raras colapsan en precisión
(`sobrecarga` 0,13, `txv_restringida` 0,12, `txv_sobrealimenta` 0,17) manteniendo recall
alto: el clasificador está regulado para no perder fallas, a costa de falsas alarmas.

Modelo de severidad (regresión): MAE 0,1030 y R² 0,652 en prueba.

Estudios de robustez:

| Factor de ruido | F1 macro | Diagnóstico incipiente | Detección incipiente |
|---|---|---|---|
| 0,5 | 0,8172 | 0,624 | 0,788 |
| **1,0** | **0,7572** | **0,482** | **0,788** |
| 2,0 | 0,6460 | 0,365 | 0,806 |

| Discrepancia modelo-planta | F1 macro | Diagnóstico incipiente |
|---|---|---|
| 0,00 | 0,8198 | 0,641 |
| 0,03 | 0,7700 | 0,529 |
| **0,05** | **0,7572** | **0,482** |
| 0,08 | 0,7491 | 0,512 |
| 0,15 | 0,6638 | 0,394 |

Cinco repeticiones con ε por corrida: F1 macro 0,7950 ± 0,0076 (mín 0,7867, máx 0,8024).

Detección frente a severidad, casos extremos: `restriccion_linea_liquido` no se detecta por
debajo de severidad ≈ 0,45 (0,031, 0,034 y 0,000 en los tres primeros tramos) y llega a
1,000 desde 0,65. `compresor_desgastado` sube 0,241 → 0,469 → 0,762 → 0,917. Es el
resultado que el informe debe leer como límite del método, no como error.

Calibración de los UA: `UA_ev = 91 066 W/K`, `UA_cd = 58 795 W/K`, convergió con RMSE
relativo 1,67e-13 en 32 evaluaciones, **marcada como provisional**, con origen «punto de
diseño de catálogo, sustituir por la hoja `Registro Campo` de la Fase 1». Hay **29
parámetros marcados como provisionales**.

---

## 4. Estado de los defectos 1, 2 y 3

### Defecto 1 — la bandera `ciclado` de la malla no es fiable: **ABIERTO**

**Dónde está.** `src/ciclo.py:571`–`581`. La bandera se fija *antes* de reintentar a
capacidad mínima:

```
elif y < p.y_min:
    ciclado = True                                  # línea 578
    r2 = _resolver(p.y_min, modo)                   # línea 579
    if r2 is not None and r2[0] < max(residuo, tol):
        (residuo, t_evap, t_cond, sh, y, e, msg), y_fijo = r2, p.y_min
```

Si el reintento a `y = y_min` no mejora el residuo, la condición de la línea 580 falla y el
código **conserva la solución no acotada** (`y < y_min`) mientras `ciclado` ya quedó en
`True`. La guarda de validez de capacidad (`src/ciclo.py:522`–`527`) invalida con
`residuo = inf` los candidatos a `y_min` que se quedan cortos, pero el candidato a `y_min`
que sobre-entrega —que es el físicamente correcto en ciclado— produce un residuo grande
porque no puede sostener el setpoint, y por eso pierde la comparación.

**Magnitud medida en la malla exportada** (`web/datos/fdd_malla.js`, 4 620 nodos):

- 623 nodos con `ciclado = 1`.
- **519 de ellos (83 %) son estados que la máquina no puede tener**: `y_capacidad < 0,25`
  con el setpoint sostenido.
- Los 519 tienen `fraccion_marcha = 1,000` en lugar de la proporción real de tiempo
  encendido, así que **el arranque matutino no se puede reconstruir con la malla**.
- 490 están en la banda `carga < 0,34`; **29 están en `carga = 0,34`**, con
  `y_capacidad` entre 0,2431 y 0,2500 (hasta 0,007 por debajo del mínimo), repartidos en
  9 de las 11 clases.

**Impacto en las métricas: ninguno.** El dataset no tiene un solo punto con
`Q_load_frac < 0,40` ni con `ciclado = True` (§3.2). El defecto es exclusivo del
visualizador.

**Documentación.** Está declarado en `README.md:248`–`261` («Zona de carga baja: DEFECTO
ABIERTO, no usar todavía»), con el caso concreto correcto (carga 0,28 a 30 °C, `y = 0,214`)
y la causa correctamente localizada. Ver §8 para una imprecisión de esa declaración.

### Defecto 2 — `buscarCelda` satura en silencio: **ABIERTO, sin mitigación**

**Dónde está.** `web/js/fdd_inferencia.js:85`–`91`:

```js
function buscarCelda(eje, v) {
  if (v <= eje[0]) return {i: 0, t: 0.0};
  if (v >= eje[eje.length - 1]) return {i: eje.length - 2, t: 1.0};
  var i = 0;
  while (i < eje.length - 2 && eje[i + 1] < v) i++;
  return {i: i, t: (v - eje[i]) / (eje[i + 1] - eje[i])};
}
```

Cualquier valor fuera del dominio se colapsa sobre el nodo del borde y **la función devuelve
exactamente la misma estructura que para un punto interior**. No hay bandera, ni valor
centinela, ni excepción.

**Verificado en vivo** (Chromium, `file://`, esta sesión):
`FDD.consultar(50, 2.0, "sano", 0)` —temperatura ambiente de 50 °C y carga del 200 %, ambas
muy fuera de la malla— devuelve un estado completo de 55 claves con `T4_C = 4,5046` y
**ninguna clave que indique extrapolación**. La búsqueda de la cadena `extrapol` en todo
`web/` devuelve **cero resultados**; la única aparición en el proyecto es un comentario de
`src/exportador_web.py:389` sobre otro asunto.

**Consecuencia.** El visualizador no puede distinguir «estado calculado» de «estado del
borde devuelto porque la consulta se salió del mapa». En una defensa, una pregunta del
jurado fuera de rango recibe una respuesta con la misma apariencia de validez que una
dentro de rango.

### Defecto 3 — `diagnosticar` alimenta residuos limpios a un modelo entrenado con ruido: **ABIERTO, documentado pero no mitigado en el código**

**Dónde está.** `web/js/fdd_inferencia.js:172`–`181`:

```js
function diagnosticar(tAmb, carga, clase, severidad) {
  var estado = consultar(tAmb, carga, clase, severidad);
  var residuos = {};
  for (var k = 0; k < FDD_MODELO.columnas_entrada.length; k++) {
    var col = FDD_MODELO.columnas_entrada[k];
    residuos[col] = estado[col];
  }
  return {estado: estado, residuos: residuos, diagnostico: predecir(residuos)};
}
```

Los residuos de la malla se generan **sin ruido de sensor y sin discrepancia
modelo-planta** (`src/exportador_web.py:343`–`348` y `366`–`367`: la referencia sana se
calcula con el mismo juego de parámetros). El clasificador se entrenó **con ambos**. El
desacuerdo está declarado como dato en `FDD_FISICA.nota_ruido`
(`src/exportador_web.py:238`–`241`): *«El clasificador se entreno CON ambos, asi que
alimentado con residuos limpios acertara mas de lo que dice el informe»*. Pero
`diagnosticar()` no aplica ruido, no avisa, y **el objeto que devuelve no lleva ninguna
marca**: quien use la función sin haber leído el archivo de física verá aciertos mejores
que los del informe y no sabrá por qué.

Cuantificación disponible del sesgo, sin reentrenar: el barrido de ruido de §3.5 da F1 macro
0,7572 con factor 1,0 y el barrido de discrepancia da 0,8198 con discrepancia nula. Es
decir, **del orden de +6 puntos de F1 macro de optimismo**, y el diagnóstico de fallas
incipientes pasa de 0,482 a 0,641 (+16 puntos). Es una cota, no una medida exacta del caso
de la malla, porque los dos efectos no son separables así: la medida exacta requeriría
reentrenar, que esta auditoría no hace.

### Hallazgo adicional no catalogado — `diagnosticar` declara «sano» los nodos sin estado estacionario

No estaba en la lista de tres defectos, y es más grave que el defecto 2.

Los 189 nodos con `convergio = 0` llevan todos sus residuos como `null`
(`src/exportador_web.py:397`–`404`, `_fila_vacia`). En `probabilidades()`
(`web/js/fdd_inferencia.js:54`) cada característica pasa por `Math.fround(residuos[col])`, y
`Math.fround(null)` vale **0**. Un nodo sin solución física entra al bosque como un vector
de once ceros, es decir **como una máquina perfectamente sana**.

Verificado en vivo: `FDD.diagnosticar(24, 0.28, "carga_baja", 0.15)` —un nodo con
`convergio = 0`— devuelve `clase: "sano"` con `confianza: 0,348`. No hay comprobación de
`estado.convergio` en ninguna parte de `diagnosticar`.

Reparto de los 189: por clase, `carga_baja` 132, `restriccion_linea_liquido` 38,
`txv_restringida` 19. Por carga, 51 en 0,28 y 32 en 0,31, pero también 18 a carga plena y
15 en 0,95 — es decir **no es un problema confinado a la zona de carga baja**.

---

## 5. Visualizador: viabilidad bajo `file://`

### 5.1 Verificación en navegador — **funciona**

Contrariamente a lo que esta auditoría supuso en un primer momento, el contenedor **sí tiene
Chromium** (`/opt/pw-browsers/chromium` y `/usr/bin/google-chrome`), así que la comprobación
se hizo en vivo y no se queda en «no determinable».

`file:///…/proyecto-fdd/web/verificacion.html` abierto en Chromium headless:

- **0 errores de página**, **0 mensajes de consola**.
- Carga completa en **3,2 s** (incluido el arranque del navegador).
- `FDD` definido; `FDD_MALLA` con 4 620 nodos; `FDD_MODELO` con 100 árboles.
- Las **ocho comprobaciones de la página pasan**: los cuatro archivos de datos cargan, la
  consulta de malla devuelve `ṁ = 1,9523 kg/s` y `W = 97,1 kW` en régimen controlado con
  interpolación bilineal, la inferencia devuelve `condensador_sucio` con confianza 1,000,
  la zona de ciclado se reporta como documentada, y la conversión de vatios a fracción de
  carga da 0,6000.

### 5.2 Archivos y tamaño

| Archivo | Bytes | Contenido |
|---|---|---|
| `web/datos/fdd_modelo.js` | 3 608 614 | `FDD_MODELO`: 100 árboles, 11 clases, umbrales y hojas |
| `web/datos/fdd_malla.js` | 1 584 913 | `FDD_MALLA`: 7 × 12 × 11 × 5 = 4 620 nodos, 47 campos continuos y 5 discretos |
| `web/datos/fdd_metricas.js` | 30 116 | `FDD_METRICAS` |
| `web/datos/fdd_fisica.js` | 10 262 | `FDD_FISICA`: parámetros, σ de ruido, campana de saturación |
| `web/js/fdd_inferencia.js` | 8 236 | inferencia de referencia (189 líneas) |
| `web/verificacion.html` | 3 804 | autoprueba de carga local |
| **Total** | **5 245 945 B = 5,00 MiB (5,25 MB)** | 6 archivos en 3 directorios |

### 5.3 Dependencias externas — **cero**

- `web/verificacion.html` tiene exactamente **cinco** etiquetas `<script src="…">`, todas
  con rutas relativas locales (líneas 23–27). Ningún `href` externo, ningún CDN, ninguna
  fuente web.
- `grep` de `fetch`, `XMLHttpRequest`, `import ` y `require(` sobre `web/js/`: la única
  aparición es el comentario de la línea 3 que declara que no se usan.
- `fdd_inferencia.js` cierra con un `module.exports` condicional, que permite cargarlo en
  Node para pruebas sin afectar la carga en navegador.
- Los cuatro archivos de datos son **declaraciones `const`**, no JSON, exactamente como se
  pidió: bajo `file://` un `fetch()` sería bloqueado por la política de mismo origen.

### 5.4 Pruebas: **156 pasan, 5 dan error**

`python -m pytest tests -q`, 171 s:

```
156 passed, 5 errors in 171.02s
```

Los cinco errores son **todos** de `tests/test_exportador.py` y **todos** la misma causa:

```
FileNotFoundError: …/proyecto-fdd/resultados/modelo_rf.joblib
```

Pruebas afectadas: `test_el_conjunto_evaluado_es_el_completo`,
`test_clase_predicha_identica_sin_tolerancia`, `test_probabilidades_coinciden_bit_a_bit`,
`test_conteo_de_muestras_al_borde_de_un_umbral`,
`test_el_modelo_exportado_declara_el_casteo_a_float32`.

El artefacto no está en el repositorio: `resultados/*.joblib` está en `.gitignore` porque el
modelo serializado pesaba 244 MB, por encima del límite de 100 MB de GitHub (se añadió
`compress=3`, pero el archivo quedó excluido de todos modos). Es decir: **en un clon limpio,
las cinco pruebas que verifican la equivalencia exacta entre JavaScript y scikit-learn no se
pueden correr sin reentrenar primero.** La equivalencia *se verificó* cuando se construyó el
exportador (1 997 muestras, clase idéntica sin tolerancia, diferencia máxima de
probabilidad 0,000e+00), y así lo declara `web/verificacion.html`, pero ese resultado
**no es reproducible hoy desde el repositorio**. Es una regresión de verificabilidad, no de
funcionalidad.

Las 156 que pasan incluyen la batería de firmas físicas (`tests/test_firmas.py`), el solver
(`tests/test_ciclo.py`), la lista blanca (`tests/test_features.py`) y la partición por grupos
(`tests/test_particion.py`).

---

## 6. Esfuerzo para adaptar el modelo a un congelador de expansión directa, R-404A, baja temperatura

### 6.0 Resultado de las sondas, antes de las horas

Tres sondas ejecutadas sobre el código tal como está, a 32 °C de ambiente y carga plena,
con el preset `parametros_expansion_directa()`:

| Refrigerante | `T_space_sp` | ¿Convergió? | `T_evap` | `T_cond` | Régimen |
|---|---|---|---|---|---|
| R-410A | +24 °C | sí | 6,54 | 47,10 | `capacidad_plena` |
| R-410A | 0 °C | sí | −9,36 | 41,03 | `capacidad_plena` |
| R-410A | −18 °C | sí | −22,83 | 37,12 | `capacidad_plena` |
| R-410A | **−25 °C** | **no** (residuo 5,29e-01) | — | — | `capacidad_plena_hambriento` |
| **R-404A** | +24 °C | sí | 6,90 | 43,42 | `capacidad_plena_hambriento` |
| **R-404A** | 0 °C | sí | −7,44 | 38,95 | `capacidad_plena` |
| **R-404A** | −18 °C | sí | −21,62 | 35,81 | `capacidad_plena` |
| **R-404A** | **−25 °C** | **no** (residuo 6,47e-01) | — | — | `capacidad_plena_hambriento` |
| **R-404A** | **−30 °C** | **no** (residuo 7,21e-01) | — | — | `capacidad_plena_hambriento` |

Causa inmediata, localizada: `src/ciclo.py:417`–`418`.

```
te_min = max(t_triple(ref) + 5.0, -25.0)
te_max = sec["t_in_ev"] - 0.5
```

Para R-404A, `T_triple + 5 = −68,15 °C`, así que **manda el literal `−25,0`**. Con el
espacio a −25 °C, `te_max = −25,5 °C` queda **por debajo** de `te_min = −25,0 °C`: el
intervalo de búsqueda está invertido y no existe solución posible. El rango del sitio nuevo
es −40 a 0 °F, es decir **−40 a −17,8 °C**: con el código actual, **la mitad inferior del
rango de operación declarado del equipo es inalcanzable por construcción**.

Una tercera sonda cargó `src/ciclo.py` en memoria con ese literal bajado a −60,0 (sin
tocar el archivo) para medir si ese valor por sí solo explica el problema. **No lo explica:**

| `T_space_sp` | ¿Convergió? | `T_evap` | `SH` | `Q_L` | COP | Régimen |
|---|---|---|---|---|---|---|
| −18 °C | **no** | −20,89 | 2,39 K | 4 159 W | 1,27 | `capacidad_plena` |
| −25 °C | **no** | −27,24 | 1,74 K | 2 833 W | 1,00 | `capacidad_plena` |
| −30 °C | sí | −31,82 | 1,32 K | 2 037 W | 0,81 | `capacidad_plena_hambriento` |
| −40 °C | sí | −40,72 | **0,22 K** | **817 W** | 0,44 | `capacidad_plena_hambriento` |

Donde converge, entrega 817 W de un serpentín nominal de 17 584 W, con 0,22 K de
sobrecalentamiento y en régimen hambriento. Eso no es un modelo de congelador: es un modelo
de aire acondicionado de 5 TR operando muy fuera de su diseño. **El piso es una condición
necesaria, no suficiente.** Dos razones estructurales lo explican:

1. **El tope físico del sobrecalentamiento** (`src/ciclo.py:423`–`427`,
   `SH_max = t_in_ev − T_evap − 0,5`) se vuelve asfixiante cuando el aire entra a −30 °C:
   el margen entre el aire y la evaporación se reduce y la válvula no puede desarrollar el
   sobrecalentamiento que necesita para abrir.
2. **El caudal de aire del evaporador escala con la carga** (`src/ciclo.py:247`:
   `m_ev = p.m_a_ev * aj.f_m_sec_ev * cond.Q_load_frac`). En un congelador el ventilador del
   evaporador es de velocidad fija y gira continuamente salvo durante el desescarche. La
   relación del código es un supuesto de enfriadora, no de cámara.

### 6.1 (a) Solo cambio de parámetros

**Qué cubre.** `TIPO_SISTEMA = "expansion_directa"`, `refrigerante = "R404A"`, `Q_nom`,
`V_disp`, `N_rev`, `eta_v0`, `k_v`, `eta_s`, `eta_motor`, `UA_ev`, `UA_cd`, `m_a_ev`,
`m_a_cd`, `K_v_valvula`, `K_ctrl_valvula`, `SH_objetivo`, `SC_nom`, `T_space_sp`,
`W_aux`, `tension_linea`, `fp`, y los rangos de `RangosContorno`. Más recalibrar los dos UA
contra un punto de diseño del catálogo Heatcraft.

**Horas: 6 – 10 h.** Incertidumbre declarada **±50 %**, y es asimétrica hacia arriba. El
desglose: 2–3 h de lectura del catálogo y de la placa; 2–3 h de derivar `V_disp` y `K_v`
desde el punto de diseño (el `K_v` ya se dimensionó mal una vez por un factor 10 en este
proyecto, así que la estimación incluye una iteración); 1–2 h de recalibración de UA;
1–2 h de ajustar los rangos y correr la verificación física.

**Qué NO cubre, y está medido.** El rango de −40 a 0 °F es inalcanzable: `src/ciclo.py:417`
es física, no configuración, y aun cambiándolo el modelo entrega resultados sin sentido
(§6.0). **La vía (a) sola no produce un modelo usable del equipo nuevo.** Esto contradice
directamente la promesa de la especificación de que el cambio de equipo de estudio cuesta
«una línea de configuración» (ver §8).

### 6.2 (b) Reescritura de física

| Trabajo | Dónde | Horas |
|---|---|---|
| Parametrizar el piso de temperatura de evaporación; sacar el literal `−25,0` | `src/ciclo.py:417` | 0,5 – 1 |
| Revisar y reformular el tope físico del sobrecalentamiento para un evaporador de aire en frío | `src/ciclo.py:423`–`427` | 3 – 6 |
| Caudal de aire del evaporador independiente de la carga (ventilador de velocidad fija) | `src/ciclo.py:246`–`249` | 1 – 2 |
| **Calor latente y formación de escarcha**: pasar de sensible puro a aire húmedo con `HAPropsSI`, y modelar el crecimiento de escarcha como degradación progresiva de UA y de caudal | `src/ciclo.py:235`–`289`, nuevo módulo | 12 – 25 |
| **Ciclo de desescarche eléctrico**: el modelo es estacionario y un desescarche es intrínsecamente transitorio. Hay que decidir entre un ciclo promediado (fracción de marcha, energía del resistor, penalización post-desescarche) o declararlo fuera de alcance | nuevo | 8 – 20 |
| **Régimen de marcha/parada por termostato**: el preset DX tiene `y_min = 1,0` y `k_carga_parcial = 0,0`, es decir sin modulación. Toda la maquinaria `controlado / saturado / ciclado` es de enfriadora con válvula deslizante; un congelador cicla por termostato | `src/ciclo.py:515`–`585` | 6 – 12 |
| Verificar el tratamiento de la mezcla zeotrópica (deslizamiento 0,66 K a −30 °C) en las definiciones de SH y SC | `src/ciclo.py:299`–`300`, `src/features.py:106`–`130` | 2 – 4 |
| **Catálogo de fallas**: desaparecen `incrustacion_evaporador` y `caudal_agua_bajo`; aparece `evaporador_sucio`; y la falla característica del sitio nuevo —**desescarche fallido / evaporador escarchado**— **no existe en el catálogo** y hay que crearla con su firma verificable | `src/fallas.py:47`–`53`, `94`–`210` | 4 – 8 |
| Reescribir la batería de firmas físicas: `tests/test_firmas.py` codifica firmas de enfriadora de agua | `tests/test_firmas.py` | 4 – 8 |
| Residuos del lado aire (`approach_evap`, `dT_air_ev`): el código ya los contempla (`src/features.py:40`–`41`), falta el inventario de instrumentos de aire y su σ de ruido | `src/features.py`, `config/params.py:230`–`255` | 2 – 4 |
| **Total (b)** | | **43 – 90 h** |

**Incertidumbre declarada: ±40 %, sesgada hacia arriba.** Los dos renglones grandes —escarcha
y desescarche— son los menos acotables, porque el proyecto no tiene todavía una decisión
tomada sobre si el desescarche se modela o se declara fuera de alcance. Esa decisión cambia
el total en unas 15 h y **no me corresponde tomarla**: afecta a lo que la Fase 5 promete
demostrar.

### 6.3 (c) Regenerar, reentrenar y re-exportar

El pipeline está parametrizado por topología, así que es sobre todo tiempo de máquina más
revisión.

**Tiempo de máquina, anclado en una medición.** El solver corre a **22,2 ms por resolución**
medido en este contenedor (150 resoluciones en 3,33 s, 150/150 convergidas, 4 núcleos
disponibles). De ahí:

- Generación de los dos datasets: 23 200 condiciones × 2 resoluciones (degradada + sana
  de referencia) ≈ **17 min en un núcleo**, del orden de **5–9 min en los 4 núcleos**.
- Exportación de la malla: 4 620 nodos × 2 resoluciones ≈ **3,5 min**.
- Validación de la malla por muestreo dirigido (9 puntos interiores por celda, 5 clases):
  del orden de **30–60 min**.
- Entrenamiento con `GridSearchCV` y los estudios de robustez: los estudios regeneran
  subconjuntos de ~3 921 filas **13 veces** (3 niveles de ruido + 5 de discrepancia +
  5 repeticiones), lo que domina el costo.
- **Tiempo total de la corrida completa: no determinable.** Ningún artefacto registra
  duraciones (`resultados/generacion.json` y `metricas.json` no guardan tiempos, y no hay
  `perf_counter` en `src/`). Para determinarlo haría falta instrumentar el pipeline o
  correrlo entero, que esta auditoría no hace.

**Trabajo humano: 10 – 18 h.** Incertidumbre **±40 %**. Desglose: recalibrar y verificar los
UA nuevos (1–2 h); correr la verificación física y leer los descartes de convergencia, que
en un equipo de baja temperatura serán muchos más que el 0,93 % actual (2–4 h);
reentrenar y revisar métricas por clase (1–2 h); re-exportar los cuatro `.js` y
**rehacer la prueba de equivalencia exacta con scikit-learn** (1–2 h, y ahora mismo
bloqueada por el `.joblib` ausente de §5.4); reescribir la prosa del informe Word, que es
toda de enfriadora (4–6 h); actualizar `README.md` y `ESPEC_Simulacion_FDD.md` (1–2 h).

### 6.4 Resumen del esfuerzo

| Vía | Horas | Incertidumbre | ¿Produce un modelo usable del sitio nuevo? |
|---|---|---|---|
| (a) solo parámetros | 6 – 10 | ±50 % | **No.** Medido: no alcanza −40 a 0 °F |
| (b) reescritura de física | 43 – 90 | ±40 % | Sí, es la vía necesaria |
| (c) regenerar y re-exportar | 10 – 18 humanas + máquina no determinable | ±40 % | Solo después de (b) |
| **(a) + (b) + (c)** | **59 – 118 h** | | |

Dos cosas que esa tabla no dice y conviene decir: el camino largo **no se puede acortar
saltándose (b)**, porque las sondas de §6.0 muestran que el modelo converge a resultados
falsos antes que no converger —que es el modo de fallo peligroso—; y la alternativa real no
es (a), es **conservar la enfriadora como sistema de estudio del módulo FDD** y tratar el
congelador como el equipo de las otras fases. Esa decisión es del proyecto, no mía, pero el
número que la informa es: entre 59 y 118 horas.

---

## 7. Plan para corregir los defectos 2 y 3 — **no implementado**

Lo que sigue es el plan pedido. **No se tocó ningún archivo.** Incluye el hallazgo adicional
de §4, porque comparte el punto de entrada con el defecto 3 y arreglar uno sin el otro deja
la función a medias.

### 7.1 Defecto 2 — hacer visible la saturación de la malla

**Principio:** la decisión de qué hacer fuera del dominio **viaja como dato desde el
exportador**, igual que ya ocurre con `celda_bilineal`, para que Python y JavaScript no
puedan divergir.

1. **`buscarCelda` devuelve el diagnóstico, no solo la celda.** Añadir a la estructura de
   retorno `fuera` (`0` dentro, `−1` por debajo, `+1` por encima) y `distancia` (cuántos
   pasos de nodo hacia fuera quedó el valor, en unidades del eje).
2. **`consultar` agrega y marca.** Recoger el `fuera` de los dos ejes continuos
   (temperatura y carga) y de los dos índices discretos (clase y severidad), y adjuntar al
   estado devuelto un bloque `_fuera_de_malla: {ejes: […], distancia_max: …}`, presente
   siempre —con `ejes: []` dentro del dominio— para que el consumidor no tenga que
   comprobar la existencia de la clave.
3. **Rechazo duro más allá de un margen declarado.** Dentro de un paso de nodo, devolver el
   borde con la bandera; más allá, devolver `null`. El margen se exporta como dato
   (`FDD_MALLA.margen_extrapolacion`), no se escribe en el JavaScript.
   **Esta es una decisión de producto que no tomo yo:** la alternativa es nunca devolver
   `null` para que la animación del visualizador no se rompa. Mi recomendación es el rechazo
   duro con margen, porque un visualizador que se queda en blanco es un error legible y un
   valor del borde disfrazado de cálculo no lo es; pero hay que decidirlo antes de escribir
   el código.
4. **Reflejar la política en el exportador.** `src/exportador_web.py` emite el margen y la
   convención; `validar_malla` gana un caso que comprueba que la bandera aparece.
5. **Pruebas nuevas en `tests/test_exportador.py`:** un caso por extremo de cada eje
   (4 casos) que compruebe que la bandera se activa y que el valor devuelto es exactamente
   el nodo del borde; un caso estrictamente interior que compruebe que la bandera está
   limpia; un caso más allá del margen que compruebe el `null`.

**Costo: 3 – 5 h**, incluido correr las pruebas. Riesgo bajo: el cambio es local a dos
funciones y a un bloque de metadatos.

### 7.2 Defecto 3 — que el diagnóstico de la malla se corresponda con el informe

El problema de fondo: los residuos son funciones **no lineales** de las mediciones
(pasan por temperaturas de saturación de CoolProp), así que *no se puede* sumar ruido a los
residuos y pretender que equivale a sumar ruido a las mediciones. Hay dos caminos y difieren
en dónde vive el cálculo.

**Opción A — ruido en el navegador.** Implementar en JavaScript un PRNG declarado y sembrado
(tipo `mulberry32`, con la semilla visible en la interfaz para que la página siga siendo
reproducible), generar normales por Box-Muller, aplicar `FDD_FISICA.sigma_ruido` —que ya
está exportado— a los campos `med_*` de la malla, y **recalcular los once residuos en el
navegador**. Esto obliga a tener `t_rocio` y `t_burbuja` en JavaScript: se podrían
interpolar de `FDD_FISICA.campana_saturacion`, que ya viaja, pero eso introduce un segundo
error de interpolación que habría que medir contra CoolProp y declarar.
**Costo: 10 – 16 h**, más el riesgo de que la equivalencia exacta con scikit-learn —que hoy
es bit a bit— deje de ser verificable en el mismo sentido.

**Opción B — ruido en Python, exportado como un segundo bloque (recomendada).** El
exportador emite, además del bloque limpio, un bloque `res_ruidoso_*` calculado en Python
con ruido de sensor y discrepancia modelo-planta a una semilla declarada y exportada.
`diagnosticar()` clasifica el bloque ruidoso y devuelve el limpio para el diagrama P-h.
Python sigue siendo el único lugar donde se calculan residuos, así que no hay riesgo de
divergencia. Costo en tamaño: 11 arreglos × 4 620 nodos ≈ **+0,4 MB** sobre los 5,25 MB
actuales (+8 %).
**Costo: 5 – 8 h.**

En ambos casos:

6. `diagnosticar()` devuelve `{semilla, factor_ruido, nivel_discrepancia}` junto al
   diagnóstico, para que la página pueda mostrar de qué condiciones habla.
7. La interfaz ofrece el mismo punto **con y sin ruido**, que es pedagógicamente lo mejor
   que tiene este módulo: muestra en vivo por qué el F1 macro cae de 0,82 a 0,76.

**Decisión que corresponde al proyecto, no a mí:** A o B. Mi recomendación es **B**, por la
regla que el proyecto ya adoptó para `celda_bilineal` —que la decisión viaje como dato y no
se reimplemente en dos lenguajes—, y porque 0,4 MB es barato comparado con 10–16 h y un
segundo error de interpolación sin medir.

### 7.3 Hallazgo adicional — rechazar los nodos sin estado estacionario

Imprescindible, y más corto que los dos anteriores:

8. `diagnosticar()` comprueba `estado.convergio` **antes** de clasificar y devuelve
   `{estado, residuos: null, diagnostico: null, motivo: "sin estado estacionario"}`.
9. `probabilidades()` valida la entrada: si alguna característica no es un número finito,
   lanza en lugar de dejar que `Math.fround(null)` la convierta en 0. Un fallo ruidoso es
   preferible a un «sano» con 0,348 de confianza.
10. Prueba nueva: tomar un nodo con `convergio = 0` de la malla real —hay 189— y comprobar
    que `diagnosticar` no devuelve clase.

**Costo: 1 – 2 h.**

### 7.4 Orden sugerido y costo total

| Orden | Trabajo | Horas |
|---|---|---|
| 1.º | Hallazgo adicional (§7.3) — el más grave y el más corto | 1 – 2 |
| 2.º | Defecto 2 (§7.1) | 3 – 5 |
| 3.º | Defecto 3, opción B (§7.2) | 5 – 8 |
| | **Total** | **9 – 15 h** |

Ninguno de los tres toca `src/ciclo.py` ni el modelo entrenado, así que **no requieren
reentrenar** y son independientes de la decisión sobre el equipo de estudio. El defecto 1
sí vive en el solver y queda fuera de este plan, porque el encargo no lo pidió.

---

## 8. Todo lo que contradice este encargo o la documentación del proyecto

Ocho puntos, del más importante al menos.

**C1. «La física NO se ha reescrito para aire» — es cierto solo a medias.** Existe y está
implementada una topología de evaporador de aire: `expansion_directa`, declarada en
`src/topologia.py`, seleccionable con una línea (`config/params.py:29`), con su rama de
lado secundario en `src/ciclo.py:246`–`249`, su preset completo de parámetros
(`config/params.py:186`–`196`), su catálogo de 10 clases (`src/fallas.py:47`–`53`,
`118`) y sus residuos de lado aire (`src/features.py:40`–`41`). Converge y da resultados
razonables a temperaturas de aire acondicionado. Lo que **no** existe es física de
**congelador**: ni latente, ni escarcha, ni desescarche, y con un piso de −25 °C en la
temperatura de evaporación. La frase correcta no es «no hay física de aire» sino **«hay
física de aire a temperaturas de A/C; no hay física de baja temperatura»**. La diferencia
importa para estimar el esfuerzo: parte del camino está hecho.

**C2. El R-404A no aparece en ninguna parte del proyecto, pero eso no lo convierte en un
cambio de configuración.** El refrigerante es un campo de dataclass y CoolProp lo conoce, así
que *parece* un cambio de una línea. Medido, no lo es: a −25 °C el solver no converge, y con
el piso bajado a mano converge entregando 817 W de un serpentín de 17 584 W (§6.0). **El
rango declarado del equipo nuevo, −40 a 0 °F, es inalcanzable con el código actual**, y la
mitad superior de ese rango (0 a −18 °C) converge pero con parámetros de un equipo de A/C
de 5 TR, no del Heatcraft.

**C3. La especificación promete un cambio de equipo que el código no puede cumplir.**
`ESPEC_Simulacion_FDD.md:32`–`33` dice: *«El modelo de expansión directa aire-aire se
conserva como topología seleccionable: si el acceso a la enfriadora se complica, el proyecto
cambia de equipo de estudio con una línea de configuración.»* Esa promesa se escribió
pensando en un equipo de **aire acondicionado** aire-aire —y para ese caso es
aproximadamente cierta—. Para un **congelador de baja temperatura con desescarche** es
falsa, y las horas de §6 son la medida de cuánto. La especificación debería corregirse para
decir de qué equipo habla la promesa.

**C4. `diagnosticar` declara «sano» los nodos sin estado estacionario.** No estaba en la
lista de tres defectos y es más grave que el defecto 2:
`Math.fround(null) = 0` convierte los 189 nodos con `convergio = 0` en vectores de once
ceros, es decir en máquinas perfectamente sanas, y el bosque responde `sano` con confianza
0,348 (verificado en vivo, §4). Entre esos 189 hay 18 a carga plena y 15 a carga 0,95: **no
es un problema confinado a la zona de carga baja**, al contrario de lo que podría sugerir la
nota del README.

**C5. El README afirma que la malla de carga ≥ 0,34 no está afectada por el defecto 1, y hay
29 nodos que lo contradicen.** `README.md:259`–`261` dice: *«El resto de la malla
(carga ≥ 0,34) no está afectado.»* Contados sobre `web/datos/fdd_malla.js`, hay **29 nodos a
carga exactamente 0,34** con `ciclado = 1` y `y_capacidad` entre 0,2431 y 0,2500, es decir
por debajo del mínimo de 0,25, en 9 de las 11 clases y a 24 y 26 °C. El rebase es pequeño
(hasta 0,007) y la afirmación es casi cierta, pero tal como está escrita es falsa en la
frontera. Debería decir «carga > 0,34» o declarar el margen.

**C6. Cinco pruebas no se pueden correr en un clon limpio.** `156 passed, 5 errors`; los
cinco errores son `FileNotFoundError` de `resultados/modelo_rf.joblib`, excluido por
`.gitignore` porque pesaba 244 MB frente al límite de 100 MB de GitHub. Son precisamente las
cinco que verifican la **equivalencia exacta entre el JavaScript y scikit-learn**. El
resultado existe y está declarado (1 997 muestras, diferencia máxima 0,000e+00), pero hoy
**no es reproducible desde el repositorio** sin reentrenar primero. El README no advierte de
esto en la sección de pruebas.

**C7. `V_agua_ev` se llama como un caudal volumétrico y contiene un caudal másico en kg/s.**
Se escribe desde `sec["m_ev"]` (`src/ciclo.py:610`) y se consume multiplicado por `cp`
(`src/features.py:119`–`123`). El uso es consistente y **no hay error numérico**, pero en la
hoja de campo el nombre invita a anotar m³/h donde se esperan kg/s. Lo mismo vale para
`V_agua_cd` y `V_air_ev`.

**C8. El `README.md` describe el defecto 1 con un caso concreto que no pude reproducir
exactamente, aunque el fenómeno sí está.** El README cita carga 0,28 a 30 °C con
`y = 0,214`; en la malla exportada el nodo de 0,34 a 24 °C da 0,2487 y los de la banda baja
dan valores diversos. No contradigo la cifra —puede provenir de una sonda directa al solver y
no de la malla—, pero **no es verificable desde los artefactos del repositorio**. Para
determinarlo haría falta correr el solver en ese punto exacto, que es trabajo de la
corrección del defecto 1, no de esta auditoría.

### Lo que NO contradice nada, y conviene afirmar

- Las métricas reportadas son defendibles y están **limpias del defecto 1**: cero filas con
  `ciclado`, cero con `Q_load_frac < 0,40`, cero con `y < y_min` (§3.2).
- El conjunto de prueba se abrió una vez por conjunto, con motivo registrado, y
  `corrida_valida = true`.
- La partición por grupos no comparte ninguna condición de contorno entre particiones.
- El visualizador carga y funciona bajo `file://` con **cero dependencias externas** y
  **cero errores de página** (§5.1).
- Los 29 parámetros provisionales están marcados como tales, con su fuente declarada.
- El desacuerdo entre la malla limpia y el modelo entrenado con ruido **está documentado como
  dato** en `FDD_FISICA.nota_ruido`; lo que falta es que el código actúe en consecuencia.

---

## 9. Qué haría falta para cerrar los «no determinable»

| Pregunta sin respuesta | Qué haría falta |
|---|---|
| Tiempo de corrida completa del pipeline | Instrumentar `src/generador.py` y `src/modelo.py` con `perf_counter` y registrarlo en los JSON, o correr el pipeline entero cronometrado |
| Sesgo exacto del defecto 3 sobre la malla | Reentrenar, o generar un conjunto limpio y evaluar el modelo guardado sobre él. Requiere el `.joblib` de C6 |
| Si el caso del README (0,28 / 30 °C / y = 0,214) se reproduce | Correr el solver en ese punto exacto, dentro del trabajo de corrección del defecto 1 |
| Parámetros reales del Heatcraft MOH019L63CF | Catálogo del fabricante y placa del equipo; hoja `Registro Campo` de la Fase 1 |
| Si el desescarche se modela o se declara fuera de alcance | Decisión del proyecto. Mueve la estimación de §6.2 en unas 15 h |
