// Texto de la Parada 2 · M14. Única fuente: Word final del M14 (y su ficha para las páginas de las obras);
// datos de la planta: PDF del Proyecto Final Integrador de REFRESH S.A. (Batista et al., 2026).
export const FIG14 = {
  1: { src: 'assets/img/m14_fig01_bimforum.png', title: 'Figura 1. Progresión del LOD 200 al LOD 400 de un equipo de refrigeración central (elemento D3030.10)', credit: '<i>Nota.</i> Tomado de <i>Especificación del nivel de desarrollo (LOD), parte I</i> (p. 128), por BIMForum, 2024 (https://bimforum.org/lod). Licencia CC BY-NC-ND 4.0; reproducido sin modificaciones.', link: true },
  2: { src: 'assets/img/m14_fig02_hu.png', title: 'Figura 2. Marco del gemelo digital para el mantenimiento 4.0 en edificios', credit: '<i>Nota.</i> Tomado de "Integrating digital twin technologies for maintenance 4.0 in the building industry: A review and conceptual framework" (Fig. 8), por W. Hu et al., 2026, <i>Building and Environment, 288</i>, Artículo 113997 (https://doi.org/10.1016/j.buildenv.2025.113997). Licencia CC BY 4.0.', link: true },
};
const DAIKIN = 'Daikin Comfort Technologies North America, 2019';

// Tabla 1 del M14 (texto del Word)
export const LOD = [
  { n: '100', c: 'Símbolo o volumen de reserva; datos aproximados', e: 'Espacio reservado para la unidad exterior junto a los Edificios D y E', u: 'Reservar desde el inicio el espacio de acceso al equipo' },
  { n: '200', c: 'Marcador genérico reconocible, con tamaño y ubicación aproximados', e: 'Unidad exterior y unidades interiores genéricas', u: 'Prever rutas de tubería y accesos al cielo raso' },
  { n: '300', c: 'Equipo especificado y medible; requisitos de acceso modelados', e: 'Unidades con dimensiones del fabricante y espacios libres de servicio', u: 'Comprobar que filtros y tableros queden accesibles' },
  { n: '350', c: 'Conexiones, soportes y penetraciones reales', e: 'Tubería de refrigerante y soportes coordinados con ductos, bandejas y estructura', u: 'Evitar interferencias que dificulten el servicio' },
  { n: '400', c: 'Componentes para fabricación e instalación', e: 'Derivaciones y soportes definidos para el montaje', u: 'Registro de lo que se instaló' },
  { n: '500', c: 'Condición as-built verificada en campo, con precisión indicada', e: 'Modelo verificado al entregar la planta', u: 'Base del modelo de operación, junto con los datos COBie' },
];

