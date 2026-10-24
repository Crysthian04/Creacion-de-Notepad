# Matriz de trazabilidad — Modelo 3D M6 + M14

Estado: **borrador para validación** (24/10/2026). Todavía no hay código del modelo.

Fuentes: Word final del M6 (`M06_Mantenimiento_Ventiladores_Distribucion.docx`, 17 págs.), Word final del M14 (`M14_Digitalizacion_BIM_Gestion_MEP.docx`), las dos fichas de `docs/` y el PDF del Proyecto Final Integrador de REFRESH S.A. (33 págs.).

- **Pág. inf.**: página del informe. La obtuve al convertir el Word a PDF con LibreOffice. En el M6 coincide con las 17 páginas de la ficha. En el M14 salen 12 y la ficha dice 13 (ver duda D1).
- **Pág. fuente**: página de la obra citada, tomada del Word o de la ficha.
- **Nivel**: **RP** = ruta principal · **PR** = profundización.
- **Sellos**: **DF** = "Dato de fuente (cita)" · **IL** = "Ilustrativo". Muchos elementos llevan los dos: el objeto 3D es IL y el texto de su tarjeta es DF.

---

## Parada 0 · Inicio (tecla 0)

| Informe | Sección/figura/tabla | Elemento del 3D | Nivel | Sello | Cita y página |
|---|---|---|---|---|---|
| — | Portadas (p. 1 de cada Word) | Pantalla de inicio: título de los dos módulos, asignatura, Grupo A, autor. Botones 1 y 2. Nota "Modelo conceptual, no a escala" | RP | — | Sin cifras |

## Parada 1 · M6 — Mantenimiento de Ventiladores y Sistemas de Distribución (tecla 1)

