# Auditoría de los scripts previos de Random Forest

**Proyecto:** Plan Integral de Mantenimiento — Sistema de Refrigeración y Aire Acondicionado
**Curso:** Mantenimiento de Sistemas de Refrigeración y A/A (0251) — UTP, Facultad de Ingeniería Mecánica
**Fase:** Fase 5 — Monitoreo e Innovación · Etapa 1 (auditoría previa a la implementación)
**Fecha:** 2 de septiembre de 2026

**Archivos auditados:**

| Alias | Archivo | Contenido |
|---|---|---|
| v1 | `Codigo de AI.txt` | Pipeline Árbol de Decisión + Random Forest con SMOTE y `GridSearchCV` (121 líneas) |
| v2 | `Codigo de AI 2.0.txt` | Pipeline Árbol de Decisión + Random Forest con exportación a Word (133 líneas) |

**Objetivo:** determinar qué se conserva y qué se descarta de estos dos scripts antes de construir el
pipeline de detección y diagnóstico de fallas (FDD) descrito en `ESPEC_Simulacion_FDD.md`.

---

## Nota previa sobre el dataset

`Predictive.csv` no está adjunto a esta auditoría. Por los nombres de columna que los scripts
referencian (`Machine failure`, `TWF`, `HDF`, `PWF`, `OSF`, `RNF`, `Product ID`, `UDI`) se trata del
**AI4I 2020 Predictive Maintenance Dataset** (10 000 filas, aproximadamente 3,4 % de fallas).

Todo lo que este informe afirma sobre el *contenido* de las columnas parte de esa identificación. Si
el CSV resultara ser otro, cambiarían los defectos **D1** y **D2**; el resto de los hallazgos se
sostiene solo con el código.

---

## 1. Tabla comparativa

| Aspecto | v1 (`Codigo de AI.txt`) | v2 (`Codigo de AI 2.0.txt`) | Mejor |
|---|---|---|---|
| Exclusión de columnas con fuga | Elimina `TWF, HDF, PWF, OSF, RNF` (L44) | **No las elimina** (L72) | **v1** |
| Codificación de categóricas | `get_dummies(drop_first=True)` (L41) | `LabelEncoder` en bucle sobre todo `object` (L33-35) | **v1** (ninguna es correcta, pero one-hot no inventa orden) |
| Eliminación de identificadores | No elimina `UDI`; expande `Product ID` en one-hot | No elimina `UDI` ni `Product ID` | Empate (ambas fallan) |
| Desbalance de clases | SMOTE solo en train (L51-52) | Nada: ni SMOTE ni `class_weight` | **v1** |
| Búsqueda de hiperparámetros | `GridSearchCV`, cv=5, ambos modelos (L58-59, L92-93) | Ninguna; valores fijos (L79, L106) | **v1** |
| Métrica de optimización | `scoring='accuracy'` (L59, L93) | No aplica | Ninguna (v1 mal, v2 ni siquiera busca) |
| Estratificación de la partición | No (L48) | No (L76) | Empate (ambas fallan) |
| Conjunto de validación separado | No (test usado para selección y reporte) | No | Empate (ambas fallan) |
| Semilla | `random_state=42` en split, SMOTE y modelos (L48, 51, 55, 89) | `random_state=42` en split y modelos (L76, 79, 106) | Empate (correcto en ambas) |
| Métricas reportadas | accuracy + `classification_report` + matriz (L73-86, L107-120) | Igual, pero encabeza con accuracy (L86, L113) | **v1** por poco |
| Matriz de confusión | Con `xticklabels` / `yticklabels` legibles (L82, L116) | Sin etiquetas de clase (L92, L119) | **v1** |
| Salida de figuras | `plt.show()` — inservible fuera de notebook (L35, 86, 120) | `savefig` + `close` (L64-65, 98-99, 125-126) | **v2** |
| Informe automatizado | Ninguno | `python-docx` completo (L12-14, 41-69, 84-133) | **v2** |
| Reproducibilidad del entorno | Sin versiones fijadas, sin hash del dataset | Igual, más `!pip install` embebido (L2) | Empate (ambas fallan) |

