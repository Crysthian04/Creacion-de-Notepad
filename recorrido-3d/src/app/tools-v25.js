// Herramientas de la Parada 5 (subventanas 5.2–5.4), adaptadas del modelo "Herramientas HVAC 3D" del grupo
// y colocadas dentro del Edificio 2. Todas son ilustrativas: casos hipotéticos o propuestas.
import * as THREE from 'three';

const V = (x, y, z) => new THREE.Vector3(x, y, z);
const B = (w, h, d) => new THREE.BoxGeometry(w, h, d);
const smooth = (a, b, x) => { const t = Math.min(1, Math.max(0, (x - a) / (b - a))); return t * t * (3 - 2 * t); };
function M(name, color, o = {}) {
  const m = new THREE.MeshStandardMaterial({ name, color, roughness: o.r ?? 0.75, metalness: o.m ?? 0 });
  if (o.t != null) { m.transparent = true; m.opacity = o.t; m.depthWrite = false; }
  if (o.side) m.side = o.side;
  if (o.e != null) { m.emissive = new THREE.Color(o.e); m.emissiveIntensity = o.ei ?? 1; }
  return m;
}
function add(parent, name, geo, mat, x = 0, y = 0, z = 0) {
  const m = new THREE.Mesh(geo, mat); m.name = name; m.position.set(x, y, z); m.castShadow = false; parent.add(m); return m;
}
function glowTex(rgb) {
  const c = document.createElement('canvas'); c.width = c.height = 128;
  const x = c.getContext('2d'), g = x.createRadialGradient(64, 64, 0, 64, 64, 64);
  g.addColorStop(0, `rgba(${rgb},1)`); g.addColorStop(0.3, `rgba(${rgb},.5)`); g.addColorStop(1, `rgba(${rgb},0)`);
  x.fillStyle = g; x.fillRect(0, 0, 128, 128);
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; return t;
}
const world = (o, out) => o.getWorldPosition(out);

