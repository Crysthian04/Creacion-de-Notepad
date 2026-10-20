// Prueba de humo: abre el HTML offline (file://), recorre las paradas 0–6, toma capturas
// y verifica cifras fijas del compendio. Uso: npm run check   (o: node tests/smoke.mjs [archivo.html])
import { chromium } from 'playwright';
import { mkdir, readFile } from 'node:fs/promises';
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
    // Contenido solo del compendio: sin Honeywell, y el 24 % no se atribuye a los mini-splits
    const body = await pg.evaluate(() => document.body.innerText);
    if (/Honeywell/.test(body)) fails.push(`${W}x${H} parada ${k}: aparece «Honeywell»`);
    if (/Mini-splits\s*·?\s*24\s*%|Mini-splits\s*\n?\s*24/.test(body)) fails.push(`${W}x${H} parada ${k}: aparece «Mini-splits · 24 %»`);
    const ov = await pg.evaluate(() => { const d = document.getElementById('dock'); return d && d.scrollHeight - d.clientHeight; });
    if (ov > 8) fails.push(`${W}x${H} parada ${k}: tarjetas desbordan ${ov}px`);
    await pg.screenshot({ path: join(shots, `${W}_parada_${k}.png`) });
  }
  // Subventanas 5.1–5.4: navegación con «Siguiente», sin desborde, sin cifras simuladas en la realidad aumentada
  await pg.keyboard.press('5'); await pg.waitForTimeout(2500);
  for (const sub of ['5.2', '5.3', '5.4']) {
    await pg.click('#spNext'); await pg.waitForTimeout(3500);
    const [t, ov] = await pg.evaluate(() => [document.getElementById('spT').textContent, document.getElementById('dock').scrollHeight - document.getElementById('dock').clientHeight]);
    if (!t.startsWith(sub)) fails.push(`${W}x${H} «Siguiente» desde la parada anterior llevó a «${t}», no a ${sub}`);
    if (ov > 8) fails.push(`${W}x${H} ${sub}: tarjetas desbordan ${ov}px`);
    if (sub === '5.3') {
      const txt = await pg.evaluate(() => document.getElementById('labels').innerText + document.getElementById('dock').innerText);
      if (/°C|HR \d/.test(txt)) fails.push(`${W}x${H} 5.3 muestra lecturas simuladas con números`);
      await pg.click('#arCtl');
      const ok = await pg.waitForFunction(() => /Ajuste aplicado|Aplicando/.test(document.getElementById('arSt').textContent), null, { timeout: 30000 }).then(() => true, () => false);
      if (!ok) fails.push(`${W}x${H} 5.3: el botón de ajuste no cambia el estado («${await pg.evaluate(() => document.getElementById('arSt').textContent)}»)`);
    }
    if (sub === '5.2' && /°C/.test(await pg.evaluate(() => document.getElementById('labels').innerText + document.getElementById('dock').innerText + document.getElementById('thermoLegend').innerText))) fails.push(`${W}x${H} 5.2 muestra °C sin dato medido`);
    if (sub === '5.4' && !/Rodando|Volando|Fuga/.test(await pg.evaluate(() => document.getElementById('droneSt').textContent))) fails.push(`${W}x${H} 5.4: sin estado del dron`);
    await pg.screenshot({ path: join(shots, `${W}_parada_${sub}.png`) });
  }
  await pg.click('#spNext'); await pg.waitForTimeout(500);
  if (!(await pg.evaluate(() => document.querySelector('.tourbar [data-stop="i"]').classList.contains('on')))) fails.push(`${W}x${H} después de 5.4 «Siguiente» no lleva a la vista integrada`);
  // Vista integrada i.1–i.3 (Fase 2.6)
  const shown = () => pg.evaluate(() => ['labels', 'dock', 'pop', 'plan'].map(id => document.getElementById(id)?.innerText || '').join('\n'));
  await pg.keyboard.press('6'); await pg.waitForTimeout(2500);
  if (!(await pg.evaluate(() => document.getElementById('spT').textContent.startsWith('i.1')))) fails.push(`${W}x${H} la tecla 6 no abre i.1`);
  await pg.click('#fNext'); await pg.waitForTimeout(300);
  if (!(await pg.evaluate(() => /Paso 2 de 6/.test(document.getElementById('fStep').textContent)))) fails.push(`${W}x${H} i.1: ▶ no avanza al paso 2`);
  await pg.click('#fPlay');
  if ((await pg.evaluate(() => document.getElementById('fPlay').textContent)) !== 'Pausar') fails.push(`${W}x${H} i.1: «Reproducir» no cambia a «Pausar»`);
  const advanced = await pg.waitForFunction(() => /Paso 3 de 6/.test(document.getElementById('fStep').textContent), null, { timeout: 40000 }).then(() => true, () => false);
  if (!advanced) fails.push(`${W}x${H} i.1: la reproducción no avanza sola`);
  await pg.click('#fPlay');
  if (/°C/.test(await shown())) fails.push(`${W}x${H} i.1 muestra °C`);
  await pg.screenshot({ path: join(shots, `${W}_integrada_i.1.png`) });
  await pg.click('#spNext'); await pg.waitForTimeout(3000);
  if (!(await pg.evaluate(() => document.getElementById('spT').textContent.startsWith('i.2')))) fails.push(`${W}x${H} «Siguiente» desde i.1 no lleva a i.2`);
  await pg.evaluate(() => { const r = document.getElementById('abR'); r.value = 3; r.dispatchEvent(new Event('input', { bubbles: true })); });
  await pg.waitForTimeout(500);
  if (!/Modelo BIM/.test(await pg.evaluate(() => document.getElementById('abS').innerText))) fails.push(`${W}x${H} i.2: el deslizador no llega a la etapa 3`);
  const t2 = await shown();
  if (/°C/.test(t2)) fails.push(`${W}x${H} i.2 muestra °C`);
  if (/(25|35|70|75)\s*(–|-)?\s*(\d+\s*)?%/.test(t2)) fails.push(`${W}x${H} i.2 muestra porcentajes de ahorro`);
  await pg.screenshot({ path: join(shots, `${W}_integrada_i.2.png`) });
  await pg.click('#spNext'); await pg.waitForTimeout(2500);
  const t3 = await shown();
  if (!/52\s*semanales/.test(t3) || !/Frecuencia según el manual del fabricante/.test(t3)) fails.push(`${W}x${H} i.3: falta el contador o la banda del manual del fabricante`);
  if (/°C/.test(t3)) fails.push(`${W}x${H} i.3 muestra °C`);
  if (await pg.evaluate(() => document.getElementById('dock').scrollHeight - document.getElementById('dock').clientHeight > 8)) fails.push(`${W}x${H} i.3: tarjetas desbordan`);
  await pg.screenshot({ path: join(shots, `${W}_integrada_i.3.png`) });
  await pg.click('#spNext'); await pg.waitForTimeout(500);
  if (!(await pg.evaluate(() => document.querySelector('[data-stop="g"]').classList.contains('on')))) fails.push(`${W}x${H} después de i.3 «Siguiente» no vuelve a la vista general`);
  if (!(await pg.evaluate(() => /no a escala/i.test(document.body.innerText)))) fails.push('Falta la nota "Modelo conceptual, no a escala"');
  // Inspector: clic sobre la proyección de UMA_03 en la vista general, luego Esc
  await pg.keyboard.press('0'); await pg.waitForTimeout(2500);
  // esperar a que la cámara se detenga (con render por software los cuadros son lentos)
  for (let i = 0, prev = ''; i < 40; i++) { const c = await pg.evaluate(() => document.querySelector('three-d-stage')._camera.position.toArray().map(x => x.toFixed(3)).join()); if (c === prev) break; prev = c; await pg.waitForTimeout(700); }
  const pt = await pg.evaluate(() => {
    const s = document.querySelector('three-d-stage'), o = s._scene.getObjectByName('UMA_03_carcasa');
    const p = o.getWorldPosition(o.position.clone()).project(s._camera), r = s.shadowRoot.querySelector('canvas').getBoundingClientRect();
    return [r.left + (p.x + 1) / 2 * r.width, r.top + (1 - p.y) / 2 * r.height];
  });
  await pg.mouse.click(pt[0], pt[1]); await pg.waitForTimeout(300);
  const ins = await pg.evaluate(() => { const e = document.getElementById('inspector'); return e.hidden ? '' : e.innerText; });
  if (/°C/.test(ins)) fails.push(`${W}x${H} el inspector muestra °C sin dato medido`);
  if (!/Investigaciones que lo tocan/i.test(ins) || !/INV2/.test(ins) || !/INV4/.test(ins)) fails.push(`${W}x${H} inspector: falta la matriz «Investigaciones que lo tocan»`);
  if (!/UMA 03/.test(ins) || !/Sin dato medido/.test(ins)) fails.push(`${W}x${H} inspector tras clic en UMA_03: «${ins.slice(0, 80)}»`);
  await pg.screenshot({ path: join(shots, `${W}_inspector.png`) });
  await pg.keyboard.press('Escape'); await pg.waitForTimeout(200);
  if (!(await pg.evaluate(() => document.getElementById('inspector').hidden))) fails.push(`${W}x${H} Esc no cierra el inspector`);
  // Modo "al pasar": tarjetas ocultas, punto sobre el elemento; al pasar el puntero aparece la tarjeta (y el VFD sigue funcionando)
  await pg.click('#tHover'); await pg.keyboard.press('4'); await pg.waitForTimeout(3000);
  const vis = await pg.evaluate(() => getComputedStyle(document.querySelector('#dock .card.anch')).visibility);
  if (vis !== 'hidden') fails.push(`${W}x${H} modo al pasar: las tarjetas siguen visibles`);
  const hot = pg.locator('.hot[aria-label*="Variador"]');
  if (!(await hot.count())) fails.push(`${W}x${H} modo al pasar: no hay punto para la tarjeta del VFD`);
  else {
    await hot.hover({ timeout: 90000 }); await pg.waitForTimeout(800); // hover() espera a que el punto esté estable
    if (!(await pg.evaluate(() => /Variador/.test(document.getElementById('pop').innerText)))) fails.push(`${W}x${H} modo al pasar: no aparece la tarjeta al pasar el puntero`);
    else {
      await pg.click('#pop [data-v="80"]'); await pg.waitForTimeout(200);
      const p = await pg.evaluate(() => document.getElementById('vfdP')?.textContent.trim());
      if (p !== '7.68 kW') fails.push(`${W}x${H} modo al pasar: VFD dentro de la ventana = ${p}`);
      await pg.screenshot({ path: join(shots, `${W}_al_pasar.png`) });
    }
    await pg.keyboard.press('Escape'); await pg.waitForTimeout(300);
    if (!(await pg.evaluate(() => document.getElementById('pop').hidden))) fails.push(`${W}x${H} modo al pasar: Esc no cierra la tarjeta`);
  }
  await pg.click('#tHover'); await pg.keyboard.press('0'); await pg.waitForTimeout(2500);
  // Calculadora psicrométrica (2.2): en pausa, no se muestra
  if (await pg.evaluate(() => !document.getElementById('psy').hidden)) fails.push(`${W}x${H} la calculadora psicrométrica (en pausa) sigue visible`);
  // Vista termográfica cualitativa: vista general y Parada 5, leyenda sin °C
  for (const k of ['0', '5']) {
    await pg.keyboard.press(k); await pg.waitForTimeout(2500);
    await pg.click('#tThermo'); await pg.waitForTimeout(500);
    const leg = await pg.evaluate(() => { const e = document.getElementById('thermoLegend'); return e.hidden ? '' : e.innerText; });
    if (!/más frío/.test(leg) || !/Representación cualitativa/.test(leg) || /°C/.test(leg)) fails.push(`${W}x${H} parada ${k}: leyenda termográfica «${leg.slice(0, 60)}»`);
    await pg.screenshot({ path: join(shots, `${W}_termografia_${k}.png`) });
    await pg.click('#tThermo'); await pg.waitForTimeout(200);
  }
  await pg.keyboard.press('1'); await pg.waitForTimeout(300);
  if (await pg.evaluate(() => !document.getElementById('thermoSeg').hidden)) fails.push(`${W}x${H} el botón de termografía aparece en la Parada 1`);
  await pg.keyboard.press('5'); await pg.waitForTimeout(300);
  if (!(await pg.evaluate(() => document.querySelector('[data-stop="5"]').classList.contains('on')))) fails.push(`${W}x${H} el atajo 5 dejó de funcionar tras el inspector`);
  // Exportación GLB: los equipos llevan clase IFC y fuente en extras
  if (W >= 1920) {
    await pg.keyboard.press('0'); await pg.waitForTimeout(1500);
    const [dl] = await Promise.all([pg.waitForEvent('download', { timeout: 30000 }), pg.evaluate(() => document.querySelector('three-d-stage')._glbBtn.click())]);
    const buf = await readFile(await dl.path()), json = JSON.parse(buf.subarray(20, 20 + buf.readUInt32LE(12)).toString('utf8'));
    const cls = n => json.nodes.find(x => x.name === n)?.extras;
    const want = { chiller_155TR: ['IfcChiller', 'real'], UMA_03: ['IfcUnitaryEquipment', 'real'], bomba_operacion_motor: ['IfcPump', 'ilustrativo'], suministro_principal_tramo1: ['IfcPipeSegment', 'ilustrativo'] };
    for (const [n, [c, f]] of Object.entries(want)) { const e = cls(n); if (e?.ifcClass !== c || e?.fuente !== f) fails.push(`GLB: ${n} extras = ${JSON.stringify(e)}`); }
  }
  fails.push(...errs.map(e => `${W}x${H} ${e}`));
  await pg.close();
}
await browser.close();
if (fails.length) { console.error('FALLÓ:\n- ' + fails.join('\n- ')); process.exit(1); }
console.log(`OK: sin errores; capturas en ${shots}`);
