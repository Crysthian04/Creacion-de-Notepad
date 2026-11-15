
---

## Figuras

Seis archivos PNG a **300 dpi**, con los nombres de clase en español legible en `export_informe/figuras/`, generados por
`python -m src.figuras_informe` (módulo introducido en el commit `789bda7`) a partir de
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
> función `src.modelo.evaluar`; dibujada por `src.figuras_informe.fig_matriz` (commit `789bda7`, el que introdujo ese módulo).

### Figura 2 — `fig2_matriz_confusion_prevalencia.png`

> **Figura 2.** Matriz de confusión sobre el conjunto de prevalencia realista (n = 9 964), donde el
> 67,67 % de las muestras son máquina sana, normalizada por fila. Comparada con la Figura 1, la
> diagonal se mantiene —el modelo no empeora— pero la interpretación cambia: con una clase
> dominante, los pocos falsos positivos de las clases raras destruyen su precisión. Es la figura que
> hay que mirar para estimar la carga de órdenes de trabajo en vano.
>
> *Origen:* `resultados/metricas.json` → `metricas.prevalencia_realista.matriz_confusion_normalizada`;
> modelo con `class_weight='balanced'` (`src/modelo.py:674`–`679`); función `src.modelo.evaluar`;
> dibujada por `src.figuras_informe.fig_matriz` (commit `789bda7`, el que introdujo ese módulo).

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
> dibujada por `src.figuras_informe.fig_pr` (commit `789bda7`).

### Figura 3b — `fig3b_curvas_pr_prevalencia.png`

> **Figura 3b.** Las mismas curvas sobre el conjunto de prevalencia realista.
> **PR-AUC macro = 0,7205.** La caída respecto de la Figura 3a no se debe a que el modelo empeore,
> sino a que la línea base de cada clase es su propia prevalencia: una clase que aparece el 0,3 % de
> las veces parte de una precisión base de 0,003.
>
> *Origen:* igual que la Figura 3a, sobre `data/dataset_prevalencia.parquet` y el modelo con
> `class_weight='balanced'` (commit `789bda7`).

### Figura 4 — `fig4_f1_por_clase.png`

> **Figura 4.** F1 por clase en los dos escenarios, ordenado de menor a mayor según la prueba
> balanceada. Las líneas discontinuas marcan el F1 macro de cada escenario (0,7543 y 0,5835).
> Aplicando el criterio de la sección (g) —**«bien diagnosticada» = F1 ≥ 0,80 en los dos
> escenarios**—, la figura separa tres grupos: **cuatro clases bien diagnosticadas**
> (`carga_baja`, `condensador_sucio`, `incondensables`, `caudal_agua_bajo`), **dos que solo
> funcionan en el balanceado** (`txv_sobrealimenta`, `compresor_desgastado`) y **cinco no
> utilizables**, entre ellas la clase sana. El contraste entre las dos barras de una misma clase
> mide cuánto castiga la prevalencia realista a las clases raras: `txv_sobrealimenta` cae de 0,8844
> a 0,2685.
>
> *Origen:* `resultados/metricas.json` → `metricas.*.f1_por_clase`; función `src.modelo.evaluar`;
> dibujada por `src.figuras_informe.fig_f1_por_clase` (commit `789bda7`). **Esta figura no existía en
> el pipeline; se añadió para este informe.**

### Figura 5 — `fig5_deteccion_por_severidad.png`

> **Figura 5.** Fracción diagnosticada correctamente frente a la severidad de la falla `f`, por
> clase, sobre el conjunto de prueba balanceado. Solo clases con falla: la clase sana no tiene
> severidad. Es la figura que decide si el método sirve para mantenimiento **predictivo**: una curva
> que solo sube al final significa que la falla se detecta cuando ya es grave.
> `restriccion_linea_liquido` es el caso extremo —0,03 / 0,03 / 0,00 en los tres primeros tramos y
> 1,00 desde 0,65—, con explicación física declarada: por debajo de ese umbral la caída de presión
> no basta para que el líquido flashee. En el otro extremo, tomando **≥ 0,80 de acierto en el tramo
> 0,25–0,35** como umbral de «avisa temprano», lo cumplen tres clases: `condensador_sucio` (0,90),
> `incondensables` (0,90) y `carga_baja` (0,82). Ninguna *supera* 0,90 en ese tramo.
>
> *Origen:* aciertos del conjunto sellado cruzados con `severidad_f`; equivale a
> `resultados/metricas.json` → `deteccion_vs_severidad` (función
> `src.modelo.fig_deteccion_vs_severidad`); recalculada y dibujada por
> `src.figuras_informe.fig_deteccion` (commit `789bda7`).

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
