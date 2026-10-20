# Plan de mejoras del Recorrido integrado (v3 → v4)

Origen: un dictamen externo propuso 6 mejoras y 4 críticas. Aquí cada una queda filtrada contra las reglas de `CLAUDE.md`: se integra, se integra con cambios o se descarta, con la razón. Hazlas en el orden indicado. Cada mejora va en su propio commit y debe pasar `npm run check`.

> **Calendario.** La defensa es el 21/10/2026 y el modelo se usa 2–3 min en el cierre. La versión de la defensa es la v3 (`dist/` generado sin cambios). Una mejora solo entra a la defensa si está terminada, revisada en capturas y probada en la laptop de la presentación antes del 20/10 a las 22:00. Si no, queda para después.

---

## Ya resuelto en la v3 (no rehacer)

- **Fuga de refrigerante (Mejora 2 del dictamen).** La Parada 3 mostraba la fuga subiendo hasta 18 m. Ahora cae y se extiende a ras de piso, y la tarjeta cita (Honeywell, 2014). Código: `tick()` en `tour-layers.js`.
- **Empaquetado monolítico frágil (crítica).** Resuelto con este proyecto: fuentes legibles, `npm run build` reproducible y prueba de humo.

---

## Fase 1: integrar (bajo riesgo, alto valor para la defensa)

### 1.1 Tarjetas que caben en 1366×768
**Por qué.** Muchos proyectores trabajan a 1366×768. Ahí las tarjetas de las Paradas 2 y 3 se desbordan y hay que desplazarlas en plena exposición.
**Cómo.** Con `@media (max-height: 800px)` reduce la letra de `.card` (13 → 12 px), el `padding`, los `gap` y el ancho (`clamp(220px, 19vw, 280px)`). Si aun así no cabe, permite colapsar tarjetas: solo la primera abierta y las demás como encabezado clicable.
**Aceptación.** En `tests/smoke.mjs`, extiende el chequeo de desborde a 1366×768 (hoy solo aplica a 1920). Ninguna parada desborda más de 8 px a 1366×768.

### 1.2 Bombeo de agua helada (Mejora 3, con cambios)
**Qué dice el dictamen.** Falta la sala de bombas primaria/secundaria; el bombeo sería del "10–18 %" del consumo.
**Qué se integra.** Una estación de bombeo **genérica e ilustrativa**: dos bombas centrífugas en paralelo (una en operación y una de respaldo), con motor, voluta, válvulas de corte y un manómetro. Van en la tubería de suministro, entre el chiller y el edificio. Una zona libre aproximada: x ≈ −15.5, z ≈ −7.5 sobre `suministro_principal` en `hvac-model.js`. Confírmala con capturas: no debe tapar al técnico de la Parada 1 ni el punto de termografía.
**Qué NO se integra.**
- El "10–18 %" del consumo y la configuración primaria/secundaria: la fuente no los da.
- Un tanque de expansión o un separador de aire con nombre propio: más mallas sin aportar a la explicación.
**Etiqueta.** "Bombeo de agua helada", con subtítulo "Configuración ilustrativa: el estudio no la detalla" y sello `ilus`. Visible en la vista general y en la Parada 5. Agrega el grupo `bombeo_agua_helada` al foco de la Parada 5 (`FOCUS[5]` en `tour-app-v2.js`).
**Partículas.** Las partículas de suministro ya recorren `supplyPaths`. Si pasan por la bomba, mejor; no hace falta un efecto nuevo.
**Aceptación.** Menos de 40 mallas nuevas (cilindros de 12–16 segmentos). Sin etiquetas encimadas en las capturas 0 y 5.