// ---------------------------------------------------------------- 5.4 · Dron en ductos (Khalil et al., 2024)
// Ducto rectangular de 0.6 × 0.5 m sobre el cielo raso del primer alto, ala izquierda (ubicación ilustrativa)
export function buildDrone(pos) {
  const g = new THREE.Group(); g.name = 'dron_en_ductos'; g.position.copy(pos);
  const W = 0.6, H = 0.5, T = 0.008, R = 0.14;
  const mSheet = M('lamina_galvanizada', 0xAEB8BF, { r: 0.35, m: 0.3, t: 0.14, side: THREE.DoubleSide });
  const mFloor = M('piso_ducto', 0x7A838A, { r: 0.5, m: 0.3 });
  const mFlange = M('bridas', 0x5E676E, { r: 0.5, m: 0.35 });
  const mRod = M('soportes', 0x4A5157, { r: 0.6, m: 0.3 });
  const edgeMat = new THREE.LineBasicMaterial({ name: 'aristas_ducto', color: 0x29A9E0, transparent: true, opacity: 0.45 });
  function straight(name, cx, cz, len, axis) {
    const sx = axis === 'x' ? len : W, sz = axis === 'x' ? W : len;
    add(g, name + '_piso', B(sx, T, sz), mFloor, cx, T / 2, cz);
    add(g, name + '_techo', B(sx, T, sz), mSheet, cx, H - T / 2, cz);
    if (axis === 'x') { add(g, name + '_pared_a', B(len, H, T), mSheet, cx, H / 2, cz - W / 2); add(g, name + '_pared_b', B(len, H, T), mSheet, cx, H / 2, cz + W / 2); }
    else { add(g, name + '_pared_a', B(T, H, len), mSheet, cx - W / 2, H / 2, cz); add(g, name + '_pared_b', B(T, H, len), mSheet, cx + W / 2, H / 2, cz); }
    const e = new THREE.LineSegments(new THREE.EdgesGeometry(B(sx, H, sz)), edgeMat); e.name = name + '_aristas'; e.position.set(cx, H / 2, cz); g.add(e);
  }
  straight('ducto_1a', -1.95, 0, 1.3, 'x'); straight('ducto_1b', -0.65, 0, 1.3, 'x');
  straight('ducto_2a', 0.6, -1.2, 1.2, 'z'); straight('ducto_2b', 0.6, -2.4, 1.2, 'z');
  const f = 0.035, fd = 0.03;
  function flange(name, x, z, axis) {
    const p = [];
    if (axis === 'x') {
      p.push(add(g, name + '_sup', B(fd, f, W + 2 * f), mFlange, x, H + f / 2, z), add(g, name + '_inf', B(fd, f, W + 2 * f), mFlange, x, -f / 2, z));
      p.push(add(g, name + '_lado_a', B(fd, H, f), mFlange, x, H / 2, z - W / 2 - f / 2), add(g, name + '_lado_b', B(fd, H, f), mFlange, x, H / 2, z + W / 2 + f / 2));
    } else {
      p.push(add(g, name + '_sup', B(W + 2 * f, f, fd), mFlange, x, H + f / 2, z), add(g, name + '_inf', B(W + 2 * f, f, fd), mFlange, x, -f / 2, z));
      p.push(add(g, name + '_lado_a', B(f, H, fd), mFlange, x - W / 2 - f / 2, H / 2, z), add(g, name + '_lado_b', B(f, H, fd), mFlange, x + W / 2 + f / 2, H / 2, z));
    }
    return p;
  }
  flange('brida_1', -2.6, 0, 'x'); flange('brida_2', -1.3, 0, 'x'); flange('brida_3', 0, 0, 'x');
  flange('brida_4', 0.6, -0.6, 'z'); flange('brida_6', 0.6, -3.0, 'z');
  const leakBar = flange('brida_5_union_fuga', 0.6, -1.8, 'z')[3];
  leakBar.material = M('union_con_fuga', 0x5E676E, { r: 0.5, m: 0.35, e: 0xC87533, ei: 0 });
  // codo
  const ring = new THREE.RingGeometry(0.3, 0.9, 40, 1, -Math.PI / 2, Math.PI / 2);
  add(g, 'codo_piso', ring, mFloor, 0, T, -0.6).rotation.x = -Math.PI / 2;
  add(g, 'codo_techo', ring, mSheet, 0, H - 0.001, -0.6).rotation.x = -Math.PI / 2;
  add(g, 'codo_pared_interior', new THREE.CylinderGeometry(0.3, 0.3, H, 40, 1, true, 0, Math.PI / 2), mSheet, 0, H / 2, -0.6);
  add(g, 'codo_pared_exterior', new THREE.CylinderGeometry(0.9, 0.9, H, 48, 1, true, 0, Math.PI / 2), mSheet, 0, H / 2, -0.6);
  for (const r of [0.3, 0.9]) for (const y of [0, H]) {
    const pts = []; for (let i = 0; i <= 32; i++) { const th = i / 32 * Math.PI / 2; pts.push(V(r * Math.sin(th), y, -0.6 + r * Math.cos(th))); }
    const l = new THREE.Line(new THREE.BufferGeometry().setFromPoints(pts), edgeMat); l.name = 'codo_arista'; g.add(l);
  }
  // soportes colgantes y cielo raso suspendido
  const rodG = new THREE.CylinderGeometry(0.006, 0.006, 0.95, 8);
  [[-2.0, 0, 'x'], [-0.7, 0, 'x'], [0.6, -1.3, 'z'], [0.6, -2.6, 'z']].forEach(([x, z, a], i) => {
    const o = W / 2 + 0.05;
    if (a === 'x') { add(g, `colgante_${i}_a`, rodG, mRod, x, 0.43, z - o); add(g, `colgante_${i}_b`, rodG, mRod, x, 0.43, z + o); add(g, `trapecio_${i}`, B(0.04, 0.025, W + 0.16), mRod, x, -0.05, z); }
    else { add(g, `colgante_${i}_a`, rodG, mRod, x - o, 0.43, z); add(g, `colgante_${i}_b`, rodG, mRod, x + o, 0.43, z); add(g, `trapecio_${i}`, B(W + 0.16, 0.025, 0.04), mRod, x, -0.05, z); }
  });
  const gp = [];
  for (let x = -3.0; x <= 1.81; x += 0.6) gp.push(V(x, -0.3, -3.4), V(x, -0.3, 0.8));
  for (let z = -3.4; z <= 0.81; z += 0.6) gp.push(V(-3.0, -0.3, z), V(1.8, -0.3, z));
  const grid = new THREE.LineSegments(new THREE.BufferGeometry().setFromPoints(gp), new THREE.LineBasicMaterial({ name: 'reticula_cielo_raso', color: 0x56606A, transparent: true, opacity: 0.7 }));
  grid.name = 'cielo_raso_suspendido'; g.add(grid);

  // dron en jaula esférica
  const drone = new THREE.Group(); drone.name = 'dron_cuadricoptero'; g.add(drone);
  const cage = new THREE.Group(); cage.name = 'jaula_esferica'; drone.add(cage);
  const mCage = M('jaula_fibra_carbono', 0x8E979E, { r: 0.45, m: 0.25 });
  for (let i = 0; i < 6; i++) add(cage, 'jaula_meridiano_' + i, new THREE.TorusGeometry(R, 0.0035, 6, 48), mCage).rotation.y = i * Math.PI / 6;
  [[0, 0], [1, 0.62], [2, -0.62]].forEach(([k, phi]) => { add(cage, 'jaula_paralelo_' + k, new THREE.TorusGeometry(R * Math.cos(phi), 0.0035, 6, 48), mCage, 0, R * Math.sin(phi), 0).rotation.x = Math.PI / 2; });
  const core = new THREE.Group(); core.name = 'nucleo_dron'; drone.add(core);
  const mBody = M('cuerpo_dron', 0x2A2F34, { r: 0.5, m: 0.2 }), mBlade = M('helices', 0xC9CED2, { r: 0.4 }), mLens = M('lente_termica', 0x29A9E0, { r: 0.2, e: 0x29A9E0, ei: 0.8 });
  add(core, 'cuerpo', B(0.085, 0.032, 0.07), mBody);
  const props = [];
  for (let i = 0; i < 4; i++) {
    const a = Math.PI / 4 + i * Math.PI / 2;
    add(core, 'brazo_' + i, B(0.1, 0.008, 0.012), mBody, Math.cos(a) * 0.04, 0.004, Math.sin(a) * 0.04).rotation.y = -a;
    const rx = Math.cos(a) * 0.078, rz = Math.sin(a) * 0.078;
    add(core, 'motor_' + i, new THREE.CylinderGeometry(0.008, 0.008, 0.016, 12), mBody, rx, 0.012, rz);
    props.push(add(core, 'helice_' + i, B(0.068, 0.002, 0.009), mBlade, rx, 0.021, rz));
  }
  add(core, 'camara_termica', B(0.026, 0.024, 0.03), mBody, 0.05, -0.012, 0);
  const lens = add(core, 'lente_camara', new THREE.CylinderGeometry(0.009, 0.009, 0.006, 20), mLens, 0.066, -0.012, 0); lens.rotation.z = Math.PI / 2;
  const pivot = new THREE.Group(); pivot.name = 'pivote_barrido'; pivot.position.set(0.069, -0.012, 0); core.add(pivot);
  const coneMat = new THREE.MeshBasicMaterial({ name: 'campo_vision_termica', color: 0x29A9E0, transparent: true, opacity: 0.14, depthWrite: false, side: THREE.DoubleSide });
  const cone = add(pivot, 'campo_vision_termica', new THREE.ConeGeometry(0.2, 0.55, 32, 1, true), coneMat, 0.275, 0, 0); cone.rotation.z = Math.PI / 2;
  const anchorEnd = new THREE.Object3D(); anchorEnd.position.set(0.55, 0, 0); pivot.add(anchorEnd);

  // fuga hipotética en una unión
  const leakPos = V(0.9, 0.3, -1.8);
  const leakGlow = new THREE.Sprite(new THREE.SpriteMaterial({ name: 'resplandor_fuga', map: glowTex('200,117,51'), transparent: true, depthWrite: false, blending: THREE.AdditiveBlending }));
  leakGlow.scale.set(0.6, 0.6, 1); leakGlow.position.set(0.97, 0.3, -1.8); g.add(leakGlow);
  const NP = 46, pPos = new Float32Array(NP * 3), seeds = [];
  for (let i = 0; i < NP; i++) seeds.push([Math.random(), Math.random(), Math.random()]);
  const pGeo = new THREE.BufferGeometry(); pGeo.setAttribute('position', new THREE.BufferAttribute(pPos, 3));
  const pMat = new THREE.PointsMaterial({ name: 'aire_fuga', color: 0xE39A5E, size: 0.02, transparent: true, opacity: 0, depthWrite: false });
  const pts = new THREE.Points(pGeo, pMat); pts.name = 'aire_escapando'; g.add(pts);

  // trayectoria: recto → codo (vuela) → recto
  const s1 = 2.3, arc = 0.6 * Math.PI / 2, s3 = 2.2, L = s1 + arc + s3, speed = 0.3, cycle = L / speed + 3.5;
  const pathAt = s => {
    if (s < s1) return [-2.3 + s, 0, 1, 0];
    if (s < s1 + arc) { const th = (s - s1) / 0.6; return [0.6 * Math.sin(th), -0.6 + 0.6 * Math.cos(th), Math.cos(th), -Math.sin(th)]; }
    const u = s - s1 - arc; return [0.6, -0.6 - u, 0, -1];
  };
  const cCyan = new THREE.Color(0x29A9E0), cCop = new THREE.Color(0xC87533);
  const A = { drone: V(), lens: V(), sweep: V(), leak: V() };
  const S = { text: '', detected: false };
  let prevS = 0, roll = 0;
  function tick(t, dt) {
    const tc = t % cycle, s = Math.min(tc * speed, L);
    let ds = s - prevS; if (ds < 0) { ds = 0; roll = 0; } prevS = s;
    const [x, z, dx, dz] = pathAt(s);
    const fly = smooth(s1 - 0.75, s1 - 0.3, s) * (1 - smooth(s1 + arc + 0.3, s1 + arc + 0.75, s));
    roll += ds * (1 - fly);
    drone.position.set(x, R + T + 0.002 + fly * (H - 2 * R - T - 0.03), z);
    drone.rotation.y = Math.atan2(-dz, dx);
    cage.rotation.z = -roll / R;
    core.rotation.z = -0.14 * fly * (s < L ? 1 : 0);
    props.forEach((p, i) => { p.rotation.y += dt * (i % 2 ? -1 : 1) * (18 + 40 * fly); });
    g.updateMatrixWorld(true);
    const u = s - s1 - arc, lv = drone.worldToLocal(g.localToWorld(leakPos.clone()));
    const aim = Math.max(-1.4, Math.min(1.4, Math.atan2(-lv.z, lv.x)));
    const near = s > s1 + arc ? smooth(0.2, 0.5, u) * (1 - smooth(1.15, 1.45, u)) : 0, sw = Math.sin(t * 1.9) * 0.75;
    pivot.rotation.y = sw + (aim - sw) * near;
    S.detected = u >= 0.5;
    const k = S.detected ? smooth(0, 0.8, (u - 0.5) / speed) : 0;
    coneMat.color.lerpColors(cCyan, cCop, k * near);
    leakGlow.material.opacity = k * (0.75 + 0.25 * Math.sin(t * 6)); leakGlow.visible = k > 0.01;
    leakBar.material.emissiveIntensity = k * (0.7 + 0.3 * Math.sin(t * 6));
    pMat.opacity = k * 0.8; pts.visible = k > 0.01;
    for (let i = 0; i < NP; i++) {
      const [a, b, c] = seeds[i], ph = (t * 0.5 + i / NP) % 1;
      pPos[i * 3] = 0.93 + ph * 0.35; pPos[i * 3 + 1] = 0.12 + a * 0.34 + ph * 0.06 * (b - 0.3); pPos[i * 3 + 2] = -1.8 + (c - 0.5) * (0.03 + ph * 0.25);
    }
    pGeo.attributes.position.needsUpdate = true;
    world(drone, A.drone).y += 0.15; world(lens, A.lens); world(anchorEnd, A.sweep); A.leak.copy(g.localToWorld(V(0.92, 0.42, -1.8)));
    S.text = S.detected ? 'Fuga detectada en una unión del ducto' : fly > 0.05 ? 'Volando para pasar el codo' : s < s1 ? 'Rodando por el piso del ducto' : 'Rodando · barrido térmico de las paredes';
  }
  tick(0, 0);
  return { group: g, tick, A, S };
}

