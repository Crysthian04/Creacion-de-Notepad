# Matriz de trazabilidad — Modelo 3D de los laboratorios del Grupo A (M6, M14, M8, M11)

Estado actual: Paradas 1 y 2 (Cristian Batista) **aprobadas en la ronda 5, 25/10/2026** (hora de Panamá, UTC−5), congeladas en `labs-3d-v1.0`. Paradas 3 y 4 (Manuel Jiménez): **en revisión** (versión candidata `labs-3d-v2.0-rc`, 28/10/2026). La primera aprobación de la matriz fue el 24/10/2026, con las correcciones de la revisión 3 incorporadas.

Fuentes: Word final del M6 (`M06_Mantenimiento_Ventiladores_Distribucion.docx`, 17 págs.), Word final del M14 (`M14_Digitalizacion_BIM_Gestion_MEP.docx`), las dos fichas de `docs/` y el PDF del Proyecto Final Integrador de REFRESH S.A. (33 págs.).

- **Referencia al informe**: por sección, figura o tabla (p. ej., "M14 · Tabla 1"). **No se citan páginas de los informes**, porque cambian según el programa y en el compendio (decisión del 24/10).
- **Páginas**: solo de las fuentes originales (la obra citada o el PDF de REFRESH), tomadas del Word o de la ficha.
- **Nivel**: **RP** = ruta principal · **PR** = profundización.
- **Sellos**: **DF** = "Dato de fuente (cita)" · **IL** = "Ilustrativo". Muchos elementos llevan los dos: el objeto 3D es IL y el texto de su tarjeta es DF.

---

## Parada 0 · Inicio (tecla 0)

| Informe | Sección/figura/tabla | Elemento del 3D | Nivel | Sello | Cita (página de la fuente original) |
|---|---|---|---|---|---|
| — | Portadas (p. 1 de cada Word) | Pantalla de inicio: título de los dos módulos, asignatura, Grupo A, autor. Botones 1 y 2. Nota "Modelo conceptual, no a escala" | RP | — | Sin cifras |

## Parada 1 · M6 — Mantenimiento de Ventiladores y Sistemas de Distribución (tecla 1)

> **Nota (desde la ronda 4).** La ruta principal de esta parada son las escenas E1–E4 (ver «Ronda 4» y «Ronda 5»). La numeración 1.0–1.8 (y P1–P9) que sigue corresponde a la profundización: todos esos pasos se conservan en la pestaña «Profundización».

**Numeración en pantalla** (programada el 24/10/2026). Ruta principal: 1.0 Ventilador y red (escena 1.0) · 1.1 Quién hace el TAB y cuándo se acepta (tarjeta 1.1 y ±5 %) · 1.2 Antes del TAB (escena 1.2) · 1.3 Método de proporción y 1.4 Flujo progresivo (escena 1.3, tarjetas 1.3b y 1.3c, Figura 5) · 1.5 Compuertas abiertas y velocidad (escena 1.4a) · 1.6 Leyes de los ventiladores (escena 1.4b, Figura 7) · 1.7 Panamá (escena 1.6, Figura 11) · 1.8 Conclusiones. Profundización: P1 NEBB, reporte y verificación (1.1 detalle) · P2 Hermeticidad (1.2a) · P3 Correas (1.2b, Figura 3) · P4 Presión (1.2c, Figura 4) · P5 Medir el caudal (1.3a; la **Figura 6** va aquí, donde el Word la introduce, y no en Bogotá) · P6 Efecto de sistema (1.4c, Figura 8) · P7 Kleberg (1.5a, Figura 10) · P8 Bogotá (1.5b, Figura 9; sin barras por rejilla) · P9 Marco panameño (1.6a). Las figuras se abren con «Ver figura»; el crédito exacto del Word queda debajo de la imagen. La Tabla 1 completa se abre con «Ver Tabla 1 completa» desde el paso 1.4.

