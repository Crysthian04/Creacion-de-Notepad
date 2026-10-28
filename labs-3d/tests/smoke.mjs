// Prueba de humo: abre el HTML offline (file://), recorre las paradas 0–4, toma capturas
// y verifica las reglas del proyecto. Uso: npm run check   (o: node tests/smoke.mjs [archivo.html])
// Estructura tomada de recorrido-3d/tests/smoke.mjs; las verificaciones por escena se agregan con cada commit.
import { chromium } from 'playwright';
import { mkdir, readFile } from 'node:fs/promises';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { dirname, join, resolve } from 'node:path';
import { readdir } from 'node:fs/promises';
import { fingerprint, diff, SIZES } from './identidad.mjs';
const root = join(dirname(fileURLToPath(import.meta.url)), '..');
const file = resolve(process.argv[2] || join(root, 'dist/Modelo3D_Labs_M6_M14_offline.html'));
const shots = join(root, 'tests/shots'); await mkdir(shots, { recursive: true });
const fails = [], notes = [];
// (a) Excepciones aprobadas: etiquetas que pueden verse a 1920 y no a 1366 (o al revés). Formato: 'parada:paso:texto inicial'.
const EXCEPTIONS = [];
const visByStep = {};
// Términos prohibidos (contenido del recorrido del Edificio 2 / Investigación 3). Búsqueda sin mayúsculas ni tildes.
const norm = s => s.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase().replace(/\s+/g, ' ');
const BANNED = ['Edificio 2', '155 TR', 'Henríquez Espinosa', 'Hosamo']; // F. Henríquez (Gollini-Mihalopoulos et al., 2023) sí puede aparecer en el M6
const banned = (txt, where) => { const t = norm(txt); for (const b of BANNED) if (t.includes(norm(b))) fails.push(`${where}: aparece «${b}»`); };
banned((await readFile(file, 'utf8')).replace(/&nbsp;/g, ' '), 'HTML');
// En los informes no se usa la palabra «según» en ningún sentido
for (const f of (await readdir(join(root, 'src/app'))).filter(f => /^(content|scene)-.*\.js$/.test(f))) if (/seg[uú]n\b/i.test(norm(await readFile(join(root, 'src/app', f), 'utf8')))) fails.push(`src/app/${f}: aparece la palabra «según»`);
// Paradas 3 y 4 (M8 y M11): solo las cifras permitidas. Se quitan del texto las citas (paréntesis con año), los números
// de paso (3.0–3.5, 4.0–4.5), E1–E4, los códigos M8/M11 y, en la Parada 4, el reparto del lubricante; si queda un dígito, falla.
const ALLOWED = {
  3: [],
  4: [/\b50\s?%/g, /\b20\s?%/g, /\b10\s?%/g], // Prayogo et al. (2024, p. 401)
};
const strayDigits = (k, txt) => {
  let t = txt.replace(/\u00a0/g, ' ').replace(/\([^()]*\b(19|20)\d\d\b[^()]*\)/g, ' ').replace(new RegExp(`\\b${k}\\.[0-5]\\b`, 'g'), ' ').replace(/\bE[1-4]\b/g, ' ').replace(/\bM(8|11)\b/g, ' ').replace(new RegExp(`Parada ${k}\\b`, 'gi'), ' '); // el panel la muestra en mayúsculas (CSS)
  for (const r of ALLOWED[k]) t = t.replace(r, ' ');
  return [...new Set(t.match(/[^\s]*[0-9][^\s]*/g) || [])];
};
const BRANDS = ['Trane', 'Spirotech', 'Empower', 'Tabreed', 'Carrier', 'Daikin', 'York', 'Danfoss']; // en las Paradas 3 y 4 (las citas en mayúsculas, como EMPOWER, sí van)
const exe = process.env.CHROMIUM_PATH; // opcional: ruta a un Chromium ya instalado
const browser = await chromium.launch({ ...(exe ? { executablePath: exe } : {}), args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
for (const [W, H] of [[1920, 1080], [1366, 768]]) {
  const pg = await browser.newPage({ viewport: { width: W, height: H } });
  const errs = [];
  pg.on('pageerror', e => errs.push('pageerror: ' + e.message));
  pg.on('console', m => { if (m.type() === 'error' || m.type() === 'warning' || /Multiple instances/.test(m.text())) errs.push(`console ${m.type()}: ` + m.text()); });
  pg.on('request', q => { if (/^https?:/.test(q.url())) errs.push('red (debe ser offline): ' + q.url()); });
  await pg.goto(pathToFileURL(file).href);
  await pg.waitForFunction(() => document.querySelector('three-d-stage')?.shadowRoot?.querySelector('canvas'), null, { timeout: 30000 });
  await pg.waitForTimeout(3000);
  // Texto en pantalla de las paradas 3 y 4: columna de tarjetas, etiquetas visibles y panel derecho (sin la vista de referencias)
  const scan34 = async (k, where) => {
    const txt = await pg.evaluate(() => [document.getElementById('dock').innerText, ...[...document.querySelectorAll('#labels .lbl:not([hidden]) .box')].map(b => b.innerText), document.querySelector('aside').innerText].join('\n')); // sin el encabezado ni la barra ← → (navegación, no contenido)
    const bad = strayDigits(k, txt); if (bad.length) fails.push(`${where}: cifras no permitidas en la parada ${k}: ${bad.join(', ')}`);
    for (const b of BRANDS) if (new RegExp(`\\b${b}\\b`).test(txt)) fails.push(`${where}: aparece la marca «${b}»`);
    if (/\b(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)\b/i.test(txt)) fails.push(`${where}: aparece una fecha`);
  };
  // Todas las paradas y todos los pasos: sin desborde (tarjetas, dock y panel derecho), sin términos prohibidos
  const plan = await pg.evaluate(() => window.__labs.STOPS.map(s => s.steps.length));
  for (const [k, n] of plan.entries()) {
    for (let i = 0; i < n; i++) {
      await pg.evaluate(([k, i]) => window.__labs.go(k, i), [k, i]); await pg.waitForTimeout(i ? 1300 : 1800);
      const where = `${W}x${H} parada ${k} paso ${i}`;
      banned(await pg.evaluate(() => document.body.innerText), where);
      const ov = await pg.evaluate(() => {
        const d = el => el ? el.scrollHeight - el.clientHeight : 0;
        const dk = document.getElementById('dock'), dr = dk.getBoundingClientRect(), bt = [...document.querySelectorAll('.bottom > *')].map(e => e.getBoundingClientRect());
        const hitBottom = dk.childElementCount ? Math.max(0, ...bt.filter(b => b.left < dr.right && b.right > dr.left).map(b => dr.bottom - b.top)) : 0;
        return { card: Math.max(0, ...[...document.querySelectorAll('[data-card]')].map(d)), dock: d(dk), aside: d(document.querySelector('aside')), nota: hitBottom };
      });
      for (const [kk, px] of Object.entries(ov)) if (px > 8) fails.push(`${where}: ${{ aside: 'panel derecho', dock: 'columna de tarjetas', card: 'tarjeta', nota: 'columna de tarjetas sobre la nota o la barra ← →' }[kk]} ${kk === 'nota' ? 'se cruza' : 'desborda'} ${px}px`);
      // Etiquetas 3D encimadas (cajas visibles que se cruzan más de 2 px)
      await pg.waitForTimeout(300);
      const ovl = await pg.evaluate(() => {
        const bx = [...document.querySelectorAll('#labels .lbl:not([hidden]) .box')].map(b => ({ t: b.innerText.replace(/\s+/g, ' ').slice(0, 40), r: b.getBoundingClientRect() })).filter(o => o.r.width > 0);
        const out = [];
        for (let a = 0; a < bx.length; a++) for (let b = a + 1; b < bx.length; b++) {
          const A = bx[a].r, B = bx[b].r, ox = Math.min(A.right, B.right) - Math.max(A.left, B.left), oy = Math.min(A.bottom, B.bottom) - Math.max(A.top, B.top);
          if (ox > 0 && oy > 0) out.push(`«${bx[a].t}» / «${bx[b].t}»`);
        }
        return out;
      });
      if (ovl.length) fails.push(`${where}: etiquetas encimadas ${ovl.join('; ')}`);
      const under = await pg.evaluate(() => {
        const cs = [...document.querySelectorAll('#dock > *')].map(c => c.getBoundingClientRect());
        return [...document.querySelectorAll('#labels .lbl:not([hidden]) .box')].filter(b => { const r = b.getBoundingClientRect(); return r.width > 0 && cs.some(q => r.left < q.right && r.right > q.left && r.top < q.bottom && r.bottom > q.top); }).map(b => b.innerText.replace(/\s+/g, ' ').slice(0, 40));
      });
      if (under.length) fails.push(`${where}: etiquetas bajo una tarjeta ${under.join('; ')}`);
      const outside = await pg.evaluate(() => {
        const v = document.getElementById('vp').getBoundingClientRect();
        return [...document.querySelectorAll('#labels .lbl:not([hidden]) .box')].filter(b => { const r = b.getBoundingClientRect(); return r.width > 0 && (r.top < v.top || r.bottom > v.bottom || r.left < v.left || r.right > v.right); }).map(b => b.innerText.replace(/\s+/g, ' ').slice(0, 40));
      });
      if (outside.length) fails.push(`${where}: etiquetas fuera del visor ${outside.join('; ')}`);
      if (k >= 3) await scan34(k, where);
      if (k === 0 && /octubre|entrega|2026/i.test(await pg.evaluate(() => document.getElementById('vp').innerText + document.querySelector('aside').innerText))) fails.push(`${where}: el inicio muestra una fecha`);
      // (a) mismo conjunto de etiquetas visibles a 1366 y a 1920
      const vset = await pg.evaluate(() => [...document.querySelectorAll('#labels .lbl:not([hidden])')].map(l => l.dataset.i + '|' + l.querySelector('.box').innerText.replace(/\s+/g, ' ').slice(0, 34)));
      const key = `${k}:${i}`, sid = await pg.evaluate(([k, i]) => window.__labs.STOPS[k].steps[i].n, [k, i]);
      if (W === 1920) visByStep[key] = vset;
      else {
        const ids = v => v.map(x => x.split('|')[0]), a = visByStep[key] || [], miss = a.filter(x => !ids(vset).includes(x.split('|')[0])), extra = vset.filter(x => !ids(a).includes(x.split('|')[0]));
        for (const x of [...miss.map(x => ['solo a 1920', x]), ...extra.map(x => ['solo a 1366', x])]) {
          const txt = x[1].split('|')[1], exc = EXCEPTIONS.some(e => e === `${k}:${sid}:${txt.slice(0, 20)}`);
          (exc ? notes : fails).push(`parada ${k} paso ${sid}: «${txt}» ${x[0]}${exc ? ' (excepción aprobada)' : ''}`);
        }
      }
      await pg.screenshot({ path: join(shots, `${W}_p${k}_${String(i).padStart(2, '0')}.png`) });
    }
  }
  // (d) rótulos y (e) chips: datos de las escenas
  if (W === 1920) {
    const data = await pg.evaluate(() => window.__labs.STOPS.slice(1).map(s => ({ short: s.short, steps: s.steps.map(x => ({ id: x.id, n: x.n, level: x.level, rot: x.rot, chips: x.chips })) })));
    const words = h => (h || '').replace(/<[^>]+>/g, ' ').replace(/&nbsp;/g, ' ').trim().split(/\s+/).filter(w => /[\p{L}\p{N}]/u.test(w)).length; // los signos sueltos (%, ·, =) no cuentan como palabra
    for (const s of data) {
      const scenes = s.steps.filter(x => x.level === 'RP');
      if (scenes.length !== 4) fails.push(`${s.short}: la ruta principal tiene ${scenes.length} escenas, no 4`);
      for (const e of scenes) {
        const r = e.rot || {};
        if (words(r.f) > 25) fails.push(`${s.short} ${e.n}: la frase tiene ${words(r.f)} palabras (máximo 25)`);
        if (r.c && words(r.c) > 12) fails.push(`${s.short} ${e.n}: la cifra tiene ${words(r.c)} palabras (máximo 12)`);
        if (!r.f || (!r.fc && !['pr', 'si'].includes(r.stamp)) || !r.stamp || !r.ref) fails.push(`${s.short} ${e.n}: al rótulo le falta frase, cita, sello o referencia`); // la propuesta y la síntesis del informe no llevan cita
        notes.push(`Rótulo ${s.short} ${e.n}: frase ${words(r.f)} palabras${r.c ? `, cifra ${words(r.c)}` : ''}`);
      }
      for (const d of s.steps.filter(x => x.level === 'PR')) {
        const n = scenes.filter(e => (e.chips || []).includes(d.id)).length;
        if (n !== 1) fails.push(`${s.short} paso ${d.n}: enlazado desde ${n} escenas (debe ser 1)`);
      }
    }
  }
  // (c) simulación de la E2 del M6: diseño igual en los 8 terminales; red sin balancear con todo abierto;
  // existe al menos una combinación con los 8 dentro de ±5 %; cerrar un paso baja su caudal y sube los demás; reabrir regresa (±1 %)
  if (W === 1920) {
    const r = await pg.evaluate(() => { const s = window.__labs.STOPS[1].sim; s.reset(); const open = s.flows(), out = { open, pos: s.positions, bal: s.flows(s.balanced), count: s.search(), mono: [] };
      for (let i = 0; i < 8; i++) for (let k = 0; k < s.positions - 1; k++) { const st = new Array(8).fill(0); st[i] = k; const a = s.flows(st); st[i] = k + 1; const b = s.flows(st); out.mono.push({ i, k, ok: b[i] < a[i] && b.every((v, j) => j === i || v > a[j]) }); }
      for (let i = 0; i < 8; i++) { const a = s.flows(); s.set(i, s.positions - 1); s.set(i, 0); const c = s.flows(); if (!c.every((v, j) => Math.abs(v - a[j]) <= 0.01 * a[j])) out.mono.push({ i, k: 'reabrir', ok: false }); }
      s.reset(); return out; });
    if (r.pos < 6) fails.push(`E2 M6: la compuerta tiene ${r.pos} posiciones (se piden unas 6)`);
    if (!r.open.some(v => v > 1.05) || !r.open.some(v => v < 0.95)) fails.push(`E2 M6: con todo abierto no hay terminales arriba y abajo de la franja (${r.open.map(v => v.toFixed(2))})`);
    if (!r.bal.every(v => Math.abs(v - 1) <= 0.05) || r.count < 1) fails.push(`E2 M6: no existe una combinación con los 8 dentro de ±5 % (encontradas ${r.count})`);
    for (const m of r.mono.filter(m => !m.ok)) fails.push(`E2 M6: falla la monotonía en la compuerta ${m.i}, paso ${m.k}`);
    notes.push(`E2 M6: con todo abierto, relación medido/diseño = ${r.open.map(v => (v * 100).toFixed(0) + ' %').join(', ')}; combinaciones simétricas balanceadas: ${r.count} de 1,296`);
  }
  // (a) estados interactivos y fases de las animaciones: mismo conjunto de etiquetas a 1366 y a 1920
  const vsetNow = () => pg.evaluate(() => [...document.querySelectorAll('#labels .lbl:not([hidden])')].map(l => l.dataset.i + '|' + l.querySelector('.box').innerText.replace(/\s+/g, ' ').slice(0, 34)));
  const goId = (k, id) => pg.evaluate(([k, id]) => window.__labs.go(k, window.__labs.STOPS[k].steps.findIndex(x => x.id === id)), [k, id]);
  const STATES = [
    ['M6 E2 compuerta cerrada', async () => { await goId(1, 'E2'); await pg.waitForTimeout(1600); await pg.evaluate(() => window.__labs.STOPS[1].sim.set(3, 5)); await pg.waitForTimeout(800); }],
    ['M6 E2 comparar métodos', async () => { await pg.click('#cmpBtn'); await pg.waitForTimeout(5000); }],
    ...['100', '200', '300', '350', '400', '500'].map(n => [`M14 E2 LOD ${n}`, async () => { if (n === '100') { await goId(2, 'E2'); await pg.waitForTimeout(1600); } await pg.click(`[data-lod="${n}"]`); await pg.waitForTimeout(500); }]),
    ['M14 E3 ficha de activo', async () => { await goId(2, 'E3'); await pg.waitForTimeout(1600); await pg.evaluate(() => window.__labs.STOPS[2].openFicha(3)); await pg.waitForTimeout(500); }],
    ['M14 E1 planta', async () => { await goId(2, 'E1'); await pg.waitForTimeout(3000); }],
    ['M14 E1 zona de estudio', async () => { await pg.waitForTimeout(9000); }],
    ['M14 E4 hoy', async () => { await goId(2, 'E4'); await pg.waitForTimeout(2500); }],
    ['M14 E4 coordinado', async () => { await pg.waitForTimeout(4000); }],
    ['M14 E4 as-built', async () => { await pg.waitForTimeout(4500); }],
    ['M8 E4 zonas, final', async () => { await goId(3, 'E4'); await pg.waitForTimeout(8000); }],
    ['M8 E3 corte del edificio', async () => { await goId(3, 'E3'); await pg.waitForTimeout(3000); }],
    ['M11 E1 sarro, final', async () => { await goId(4, 'E1'); await pg.waitForTimeout(14000); }],
    ['M11 E2 limpieza en curso', async () => { await goId(4, 'E2'); await pg.waitForTimeout(6000); }],
    ['M11 E2 tubo limpio', async () => { await pg.waitForTimeout(12000); }],
    ['M11 E3 aceite', async () => { await goId(4, 'E3'); await pg.waitForTimeout(3000); }],
    ['M11 E4 vista dividida', async () => { await goId(4, 'E4'); await pg.waitForTimeout(3000); }],
  ];
  for (const [name, act] of STATES) {
    await act(); const v = await vsetNow(), key = 'estado:' + name;
    if (W === 1920) visByStep[key] = v;
    else { const ids = x => x.map(y => y.split('|')[0]), a = visByStep[key] || [];
      for (const x of a.filter(y => !ids(v).includes(y.split('|')[0]))) fails.push(`${name}: «${x.split('|')[1]}» solo a 1920`);
      for (const x of v.filter(y => !ids(a).includes(y.split('|')[0]))) fails.push(`${name}: «${x.split('|')[1]}» solo a 1366`); }
    const out = await pg.evaluate(() => { const vp = document.getElementById('vp').getBoundingClientRect(); return [...document.querySelectorAll('#labels .lbl:not([hidden]) .box')].filter(b => { const r = b.getBoundingClientRect(); return r.top < vp.top || r.bottom > vp.bottom || r.left < vp.left || r.right > vp.right; }).length; });
    if (out) fails.push(`${W}x${H} ${name}: ${out} etiquetas fuera del visor`);
    if (/^M(8|11) /.test(name)) await scan34(name.startsWith('M8') ? 3 : 4, `${W}x${H} ${name}`);
    if (W === 1366) await pg.screenshot({ path: join(shots, `${W}_estado_${name.replace(/[^\w]+/g, '_')}.png`) });
  }
  // Escenas narrativas: se reproducen una vez y se quedan en el estado final (M14 E1 a los 60 s sigue en la zona de estudio)
  if (W === 1920) {
    await goId(2, 'E1'); await pg.waitForTimeout(60000);
    const z = await pg.evaluate(() => [...document.querySelectorAll('#labels .lbl:not([hidden]) .box')].some(b => /zona de estudio/.test(b.innerText)));
    if (!z) fails.push('M14 E1: a los 60 s ya no está en la zona de estudio (debe quedarse en el estado final)');
    const sheet = await pg.evaluate(() => { window.__labs.go(2, window.__labs.STOPS[2].steps.findIndex(x => x.id === 'E4')); return true; }); await pg.waitForTimeout(20000);
    const ab = await pg.evaluate(() => [...document.querySelectorAll('#labels .lbl:not([hidden]) .box')].map(b => b.innerText).join(' | '));
    if (!/as-built de D y E/i.test(ab)) fails.push('M14 E4: a los 20 s no está en la fase as-built (debe quedarse en el estado final)');
    if (!(await pg.evaluate(() => !!document.querySelector('[data-replay]')))) fails.push('M14 E4: falta el botón «↺ Repetir»');
    // M8 E4: las cuatro zonas siguen visibles; M11 E1: la capa sigue formada; M11 E2: el tubo queda limpio (estado final)
    await goId(3, 'E4'); await pg.waitForTimeout(40000);
    { const z = await pg.evaluate(() => window.__labs.STOPS[3].probe()); if (z.zones !== 4) fails.push(`M8 E4: a los 40 s se ven ${z.zones} zonas, no 4`); }
    await goId(4, 'E1'); await pg.waitForTimeout(40000);
    { const z = await pg.evaluate(() => window.__labs.STOPS[4].probe()); if (z.deposits < 300) fails.push(`M11 E1: a los 40 s la capa ya no está formada (${z.deposits} depósitos)`); }
    await goId(4, 'E2'); await pg.waitForTimeout(40000);
    { const z = await pg.evaluate(() => window.__labs.STOPS[4].probe()); if (z.deposits > 0 || z.bubbles) fails.push(`M11 E2: a los 40 s el tubo no quedó limpio y en reposo (${z.deposits} depósitos, burbujas: ${z.bubbles})`); }
    for (const [k, id] of [[3, 'E4'], [4, 'E1'], [4, 'E2']]) { await goId(k, id); await pg.waitForTimeout(400); if (!(await pg.evaluate(() => !!document.querySelector('[data-replay]')))) fails.push(`parada ${k} ${id}: falta el botón «↺ Repetir»`); }
  }
  // Navegación: 0 = inicio; → desde el inicio entra a la parada 1; ← regresa; la nota «no a escala» siempre visible
  await pg.keyboard.press('0'); await pg.waitForTimeout(400);
  await pg.keyboard.press('ArrowRight'); await pg.waitForTimeout(400);
  if ((await pg.evaluate(() => window.__labs.cur)) !== 1) fails.push(`${W}x${H} → desde el inicio no entra a la parada 1`);
  await pg.keyboard.press('ArrowLeft'); await pg.waitForTimeout(400);
  if ((await pg.evaluate(() => window.__labs.cur)) !== 0) fails.push(`${W}x${H} ← desde la parada 1 no regresa al inicio`);
  // Las flechas pasan de la parada 2 a la 3 y de la 3 a la 4 (y regresan)
  for (const [from, to] of [[2, 3], [3, 4]]) {
    const last = await pg.evaluate(k => { const s = window.__labs.STOPS[k]; return s.steps.findIndex(x => x.id === 'E4'); }, from);
    await pg.evaluate(([k, i]) => window.__labs.go(k, i), [from, last]); await pg.waitForTimeout(300);
    await pg.keyboard.press('ArrowRight'); await pg.waitForTimeout(400);
    const at = await pg.evaluate(() => [window.__labs.cur, window.__labs.STOPS[window.__labs.cur].steps[window.__labs.step].id]);
    if (at[0] !== to || at[1] !== 'E1') fails.push(`${W}x${H} → desde E4 de la parada ${from} no entra a E1 de la parada ${to} (${at})`);
    await pg.keyboard.press('ArrowLeft'); await pg.waitForTimeout(400);
    const back = await pg.evaluate(() => [window.__labs.cur, window.__labs.STOPS[window.__labs.cur].steps[window.__labs.step].id]);
    if (back[0] !== from || back[1] !== 'E4') fails.push(`${W}x${H} ← desde E1 de la parada ${to} no regresa a E4 de la parada ${from} (${back})`);
  }
  // Encabezado: título del grupo y autor de cada parada
  const AUTH = ['Cristian Batista y Manuel Jiménez', 'Cristian Batista', 'Cristian Batista', 'Manuel Jiménez', 'Manuel Jiménez'];
  for (const k of [0, 1, 2, 3, 4]) {
    await pg.evaluate(k => window.__labs.go(k, 0), k); await pg.waitForTimeout(200);
    const hd = await pg.evaluate(() => ({ h1: document.querySelector('.hd h1').textContent, a: document.getElementById('autor').textContent, rows: Math.round(document.querySelector('.hd').getBoundingClientRect().height) }));
    if (hd.h1 !== 'Laboratorios del Grupo A · Modelo 3D' || hd.a !== AUTH[k]) fails.push(`${W}x${H} parada ${k}: encabezado «${hd.h1}» / autor «${hd.a}»`);
  }
  // Inicio: cuatro miniaturas en el orden 1 M6, 2 M14, 3 M8, 4 M11, con sus 4 escenas y sin cifras
  await pg.keyboard.press('0'); await pg.waitForTimeout(1500);
  { const mins = await pg.evaluate(() => [...document.querySelectorAll('#labels .lbl:not([hidden]) .box')].map(b => b.innerText.replace(/\s+/g, ' ')));
    const want = ['1 · M6', '2 · M14', '3 · M8', '4 · M11'];
    if (mins.length !== 4 || !want.every(w => mins.some(m => m.includes(w)))) fails.push(`${W}x${H} inicio: no se ven las 4 miniaturas (${mins.length})`);
    const sc = await pg.evaluate(() => window.__labs.STOPS.slice(1).map(s => s.steps.filter(x => x.level === 'RP').map(x => x.title)));
    sc.forEach((titles, i) => { const m = mins.find(x => x.includes(want[i])) || ''; for (const t of titles) if (!m.includes(t)) fails.push(`${W}x${H} inicio: la miniatura ${want[i]} no muestra «${t}»`); });
    if (mins.some(m => /\d/.test(m.replace(/^.*?(\d) · M(6|14|8|11)/, '').replace(/M(6|14|8|11)/g, '')))) fails.push(`${W}x${H} inicio: una miniatura muestra cifras`); }
  for (const k of '01234') {
    await pg.keyboard.press(k); await pg.waitForTimeout(1500); // desde el inicio, la cámara entra en la miniatura (≈ 1 s)
    if ((await pg.evaluate(() => window.__labs.cur)) !== +k) fails.push(`${W}x${H} la tecla ${k} no abre la parada ${k}`);
    if (!/no a escala/.test(await pg.evaluate(() => document.getElementById('note').innerText))) fails.push(`${W}x${H} parada ${k}: falta «no a escala»`);
  }
  // Parada 1: la tecla R y el botón «Referencias» abren las referencias del M6 (10 obras del Word)
  for (const how of ['tecla', 'botón']) {
    await pg.keyboard.press('1'); await pg.waitForTimeout(400);
    if (how === 'tecla') await pg.keyboard.press('r'); else await pg.click('#refBtn');
    await pg.waitForTimeout(300);
    const rf = await pg.evaluate(() => ({ open: !document.getElementById('refbox').hidden, h: document.querySelector('#refbody h3')?.textContent, n: document.querySelectorAll('#refbody p').length, t: document.getElementById('refbody').innerText }));
    if (!rf.open || !/M6/.test(rf.h || '') || rf.n !== 10 || !/Pedranzini/.test(rf.t)) fails.push(`${W}x${H} parada 1 (${how}): no abre las referencias del M6 (${JSON.stringify({ open: rf.open, h: rf.h, n: rf.n })})`);
    if (W === 1366 && how === 'tecla') await pg.screenshot({ path: join(shots, `${W}_p1_referencias.png`) });
    await pg.keyboard.press('Escape');
  }
  // Paradas 3 y 4: referencias del Word (M8: 4; M11: 4, con Prayogo et al. y Yao)
  for (const [k, n, must] of [[3, 4, ['TRABEED. (2024)', 'IDEA. (2023)', 'ASHRAE. (2024)', 'EMPOWER. (2024)']], [4, 4, ['Prayogo, G. S.', 'Yao, Y. (2016)', 'ASHRAE. (2021)', 'DIRECT, S. (2023']]]) {
    await pg.keyboard.press(String(k)); await pg.waitForTimeout(400); await pg.keyboard.press('r'); await pg.waitForTimeout(300);
    const rf = await pg.evaluate(() => ({ h: document.querySelector('#refbody h3')?.textContent, n: document.querySelectorAll('#refbody p').length, t: document.getElementById('refbody').innerText }));
    if (!new RegExp(`M${k === 3 ? 8 : 11}`).test(rf.h || '') || rf.n !== n || !must.every(m => rf.t.includes(m))) fails.push(`${W}x${H} parada ${k}: referencias incompletas (${rf.n}: ${must.filter(m => !rf.t.includes(m)).join(', ')})`);
    if (W === 1366) await pg.screenshot({ path: join(shots, `${W}_p${k}_referencias.png`) });
    await pg.keyboard.press('Escape');
  }
  // Parada 1 · leyes de los ventiladores: barras sin cifras y rótulo exacto del Word
  const li = await pg.evaluate(() => window.__labs.STOPS[1].steps.findIndex(s => s.id === 'leyes'));
  await pg.evaluate(i => window.__labs.go(1, i), li); await pg.waitForTimeout(600);
  await pg.click('#spd80'); await pg.waitForTimeout(300);
  const lw = await pg.evaluate(() => ({ rot: document.getElementById('rot').innerText.replace(/\u00a0/g, ' '), hot: document.getElementById('rot').classList.contains('hot'), bars: [...document.querySelectorAll('.laws .bar')].map(b => b.innerText).join('|') }));
  if (!lw.rot.includes('Reducir la velocidad del ventilador un 20 % disminuye su potencia un 50 %') || !lw.hot) fails.push(`${W}x${H} leyes: rótulo del 80 % incorrecto`);
  if (/\d/.test(lw.bars.replace(/N[²³]/g, ''))) fails.push(`${W}x${H} leyes: las barras muestran cifras (${lw.bars})`);
  // Parada 1 · contadores: proporción llega a 14 y flujo progresivo a 10
  for (const [id, want, wait] of [['proporcion', '14', 21500], ['progresivo', '10', 14000]]) {
    const i = await pg.evaluate(id => window.__labs.STOPS[1].steps.findIndex(s => s.id === id), id);
    await pg.evaluate(i => window.__labs.go(1, i), i); await pg.waitForTimeout(wait);
    const c = await pg.evaluate(() => document.querySelector('[data-cnt]')?.textContent);
    if (c !== want) fails.push(`${W}x${H} ${id}: el contador llega a ${c}, no a ${want}`);
    if (W === 1366) await pg.screenshot({ path: join(shots, `${W}_p1_${id}_final.png`) });
  }
  // Parada 2 (M14)
  const step2 = id => pg.evaluate(id => window.__labs.go(2, window.__labs.STOPS[2].steps.findIndex(s => s.id === id)), id);
  const txt = sel => pg.evaluate(sel => [...document.querySelectorAll(sel)].map(e => e.offsetParent || e.closest('#labels') ? e.innerText : '').join(' | ').replace(/\u00a0/g, ' '), sel);
  const visLabels = () => pg.evaluate(() => [...document.querySelectorAll('#labels .lbl:not([hidden]) .box')].map(b => b.innerText.replace(/\s+/g, ' ')).join(' | ').replace(/\u00a0/g, ' '));
  await pg.keyboard.press('2'); await pg.waitForTimeout(400); await pg.keyboard.press('r'); await pg.waitForTimeout(300);
  const r14 = await pg.evaluate(() => ({ h: document.querySelector('#refbody h3')?.textContent, n: document.querySelectorAll('#refbody p').length, t: document.getElementById('refbody').innerText }));
  if (!/M14/.test(r14.h || '') || r14.n !== 9 || !/Khanzode/.test(r14.t)) fails.push(`${W}x${H} parada 2: no abre las 9 referencias del M14 (${r14.n})`);
  await pg.keyboard.press('Escape');
  await step2('mep'); await pg.waitForTimeout(1800);
  { const vl = await visLabels(); if (!/medidor de energía propuesto/i.test(vl) || !/Propuesta · M14 · Figura 3/i.test(vl)) fails.push(`${W}x${H} 2.5: el rótulo del medidor propuesto (con su sello de propuesta) no se ve en la escena`); }
  // Niveles de la Figura 3: de arriba abajo deben leerse 4 → 3 → 2 (2.5, P1 y E3)
  for (const id of ['mep', 'inspector', 'E3']) {
    await step2(id); await pg.waitForTimeout(1600);
    const ord = await pg.evaluate(() => [...document.querySelectorAll('#labels .lbl:not([hidden]) .box')].map(b => ({ t: b.innerText.trim(), y: b.getBoundingClientRect().top })).filter(o => /^Nivel [234]/.test(o.t)).sort((a, b) => a.y - b.y).map(o => o.t[6]).join(''));
    if (ord !== '432') fails.push(`${W}x${H} ${id}: los niveles se leen ${ord || '(ninguno)'} de arriba abajo, no 432`);
  }
  // Ficha de activo (E3 del M14): campos vacíos y nota de COBie
  await step2('E3'); await pg.waitForTimeout(800); await pg.evaluate(() => window.__labs.STOPS[2].openFicha(3)); await pg.waitForTimeout(300);
  { const f = await txt('#fichaCard'); if (!/Fabricante: —/.test(f) || !/COBie/.test(f) || !/PROPUESTA|Propuesta/.test(f)) fails.push(`${W}x${H} E3 M14: la ficha de activo no muestra los campos vacíos y la nota de COBie`); }
  // Chip «Detalle» y botón «← Volver a la escena»
  await pg.evaluate(() => window.__labs.go(1, 0)); await pg.waitForTimeout(600);
  await pg.click('[data-chip]'); await pg.waitForTimeout(500);
  if (await pg.evaluate(() => document.getElementById('back').hidden)) fails.push(`${W}x${H}: al entrar por un chip no aparece «← Volver a la escena»`);
  await pg.click('#back'); await pg.waitForTimeout(500);
  if ((await pg.evaluate(() => window.__labs.step)) !== 0) fails.push(`${W}x${H}: «← Volver a la escena» no regresa a E1`);
  await step2('gemelo'); await pg.waitForTimeout(1800);
  if (!(await visLabels()).includes('Marco general (Hu et al., 2026); en REFRESH es una propuesta')) fails.push(`${W}x${H} 2.4: falta el rótulo del marco general en la escena`);
  await step2('lod'); await pg.waitForTimeout(600);
  if (!(await txt('[data-lodf="e"]')).includes('Espacio reservado para la unidad exterior junto a los Edificios D y E')) fails.push(`${W}x${H} 2.2: el LOD 100 no usa el texto de la Tabla 1`);
  await step2('ventajas'); await pg.waitForTimeout(5500);
  const t2 = await txt('.t2');
  for (const v of ['2 de 233', '40 de 25,000 h', 'USD 15,824 millones', 'USD 10,648 millones', 'USD 9,093 millones', 'Gallaher et al. (2004, p. ES-7)']) if (!t2.includes(v)) fails.push(`${W}x${H} 2.3: Tabla 2 sin «${v}»`);
  await step2('inspector'); await pg.waitForTimeout(800); await pg.click('[data-pt="M5"]'); await pg.waitForTimeout(200);
  if (!/medidor/.test(await txt('#ptinfo'))) fails.push(`${W}x${H} P1: el inspector no muestra la ficha de M5`);
  if (/\d+(\.\d+)?\s*(kW|TR|BTU|°C|%)/.test(await txt('#ptinfo'))) fails.push(`${W}x${H} P1: el inspector muestra una lectura`);
  if (errs.length) fails.push(...errs.map(e => `${W}x${H} ${e}`));
  await pg.close();
}
// Paradas 1 y 2 idénticas a la v1.0 (huella con el reloj detenido, a 1366 y 1920)
{
  const ref = JSON.parse(await readFile(join(root, 'tests/fixtures/v1_paradas_1_2.json'), 'utf8'));
  const all = await fingerprint(file);
  for (const [W, H] of SIZES) { const cur = all[`${W}x${H}`], d = diff(ref[`${W}x${H}`], cur, `v1.0 ${W}x${H}`); fails.push(...d); notes.push(`Identidad v1.0 ${W}x${H}: ${Object.keys(cur).length} estados comparados, ${d.length} diferencias`); }
}
await browser.close();
if (fails.length) { if (notes.length) console.log('NOTAS:\n' + notes.join('\n')); console.error('FALLAS:\n' + fails.join('\n')); process.exit(1); }
if (notes.length) console.log('NOTAS:\n' + notes.join('\n'));
console.log('OK: sin errores; capturas en ' + shots);
