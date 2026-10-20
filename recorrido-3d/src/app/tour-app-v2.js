import * as THREE from 'three';
import { buildModel, H } from 'app/hvac-model.js';
import { buildTour } from 'app/tour-layers.js';
import { STAMP, ICON, STOPS, CARDS, inspectorHTML, THERMO, GLB_LABEL, FALLA, ANTES_DESPUES, PLAN_SPLIT, PLAN_TEXT, ROADMAP } from 'app/tour-content.js';
import { enrichSite } from 'app/site-v2.js';
import { createSky } from 'app/sky-v2.js';
import { coilProcess } from 'app/psychro.js';
import { FEATURES } from 'app/features.js';
import { buildDrone, buildAR, buildIRCamera } from 'app/tools-v25.js';
import { buildFalla } from 'app/falla-scene.js';

const stage = document.querySelector('three-d-stage');
await stage.ready;
const m = buildModel();
stage.setObject(m.root);
const scene = stage._scene, cam = stage._camera, ctl = stage._controls;
if (stage._glbBtn) { stage._glbBtn.textContent = GLB_LABEL; Object.assign(stage._toolbar.style, { flexDirection: 'column', alignItems: 'flex-end' }); }
cam.near = 0.1; cam.far = 600; cam.updateProjectionMatrix();
ctl.maxDistance = 120; ctl.minDistance = 6; ctl.maxPolarAngle = Math.PI * 0.495;
m.root.traverse(o => {
  if (!o.isMesh) return;
  const mat = o.material;
  if (mat.transparent || mat === m.M.thermal || mat === m.M.sensor) o.castShadow = false;
  if (mat.transparent) o.receiveShadow = false;
});
scene.add(new THREE.AmbientLight(0xffffff, 0.7));
const lamps = enrichSite(m);
scene.add(m.site);
const grid = new THREE.GridHelper(140, 70, 0x3A434C, 0x2A3036);
grid.position.y = 0.05; grid.material.transparent = true; grid.material.opacity = 0.3; scene.add(grid);
const fx = new THREE.Group(); fx.name = 'efectos'; scene.add(fx);
const sky = createSky({ scene, stage, m, lamps });
const T = buildTour(); Object.values(T.groups).forEach(g => { g.visible = false; scene.add(g); });
// Herramientas de las subventanas 5.2–5.4 (ubicaciones ilustrativas dentro del edificio)
const TOOLS = {
  '5.2': buildIRCamera(m.thermalPts),
  '5.3': buildAR(new THREE.Vector3(13.75, H + 0.26, 1.425), Math.PI / 2),
  '5.4': buildDrone(new THREE.Vector3(-10.5, H + 3.0, 2.0)),
};
Object.values(TOOLS).forEach(t => { t.group.visible = false; scene.add(t.group); });
const TA = { irCam: TOOLS['5.2'].A.cam, arTablet: TOOLS['5.3'].A.tablet, arAc: TOOLS['5.3'].A.ac, drone: TOOLS['5.4'].A.drone, droneLeak: TOOLS['5.4'].A.leak };

// Resplandor térmico
const cv = document.createElement('canvas'); cv.width = cv.height = 128;
const g2 = cv.getContext('2d'), rg = g2.createRadialGradient(64, 64, 0, 64, 64, 64);
rg.addColorStop(0, 'rgba(255,200,120,1)'); rg.addColorStop(0.25, 'rgba(255,106,43,.75)'); rg.addColorStop(1, 'rgba(255,60,20,0)');
g2.fillStyle = rg; g2.fillRect(0, 0, 128, 128);
const haloMat = new THREE.SpriteMaterial({ map: new THREE.CanvasTexture(cv), blending: THREE.AdditiveBlending, depthWrite: false, transparent: true });
const halos = m.thermalPts.map((p, i) => { const s = new THREE.Sprite(haloMat); s.name = 'halo_termico_' + i; s.position.copy(p); s.userData.base = i ? 1.0 : 1.6; fx.add(s); return s; });
// i.1 · escenas con personas para los 6 pasos de la falla
const FS = buildFalla({ m, halos, haloMat, irCam: TOOLS['5.2'] }); FS.group.visible = false; scene.add(FS.group);
let fallaRep = 0;

// Partículas
function mkPath(pts) { const L = [0]; for (let i = 1; i < pts.length; i++) L.push(L[i - 1] + pts[i].distanceTo(pts[i - 1])); return { pts, L, len: L[L.length - 1] }; }
function at(p, d, out) { let i = 1; while (i < p.L.length - 1 && p.L[i] < d) i++; const t = (d - p.L[i - 1]) / (p.L[i] - p.L[i - 1] || 1); return out.lerpVectors(p.pts[i - 1], p.pts[i], t); }
function flow(paths, color, r, spacing, speed, name) {
  const ps = paths.map(mkPath), items = [];
  ps.forEach(p => { const n = Math.max(2, Math.floor(p.len / spacing)), o = Math.random() * spacing; for (let i = 0; i < n; i++) items.push({ p, off: o + i * spacing }); });
  const im = new THREE.InstancedMesh(new THREE.SphereGeometry(r, 10, 8), new THREE.MeshBasicMaterial({ color }), items.length);
  im.name = name; im.frustumCulled = false; fx.add(im);
  return { im, items, speed };
}
const flows = [
  flow(m.supplyPaths, 0xD8FFF2, 0.085, 1.5, 1.8, 'particulas_suministro'),
  flow(m.returnPaths, 0xFFB27A, 0.085, 1.5, 1.8, 'particulas_retorno'),
];
const dataFlow = flow(m.dataLines.map(([a, b]) => [a, b]), 0x7FD6FF, 0.1, 2.2, 3.2, 'particulas_datos');
const arcFlow = flow(T.arcs, 0xFFF4D6, 0.13, 1.4, 3.0, 'particulas_recorrido'); arcFlow.im.visible = false;
const tmp = new THREE.Object3D();
function stepFlow(f, t) {
  f.items.forEach((it, i) => { at(it.p, (it.off + t * f.speed) % it.p.len, tmp.position); tmp.updateMatrix(); f.im.setMatrixAt(i, tmp.matrix); });
  f.im.instanceMatrix.needsUpdate = true;
}

