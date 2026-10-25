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
function label(anchor, html, { cls = '', down = false, onClick = null, id = '' } = {}) {
  const el = document.createElement('div');
  el.className = 'lbl ' + cls + (onClick ? ' click' : '');
  el.innerHTML = down ? `<div class="dot"></div><div class="stem"></div><div class="box">${html}</div>` : `<div class="box">${html}</div><div class="stem"></div><div class="dot"></div>`;
  if (onClick) el.addEventListener('click', onClick);
  el.dataset.id = id; el.hidden = true; host.appendChild(el);
  const L = { el, anchor, on: false, set(h) { el.querySelector('.box').innerHTML = h; } };
  labels.push(L); return L;
}
function placeLabels() {
  const r = host.getBoundingClientRect();
  for (const L of labels) {
    if (!L.on) continue;
    const p = L.anchor.isVector3 ? v.copy(L.anchor) : L.anchor.getWorldPosition(v);
    p.project(cam);
    const vis = p.z < 1 && Math.abs(p.x) < 1.1 && Math.abs(p.y) < 1.1;
    L.el.hidden = !vis;
    if (vis) {
      const x = (p.x + 1) / 2 * r.width, y = (1 - p.y) / 2 * r.height;
      const down = L.el.firstElementChild.classList.contains('dot');
      L.el.style.transform = `translate(${x}px, ${y}px) translate(-50%, ${down ? '0' : '-100%'})`;
    }
  }
}

const root = new THREE.Group(); root.name = 'labs_m6_m14';
const ctx = { THREE, scene, cam, label, go: (s, i) => go(s, i) };
const STOPS = [buildInicio(ctx), buildM6(ctx), buildM14(ctx)];
STOPS.forEach(s => root.add(s.group));
stage.setObject(root);
scene.add(new THREE.AmbientLight(0xffffff, 0.55));
cam.near = 0.1; cam.far = 1500; cam.updateProjectionMatrix();
ctl.maxPolarAngle = Math.PI * 0.495; ctl.minDistance = 2; ctl.maxDistance = 400;
if (stage._toolbar) stage._toolbar.style.display = 'none';

// ---------- Tarjetas ----------
const STAMP = { df: 'Dato de fuente', il: 'Ilustrativo' };
export function cardHTML(c) {
  const stamp = c.stamp ? `<span class="st ${c.stamp}">${STAMP[c.stamp]}</span>${c.cite ? `<span class="cite">(${c.cite})</span>` : ''}` : '';
  const ref = c.ref ? `<span class="ref">${c.ref}</span>` : '';
  const fig = c.fig ? `<div class="fig"><div class="ft">${c.fig.title}</div><img src="${c.fig.src}" alt="${c.fig.alt || ''}" data-fig><div class="cr">${c.fig.credit}</div></div>` : '';
  if (c.fold) return `<details class="card" data-card><summary>${c.title}</summary>${c.body}</details>`;
  return `<div class="card${c.wide ? ' wide' : ''}" data-card>${(ref || stamp) ? `<div class="ch">${ref}${stamp}</div>` : ''}${c.title ? `<h4>${c.title}</h4>` : ''}${c.body || ''}${fig}</div>`;
}
const dock = document.getElementById('dock');
dock.addEventListener('click', e => {
  const img = e.target.closest('img[data-fig]'); if (!img) return;
  const f = img.closest('.fig');
  document.getElementById('figbody').innerHTML = `<div class="ft" style="font-weight:600;margin-bottom:8px">${f.querySelector('.ft').innerHTML}</div><img src="${img.src}" alt=""><div class="cr" style="margin-top:8px;font-size:12px;color:#9AA6B1;font-style:italic">${f.querySelector('.cr').innerHTML}</div>`;
  document.getElementById('figbox').hidden = false;
});
document.querySelectorAll('[data-close]').forEach(b => b.addEventListener('click', closeOverlays));
document.querySelectorAll('.overlay').forEach(o => o.addEventListener('click', e => { if (e.target === o) closeOverlays(); }));
function closeOverlays() { document.querySelectorAll('.overlay').forEach(o => o.hidden = true); }

// ---------- Navegación ----------
let cur = -1, step = 0, deepNav = false, t0 = performance.now();
const $ = id => document.getElementById(id);
const order = s => deepNav ? s.steps : s.steps.filter(x => x.level === 'RP');
function go(si, idx = 0) {
  const s = STOPS[si];
  if (si !== cur) { STOPS.forEach((x, i) => { x.group.visible = i === si; }); cur = si; buildAside(s); }
  step = Math.max(0, Math.min(idx, s.steps.length - 1));
  const st = s.steps[step];
  labels.forEach(L => { L.on = false; L.el.hidden = true; });
  (st.labels || []).forEach(L => { L.on = true; });
  dock.innerHTML = (st.cards || []).map(cardHTML).join('');
  dock.scrollTop = 0;
  $('start').hidden = !st.start; if (st.start) $('start').innerHTML = st.start;
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
$('deepBtn').onclick = () => setDeep(!deepNav);
document.querySelectorAll('#tabs [data-tab]').forEach(b => b.onclick = () => showTab(b.dataset.tab)); $('refBtn').onclick = showRefs;
document.querySelectorAll('#stops [data-stop]').forEach(b => b.onclick = () => go(+b.dataset.stop, 0));
addEventListener('keydown', e => {
  if (e.target.closest && e.target.closest('input,textarea')) return;
  if (e.key === 'Escape') return closeOverlays();
  if ('012'.includes(e.key) && e.key.length === 1) { closeOverlays(); go(+e.key, 0); }
  else if (e.key === 'ArrowRight') { closeOverlays(); move(1); }
  else if (e.key === 'ArrowLeft') { closeOverlays(); move(-1); }
  else if (e.key === 'p' || e.key === 'P') setDeep(!deepNav);
  else if (e.key === 'r' || e.key === 'R') { const o = $('refbox').hidden; closeOverlays(); if (o) showRefs(); }
});

// ---------- Cámara ----------
let fly = null;
function flyTo([x, y, z, tx, ty, tz]) {
  fly = { a: cam.position.clone(), b: new THREE.Vector3(x, y, z), at: ctl.target.clone(), bt: new THREE.Vector3(tx, ty, tz), t: 0 };
}
let last = performance.now();
stage.onFrame = () => {
  const now = performance.now(), dt = Math.min(0.05, (now - last) / 1000); last = now;
  if (fly) {
    fly.t = Math.min(1, fly.t + dt / 1.1);
    const e = fly.t < 0.5 ? 2 * fly.t * fly.t : 1 - Math.pow(-2 * fly.t + 2, 2) / 2;
    cam.position.lerpVectors(fly.a, fly.b, e); ctl.target.lerpVectors(fly.at, fly.bt, e);
    if (fly.t >= 1) fly = null;
  }
  const s = STOPS[cur];
  if (s && s.tick) s.tick(dt, (now - t0) / 1000, s.steps[step]);
  placeLabels();
};
window.__labs = { go, move, setDeep, get cur() { return cur; }, get step() { return step; }, STOPS };
go(0, 0);