| Informe | Sección/figura/tabla | Elemento del 3D | Nivel | Sello | Cita y página |
|---|---|---|---|---|---|
| M6 | Introducción (p. 2) | **Escena 1.0 · Ventilador y red.** Ventilador con correas, filtro, serpentín, ducto principal con ramales, compuertas y 8 terminales. Tarjeta de apertura: qué es el TAB (prueba, ajuste, balanceo) y "casi el 60 %" de la electricidad del país en el sector comercial y las oficinas públicas | RP | IL (escena) · DF (tarjeta) | (Consejo de Gabinete, 2022); (DOE y AMCA, 2003); (Pedranzini et al., 2013, p. 322) · inf. p. 2 |
| M6 | Figura 1 · *Example Fan System Components* (p. 3) | Imagen en la tarjeta de la escena 1.0, con crédito. Las piezas 3D (filtro, serpentín, ventilador, ductos, compuertas, difusores) siguen esa lista | RP | DF | (DOE y AMCA, 2003, p. 10) · inf. p. 3 |
| M6 | §El TAB y su marco normativo: NEBB, AABC y TABB (pp. 3–4) | **Tarjeta 1.1 · Quién hace el TAB.** Empresa AABC, NEBB o TABB, contratada aparte del contratista mecánico; procedimientos AABC MN-1, NEBB y SMACNA 1780; requisitos previos de NEBB; contenido del reporte | RP (resumen) · PR (detalle NEBB y reporte) | DF | (Yale Facilities, 2025); (NEBB, 2019, como se citó en Guzmán Solano, 2025); (Guzmán Solano, 2025, pp. 51–52) · inf. pp. 3–4 |
| M6 | ídem, criterio de aceptación (p. 4) | **Franja de ±5 % en cada terminal** (se usa en la escena 1.3). Tarjeta de verificación: se vuelven a medir el 25 % de los terminales; el reporte se rechaza si el 10 % o más se desvía 10 % o más | RP (±5 %) · PR (25 % y rechazo) | DF | (Yale Facilities, 2025, §4.3A, p. 23; pp. 1, 29) · inf. p. 4 |
| M6 | Figura 2 · Secuencia del proceso TAB (p. 4) | **Barra de pasos de la parada**: contratación → pruebas previas → balanceo → verificación. La figura se muestra en la tarjeta 1.1 con su crédito | RP | DF | Elaboración propia a partir de (Yale Facilities, 2025) y (Guzmán Solano, 2025) · inf. p. 4 |
| M6 | §Pruebas previas: limpieza, hermeticidad y estado del ventilador (pp. 5–6) | **Escena 1.2 · Antes del TAB.** Se reemplaza el filtro sucio por uno limpio; prueba de fugas del ducto (las uniones se iluminan); revisión de correas y poleas. Animación de una compuerta trabada abierta que le "roba" caudal a los demás ramales | RP | IL (animación) · DF (texto) | (Yale Facilities, 2025); (DOE y AMCA, 2003) · inf. p. 5 |
| M6 | ídem, clase de fuga CL 48 → 24 → 6 (12 y 3 en redondos); pruebas en sistemas de más de 2 o 3 in wg (p. 5) | Tarjeta 1.2a · Hermeticidad: tres estados del ducto (sin sellar, juntas transversales selladas, todo sellado) | PR | DF | (DOE y AMCA, 2003, p. 38; p. 12) · inf. p. 5 |
| M6 | ídem, correas 5 %–10 %; 200 hp → 10 hp ≈ USD 3,270/año a USD 0.05/kWh; lista de mantenimiento (p. 5) | Tarjeta 1.2b · Correas y lista de mantenimiento | PR | DF | (DOE y AMCA, 2003, p. 25) · inf. p. 5 |
| M6 | Figura 3 · (a) *Proper Belt Tension*; (b) *Improper Alignment* (p. 6) | Imagen en la tarjeta 1.2b, con crédito | PR | DF | (DOE y AMCA, 2003, pp. 49–50) · inf. p. 6 |
| M6 | ídem, medición de presión según la conexión a ductos (p. 6) | Tarjeta 1.2c · Medición de presión: tomas en la entrada y la salida del ventilador 3D | PR | DF | (DOE y AMCA, 2003, p. 57) · inf. p. 6 |
| M6 | Figura 4 · *Alternative Methods of Measuring Fan Pressure* (p. 6) | Imagen en la tarjeta 1.2c, con crédito | PR | DF | (DOE y AMCA, 2003, p. 58) · inf. p. 6 |
| M6 | §Métodos de balanceo: proporción frente a flujo progresivo (pp. 6–7) | **Escena 1.3 · Balanceo.** Primero, el método de proporción: se abren todas las compuertas, se igualan las relaciones por pares desde los dos terminales más desfavorecidos y al final se ajusta la velocidad del ventilador; es iterativo. Después, el flujo progresivo: un terminal a la vez, desde el último hacia el ventilador, con variador y lazo de control. Contador de pasos: **14 contra 10**. Barras sin escala numérica que entran en la franja de ±5 % | RP | IL (red y barras) · DF (pasos y procedimiento) | (Pedranzini et al., 2013, pp. 323, 325, 328); (Yale Facilities, 2025, p. 26) · inf. pp. 6–7. Ver choque C1 |
| M6 | ídem, medición del caudal con anemómetro o tubo de Pitot (p. 6) | Tarjeta 1.3a · Medir no es trivial: el técnico mide en una rejilla con varias lecturas | PR | DF | (Pedranzini et al., 2013); (Cristiano Mendivelso y Hernández Romero, 2023, pp. 122–125) · inf. pp. 6–7 |
| M6 | ídem, banco de 8 terminales, 100–200 m³/h, 200–650 Pa; 2n + b − 1 mediciones evitadas, 57 %–67 % (p. 7) | Tarjeta 1.3b · El banco de prueba (la red 3D tiene 8 terminales por esta razón) | RP | DF | (Pedranzini et al., 2013, pp. 322, 325, 329) · inf. p. 7 |
| M6 | Tabla 1 · Comparación de los métodos de proporción y de flujo progresivo (p. 8) | Tarjeta 1.3c con la Tabla 1 completa (6 criterios), incluida la limitación "validado en un banco de laboratorio a escala, no en un edificio" | RP | DF | (Pedranzini et al., 2013, pp. 323–329) · inf. p. 8 |
| M6 | Figura 5 · (a) *Schematic layout of the reference air distribution network*; (b) *Scheme of the control loop* (p. 8) | Imagen en la tarjeta 1.3c, con crédito. El lazo de control se dibuja en 3D durante el flujo progresivo | RP | DF | (Pedranzini et al., 2013, p. 326) · inf. p. 8 |
| M6 | Figura 6 · Mediciones del proceso de validación, Bogotá (p. 9) | Imagen en la tarjeta 1.5b (caso Bogotá), con crédito | PR | DF | (Cristiano Mendivelso y Hernández Romero, 2023, p. 132) · inf. p. 9 |
| M6 | §Del balanceo al consumo de energía, ΔP = R·Q² y apertura máxima (p. 9) | **Escena 1.4a · Compuerta abierta y velocidad.** Con el mismo caudal: compuertas casi cerradas y ventilador rápido contra compuertas abiertas y ventilador más lento. El último paso del TAB se hace en el ventilador (velocidad, poleas o variador) | RP | IL (animación) · DF (texto) | (Pedranzini et al., 2013, pp. 323–324); (Yale Facilities, 2025, p. 28) · inf. p. 9 |
| M6 | ídem, leyes de los ventiladores; −20 % de velocidad ≈ −50 % de potencia (p. 9) | **Escena 1.4b · Leyes de los ventiladores.** Control de velocidad con tres medidores relativos: caudal ∝ N, presión ∝ N², potencia ∝ N³. El punto del 80 % se rotula con la frase del informe | RP | DF (leyes y punto del 80 %) | (DOE y AMCA, 2003, pp. 4, 18) · inf. p. 9. Ver choque C2 |
| M6 | Figura 7 · Caudal, presión y potencia en función de la velocidad (p. 10) | Imagen en la tarjeta 1.4b, con crédito; las curvas del control 3D son las mismas | RP | DF | Elaboración propia con (DOE y AMCA, 2003, p. 4) · inf. p. 10 |
| M6 | ídem, efecto de sistema: codo en la salida, hasta −30 % de caudal; sobredimensionamiento (p. 10) | Tarjeta 1.4c · Efecto de sistema: un codo pegado a la salida del ventilador 3D | PR | DF | (DOE y AMCA, 2003, p. 9) · inf. p. 10 |
| M6 | Figura 8 · *System Effect for a Typical Fan and System* (p. 11) | Imagen en la tarjeta 1.4c, con crédito | PR | DF | (DOE y AMCA, 2003, p. 9) · inf. p. 11 |
| M6 | §Evidencia de campo, Bogotá: 33 rejillas, error promedio de 7.8 %, 17 de 33 fuera de ±5 %, 6 por encima del 10 %, 74 % (60 → 105 CFM), 5.7 % sin ese caso (p. 11) | Tarjeta 1.5b · "El promedio oculta la dispersión". Sin barras por rejilla: el informe no trae los 33 valores | PR | DF (cálculo propio del informe) | Elaboración propia con datos de (Cristiano Mendivelso y Hernández Romero, 2023, pp. 137–138) · inf. p. 11 |
| M6 | Figura 9 · Desviación del caudal en las 33 rejillas (p. 12) | Imagen en la tarjeta 1.5b, con crédito | PR | DF | Elaboración propia con la Tabla 29 de (Cristiano Mendivelso y Hernández Romero, 2023, pp. 137–138) · inf. p. 12 |
| M6 | ídem, Kleberg: ≈ 165,030 ft²; presión estática de 1.5 a 1.0 in wg (0.5 de noche); agua helada −63.6 %, agua caliente −84.2 %; balance de aire 1998–1999 ≈ −7 % de electricidad, ≈ 30,000 kWh/mes (p. 12) | Tarjeta 1.5a · Caso Kleberg | PR | DF | (Claridge et al., 2003) · inf. p. 12 |
| M6 | Figura 10 · *Pre-CC and post-CC heating water consumption at the Kleberg Building…* (p. 13) | Imagen en la tarjeta 1.5a, con crédito | PR | DF | (Claridge et al., 2003, Figura 1) · inf. p. 13 |
| M6 | ídem, seguimiento: en 2000 el ahorro de agua helada bajó a 37.7 %; 44 edificios, 2 %–49 %, promedio de 17.5 %, retorno de 0.1–4.2 años; ninguna fuente aísla el TAB (p. 13) | Tarjeta 1.5a (continuación) · "Sin seguimiento, el ahorro se pierde" | PR | DF | (Claridge et al., 2003); (Gregerson, 1997, como se citó en Claridge et al., 2003) · inf. p. 13 |
| M6 | §Aplicación al contexto panameño, Edificio N.° 1 de la UTP: 72.90 % de 2,404,170.72 kWh/año; −35 % en el motor de una manejadora (simulación); 14.10 %, 352,224 kWh y B/. 53,777.56 al año (pp. 13–14) | **Escena 1.6 · Panamá.** Tarjeta grande con las cifras y la aclaración "simulación y cambio a VAV, no un TAB". No se modela el edificio | RP | DF | (Gollini-Mihalopoulos et al., 2023, pp. 143, 146, 148) · inf. pp. 13–14 |
| M6 | Figura 11 · Modelo energético del Edificio N°1 antes de simulación (p. 14) | Imagen en la tarjeta 1.6, con crédito | RP | DF | (Gollini-Mihalopoulos et al., 2023, p. 143) · inf. p. 14. Ver choque C3 |
| M6 | ídem, marco normativo: Res. N.° 3142 de 2016 (nuevas edificaciones, 15 % y 20 %, variadores en UMA, sin requisitos de ductos, filtros ni balanceo); ENUREE; Ley 69 de 2012 (comité de energía, plan de 5 años revisado cada año) (pp. 14–15) | Tarjeta 1.6a · Marco panameño y "el lugar práctico para un TAB periódico" | PR | DF | (Secretaría Nacional de Energía, 2016, p. 21); (Consejo de Gabinete, 2022, pp. 58, 60); (Asamblea Nacional, 2012, arts. 8 y 23) · inf. pp. 14–15 |
| M6 | Conclusiones 1–5 (p. 15) | Tarjeta de cierre de la parada: cinco frases cortas, cada una enlazada a su escena (1.3, 1.2, 1.3, 1.4, 1.6). Sin datos nuevos | RP | DF | Citas de cada conclusión · inf. p. 15 |

