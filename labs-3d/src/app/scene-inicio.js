// Parada 0 · Inicio: dos pedestales con miniaturas hechas con la geometría real de cada parada (ilustrativas).
// Clic en una miniatura (o teclas 1 y 2): la cámara entra en ella y pasa a la parada.
import { INICIO } from 'app/content-inicio.js';

export function buildInicio({ THREE, label, go, fly, m6, m14 }) {
  const g = new THREE.Group(); g.name = 'parada_0_inicio';
  const ped = new THREE.MeshStandardMaterial({ color: 0x2A3036, roughness: 0.8 });
  const X = 5.5, pedestal = x => { const p = new THREE.Mesh(new THREE.CylinderGeometry(3.3, 3.5, 0.5, 48), ped); p.position.set(x, 0.25, 0); g.add(p); };
  pedestal(-X); pedestal(X);
  // M6: ventilador (correa corregida), filtro, serpentín y red de 4 ramales y 8 terminales, con el aire en movimiento
  const a = m6.mini(), A = new THREE.Group(); A.position.set(-X, 0.5, 0); g.add(A);
  a.group.scale.setScalar(0.22); a.group.position.set(0.12, 0, -0.1); A.add(a.group); // centrada en su pedestal
  // M14: planta REFRESH completa; D y E resaltados con sus fachadas
  const b = m14.mini(), Bg = new THREE.Group(); Bg.position.set(X, 0.5, 0); g.add(Bg);
  b.group.scale.setScalar(0.06); b.group.position.y = 0.013; Bg.add(b.group);
  let busy = false;
  const CAMIN = { 1: [-X + 1.2, 2.2, 3.4, -X + 0.6, 0.9, 0], 2: [X - 0.4, 3.2, 2.6, X - 1.4, 0.4, 0.2] }; // la cámara entra en la miniatura
  function enterStop(k) { // la cámara entra en la miniatura y luego pasa a la parada
    if (busy) return; busy = true; document.getElementById('start').hidden = true; fly(CAMIN[k]); setTimeout(() => { busy = false; go(k, 0); }, 1050);
  }
  const L1 = label(new THREE.Vector3(-X, 2.6, 0), INICIO.lbl1, { cls: 'amber', onClick: () => enterStop(1) });
  const L2 = label(new THREE.Vector3(X, 2.6, 0), INICIO.lbl2, { cls: 'cyan', onClick: () => enterStop(2) });
  return {
    group: g, ...INICIO.stop, note: INICIO.note, extraCards: INICIO.extraCards,
    steps: INICIO.steps.map(s => ({ ...s, labels: [L1, L2], cam: [0, 5.4, 15.2, 0, 1.2, 0] })),
    enterStop,
    pick(r) { if (r.intersectObject(A, true).length) return 1; if (r.intersectObject(Bg, true).length) return 2; return 0; },
    tick(dt) { A.rotation.y += dt * 0.12; Bg.rotation.y += dt * 0.08; if (a.wheel) a.wheel.rotation.z -= dt * 7; m6.air(dt); },
  };
}
