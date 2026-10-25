// Prueba de humo: abre el HTML offline (file://), recorre las paradas 0–2, toma capturas
// y verifica las reglas del proyecto. Uso: npm run check   (o: node tests/smoke.mjs [archivo.html])
// Estructura tomada de recorrido-3d/tests/smoke.mjs; las verificaciones por escena se agregan con cada commit.
import { chromium } from 'playwright';
import { mkdir, readFile } from 'node:fs/promises';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { dirname, join, resolve } from 'node:path';
const root = join(dirname(fileURLToPath(import.meta.url)), '..');
const file = resolve(process.argv[2] || join(root, 'dist/Modelo3D_Labs_M6_M14_offline.html'));
const shots = join(root, 'tests/shots'); await mkdir(shots, { recursive: true });
const fails = [];
// Términos prohibidos (contenido del recorrido del Edificio 2 / Investigación 3). Búsqueda sin mayúsculas ni tildes.
const norm = s => s.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase().replace(/\s+/g, ' ');
const BANNED = ['Edificio 2', '155 TR', 'Henríquez Espinosa', 'Hosamo']; // F. Henríquez (Gollini-Mihalopoulos et al., 2023) sí puede aparecer en el M6
const banned = (txt, where) => { const t = norm(txt); for (const b of BANNED) if (t.includes(norm(b))) fails.push(`${where}: aparece «${b}»`); };
banned((await readFile(file, 'utf8')).replace(/&nbsp;/g, ' '), 'HTML');
// En los informes no se usa la palabra «según» en ningún sentido
if (/seg[uú]n\b/i.test(norm(await readFile(join(root, 'src/app/content-m14.js'), 'utf8') + await readFile(join(root, 'src/app/content-m6.js'), 'utf8') + await readFile(join(root, 'src/app/content-inicio.js'), 'utf8') + await readFile(join(root, 'src/app/scene-m14.js'), 'utf8') + await readFile(join(root, 'src/app/scene-m6.js'), 'utf8')))) fails.push('src: aparece la palabra «según»');
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
      if (k === 0 && /octubre|entrega|2026/i.test(await pg.evaluate(() => document.getElementById('vp').innerText + document.querySelector('aside').innerText))) fails.push(`${where}: el inicio muestra una fecha`);
      await pg.screenshot({ path: join(shots, `${W}_p${k}_${String(i).padStart(2, '0')}.png`) });
    }
  }
  // Navegación: 0 = inicio; → desde el inicio entra a la parada 1; ← regresa; la nota «no a escala» siempre visible
  await pg.keyboard.press('0'); await pg.waitForTimeout(400);
  await pg.keyboard.press('ArrowRight'); await pg.waitForTimeout(400);
  if ((await pg.evaluate(() => window.__labs.cur)) !== 1) fails.push(`${W}x${H} → desde el inicio no entra a la parada 1`);
  await pg.keyboard.press('ArrowLeft'); await pg.waitForTimeout(400);
  if ((await pg.evaluate(() => window.__labs.cur)) !== 0) fails.push(`${W}x${H} ← desde la parada 1 no regresa al inicio`);
  for (const k of '012') {
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
  { const dup = await pg.evaluate(() => [...document.querySelectorAll('#labels .lbl:not([hidden]) .box')].map(b => b.innerText.replace(/\s+/g, ' ').toLowerCase()).filter(t => t.includes('controlador central vrf')).length);
    if (dup > 1) fails.push(`${W}x${H} 2.5: «Controlador central VRF» aparece ${dup} veces`); }
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
await browser.close();
if (fails.length) { console.error('FALLAS:\n' + fails.join('\n')); process.exit(1); }
console.log('OK: sin errores; capturas en ' + shots);
