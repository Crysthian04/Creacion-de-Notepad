"""Contrato de la inferencia en JavaScript, sin depender del modelo serializado.

Estas pruebas NO cargan `resultados/modelo_rf.joblib`: corren contra los
archivos realmente exportados en `web/`, que sí están en el repositorio. Esa
independencia es deliberada —las cinco pruebas de `test_exportador.py` que
verifican la equivalencia exacta con scikit-learn no se pueden correr en un clon
limpio porque el `.joblib` pesa 244 MB y está excluido— así que el contrato de
comportamiento del visualizador queda cubierto de todos modos.

Lo que se verifica aquí:

  * un punto SIN estado estacionario se RECHAZA en lugar de clasificarse
    (`Math.fround(null)` vale 0, y sin la comprobación el bosque devolvía `sano`);
  * `probabilidades()` falla ruidosamente ante una entrada no finita;
  * una consulta fuera de la malla se marca, y más allá del margen se rechaza;
  * `diagnosticar()` clasifica el bloque de residuos CON ruido y declara con qué
    semilla, factor de ruido y nivel de discrepancia se generó.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
DIR_DATOS = RAIZ / "web" / "datos"
DIR_JS = RAIZ / "web" / "js"
ARCHIVOS = [DIR_DATOS / "fdd_modelo.js", DIR_DATOS / "fdd_fisica.js",
            DIR_DATOS / "fdd_malla.js", DIR_DATOS / "fdd_metricas.js",
            DIR_JS / "fdd_inferencia.js"]

pytestmark = pytest.mark.skipif(
    shutil.which("node") is None or not all(a.exists() for a in ARCHIVOS),
    reason="requiere node y los archivos exportados (`python -m src.exportador_web`)")


ARNES = r"""
// argv[2] = archivo con el cuerpo de la función a evaluar; argv[3:] = archivos a cargar.
const fs = require('fs'), vm = require('vm');
const ctx = vm.createContext({console: console});
const cuerpo = fs.readFileSync(process.argv[2], 'utf8');
for (const f of process.argv.slice(3)) {
  vm.runInContext(fs.readFileSync(f, 'utf8'), ctx, {filename: f});
}
let salida;
try {
  salida = {ok: vm.runInContext('(function(){' + cuerpo + '\n})()', ctx,
                                {filename: 'expresion.js'})};
} catch (e) {
  salida = {error: String(e && e.message ? e.message : e)};
}
process.stdout.write(JSON.stringify(salida === undefined ? {ok: null} : salida));
"""


def evaluar(expresion: str, tmp: Path | None = None) -> dict:
    """Corre una expresión JavaScript con los archivos exportados ya cargados.

    Devuelve `{"ok": valor}` o `{"error": mensaje}`, para poder afirmar tanto
    sobre los resultados como sobre los fallos esperados. El arnés se escribe a
    un archivo —y no se pasa con `node -e`— porque con `-e` los argumentos se
    desplazan un lugar y una ruta absoluta acabaría interpretada como una
    expresión regular.
    """
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        dd = Path(d)
        (dd / "arnes.js").write_text(ARNES, encoding="utf-8")
        (dd / "expresion.js").write_text(expresion, encoding="utf-8")
        r = subprocess.run(
            ["node", str(dd / "arnes.js"), str(dd / "expresion.js"),
             *map(str, ARCHIVOS)],
            capture_output=True, text=True, timeout=600)
    assert r.returncode == 0, f"node falló: {r.stderr[-2000:]}"
    return json.loads(r.stdout)


# Localiza en la malla REAL el primer nodo con `convergio = 0` y devuelve sus
# coordenadas. No se inventa un punto: se usa uno de los 189 que existen.
NODO_SIN_ESTADO = r"""
const M = FDD_MALLA;
const nT = M.temperaturas_C.length, nQ = M.cargas.length;
const nC = M.nClases, nS = M.nSeveridades;
for (let i = 0; i < M.discretos.convergio.length; i++) {
  if (M.discretos.convergio[i] === 0) {
    const s = i % nS, c = Math.floor(i / nS) % nC;
    const q = Math.floor(i / (nS * nC)) % nQ, t = Math.floor(i / (nS * nC * nQ)) % nT;
    return {idx: i, T: M.temperaturas_C[t], carga: M.cargas[q],
            clase: M.clases[c], sev: M.severidades[s]};
  }
}
return null;
"""


@pytest.fixture(scope="module")
def nodo_sin_estado():
    r = evaluar(NODO_SIN_ESTADO)
    assert "error" not in r, r
    if r["ok"] is None:
        pytest.skip("la malla exportada no tiene nodos sin estado estacionario")
    return r["ok"]


# ---------------------------------------------------------------------------
# 1. Puntos sin estado estacionario: se rechazan, no se clasifican
# ---------------------------------------------------------------------------
def test_diagnosticar_rechaza_un_nodo_sin_estado_estacionario(nodo_sin_estado):
    n = nodo_sin_estado
    r = evaluar(f"""
      const d = FDD.diagnosticar({n['T']}, {n['carga']},
                                 {json.dumps(n['clase'])}, {n['sev']});
      return {{diagnostico: d.diagnostico, residuos: d.residuos,
               motivo: d.motivo, convergio: d.estado.convergio}};
    """)
    assert "error" not in r, r
    d = r["ok"]
    assert d["convergio"] == 0, "el nodo elegido debería ser uno sin estado estacionario"
    assert d["diagnostico"] is None, (
        "un punto sin solución física NO puede devolver una clase; devolvió "
        f"{d['diagnostico']}")
    assert d["residuos"] is None
    assert "sin estado estacionario" in d["motivo"]


def test_todos_los_nodos_sin_estado_se_rechazan():
    """No basta con uno: ninguno de los nodos con `convergio = 0` debe clasificarse."""
    r = evaluar(r"""
      const M = FDD_MALLA;
      const nT = M.temperaturas_C.length, nQ = M.cargas.length;
      const nC = M.nClases, nS = M.nSeveridades;
      let total = 0, clasificados = 0;
      for (let i = 0; i < M.discretos.convergio.length; i++) {
        if (M.discretos.convergio[i] !== 0) continue;
        total++;
        const s = i % nS, c = Math.floor(i / nS) % nC;
        const q = Math.floor(i / (nS * nC)) % nQ, t = Math.floor(i / (nS * nC * nQ)) % nT;
        const d = FDD.diagnosticar(M.temperaturas_C[t], M.cargas[q],
                                   M.clases[c], M.severidades[s]);
        if (d.diagnostico !== null) clasificados++;
      }
      return {total: total, clasificados: clasificados};
    """)
    assert "error" not in r, r
    assert r["ok"]["total"] > 0
    assert r["ok"]["clasificados"] == 0, (
        f"{r['ok']['clasificados']} de {r['ok']['total']} nodos sin estado "
        "estacionario siguen recibiendo una clase")


# ---------------------------------------------------------------------------
# 2. `probabilidades()` falla ruidosamente ante entradas no finitas
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("valor,etiqueta", [
    ("null", "null"),            # es lo que traen los nodos sin estado estacionario
    ("undefined", "undefined"),  # columna ausente
    ("NaN", "NaN"),
    ("Infinity", "Infinity"),
])
def test_probabilidades_rechaza_entradas_no_finitas(valor, etiqueta):
    r = evaluar(f"""
      const cols = FDD_MODELO.columnas_entrada;
      const fila = {{}};
      for (const c of cols) fila[c] = 0.0;
      fila[cols[0]] = {valor};
      return FDD.probabilidades(fila);
    """)
    assert "error" in r, (
        f"con {etiqueta} en la primera columna, `probabilidades` devolvió un "
        f"resultado en lugar de fallar: {r.get('ok')}")
    assert "no finito" in r["error"]


def test_probabilidades_acepta_una_fila_completa_de_ceros():
    """El complemento de la prueba anterior: ceros legítimos SÍ se clasifican."""
    r = evaluar("""
      const fila = {};
      for (const c of FDD_MODELO.columnas_entrada) fila[c] = 0.0;
      const pr = FDD.probabilidades(fila);
      let suma = 0;
      for (const v of pr) suma += v;
      return {n: pr.length, suma: suma};
    """)
    assert "error" not in r, r
    assert r["ok"]["n"] == 11
    assert abs(r["ok"]["suma"] - 1.0) < 1e-9


# ---------------------------------------------------------------------------
# 3. Fuera de la malla: borde + bandera dentro de un paso, rechazo más allá
# ---------------------------------------------------------------------------
def test_la_malla_declara_el_margen_de_extrapolacion():
    """La regla viaja como DATO, igual que `celda_bilineal`."""
    from src.exportador_web import CARGAS, SEVERIDADES, TEMPERATURAS, margenes_extrapolacion
    esperado = margenes_extrapolacion({"temperaturas": list(TEMPERATURAS),
                                       "cargas": list(CARGAS),
                                       "severidades": list(SEVERIDADES)})
    r = evaluar("return FDD_MALLA.margen_extrapolacion;")
    assert "error" not in r, r
    m = r["ok"]
    assert m["temperaturas_C"] == esperado["temperaturas_C"]
    assert m["cargas"] == esperado["cargas"]
    assert m["severidades"] == esperado["severidades"]
    # Un paso de nodo a cada lado, con el eje de cargas NO uniforme.
    assert m["temperaturas_C"] == [22.0, 38.0]
    assert m["cargas"] == [0.25, 1.05]


def test_dentro_del_dominio_no_hay_bandera():
    r = evaluar("""
      const e = FDD.consultar(30, 0.70, 'condensador_sucio', 0.55);
      return {extrapolado: e._extrapolado, ejes: e._fuera_de_malla.ejes,
              dmax: e._fuera_de_malla.distancia_max};
    """)
    assert "error" not in r, r
    assert r["ok"]["extrapolado"] is False
    assert r["ok"]["ejes"] == []
    assert r["ok"]["dmax"] == 0.0


@pytest.mark.parametrize("tAmb,carga,eje,lado", [
    (23.0, 0.70, "temperaturas_C", -1),   # un paso por debajo en temperatura
    (37.0, 0.70, "temperaturas_C", 1),
    (30.0, 0.27, "cargas", -1),           # dentro del paso bajo (0,03)
    (30.0, 1.03, "cargas", 1),            # dentro del paso alto (0,05)
])
def test_dentro_de_un_paso_devuelve_el_borde_marcado(tAmb, carga, eje, lado):
    """Se sirve el nodo del borde, pero MARCADO. Antes no había marca alguna."""
    r = evaluar(f"""
      const e = FDD.consultar({tAmb}, {carga}, 'sano', 0);
      const M = FDD_MALLA;
      const iT = {lado} < 0 && '{eje}' === 'temperaturas_C' ? 0
               : {lado} > 0 && '{eje}' === 'temperaturas_C' ? M.temperaturas_C.length - 1
               : null;
      const borde = FDD.consultar(
        iT === null ? {tAmb} : M.temperaturas_C[iT],
        '{eje}' === 'cargas' ? ({lado} < 0 ? M.cargas[0] : M.cargas[M.cargas.length - 1])
                             : {carga},
        'sano', 0);
      return {{extrapolado: e._extrapolado, ejes: e._fuera_de_malla.ejes,
               dmax: e._fuera_de_malla.distancia_max,
               igual_al_borde: e.T4_C === borde.T4_C && e.m_r === borde.m_r}};
    """)
    assert "error" not in r, r
    o = r["ok"]
    assert o["extrapolado"] is True, "la consulta fuera del dominio no quedó marcada"
    assert [x["eje"] for x in o["ejes"]] == [eje]
    assert o["ejes"][0]["lado"] == lado
    assert o["dmax"] > 0.0
    assert o["igual_al_borde"], "el valor servido debería ser exactamente el del borde"


@pytest.mark.parametrize("tAmb,carga", [
    (50.0, 2.00),    # el caso de la auditoría: antes devolvía T4_C = 4,5046 sin aviso
    (21.0, 0.70),    # más de un paso por debajo en temperatura
    (39.0, 0.70),
    (30.0, 0.20),    # más de un paso por debajo en carga
    (30.0, 1.10),
])
def test_mas_de_un_paso_fuera_se_rechaza(tAmb, carga):
    r = evaluar(f"return FDD.consultar({tAmb}, {carga}, 'sano', 0);")
    assert "error" not in r, r
    assert r["ok"] is None, (
        f"consultar({tAmb}, {carga}) debería devolver null y devolvió un estado")


def test_diagnosticar_rechaza_una_consulta_fuera_de_la_malla():
    r = evaluar("""
      const d = FDD.diagnosticar(50, 2.0, 'sano', 0);
      return {estado: d.estado, diagnostico: d.diagnostico, motivo: d.motivo};
    """)
    assert "error" not in r, r
    assert r["ok"]["estado"] is None
    assert r["ok"]["diagnostico"] is None
    assert "fuera de la malla" in r["ok"]["motivo"]


def test_la_severidad_fuera_del_rango_se_marca_pero_no_se_rechaza():
    """El eje de severidad es vecino más próximo por diseño: se marca, no se corta."""
    r = evaluar("""
      const e = FDD.consultar(30, 0.70, 'condensador_sucio', 0.05);
      return {nulo: e === null, extrapolado: e._extrapolado,
              ejes: e._fuera_de_malla.ejes.map(x => x.eje)};
    """)
    assert "error" not in r, r
    assert r["ok"]["nulo"] is False
    assert r["ok"]["extrapolado"] is True
    assert r["ok"]["ejes"] == ["severidades"]


@pytest.mark.parametrize("severidad", ["-0.1", "1.5"])
def test_una_severidad_imposible_falla_ruidosamente(severidad):
    r = evaluar(f"return FDD.consultar(30, 0.70, 'condensador_sucio', {severidad});")
    assert "error" in r, r
    assert "severidad fuera de [0, 1]" in r["error"]


def test_la_clase_sana_no_se_marca_por_la_severidad():
    """`sano` ignora la severidad por construcción, así que no debe marcarse."""
    r = evaluar("""
      const e = FDD.consultar(30, 0.70, 'sano', 0.0);
      return {extrapolado: e._extrapolado, ejes: e._fuera_de_malla.ejes};
    """)
    assert "error" not in r, r
    assert r["ok"]["extrapolado"] is False
    assert r["ok"]["ejes"] == []
