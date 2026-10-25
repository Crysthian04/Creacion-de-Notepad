// Motor del modelo: paradas (0 inicio, 1 M6, 2 M14), pasos de ruta principal y profundización,
// cámara, etiquetas 3D, tarjetas con sello, figuras y vista de referencias.
// El texto vive en content-*.js; la geometría y las animaciones, en scene-*.js.
import * as THREE from 'three';
import { buildInicio } from 'app/scene-inicio.js';
import { buildM6 } from 'app/scene-m6.js';
import { buildM14 } from 'app/scene-m14.js';

const stage = document.querySelector('three-d-stage');
await stage.ready;
const scene = stage._scene, cam = stage._camera, ctl = stage._controls;
// ---------- Etiquetas ----------
const host = document.getElementById('labels'), labels = [];
const v = new THREE.Vector3();
function label(anchor, html, { cls = '', down = false, onClick = null, id = '', prio = false } = {}) {
  const el = document.createElement('div');
  el.className = 'lbl ' + cls + (onClick ? ' click' : '');
  el.innerHTML = down ? `<div class="dot"></div><div class="stem"></div><div class="box">${html}</div>` : `<div class="box">${html}</div><div class="stem"></div><div class="dot"></div>`;
  if (onClick) el.addEventListener('click', onClick);
  el.dataset.id = id; el.dataset.i = labels.length; el.hidden = true; host.appendChild(el);
  const L = { el, anchor, prio, on: false, set(h) { el.querySelector('.box').innerHTML = h; } };
  labels.push(L); return L;
}
function placeLabels() {
  const r = host.getBoundingClientRect(), dk = document.getElementById('dock');
  const dockRight = dk && dk.childElementCount ? dk.offsetLeft + dk.offsetWidth + 6 : 0;
  const vis = [];
  for (const L of labels) {
    if (!L.on) continue;
    const p = L.anchor.isVector3 ? v.copy(L.anchor) : L.anchor.getWorldPosition(v);
    p.project(cam);
    let ok = p.z < 1 && Math.abs(p.x) < 1.1 && Math.abs(p.y) < 1.1;
    if (ok && dockRight && (p.x + 1) / 2 * r.width < dockRight) ok = false; // detrás de la columna de tarjetas
    L.el.hidden = !ok;
    if (ok) vis.push({ L, x: (p.x + 1) / 2 * r.width, y: (1 - p.y) / 2 * r.height });
  }
  // Separación de etiquetas encimadas: la caja se aleja de su punto alargando el tallo
  // Las tarjetas también cuentan como zonas ocupadas: ninguna etiqueta queda bajo una tarjeta
  const hr = host.getBoundingClientRect(), zone = q => ({ l: q.left - hr.left - 4, r: q.right - hr.left + 4, t: q.top - hr.top - 4, b: q.bottom - hr.top + 4 });
  const cards = dk && dk.childElementCount ? [...dk.children].map(c => zone(c.getBoundingClientRect())) : [];
  const ins = document.getElementById('inset'); if (ins && !ins.hidden) cards.push(zone(ins.getBoundingClientRect()));
  document.querySelectorAll('.bottom > *').forEach(e => cards.push(zone(e.getBoundingClientRect()))); // nota y barra ← →
  const placed = [], H = r.height;
  vis.sort((a, b) => (b.L.prio ? 1 : 0) - (a.L.prio ? 1 : 0) || b.y - a.y); // las etiquetas prioritarias (niveles) se colocan primero
  for (const o of vis) {
    const box = o.L.el.querySelector('.box'), w = box.offsetWidth, h = box.offsetHeight;
    const nat = o.L.el.firstElementChild.classList.contains('dot'); // true = la caja va debajo del punto
    const x = Math.max(w / 2 + 4, Math.min(r.width - w / 2 - 4, o.x));
    // Coloca la caja hacia arriba o hacia abajo; si se sale del visor en su sentido natural, se voltea
    const fit = down => {
      let stem = 16, rect;
      for (let k = 0; k < 40; k++) {
        const top = down ? o.y + 5 + stem : o.y - 5 - stem - h;
        rect = { l: x - w / 2 - 5, r: x + w / 2 + 5, t: top - 5, b: top + h + 5 };
        const hit = placed.find(q => rect.l < q.r && rect.r > q.l && rect.t < q.b && rect.b > q.t);
        if (!hit) break;
        stem += down ? hit.b - rect.t + 1 : rect.b - hit.t + 1;
      }
      return { stem, rect, down, inside: rect.t + 5 >= 2 && rect.b - 5 <= H - 2 };
    };
    let f = fit(nat); if (!f.inside) { const g2 = fit(!nat); if (g2.inside && g2.stem <= 48) f = g2; } // solo se voltea si queda cerca de su punto
    if (!f.inside || cards.some(q => f.rect.l < q.r && f.rect.r > q.l && f.rect.t < q.b && f.rect.b > q.t)) { o.L.el.hidden = true; continue; }
    placed.push(f.rect);
    o.L.el.classList.toggle('flip', f.down !== nat);
    const st = o.L.el.querySelector('.stem'); if (st.style.height !== f.stem + 'px') st.style.height = f.stem + 'px';
    o.L.el.style.transform = `translate(${x}px, ${o.y}px) translate(-50%, ${f.down ? '0' : '-100%'})`;
  }
}

