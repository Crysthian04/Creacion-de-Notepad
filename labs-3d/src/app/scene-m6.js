// Parada 1 · M6 (se programa en su propio entregable).
export function buildM6({ THREE }) {
  const g = new THREE.Group(); g.name = 'parada_1_m6';
  return {
    group: g, kicker: 'Parada 1 · M6', short: 'M6', title: 'Ventiladores y distribución', lead: '', note: 'Modelo conceptual, no a escala.',
    steps: [{ n: '1.0', level: 'RP', title: 'Pendiente', cards: [{ title: 'Parada pendiente', body: '<p>Esta parada se programa en el siguiente entregable.</p>' }], cam: [0, 8, 18, 0, 1, 0] }],
  };
}