// Etiquetas
const host = document.getElementById('labels'), A = m.anchors, B = T.A, labels = [];
function label(pos, title, sub, cls = '', mode = 'all', o = {}) {
  const el = document.createElement('div'); el.className = 'lbl ' + cls + (o.down ? ' down' : '') + (o.stops ? ' tour' : '');
  const t = o.icon ? `<span class="ic">${o.icon}<span>${title}</span></span>` : title;
  const bx = `<div class="box">${o.stamp ? STAMP[o.stamp] : ''}${t}${sub ? `<small>${sub}</small>` : ''}</div>`;
  const st = `<div class="stem" style="height:${o.stem ?? 16}px"></div>`;
  el.innerHTML = `${bx}${st}<div class="dot"></div>`;
  el.style.display = 'none';
  host.appendChild(el);
  labels.push({ el, pos, mode, stops: o.stops || ['g'], inside: !!o.inside, down: !!o.down, dx: o.dx || 0, stem0: o.stem ?? 16, prio: o.prio ?? 5, floor: cls === 'floor', bx: el.querySelector('.box'), st: el.querySelector('.stem') });
}
// Vista general (original + sellos)
label(A.chiller, 'Chiller enfriado por aire · 155 TR', 'Exterior · parte posterior izquierda', '', 'all', { stem: 34, prio: 2, stamp: 'real' });
label(A.thermal, 'Deterioro detectado por termografía', '(una sola inspección)', 'heat', 'all', { down: true, stem: 26, dx: 60, prio: 1, stamp: 'real' });
label(A.uma, '16 UMA en total', 'Distribución por piso ilustrativa', '', 'actual', { stem: 40, prio: 4, inside: true, stamp: 'real' });
label(A.split, 'Mini-split inverter · 12,000–60,000 BTU/h', 'Añadidos tras el diseño original', 'tag', 'all', { stem: 40, dx: -40, prio: 3, stamp: 'real' });
label(A.pump, 'Bombeo de agua helada', 'Configuración ilustrativa: el estudio no la detalla', 'wrap', 'all', { stem: 30, dx: 140, prio: 3, stamp: 'ilus' });
['Planta baja', 'Primer alto', 'Segundo alto'].forEach((t, i) => label(A.floors[i], t, '', 'floor', 'all', { stem: 0, prio: 6 }));
// i.2 · Antes / después: cada etiqueta aparece desde su etapa (INV3, p. 37)
let abStage = 0;
const atStage = (k, ...args) => { label(...args); labels[labels.length - 1].cond = () => abStage >= k; };
atStage(1, A.bms, 'BMS', 'Etapa 1 · integra los sensores', 'cyan', 'all', { stops: ['i.2'], stem: 10, prio: 1, stamp: 'ilus' });
atStage(2, A.ia, 'Detección de anomalías', 'Etapa 2', 'cyan', 'all', { stops: ['i.2'], down: true, stem: 10, prio: 1, stamp: 'ilus' });
atStage(3, A.bim, 'Modelo BIM del edificio', 'Etapa 3', 'cyan', 'all', { stops: ['i.2'], down: true, stem: 10, prio: 1, stamp: 'ilus' });
atStage(1, A.pilotLabel, 'Piloto en las UMA', 'Conviene empezar aquí', 'cyan', 'all', { stops: ['i.2'], stem: 24, prio: 2, stamp: 'ilus' });
atStage(1, A.sensorsUma, 'Sensores IoT (chiller y 16 UMA)', 'T suministro/retorno · ΔP filtros · corriente ventiladores', 'cyan wrap', 'all', { stops: ['i.2'], stem: 20, prio: 3, stamp: 'ilus' });
label(A.thermal, 'Deterioro en uniones de la tubería de agua fría', 'Una sola inspección termográfica', 'heat wrap', 'all', { stops: ['i.2'], stamp: 'real', down: true, stem: 30, dx: 70, prio: 1 });
labels[labels.length - 1].cond = () => abStage === 0;
// i.1 · la falla
label(A.thermal, 'Uniones con deterioro', 'Detectadas en la auditoría energética', 'heat', 'all', { stops: ['i'], stamp: 'real', down: true, stem: 30, dx: 80, prio: 1 });
labels[labels.length - 1].cond = () => fallaRep < 1 && falla.k !== 1 && falla.k !== 5;
const atStep = (ks, ...args) => { label(...args); labels[labels.length - 1].cond = () => ks.includes(falla.k); };
atStep([1], FS.A.cmms, 'CMMS · orden de trabajo', 'AF-UNION-01 · Estado: programada', '', 'all', { stops: ['i'], stamp: 'ilus', stem: 30, prio: 1 });
atStep([5], FS.A.cmms, 'CMMS · orden de trabajo', 'AF-UNION-01 · Estado: cerrada', '', 'all', { stops: ['i'], stamp: 'ilus', stem: 30, prio: 1 });
atStep([2], FS.A.lock, 'Candado y tarjeta', 'Técnico eléctrico · NFPA 70E', '', 'all', { stops: ['i'], stamp: 'ilus', stem: 40, dx: 60, prio: 1 });
atStep([2], FS.A.valve, 'Válvula de corte cerrada', 'Purga de presiones', '', 'all', { stops: ['i'], stamp: 'ilus', stem: 34, dx: -60, prio: 1 });
atStep([0], FS.A.insul, 'Aislamiento térmico (translúcido para ver la tubería)', '', '', 'all', { stops: ['i'], stamp: 'ilus', stem: 40, dx: -140, prio: 2 });
label(FS.A.insul, 'Aislamiento térmico (translúcido para ver la tubería)', '', '', 'all', { stops: ['5.2'], stamp: 'ilus', stem: 40, dx: -140, prio: 2 });
atStep([3], FS.A.repair, 'Se rehace la unión y su aislamiento', '', '', 'all', { stops: ['i'], stamp: 'ilus', stem: 60, dx: -150, prio: 1 });
label(A.thermal, 'Unión reparada', 'Sin anomalía en la nueva lectura', '', 'all', { stops: ['i'], stamp: 'resIlus', down: true, stem: 30, dx: 80, prio: 1 });
labels[labels.length - 1].cond = () => fallaRep >= 1 && (falla.k === 3 || falla.k === 4);
// Clima (vista general e integrada)
label(sky.radAnchor, 'Radiación solar sobre la fachada', 'Intensidad relativa', 'sun', 'all', { stops: ['g'], stamp: 'ilus', stem: 28, dx: 50, prio: 2 });
labels[labels.length - 1].cond = () => sky.S.active && !sky.S.night && sky.S.irr > 0.15 && sky.bestFace();
// Parada 1
const S = (s, x = {}) => Object.assign({ stops: [s], stamp: 'ilus' }, x);
label(B.tech, 'Técnico en el tablero del chiller', 'Guantes dieléctricos clase 00 · gafas de seguridad · calzado dieléctrico · ropa ignífuga contra arco (NFPA 70E)', 'wrap', 'all', S('1', { stem: 40, dx: 30, prio: 1 }));
label(B.roofTech, 'Técnico en la azotea', 'Arnés con línea de vida de doble amortiguador · casco con barboquejo de 4 puntos', 'wrap', 'all', S('1', { stem: 26, dx: 60, prio: 1 }));
label(B.tablero, 'NFPA 70E – arco eléctrico', 'Tablero del chiller', '', 'all', S('1', { down: true, stem: 44, dx: 70, prio: 2 }));
label(B.cyl, 'Cilindros · clase ASHRAE 34', '<span class="sw3" style="background:#D98FA6"></span>R-410A (A1)<span class="sw3" style="background:#9CC7E3"></span>R-32 (A2L)<span class="sw3" style="background:#C7392F"></span>R-290 (A3)<br>EPP: gafas herméticas · guantes criogénicos o de nitrilo grueso', '', 'all', S('1', { stem: 30, prio: 2 }));
// Parada 2
label(B.split2, 'Mini-split inverter', 'El edificio tiene mini-splits inverter de 12,000 a 60,000 BTU/h', 'wrap', 'all', S('2', { stamp: 'real', stem: 34, dx: 40, prio: 1 }));
// Parada 3
label(B.leak, 'Fuga de refrigerante', 'Más densa que el aire: se extiende a ras de piso', 'wrap', 'all', S('3', { stem: 26, dx: -90, prio: 1 }));
label(B.atmos, 'Atmósfera', 'Destino final de la emisión (GWP)', '', 'all', S('3', { stem: 16, prio: 2 }));
label(B.machine, 'Máquina recuperadora + cilindro', 'Recuperar → Reciclar → Regenerar', '', 'all', S('3', { stem: 30, dx: 60, prio: 1 }));
// Parada 4
label(B.uma3, 'UMA ilustrativa – caso de la INV5', '', '', 'all', S('4', { stem: 40, dx: 110, prio: 1 }));
label(B.bmsScreen, 'Pantalla BMS / EMS', 'Indicadores: EER · SEER · COP', '', 'all', S('4', { stem: 30, dx: 30, prio: 2 }));
label(B.audit, 'Auditoría energética · Ley 69 de 2012', '', '', 'all', S('4', { down: true, stem: 28, dx: 40, prio: 2 }));
label(B.iplv, 'IPLV en el chiller', 'Eficiencia a carga parcial', '', 'all', S('4', { stem: 30, prio: 1 }));
// Parada 5
label(A.chiller, 'Chiller enfriado por aire · 155 TR', '', '', 'all', S('5', { stamp: 'real', stem: 30, prio: 1 }));
label(A.uma, '16 UMA', 'En los 3 pisos', '', 'all', S('5', { stamp: 'real', stem: 40, prio: 2 }));
label(A.thermal, 'Deterioro en uniones de la tubería de agua fría', 'Detectado en una inspección termográfica', 'heat wrap', 'all', S('5', { stamp: 'real', down: true, stem: 30, dx: 70, prio: 1 }));
label(A.sensorsUma, 'Sensores IoT en chiller y UMA', 'T suministro/retorno · ΔP filtros · corriente ventiladores', 'cyan wrap', 'all', S('5', { stem: 26, prio: 2 }));
label(A.bms, 'Pantalla BMS', '', 'cyan', 'all', S('5', { stem: 12, prio: 1 }));
label(A.ia, 'Detección de anomalías', '(aprendizaje automático)', 'cyan', 'all', S('5', { down: true, stem: 12, prio: 1 }));
label(A.bim, 'Gemelo digital / BIM', '', 'cyan', 'all', S('5', { down: true, stem: 12, prio: 1 }));
label(A.pump, 'Bombeo de agua helada', 'Configuración ilustrativa: el estudio no la detalla', 'wrap', 'all', S('5', { stem: 30, dx: -40, prio: 3 }));
// 5.2 · Termografía
label(TOOLS['5.2'].A.cam, 'Cámara termográfica portátil', '', '', 'all', S('5.2', { stem: 26, dx: -60, prio: 2 }));
label(A.thermal, 'Deterioro en uniones de la tubería de agua fría', 'Detectado en una sola inspección termográfica', 'heat wrap', 'all', S('5.2', { stamp: 'real', down: true, stem: 30, dx: 70, prio: 1 }));
label(A.chiller, 'Chiller enfriado por aire · 155 TR', '', '', 'all', S('5.2', { stamp: 'real', stem: 30, prio: 3 }));
// 5.3 · Realidad aumentada (zonas con texto cualitativo que cambia con el ajuste)
const arZones = TOOLS['5.3'].ZONES.map(([nm], i) => { label(TOOLS['5.3'].A.zones[i], nm, '—', 'cyan', 'all', S('5.3', { stem: 18, prio: 1 })); return labels[labels.length - 1]; });
label(TOOLS['5.3'].A.sensors, 'Sensores IoT', '', 'cyan', 'all', S('5.3', { stem: 30, prio: 2 }));
label(TOOLS['5.3'].A.overlay, 'Datos superpuestos al espacio real', '', 'cyan', 'all', S('5.3', { stem: 22, prio: 3, down: true }));
label(TOOLS['5.3'].A.tablet, 'Control del sistema desde la tableta', '', '', 'all', S('5.3', { stem: 40, dx: 60, prio: 2 }));
// 5.4 · Dron en ductos
label(TOOLS['5.4'].A.drone, 'Rueda y vuela dentro del ducto', '', '', 'all', S('5.4', { stem: 30, prio: 1 }));
label(TOOLS['5.4'].A.lens, 'Cámara térmica', '', 'cyan', 'all', S('5.4', { stem: 40, dx: -70, prio: 2, down: true }));
label(TOOLS['5.4'].A.leak, 'Fuga detectada', 'Caso hipotético', 'heat', 'all', S('5.4', { stem: 34, dx: 70, prio: 1 }));
labels[labels.length - 1].cond = () => TOOLS['5.4'].S.detected;
// Vista integrada

