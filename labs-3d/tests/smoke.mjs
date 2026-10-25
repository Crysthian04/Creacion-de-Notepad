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
        return { card: Math.max(0, ...[...document.querySelectorAll('[data-card]')].map(d)), dock: d(document.getElementById('dock')), aside: d(document.querySelector('aside')) };
      });
      for (const [kk, px] of Object.entries(ov)) if (px > 8) fails.push(`${where}: ${kk === 'aside' ? 'panel derecho' : kk === 'dock' ? 'columna de tarjetas' : 'tarjeta'} desborda ${px}px`);
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
