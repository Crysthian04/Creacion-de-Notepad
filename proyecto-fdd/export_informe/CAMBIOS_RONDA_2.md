# Qué cambió en la segunda ronda

Sobre `export_informe/`, sin reentrenar. El modelo, los datasets y
`resultados/metricas.json` son los mismos de la primera ronda; lo que se añade son dos módulos de
análisis que **leen** el modelo guardado, y correcciones de texto.

## Resumen

| # | Pedido | Qué se hizo | Dónde |
|---|---|---|---|
| 1 | Separar prueba principal de estudios | Tabla comparativa nueva; encabezado de aviso en las tablas de robustez; la frase «0,757 a 0,820» sustituida | §(g) «Dos conjuntos distintos», §(g) robustez, §(d) |
| 2 | Explicar las repeticiones y quitar la afirmación | Explicado `por_corrida` vs `por_condicion`; afirmación retirada | §(g) robustez |
| 3 | Confirmar origen de 0,788 y 0,482 | Confirmado: estudio, no prueba principal. Equivalentes calculados | §(g) «Detección sano/no-sano» |
| 4 | Tasa de falsas alarmas en prevalencia | Tus dos cifras verificadas exactas | §(g) «Falsas alarmas» |
| 5 | Estudio de persistencia | Hecho empíricamente, con supuestos declarados | §(g) «Persistencia», `src/persistencia.py` |
| 6 | Instrumentación y hoja `Instrumentos` | Frase sustituida; procedencia de la hoja investigada | §(a), §(d) |
| 7 | Parámetros de catálogo sin ruta de calibración | Reescritas limitación 3 y §(a) | §(a), §(j) |
| 8 | Commits correctos | `8764236` → `789bda7` en las seis citas del módulo | §Figuras, `pies_de_figura.md` |
| 9 | Figuras con etiquetas en español | Diccionario documentado; rejilla horizontal quitada en fig4 | `src/figuras_informe.py` |
| 10 | `carga_baja` en la alarma de fuga | Revisión por clase, con justificación física | §(g) alarma, `metricas.json` |

---

## Detalle de lo que cambió de significado

### 3. Las cifras 0,788 y 0,482 no son de la prueba principal — y una de ellas es optimista

Confirmado archivo, clave, conjunto y función:

- **0,7882** = `resultados/metricas.json` → `sensibilidad_al_ruido["1.0"].deteccion_incipiente`
- **0,4824** = la misma clave, `.diagnostico_incipiente`
- Ambas calculadas por `src.modelo._entrenar_y_medir` (`src/modelo.py:502`–`514`) sobre el **split
  de validación** de un dataset de **120 condiciones** generado dentro del estudio, con un bosque
  **reentrenado dentro del estudio**.

Calculé los equivalentes sobre el conjunto de prueba sellado, con la misma definición:

| | Citado (estudio) | **Prueba principal** |
|---|---|---|
| Detección incipiente | 0,7882 | **0,6951** |
| Diagnóstico incipiente | 0,4824 | **0,4770** |

**La detección citada es 9,3 puntos optimista.** El diagnóstico está cerca.

### 4. Tus dos números son exactos

**2 430/6 743 = 0,3604** y **2 831/5 261 = 0,5381**, reproducidos desde la matriz de confusión.
Añadí también las fallas perdidas (390/3 221 = 0,1211) y la columna equivalente de la prueba
balanceada, donde la precisión del aviso es 0,9598 —muy distinta— precisamente porque allí las
clases están balanceadas.

### 5. La persistencia sí era viable, y da el resultado más útil del informe

No hizo falta suponer independencia **ni** resamplear: entre dos lecturas de la misma máquina en el
mismo punto solo cambia el ruido de instrumento, así que resolví el ciclo una vez por condición y
sorteé cinco vectores de ruido. La discrepancia modelo-planta ε **se mantiene fija**, que es lo
físicamente correcto: es calibración, no ruido.

**Validación:** la lectura 0 reproduce el dataset publicado con diferencia máxima **0,00e+00** sobre
9 964 condiciones. El módulo aborta si no lo logra.

| N | Falsa alarma | Si fueran independientes | Fallas perdidas | Precisión de la orden |
|---|---|---|---|---|
| 1 | 0,3604 | 0,3604 | 0,1211 | 0,4731 |
| 2 | 0,1548 | 0,1299 | 0,1860 | 0,8344 |
| **3** | **0,0817** | 0,0468 | **0,2173** | **0,9448** |
| 5 | 0,0334 | 0,0061 | 0,2639 | 0,9919 |

**Exigir tres lecturas sube la precisión de la orden de trabajo de 0,47 a 0,94.** Y la persistencia
ayuda **5,5 veces menos** de lo que predice multiplicar probabilidades, porque el error de
calibración es sistemático en cada punto. Supuestos declarados en el informe y en el JSON.

### 6. La hoja `Instrumentos`: no determinable, pero no puede ser la del KFC

El archivo **no está en el repositorio**; se cita en tres sitios y nada más. Pero el inventario
codificado **no puede ser el del local**:

1. Incluye `T_agua_in_ev`, `T_agua_out_ev` y `V_agua_ev` — tres instrumentos de un circuito de agua
   helada que un equipo de expansión directa no tiene.
2. El manómetro de succión está declarado a **300 psig de fondo de escala**. Un congelador con
   R-404A a −40 °C trabaja a **4,3 psig**; a −30 °C, a 14,6 psig. Con el 0,25 % de clase, ese
   instrumento daría un error absoluto mayor que la lectura.

### 10. `carga_baja` no es fuga, y una precisión

Tu cifra de F1 era 0,95; el valor exacto es **0,9477**, que **no** supera el umbral. Lo que sí lo
supera es su **PR-AUC, 0,9905**. Revisé las cuatro clases que pasan de 0,95 en alguna de las dos
métricas y todas tienen firma física única; la de `carga_baja` es la más clara: es la única clase
cuyo **subenfriamiento baja mientras el sobrecalentamiento sube**. La revisión viaja en
`metricas.json` → `alarma_de_fuga.revision_por_clase`, con un campo `todas_justificadas` que hoy
vale `true`. **Si alguna clase quedara sin justificar, habría que tratarla como fuga.**

---

## Una celda que no pude calcular

En la tabla de detección incipiente, el número de filas incipientes del estudio figura como
**«no disponible»**: el JSON guarda `n_filas = 3 921`, que es el dataset completo, no el tamaño del
split de validación ni cuántas de sus filas son incipientes. No se registra, y no quise citarlo sin
calcularlo.

## Archivos nuevos

| Archivo | Qué es |
|---|---|
| `src/persistencia.py` | estudio de persistencia; no reentrena, valida su propia reconstrucción |
| `resultados/persistencia.json` | su salida, enlazada entera en `export_informe/metricas.json` |
| `export_informe/CAMBIOS_RONDA_2.md` | este archivo |

## Verificación

- **Figuras deterministas:** regeneradas dos veces, las seis salen **byte a byte idénticas**.
- **Comprobación 1e-12 intacta:** `src/figuras_informe.py` sigue abortando si algún número difiere
  de `resultados/metricas.json`. No abortó.
- **Sin reentrenar:** `resultados/metricas.json`, `resultados/modelo_rf.joblib` y los `.parquet` no
  se tocaron en esta ronda.