## Parada 2 · M14 — Digitalización, BIM y Gestión Inteligente de Instalaciones (MEP) (tecla 2)

Escena base: la planta REFRESH S.A. con las dimensiones del PDF (terreno 100 × 100 m; Nave A 40 × 20 m; Nave B 30 × 18 m; Edificio C 24 × 12 m; Edificio D 25 × 12 m; Edificio E 20 × 10 m; zona de descarga 15 × 6 m; patio de silos 15 × 10 m). Sello DF (Batista et al., 2026), PDF p. 22. Las alturas, salvo la de Nave A, son IL.

| Informe | Sección/figura/tabla | Elemento del 3D | Nivel | Sello | Cita y página |
|---|---|---|---|---|---|
| M14 | Introducción: USD 15,824 millones (2002), ≈ dos tercios para propietarios y operadores; BIM como repositorio y gemelo digital (p. 2) | Tarjeta de apertura de la parada sobre la vista aérea de REFRESH | RP | DF | (Gallaher et al., 2004, p. ES-6); (Hu et al., 2026) · inf. p. 2 |
| M14 | §La metodología BIM aplicada a sistemas HVAC-R (pp. 2–3) | **Escena 2.1 · Coordinación.** Tramo de cielo raso **genérico** (no es REFRESH): los modelos de HVAC, eléctrico, plomería y estructura se superponen; se resaltan interferencias en rojo y se resuelven, con el ducto de HVAC como prioridad. Tarjeta: edificio médico de USD 96.9 millones en California; el contratista de HVAC lideró; elementos no modelados (acabados, mobiliario, soportes) causaron conflictos | RP | IL (escena) · DF (tarjeta) | (BIMForum, 2024); (Khanzode et al., 2008, pp. 328–329, 339–340) · inf. pp. 2–3 |
| M14 | §Niveles de desarrollo (LOD): definiciones 100–500; el LOD no es el nivel de detalle; requisitos acumulativos salvo el 500 (p. 3) | **Escena 2.2 · LOD.** La unidad exterior del VRF y un tramo de su tubería, junto al Edificio E, pasan por LOD 100 (volumen de reserva), 200, 300 (con espacios de servicio), 350 (tubería y soportes coordinados), 400 (derivaciones y soportes) y 500 (as-built verificado; se muestra con un sello de verificación, no como "más detalle") | RP | IL (objeto) · DF (texto de cada paso) | (BIMForum, 2024, pp. 12–13) · inf. p. 3 |
| M14 | ídem: no existe un "modelo LOD 300"; el LOD es solo geometría y los datos van por COBie (pp. 3–4) | Tarjeta 2.2a · Dos aclaraciones para mantenimiento | RP | DF | (BIMForum, 2024, pp. 11, 195) · inf. pp. 3–4 |
| M14 | Figura 1 · Progresión del LOD 200 al LOD 400 (D3030.10) (p. 4) | Imagen sin modificar en la tarjeta 2.2, con crédito y licencia CC BY-NC-ND 4.0 | RP | DF | (BIMForum, 2024, p. 128) · inf. p. 4 |
| M14 | Tabla 1 · Elementos del VRF de REFRESH por LOD (p. 5) | Texto de cada paso de la escena 2.2 (columnas Contenido, Ejemplo y Utilidad), más la nota "asignación D3030.10 / D3050.50 = interpretación del grupo" | RP | DF | (BIMForum, 2024) · inf. p. 5 |
| M14 | §Ventajas cuantificadas (pp. 5–6) | **Escena 2.3 · Ventajas.** Tarjeta con contadores animados que se llenan con las cifras de la Tabla 2 | RP | DF | (Khanzode et al., 2008, pp. 336–339) · inf. pp. 5–6 |
| M14 | Tabla 2 · Ventajas cuantificadas y costo de la falta de interoperabilidad (p. 6) | Las 8 filas de la Tabla 2 en la escena 2.3, con su nota (un solo proyecto; estimaciones para EE. UU.) | RP | DF | (Khanzode et al., 2008, pp. 336–339); (Gallaher et al., 2004, pp. ES-6, ES-7) · inf. p. 6 |
| M14 | §Del modelo BIM al gemelo digital, caso IfM (pp. 6–7) | **Escena 2.4 · Gemelo digital.** Cinco capas apiladas en 3D (datos → procesamiento → modelos inteligentes → visualización → nube) sobre el modelo de REFRESH. **Tarjeta del caso IfM**: 2 bombas de agua helada, Revit → IFC4 extendido, tabla de correspondencia BIM–BMS–sensores, bayesiano contra CUSUM (2 falsas alarmas; casi una semana de retraso). No se modela el edificio de Cambridge | RP | IL (capas) · DF (tarjeta) | (Lu et al., 2020); (Hu et al., 2026, sección 6.1) · inf. pp. 6–7 |
| M14 | ídem: límites de la evidencia (prototipos, datos aislados; dos bombas) (p. 7) | Tarjeta 2.4a · Límites | PR | DF | (Hu et al., 2026); (Lu et al., 2020) · inf. p. 7 |
| M14 | Figura 2 · Marco del gemelo digital para el mantenimiento 4.0 (p. 7) | Imagen en la tarjeta 2.4, con crédito y licencia CC BY 4.0. Las capas 3D usan sus nombres | RP | DF | (Hu et al., 2026, Fig. 8) · inf. p. 7 |
| M14 | §Sistema MEP integrado para la planta REFRESH S.A. (pp. 8–9) | **Escena 2.5 · Sistema MEP.** En D: unidades interiores en el laboratorio QC y el comedor. En E: recepción, oficinas y sala de juntas. Además: unidad exterior VRF, tubería de refrigerante, unidad de aire exterior con su ducto, tableros de D y E con medidor y sala eléctrica/UPS del Edificio C. Etiquetas M1–M6 y C1–C4. **Animación**: aviso de filtro (M3) → controlador central → pasarela BACnet/IP → SCADA → tablero → orden de trabajo en el CMMS. **Paro forzado (C3)** desde el SCADA: se apagan todas las unidades interiores | RP | IL (ubicación de equipos y salas) · DF (componentes y puntos) | (Batista et al., 2026); (Thornton y Wagner, 2012, pp. 4–5); (Daikin Comfort Technologies North America, 2019, pp. 8, 24–26, 30–31) · inf. pp. 8–9 |
| M14 | Figura 3 · Esquema conceptual del sistema MEP integrado (p. 9) | La escena 2.5 reproduce la Figura 3: cuatro niveles (campo, automatización, supervisión, información) apilados sobre la planta. No se inserta la imagen | RP | DF (elaboración propia del informe) | Elaboración propia con base en Batista et al. (2026), Daikin (2019), Hu et al. (2026), Lu et al. (2020) y Thornton y Wagner (2012) · inf. p. 9 |
| M14 | ídem: dos condiciones; la potencia del VRF es calculada y no reemplaza al medidor; solo existen los puntos que se habilitan (pp. 8–9) | **Inspector 2.5a**: al hacer clic en cada punto M o C se ve qué es, qué equipo lo entrega y su condición. La unidad exterior muestra "potencia calculada (no medida)"; M5 muestra "medidor en el tablero (propuesto)". Sin valores numéricos | PR | DF | (Daikin Comfort Technologies North America, 2019, pp. 25, 30–31, 33) · inf. pp. 8–9 |
| M14 | ídem: protocolos Profibus, Profinet y EtherNet/IP; la integración BACnet ↔ SCADA queda por confirmar (pp. 8–9) | Tarjeta 2.5b · Condición de integración (la pasarela se ve con un aviso "por confirmar") | PR | DF | (Batista et al., 2026; PDF de REFRESH, p. 13) · inf. pp. 8–9 |
| M14 | §Propuesta de aplicación al proyecto REFRESH S.A. (p. 10) | **Escena 2.6 · Propuesta.** Tres "hojas" separadas (vista isométrica, P&ID, unifilar) se juntan en un modelo coordinado: el VRF pasa de volumen de reserva a LOD 350 junto a las tuberías de proceso, las bandejas y la estructura, y termina en as-built + COBie | RP | IL (animación) · DF (texto) | (Batista et al., 2026); (BIMForum, 2024) · inf. p. 10 |
| M14 | ídem: mantenimiento del VRF (filtros, serpentines, condensado; unidad exterior mínima; de calendario a condición) (p. 10) | Tarjeta 2.6a · Mantenimiento del VRF | PR | DF | (Thornton y Wagner, 2012, pp. 7, 18, 24); (Daikin, 2019); (Hu et al., 2026) · inf. p. 10 |
| M14 | ídem: riesgos (fugas difíciles de localizar; repuestos no intercambiables) (p. 10) | Tarjeta 2.6b · Riesgos. La tubería 3D parpadea a lo largo del edificio | PR | DF | (Thornton y Wagner, 2012, pp. 12, 25) · inf. p. 10 |
| M14 | Conclusiones 1–4 (pp. 10–11) | Tarjeta de cierre: cuatro frases enlazadas a las escenas 2.2, 2.3, 2.4 y Panamá | RP | DF | Citas de cada conclusión · inf. pp. 10–11 |
| M14 | Conclusión 4 · Panamá: sin iniciativa pública de BIM; BIM Fórum Panamá (p. 11) | Tarjeta 2.7 · Panamá | PR | DF | (Soto y Manríquez, 2023, pp. 17–18) · inf. p. 11 |
| M14 | Recomendaciones 1–2 (p. 11) | Tarjeta 2.8 · Recomendaciones (tabla LOD desde el anteproyecto; pedir la lista de puntos BACnet) | PR | DF | (BIMForum, 2024); (Daikin, 2019); (Thornton y Wagner, 2012) · inf. p. 11 |

