# Cifras en pantalla — Modelo 3D de los laboratorios del Grupo A (M6, M14, M8, M11)

Paradas 1 y 2: generado el 25/10/2026 (hora de Panamá), ronda 5, y sin cambios en la versión 2. Paradas 0, 3 y 4: versión 2, 28/10/2026. Todo se obtiene a partir de `src/app/content-*.js` y de las etiquetas de `src/app/scene-*.js`.

Criterio (ronda 4): la columna «Escena» indica desde qué escena de la ruta principal se llega al paso (chips «Detalle»). La referencia al informe va por sección, figura o tabla, sin páginas del informe (decisión del 24/10). La página corresponde a la **fuente original**. Si la página dice "—", ni el Word ni la ficha la indican. No se listan los números de navegación (pasos, teclas, "1 de 9") ni los números de figura o tabla.

## Rótulos de la ruta principal (escenas E1–E4)

| Cifra | Escena | Informe | Fuente original y página |
|---|---|---|---|
| ±5 % del caudal de diseño | M6 · E1 (y franja 3D en E1 y E2) | M6 · El TAB y su marco normativo | Yale Facilities (2025), §4.3A, p. 23 |
| Banco de 8 terminales: 14 pasos por proporción, 10 por flujo progresivo (y contador doble «k de 14», «k de 10») | M6 · E2 | M6 · Métodos de balanceo · Tabla 1 | Pedranzini et al. (2013), p. 328 |
| −20 % de velocidad = −50 % de potencia (y botón «−20 % de velocidad») | M6 · E3 | M6 · Del balanceo al consumo de energía · Figura 7 | DOE y AMCA (2003), p. 18 |
| 72.90 % del consumo eléctrico teórico (Edificio N.° 1 de la UTP) | M6 · E4 | M6 · Aplicación al contexto panameño | Gollini-Mihalopoulos et al. (2023), p. 143 |
| −14.10 % en la simulación (volumen variable) | M6 · E4 | Ídem | Gollini-Mihalopoulos et al. (2023), pp. 146, 148 |
| USD 15,824 millones en 2002; cerca de dos terceras partes | M14 · E1 | M14 · Introducción | Gallaher et al. (2004), p. ES-6 |
| LOD 100, 200, 300, 350, 400, 500 (botones y nombre del nivel) | M14 · E2 | M14 · Niveles de desarrollo (LOD) · Tabla 1 | BIMForum (2024), pp. 12–13 |
| Caso real: 2 de 233 RFI y 0 órdenes de cambio | M14 · E4 | M14 · Tabla 2 | Khanzode et al. (2008), p. 336 |
| 50 % compresor · 20 % evaporador · 10 % secador, mangueras y condensador (y etiquetas 3D: compresor 50 %, evaporador 20 %, condensador 10 %, filtro secador 10 %, mangueras y líneas 10 %) | M11 · E3 | M11 · Aditivos nanotecnológicos | Prayogo et al. (2024), p. 401 (**pendiente de verificación**: ver `VERIFICACION_FUENTES_M8_M11.md`) |

Los rótulos de M8 E1–E4 y de M11 E1, E2 y E4 no tienen cifras.

La simulación de la E2 del M6 no muestra valores ni unidades (sello «Simulación ilustrativa · sin valores»; en texto, «ΔP = R·Q² (Pedranzini et al., 2013, p. 323)»). Sus 6 posiciones de compuerta y el caudal de diseño son ilustrativos y no se muestran como cifras. La ficha de activo de la E3 del M14 muestra los campos vacíos («—») a propósito.

## Parada 0 · Inicio

Sin cifras: el inicio no muestra fechas ni datos (decisión de la ronda 3). En la versión 2, los únicos números son el orden de las paradas (1–4) y los códigos de módulo (M6, M14, M8, M11).

## Parada 1 · M6

