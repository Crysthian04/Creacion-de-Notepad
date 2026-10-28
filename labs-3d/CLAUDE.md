# Modelo 3D de los laboratorios del Grupo A

Modelo 3D en el navegador (three.js r184, sin framework) de los laboratorios M6 y M14 de Cristian Batista y M8 y M11 de Manuel Jiménez (Mantenimiento de Sistemas de Refrigeración y A/A, UTP, Grupo A). Proyecto independiente de `../recorrido-3d/`, que **no se toca**.

| Tecla | Parada | Informe |
|---|---|---|
| 0 | Inicio | — |
| 1 | M6 · Mantenimiento de Ventiladores y Sistemas de Distribución | M6 (Cristian Batista) |
| 2 | M14 · Digitalización, BIM y Gestión Inteligente de Instalaciones (MEP) | M14 (Cristian Batista) |
| 3 | M8 · Aplicaciones Avanzadas de Refrigeración y A/A: District Cooling | M8 (Manuel Jiménez) |
| 4 | M11 · Métodos Innovadores de Mantenimiento | M11 (Manuel Jiménez) |

**Las Paradas 1 y 2 están congeladas en `labs-3d-v1.0`:** `npm run check` compara su huella con `tests/fixtures/v1_paradas_1_2.json` y falla si cambia algo (etiquetas, rótulos, chips, sellos, estados). No se tocan `content-m6.js`, `scene-m6.js`, `content-m14.js` ni `scene-m14.js`.

Cada parada tiene **ruta principal** (4 escenas E1–E4 con rótulo breve: frase ≤ 25 palabras, cifra ≤ 12, cita, sello y referencia, más chips «Detalle») y **profundización** (todos los pasos con texto completo). ← → recorren E1–E4; con «Profundización en ← →: sí» siguen por los pasos.

Especificación: `docs/Plan_Modelo3D_Labs_M6_M14.md`. Trazabilidad: `docs/MATRIZ_TRAZABILIDAD.md` (validarla antes de cambiar escenas).

## Comandos

```bash
npm install
npm run dev     # http://localhost:5173
npm run build   # dist/Modelo3D_Labs_M6_M14_offline.html (UN archivo, sin internet)
npm run check   # build + prueba de humo (paradas 0–4, identidad v1.0, cifras permitidas, sin red, sin desborde)
```

Si Playwright no encuentra navegador, exporta `CHROMIUM_PATH` con la ruta a un Chromium ya instalado (en el contenedor: `/opt/pw-browsers/chromium`).

## Fuentes (las únicas)

1. Word final del M6 (`M06_Mantenimiento_Ventiladores_Distribucion.docx`), del M14 (`M14_Digitalizacion_BIM_Gestion_MEP.docx`), del M8 (`M08_Aplicaciones_Avanzadas_Refrigeracion_AA.docx`) y del M11 (`M11_Metodos_Innovadores_Mantenimiento.docx`).
2. `docs/M6_Ficha_Fuentes_BORRADOR.md` y `docs/M14_Ficha_Fuentes_y_Esquema_BORRADOR.md`.
3. PDF del Proyecto Final Integrador de REFRESH S.A.: dimensiones y datos de la planta.

Si una ficha y su Word no coinciden, manda el Word. Si el simulador de REFRESH y el PDF no coinciden, manda el PDF.

## Reglas de contenido (no negociables)

1. **Cada parada refleja solo su propio informe.** No se mete el M6 dentro de REFRESH: el informe del M6 no menciona REFRESH.
2. **Trazabilidad en los dos sentidos.** Cada escena, animación o tarjeta indica la sección, figura o tabla del informe que la respalda (p. ej., "M14 · Tabla 1"), y ninguna sección del Desarrollo queda sin representación.
3. **Sellos propios** (no los del recorrido): "Dato de fuente" con la cita APA entre paréntesis, o "Ilustrativo". Citas solo entre paréntesis; nunca "según X".
4. **Cero cifras sin respaldo.** Sin capacidades (TR, kW, BTU/h), caudales ni lecturas que no estén en los informes. Un número en pantalla es un dato para la audiencia.
5. **Español de Panamá**, con tildes. Decimal: punto; miles: coma. Unidades con espacio y `&nbsp;`.
6. **Imágenes.** M6: cualquier figura del Word con su crédito debajo (uso didáctico). M14: solo la Figura 1 (BIMForum, CC BY-NC-ND, sin modificar) y la Figura 2 (Hu et al., CC BY), con su crédito; ninguna otra figura de terceros.
7. **REFRESH.** Dimensiones (PDF p. 22) y ubicación (plano, PDF p. 21) de los edificios: "Dato de fuente" (Batista et al., 2026). Salas de D y E: orden = "Dato de fuente" (p. 21); tamaños = "Ilustrativo". Unidades interiores solo donde las pone la Figura 3 del M14 (E: recepción, oficinas, sala de juntas; D: laboratorio QC, comedor); baños y taller sin equipos. Alturas: los 22 m son solo de la zona de la torre de la Nave A; todo lo demás, "Ilustrativo".
8. El caso IfM (Lu et al., 2020) va como tarjeta o esquema; no se modela ese edificio.
9. Nota visible: "Modelo conceptual, no a escala", salvo las dimensiones de REFRESH.
10. Del recorrido se reutiliza solo lo visual y técnico. **Nada** del Edificio 2 de la UTP ni de las investigaciones (evita autoplagio con la Investigación 3). La prueba de humo falla si aparecen "Edificio 2", "155 TR", "Henríquez Espinosa" o "Hosamo" (sin distinguir mayúsculas ni tildes). El crédito de F. Henríquez (coautor de Gollini-Mihalopoulos et al., 2023) en la Figura 11 del M6 es correcto y se mantiene.
11. **Referencias al informe por sección, figura o tabla** ("M6 · Tabla 1"), nunca por página del informe. Las páginas solo se citan para las fuentes originales.
12. **Paradas 3 y 4 (M8 y M11):** solo las cifras aprobadas (hoy, únicamente el reparto del lubricante del M11: 50/20/10/10/10 %, Prayogo et al., 2024, p. 401). Cualquier otra cifra de esos Word se expresa sin número; la prueba de humo busca dígitos en esas paradas. Una frase solo se usa si el Word la cita en ese párrafo; sin figuras ni infografías de los Word; sin marcas comerciales. El M8 y el M11 no se mezclan entre sí ni con REFRESH, la UTP, el M6 o el M14. Citas: «industry, M. E. (2024)» = (Prayogo et al., 2024) y «YAO / review (2015)» = (Yao, 2016); las demás, como en el Word. Pendientes de verificar: `docs/VERIFICACION_FUENTES_M8_M11.md`.

## Restricciones técnicas

- Un solo HTML que abre con doble clic, sin internet; `npm run check` falla si hay peticiones de red.
- Fluido en laptop sin GPU dedicada: geometría baja, `InstancedMesh`, sin texturas pesadas ni posprocesado.
- Pantallas: 1920×1080 y 1366×768.
- `vendor/` (three.js r184) y `src/stage/three-d-stage.js` se copiaron del recorrido: no se actualizan ni se agrega otra versión de three.js.

## Cómo cerrar un commit

1. `npm run check` pasa.
2. Revisar las capturas de `tests/shots/` a 1920×1080 y 1366×768.
3. Agregar pruebas a `tests/smoke.mjs`.
4. Reportar los textos nuevos con su fuente (informe y página).
5. Un commit por escena o función, mensaje en español.