---

## 2. Defectos metodológicos, ordenados por gravedad

### D1 — CRÍTICO · Fuga de objetivo en v2

`Codigo de AI 2.0.txt`, líneas 72-73:

```python
X = df.drop('Machine failure', axis=1)   # Features
y = df['Machine failure']                # Target
```

`X` conserva `TWF`, `HDF`, `PWF`, `OSF` y `RNF`. En el AI4I 2020 la etiqueta `Machine failure` se
construye como disyunción de los modos de falla: si alguno de ellos vale 1, la etiqueta vale 1
(`RNF` es el modo aleatorio y, según la documentación del dataset, no siempre propaga a la
etiqueta).

El modelo no aprende física de la máquina: aprende un OR lógico que ya tiene en la entrada.
Cualquier exactitud o F1 que reporte v2 (L113) es **artefacto de la fuga, no desempeño**. Un árbol de
decisión sin podar sobre esas columnas alcanza cerca del 100 % con dos o tres nodos.

> Si en su momento la v2 dio métricas casi perfectas frente a la v1, esta es la explicación completa.

La v1 resuelve esto bien y de forma explícita en la línea 44.

---

### D2 — CRÍTICO · Identificadores sin contenido informativo, en ambas versiones

**v2, línea 72:** `UDI` (índice de fila 1…10000) y `Product ID` (identificador único de pieza, con
unos 10 000 valores distintos) entran como características. En el AI4I las filas están ordenadas por
proceso, así que `UDI` funciona como proxy temporal y el árbol puede cortar sobre él.

**v1, línea 41:**

```python
df = pd.get_dummies(df, drop_first=True)
```

Se aplica a *todo* el DataFrame **antes** de separar `X`. Como `Product ID` es de alta cardinalidad,
esta línea expande el espacio de características en miles de columnas dummy —una por pieza, cada una
con una sola fila en 1—. Además, `UDI` sobrevive dentro de `X` porque la línea 44 no lo elimina.

Es un defecto de la misma familia que D1: el modelo recibe la identidad de la fila. **Ninguna de las
dos versiones elimina `UDI`. Ninguna trata `Product ID` como lo que es: una llave, no una variable.**

#### Consecuencia sobre el SMOTE de la v1 (interacción D2 × D3)

Hay un efecto de segundo orden que conviene desarrollar, porque explica un resultado observado y no
solo un riesgo teórico.

SMOTE genera cada muestra sintética interpolando linealmente entre una muestra minoritaria y uno de
sus *k* vecinos más cercanos, con la distancia euclídea como criterio de vecindad. En la v1 ese
remuestreo (L51-52) no opera sobre las cinco o seis variables de proceso —temperaturas, par,
velocidad de giro, desgaste de herramienta—, sino sobre el espacio expandido por `get_dummies`
(L41): **miles de columnas dummy, casi todas en cero, una por cada `Product ID`**.

En un espacio de esa dimensionalidad aparece el fenómeno de concentración de distancias: a medida
que crece el número de dimensiones, la distancia al vecino más cercano y la distancia al más lejano
tienden a igualarse, y el contraste relativo entre ambas tiende a cero. El concepto de «vecino más
cercano» pierde poder discriminante: el vecino que SMOTE elige deja de ser un punto genuinamente
parecido y pasa a ser prácticamente uno cualquiera del conjunto minoritario.

Las consecuencias son tres:

1. **Las muestras sintéticas dejan de ser plausibles.** La interpolación entre dos puntos que no son
   vecinos en ningún sentido físico produce combinaciones de par, velocidad y desgaste que no
   corresponden a ningún estado real de la máquina.
