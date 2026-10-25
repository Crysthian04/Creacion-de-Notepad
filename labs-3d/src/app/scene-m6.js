// Parada 1 · M6: unidad con filtro, serpentín y ventilador con correas; ducto principal, 4 ramales,
// 8 terminales con compuerta y difusor. Barras (relación medido/diseño, sin escala) con la franja de ±5 %.
// Toda la geometría es ilustrativa; el texto está en content-m6.js.
import { M6 } from 'app/content-m6.js';

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
  // Motor, poleas y correa
  const motor = new THREE.Mesh(new THREE.CylinderGeometry(0.38, 0.38, 0.8, 24), mat.casing); motor.rotation.x = Math.PI / 2; motor.position.set(-10.4, 0.45, 1.6); motor.name = 'motor'; g.add(motor);
  const pul = (y, z, r) => { const p = new THREE.Mesh(new THREE.CylinderGeometry(r, r, 0.12, 24), mat.pulley); p.rotation.x = Math.PI / 2; p.position.set(-10.4, y, z); g.add(p); return p; };
  const p1 = pul(0.45, 2.05, 0.22), p2 = pul(fanC.y, 0.55, 0.4);
  const beltG = new THREE.Group(); beltG.name = 'correa'; g.add(beltG);
  [[0.22, 0.4], [-0.22, -0.4]].forEach(([d1, d2]) => {
    const a = v3(-10.4 + d1 * 0, 0.45 + d1, 2.05), b = v3(-10.4, fanC.y + d2, 0.55);
    const len = a.distanceTo(b), seg = new THREE.Mesh(new THREE.BoxGeometry(0.06, len, 0.08), mat.belt);
    seg.position.copy(a).add(b).multiplyScalar(0.5); seg.lookAt(b); seg.rotateX(Math.PI / 2); beltG.add(seg);
  });
  const motorBase = box(1.0, 0.1, 1.0, mat.dark, -10.4, 0.05, 1.6, g);

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
      T.push({ b, z, x: bx, damp, diff, bar, band, r: 1, rt: 1, ang: 0, angT: 0, flowPath: [v3(-9.6, DY, 0), v3(bx, DY, 0), v3(bx, DY, z), v3(bx, TY - 0.3, z)] });
    });
  });
  // Ordenar del más cercano al más lejano (por longitud de recorrido)
  T.sort((a, b) => (a.x + Math.abs(a.z) * 0.01) - (b.x + Math.abs(b.z) * 0.01));
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
  const elbow = new THREE.Group(); elbow.visible = false; g.add(elbow);
  box(0.95, 0.95, 0.95, mat.elbow, -9.6, DY + 0.55, 0, elbow); box(1.6, 0.85, 0.95, mat.elbow, -10.6, DY + 0.55, 0, elbow);
  const vfd = box(0.5, 0.8, 0.3, mat.vfd, -11.6, 0.9, 1.9, g, 'variador'); vfd.visible = false;
  const vavs = BX.map((bx, i) => { const o = box(0.7, 0.6, 0.8, mat.vav, bx, DY, 1.4, g, `caja_vav_${i + 1}`); o.visible = false; return o; });
  const probe = box(0.12, 0.6, 0.12, mat.probe, 0, TY + 0.6, 0, g, 'sonda_referencia'); probe.visible = false;
  const anem = new THREE.Group(); anem.visible = false; g.add(anem);
  box(0.9, 0.5, 0.9, new THREE.MeshStandardMaterial({ color: 0x31363B, transparent: true, opacity: 0.85 }), 0, 0, 0, anem); box(0.08, 1.2, 0.08, mat.dark, 0, -0.85, 0, anem);
  const taps = [v3(-11.6, Y + 0.2, 0.55), v3(-9.6, DY - 0.2, 0.55)];

  // Etiquetas
  const il = '<span class="st il">Ilustrativo</span>';
  const L = {
    filtro: label(v3(-14.4, Y - 1.0, 0.9), 'Filtro', { down: true }),
    serp: label(v3(-12.8, Y + 1.15, 0), 'Serpentín'),
    vent: label(v3(-10.0, Y + 3.4, 0), 'Ventilador y descarga'),
    motor: label(v3(-10.4, 0.9, 1.6), 'Motor, poleas y correa', { down: true }),
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
    correa: label(v3(-10.4, 1.4, 1.3), `${il}Correas y poleas: estado, tensión y alineación`, { cls: 'amber' }),
  };
  const base = [L.filtro, L.serp, L.vent, L.ducto, L.comp, L.term];
  const net = [L.banda, L.barra];

  // Cámara por paso [posición, objetivo]
  const CAM = {
    red: [-19, 16, 18, 1, 1.5, 0], marco: [-15, 13, 17, 3, 1.0, 0], previas: [-6, 6, 11, -11.5, 1.8, 0],
    proporcion: [-15, 13, 17, 3, 1.0, 0], progresivo: [-15, 13, 17, 3, 1.0, 0], apertura: [-14, 11, 15, 3, 2.5, 0],
    leyes: [-6, 5, 9, -10.8, 1.8, 0], panama: [-17, 14, 17, 2, 2, 0], cierre: [-19, 16, 18, 1, 1.5, 0],
    nebb: [-15, 13, 17, 3, 1.0, 0], fugas: [-9, 9, 11, 2, 3.4, 0], correas: [-7, 3.2, 7, -10.6, 1, 1],
    presion: [-6, 5, 8, -10.8, 2.4, 0], medir: [-2, 5, 9, 1.0, 2.2, 3.2], efecto: [-6, 7, 10, -10.2, 3.2, 0],
    kleberg: [-19, 16, 18, 1, 1.5, 0], bogota: [-15, 13, 17, 3, 1.0, 0], normas: [-19, 16, 18, 1, 1.5, 0],
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
    elbow.visible = st.id === 'efecto'; vfd.visible = ['progresivo', 'panama'].includes(st.id); vavs.forEach(v => v.visible = st.id === 'panama');
    probe.visible = st.id === 'progresivo'; if (probe.visible) probe.position.set(T[0].x, TY + 0.6, T[0].z);
    anem.visible = st.id === 'medir'; if (anem.visible) anem.position.set(T[2].x, TY - 0.55, T[2].z);
    L.anem.anchor.set(T[2].x, TY - 0.85, T[2].z); L.sonda.anchor.set(T[0].x, TY + 1.0, T[0].z);
    const showBars = ['marco', 'proporcion', 'progresivo'].includes(st.id); // en Bogotá no hay valores por rejilla en el informe
    T.forEach(t => { t.bar.visible = t.band.visible = showBars; });
    if (st.id === 'proporcion' || st.id === 'progresivo') { T.forEach((t, i) => { t.r = t.rt = R0[i]; }); cnt(0); }
    if (st.id === 'previas') filt.material = mat.filterDirty;
    if (st.id === 'leyes') { const s = document.getElementById('spd'), b = document.getElementById('spd80'); if (s) { s.oninput = laws; b.onclick = () => { s.value = 80; laws(); }; laws(); } }
    setBars();
  }
  function laws() {
    const s = document.getElementById('spd'); if (!s) return; const n = s.value / 100;
    [1, 2, 3].forEach(k => { const el = document.querySelector(`[data-law="${k}"]`); if (el) el.style.width = (Math.pow(n, k) * 100).toFixed(1) + '%'; });
    document.getElementById('rot').classList.toggle('hot', Math.abs(s.value - 80) < 1);
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

  const steps = M6.steps.map(s => ({ ...s, cam: CAM[s.id], labels: LBL[s.id] || [] }));
  return { group: g, ...M6.stop, note: M6.note, refs: M6.refs, steps, enter, tick, setRestart(fn) { stopRef.t0 = fn; } };
}
