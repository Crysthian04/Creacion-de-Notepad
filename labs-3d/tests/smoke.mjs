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
const exe = process.env.CHROMIUM_PATH; // opcional: ruta a un Chromium ya instalado
const browser = await chromium.launch({ ...(exe ? { executablePath: exe } : {}), args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
for (const [W, H] of [[1920, 1080], [1366, 768]]) {
  const pg = await browser.newPage({ viewport: { width: W, height: H } });
  const errs = [];
  pg.on('pageerror', e => errs.push('pageerror: ' + e.message));
  pg.on('console', m => { if (m.type() === 'error' || /Multiple instances/.test(m.text())) errs.push('console: ' + m.text()); });
  pg.on('request', q => { if (/^https?:/.test(q.url())) errs.push('red (debe ser offline): ' + q.url()); });
  await pg.goto(pathToFileURL(file).href);
  await pg.waitForFunction(() => document.querySelector('three-d-stage')?.shadowRoot?.querySelector('canvas'), null, { timeout: 30000 });
  await pg.waitForTimeout(3000);
  for (const k of '012') {
    await pg.keyboard.press(k); await pg.waitForTimeout(2000);
    banned(await pg.evaluate(() => document.body.innerText), `${W}x${H} parada ${k}`);
    const ov = await pg.evaluate(() => [...document.querySelectorAll('[data-card]')].map(c => c.scrollHeight - c.clientHeight).reduce((a, b) => Math.max(a, b), 0));
    if (ov > 8) fails.push(`${W}x${H} parada ${k}: tarjetas desbordan ${ov}px`);
    await pg.screenshot({ path: join(shots, `${W}_parada_${k}.png`) });
  }
  // Navegación: 0 = inicio; → desde el inicio entra a la parada 1; ← regresa; la nota «no a escala» siempre visible
  await pg.keyboard.press('0'); await pg.waitForTimeout(400);
  await pg.keyboard.press('ArrowRight'); await pg.waitForTimeout(400);
  if ((await pg.evaluate(() => window.__labs.cur)) !== 1) fails.push(`${W}x${H} → desde el inicio no entra a la parada 1`);
  await pg.keyboard.press('ArrowLeft'); await pg.waitForTimeout(400);
  if ((await pg.evaluate(() => window.__labs.cur)) !== 0) fails.push(`${W}x${H} ← desde la parada 1 no regresa al inicio`);
  for (const k of '012') {
    await pg.keyboard.press(k); await pg.waitForTimeout(300);
    if ((await pg.evaluate(() => window.__labs.cur)) !== +k) fails.push(`${W}x${H} la tecla ${k} no abre la parada ${k}`);
    if (!/no a escala/.test(await pg.evaluate(() => document.getElementById('note').innerText))) fails.push(`${W}x${H} parada ${k}: falta «no a escala»`);
  }
  if (errs.length) fails.push(...errs.map(e => `${W}x${H} ${e}`));
  await pg.close();
}
await browser.close();
if (fails.length) { console.error('FALLAS:\n' + fails.join('\n')); process.exit(1); }
console.log('OK: sin errores; capturas en ' + shots);