const v = new THREE.Vector3(), vp = document.querySelector('.vp');
let sorted = null;
function placeLabels() {
  if (host.classList.contains('off')) return;
  const w = host.clientWidth, h = host.clientHeight, placed = [], hr = host.getBoundingClientRect();
  [...vp.querySelectorAll('.seg, .note, .hint, .k, .stlegend, #dock, .tnav, #plan:not([hidden])'), stage._toolbar].forEach(e => {
    const b = e.getBoundingClientRect();
    if (b.width && b.right > hr.left && b.left < hr.right && b.bottom > hr.top && b.top < hr.bottom)
      placed.push({ l: b.left - hr.left - 6, r: b.right - hr.left + 6, t: b.top - hr.top - 6, b: b.bottom - hr.top + 6 });
  });
  sorted = sorted || [...labels].sort((p, q) => p.prio - q.prio);
  sorted.forEach(l => {
    if (hoverMode && !l.floor) { l.el.style.display = 'none'; if (l.fb) { l.fb.el.style.display = 'none'; l.fb.on = false; } return; }
    if (l.hidden || (l.cond && !l.cond()) || (l.floor && currentView === 'superior') || (l.inside && shell === 'facade' && stop === 'g')) { l.el.style.display = 'none'; return; }
    v.copy(l.pos).project(cam);
    if (v.z > 1 || v.z < -1) { l.el.style.display = 'none'; return; }
    l.el.style.display = '';
    if (!l.bw) { l.bw = l.bx.offsetWidth; l.bh = l.bx.offsetHeight; }
    const x = (v.x * 0.5 + 0.5) * w, y = (-v.y * 0.5 + 0.5) * h, tail = l.floor ? 0 : 4, sh = l.bw * 0.42;
    let best = null;
    outer: for (const dn of (l.floor ? [false] : [l.down, !l.down])) for (let k = 0; k < 7; k++) {
      const stem = l.floor ? 0 : l.stem0 + k * 18;
      for (const d of [0, sh, -sh]) {
        const cx = Math.min(w - 8 - l.bw / 2, Math.max(8 + l.bw / 2, x + l.dx + d));
        const t = dn ? y + 1 + stem : y - l.bh - stem - tail;
        const r = { l: cx - l.bw / 2 - 4, r: cx + l.bw / 2 + 4, t: t - 3, b: t + l.bh + 3 };
        if (r.t >= 0 && r.b <= h && !placed.some(p => r.l < p.r && r.r > p.l && r.t < p.b && r.b > p.t)) { best = { cx, stem, r, dn }; break outer; }
      }
    }
    if (!best) { l.el.style.display = 'none'; if (stop !== 'g') fallback(l); return; }
    if (l.fb) { l.fb.el.style.display = 'none'; l.fb.on = false; }
    placed.push(best.r);
    if (l.st) l.st.style.height = best.stem + 'px';
    l.el.classList.toggle('down', best.dn);
    l.bx.style.transform = `translateX(${best.cx - x}px)`;
    l.el.style.transform = `translate(${x}px, ${y}px) translate(-50%, ${best.dn ? '-3px' : '-100%'})`;
  });
}
const remeasure = () => labels.forEach(l => { l.bw = 0; });
document.fonts && document.fonts.ready.then(remeasure);
addEventListener('resize', remeasure);

// Tarjetas acopladas + líneas guía
const dock = document.getElementById('dock'), leaders = document.getElementById('leaders'), NS = 'http://www.w3.org/2000/svg';
let docks = [];
const anchorOf = k => B[k] || A[k] || TA[k];
function buildDock(s) {
  closePop();
  dock.innerHTML = ''; leaders.innerHTML = ''; docks = []; labels.forEach(l => { l.fb = null; });
  (CARDS[s] || []).forEach(([html, k, cls]) => {
    const el = document.createElement('div'); el.className = 'card' + (cls ? ' ' + cls : ''); el.innerHTML = html; dock.appendChild(el);
    const ch = el.querySelector('.ch'), cb = document.createElement('div'); cb.className = 'cb';
    if (ch) { while (ch.nextSibling) cb.appendChild(ch.nextSibling); el.appendChild(cb); }
    const ln = document.createElementNS(NS, 'line'), c = document.createElementNS(NS, 'circle');
    ln.setAttribute('stroke', 'rgba(214,224,232,.5)'); ln.setAttribute('stroke-width', '1'); ln.setAttribute('stroke-dasharray', '3 3');
    c.setAttribute('r', '3.5'); c.setAttribute('fill', '#F1F4F6');
    if (!k) return;
    el.classList.add('anch'); leaders.append(ln, c); docks.push({ el, a: anchorOf(k), ln, c });
  });
  layoutDock(); fitDock(0);
}
// Pantallas bajas (1366×768): si las tarjetas no caben, solo una queda abierta y las demás se pliegan a su encabezado
function fitDock(open) {
  const cards = [...dock.children].filter(c => !c.classList.contains('mini') && c.querySelector('.cb'));
  cards.forEach(c => { c.classList.remove('fold'); const h = c.querySelector('.ch'); h.removeAttribute('role'); h.removeAttribute('tabindex'); h.removeAttribute('aria-expanded'); });
  if (cards.length < 2 || dock.scrollHeight - dock.clientHeight <= 8) return;
  cards.forEach((c, i) => {
    const h = c.querySelector('.ch');
    c.classList.toggle('fold', i !== open);
    h.setAttribute('role', 'button'); h.tabIndex = 0; h.setAttribute('aria-expanded', i === open);
  });
}
function unfold(h) {
  const cards = [...dock.querySelectorAll('.card .ch[role=button]')].map(x => x.parentElement), c = h.parentElement;
  if (!c.classList.contains('fold')) return;
  cards.forEach(x => { x.classList.toggle('fold', x !== c); x.querySelector('.ch').setAttribute('aria-expanded', x === c); });
}
dock.addEventListener('click', e => { const h = e.target.closest('.ch[role=button]'); if (h) unfold(h); });
dock.addEventListener('keydown', e => { const h = e.target.closest('.ch[role=button]'); if (h && (e.key === 'Enter' || e.key === ' ')) { unfold(h); e.preventDefault(); } });
function layoutDock() {
  const hr = vp.getBoundingClientRect(), tb = vp.querySelector('.top').getBoundingClientRect(), bb = vp.querySelector('.bottom').getBoundingClientRect();
  dock.style.top = (tb.bottom - hr.top + 12) + 'px';
  dock.style.height = Math.max(160, bb.top - tb.bottom - 24) + 'px';
}
function fallback(l) {
  if (!l.fb) {
    const el = document.createElement('div'); el.className = 'card mini'; el.innerHTML = l.bx.innerHTML; dock.appendChild(el);
    const ln = document.createElementNS(NS, 'line'), c = document.createElementNS(NS, 'circle');
    ln.setAttribute('stroke', 'rgba(214,224,232,.5)'); ln.setAttribute('stroke-width', '1'); ln.setAttribute('stroke-dasharray', '3 3');
    c.setAttribute('r', '3.5'); c.setAttribute('fill', '#F1F4F6'); leaders.append(ln, c);
    l.fb = { el, a: l.pos, ln, c, fbl: l }; docks.push(l.fb);
  }
  if (l.fb.on) return;
  l.fb.el.style.display = ''; l.fb.on = true;
  if (dock.scrollHeight - dock.clientHeight > 8 && !dock.querySelector('.card.fold')) fitDock(0);
  // Si aun así no cabe, la etiqueta se queda oculta en lugar de desbordar el panel de tarjetas
  if (dock.scrollHeight - dock.clientHeight > 8) { l.fb.el.style.display = 'none'; l.fb.on = false; }
}
function placeDock() {
  if (!docks.length) return;
  const hr = vp.getBoundingClientRect(), w = hr.width, h = hr.height, dr = dock.getBoundingClientRect();
  docks.forEach(d => {
    v.copy(d.a).project(cam);
    const cb = d.el.getBoundingClientRect();
    const vis = (!d.fbl || d.on) && v.z < 1 && v.z > -1 && cb.bottom > dr.top + 20 && cb.top < dr.bottom - 20;
    d.ln.style.display = d.c.style.display = vis ? '' : 'none';
    if (!vis) return;
    const x = (v.x * 0.5 + 0.5) * w, y = (-v.y * 0.5 + 0.5) * h, b = d.el.getBoundingClientRect();
    const x0 = b.right - hr.left, y0 = Math.min(Math.min(b.bottom, dr.bottom) - hr.top - 14, Math.max(Math.max(b.top, dr.top) - hr.top + 14, y));
    d.ln.setAttribute('x1', x0); d.ln.setAttribute('y1', y0); d.ln.setAttribute('x2', x); d.ln.setAttribute('y2', y);
    d.c.setAttribute('cx', x); d.c.setAttribute('cy', y);
  });
}