const root = new THREE.Group(); root.name = 'labs_m6_m14';
const ctx = { THREE, scene, cam, label, go: (s, i) => go(s, i), fly: c => flyTo(c) };
const S1 = buildM6(ctx), S2 = buildM14(ctx);
const STOPS = [buildInicio({ ...ctx, m6: S1, m14: S2 }), S1, S2]; // el inicio usa miniaturas con la geometría de las paradas
STOPS.forEach(s => root.add(s.group));
stage.setObject(root);
STOPS[0].group.traverse(o => { if (o.isMesh) o.castShadow = false; }); // sin sombras sueltas bajo los pedestales
scene.add(new THREE.AmbientLight(0xffffff, 0.55));
cam.near = 0.1; cam.far = 1500; cam.updateProjectionMatrix();
ctl.maxPolarAngle = Math.PI * 0.495; ctl.minDistance = 2; ctl.maxDistance = 400;
if (stage._toolbar) stage._toolbar.style.display = 'none';

// ---------- Tarjetas ----------
const STAMP = { df: 'Dato de fuente', il: 'Ilustrativo', pr: 'Propuesta' }, POPS = [];
// Rótulo de una escena: frase (≤ 25 palabras), cifra opcional (≤ 12), cita, sello, referencia y chips «Detalle»
function rotHTML(r, chips) {
  const st = (k, txt) => `<span class="st ${k}">${txt || STAMP[k]}</span>`;
  return `<div class="card rot" data-card><div class="ch"><span class="ref">${r.ref}</span>${st(r.stamp, r.stampText)}</div>
<p class="frase">${r.f} <span class="cite">(${r.fc})</span></p>${r.c ? `<p class="cifra">${r.cs ? st(r.cs) + ' ' : ''}${r.c}${r.cc ? ` <span class="cite">(${r.cc})</span>` : ''}</p>` : ''}
${r.extra ? `<p class="small">${r.extra}</p>` : ''}${r.ui || ''}${r.replay ? '<button class="btn replay" data-replay>↺ Repetir</button>' : ''}
<div class="chips"><span>Detalle:</span>${chips.map(c => `<button class="btn chip" data-chip="${c.i}" title="${c.t}">${c.n}</button>`).join('')}</div></div>`;
}
export function cardHTML(c) {
  const stamp = c.stamp ? `<span class="st ${c.stamp}">${STAMP[c.stamp]}</span>${c.cite ? `<span class="cite">(${c.cite})</span>` : ''}` : '';
  const ref = c.ref ? `<span class="ref">${c.ref}</span>` : '';
  const fig = !c.fig ? '' : c.fig.link
    ? `<div class="fig link"><button class="btn figbtn" data-figsrc="${c.fig.src}">Ver figura</button><div class="ft">${c.fig.title}</div><div class="cr">${c.fig.credit}</div></div>`
    : `<div class="fig"><div class="ft">${c.fig.title}</div><img src="${c.fig.src}" alt="${c.fig.alt || ''}" data-fig><div class="cr">${c.fig.credit}</div></div>`;
  const pop = c.popup ? `<button class="btn popbtn" data-pop="${POPS.push(c.popup.html) - 1}">${c.popup.label}</button>` : '';
  if (c.fold) return `<details class="card" data-card${c.open ? ' open' : ''}><summary>${c.ref || c.stamp ? `<span class="ch">${c.ref ? `<span class="ref">${c.ref}</span>` : ''}${c.stamp ? `<span class="st ${c.stamp}">${STAMP[c.stamp]}</span>${c.cite ? `<span class="cite">(${c.cite})</span>` : ''}` : ''}</span>` : ''}<b class="sm">${c.title}</b></summary>${c.body}${c.fig ? '' : ''}</details>`;
  return `<div class="card${c.wide ? ' wide' : ''}" data-card>${(ref || stamp) ? `<div class="ch">${ref}${stamp}</div>` : ''}${c.title ? `<h4>${c.title}</h4>` : ''}${c.body || ''}${pop}${fig}</div>`;
}
const dock = document.getElementById('dock');
function openFig(f, src) {
  document.getElementById('figbody').innerHTML = `<div class="ft" style="font-weight:600;margin-bottom:8px">${f.querySelector('.ft').innerHTML}</div><img src="${src}" alt=""><div class="cr" style="margin-top:8px;font-size:12px;color:#9AA6B1">${f.querySelector('.cr').innerHTML}</div>`;
  document.getElementById('figbox').hidden = false;
}
dock.addEventListener('click', e => {
  const img = e.target.closest('img[data-fig]'); if (img) return openFig(img.closest('.fig'), img.src);
  const fb = e.target.closest('[data-figsrc]'); if (fb) return openFig(fb.closest('.fig'), fb.dataset.figsrc);
  if (e.target.closest('[data-replay]')) return go(cur, step); // la animación narrativa vuelve a empezar
  const ch = e.target.closest('[data-chip]'); if (ch) return go(cur, +ch.dataset.chip, { back: step });
  const pb = e.target.closest('[data-pop]');
  if (pb) { document.getElementById('figbody').innerHTML = POPS[+pb.dataset.pop]; document.getElementById('figbox').hidden = false; }
});
document.querySelectorAll('[data-close]').forEach(b => b.addEventListener('click', closeOverlays));
document.querySelectorAll('.overlay').forEach(o => o.addEventListener('click', e => { if (e.target === o) closeOverlays(); }));
function closeOverlays() { document.querySelectorAll('.overlay').forEach(o => o.hidden = true); }