**Cobertura:** las 7 secciones del Desarrollo del M6, sus 11 figuras y su Tabla 1, y las 6 secciones del Desarrollo del M14, sus Figuras 1–3 y sus Tablas 1 y 2, tienen cada una al menos un elemento.

---

## Lo que propongo dejar fuera y por qué

1. **El término "DALT"** del plan. El Word dice "prueba de fugas de los ductos" y no usa la sigla. Uso el texto del Word.
2. **Datos de la ficha que no están en el Word.** Del M14: D3060 y D8010 (BIMForum), "≈ doble de refrigerante", ASHRAE 15 y "evaluación basada en literatura" (Thornton y Wagner, 2012). Del M6, nada relevante. Si una ficha y su Word no coinciden, manda el Word.
3. **Barras por rejilla del caso Bogotá.** El informe solo trae los agregados; los 33 valores están en la tesis. Muestro la Figura 9 como imagen.
4. **El equipo de proceso de REFRESH** (torre, tanques, envasado) y sus datos (THD, capacidades, kVA). El M14 no los usa. Las naves quedan como volúmenes.
5. **La Figura 3 del M14 como imagen.** La escena 2.5 la reproduce en 3D; repetirla en imagen ocupa espacio sin aportar.
6. **Toda capacidad o lectura del VRF.** El inspector muestra qué entrega cada punto, nunca un valor.
7. **Imágenes del M6 en PNG original.** Suman unos 4 MB, y la Figura 6 sola pesa 2.1 MB. Propongo pasarlas a JPEG a unos 1,200 px de ancho, sin recortarlas, para que el HTML quede cerca de 3 MB. Esa compresión no modifica el contenido de la figura. Las Figuras 1 y 2 del M14 conviene dejarlas en PNG: la licencia CC BY-NC-ND pide no modificarlas.