// Modo "al pasar": tarjetas y etiquetas ocultas; un punto por elemento y su contenido aparece al pasar el puntero (o fijo con clic)
const hots = document.createElement('div'); hots.id = 'hots'; host.appendChild(hots);
const pop = document.getElementById('pop'), hotMap = new Map(), HOVER_KEY = 'utp-recorrido-al-pasar';
let hoverMode = false, popKey = null, popPinned = false, popTimer = 0, popCards = [];
function hotGroups() {
  const g = new Map(), add = (pos, it) => { if (!g.has(pos)) g.set(pos, []); g.get(pos).push(it); };
  labels.forEach(l => {
    if (l.floor || l.hidden || (l.cond && !l.cond()) || (l.inside && shell === 'facade' && stop === 'g')) return;
    add(l.pos, { l, html: l.bx.innerHTML, cls: l.el.className });
  });
  docks.forEach(d => { if (!d.fbl) add(d.a, { card: d.el, html: d.el.innerHTML, cls: '' }); });
  return g;
}
function placeHots() {
  const on = hoverMode && !host.classList.contains('off'), w = vp.clientWidth, h = vp.clientHeight;
  // Agrupar los elementos cuyos anclajes están a menos de 1.6 m (p. ej., una tarjeta y una etiqueta sobre el mismo equipo).
  // Se agrupa en el modelo y no en pantalla para que el grupo no cambie mientras la cámara se mueve.
  const clusters = [];
  if (on) hotGroups().forEach((items, k) => {
    const c = clusters.find(c => c.k.distanceTo(k) < 1.6);
    if (c) c.items.push(...items); else clusters.push({ k, items: [...items] });
  });
  clusters.forEach(c => {
    v.copy(c.k).project(cam);
    c.vis = v.z < 1 && v.z > -1; c.x = (v.x * 0.5 + 0.5) * w; c.y = (-v.y * 0.5 + 0.5) * h;
  });
  const keys = new Set(clusters.map(c => c.k));
  hotMap.forEach((el, k) => { if (!keys.has(k)) el.style.display = 'none'; });
  clusters.forEach(({ k, x, y, items, vis }) => {
    let el = hotMap.get(k);
    if (!el) {
      el = document.createElement('button'); el.className = 'hot'; el.type = 'button'; hots.appendChild(el); hotMap.set(k, el);
      el.addEventListener('pointerenter', () => { if (!popPinned) openPop(k); });
      el.addEventListener('pointerleave', () => { if (!popPinned) schedClose(); });
      el.addEventListener('click', () => { if (popPinned && popKey === k) { closePop(); return; } openPop(k); popPinned = true; });
    }
    el._items = items; el._xy = [x, y];
    const tag = items.some(i => /st real/.test(i.html)) ? 'real' : items.some(i => /\bcyan\b/.test(i.cls)) ? 'cyan' : items.some(i => /\bheat\b/.test(i.cls)) ? 'heat' : '';
    el.className = 'hot ' + tag + (popKey === k ? ' on' : '');
    el.setAttribute('aria-label', items.map(i => (i.card ? i.card.querySelector('h4')?.textContent : i.l?.bx.textContent) || '').join(' · ').trim());
    el.style.display = vis ? '' : 'none';
    el.style.transform = `translate(${x}px, ${y}px)`;
  });
  if (popKey) {
    const el = hotMap.get(popKey);
    if (!on || !el || el.style.display === 'none') { closePop(); return; }
    const [x, y] = el._xy, pw = pop.offsetWidth, ph = pop.offsetHeight;
    const left = x + 18 + pw <= w - 8 ? x + 18 : Math.max(8, x - 18 - pw), top = Math.min(h - ph - 8, Math.max(8, y - 24));
    pop.style.transform = `translate(${left}px, ${top}px)`;
  }
}
function openPop(k) {
  clearTimeout(popTimer);
  if (popKey === k) return;
  closePop();
  const items = hotMap.get(k)?._items || [];
  items.forEach(i => {
    if (i.card) { i.card.classList.remove('fold'); popCards.push(i.card); pop.appendChild(i.card); }
    else { const c = document.createElement('div'); c.className = 'card mini'; c.innerHTML = i.html; pop.appendChild(c); }
  });
  popKey = k; pop.hidden = false;
}
function closePop() {
  clearTimeout(popTimer);
  popCards.forEach(c => dock.appendChild(c)); popCards = [];
  pop.innerHTML = ''; pop.hidden = true; popKey = null; popPinned = false;
}
const schedClose = () => { clearTimeout(popTimer); popTimer = setTimeout(closePop, 280); };
pop.addEventListener('pointerenter', () => clearTimeout(popTimer));
pop.addEventListener('pointerleave', () => { if (!popPinned) schedClose(); });
vp.addEventListener('pointermove', e => { if (popKey && !popPinned && !e.target.closest?.('.hot, #pop')) schedClose(); });
addEventListener('keydown', e => { if (e.key === 'Escape' && popKey) closePop(); });
function setHoverMode(on) {
  hoverMode = on; closePop();
  vp.classList.toggle('hover', on);
  const b = document.getElementById('tHover'); b.classList.toggle('on', on); b.textContent = on ? 'Tarjetas: al pasar' : 'Tarjetas: siempre';
  try { localStorage.setItem(HOVER_KEY, on ? '1' : '0'); } catch (e) {}
  if (stop !== 'g') buildDock(stop);
}
document.getElementById('tHover').onclick = () => setHoverMode(!hoverMode);

// Atenuación del resto del modelo
const shellSet = new Set(m.shell.mats.map(s => s.mat)), base = [], dimCache = new Map();
[m.root, m.site].forEach(r => r.traverse(o => { if (o.isMesh || o.isLine) base.push({ o, mat: o.material, cast: o.castShadow, site: r === m.site }); }));
function dimMat(mat, site) {
  const key = mat.uuid + (site ? 's' : '');
  if (dimCache.has(key)) return dimCache.get(key);
  const d = mat.clone();
  if (mat.isLineBasicMaterial) { d.transparent = true; d.opacity = (mat.opacity ?? 1) * 0.3; }
  else if (site) d.color.multiplyScalar(0.42);
  else if (shellSet.has(mat)) { d.transparent = true; d.opacity = 0.05; d.depthWrite = false; }
  else { d.transparent = true; d.opacity = 0.13; d.depthWrite = false; if (d.emissiveIntensity) d.emissiveIntensity *= 0.3; }
  dimCache.set(key, d); return d;
}
const byName = n => m.root.getObjectByName(n);
const chG = byName('chiller_155TR'), umaG = byName('unidades_manejadoras'), pipeG = byName('circuito_agua_helada'), uma3 = byName('UMA_03'), pumpG = byName('bombeo_agua_helada');
const under = (o, g) => { for (let p = o; p; p = p.parent) if (p === g) return true; return false; };
const FOCUS = {
  1: o => under(o, chG) || /^bloque_alto/.test(o.name),
  2: o => /^minisplit_2_/.test(o.name),
  3: o => /^minisplit_1_/.test(o.name),
  4: o => under(o, uma3) || under(o, chG),
  5: o => under(o, chG) || under(o, umaG) || under(o, pipeG) || under(o, pumpG) || under(o, m.prop),
  '5.2': o => under(o, chG) || under(o, pipeG) || under(o, pumpG),
  '5.3': () => false,
  '5.4': () => false,
  i: o => under(o, chG) || under(o, pipeG) || under(o, pumpG),
  'i.2': o => under(o, chG) || under(o, umaG) || under(o, pipeG) || under(o, pumpG) || under(o, m.prop),
  'i.3': () => false,
};
function dimFor(s) {
  base.forEach(b => {
    const keep = !b.site && FOCUS[s](b.o);
    b.o.material = keep ? b.mat : dimMat(b.mat, b.site);
    b.o.castShadow = keep && b.cast && !shellSet.has(b.mat);
  });
  m.shell.lines.forEach(l => l.visible = true);
}
function restoreMats() { base.forEach(b => { b.o.material = b.mat; b.o.castShadow = b.cast; }); }

// Modo (vista general)
let mode = 'actual', stop = 'g';
function refreshLabels() {
  labels.forEach(l => {
    l.hidden = stop === 'g' ? (!l.stops.includes('g') || (l.mode !== 'all' && l.mode !== mode)) : !l.stops.includes(stop);
    if (l.hidden) l.el.style.display = 'none';
  });
}
function setMode(md) {
  mode = md;
  m.prop.visible = md === 'prop'; dataFlow.im.visible = md === 'prop';
  refreshLabels();
  if (md === 'prop' && currentView !== 'superior') goView(currentView);
}

