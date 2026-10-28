// Texto de la parada 0 (inicio). Fuente: portadas e introducciones de los Word del M6, M14 (Cristian Batista),
// M8 y M11 (Manuel Jiménez). Sin cifras ni fechas.
export const INICIO = {
  extraCards: [
      { ref: 'M6 · Introducción', title: '1 · Módulo 6 — Mantenimiento de Ventiladores y Sistemas de Distribución',
        body: '<p class="au">Cristian Batista</p>' },
      { ref: 'M14 · Introducción', title: '2 · Módulo 14 — Digitalización, BIM y Gestión Inteligente de Instalaciones (MEP)',
        body: '<p class="au">Cristian Batista</p>' },
      { ref: 'M8 · Introducción', title: '3 · Módulo 8 — Aplicaciones Avanzadas de Refrigeración y Aire Acondicionado',
        body: '<p class="au">Manuel Jiménez</p>' },
      { ref: 'M11 · Introducción', title: '4 · Módulo 11 — Métodos Innovadores de Mantenimiento',
        body: '<p class="au">Manuel Jiménez</p>' },
      { fold: true, title: 'Cómo se recorre (teclas)',
        body: '<ul><li><b class="n">0 a 4</b> cambian de parada.</li><li><b class="n">← →</b> avanzan por la ruta principal y pasan de una parada a la siguiente.</li><li><b class="n">P</b> incluye la profundización en ← →; también se abre con un clic en la lista de la derecha.</li><li><b class="n">R</b> abre las referencias del informe de la parada.</li><li>Cada tarjeta indica su sección, figura o tabla del informe y su sello: <span class="st df">Dato de fuente</span>, <span class="st il">Ilustrativo</span>, <span class="st pr">Propuesta</span> o <span class="st si">Síntesis del informe</span>.</li></ul>' },
    ],
  stop: { kicker: 'Inicio', short: 'Inicio', title: 'Laboratorios del Grupo A', lead: 'Cuatro paradas, una por informe. Cada una tiene su ruta principal y su profundización.' },
  note: 'Modelo conceptual, no a escala. Miniaturas de las paradas: ilustrativas.',
  // Etiquetas de las miniaturas: sello, título, autor y los títulos de sus 4 escenas (sin cifras)
  lbl: [
    '<span class="st il">Ilustrativo · miniatura</span>1 · M6 · Ventiladores y distribución<small class="au">Cristian Batista</small><small>La red y su criterio</small><small>Cerrar una compuerta mueve a todas</small><small>Abrir compuertas y bajar el ventilador</small><small>Panamá</small>',
    '<span class="st il">Ilustrativo · miniatura</span>2 · M14 · BIM y gestión MEP<small class="au">Cristian Batista</small><small>De la planta a la zona de estudio</small><small>Cuánto confiar en el modelo: LOD</small><small>Una falla de punta a punta</small><small>Hoy frente a la propuesta</small>',
    '<span class="st il">Ilustrativo · miniatura</span>3 · M8 · District Cooling<small class="au">Manuel Jiménez</small><small>Una planta para muchos edificios</small><small>Frío que sale, calor que vuelve</small><small>La estación de cada edificio</small><small>¿Y en Panamá?</small>',
    '<span class="st il">Ilustrativo · miniatura</span>4 · M11 · Mantenimiento innovador<small class="au">Manuel Jiménez</small><small>El sarro aísla</small><small>Cavitación ultrasónica</small><small>Dónde está el aceite</small><small>Dos métodos, dos lados</small>',
  ],
  steps: [{
    n: '0', level: 'RP', title: 'Inicio',
    start: `<div class="uni">Universidad Tecnológica de Panamá · Facultad de Ingeniería Mecánica · Lic. en Ingeniería de Mantenimiento</div>
      <h2>Laboratorios del Grupo A</h2>
      <p>Mantenimiento de Sistemas de Refrigeración y Aire Acondicionado · Prof. Doris de León · Grupo A · Cristian Batista y Manuel Jiménez</p>`,
  }],
};
