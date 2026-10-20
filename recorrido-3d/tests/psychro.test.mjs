// Prueba numérica de la calculadora psicrométrica (PLAN_MEJORAS 2.2). Uso: npm test
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { pws, humidityRatio, enthalpy, state, coilProcess } from '../src/app/psychro.js';

const near = (got, want, what) => assert.ok(Math.abs(got - want) <= Math.abs(want) * 0.005, `${what}: ${got} ≠ ${want} (±0.5 %)`);
for (const [t, rh, P, W, h] of [[30, 0.75, 4246, 0.02018, 81.78], [25, 0.5, 3169, 0.00988, 50.32], [13, 1, 1498, 0.00933, 36.64]]) {
  test(`${t} °C, ${rh * 100} %`, () => {
    near(pws(t), P, 'p_ws'); const w = humidityRatio(t, rh); near(w, W, 'W'); near(enthalpy(t, w), h, 'h');
  });
}
test('Proceso 30/75 → 13/100', () => {
  const r = coilProcess({ t: 30, rh: 0.75 }, { t: 13, rh: 1 });
  near(r.qt, 45.14, 'q_total'); near(r.qs, 17.74, 'q_sensible'); near(r.ql, 27.40, 'q_latente'); near(r.shr, 0.393, 'SHR');
});
test('Punto de rocío de aire saturado = temperatura de bulbo seco', () => { assert.ok(Math.abs(state(13, 1).td - 13) < 1e-6); });