## Dudas y choques entre el plan, las fichas y los Word

- **C1 · Balanceo "terminal por terminal" (plan).** En el Word (p. 7), el método de **proporción** iguala las relaciones **por pares** y deja la velocidad del ventilador para el final. El ajuste **un terminal a la vez** es el método de **flujo progresivo**. La animación del plan mezcla los dos. Propongo animar los dos métodos, en el orden de la tabla de arriba, con el contador de 14 contra 10. Ver panel asesor A.
- **C2 · Cifras del control de velocidad.** El informe da las leyes (∝ N, N², N³) y una sola cifra: −20 % de velocidad ≈ −50 % de potencia. Si el control muestra porcentajes calculados (por ejemplo, 0.8³ = 51.2 %), esas cifras no están en el informe. Ver panel asesor B.
- **C3 · Choque con la prueba de "Henríquez".** El crédito de la Figura 11 y la referencia del M6 nombran a **F. Henríquez**, coautor de Gollini-Mihalopoulos et al. (2023). No es Henríquez Espinosa (2021), la fuente del Edificio 2. Con la prueba tal como la pediste, el crédito obligatorio de la Figura 11 hace fallar el build. Propongo prohibir **"Henríquez Espinosa"** en lugar de "Henríquez". Otra opción es abreviar el crédito como "Gollini-Mihalopoulos et al., 2023", pero el crédito del Word dejaría de ser textual.
- **C4 · Distribución interior de D y E.** Tú indicaste que no está en el proyecto, pero el plano general del PDF (p. 21) dibuja el orden de las salas. En D, de norte a sur: laboratorio QC, comedor, baños/lockers de hombres, baños/lockers de mujeres y taller. En E, de oeste a este: recepción, oficinas y sala de juntas. Lo que no trae son las medidas de cada sala. Propongo sellar como DF el **orden** (Batista et al., 2026, p. 21) y como IL los **tamaños** y la ubicación de las unidades interiores.
- **C5 · El simulador contradice al PDF en la ubicación de los edificios.** En `data.js`, E queda al norte junto al estacionamiento, D al sureste de la Nave A y C girado al este. En el plano del PDF (p. 21), D, C y E forman una columna al oeste (D al norte, C al centro, E al sur), con el lado largo en dirección norte–sur. La Nave A está al centro-norte, la Nave B al centro-sur, los silos y la descarga al norte, las bahías al sur y la expansión al este. Uso el PDF.
- **C6 · Alturas.** El PDF solo da 22 m para la Nave A en la zona de la torre (p. 22). Las alturas del simulador (B 10 m, C 8 m, D 6 m, E 5 m) no salen del PDF y se sellan IL. La nota visible diría: "Modelo conceptual, no a escala; planta y dimensiones de REFRESH: Batista et al. (2026)".
- **C7 · Diferencias entre ficha y Word (manda el Word).** M14, Tabla 2: USD 9,093 millones (la ficha dice 9,093.3), y la parte de propietarios y operadores en la p. ES-7 (la ficha dice ES-6). El Word agrega USD 96.9 millones (el edificio médico) y "≈ USD 500,000 de un contrato de ≈ USD 9.4 millones", que la ficha no trae. M6: el nombre del archivo (la ficha nombra `M6_…_Cristian_Batista.docx`; el final es `M06_Mantenimiento_Ventiladores_Distribucion.docx`, por tu indicación).
- **C8 · LOD con un solo objeto.** El plan anima solo la unidad exterior, pero la Tabla 1 usa la tubería y los soportes en los LOD 350 y 400, y la Figura 1 va solo del 200 al 400. Propongo animar la unidad y un tramo de tubería. El LOD 500 se representa con un sello "verificado en campo", porque el informe dice que no es un nivel superior al 400.
- **C9 · Escena 2.1 (coordinación).** Si la hago sobre REFRESH, parecería que REFRESH tuvo interferencias, lo que nadie afirma. Propongo un tramo de cielo raso genérico, sellado IL, fuera de la planta.
- **D1 · Páginas del M14.** LibreOffice da 12 páginas y la ficha dice 13. Las páginas del M14 en esta matriz pueden estar corridas por una. ¿Me envías el PDF exportado del Word final, o confirmas las páginas de las Figuras 1–3 y de las Tablas 1 y 2?
- **D2 · Plan, mantenimiento del VRF.** El plan lo cita a Thornton y Wagner; en el Word está en la sección "Propuesta de aplicación" (p. 10). Lo enlazo a esa sección.