// Cámara
const VIEWS = {
  corte: { a: { pos: [-30, 15, 30], tgt: [-2, 4.5, -3] }, p: { pos: [-36, 22, 38], tgt: [-2, 9, -3] } },
  frontal: { a: { pos: [0, 8, 44], tgt: [0, 5.5, 0] }, p: { pos: [0, 12, 52], tgt: [0, 10.5, -2] } },
  superior: { a: { pos: [0, 58, 0.6], tgt: [0, 0, -3.5] }, p: { pos: [0, 64, 0.6], tgt: [0, 0, -3.5] } },
};
let currentView = 'corte', tween = null, offT = 0, offCur = 0, lastOff = -1, lw = 0, lh = 0;
function goPose(vw, d = 1300, tour = false) {
  const W = vp.clientWidth, Hh = vp.clientHeight; let eff = (W - offT * 2) / Hh; if (!isFinite(eff) || eff <= 0) eff = 1.6; eff = Math.max(0.6, eff);
  const q1 = new THREE.Vector3(...vw.tgt), p1 = new THREE.Vector3(...vw.pos);
  p1.sub(q1).multiplyScalar(tour ? Math.min(1.7, Math.max(0.8, 1.2 / eff)) : Math.min(1.8, Math.max(0.85, 1.45 / eff))).add(q1);
  tween = { t0: performance.now(), d, p0: cam.position.clone(), q0: ctl.target.clone(), p1, q1 };
}
function goView(name) {
  currentView = name;
  goPose(VIEWS[name][mode === 'prop' ? 'p' : 'a'], 900);
  document.querySelectorAll('[data-view]').forEach(b => b.classList.toggle('on', b.dataset.view === name));
}
document.querySelectorAll('[data-view]').forEach(b => b.onclick = () => goView(b.dataset.view));
ctl.addEventListener('start', () => { tween = null; });

// Fachada / Rayos X
let shell = 'xray';
function setShell(s) {
  shell = s; const x = s === 'xray';
  m.shell.mats.forEach(({ mat, xo }) => { mat.transparent = x; mat.opacity = x ? xo : 1; mat.depthWrite = !x; mat.needsUpdate = true; });
  m.shell.meshes.forEach(o => { o.castShadow = !x; o.receiveShadow = !x; });
  m.shell.lines.forEach(l => l.visible = x);
  document.querySelectorAll('[data-shell]').forEach(b => b.classList.toggle('on', b.dataset.shell === s));
  if (thermo) applyThermo();
}
document.querySelectorAll('[data-shell]').forEach(b => b.onclick = () => setShell(b.dataset.shell));

// VFD (parada 4)
const vfdFan = m.fans.find(f => f.obj.name === 'UMA_03_rotor'), vfdBase = vfdFan.speed;
let vfdPct = 100;
const fmt = (n, d) => n.toLocaleString('en-US', { maximumFractionDigits: d });
function applyVfd() {
  const s = vfdPct / 100, c = s ** 3, P = 15 * c, E = P * 360, saved = (15 - P) * 360;
  vfdFan.speed = vfdBase * s;
  const $ = id => document.getElementById(id);
  if (!$('vfdR')) return;
  $('vfdR').value = vfdPct; $('vfdV').textContent = vfdPct + ' %';
  $('vfdP').textContent = fmt(P, 2) + ' kW';
  $('vfdE').textContent = fmt(E, 1) + ' kWh/mes';
  $('vfdS').textContent = fmt((1 - c) * 100, 1) + ' %';
  $('vfdB').textContent = 'B/. ' + (saved * 0.18).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + ' /mes';
}
[dock, pop].forEach(el => {
  el.addEventListener('click', e => { if (e.target.closest('#arCtl')) { const S = TOOLS['5.3'].S; S.target = S.target ? 0 : 1; e.target.textContent = S.target ? 'Restablecer' : 'Aplicar ajuste'; } });
  el.addEventListener('input', e => { if (e.target.id === 'vfdR') { vfdPct = +e.target.value; applyVfd(); } });
  el.addEventListener('click', e => { const b = e.target.closest('[data-v]'); if (b) { vfdPct = +b.dataset.v; applyVfd(); } });
});

// Vista termográfica cualitativa: paleta Ironbow sobre una temperatura relativa (0–1) por clase de componente, sin °C
const $t = id => document.getElementById(id);
const IRON = [[0, 0x07041A], [0.22, 0x1F1A8A], [0.48, 0x9B1F9A], [0.74, 0xF06A1F], [0.92, 0xFFD23F], [1, 0xFFF6CC]].map(([k, c]) => [k, new THREE.Color(c)]);
function ironbow(t) {
  t = Math.min(1, Math.max(0, t)); let i = 1; while (i < IRON.length - 1 && IRON[i][0] < t) i++;
  const [k0, c0] = IRON[i - 1], [k1, c1] = IRON[i]; return c0.clone().lerp(c1, (t - k0) / (k1 - k0));
}
const TH = { supply: 0.16, ret: 0.3, pump: 0.2, motor: 0.62, equip: 0.5, duct: 0.24, inner: 0.1, anomaly: 1 };
const shellSetMesh = new Set(m.shell.meshes), thermoCache = new Map(), nrm = new THREE.Vector3(), radFaces = [];
scene.traverse(o => { if (o.name === 'radiacion_cara') radFaces.push(o); });
function thermoTemp(o, site, mt) {
  if (site) return null; // el entorno no se colorea: se oscurece para no distraer
  if (mt === m.M.thermal) return TH.anomaly;
  if (mt === m.M.insul) return null; // la funda queda translúcida: no tapa el color de la tubería ni la anomalía de las uniones
  if (mt === m.M.supply) return TH.supply;
  if (mt === m.M.ret) return TH.ret;
  if (under(o, pumpG)) return /motor/.test(o.name) ? TH.motor : TH.pump;
  if (shellSetMesh.has(o)) {
    // Fachada: más caliente cuanto más perpendicular le llega el sol (índice relativo de sky-v2), de noche se enfría
    const K = sky.S, up = /techo|cubierta|cornisa/.test(o.name);
    if (up) nrm.set(0, 1, 0); else nrm.set(0, 0, 1).transformDirection(o.matrixWorld);
    const sun = K.night ? 0 : K.irr * Math.max(0, nrm.dot(K.sd));
    return (K.night ? 0.2 : 0.26) + 0.6 * sun;
  }
  if (under(o, umaG) && /ducto|difusor/.test(o.name)) return TH.duct; // aire de suministro ya enfriado
  if (under(o, chG) || under(o, umaG) || /^minisplit_/.test(o.name)) return TH.equip;
  return TH.inner;
}
function thermoMat(t, shellMesh) {
  const x = shellMesh && shell === 'xray', key = Math.round(t * 50) + (x ? 'x' : shellMesh ? 'f' : '');
  if (!thermoCache.has(key)) thermoCache.set(key, new THREE.MeshBasicMaterial({ name: 'termografia', color: ironbow(Math.round(t * 50) / 50),
    transparent: x, opacity: x ? 0.1 : 1, depthWrite: !x, side: shellMesh ? THREE.DoubleSide : THREE.FrontSide }));
  return thermoCache.get(key);
}
let thermo = false, autoThermo = false;
const THERMO_OK = ['g', '5', '5.2'];
m.root.updateMatrixWorld(true);
const thermoBase = base.map(b => ({ ...b, temp: b.o.isMesh && !under(b.o, m.prop) ? thermoTemp(b.o, b.site, b.mat) : null, shellMesh: shellSetMesh.has(b.o) }));
function applyThermo() {
  if (!thermo) return;
  thermoBase.forEach(b => {
    if (stop !== 'g' && (b.site || !FOCUS[stop](b.o))) return; // en las paradas el resto sigue atenuado
    if (b.site) { b.o.material = dimMat(b.mat, true); return; }
    if (b.temp === null) return;
    if (b.shellMesh) b.temp = thermoTemp(b.o, false, b.mat);
    b.o.material = thermoMat(b.temp, b.shellMesh); b.o.castShadow = false;
  });
  radFaces.forEach(f => { f.visible = false; });
}
function setThermo(on) {
  thermo = on && THERMO_OK.includes(stop);
  $t('tThermo').classList.toggle('on', thermo);
  $t('thermoLegend').hidden = !thermo;
  if (thermo) { applyThermo(); $t('thermoLegend').parentElement.scrollTop = 0; return; }
  radFaces.forEach(f => { f.visible = true; });
  if (stop === 'g') { restoreMats(); setShell(shell); } else dimFor(stop);
}
$t('thT').innerHTML = THERMO.title + STAMP.ilus; $t('thC').textContent = THERMO.cold; $t('thH').textContent = THERMO.hot;
$t('thN').textContent = THERMO.note; $t('thK').textContent = THERMO.classes; $t('tThermo').textContent = THERMO.button;
$t('tThermo').onclick = () => setThermo(!thermo);
// Las exportaciones OBJ/GLB llevan los materiales reales, no los de la vista termográfica
stage._toolbar.addEventListener('click', () => { if (thermo) setThermo(false); }, true);

