// Parada 4 · M11: a la izquierda, un chiller enfriado por agua genérico (condensador de tubos y coraza, evaporador,
// compresor y torre de enfriamiento) con un corte ampliado de un tubo del condensador; a la derecha, aparte, un
// circuito de refrigeración por compresión (compresor, condensador, filtro secador, válvula de expansión, evaporador).
// Toda la geometría es ilustrativa; el texto está en content-m11.js.
import { M11, SC11 } from 'app/content-m11.js';

export function buildM11({ THREE, label }) {
  const g = new THREE.Group(); g.name = 'parada_4_m11';
  const M = (c, o = {}) => new THREE.MeshStandardMaterial({ color: c, roughness: 0.65, metalness: 0.2, ...o });
  const C = {
    floor: M(0x252A2F, { roughness: 1 }), slab: M(0x5A646D), shell: M(0x5F8FA8, { metalness: 0.35, roughness: 0.45 }), wbox: M(0x4E7C93, { metalness: 0.35 }), comp: M(0x3A424A),
    tower: M(0xD5DCE2), fan: M(0x3A424A), water: M(0x3FA7C9, { emissive: 0x0D2E3A }), copper: M(0xC07A4A, { metalness: 0.6, roughness: 0.35 }),
    wall: M(0xC07A4A, { metalness: 0.55, roughness: 0.4, side: THREE.DoubleSide }), coil: M(0x8F9AA4), fin: M(0xB8C2CA), brass: M(0xD9A441, { metalness: 0.6, roughness: 0.35 }),
    drier: M(0x6E7A85), oil: M(0xE3A857, { emissive: 0x5A3A0A }), xd: M(0xE6EBEF), gaugeF: M(0x8F9AA4), gauge: M(0xE5534B, { emissive: 0x3A1210 }), divider: new THREE.MeshBasicMaterial({ color: 0xD5DCE2, transparent: true, opacity: 0.08, depthWrite: false, side: THREE.DoubleSide }),
    hshell: new THREE.MeshStandardMaterial({ color: 0x3A424A, transparent: true, opacity: 1, roughness: 0.6 }),
  };
  const v3 = (x, y, z) => new THREE.Vector3(x, y, z), UP = v3(0, 1, 0);
  const box = (w, h, d, m, x, y, z, parent = g, name = '') => { const o = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), m); o.position.set(x, y, z); o.name = name; parent.add(o); return o; };
  const cylX = (r, len, m, x, y, z, parent = g, name = '') => { const o = new THREE.Mesh(new THREE.CylinderGeometry(r, r, len, 32), m); o.rotation.z = Math.PI / 2; o.position.set(x, y, z); o.name = name; parent.add(o); return o; };
  const cylY = (r, h, m, x, y, z, parent = g, name = '') => { const o = new THREE.Mesh(new THREE.CylinderGeometry(r, r, h, 28), m); o.position.set(x, y, z); o.name = name; parent.add(o); return o; };
  const seg = (a, b, r, m, parent) => { const d = b.clone().sub(a), l = d.length(); const o = new THREE.Mesh(new THREE.CylinderGeometry(r, r, l, 10), m); o.position.copy(a).add(b).multiplyScalar(0.5); o.quaternion.setFromUnitVectors(UP, d.normalize()); parent.add(o); return o; };
  const tube = (pts, r, m, parent = g) => { for (let i = 0; i < pts.length - 1; i++) seg(pts[i], pts[i + 1], r, m, parent); for (let i = 1; i < pts.length - 1; i++) { const j = new THREE.Mesh(new THREE.SphereGeometry(r, 10, 8), m); j.position.copy(pts[i]); parent.add(j); } };
  const poly = pts => { const sg = []; let L = 0; for (let i = 0; i < pts.length - 1; i++) { const l = pts[i].distanceTo(pts[i + 1]); sg.push({ a: pts[i], b: pts[i + 1], l }); L += l; }
    return { L, at(u, out) { let d = ((u % 1) + 1) % 1 * L; for (const s of sg) { if (d <= s.l) return out.copy(s.a).lerp(s.b, s.l ? d / s.l : 0); d -= s.l; } return out.copy(pts[pts.length - 1]); } }; };
  const tm = new THREE.Object3D(), pv = v3(0, 0, 0);
  // Pseudoaleatorio con semilla: la escena es idéntica en cada carga
  let seed = 7; const rnd = () => (seed = (seed * 16807) % 2147483647) / 2147483647;

  const fl = box(42, 0.1, 22, C.floor, 0, -0.05, -1, g, 'piso'); fl.receiveShadow = true;

  // ---------- Lado del agua: chiller enfriado por agua y torre de enfriamiento ----------
  const XC = -9.5;
  box(8.4, 0.3, 2.6, C.slab, XC, 0.15, 0, g, 'base_chiller');
  cylX(0.75, 6.4, C.shell, XC, 1.15, 0, g, 'evaporador_chiller');
  const cond = cylX(0.8, 6.4, C.shell, XC, 2.85, 0, g, 'condensador_tubos_y_coraza');
  [XC - 3.45, XC + 3.45].forEach(x => cylX(0.95, 0.5, C.wbox, x, 2.85, 0, g, 'caja_de_agua'));
  box(1.8, 1.1, 1.3, C.comp, XC, 4.1, 0, g, 'compresor_chiller'); cylX(0.45, 1.2, C.comp, XC + 1.4, 4.1, 0, g, 'motor_compresor');
  box(4.5, 4.6, 4.5, C.tower, XC, 2.6, -9, g, 'torre_enfriamiento'); cylY(1.6, 0.8, C.tower, XC, 5.3, -9, g, 'chimenea_torre');
  const tfan = new THREE.Group(); tfan.position.set(XC, 5.6, -9); g.add(tfan);
  for (let k = 0; k < 4; k++) { const b = box(2.8, 0.06, 0.36, C.fan, 0, 0, 0, tfan); b.rotation.y = k * Math.PI / 4; }
  const wA = [v3(XC - 2.25, 1.0, -6.75), v3(XC - 4.6, 1.0, -6.75), v3(XC - 4.6, 1.0, 0), v3(XC - 4.6, 2.85, 0), v3(XC - 3.7, 2.85, 0)];
  const wB = [v3(XC + 3.7, 2.85, 0), v3(XC + 4.6, 2.85, 0), v3(XC + 4.6, 4.6, 0), v3(XC + 4.6, 4.6, -9), v3(XC + 2.25, 4.6, -9)];
  tube(wA, 0.2, C.water); tube(wB, 0.2, C.water);
  const wLoop = poly([...wA, v3(XC + 3.7, 2.85, 0), ...wB, v3(XC, 1.0, -9), wA[0]]); // por los tubos del condensador y la torre
  const NW = 40, wp = new THREE.InstancedMesh(new THREE.SphereGeometry(0.12, 8, 6), new THREE.MeshBasicMaterial({ color: 0x9FE3F5 }), NW); wp.userData.noShadow = true; wp.name = 'particulas_agua'; g.add(wp);
  let wT = 0; const stepWater = dt => { wT += dt * 0.045; for (let i = 0; i < NW; i++) { wLoop.at(wT + i / NW, pv); tm.position.copy(pv); tm.scale.setScalar(1); tm.updateMatrix(); wp.setMatrixAt(i, tm.matrix); } wp.instanceMatrix.needsUpdate = true; };
  // Transductores sobre la tubería de agua de condensación (vista dividida y miniatura)
  const xdPipe = new THREE.Group(); xdPipe.name = 'transductores_tuberia'; g.add(xdPipe);
  [0.2, -2.2, -4.6].forEach(z => { cylY(0.16, 0.42, C.xd, XC + 4.6 + 0.34, 3.6, z, xdPipe, 'transductor').rotation.z = Math.PI / 2; });
  // Indicador de consumo del compresor: sin escala ni valores
  box(0.5, 3.0, 0.08, C.gaugeF, XC + 5.6, 4.6, 1.2, g, 'marco_indicador'); const gFill = box(0.38, 2.8, 0.1, C.gauge, XC + 5.6, 3.2, 1.22, g, 'indicador_consumo');
  gFill.geometry.translate(0, 1.4, 0); gFill.position.y = 3.2;

  // ---------- Corte ampliado de un tubo del condensador (lupa ilustrativa) ----------
  const lupa = new THREE.Group(); lupa.name = 'corte_tubo_ampliado'; lupa.position.set(XC, 7.4, 3.6); g.add(lupa);
  const R = 1.55, LEN = 7, TS = 0.53 + 0.35 * Math.PI, TL = 1.3 * Math.PI; // la abertura del corte mira hacia la cámara
  const wall = new THREE.Mesh(new THREE.CylinderGeometry(R, R, LEN, 64, 1, true, TS, TL), C.wall); wall.rotation.z = Math.PI / 2; wall.name = 'pared_tubo'; lupa.add(wall);
  const callout = new THREE.Line(new THREE.BufferGeometry().setFromPoints([v3(XC + 1.5, 3.65, 0.8), v3(XC + 1.5, 5.9, 3.0)]), new THREE.LineDashedMaterial({ color: 0xE3A857, dashSize: 0.25, gapSize: 0.18 }));
  callout.computeLineDistances(); g.add(callout);
  const onWall = (th, x, rr, out) => out.set(x, Math.sin(th) * rr, Math.cos(th) * rr); // punto sobre la pared (coordenadas de la lupa)
  // Depósitos: tres capas (sarro, óxido, biofilm) que crecen desde la pared hacia el centro
  const LAYERS = [0xD8C9A0, 0xB5651D, 0x6FA84F], NL = 120, dep = new THREE.InstancedMesh(new THREE.DodecahedronGeometry(0.11, 0), M(0xffffff, { roughness: 0.9, metalness: 0 }), NL * 3);
  dep.name = 'depositos'; dep.userData.noShadow = true; lupa.add(dep);
  const D = [];
  for (let l = 0; l < 3; l++) for (let i = 0; i < NL; i++) {
    const th = TS + rnd() * TL, x = -LEN / 2 + 0.2 + rnd() * (LEN - 0.4), rr = R - 0.08 - l * 0.13 - rnd() * 0.04;
    D.push({ th, x, rr, l, delay: l * 0.28 + rnd() * 0.25, det: 3 + rnd() * 10, sc: 0.8 + rnd() * 0.6, rot: rnd() * 6 });
    dep.setColorAt(l * NL + i, new THREE.Color(LAYERS[l]));
  }
  const setDep = (grow, t, cleaning) => { // grow 0–1: espesor de la capa; cleaning: tiempo de la limpieza (o −1)
    D.forEach((d, i) => {
      let s = Math.max(0, Math.min(1, (grow - d.delay) / 0.35)) * d.sc;
      onWall(d.th, d.x, d.rr, pv);
      if (cleaning >= 0 && cleaning > d.det) { const u = Math.min(1, (cleaning - d.det) / 1.6); pv.multiplyScalar(1 - 0.6 * u); pv.x = d.x + u * 2.5; s *= 1 - u; } // se desprende y sigue con el agua
      d.cur = s; tm.position.copy(pv); tm.rotation.set(d.rot, d.rot * 0.7, 0); tm.scale.setScalar(s); tm.updateMatrix(); dep.setMatrixAt(i, tm.matrix);
    });
    dep.instanceMatrix.needsUpdate = true; tm.rotation.set(0, 0, 0);
  };
  if (dep.instanceColor) dep.instanceColor.needsUpdate = true;
  // Agua dentro del tubo (bucle)
  const NI = 36, inW = new THREE.InstancedMesh(new THREE.SphereGeometry(0.09, 8, 6), new THREE.MeshBasicMaterial({ color: 0x9FE3F5 }), NI); inW.userData.noShadow = true; inW.name = 'agua_tubo'; lupa.add(inW);
  const IW = Array.from({ length: NI }, () => ({ y: (rnd() - 0.5) * 1.6, z: (rnd() - 0.5) * 1.6, o: rnd() }));
  let iT = 0; const stepIn = dt => { iT += dt * 0.12; IW.forEach((p, i) => { tm.position.set(-LEN / 2 + ((iT + p.o) % 1) * LEN, p.y, p.z); tm.scale.setScalar(1); tm.updateMatrix(); inW.setMatrixAt(i, tm.matrix); }); inW.instanceMatrix.needsUpdate = true; };
  // Transductores sobre el tubo ampliado, ondas y microburbujas junto a la pared (E2)
  const XTH = 2.6, XDIR = v3(0, Math.sin(XTH), Math.cos(XTH)); // transductores sobre la pared, detrás y arriba
  const xdT = [-2.2, 0, 2.2].map(x => { const o = cylY(0.22, 0.5, C.xd, 0, 0, 0, lupa, 'transductor'); onWall(XTH, x, R + 0.24, o.position); o.quaternion.setFromUnitVectors(UP, XDIR); return { o, x, th: XTH }; });
  const waveM = new THREE.MeshBasicMaterial({ color: 0xBFE7F8, transparent: true, opacity: 0.0, depthWrite: false, side: THREE.DoubleSide });
  const waves = []; xdT.forEach(t => { for (let k = 0; k < 3; k++) { const w = new THREE.Mesh(new THREE.SphereGeometry(1, 20, 12, 0, Math.PI * 2, 0, Math.PI / 2), waveM.clone()); onWall(t.th, t.x, R, w.position); w.quaternion.setFromUnitVectors(UP, XDIR.clone().negate()); w.visible = false; w.userData.noShadow = true; lupa.add(w); waves.push({ w, k }); } });
  const NB = 70, bub = new THREE.InstancedMesh(new THREE.SphereGeometry(0.08, 10, 8), new THREE.MeshBasicMaterial({ color: 0xFFFFFF, transparent: true, opacity: 0.9 }), NB); bub.userData.noShadow = true; bub.name = 'microburbujas'; lupa.add(bub);
  const BB = Array.from({ length: NB }, () => ({ th: TS + rnd() * TL, x: -LEN / 2 + 0.3 + rnd() * (LEN - 0.6), o: rnd() }));
  let bubOn = false;
  const setBub = (on, t) => { bubOn = on; BB.forEach((b, i) => { const u = (t * 1.3 + b.o) % 1; const s = !on ? 0 : u < 0.85 ? 0.4 + u : 1.6 * (1 - (u - 0.85) / 0.15); onWall(b.th, b.x, R - 0.75, pv); tm.position.copy(pv); tm.scale.setScalar(Math.max(0, s)); tm.updateMatrix(); bub.setMatrixAt(i, tm.matrix); }); bub.instanceMatrix.needsUpdate = true; }; // crece e implota
  setBub(false, 0);

  // ---------- Lado del refrigerante: circuito de compresión ----------
  const XR = 9.5;
  const hcomp = cylY(0.8, 1.8, C.hshell, XR - 3.5, 1.05, 2, g, 'compresor'); cylY(0.82, 0.12, C.comp, XR - 3.5, 1.98, 2, g);
  const sump = cylY(0.7, 0.55, C.oil, XR - 3.5, 0.45, 2, g, 'aceite_compresor');
  const coilBox = (x, y, z, name) => { const c = new THREE.Group(); c.position.set(x, y, z); c.name = name; g.add(c); box(3.4, 2.1, 0.5, C.coil, 0, 0, 0, c, name); for (let i = 0; i < 16; i++) box(0.04, 2.0, 0.6, C.fin, -1.6 + i * 0.21, 0, 0, c); return c; };
  box(10.4, 0.2, 9, C.slab, XR + 0.6, 0.1, 0, g, 'base_circuito');
  const condR = coilBox(XR + 1, 3.6, 3.2, 'condensador'), evapR = coilBox(XR + 1, 1.35, -3.0, 'evaporador');
  const cfan = new THREE.Mesh(new THREE.CylinderGeometry(0.85, 0.85, 0.12, 28), C.fan); cfan.rotation.x = Math.PI / 2; cfan.position.set(XR + 1, 3.6, 3.55); g.add(cfan);
  const drier = cylX(0.2, 0.9, C.drier, XR + 4.2, 1.7, 1.2, g, 'filtro_secador');
  const txv = box(0.36, 0.36, 0.36, C.brass, XR + 4.2, 1.35, -1.4, g, 'valvula_expansion');
  const rLoop = [v3(XR - 3.5, 2.05, 2), v3(XR - 3.5, 3.6, 2), v3(XR - 0.7, 3.6, 3.2), v3(XR + 2.7, 3.6, 3.2), v3(XR + 4.2, 3.6, 3.2), v3(XR + 4.2, 1.7, 3.2), v3(XR + 4.2, 1.7, 1.2), v3(XR + 4.2, 1.35, -1.4), v3(XR + 4.2, 1.35, -3.0), v3(XR + 2.7, 1.35, -3.0), v3(XR - 0.7, 1.35, -3.0), v3(XR - 3.5, 1.35, -3.0), v3(XR - 3.5, 1.35, 1.2), v3(XR - 3.5, 1.2, 1.2)];
  tube(rLoop.slice(0, 3), 0.1, C.copper); tube(rLoop.slice(3, 9), 0.1, C.copper); tube(rLoop.slice(9), 0.1, C.copper);
  const lines = g.children.filter(o => o.isMesh && o.material === C.copper);
  const rPath = poly(rLoop);
  const NR = 48, rp = new THREE.InstancedMesh(new THREE.SphereGeometry(0.1, 8, 6), new THREE.MeshBasicMaterial({ color: 0xffffff }), NR); rp.userData.noShadow = true; rp.name = 'particulas_refrigerante'; g.add(rp);
  const cRef = new THREE.Color(0xD5DCE2), cOil = new THREE.Color(0xF2C14E);
  for (let i = 0; i < NR; i++) rp.setColorAt(i, i % 4 === 0 ? cOil : cRef); // una fracción del aceite circula con el refrigerante
  let rT = 0; const stepRef = dt => { rT += dt * 0.05; for (let i = 0; i < NR; i++) { rPath.at(rT + i / NR, pv); tm.position.copy(pv); tm.scale.setScalar(1); tm.updateMatrix(); rp.setMatrixAt(i, tm.matrix); } rp.instanceMatrix.needsUpdate = true; };
  // Nanopartículas en el aceite del compresor (puntos brillantes, sin escala)
  const NN = 60, nano = new THREE.InstancedMesh(new THREE.SphereGeometry(0.035, 6, 4), new THREE.MeshBasicMaterial({ color: 0xFFF4D6 }), NN); nano.userData.noShadow = true; nano.name = 'nanoparticulas'; g.add(nano);
  const NP = Array.from({ length: NN }, () => ({ a: rnd() * 6.28, r: rnd() * 0.62, y: rnd() * 0.45, o: rnd() * 6.28 }));
  const stepNano = t => { NP.forEach((p, i) => { tm.position.set(XR - 3.5 + Math.cos(p.a + t * 0.6) * p.r, 0.22 + p.y + Math.sin(t * 3 + p.o) * 0.03, 2 + Math.sin(p.a + t * 0.6) * p.r); tm.scale.setScalar(1); tm.updateMatrix(); nano.setMatrixAt(i, tm.matrix); }); nano.instanceMatrix.needsUpdate = true; };
  stepNano(0);
  // Resaltado del aceite (E3): ámbar en cada componente
  const GLOW = { cond: M(0x8F9AA4, { emissive: 0xE3A857, emissiveIntensity: 0.25 }), evap: M(0x8F9AA4, { emissive: 0xE3A857, emissiveIntensity: 0.5 }), drier: M(0x6E7A85, { emissive: 0xE3A857, emissiveIntensity: 0.35 }) };
  const oilGlow = (on) => {
    hcomp.material.opacity = on ? 0.35 : 1; hcomp.material.depthWrite = !on;
    condR.children[0].material = on ? GLOW.cond : C.coil; evapR.children[0].material = on ? GLOW.evap : C.coil;
    drier.material = on ? GLOW.drier : C.drier;
    lines.forEach(l => l.material = on ? C.oil : C.copper);
    nano.visible = on;
  };

  // Separación de la vista dividida (E4)
  const divider = new THREE.Mesh(new THREE.PlaneGeometry(0.01 + 22, 9), C.divider); divider.rotation.y = Math.PI / 2; divider.position.set(0, 4.5, -1); divider.visible = false; divider.name = 'division'; divider.userData.noShadow = true; g.add(divider);
  const divLine = box(0.06, 9, 0.06, M(0xE6EBEF, { emissive: 0x555555 }), 0, 4.5, 10, g, 'linea_division'); divLine.visible = false;

  // ---------- Etiquetas ----------
  const il = '<span class="st il">Ilustrativo</span>', si = '<span class="st si">Síntesis del informe</span>';
  const L = {
    lupa: label(v3(XC, 9.2, 3.6), `${il}Corte ampliado de un tubo del condensador`, { prio: true }),
    capas: label(v3(XC - 2.6, 6.2, 4.4), 'Sarro, óxido y biofilm', { down: true }),
    cond: label(v3(XC - 2.2, 2.85, 0.9), 'Condensador de tubos y coraza', { down: true }),
    gauge: label(v3(XC + 5.6, 6.2, 1.2), `${il}Consumo del compresor<small>sin escala ni valores</small>`),
    torre: label(v3(XC, 6.2, -9), 'Torre de enfriamiento'),
    xd: label(v3(XC + 2.2, 9.0, 2.6), 'Transductores'),
    ondas: label(v3(XC - 1.0, 6.6, 4.6), 'Ondas y microburbujas que implosionan junto a la pared', { down: true }),
    sueltos: label(v3(XC + 2.8, 7.0, 4.8), 'Depósitos que se desprenden y siguen con el agua', { down: true }),
    pComp: label(v3(XR - 3.5, 2.3, 2), 'Compresor · 50&nbsp;%', { cls: 'amber', prio: true }), pEvap: label(v3(XR + 2.2, 2.45, -3.0), 'Evaporador · 20&nbsp;%', { cls: 'amber' }),
    pCond: label(v3(XR + 1, 4.75, 3.2), 'Condensador · 10&nbsp;%', { cls: 'amber' }), pDrier: label(v3(XR + 4.2, 2.0, 1.2), 'Filtro secador · 10&nbsp;%', { cls: 'amber' }),
    pLin: label(v3(XR - 3.5, 1.35, -1.0), 'Mangueras y líneas · 10&nbsp;%', { cls: 'amber', down: true }),
    nano: label(v3(XR - 3.5, 0.3, 2.6), `${il}Nanopartículas en el lubricante`, { down: true }),
    agua: label(v3(XC + 4.2, 7.8, -1), `${si}Lado del agua<small>cavitación ultrasónica en los intercambiadores</small>`, { cls: 'cyan' }),
    refr: label(v3(XR - 1.5, 6.4, -1), `${si}Lado del refrigerante<small>nanolubricante en el circuito hermético</small>`, { cls: 'amber' }),
  };
  const CAM = { E1: [0, 11, 22, XC + 1, 4.6, 1.2], E2: [-4, 10.6, 16.5, XC + 0.4, 6.6, 3.6], E3: [20, 9, 15, XR + 0.8, 1.8, 0], E4: [0.5, 17, 34, 0.5, 2.6, -1] };
  Object.assign(CAM, { fouling: CAM.E1, cavitacion: CAM.E2, nano: CAM.E3, desafios: CAM.E3, comparacion: CAM.E4, panama: CAM.E4 });
  const LBL = { E1: [L.lupa, L.capas, L.cond, L.gauge, L.torre], E2: [L.lupa, L.xd, L.ondas, L.sueltos], E3: [L.pComp, L.pEvap, L.pCond, L.pDrier, L.pLin, L.nano], E4: [L.agua, L.refr] };
  Object.assign(LBL, { fouling: LBL.E1, cavitacion: LBL.E2, nano: LBL.E3, desafios: [L.nano, L.pComp], comparacion: LBL.E4, panama: LBL.E4 });
  const BASE = { fouling: 'E1', cavitacion: 'E2', nano: 'E3', desafios: 'E3', comparacion: 'E4', panama: 'E4' };

  let gauge = 0.3;
  function enter(st) {
    const id = BASE[st.id] || st.id;
    lupa.visible = callout.visible = id === 'E1' || id === 'E2';
    xdT.forEach(x => x.o.visible = id === 'E2'); waves.forEach(w => w.w.visible = false);
    xdPipe.visible = id === 'E4'; divider.visible = divLine.visible = id === 'E4';
    oilGlow(id === 'E3' || id === 'E4');
    setBub(false, 0);
    gauge = id === 'E2' ? 0.85 : 0.3;
    setDep(id === 'E2' ? 1.3 : 0, 0, -1);
  }
  function tick(dt, t, st) {
    const id = BASE[st.id] || st.id;
    tfan.rotation.y += dt * 4; stepWater(dt); stepRef(dt);
    if (id === 'E1' || id === 'E2') stepIn(dt);
    if (id === 'E1') { const gr = Math.min(1.3, Math.max(0, (t - 1.5) / 9)); setDep(gr, t, -1); gauge = 0.3 + 0.55 * Math.min(1, gr / 1.3); } // la capa crece una vez y se queda
    if (id === 'E2') { // limpieza: ondas y microburbujas entre los 2 y los 15 s; después queda el tubo limpio
      const on = t > 2 && t < 15, c = Math.max(-1, t - 2);
      setDep(1.3, t, c); setBub(on, t); gauge = 0.85 - 0.55 * Math.min(1, Math.max(0, (t - 3) / 11));
      waves.forEach(({ w, k }) => { w.visible = on; if (on) { const u = (t * 0.9 + k / 3) % 1; w.scale.setScalar(0.15 + u * 0.85); w.material.opacity = 0.28 * (1 - u); } });
    }
    if (id === 'E3' || id === 'E4') stepNano(t);
    gFill.scale.y += (gauge - gFill.scale.y) * Math.min(1, dt * 3);
  }
  const steps = [...SC11.map(s => ({ ...s, cam: CAM[s.id], labels: LBL[s.id] || [] })), ...M11.steps.map(s => ({ ...s, level: 'PR', cam: CAM[s.id], labels: LBL[s.id] || [] }))];
  function mini() {
    const m = g.clone(true), drop = [];
    m.traverse(o => { if (/^(piso|corte_tubo_ampliado|division|linea_division|nanoparticulas|transductores_tuberia)$/.test(o.name) || o.isLine) drop.push(o); });
    drop.forEach(o => o.parent && o.parent.remove(o)); m.visible = true;
    m.traverse(o => { if (o.isInstancedMesh && o.name === 'particulas_agua') o.instanceMatrix = wp.instanceMatrix; if (o.isInstancedMesh && o.name === 'particulas_refrigerante') o.instanceMatrix = rp.instanceMatrix; });
    return { group: m };
  }
  const probe = () => ({ deposits: D.filter(d => d.cur > 0.01).length, bubbles: bubOn }); // para la prueba de humo
  return { group: g, probe, ...M11.stop, note: M11.note, refs: M11.refs, steps, enter, tick, mini, air: dt => { stepWater(dt); stepRef(dt); } };
}