### 1.3 Inspector por clic de los equipos (Mejora 4, con cambios)
**Qué dice el dictamen.** Clic en cada UMA para ver CFM, ΔP de filtros y agua de 7 °C / 12 °C.
**Qué se integra.** Un inspector con **solo datos honestos**:
- Clic (Raycaster con `pointerdown` y tolerancia de arrastre: si el puntero se movió más de 5 px, no es clic) sobre cualquier malla dentro de `UMA_01`…`UMA_16`, `chiller_155TR`, un `minisplit_*` o la nueva bomba.
- El equipo se resalta (emisivo o contorno con `EdgesGeometry`). En el panel derecho aparece una sección "Inspector":
  - **Identificación**: "UMA 07 · Primer alto" (el piso sale de `LAYOUT`, con sello `ilus` porque la distribución es ilustrativa).
  - **Dato real del conjunto** (sello `real`): "16 UMA · 38 % del consumo de climatización".
  - **Variables a monitorear (propuesta INV3)** (sello `ilus`): temperatura de suministro/retorno, ΔP del filtro, corriente del ventilador, vibración. **Sin valores.** Cada una muestra "Sin dato medido".
  - Chiller: "155 TR · enfriado por aire · 38 % del consumo de climatización" (`real`). Mini-split: "Inverter · 12,000–60,000 BTU/h" (`real`).
- `Esc` o clic en vacío cierra el inspector. Funciona en la vista general y en la Parada 5. En las otras paradas no hace nada, para no romper la narración.
**Qué NO se integra.** Lecturas numéricas ficticias (CFM, pulgadas de columna de agua, 7/12 °C), ni siquiera con el sello "Simulación". Para la audiencia, un número en pantalla es un dato.
**Aceptación.** Una prueba en `smoke.mjs` hace clic sobre la proyección de `UMA_03`, comprueba que el inspector muestra "UMA 03" y "Sin dato medido", y que `Esc` lo cierra. Los atajos 0–6 siguen funcionando.

---

## Fase 2: integrar después de la defensa (valor académico, más trabajo)

### 2.1 Vista termográfica cualitativa (Mejora 1, con cambios)
**Qué dice el dictamen.** Un shader Ironbow con gradiente de 6 °C a 28 °C.
**Qué se integra.**
- Un botón "Vista termográfica" en la vista general y en la Parada 5. Cambia los materiales de la escena por una paleta Ironbow (negro → azul → magenta → naranja → amarillo), usando una **temperatura relativa** asignada por clase de componente: suministro de agua helada = frío; retorno = algo menos frío; UMA y chiller = intermedio; fachada = según la irradiancia que ya calcula `sky-v2.js`; uniones con deterioro (`thermalPts`) = anomalía cálida.
- Implementación barata: un `ShaderMaterial` o `MeshBasicMaterial` con color calculado por componente, guardando y restaurando los materiales como ya hace `dimFor`/`restoreMats`. Sin posprocesado de pantalla completa.
- Barra de color con **"más frío ↔ más caliente", sin °C**, y la nota: "Representación cualitativa. El estudio reporta el deterioro detectado en una inspección termográfica, sin temperaturas en este modelo." Sello `ilus`; la anomalía en las uniones conserva su etiqueta `real`.
**Qué NO se integra.** Escala en °C ni "lectura cuantitativa": no hay temperaturas medidas.
**Coherencia.** El modelo "Herramientas HVAC" ya tiene una pestaña de termografía del Edificio 2. Usa la misma paleta y el mismo lenguaje.

### 2.2 Calculadora psicrométrica (Mejora 5, con cambios)
**Qué dice el dictamen.** En Panamá, del 45 al 60 % de la carga de una UMA es latente.
**Matiz.** Esa proporción se alcanza al enfriar **aire 100 % exterior** (ver la prueba de abajo: unos 61 %). En una UMA que recircula aire, la fracción latente es menor. La fuente no da la fracción de aire exterior del Edificio 2, así que no se puede afirmar para este edificio.
**Qué se integra.** En el panel "Clima y hora", una sección plegable "Calor sensible y latente" (sello `ilus`):
- Entradas que mueve el usuario: aire de entrada (T bulbo seco, HR) y aire de salida del serpentín (T, HR). Valores por defecto: 30 °C / 75 % → 13 °C / 100 %, con el rótulo **"valores de ejemplo, no medidos en el Edificio 2"**. Si se quiere un clima de Panamá real, se cita una climatología verificable (por ejemplo, IMHPA, estación Tocumen) o no se pone.
- Presión fija de 101.325 kPa (el campus está prácticamente al nivel del mar).
- Ecuaciones de ASHRAE Handbook—Fundamentals, cap. 1 (Psicrometría):
  - p_ws: Hyland-Wexler sobre agua líquida (ec. 6).
  - W = 0.621945 · p_w / (p − p_w), con p_w = HR · p_ws.
  - h = 1.006·t + W·(2501 + 1.86·t) [kJ/kg aire seco].
  - q_total = h₁ − h₂; q_sensible ≈ (1.006 + 1.86·W₁)(t₁ − t₂); q_latente = q_total − q_sensible.
