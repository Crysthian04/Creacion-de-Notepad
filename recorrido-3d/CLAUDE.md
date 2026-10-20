# Recorrido integrado 3D — Edificio 2 (Postgrado, UTP)

Modelo 3D en el navegador (three.js r184, sin framework) del sistema de climatización del Edificio 2 del Campus Víctor Levi Sasso. Es material de apoyo académico del Grupo A (Mantenimiento de Sistemas de Refrigeración y A/A, UTP). Recorre las 5 investigaciones sobre un mismo sistema:

| Tecla | Parada | Investigación |
|---|---|---|
| 0 | Vista general (introducción) | — |
| 1 | Seguridad | INV4 |
| 2 | Planificación | INV2 |
| 3 | Refrigerantes | INV1 |
| 4 | Energía | INV5 |
| 5 | Innovación (subventanas 5.1 Monitoreo IoT · 5.2 Termografía · 5.3 Realidad aumentada · 5.4 Dron en ductos) | INV3 |
| 6 | Vista integrada (sub-vistas i.1 Una falla · i.2 Antes / después · i.3 Plan de 2 años) | todas |

El plan de trabajo está en `docs/PLAN_MEJORAS.md`. Léelo antes de cambiar nada.

## Comandos

```bash
npm install          # esbuild + playwright
npm run dev          # http://localhost:5173 (el import map necesita http://, no file://)
npm run build        # dist/Recorrido_integrado_Edificio2_offline.html (UN archivo, sin internet)
npm test             # prueba numérica de la psicrometría (node --test)
npm run check        # npm test + build + prueba de humo (paradas 0–6, subventanas 5.x, modo al pasar, VFD, inspector, termografía, psicrometría, GLB, sin red)
```

Si Playwright no encuentra navegador: `npx playwright install chromium`, o exporta `CHROMIUM_PATH` con la ruta a un Chromium ya instalado.

## Mapa del código

- `index.html`: interfaz (barra de paradas, panel derecho, tarjetas, panel Clima y hora) y todo el CSS.
- `src/main.js`: entrada; importa `app/tour-app-v2.js`.
- `src/app/hvac-model.js`: geometría procedural. Edificio, chiller (`chiller_155TR`), 16 UMA (`UMA_01`…`UMA_16`, grupo `unidades_manejadoras`), circuito de agua helada (`circuito_agua_helada`), mini-splits, puntos de termografía (`thermalPts`) y propuesta IoT (`m.prop`).
- `src/app/tour-app-v2.js`: escena, cámara, etiquetas, tarjetas, atenuación por parada, VFD, bucle de animación y atajos 0–6.
- `src/app/tour-layers.js`: objetos propios de cada parada (técnicos, LOTO, cilindros, recuperadora, fuga, VFD, BMS) y su animación (`tick`).
- `src/app/tour-content.js`: TODO el texto (viñetas, tarjetas, sellos). Los cambios de contenido van aquí.
- `src/app/tools-v25.js`: escenas de las subventanas 5.2–5.4 (cámara termográfica portátil, salón con realidad aumentada, dron en ducto), adaptadas del modelo «Herramientas HVAC 3D» del grupo y colocadas dentro del edificio. Internamente son las paradas `'5.2'`, `'5.3'` y `'5.4'`; la `'5'` es la 5.1. Igual en la vista integrada: `'i'` es la i.1, y `'i.2'`, `'i.3'`.
- `src/app/features.js`: interruptores (`FEATURES.psychro = false`: calculadora en pausa).
- `src/app/psychro.js`: psicrometría a 101.325 kPa (Hyland-Wexler, W, h, punto de rocío, proceso de serpentín). Funciones puras, probadas en `tests/psychro.test.mjs`.
- `src/app/sky-v2.js`: sol astronómico (9.0247° N, 79.5299° O, UTC−5), clima y ocupación del edificio (solo indicador).
- `src/app/site-v2.js`: entorno ilustrativo (loma, Edificio 1, kiosco, autos, postes).
- `src/stage/three-d-stage.js`: componente `<three-d-stage>` (renderizador, OrbitControls, barra de exportación OBJ/GLB). Evita modificarlo.
- `vendor/`: three.js r184 y addons, copiados tal cual. No los actualices.
- `scripts/build-offline.mjs`: empaqueta todo en un solo HTML (fuentes en base64, una sola copia de three.js).
- `tests/smoke.mjs`: prueba de humo y capturas en `tests/shots/`.
- Equipos con metadatos en `userData`: `equip` (inspector por clic) e `ifcClass`/`fuente` (se exportan como `extras` en el GLB).