| Informe | Sección/figura/tabla | Elemento del 3D | Nivel | Sello | Cita (página de la fuente original) |
|---|---|---|---|---|---|
| M6 | Introducción | **Escena 1.0 · Ventilador y red.** Ventilador con correas, filtro, serpentín, ducto principal con ramales, compuertas y 8 terminales. Tarjeta de apertura: qué es el TAB (prueba, ajuste, balanceo) y "casi el 60 %" de la electricidad del país en el sector comercial y las oficinas públicas | RP | IL (escena) · DF (tarjeta) | (Consejo de Gabinete, 2022, p. 34); (U.S. Department of Energy [DOE] y Air Movement and Control Association International [AMCA], 2003) — única vez con la sigla definida; en el resto: (DOE y AMCA, 2003); (Pedranzini et al., 2013, p. 322) |
| M6 | Figura 1 · *Example Fan System Components* | Imagen en la tarjeta de la escena 1.0, con crédito. Las piezas 3D (filtro, serpentín, ventilador, ductos, compuertas, difusores) siguen esa lista | RP | DF | (DOE y AMCA, 2003, p. 10) |
| M6 | §El TAB y su marco normativo: NEBB, AABC y TABB | **Tarjeta 1.1 · Quién hace el TAB.** Empresa AABC, NEBB o TABB, contratada aparte del contratista mecánico; procedimientos AABC MN-1, NEBB y SMACNA 1780; requisitos previos de NEBB; contenido del reporte | RP (resumen) · PR (detalle NEBB y reporte) | DF | (Yale Facilities, 2025); (NEBB, 2019, como se citó en Guzmán Solano, 2025); (Guzmán Solano, 2025, pp. 51–52) |
| M6 | ídem, criterio de aceptación | **Franja de ±5 % en cada terminal** (se usa en la escena 1.3). Tarjeta de verificación: se vuelven a medir el 25 % de los terminales; el reporte se rechaza si el 10 % o más se desvía 10 % o más | RP (±5 %) · PR (25 % y rechazo) | DF | (Yale Facilities, 2025, §4.3A, p. 23; pp. 1, 29) |
| M6 | Figura 2 · Secuencia del proceso TAB | **Barra de pasos de la parada**: contratación → pruebas previas → balanceo → verificación. La figura se muestra en la tarjeta 1.1 con su crédito | RP | DF | Elaboración propia a partir de (Yale Facilities, 2025) y (Guzmán Solano, 2025) |
| M6 | §Pruebas previas: limpieza, hermeticidad y estado del ventilador | **Escena 1.2 · Antes del TAB.** Se reemplaza el filtro sucio por uno limpio; prueba de fugas del ducto (las uniones se iluminan); revisión de correas y poleas. Animación de una compuerta trabada abierta que le "roba" caudal a los demás ramales | RP | IL (animación) · DF (texto) | (Yale Facilities, 2025); (DOE y AMCA, 2003) |
| M6 | ídem, clase de fuga CL 48 → 24 → 6 (12 y 3 en redondos); pruebas en sistemas de más de 2 o 3 in wg | Tarjeta 1.2a · Hermeticidad: tres estados del ducto (sin sellar, juntas transversales selladas, todo sellado) | PR | DF | (DOE y AMCA, 2003, p. 38; p. 12) |
| M6 | ídem, correas 5 %–10 %; 200 hp → 10 hp ≈ USD 3,270/año a USD 0.05/kWh; lista de mantenimiento | Tarjeta 1.2b · Correas y lista de mantenimiento | PR | DF | (DOE y AMCA, 2003, p. 25) |
| M6 | Figura 3 · (a) *Proper Belt Tension*; (b) *Improper Alignment* | Imagen en la tarjeta 1.2b, con crédito | PR | DF | (DOE y AMCA, 2003, pp. 49–50) |
| M6 | ídem, medición de presión según la conexión a ductos | Tarjeta 1.2c · Medición de presión: tomas en la entrada y la salida del ventilador 3D | PR | DF | (DOE y AMCA, 2003, p. 57) |
| M6 | Figura 4 · *Alternative Methods of Measuring Fan Pressure* | Imagen en la tarjeta 1.2c, con crédito | PR | DF | (DOE y AMCA, 2003, p. 58) |
| M6 | §Métodos de balanceo: proporción frente a flujo progresivo | **Escena 1.3 · Balanceo, dos métodos.** (a) **Método de proporción**: se abren todas las compuertas, se igualan las relaciones caudal medido/caudal de diseño por pares, empezando por los dos terminales más desfavorecidos, y al final se ajusta la velocidad del ventilador; es iterativo. (b) **Método de flujo progresivo**: un terminal a la vez, directamente a su caudal de diseño, desde el último terminal hacia el ventilador, con variador y lazo de control. **Contador de pasos con el texto del Word**: "10 pasos frente a 14 del método de proporción" (flujo progresivo = 10; proporción = 14). **Meta**: "dentro de ±5 % de los caudales de diseño". Barras sin escala numérica; la franja de ±5 % es el único dato | RP | IL (red y barras) · DF (procedimientos, pasos y meta) | (Pedranzini et al., 2013, pp. 323, 325, 328); (Yale Facilities, 2025, §4.3A, p. 23; p. 26) |
| M6 | ídem, medición del caudal con anemómetro o tubo de Pitot | Tarjeta 1.3a · Medir no es trivial: el técnico mide en una rejilla con varias lecturas | PR | DF | (Pedranzini et al., 2013); (Cristiano Mendivelso y Hernández Romero, 2023, pp. 122–125) |
| M6 | ídem, banco de 8 terminales, 100–200 m³/h, 200–650 Pa; 2n + b − 1 mediciones evitadas, 57 %–67 % | Tarjeta 1.3b · El banco de prueba (la red 3D tiene 8 terminales por esta razón) | RP | DF | (Pedranzini et al., 2013, pp. 322, 325, 329) |
| M6 | Tabla 1 · Comparación de los métodos de proporción y de flujo progresivo | Tarjeta 1.3c con la Tabla 1 completa (6 criterios), incluida la limitación "validado en un banco de laboratorio a escala, no en un edificio" | RP | DF | (Pedranzini et al., 2013, pp. 323–329) |
| M6 | Figura 5 · (a) *Schematic layout of the reference air distribution network*; (b) *Scheme of the control loop* | Imagen en la tarjeta 1.3c, con crédito. El lazo de control se dibuja en 3D durante el flujo progresivo | RP | DF | (Pedranzini et al., 2013, p. 326) |
| M6 | Figura 6 · Mediciones del proceso de validación, Bogotá | Imagen en la tarjeta 1.5b (caso Bogotá), con crédito | PR | DF | (Cristiano Mendivelso y Hernández Romero, 2023, p. 132) |
| M6 | §Del balanceo al consumo de energía, ΔP = R·Q² y apertura máxima | **Escena 1.4a · Compuerta abierta y velocidad.** Con el mismo caudal: compuertas casi cerradas y ventilador rápido contra compuertas abiertas y ventilador más lento. El último paso del TAB se hace en el ventilador (velocidad, poleas o variador) | RP | IL (animación) · DF (texto) | (Pedranzini et al., 2013, pp. 323–324); (Yale Facilities, 2025, p. 28) |
| M6 | ídem, leyes de los ventiladores | **Escena 1.4b · Leyes de los ventiladores.** Control de velocidad con tres barras relativas **sin cifras**: caudal ∝ N, presión ∝ N², potencia ∝ N³. **Un solo rótulo**, con la redacción exacta del Word: "Reducir la velocidad del ventilador un 20 % disminuye su potencia un 50 %" | RP | DF | (DOE y AMCA, 2003, p. 4; p. 18 para el rótulo) |
| M6 | Figura 7 · Caudal, presión y potencia en función de la velocidad | Imagen en la tarjeta 1.4b, con crédito; las curvas del control 3D son las mismas | RP | DF | Elaboración propia con (DOE y AMCA, 2003, p. 4) |
| M6 | ídem, efecto de sistema: codo en la salida, hasta −30 % de caudal; sobredimensionamiento | Tarjeta 1.4c · Efecto de sistema: un codo pegado a la salida del ventilador 3D | PR | DF | (DOE y AMCA, 2003, p. 9) |
| M6 | Figura 8 · *System Effect for a Typical Fan and System* | Imagen en la tarjeta 1.4c, con crédito | PR | DF | (DOE y AMCA, 2003, p. 9) |
| M6 | §Evidencia de campo, Bogotá: 33 rejillas, error promedio de 7.8 %, 17 de 33 fuera de ±5 %, 6 por encima del 10 %, 74 % (60 → 105 CFM), 5.7 % sin ese caso | Tarjeta 1.5b · "El promedio oculta la dispersión". Sin barras por rejilla: el informe no trae los 33 valores | PR | DF (cálculo propio del informe) | Elaboración propia con datos de (Cristiano Mendivelso y Hernández Romero, 2023, pp. 137–138) |
| M6 | Figura 9 · Desviación del caudal en las 33 rejillas | Imagen en la tarjeta 1.5b, con crédito | PR | DF | Elaboración propia con la Tabla 29 de (Cristiano Mendivelso y Hernández Romero, 2023, pp. 137–138) |
| M6 | ídem, Kleberg: ≈ 165,030 ft²; presión estática de 1.5 a 1.0 in wg (0.5 de noche); agua helada −63.6 %, agua caliente −84.2 %; balance de aire 1998–1999 ≈ −7 % de electricidad, ≈ 30,000 kWh/mes | Tarjeta 1.5a · Caso Kleberg | PR | DF | (Claridge et al., 2003) |
| M6 | Figura 10 · *Pre-CC and post-CC heating water consumption at the Kleberg Building…* | Imagen en la tarjeta 1.5a, con crédito | PR | DF | (Claridge et al., 2003, Figura 1) |
| M6 | ídem, seguimiento: en 2000 el ahorro de agua helada bajó a 37.7 %; 44 edificios, 2 %–49 %, promedio de 17.5 %, retorno de 0.1–4.2 años; ninguna fuente aísla el TAB | Tarjeta 1.5a (continuación) · "Sin seguimiento, el ahorro se pierde" | PR | DF | (Claridge et al., 2003); (Gregerson, 1997, como se citó en Claridge et al., 2003) |
| M6 | §Aplicación al contexto panameño, Edificio N.° 1 de la UTP: 72.90 % de 2,404,170.72 kWh/año; −35 % en el motor de una manejadora (simulación); 14.10 %, 352,224 kWh y B/. 53,777.56 al año | **Escena 1.6 · Panamá.** Tarjeta grande con las cifras y la aclaración "simulación y cambio a VAV, no un TAB". No se modela el edificio | RP | DF | (Gollini-Mihalopoulos et al., 2023, pp. 143, 146, 148) |
| M6 | Figura 11 · Modelo energético del Edificio N°1 antes de simulación | Imagen en la tarjeta 1.6, con crédito | RP | DF | (Gollini-Mihalopoulos et al., 2023, p. 143). El crédito con F. Henríquez se mantiene (C3) |
| M6 | ídem, marco normativo: Res. N.° 3142 de 2016 (nuevas edificaciones, 15 % y 20 %, variadores en UMA, sin requisitos de ductos, filtros ni balanceo); ENUREE; Ley 69 de 2012 (comité de energía, plan de 5 años revisado cada año) | Tarjeta 1.6a · Marco panameño y "el lugar práctico para un TAB periódico" | PR | DF | (Secretaría Nacional de Energía, 2016, p. 21); (Consejo de Gabinete, 2022, pp. 58, 60); (Asamblea Nacional, 2012, arts. 8 y 23) |
| M6 | Conclusiones 1–5 | Tarjeta de cierre de la parada: cinco frases cortas, cada una enlazada a su escena (1.3, 1.2, 1.3, 1.4, 1.6). Sin datos nuevos | RP | DF | Citas de cada conclusión |
| M6 | Referencias | **Vista "Referencias" (M6)**: la lista de referencias del Word copiada tal cual (10 obras, APA 7). Toda obra citada en pantalla está en ella. Los créditos de las figuras usan el texto exacto del Word ("Tomado de…, por…" / "Elaboración propia…") | PR | — | Lista de referencias del Word del M6 |

