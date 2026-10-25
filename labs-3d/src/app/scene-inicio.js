// Parada 0 · Inicio: dos pedestales con maquetas ilustrativas (ventilador del M6, planta del M14).
import { INICIO } from 'app/content-inicio.js';

export function buildInicio({ THREE, label, go }) {
  const g = new THREE.Group(); g.name = 'parada_0_inicio';
  const M = (c, o = {}) => new THREE.MeshStandardMaterial({ color: c, roughness: 0.75, metalness: 0.1, ...o });
  const ped = M(0x2A3036), metal = M(0xB8C2CA, { metalness: 0.3, roughness: 0.5 }), blade = M(0x6FA8C8);
  const pedestal = x => { const p = new THREE.Mesh(new THREE.CylinderGeometry(3.2, 3.4, 0.6, 40), ped); p.position.set(x, 0.3, 0); g.add(p); return p; };
  pedestal(-5); pedestal(5);
  // Maqueta del M6: carcasa de ventilador con rodete que gira y un tramo de ducto
  const fan = new THREE.Group(); fan.position.set(-5, 0.6, 0); g.add(fan);
  const hous = new THREE.Mesh(new THREE.CylinderGeometry(1.25, 1.25, 0.9, 40, 1, true), metal); hous.rotation.z = Math.PI / 2; hous.position.y = 1.6; fan.add(hous);
  const wheel = new THREE.Group(); wheel.position.y = 1.6; fan.add(wheel);
  for (let i = 0; i < 8; i++) { const b = new THREE.Mesh(new THREE.BoxGeometry(0.06, 1.05, 0.7), blade); b.position.y = 0.5; const a = new THREE.Group(); a.rotation.x = i * Math.PI / 4; a.add(b); wheel.add(a); }
  const duct = new THREE.Mesh(new THREE.BoxGeometry(2.2, 0.8, 0.8), metal); duct.position.set(1.6, 1.6, 0); fan.add(duct);
  const base = new THREE.Mesh(new THREE.BoxGeometry(1.4, 0.35, 1.2), ped); base.position.y = 0.2; fan.add(base);
  // Maqueta del M14: volúmenes de una planta (ilustrativa, sin escala)
  const plant = new THREE.Group(); plant.position.set(5, 0.6, 0); g.add(plant);
  const blk = (w, h, d, x, z, c) => { const m = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), M(c)); m.position.set(x, h / 2, z); plant.add(m); };
  blk(2.4, 1.1, 1.2, 0.3, -0.7, 0xC9CFD4); blk(1.8, 0.7, 1.0, 0.1, 0.8, 0xB5BCC2);
  blk(0.6, 0.45, 1.2, -1.75, -1.0, 0x7FB3D5); blk(0.6, 0.45, 1.2, -1.75, 0.3, 0x9AA6B1); blk(0.5, 0.4, 1.0, -1.75, 1.5, 0x7FB3D5);
  const L1 = label(new THREE.Vector3(-5, 4.2, 0), INICIO.lbl1, { cls: 'amber', onClick: () => go(1, 0) });
  const L2 = label(new THREE.Vector3(5, 3.2, 0), INICIO.lbl2, { cls: 'cyan', onClick: () => go(2, 0) });
  return {
    group: g, ...INICIO.stop, note: INICIO.note, extraCards: INICIO.extraCards,
    steps: INICIO.steps.map(s => ({ ...s, labels: [L1, L2], cam: [0, 9, 19, 0, 3.2, 0] })),
    tick(dt) { wheel.rotation.x += dt * 2.4; plant.rotation.y += dt * 0.15; },
  };
}