| Cifra | Paso | Escena | Informe (sección, figura o tabla) | Fuente original y página |
|---|---|---|---|---|
| casi 60 % de la electricidad | 1.0 | E1 | M6 · Introducción | Consejo de Gabinete (2022), p. 34 |
| 8 terminales (banco de prueba) | 1.0, 1.3, 1.4 | E1, E2 | M6 · Métodos de balanceo | Pedranzini et al. (2013), p. 325 |
| 4 ramales | 1.0 | E1 | Red del modelo (ilustrativa) | Sello "Ilustrativo"; no es un dato |
| ±5 % de los caudales de diseño | 1.1, 1.3, 1.4, 1.8 y franja 3D | E1, E2, E4 | M6 · El TAB y su marco normativo | Yale Facilities (2025), §4.3A, p. 23 |
| 14 pasos (proporción) | 1.3, 1.4, Tabla 1, contador 3D | E2 | M6 · Métodos de balanceo · Tabla 1 | Pedranzini et al. (2013), p. 328 |
| 10 pasos (flujo progresivo) | 1.4, Tabla 1, contador 3D | E2 | Ídem | Pedranzini et al. (2013), p. 328 |
| 100 a 200 m³/h; 200 a 650 Pa | 1.4 | E2 | M6 · Métodos de balanceo | Pedranzini et al. (2013), p. 325 |
| 2n + b − 1 mediciones evitadas; 57 % a 67 % | 1.4 (Tabla 1 resumida y completa), 1.8 | E2, E4 | M6 · Tabla 1 | Pedranzini et al. (2013), pp. 322, 329 |
| n + 2(n + b − 1) + 1 | 1.4 (Tabla 1 completa) | E2 | M6 · Tabla 1 | Pedranzini et al. (2013), pp. 323–329 |
| −20 % de velocidad, −50 % de potencia (rótulo y botón) | 1.6 | E3 | M6 · Del balanceo al consumo de energía | DOE y AMCA (2003), p. 18 |
| ∝ N, N², N³ (exponentes de las leyes) | 1.6 | E3 | Ídem · Figura 7 | DOE y AMCA (2003), p. 4 |
| 72.90 %; 2,404,170.72 kWh al año | 1.7 | E4 | M6 · Aplicación al contexto panameño | Gollini-Mihalopoulos et al. (2023), p. 143 |
| 35 %; 14.10 %; 352,224 kWh; B/. 53,777.56 al año | 1.7 | E4 | Ídem | Gollini-Mihalopoulos et al. (2023), pp. 146, 148 |
| verificación del 25 % | 1.7, P1 | E1, E4 | M6 · El TAB y su marco normativo | Yale Facilities (2025), pp. 1, 29 |
| 10 % o más de los puntos con desvío del 10 % o más | P1 | E1 | Ídem | Yale Facilities (2025), pp. 1, 29 |
| CL 48; 24 (12 en redondos); 6 (3 en redondos) | P2 y etiqueta 3D | E1 | M6 · Pruebas previas | DOE y AMCA (2003), p. 38 |
| más de 2 o 3 in wg | P2 | E1 | Ídem | DOE y AMCA (2003), p. 12 |
| 5 % a 10 % (correas); 200 hp; 5 %; 10 hp; USD 3,270 al año; USD 0.05/kWh | P3 | E1 | Ídem | DOE y AMCA (2003), p. 25 |
| hasta 30 % de caudal (efecto de sistema) | P6 y etiqueta 3D | E3 | M6 · Del balanceo al consumo de energía | DOE y AMCA (2003), p. 9 |
| ≈ 165,030 ft²; 1.5 → 1.0 in wg (0.5 de noche); −63.6 %; −84.2 % | P7 | E4 | M6 · Evidencia de campo | Claridge et al. (2003), — |
| 1998–1999; 12 zonas; cerca de −7 %; unos 30,000 kWh al mes | P7 | E4 | Ídem | Claridge et al. (2003), — |
| 2000: 37.7 % | P7 | E4 | Ídem | Claridge et al. (2003), — |
| 44 edificios; 2 % a 49 %; 17.5 %; 0.1 a 4.2 años | P7 | E4 | Ídem | Gregerson (1997), como se citó en Claridge et al. (2003), — |
| 33 rejillas; error promedio de 7.8 % | P8 | E4 | Ídem | Cristiano Mendivelso y Hernández Romero (2023), pp. 137–138 |
| 17 de 33; 6 por encima del 10 %; 74 % (60 → 105 CFM); 5.7 % | P8 | E4 | Ídem (cálculo propio del informe) | Con datos de Cristiano Mendivelso y Hernández Romero (2023), pp. 137–138 |
| recortada en 20 % (crédito de la Figura 9) | P8 | E4 | M6 · Figura 9 | Crédito del Word |
| Res. N.° 3142 de 2016; 15 % y luego 20 % | P9 | E4 | M6 · Aplicación al contexto panameño | Secretaría Nacional de Energía (2016), p. 21 |
| Ley 69 de 2012; plan de al menos cinco años, revisado cada año | P9, 1.8 | E4 | Ídem | Asamblea Nacional (2012), arts. 8 y 23 |
| Edificio N.° 1; Edificio N°1 (crédito de la Figura 11) | 1.7 | E4 | Ídem · Figura 11 | Gollini-Mihalopoulos et al. (2023), p. 143 |