## Parada 2 · M14 — Digitalización, BIM y Gestión Inteligente de Instalaciones (MEP) (tecla 2)

> **Nota (desde la ronda 4).** La ruta principal de esta parada son las escenas E1–E4 (ver «Ronda 4» y «Ronda 5»). La numeración 2.0–2.7 (y P1–P7) que sigue corresponde a la profundización: todos esos pasos se conservan en la pestaña «Profundización».

**Numeración en pantalla** (programada el 24/10/2026). Ruta principal: 2.0 La planta REFRESH S.A. (apertura y escena base) · 2.1 Coordinación (escena 2.1) · 2.2 LOD (escena 2.2, tarjeta 2.2a, Figura 1 y Tabla 1) · 2.3 Ventajas (Tabla 2; las filas aparecen una a una, sin contadores que muestren cifras intermedias) · 2.4 Gemelo digital (escena 2.4, Figura 2 y rótulo «Marco general (Hu et al., 2026); en REFRESH es una propuesta») · 2.5 Sistema MEP (escena 2.5, Figura 3, rótulos «medidor propuesto» en los tableros de D y E) · 2.6 Propuesta · 2.7 Conclusiones. Profundización: P1 Inspector de puntos (2.5a) · P2 Condición de integración (2.5b) · P3 Límites de la evidencia (2.4a) · P4 Mantenimiento del VRF (2.6a) · P5 Riesgos (2.6b) · P6 Panamá (2.7) · P7 Recomendaciones (2.8). Los niveles 2–4 de la Figura 3 y las capas del marco de Hu et al. se dibujan como esquema flotante, con el rótulo «no es una ubicación física».

Escena base: la planta REFRESH S.A. con las dimensiones del PDF (terreno 100 × 100 m; Nave A 40 × 20 m; Nave B 30 × 18 m; Edificio C 24 × 12 m; Edificio D 25 × 12 m; Edificio E 20 × 10 m; zona de descarga 15 × 6 m; patio de silos 15 × 10 m), sello DF (Batista et al., 2026, p. 22), y la ubicación del plano general, sello DF (Batista et al., 2026, p. 21). Alturas: los **22 m son solo de la zona de la torre de la Nave A** (DF, p. 22); el resto de la Nave A y los demás edificios llevan altura IL. Salas de D y E: el **orden** es DF (Batista et al., 2026, p. 21) y los **tamaños** son IL.