// Puntos de la Figura 3 (leyenda del Word) y lo que dice el informe de cada uno
export const PTS = {
  M1: { t: 'Temperatura de sala', eq: 'Cada unidad interior (D y E)', d: 'Punto que la unidad interior entrega al BMS.', cite: `${DAIKIN}, pp. 25–26` },
  M2: { t: 'Alarma con código de error', eq: 'Cada unidad interior y la unidad exterior', d: 'Alarma con su código de error, entregada al BMS.', cite: `${DAIKIN}, pp. 25–26` },
  M3: { t: 'Aviso de filtro', eq: 'Cada unidad interior (D y E)', d: 'Con el aviso de filtro conectado al SCADA, el cambio de filtros puede pasar de un calendario fijo a la condición del equipo.', cite: `${DAIKIN}, pp. 25–26; Hu et al., 2026` },
  M4: { t: 'Presiones y velocidad del compresor', eq: 'Unidad exterior VRF', d: 'Presiones de condensación y evaporación y velocidad del compresor. La unidad exterior también entrega una potencia eléctrica <b>calculada</b>, no medida.', cite: `${DAIKIN}, pp. 30–31` },
  M5: { t: 'Energía medida en el tablero', eq: 'Tableros de D y E · medidor propuesto', d: 'La potencia que reporta el VRF es calculada y no reemplaza a un medidor de energía en el tablero; por eso el esquema propone un medidor en los tableros de D y E.', cite: `${DAIKIN}, pp. 30–31` },
  M6: { t: 'Temperatura de la sala eléctrica', eq: 'Edificio C · sala eléctrica / UPS', d: 'La sala eléctrica se incluye solo como punto de monitoreo de temperatura.', cite: 'Batista et al., 2026' },
  C1: { t: 'Consigna y horario por zona', eq: 'Cada unidad interior (D y E)', d: 'Punto de control desde el BMS.', cite: DAIKIN },
  C2: { t: 'Encendido y apagado remoto', eq: 'Cada unidad interior (D y E)', d: 'Punto de control desde el BMS.', cite: DAIKIN },
  C3: { t: 'Paro forzado por señal de emergencia', eq: 'Ordenado por el SCADA a través de la pasarela', d: 'Apaga todas las unidades interiores cuando el BMS recibe una señal de emergencia; útil en una planta con zonas clasificadas por polvo combustible.', cite: `${DAIKIN}, p. 24; Batista et al., 2026` },
  C4: { t: 'Marcha y paro de la unidad de aire exterior', eq: 'Unidad de aire exterior (ventilación de D y E)', d: 'Punto de control de la unidad separada de aire exterior.', cite: 'Thornton y Wagner, 2012, p. 4' },
};
export const PT_NOTE = `Solo se generan los puntos que existen en el modelo de equipo y que se habilitan durante la puesta en marcha (${DAIKIN}, pp. 25, 33).`;

const T2 = [
  ['RFI por conflictos en campo', '2 de 233, ambas de sistemas no modelados', 'Khanzode et al. (2008, p. 336)'],
  ['Órdenes de cambio por conflictos en campo', '0', 'Khanzode et al. (2008, p. 336)'],
  ['Retrabajo del contratista mecánico', '40 de 25,000&nbsp;h de campo (menos de 0.2&nbsp;%)', 'Khanzode et al. (2008, p. 339)'],
  ['Mano de obra devuelta por el contratista mecánico', '≈ USD&nbsp;500,000 de un contrato de ≈ USD&nbsp;9.4 millones', 'Khanzode et al. (2008, p. 338)'],
  ['Ahorro frente a diseño-licitación-construcción', '≈ USD&nbsp;9 millones y 6 meses (BIM más entrega colaborativa)', 'Khanzode et al. (2008, p. 337)'],
  ['Costo anual de la falta de interoperabilidad (EE. UU., 2002)', 'USD&nbsp;15,824 millones', 'Gallaher et al. (2004, p. ES-6)'],
  ['Parte pagada por propietarios y operadores', 'USD&nbsp;10,648 millones (≈ dos tercios)', 'Gallaher et al. (2004, p. ES-7)'],
  ['Costo en la fase de operación y mantenimiento', 'USD&nbsp;9,093 millones', 'Gallaher et al. (2004, p. ES-7)'],
];

