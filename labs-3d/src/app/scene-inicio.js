// Parada 0 · Inicio: cuatro pedestales con miniaturas hechas con la geometría real de cada parada (ilustrativas),
// en el orden 1 M6, 2 M14, 3 M8, 4 M11. Clic en una miniatura (o teclas 1–4): la cámara entra en ella y pasa a la parada.
import { INICIO } from 'app/content-inicio.js';

export function buildInicio({ THREE, label, go, fly, m6, m14, m8, m11 }) {
  const g = new THREE.Group(); g.name = 'parada_0_inicio';
  const ped = new THREE.MeshStandardMaterial({ color: 0x2A3036, roughness: 0.8 });
  const XS = [-11.4, -3.8, 3.8, 11.4], R = 3.3;
  const pedestal = x => { const p = new THREE.Mesh(new THREE.CylinderGeometry(R, R + 0.2, 0.5, 48), ped); p.position.set(x, 0.25, 0); g.add(p); };
  XS.forEach(pedestal);
  // Miniaturas: M6 (ventilador y red, con el aire en movimiento), M14 (planta REFRESH; D y E resaltados),
  // M8 (ciudad con la planta central y la red), M11 (chiller y circuito de compresión)
  const mk = (src, x, s, dx = 0, dy = 0, dz = 0) => { const grp = new THREE.Group(); grp.position.set(x, 0.5, 0); g.add(grp); src.group.scale.setScalar(s); src.group.position.set(dx, dy, dz); grp.add(src.group); return grp; };
  const a = m6.mini(), A = mk(a, XS[0], 0.22, 0.12, 0, -0.1);
  const b = m14.mini(), Bg = mk(b, XS[1], 0.06, 0, 0.013);
  const c = m8.mini(), Cg = mk(c, XS[2], 0.07, 0, 0.08); // elevada para que la red enterrada quede sobre el pedestal
  const d = m11.mini(), Dg = mk(d, XS[3], 0.18, 0, 0.01);
  const MIN = [A, Bg, Cg, Dg];
  let busy = false;
  // La cámara entra en la miniatura y luego pasa a la parada
  const CAMIN = { 1: [XS[0] + 1.2, 2.2, 3.4, XS[0] + 0.6, 0.9, 0], 2: [XS[1] - 0.4, 3.2, 2.6, XS[1] - 1.4, 0.4, 0.2], 3: [XS[2] + 0.6, 2.6, 3.0, XS[2], 0.7, 0], 4: [XS[3] + 0.4, 2.2, 3.0, XS[3], 0.8, 0] };
  function enterStop(k) {
    if (busy) return; busy = true; document.getElementById('start').hidden = true; fly(CAMIN[k]); setTimeout(() => { busy = false; go(k, 0); }, 1050);
  }
  const L = INICIO.lbl.map((html, i) => label(new THREE.Vector3(XS[i], 2.4, 0), html, { cls: i < 2 ? 'amber' : 'cyan', onClick: () => enterStop(i + 1) }));
  return {
    group: g, ...INICIO.stop, note: INICIO.note, extraCards: INICIO.extraCards,
    steps: INICIO.steps.map(s => ({ ...s, labels: L, cam: [0, 8.4, 25, 0, 1.0, 0] })),
    enterStop,
    pick(r) { for (let i = 0; i < MIN.length; i++) if (r.intersectObject(MIN[i], true).length) return i + 1; return 0; },
    tick(dt) { MIN.forEach((m, i) => m.rotation.y += dt * [0.12, 0.08, 0.08, 0.1][i]); if (a.wheel) a.wheel.rotation.z -= dt * 7; m6.air(dt); m8.air(dt); m11.air(dt); },
  };
}
