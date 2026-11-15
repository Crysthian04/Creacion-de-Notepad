# Qué cambió en la tercera ronda

Sin reentrenar. El modelo, los datasets y `resultados/metricas.json` son los mismos.

## Resumen

| # | Pedido | Qué se hizo |
|---|---|---|
| 1 | Guardar las métricas que faltaban en el JSON | Tres bloques nuevos, cada valor con archivo, clave, función y commit |
| 2 | Regenerar desde árbol limpio | `arbol_git_limpio_al_generar = true` en la corrida final |
| 3 | Corregir `carga_baja` en 0,25–0,35 | Era **0,82**, no «supera el 90 %»; «seis clases» era falso |
| 4 | Criterio de «bien diagnosticadas» | **F1 ≥ 0,80 en los dos escenarios**, usado igual en (g) y en el pie de la fig. 4 |
| 5 | Persistencia | Modelo declarado; recomendación de N sustituida por umbrales de costo; precisión siempre con cobertura |
| 6 | Origen de 4,3 y 14,6 psig | CoolProp 8.0.0, **rocío** (Q = 1), con el contraste de burbuja |
| 7 | ¿Es `8764236` el commit correcto? | **Sí, pero engaña**: es el último que tocó el archivo, no el que define la lista blanca |
| 8 | Separar lo interno | `NOTAS_INTERNAS.md`; `FDD_informe.md` queda sin una sola referencia al encargo |
| 9 | Separador decimal | **Coma**, en ejes, leyendas, títulos y anotaciones de las seis figuras |

---

## 1. Lo que ahora guarda `export_informe/metricas.json`

Tres claves nuevas, todas con su `origen`:

- **`por_nivel_de_severidad`** — detección y diagnóstico por nivel, en los dos conjuntos:

  | Conjunto | Nivel | n | Detección | Diagnóstico |
  |---|---|---|---|---|
  | Prueba sellada | incipiente | 610 | **0,6951** | **0,4770** |
  | Prueba sellada | moderada | 610 | 0,9262 | 0,8131 |
  | Prueba sellada | severa | 594 | 0,9848 | 0,9579 |
  | Prevalencia | incipiente | 1 095 | **0,7215** | **0,5142** |
  | Prevalencia | moderada | 1 082 | 0,9399 | 0,8669 |
  | Prevalencia | severa | 1 044 | 0,9808 | 0,9464 |

  Lleva además un campo `aviso` que advierte de no confundirlas con las del estudio de
  sensibilidad (0,7882 y 0,4824), y un campo `modelo_usado` que dice cuál se empleó en cada
  conjunto.

- **`cotas_de_referencia`** — F1 macro sin discrepancia (**0,8270** balanceado) y prevalencia sin
  `class_weight` (**0,5851**), con el comando que produce cada artefacto.

- **`estudios_de_sensibilidad`** — las dos tablas de barrido y las repeticiones, bajo un `aviso`
  que recuerda que son otro protocolo y que su caso base propio es 0,7572.

## 3. La corrección de `carga_baja`

Tenías razón. El texto decía que `carga_baja`, `condensador_sucio` e `incondensables` «superan el
90 % ya en severidad 0,25–0,35». Los valores reales en ese tramo son **0,82**, **0,90** y **0,90**:
ninguno *supera* 0,90, dos lo alcanzan exactamente y `carga_baja` se queda en 0,82. Y «seis clases
avisan temprano» no tenía respaldo: el párrafo solo nombraba tres.

Ahora el texto fija un umbral explícito —**≥ 0,80 de acierto en el tramo 0,25–0,35**— y dice que lo
cumplen **tres** clases, con sus cifras. Corregido igual en el pie de la figura 5.

## 4. El criterio de «bien diagnosticada»

**F1 ≥ 0,80 en los dos escenarios**, balanceado y prevalencia. Exigir los dos es deliberado: una
clase puede ir bien en el balanceado y hundirse en prevalencia, y entonces no sirve en campo.

| Grupo | Clases |
|---|---|
| Bien diagnosticadas (4) | `carga_baja`, `condensador_sucio`, `incondensables`, `caudal_agua_bajo` |
| Solo en balanceado (2) | `txv_sobrealimenta` (0,8844 / 0,2685), `compresor_desgastado` (0,8218 / 0,5158) |
| No utilizables (5) | `incrustacion_evaporador`, `sobrecarga`, `restriccion_linea_liquido`, `txv_restringida`, `sano` |