2. **Las columnas dummy también se interpolan.** Cada muestra sintética recibe valores fraccionarios
   —0,37 en la columna de una pieza y 0,63 en la de otra— sobre variables que solo admiten 0 o 1. El
   resultado no es una pieza: es una superposición de dos identificadores que no existe.
3. **El desbalance queda formalmente corregido y sustancialmente no.** El conteo de clases se iguala,
   pero lo que se agregó a la clase minoritaria es ruido estructurado, no información sobre la
   frontera de decisión.

Esto es, con alta probabilidad, la explicación de por qué el balanceo de la v1 no mejoró el
desempeño tanto como cabía esperar. El defecto no estaba en SMOTE ni en la decisión de balancear:
estaba en el espacio sobre el que SMOTE fue obligado a trabajar, heredado de la línea 41. Eliminar
`Product ID` antes del remuestreo habría dejado a SMOTE operando sobre las variables de proceso, que
es donde la interpolación entre vecinos sí tiene sentido.

**Lección para el proyecto nuevo:** un preprocesamiento defectuoso no se manifiesta necesariamente
como un error visible, sino como una técnica correcta que rinde por debajo de lo esperado sin causa
aparente. Es un modo de fallo silencioso y por eso conviene dejarlo documentado.

---

### D3 — GRAVE · SMOTE fuera del bucle de validación cruzada (v1)

`Codigo de AI.txt`, líneas 48-60:

```python
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

smote = SMOTE(random_state=42)
X_train_balanced, y_train_balanced = smote.fit_resample(X_train, y_train)
...
grid_search_tree = GridSearchCV(estimator=tree_model, param_grid=param_grid_tree, cv=5, scoring='accuracy')
grid_search_tree.fit(X_train_balanced, y_train_balanced)
```

El orden respecto a `train_test_split` **es correcto**: SMOTE toca solo el conjunto de entrenamiento
y el de prueba queda limpio. Ese punto está bien resuelto y conviene decirlo.

El defecto está un nivel más abajo: el remuestreo se ejecuta **antes** de entrar a `GridSearchCV`, de
modo que dentro de cada uno de los 5 pliegues hay muestras sintéticas interpoladas a partir de
vecinos que quedaron del otro lado del corte. El pliegue de validación contiene puntos derivados del
pliegue de entrenamiento, y por eso `best_params_` (L64 y L98) se elige contra un score de validación
cruzada optimista.

**Corrección:** usar `imblearn.pipeline.Pipeline([('smote', SMOTE(...)), ('clf', ...)])` como
estimador del grid, para que el remuestreo se ejecute dentro de cada pliegue. El mismo error se
repite en la línea 94 para el Random Forest.

---

### D4 — GRAVE · `scoring='accuracy'` sobre clases desbalanceadas (v1)

Líneas 59 y 93:

```python
grid_search_tree = GridSearchCV(..., cv=5, scoring='accuracy')
grid_search_rf   = GridSearchCV(..., cv=5, scoring='accuracy')
```

El grid corre sobre datos ya balanceados por SMOTE, así que la exactitud no es tan engañosa *dentro*
del grid. El problema es que la configuración así elegida se evalúa después sobre un conjunto de
prueba con ~3,4 % de positivos (L70-74 y L104-108), donde la exactitud sube sola. Se está optimizando
una métrica que no es la del problema.

**Corrección:** `scoring='f1_macro'` o `scoring='average_precision'`.

---

### D5 — GRAVE · `LabelEncoder` sobre variables nominales (v2)

Líneas 29-35:

```python
non_numeric_columns = df.select_dtypes(include=['object']).columns
for col in non_numeric_columns:
    le = LabelEncoder()
    df[col] = le.fit_transform(df[col])
```

Tres problemas en cuatro líneas:

1. `LabelEncoder` está documentado para el vector objetivo `y`, no para columnas de `X`.
2. Impone un orden aritmético falso: `Product ID` pasa a ser un entero 0…9999 y el árbol puede
   preguntar `Product_ID < 4823`, comparación sin significado físico.
