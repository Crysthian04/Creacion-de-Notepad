# Notas internas del módulo FDD

**No forma parte del Anexo H.** Este archivo guarda la trazabilidad entre `FDD_informe.md` y el
repositorio: de dónde sale cada cifra cuando alguien la recordaba distinta, qué premisas de partida
no coincidían con el código, y cómo se resolvió cada una. Sirve para defender el informe si alguien
pregunta «¿y esta cifra que yo tenía anotada?», y para que la próxima ronda no repita el trabajo.

El documento que va al informe es `FDD_informe.md`. Este no.

---

## Procedencia del nombre del sitio

El nombre **«KFC San Francisco» no aparece en ningún archivo de texto del módulo FDD**. Se comprobó
con una búsqueda sobre todo el repositorio: las únicas coincidencias son secuencias de bytes dentro
de `.png` y `.parquet`, no texto. El nombre procede del encargo de exportación, no del código ni de
la documentación del módulo.

Lo que el módulo sí documenta es el equipo modelado —una enfriadora de agua de 100 TR con R-134a— y
que **no es el equipo del local**. Eso sí está en el informe, sección (c), porque es una limitación
técnica y no una nota de procedencia.

---

## Comparación con los valores citados en el encargo

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

## Resumen de las correcciones a las premisas de partida

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


---

## Historial de rondas

| Ronda | Fecha | Qué se resolvió |
|---|---|---|
| 1 | 15 nov 2026 | Exportación inicial; ocho correcciones a las premisas de partida |
| 2 | 15 nov 2026 | Separación de conjuntos, estudio de persistencia, etiquetas en español |
| 3 | 15 nov 2026 | Métricas por nivel en el JSON, criterios explícitos, informe listo para el Anexo H |

El detalle de las rondas 2 y 3 está en `CAMBIOS_RONDA_2.md` y `CAMBIOS_RONDA_3.md`.