// Inspector por clic (vista general y Parada 5)
const equipOf = o => { for (let p = o; p; p = p.parent) if (p.userData.equip) return p.userData.equip; return null; };
const equipKey = e => e.type + (e.n ?? '');
const pickables = [], equipMeshes = new Map();
m.root.traverse(o => {
  const e = o.isMesh && equipOf(o); if (!e) return;
  pickables.push(o); const k = equipKey(e); if (!equipMeshes.has(k)) equipMeshes.set(k, []); equipMeshes.get(k).push(o);
});
const inspEl = document.getElementById('inspector'), inBody = document.getElementById('inBody'), ray = new THREE.Raycaster(), ndc = new THREE.Vector2();
const hiMat = new THREE.LineBasicMaterial({ color: 0xF2C14E, depthTest: false, transparent: true });
let hi = null, inspKey = null, downAt = null;
function closeInspector() {
  if (hi) { scene.remove(hi); hi.geometry.dispose(); hi = null; }
  inspKey = null; inspEl.hidden = true;
}
function openInspector(e) {
  closeInspector();
  const k = equipKey(e), bb = new THREE.Box3();
  // la tubería se resalta solo en el tramo principal del chiller al edificio, no en todo el circuito
  equipMeshes.get(k).filter(o => k !== 'pipe' || /^(suministro|retorno)_principal|brida_|punto_termico/.test(o.name)).forEach(o => bb.expandByObject(o));
  const size = bb.getSize(new THREE.Vector3()).addScalar(0.15);
  hi = new THREE.LineSegments(new THREE.EdgesGeometry(new THREE.BoxGeometry(size.x, size.y, size.z)), hiMat);
  hi.name = 'inspector_resaltado'; hi.renderOrder = 10; bb.getCenter(hi.position); scene.add(hi);
  const c = inspectorHTML(e);
  inBody.innerHTML = `${STAMP[c.st]}<h3>${c.title}</h3><p class="isub">${c.sub}</p>${c.body}`;
  inspKey = k; inspEl.hidden = false; inspEl.parentElement.scrollTop = 0;
}
const fromCanvas = ev => ev.button === 0 && ev.composedPath()[0]?.tagName === 'CANVAS';
stage.addEventListener('pointerdown', ev => { downAt = fromCanvas(ev) ? [ev.clientX, ev.clientY] : null; });
stage.addEventListener('pointerup', ev => {
  if (!downAt || !fromCanvas(ev) || Math.hypot(ev.clientX - downAt[0], ev.clientY - downAt[1]) > 5) return;
  downAt = null;
  if (!THERMO_OK.includes(stop)) return; // misma regla: vista general, 5.1 y 5.2
  const r = ev.composedPath()[0].getBoundingClientRect();
  ndc.set((ev.clientX - r.left) / r.width * 2 - 1, -(ev.clientY - r.top) / r.height * 2 + 1);
  ray.setFromCamera(ndc, cam);
  const occ = stop === 'g' && shell === 'facade' ? m.shell.meshes : [];
  const hit = ray.intersectObjects([...pickables, ...occ], false).find(h => h.object.visible);
  const e = hit && equipOf(hit.object);
  if (e) openInspector(e); else closeInspector();
});
addEventListener('keydown', ev => { if (ev.key === 'Escape' && inspKey) closeInspector(); });

// ---------------------------------------------------------------- Vista integrada
// i.1 · Una falla de punta a punta: 6 pasos sobre las uniones con deterioro; ◀ ▶ por paso y Reproducir
const falla = { k: 0, playing: false, t0: 0 }, STEP_MS = 7000;
function showStep(k, move = true) {
  falla.k = Math.max(0, Math.min(FALLA.length - 1, k)); falla.t0 = performance.now();
  const f = FALLA[falla.k], box = document.getElementById('falla');
  if (box) box.innerHTML = `<div class="fhd"><span class="fk" id="fStep">Paso ${falla.k + 1} de ${FALLA.length} · ${f.inv}</span>${STAMP[f.st]}</div><b class="ft">${f.t}</b><div class="fb">${f.html}</div><p class="fn">${f.src}</p>`;
  const dots = document.getElementById('fDots');
  if (dots) dots.innerHTML = FALLA.map((x, i) => `<button class="fdot${i === falla.k ? ' on' : ''}" data-step="${i}" aria-label="Paso ${i + 1}">${i + 1}</button>`).join('');
  syncPlay();
  const fc = box?.closest('.card'); if (fc) { dock.scrollTop = 0; const ot = box.querySelector('.ot'); if (ot) ot.scrollTop = 0; }
  [...document.getElementById('spB').children].forEach((li, i) => li.classList.toggle('cur', i === falla.k));
  FS.setStep(falla.k);
  TOOLS['5.2'].group.visible = stop === 'i' && (falla.k === 0 || falla.k === 4); // pasos 1 y 5: cámara termográfica sobre las uniones
  if (move && stop === 'i') goPose(f.pose, 1100, true);
}
function syncPlay() { const b = document.getElementById('fPlay'); if (b) { b.textContent = falla.playing ? 'Pausar' : 'Reproducir'; b.classList.toggle('on', falla.playing); } }
function playTick() {
  if (!falla.playing || stop !== 'i' || performance.now() - falla.t0 < STEP_MS) return;
  if (falla.k < FALLA.length - 1) showStep(falla.k + 1); else { falla.playing = false; syncPlay(); }
}
// i.2 · Antes / después: 0 = antes (2021); 1–3 = etapas de la INV3 sobre la geometría de la propuesta
function setStage(k) {
  abStage = k;
  m.prop.visible = k > 0;
  m.prop.children.forEach(c => { c.visible = c.name === 'IA_deteccion_anomalias' ? k >= 2 : c.name === 'modelo_BIM' ? k >= 3 : k >= 1; });
  dataFlow.im.visible = k >= 1;
  const a = ANTES_DESPUES[k], box = document.getElementById('abS'), r = document.getElementById('abR');
  if (box) box.innerHTML = `${STAMP[a.st]}<b>${a.t}</b><p>${a.html}</p>`;
  if (r && +r.value !== k) r.value = k;
}
// i.3 · Plan de 2 años: calendario de 104 semanas, construido una vez desde tour-content.js
const planEl = document.getElementById('plan');
function buildPlan() {
  const W = 104, pct = w => (w / W * 100).toFixed(3) + '%';
  const marks = (weeks, cls = 'pm') => weeks.map(w => `<i class="${cls}" style="left:${pct(w + 0.5)}"></i>`).join('');
  const weeksOf = r => r.every ? Array.from({ length: W / r.every }, (_, i) => (i + 1) * r.every - 1) : Array.from({ length: r.perYear * 2 }, (_, i) => Math.round((i + 1) * 52 / r.perYear) - 1);
  const head = `<div class="pl-l"></div><div class="pl-t pl-h">${[1, 2].map(y => `<span class="py" style="left:${pct((y - 1) * 52)};width:${pct(52)}">Año ${y}</span>`).join('')}${Array.from({ length: 8 }, (_, q) => `<span class="pq" style="left:${pct(q * 13)};width:${pct(13)}">T${q % 4 + 1}</span>`).join('')}</div>`;
  const row = (l, t, cls = '') => `<div class="pl-l ${cls}">${l}</div><div class="pl-t ${cls}">${t}</div>`;
  const sec = (title, stamp, note = '') => `<div class="pl-s">${stamp || ''}<b>${title}</b>${note ? `<span>${note}</span>` : ''}</div>`;
  const split = PLAN_SPLIT.map(r => row(`<b>${r.f}</b><small>${r.a}</small><small class="pr">${r.r}</small>`, marks(weeksOf(r), r.every === 1 ? 'pm thin' : 'pm'))).join('');
  const road = ROADMAP.map(([a, b, t, src]) => `<span class="pbar" style="left:${pct(a)};width:${pct(b - a)}" title="${src}">${t}<small>${src}</small></span>`).join('');
  planEl.innerHTML = `<div class="pl-top"><b>Plan de mantenimiento de 2 años</b><span class="pl-c">${PLAN_TEXT.counter}</span></div>
    <div class="pl-grid">${head}
      ${sec('Mini-split (por equipo)', STAMP.split, PLAN_TEXT.splitNote)}${split}
      ${sec(PLAN_TEXT.big, STAMP.ilus, PLAN_TEXT.bigTasks + ' ' + PLAN_TEXT.chiller)}${row('<b>Chiller, UMA y bombas</b>', `<span class="pband">${PLAN_TEXT.bigBand}</span>`)}
      ${sec(PLAN_TEXT.evalT, STAMP.ilus)}${row(`<small>${PLAN_TEXT.evalNote}</small>`, marks(Array.from({ length: 8 }, (_, q) => (q + 1) * 13 - 1), 'pe'))}
      ${sec(PLAN_TEXT.roadT, STAMP.prop, PLAN_TEXT.roadNote)}${row('<b>Etapas en orden</b>', road, 'tall')}
      ${sec(PLAN_TEXT.corrT, STAMP.ilus)}${row(`<small>${PLAN_TEXT.corr}</small>`, `<span class="pcorr">Sin fecha fija: ocurre cuando hay indicios de falla <button class="btn" data-go="i">Ver una falla de punta a punta (i.1)</button></span>`)}
    </div>`;
}
buildPlan();
function layoutPlan() {
  const hr = vp.getBoundingClientRect(), tb = vp.querySelector('.top').getBoundingClientRect(), bb = vp.querySelector('.bottom').getBoundingClientRect();
  planEl.style.top = (tb.bottom - hr.top + 12) + 'px';
  planEl.style.height = Math.max(200, bb.top - tb.bottom - 24) + 'px';
}
[dock, pop, planEl].forEach(el => {
  el.addEventListener('click', e => {
    const go = e.target.closest('[data-go]'); if (go) { applyStop(go.dataset.go); return; }
    if (e.target.closest('#fPrev')) { falla.playing = false; showStep(falla.k - 1); }
    if (e.target.closest('#fNext')) { falla.playing = false; showStep(falla.k + 1); }
    const d = e.target.closest('[data-step]'); if (d) { falla.playing = false; showStep(+d.dataset.step); }
    if (e.target.closest('#fPlay')) { falla.playing = !falla.playing; if (falla.playing && falla.k === FALLA.length - 1) showStep(0); else { falla.t0 = performance.now(); syncPlay(); } }
  });
  el.addEventListener('input', e => { if (e.target.id === 'abR') setStage(+e.target.value); });
});