### Panel asesor A · Cómo animar el balanceo (C1)
- ⚙️ **Operador:** las dos animaciones usan la misma red de 8 terminales. Solo cambia el guion: unas 2 horas más que una sola animación.
- 🛡️ **Escéptico:** animar la proporción "terminal por terminal" contradice la p. 7 y la Tabla 1, y una pregunta de la profesora lo dejaría en evidencia.
- 🔭 **Visionario:** ver los dos métodos uno tras otro convierte el "14 contra 10" en algo visible.
- 🎯 **Defensor del usuario:** en 7–8 minutos no caben las dos animaciones completas. La proporción va en la ruta principal y el flujo progresivo en una versión acelerada.
- 📊 **Mente financiera:** el costo marginal es bajo, porque la red se reutiliza.
- **Síntesis:** animar los dos métodos fieles al Word, con las barras sin escala numérica y la franja de ±5 % como único dato (Yale Facilities, 2025, §4.3A). El costo es poco más de tiempo; a cambio, se elimina un error de contenido.

### Panel asesor B · Números en el control de velocidad (C2)
- ⚙️ **Operador:** las curvas sin números son triviales; con números, también.
- 🛡️ **Escéptico:** "51.2 %" no aparece en el informe, y la regla dice que un número en pantalla es un dato.
- 🔭 **Visionario:** el control con números es la escena más interactiva del M6.
- 🎯 **Defensor del usuario:** la audiencia necesita ver que la potencia cae más rápido que el caudal, y eso se ve sin decimales.
- 📊 **Mente financiera:** el costo es igual en las dos opciones; el riesgo está solo en la versión con números.
- **Síntesis (recomendada):** barras relativas sin cifras, con el único rótulo numérico en el punto del 80 %: "−20 % de velocidad ≈ −50 % de potencia (DOE y AMCA, 2003, p. 18)". Si prefieres porcentajes calculados, irían con el sello "Cálculo con las leyes de los ventiladores (DOE y AMCA, 2003, p. 4)" y entrarían en `CIFRAS_EN_PANTALLA.md` como cálculo.

