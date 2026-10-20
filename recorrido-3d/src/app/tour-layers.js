import * as THREE from 'three';

const V = (x, y, z) => new THREE.Vector3(x, y, z), UP = V(0, 1, 0);
const mat = (name, color, o = {}) => new THREE.MeshStandardMaterial({ name, color, roughness: o.r ?? 0.6, metalness: o.m ?? 0.1, emissive: o.e ?? 0x000000, emissiveIntensity: o.ei ?? 0 });
function box(g, name, w, h, d, m, x, y, z) { const o = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), m); o.name = name; o.position.set(x, y, z); g.add(o); return o; }
function cyl(g, name, r, h, m, x, y, z) { const o = new THREE.Mesh(new THREE.CylinderGeometry(r, r, h, 14), m); o.name = name; o.position.set(x, y, z); g.add(o); return o; }
function seg(g, name, a, b, r, m) {
  const dir = b.clone().sub(a), o = new THREE.Mesh(new THREE.CylinderGeometry(r, r, dir.length(), 8, 1, true), m);
  o.name = name; o.position.copy(a).add(b).multiplyScalar(0.5); o.quaternion.setFromUnitVectors(UP, dir.normalize()); g.add(o); return o;
}
function poly(g, name, pts, r, m) {
  const jg = new THREE.SphereGeometry(r, 8, 6);
  pts.forEach((p, i) => { if (i) seg(g, `${name}_${i}`, pts[i - 1], p, r, m); const j = new THREE.Mesh(jg, m); j.position.copy(p); g.add(j); });
}
function outline(g, name, w, h, d, x, y, z, color = 0xE6EBEF, op = 0.75) {
  const l = new THREE.LineSegments(new THREE.EdgesGeometry(new THREE.BoxGeometry(w, h, d)), new THREE.LineBasicMaterial({ color, transparent: true, opacity: op }));
  l.name = name; l.position.set(x, y, z); g.add(l); return l;
}

const P = {
  pants: mat('pantalon', 0x2E3A4A, { r: 0.9 }), vest: mat('chaleco_alta_visibilidad', 0xC9D63C, { r: 0.7, e: 0xC9D63C, ei: 0.15 }),
  skin: mat('piel', 0xB98A68, { r: 0.8 }), helmet: mat('casco', 0xF4F4F0, { r: 0.4 }), dark: mat('oscuro', 0x1E252B, { r: 0.5 }),
  glove: mat('guantes', 0xD8A23A, { r: 0.8 }), harness: mat('arnes', 0xF29E1F, { r: 0.6, e: 0xF29E1F, ei: 0.2 }),
  steel: mat('acero', 0xA7B0B8, { m: 0.6, r: 0.35 }), red: mat('bloqueo_rojo', 0xD0342C, { e: 0xD0342C, ei: 0.35 }),
  white: mat('tarjeta', 0xF4F1EA, { r: 0.8 }), desk: mat('escritorio', 0x8A7357, { r: 0.85 }),
  screen: mat('pantalla', 0x13232E, { e: 0x7FB4D6, ei: 0.55, r: 0.3 }), amber: mat('display_vfd', 0xF2C14E, { e: 0xF2C14E, ei: 0.9 }),
  machine: mat('recuperadora', 0xC9CED3, { r: 0.5 }), orange: mat('recuperadora_panel', 0xD9822B, { e: 0xD9822B, ei: 0.2 }),
  hose: mat('manguera', 0x3D6FA8, { r: 0.6 }), cylGray: mat('cilindro_recuperacion', 0x8F979E, { m: 0.4, r: 0.45 }), yellow: mat('cilindro_hombro', 0xE6C229, { r: 0.5 }),
};

