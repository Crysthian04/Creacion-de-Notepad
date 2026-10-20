// Psicrometría a presión fija, funciones puras. Ecuaciones de ASHRAE Handbook—Fundamentals, cap. 1 (Psicrometría).
// Unidades: t en °C, HR en fracción (0–1), presiones en Pa, W en kg/kg de aire seco, h en kJ/kg de aire seco.
export const P_ATM = 101325; // nivel del mar: el campus está prácticamente a esa altura

// Presión de saturación del vapor sobre agua líquida (Hyland-Wexler, ec. 6), 0–200 °C
export function pws(t) {
  const T = t + 273.15;
  return Math.exp(-5.8002206e3 / T + 1.3914993 - 4.8640239e-2 * T + 4.1764768e-5 * T ** 2 - 1.4452093e-8 * T ** 3 + 6.5459673 * Math.log(T));
}
export const humidityRatio = (t, rh, p = P_ATM) => { const pw = rh * pws(t); return 0.621945 * pw / (p - pw); };
export const enthalpy = (t, W) => 1.006 * t + W * (2501 + 1.86 * t);
// Punto de rocío: t tal que pws(t) = HR · pws(t_bs), por bisección
export function dewPoint(t, rh) {
  const pw = rh * pws(t); let lo = -0.01, hi = t;
  if (pws(lo) >= pw) return null; // fuera del rango de la ecuación sobre agua líquida
  for (let i = 0; i < 60; i++) { const mid = (lo + hi) / 2; if (pws(mid) < pw) lo = mid; else hi = mid; }
  return (lo + hi) / 2;
}
export function state(t, rh, p = P_ATM) {
  const W = humidityRatio(t, rh, p);
  return { t, rh, pws: pws(t), W, h: enthalpy(t, W), td: dewPoint(t, rh) };
}
// Proceso de enfriamiento y deshumidificación en un serpentín, por kg de aire seco
export function coilProcess(a, b) {
  const s1 = state(a.t, a.rh), s2 = state(b.t, b.rh);
  const qt = s1.h - s2.h, qs = (1.006 + 1.86 * s1.W) * (s1.t - s2.t), ql = qt - qs;
  return { s1, s2, qt, qs, ql, shr: qt ? qs / qt : null, condenses: s2.W < s1.W };
}
