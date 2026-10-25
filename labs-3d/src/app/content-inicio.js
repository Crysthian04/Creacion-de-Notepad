// Texto de la parada 0 (inicio). Fuente: portadas e introducciones de los Word del M6 y del M14.
export const INICIO = {
  extraCards: [
      { ref: 'M6 · Introducción', title: '1 · Módulo 6 — Mantenimiento de Ventiladores y Sistemas de Distribución',
        body: '<p>Métodos de balanceo de aire bajo los procedimientos de NEBB y AABC, su efecto sobre el consumo de energía y su aplicación al caso panameño.</p>' },
      { ref: 'M14 · Introducción', title: '2 · Módulo 14 — Digitalización, BIM y Gestión Inteligente de Instalaciones (MEP)',
        body: '<p>Metodología BIM y niveles de desarrollo (LOD), ventajas cuantificadas, un caso real de gemelo digital en climatización y un esquema MEP integrado para la planta REFRESH S.A., un proyecto académico de la carrera.</p>' },
      { fold: true, title: 'Cómo se recorre (teclas)',
        body: '<ul><li><b class="n">0 · 1 · 2</b> cambian de parada.</li><li><b class="n">← →</b> avanzan por la ruta principal.</li><li><b class="n">P</b> incluye la profundización en ← →; también se abre con un clic en la lista de la derecha.</li><li><b class="n">R</b> abre las referencias del informe de la parada.</li><li>Cada tarjeta indica su sección, figura o tabla del informe y su sello: <span class="st df">Dato de fuente</span> o <span class="st il">Ilustrativo</span>.</li></ul>' },
    ],
  stop: { kicker: 'Inicio', short: 'Inicio', title: 'Laboratorios M6 y M14', lead: 'Dos paradas, una por informe. Cada una tiene su ruta principal y su profundización.' },
  note: 'Modelo conceptual, no a escala. Maquetas del inicio: ilustrativas.',
  lbl1: '<span class="st il">Ilustrativo</span>1 · M6<small>Ventiladores y distribución</small>',
  lbl2: '<span class="st il">Ilustrativo</span>2 · M14<small>BIM y gestión MEP</small>',
  steps: [{
    n: '0', level: 'RP', title: 'Inicio',
    start: `<div class="uni">Universidad Tecnológica de Panamá · Facultad de Ingeniería Mecánica · Lic. en Ingeniería de Mantenimiento</div>
      <h2>Laboratorios M6 y M14</h2>
      <p>Mantenimiento de Sistemas de Refrigeración y Aire Acondicionado · Prof. Doris de León · Grupo A · Cristian Batista · Entrega:&nbsp;28&nbsp;de&nbsp;octubre&nbsp;de&nbsp;2026</p>`,
  }],
};