---

## Geometría de REFRESH: qué se adapta y cómo

Origen: `origin/claude/spanish-greeting-CWfoM:asignacion-6-distribucion-planta/plano3d.js` y `data.js`. Los leí con `git show`; esa rama no se trae a la nuestra.

| Elemento | Del simulador | Cómo se adapta |
|---|---|---|
| Terreno, vial perimetral e interior | `BoxGeometry` 100 × 100 y franja de vial | Se reescribe como módulo ES con `vendor/three.module.js` (r184). Terreno de 100 × 100 m y vial de 7.00 m (PDF p. 22) |
| Edificios | `cajaMalla()` (caja + `EdgesGeometry`) | Misma técnica. **Dimensiones de la tabla del PDF (p. 22) y ubicación del plano (p. 21)**, no de `data.js` (ver C5). Alturas: Nave A, 22 m (dato); el resto, IL |
| Pasarela A–B | Caja de 3 × 4 × 8 | Se conserva el ancho de 3.00 m (PDF p. 23); la longitud sale del plano |
| Patio de silos | 4 cilindros con cono | Se conservan Ø 2.50 m (PDF p. 22); la altura es IL. `InstancedMesh` |
| Zona de descarga y estacionamiento | Losas planas | Losas de 15 × 6 m y 30 puestos (PDF p. 22), sin autos |
| Equipos de proceso, partículas de flujo, P&ID, unifilar | Varios | **No se adaptan** (fuera del M14) |
| Salas de D y E | No existen en el simulador | Particiones bajas con el orden del plano (p. 21), en el orden indicado en C4; tamaños IL |
| Equipos del VRF y puntos M/C | No existen | Geometría propia y baja; ubicación IL |

No se copia `lib/three.min.js` (r128) ni ningún código que dependa de él. Las coordenadas se convierten del plano (x, y) a three.js (x − 50, altura, y − 50), como en el original.