| Informe | Sección/figura/tabla | Elemento del 3D | Nivel | Sello | Cita (página de la fuente original) |
|---|---|---|---|---|---|
| M14 | Introducción: USD 15,824 millones (2002), ≈ dos tercios para propietarios y operadores; BIM como repositorio y gemelo digital | Tarjeta de apertura de la parada sobre la vista aérea de REFRESH | RP | DF | (Gallaher et al., 2004, p. ES-6); (Hu et al., 2026) |
| M14 | §La metodología BIM aplicada a sistemas HVAC-R | **Escena 2.1 · Coordinación.** Tramo de cielo raso **genérico** (no es REFRESH): los modelos de HVAC, eléctrico, plomería y estructura se superponen; se resaltan interferencias en rojo y se resuelven, con el ducto de HVAC como prioridad. Tarjeta: edificio médico de USD 96.9 millones en California; el contratista de HVAC lideró; elementos no modelados (acabados, mobiliario, soportes) causaron conflictos | RP | IL (escena) · DF (tarjeta) | (BIMForum, 2024); (Khanzode et al., 2008, pp. 328–329, 339–340) |
| M14 | §Niveles de desarrollo (LOD): definiciones 100–500; el LOD no es el nivel de detalle; requisitos acumulativos salvo el 500 | **Escena 2.2 · LOD.** La unidad exterior del VRF y un tramo de su tubería, junto al Edificio E, pasan por LOD 100 ("Espacio reservado para la unidad exterior junto a los Edificios D y E", texto de la Tabla 1), 200, 300 (con espacios de servicio), 350 (tubería y soportes coordinados), 400 (derivaciones y soportes) y 500 (as-built verificado; se muestra con un sello de verificación, no como "más detalle") | RP | IL (objeto) · DF (texto de cada paso) | (BIMForum, 2024, pp. 12–13) |
| M14 | ídem: no existe un "modelo LOD 300"; el LOD es solo geometría y los datos van por COBie | Tarjeta 2.2a · Dos aclaraciones para mantenimiento | RP | DF | (BIMForum, 2024, pp. 11, 195) |
| M14 | Figura 1 · Progresión del LOD 200 al LOD 400 (D3030.10) | Imagen sin modificar en la tarjeta 2.2, con crédito y licencia CC BY-NC-ND 4.0 | RP | DF | (BIMForum, 2024, p. 128) |
| M14 | Tabla 1 · Elementos del VRF de REFRESH por LOD | Texto de cada paso de la escena 2.2 (columnas Contenido, Ejemplo y Utilidad), más la nota "asignación D3030.10 / D3050.50 = interpretación del grupo" | RP | DF | (BIMForum, 2024) |
| M14 | §Ventajas cuantificadas | **Escena 2.3 · Ventajas.** Tarjeta con contadores animados que se llenan con las cifras de la Tabla 2 | RP | DF | (Khanzode et al., 2008, pp. 336–339) |
| M14 | Tabla 2 · Ventajas cuantificadas y costo de la falta de interoperabilidad | Las 8 filas de la Tabla 2 en la escena 2.3, con su nota (un solo proyecto; estimaciones para EE. UU.) | RP | DF | (Khanzode et al., 2008, pp. 336–339); (Gallaher et al., 2004, pp. ES-6, ES-7) |
| M14 | §Del modelo BIM al gemelo digital, caso IfM | **Escena 2.4 · Gemelo digital.** Cinco capas apiladas en 3D (datos → procesamiento → modelos inteligentes → visualización → nube) sobre el modelo de REFRESH, con el rótulo visible **"Marco general (Hu et al., 2026); en REFRESH es una propuesta"**. **Tarjeta del caso IfM**: 2 bombas de agua helada, Revit → IFC4 extendido, tabla de correspondencia BIM–BMS–sensores, bayesiano contra CUSUM (2 falsas alarmas; casi una semana de retraso). No se modela el edificio de Cambridge | RP | IL (capas) · DF (tarjeta) | (Lu et al., 2020); (Hu et al., 2026, sección 6.1) |
| M14 | ídem: límites de la evidencia (prototipos, datos aislados; dos bombas) | Tarjeta 2.4a · Límites | PR | DF | (Hu et al., 2026); (Lu et al., 2020) |
| M14 | Figura 2 · Marco del gemelo digital para el mantenimiento 4.0 | Imagen en la tarjeta 2.4, con crédito y licencia CC BY 4.0. Las capas 3D usan sus nombres | RP | DF | (Hu et al., 2026, Fig. 8) |
| M14 | §Sistema MEP integrado para la planta REFRESH S.A. | **Escena 2.5 · Sistema MEP.** Unidades interiores **solo donde las pone la Figura 3**: en E, recepción, oficinas y sala de juntas; en D, laboratorio QC y comedor. **Baños/lockers y taller de D aparecen sin equipos.** Además: unidad exterior VRF, tubería de refrigerante, unidad de aire exterior con su ducto, tableros de D y E con el rótulo visible **"medidor propuesto"** (en la ruta principal, no solo en el inspector) y sala eléctrica/UPS del Edificio C. Etiquetas M1–M6 y C1–C4 como en la Figura 3. **Animación**: aviso de filtro (M3) → controlador central → pasarela BACnet/IP → SCADA → tablero → orden de trabajo en el CMMS. **Paro forzado (C3)** desde el SCADA: se apagan todas las unidades interiores | RP | IL (ubicación de equipos y tamaño de salas) · DF (componentes, puntos y orden de salas) | (Batista et al., 2026, p. 21); (Thornton y Wagner, 2012, pp. 4–5); (Daikin Comfort Technologies North America, 2019, pp. 8, 24–26, 30–31) |
| M14 | Figura 3 · Esquema conceptual del sistema MEP integrado | La escena 2.5 reproduce la Figura 3: cuatro niveles (campo, automatización, supervisión, información) apilados sobre la planta. No se inserta la imagen | RP | DF (elaboración propia del informe) | Elaboración propia con base en Batista et al. (2026), Daikin Comfort Technologies North America (2019), Hu et al. (2026), Lu et al. (2020) y Thornton y Wagner (2012) |
| M14 | ídem: dos condiciones; la potencia del VRF es calculada y no reemplaza al medidor; solo existen los puntos que se habilitan | **Inspector 2.5a**: al hacer clic en cada punto M o C se ve qué es, qué equipo lo entrega y su condición. La unidad exterior muestra "potencia calculada (no medida)"; M5 muestra "medidor en el tablero (propuesto)". Sin valores numéricos | PR | DF | (Daikin Comfort Technologies North America, 2019, pp. 25, 30–31, 33) |
| M14 | ídem: protocolos Profibus, Profinet y EtherNet/IP; la integración BACnet ↔ SCADA queda por confirmar | Tarjeta 2.5b · Condición de integración (la pasarela se ve con un aviso "por confirmar") | PR | DF | (Batista et al., 2026, p. 13) |
| M14 | §Propuesta de aplicación al proyecto REFRESH S.A. | **Escena 2.6 · Propuesta.** Tres "hojas" separadas (vista isométrica, P&ID, unifilar) se juntan en un modelo coordinado: el VRF pasa de volumen de reserva a LOD 350 junto a las tuberías de proceso, las bandejas y la estructura, y termina en as-built + COBie | RP | IL (animación) · DF (texto) | (Batista et al., 2026); (BIMForum, 2024) |
| M14 | ídem: mantenimiento del VRF (filtros, serpentines, condensado; unidad exterior mínima; de calendario a condición) | Tarjeta 2.6a · Mantenimiento del VRF | PR | DF | (Thornton y Wagner, 2012, pp. 7, 18, 24); (Daikin Comfort Technologies North America, 2019); (Hu et al., 2026) |
| M14 | ídem: riesgos (fugas difíciles de localizar; repuestos no intercambiables) | Tarjeta 2.6b · Riesgos. La tubería 3D parpadea a lo largo del edificio | PR | DF | (Thornton y Wagner, 2012, pp. 12, 25) |
| M14 | Conclusiones 1–4 | Tarjeta de cierre: cuatro frases enlazadas a las escenas 2.2, 2.3, 2.4 y Panamá | RP | DF | Citas de cada conclusión |
| M14 | Conclusión 4 · Panamá: sin iniciativa pública de BIM; BIM Fórum Panamá | Tarjeta 2.7 · Panamá | PR | DF | (Soto y Manríquez, 2023, pp. 17–18) |
| M14 | Referencias | **Vista "Referencias" (M14)**: la lista de referencias del Word copiada tal cual (9 obras, APA 7). Créditos de las Figuras 1 y 2 con el texto exacto del Word ("Tomado de…, por…", con licencia) | PR | — | Lista de referencias del Word del M14 |
| M14 | Recomendaciones 1–2 | Tarjeta 2.8 · Recomendaciones (tabla LOD desde el anteproyecto; pedir la lista de puntos BACnet) | PR | DF | (BIMForum, 2024); (Daikin Comfort Technologies North America, 2019); (Thornton y Wagner, 2012) |

