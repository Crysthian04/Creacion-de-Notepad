// Huella de las Paradas 1 (M6) y 2 (M14): etiquetas visibles (texto y posición), columna de tarjetas
// (rótulo, chips y sellos, HTML exacto), panel derecho, nota y tamaño del visor, en todos los pasos y en los
// estados interactivos, a 1366 y 1920. El reloj de la página está detenido y solo avanza con runFor: la huella no
// depende de la velocidad de la máquina. La prueba de humo compara la versión actual contra la huella de la v1.0.
// Generar la huella: node tests/identidad.mjs <html v1.0> tests/fixtures/v1_paradas_1_2.json
import { pathToFileURL } from 'node:url';
import { writeFile } from 'node:fs/promises';

export const SIZES = [[1920, 1080], [1366, 768]];
export async function snapshot(browser, file, W, H) {
  const pg = await browser.newPage({ viewport: { width: W, height: H } });
  await pg.clock.install({ time: new Date('2026-10-25T09:00:00-05:00') });
  await pg.clock.pauseAt(new Date('2026-10-25T09:00:01-05:00'));
  await pg.goto(pathToFileURL(file).href);
  for (let k = 0; k < 150 && !(await pg.evaluate(() => !!window.__labs)); k++) await pg.clock.runFor(200); // con el reloj detenido, waitForFunction no avanza
  await pg.evaluate(() => document.fonts.ready); await pg.clock.runFor(2000);
  // Esperas largas: el reloj salta y solo se dibuja el último 1.2 s (basta para que terminen los vuelos de cámara)
  const run = async ms => { if (ms > 1500) await pg.clock.fastForward(ms - 1200); await pg.clock.runFor(Math.min(ms, 1200)); };
  const grab = () => pg.evaluate(() => {
    const q = s => document.querySelector(s), vp = q('#vp').getBoundingClientRect();
    const labels = [...document.querySelectorAll('#labels .lbl:not([hidden]) .box')].map(b => { const r = b.getBoundingClientRect(); return `${b.innerText.replace(/\s+/g, ' ').trim()} @ ${Math.round(r.left)},${Math.round(r.top)}`; }).sort();
    return { vp: [vp.left, vp.top, vp.width, vp.height].map(Math.round).join(','), labels, dock: q('#dock').innerHTML, aside: q('aside').innerText, note: q('#note').innerHTML, pos: q('#pos').textContent, back: q('#back').hidden ? '' : q('#back').textContent, inset: q('#inset').hidden ? '' : q('#inset').innerHTML };
  });
  const out = {};
  const go = (k, i) => pg.evaluate(([k, i]) => window.__labs.go(k, i), [k, i]);
  const goId = (k, id) => pg.evaluate(([k, id]) => window.__labs.go(k, window.__labs.STOPS[k].steps.findIndex(x => x.id === id)), [k, id]);
  for (const k of [1, 2]) {
    const n = await pg.evaluate(k => window.__labs.STOPS[k].steps.length, k);
    for (let i = 0; i < n; i++) { await go(k, i); await run(2500); out[`p${k}:${i}`] = await grab(); }
  }
  const STATES = [
    ['M6 E1 a los 12 s', async () => { await goId(1, 'E1'); await run(12000); }],
    ['M6 E1 final (35 s)', async () => { await run(23000); }],
    ['M6 E2 todo abierto', async () => { await goId(1, 'E2'); await run(2500); }],
    ['M6 E2 compuerta cerrada', async () => { await pg.evaluate(() => window.__labs.STOPS[1].sim.set(3, 5)); await run(1500); }],
    ['M6 E2 balanceada 4-4-3-3', async () => { await pg.evaluate(() => window.__labs.STOPS[1].sim.apply([4, 4, 3, 3, 0, 0, 0, 0])); await run(2000); }],
    ['M6 E2 comparar métodos', async () => { await pg.click('#cmpBtn'); await run(5000); }],
    ['M6 E2 comparar, final', async () => { await run(16000); }],
    ['M6 E3 −20 %', async () => { await goId(1, 'E3'); await run(2500); await pg.click('#spd80'); await run(1500); }],
    ['M6 E4 final', async () => { await goId(1, 'E4'); await run(9000); }],
    ...['100', '200', '300', '350', '400', '500'].map(n => [`M14 E2 LOD ${n}`, async () => { if (n === '100') { await goId(2, 'E2'); await run(2500); } await pg.click(`[data-lod="${n}"]`); await run(800); }]),
    ['M14 E3 aviso M3', async () => { await goId(2, 'E3'); await run(4000); }],
    ['M14 E3 paro C3', async () => { await run(8500); }],
    ['M14 E3 ficha de activo', async () => { await pg.evaluate(() => window.__labs.STOPS[2].openFicha(3)); await run(800); }],
    ['M14 E1 planta', async () => { await goId(2, 'E1'); await run(3000); }],
    ['M14 E1 zona de estudio', async () => { await run(9000); }],
    ['M14 E4 hoy', async () => { await goId(2, 'E4'); await run(2500); }],
    ['M14 E4 coordinado', async () => { await run(4000); }],
    ['M14 E4 as-built', async () => { await run(4500); }],
    ['M14 E4 repetir', async () => { await pg.click('[data-replay]'); await run(2500); }],
    ['M6 chip y volver', async () => { await goId(1, 'E1'); await run(1500); await pg.click('[data-chip]'); await run(2000); }],
  ];
  for (const [name, act] of STATES) { await act(); out['estado:' + name] = await grab(); }
  // Referencias de las paradas 1 y 2
  for (const k of [1, 2]) { await go(k, 0); await run(500); await pg.keyboard.press('r'); out[`refs:${k}`] = await pg.evaluate(() => document.getElementById('refbody').innerHTML); await pg.keyboard.press('Escape'); }
  await pg.close();
  return out;
}
// Compara dos huellas y devuelve las diferencias legibles
export function diff(ref, cur, where) {
  const d = [];
  for (const key of Object.keys(ref)) {
    const a = ref[key], b = cur[key];
    if (b === undefined) { d.push(`${where} ${key}: falta en la versión actual`); continue; }
    if (typeof a === 'string') { if (a !== b) d.push(`${where} ${key}: cambió`); continue; }
    for (const f of Object.keys(a)) {
      if (f === 'labels') {
        const miss = a.labels.filter(x => !b.labels.includes(x)), extra = b.labels.filter(x => !a.labels.includes(x));
        for (const x of miss) d.push(`${where} ${key}: etiqueta de la v1.0 que ya no está igual «${x}»`);
        for (const x of extra) d.push(`${where} ${key}: etiqueta nueva o movida «${x}»`);
      } else if (a[f] !== b[f]) d.push(`${where} ${key}: cambió «${f}»`);
    }
  }
  return d;
}

// Huella completa (1920 y 1366) en un navegador propio; composición por software: mismo resultado, más rápido
export async function fingerprint(file) {
  const { chromium } = await import('playwright');
  const exe = process.env.CHROMIUM_PATH;
  const browser = await chromium.launch({ ...(exe ? { executablePath: exe } : {}), args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist', '--disable-gpu-compositing'] });
  const res = {};
  for (const [W, H] of SIZES) res[`${W}x${H}`] = await snapshot(browser, file, W, H);
  await browser.close();
  return res;
}

if (import.meta.url === pathToFileURL(process.argv[1]).href) { // node tests/identidad.mjs <html> <salida.json>
  const res = await fingerprint(process.argv[2]);
  await writeFile(process.argv[3], JSON.stringify(res, null, 1));
  console.log('Huella escrita en ' + process.argv[3] + ': ' + Object.values(res).map(r => Object.keys(r).length).join(' + ') + ' estados');
}