El mismo criterio, con las mismas tres categorías, aparece ahora en (g) y en el pie de la figura 4.

## 5. Persistencia

- **Modelo declarado**: `modelo_balanceado`, el de `class_weight='balanced'`, que es el mismo con el
  que se evalúa la prevalencia realista. Queda escrito en el informe y en
  `resultados/persistencia.json` → `modelo_usado`.
- **La recomendación de N = 3 se retiró.** En su lugar, los umbrales de la razón de costos
  **r = coste de una falla no detectada / coste de una inspección en vano**:

  | Comparación | El N mayor gana mientras… |
  |---|---|
  | N = 2 frente a N = 1 | r < **6,63** |
  | N = 3 frente a N = 2 | r < **4,88** |
  | N = 5 frente a N = 3 | r < **2,17** |

  Con r < 2,17 conviene N = 5; entre 2,17 y 4,88, N = 3; entre 4,88 y 6,63, N = 2; por encima de
  6,63, una sola lectura. **Fijar r es decisión del plan de mantenimiento, no del módulo.**
- **Precisión y cobertura siempre juntas**: de N = 1 a N = 3, precisión 0,4731 → 0,9448 **con**
  cobertura 0,7727 → 0,6594.

## 6. De dónde salen 4,3 y 14,6 psig

**CoolProp 8.0.0**, `PropsSI('P', 'T', T, 'Q', 1, 'R404A')` — **presión de rocío**, convertida a
manométrica restando 101 325 Pa. Rocío y no burbuja porque el manómetro de succión lee a la salida
del evaporador, donde el refrigerante es vapor saturado o recalentado.

| T | Burbuja | Rocío | Deslizamiento |
|---|---|---|---|
| −40 °C | 4,9 psig | **4,3 psig** | 0,72 K |
| −30 °C | 15,4 psig | **14,6 psig** | 0,66 K |

La conclusión sobre el fondo de escala de 300 psig no cambia con ninguna de las dos convenciones.

## 7. Sobre el commit `8764236`

**Es correcto en sentido literal y engañoso en sentido práctico.** Es el último commit que tocó
`src/features.py`, que es lo que devuelve `git log -1 -- <archivo>`. Pero lo que `8764236` añadió
fueron 29 líneas con la tabla de unidades de los residuos, para las figuras de este informe.
**La función `columnas_residuos` —la lista blanca propiamente dicha— no cambia desde `cd5f1db`.**

El JSON mantiene `8764236` porque describe el estado del archivo, y el informe gana una nota que
dice que quien quiera auditar la lista blanca debe mirar `cd5f1db`.

## 8. Qué se sacó del informe

`FDD_informe.md` ya no contiene **ninguna** referencia al encargo (verificado: 0 ocurrencias). Se
movió a `NOTAS_INTERNAS.md`:

- la nota de procedencia del nombre «KFC San Francisco»;
- la sección «Comparación con los valores citados en el encargo»;
- el anexo de correcciones a las premisas de partida.

Los recuadros que decían «Corrección a la premisa del encargo» se reformularon como notas de estado
—«corregido el 10 de noviembre», «nota sobre un resultado anterior»— porque la información técnica
sí pertenece al anexo; lo que no pertenece es la referencia a quién se equivocó.

## 9. Separador decimal: coma

En ejes, leyendas, títulos y anotaciones de la matriz de confusión. matplotlib no lo hace solo: hay
un formateador propio, `dec()`, y un `FuncFormatter` por eje. Las seis figuras lo usan.

---

## Verificación

- **Figuras deterministas:** regeneradas, salen byte a byte idénticas entre corridas consecutivas.
- **Comprobación 1e-12 intacta:** no abortó.
- **Árbol limpio:** la corrida final se hizo con `git status --porcelain` vacío, y el JSON lo
  registra en `procedencia.arbol_git_limpio_al_generar`.
- **Sin reentrenar:** `resultados/metricas.json`, `resultados/modelo_rf.joblib` y los `.parquet` no
  se tocaron.