- Salidas: W, h, punto de rocío, q_total, q_sensible, q_latente y el factor de calor sensible (SHR), por kg de aire seco.
- Va en un módulo aparte, `src/app/psychro.js`, con funciones puras.
**Prueba numérica obligatoria** (calculada con Hyland-Wexler; tolerancia ±0.5 %), en `tests/psychro.test.mjs` con `node --test`:

| Caso | p_ws (Pa) | W (kg/kg) | h (kJ/kg) |
|---|---|---|---|
| 30 °C, 75 % | 4,246 | 0.02018 | 81.78 |
| 25 °C, 50 % | 3,169 | 0.00988 | 50.32 |
| 13 °C, 100 % | 1,498 | 0.00933 | 36.64 |
| Proceso 30/75 → 13/100 | q_total 45.14 · q_sens 17.74 · q_lat 27.40 · SHR 0.393 | | |

**Qué NO se integra.** Que la calculadora mueva el consumo del chiller o la "carga" del edificio: no hay modelo de carga del Edificio 2.

### 2.3 Metadatos de equipos en la exportación GLB (crítica "falso BIM", con cambios)
**Valoración.** La crítica es parcialmente un hombre de paja: el modelo nunca se llama BIM; "Modelo BIM / Gemelo digital" aparece como **propuesta** con sello `ilus`. Aun así se puede mejorar de forma honesta.
**Qué se integra.** En cada equipo, `userData` con `{ ifcClass: 'IfcChiller' | 'IfcUnitaryEquipment' | 'IfcPump' | 'IfcPipeSegment', fuente: 'real' | 'ilustrativo' }`. El exportador GLB ya existente lo guarda en `extras`.
**Rótulo en el botón.** "Descargar GLB (con clases IFC como metadatos)".
**Qué NO se dice.** Que es un modelo BIM o un archivo IFC: no lo es (ISO 16739-1).

---

## Fase 3: demostración de detección de fallas con datos públicos (después de la defensa, opcional)

> No empieces esta fase hasta que Cristian lo pida expresamente. Va en la carpeta `analisis-fdd/`, separada del modelo 3D.

**Objetivo.** Mostrar, con datos reales y públicos, cómo un método de detección de anomalías encuentra fallas en equipos HVAC, como respaldo de la propuesta "Detección de anomalías" de la INV3. **No** es un diagnóstico del Edificio 2.

