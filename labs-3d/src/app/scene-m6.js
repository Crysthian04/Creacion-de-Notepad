// Parada 1 · M6: unidad con filtro, serpentín y ventilador con correas; ducto principal, 4 ramales,
// 8 terminales con compuerta y difusor. Barras (relación medido/diseño, sin escala) con la franja de ±5 %.
// Toda la geometría es ilustrativa; el texto está en content-m6.js.
import { M6, SC6 } from 'app/content-m6.js';

export function buildM6({ THREE, label }) {
  const g = new THREE.Group(); g.name = 'parada_1_m6';
  const M = (c, o = {}) => new THREE.MeshStandardMaterial({ color: c, roughness: 0.7, metalness: 0.15, ...o });
  const mat = {
    duct: M(0xC5CDD3, { metalness: 0.3, roughness: 0.45 }), casing: M(0x8F9AA4), dark: M(0x3A424A), floor: M(0x252A2F, { roughness: 1 }),
    filterDirty: M(0x8A6A3E), filterClean: M(0xEDEFF0), coil: M(0x5F8FA8), wheel: M(0x6FA8C8), belt: M(0x1E2226), pulley: M(0xA9B2BA, { metalness: 0.4 }),
    diff: M(0xE6EBEF), damper: M(0xE3A857), joint: M(0xC5CDD3, { metalness: 0.3, roughness: 0.45, emissive: 0x000000 }),
    bar: M(0x29A9E0, { emissive: 0x0B3346 }), band: new THREE.MeshBasicMaterial({ color: 0x4FAE5B, transparent: true, opacity: 0.35, depthWrite: false }),
    elbow: M(0xE5534B), vfd: M(0x2E6E8E), vav: M(0x7FB3D5), probe: M(0xF2C14E),
  };
  const box = (w, h, d, m, x, y, z, parent = g, name = '') => { const o = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), m); o.position.set(x, y, z); o.name = name; parent.add(o); return o; };
  const v3 = (x, y, z) => new THREE.Vector3(x, y, z);

  // Piso (ilustrativo)
  const fl = box(34, 0.1, 14, mat.floor, 1.5, -0.05, 0, g, 'piso'); fl.receiveShadow = true;
  // Unidad: filtro → serpentín → ventilador
  const Y = 1.3; // eje de la unidad
  box(0.25, 2.0, 2.0, mat.casing, -14.6, Y, 0, g, 'marco_filtro');
  const filt = box(0.18, 1.8, 1.8, mat.filterDirty, -14.4, Y, 0, g, 'filtro');
  box(2.4, 2.2, 2.2, new THREE.MeshStandardMaterial({ color: 0x8F9AA4, transparent: true, opacity: 0.18, depthWrite: false }), -13.2, Y, 0, g, 'carcasa_unidad');
  const coil = box(0.5, 1.8, 1.8, mat.coil, -12.6, Y, 0, g, 'serpentin');
  for (let i = 0; i < 9; i++) box(0.52, 0.04, 1.82, mat.dark, -12.6, Y - 0.8 + i * 0.2, 0, g);
  // Ventilador centrífugo (carcasa abierta para ver el rodete)
  const fanC = v3(-10.4, Y + 0.2, 0);
  const hous = new THREE.Mesh(new THREE.CylinderGeometry(1.1, 1.1, 0.9, 40, 1, true, 0, Math.PI * 1.6), new THREE.MeshStandardMaterial({ color: 0x8F9AA4, side: THREE.DoubleSide, roughness: 0.6 }));
  hous.rotation.x = Math.PI / 2; hous.position.copy(fanC); hous.name = 'carcasa_ventilador'; g.add(hous);
  const wheel = new THREE.Group(); wheel.position.copy(fanC); wheel.name = 'rodete'; g.add(wheel);
  for (let i = 0; i < 12; i++) { const a = new THREE.Group(); a.rotation.z = i * Math.PI / 6; box(0.05, 0.42, 0.8, mat.wheel, 0, 0.62, 0, a); wheel.add(a); }
  // Descarga del ventilador hacia el ducto principal
  box(0.9, 2.4, 0.9, mat.duct, -9.6, Y + 1.9, 0, g, 'descarga');
  // Motor, poleas y correa: las dos poleas en el mismo plano (z = ZP) con ejes paralelos (eje z);
  // la correa está en ese plano, con tramos tangentes y arcos alrededor de cada polea (caso «correcto» de la Figura 3).
  const ZP = 1.25, PW = 0.12, MY = 0.45, R1 = 0.22, R2 = 0.4; // plano de poleas, ancho de polea, eje del motor, radios
  const shaft = (x, y, z0, z1, r) => { const m = new THREE.Mesh(new THREE.CylinderGeometry(r, r, z1 - z0, 12), mat.pulley); m.rotation.x = Math.PI / 2; m.position.set(x, y, (z0 + z1) / 2); g.add(m); return m; };
  shaft(-10.4, fanC.y, 0.45, ZP + PW / 2 + 0.04, 0.05); // eje del ventilador, alargado hasta el plano de las poleas
  shaft(-10.4, MY, 1.1, ZP + PW / 2 + 0.04, 0.05);       // eje del motor (el cuerpo queda detrás del plano de poleas, hacia el ventilador)
  const motor = new THREE.Mesh(new THREE.CylinderGeometry(0.36, 0.36, 0.6, 24), mat.casing); motor.rotation.x = Math.PI / 2; motor.position.set(-10.4, MY, 0.82); motor.name = 'motor'; g.add(motor);
  const pul = (y, r) => { const p = new THREE.Mesh(new THREE.CylinderGeometry(r, r, PW, 32), mat.pulley); p.rotation.x = Math.PI / 2; p.position.set(-10.4, y, ZP); p.name = 'polea'; g.add(p); return p; };
  const p1 = pul(MY, R1), p2 = pul(fanC.y, R2);
  const beltG = new THREE.Group(); beltG.name = 'correa'; g.add(beltG);
  {
    const d = fanC.y - MY, be = Math.asin((R2 - R1) / d), T = 0.035; // ángulo de los tramos rectos y espesor de la correa
    const loop = off => { // contorno cerrado: arco superior (polea del ventilador) + arco inferior (polea del motor)
      const pts = [], arc = (cy, r, a0, a1) => { for (let i = 0; i <= 24; i++) { const a = a0 + (a1 - a0) * i / 24; pts.push(new THREE.Vector2(Math.cos(a) * (r + off), cy + Math.sin(a) * (r + off))); } };
      arc(fanC.y, R2, -be, Math.PI + be); arc(MY, R1, Math.PI + be, 2 * Math.PI - be); return pts;
    };
    const shape = new THREE.Shape(loop(T)); shape.holes.push(new THREE.Path(loop(0)));
    const belt = new THREE.Mesh(new THREE.ExtrudeGeometry(shape, { depth: PW, bevelEnabled: false, curveSegments: 4 }), mat.belt);
    belt.position.set(-10.4, 0, ZP - PW / 2); belt.name = 'correa_plana'; beltG.add(belt);
  }
  const motorBase = box(0.9, 0.1, 0.8, mat.dark, -10.4, 0.05, 0.82, g);

  // Ducto principal y ramales
  const DY = 3.6, X0 = -9.6, X1 = 13.6;
  box(X1 - X0 + 0.9, 0.7, 0.9, mat.duct, (X0 + X1) / 2, DY, 0, g, 'ducto_principal');
  const joints = [];
  for (let x = X0 + 2; x < X1; x += 2.4) joints.push(box(0.12, 0.78, 0.98, mat.joint.clone(), x, DY, 0, g, 'union'));
  const BX = [-4.5, 1.5, 7.5, 13.2], Z = 3.2, TY = 2.9;
  const T = []; // terminales: 0 = más cercano al ventilador … 7 = el último
  BX.forEach((bx, b) => {
    box(0.6, 0.5, Z * 2, mat.duct, bx, DY, 0, g, `ramal_${b + 1}`);
    [-1, 1].forEach(s => {
      const z = s * Z, neck = new THREE.Group(); neck.position.set(bx, TY + 0.25, z); g.add(neck);
      box(0.55, 0.7, 0.55, new THREE.MeshStandardMaterial({ color: 0xC5CDD3, transparent: true, opacity: 0.35, depthWrite: false }), 0, 0.15, 0, neck);
      const damp = new THREE.Group(); neck.add(damp); box(0.5, 0.04, 0.5, mat.damper, 0, 0, 0, damp, 'compuerta');
      damp.rotation.x = Math.PI / 2; // abierta: hoja vertical, paralela al flujo
      const diff = box(0.9, 0.08, 0.9, mat.diff, bx, TY - 0.15, z, g, 'difusor');
      // Barra de relación (medido/diseño) sobre el piso y franja de ±5 %
      const bar = box(0.5, 1, 0.5, mat.bar, bx, 0.5, z, g, 'barra_relacion');
      const band = box(0.8, 0.16, 0.8, mat.band, bx, 1.6, z, g, 'franja_5'); band.castShadow = false;
      T.push({ b, z, x: bx, damp, neck, diff, bar, band, r: 1, rt: 1, ang: 0, angT: 0, flowPath: [v3(-9.6, DY, 0), v3(bx, DY, 0), v3(bx, DY, z), v3(bx, TY - 0.3, z)] });
    });
  });
  // Ordenar del más cercano al más lejano (por longitud de recorrido)
  T.sort((a, b) => (a.x + Math.abs(a.z) * 0.01) - (b.x + Math.abs(b.z) * 0.01));
  T.forEach((t, i) => [t.neck, t.diff].forEach(o => o.traverse(q => { q.userData.term = i; }))); // clic sobre la compuerta (E2)
  const H1 = 1.6; // altura de la barra cuando la relación es 1 (centro de la franja)
  const setBars = () => T.forEach(t => { const h = Math.max(0.05, t.r * H1); t.bar.scale.y = h; t.bar.position.y = h / 2; const ok = Math.abs(t.r - 1) <= 0.05; t.bar.material = ok ? barOk : mat.bar; });
  const barOk = M(0x4FAE5B, { emissive: 0x123A18 });

  // Partículas de aire (InstancedMesh)
  const PER = 9, N = T.length * PER;
  const pim = new THREE.InstancedMesh(new THREE.SphereGeometry(0.07, 8, 6), new THREE.MeshBasicMaterial({ color: 0xD8FFF2 }), N); pim.name = 'particulas_aire'; pim.frustumCulled = false; g.add(pim);
  const paths = T.map(t => { const L = [0]; for (let i = 1; i < t.flowPath.length; i++) L.push(L[i - 1] + t.flowPath[i].distanceTo(t.flowPath[i - 1])); return { pts: t.flowPath, L, len: L[L.length - 1] }; });
  const off = new Float32Array(N).map((_, i) => (i % PER) / PER);
  const tmp = new THREE.Object3D(), pv = new THREE.Vector3();
  function at(p, d) { let i = 1; while (i < p.L.length - 1 && p.L[i] < d) i++; return pv.lerpVectors(p.pts[i - 1], p.pts[i], (d - p.L[i - 1]) / (p.L[i] - p.L[i - 1] || 1)); }
  const stuck = { on: false, i: 2 };
  function stepParticles(dt, speed) {
    for (let k = 0; k < T.length; k++) {
      const t = T[k], sp = 0.12 * speed * (stuck.on && k === stuck.i ? 2.2 : (stuck.on ? 0.75 : t.r));
      for (let j = 0; j < PER; j++) { const i = k * PER + j; off[i] = (off[i] + dt * sp) % 1; tmp.position.copy(at(paths[k], off[i] * paths[k].len)); tmp.updateMatrix(); pim.setMatrixAt(i, tmp.matrix); }
    }
    pim.instanceMatrix.needsUpdate = true;
  }

  // Objetos de pasos específicos
  const elbow = new THREE.Group(); elbow.name = 'codo'; elbow.visible = false; g.add(elbow);
  box(0.95, 0.95, 0.95, mat.elbow, -9.6, DY + 0.55, 0, elbow); box(1.6, 0.85, 0.95, mat.elbow, -10.6, DY + 0.55, 0, elbow);
  const vfd = box(0.5, 0.8, 0.3, mat.vfd, -11.6, 0.9, 1.9, g, 'variador'); vfd.visible = false;
  const vavs = BX.map((bx, i) => { const o = box(0.7, 0.6, 0.8, mat.vav, bx, DY, 1.4, g, `caja_vav_${i + 1}`); o.visible = false; return o; });
  const probe = box(0.12, 0.6, 0.12, mat.probe, 0, TY + 0.6, 0, g, 'sonda_referencia'); probe.visible = false;
  const anem = new THREE.Group(); anem.name = 'anemometro'; anem.visible = false; g.add(anem);
  box(0.9, 0.5, 0.9, new THREE.MeshStandardMaterial({ color: 0x31363B, transparent: true, opacity: 0.85 }), 0, 0, 0, anem); box(0.08, 1.2, 0.08, mat.dark, 0, -0.85, 0, anem);
  const taps = [v3(-11.6, Y + 0.2, 0.55), v3(-9.6, DY - 0.2, 0.55)];

  // Etiquetas
  const il = '<span class="st il">Ilustrativo</span>';
  const L = {
    filtro: label(v3(-14.4, Y - 1.0, 0.9), 'Filtro', { down: true }),
    serp: label(v3(-12.8, Y + 1.15, 0), 'Serpentín'),
    fs: label(v3(-13.5, Y + 1.15, 0), 'Filtro · serpentín'),
    vent: label(v3(-10.0, Y + 3.4, 0), 'Ventilador y descarga'),
    motor: label(v3(-10.4, 0.25, 1.3), 'Motor, poleas y correa', { down: true }),
    ducto: label(v3(0, DY + 0.45, 0), 'Ducto principal'),
    ramal: label(v3(BX[1], DY + 0.35, -Z * 0.55), 'Ramal'),
    comp: label(v3(BX[3], TY + 0.6, Z), 'Compuerta'),
    term: label(v3(BX[3], TY - 0.2, -Z), 'Terminal (difusor)', { down: true }),
    banda: label(v3(BX[0], 1.75, -Z), `${'<span class="st df">Dato de fuente</span>'}Franja de ±5&nbsp;% del diseño<small>(Yale Facilities, 2025)</small>`, { cls: 'green' }),
    barra: label(v3(BX[0], 0.9, Z), `${il}Barra: medido / diseño<small>sin escala</small>`, { down: true }),
    fase: label(v3(-12.6, Y + 2.3, 0), '', { cls: 'amber' }),
    estado: label(v3(2, DY + 1.2, 0), '', { cls: 'amber' }),
    cuenta: label(v3(BX[1], DY + 1.4, 0), '', { cls: 'amber' }),
    vfd: label(v3(-11.6, 1.4, 1.9), `${il}Variador de frecuencia`, { cls: 'cyan' }),
    sonda: label(v3(0, TY + 1.0, 0), `${il}Sonda de referencia<small>primer terminal</small>`, { cls: 'cyan' }),
    vav: label(v3(BX[1], DY + 0.4, 1.4), `${il}Cajas VAV en las derivaciones`, { cls: 'cyan' }),
    codo: label(v3(-10.4, DY + 1.1, 0), `${il}Codo junto a la salida<small>hasta −30&nbsp;% de caudal (DOE y AMCA, 2003, p. 9)</small>`, { cls: 'red' }),
    tomaIn: label(taps[0], `${il}Toma de presión · entrada`, { cls: 'cyan', down: true }),
    tomaOut: label(taps[1], `${il}Toma de presión · salida`, { cls: 'cyan' }),
    anem: label(v3(0, TY + 0.4, 0), `${il}Anemómetro: varias lecturas y promedio`, { cls: 'cyan', down: true }),
    cl: label(v3(4, DY + 0.6, 0), '', { cls: 'amber' }),
    correa: label(v3(-9.7, 2.2, 1.25), `${il}Correas y poleas: estado, tensión y alineación`, { cls: 'amber' }),
  };
  const base = [L.fs, L.vent, L.ducto, L.comp, L.term];
  const net = [L.banda, L.barra];

  // Cámara por paso [posición, objetivo]
  const CAM = {
    red: [-10, 16, 24, -4, 1.2, 0], marco: [-15, 13, 17, 3, 1.0, 0], previas: [-6, 6, 11, -11.5, 1.8, 0],
    proporcion: [-15, 13, 17, 3, 1.0, 0], progresivo: [-15, 13, 17, 3, 1.0, 0], apertura: [-14, 11, 15, 3, 2.5, 0],
    leyes: [-6, 5, 9, -10.8, 1.8, 0], panama: [-11, 14, 22, -5, 1.5, 0], cierre: [-10, 16, 24, -4, 1.2, 0],
    nebb: [-15, 13, 17, 3, 1.0, 0], fugas: [-9, 9, 11, 2, 3.4, 0], correas: [-8.6, 1.7, 5.6, -10.4, 1.0, 1.25],
    presion: [-6, 5, 8, -10.8, 2.4, 0], medir: [-2, 5, 9, 1.0, 2.2, 3.2], efecto: [-6, 7, 10, -10.2, 3.2, 0],
    kleberg: [-10, 16, 24, -4, 1.2, 0], bogota: [-15, 13, 17, 3, 1.0, 0], normas: [-10, 16, 24, -4, 1.2, 0],
  };

  const LBL = {
    red: [...base, L.motor, L.ramal], marco: [...net, L.term], previas: [L.filtro, L.fase, L.motor], proporcion: [...net, L.cuenta],
    progresivo: [L.barra, L.cuenta, L.vfd, L.sonda], apertura: [L.estado, L.comp, L.vent], leyes: [L.vent, L.motor], panama: [L.vfd, L.vav, L.ducto],
    cierre: [...base], nebb: [...base], fugas: [L.cl, L.ducto], correas: [L.correa], presion: [L.tomaIn, L.tomaOut, L.vent], medir: [L.anem, L.term],
    efecto: [L.codo, L.vent], kleberg: [...base], bogota: [...base], normas: [...base],
  };

  // ---------- Animaciones ----------
  const R0 = [1.34, 1.27, 1.18, 1.08, 0.97, 0.88, 0.79, 0.72]; // relaciones iniciales ilustrativas (más aire cerca del ventilador)
  // Método de proporción: 13 ajustes de compuerta (iterativo, por pares desde los más desfavorecidos) + ajuste final del ventilador
  const PROP = (() => {
    const order = [6, 5, 4, 3, 2, 1, 0, 5, 3, 1, 4, 2, 0];
    let r = R0.slice(), ang = new Array(8).fill(0); const frames = [{ r: r.slice(), ang: ang.slice(), fan: 1 }];
    order.forEach((i, k) => {
      const ref = Math.min(...r), target = ref * (k < 7 ? 1.0 : 1.01), d = r[i] - target;
      r = r.map((x, j) => j === i ? target : x + d * 0.09); ang[i] = Math.min(1, ang[i] + d * 1.6);
      if (k === order.length - 1) { const c = r.reduce((a, b) => a + b) / 8; r = r.map((x, j) => c * (1 + [0.02, -0.015, 0.01, -0.02, 0.015, -0.01, 0.02, -0.005][j])); }
      frames.push({ r: r.slice(), ang: ang.slice(), fan: 1 });
    });
    const c = r.reduce((a, b) => a + b) / 8; frames.push({ r: r.map(x => x / c), ang: ang.slice(), fan: 1 / c });
    return frames; // 15 cuadros = estado inicial + 14 pasos
  })();
  const PROG = (() => { const fr = [{ r: R0.slice() }]; let r = R0.slice(); for (let i = 7; i >= 0; i--) { r = r.slice(); r[i] = 1 + [0.01, -0.02, 0.015, -0.01, 0.02, -0.015, 0.01, 0][i]; fr.push({ r: r.slice(), i }); } return fr; })();
  let fanSpeed = 1, fanT = 1, cntEl = null;
  const cnt = v => { cntEl = cntEl && cntEl.isConnected ? cntEl : document.querySelector('[data-cnt]'); if (cntEl) cntEl.textContent = v; };
  function resetNet() { T.forEach((t, i) => { t.rt = 1; t.r = 1; t.angT = 0; }); fanT = 1; stuck.on = false; filt.material = mat.filterClean; joints.forEach(j => j.material.emissive.setHex(0)); }

  function enter(st) {
    resetNet(); cntEl = null;
    elbow.visible = st.id === 'efecto'; vfd.visible = ['progresivo', 'panama', 'E4'].includes(st.id); vavs.forEach(v => v.visible = ['panama', 'E4'].includes(st.id));
    probe.visible = st.id === 'progresivo'; if (probe.visible) probe.position.set(T[0].x, TY + 0.6, T[0].z);
    anem.visible = st.id === 'medir'; if (anem.visible) anem.position.set(T[2].x, TY - 0.55, T[2].z);
    L.anem.anchor.set(T[2].x, TY - 0.85, T[2].z); L.sonda.anchor.set(T[0].x, TY + 1.0, T[0].z);
    const showBars = ['marco', 'proporcion', 'progresivo', 'E2'].includes(st.id); // en Bogotá no hay valores por rejilla en el informe
    T.forEach(t => { t.bar.visible = t.band.visible = showBars; });
    if (st.id === 'proporcion' || st.id === 'progresivo') { T.forEach((t, i) => { t.r = t.rt = R0[i]; }); cnt(0); }
    if (st.id === 'previas') filt.material = mat.filterDirty;
    if (st.id === 'leyes') { const s = document.getElementById('spd'), b = document.getElementById('spd80'); if (s) { s.oninput = laws; b.onclick = () => { s.value = 80; laws(); }; laws(); } }
    scEnter(st);
    setBars();
  }
  function laws() {
    const s = document.getElementById('spd'); if (!s) return; const n = s.value / 100;
    [1, 2, 3].forEach(k => { const el = document.querySelector(`[data-law="${k}"]`); if (el) el.style.width = (Math.pow(n, k) * 100).toFixed(1) + '%'; });
    document.getElementById('rot')?.classList.toggle('hot', Math.abs(s.value - 80) < 1);
    fanT = n;
  }

  function tick(dt, t, st) {
    const id = st.id;
    if (id === 'previas') {
      const ph = Math.floor((t % 16) / 4);
      filt.material = ph === 0 && (t % 16) < 2 ? mat.filterDirty : mat.filterClean;
      joints.forEach((j, k) => j.material.emissive.setHex(ph === 1 && (Math.floor(t * 3) % joints.length) === k ? 0xE3A857 : 0));
      stuck.on = ph === 2; T.forEach(tt => tt.angT = 0); if (stuck.on) T[stuck.i].angT = 0;
      beltG.children.forEach(b => b.material = ph === 3 && Math.floor(t * 4) % 2 ? mat.damper : mat.belt);
      const txt = ['① Filtro sucio → filtro limpio', '② Prueba de fugas en las uniones', '③ Compuerta trabada abierta: roba caudal', '④ Correas y poleas'][ph];
      L.fase.set(`<span class="st il">Ilustrativo</span>${txt}`);
      L.fase.anchor.copy(ph === 1 ? v3(0, DY + 0.8, 0) : ph === 2 ? v3(T[stuck.i].x, TY + 1.2, T[stuck.i].z) : ph === 3 ? v3(-10.4, 2.3, 1.3) : v3(-14.4, Y + 1.3, 0));
    } else beltG.children.forEach(b => b.material = mat.belt);
    if (id === 'proporcion') {
      const k = Math.min(14, Math.floor(t / 1.4)); const f = PROP[k];
      T.forEach((tt, i) => { tt.rt = f.r[i]; tt.angT = f.ang[i]; }); fanT = f.fan; cnt(k);
      L.cuenta.set(`<span class="st df">Dato de fuente</span>Proporción: paso ${k} de 14<small>(Pedranzini et al., 2013, p. 328)</small>`);
      if (t > 14 * 1.4 + 4) { T.forEach((tt, i) => { tt.r = tt.rt = R0[i]; tt.angT = 0; tt.ang = 0; }); fanT = 1; return enter.restart(st); }
    }
    if (id === 'progresivo') {
      const k = Math.min(8, Math.floor(t / 1.6)), f = PROG[k];
      T.forEach((tt, i) => { tt.rt = f.r[i]; }); const c = Math.min(10, Math.round(k * 10 / 8)); cnt(c);
      L.cuenta.set(`<span class="st df">Dato de fuente</span>Flujo progresivo: ${c} de 10 pasos<small>(Pedranzini et al., 2013, p. 328)</small>`);
      if (k < 8) L.cuenta.anchor.set(T[7 - k].x, DY + 1.0, T[7 - k].z * 0.4);
      if (t > 8 * 1.6 + 4) { T.forEach((tt, i) => { tt.r = tt.rt = R0[i]; }); return enter.restart(st); }
    }
    if (id === 'apertura') {
      const closed = Math.floor(t / 4) % 2 === 0;
      T.forEach(tt => tt.angT = closed ? 0.85 : 0); fanT = closed ? 1.6 : 0.9;
      L.estado.set(`<span class="st il">Ilustrativo</span>${closed ? 'Compuertas casi cerradas · ventilador rápido' : 'Compuertas abiertas · ventilador más lento'}<small>mismo caudal en los terminales</small>`);
    }
    if (id === 'fugas') {
      const ph = Math.floor(t / 3) % 3, col = [0xE5534B, 0xE3A857, 0x4FAE5B][ph];
      joints.forEach(j => j.material.emissive.setHex(col)); joints.forEach(j => j.material.emissiveIntensity = 0.6);
      L.cl.set(`<span class="st df">Dato de fuente</span>${['CL 48 · rectangular sin sellar', 'CL 24 · uniones transversales selladas', 'CL 6 · todo sellado'][ph]}<small>(DOE y AMCA, 2003, p. 38)</small>`);
    }
    if (id === 'correas') beltG.children.forEach(b => b.material = Math.floor(t * 3) % 2 ? mat.damper : mat.belt);
    scTick(dt, t, st);
    // Interpolación suave de barras, compuertas y velocidad
    const a = Math.min(1, dt * 4);
    T.forEach(tt => { tt.r += (tt.rt - tt.r) * a; tt.ang += (tt.angT - tt.ang) * a; tt.damp.rotation.x = Math.PI / 2 - tt.ang * (Math.PI / 2) * 0.85; });
    fanSpeed += (fanT - fanSpeed) * a;
    wheel.rotation.z -= dt * 7 * fanSpeed; p2.rotation.y -= dt * 7 * fanSpeed; p1.rotation.y -= dt * 12 * fanSpeed;
    stepParticles(dt, fanSpeed);
    if (T[0].bar.visible) setBars();
  }
  enter.restart = st => { stopRef.t0(); enter(st); };
  const stopRef = { t0: () => {} };

  // ---------- E2 · simulación ilustrativa de la red (sin valores en pantalla) ----------
  // Tramos del ducto principal (Rm), ramales (Rb), terminales (Rt) y compuertas (Rd) con ΔP = R·Q²;
  // ventilador con curva P = P0·(1 − (Q/Qmax)²). En serie las R se suman; en paralelo se suman las conductancias 1/√R.
  const SIM = { Rm: 0.06, Rb: 0.12, Rt: 1, Rd: [0, 3, 40], P0: 1, Qmax: 2.6, st: new Array(8).fill(0) };
  const cond = R => 1 / Math.sqrt(R), par = (...R) => 1 / Math.pow(R.reduce((a, r) => a + cond(r), 0), 2);
  const byB = [0, 1, 2, 3].map(b => T.map((t, i) => t.b === b ? i : -1).filter(i => i >= 0));
  function solve(st = SIM.st) {
    const Rt = st.map(k => SIM.Rt + SIM.Rd[k]), Rpar = byB.map(ix => par(...ix.map(i => Rt[i]))), Rbr = Rpar.map(r => SIM.Rb + r);
    const Req = new Array(4); Req[3] = Rbr[3]; for (let b = 2; b >= 0; b--) Req[b] = par(Rbr[b], SIM.Rm + Req[b + 1]);
    const Rsys = SIM.Rm + Req[0];
    // Punto de operación: R_sys·Q² = P0·(1 − (Q/Qmax)²); se resuelve por iteración (punto fijo amortiguado)
    let Q = SIM.Qmax / 2; for (let k = 0; k < 60; k++) Q = 0.5 * Q + 0.5 * Math.sqrt(SIM.P0 * (1 - Math.min(0.999, (Q / SIM.Qmax) ** 2)) / Rsys);
    const q = new Array(8); let Qin = Q, Pn = Req[0] * Q * Q;
    for (let b = 0; b < 4; b++) {
      const Qb = b === 3 ? Qin : Math.sqrt(Pn / Rbr[b]), Pt = Rpar[b] * Qb * Qb;
      byB[b].forEach(i => { q[i] = Math.sqrt(Pt / Rt[i]); });
      Qin -= Qb; if (b < 3) Pn -= SIM.Rm * Qin * Qin;
    }
    return q;
  }
  const QD = solve(new Array(8).fill(0)); // caudal de «diseño»: todas las compuertas abiertas (ilustrativo)
  const simApply = () => { const q = solve(); T.forEach((t, i) => { t.rt = q[i] / QD[i]; t.angT = [0, 0.5, 0.95][SIM.st[i]]; }); };
  const sim = { flows: () => solve().map((v, i) => v / QD[i]), set(i, k) { SIM.st[i] = k; simApply(); }, reset() { SIM.st.fill(0); simApply(); } };
  let cmp = null; // comparación de métodos (contador doble)
  function onClick(ray, st) {
    if (st.id !== 'E2' || cmp) return;
    const hit = ray.intersectObjects(T.flatMap(t => [t.neck, t.diff]), true).find(h => h.object.userData.term !== undefined);
    if (hit) { const i = hit.object.userData.term; sim.set(i, (SIM.st[i] + 1) % 3); }
  }
  // Etiquetas de las escenas (pocas, para que quepan a 1366)
  const LS = {
    filtroE: label(v3(-14.4, Y + 1.1, 0), 'Filtro'), fase1: label(v3(-12.6, Y + 2.6, 0), '', { cls: 'amber' }),
    clic: label(v3(BX[2], TY + 0.9, Z), `${il}Clic: compuerta abierta / media / cerrada`, { cls: 'amber' }),
    simS: label(v3(BX[1], 2.4, -Z), `${il}Simulación ilustrativa · sin valores`, { cls: 'amber' }),
  };
  Object.assign(CAM, { E1: [-10, 16, 24, -4, 1.2, 0], E2: [-15, 13, 17, 3, 1.0, 0], E3: [-14, 11, 15, 3, 2.5, 0], E4: [-11, 14, 22, -5, 1.5, 0] });
  Object.assign(LBL, { E1: [LS.filtroE, LS.fase1, L.vent, L.banda, L.barra], E2: [L.banda, L.barra, LS.clic, LS.simS], E3: [L.estado, L.comp, L.vent], E4: [L.vfd, L.vav, L.ducto] });
  const scEnter = st => {
    if (st.id === 'E2') { cmp = null; sim.reset(); T.forEach(t => { t.r = t.rt; }); const b = document.getElementById('cmpBtn'); if (b) b.onclick = () => { cmp = { t0: performance.now() }; document.querySelectorAll('.cmprow').forEach(r => r.hidden = false); }; }
    if (st.id === 'E1') { filt.material = mat.filterDirty; T.forEach((t, i) => { t.r = t.rt = R0[i]; }); }
    if (st.id === 'E3') { userSpd = false; const sp = document.getElementById('spd'), b = document.getElementById('spd80'); if (sp) { sp.oninput = () => { userSpd = true; laws(); }; b.onclick = () => { userSpd = true; sp.value = 80; laws(); }; laws(); } }
  };
  let userSpd = false;
  const scTick = (dt, t, st) => {
    if (st.id === 'E1') { // filtro sucio → limpio; luego barras medido/diseño y franja de ±5 %; se balancean; bucle de 48 s
      const u = t % 48; filt.material = u < 7 ? mat.filterDirty : mat.filterClean;
      const showB = u > 10; T.forEach((tt, i) => { tt.bar.visible = tt.band.visible = showB; tt.rt = u < 22 ? R0[i] : 1 + [0.01, -0.02, 0.015, -0.01, 0.02, -0.015, 0.01, 0][i]; });
      LS.fase1.set(`<span class="st il">Ilustrativo</span>${u < 7 ? 'Filtro sucio' : u < 10 ? 'Filtro limpio' : u < 22 ? 'Antes del balanceo' : 'Balanceada: todas en la franja'}`);
    }
    if (st.id === 'E2' && cmp) { // contador doble: proporción (14) y flujo progresivo (10) avanzan en paralelo
      const tc = (performance.now() - cmp.t0) / 1000, kp = Math.min(14, Math.floor(tc / 1.4)), kf = Math.min(10, Math.floor(tc / 1.4));
      const f = PROP[kp]; T.forEach((tt, i) => { tt.rt = f.r[i]; tt.angT = f.ang[i]; });
      const put = (k, n, m) => { const i = document.querySelector(`[data-cmp="${k}"]`), b = document.querySelector(`[data-cmpn="${k}"]`); if (i) i.style.width = (n / 14 * 100) + '%'; if (b) b.textContent = `${n} de ${m}`; };
      put('p', kp, 14); put('f', kf, 10);
      if (tc > 14 * 1.4 + 5) { cmp = null; sim.reset(); }
    }
    if (st.id === 'E3') { // compuertas de casi cerradas a abiertas mientras baja la velocidad; bucle de 40 s
      const open = (t % 40) > 14; T.forEach(tt => tt.angT = open ? 0 : 0.85);
      if (!userSpd) { const sp = document.getElementById('spd'); if (sp) { const v = open ? 80 : 100; if (+sp.value !== v) { sp.value = v; laws(); } } }
      L.estado.set(`<span class="st il">Ilustrativo</span>${open ? 'Compuertas abiertas · menor velocidad' : 'Compuertas casi cerradas · ventilador rápido'}<small>mismo caudal en los terminales</small>`);
    }
    if (st.id === 'E4') { const on = (t % 40) > 3; vfd.visible = on; vavs.forEach(v => v.visible = on); fanT = on ? 0.85 + 0.08 * Math.sin(t * 0.6) : 1; }
  };
  const steps = [...SC6.map(s => ({ ...s, cam: CAM[s.id], labels: LBL[s.id] || [] })), ...M6.steps.map(s => ({ ...s, level: 'PR', cam: CAM[s.id], labels: LBL[s.id] || [] }))];
  // Miniatura para el inicio: la misma geometría (correa corregida incluida), sin piso, barras ni objetos de pasos específicos
  function mini() {
    const m = g.clone(true), drop = [];
    m.traverse(o => { if (/^(piso|barra_relacion|franja_5|variador|caja_vav_\d|sonda_referencia|codo|anemometro)$/.test(o.name)) drop.push(o); });
    drop.forEach(o => o.parent.remove(o)); m.visible = true;
    m.getObjectByName('filtro').material = mat.filterClean;
    m.traverse(o => { if (o.isInstancedMesh && o.name === 'particulas_aire') o.instanceMatrix = pim.instanceMatrix; }); // comparte el movimiento del aire
    return { group: m, wheel: m.getObjectByName('rodete') };
  }
  const air = dt => stepParticles(dt, 1);
  return { group: g, ...M6.stop, note: M6.note, refs: M6.refs, steps, enter, tick, mini, air, onClick, sim, setRestart(fn) { stopRef.t0 = fn; } };
}