// ---------------------------------------------------------------- 5.3 · Realidad aumentada (Mohammadi et al., 2024)
// Salón del primer alto, ala derecha, con la fachada hacia el frente del edificio (ubicación ilustrativa).
// El campo de temperatura es simulado y se muestra SOLO de forma cualitativa (sin °C ni % de HR).
export function buildAR(pos, rotY) {
  const g = new THREE.Group(); g.name = 'realidad_aumentada_salon'; g.position.copy(pos); g.rotation.y = rotY;
  const mFloor = M('piso_baldosa', 0xB9BDBC, { r: 0.85 }), mPaint = M('pared_pintura', 0xE2DFD8, { r: 0.9 });
  const mBrick = M('ladrillo_fachada', 0xA34E36, { r: 0.9 }), mBand = M('franja_clara', 0xE2D6BF, { r: 0.85 });
  const mGlass = M('vidrio', 0x7FA3B3, { r: 0.15, m: 0.2, t: 0.3 }), mWood = M('tablero_pupitre', 0x9C7A55, { r: 0.7 });
  const mFrame = M('estructura_metal', 0x4A5157, { r: 0.55, m: 0.3 }), mSeat = M('asiento_plastico', 0x3F5568, { r: 0.6 });
  const mWhite = M('equipo_blanco', 0xF0EFEA, { r: 0.5 }), mDark = M('plastico_oscuro', 0x24282C, { r: 0.5 });
  const mLed = M('led_cian', 0x29A9E0, { e: 0x29A9E0, ei: 1 });
  add(g, 'piso_salon', B(7, 0.1, 6), mFloor, 0, -0.05, 0);
  add(g, 'pared_fondo', B(7.15, 3, 0.15), mPaint, -0.075, 1.5, -3.075);
  const lw = ext => [mPaint, ext, mPaint, mPaint, mPaint, mPaint];
  add(g, 'fachada_antepecho', B(0.15, 0.9, 6), lw(mBrick), -3.575, 0.45, 0);
  add(g, 'fachada_franja', B(0.15, 0.7, 6), lw(mBand), -3.575, 2.65, 0);
  [[-2.85, 0.3], [-0.95, 0.5], [0.95, 0.5], [2.85, 0.3]].forEach(([z, w], i) => add(g, 'fachada_pilar_' + i, B(0.15, 1.4, w), lw(mBrick), -3.575, 1.6, z));
  [[-1.95, 1.5], [0, 1.4], [1.95, 1.5]].forEach(([z, w], i) => add(g, 'ventana_' + i, B(0.03, 1.4, w), mGlass, -3.575, 1.6, z));
  add(g, 'pizarra', B(2.6, 1.1, 0.03), mWhite, -1.0, 1.55, -2.985);
  add(g, 'unidad_aa', B(1.0, 0.3, 0.22), mWhite, 2.0, 2.55, -2.89);
  add(g, 'unidad_aa_rejilla', B(0.9, 0.04, 0.02), mDark, 2.0, 2.43, -2.775);
  add(g, 'unidad_aa_indicador', B(0.03, 0.012, 0.005), mLed, 2.38, 2.5, -2.778);
  let n = 0;
  for (const z of [-1.5, -0.3, 0.9]) for (const x of [-2.5, -1.4, -0.3, 0.8]) {
    add(g, `pupitre_${n}_tablero`, B(0.62, 0.03, 0.45), mWood, x, 0.74, z);
    add(g, `pupitre_${n}_lado_a`, B(0.03, 0.72, 0.4), mFrame, x - 0.28, 0.37, z); add(g, `pupitre_${n}_lado_b`, B(0.03, 0.72, 0.4), mFrame, x + 0.28, 0.37, z);
    add(g, `silla_${n}_asiento`, B(0.42, 0.03, 0.4), mSeat, x, 0.45, z + 0.45); add(g, `silla_${n}_respaldo`, B(0.42, 0.36, 0.03), mSeat, x, 0.68, z + 0.66);
    add(g, `silla_${n}_base`, new THREE.CylinderGeometry(0.02, 0.02, 0.44, 8), mFrame, x, 0.22, z + 0.45);
    n++;
  }
  // sensores IoT con pulso de señal
  const sensors = [];
  [[-2.7, 1.6, -2.985, 'z'], [0.85, 1.6, -2.985, 'z'], [-3.485, 1.6, -0.95, 'x'], [-3.485, 1.6, 0.95, 'x']].forEach(([x, y, z, ax], i) => {
    const grp = new THREE.Group(); grp.name = 'sensor_iot_' + (i + 1); grp.position.set(x, y, z); if (ax === 'x') grp.rotation.y = Math.PI / 2;
    add(grp, 'sensor_carcasa_' + (i + 1), B(0.09, 0.13, 0.03), mDark);
    add(grp, 'sensor_led_' + (i + 1), new THREE.SphereGeometry(0.011, 12, 8), mLed, 0, 0.035, 0.017);
    const rm = new THREE.MeshBasicMaterial({ name: 'senal_iot_' + (i + 1), color: 0x29A9E0, transparent: true, opacity: 0, depthWrite: false });
    const ring = add(grp, 'senal_iot_' + (i + 1), new THREE.TorusGeometry(0.08, 0.004, 6, 40), rm, 0, 0, 0.02);
    g.add(grp); sensors.push({ grp, ring, rm, off: i * 0.6 });
  });
  // técnico con tableta
  const tech = new THREE.Group(); tech.name = 'tecnico'; tech.position.set(2.45, 0, 2.15); tech.rotation.y = Math.atan2(-2.75, -2.65);
  const mSuit = M('uniforme', 0x4A6178, { r: 0.8 }), mPants = M('pantalon', 0x2E3540, { r: 0.85 }), mSkin = M('piel', 0xB08A70, { r: 0.7 }), mHat = M('casco', 0xE8E4D8, { r: 0.45 });
  const legG = new THREE.CylinderGeometry(0.07, 0.065, 0.86, 16);
  add(tech, 'pierna_izq', legG, mPants, -0.095, 0.43, 0); add(tech, 'pierna_der', legG, mPants, 0.095, 0.43, 0);
  add(tech, 'torso', new THREE.CapsuleGeometry(0.17, 0.4, 8, 20), mSuit, 0, 1.12, 0);
  add(tech, 'cuello', new THREE.CylinderGeometry(0.05, 0.05, 0.08, 12), mSkin, 0, 1.47, 0);
  add(tech, 'cabeza', new THREE.SphereGeometry(0.11, 24, 16), mSkin, 0, 1.6, 0);
  add(tech, 'casco', new THREE.SphereGeometry(0.118, 24, 12, 0, Math.PI * 2, 0, Math.PI / 2), mHat, 0, 1.62, 0);
  add(tech, 'casco_ala', new THREE.CylinderGeometry(0.14, 0.14, 0.012, 24), mHat, 0, 1.625, 0.01);
  const limb = (name, a, b, r, mat) => {
    const d = new THREE.Vector3().subVectors(b, a), m = add(tech, name, new THREE.CapsuleGeometry(r, Math.max(0.01, d.length()), 6, 12), mat);
    m.position.copy(a).add(b).multiplyScalar(0.5); m.quaternion.setFromUnitVectors(V(0, 1, 0), d.normalize());
  };
  for (const sx of [-1, 1]) {
    const sh = V(0.21 * sx, 1.4, 0), el = V(0.24 * sx, 1.13, 0.12), hd = V(0.13 * sx, 1.15, 0.32);
    limb(sx < 0 ? 'brazo_izq' : 'brazo_der', sh, el, 0.05, mSuit); limb(sx < 0 ? 'antebrazo_izq' : 'antebrazo_der', el, hd, 0.042, mSuit);
  }
  const tab = new THREE.Group(); tab.name = 'tableta'; tab.position.set(0, 1.19, 0.36); tab.rotation.x = 0.5; tech.add(tab);
  add(tab, 'tableta_cuerpo', B(0.28, 0.19, 0.012), mDark);
  const tc = document.createElement('canvas'); tc.width = 512; tc.height = 348; const tx = tc.getContext('2d');
  const tabTex = new THREE.CanvasTexture(tc); tabTex.colorSpace = THREE.SRGBColorSpace; tabTex.anisotropy = 4;
  add(tab, 'tableta_pantalla', new THREE.PlaneGeometry(0.26, 0.176), new THREE.MeshBasicMaterial({ name: 'pantalla_ar', map: tabTex }), 0, 0, -0.0065).rotation.y = Math.PI;
  g.add(tech);

  // campo simulado (solo forma): más cálido junto a las ventanas y donde se sientan los estudiantes, más fresco cerca del equipo de A/A
  function field(x, z, k) {
    const win = Math.exp(-((x + 3.5) ** 2) / (2 * 1.5 ** 2)), ac = Math.exp(-((x - 2.0) ** 2 + (z + 3) ** 2) / (2 * 2.1 ** 2));
    const occ = Math.exp(-((x + 0.9) ** 2 + (z + 0.2) ** 2) / (2 * 1.7 ** 2));
    const a = 0.62 + 0.37 * win + 0.17 * occ - 0.51 * ac, b = 0.12 + 0.11 * win + 0.06 * occ - 0.14 * ac; // índice relativo 0–1
    return a + (b - a) * k;
  }
  const cA = new THREE.Color(0x7FD1B9), cB = new THREE.Color(0xE2D59A), cC = new THREE.Color(0xC87533);
  const tColor = (u, out) => { u = Math.min(1, Math.max(0, u)); return u < 0.5 ? out.lerpColors(cA, cB, u * 2) : out.lerpColors(cB, cC, (u - 0.5) * 2); };
  const hGeo = new THREE.PlaneGeometry(6.9, 5.9, 46, 40); hGeo.rotateX(-Math.PI / 2);
  const hCol = new Float32Array(hGeo.attributes.position.count * 3); hGeo.setAttribute('color', new THREE.BufferAttribute(hCol, 3));
  add(g, 'mapa_color_ar', hGeo, new THREE.MeshBasicMaterial({ name: 'mapa_color_ar', vertexColors: true, transparent: true, opacity: 0.6, depthWrite: false }), 0, 0.006, 0);
  const _c = new THREE.Color();
  const paint = k => { const p = hGeo.attributes.position; for (let i = 0; i < p.count; i++) { tColor(field(p.getX(i), p.getZ(i), k), _c); hCol.set([_c.r, _c.g, _c.b], i * 3); } hGeo.attributes.color.needsUpdate = true; };
  // flujo de aire del equipo de A/A
  const NA = 90, aPos = new Float32Array(NA * 3), aSeed = [];
  for (let i = 0; i < NA; i++) aSeed.push([Math.random(), Math.random()]);
  const aGeo = new THREE.BufferGeometry(); aGeo.setAttribute('position', new THREE.BufferAttribute(aPos, 3));
  const aMat = new THREE.PointsMaterial({ name: 'flujo_aire', color: 0x7FD1B9, size: 0.035, transparent: true, opacity: 0.25, depthWrite: false });
  const air = new THREE.Points(aGeo, aMat); air.name = 'flujo_aire_aa'; g.add(air);

  const ZONES = [['Zona A', -1.75, -1.5], ['Zona B', 1.75, -1.5], ['Zona C', -1.75, 1.5], ['Zona D', 0.9, 1.9]];
  const word = u => u > 0.66 ? 'más cálida' : u > 0.4 ? 'intermedia' : 'más fresca';
  const A = { zones: ZONES.map(() => V()), sensors: V(), tablet: V(), overlay: V(), ac: V() };
  const S = { target: 0, k: 0, zones: ZONES.map(() => ''), text: '' };
  let lastK = -1;
  function drawTablet() {
    tx.fillStyle = '#101316'; tx.fillRect(0, 0, 512, 348);
    tx.fillStyle = '#29A9E0'; tx.font = '600 22px "IBM Plex Mono", monospace'; tx.fillText('AR · SALÓN', 22, 38);
    tx.fillStyle = '#8B949B'; tx.font = '400 16px "IBM Plex Mono", monospace'; tx.fillText('Edificio 2 · ilustrativo', 22, 62);
    for (let i = 0; i < 22; i++) for (let j = 0; j < 19; j++) {
      tx.fillStyle = '#' + tColor(field(-3.45 + (i + 0.5) / 22 * 6.9, -2.95 + (j + 0.5) / 19 * 5.9, S.k), _c).getHexString(); tx.fillRect(22 + i * 13, 78 + j * 13, 12, 12);
    }
    tx.font = '500 17px "IBM Plex Mono", monospace';
    ZONES.forEach(([nm], i) => { tx.fillStyle = '#C9CED2'; tx.fillText(nm.replace('Zona ', '') + '  ' + S.zones[i], 320, 100 + i * 34); });
    const on = S.target === 1;
    tx.beginPath(); tx.roundRect(326, 262, 166, 52, 10); tx.fillStyle = on ? '#29A9E0' : 'rgba(41,169,224,0.12)'; tx.fill();
    tx.lineWidth = 2; tx.strokeStyle = '#29A9E0'; tx.stroke();
    tx.fillStyle = on ? '#0E1A21' : '#FFFFFF'; tx.font = '600 18px "IBM Plex Sans", sans-serif'; tx.fillText('Control HVAC', 350, 294);
    tabTex.needsUpdate = true;
  }
  document.fonts && document.fonts.ready.then(() => { lastK = -1; });
  function tick(t, dt) {
    S.k += (S.target - S.k) * Math.min(1, dt * 1.1); if (Math.abs(S.target - S.k) < 0.002) S.k = S.target;
    if (Math.abs(S.k - lastK) > 0.0015 || lastK < 0) {
      ZONES.forEach(([, x, z], i) => { S.zones[i] = word(field(x, z, S.k)); });
      paint(S.k); drawTablet(); lastK = S.k;
    }
    S.text = S.k > 0.95 ? 'Ajuste aplicado: temperatura más pareja en el salón' : S.target ? 'Aplicando el ajuste desde la tableta…' : 'Antes del ajuste: más calor junto a las ventanas';
    sensors.forEach(s => { const ph = (t * 0.45 + s.off) % 1; s.ring.scale.setScalar(1 + ph * 2.2); s.rm.opacity = (1 - ph) * 0.7; });
    mLed.emissiveIntensity = 0.7 + 0.5 * Math.sin(t * 3);
    aMat.opacity = 0.22 + 0.5 * S.k;
    for (let i = 0; i < NA; i++) {
      const [a, b] = aSeed[i], ph = (t * 0.32 + i / NA) % 1;
      aPos[i * 3] = 2.0 + (a - 0.5) * (0.85 + ph * 1.4); aPos[i * 3 + 1] = 2.4 - ph * 1.5 - ph * ph * 0.5; aPos[i * 3 + 2] = -2.75 + ph * (1.6 + 1.2 * S.k) + (b - 0.5) * 0.2;
    }
    aGeo.attributes.position.needsUpdate = true;
  }
  g.updateMatrixWorld(true);
  ZONES.forEach(([, x, z], i) => A.zones[i].copy(g.localToWorld(V(x, 1.9, z))));
  world(sensors[1].grp, A.sensors); world(tab, A.tablet); A.overlay.copy(g.localToWorld(V(-2.6, 0.02, 2.5))); A.ac.copy(g.localToWorld(V(2.0, 2.75, -2.89)));
  tick(0, 0);
  return { group: g, tick, A, S, ZONES };
}