**Cobertura:** las 7 secciones del Desarrollo del M6, sus 11 figuras y su Tabla 1, y las 6 secciones del Desarrollo del M14, sus Figuras 1–3 y sus Tablas 1 y 2, tienen cada una al menos un elemento.

---

## Parada 3 · M8 — Aplicaciones Avanzadas de Refrigeración y Aire Acondicionado: District Cooling (tecla 3)

Autor: **Manuel Jiménez**. Fuente única: Word del M8 (`M08_Aplicaciones_Avanzadas_Refrigeracion_AA.docx`). Las citas van con la forma del Word: (ASHRAE, 2024), (IDEA, 2023), (TRABEED, 2024), (EMPOWER, 2024). **Ninguna cifra del Word se muestra** (temperaturas de suministro y retorno, ahorro del 20–50 %, COP, vida útil). Sin figuras ni infografías del Word, sin marcas comerciales. Escena base: ciudad genérica con sello «Ilustrativo» (no es Panamá real, ni REFRESH, ni la UTP).

> **Ruta principal:** escenas E1–E4. La numeración 3.0–3.5 corresponde a la profundización.

| Informe | Sección | Elemento del 3D | Nivel | Sello | Cita |
|---|---|---|---|---|---|
| M8 | Fundamentos · Componentes | **E1 · Una planta para muchos edificios.** Planta central con chillers, torres de enfriamiento, bombas, tanque de almacenamiento térmico y sala de control. Rótulo: «Una planta central enfría agua con chillers y la distribuye por una red de tuberías a varios edificios». Chips 3.0, 3.1 | RP | DF (rótulo) · IL (objetos) | (ASHRAE, 2024)* |
| M8 | Red de distribución | **E2 · Frío que sale, calor que vuelve.** Red enterrada: suministro azul, retorno rojo; el agua cambia de color en cada estación; flujo en bucle; sin temperaturas. Rótulo: «El agua fría viaja por tuberías aisladas y regresa más caliente a la planta, donde se enfría de nuevo». Chip 3.2 | RP | DF · IL | (ASHRAE, 2024; IDEA, 2023)* |
| M8 | Fundamentos · Estaciones de intercambio | **E3 · La estación de cada edificio.** Corte del podio comercial: intercambiador de placas, válvulas de control, medidor de energía térmica, circuito del edificio y fan coil; el aire de la sala se enfría (bucle). Rótulo: «En cada edificio, el agua fría absorbe el calor en un intercambiador y retorna a la planta». Chip 3.3 | RP | DF · IL | (ASHRAE, 2024)* |
| M8 | Potencial de implementación en Panamá | **E4 · ¿Y en Panamá?** La misma ciudad genérica con cuatro zonas que aparecen una a una y se quedan (↺ Repetir): Área Bancaria, Ciudad de la Salud, Tocumen y Ciudad del Saber. Rótulo: «El informe propone zonas de alta densidad y demanda continua…». Chips 3.4, 3.5 | RP | «Propuesta · M8» | Sin cita (propuesta del informe) |
| M8 | Fundamentos del District Cooling | **3.0 Fundamentos.** Definición, intercambio en cada edificio, retorno a la planta, unidades TR y MWt (sin valores) | PR | DF | (ASHRAE, 2024)* |
| M8 | Componentes principales · Planta central | **3.1 Componentes de la planta.** Chillers centrífugos, torres, bombas, almacenamiento térmico, control | PR | Sin sello DF (la sección no tiene cita en el Word) · IL (objetos) | — |
| M8 | Red de distribución | **3.2 Red de distribución.** Tuberías aisladas que llevan agua fría y retornan el agua caliente. Sin la lista de temperaturas | PR | DF | (IDEA, 2023) |
| M8 | Sistema de control | **3.3 SCADA.** Regular caudales, monitorear temperaturas, detectar fugas, optimizar el consumo | PR | DF | (TRABEED, 2024) |
| M8 | Casos de estudio · Dubái | **3.4 Dubái.** Uno de los mayores sistemas del mundo; refrigeración a miles de edificios. Sin el nombre comercial en el texto y sin cifras | PR | DF | (EMPOWER, 2024) |
| M8 | Potencial de implementación en Panamá | **3.5 Panamá.** Condiciones favorables y cuatro zonas con su razón (sin «24 horas»: «refrigeración continua») | PR | Propuesta | Sin cita |

\* La cita del Word está al final de la sección, no en el mismo párrafo de la frase: ver `docs/VERIFICACION_FUENTES_M8_M11.md`, sección 4.

**Fuera, por falta de cita en el Word o porque son cifras:** la tabla comparativa con HVAC convencional; «reducir el consumo entre un 20 % y un 50 %»; «Ventajas energéticas y ambientales» (COP, emisiones, refrigerantes, espacio); Singapur y Estocolmo; las cinco etapas con temperaturas; la imagen del Word.

## Parada 4 · M11 — Métodos Innovadores de Mantenimiento de Sistemas de A/A y Refrigeración (tecla 4)

Autor: **Manuel Jiménez**. Fuente única: Word del M11 (`M11_Metodos_Innovadores_Mantenimiento.docx`). En pantalla, «industry, M. E. (2024)» se cita como **(Prayogo et al., 2024)** y «YAO, 2015» / «review, 2015» como **(Yao, 2016)**: son las obras reales detrás de esas entradas. (ASHRAE, 2021) y (DIRECT, 2023) van como en el Word. **La única cifra en pantalla** es el reparto del lubricante. Fuera: 0.8 mm, 10–12 %, 20–40 kHz, 92–98 %, 5–8 %, 10–18 %, 10–20 %, el clima, el ROI y «tres años».

