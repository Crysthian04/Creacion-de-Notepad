// Parada 2 · M14: planta REFRESH S.A. (dimensiones del PDF, p. 22; ubicación aproximada al plano general, p. 21),
// VRF de los Edificios D y E, niveles de la Figura 3, LOD, coordinación BIM (tramo genérico) y capas del gemelo digital.
// Técnica de volúmenes con aristas adaptada de plano3d.js (simulador de REFRESH) a three.js r184.
// Plano (x hacia el este, y hacia el sur, origen en la esquina noroeste) → 3D (x − 50, altura, y − 50).
import { M14, LOD, PTS } from 'app/content-m14.js';

export function buildM14({ THREE, label, go }) {
  const g = new THREE.Group(); g.name = 'parada_2_m14';
  const M = (c, o = {}) => new THREE.MeshStandardMaterial({ color: c, roughness: 0.8, metalness: 0.05, ...o });
  const glass = (c, op) => new THREE.MeshStandardMaterial({ color: c, transparent: true, opacity: op, depthWrite: false, roughness: 0.9 });
  const edgeMat = new THREE.LineBasicMaterial({ color: 0x1C1F22, transparent: true, opacity: 0.55 });
  const v3 = (x, y, z) => new THREE.Vector3(x, y, z);
  const P = (x, y, h = 0) => v3(x - 50, h, y - 50); // plano → 3D
  // Volumen sobre un rectángulo del plano (x, y = esquina noroeste; w = este-oeste; d = norte-sur)
  function vol(x, y, w, d, h, mat, name, parent = g, y0 = 0) {
    const m = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), mat); m.position.copy(P(x + w / 2, y + d / 2, y0 + h / 2)); m.name = name; parent.add(m);
    const e = new THREE.LineSegments(new THREE.EdgesGeometry(m.geometry), edgeMat); e.position.copy(m.position); parent.add(e);
    return m;
  }
  const C = { ground: M(0x56624F), vial: M(0x5A6168), expan: M(0x6B7A60), naveA: M(0xC9CFD4), naveB: M(0xB5BCC2), edC: M(0x9AA6B1), shell: glass(0xD5DCE2, 0.16),
    wall: M(0xE6EBEF), room: M(0x3A424A), silo: M(0xB8C2CA, { metalness: 0.3 }), slab: M(0x7D8792), tower: M(0xE3C98A), iu: M(0xF1F4F6), ou: M(0xD9DEE2),
    pipe: M(0x2E6E8E), oa: M(0x5E9A4A), panel: M(0x4A5560), sensor: M(0xF2C14E), node: M(0x23292F), off: M(0xE5534B, { emissive: 0x5a1010 }),
    fac: M(0xD9DEE2, { transparent: true, opacity: 1 }), win: M(0x2B3A46, { transparent: true, opacity: 1 }) }; // fachadas de D y E (ilustrativas): se desvanecen en la zona de estudio

  // ---------- Planta (dimensiones: PDF p. 22; posiciones aproximadas al plano, p. 21) ----------
  const site = new THREE.Group(); site.name = 'planta_refresh'; g.add(site);
  vol(0, 0, 100, 100, 0.2, C.vial, 'terreno_100x100', site, -0.2);
  vol(7, 7, 86, 86, 0.06, C.ground, 'interior', site, 0);
  vol(77, 8, 16, 84, 0.08, C.expan, 'area_expansion', site, 0);
  const naveA = vol(32, 23, 40, 20, 12, C.naveA, 'nave_A_40x20', site);
  const torre = vol(46, 26, 12, 14, 22, C.tower, 'zona_torre_22m', site); // huella ~12 × 14 m (PDF p. 13); altura 22 m (p. 22)
  vol(50.5, 43, 3, 7, 4, C.naveB, 'pasarela_3m', site, 4);
  const naveB = vol(37, 50, 30, 18, 9, C.naveB, 'nave_B_30x18', site);
  const edC = vol(9, 41, 12, 24, 6, C.edC, 'edificio_C_24x12', site), edCGlass = glass(0x9AA6B1, 0.3);
  vol(34, 8, 15, 6, 0.3, C.slab, 'zona_descarga_15x6', site);
  vol(54, 8, 15, 10, 0.3, C.slab, 'patio_silos_15x10', site);
  const siloG = new THREE.CylinderGeometry(1.25, 1.25, 12, 20);
  const silos = new THREE.InstancedMesh(siloG, C.silo, 4); silos.name = 'silos_d2.5'; site.add(silos);
  const tm = new THREE.Object3D(); for (let i = 0; i < 4; i++) { tm.position.copy(P(56 + i * 3.6, 13, 6.3)); tm.updateMatrix(); silos.setMatrixAt(i, tm.matrix); }
  vol(31, 74, 22, 12, 0.08, C.slab, 'estacionamientos', site);
  vol(39, 69, 26, 5, 0.6, C.slab, 'bahias_despacho', site);
  // Edificios D y E en corte: muros bajos y salas (orden del plano, p. 21; tamaños ilustrativos)
  const DE = new THREE.Group(); DE.name = 'edificios_D_E'; site.add(DE);
  vol(9, 11, 12, 25, 4.5, C.fac, 'edificio_D_25x12', DE);
  vol(9, 76, 20, 10, 4.5, C.fac, 'edificio_E_20x10', DE);
  [[20.98, 12, 0.08, 23], [8.94, 12, 0.08, 23], [10, 75.94, 18, 0.08], [10, 85.98, 18, 0.08]].forEach(([x0, y0, w, d]) => vol(x0, y0, w, d, 1.0, C.win, 'ventanas', DE, 2.0));
  const rooms = {}; let y = 11;
  [['labQC', 'Laboratorio QC', 6], ['comedor', 'Comedor', 5], ['banosH', 'Baños/lockers H', 3], ['banosM', 'Baños/lockers M', 3], ['taller', 'Taller', 8]].forEach(([k, n, d]) => {
    vol(9.15, y + 0.1, 11.7, d - 0.2, 0.1, C.room, 'sala_' + k, DE, 0.02); vol(9, y + d - 0.1, 12, 0.2, 2.4, C.wall, 'muro', DE); rooms[k] = { n, c: P(15, y + d / 2) }; y += d;
  });
  let x = 9;
  [['recepcion', 'Recepción', 6], ['oficinas', 'Oficinas', 8], ['juntas', 'Sala de juntas', 6]].forEach(([k, n, w]) => {
    vol(x + 0.1, 76.15, w - 0.2, 9.7, 0.1, C.room, 'sala_' + k, DE, 0.02); if (x > 9) vol(x - 0.1, 76, 0.2, 10, 2.4, C.wall, 'muro', DE); rooms[k] = { n, c: P(x + w / 2, 81) }; x += w;
  });
  const roomLbl = Object.values(rooms).map(r => label(r.c.clone().setY(0.4), r.n, { cls: 'floor', down: true }));

  // ---------- VRF (ubicación ilustrativa) ----------
  const vrf = new THREE.Group(); vrf.name = 'vrf_D_E'; g.add(vrf);
  const IU = ['labQC', 'comedor', 'recepcion', 'oficinas', 'juntas'].map(k => { const m = new THREE.Mesh(new THREE.BoxGeometry(1.4, 0.35, 1.4), C.iu); m.position.copy(rooms[k].c).setY(3.6); m.name = 'unidad_interior_' + k; vrf.add(m); return m; });
  const OU = P(25, 55.5), OA = P(25, 61);
  const pipePts = [[OU.clone().setY(1.2), P(23, 55.5, 3.4), P(23, 14, 3.4), P(21, 14, 3.4), rooms.labQC.c.clone().setY(3.4)], [P(23, 19.5, 3.4), P(21, 19.5, 3.4), rooms.comedor.c.clone().setY(3.4)],
    [P(23, 55.5, 3.4), P(23, 74, 3.4), P(12, 74, 3.4), P(12, 76, 3.4), rooms.recepcion.c.clone().setY(3.4)], [P(19, 74, 3.4), rooms.oficinas.c.clone().setY(3.4)], [P(26, 74, 3.4), rooms.juntas.c.clone().setY(3.4)]];
  const tube = (pts, r, mat, name, parent) => { const grp = new THREE.Group(); grp.name = name; for (let i = 1; i < pts.length; i++) { const a = pts[i - 1], b = pts[i], L = a.distanceTo(b), m = new THREE.Mesh(new THREE.CylinderGeometry(r, r, L, 8), mat); m.position.copy(a).add(b).multiplyScalar(0.5); m.quaternion.setFromUnitVectors(v3(0, 1, 0), b.clone().sub(a).normalize()); grp.add(m); } parent.add(grp); return grp; };
  const pipeMat = C.pipe.clone(); const pipes = pipePts.map((p, i) => tube(p, 0.18, pipeMat, 'tuberia_refrigerante_' + i, vrf));
  const oaMat = C.oa.clone(); tube([OA.clone().setY(1.6), P(22, 61, 2.8), P(22, 22, 2.8), P(21, 22, 2.8)], 0.32, oaMat, 'ducto_aire_exterior_D', vrf); tube([P(22, 61, 2.8), P(22, 78, 2.8), P(20, 78, 2.8)], 0.32, oaMat, 'ducto_aire_exterior_E', vrf);
  const oaUnit = vol(24, 60, 2.4, 2, 1.8, M(0x7FA36E), 'unidad_aire_exterior', vrf);
  // Paneles de distribución PD-D y PD-E (unifilar, PDF p. 25); ubicación dentro de D y E ilustrativa
  const tabD = vol(19.4, 11.25, 1.2, 0.4, 1.8, C.panel, 'panel_PD-D', vrf, 0.3), tabE = vol(9.25, 77, 0.4, 1.2, 1.8, C.panel, 'panel_PD-E', vrf, 0.3);
  const cableMat = new THREE.LineDashedMaterial({ color: 0xE3A857, dashSize: 0.9, gapSize: 0.6 });
  [[P(15, 61, 0.3), P(22.5, 61, 0.3), P(22.5, 11.9, 0.3), P(20, 11.9, 0.3)], [P(22.5, 61, 0.3), P(22.5, 74, 0.3), P(9.9, 74, 0.3), P(9.9, 77.6, 0.3)]].forEach(pts => {
    const l = new THREE.Line(new THREE.BufferGeometry().setFromPoints(pts), cableMat); l.computeLineDistances(); l.name = 'cable_ilustrativo'; vrf.add(l); });
  const sensC = new THREE.Mesh(new THREE.SphereGeometry(0.45, 12, 8), C.sensor); sensC.position.copy(P(15, 61, 3)); sensC.name = 'sensor_temp_sala_electrica'; vrf.add(sensC);
  // Unidad exterior en sus niveles de desarrollo (escena 2.2): un grupo por LOD
  const lodG = new THREE.Group(); lodG.name = 'unidad_exterior_LOD'; lodG.position.copy(OU); g.add(lodG);
  const LV = {};
  const reserve = glass(0x29A9E0, 0.28), generic = M(0xBFC7CD), access = glass(0x4FAE5B, 0.16), support = M(0x5A6168);
  const unitDetail = grp => { const b = new THREE.Mesh(new THREE.BoxGeometry(2.6, 1.9, 1.1), C.ou); b.position.y = 0.95; grp.add(b); [-0.6, 0.6].forEach(dx => { const f = new THREE.Mesh(new THREE.CylinderGeometry(0.45, 0.45, 0.06, 20), M(0x3A424A)); f.rotation.x = Math.PI / 2; f.position.set(dx, 1.05, 0.56); grp.add(f); }); };
  const pipeRun = (grp, sup, branch) => { const p = new THREE.Mesh(new THREE.BoxGeometry(0.22, 0.22, 7), C.pipe); p.position.set(-1.6, 2.6, -3.0); grp.add(p); if (sup) for (let i = 0; i < 4; i++) { const s = new THREE.Mesh(new THREE.BoxGeometry(0.08, 2.6, 0.08), support); s.position.set(-1.6, 1.3, -0.4 - i * 1.8); grp.add(s); } if (branch) { const b = new THREE.Mesh(new THREE.BoxGeometry(1.6, 0.18, 0.18), C.pipe); b.position.set(-2.4, 2.6, -3.3); grp.add(b); const j = new THREE.Mesh(new THREE.SphereGeometry(0.22, 12, 8), M(0xE3A857)); j.position.set(-1.6, 2.6, -3.3); grp.add(j); } }; // LOD 400: la derivación es lo que cambia respecto del 350
  LOD.forEach(l => { const grp = new THREE.Group(); grp.name = 'LOD_' + l.n; grp.visible = false; lodG.add(grp); LV[l.n] = grp; });
  { const r = new THREE.Mesh(new THREE.BoxGeometry(3.2, 2.4, 1.8), reserve); r.position.y = 1.2; LV['100'].add(r); } // algo mayor que la unidad (2.6 × 1.9 × 1.1)
  { const r = new THREE.Mesh(new THREE.BoxGeometry(2.6, 1.9, 1.1), generic); r.position.y = 0.95; LV['200'].add(r); }
  ['300', '350', '400', '500'].forEach(n => { unitDetail(LV[n]); const a = new THREE.Mesh(new THREE.BoxGeometry(3.6, 2.2, 1.0), access); a.position.set(0, 1.1, 1.1); LV[n].add(a); });
  pipeRun(LV['350'], true, false); pipeRun(LV['400'], true, true); pipeRun(LV['500'], true, true);
  const showLOD = n => Object.entries(LV).forEach(([k, gg]) => gg.visible = k === n);

  // ---------- Figura 3: niveles 2–4 como esquema flotante sobre el área de expansión (no es una ubicación física) ----------
  const lv = new THREE.Group(); lv.name = 'niveles_figura_3'; g.add(lv);
  const plate = (h, name) => { const m = new THREE.Mesh(new THREE.BoxGeometry(18, 0.2, 40), glass(0x29A9E0, 0.08)); m.position.copy(P(85, 50, h)); m.name = name; lv.add(m); return m; };
  plate(9, 'nivel_2_automatizacion'); plate(14, 'nivel_3_supervision'); plate(19, 'nivel_4_informacion');
  const node = (px, py, h, name) => { const m = new THREE.Mesh(new THREE.BoxGeometry(4.5, 1.6, 3), C.node.clone()); m.position.copy(P(px, py, h + 0.9)); m.name = name; lv.add(m); return m; };
  const N = { ctrl: node(85, 42, 9, 'controlador_central_VRF'), gw: node(85, 58, 9, 'pasarela_BACnet_IP'), scada: node(85, 50, 14, 'SCADA_central'),
    bim: node(85, 34, 19, 'modelo_BIM_as_built'), cmms: node(85, 50, 19, 'CMMS'), tab: node(85, 66, 19, 'tablero_gemelo_digital') };
  const dash = new THREE.LineDashedMaterial({ color: 0x7FD6FF, dashSize: 1, gapSize: 0.7, transparent: true, opacity: 0.7 });
  const line = pts => { const l = new THREE.Line(new THREE.BufferGeometry().setFromPoints(pts), dash); l.computeLineDistances(); lv.add(l); return l; };
  const c = o => o.position.clone();
  line([c(IU[3]), c(N.ctrl)]); line([c(IU[0]), c(N.ctrl)]); line([OU.clone().setY(2), c(N.ctrl)]); line([c(N.ctrl), c(N.gw)]); line([c(N.gw), c(N.scada)]);
  line([c(N.scada), c(N.bim)]); line([c(N.scada), c(N.cmms)]); line([c(N.scada), c(N.tab)]); line([c(tabE), c(N.scada)]); line([c(sensC), c(N.scada)]);
  line([c(N.bim), c(N.cmms)]); line([c(N.cmms), c(N.tab)]);
  const pulse = new THREE.Mesh(new THREE.SphereGeometry(0.7, 14, 10), new THREE.MeshBasicMaterial({ color: 0xF2C14E })); pulse.visible = false; g.add(pulse);

  // ---------- 2.4 · cinco capas del marco de Hu et al. (2026) ----------
  const twin = new THREE.Group(); twin.name = 'capas_gemelo_digital'; twin.visible = false; g.add(twin);
  const LAY = ['Recolección de datos', 'Procesamiento', 'Modelos inteligentes', 'Plataforma de visualización', 'Soporte en la nube'];
  const layCol = [0x29A9E0, 0x4FAE5B, 0xE3A857, 0xB07FD6, 0x7FD6FF];
  const layers = LAY.map((n, i) => { const m = new THREE.Mesh(new THREE.BoxGeometry(46, 0.3, 46), glass(layCol[i], 0.18)); m.position.copy(P(45, 48, 28 + i * 7)); m.name = 'capa_' + (i + 1); twin.add(m); return m; });
  const rise = new THREE.InstancedMesh(new THREE.SphereGeometry(0.35, 8, 6), new THREE.MeshBasicMaterial({ color: 0x7FD6FF }), 30); rise.name = 'datos'; twin.add(rise);

  // ---------- 2.1 · coordinación BIM en un tramo de cielo raso genérico (fuera de la planta) ----------
  const co = new THREE.Group(); co.name = 'coordinacion_generica'; co.position.set(-110, 0, 0); co.visible = false; g.add(co);
  const cbox = (w, h, d, mat, px, py, pz, name) => { const m = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), mat); m.position.set(px, py, pz); m.name = name; co.add(m); return m; };
  cbox(14, 0.25, 8, glass(0x9AA6B1, 0.12), 0, 4.2, 0, 'losa');
  const beam = cbox(14, 0.7, 0.4, M(0x9AA6B1), 0, 3.7, 0, 'viga_estructura');
  const duct = cbox(1.6, 0.8, 8, M(0x29A9E0), -1.5, 3.0, 0, 'ducto_HVAC');
  const tray = cbox(0.8, 0.15, 8, M(0xE3A857), 2.0, 3.45, 0, 'bandeja_electrica');
  const pipeP = new THREE.Mesh(new THREE.CylinderGeometry(0.15, 0.15, 14, 12), M(0x4FAE5B)); pipeP.rotation.z = Math.PI / 2; pipeP.position.set(0, 3.1, 2.5); pipeP.name = 'tuberia_plomeria'; co.add(pipeP);
  cbox(14, 0.08, 8, glass(0xE6EBEF, 0.06), 0, 2.2, 0, 'cielo_raso');
  const clashMat = new THREE.MeshBasicMaterial({ color: 0xE5534B, transparent: true, opacity: 0.8 });
  const clashes = [v3(-1.5, 3.1, 2.5), v3(2.0, 3.45, -0.0)].map(p => { const s = new THREE.Mesh(new THREE.SphereGeometry(0.55, 14, 10), clashMat); s.position.copy(p); co.add(s); return s; });

  // ---------- 2.6 · tres planos independientes que se juntan en el modelo ----------
  const sheets = new THREE.Group(); sheets.visible = false; g.add(sheets);
  const sheetMat = c => new THREE.MeshBasicMaterial({ color: c, transparent: true, opacity: 0.55, side: THREE.DoubleSide, depthWrite: false });
  const SH = [0xE6EBEF, 0xBFE7F8, 0xF1E3C0].map((col, i) => { const m = new THREE.Mesh(new THREE.PlaneGeometry(26, 18), sheetMat(col)); m.name = ['plano_isometrico', 'plano_PID', 'plano_unifilar'][i]; m.userData.a = P(5 + i * 32, 30, 34); sheets.add(m); return m; });

  // ---------- Etiquetas ----------
  // Tablero: dato de fuente; medidor: propuesta del informe (dos sellos)
  const MED = e => `<span class="st df">Dato de fuente</span>Panel PD-${e} · tablero de ${e}<small>(Batista et al., 2026, p. 25)</small><span class="st pr" style="margin-top:5px">Propuesta · M14 · Figura 3</span>medidor de energía propuesto`;
  const df = c => `<span class="st df">Dato de fuente</span>`, il = '<span class="st il">Ilustrativo</span>', B = '<small>(Batista et al., 2026, p. 22)</small>';
  const L = {
    naveA: label(P(36, 33, 12.5), `${df()}Nave A · Proceso<small>40 × 20 m · zona de la torre: 22 m</small>${B}`), torre: label(P(52, 26, 15), `${df()}Zona de la torre · 22 m${B}`, { cls: 'amber' }),
    naveB: label(P(52, 59, 9.5), `${df()}Nave B · Envasado<small>30 × 18 m</small>${B}`), edC: label(P(15, 45, 6.5), `${df()}Edificio C · Servicios<small>24 × 12 m</small>${B}`),
    edD: label(P(15, 11, 5), `${df()}Edificio D · Operativo<small>25 × 12 m</small>${B}`), edE: label(P(19, 86, 5), `${df()}Edificio E · Corporativo<small>20 × 10 m</small>${B}`, { down: true }),
    terreno: label(P(85, 92, 0.5), `${df()}Terreno 100 × 100 m (10,000 m²)${B}`, { down: true }),
    expan: label(P(85, 20, 0.5), `${df()}Área de expansión futura<small>3,000 m² (30 %)</small>${B}`),
    silos: label(P(61, 13, 12.5), `${df()}Patio de silos · 4 silos Ø 2.50 m${B}`),
    salas: label(P(15, 23, 5), `${df()}Orden de las salas: plano general<small>(Batista et al., 2026, p. 21) · tamaños ilustrativos</small>`, { cls: 'green' }),
    ou: label(OU.clone().setY(2.6), `${il}Unidad exterior VRF`), oa: label(OA.clone().setY(2.4), `${il}Unidad de aire exterior`, { down: true }),
    medD: label(c(tabD).setY(2.6), MED('D'), { cls: 'amber' }),
    medE: label(c(tabE).setY(2.6), MED('E'), { cls: 'amber' }),
    salaElec: label(c(sensC).setY(3.7), `${df()}Sala eléctrica / UPS<small>(Batista et al., 2026, p. 22)</small>`),
    n2: label(P(94, 30, 9.5), 'Nivel 2 · Automatización del VRF', { cls: 'cyan' }), n3: label(P(94, 30, 14.5), 'Nivel 3 · Supervisión', { cls: 'cyan' }), n4: label(P(94, 30, 19.5), 'Nivel 4 · Gestión de la información', { cls: 'cyan' }),
    ctrl: label(c(N.ctrl).setY(11), 'Nivel 2 · Controlador central VRF'), gw: label(c(N.gw).setY(11), 'Nivel 2 · Pasarela BACnet/IP'), scada: label(c(N.scada).setY(16), 'Nivel 3 · SCADA central de REFRESH'),
    bim: label(c(N.bim).setY(21), 'Nivel 4 · Modelo BIM as-built (LOD 500) + COBie'), cmms: label(c(N.cmms).setY(21), 'Nivel 4 · CMMS · órdenes de trabajo'), tab: label(c(N.tab).setY(21), 'Nivel 4 · Tablero / gemelo digital'),
    esquema: label(P(85, 74, 9), `${il}Esquema de la Figura 3<small>no es una ubicación física</small>`, { down: true }),
    flujo: label(P(60, 50, 30), '', { cls: 'amber' }),
    gwConf: label(c(N.gw).setY(7.6), '<span class="st df">Dato de fuente</span>Integración con el SCADA: por confirmar<small>(Batista et al., 2026, p. 13)</small>', { cls: 'red', down: true }),
    lod: label(OU.clone().setY(4.2), '', { cls: 'amber' }),
    nD: label(P(15, 33, 4.8), `${df()}Edificio D<small>(Batista et al., 2026, p. 21)</small>`), nC: label(P(15, 52, 6.3), `${df()}Edificio C<small>(Batista et al., 2026, p. 21)</small>`),
    nE: label(P(16, 78, 4.8), `${df()}Edificio E<small>(Batista et al., 2026, p. 21)</small>`),
    twinRot: label(P(45, 25, 64), '<span class="st df">Dato de fuente</span>Marco general (Hu et al., 2026); en REFRESH es una propuesta', { cls: 'amber' }),
    coSt: label(v3(-110, 6, 0), '', { cls: 'amber' }),
    coD: label(v3(-111.5, 2.4, -3.5), 'HVAC · lidera la coordinación', { down: true }), coB: label(v3(-104, 4.4, 0), 'Estructura'), coT: label(v3(-108, 3.8, -3.6), 'Eléctrico'), coP: label(v3(-115, 3.3, 2.5), 'Plomería', { down: true }),
    sheet: label(P(15, 48, 16), '', { cls: 'amber' }),
    fach: label(P(15, 36.5, 4.6), '<span class="st il">Ilustrativo</span>REFRESH no define fachadas', { down: true }),
    cable: label(P(22.5, 40, 0.4), '<span class="st il">Ilustrativo</span>Recorrido del cable de alimentación', { down: true }),
    pdD: label(c(tabD).setY(2.4), MED('D'), { cls: 'amber' }), pdE: label(c(tabE).setY(2.4), MED('E'), { cls: 'amber' }), fuga: label(P(23, 40, 4.5), `${il}Fugas: difíciles de localizar en toda la red`, { cls: 'red' }),
  };
  LAY.forEach((n, i) => { L['lay' + i] = label(P(22, 25, 28.5 + i * 7), n, { cls: 'cyan' }); });
  // Puntos M/C (clic → inspector)
  const iP = () => M14.steps.findIndex(s => s.id === 'inspector');
  const pt = (k, pos, extra = '') => label(pos, `${k}${extra}`, { cls: 'pt ' + (k[0] === 'M' ? 'cyan' : 'amber'), onClick: () => { selPt = k; go(2, iP()); } });
  const PL = {
    M3: pt('M3', c(IU[3]).setY(4.4), ' · aviso de filtro'), iuE: pt('M1', c(IU[2]).setY(4.4), ' M2 M3 C1 C2 · en cada unidad interior'), iuD: pt('M1', c(IU[0]).setY(4.4), ' M2 M3 C1 C2 · en cada unidad interior'),
    ou: pt('M4', OU.clone().setY(1.2).add(v3(1.6, 0, 0)), ' M2 · unidad exterior'), M5: pt('M5', c(tabE).setY(1.2).add(v3(1.2, 0, 0)), ' · energía medida'), M6: pt('M6', c(sensC).setY(2.2), ' · temperatura'),
    C3: pt('C3', c(N.scada).setY(13).add(v3(4.5, 0, 0)), ' · paro forzado'), C4: pt('C4', OA.clone().setY(0.8).add(v3(1.8, 0, 0)), ' · marcha y paro'),
  };
  let selPt = 'M3';

  // ---------- Cámaras y etiquetas por paso ----------
  const W0 = [-104, 116, 124, -12, 7, -8]; // vista de conjunto desde el suroeste; la planta queda a la derecha de las tarjetas
  const CAM = {
    planta: W0, coord: [-124, 8.5, 13, -110, 3, 0], lod: [OU.x + 8, 4.8, OU.z + 6.5, OU.x - 0.8, 1.3, OU.z - 2.2], ventajas: W0,
    gemelo: [-80, 92, 128, 2, 22, 0], mep: [-108, 100, 124, 0, 15, 4], propuesta: [-2, 52, 62, -34, 0, 0], cierre: W0, zona: [-2, 52, 62, -34, 0, 0],
    inspector: [-108, 100, 124, 0, 15, 4], integracion: [2, 30, 52, 35, 13, 6], limites: [-80, 92, 128, 2, 22, 0], mantto: [-52, 34, 58, -33, 2, 8],
    riesgos: [-56, 46, 66, -26, 2, 10], panama: W0, recom: [-62, 78, 96, 12, 8, 4],
  };

  const base = [L.naveA, L.naveB, L.edC, L.edD, L.edE];
  const mepL = [L.ou, L.medD, L.medE, L.salaElec, L.ctrl, L.gw, L.scada, L.bim, L.cmms, L.tab, L.flujo, PL.M3];
  const mepAll = [...mepL.filter(l => l !== L.flujo), L.oa, L.esquema, PL.iuD, PL.iuE, PL.ou, PL.M5, PL.M6, PL.C3, PL.C4, L.salas];
  const LBL = {
    planta: [...base, L.terreno, L.expan, L.silos, L.fach], zona: [L.fach, L.pdD, L.pdE, L.salaElec, L.cable, L.salas, L.ou], coord: [L.coSt, L.coD, L.coB, L.coT, L.coP], lod: [L.lod], ventajas: base, gemelo: [L.twinRot, ...LAY.map((_, i) => L['lay' + i])],
    mep: mepL, propuesta: [L.sheet, L.ou], cierre: base, inspector: mepAll, integracion: [L.gwConf, L.gw, L.scada, L.ctrl, L.n2, L.n3],
    limites: [L.twinRot, ...LAY.map((_, i) => L['lay' + i])], mantto: [PL.iuD, PL.iuE], riesgos: [L.fuga, L.ou], panama: base, recom: [L.ou, L.n2],
  };
  const MEP_IDS = ['zona', 'mep', 'inspector', 'integracion', 'mantto', 'riesgos', 'recom', 'propuesta'];
  const XRAY = [...MEP_IDS, 'lod']; // pasos de la zona de estudio: fachadas de D y E en rayos X

  // ---------- Animaciones ----------
  let lodSel = '100', lodAuto = true;
  function fillLOD(n) {
    lodSel = n; showLOD(n); const r = LOD.find(l => l.n === n);
    document.querySelectorAll('[data-lodn]').forEach(e => e.textContent = n);
    ['c', 'e', 'u'].forEach(f => { const el = document.querySelector(`[data-lodf="${f}"]`); if (el) el.textContent = r[f]; });
    document.querySelectorAll('[data-lod]').forEach(b => b.classList.toggle('on', b.dataset.lod === n));
    L.lod.set(n === '500' ? '<span class="st df">Dato de fuente</span>LOD 500 · as-built verificado en campo<small>no es un nivel superior al 400 (BIMForum, 2024, p. 13)</small>' : `<span class="st il">Ilustrativo</span>LOD ${n}`);
  }
  function fillPt(k) {
    selPt = k; const p = PTS[k], el = document.getElementById('ptinfo'); if (!el) return;
    el.innerHTML = `<h4>${k} · ${p.t}</h4><p><b>Equipo:</b> ${p.eq}</p><p>${p.d}</p><p class="cite">(${p.cite})</p>`;
    document.querySelectorAll('[data-pt]').forEach(b => b.classList.toggle('on', b.dataset.pt === k));
  }
  const FLOW = [[c(IU[3]), 'M3 · aviso de filtro en la unidad interior (Oficinas, E)'], [c(N.ctrl), 'Controlador central VRF'], [c(N.gw), 'Pasarela BACnet/IP'], [c(N.scada), 'SCADA central de REFRESH'], [c(N.tab), 'Tablero: alerta'], [c(N.cmms), 'CMMS: orden de trabajo']];
  const STOPF = [[c(N.scada), 'C3 · paro forzado desde el SCADA'], [c(N.gw), 'Pasarela BACnet/IP'], [c(N.ctrl), 'Controlador central VRF'], [c(IU[3]), 'Todas las unidades interiores: apagadas']];
  const nodeBase = 0x23292F, hot = 0xE3A857;

  function enter(st) {
    const id = st.id, mepish = MEP_IDS.includes(id);
    site.visible = id !== 'coord'; co.visible = id === 'coord'; twin.visible = id === 'gemelo' || id === 'limites';
    vrf.visible = mepish; lv.visible = ['mep', 'inspector', 'integracion', 'recom'].includes(id); lodG.visible = mepish || id === 'lod';
    sheets.visible = id === 'propuesta'; pulse.visible = false;
    // En 2.2, C y las naves translúcidos para que no tapen la unidad exterior
    edC.material = id === 'lod' ? edCGlass : C.edC; naveA.material = id === 'lod' ? edCGlass : C.naveA; naveB.material = id === 'lod' ? edCGlass : C.naveB; torre.material = id === 'lod' ? edCGlass : C.tower;
    IU.forEach(u => u.material = C.iu); Object.values(N).forEach(n => n.material.color.setHex(nodeBase)); pipeMat.color.setHex(0x2E6E8E); pipeMat.emissive.setHex(0);
    if (id === 'lod') { lodAuto = true; fillLOD('100'); document.querySelectorAll('[data-lod]').forEach(b => b.onclick = () => { lodAuto = false; fillLOD(b.dataset.lod); }); }
    else showLOD(id === 'propuesta' ? '100' : '400');
    if (id === 'ventajas') document.querySelectorAll('.t2 [data-row]').forEach(r => r.style.opacity = 0.15);
    if (id === 'inspector') { document.querySelectorAll('[data-pt]').forEach(b => b.onclick = () => fillPt(b.dataset.pt)); fillPt(selPt); }
    if (id === 'integracion') N.gw.material.color.setHex(0xE5534B);
  }
  // En 2.5, la etiqueta normal del nodo resaltado se oculta para que no salga dos veces
  function dedup(lbl) { [PL.M3, L.ctrl, L.gw, L.scada, L.tab, L.cmms].forEach(l => { const on = l !== lbl; if (l.on !== on) { l.on = on; if (!on) l.el.hidden = true; } }); }
  function along(path, t, seg) { const k = Math.min(path.length - 2, Math.floor(t / seg)), u = Math.min(1, (t - k * seg) / seg); return { k, p: path[k][0].clone().lerp(path[k + 1][0], u), u }; }
  function tick(dt, t, st) {
    const id = st.id;
    { const tgt = XRAY.includes(id) ? 0.1 : 1, a = Math.min(1, dt * 2.2); // fachadas: opacas en la planta, rayos X en la zona de estudio
      C.fac.opacity += (tgt - C.fac.opacity) * a; C.win.opacity += (tgt - C.win.opacity) * a; C.fac.depthWrite = C.win.depthWrite = C.fac.opacity > 0.95; }
    if (id === 'coord') {
      const ph = Math.floor((t % 14) / 2); // 0 estructura, 1 HVAC, 2 eléctrico, 3 plomería, 4 interferencias, 5–6 resuelto
      beam.visible = true; duct.visible = ph >= 1; tray.visible = ph >= 2; pipeP.visible = ph >= 3;
      clashes.forEach(s => { s.visible = ph === 4; s.scale.setScalar(1 + 0.25 * Math.sin(t * 8)); });
      pipeP.position.y = ph >= 5 ? 2.45 : 3.1; tray.position.x = ph >= 5 ? 3.2 : 2.0;
      L.coSt.set(`<span class="st il">Ilustrativo</span>${['① Estructura', '② HVAC: ductos sobre el cielo raso', '③ Eléctrico: bandejas', '④ Plomería', '⑤ Interferencias detectadas', '⑥ Resueltas antes de construir', '⑥ Resueltas antes de construir'][ph]}<small>(Khanzode et al., 2008)</small>`);
    }
    if (id === 'lod' && lodAuto) { const n = LOD[Math.floor(t / 3.5) % LOD.length].n; if (n !== lodSel) fillLOD(n); }
    if (id === 'ventajas') document.querySelectorAll('.t2 [data-row]').forEach(r => { r.style.opacity = t > 0.4 + (+r.dataset.row) * 0.55 ? 1 : 0.15; });
    if (id === 'gemelo' || id === 'limites') {
      layers.forEach((m, i) => m.material.opacity = 0.14 + 0.1 * Math.max(0, Math.sin(t * 2 - i * 0.8)));
      for (let i = 0; i < 30; i++) { const u = ((t * 0.25 + i / 30) % 1); tm.position.copy(P(30 + (i * 37) % 30, 35 + (i * 17) % 28, 4 + u * 32)); tm.updateMatrix(); rise.setMatrixAt(i, tm.matrix); }
      rise.instanceMatrix.needsUpdate = true;
    }
    if (id === 'mep') {
      const T1 = (FLOW.length - 1) * 1.3, T2 = (STOPF.length - 1) * 1.1, cyc = t % (T1 + 1.5 + T2 + 3);
      Object.values(N).forEach(n => n.material.color.setHex(nodeBase)); IU.forEach(u => u.material = C.iu); pulse.visible = true;
      if (cyc < T1 + 1.5) {
        const a = along(FLOW, Math.min(cyc, T1), 1.3); pulse.position.copy(a.p); pulse.material.color.setHex(0xF2C14E);
        const k = cyc >= T1 ? FLOW.length - 1 : (a.u > 0.98 ? a.k + 1 : a.k);
        const nodeAt = [null, N.ctrl, N.gw, N.scada, N.tab, N.cmms][k]; if (nodeAt) nodeAt.material.color.setHex(hot);
        dedup([PL.M3, L.ctrl, L.gw, L.scada, L.tab, L.cmms][k]);
        L.flujo.set(`<span class="st pr">Propuesta · M14 · Figura 3</span>${FLOW[k][1]}<small>(Daikin Comfort Technologies North America, 2019, pp. 25–26)</small>`); L.flujo.anchor.copy(FLOW[k][0]).add(v3(0, 4, 0));
      } else {
        const t2 = cyc - T1 - 1.5, a = along(STOPF, Math.min(t2, T2), 1.1); pulse.position.copy(a.p); pulse.material.color.setHex(0xE5534B);
        const k = t2 >= T2 ? STOPF.length - 1 : a.k; if (k === STOPF.length - 1) IU.forEach(u => u.material = C.off);
        dedup([L.scada, L.gw, L.ctrl, null][k]);
        L.flujo.set(`<span class="st pr">Propuesta · M14 · Figura 3</span>${STOPF[k][1]}<small>(Daikin Comfort Technologies North America, 2019, p. 24)</small>`); L.flujo.anchor.copy(STOPF[k][0]).add(v3(0, 4, 0));
      }
    }
    if (id === 'riesgos') { const on = Math.floor(t * 3) % 2; pipeMat.color.setHex(on ? 0xE3A857 : 0x2E6E8E); pipeMat.emissive.setHex(on ? 0x553300 : 0); }
    if (id === 'propuesta') {
      const u = Math.min(1, Math.max(0, (t % 12 - 1) / 4));
      SH.forEach((m, i) => { m.position.copy(m.userData.a).lerp(P(15, 48, 8), u); m.material.opacity = 0.55 * (1 - Math.max(0, (t % 12 - 5) / 2)); m.rotation.x = -Math.PI / 2 * u * 0.9; m.visible = m.material.opacity > 0.02; });
      const ph = t % 12 < 5 ? 0 : t % 12 < 8 ? 1 : 2; showLOD(['100', '350', '500'][ph]);
      L.sheet.set(`<span class="st pr">Propuesta · M14 · Propuesta de aplicación</span>${['Hoy: vista isométrica 3D, P&amp;ID y unifilar independientes', 'Modelo coordinado de D y E: VRF en LOD 350', 'Modelo as-built de D y E + datos COBie'][ph]}<small>(Batista et al., 2026; BIMForum, 2024)</small>`);
      L.ou.set(`<span class="st pr">Propuesta · M14</span>${['Volumen de reserva (anteproyecto)', 'LOD 350 · coordinación', 'As-built (LOD 500) + COBie'][ph]}`);
    } else if (L.ou.el.querySelector('.box').textContent !== 'IlustrativoUnidad exterior VRF') L.ou.set(`${il}Unidad exterior VRF`);
  }
  // 2.2: recuadro con la planta de D, C y E (plano, p. 21) y la vista de la cámara; la ubicación de la unidad es ilustrativa
  const R2 = (x, y, w, d, t) => `<rect x="${y}" y="${x}" width="${d}" height="${w}" fill="#3A424A" stroke="#C9D1D8" stroke-width=".4"/><text x="${y + d / 2}" y="${x + w / 2 + 1.6}" font-size="5" fill="#F1F4F6" text-anchor="middle">${t}</text>`;
  const INSET = `<span class="st df">Dato de fuente</span>Planta: D, C y E <small>(Batista et al., 2026, p. 21)</small>
<svg viewBox="8 4 84 30">${R2(9, 11, 12, 25, 'D')}${R2(9, 41, 12, 24, 'C')}${R2(9, 76, 20, 10, 'E')}<circle cx="55.5" cy="25" r="1.6" fill="#E3A857"/><path d="M62 33 L55.8 25.6 M62 33 L58.5 33.6 M62 33 L62.2 29.6" stroke="#29A9E0" stroke-width=".7" fill="none"/><text x="10" y="33" font-size="3.6" fill="#9AA6B1">← N</text></svg>
<span class="st il">Ilustrativo</span>ubicación de la unidad exterior (●) y dirección de la vista.`;
  // Miniatura para el inicio: la planta completa con la misma geometría; D y E resaltados con sus fachadas
  function mini() {
    const m = site.clone(true), hi = M(0xF2D49B), win = M(0x2B3A46);
    m.traverse(o => { if (o.isMesh && o.material === C.fac) o.material = hi; else if (o.isMesh && o.material === C.win) o.material = win; });
    m.visible = true; return { group: m };
  }
  const steps = M14.steps.map(s => ({ ...s, cam: CAM[s.id], labels: LBL[s.id] || [], inset: s.id === 'lod' ? INSET : null }));
  return { group: g, ...M14.stop, note: M14.note, refs: M14.refs, steps, enter, tick, mini };
}
