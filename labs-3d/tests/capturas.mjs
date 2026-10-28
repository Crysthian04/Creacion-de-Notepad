// Capturas de entrega (1366×768 y 1920×1080) en tests/shots/entrega: inicio y las 8 escenas de las Paradas 3 y 4,
// más la captura limpia del inicio a 1920×1080 (Playwright no dibuja el cursor). Uso: node tests/capturas.mjs
import { chromium } from 'playwright';
import { mkdir } from 'node:fs/promises';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { dirname, join } from 'node:path';
const root = join(dirname(fileURLToPath(import.meta.url)), '..'), out = join(root, 'tests/shots/entrega');
await mkdir(out, { recursive: true });
const exe = process.env.CHROMIUM_PATH;
const b = await chromium.launch({ ...(exe ? { executablePath: exe } : {}), args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'] });
// Espera de cada escena: las narrativas se capturan en su estado final; E2 del M11, a media limpieza y al final
const SC = [[3, 'E1', 6000], [3, 'E2', 6000], [3, 'E3', 6000], [3, 'E4', 9000], [4, 'E1', 14000], [4, 'E2', 7000, 'limpieza'], [4, 'E2', 18000, 'final'], [4, 'E3', 6000], [4, 'E4', 6000]];
for (const [W, H] of [[1366, 768], [1920, 1080]]) {
  const pg = await b.newPage({ viewport: { width: W, height: H } });
  await pg.goto(pathToFileURL(join(root, 'dist/Modelo3D_Labs_M6_M14_offline.html')).href); await pg.waitForTimeout(5000);
  await pg.screenshot({ path: join(out, `${W}_v2_inicio.png`) });
  if (W === 1920) await pg.screenshot({ path: join(out, 'Inicio_v2_1920x1080.png') }); // limpia: el ratón no se movió
  for (const [k, id, wait, tag] of SC) {
    await pg.evaluate(([k, id]) => window.__labs.go(k, window.__labs.STOPS[k].steps.findIndex(x => x.id === id)), [k, id]);
    await pg.waitForTimeout(wait);
    await pg.screenshot({ path: join(out, `${W}_v2_${k === 3 ? 'M8' : 'M11'}_${id}${tag ? '_' + tag : ''}.png`) });
  }
  await pg.close();
}
await b.close();
console.log('Capturas en ' + out);