> **Ruta principal:** escenas E1–E4. La numeración 4.0–4.5 corresponde a la profundización.

| Informe | Sección | Elemento del 3D | Nivel | Sello | Cita |
|---|---|---|---|---|---|
| M11 | Cavitación ultrasónica | **E1 · El sarro aísla.** Corte ampliado de un tubo del condensador: la capa de sarro, óxido y biofilm crece una vez y se queda (↺ Repetir). Indicador de consumo del compresor sin escala ni valores. Chip 4.0 | RP | DF (rótulo) · IL (corte e indicador) | (ASHRAE, 2021; DIRECT, 2023) |
| M11 | Cavitación ultrasónica | **E2 · Cavitación ultrasónica.** Transductores, ondas y microburbujas que implosionan junto a la pared; los depósitos se desprenden y siguen con el agua; al final el tubo queda limpio (↺ Repetir). Sin frecuencias. Chip 4.1 | RP | DF (rótulo) · IL (animación) | (Yao, 2016)* |
| M11 | Aditivos nanotecnológicos | **E3 · Dónde está el aceite.** Compresor, condensador, filtro secador, válvula de expansión y evaporador; el aceite en ámbar con su porcentaje; nanopartículas en el lubricante; una fracción del aceite circula con el refrigerante. Cifra: «50 % compresor · 20 % evaporador · 10 % secador, mangueras y condensador». Chips 4.2, 4.3 | RP | DF | (Prayogo et al., 2024, p. 401)* |
| M11 | Comparación · Conclusiones | **E4 · Dos métodos, dos lados.** Vista dividida: lado del agua (transductores en la tubería de condensación) y lado del refrigerante (nanolubricante). Chips 4.4, 4.5 | RP | «Síntesis del informe» | Sin cita |
| M11 | Cavitación ultrasónica | **4.0 El problema del fouling.** Aislante térmico; sube la temperatura y la presión de condensación; el compresor consume más | PR | DF | (ASHRAE, 2021; DIRECT, 2023) |
| M11 | Cavitación ultrasónica | **4.1 Cavitación acústica y microcorrientes.** Microchorros, ondas de choque, mezcla local, menor resistencia de la capa límite; película de lubricante y depósitos | PR | DF | (Yao, 2016)* |
| M11 | Aditivos nanotecnológicos | **4.2 Nanolubricantes.** Conductividad térmica, fricción y desgaste, potencia del compresor, COP (sin valores); TiO₂, SiO₂ y Al₂O₃; reparto del lubricante | PR | DF | (Prayogo et al., 2024, p. 401)* |
| M11 | Desafíos en el uso de nanolubricantes | **4.3 Desafíos.** Estabilidad de la dispersión, aglomeración y sedimentación, compatibilidad, uso prolongado, costo, falta de estándares | PR | DF | (Prayogo et al., 2024, pp. 390–406)* |
| M11 | Comparación de rendimiento | **4.4 Comparación.** Punto de aplicación, mecanismo e impacto en el mantenimiento (sin ahorro ni frecuencia) | PR | Síntesis del informe | Sin cita |
| M11 | Aplicación práctica al caso panameño | **4.5 Panamá.** Incrustaciones por la calidad del agua de las torres; operación continua de Split, VRF y Rooftop (sin clima ni ROI) | PR | Propuesta | Sin cita |

\* Pendiente de verificación o con la cita fuera del párrafo: ver `docs/VERIFICACION_FUENTES_M8_M11.md`.

## Lo que propongo dejar fuera y por qué

1. **El término "DALT"** del plan. El Word dice "prueba de fugas de los ductos" y no usa la sigla. Uso el texto del Word.
2. **Datos de la ficha que no están en el Word.** Del M14: D3060 y D8010 (BIMForum), "≈ doble de refrigerante", ASHRAE 15 y "evaluación basada en literatura" (Thornton y Wagner, 2012). Del M6, nada relevante. Si una ficha y su Word no coinciden, manda el Word.
3. **Barras por rejilla del caso Bogotá.** El informe solo trae los agregados; los 33 valores están en la tesis. Muestro la Figura 9 como imagen.
4. **El equipo de proceso de REFRESH** (torre, tanques, envasado) y sus datos (THD, capacidades, kVA). El M14 no los usa. Las naves quedan como volúmenes.
5. **La Figura 3 del M14 como imagen.** La escena 2.5 la reproduce en 3D; repetirla en imagen ocupa espacio sin aportar.
6. **Toda capacidad o lectura del VRF.** El inspector muestra qué entrega cada punto, nunca un valor.
7. **Imágenes del M6 en PNG original.** Suman unos 4 MB, y la Figura 6 sola pesa 2.1 MB. Propongo pasarlas a JPEG a unos 1,200 px de ancho, sin recortarlas, para que el HTML quede cerca de 3 MB. Esa compresión no modifica el contenido de la figura. Las Figuras 1 y 2 del M14 conviene dejarlas en PNG: la licencia CC BY-NC-ND pide no modificarlas.

## Dudas y choques entre el plan, las fichas y los Word

### Resueltas por Cristian (24/10/2026)
- **C1 · Balanceo.** Se animan los dos métodos con su contador de pasos. Qué método lleva 14 y cuál 10, y la meta de ±5 %, salen tal cual del Word, con sus citas (Pedranzini et al., 2013, p. 328; Yale Facilities, 2025). Se corrigió la frase del plan.
- **C2 · Control de velocidad.** Barras sin cifras y un solo rótulo, con la redacción exacta del Word (DOE y AMCA, 2003, p. 18).
- **C3 · Términos prohibidos.** Se prohíbe "Henríquez Espinosa" (sin mayúsculas ni tildes) en lugar de "Henríquez". El crédito de F. Henríquez en la Figura 11 del M6 se queda.
- **C4 · Salas de D y E.** El orden es DF (Batista et al., 2026, p. 21) y los tamaños son IL. Las unidades interiores van solo donde las pone la Figura 3 del M14; baños y taller, sin equipos.
- **C5 · Ubicación.** Se usa el plano del PDF (p. 21), no `data.js`.
- **C6 · Alturas.** Los 22 m corresponden solo a la zona de la torre de la Nave A (PDF p. 22); el resto de la Nave A y los demás edificios tienen altura IL.
- **D1 · Páginas de los informes.** No se citan en el 3D ni en esta matriz; la referencia va por sección, figura o tabla. Las páginas quedan solo para las fuentes originales.

