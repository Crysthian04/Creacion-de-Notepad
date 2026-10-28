// Texto de la Parada 4 · M11 (Métodos innovadores de mantenimiento). Autor: Manuel Jiménez. Única fuente: Word del M11.
// Solo se usa texto con cita en el Word; la única cifra en pantalla es el reparto del lubricante (Prayogo et al., 2024, p. 401).
// «Prayogo et al., 2024» y «Yao, 2016» son las obras reales detrás de «industry, M. E. (2024)» y «YAO / review, S. R. (2015)» del Word.
const PRAYOGO = 'Prayogo et al., 2024';
const PCT = '50&nbsp;% compresor · 20&nbsp;% evaporador · 10&nbsp;% secador, mangueras y condensador';
export const M11 = {
  stop: { kicker: 'Parada 4 · M11', short: 'M11', author: 'Manuel Jiménez', title: 'Métodos Innovadores de Mantenimiento de Sistemas de Aire Acondicionado y Refrigeración', lead: 'Cavitación ultrasónica en intercambiadores y aditivos nanotecnológicos para el lubricante.' },
  note: 'Modelo conceptual, no a escala. Equipos genéricos e ilustrativos.',
  pct: PCT,
  steps: [
    { id: 'fouling', n: '4.0', title: 'El problema del fouling', ref: 'M11 · Cavitación ultrasónica',
      cards: [{ ref: 'M11 · Cavitación ultrasónica', stamp: 'df', cite: 'ASHRAE, 2021; DIRECT, 2023', title: 'Una capa que aísla',
        body: '<p>La acumulación de sarro, óxidos y biofilm en las tuberías e intercambiadores de calor (condensadores de tubos y coraza o chillers enfriados por agua) actúa como un aislante térmico.</p><p>Por eso aumentan de forma sostenida la temperatura y la presión de condensación, y con ellas el consumo energético del compresor.</p>' }] },
    { id: 'cavitacion', n: '4.1', title: 'Cavitación acústica y microcorrientes', ref: 'M11 · Cavitación ultrasónica',
      cards: [{ ref: 'M11 · Cavitación ultrasónica', stamp: 'df', cite: 'Yao, 2016', title: 'Lo que hace el ultrasonido junto a la pared',
        body: '<p>Las ondas ultrasónicas de baja frecuencia que se propagan en un líquido generan cavitación acústica y microcorrientes acústicas (<i>acoustic microstreaming</i>). La cavitación produce microchorros, ondas de choque y una intensa mezcla local del fluido.</p><p>Las microcorrientes son movimientos localizados del fluido cerca de superficies sólidas: mejoran la circulación donde habría zonas de baja velocidad o estancamiento.</p><p>Así se reduce la resistencia térmica de la capa límite, los intercambiadores alcanzan mayores coeficientes de transferencia de calor y disminuyen los efectos de las incrustaciones y los depósitos. También ayuda a desprender la película de lubricante y los depósitos de las superficies internas de las tuberías.</p>' }] },
    { id: 'nano', n: '4.2', title: 'Nanolubricantes', ref: 'M11 · Aditivos nanotecnológicos',
      cards: [{ ref: 'M11 · Aditivos nanotecnológicos al lubricante', stamp: 'df', cite: `${PRAYOGO}, p. 401`, title: 'Un lubricante que conduce mejor el calor',
        body: `<p>Los nanolubricantes incrementan la conductividad térmica del lubricante y mejoran sus propiedades tribológicas: reducen la fricción y el desgaste, sobre todo en el compresor. Con ello se optimiza el intercambio térmico, disminuye la potencia requerida por el compresor y aumenta el coeficiente de desempeño (COP).</p><p>Nanopartículas: TiO₂, SiO₂ y Al₂O₃.</p><p>La mayor parte del lubricante queda en el compresor y una fracción circula mezclada con el refrigerante: <b class="n">${PCT}</b>.</p>` }] },
    { id: 'desafios', n: '4.3', title: 'Desafíos de los nanolubricantes', ref: 'M11 · Aditivos nanotecnológicos · Desafíos',
      cards: [{ ref: 'M11 · Desafíos en el uso de nanolubricantes', stamp: 'df', cite: `${PRAYOGO}, pp. 390–406`, title: 'Lo que falta resolver',
        body: '<ul><li>Mantener la estabilidad de la dispersión de las nanopartículas durante la operación.</li><li>Evitar la aglomeración y la sedimentación, que pueden obstruir componentes.</li><li>Garantizar la compatibilidad química entre nanopartículas, lubricantes y refrigerantes.</li><li>Evaluar los efectos del uso prolongado sobre compresores, válvulas e intercambiadores.</li><li>Reducir el costo de producción y aplicación.</li><li>Establecer normativas y estándares técnicos para su uso industrial.</li></ul>' }] },
    { id: 'comparacion', n: '4.4', title: 'Comparación de los dos métodos', ref: 'M11 · Comparación de rendimiento',
      cards: [{ ref: 'M11 · Comparación de los dos métodos', stamp: 'si', title: 'Dos métodos, dos lados', wide: true,
        body: '<table><tr><th></th><th>Cavitación ultrasónica</th><th>Aditivos nanotecnológicos</th></tr><tr><th>Punto de aplicación</th><td>Lado del agua de los intercambiadores</td><td>Lado del refrigerante: circuito hermético interno</td></tr><tr><th>Mecanismo</th><td>Implosión de microburbujas por ondas ultrasónicas</td><td>Eliminación del <i>oil fouling</i> y menor fricción</td></tr><tr><th>Impacto en el mantenimiento</th><td>Evita químicos ácidos nocivos y paradas prolongadas</td><td>No requiere desarmar tuberías ni modificar el diseño mecánico</td></tr></table>' }] },
    { id: 'panama', n: '4.5', title: 'Aplicación en Panamá', ref: 'M11 · Aplicación práctica al caso panameño',
      cards: [{ ref: 'M11 · Aplicación práctica al caso panameño', stamp: 'pr', title: 'Propuesta del informe',
        body: '<p><b>Cavitación ultrasónica:</b> en edificios comerciales de la Ciudad de Panamá y de la Zona Libre de Colón, los chillers enfriados por agua sufren incrustaciones biológicas y salinas por la calidad del agua de las torres de enfriamiento. Incluirla en el mantenimiento preventivo evita desincrustantes químicos agresivos que aceleran la corrosión y extiende la vida útil de los tubos.</p><p><b>Aditivos nanotecnológicos:</b> por la operación continua de equipos Split, VRF y Rooftop, la degradación por <i>oil fouling</i> es acelerada. Son una solución de rápida implementación y bajo costo inicial, que permite recuperar la capacidad de enfriamiento sin reemplazar los equipos.</p>' }] },
  ],
  refs: [
    'ASHRAE. (2021).',
    'DIRECT, S. (2023, OCTUBRE). Retrieved from https://www.sciencedirect.com/science/article/pii/S1359431123012401?ref=pdf_download&amp;fr=RR-2&amp;rr=a5071dc2189f7a26',
    'Prayogo, G. S., Mamat, R., Ghazali, M. F., Nugroho, A., Kozin, M., y Muriban, J. (2024). A review on nanolubricant for refrigeration systems: Stability, thermophysical properties, and performance characteristics. <i>Mechanical Engineering for Society and Industry, 4</i>(3), 388–414. https://doi.org/10.31603/mesi.12204',
    'Yao, Y. (2016). Research and applications of ultrasound in HVAC field: A review. <i>Renewable and Sustainable Energy Reviews, 58</i>, 52–68. https://doi.org/10.1016/j.rser.2015.12.222',
  ],
};
// Ruta principal: 4 escenas con rótulo breve; los pasos 4.0–4.5 quedan en la profundización (chips «Detalle»)
export const SC11 = [
  { id: 'E1', n: 'E1', level: 'RP', title: 'El sarro aísla', chips: ['fouling'],
    rot: { replay: true, ref: 'M11 · Cavitación ultrasónica', stamp: 'df', f: 'El sarro y el biofilm en los tubos actúan como aislante: suben la temperatura y la presión de condensación, y el compresor consume más', fc: 'ASHRAE, 2021; DIRECT, 2023',
      extra: '<span class="st il">Ilustrativo</span> Corte ampliado de un tubo del condensador. El indicador de consumo no tiene escala ni valores.' } },
  { id: 'E2', n: 'E2', level: 'RP', title: 'Cavitación ultrasónica', chips: ['cavitacion'],
    rot: { replay: true, ref: 'M11 · Cavitación ultrasónica', stamp: 'df', f: 'El ultrasonido genera cavitación y microcorrientes junto a la pared: mejora la transferencia de calor y reduce los depósitos', fc: 'Yao, 2016',
      extra: '<span class="st il">Ilustrativo</span> Animación: transductores, ondas y microburbujas que implosionan junto a la pared; los depósitos se desprenden y siguen con el agua.' } },
  { id: 'E3', n: 'E3', level: 'RP', title: 'Dónde está el aceite', chips: ['nano', 'desafios'],
    rot: { ref: 'M11 · Aditivos nanotecnológicos', stamp: 'df', f: 'Cerca de la mitad del lubricante queda en el compresor y el resto circula con el refrigerante; las nanopartículas mejoran la transferencia de calor', fc: PRAYOGO,
      c: PCT, cc: `${PRAYOGO}, p. 401`,
      extra: '<span class="st il">Ilustrativo</span> Circuito genérico de compresión; el aceite se resalta en ámbar y las nanopartículas se dibujan sin escala.' } },
  { id: 'E4', n: 'E4', level: 'RP', title: 'Dos métodos, dos lados', chips: ['comparacion', 'panama'],
    rot: { ref: 'M11 · Comparación · Conclusiones', stamp: 'si', f: 'La cavitación actúa en el lado del agua de los intercambiadores; el nanolubricante, dentro del circuito del refrigerante',
      extra: '<span class="st il">Ilustrativo</span> Vista dividida: a la izquierda, el lado del agua; a la derecha, el lado del refrigerante.' } },
];