3. Se aplica a ciegas a toda columna `object`, sin distinguir `Type` (L/M/H, que sí es ordinal y
   admitiría un mapeo explícito 0/1/2) de `Product ID` (nominal puro, que había que eliminar).

**Consecuencia colateral**, línea 58: `corr_matrix = df.corr()` incluye esos códigos inventados, así
que la matriz de correlación que se inserta en el informe Word (L68-69) contiene celdas sin
interpretación posible.

---

### D6 — MODERADO · Partición no estratificada, en ambas versiones

v1 línea 48 y v2 línea 76 llaman:

```python
train_test_split(X, y, test_size=0.2, random_state=42)
```

sin `stratify=y`. Con 3,4 % de positivos, la proporción de la clase minoritaria en el conjunto de
prueba queda librada al azar de la semilla. Falta también `shuffle` explícito en el `cv=5` de v1
(`GridSearchCV` con un entero usa `StratifiedKFold` sin barajar).

---

### D7 — MODERADO · No hay conjunto de validación; el test se usa para seleccionar y para reportar

En v1, `best_params_` sale de la validación cruzada sobre el train (L60 y L94), pero la comparación
final entre Árbol de Decisión y Random Forest (L74 frente a L108) se hace mirando el mismo conjunto
de prueba. Elegir el modelo ganador con el test convierte esa cifra en una estimación sesgada.

**Corrección:** partición 70/15/15 (entrenamiento / validación / prueba), como pide la sección 7.1 de
la especificación.

---

### D8 — MODERADO · v2 no trata el desbalance en absoluto

No hay SMOTE, no hay `class_weight='balanced'`, no hay ajuste de umbral. Con 3,4 % de positivos, el
`classification_report` de la línea 114 va a mostrar recall bajo en la clase 1 — enmascarado por la
exactitud de la línea 113, que es lo primero que el documento imprime.

---

### D9 — MODERADO · v2 rotula como «mejores parámetros» los parámetros por defecto

Líneas 85 y 112:

```python
doc.add_paragraph(f'Mejores parámetros: {dt_model.get_params()}')
doc.add_paragraph(f'Mejores parámetros: {rf_model.get_params()}')
```

No se ejecutó ninguna búsqueda de hiperparámetros. El informe Word afirma una optimización que no
ocurrió. Es un defecto de honestidad del reporte, no solo de código.

---

### D10 — MENOR · Reproducibilidad: la semilla está, el control del entorno no

Contra lo que suele suponerse, **ambas versiones fijan `random_state=42`** donde importa:

- v1: líneas 48, 51, 55 y 89
- v2: líneas 76, 79 y 106

Eso está bien y se conserva. Lo que falta en las dos:

- Sin `requirements.txt` ni versiones fijadas. La v2 resuelve dependencias con `!pip install
  python-docx` (L2), que instala la última versión disponible el día en que se corra.
- Sin registro de procedencia ni hash del CSV. Las rutas son frágiles y distintas entre versiones:
  `'/content/Predictive.csv'` (v1 L13) frente a `'Predictive.csv'` (v2 L26).
- `permutation_importance`, cuando se agregue, necesita su propio `random_state`.

---

### D11 — MENOR · Redundancia y fragilidad

- **v1, líneas 67 y 101:** `best_tree_model.fit(...)` y `best_rf_model.fit(...)` después del grid.
  `GridSearchCV` ya devuelve el estimador reentrenado sobre todo el train (`refit=True` por defecto);
  es cómputo duplicado.
- **v2, líneas 19-23:** la redirección de `sys.stdout` no está en `try/finally`. Si `df.info()`
  lanzara una excepción, la salida estándar quedaría apuntando al `StringIO` durante el resto de la
  sesión.
- **v1, líneas 35, 86 y 120:** usa `plt.show()`. El script no deja ninguna figura en disco, así que
  nada de lo que produce sirve para el informe sin volver a correrlo a mano.