### 3.1 Datos (los aporta Cristian; no inventes ni sintetices)
- **Opción preferida, de acceso abierto:** base etiquetada de LBNL con equipos HVAC con y sin fallas, con datos de simulación, laboratorio y campo (Granderson et al., 2023, *Scientific Data*, 10, https://doi.org/10.1038/s41597-023-02197-w).
- **Opción alternativa:** ASHRAE RP-1043, un chiller centrífugo de 90 TR enfriado por agua, con fallas introducidas en 4 niveles de severidad (Comstock & Braun, 1999). Puede requerir acceso por ASHRAE.
- Los archivos van en `analisis-fdd/data/raw/` (fuera de git si pesan más de 50 MB). Si no están, **detente y pídeselos a Cristian**; no descargues de espejos no oficiales.
- `analisis-fdd/data/README.md` debe registrar la fuente, la versión, la fecha de descarga, la licencia y qué subconjunto se usó.
- Antes de modelar, haz un inventario de los equipos, variables, fallas y severidades disponibles. Elige con Cristian el subconjunto más parecido a lo que hay en el Edificio 2 (chiller o UMA).

### 3.2 Análisis (Python, reproducible)
- `analisis-fdd/` con `requirements.txt` fijado (pandas, scikit-learn, matplotlib), semilla fija y un solo punto de entrada: `python -m fdd.run`.
- **Método:** Isolation Forest (Liu, Ting & Zhou, 2008) entrenado **solo con datos sin falla** y evaluado con datos etiquetados con falla.
- **Línea base obligatoria para comparar:** una regla simple (umbral de puntaje z por variable). Si el Isolation Forest no la supera, el resumen lo dice.
- Para evitar fuga de información, separa entrenamiento y prueba por días o por corridas completas, nunca por filas al azar.
- **Métricas:** precisión, exhaustividad (recall), F1 y matriz de confusión, desglosadas por tipo de falla y por severidad. Reporta que las fallas leves (incipientes) son las más difíciles de detectar, si así sale.
- **Salidas:** `analisis-fdd/out/resultados.json` y gráficas en SVG.

### 3.3 Integración opcional al modelo 3D (solo si Cristian aprueba los resultados)
- Una tarjeta en la Parada 5: "Demostración: detección de anomalías con datos públicos". Lee el JSON **incrustado en el build**, sin servidor ni API, para que el HTML siga abriendo offline.
- Sello nuevo en `STAMP`: `ext` = "Datos públicos – no son del Edificio 2". Fuente citada en la tarjeta.
- Texto de limitación obligatorio: "El equipo de los datos no es el del Edificio 2 (ejemplo: RP-1043 es un chiller enfriado por agua de 90 TR; el del Edificio 2 es enfriado por aire, de 155 TR). Un modelo entrenado en uno no se aplica al otro sin datos propios."

### Aceptación
- `python -m fdd.run` regenera los mismos números con la misma semilla.
- El resumen incluye la comparación con la línea base y las limitaciones.
- `npm run check` sigue pasando y no hay peticiones de red.

---

## Descartado (y por qué)

| Propuesta del dictamen | Decisión | Razón |
|---|---|---|
| Pérdidas en B/. de la junta dañada ("80–120 W/m") | Descartar | Cifra sin fuente; no hay longitud, temperatura ni estado del aislamiento medidos. Sería inventar datos sobre un edificio real. |
| Motor en Python con Isolation Forest y API REST, con datos sintéticos (Mejora 6) | Aplazado y reformulado → **Fase 3** | Con datos sintéticos el detector solo encuentra las anomalías que uno programó (razonamiento circular), y la API en vivo rompe el HTML offline. La Fase 3 usa datos públicos reales y resultados precalculados. |
| Telemetría por UMA con valores | Descartar (se integró el inspector sin valores, 1.3) | Mismo motivo que arriba. |
| "Bombeo = 10–18 % del consumo" | Descartar la cifra (se integró el bombeo ilustrativo, 1.2) | Sin fuente verificable. |
| Casos "Texas A&M −42 %" y "ACP −30 % con MCSA" | No usar en ningún texto | No se pudieron verificar; el segundo parece inventado. |
| OSHA 29 CFR 1910.120 para refrigerantes | No citar | Es la norma de residuos peligrosos y respuesta a emergencias (HAZWOPER). Para refrigeración aplican ASHRAE 15 y ASHRAE 34. |
| "60 FPS estables" | No afirmar | No está medido. Si quieres una cifra, mídela con `renderer.info` y `performance.now()` en la laptop de la defensa. |
| Mostrar límites del VFD (pérdidas, par a baja frecuencia) | Ya cubierto | La tarjeta de la Parada 4 dice "Resultado teórico: no incluye pérdidas del VFD; hay que verificar que se mantenga la ventilación". |

---

## Orden sugerido para Claude Code

1. `npm install && npm run check`: confirma que la línea base pasa antes de tocar nada.
2. 1.1 → commit → `npm run check` → revisar capturas.
3. 1.2 → commit → ídem.
4. 1.3 → commit → ídem.
5. (Después del 21/10) 2.2 (con pruebas numéricas) → 2.1 → 2.3.
6. (Solo si Cristian lo pide) Fase 3, empezando por 3.1: inventario de datos y elección del subconjunto con él.
7. Al terminar cada fase, entrega `dist/Recorrido_integrado_Edificio2_offline.html` y un resumen de cambios, con la fuente de cada texto nuevo.