function person(name, o = {}) {
  const g = new THREE.Group(); g.name = name;
  [-1, 1].forEach(s => {
    box(g, name + '_pierna', 0.15, 0.82, 0.16, P.pants, 0, 0.41, s * 0.1);
    box(g, name + '_brazo', 0.13, 0.56, 0.12, P.vest, 0.03, 1.13, s * 0.29);
    box(g, name + '_guante', 0.13, 0.13, 0.13, P.glove, 0.05, 0.79, s * 0.29);
  });
  box(g, name + '_torso', 0.26, 0.62, 0.44, P.vest, 0, 1.13, 0);
  const head = new THREE.Mesh(new THREE.SphereGeometry(0.12, 14, 10), P.skin); head.position.set(0, 1.6, 0); g.add(head);
  const hm = new THREE.Mesh(new THREE.SphereGeometry(0.145, 14, 8, 0, Math.PI * 2, 0, Math.PI / 2), P.helmet); hm.name = name + '_casco'; hm.position.set(0, 1.63, 0); g.add(hm);
  cyl(g, name + '_ala_casco', 0.17, 0.02, P.helmet, 0.02, 1.635, 0);
  box(g, name + '_barboquejo', 0.05, 0.02, 0.2, P.dark, 0.04, 1.47, 0);
  [-1, 1].forEach(s => box(g, name + '_barboquejo_lado', 0.02, 0.17, 0.02, P.dark, 0.03, 1.55, s * 0.11));
  box(g, name + '_gafas', 0.04, 0.065, 0.22, P.dark, 0.12, 1.625, 0);
  if (o.harness) {
    [-1, 1].forEach(s => box(g, name + '_arnes_tirante', 0.28, 0.6, 0.05, P.harness, 0, 1.15, s * 0.12));
    box(g, name + '_arnes_cintura', 0.28, 0.07, 0.46, P.harness, 0, 0.9, 0);
    [-1, 1].forEach(s => box(g, name + '_arnes_pierna', 0.18, 0.06, 0.18, P.harness, 0, 0.78, s * 0.1));
  }
  return g;
}