---

## 3. Patrones que sí conviene conservar y reutilizar

1. **Estructura del `GridSearchCV`** (v1, L58-64 y L92-98): `param_grid` como diccionario, `cv=5`,
   lectura de `best_estimator_` y `best_params_`. Se reutiliza tal cual, cambiando
   `scoring='accuracy'` por `scoring='f1_macro'` y metiendo el estimador dentro de un `Pipeline`.

2. **`classification_report` por clase** (v1, L78 y L112): es exactamente lo que pide la sección 7.3
   de la especificación — recall y F1 por clase, nunca solo el promedio.

3. **Matriz de confusión con seaborn y etiquetas de clase** (v1, L81-86):

   ```python
   sns.heatmap(confusion_matrix(y_test, y_pred), annot=True, fmt="d", cmap='Blues',
               xticklabels=[...], yticklabels=[...])
   ```

   La versión de v1 es mejor que la de v2 justamente por las etiquetas; con 10 clases son
   imprescindibles. Se adapta a `normalize='true'` y `fmt=".2f"`.

4. **Módulo de exportación a Word de v2** (L12-14, L41-69 y L84-133): `Document()`,
   `add_heading(level=…)`, `savefig` → `add_picture(..., width=Inches(5.5))`. Es el patrón correcto y
   se traslada casi literal.

5. **`plt.savefig()` + `plt.close()` de v2** (L64-65, L98-99, L125-126) en lugar del `plt.show()` de
   v1: obligatorio para un pipeline por script. Se le agrega `dpi=300` para las figuras del informe.

6. **`capture_df_info()` de v2** (L18-23) como idea: llevar diagnósticos del dataset al documento
   automáticamente. Se reescribe con `contextlib.redirect_stdout`, que es a prueba de excepciones.

7. **`random_state=42` consistente en todo el pipeline** (ambas versiones): la disciplina ya está;
   solo hay que centralizarla en una constante única y declararla en el informe.

8. **Comparar un modelo simple contra el Random Forest** (v1, Árbol de Decisión frente a RF): buen
   reflejo metodológico. En el proyecto nuevo sirve como línea base, seleccionada con el conjunto de
   validación y no con el de prueba.

9. **Eliminación explícita y comentada de columnas con fuga** (v1, L44): el gesto correcto. En el
   proyecto nuevo se endurece hasta volverse la regla de usar únicamente columnas `res_*`.

---

## 4. Veredicto

> **La base es la v1**: es la única de las dos que excluye las columnas derivadas del objetivo, busca
> hiperparámetros y trata el desbalance. De la v2 se rescata únicamente el módulo de exportación a
> Word y el guardado de figuras a disco.

---

## 5. Traspaso a la Etapa 2

Tres reglas que esta auditoría traslada al pipeline nuevo. No son observaciones históricas: son
restricciones de diseño que el código debe hacer cumplir.

- **Regla 1 (deriva de D1 y D2) — lista blanca, nunca `drop`.** La regla «el clasificador se entrena
  solo con columnas `res_*`» de la especificación es la versión endurecida del defecto D1. La matriz
  de características se construye seleccionando explícitamente las columnas de residuos, no
  eliminando las no deseadas. La diferencia importa: un `drop` falla en silencio cuando alguien
  agrega una columna nueva al dataset, y esa columna entra al modelo sin que nadie lo note. Una lista
  blanca falla ruidosamente, que es como debe fallar.

- **Regla 2 (deriva de D3) — sin remuestreo sintético.** El defecto D3 **desaparece por
  construcción**: el conjunto balanceado de la sección 6.1 de la especificación se genera balanceado
  desde el simulador —10 clases × 3 niveles de severidad × 400 condiciones— y no necesita SMOTE.
  El desbalance del conjunto de prevalencia realista se trata con `class_weight='balanced'`, no
  fabricando muestras. SMOTE no entra al proyecto nuevo.