// Recorrido
const ORDER = ['g', '1', '2', '3', '4', '5', '5.2', '5.3', '5.4', 'i', 'i.2', 'i.3'], KEYS = ['g', '1', '2', '3', '4', '5', 'i'], app = document.querySelector('.app');
const isFive = s => s === '5' || s.startsWith('5.'), isI = s => s === 'i' || s.startsWith('i.');
const subN = s => s === '5' ? '5.1' : s === 'i' ? 'i.1' : s;
const spPanel = document.getElementById('stopPanel'), donut = document.getElementById('donutSec'), genAside = document.getElementById('genAside');
function panel(s) {
  spPanel.hidden = s === 'g'; genAside.hidden = s !== 'g'; donut.hidden = !['g', '4', '5'].includes(s);
  if (s === 'g') return;
  const d = STOPS[s], n = KEYS.indexOf(isFive(s) ? '5' : s);
  document.getElementById('spK').textContent = isI(s) ? 'Cierre del recorrido · Vista integrada' : isFive(s) ? `Parada 5 de 5 · ${d.inv} · ${d.name}` : `Parada ${n} de 5 · ${d.inv}`;
  document.getElementById('spT').textContent = isI(s) || isFive(s) ? `${subN(s)} · ${d.sub}` : `${n} · ${d.name}`;
  document.getElementById('spL').textContent = d.loc;
  document.getElementById('spB').innerHTML = d.bullets.map(([t, st]) => `<li class="${st}">${t}</li>`).join('');
}
function navLabels(s) {
  const n = ORDER.indexOf(s), nm = k => k === 'g' ? 'Vista general' : isI(k) || isFive(k) ? `${subN(k)} ${STOPS[k].short}` : STOPS[k].name;
  const pv = document.getElementById('spPrev'), nx = document.getElementById('spNext');
  pv.hidden = n === 0; pv.textContent = '← ' + (n > 0 ? nm(ORDER[n - 1]) : '');
  nx.textContent = (s === 'i.3' ? 'Vista general' : (n === 0 ? 'Iniciar recorrido: ' : '') + nm(ORDER[n + 1])) + ' →';
  document.getElementById('navPos').textContent = s === 'g' ? 'General' : isI(s) ? `Integrada ${subN(s)}` : isFive(s) ? `Parada ${subN(s)} / 5` : `Parada ${n} / 5`;
  fitBottom();
}
document.getElementById('spPrev').onclick = () => step(-1);
document.getElementById('spNext').onclick = () => { if (stop === 'i.3') applyStop('g'); else step(1); };
// La nota y los controles de abajo a la izquierda no deben quedar debajo de la navegación de abajo a la derecha
function fitBottom() { const nav = vp.querySelector('.tnav'); vp.querySelector('.bottom').style.maxWidth = Math.max(260, vp.clientWidth - nav.offsetWidth - 54) + 'px'; }
addEventListener('resize', fitBottom);
function step(d) { const i = ORDER.indexOf(stop) + d; if (i >= 0 && i < ORDER.length) applyStop(ORDER[i]); }
// La cámara se corre a la derecha lo que ocupan las tarjetas visibles a la izquierda
// (en modo "al pasar" las tarjetas quedan invisibles pero ocupan su lugar, así el encuadre no cambia)
function dockOffset() { return dock.children.length ? (dock.getBoundingClientRect().right - vp.getBoundingClientRect().left) / 2 : 0; }
function applyStop(s) {
  if (s !== stop) closeInspector();
  const keepThermo = thermo && THERMO_OK.includes(s) && !(autoThermo && s !== '5.2');
  if (thermo && !keepThermo) { setThermo(false); autoThermo = false; }
  stop = s; const g = s === 'g';
  app.classList.toggle('touring', !g);
  Object.entries(T.groups).forEach(([k, grp]) => grp.visible = k === s && k !== 'i'); // los íconos de la vista integrada anterior ya no se usan
  if (g) { restoreMats(); setShell(shell); }
  else { dimFor(s); m.prop.visible = s === '5'; dataFlow.im.visible = s === '5'; }
  flows.forEach(f => f.im.visible = g || s === '5' || s === '5.2' || s === 'i' || s === 'i.2');
  FS.group.visible = s === 'i'; if (s !== 'i') FS.reset();
  halos.forEach(h => h.visible = g || s === '5' || s === '5.2' || s === 'i' || s === 'i.2');
  Object.entries(TOOLS).forEach(([k, t]) => { t.group.visible = k === s || (k === '5.2' && s === 'i' && (falla.k === 0 || falla.k === 4)); });
  if (s !== 'i') falla.playing = false;
  m.prop.children.forEach(c => { c.visible = true; });
  if (s === 'i.2') setStage(abStage);
  if (s === 'i.3') layoutPlan();
  document.getElementById('subbarI').hidden = !isI(s);
  document.getElementById('plan').hidden = s !== 'i.3';
  ctl.minDistance = s === '5.3' || s === '5.4' ? 1.2 : 6;
  document.getElementById('subbar').hidden = !isFive(s);
  arcFlow.im.visible = false;
  vp.querySelectorAll('[data-gen]').forEach(e => e.hidden = !g);
  document.querySelectorAll('[data-stop]').forEach(b => b.classList.toggle('on', b.dataset.stop === s || (!!b.closest('.tourbar') && ((b.dataset.stop === '5' && isFive(s)) || (b.dataset.stop === 'i' && isI(s))))));
  panel(s); navLabels(s);
  sky.setActive(g); document.getElementById('skyPanel').hidden = !g;
  buildDock(s);
  offT = dockOffset();
  if (g) setMode(mode); else refreshLabels();
  if (s === 'i') showStep(falla.k, false);
  if (g) goView(currentView); else goPose(s === 'i' ? FALLA[falla.k].pose : STOPS[s].pose, 1300, true);
  stage._toolbar.style.display = g ? '' : 'none'; Object.assign(stage._toolbar.style, { top: 'auto', bottom: '70px' });
  if (s === '4') applyVfd(); else vfdFan.speed = vfdBase;
  document.getElementById('thermoSeg').hidden = !THERMO_OK.includes(s);
  if (keepThermo) applyThermo();
  if (s === '5.2' && !thermo) { setThermo(true); autoThermo = thermo; } // la 5.2 abre con la vista termográfica
}
document.querySelectorAll('[data-stop]').forEach(b => b.onclick = () => applyStop(b.dataset.stop));
addEventListener('keydown', e => {
  if (e.metaKey || e.ctrlKey || e.altKey) return;
  const inField = e.target.closest && e.target.closest('input, textarea, select');
  if (/^[0-6]$/.test(e.key) && !(inField && e.target.type !== 'range')) { applyStop(KEYS[+e.key]); e.preventDefault(); }
});
new ResizeObserver(() => { layoutDock(); layoutPlan(); fitDock(Math.max(0, [...dock.querySelectorAll('.card:not(.mini)')].findIndex(c => c.querySelector('.ch[aria-expanded=true]')))); offT = dockOffset(); }).observe(vp);

// Etiquetas / pausa
const tL = document.getElementById('tLabels'), tP = document.getElementById('tPause');
tL.onclick = () => { const off = host.classList.toggle('off'); tL.textContent = off ? 'Etiquetas: no' : 'Etiquetas: sí'; tL.classList.toggle('on', !off); };
let paused = false;
tP.onclick = () => { paused = !paused; tP.textContent = paused ? 'Reanudar animación' : 'Pausar animación'; tP.classList.toggle('on', paused); };