## Parada 2 · M14

| Cifra | Paso | Escena | Informe (sección, figura o tabla) | Fuente original y página |
|---|---|---|---|---|
| USD 15,824 millones (2002); cerca de dos terceras partes | 2.0 | E1 | M14 · Introducción | Gallaher et al. (2004), p. ES-6 |
| cinco edificios; terreno de 10,000 m² | 2.0 | E1 | M14 · Sistema MEP integrado | Batista et al. (2026), p. 22 |
| PD-D; PD-E (identificadores de los paneles de distribución de D y E; sin amperajes) | 2.0b, 2.5, P1 (etiquetas) | E1, E3 | M14 · Figura 3 (tableros de D y E) | Batista et al. (2026), p. 25 (unifilar) |
| Terreno 100 × 100 m (10,000 m²) | 2.0 (etiqueta) | E1 | M14 · Sistema MEP integrado | Batista et al. (2026), p. 22 |
| Nave A 40 × 20 m (la etiqueta incluye «zona de la torre: 22 m»); Nave B 30 × 18 m; Edificio C 24 × 12 m; Edificio D 25 × 12 m; Edificio E 20 × 10 m | 2.0 y vistas de conjunto (etiquetas) | E1 | Ídem | Batista et al. (2026), p. 22 |
| zona de la torre: 22 m | 2.0 y vistas de conjunto (en la etiqueta de la Nave A) | E1 | Ídem | Batista et al. (2026), p. 22 |
| 4 silos Ø 2.50 m | 2.0 (etiqueta) | E1 | Escena base | Batista et al. (2026), p. 22 |
| Área de expansión futura · 3,000 m² (30 %) | 2.0 (etiqueta) | E1 | Escena base | Batista et al. (2026), p. 22 |
| USD 96.9 millones (edificio médico) | 2.1 | E4 | M14 · La metodología BIM aplicada a sistemas HVAC-R | Khanzode et al. (2008), p. 324 |
| LOD 100, 200, 300, 350, 400, 500 | 2.2, 2.6, P7 | E2, E4 | M14 · Niveles de desarrollo (LOD) · Tabla 1 | BIMForum (2024), pp. 12–13 |
| LOD 500 no es superior al 400 (etiqueta) | 2.2 | E2 | Ídem | BIMForum (2024), p. 13 |
| «modelo LOD 300» | 2.2 | E2 | Ídem | BIMForum (2024), p. 195 |
| D3030.10; D3050.50 | 2.2 (nota de la Tabla 1; título de la Figura 1) | E2 | M14 · Tabla 1 · Figura 1 | BIMForum (2024), p. 128; la asignación es del grupo |
| 2 de 233 RFI; 0 órdenes de cambio | 2.3 | E4 | M14 · Tabla 2 | Khanzode et al. (2008), p. 336 |
| 40 de 25,000 h (menos de 0.2 %) | 2.3 | E4 | M14 · Tabla 2 | Khanzode et al. (2008), p. 339 |
| ≈ USD 500,000 de ≈ USD 9.4 millones | 2.3 | E4 | M14 · Tabla 2 | Khanzode et al. (2008), p. 338 |
| ≈ USD 9 millones y 6 meses | 2.3 | E4 | M14 · Tabla 2 | Khanzode et al. (2008), p. 337 |
| USD 15,824 millones | 2.3 | E4 | M14 · Tabla 2 | Gallaher et al. (2004), p. ES-6 |
| USD 10,648 millones (≈ dos tercios) | 2.3 | E4 | M14 · Tabla 2 | Gallaher et al. (2004), p. ES-7 |
| USD 9,093 millones | 2.3 | E4 | M14 · Tabla 2 | Gallaher et al. (2004), p. ES-7 |
| dos bombas; IFC4; dos falsas alarmas; casi una semana | 2.4 | E3 | M14 · Del modelo BIM al gemelo digital | Lu et al. (2020), — |
| cinco capas | 2.4 | E3 | Ídem · Figura 2 | Hu et al. (2026), sección 6.1, Fig. 8 |
| dos conjuntos de datos de dos bombas | P3 | E3 | Ídem | Lu et al. (2020), — |
| M1–M6, C1–C4 (identificadores de puntos) | 2.5, P1 | E3 | M14 · Figura 3 | Elaboración propia del informe; Daikin Comfort Technologies North America (2019), pp. 24–26, 30–31, 33 |
| LOD 500 (etiqueta del modelo BIM as-built) | 2.5, P1 | E3 | M14 · Figura 3 | BIMForum (2024), p. 13 |
| 2022 (diagnóstico regional) | 2.7, P6 | E4 | M14 · Conclusiones | Soto y Manríquez (2023), pp. 17–18 |
| CC BY-NC-ND 4.0; CC BY 4.0; Artículo 113997; 288 | 2.2, 2.4 (créditos) | E2, E3 | M14 · Figuras 1 y 2 | Créditos del Word |

