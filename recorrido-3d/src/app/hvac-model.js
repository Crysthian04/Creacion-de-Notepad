import * as THREE from 'three';

export const H = 3.6;
// ilustrativo: total 16 (8 ala izquierda · 8 ala derecha)
const LAYOUT = [[-20, -14, -7.5, 7.5, 14, 20], [-20, -14, -7.5, 10, 17.5], [-17, -7.5, 7.5, 14, 20]];
export const UMA_PER_FLOOR = LAYOUT.map(l => l.length);
const V = (x, y, z) => new THREE.Vector3(x, y, z);
const UP = V(0, 1, 0);
const hT = 3 * H;
const RXS = -10.5, RXR = -10, ZS = -4.3, ZR = -3.85, ZU = -3.2;

function std(name, color, roughness, metalness, emissive = 0x000000, ei = 0) {
  return new THREE.MeshStandardMaterial({ name, color, roughness, metalness, emissive, emissiveIntensity: ei });
}
function box(name, w, h, d, mat, x, y, z) {
  const m = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), mat);
  m.name = name; m.position.set(x, y, z); return m;
}
function seg(name, a, b, r, mat) {
  const dir = b.clone().sub(a), len = dir.length();
  const m = new THREE.Mesh(new THREE.CylinderGeometry(r, r, len, 16, 1, true), mat);
  m.name = name;
  m.position.copy(a).add(b).multiplyScalar(0.5);
  m.quaternion.setFromUnitVectors(UP, dir.normalize());
  return m;
}
function pipe(group, name, pts, r, mat) {
  const jg = new THREE.SphereGeometry(r * 1.02, 16, 10);
  pts.forEach((p, i) => {
    if (i > 0) group.add(seg(`${name}_tramo${i}`, pts[i - 1], p, r, mat));
    const j = new THREE.Mesh(jg, mat); j.name = `${name}_codo${i}`; j.position.copy(p); group.add(j);
  });
}
function edges(name, geo, color, opacity = 1) {
  const l = new THREE.LineSegments(new THREE.EdgesGeometry(geo),
    new THREE.LineBasicMaterial({ name: name + '_mat', color, transparent: opacity < 1, opacity }));
  l.name = name; return l;
}
function fanBlades(name, r, mat, n = 4) {
  const g = new THREE.Group(); g.name = name;
  const hub = new THREE.Mesh(new THREE.CylinderGeometry(r * 0.18, r * 0.18, 0.06, 20), mat);
  hub.name = name + '_cubo'; g.add(hub);
  for (let i = 0; i < n; i++) {
    const b = new THREE.Mesh(new THREE.BoxGeometry(r * 1.7, 0.02, r * 0.32), mat);
    b.name = `${name}_aspa${i}`; b.rotation.y = (i / n) * Math.PI; b.rotation.x = 0.25;
    g.add(b);
  }
  return g;
}
// Techo a cuatro aguas (w a lo largo de x)
function hipGeo(w, d, h) {
  const swap = d > w; if (swap) [w, d] = [d, w];
  const a = w / 2, b = d / 2, r = Math.max(0, a - b);
  const c0 = [-a, 0, -b], c1 = [a, 0, -b], c2 = [a, 0, b], c3 = [-a, 0, b], r0 = [-r, h, 0], r1 = [r, h, 0];
  const tris = [c3, c2, r1, c3, r1, r0, c1, c0, r0, c1, r0, r1, c2, c1, r1, c0, c3, r0];
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(tris.flat(), 3));
  if (swap) g.rotateY(Math.PI / 2);
  g.computeVertexNormals(); return g;
}
function rng(seed) { return () => { seed |= 0; seed = seed + 0x6D2B79F5 | 0; let t = Math.imul(seed ^ seed >>> 15, 1 | seed); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }

export function buildModel() {
  const M = {
    concrete: std('hormigon', 0x4A525A, 0.9, 0),
    uma: std('uma_carcasa', 0xC4CCD3, 0.55, 0.2),
    dark: std('metal_oscuro', 0x262B30, 0.6, 0.3),
    duct: std('ducto', 0x7E8993, 0.5, 0.3),
    chiller: std('chiller_carcasa', 0xD9DFE3, 0.5, 0.2),
    coil: std('serpentin', 0x5F6B75, 0.7, 0.3),
    supply: std('tuberia_suministro', 0x7FD1B9, 0.45, 0.1, 0x7FD1B9, 0.25),
    ret: std('tuberia_retorno', 0xC87533, 0.4, 0.3, 0xC87533, 0.2),
    split: std('minisplit', 0xEEF0EE, 0.4, 0),
    splitAccent: std('minisplit_acento', 0xE3A857, 0.5, 0, 0xE3A857, 0.35),
    refrig: std('linea_refrigerante', 0xA8876A, 0.45, 0.3),
    thermal: new THREE.MeshBasicMaterial({ name: 'punto_termografia', color: 0xFF6A2B }),
    sensor: new THREE.MeshStandardMaterial({ name: 'sensor_iot', color: 0x29A9E0, emissive: 0x29A9E0, emissiveIntensity: 1.2, roughness: 0.3 }),
    platform: new THREE.MeshStandardMaterial({ name: 'plataforma', color: 0x0F2A38, emissive: 0x29A9E0, emissiveIntensity: 0.25, roughness: 0.5, transparent: true, opacity: 0.85 }),
  };
  // Envolvente: materiales que alternan entre fachada (opaco) y rayos X
  const shellMats = [];
  const sh = (name, color, xo, rough = 0.85, metal = 0) => {
    const mat = new THREE.MeshStandardMaterial({ name, color, roughness: rough, metalness: metal, transparent: true, opacity: xo, depthWrite: false, side: THREE.DoubleSide });
    shellMats.push({ mat, xo }); return mat;
  };
  const S = {
    brick: sh('ladrillo', 0xA9533B, 0.13),
    band: sh('franja_clara', 0xE6D8BA, 0.2),
    win: sh('ventanas', 0x3C4E5A, 0.07, 0.2, 0.3),
    tile: sh('teja_roja', 0x8E3B2B, 0.11, 0.8),
    cream: sh('muro_crema', 0xE2CFA6, 0.13),
    ochre: sh('bloque_posterior', 0xD2A85E, 0.1),
    plate: sh('losa_cubierta', 0x8C8478, 0.08),
  };
  const root = new THREE.Group(); root.name = 'Edificio2_Postgrado_HVAC';
  const fans = [], anchors = {}, shellLines = [];
  const LC = 0x7A8691;

  // ---------- Edificio ----------
  const bld = new THREE.Group(); bld.name = 'edificio'; root.add(bld);
  const outline = (name, geo, x, y, z) => { const l = edges(name, geo, LC, 0.55); l.position.set(x, y, z); bld.add(l); shellLines.push(l); };
  function facade(name, len, wall, o = {}) {
    const g = new THREE.Group(); g.name = name;
    if (o.plain) g.add(box(name + '_muro', len, hT, 0.16, wall, 0, hT / 2, 0));
    else {
      g.add(box(name + '_ventanas', len, hT, 0.04, S.win, 0, hT / 2, -0.03));
      for (let f = 0; f < 3; f++) {
        g.add(box(`${name}_antepecho_p${f}`, len, 0.75, 0.16, wall, 0, f * H + 0.725, 0));
        g.add(box(`${name}_dintel_p${f}`, len, 0.5, 0.16, wall, 0, f * H + 3.35, 0));
      }
      const n = Math.max(1, Math.round(len / 2.4));
      for (let i = 0; i <= n; i++) {
        const x = -len / 2 + (i * len) / n;
        if ((o.skip || []).some(s => Math.abs(s - x) < 0.9)) continue;
        g.add(box(`${name}_pilastra_${i}`, 0.5, hT, 0.3, wall, x, hT / 2, 0.12));
      }
    }
    for (let f = 0; f < 3; f++) g.add(box(`${name}_franja_p${f}`, len + 0.1, 0.35, 0.36, S.band, 0, f * H + 0.175, 0.1));
    g.add(box(name + '_cornisa', len + 0.3, 0.45, 0.5, S.band, 0, hT + 0.1, 0.12));
    g.position.set(o.x || 0, 0, o.z || 0); g.rotation.y = o.ry || 0;
    bld.add(g); return g;
  }
  function hip(name, w, d, h, x, y, z) {
    const geo = hipGeo(w, d, h), r = new THREE.Mesh(geo, S.tile); r.name = name; r.position.set(x, y, z); bld.add(r);
    outline(name + '_aristas', geo, x, y, z);
  }
  function slabs(name, w, d, x, z) {
    [1, 2].forEach(f => {
      const s = box(`${name}_losa_p${f}`, w, 0.25, d, M.concrete, x, f * H + 0.125, z); bld.add(s);
      const e = edges(s.name + '_borde', s.geometry, 0x6E7C89); e.position.copy(s.position); bld.add(e);
    });
    bld.add(box(name + '_losa_cubierta', w, 0.2, d, S.plate, x, hT + 0.1, z));
  }
  bld.add(box('losa_planta_baja', 47, 0.25, 11, M.concrete, 0, 0.125, 0));
  bld.add(box('losa_planta_baja_posterior', 12.5, 0.25, 6.5, M.concrete, 0, 0.125, -8));
  // Alas
  [-1, 1].forEach(s => {
    const cx = s * 13.25, len = 19.5, nm = s < 0 ? 'ala_izquierda' : 'ala_derecha';
    facade(nm + '_fachada_frontal', len, S.brick, { x: cx, z: 5 });
    facade(nm + '_fachada_posterior', len, S.brick, { x: cx, z: -5, ry: Math.PI, skip: s < 0 ? [cx - (RXS + RXR) / 2] : [] });
    facade(nm + '_muro_extremo', 10, S.brick, { x: s * 23, ry: s * Math.PI / 2, plain: true });
    slabs(nm, len, 10, cx, 0);
    outline(nm + '_contorno', new THREE.BoxGeometry(len, hT, 10), cx, hT / 2, 0);
    hip(nm + '_techo', len + 1.2, 11.2, 2.8, cx, hT + 0.3, 0);
  });
  // Núcleo central
  facade('nucleo_fachada', 7, S.cream, { z: 5 });
  slabs('nucleo', 7, 10, 0, 0);
  hip('nucleo_techo', 8.2, 11.4, 3.7, 0, hT + 0.3, 0);
  // Bloque posterior y bloque alto
  facade('posterior_lado_izq', 6, S.brick, { x: -6, z: -8, ry: -Math.PI / 2 });
  facade('posterior_lado_der', 6, S.brick, { x: 6, z: -8, ry: Math.PI / 2 });
  facade('posterior_fondo', 12, S.brick, { z: -11, ry: Math.PI });
  slabs('bloque_posterior', 12, 6, 0, -8);
  outline('bloque_posterior_contorno', new THREE.BoxGeometry(12, hT, 6), 0, hT / 2, -8);
  hip('bloque_posterior_techo', 13.2, 7.2, 2.6, 0, hT + 0.3, -8);
  const tw = box('bloque_alto', 9, 15.5, 6, S.ochre, 0, 7.75, -14); bld.add(tw);
  outline('bloque_alto_contorno', tw.geometry, 0, 7.75, -14);
  bld.add(box('bloque_alto_pretil', 9.3, 0.4, 6.3, S.band, 0, 15.6, -14));
  // Vestíbulo curvo
  const R = 3.6, VZ = 5, half = (r, h, y, mat, name) => {
    const m = new THREE.Mesh(new THREE.CylinderGeometry(r, r, h, 40, 1, true, -Math.PI / 2, Math.PI), mat);
    m.name = name; m.position.set(0, y, VZ); bld.add(m); return m;
  };
  half(R, 2 * H, H, S.win, 'vestibulo_ventanal');
  half(R + 0.04, 0.9, 0.45, S.brick, 'vestibulo_zocalo');
  [0, 1, 2].forEach(i => half(R + 0.12, 0.35, i * H + 0.175, S.band, `vestibulo_franja_${i}`));
  for (let a = -60; a <= 60; a += 30) {
    const t = a * Math.PI / 180, mu = box(`vestibulo_parteluz_${a}`, 0.18, 2 * H, 0.18, S.cream, R * Math.sin(t), H, VZ + R * Math.cos(t));
    mu.rotation.y = t; bld.add(mu);
  }
  const disc = new THREE.Mesh(new THREE.CircleGeometry(R, 40, Math.PI, Math.PI), M.concrete);
  disc.name = 'vestibulo_losa'; disc.rotation.x = -Math.PI / 2; disc.position.set(0, H + 0.1, VZ); bld.add(disc);
  const vr = new THREE.Mesh(new THREE.ConeGeometry(R + 0.7, 1.8, 40, 1, true, -Math.PI / 2, Math.PI), S.tile);
  vr.name = 'vestibulo_techo'; vr.position.set(0, 2 * H + 0.35 + 0.9, VZ); bld.add(vr);
  outline('vestibulo_contorno', new THREE.CylinderGeometry(R, R, 2 * H, 12, 1, true, -Math.PI / 2, Math.PI), 0, H, VZ);
  const shellMeshes = [];
  bld.traverse(o => { if (o.isMesh && shellMats.some(s => s.mat === o.material)) shellMeshes.push(o); });

  // ---------- Chiller (exterior, posterior izquierda) ----------
  const CX = -17, CZ = -11;
  const ch = new THREE.Group(); ch.name = 'chiller_155TR'; ch.position.set(CX, 0, CZ); root.add(ch);
  ch.userData.equip = { type: 'chiller' };
  ch.add(box('chiller_base', 5.2, 0.2, 3.2, M.concrete, 0, 0.1, 0));
  ch.add(box('chiller_cuerpo', 4.5, 1.6, 2.6, M.chiller, 0, 1.0, 0));
  [-1, 1].forEach(s => ch.add(box(`chiller_serpentin_${s > 0 ? 'a' : 'b'}`, 4.3, 1.2, 0.05, M.coil, 0, 1.05, s * 1.31)));
  ch.add(box('chiller_cubierta', 4.5, 0.08, 2.6, M.dark, 0, 1.84, 0));
  ch.add(box('chiller_tablero', 0.5, 0.9, 0.4, M.dark, 2.45, 0.65, 0.6));
  [-1.65, -0.55, 0.55, 1.65].forEach((x, i) => {
    const s = new THREE.Mesh(new THREE.CylinderGeometry(0.5, 0.5, 0.32, 32, 1, true), M.dark);
    s.material.side = THREE.DoubleSide; s.name = `chiller_virola_${i}`; s.position.set(x, 2.02, 0); ch.add(s);
    const ring = new THREE.Mesh(new THREE.TorusGeometry(0.5, 0.035, 8, 32), M.chiller);
    ring.name = `chiller_aro_${i}`; ring.rotation.x = Math.PI / 2; ring.position.set(x, 2.18, 0); ch.add(ring);
    const b = fanBlades(`chiller_ventilador_${i}`, 0.45, M.coil); b.position.set(x, 2.0, 0); ch.add(b);
    fans.push({ obj: b, axis: 'y', speed: 6 + i * 0.3 });
  });
  anchors.chiller = V(CX, 2.6, CZ);

  // ---------- Agua helada ----------
  const pipes = new THREE.Group(); pipes.name = 'circuito_agua_helada'; root.add(pipes);
  const mainS = [V(CX - 0.6, 0.9, -9.7), V(CX - 0.6, 0.9, -7.5), V(RXS, 0.9, -7.5), V(RXS, 0.9, ZS)];
  const mainR = [V(RXR, 0.5, ZR), V(RXR, 0.5, -8.2), V(CX + 0.6, 0.5, -8.2), V(CX + 0.6, 0.5, -9.7)];
  const topHy = 2 * H + 3.1;
  pipe(pipes, 'suministro_principal', [...mainS, V(RXS, topHy, ZS)], 0.13, M.supply);
  pipe(pipes, 'retorno_principal', [V(RXR, topHy, ZR), ...mainR], 0.13, M.ret);
  [[V(RXS, 0.9, -5.12), M.supply, 'brida_suministro_muro'], [V(RXS, 0.9, -7.25), M.supply, 'brida_suministro_codo'], [V(RXR, 0.5, -5.12), M.ret, 'brida_retorno_muro']]
    .forEach(([p, m, n]) => { const t = new THREE.Mesh(new THREE.TorusGeometry(0.17, 0.05, 10, 28), m); t.name = n; t.position.copy(p); pipes.add(t); });
  const thermalPts = [V(RXS, 0.9, -5.12), V(RXS, 0.9, -7.25)];
  thermalPts.forEach((p, i) => { const s = new THREE.Mesh(new THREE.SphereGeometry(i ? 0.14 : 0.2, 20, 14), M.thermal); s.name = `punto_termico_${i}`; s.position.copy(p); pipes.add(s); });
  anchors.thermal = thermalPts[0].clone();

  // ---------- Bombeo de agua helada (ilustrativo: el estudio no detalla la configuración) ----------
  // Dos bombas centrífugas en línea en paralelo: la de operación sobre el suministro principal, la de respaldo en un ramal
  const pumpG = new THREE.Group(); pumpG.name = 'bombeo_agua_helada'; root.add(pumpG);
  pumpG.userData.equip = { type: 'pump' };
  const PX = -15.5, PZ = -7.5, BZ = -6.3, PY = 0.9;
  const pumpM = std('bomba_carcasa', 0x3F6F8F, 0.5, 0.3), motorM = std('bomba_motor', 0x8E99A3, 0.5, 0.35), wheelM = std('valvula_volante', 0xB8402F, 0.6, 0.1);
  const vcyl = (name, r, h, mat, x, y, z, axis) => {
    const o = new THREE.Mesh(new THREE.CylinderGeometry(r, r, h, 16), mat); o.name = name; o.position.set(x, y, z);
    if (axis === 'x') o.rotation.z = Math.PI / 2; pumpG.add(o); return o;
  };
  pumpG.add(box('bombeo_base', 2.5, 0.15, 2.1, M.concrete, PX, 0.075, (PZ + BZ) / 2));
  pipe(pumpG, 'bombeo_ramal_respaldo', [V(PX - 1, PY, PZ), V(PX - 1, PY, BZ), V(PX + 1, PY, BZ), V(PX + 1, PY, PZ)], 0.11, M.supply);
  [['operacion', PZ], ['respaldo', BZ]].forEach(([k, z]) => {
    const id = 'bomba_' + k;
    pumpG.add(box(id + '_soporte', 0.32, PY - 0.37, 0.32, M.dark, PX, 0.15 + (PY - 0.37) / 2, z));
    vcyl(id + '_voluta', 0.26, 0.36, pumpM, PX, PY, z);
    vcyl(id + '_acople', 0.09, 0.2, M.dark, PX, PY + 0.28, z);
    vcyl(id + '_motor', 0.2, 0.55, motorM, PX, PY + 0.65, z);
    vcyl(id + '_motor_tapa', 0.14, 0.06, M.dark, PX, PY + 0.95, z);
    [-0.6, 0.6].forEach((dx, j) => {
      const vn = `${id}_valvula_corte_${j ? 'descarga' : 'succion'}`;
      vcyl(vn, 0.15, 0.16, M.dark, PX + dx, PY, z, 'x');
      vcyl(vn + '_vastago', 0.025, 0.3, M.dark, PX + dx, PY + 0.28, z);
      const w = new THREE.Mesh(new THREE.TorusGeometry(0.11, 0.022, 6, 16), wheelM); w.name = vn + '_volante';
      w.rotation.x = Math.PI / 2; w.position.set(PX + dx, PY + 0.43, z); pumpG.add(w);
    });
  });
  vcyl('bombeo_manometro_toma', 0.02, 0.3, M.dark, PX + 0.88, PY + 0.25, PZ);
  const gauge = new THREE.Mesh(new THREE.CylinderGeometry(0.1, 0.1, 0.05, 16), M.chiller); gauge.name = 'bombeo_manometro';
  gauge.rotation.x = Math.PI / 2; gauge.position.set(PX + 0.88, PY + 0.45, PZ + 0.02); pumpG.add(gauge);
  anchors.pump = V(PX, PY + 1.05, (PZ + BZ) / 2);

  // ---------- UMA ----------
  const umaG = new THREE.Group(); umaG.name = 'unidades_manejadoras'; root.add(umaG);
  const supplyPaths = [], returnPaths = [], umas = [];
  let n = 0;
  LAYOUT.forEach((xs, f) => {
    const y0 = f * H, hy = y0 + 3.1, my = y0 + 0.85;
    const lo = Math.min(...xs), hi = Math.max(...xs);
    pipe(pipes, `suministro_cabezal_p${f}`, [V(lo - 0.3, hy, ZS), V(hi - 0.3, hy, ZS)], 0.09, M.supply);
    pipe(pipes, `retorno_cabezal_p${f}`, [V(hi + 0.3, hy, ZR), V(lo + 0.3, hy, ZR)], 0.09, M.ret);
    xs.forEach(x => {
      n++;
      const id = `UMA_${String(n).padStart(2, '0')}`;
      const g = new THREE.Group(); g.name = id; umaG.add(g);
      g.userData.equip = { type: 'uma', n, f };
      g.add(box(id + '_carcasa', 1.5, 1.2, 1.0, M.uma, x, my, ZU));
      g.add(box(id + '_filtro', 0.08, 1.05, 0.9, M.dark, x - 0.78, my, ZU));
      const back = new THREE.Mesh(new THREE.CylinderGeometry(0.36, 0.36, 0.02, 32), M.dark);
      back.name = id + '_boca'; back.rotation.x = Math.PI / 2; back.position.set(x, my, ZU + 0.51); g.add(back);
      const ring = new THREE.Mesh(new THREE.TorusGeometry(0.37, 0.045, 8, 32), M.dark);
      ring.name = id + '_aro'; ring.position.set(x, my, ZU + 0.53); g.add(ring);
      const fb = fanBlades(id + '_ventilador', 0.32, M.coil); fb.rotation.x = Math.PI / 2;
      const spin = new THREE.Group(); spin.name = id + '_rotor'; spin.position.set(x, my, ZU + 0.56); spin.add(fb); g.add(spin);
      fans.push({ obj: spin, axis: 'z', speed: 9 + (n % 3) });
      g.add(box(id + '_ducto_vertical', 0.6, 1.15, 0.4, M.duct, x, y0 + 2.025, ZU));
      g.add(box(id + '_ducto_horizontal', 0.6, 0.4, 6.2, M.duct, x, y0 + 2.6, ZU + 3.1));
      g.add(box(id + '_difusor', 0.9, 0.06, 0.9, M.dark, x, y0 + 2.38, 2.6));
      pipe(pipes, id + '_suministro', [V(x - 0.3, hy, ZS), V(x - 0.3, my, ZS), V(x - 0.3, my, ZU - 0.5)], 0.06, M.supply);
      pipe(pipes, id + '_retorno', [V(x + 0.3, my, ZU - 0.5), V(x + 0.3, my, ZR), V(x + 0.3, hy, ZR)], 0.06, M.ret);
      supplyPaths.push([...mainS, V(RXS, hy, ZS), V(x - 0.3, hy, ZS), V(x - 0.3, my, ZS), V(x - 0.3, my, ZU - 0.5)]);
      returnPaths.push([V(x + 0.3, my, ZU - 0.5), V(x + 0.3, my, ZR), V(x + 0.3, hy, ZR), V(RXR, hy, ZR), ...mainR]);
      umas.push({ id, x, f, y0, my });
    });
  });
  const lastU = umas[umas.length - 1];
  anchors.uma = V(lastU.x, 2 * H + 1.6, ZU);
  anchors.floors = [0, 1, 2].map(f => V(24.2, f * H + 1.6, 5));

  // ---------- Mini-splits (muro extremo del ala izquierda) ----------
  const ms = new THREE.Group(); ms.name = 'mini_splits_inverter'; root.add(ms);
  const XW = -23;
  [{ f: 0, z: 3 }, { f: 1, z: 3.5 }, { f: 1, z: -1.5 }, { f: 2, z: 1 }].forEach(({ f, z }, i) => {
    const yi = f * H + 2.7, yo = f * H + 0.9, id = `minisplit_${i + 1}`, k0 = ms.children.length;
    ms.add(box(id + '_interior', 0.24, 0.32, 1.0, M.split, XW + 0.28, yi, z));
    ms.add(box(id + '_rejilla', 0.02, 0.05, 0.9, M.dark, XW + 0.41, yi - 0.1, z));
    ms.add(box(id + '_franja', 0.02, 0.03, 0.3, M.splitAccent, XW + 0.41, yi + 0.08, z + 0.3));
    ms.add(box(id + '_condensadora', 0.5, 0.75, 0.85, M.split, XW - 0.65, yo, z));
    ms.add(box(id + '_franja_ext', 0.5, 0.04, 0.85, M.splitAccent, XW - 0.65, yo + 0.395, z));
    if (f > 0) ms.add(box(id + '_mensula', 0.6, 0.05, 0.9, M.dark, XW - 0.65, yo - 0.4, z));
    const ring = new THREE.Mesh(new THREE.TorusGeometry(0.25, 0.03, 8, 28), M.dark);
    ring.name = id + '_aro'; ring.rotation.y = Math.PI / 2; ring.position.set(XW - 0.91, yo, z); ms.add(ring);
    const fb = fanBlades(id + '_ventilador', 0.22, M.coil, 3); fb.rotation.z = Math.PI / 2;
    const spin = new THREE.Group(); spin.name = id + '_rotor'; spin.position.set(XW - 0.91, yo, z); spin.add(fb); ms.add(spin);
    fans.push({ obj: spin, axis: 'x', speed: 7 });
    pipe(ms, id + '_linea', [V(XW + 0.16, yi, z + 0.4), V(XW - 0.5, yi, z + 0.4), V(XW - 0.5, yo + 0.4, z + 0.4)], 0.03, M.refrig);
    ms.children.slice(k0).forEach(o => { o.userData.equip = { type: 'split', n: i + 1, f }; });
  });
  anchors.split = V(XW - 0.65, 2 * H + 1.4, 1);

  // ---------- Propuesta (hipotética) ----------
  const prop = new THREE.Group(); prop.name = 'propuesta_IoT'; root.add(prop);
  const sg = new THREE.OctahedronGeometry(0.11, 0), gg = new THREE.OctahedronGeometry(0.17, 0);
  const node = (name, p, big) => { const m = new THREE.Mesh(big ? gg : sg, M.sensor); m.name = name; m.position.copy(p); prop.add(m); return m; };
  const BMS = V(0, 19.5, 2), IA = V(-11, 22, 2), BIM = V(11, 22, 2);
  const dataLines = [];
  node('sensor_chiller_T_suministro', V(CX - 0.6, 1.15, -9.5));
  node('sensor_chiller_T_retorno', V(CX + 0.6, 0.75, -9.5));
  node('sensor_chiller_corriente', V(CX + 2.45, 1.2, CZ + 0.8));
  const chGw = node('nodo_chiller', V(CX, 2.45, CZ + 1.1), true).position;
  dataLines.push([chGw, BMS]);
  const pilot = new THREE.Group(); pilot.name = 'piloto_etapa1'; prop.add(pilot);
  umas.forEach(u => {
    node(u.id + '_sensor_T_suministro', V(u.x - 0.3, u.my + 0.55, ZS));
    node(u.id + '_sensor_T_retorno', V(u.x + 0.3, u.my + 0.55, ZR));
    node(u.id + '_sensor_dP_filtro', V(u.x - 0.85, u.my + 0.3, ZU));
    node(u.id + '_sensor_corriente', V(u.x + 0.55, u.my + 0.42, ZU + 0.54));
    const gw = node(u.id + '_nodo', V(u.x + 0.5, u.y0 + 1.5, ZU + 0.35), true).position;
    dataLines.push([gw, BMS]);
    const o = edges(u.id + '_piloto', new THREE.BoxGeometry(1.75, 1.45, 1.25), 0x29A9E0, 0.9);
    o.position.set(u.x, u.my, ZU); pilot.add(o);
  });
  dataLines.push([BMS, IA], [BMS, BIM]);
  const lp = [];
  dataLines.forEach(([a, b]) => lp.push(a, b));
  const lines = new THREE.LineSegments(new THREE.BufferGeometry().setFromPoints(lp),
    new THREE.LineBasicMaterial({ name: 'lineas_datos', color: 0x29A9E0, transparent: true, opacity: 0.28 }));
  lines.name = 'lineas_datos'; prop.add(lines);
  const bms = new THREE.Group(); bms.name = 'plataforma_BMS'; bms.position.copy(BMS); prop.add(bms);
  const bb = box('BMS_gabinete', 2.4, 1.4, 1.2, M.platform, 0, 0, 0); bms.add(bb);
  bms.add(edges('BMS_borde', bb.geometry, 0x29A9E0));
  [-0.35, 0, 0.35].forEach((y, i) => bms.add(box(`BMS_ranura_${i}`, 1.9, 0.08, 0.02, M.sensor, 0, y, 0.61)));
  const ia = new THREE.Mesh(new THREE.IcosahedronGeometry(0.85, 0), M.platform); ia.name = 'IA_deteccion_anomalias'; ia.position.copy(IA); prop.add(ia);
  ia.add(edges('IA_borde', ia.geometry, 0x29A9E0));
  const bim = new THREE.Group(); bim.name = 'modelo_BIM'; bim.position.copy(BIM); prop.add(bim);
  const bimB = box('BIM_volumen', 2.0, 1.2, 1.1, M.platform, 0, 0, 0); bim.add(bimB);
  bim.add(edges('BIM_borde', bimB.geometry, 0x29A9E0));
  [-0.2, 0.2].forEach((y, i) => bim.add(edges(`BIM_losa_${i}`, new THREE.BoxGeometry(2.0, 0.001, 1.1), 0x29A9E0, 0.7).translateY(y)));
  anchors.bms = BMS.clone().setY(BMS.y + 1.0); anchors.ia = IA.clone().setY(IA.y - 1.0); anchors.bim = BIM.clone().setY(BIM.y - 0.8);
  anchors.pilotLabel = V(umas[5].x, umas[5].my + 0.75, ZU);
  anchors.sensorsUma = V(umas[2].x + 0.55, umas[2].my + 0.42, ZU + 0.54);

  // ---------- Entorno (no se exporta) ----------
  const site = new THREE.Group(); site.name = 'entorno';
  const flat = (name, geo, mat, x, y, z) => { const m = new THREE.Mesh(geo, mat); m.name = name; m.rotation.x = -Math.PI / 2; m.position.set(x, y, z); m.receiveShadow = true; site.add(m); return m; };
  const lawn = std('cesped', 0x2C3A2C, 1, 0), lawn2 = std('cesped_jardin', 0x3B5234, 1, 0), road = std('asfalto', 0x33373B, 0.95, 0), curb = std('bordillo', 0xBDB6A2, 0.9, 0);
  flat('terreno', new THREE.CircleGeometry(80, 64), lawn, 0, 0, 0);
  flat('estacionamiento', new THREE.PlaneGeometry(28, 13), road, 0, 0.02, 12.5);
  flat('jardin_frontal', new THREE.PlaneGeometry(11, 3.4), lawn2, 0, 0.03, 13.6);
  flat('rotonda_via', new THREE.RingGeometry(7.5, 11.5, 64), road, 0, 0.02, 30);
  flat('rotonda_jardin', new THREE.CircleGeometry(7.5, 64), lawn2, 0, 0.03, 30);
  flat('rotonda_bordillo', new THREE.RingGeometry(7.3, 7.65, 64), curb, 0, 0.035, 30);
  flat('via_frontal', new THREE.PlaneGeometry(7, 40), road, 0, 0.02, 59);
  flat('via_derecha', new THREE.PlaneGeometry(60, 7), road, 40, 0.02, 30);
  flat('via_izquierda', new THREE.PlaneGeometry(60, 7), road, -40, 0.02, 30);
  const greens = [0x2E5E34, 0x3C7238, 0x4A7F3F, 0x2A4F2E].map((c, i) => new THREE.MeshStandardMaterial({ name: 'follaje_' + i, color: c, roughness: 0.95, flatShading: true }));
  const trunkM = std('tronco', 0x5A4634, 0.95, 0);
  const crownG = new THREE.IcosahedronGeometry(1, 0), trunkG = new THREE.CylinderGeometry(0.16, 0.26, 1, 7);
  const r = rng(7);
  const blocked = (x, z) => (x > -28 && x < 28 && z > -21 && z < 10) || (x < 0 && z > 6) || (Math.abs(x) < 30 && z > 6)
    || (Math.abs(z - 30) < 5.5) || (Math.abs(x) < 5 && z > 38) || Math.hypot(x, z) > 74;
  let t = 0;
  for (let k = 0; k < 400 && t < 95; k++) {
    const x = (r() - 0.5) * 150, z = (r() - 0.5) * 150;
    if (blocked(x, z)) continue;
    t++;
    const h = 4 + r() * 5.5, tr = new THREE.Group(); tr.name = 'arbol_' + t; tr.position.set(x, 0, z);
    const tk = new THREE.Mesh(trunkG, trunkM); tk.scale.set(1, h * 0.55, 1); tk.position.y = h * 0.275; tk.castShadow = true; tr.add(tk);
    const nc = 2 + Math.floor(r() * 2);
    for (let c = 0; c < nc; c++) {
      const s = 1.5 + r() * 1.7, cm = new THREE.Mesh(crownG, greens[Math.floor(r() * greens.length)]);
      cm.scale.set(s, s * 0.8, s); cm.position.set((r() - 0.5) * 2, h * 0.65 + c * 0.9, (r() - 0.5) * 2); cm.rotation.y = r() * 3; cm.castShadow = true; tr.add(cm);
    }
    site.add(tr);
  }
  [-21, -17, -13, -9, -5.5, 5.5, 9, 13, 17, 21].forEach((x, i) => {
    const b = new THREE.Mesh(crownG, greens[i % 3]); b.name = 'arbusto_' + i;
    b.scale.set(0.9, 0.55, 0.6); b.position.set(x, 0.35, 6.1); site.add(b);
  });

  return { root, site, M, fans, prop, ia, supplyPaths, returnPaths, dataLines, thermalPts, anchors,
    shell: { mats: shellMats, meshes: shellMeshes, lines: shellLines } };
}
