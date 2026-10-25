// Parada 2 · M14 (se programa en su propio entregable).
export function buildM14({ THREE }) {
  const g = new THREE.Group(); g.name = 'parada_2_m14';
  return {
    group: g, kicker: 'Parada 2 · M14', short: 'M14', title: 'BIM y gestión MEP', lead: '', note: 'Modelo conceptual, no a escala.',
    steps: [{ n: '2.0', level: 'RP', title: 'Pendiente', cards: [{ title: 'Parada pendiente', body: '<p>Esta parada se programa en el siguiente entregable.</p>' }], cam: [0, 8, 18, 0, 1, 0] }],
  };
}
