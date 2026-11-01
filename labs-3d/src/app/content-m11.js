// Texto de la Parada 4 · M11 (Métodos innovadores de mantenimiento). Autor: Manuel Jiménez. Única fuente: Word del M11.
// Decisión del 29/10: manda el compendio (Word del 28/10). Una cita solo cubre el párrafo que cierra; lo demás lleva
// sello «Síntesis del informe» o «Ilustrativo», o sale. Ninguna cifra. Citas y referencias tal como están en el compendio:
// (ASHRAE, 2021) (DIRECT, 2023), (YAO, 2015), (review, 2015), (industry, 2024). «IPCC, 2022» no aparece.
const SI = '<span class="st si">Síntesis del informe</span>', DF = '<span class="st df">Dato de fuente</span>';
export const M11 = {
  stop: { kicker: 'Parada 4 · M11', short: 'M11', author: 'Manuel Jiménez', title: 'Métodos Innovadores de Mantenimiento de Sistemas de Aire Acondicionado y Refrigeración', lead: 'Cavitación ultrasónica en intercambiadores y aditivos nanotecnológicos para el lubricante.' },
  note: 'Modelo conceptual, no a escala. Equipos genéricos e ilustrativos.',
  steps: [
    { id: 'fouling', n: '4.0', title: 'El problema del fouling', ref: 'M11 · Cavitación ultrasónica',
      cards: [{ ref: 'M11 · Cavitación ultrasónica', stamp: 'si', title: 'Una capa que aísla',
        body: '<p>La acumulación de sarro, óxidos y biofilm en las tuberías e intercambiadores de calor (condensadores de tubos y coraza o chillers enfriados por agua) actúa como un aislante térmico.</p><p>Por eso aumentan de forma sostenida la temperatura y la presión de condensación, y con ellas el consumo energético del compresor.</p>' }] },
    // Cada párrafo con su cita; los párrafos sin cita en el compendio llevan «Síntesis del informe»
    { id: 'cavitacion', n: '4.1', title: 'Cavitación acústica y microcorrientes', ref: 'M11 · Cavitación ultrasónica',
      cards: [{ ref: 'M11 · Cavitación ultrasónica', title: 'Lo que hace el ultrasonido junto a la pared',
        body: `<p>${SI} Las ondas ultrasónicas de baja frecuencia que se propagan en un líquido generan cavitación acústica y microcorrientes acústicas (<i>acoustic microstreaming</i>). La cavitación produce microchorros, ondas de choque y una intensa mezcla local del fluido; las microcorrientes mejoran la circulación cerca de las superficies sólidas.</p><p>${DF} La energía ultrasónica puede reducir la resistencia térmica de la capa límite: los intercambiadores alcanzan mayores coeficientes de transferencia de calor y se reducen los efectos de las incrustaciones y los depósitos <span class="cite">(YAO, 2015)</span>.</p><p>${DF} La cavitación y las microcorrientes acústicas contribuyen a desprender y eliminar la película de lubricante y los depósitos de las superficies internas de las tuberías <span class="cite">(review, 2015)</span>.</p>` }] },
    { id: 'nano', n: '4.2', title: 'Nanolubricantes', ref: 'M11 · Aditivos nanotecnológicos',
      cards: [{ ref: 'M11 · Aditivos nanotecnológicos al lubricante', stamp: 'df', cite: 'industry, 2024', title: 'Un lubricante que conduce mejor el calor',
        body: '<p>Gracias a su elevada conductividad térmica y a la mejora de la lubricación, los nanolubricantes reducen las pérdidas de energía por fricción, optimizan el intercambio térmico y disminuyen la potencia requerida por el compresor. Como resultado, aumenta el coeficiente de desempeño (COP).</p>' }] },
    { id: 'desafios', n: '4.3', title: 'Desafíos de los nanolubricantes', ref: 'M11 · Aditivos nanotecnológicos · Desafíos',
      cards: [{ ref: 'M11 · Desafíos en el uso de nanolubricantes', stamp: 'si', title: 'Lo que falta resolver',
        body: '<ul><li>Mantener la estabilidad de la dispersión de las nanopartículas durante la operación.</li><li>Evitar la aglomeración y la sedimentación, que pueden obstruir componentes.</li><li>Garantizar la compatibilidad química entre nanopartículas, lubricantes y refrigerantes.</li><li>Evaluar los efectos del uso prolongado sobre compresores, válvulas e intercambiadores.</li><li>Reducir el costo de producción y aplicación.</li><li>Establecer normativas y estándares técnicos para su uso industrial.</li></ul>' }] },
    { id: 'comparacion', n: '4.4', title: 'Comparación de los dos métodos', ref: 'M11 · Comparación de rendimiento',
      cards: [{ ref: 'M11 · Comparación de los dos métodos', stamp: 'si', title: 'Dos métodos, dos lados', wide: true,
        body: '<table><tr><th></th><th>Cavitación ultrasónica</th><th>Aditivos nanotecnológicos</th></tr><tr><th>Punto de aplicación</th><td>Lado del agua de los intercambiadores</td><td>Lado del refrigerante: circuito hermético interno</td></tr><tr><th>Mecanismo</th><td>Implosión de microburbujas por ondas ultrasónicas</td><td>Eliminación del <i>oil fouling</i> y menor fricción</td></tr><tr><th>Impacto en el mantenimiento</th><td>Evita químicos ácidos nocivos y paradas prolongadas</td><td>No requiere desarmar tuberías ni modificar el diseño mecánico</td></tr></table>' }] },
    { id: 'panama', n: '4.5', title: 'Aplicación en Panamá', ref: 'M11 · Aplicación práctica al caso panameño',
      cards: [{ ref: 'M11 · Aplicación práctica al caso panameño', stamp: 'pr', title: 'Propuesta del informe',
        body: '<p><b>Cavitación ultrasónica:</b> en edificios comerciales de la Ciudad de Panamá y de la Zona Libre de Colón, los chillers enfriados por agua sufren incrustaciones biológicas y salinas por la calidad del agua de las torres de enfriamiento. Incluirla en el mantenimiento preventivo evita desincrustantes químicos agresivos que aceleran la corrosión y extiende la vida útil de los tubos.</p><p><b>Aditivos nanotecnológicos:</b> por la operación continua de equipos Split, VRF y Rooftop, la degradación por <i>oil fouling</i> es acelerada. Son una solución de rápida implementación y bajo costo inicial, que permite recuperar la capacidad de enfriamiento sin reemplazar los equipos.</p>' }] },
  ],
  // Tal como están en el compendio (bibliografía del Word del M11), sin completarlas ni corregirlas
  refs: [
    'ASHRAE. (2021).',
    'DIRECT, S. (2023, OCTUBRE). Retrieved from https://www.sciencedirect.com/science/article/pii/S1359431123012401?ref=pdf_download&amp;fr=RR-2&amp;rr=a5071dc2189f7a26',
    'industry, M. E. (2024). Mechanical Engineering for society and industry. Retrieved from file:///C:/Users/Dell/Downloads/mujisetiyo,+4.+Galang+Sandy+P_12204.pdf',
    'review, S. R. (2015). Retrieved from https://es.scribd.com/document/651632991/Research-and-applications-of-ultrasound-in-HVAC-field',
    'YAO, Y. (2015, DICIEMBRE). SCIENCE DIRECT. Retrieved from https://es.scribd.com/document/651632991/Research-and-applications-of-ultrasound-in-HVAC-field',
  ],
};
// Ruta principal: 4 escenas con rótulo breve; los pasos 4.0–4.5 quedan en la profundización (chips «Detalle»)
export const SC11 = [
  { id: 'E1', n: 'E1', level: 'RP', title: 'El sarro aísla', chips: ['fouling'],
    rot: { replay: true, ref: 'M11 · Cavitación ultrasónica', stamp: 'df', f: 'El sarro y el biofilm en los tubos actúan como aislante: suben la temperatura y la presión de condensación, y el compresor consume más', fc: ['ASHRAE, 2021', 'DIRECT, 2023'],
      extra: '<span class="st il">Ilustrativo</span> Corte ampliado de un tubo del condensador. El indicador de consumo no tiene escala ni valores.' } },
  { id: 'E2', n: 'E2', level: 'RP', title: 'Cavitación ultrasónica', chips: ['cavitacion'],
    rot: { replay: true, ref: 'M11 · Cavitación ultrasónica', stamp: 'df', f: 'El ultrasonido genera cavitación y microcorrientes junto a la pared: mejora la transferencia de calor y reduce los depósitos', fc: ['YAO, 2015', 'review, 2015'],
      extra: '<span class="st il">Ilustrativo</span> Animación: transductores, ondas y microburbujas que implosionan junto a la pared; los depósitos se desprenden y siguen con el agua.' } },
  { id: 'E3', n: 'E3', level: 'RP', title: 'Dónde está el aceite', chips: ['nano', 'desafios'],
    rot: { ref: 'M11 · Aditivos nanotecnológicos', stamp: 'si', f: 'Cerca de la mitad del lubricante queda en el compresor y el resto circula con el refrigerante',
      extra: `${DF} Las nanopartículas mejoran la transferencia de calor <span class="cite">(industry, 2024)</span>.<br><span class="st il">Ilustrativo</span> Circuito genérico de compresión: el aceite se resalta en ámbar; las nanopartículas (TiO₂, SiO₂ y Al₂O₃) se dibujan sin escala.` } },
  { id: 'E4', n: 'E4', level: 'RP', title: 'Dos métodos, dos lados', chips: ['comparacion', 'panama'],
    rot: { ref: 'M11 · Comparación · Conclusiones', stamp: 'si', f: 'La cavitación actúa en el lado del agua de los intercambiadores; el nanolubricante, dentro del circuito del refrigerante',
      extra: '<span class="st il">Ilustrativo</span> Vista dividida: a la izquierda, el lado del agua; a la derecha, el lado del refrigerante.' } },
];
