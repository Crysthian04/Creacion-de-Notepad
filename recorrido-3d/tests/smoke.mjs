// Prueba de humo: abre el HTML offline (file://), recorre las paradas 0–6, toma capturas
// y verifica cifras fijas del compendio. Uso: npm run check   (o: node tests/smoke.mjs [archivo.html])
import { chromium } from 'playwright';
import { mkdir } from 'node:fs/promises';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { dirname, join, resolve } from 'node:path';
const root = join(dirname(fileURLToPath(import.meta.url)), '..');
const file = resolve(process.argv[2] || join(root, 'dist/Recorrido_integrado_Edificio2_offline.html'));
const shots = join(root, 'tests/shots'); await mkdir(shots, { recursive: true });
const exe = process.env.CHROMIUM_PATH; // opcional: ruta a un Chromium ya instalado
const browser = await chromium.launch({ ...(exe ? { executablePath: exe } : {}), args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
const fails = [];
for (const [W, H] of [[1920, 1080], [1366, 768]]) {
  const pg = await browser.newPage({ viewport: { width: W, height: H } });
  const errs = [];
  pg.on('pageerror', e => errs.push('pageerror: ' + e.message));
  pg.on('console', m => { if (m.type() === 'error' || /Multiple instances/.test(m.text())) errs.push('console: ' + m.text()); });
  pg.on('request', q => { if (/^https?:/.test(q.url())) errs.push('red (debe ser offline): ' + q.url()); });
  await pg.goto(pathToFileURL(file).href);
  await pg.waitForFunction(() => document.querySelector('three-d-stage')?.shadowRoot?.querySelector('canvas'), null, { timeout: 30000 });
  await pg.waitForTimeout(4000);
  for (const k of '0123456') {
    await pg.keyboard.press(k); await pg.waitForTimeout(2500);
    if (k === '4') {
      await pg.click('[data-v="80"]'); await pg.waitForTimeout(300);
      const v = await pg.evaluate(() => ['vfdP', 'vfdE', 'vfdS', 'vfdB'].map(i => document.getElementById(i)?.textContent.trim()));
      const want = ['7.68 kW', '2,764.8 kWh/mes', '48.8 %', 'B/. 474.34 /mes'];
      if (JSON.stringify(v) !== JSON.stringify(want)) fails.push(`VFD 80 %: ${v} ≠ ${want}`);
    }
    const ov = await pg.evaluate(() => { const d = document.getElementById('dock'); return d && d.scrollHeight - d.clientHeight; });
    if (ov > 8) fails.push(`${W}x${H} parada ${k}: tarjetas desbordan ${ov}px`);
    await pg.screenshot({ path: join(shots, `${W}_parada_${k}.png`) });
  }
  if (!(await pg.evaluate(() => /no a escala/i.test(document.body.innerText)))) fails.push('Falta la nota "Modelo conceptual, no a escala"');
  // Inspector: clic sobre la proyección de UMA_03 en la vista general, luego Esc
  await pg.keyboard.press('0'); await pg.waitForTimeout(2500);
  const pt = await pg.evaluate(() => {
    const s = document.querySelector('three-d-stage'), o = s._scene.getObjectByName('UMA_03_carcasa');
    const p = o.getWorldPosition(o.position.clone()).project(s._camera), r = s.shadowRoot.querySelector('canvas').getBoundingClientRect();
    return [r.left + (p.x + 1) / 2 * r.width, r.top + (1 - p.y) / 2 * r.height];
  });
  await pg.mouse.click(pt[0], pt[1]); await pg.waitForTimeout(300);
  const ins = await pg.evaluate(() => { const e = document.getElementById('inspector'); return e.hidden ? '' : e.innerText; });
  if (!/UMA 03/.test(ins) || !/Sin dato medido/.test(ins)) fails.push(`${W}x${H} inspector tras clic en UMA_03: «${ins.slice(0, 80)}»`);
  await pg.screenshot({ path: join(shots, `${W}_inspector.png`) });
  await pg.keyboard.press('Escape'); await pg.waitForTimeout(200);
  if (!(await pg.evaluate(() => document.getElementById('inspector').hidden))) fails.push(`${W}x${H} Esc no cierra el inspector`);
  // Calculadora psicrométrica (valores por defecto 30 °C/75 % → 13 °C/100 %)
  await pg.evaluate(() => { const d = document.getElementById('psy'); d.open = true; d.scrollIntoView(); });
  await pg.waitForTimeout(300);
  const psq = await pg.evaluate(() => [...document.querySelectorAll('#psQ b')].map(b => b.textContent.replace(/\s+/g, ' ').trim()));
  const psWant = ['45.14 kJ/kg', '17.74 kJ/kg', '27.40 kJ/kg', '0.393'];
  if (JSON.stringify(psq) !== JSON.stringify(psWant)) fails.push(`${W}x${H} psicrometría: ${psq} ≠ ${psWant}`);
  if (!(await pg.evaluate(() => /no medidos en el Edificio 2/.test(document.getElementById('psy').innerText)))) fails.push('Falta el aviso de valores de ejemplo en la calculadora');
  await pg.screenshot({ path: join(shots, `${W}_psicrometria.png`) });
  await pg.evaluate(() => { document.getElementById('psy').open = false; });
  await pg.keyboard.press('5'); await pg.waitForTimeout(300);
  if (!(await pg.evaluate(() => document.querySelector('[data-stop="5"]').classList.contains('on')))) fails.push(`${W}x${H} el atajo 5 dejó de funcionar tras el inspector`);
  fails.push(...errs.map(e => `${W}x${H} ${e}`));
  await pg.close();
}
await browser.close();
if (fails.length) { console.error('FALLÓ:\n- ' + fails.join('\n- ')); process.exit(1); }
console.log(`OK: sin errores; capturas en ${shots}`);