export const M14 = {
  stop: { kicker: 'Parada 2 · M14', short: 'M14', title: 'Digitalización, BIM y Gestión Inteligente de Instalaciones (MEP)', lead: 'BIM, niveles de desarrollo, gemelo digital y un esquema MEP integrado para la planta REFRESH S.A.' },
  note: 'Modelo conceptual, no a escala, salvo las dimensiones en planta de REFRESH (Batista et al., 2026).',
  steps: [
    { id: 'planta', n: '2.0', level: 'RP', title: 'La planta REFRESH S.A.', ref: 'M14 · Introducción · Sistema MEP integrado', cards: [
      { ref: 'M14 · Introducción', stamp: 'df', cite: 'Gallaher et al., 2004, p. ES-6; Hu et al., 2026', title: 'La información que no llega a operación',
        body: '<p>La falta de interoperabilidad costó <b class="n">15,824 millones de dólares</b> en 2002 a la industria de instalaciones de Estados Unidos; cerca de dos terceras partes recayeron en propietarios y operadores. BIM es el repositorio central, y el gemelo digital lo conecta con datos de operación para mantener por condición y de forma predictiva.</p>' },
      { ref: 'M14 · Sistema MEP integrado para la planta REFRESH S.A.', stamp: 'df', cite: 'Batista et al., 2026', title: 'REFRESH S.A., proyecto académico de la carrera',
        body: '<p>Planta de detergente en polvo diseñada en Selección de Equipos y Trazado de Planta: cinco edificios en un terreno de 10,000&nbsp;m². Los Edificios D (laboratorio de control de calidad, comedor, baños y taller) y E (recepción, oficinas y sala de juntas) concentran los espacios ocupados que requieren climatización. Un SCADA central integra los PLC de los equipos de proceso.</p>' },
      { stamp: 'df', cite: 'Batista et al., 2026, pp. 21–22', title: 'Planta y dimensiones',
        body: '<p>Dimensiones de cada edificio en sus etiquetas; ubicación aproximada al plano general. La única altura de fuente es la de la zona de la torre de la Nave A (22&nbsp;m). <span class="st il">Ilustrativo</span> las demás alturas y el tamaño de las salas.</p>' },
    ] },
    { id: 'coord', n: '2.1', level: 'RP', title: 'Metodología BIM: coordinación', ref: 'M14 · La metodología BIM aplicada a sistemas HVAC-R', cards: [
      { ref: 'M14 · La metodología BIM aplicada a sistemas HVAC-R', stamp: 'df', cite: 'BIMForum, 2024', title: 'Elementos con información',
        body: '<p>Cada elemento (una puerta, una viga, una bomba) se representa en 3D y puede asociarse con información; como el gráfico puede aparentar más precisión de la que tiene, el LOD comunica cuánto confiar en cada uno.</p>' },
      { ref: 'M14 · La metodología BIM aplicada a sistemas HVAC-R', stamp: 'df', cite: 'Khanzode et al., 2008, pp. 328–329', title: 'Edificio médico de USD&nbsp;96.9 millones, California',
        body: '<p>Cada subcontratista modeló su sistema en 3D y el contratista de HVAC lideró la coordinación sobre el cielo raso, porque sus ductos ocupan la mayor parte de ese espacio. Los modelos se integraron y las interferencias se detectaron de forma automática, en un proceso que se repitió hasta resolverlas antes de construir.</p>' },
      { ref: 'M14 · La metodología BIM aplicada a sistemas HVAC-R', stamp: 'df', cite: 'Khanzode et al., 2008, pp. 339–340', title: 'Lo que no se modela, choca',
        body: '<p>Acabados, mobiliario y soportes misceláneos de acero sin modelar provocaron reubicaciones de tomacorrientes y conflictos en obra: el nivel de detalle se decide entre todos, según su uso. <span class="st il">Ilustrativo</span> cielo raso genérico, no es REFRESH ni el edificio médico.</p>' },
    ] },
    { id: 'lod', n: '2.2', level: 'RP', title: 'Niveles de desarrollo (LOD)', ref: 'M14 · Niveles de desarrollo (LOD) · Figura 1 · Tabla 1', cards: [
      { ref: 'M14 · Tabla 1', stamp: 'df', cite: 'BIMForum, 2024, pp. 12–13', title: 'LOD <span data-lodn>100</span> · unidad exterior y tubería del VRF',
        body: `<div class="lodbtns">${LOD.map(l => `<button class="btn" data-lod="${l.n}">${l.n}</button>`).join('')}</div>
<table class="lodt"><tr><th>Contenido del elemento</th><td data-lodf="c"></td></tr><tr><th>Ejemplo en el VRF de REFRESH</th><td data-lodf="e"></td></tr><tr><th>Utilidad para mantenimiento</th><td data-lodf="u"></td></tr></table>
<p class="small"><i>Nota.</i> Elaboración propia con base en BIMForum (2024). La especificación no tiene una ficha propia para VRF; la asignación de la unidad exterior al elemento D3030.10 y de las unidades interiores y ductos al elemento D3050.50 es una interpretación del grupo.</p>
<p><span class="st il">Ilustrativo</span> geometría de cada nivel; la ubicación de la unidad exterior es ilustrativa.</p>` },
      { ref: 'M14 · Niveles de desarrollo (LOD)', stamp: 'df', cite: 'BIMForum, 2024, pp. 11–13, 195', title: 'Dos aclaraciones para mantenimiento',
        body: '<p>El LOD indica cuánto se ha estudiado la geometría, no la cantidad de detalle; los requisitos son acumulativos, salvo el LOD 500, que no es superior al 400 sino la condición as-built verificada en campo. No existe un «modelo LOD 300»: cada entrega tiene elementos en distintos niveles. El LOD describe solo la geometría; fabricante, modelo o garantía van por protocolos como COBie.</p>', fig: FIG14[1] },
    ] },
    { id: 'ventajas', n: '2.3', level: 'RP', title: 'Ventajas cuantificadas', ref: 'M14 · Ventajas cuantificadas · Tabla 2', cards: [
      { ref: 'M14 · Tabla 2', stamp: 'df', cite: 'Khanzode et al., 2008; Gallaher et al., 2004', title: 'Ventajas de BIM y costo de la falta de interoperabilidad', wide: true,
        body: `<table class="t2"><tr><th>Indicador</th><th>Resultado</th><th>Fuente</th></tr>${T2.map((r, i) => `<tr data-row="${i}"><td>${r[0]}</td><td><b>${r[1]}</b></td><td>${r[2]}</td></tr>`).join('')}</table>
<p class="small"><i>Nota.</i> Las cifras de Khanzode et al. (2008) corresponden a un solo proyecto; las de Gallaher et al. (2004) son estimaciones para la industria de Estados Unidos.</p>` },
      { ref: 'M14 · Ventajas cuantificadas', stamp: 'df', cite: 'Khanzode et al., 2008, p. 337', title: 'El modelo as-built llegó a la operación',
        body: '<p>El equipo de instalaciones gestiona el edificio con el modelo as-built, más fácil de consultar que los planos 2D; el ahorro se atribuye a BIM más una entrega colaborativa y acelerada, no únicamente a BIM.</p>' },
    ] },
    { id: 'gemelo', n: '2.4', level: 'RP', title: 'Del BIM al gemelo digital', ref: 'M14 · Del modelo BIM al gemelo digital · Figura 2', cards: [
      { ref: 'M14 · Del modelo BIM al gemelo digital', stamp: 'df', cite: 'Lu et al., 2020', title: 'Caso real: edificio del IfM, Universidad de Cambridge',
        body: '<p>Gemelo digital de las dos bombas centrífugas que retornan el agua helada de las manejadoras y los fan coils al chiller. Modelo en Revit, exportado a IFC4 y extendido con entidades de operación y mantenimiento; una tabla de correspondencia vincula cada objeto del modelo con su identificador en el BMS y en los sensores.</p><p>Con la vibración y la señal de servicio, el método bayesiano detectó la parada programada de una bomba sin las dos falsas alarmas del CUSUM; con datos de una bomba anómala, el CUSUM tardó casi una semana.</p><p><span class="st il">Ilustrativo</span> no se modela el edificio de Cambridge.</p>' },
      { ref: 'M14 · Figura 2', stamp: 'df', cite: 'Hu et al., 2026', title: 'Marco de cinco capas',
        body: '<p>Recolección de datos → procesamiento → modelos inteligentes → plataforma de visualización → soporte en la nube. El BIM as-built es el repositorio central; la integración usa formatos como IFC, COBie y JSON.</p><p class="rot hot">Marco general (Hu et al., 2026); en REFRESH es una propuesta.</p>', fig: FIG14[2] },
    ] },
    { id: 'mep', n: '2.5', level: 'RP', title: 'Sistema MEP integrado para REFRESH', ref: 'M14 · Sistema MEP integrado · Figura 3', cards: [
      { ref: 'M14 · Sistema MEP integrado para la planta REFRESH S.A.', stamp: 'df', cite: 'Thornton y Wagner, 2012, pp. 4–5, 19', title: 'VRF para los Edificios D y E',
        body: '<p>Unidad exterior con compresor de velocidad variable y tubería de refrigerante hacia unidades interiores tipo fan coil; el aire exterior llega por una unidad separada. Autodiagnóstico, puntos de monitoreo y protocolos abiertos como BACnet y LonWorks.</p>' },
      { ref: 'M14 · Figura 3', stamp: 'df', cite: `${DAIKIN}, pp. 8, 24`, title: 'Cuatro niveles y una alerta',
        body: '<p>Campo → automatización del VRF → supervisión (SCADA) → información (BIM as-built + COBie, CMMS y tablero). <b>Animación:</b> aviso de filtro (M3) → controlador → pasarela BACnet/IP → SCADA → tablero → orden de trabajo en el CMMS; luego, <b>paro forzado (C3)</b>: se apagan todas las unidades interiores.</p><p><span class="st il">Ilustrativo</span> ubicación de equipos y tamaño de salas; orden de las salas del plano general (Batista et al., 2026, p. 21).</p>' },
      { ref: 'M14 · Sistema MEP integrado', stamp: 'df', cite: `${DAIKIN}, pp. 30–31`, title: 'Medidor propuesto (M5)',
        body: '<p>La potencia que reporta el VRF es calculada y no reemplaza a un medidor de energía en el tablero: el esquema propone un medidor en los tableros de D y E.</p>' },
    ] },
    { id: 'propuesta', n: '2.6', level: 'RP', title: 'Propuesta para REFRESH', ref: 'M14 · Propuesta de aplicación al proyecto REFRESH S.A.', cards: [
      { ref: 'M14 · Propuesta de aplicación', stamp: 'df', cite: 'Batista et al., 2026', title: 'Hoy: planos independientes',
        body: '<p>REFRESH se documentó con una vista isométrica 3D, un diagrama de tuberías e instrumentación (P&amp;ID) y un diagrama unifilar eléctrico, presentados como planos independientes, sin la climatización de los espacios ocupados.</p>' },
      { ref: 'M14 · Propuesta de aplicación', stamp: 'df', cite: 'BIMForum, 2024', title: 'Con BIM: un modelo coordinado',
        body: '<p>Los elementos del VRF avanzarían desde símbolos o volúmenes de reserva en el anteproyecto hasta el LOD 350 en la coordinación con las tuberías de proceso, las bandejas eléctricas y la estructura, para terminar en un modelo as-built con sus datos COBie.</p><p>Con el aviso de filtro y las alarmas en el SCADA, el mantenimiento puede pasar de un calendario fijo a la condición del equipo (Daikin Comfort Technologies North America, 2019; Hu et al., 2026).</p><p><span class="st il">Ilustrativo</span> la animación junta los tres planos en el modelo.</p>' },
    ] },
    { id: 'cierre', n: '2.7', level: 'RP', title: 'Conclusiones', ref: 'M14 · Conclusiones', cards: [
      { ref: 'M14 · Conclusiones', stamp: 'df', title: 'Cuatro conclusiones', wide: true,
        body: '<ol><li>El LOD comunica cuánto se puede confiar en la geometría de cada elemento, pero no contiene los datos que necesita mantenimiento; BIM sirve en la operación si se combina con requisitos de información como COBie (BIMForum, 2024). → 2.2</li><li>Las ventajas mejor documentadas de BIM en MEP son menos conflictos, RFI y retrabajo en obra, y un modelo as-built útil para operar (Khanzode et al., 2008); el mayor costo de no compartir la información se paga en operación y mantenimiento (Gallaher et al., 2004). → 2.3</li><li>Los gemelos digitales permiten mantener los equipos de climatización con base en su condición, pero la evidencia proviene sobre todo de pilotos con pocos equipos (Hu et al., 2026; Lu et al., 2020). → 2.4</li><li>En Panamá, el diagnóstico regional de 2022 no identificó una iniciativa pública de impulso a BIM, sino una privada, el BIM Fórum Panamá (Soto y Manríquez, 2023); su adopción en proyectos industriales dependerá de que los propietarios exijan desde el diseño la información para el mantenimiento, como se propone para REFRESH S.A. (Batista et al., 2026). → P6</li></ol>' },
    ] },
    // ---------- Profundización ----------
    { id: 'inspector', n: 'P1', level: 'PR', title: 'Inspector de puntos M y C', ref: 'M14 · Sistema MEP integrado · Figura 3', cards: [
      { ref: 'M14 · Figura 3', stamp: 'df', title: 'Inspector de puntos',
        body: `<div class="ptbtns">${Object.keys(PTS).map(k => `<button class="btn" data-pt="${k}">${k}</button>`).join('')}</div><div id="ptinfo"></div><p class="small">${PT_NOTE}</p><p class="small">Un clic en una etiqueta M o C del modelo también abre su ficha. Sin valores numéricos: el informe no trae lecturas.</p>` },
    ] },
    { id: 'integracion', n: 'P2', level: 'PR', title: 'Condición de integración', ref: 'M14 · Sistema MEP integrado', cards: [
      { ref: 'M14 · Sistema MEP integrado', stamp: 'df', cite: 'Batista et al., 2026, p. 13', title: 'BACnet ↔ SCADA: por confirmar',
        body: '<p>Los equipos de REFRESH se especificaron con protocolos industriales como Profibus, Profinet y EtherNet/IP; la integración de la pasarela BACnet con el SCADA debe confirmarse al seleccionar los equipos.</p>' },
    ] },
    { id: 'limites', n: 'P3', level: 'PR', title: 'Límites de la evidencia', ref: 'M14 · Del modelo BIM al gemelo digital', cards: [
      { ref: 'M14 · Del modelo BIM al gemelo digital', stamp: 'df', cite: 'Hu et al., 2026; Lu et al., 2020', title: 'Todavía, sobre todo pilotos',
        body: '<p>La mayoría de las investigaciones no pasa de la etapa de prototipo o piloto y los datos siguen aislados por sistema. En el caso del IfM, la evaluación se limitó a dos conjuntos de datos de dos bombas.</p>' },
    ] },
    { id: 'mantto', n: 'P4', level: 'PR', title: 'Mantenimiento del VRF', ref: 'M14 · Propuesta de aplicación', cards: [
      { ref: 'M14 · Propuesta de aplicación', stamp: 'df', cite: 'Thornton y Wagner, 2012, pp. 7, 18, 24', title: 'Filtros, serpentines y condensado',
        body: '<p>El mantenimiento regular de un VRF consiste en cambiar filtros y limpiar los serpentines de las unidades interiores, junto con la limpieza del sistema de condensado; el de la unidad exterior es mínimo.</p>' },
    ] },
    { id: 'riesgos', n: 'P5', level: 'PR', title: 'Riesgos de la propuesta', ref: 'M14 · Propuesta de aplicación', cards: [
      { ref: 'M14 · Propuesta de aplicación', stamp: 'df', cite: 'Thornton y Wagner, 2012, pp. 12, 25', title: 'Fugas y repuestos',
        body: '<p>Las fugas de refrigerante son difíciles de localizar en una red de tubería que recorre el edificio, y los componentes de un fabricante no son intercambiables con los de otro ni cuentan con un mercado secundario: hay que definir desde el inicio los repuestos críticos y el soporte técnico disponible en el país.</p><p><span class="st il">Ilustrativo</span> la tubería de refrigerante parpadea en todo su recorrido.</p>' },
    ] },
    { id: 'panama', n: 'P6', level: 'PR', title: 'Panamá y BIM', ref: 'M14 · Conclusiones', cards: [
      { ref: 'M14 · Conclusiones', stamp: 'df', cite: 'Soto y Manríquez, 2023, pp. 17–18', title: 'Una iniciativa privada',
        body: '<p>El diagnóstico regional de 2022 no identificó en Panamá una iniciativa pública de impulso a BIM, sino una privada: el BIM Fórum Panamá, auspiciado por la cámara de la construcción. Su adopción en proyectos industriales dependerá de que los propietarios exijan desde el diseño la entrega de información para el mantenimiento, como se propone para REFRESH S.A. (Batista et al., 2026).</p>' },
    ] },
    { id: 'recom', n: 'P7', level: 'PR', title: 'Recomendaciones', ref: 'M14 · Recomendaciones', cards: [
      { ref: 'M14 · Recomendaciones', stamp: 'df', title: 'Dos recomendaciones',
        body: '<ol><li>En los proyectos de diseño de la carrera, incluir desde el anteproyecto una tabla con el LOD esperado de cada elemento y la lista de datos que necesitará mantenimiento, para entregar el modelo final a la operación (BIMForum, 2024).</li><li>Al seleccionar un sistema VRF, pedir al fabricante la lista de puntos BACnet del modelo exacto y verificar su compatibilidad con el SCADA o BMS existente antes de la compra (Daikin Comfort Technologies North America, 2019; Thornton y Wagner, 2012).</li></ol>' },
    ] },
  ],
  refs: [
    'Batista, C., Jiménez, M., Camarena, A., y Stephenson, R. (2026). <i>REFRESH S.A.: Diseño de una planta de detergente en polvo</i> [Proyecto final no publicado]. Universidad Tecnológica de Panamá.',
    'BIMForum. (2024). <i>Especificación del nivel de desarrollo (LOD), parte I</i> (C. Vera y H. Santacruz, Trads.). https://bimforum.org/lod',
    'Daikin Comfort Technologies North America. (2019). <i>Intelligent Touch Manager (iTM) BACnet server gateway: Design guide</i> (DCM014A51). https://daikincomfort.com/docs/default-source/itm-bacnet-server-gateway-option/eg-itm_bacnetgatewayguide_v2-0.pdf',
    'Gallaher, M. P., O\'Connor, A. C., Dettbarn, J. L., Jr., y Gilday, L. T. (2004). <i>Cost analysis of inadequate interoperability in the U.S. capital facilities industry</i> (NIST GCR 04-867). National Institute of Standards and Technology. https://doi.org/10.6028/NIST.GCR.04-867',
    'Hu, W., Ou, Y., Liu, H., Ni, P., y Chang, C. (2026). Integrating digital twin technologies for maintenance 4.0 in the building industry: A review and conceptual framework. <i>Building and Environment, 288</i>, Artículo 113997. https://doi.org/10.1016/j.buildenv.2025.113997',
    'Khanzode, A., Fischer, M., y Reed, D. (2008). Benefits and lessons learned of implementing building virtual design and construction (VDC) technologies for coordination of mechanical, electrical, and plumbing (MEP) systems on a large healthcare project. <i>Journal of Information Technology in Construction, 13</i>, 324–342. https://www.itcon.org/2008/22',
    'Lu, Q., Xie, X., Parlikad, A. K., y Schooling, J. M. (2020). Digital twin-enabled anomaly detection for built asset monitoring in operation and maintenance. <i>Automation in Construction, 118</i>, Artículo 103277. https://doi.org/10.1016/j.autcon.2020.103277',
    'Soto, C., y Manríquez, S. (2023). <i>Panorama general del avance de BIM en América Latina y el Caribe</i>. CAF.',
    'Thornton, B., y Wagner, A. (2012). <i>Variable refrigerant flow systems</i> (PNNL-21548). Pacific Northwest National Laboratory. https://www.pnnl.gov/main/publications/external/technical_reports/PNNL-21548.pdf',
  ],
};