export function buildTour() {
  const G = {}, A = {};
  const grp = k => (G[k] = Object.assign(new THREE.Group(), { name: 'recorrido_parada_' + k }));

  // 1 · Seguridad (INV4)
  const g1 = grp('1');
  const t1 = person('tecnico_tablero'); t1.position.set(-13.62, 0, -10.4); t1.rotation.y = Math.PI; g1.add(t1);
  box(g1, 'candado_cuerpo', 0.09, 0.1, 0.08, P.red, -14.24, 0.56, -10.28);
  const sh = new THREE.Mesh(new THREE.TorusGeometry(0.035, 0.01, 6, 14, Math.PI), P.steel); sh.position.set(-14.24, 0.61, -10.28); sh.rotation.y = Math.PI / 2; g1.add(sh);
  box(g1, 'tarjeta_bloqueo', 0.01, 0.17, 0.1, P.white, -14.25, 0.42, -10.16);
  box(g1, 'tarjeta_bloqueo_franja', 0.012, 0.04, 0.1, P.red, -14.25, 0.49, -10.16);
  const cylC = [0xD98FA6, 0x9CC7E3, 0xC7392F];
  box(g1, 'tarima_cilindros', 2.0, 0.1, 0.8, P.desk, -8, 0.05, -6.5);
  [-8.6, -8, -7.4].forEach((x, i) => {
    const m = mat('cilindro_' + ['R410A', 'R32', 'R290'][i], cylC[i], { r: 0.45, m: 0.2 });
    cyl(g1, 'cilindro_' + i, 0.17, 0.85, m, x, 0.53, -6.5);
    const top = new THREE.Mesh(new THREE.SphereGeometry(0.17, 12, 6, 0, Math.PI * 2, 0, Math.PI / 2), m); top.position.set(x, 0.955, -6.5); g1.add(top);
    cyl(g1, 'valvula_' + i, 0.04, 0.12, P.steel, x, 1.17, -6.5);
    if (i === 1) cyl(g1, 'franja_A2L', 0.172, 0.08, P.red, x, 0.9, -6.5);
  });
  const RY = 15.8;
  [-3.8, 3.8].forEach((x, i) => cyl(g1, 'poste_linea_vida_' + i, 0.05, 1.0, P.steel, x, RY + 0.5, -16.4));
  seg(g1, 'linea_de_vida', V(-3.8, RY + 0.95, -16.4), V(3.8, RY + 0.95, -16.4), 0.025, P.harness);
  const t2 = person('tecnico_azotea', { harness: true }); t2.position.set(1, RY, -15); t2.rotation.y = Math.PI / 2; g1.add(t2);
  poly(g1, 'eslinga', [V(1, RY + 1.3, -14.86), V(1, RY + 1.45, -15.6), V(1, RY + 0.95, -16.4)], 0.02, P.harness);
  Object.assign(A, {
    tech: V(-13.62, 1.85, -10.4), lock: V(-14.24, 0.56, -10.28), tablero: V(-14.55, 1.12, -10.4), cyl: V(-8, 1.25, -6.5),
    hot: V(-18.2, 1.85, -9.6), roofTech: V(1, RY + 1.85, -15), roofEdge: V(4.4, RY + 0.1, -17.1),
  });

  // 2 · Planificación (INV2) — oficina en el primer alto con mini-split
  const g2 = grp('2'), y1 = 3.6 + 0.25;
  outline(g2, 'oficina_contorno', 6, 3.05, 4.2, -20, y1 + 1.525, 2.8);
  box(g2, 'escritorio', 1.4, 0.06, 0.7, P.desk, -18.2, y1 + 0.75, 2.1);
  [[-0.62, -0.28], [0.62, -0.28], [-0.62, 0.28], [0.62, 0.28]].forEach(([dx, dz], i) => box(g2, 'escritorio_pata_' + i, 0.05, 0.72, 0.05, P.dark, -18.2 + dx, y1 + 0.36, 2.1 + dz));
  box(g2, 'monitor_CMMS', 0.62, 0.38, 0.04, P.screen, -18.2, y1 + 1.03, 1.86);
  box(g2, 'monitor_pie', 0.06, 0.2, 0.06, P.dark, -18.2, y1 + 0.85, 1.84);
  outline(g2, 'minisplit_resaltado', 0.4, 0.5, 1.2, -22.72, 6.3, 3.5, 0x8FDB93, 0.95);
  Object.assign(A, { split2: V(-22.6, 6.5, 3.5), cond2: V(-23.65, 4.95, 3.5), cmms: V(-18.2, y1 + 1.25, 1.86), office: V(-20, y1 + 0.1, 4.6) });

  // 3 · Refrigerantes (INV1) — condensadora del mini-split 1 y atmósfera
  const g3 = grp('3');
  box(g3, 'recuperadora_cuerpo', 0.6, 0.42, 0.42, P.machine, -25.7, 0.21, 4.7);
  box(g3, 'recuperadora_panel', 0.02, 0.26, 0.34, P.orange, -25.39, 0.25, 4.7);
  [-0.08, 0.08].forEach((dz, i) => { const c = cyl(g3, 'manometro_' + i, 0.05, 0.02, P.white, -25.38, 0.33, 4.7 + dz); c.rotation.z = Math.PI / 2; });
  cyl(g3, 'cilindro_recuperacion', 0.19, 0.8, P.cylGray, -26.5, 0.4, 5.5);
  const sh3 = new THREE.Mesh(new THREE.SphereGeometry(0.19, 12, 6, 0, Math.PI * 2, 0, Math.PI / 2), P.yellow); sh3.position.set(-26.5, 0.8, 5.5); g3.add(sh3);
  poly(g3, 'manguera_unidad', [V(-25.42, 0.3, 4.55), V(-24.8, 0.04, 4.2), V(-23.75, 0.04, 3.7), V(-23.5, 0.6, 3.46)], 0.025, P.hose);
  poly(g3, 'manguera_cilindro', [V(-25.98, 0.3, 4.8), V(-26.3, 0.04, 5.2), V(-26.5, 1.0, 5.5)], 0.025, P.hose);
  const LN = 160, leakIm = new THREE.InstancedMesh(new THREE.IcosahedronGeometry(1, 0), new THREE.MeshBasicMaterial({ color: 0xE9B8DA, transparent: true, opacity: 0.55, depthWrite: false }), LN);
  leakIm.name = 'fuga_refrigerante'; leakIm.frustumCulled = false; g3.add(leakIm);
  const seeds = Array.from({ length: LN }, (_, i) => [i / LN, Math.sin(i * 12.9898) * 0.5 + 0.5, Math.sin(i * 78.233) * 0.5 + 0.5]);
  Object.assign(A, { leak: V(-27.6, 0.35, 1.2), atmos: V(-30, 13.5, 0.5), machine: V(-25.7, 0.5, 4.7), cond1: V(-23.65, 1.3, 3) });

  // 4 · Energía (INV5) — UMA_03 con VFD
  const g4 = grp('4');
  box(g4, 'VFD_gabinete', 0.3, 0.5, 0.22, P.dark, -6.35, 1.0, -3.4);
  box(g4, 'VFD_display', 0.18, 0.08, 0.01, P.amber, -6.35, 1.12, -3.285);
  poly(g4, 'VFD_cable', [V(-6.35, 0.75, -3.3), V(-6.35, 0.62, -2.62), V(-7.2, 0.62, -2.62)], 0.018, P.dark);
  outline(g4, 'UMA_resaltada', 1.8, 1.5, 1.3, -7.5, 0.85, -3.2, 0xF2C14E, 0.9);
  box(g4, 'mesa_BMS', 1.6, 0.06, 0.7, P.desk, -11.2, 1.0, 1.6);
  [[-0.72, -0.28], [0.72, -0.28], [-0.72, 0.28], [0.72, 0.28]].forEach(([dx, dz], i) => box(g4, 'mesa_pata_' + i, 0.05, 0.72, 0.05, P.dark, -11.2 + dx, 0.62, 1.6 + dz));
  box(g4, 'pantalla_BMS_EMS', 0.8, 0.46, 0.04, P.screen, -11.4, 1.3, 1.36);
  box(g4, 'carpeta_auditoria', 0.3, 0.04, 0.4, P.white, -10.6, 1.05, 1.7);
  Object.assign(A, { vfd: V(-6.35, 1.3, -3.4), uma3: V(-7.5, 1.65, -3.2), filter: V(-8.3, 0.85, -3.2), bmsScreen: V(-11.4, 1.6, 1.36), audit: V(-10.6, 1.1, 1.7), iplv: V(-17.8, 2.25, -11) });

  // 5 · Innovación: reutiliza el modelo (grupo vacío)
  grp('5');

  // Vista integrada: íconos + flecha
  const gi = grp('i');
  const PI = [V(-15.6, 4.6, -10.4), V(-20, 8.6, 3.2), V(-26.5, 15.5, 2.2), V(-7.5, 3.4, -3.2), V(0, 22, 2)];
  const glow = new THREE.MeshBasicMaterial({ color: 0xFFF4D6 }), arrowM = new THREE.MeshBasicMaterial({ color: 0xF1E3C0, transparent: true, opacity: 0.85 });
  const arcs = [];
  PI.forEach((p, i) => {
    const s = new THREE.Mesh(new THREE.SphereGeometry(0.5, 18, 12), glow); s.name = 'icono_parada_' + (i + 1); s.position.copy(p); gi.add(s);
    const r = new THREE.Mesh(new THREE.TorusGeometry(0.85, 0.05, 8, 32), glow); r.position.copy(p); gi.add(r); r.userData.ring = true;
    if (!i) return;
    const a = PI[i - 1], b = p, d = b.clone().sub(a).normalize();
    const a1 = a.clone().addScaledVector(d, 1.1), b1 = b.clone().addScaledVector(d, -1.5);
    const mid = a1.clone().add(b1).multiplyScalar(0.5).add(V(0, 2.2, 0));
    const c = new THREE.QuadraticBezierCurve3(a1, mid, b1);
    const tube = new THREE.Mesh(new THREE.TubeGeometry(c, 40, 0.09, 6), arrowM); tube.name = 'flecha_' + i; gi.add(tube);
    const tan = c.getTangent(1), cone = new THREE.Mesh(new THREE.ConeGeometry(0.32, 0.8, 12), arrowM);
    cone.position.copy(b1).addScaledVector(tan, 0.3); cone.quaternion.setFromUnitVectors(UP, tan); gi.add(cone);
    arcs.push(c.getPoints(40));
  });
  A.icons = PI;

  const tmp = new THREE.Object3D();
  function tick(t) {
    if (G['3'].visible) {
      // Vapor más denso que el aire (densidad de vapor ≈ 3; aire = 1): sale de la condensadora,
      // cae al piso y se extiende en una capa baja que se diluye (no asciende).
      seeds.forEach(([ph, s1, s2], i) => {
        const f = (ph + t * 0.06) % 1;
        const th = Math.PI + (s1 - 0.5) * 2.4;            // abanico hacia afuera del edificio (−x)
        let x, y, z, sx, sy;
        if (f < 0.14) {                                     // chorro corto que cae por gravedad
          const k = f / 0.14;
          x = -23.9 + Math.cos(th) * 1.4 * k; z = 3 + Math.sin(th) * 1.4 * k;
          y = 1.25 - 1.05 * k * k; sx = 0.06 + 0.12 * k; sy = sx;
        } else {                                            // capa a ras de piso que se expande
          const k = (f - 0.14) / 0.86, r = 1.4 + 5.2 * Math.sqrt(k) * (0.55 + 0.45 * s2);
          x = -23.9 + Math.cos(th) * r + Math.sin(t * 0.5 + s1 * 6.28) * 0.15;
          z = 3 + Math.sin(th) * r;
          y = 0.12 + 0.18 * s2 + 0.1 * k; sx = 0.18 + 0.5 * k; sy = sx * 0.35;
        }
        if (f > 0.8) { const fd = (1 - f) / 0.2; sx *= fd; sy *= fd; }
        tmp.position.set(x, y, z); tmp.scale.set(sx, sy, sx); tmp.rotation.set(0, s1 * 6, 0);
        tmp.updateMatrix(); leakIm.setMatrixAt(i, tmp.matrix);
      });
      leakIm.instanceMatrix.needsUpdate = true;
    }
    if (G.i.visible) gi.children.forEach(o => { if (o.userData.ring) { o.lookAt(o.position.clone().add(V(0, 0, 1))); o.scale.setScalar(1 + 0.12 * Math.sin(t * 3)); } });
  }
  return { groups: G, A, arcs, tick };
}