- **C7 · Diferencias entre ficha y Word.** Manda el Word. Tabla 2: USD 9,093 millones (la ficha dice 9,093.3). USD 10,648 millones se cita con la p. ES-7 (tabla); "dos tercios" está en el texto de la p. ES-6. El Word agrega USD 96.9 millones (edificio médico) y "≈ USD 500,000 de un contrato de ≈ USD 9.4 millones". M6: el archivo final es `M06_Mantenimiento_Ventiladores_Distribucion.docx` (la ficha tiene el nombre anterior).
- **C8 · LOD (aprobado).** El plan anima solo la unidad exterior, pero la Tabla 1 usa la tubería y los soportes en los LOD 350 y 400, y la Figura 1 va solo del 200 al 400. Propongo animar la unidad y un tramo de tubería. El LOD 500 se representa con un sello "verificado en campo", porque el informe dice que no es un nivel superior al 400.
- **C9 · Escena 2.1 (aprobado).** Si la hago sobre REFRESH, parecería que REFRESH tuvo interferencias, lo que nadie afirma. Propongo un tramo de cielo raso genérico, sellado IL, fuera de la planta.
- **D2 · Mantenimiento del VRF (aprobado).** El plan lo cita a Thornton y Wagner; en el Word está en la sección "Propuesta de aplicación". Lo enlazo a esa sección.

### Revisión 3 (24/10/2026)
- Citas en pantalla con la forma exacta de cada Word: "Daikin Comfort Technologies North America, 2019" completo; en el M6, la sigla se define una vez en la tarjeta de apertura ("U.S. Department of Energy [DOE] y Air Movement and Control Association International [AMCA], 2003") y después se usa "DOE y AMCA, 2003".
- Vista "Referencias" en cada parada, copiada del Word; créditos de figuras con el texto exacto del Word.
- Rótulos visibles: "medidor propuesto" (escena 2.5) y "Marco general (Hu et al., 2026); en REFRESH es una propuesta" (escena 2.4).

---

## Geometría de REFRESH: qué se adapta y cómo

Origen: `origin/claude/spanish-greeting-CWfoM:asignacion-6-distribucion-planta/plano3d.js` y `data.js`. Los leí con `git show`; esa rama no se trae a la nuestra.

| Elemento | Del simulador | Cómo se adapta |
|---|---|---|
| Terreno, vial perimetral e interior | `BoxGeometry` 100 × 100 y franja de vial | Se reescribe como módulo ES con `vendor/three.module.js` (r184). Terreno de 100 × 100 m y vial de 7.00 m (PDF p. 22) |
| Edificios | `cajaMalla()` (caja + `EdgesGeometry`) | Misma técnica. **Dimensiones de la tabla del PDF (p. 22) y ubicación del plano (p. 21)**, no de `data.js` (ver C5). Alturas: 22 m solo en la zona de la torre de la Nave A (dato, p. 22), como volumen propio dentro de la nave; el resto de la Nave A y los demás edificios, IL |
| Pasarela A–B | Caja de 3 × 4 × 8 | Se conserva el ancho de 3.00 m (PDF p. 23); la longitud sale del plano |
| Patio de silos | 4 cilindros con cono | Se conservan Ø 2.50 m (PDF p. 22); la altura es IL. `InstancedMesh` |
| Zona de descarga y estacionamiento | Losas planas | Losas de 15 × 6 m y 30 puestos (PDF p. 22), sin autos |
| Equipos de proceso, partículas de flujo, P&ID, unifilar | Varios | **No se adaptan** (fuera del M14) |
| Salas de D y E | No existen en el simulador | Particiones bajas con el orden del plano (p. 21): en D, de norte a sur, laboratorio QC, comedor, baños/lockers de hombres, baños/lockers de mujeres y taller; en E, de oeste a este, recepción, oficinas y sala de juntas. Orden DF; tamaños IL |
| Equipos del VRF y puntos M/C | No existen | Geometría propia y baja; ubicación IL |

No se copia `lib/three.min.js` (r128) ni ningún código que dependa de él. Las coordenadas se convierten del plano (x, y) a three.js (x − 50, altura, y − 50), como en el original.


---

## Ronda 3 (24/10/2026)

- **Inicio:** dos miniaturas hechas con la geometría real de cada parada. La del M6 tiene la correa corregida y el aire animado; la del M14 es la planta completa, con D y E resaltados. Sello «Ilustrativo · miniatura de la parada», tres hitos sin cifras y sin fecha. Con un clic o con las teclas 1 y 2, la cámara entra en la miniatura y pasa a la parada.
- **M6 · correa (1.2, P3 y toda escena con el motor):** las dos poleas en el mismo plano, con ejes paralelos, y una correa plana con tramos tangentes y arcos.
- **M14 · 2.0b Zona de estudio (nuevo paso de ruta principal):** fachadas de D y E opacas en la planta, con el sello «Ilustrativo · REFRESH no define fachadas»; en la zona de estudio se desvanecen (rayos X) para mostrar las salas, las unidades y la tubería. Paneles PD-D y PD-E: «Dato de fuente (Batista et al., 2026, p. 25)», sin amperajes. El recorrido del cable es ilustrativo. No se modelan en 3D el P&ID ni el cableado de la planta.
- **M14 · 2.2 LOD:** vista cercana y fija, en diagonal; la unidad mide alrededor de 130 px a 1366. Un recuadro con la planta de D, C y E (p. 21) marca la unidad y la dirección de la vista. D y E están a unos 40 m entre sí, así que a 1366 no pueden verse completos en la misma vista cuando la unidad mide 120–150 px. El LOD 400 se distingue del 350 por la derivación (Tabla 1: «Derivaciones y soportes definidos para el montaje»).
- **M14 · 2.5:** el flujo M3 y el paro C3 llevan «Propuesta · M14 · Figura 3». Cada nodo lleva su nivel en el nombre para que quepan los cuatro niveles. La tarjeta del medidor marca la propuesta.
- **M14 · 2.6:** el modelo coordinado se muestra solo sobre D y E, con el sello de propuesta.
- **Sin cambios:** 2.1 (cielo raso genérico, caso Khanzode) y 2.4 (marco general con el rótulo de propuesta) siguen sin presentarse como REFRESH.


---

## Ronda 4 (25/10/2026) · Ruta principal de 4 escenas por parada

La ruta principal muestra el mecanismo con rótulos breves, y el texto completo queda en la profundización. No se borró ningún contenido: todos los pasos anteriores conservan su numeración en la pestaña «Profundización».