// ---------------------------------------------------------------- 5.2 · Cámara termográfica portátil
// Recorre la tubería de agua helada y apunta a las dos uniones con deterioro (puntos de la inspección)
export function buildIRCamera(targets) {
  const dev = new THREE.Group(); dev.name = 'camara_termografica';
  const body = new THREE.Group(); body.scale.setScalar(1.6); dev.add(body);
  const mCam = M('camara_carcasa', 0x3A3F44, { r: 0.55 }), mAcc = M('camara_detalle', 0xC87533, { r: 0.5 }), mIR = M('camara_lente', 0x29A9E0, { r: 0.2, e: 0x29A9E0, ei: 0.6 });
  add(body, 'camara_cuerpo', B(0.11, 0.09, 0.16), mCam);
  add(body, 'camara_objetivo', new THREE.CylinderGeometry(0.036, 0.036, 0.05, 28), mCam, 0, 0.008, 0.1).rotation.x = Math.PI / 2;
  add(body, 'camara_lente', new THREE.CylinderGeometry(0.028, 0.028, 0.006, 28), mIR, 0, 0.008, 0.126).rotation.x = Math.PI / 2;
  add(body, 'camara_empunadura', B(0.055, 0.14, 0.05), mAcc, 0, -0.1, -0.025).rotation.x = 0.25;
  const sc = document.createElement('canvas'); sc.width = 64; sc.height = 48; const sx = sc.getContext('2d');
  const sg = sx.createLinearGradient(0, 0, 64, 0); sg.addColorStop(0, '#1E4FD8'); sg.addColorStop(0.5, '#6B2470'); sg.addColorStop(0.8, '#E0301E'); sg.addColorStop(1, '#F2D22E');
  sx.fillStyle = sg; sx.fillRect(0, 0, 64, 48);
  const st = new THREE.CanvasTexture(sc); st.colorSpace = THREE.SRGBColorSpace;
  add(body, 'camara_pantalla', new THREE.PlaneGeometry(0.09, 0.068), new THREE.MeshBasicMaterial({ name: 'camara_pantalla', map: st }), 0, 0.005, -0.0805).rotation.y = Math.PI;
  const cone = add(body, 'campo_vision_ir', new THREE.ConeGeometry(0.5, 1, 32, 1, true),
    new THREE.MeshBasicMaterial({ name: 'campo_vision_ir', color: 0x29A9E0, transparent: true, opacity: 0.14, depthWrite: false, side: THREE.DoubleSide }));
  cone.rotation.x = -Math.PI / 2;
  const [U1, U2] = targets;
  const P0 = V(-13.6, 2.0, -9.6), P1 = V(-12.0, 1.35, -5.4), P2 = V(-12.0, 1.35, -7.7);
  const keys = [[0, P0, U1], [4, P1, U1], [7.5, P1, U1], [10, P2, U2], [13.5, P2, U2], [17, P0, U1]];
  const cyc = 17, aim = V(), A = { cam: V() };
  function tick(t) {
    const tc = t % cyc; let i = 0; while (i < keys.length - 2 && tc > keys[i + 1][0]) i++;
    const [ta, pa, aa] = keys[i], [tb, pb, ab] = keys[i + 1], u = smooth(0, 1, (tc - ta) / (tb - ta));
    dev.position.lerpVectors(pa, pb, u); aim.lerpVectors(aa, ab, u);
    aim.y += Math.sin(t * 1.3) * 0.05; aim.z += Math.sin(t * 0.9) * 0.12; dev.position.y += Math.sin(t * 1.7) * 0.025;
    dev.lookAt(aim);
    const l = Math.max(0.2, (dev.position.distanceTo(aim) - 0.2) / 1.6);
    cone.scale.set(l * 0.34, l, l * 0.34); cone.position.set(0, 0.008, 0.13 + l / 2);
    A.cam.copy(dev.position).y += 0.25;
  }
  tick(0);
  return { group: dev, tick, A };
}