// ---------- Navegación ----------
let cur = -1, step = 0, deepNav = false, t0 = performance.now(), backTo = null;
const $ = id => document.getElementById(id);
const order = s => deepNav ? s.steps : s.steps.filter(x => x.level === 'RP');
function go(si, idx = 0, opt = {}) {
  backTo = opt.back !== undefined ? { si, idx: opt.back } : null;
  const s = STOPS[si];
  if (si !== cur) { STOPS.forEach((x, i) => { x.group.visible = i === si; }); cur = si; buildAside(s); }
  step = Math.max(0, Math.min(idx, s.steps.length - 1));
  const st = s.steps[step];
  labels.forEach(L => { L.on = false; L.el.hidden = true; });
  (st.labels || []).forEach(L => { L.on = true; });
  POPS.length = 0;
  const chips = (st.chips || []).map(id => { const i = s.steps.findIndex(x => x.id === id); return { i, n: s.steps[i].n, t: s.steps[i].title }; });
  dock.innerHTML = (st.rot ? rotHTML(st.rot, chips) : '') + (st.cards || []).map(cardHTML).join('');
  $('back').hidden = !backTo; if (backTo) $('back').textContent = `← Volver a la escena ${s.steps[backTo.idx].n}`;
  dock.scrollTop = 0;
  $('start').hidden = !st.start; if (st.start) $('start').innerHTML = st.start;
  $('inset').hidden = !st.inset; if (st.inset) $('inset').innerHTML = st.inset;
  $('note').innerHTML = s.note;
  document.querySelectorAll('#stops [data-stop]').forEach(b => b.classList.toggle('on', +b.dataset.stop === si));
  document.querySelectorAll('.steps li').forEach(li => li.classList.toggle('on', +li.dataset.i === step));
  showTab(st.level === 'PR' ? 'deep' : 'main');
  const seq = order(s), k = seq.indexOf(st);
  $('pos').textContent = st.level === 'PR' && !deepNav ? `${st.n} · profundización` : `${st.n} · ${k + 1} de ${seq.length}`;
  if (st.cam) flyTo(st.cam);
  s.enter && s.enter(st, step);
  t0 = performance.now();
}
function move(d) {
  const s = STOPS[cur], seq = order(s), st = s.steps[step];
  let k = seq.indexOf(st);
  if (k < 0) k = seq.findIndex(x => s.steps.indexOf(x) > step) - (d > 0 ? 1 : 0);
  const nk = k + d;
  if (nk >= 0 && nk < seq.length) go(cur, s.steps.indexOf(seq[nk]));
  else if (nk >= seq.length && cur < STOPS.length - 1) go(cur + 1, 0);
  else if (nk < 0 && cur > 0) { const p = STOPS[cur - 1], ps = order(p); go(cur - 1, p.steps.indexOf(ps[ps.length - 1])); }
}
function buildAside(s) {
  $('kick').textContent = s.kicker; $('stitle').textContent = s.title; $('slead').innerHTML = s.lead || '';
  const li = (x, i) => `<li data-i="${i}"><span class="k">${x.n}</span><span>${x.title}${x.ref ? `<span class="r">${x.ref}</span>` : ''}</span></li>`;
  const main = s.steps.map((x, i) => x.level === 'RP' ? li(x, i) : '').join(''), deep = s.steps.map((x, i) => x.level === 'PR' ? li(x, i) : '').join('');
  $('main').innerHTML = main; $('deep').innerHTML = deep;
  const multi = s.steps.length > 1;
  $('tabs').hidden = !deep; $('main').hidden = !multi; $('deep').hidden = true;
  $('deepBtn').hidden = !deep; $('refBtn').hidden = !s.refs;
  $('extra').innerHTML = (s.extraCards || []).map(cardHTML).join('');
  document.querySelectorAll('.steps li').forEach(el => el.addEventListener('click', () => go(cur, +el.dataset.i)));
}
function showTab(t) {
  if ($('tabs').hidden) return;
  $('main').hidden = t !== 'main'; $('deep').hidden = t !== 'deep';
  document.querySelectorAll('#tabs [data-tab]').forEach(b => b.classList.toggle('on', b.dataset.tab === t));
}
function setDeep(on) { deepNav = on; $('deepBtn').textContent = `Profundización en ← →: ${on ? 'sí' : 'no'}`; $('deepBtn').classList.toggle('on', on); go(cur, step); }
function showRefs() {
  const s = STOPS[cur]; if (!s.refs) return;
  $('refbody').innerHTML = `<h3>Referencias · ${s.short}</h3>` + s.refs.map(r => `<p>${r}</p>`).join('');
  $('refbox').hidden = false;
}
$('prev').onclick = () => move(-1); $('next').onclick = () => move(1);
$('back').onclick = () => { if (backTo) go(backTo.si, backTo.idx); };
$('deepBtn').onclick = () => setDeep(!deepNav);
document.querySelectorAll('#tabs [data-tab]').forEach(b => b.onclick = () => showTab(b.dataset.tab)); $('refBtn').onclick = showRefs;
// Desde el inicio, la cámara entra en la miniatura antes de pasar a la parada
const enterStop = k => (cur === 0 && k > 0 && STOPS[0].enterStop) ? STOPS[0].enterStop(k) : go(k, 0);
document.querySelectorAll('#stops [data-stop]').forEach(b => b.onclick = () => enterStop(+b.dataset.stop));
addEventListener('keydown', e => {
  if (e.target.closest && e.target.closest('input,textarea')) return;
  if (e.key === 'Escape') return closeOverlays();
  if ('012'.includes(e.key) && e.key.length === 1) { closeOverlays(); enterStop(+e.key); }
  else if (e.key === 'ArrowRight') { closeOverlays(); move(1); }
  else if (e.key === 'ArrowLeft') { closeOverlays(); move(-1); }
  else if (e.key === 'p' || e.key === 'P') setDeep(!deepNav);
  else if (e.key === 'r' || e.key === 'R') { const o = $('refbox').hidden; closeOverlays(); if (o) showRefs(); }
});

