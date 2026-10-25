// Capturas de revisión (1366×768 y 1920×1080) en tests/shots/entrega. Uso: node tests/capturas.mjs
import { chromium } from 'playwright';
import { mkdir } from 'node:fs/promises';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { dirname, join } from 'node:path';
const root = join(dirname(fileURLToPath(import.meta.url)), '..'), out = join(root, 'tests/shots/entrega'); await mkdir(out, { recursive: true });
const exe = process.env.CHROMIUM_PATH;
const b = await chromium.launch({ ...(exe ? { executablePath: exe } : {}), args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'] });
for (const [W, H] of [[1366, 768], [1920, 1080]]) {
  const pg = await b.newPage({ viewport: { width: W, height: H } });
  await pg.goto(pathToFileURL(join(root, 'dist/Modelo3D_Labs_M6_M14_offline.html')).href); await pg.waitForTimeout(3000);
  const shot = n => pg.screenshot({ path: join(out, `${W}_${n}.png`) });
  const go = async (s, id, wait = 2000) => { await pg.evaluate(([s, id]) => window.__labs.go(s, id === null ? 0 : window.__labs.STOPS[s].steps.findIndex(x => x.id === id)), [s, id]); await pg.waitForTimeout(wait); };
  const cam = async (p, t) => { await pg.evaluate(([p, t]) => { const s = document.querySelector('three-d-stage'); s._camera.position.set(...p); s._controls.target.set(...t); }, [p, t]); await pg.waitForTimeout(700); };
  await go(0, null, 2500); await shot('0_inicio');
  await pg.keyboard.press('1'); await pg.waitForTimeout(600); await shot('0_transicion_a_M6'); await pg.waitForTimeout(1800);
  await go(1, 'previas', 2500); await shot('1.2_antes_del_TAB');
  await go(1, 'correas'); await shot('P3_correas');
  await cam([-10.4, 1.0, 5.2], [-10.4, 1.0, 1.25]); await shot('P3_correa_frente');
  await cam([-6.2, 1.0, 1.25], [-10.4, 1.0, 1.25]); await shot('P3_correa_lado');
  await go(2, 'planta', 2500); await shot('2.0_planta');
  await go(2, 'zona', 700); await shot('2.0b_transicion_zona_a'); await pg.waitForTimeout(2300); await shot('2.0b_transicion_zona_b');
  await go(2, 'lod');
  for (const n of ['100', '200', '300', '350', '400', '500']) { await pg.click(`[data-lod="${n}"]`); await pg.waitForTimeout(500); await shot(`2.2_LOD${n}`); }
  await go(2, 'mep', 3500); await shot('2.5_alerta_M3'); await pg.waitForTimeout(6500); await shot('2.5_paro_C3');
  await go(2, 'inspector'); await shot('P1_inspector');
  await go(2, 'propuesta', 9000); await shot('2.6_propuesta_D_E');
  await pg.close();
}
await b.close();
console.log('Capturas en ' + out);