// Panel Clima y hora
const KEY = 'utp-recorrido-cielo-v2';
let playing = false, spd = 1;
try { const s = JSON.parse(localStorage.getItem(KEY) || 'null'); if (s) { sky.set({ hour: s.hour ?? 10, month: s.month ?? sky.S.month, wx: s.wx ?? 'soleado', front: s.front ?? 45 }); spd = s.spd ?? 1; } } catch (e) {}
const q = id => document.getElementById(id);
const MES = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'];
const RUMBO = ['N', 'NE', 'E', 'SE', 'S', 'SO', 'O', 'NO'];
q('skMonth').innerHTML = MES.map((x, i) => `<option value="${i + 1}">${x}</option>`).join('');
let saveT = 0;
// Ocupación del edificio: solo un indicador (no calcula carga, consumo ni ahorro). Horario según FUENTES_COMPENDIO, «Observación del grupo»
function syncOcc(h) {
  const st = h >= 7 && h < 22.75 ? 'uso' : h >= 22.75 && h < 23.5 ? 'salida' : 'vacio';
  const b = q('occState'); b.dataset.o = st;
  b.textContent = { uso: 'En uso (horario de clases)', salida: 'Salida del edificio', vacio: 'Desocupado: solo personal de seguridad' }[st];
  q('occNow').style.left = (h / 24 * 100).toFixed(2) + '%';
  const html = st === 'uso' ? `<span>${STAMP.sup}Inicio: 7:00 a.&nbsp;m.</span><span>${STAMP.obs}Fin de clases: 10:45 p.&nbsp;m.</span>`
    : st === 'salida' ? `<span>${STAMP.obs}De 10:45 p.&nbsp;m. a 11:30 p.&nbsp;m.</span>` : `<span>${STAMP.obs}De 11:30 p.&nbsp;m. a 7:00 a.&nbsp;m.</span>`;
  if (q('occStamps').innerHTML !== html) q('occStamps').innerHTML = html;
  q('occExtra').hidden = st !== 'vacio';
}
function syncSky() {
  if (thermo) applyThermo();
  const K = sky.S, hh = Math.floor(K.hour), mm = Math.floor((K.hour - hh) * 60);
  q('skHour').value = K.hour; q('skTime').textContent = `${String(hh).padStart(2, '0')}:${String(mm).padStart(2, '0')}`;
  q('skSun').textContent = K.el > 0 ? `Sol a ${Math.round(K.el / Math.PI * 180)}° de altura` : K.night ? 'Noche' : 'Crepúsculo';
  q('skMonth').value = K.month;
  q('skSeason').textContent = K.month === 12 || K.month <= 4 ? 'Estación seca (dic–abr)' : 'Estación lluviosa (may–nov)';
  document.querySelectorAll('[data-wx]').forEach(b => b.classList.toggle('on', b.dataset.wx === K.wx));
  document.querySelectorAll('[data-spd]').forEach(b => b.classList.toggle('on', +b.dataset.spd === spd));
  q('skOri').value = K.front; q('skOriV').textContent = `${RUMBO[Math.round(K.front / 45) % 8]} · ${Math.round(K.front)}°`;
  q('skNeedle').style.transform = `rotate(${-K.front}deg)`;
  q('skPlay').textContent = playing ? 'Pausar ciclo' : 'Reproducir ciclo';
  syncOcc(K.hour);
  const now = performance.now(); if (now - saveT > 800) { saveT = now; localStorage.setItem(KEY, JSON.stringify({ hour: K.hour, month: K.month, wx: K.wx, front: K.front, spd })); }
}
q('skHour').oninput = e => { sky.set({ hour: +e.target.value }); syncSky(); };
q('skMonth').onchange = e => { sky.set({ month: +e.target.value }); syncSky(); };
q('skOri').oninput = e => { sky.set({ front: +e.target.value }); syncSky(); };
q('skPlay').onclick = () => { playing = !playing; syncSky(); };
document.querySelectorAll('[data-wx]').forEach(b => b.onclick = () => { sky.set({ wx: b.dataset.wx }); syncSky(); });
document.querySelectorAll('[data-spd]').forEach(b => b.onclick = () => { spd = +b.dataset.spd; syncSky(); });
syncSky();

// Calculadora psicrométrica (valores de ejemplo, no medidos)
function syncPsy() {
  const num = id => parseFloat(q(id).value), t1 = num('psT1'), r1 = num('psR1'), t2 = num('psT2'), r2 = num('psR2');
  const ok = [t1, t2].every(t => t >= 0 && t <= 50) && [r1, r2].every(r => r >= 1 && r <= 100);
  if (!ok) { q('psOut').innerHTML = q('psQ').innerHTML = ''; q('psNote').textContent = 'Usa temperaturas de 0 a 50 °C y humedad relativa de 1 a 100 %.'; return; }
  const r = coilProcess({ t: t1, rh: r1 / 100 }, { t: t2, rh: r2 / 100 }), f = (x, d) => x == null ? '—' : x.toFixed(d);
  q('psOut').innerHTML = `<span></span><span class="hd2">Entrada</span><span class="hd2">Salida</span>`
    + [['Humedad absoluta W (g/kg)', s => f(s.W * 1000, 2)], ['Entalpía h (kJ/kg)', s => f(s.h, 2)], ['Punto de rocío (°C)', s => f(s.td, 1)]]
      .map(([n, g]) => `<span>${n}</span><b>${g(r.s1)}</b><b>${g(r.s2)}</b>`).join('');
  q('psQ').innerHTML = [['q total', r.qt, 2, 'kJ/kg'], ['q sensible', r.qs, 2, 'kJ/kg'], ['q latente', r.ql, 2, 'kJ/kg'], ['SHR', r.shr, 3, '']]
    .map(([n, v, d, u]) => `<div>${n}<b>${f(v, d)}${u ? `&nbsp;<small>${u}</small>` : ''}</b></div>`).join('');
  q('psNote').textContent = t2 >= t1 ? 'La salida no está más fría que la entrada: no es un proceso de enfriamiento.'
    : !r.condenses ? 'La salida no tiene menos humedad que la entrada: no hay condensación, solo calor sensible (o el estado no es físico).'
    : `Fracción latente con estos valores: ${f(r.ql / r.qt * 100, 0)} %.`;
}
q('psy').hidden = !FEATURES.psychro;
['psT1', 'psR1', 'psT2', 'psR2'].forEach(id => { q(id).oninput = syncPsy; });
syncPsy();

// Textos en vivo de las subventanas 5.3 y 5.4
function syncTools() {
  const set = (id, t) => { const e = document.getElementById(id); if (e && e.textContent !== t) e.textContent = t; };
  if (stop === '5.4') set('droneSt', TOOLS['5.4'].S.text);
  if (stop === '5.3') {
    const S = TOOLS['5.3'].S; set('arSt', S.text);
    arZones.forEach((l, i) => { const h = `${STAMP.ilus}${TOOLS['5.3'].ZONES[i][0]}<small>${S.zones[i]}</small>`; if (l.bx.innerHTML !== h) { l.bx.innerHTML = h; l.bw = 0; } });
  }
}

// Bucle
let simT = 0, flowT = 0, last = performance.now();
stage.onFrame = () => {
  const now = performance.now(), dt = Math.max(0, Math.min(0.05, (now - last) / 1000)); last = now;
  if (tween) {
    const bad = v3 => !isFinite(v3.x) || !isFinite(v3.y) || !isFinite(v3.z);
    if (bad(tween.p1) || bad(tween.q1)) tween = null;
  }
  if (!isFinite(cam.position.x + cam.position.y + cam.position.z)) cam.position.set(-30, 15, 30);
  if (!isFinite(ctl.target.x + ctl.target.y + ctl.target.z)) ctl.target.set(-2, 4.5, -3);
  if (tween) {
    if (!isFinite(tween.p0.x + tween.p0.y + tween.p0.z)) tween.p0.copy(cam.position);
    const k = Math.min(1, (now - tween.t0) / tween.d), e = k < 0.5 ? 4 * k * k * k : 1 - Math.pow(-2 * k + 2, 3) / 2;
    cam.position.lerpVectors(tween.p0, tween.p1, e); ctl.target.lerpVectors(tween.q0, tween.q1, e);
    if (k >= 1) tween = null;
  }
  offCur = Math.abs(offT - offCur) < 0.5 ? offT : offCur + (offT - offCur) * Math.min(1, dt * 5);
  const W = stage.clientWidth, Hh = stage.clientHeight;
  if (offCur !== lastOff || W !== lw || Hh !== lh) {
    if (offCur < 0.5) cam.clearViewOffset(); else cam.setViewOffset(W, Hh, -offCur, 0, W, Hh);
    lastOff = offCur; lw = W; lh = Hh;
  }
  if (!paused) {
    simT += dt;
    const lf = sky.S.active ? sky.S.factor : 1; flowT += dt * lf;
    m.fans.forEach(f => { f.obj.rotation[f.axis] += f.speed * dt * lf; });
    if (flows[0].im.visible) flows.forEach(f => stepFlow(f, flowT));
    if (sky.S.active && playing) { sky.set({ hour: (sky.S.hour + dt * spd / 3) % 24 }); syncSky(); }
    sky.update(dt, simT);
    if (dataFlow.im.visible) { stepFlow(dataFlow, simT); m.ia.rotation.y += 0.4 * dt; m.M.sensor.emissiveIntensity = 0.9 + 0.6 * Math.sin(simT * 4); }
    if (arcFlow.im.visible) stepFlow(arcFlow, simT);
    T.tick(simT);
    const tool = TOOLS[stop] || (stop === 'i' && (falla.k === 0 || falla.k === 4) ? TOOLS['5.2'] : null);
    if (tool) tool.tick(simT, dt);
    const pulse = 0.82 + 0.18 * Math.sin(simT * 3.2);
    halos.forEach(s => s.scale.setScalar(s.userData.base * pulse));
  }
  syncTools();
  if (stop === 'i') fallaRep = FS.tick(simT, (performance.now() - falla.t0) / 1000);
  playTick();
  placeLabels();
  placeDock();
  placeHots();
};
flows.forEach(f => stepFlow(f, 0)); stepFlow(dataFlow, 0); stepFlow(arcFlow, 0); T.tick(0);
setShell('xray');
applyStop('g');
try { if (localStorage.getItem(HOVER_KEY) === '1') setHoverMode(true); } catch (e) {}
if (tween) tween.d = 1;
if (!vp.clientHeight) { const ro0 = new ResizeObserver(() => { if (vp.clientHeight) { ro0.disconnect(); goView(currentView); if (tween) tween.d = 1; } }); ro0.observe(vp); }