// ---------- Cámara ----------
let fly = null;
function flyTo([x, y, z, tx, ty, tz]) {
  // A 1366 el área libre (a la derecha de las tarjetas) es más angosta: la cámara se aleja en proporción
  const w = stage.clientWidth, h = stage.clientHeight, dw = dock.childElementCount ? dock.offsetWidth + 18 : 0;
  const k = w && h ? Math.max(1, 1.12 / ((w - dw) / h)) : 1;
  x = tx + (x - tx) * k; y = ty + (y - ty) * k; z = tz + (z - tz) * k;
  fly = { a: cam.position.clone(), b: new THREE.Vector3(x, y, z), at: ctl.target.clone(), bt: new THREE.Vector3(tx, ty, tz), t: 0, t0: performance.now() };
}
let last = performance.now();
stage.onFrame = () => {
  const now = performance.now(), dt = Math.min(0.05, (now - last) / 1000); last = now;
  if (fly) {
    fly.t = Math.min(1, (now - fly.t0) / 1100); // tiempo real: igual de rápido con pocos cuadros por segundo
    const e = fly.t < 0.5 ? 2 * fly.t * fly.t : 1 - Math.pow(-2 * fly.t + 2, 2) / 2;
    cam.position.lerpVectors(fly.a, fly.b, e); ctl.target.lerpVectors(fly.at, fly.bt, e);
    if (fly.t >= 1) fly = null;
  }
  // Encuadre: el centro de la vista se corre a la derecha de la columna de tarjetas
  const w = stage.clientWidth, h = stage.clientHeight, dw = dock.childElementCount ? dock.offsetWidth + 18 : 0;
  if (w && h && (cam.view?.fullWidth !== w + dw || cam.view?.height !== h || !cam.view?.enabled)) { cam.setViewOffset(w + dw, h, 0, 0, w, h); cam.aspect = (w + dw) / h; cam.updateProjectionMatrix(); }
  else if (w && h && Math.abs(cam.aspect - (w + dw) / h) > 1e-3) { cam.aspect = (w + dw) / h; cam.updateProjectionMatrix(); }
  const s = STOPS[cur];
  if (s && s.tick) s.tick(dt, (now - t0) / 1000, s.steps[step]);
  placeLabels();
};
STOPS.forEach(s => s.setRestart && s.setRestart(() => { t0 = performance.now(); }));
{ // clic sobre una miniatura del inicio
  const ray = new THREE.Raycaster(), ndc = new THREE.Vector2(); let down0 = null;
  const cv = stage.shadowRoot.querySelector('canvas');
  cv.addEventListener('pointerdown', e => { down0 = [e.clientX, e.clientY]; });
  cv.addEventListener('pointerup', e => {
    if (!down0 || Math.hypot(e.clientX - down0[0], e.clientY - down0[1]) > 5) return;
    const q = cv.getBoundingClientRect(); ndc.set((e.clientX - q.left) / q.width * 2 - 1, -(e.clientY - q.top) / q.height * 2 + 1);
    ray.setFromCamera(ndc, cam);
    if (cur === 0 && STOPS[0].pick) { const k = STOPS[0].pick(ray); if (k) enterStop(k); }
    else if (STOPS[cur].onClick) STOPS[cur].onClick(ray, STOPS[cur].steps[step]);
  });
}
window.__labs = { go, move, setDeep, get cur() { return cur; }, get step() { return step; }, STOPS };
go(0, 0);
