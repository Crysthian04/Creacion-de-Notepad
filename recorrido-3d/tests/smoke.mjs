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
    if (W >= 1920 && ov > 8) fails.push(`${W}x${H} parada ${k}: tarjetas desbordan ${ov}px`);
    await pg.screenshot({ path: join(shots, `${W}_parada_${k}.png`) });
  }
  if (!(await pg.evaluate(() => /no a escala/i.test(document.body.innerText)))) fails.push('Falta la nota "Modelo conceptual, no a escala"');
  fails.push(...errs.map(e => `${W}x${H} ${e}`));
  await pg.close();
}
await browser.close();
if (fails.length) { console.error('FALLÓ:\n- ' + fails.join('\n- ')); process.exit(1); }
console.log(`OK: sin errores; capturas en ${shots}`);
