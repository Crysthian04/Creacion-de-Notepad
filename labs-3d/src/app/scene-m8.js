// Parada 3 · M8: ciudad genérica (ilustrativa) con una planta central de District Cooling, red enterrada de
// suministro (azul) y retorno (rojo) y cuatro edificios con su estación de intercambio. Toda la geometría es
// ilustrativa: no es Panamá ni un lugar real. El texto está en content-m8.js.
import { M8, SC8 } from 'app/content-m8.js';

export function buildM8({ THREE, label }) {
  const g = new THREE.Group(); g.name = 'parada_3_m8';
  const M = (c, o = {}) => new THREE.MeshStandardMaterial({ color: c, roughness: 0.75, metalness: 0.1, ...o });
  const T = (c, op) => new THREE.MeshStandardMaterial({ color: c, transparent: true, opacity: op, depthWrite: false, roughness: 0.8 });
  const C = {
    ground: T(0x3E4A3F, 0.72), road: T(0x23282C, 0.6), under: M(0x1A1E21, { roughness: 1 }),
    bldg: M(0xC9D1D8), bldg2: M(0xAEB8C1), glass: M(0x7FA9C4, { metalness: 0.3, roughness: 0.4 }), hosp: M(0xE6EBEF), uni: M(0xD8C9A8), res: M(0xBFB4A6), ctx: M(0x8F9AA4), low: M(0xB8C2CA),
    plant: T(0x8F9AA4, 0.22), slab: M(0x5A646D), chiller: M(0x5F8FA8, { metalness: 0.35, roughness: 0.45 }), comp: M(0x3A424A), tower: M(0xD5DCE2), fan: M(0x3A424A), tank: M(0xE6EBEF, { metalness: 0.25, roughness: 0.5 }),
    pump: M(0x2E6E8E), motor: M(0x6E7A85), ctrl: M(0x2A3036), screen: M(0x29A9E0, { emissive: 0x0E4A66 }),
    sup: M(0x29A9E0, { emissive: 0x0B3346 }), ret: M(0xE5534B, { emissive: 0x3A1210 }), ets: M(0x4FAE5B),
    hx: M(0xA9B2BA, { metalness: 0.5, roughness: 0.35 }), valve: M(0xE3A857), meter: M(0x2A3036), bsup: M(0x7FD6FF, { emissive: 0x123844 }), bret: M(0xF29AA0, { emissive: 0x3A1C1E }),
    fc: M(0xD5DCE2), zone: new THREE.MeshBasicMaterial({ color: 0xE3A857, transparent: true, opacity: 0, depthWrite: false, side: THREE.DoubleSide }),
  };
  const v3 = (x, y, z) => new THREE.Vector3(x, y, z);
  const box = (w, h, d, m, x, y, z, parent = g, name = '') => { const o = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), m); o.position.set(x, y, z); o.name = name; parent.add(o); return o; };
  const cyl = (r, h, m, x, y, z, parent = g, name = '', seg = 20) => { const o = new THREE.Mesh(new THREE.CylinderGeometry(r, r, h, seg), m); o.position.set(x, y, z); o.name = name; parent.add(o); return o; };
  const UP = v3(0, 1, 0);
  const seg = (a, b, r, m, parent) => { const d = b.clone().sub(a), l = d.length(); const o = new THREE.Mesh(new THREE.CylinderGeometry(r, r, l, 10), m); o.position.copy(a).add(b).multiplyScalar(0.5); o.quaternion.setFromUnitVectors(UP, d.normalize()); parent.add(o); return o; };
  const tube = (pts, r, m, parent = g) => { for (let i = 0; i < pts.length - 1; i++) seg(pts[i], pts[i + 1], r, m, parent); for (let i = 1; i < pts.length - 1; i++) { const j = new THREE.Mesh(new THREE.SphereGeometry(r, 10, 8), m); j.position.copy(pts[i]); parent.add(j); } };
  // Recorrido por una polilínea (u en [0, 1))
  const poly = pts => { const sg = []; let L = 0; for (let i = 0; i < pts.length - 1; i++) { const l = pts[i].distanceTo(pts[i + 1]); sg.push({ a: pts[i], b: pts[i + 1], l }); L += l; }
    return { L, at(u, out) { let d = ((u % 1) + 1) % 1 * L; for (const s of sg) { if (d <= s.l) return out.copy(s.a).lerp(s.b, s.l ? d / s.l : 0); d -= s.l; } return out.copy(pts[pts.length - 1]); } }; };

  // ---------- Terreno, calles y subsuelo (la red enterrada se ve a través del suelo) ----------
  box(80, 0.1, 56, C.under, 0, -1.6, 0, g, 'subsuelo');
  const gr = box(80, 0.08, 56, C.ground, 0, -0.04, 0, g, 'terreno'); gr.receiveShadow = true; gr.userData.noShadow = true;
  [[80, 4, 0, 0], [4, 56, 12, 0], [4, 56, -14, 0]].forEach(([w, d, x, z]) => { const r = box(w, 0.02, d, C.road, x, 0.02, z, g, 'calle'); r.userData.noShadow = true; });

  // ---------- Planta central: chillers, torres, bombas, tanque de almacenamiento y sala de control ----------
  const plant = new THREE.Group(); plant.name = 'planta_central'; g.add(plant);
  box(13, 0.3, 12, C.slab, -25, 0.15, -10.5, plant, 'losa_planta');
  [[13, 4.2, 0.12, -25, 2.1, -4.5], [13, 4.2, 0.12, -25, 2.1, -16.5], [0.12, 4.2, 12, -31.5, 2.1, -10.5], [0.12, 4.2, 12, -18.5, 2.1, -10.5]].forEach(([w, h, d, x, y, z]) => box(w, h, d, C.plant, x, y, z, plant, 'muro_planta'));
  const chillers = [];
  for (const x of [-29, -25, -21]) { // shells de evaporador y condensador + compresor
    const c = new THREE.Group(); c.position.set(x, 0, -13); c.name = 'chiller'; plant.add(c); chillers.push(c);
    for (const y of [0.95, 2.05]) { const s = cyl(0.5, 3.2, C.chiller, 0, y, 0, c, 'shell'); s.rotation.z = Math.PI / 2; }
    box(1.0, 0.7, 0.8, C.comp, 0, 2.95, 0, c, 'compresor'); box(3.4, 0.25, 1.2, C.slab, 0, 0.42, 0, c);
  }
  const pumps = [];
  for (let i = 0; i < 4; i++) { const x = -29.5 + i * 2; cyl(0.32, 0.7, C.pump, x, 0.7, -7.2, plant, 'bomba'); const m = cyl(0.25, 0.8, C.motor, x + 0.55, 0.7, -7.2, plant, 'motor_bomba'); m.rotation.z = Math.PI / 2; pumps.push(m); }
  const ctrl = box(3.2, 2.6, 3.0, C.ctrl, -20.6, 1.6, -6.6, plant, 'sala_control');
  [-21.4, -20.6, -19.8].forEach(x => box(0.6, 0.4, 0.04, C.screen, x, 2.0, -5.08, plant, 'pantalla_scada'));
  const fans = [];
  for (const x of [-29, -25, -21]) { // torres de enfriamiento sobre su losa, al norte de la nave
    box(3.4, 4.6, 3.4, C.tower, x, 2.6, -21, plant, 'torre_enfriamiento');
    cyl(1.3, 0.8, C.tower, x, 5.3, -21, plant, 'chimenea_torre', 24);
    const f = new THREE.Group(); f.position.set(x, 5.55, -21); plant.add(f); fans.push(f);
    for (let k = 0; k < 4; k++) { const b = box(2.2, 0.06, 0.32, C.fan, 0, 0, 0, f); b.rotation.y = k * Math.PI / 4; }
  }
  box(13, 0.3, 4.6, C.slab, -25, 0.15, -21, plant, 'losa_torres');
  cyl(2.0, 9, C.tank, -34, 4.6, -10.5, plant, 'tanque_almacenamiento_termico', 32);
  cyl(2.05, 0.2, C.slab, -34, 9.2, -10.5, plant, '', 32);
  // Colectores: de los chillers a la red (suministro) y de la red a los chillers (retorno)
  tube([v3(-29, 1.4, -12.1), v3(-21, 1.4, -12.1)], 0.18, C.sup, plant); tube([v3(-29, 1.9, -11.6), v3(-21, 1.9, -11.6)], 0.18, C.ret, plant);
  tube([v3(-25.6, 1.4, -12.1), v3(-25.6, 1.4, -5.2), v3(-25.6, -0.6, -5.2)], 0.2, C.sup, plant);
  tube([v3(-24.4, 1.9, -11.6), v3(-24.4, 1.9, -5.0), v3(-24.4, -1.0, -5.0)], 0.2, C.ret, plant);

  // ---------- Edificios y estaciones de intercambio ----------
  const B = {}; const bl = (k, parts, ets) => { const grp = new THREE.Group(); grp.name = 'edificio_' + k; g.add(grp); parts.forEach(p => box(...p, grp)); B[k] = { grp, ets }; };
  bl('residencial', [[5, 10, 4, C.res, -7, 5, -14], [5, 12, 4, C.res, 0, 6, -17], [5, 9, 4, C.res, 6, 4.5, -12]], v3(-1, 0.5, -4.2));
  bl('universidad', [[8, 6, 6, C.uni, -6, 3, 13], [6, 7, 8, C.uni, 4, 3.5, 15], [4, 4, 4, C.uni, -1, 2, 20]], v3(-1, 0.5, 4.2));
  bl('hospital', [[14, 8, 7, C.hosp, 26, 4, 12], [5, 5, 8, C.hosp, 20.5, 2.5, 18.5], [3, 1.2, 3, C.hosp, 31, 8.6, 12]], v3(22, 0.5, 4.2));
  // Comercial: podio (con la estación de intercambio a la vista en E3) y torre; una segunda torre de contexto
  const com = new THREE.Group(); com.name = 'edificio_comercial'; g.add(com);
  const pod = { roof: box(9, 0.3, 9, C.bldg2, 24, 4.15, -11, com, 'podio_techo'), back: box(9, 4, 0.2, C.bldg2, 24, 2, -15.4, com, 'podio_muro'), east: box(0.2, 4, 9, C.bldg2, 28.4, 2, -11, com, 'podio_muro'),
    front: box(9, 4, 0.2, C.glass, 24, 2, -6.6, com, 'podio_fachada'), west: box(0.2, 4, 9, C.glass, 19.6, 2, -11, com, 'podio_fachada') };
  const towerMat = M(0x7FA9C4, { metalness: 0.3, roughness: 0.4, transparent: true, opacity: 1 });
  const tw = box(6, 20, 6, towerMat, 24.5, 14.3, -11.5, com, 'torre_comercial');
  box(5, 16, 5, C.glass, 32.5, 8, -19, g, 'torre_contexto');
  B.comercial = { grp: com, ets: v3(21.2, 0.5, -7.6) };
  // Contexto: una nave baja de gran superficie y bloques menores (ilustrativos)
  box(16, 3.5, 9, C.low, -26, 1.75, 13, g, 'nave_baja');
  [[4, 6, 4, -34, 3, 22], [4, 5, 4, 7, 2.5, 22], [4, 7, 4, 33, 3.5, 22], [4, 4, 4, 7, 2, -23], [4, 5, 4, -8, 2.5, -23]].forEach(([w, h, d, x, y, z]) => box(w, h, d, C.ctx, x, y, z, g, 'edificio_contexto'));
  // Estaciones de intercambio (cubos verdes) en la base de cada edificio
  const ETS = {}; Object.entries(B).forEach(([k, b]) => { ETS[k] = box(1.1, 1.0, 1.1, C.ets, b.ets.x, 0.5, b.ets.z, g, 'estacion_intercambio_' + k); });

  // ---------- Red enterrada: suministro (azul, y = −0.6) y retorno (rojo, y = −1.0) ----------
  const YS = -0.6, YR = -1.0, ZS = -0.6, ZR = 0.6;
  tube([v3(-25.6, YS, -5.2), v3(-25.6, YS, ZS), v3(30, YS, ZS)], 0.24, C.sup);
  tube([v3(-24.4, YR, -5.0), v3(-24.4, YR, ZR), v3(30, YR, ZR)], 0.24, C.ret);
  const loops = [];
  for (const [k, b] of Object.entries(B)) {
    const e = b.ets, xs = e.x - 0.25, xr = e.x + 0.25;
    const sup = [v3(-25.6, 1.4, -12.1), v3(-25.6, 1.4, -5.2), v3(-25.6, YS, -5.2), v3(-25.6, YS, ZS), v3(xs, YS, ZS), v3(xs, YS, e.z), v3(xs, 0.3, e.z)];
    const ret = [v3(xr, 0.3, e.z), v3(xr, YR, e.z), v3(xr, YR, ZR), v3(-24.4, YR, ZR), v3(-24.4, YR, -5.0), v3(-24.4, 1.9, -5.0), v3(-24.4, 1.9, -11.6)];
    tube(sup.slice(4), 0.17, C.sup); tube(ret.slice(0, 3), 0.17, C.ret);
    const ps = poly(sup), pr = poly(ret); loops.push({ k, ps, pr, f: ps.L / (ps.L + pr.L) });
  }
  // Partículas de agua: azul al salir; rojo después de la estación de intercambio (ilustrativo, sin temperaturas)
  const NP = 34, pg = new THREE.InstancedMesh(new THREE.SphereGeometry(0.3, 8, 6), new THREE.MeshBasicMaterial({ color: 0xffffff }), loops.length * NP);
  pg.name = 'particulas_agua'; pg.userData.noShadow = true; g.add(pg);
  const cS = new THREE.Color(0x7FD6FF), cR = new THREE.Color(0xFF7A70), tm = new THREE.Object3D(), pv = v3(0, 0, 0);
  let flowT = 0;
  const stepFlow = dt => { flowT += dt * 0.035;
    loops.forEach((lp, j) => { for (let i = 0; i < NP; i++) { const u = (flowT + i / NP) % 1, onS = u < lp.f;
      if (onS) lp.ps.at(u / lp.f, pv); else lp.pr.at((u - lp.f) / (1 - lp.f), pv);
      tm.position.copy(pv); tm.updateMatrix(); pg.setMatrixAt(j * NP + i, tm.matrix); pg.setColorAt(j * NP + i, onS ? cS : cR); } });
    pg.instanceMatrix.needsUpdate = true; if (pg.instanceColor) pg.instanceColor.needsUpdate = true; };
  stepFlow(0);

  // ---------- E3 · corte del podio comercial: intercambiador de placas, válvulas, medidor y circuito del edificio ----------
  const cut = new THREE.Group(); cut.name = 'corte_estacion'; cut.visible = false; g.add(cut);
  box(2.0, 1.7, 0.18, C.hx, 22.2, 1.05, -9.0, cut, 'bastidor_intercambiador'); box(2.0, 1.7, 0.18, C.hx, 22.2, 1.05, -10.6, cut);
  for (let i = 0; i < 11; i++) box(1.8, 1.5, 0.05, C.hx, 22.2, 1.05, -9.15 - i * 0.13, cut, 'placa');
  tube([v3(21.0, 0.3, -7.6), v3(21.0, 1.5, -7.6), v3(21.0, 1.5, -9.0)], 0.12, C.sup, cut); // del distrito al intercambiador
  tube([v3(21.4, 0.3, -7.6), v3(21.4, 0.7, -7.6), v3(21.4, 0.7, -9.0)], 0.12, C.ret, cut); // del intercambiador al retorno
  const valves = [v3(21.0, 1.5, -8.2), v3(21.4, 0.7, -8.3)].map(p => { const vg = new THREE.Group(); vg.position.copy(p); cut.add(vg); cyl(0.17, 0.32, C.valve, 0, 0, 0, vg, 'valvula_control'); box(0.24, 0.24, 0.24, C.valve, 0, 0.3, 0, vg); return vg; });
  const meter = box(0.55, 0.4, 0.14, C.meter, 20.4, 1.7, -8.0, cut, 'medidor_energia_termica'); box(0.4, 0.2, 0.02, C.screen, 20.4, 1.74, -7.92, cut);
  cyl(0.04, 1.4, C.motor, 20.4, 0.8, -8.05, cut);
  // Circuito del edificio (lado secundario) hasta un fan coil bajo el techo
  tube([v3(23.3, 1.5, -9.8), v3(25.0, 1.5, -9.8), v3(25.0, 3.4, -9.8), v3(25.6, 3.4, -9.8)], 0.1, C.bsup, cut);
  tube([v3(23.3, 0.7, -10.2), v3(26.4, 0.7, -10.2), v3(26.4, 3.4, -10.2), v3(26.0, 3.4, -10.2)], 0.1, C.bret, cut);
  box(2.0, 0.5, 1.2, C.fc, 25.8, 3.55, -10.6, cut, 'fan_coil');
  const airPath = poly([v3(27.6, 1.0, -12.6), v3(26.9, 3.3, -11.0), v3(24.7, 3.3, -11.0), v3(22.6, 1.0, -12.6), v3(25.1, 0.5, -13.6), v3(27.6, 1.0, -12.6)]);
  const NA = 28, air = new THREE.InstancedMesh(new THREE.SphereGeometry(0.11, 8, 6), new THREE.MeshBasicMaterial({ color: 0xffffff }), NA); air.userData.noShadow = true; air.name = 'particulas_aire'; cut.add(air);
  const cWarm = new THREE.Color(0xF2A65A), cCool = new THREE.Color(0x7FD6FF), cTmp = new THREE.Color();
  let airT = 0;
  const stepAir = dt => { airT += dt * 0.09; for (let i = 0; i < NA; i++) { const u = (airT + i / NA) % 1; airPath.at(u, pv); tm.position.copy(pv); tm.updateMatrix(); air.setMatrixAt(i, tm.matrix);
    // antes del fan coil: aire de la sala (cálido); al salir: frío; se calienta poco a poco en la sala
    const w = u < 0.2 ? 1 : u < 0.42 ? 0 : Math.min(1, (u - 0.42) / 0.58); air.setColorAt(i, cTmp.copy(cCool).lerp(cWarm, w)); }
    air.instanceMatrix.needsUpdate = true; if (air.instanceColor) air.instanceColor.needsUpdate = true; };
  stepAir(0);

  // ---------- E4 · cuatro zonas propuestas (aros sobre el terreno; no es un mapa real) ----------
  const ZONES = [['bancaria', 25, -13], ['salud', 25.5, 13], ['tocumen', -26, 13], ['saber', -1, 14]].map(([k, x, z]) => {
    const m = new THREE.Mesh(new THREE.RingGeometry(9.2, 9.8, 64), C.zone.clone()); m.rotation.x = -Math.PI / 2; m.position.set(x, 0.12, z); m.name = 'zona_' + k; m.visible = false; g.add(m);
    const f = new THREE.Mesh(new THREE.CircleGeometry(9.2, 64), new THREE.MeshBasicMaterial({ color: 0xE3A857, transparent: true, opacity: 0, depthWrite: false })); f.rotation.x = -Math.PI / 2; f.position.set(x, 0.1, z); f.visible = false; g.add(f);
    return { m, f };
  });

  // ---------- Etiquetas ----------
  const il = '<span class="st il">Ilustrativo</span>', pr = '<span class="st pr">Propuesta · M8</span>';
  const L = {
    chillers: label(v3(-25, 3.6, -13), `${il}Chillers`, { prio: true }), torres: label(v3(-29, 6.2, -21), 'Torres de enfriamiento'), bombas: label(v3(-28.5, 1.1, -7.2), 'Bombas de circulación', { down: true }),
    tanque: label(v3(-34, 9.4, -10.5), 'Tanque de almacenamiento térmico'), control: label(v3(-20.6, 3.0, -6.6), 'Sala de control'),
    scada: label(v3(-20.6, 3.0, -6.6), `${il}Sala de control · SCADA`, { prio: true }),
    plantaN: label(v3(-25, 6.5, -10.5), 'Planta central', { cls: 'amber' }),
    comN: label(v3(24.5, 24.6, -11.5), 'Comercial'), hospN: label(v3(26, 8.4, 12), 'Hospital', { down: true }), uniN: label(v3(-1, 7.4, 15), 'Universidad', { down: true }), resN: label(v3(0, 12.4, -17), 'Residencial'),
    sum: label(v3(4, YS, ZS), 'Suministro: agua fría', { cls: 'cyan' }), ret: label(v3(-6, YR, ZR), 'Retorno: agua más caliente', { cls: 'red', down: true }),
    red: label(v3(-14, -0.8, 0), `${il}Red enterrada de tuberías aisladas`, { down: true }),
    etsG: label(v3(22, 1.1, 4.2), 'Estación de intercambio', { cls: 'green' }),
    hx: label(v3(22.2, 1.9, -9.9), 'Intercambiador de placas', { prio: true }), valv: label(v3(21.2, 0.7, -8.3), 'Válvulas de control', { down: true }),
    med: label(v3(20.4, 2.0, -8.0), 'Medidor de energía térmica', { down: true }), circ: label(v3(26.4, 2.2, -10.2), 'Circuito del edificio', { cls: 'cyan', down: true }),
    aire: label(v3(25.8, 3.9, -10.9), `${il}El aire interior se enfría`), dist: label(v3(21.2, 0.3, -7.6), 'Del distrito: suministro y retorno', { down: true }),
    zBan: label(v3(25, 1.2, -4.0), `${pr}Área Bancaria<small>alta densidad de torres comerciales</small>`, { down: true }),
    zSal: label(v3(25.5, 1.2, 22.0), `${pr}Ciudad de la Salud<small>refrigeración continua</small>`, { down: true }),
    zToc: label(v3(-26, 4.2, 13), `${pr}Tocumen<small>gran superficie climatizada</small>`),
    zSab: label(v3(-1, 1.2, 23.0), `${pr}Ciudad del Saber<small>proyecto piloto educativo</small>`, { down: true }),
  };
  const CAM = {
    E1: [-13, 19, 5, -25.5, 2.2, -12], E2: [14, 57, 57, 5, -1, 0], E3: [17.6, 10.5, -1.0, 23.8, 1.5, -10.6], E4: [12, 64, 57, 3, 0, 3],
    fund: [16, 59, 63, 6, 0, 0], dubai: [16, 59, 63, 6, 0, 0],
  };
  Object.assign(CAM, { planta: CAM.E1, red: CAM.E2, control: [-12, 9.5, 4, -22, 1.8, -8.5], panama: CAM.E4 });
  const LBL = {
    E1: [L.chillers, L.torres, L.bombas, L.tanque, L.control], E2: [L.sum, L.ret, L.red, L.comN, L.hospN, L.uniN, L.resN, L.plantaN], E3: [L.hx, L.valv, L.med, L.circ, L.aire], E4: [L.zBan, L.zSal, L.zToc, L.zSab],
    fund: [L.plantaN, L.comN, L.hospN, L.uniN, L.resN], dubai: [], control: [L.scada, L.bombas],
  };
  Object.assign(LBL, { planta: LBL.E1, red: LBL.E2, panama: LBL.E4 });
  const BASE = { planta: 'E1', red: 'E2', panama: 'E4', control: 'E1' };

  function enter(st) {
    const id = BASE[st.id] || st.id;
    cut.visible = id === 'E3'; pod.front.visible = pod.west.visible = pod.roof.visible = ETS.comercial.visible = id !== 'E3'; // corte: sin fachadas ni techo del podio
    towerMat.opacity = id === 'E3' ? 0.12 : 1; towerMat.depthWrite = id !== 'E3';
    ZONES.forEach(z => { z.m.visible = z.f.visible = id === 'E4'; z.m.material.opacity = z.f.material.opacity = 0; });
  }
  function tick(dt, t, st) {
    const id = BASE[st.id] || st.id;
    fans.forEach(f => f.rotation.y += dt * 4); pumps.forEach(p => p.rotation.x += dt * 9);
    stepFlow(dt); if (id === 'E3') stepAir(dt);
    if (id === 'E4') ZONES.forEach((z, k) => { const a = Math.max(0, Math.min(1, (t - 1 - k * 1.4) / 0.8)); z.m.material.opacity = 0.9 * a; z.f.material.opacity = 0.12 * a; }); // aparecen una a una y se quedan
  }
  const steps = [...SC8.map(s => ({ ...s, cam: CAM[s.id], labels: LBL[s.id] || [] })), ...M8.steps.map(s => ({ ...s, level: 'PR', cam: CAM[s.id], labels: LBL[s.id] || [] }))];
  // Miniatura para el inicio: la misma ciudad con su red, sin el corte del podio ni las zonas
  function mini() {
    const m = g.clone(true), drop = [];
    m.traverse(o => { if (/^(corte_estacion|zona_\w+|subsuelo)$/.test(o.name) || (o.isMesh && o.geometry.type === 'CircleGeometry')) drop.push(o); });
    drop.forEach(o => o.parent.remove(o)); m.visible = true;
    m.traverse(o => { if (o.isInstancedMesh && o.name === 'particulas_agua') { o.instanceMatrix = pg.instanceMatrix; o.instanceColor = pg.instanceColor; } });
    return { group: m };
  }
  const probe = () => ({ zones: ZONES.filter(z => z.m.visible && z.m.material.opacity > 0.5).length }); // para la prueba de humo
  return { group: g, ...M8.stop, note: M8.note, refs: M8.refs, steps, enter, tick, mini, probe, air: dt => stepFlow(dt) };
}
