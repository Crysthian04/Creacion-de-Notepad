# Recorrido integrado 3D — Edificio 2 (Postgrado, UTP)

Modelo 3D en el navegador (three.js r184, sin framework) del sistema de climatización del Edificio 2 del Campus Víctor Levi Sasso. Es material de apoyo académico del Grupo A (Mantenimiento de Sistemas de Refrigeración y A/A, UTP). Recorre las 5 investigaciones sobre un mismo sistema:

| Tecla | Parada | Investigación |
|---|---|---|
| 0 | Vista general | — |
| 1 | Seguridad | INV4 |
| 2 | Planificación | INV2 |
| 3 | Refrigerantes | INV1 |
| 4 | Energía | INV5 |
| 5 | Innovación | INV3 |
| 6 | Vista integrada | todas |

El plan de trabajo está en `docs/PLAN_MEJORAS.md`. Léelo antes de cambiar nada.

## Comandos

```bash
npm install          # esbuild + playwright
npm run dev          # http://localhost:5173 (el import map necesita http://, no file://)
npm run build        # dist/Recorrido_integrado_Edificio2_offline.html (UN archivo, sin internet)
npm test             # prueba numérica de la psicrometría (node --test)
npm run check        # npm test + build + prueba de humo (paradas 0–6, VFD, inspector, termografía, psicrometría, GLB, sin red)
```

Si Playwright no encuentra navegador: `npx playwright install chromium`, o exporta `CHROMIUM_PATH` con la ruta a un Chromium ya instalado.

## Mapa del código

- `index.html`: interfaz (barra de paradas, panel derecho, tarjetas, panel Clima y hora) y todo el CSS.
- `src/main.js`: entrada; importa `app/tour-app-v2.js`.
- `src/app/hvac-model.js`: geometría procedural. Edificio, chiller (`chiller_155TR`), 16 UMA (`UMA_01`…`UMA_16`, grupo `unidades_manejadoras`), circuito de agua helada (`circuito_agua_helada`), mini-splits, puntos de termografía (`thermalPts`) y propuesta IoT (`m.prop`).
- `src/app/tour-app-v2.js`: escena, cámara, etiquetas, tarjetas, atenuación por parada, VFD, bucle de animación y atajos 0–6.
- `src/app/tour-layers.js`: objetos propios de cada parada (técnicos, LOTO, cilindros, recuperadora, fuga, VFD, BMS) y su animación (`tick`).
- `src/app/tour-content.js`: TODO el texto (viñetas, tarjetas, sellos). Los cambios de contenido van aquí.
- `src/app/psychro.js`: psicrometría a 101.325 kPa (Hyland-Wexler, W, h, punto de rocío, proceso de serpentín). Funciones puras, probadas en `tests/psychro.test.mjs`.
- `src/app/sky-v2.js`: sol astronómico (9.0247° N, 79.5299° O, UTC−5), clima y respuesta cualitativa.
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
6. **Física correcta.** El vapor de refrigerante es más denso que el aire: cae y se extiende a ras de piso (Honeywell, 2014). Ya está corregido en la Parada 3; no lo reviertas.
7. Mantén la nota "Modelo conceptual, no a escala…".

## Datos verificados (compendio final del grupo)

- **Edificio 2** (Henríquez Espinosa et al., 2021): chiller enfriado por aire de 155 TR; 16 UMA; mini-splits inverter de 12,000–60,000 BTU/h. Climatización = 69 % del consumo; dentro de la climatización: chiller 38 %, UMA 38 %. El anillo del modelo pone el 24 % restante como "Mini-splits"; Cristian debe confirmarlo en la fuente. Hasta entonces no repitas ese 24 % en ningún otro lugar. Deterioro en uniones de la tubería de agua fría detectado en una sola inspección termográfica. La distribución de UMA por piso del modelo es ilustrativa.
- **INV1**: GWP a 100 años: R-22 = 1,810 (ODP 0.055), R-410A = 2,088, R-32 = 675, R-290 = 3. Kigali ratificado por Ley 87 de 2017. Meta −80 % de HFC al 2045. En Panamá no existen instalaciones de recuperación y reciclaje (Plan de Enfriamiento de Panamá, 2020).
- **INV2** (ejemplo ilustrativo): MTBF = 360 h, MTTR = 5 h, disponibilidad = 98.63 %. Frecuencias: semanal, mensual, 3 meses, 6 meses, anual. Split de referencia de 12,000 BTU/h.
- **INV4**: OSHA 29 CFR 1910.147 (LOTO, 6 pasos), NFPA 70E, ASHRAE 34 (A1/A2L/A3).
- **INV5** (caso ilustrativo, NO es del Edificio 2): ventilador de 15 kW, 360 h/mes; al 80 %: 7.68 kW, 2,764.8 kWh/mes, 48.8 % de ahorro, B/. 474.34/mes con tarifa hipotética de B/. 0.18/kWh. Ley 69 de 2012.
- **Refrigerante**: vapor de R-410A con densidad ≈ 3 (aire = 1); desplaza el oxígeno y se acumula en zonas bajas (Honeywell, 2014).

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