| Parada | Escena | Rótulo (resumen) | Sello | Referencia al informe | Chips «Detalle» |
|---|---|---|---|---|---|
| M6 | E1 · La red y su criterio | ±5 % del caudal de diseño | Dato de fuente | El TAB y su marco normativo | 1.0, 1.1, 1.2, P1, P2, P3, P4 |
| M6 | E2 · Cerrar una compuerta mueve a todas (interactiva) | cada ajuste cambia a los demás; 14 contra 10 pasos | Dato de fuente + «Simulación ilustrativa · ΔP = R·Q² · sin valores» | Métodos de balanceo · Tabla 1 | 1.3, 1.4, P5 |
| M6 | E3 · Abrir compuertas y bajar el ventilador | último ajuste en el ventilador; −20 % = −50 % | Dato de fuente | Del balanceo al consumo de energía · Figura 7 | 1.5, 1.6, P6 |
| M6 | E4 · Panamá | 72.90 %; −14.10 % en la simulación | Dato de fuente | Aplicación al contexto panameño · Figura 11 | 1.7, 1.8, P7, P8, P9 |
| M14 | E1 · De la planta a la zona de estudio | USD 15,824 millones; zona de estudio D y E | Dato de fuente | Introducción · Sistema MEP integrado | 2.0, 2.0b |
| M14 | E2 · Cuánto confiar en el modelo: LOD | LOD 500 = lo verificado | Dato de fuente | Niveles de desarrollo (LOD) · Tabla 1 | 2.2 |
| M14 | E3 · Una falla de punta a punta (ficha de activo) | de calendario a condición | Propuesta · M14 · Figura 3 | Sistema MEP integrado · Figura 3 | 2.4, 2.5, P1, P2, P3, P4 |
| M14 | E4 · Hoy frente a la propuesta | planos independientes → modelo coordinado + COBie; 2 de 233 RFI | Propuesta + Dato de fuente | Propuesta de aplicación · Tabla 2 | 2.1, 2.3, 2.6, 2.7, P5, P6, P7 |

**Simulación E2 (M6, ilustrativa).** La red es serie-paralelo:
- Tiene resistencias en los tramos del ducto principal, en los ramales, en los terminales y en las compuertas (abierta, media, cerrada), con ΔP = R·Q² en cada uno.
- La curva del ventilador es P = P0·(1 − (Q/Qmax)²) y el punto de operación se resuelve por iteración.
- ~~El caudal de «diseño» es el de todas las compuertas abiertas.~~ **Superado en la ronda 5:** el caudal de diseño es igual en los 8 terminales (el de una combinación balanceada de referencia, ilustrativo) y con todo abierto la red no lo entrega.
- No muestra valores.

**Otros cambios de la ronda 4:**
- La unidad exterior pasó al sur del Edificio E, del lado contrario a C (ATEX).
- Los niveles de la Figura 3 se rotulan uno por franja (4 → 3 → 2).
- En P1, el rótulo «Orden de las salas» se quitó; ese dato está en 2.0b.
- En el inicio, las miniaturas llevan los títulos de las escenas y D y E van en cian.


---

## Ronda 5 (25/10/2026)

- **Rótulos fieles al Word:**
  - M6 E2: «…de los demás terminales…».
  - M14 E2: «…verificado en campo».
  - M14 E3: «…puede pasar…».
- **M6 E2, simulación:**
  - Caudal de diseño igual en los 8 terminales. Es ilustrativo: el de una combinación balanceada de referencia.
  - Con todo abierto la red no entrega el diseño (M6 · Introducción; Pedranzini et al., 2013): los terminales cercanos quedan sobre la franja (152 %) y los lejanos debajo (78 %).
  - Cada compuerta tiene 6 posiciones (abierta → cerrada) y hay un botón «Reiniciar».
  - La búsqueda exhaustiva sobre las 6⁸ = 1,679,616 combinaciones encuentra 7 con los 8 terminales dentro de ±5 %.
  - El sello dice «Simulación ilustrativa · sin valores»; «ΔP = R·Q² (Pedranzini et al., 2013, p. 323)» va en texto normal.
- **Escenas narrativas** (M6 E1, M6 E4, M14 E1, M14 E4 y el paso 2.6): se reproducen una vez, quedan en su estado final y tienen el botón «↺ Repetir». Solo el aire y el giro del ventilador siguen en bucle.
- **M14 E4 / 2.6:**
  - La fase «Hoy» lleva «Dato de fuente» (Batista et al., 2026), sin VRF («Hoy: sin climatización de los espacios ocupados»).
  - Las fases «Modelo coordinado de D y E» y «Modelo as-built + COBie» llevan el sello de propuesta.
- **Unidad de aire exterior:** junto a la unidad exterior, al sur del Edificio E, lejos de C (ATEX). Aparece en el recuadro de planta (■).
- **P1:** se quitaron dos etiquetas repetidas: «M3 · aviso de filtro» (M3 ya está en «M1 M2 M3 C1 C2 · en cada unidad interior») y la segunda copia de esa etiqueta en el Edificio E. El inspector conserva los 10 puntos.

---

## Versión 2 (28/10/2026) · Paradas 3 y 4

- Rama `labs-3d-v2`, creada desde la etiqueta `labs-3d-v1.0`. `content-m6.js`, `scene-m6.js`, `content-m14.js` y `scene-m14.js` no cambian.
- **Encabezado e inicio:** «Laboratorios del Grupo A · Modelo 3D». El encabezado muestra el autor de la parada (1–2: Cristian Batista; 3–4: Manuel Jiménez). El inicio tiene 4 miniaturas reales en el orden 1 M6, 2 M14, 3 M8, 4 M11, con sus 4 títulos de escena, el autor y sin cifras. Teclas 0–4; las flechas pasan de la Parada 2 a la 3 y de la 3 a la 4.
- **Paradas 1 y 2 idénticas a la v1.0:** la prueba de humo compara una huella tomada del HTML v1.0 aprobado (`tests/fixtures/v1_paradas_1_2.json`). La huella incluye etiquetas visibles con su texto y posición, columna de tarjetas (rótulo, chips, sellos), panel derecho, nota, barra ← →, recuadro y tamaño del visor, en los 42 pasos de las dos paradas (escenas y profundización), en 25 estados interactivos y en las 2 vistas de referencias (69 por resolución), a 1366 y 1920, con el reloj de la página detenido. Resultado de la versión candidata: 0 diferencias.
- El suelo y las sombras del escenario se calculan con el inicio, el M6 y el M14, como en la v1.0. Las paradas 3 y 4 se agregan después para no cambiar ese ajuste.
- **Sello nuevo:** «Síntesis del informe» (M11 E4 y 4.4).
- **Conteo de palabras de los rótulos:** los signos sueltos (%, ·, =) ya no cuentan como palabra. Los límites (25 y 12) siguen iguales.