## Parada 3 · M8 (Manuel Jiménez)

**Ninguna cifra en pantalla.** La prueba de humo busca dígitos en la columna de tarjetas, las etiquetas visibles, el panel derecho y el encabezado de la parada 3, en los 10 pasos y en sus estados. Falla si queda alguno después de quitar las citas (año y página), los números de paso (3.0–3.5), E1–E4 y el código M8.

Cifras del Word que **no** se muestran y cómo quedaron en pantalla:

| Cifra del Word | En pantalla |
|---|---|
| Agua fría «entre 4 °C y 7 °C»; retorno «12 °C a 16 °C»; «aproximadamente 5 °C»; «cercana a 14 °C» | «agua fría» / «regresa más caliente»; azul y rojo, sin escala de temperatura |
| Reducción del consumo «entre un 20 % y un 50 %» | No se usa (sin cita en el Word) |
| COP «entre 3 y 5» y «superior a 6» | No se usa (sección sin cita) |
| Vida útil «15–20 años» y «25–40 años» (tabla) | No se usa (tabla sin cita) |
| «las 24 horas» (Ciudad de la Salud) | «refrigeración continua» |
| TR y MWt | Se nombran las unidades, sin valores (3.0) |

## Parada 4 · M11 (Manuel Jiménez)

**Única cifra en pantalla:** el reparto del lubricante (50, 20, 10, 10 y 10 %; Prayogo et al., 2024, p. 401) en el rótulo y en las etiquetas de E3 y en la tarjeta 4.2. La prueba de humo falla con cualquier otro dígito en la parada 4 (mismas exclusiones que en la parada 3, con 4.0–4.5 y M11). Los subíndices de TiO₂, SiO₂ y Al₂O₃ no son cifras.

| Cifra del Word | En pantalla |
|---|---|
| «0.8 mm» de incrustación; consumo «hasta en un 10 %–12 %» | «el compresor consume más» |
| «entre 20 kHz y 40 kHz» | «ondas ultrasónicas de baja frecuencia» (texto del Word), sin valores |
| Recuperación «92 %–98 %»; descarga «5 %–8 %»; ahorro «10 %–18 %» y «10 %–20 %» | No se usan (sin cita en el Word) |
| Clima: «superiores a 30 °C», «supera frecuentemente el 80 %» | No se usa |
| ROI «menos de 6 a 8 meses»; «más de tres años de uso» | «recuperar la capacidad de enfriamiento sin reemplazar los equipos» |
| Frecuencia de mantenimiento (tabla) | No se usa |

## Geometría con dato que no se muestra como cifra

- **Huella de la zona de la torre:** 12 × 14 m (Batista et al., 2026, p. 13), usada para el volumen de 22 m.
- **Pasarela A–B:** 3 m de ancho (Batista et al., 2026, p. 23).
- **Zona de descarga:** 15 × 6 m (Batista et al., 2026, p. 22).
- **Patio de silos:** 15 × 10 m (Batista et al., 2026, p. 22).
- **Ubicación de los edificios:** aproximada al plano general (Batista et al., 2026, p. 21).
- **Ilustrativo (sin cifra en pantalla):** las demás alturas, el tamaño de las salas, la ubicación de los equipos del VRF y la red del M6.

## Notas

1. **USD 96.9 millones (paso 2.1):** página confirmada por Cristian el 24/10/2026: Khanzode et al. (2008), p. 324. La tarjeta cita (Khanzode et al., 2008, pp. 324, 328–329): p. 324 para la cifra y pp. 328–329 para la coordinación liderada por el contratista de HVAC.
2. **Claridge et al. (2003) y Lu et al. (2020):** el Word no indica páginas de sus cifras, así que en pantalla se citan sin página, como en el informe.