- **Regla 3 (deriva de D7) — el conjunto de prueba se toca una sola vez.** Esta es vinculante y hay
  que decirla sin ambigüedad:

  > La comparación entre el clasificador base y el Random Forest, y la elección de hiperparámetros,
  > se resuelven **exclusivamente con el conjunto de validación**. El conjunto de prueba se usa
  > **una sola vez, al final, para reportar** — nunca para decidir.

  Y, sobre todo, **debe quedar impuesto por la estructura del código, no confiado a la disciplina de
  quien lo corra**. Un comentario que diga «no mirar el test todavía» no es un control: es una
  intención. Mecanismos concretos que lo hacen estructural:

  - La función que selecciona el modelo recibe únicamente `(X_train, y_train, X_val, y_val)` en su
    firma. No tiene acceso léxico al conjunto de prueba, así que no puede evaluarlo aunque el código
    se modifique por descuido.
  - La partición devuelve los conjuntos de prueba en un contenedor sellado que la etapa de selección
    no abre; solo la función final de reporte lo hace.
  - La evaluación sobre el test se ejecuta en un único punto del pipeline, después de que el modelo
    ganador ya está congelado y serializado.
  - Un contador de accesos al conjunto de prueba, registrado en `resultados/metricas.json`. Si al
    terminar la corrida marca más de uno por conjunto, la corrida se declara inválida.

  El motivo de fondo es que en la v1 este defecto no produjo ningún síntoma visible: el número
  reportado se ve igual de bien esté sesgado o no. Los defectos que no se manifiestan son los que
  necesitan un control estructural, porque no hay revisión posterior que los detecte.

### Resumen de decisiones

| Del código anterior | Decisión |
|---|---|
| `Predictive.csv` como fuente de datos | **Se descarta** — se sustituye por el generador sintético |
| `LabelEncoder` aplicado indiscriminadamente | **Se descarta** (D5) |
| Selección de características por `drop` de columnas | **Se descarta** — se sustituye por lista blanca `res_*` (D1, D2) |
| SMOTE | **Se descarta** — innecesario con dataset balanceado por diseño (D3) |
| `scoring='accuracy'` | **Se descarta** — se sustituye por `f1_macro` (D4) |
| Estructura del `GridSearchCV` | **Se conserva y adapta** |
| `classification_report` | **Se conserva** |
| Matriz de confusión con seaborn | **Se conserva y adapta** (normalizada por fila) |
| Exportación a Word con `python-docx` | **Se conserva casi literal** |
| `savefig` + `close` en lugar de `show` | **Se conserva**, con `dpi=300` |
| `random_state` fijo | **Se conserva**, centralizado en una sola constante |

---

## 6. Referencias pertinentes a esta auditoría

- Breiman, L. (2001). Random forests. *Machine Learning, 45*(1), 5–32.
- Chawla, N. V., Bowyer, K. W., Hall, L. O., & Kegelmeyer, W. P. (2002). SMOTE: Synthetic minority
  over-sampling technique. *Journal of Artificial Intelligence Research, 16*, 321–357.
- Kaufman, S., Rosset, S., Perlich, C., & Stitelman, O. (2012). Leakage in data mining: Formulation,
  detection, and avoidance. *ACM Transactions on Knowledge Discovery from Data, 6*(4), 1–21.
  *(Marco formal del defecto D1.)*
- Pedregosa, F., Varoquaux, G., Gramfort, A., Michel, V., Thirion, B., Grisel, O., … Duchesnay, É.
  (2011). Scikit-learn: Machine learning in Python. *Journal of Machine Learning Research, 12*,
  2825–2830.
- Saito, T., & Rehmsmeier, M. (2015). The precision-recall plot is more informative than the ROC plot
  when evaluating binary classifiers on imbalanced datasets. *PLOS ONE, 10*(3), e0118432.
  *(Sustento de los defectos D4 y D8.)*