## Reglas de contenido (no negociables)

1. **No inventar cifras.** Toda cifra debe venir de la lista "Datos verificados" de abajo o de una fuente citable. Si no hay dato, la interfaz muestra "Sin dato medido". No uses un valor plausible.
2. **Separar dato real de ilustrativo.** Usa los sellos de `STAMP` en `tour-content.js`:
   - `real` = "Dato real – Edificio 2", solo para datos de Henríquez Espinosa et al. (2021).
   - `ilus` = "Ilustrativo", para todo lo demás (casos de las investigaciones, normas, propuestas, simulaciones).
   - Si una función calcula con valores de ejemplo, debe decirlo en pantalla.
3. **Citas** entre paréntesis, estilo APA 7: (Autor, año). Nada de "Fulano dijo…".
4. **Texto en español de Panamá**, con tildes y concordancia correctas. Unidades con espacio: `38 %`, `155 TR`, `B/. 474.34`. Usa `&nbsp;` para que el número no quede separado de su unidad.
5. **Nunca asignes un refrigerante concreto al chiller ni a los mini-splits**: la fuente no lo dice. Los cilindros R-410A/R-32/R-290 de la Parada 1 solo ilustran las clases ASHRAE 34.
6. **Física correcta.** Los refrigerantes son más densos que el aire: caen, desplazan el oxígeno y se acumulan en zonas bajas (National Refrigerants, s. f.; INV4, p. 43). Ya está corregido en la Parada 3; no lo reviertas.
7. Mantén la nota "Modelo conceptual, no a escala…".
8. La realidad aumentada (5.3) muestra el campo simulado solo de forma cualitativa (más cálida / intermedia / más fresca): sin °C ni % de humedad.

## Datos verificados: `docs/FUENTES_COMPENDIO.md`

La ÚNICA fuente de contenido es `docs/FUENTES_COMPENDIO.md`, un extracto del Compendio de Investigaciones del Grupo A (PDF de 64 páginas) con el número de página de cada dato. Léelo completo antes de escribir texto.
- Ningún texto ni cifra nueva sin una línea de ese archivo que lo respalde. Cita como aparece ahí.
- Lo que no esté ahí se omite o se marca "Propuesta del grupo (ilustrativa)", sin cifras.
- El único "Dato real – Edificio 2" es el de Henríquez Espinosa et al. (2021) en la INV3 (pp. 35–37). El 24 % restante de la climatización se rotula "Resto de la climatización (no desglosado en la fuente)", nunca "Mini-splits".
- Los casos de ejemplo (VFD de la INV5, KPI de un compresor de la INV2) son ilustrativos y no son del Edificio 2.

## Restricciones técnicas

- El HTML final debe abrir con doble clic, sin internet. `npm run check` falla si hay peticiones de red.
- Debe correr fluido en una laptop sin GPU dedicada. Geometría baja, `InstancedMesh` para elementos repetidos, nada de texturas pesadas ni posprocesado de pantalla completa.
- Atajos 0–6 y la navegación ← → deben seguir funcionando.
- Pantallas objetivo: 1920×1080 y 1366×768 (proyector).

## Cómo dar por terminada una tarea

1. `npm run check` pasa.
2. Revisa TÚ las capturas de `tests/shots/`: sin etiquetas encimadas, nada cortado, sellos presentes.
3. Si agregaste una cifra, indica su fuente en el resumen.
4. Un commit por mejora, con mensaje en español.
