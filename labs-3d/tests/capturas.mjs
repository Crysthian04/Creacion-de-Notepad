// Capturas de revisión (1366×768 y 1920×1080) en tests/shots/entrega. Uso: node tests/capturas.mjs
import { chromium } from 'playwright';
import { mkdir, rm } from 'node:fs/promises';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { dirname, join } from 'node:path';
const root = join(dirname(fileURLToPath(import.meta.url)), '..'), out = join(root, 'tests/shots/entrega');
await rm(out, { recursive: true, force: true }); await mkdir(out, { recursive: true });
const exe = process.env.CHROMIUM_PATH;
const b = await chromium.launch({ ...(exe ? { executablePath: exe } : {}), args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'] });
for (const [W, H] of [[1366, 768], [1920, 1080]]) {
  const pg = await b.newPage({ viewport: { width: W, height: H } });
  await pg.goto(pathToFileURL(join(root, 'dist/Modelo3D_Labs_M6_M14_offline.html')).href); await pg.waitForTimeout(3000);
  const shot = n => pg.screenshot({ path: join(out, `${W}_${n}.png`) });
  const go = async (s, id, wait = 2200) => { await pg.evaluate(([s, id]) => window.__labs.go(s, window.__labs.STOPS[s].steps.findIndex(x => x.id === id)), [s, id]); await pg.waitForTimeout(wait); };
  await pg.evaluate(() => window.__labs.go(0, 0)); await pg.waitForTimeout(2500); await shot('0_inicio');
  // Escenas del M6
  await go(1, 'E1', 14000); await shot('M6_E1_red_y_criterio');
  await go(1, 'E2'); await shot('M6_E2_simulacion');
  await pg.evaluate(() => window.__labs.STOPS[1].sim.set(3, 2)); await pg.waitForTimeout(1500); await shot('M6_E2_compuerta_cerrada');
  await pg.click('#cmpBtn'); await pg.waitForTimeout(9000); await shot('M6_E2_comparar_metodos');
  await go(1, 'E3', 17000); await shot('M6_E3_compuertas_y_velocidad');
  await go(1, 'E4', 5000); await shot('M6_E4_panama');
  // Escenas del M14
  await go(2, 'E1', 2500); await shot('M14_E1_a_planta'); await pg.waitForTimeout(8000); await shot('M14_E1_b_zona_de_estudio');
  await go(2, 'E2'); for (const n of ['100', '500']) { await pg.click(`[data-lod="${n}"]`); await pg.waitForTimeout(600); await shot(`M14_E2_LOD${n}`); }
  await go(2, 'E3', 3500); await shot('M14_E3_falla');
  await pg.evaluate(() => window.__labs.STOPS[2].openFicha(3)); await pg.waitForTimeout(500); await shot('M14_E3_ficha_de_activo');
  await go(2, 'E4', 9000); await shot('M14_E4_hoy_y_propuesta');
  if (W === 1366) { // ronda 5: simulación sin balancear / ajustada / balanceada; escenas que se quedan en su estado final
    await go(1, 'E2'); await shot('r5_M6_E2_todo_abierto');
    await pg.evaluate(() => window.__labs.STOPS[1].sim.set(0, 4)); await pg.waitForTimeout(1500); await shot('r5_M6_E2_una_compuerta_ajustada');
    await pg.evaluate(() => { const s = window.__labs.STOPS[1].sim; s.apply(s.balanced); }); await pg.waitForTimeout(1800); await shot('r5_M6_E2_balanceada');
    await go(2, 'E1', 10000); await shot('r5_M14_E1_10s'); await pg.waitForTimeout(50000); await shot('r5_M14_E1_60s');
    await go(2, 'E2'); await pg.click('[data-lod="500"]'); await pg.waitForTimeout(600); await shot('r5_M14_E2_LOD500');
    await go(2, 'E4', 2500); await shot('r5_M14_E4_hoy'); await pg.waitForTimeout(9000); await shot('r5_M14_E4_as-built');
  }
  if (W === 1366) { // verificación de las correcciones de la ronda 3
    for (const [s, id, n, w] of [[1, 'marco', '1.1'], [1, 'proporcion', '1.3', 6000], [1, 'progresivo', '1.4', 6000], [1, 'panama', '1.7'], [2, 'planta', '2.0'], [2, 'zona', '2.0b', 3500], [2, 'mep', '2.5', 3500], [2, 'inspector', 'P1']]) { await go(s, id, w || 2200); await shot(`detalle_${n}`); }
  }
  await pg.close();
}
await b.close();
console.log('Capturas en ' + out);
