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


# ---------------------------------------------------------------------------
# 4. Bloque `res_ruidoso_*`: lo que clasifica el visualizador
# ---------------------------------------------------------------------------
# El clasificador se entrenó CON ruido de sensor y CON un gemelo desafinado al
# 5 %. La malla limpia no es comparable con eso. Estas pruebas no necesitan
# `modelo_rf.joblib`: verifican que los residuos ruidosos que viajan en la malla
# son los que el pipeline de entrenamiento habría calculado, y que JavaScript los
# usa sin promediarlos.
NODOS_DE_MUESTRA = [(2, 7, "condensador_sucio", 3),    # 28 °C, carga 0,70, sev 0,75
                    (5, 11, "sano", 0),                 # 34 °C, carga 1,00
                    (0, 4, "txv_restringida", 1)]       # 24 °C, carga 0,40, sev 0,35


@pytest.fixture(scope="module")
def contexto_malla():
    """Parámetros, semillas y epsilon tal como los deriva `generar_malla`."""
    import numpy as np

    from config.params import MODO_DISCREPANCIA, NIVEL_DISCREPANCIA, ParametrosEquipo
    from src.calibracion import aplicar_calibracion
    from src.exportador_web import CARGAS, SEMILLA_MALLA, SEVERIDADES, TEMPERATURAS
    from src.fallas import clases
    from src.generador import muestrear_discrepancia

    p = aplicar_calibracion(ParametrosEquipo())
    nT, nQ = len(TEMPERATURAS), len(CARGAS)
    nC, nS = len(clases(p.topologia)), len(SEVERIDADES)
    raiz = np.random.SeedSequence(SEMILLA_MALLA)
    sem_eps, sem_ruido = raiz.spawn(2)
    eps = muestrear_discrepancia(p, sem_eps, nT * nQ,
                                 nivel=NIVEL_DISCREPANCIA, modo=MODO_DISCREPANCIA)
    sem_nodo = sem_ruido.spawn(nT * nQ * nC * nS)
    return {"p": p, "eps": eps, "sem_nodo": sem_nodo, "nT": nT, "nQ": nQ,
            "nC": nC, "nS": nS, "clases": list(clases(p.topologia))}


def test_la_tolerancia_del_solver_coincide_con_la_del_generador():
    """Si divergieran, el bloque ruidoso no sería comparable con el dataset."""
    import inspect

    from config.params import TOL_BALANCE
    from src.ciclo import resolver_ciclo

    por_defecto = inspect.signature(resolver_ciclo).parameters["tol"].default
    assert por_defecto == TOL_BALANCE, (
        f"`resolver_ciclo` usa tol={por_defecto} por defecto y el generador "
        f"usa TOL_BALANCE={TOL_BALANCE}: la malla y el dataset no serían comparables")


@pytest.mark.parametrize("iT,iQ,clase,iS", NODOS_DE_MUESTRA)
def test_el_bloque_ruidoso_de_la_malla_es_reproducible(contexto_malla, iT, iQ, clase, iS):
    """Re-ejecuta `_estado_punto` y compara con lo que viaja en el `.js`.

    Cubre la derivación de semillas y el redondeo del exportador. Si el ruido
    dependiera del orden de ejecución en paralelo, esta prueba fallaría.
    """
    from src.exportador_web import (CARGAS, DECIMALES_RUIDOSO, SEVERIDADES, TEMPERATURAS,
                                    _estado_punto, columnas_ruidosas)

    c = contexto_malla
    iC = c["clases"].index(clase)
    k = ((iT * c["nQ"] + iQ) * c["nC"] + iC) * c["nS"] + iS
    f = 0.0 if clase == "sano" else SEVERIDADES[iS]
    fila = _estado_punto(TEMPERATURAS[iT], CARGAS[iQ], clase, f, c["p"],
                         eps=c["eps"][iT * c["nQ"] + iQ],
                         semilla_ruido=c["sem_nodo"][k])
    assert fila is not None

    cols = list(columnas_ruidosas(c["p"].topologia))
    r = evaluar(f"""
      const M = FDD_MALLA, out = {{}};
      for (const col of {json.dumps(cols)}) out[col] = M.datos[col][{k}];
      return out;
    """)
    assert "error" not in r, r
    for col in cols:
        esperado = round(float(fila[col]), DECIMALES_RUIDOSO)
        assert r["ok"][col] == pytest.approx(esperado, abs=10 ** -DECIMALES_RUIDOSO), (
            f"{col} en el nodo {k}: la malla trae {r['ok'][col]} y recalcular da {esperado}")


@pytest.mark.parametrize("iT,iQ,clase,iS", NODOS_DE_MUESTRA)
def test_el_bloque_ruidoso_coincide_con_el_pipeline_de_entrenamiento(
        contexto_malla, iT, iQ, clase, iS):
    """La prueba que importa: ¿es el MISMO cálculo que hizo el dataset?

    Se reconstruye el residuo ruidoso con las primitivas de `src.generador`
    —`aplicar_discrepancia`, `_referencia_sana`, `aplicar_ruido`— en lugar de
    volver a llamar al exportador. Así, si el exportador se desviara de cómo se
    generaron los datos de entrenamiento, se vería aquí y no en la defensa.
    """
    from config.params import TOL_BALANCE
    from src.ciclo import AjustesCiclo, CondicionContorno, resolver_ciclo
    from src.exportador_web import (CARGAS, HR_FIJA, SEVERIDADES, TEMPERATURAS,
                                    _estado_punto, columnas_ruidosas)
    from src.fallas import ajustes_de_falla
    from src.features import calcular_residuos, columnas_residuos, derivadas_desde_medicion
    from src.generador import _referencia_sana, aplicar_discrepancia, aplicar_ruido, rng_desde

    c = contexto_malla
    p = c["p"]
    iC = c["clases"].index(clase)
    k = ((iT * c["nQ"] + iQ) * c["nC"] + iC) * c["nS"] + iS
    f = 0.0 if clase == "sano" else SEVERIDADES[iS]
    eps = c["eps"][iT * c["nQ"] + iQ]
    cond = CondicionContorno(TEMPERATURAS[iT], HR_FIJA, CARGAS[iQ])

    # --- camino del pipeline de entrenamiento (src.generador) --------------
    p_modelo = aplicar_discrepancia(p, eps)
    _, _, derivadas_ref = _referencia_sana(cond, p_modelo)
    assert derivadas_ref is not None
    if clase == "sano":
        deg = resolver_ciclo(cond, p, AjustesCiclo(), tol=TOL_BALANCE)
    else:
        deg = resolver_ciclo(cond, p, ajustes_de_falla(clase, f, p), tol=TOL_BALANCE)
    assert deg.convergio
    medido = aplicar_ruido(deg.dict_medible(), rng_desde(c["sem_nodo"][k]), 1.0)
    esperado = calcular_residuos(derivadas_desde_medicion(medido, p),
                                 derivadas_ref, p.topologia)

    # --- camino del exportador --------------------------------------------
    fila = _estado_punto(TEMPERATURAS[iT], CARGAS[iQ], clase, f, p,
                         eps=eps, semilla_ruido=c["sem_nodo"][k])

    for limpio, ruidoso in zip(columnas_residuos(p.topologia),
                               columnas_ruidosas(p.topologia)):
        assert fila[ruidoso] == pytest.approx(esperado[limpio], rel=1e-12, abs=1e-12), (
            f"{ruidoso} divergió del cálculo de src.generador")


def test_el_bloque_ruidoso_se_diferencia_del_limpio(contexto_malla):
    """Control de que el bloque no es una copia del limpio con otro nombre."""
    r = evaluar("""
      const M = FDD_MALLA, mapa = M.residuo_ruidoso;
      let n = 0, iguales = 0, nulos = 0;
      for (const limpio in mapa) {
        const a = M.datos[limpio], b = M.datos[mapa[limpio]];
        for (let i = 0; i < a.length; i++) {
          if (b[i] === null) { nulos++; continue; }
          n++;
          if (a[i] === b[i]) iguales++;
        }
      }
      return {n: n, iguales: iguales, nulos: nulos};
    """)
    assert "error" not in r, r
    o = r["ok"]
    assert o["n"] > 0
    # Con sigmas de sensor no nulas, dos bloques iguales serían un error de copia.
    assert o["iguales"] / o["n"] < 0.01, (
        f"{o['iguales']} de {o['n']} valores ruidosos son idénticos al limpio")


def test_los_residuos_ruidosos_no_se_interpolan_nunca():
    """Interpolar ruido independiente reduce sigma a la mitad: no se hace.

    Se consulta el CENTRO de una celda interpolable. El bloque limpio debe
    haberse interpolado —su valor no coincide con ninguna esquina— y el ruidoso
    debe ser exactamente el de la esquina del vecino más próximo, que en el
    centro es la esquina superior por el criterio `t < 0.5` de `consultar`.
    """
    r = evaluar("""
      const M = FDD_MALLA;
      const nT = M.temperaturas_C.length, nQ = M.cargas.length;
      const nC = M.nClases, nS = M.nSeveridades;
      const iC = M.clases.indexOf('condensador_sucio'), iS = 3;
      const plano = (t, q) => ((t * nQ + q) * nC + iC) * nS + iS;
      for (let iT = 0; iT < nT - 1; iT++) {
        for (let iQ = 0; iQ < nQ - 1; iQ++) {
          const idxC = ((iT * (nQ - 1) + iQ) * nC + iC) * nS + iS;
          if (M.celda_bilineal[idxC] !== 1) continue;
          const T = (M.temperaturas_C[iT] + M.temperaturas_C[iT + 1]) / 2;
          const q = (M.cargas[iQ] + M.cargas[iQ + 1]) / 2;
          const centro = FDD.consultar(T, q, 'condensador_sucio', M.severidades[iS]);
          if (centro === null || centro._interpolacion !== 'bilineal') continue;
          const esq = [plano(iT, iQ), plano(iT + 1, iQ),
                       plano(iT, iQ + 1), plano(iT + 1, iQ + 1)];
          // En el centro, t = 0,5 en los dos ejes, asi que el vecino mas
          // proximo es la esquina alta: `t < 0.5` es falso en ambos.
          const vecino = esq[3];
          const limpias = esq.map(k => M.datos.res_SC[k]);
          const ruidosas = esq.map(k => M.datos.res_ruidoso_SC[k]);
          const media = (ruidosas[0] + ruidosas[1] + ruidosas[2] + ruidosas[3]) / 4;
          return {
            celda: [iT, iQ],
            limpio_centro: centro.res_SC,
            limpio_en_alguna_esquina: limpias.some(v => v === centro.res_SC),
            ruidoso_centro: centro.res_ruidoso_SC,
            ruidoso_vecino: M.datos.res_ruidoso_SC[vecino],
            ruidoso_media_4: media,
            dispersion_esquinas: Math.max.apply(null, ruidosas)
                               - Math.min.apply(null, ruidosas)
          };
        }
      }
      return null;
    """)
    assert "error" not in r, r
    assert r["ok"] is not None, "no se encontró ninguna celda interpolable de prueba"
    o = r["ok"]
    assert not o["limpio_en_alguna_esquina"], (
        "el campo limpio debería haberse interpolado en el centro de la celda")
    assert o["ruidoso_centro"] == o["ruidoso_vecino"], (
        f"el bloque ruidoso NO es el del vecino más próximo en la celda {o['celda']}: "
        f"{o['ruidoso_centro']} frente a {o['ruidoso_vecino']}")
    # Y no es la media de las cuatro esquinas, que es lo que daría una bilineal
    # en el centro y lo que reduciría el ruido a la mitad.
    assert o["dispersion_esquinas"] > 0.0
    assert o["ruidoso_centro"] != pytest.approx(o["ruidoso_media_4"], abs=1e-9), (
        "el valor servido coincide con la media de las cuatro esquinas: se interpoló")


def test_diagnosticar_declara_con_que_ruido_clasifica():
    r = evaluar("""
      const d = FDD.diagnosticar(30, 0.70, 'condensador_sucio', 0.75);
      const cols = FDD_MODELO.columnas_entrada;
      return {semilla: d.semilla, factor_ruido: d.factor_ruido,
              nivel_discrepancia: d.nivel_discrepancia,
              modo_discrepancia: d.modo_discrepancia,
              clase: d.diagnostico.clase, confianza: d.diagnostico.confianza,
              usa_ruidoso: d.residuos[cols[0]] === FDD.consultar(30, 0.70,
                  'condensador_sucio', 0.75)[FDD_MALLA.residuo_ruidoso[cols[0]]],
              tiene_limpios: d.residuos_limpios[cols[0]] !== undefined};
    """)
    assert "error" not in r, r
    o = r["ok"]
    from src.exportador_web import FACTOR_RUIDO_MALLA, SEMILLA_MALLA
    from config.params import MODO_DISCREPANCIA, NIVEL_DISCREPANCIA
    assert o["semilla"] == SEMILLA_MALLA
    assert o["factor_ruido"] == FACTOR_RUIDO_MALLA
    assert o["nivel_discrepancia"] == NIVEL_DISCREPANCIA
    assert o["modo_discrepancia"] == MODO_DISCREPANCIA
    assert o["usa_ruidoso"], "`diagnosticar` no está clasificando el bloque ruidoso"
    assert o["tiene_limpios"], "los residuos limpios deben seguir disponibles"
    assert isinstance(o["clase"], str) and len(o["clase"]) > 0


# ---------------------------------------------------------------------------
# 5. Dominio de entrenamiento: la malla llega más abajo que el dataset
# ---------------------------------------------------------------------------
# `config/params.py` muestreó el hipercubo latino con `Q_load_frac >= 0,40`, y la
# malla se extendió hasta 0,28 para poder dibujar la zona de ciclado. El
# clasificador no vio ni un solo punto de esa banda —el dataset tiene cero filas
# por debajo de 0,40 y cero filas en ciclado—, así que ahí no se diagnostica.
def test_la_malla_declara_el_dominio_de_entrenamiento():
    """Los rangos se LEEN de la configuración que generó el dataset."""
    from config.params import RangosContorno
    from src.exportador_web import dominio_entrenamiento

    r = RangosContorno()
    res = evaluar("return FDD_MALLA.dominio_entrenamiento;")
    assert "error" not in res, res
    d = res["ok"]
    assert d["T_amb_C"] == [r.T_amb_min, r.T_amb_max]
    assert d["Q_load_frac"] == [r.Q_load_frac_min, r.Q_load_frac_max]
    assert d["HR_amb_pct"] == [r.HR_amb_min, r.HR_amb_max]
    assert d["ejes_comprobados"] == ["T_amb_C", "Q_load_frac"]
    esperado = dominio_entrenamiento()
    assert d["T_amb_C"] == esperado["T_amb_C"]
    assert d["Q_load_frac"] == esperado["Q_load_frac"]


def test_el_dominio_declarado_cubre_los_datos_realmente_muestreados():
    """Guardia contra una configuración que ya no describa los `.parquet`.

    Si alguien cambiara `RangosContorno` sin regenerar los datos, el dato
    exportado mentiría. Esta prueba compara el rango declarado con los mínimos y
    máximos que de verdad hay en los datasets.
    """
    import pandas as pd

    from src.exportador_web import dominio_entrenamiento

    rutas = [RAIZ / "data" / "dataset_balanceado.parquet",
             RAIZ / "data" / "dataset_prevalencia.parquet"]
    if not all(r.exists() for r in rutas):
        pytest.skip("los datasets no están generados")
    d = dominio_entrenamiento()
    for ruta in rutas:
        df = pd.read_parquet(ruta, columns=["T_amb", "Q_load_frac"])
        assert df["Q_load_frac"].min() >= d["Q_load_frac"][0] - 1e-9, ruta.name
        assert df["Q_load_frac"].max() <= d["Q_load_frac"][1] + 1e-9, ruta.name
        assert df["T_amb"].min() >= d["T_amb_C"][0] - 1e-9, ruta.name
        assert df["T_amb"].max() <= d["T_amb_C"][1] + 1e-9, ruta.name


@pytest.mark.parametrize("tAmb,carga,ejes", [
    (30.0, 0.28, ["Q_load_frac"]),   # el suelo de la malla, muy por debajo del dataset
    (30.0, 0.31, ["Q_load_frac"]),
    (30.0, 0.34, ["Q_load_frac"]),
    (30.0, 0.37, ["Q_load_frac"]),
    (37.0, 0.70, ["T_amb_C"]),       # dentro del margen de malla, fuera del dataset
    (23.0, 0.30, ["T_amb_C", "Q_load_frac"]),
    (30.0, 1.03, ["Q_load_frac"]),   # por ENCIMA del techo de carga del dataset
])
def test_fuera_del_dominio_se_marca_y_no_se_clasifica(tAmb, carga, ejes):
    r = evaluar(f"""
      const e = FDD.consultar({tAmb}, {carga}, 'sano', 0);
      const d = FDD.diagnosticar({tAmb}, {carga}, 'sano', 0);
      return {{marca: e._fuera_de_entrenamiento,
               ejes: e._fuera_de_entrenamiento_ejes.map(x => x.eje),
               diagnostico: d.diagnostico, residuos: d.residuos,
               bandera: d.fuera_de_entrenamiento, motivo: d.motivo,
               hay_estado: d.estado !== null && isFinite(d.estado.T4_C)}};
    """)
    assert "error" not in r, r
    o = r["ok"]
    assert o["marca"] is True, f"({tAmb}, {carga}) no quedó marcado"
    assert sorted(o["ejes"]) == sorted(ejes)
    assert o["diagnostico"] is None, "se clasificó un punto fuera del dominio de entrenamiento"
    assert o["residuos"] is None
    assert o["bandera"] is True
    assert "fuera del dominio de entrenamiento" in o["motivo"]
    # El ESTADO del ciclo sí se devuelve: lo que falta es el mandato, no el cálculo.
    assert o["hay_estado"] is True


@pytest.mark.parametrize("tAmb,carga", [(24.0, 0.40), (30.0, 0.70), (36.0, 1.00)])
def test_dentro_del_dominio_si_se_clasifica(tAmb, carga):
    """Los bordes exactos del dominio cuentan como DENTRO."""
    r = evaluar(f"""
      const e = FDD.consultar({tAmb}, {carga}, 'condensador_sucio', 0.75);
      const d = FDD.diagnosticar({tAmb}, {carga}, 'condensador_sucio', 0.75);
      return {{marca: e._fuera_de_entrenamiento, ejes: e._fuera_de_entrenamiento_ejes,
               clase: d.diagnostico && d.diagnostico.clase,
               bandera: d.fuera_de_entrenamiento}};
    """)
    assert "error" not in r, r
    o = r["ok"]
    assert o["marca"] is False, f"({tAmb}, {carga}) está dentro del dominio y quedó marcado"
    assert o["ejes"] == []
    assert o["bandera"] is False
    assert isinstance(o["clase"], str)


def test_la_marca_cubre_toda_la_zona_de_ciclado():
    """El defecto 1 vive en la zona de ciclado; la marca debe cubrirla entera.

    No es una coincidencia afortunada: la máquina solo cicla por debajo de la
    carga mínima que sostiene el compresor, y el dataset nunca bajó hasta ahí.
    Pero conviene comprobarlo en lugar de suponerlo.
    """
    r = evaluar("""
      const M = FDD_MALLA, d = M.dominio_entrenamiento;
      const nT = M.temperaturas_C.length, nQ = M.cargas.length;
      const nC = M.nClases, nS = M.nSeveridades;
      let ciclado = 0, cicladoCubierto = 0, imposibles = 0, imposiblesCubiertos = 0;
      let sinEstado = 0, sinEstadoCubierto = 0;
      for (let i = 0; i < M.discretos.ciclado.length; i++) {
        const q = Math.floor(i / (nS * nC)) % nQ, t = Math.floor(i / (nS * nC * nQ)) % nT;
        const carga = M.cargas[q], T = M.temperaturas_C[t];
        const fuera = carga < d.Q_load_frac[0] || carga > d.Q_load_frac[1]
                   || T < d.T_amb_C[0] || T > d.T_amb_C[1];
        if (M.discretos.convergio[i] === 0) { sinEstado++; if (fuera) sinEstadoCubierto++; }
        if (M.discretos.ciclado[i] === 1) {
          ciclado++; if (fuera) cicladoCubierto++;
          if (M.datos.y_capacidad[i] < FDD_FISICA.capacidad_minima_compresor) {
            imposibles++; if (fuera) imposiblesCubiertos++;
          }
        }
      }
      return {ciclado, cicladoCubierto, imposibles, imposiblesCubiertos,
              sinEstado, sinEstadoCubierto};
    """)
    assert "error" not in r, r
    o = r["ok"]
    assert o["imposibles"] > 0 and o["ciclado"] > 0
    assert o["imposiblesCubiertos"] == o["imposibles"], (
        f"{o['imposibles'] - o['imposiblesCubiertos']} estados imposibles del defecto 1 "
        "quedan DENTRO del dominio de entrenamiento y se seguirían diagnosticando")
    assert o["cicladoCubierto"] == o["ciclado"], (
        "la zona de ciclado no queda cubierta entera por la marca")
    # Las dos marcas NO son redundantes: hay nodos sin estado estacionario
    # dentro del dominio, que solo atrapa la comprobación de `convergio`.
    assert o["sinEstadoCubierto"] < o["sinEstado"], (
        "si la marca de entrenamiento cubriera todos los nodos sin estado "
        "estacionario, la comprobación de `convergio` sería redundante; no lo es")


# ---------------------------------------------------------------------------
# 6. Contrato estático de la página de demostración
# ---------------------------------------------------------------------------
# El comportamiento de `web/demo.html` se verifica en un navegador real; aquí se
# fija lo que debe cumplirse SIEMPRE y es barato comprobar: que abra con doble
# clic bajo file://, que no traiga dependencias externas, y que no escriba a mano
# datos que deben viajar desde Python.
DEMO = RAIZ / "web" / "demo.html"


@pytest.fixture(scope="module")
def demo_html():
    if not DEMO.exists():
        pytest.skip("web/demo.html no existe")
    return DEMO.read_text(encoding="utf-8")


def test_la_demo_no_tiene_dependencias_externas(demo_html):
    import re

    fuentes = re.findall(r'<script[^>]+src="([^"]+)"', demo_html)
    assert fuentes == ["datos/fdd_modelo.js", "datos/fdd_fisica.js",
                       "datos/fdd_malla.js", "datos/fdd_metricas.js",
                       "js/fdd_inferencia.js"]
    for f in fuentes:
        assert (RAIZ / "web" / f).exists(), f
    assert re.search(r'<link[^>]+href=', demo_html) is None, "la demo enlaza una hoja externa"
    assert "//cdn" not in demo_html and "https://" not in demo_html


def _sin_comentarios(html: str) -> str:
    """Quita los comentarios HTML y las lineas `//` del script."""
    import re

    sin = re.sub(r"<!--.*?-->", "", html, flags=re.S)
    return "\n".join(ln for ln in sin.splitlines() if not ln.strip().startswith("//"))


def test_la_demo_no_usa_fetch_ni_modulos(demo_html):
    """Bajo `file://` el origen es `null` y `fetch()` queda bloqueado."""
    codigo = _sin_comentarios(demo_html)
    for prohibido in ("fetch(", "XMLHttpRequest", "import(", 'type="module"'):
        assert prohibido not in codigo, (
            f"`{prohibido}` aparece en el código de la demo, no solo en un comentario")


def test_la_guardia_de_comentarios_no_es_vacua(demo_html):
    """Si `_sin_comentarios` dejara de quitar nada, la prueba anterior mentiría."""
    assert len(_sin_comentarios(demo_html)) < len(demo_html)
    assert "fetch()" in demo_html, "el comentario que explica por qué no se usa fetch"


def test_la_demo_lleva_el_rotulo_fijo(demo_html):
    for trozo in ("enfriadora condensada por aire", "R-134a", "100 TR (351,7 kW)",
                  "Sistema distinto del congelador del sitio", "Resultados simulados"):
        assert trozo in demo_html, f"falta del rótulo fijo: {trozo}"


def test_la_demo_no_escribe_a_mano_los_datos_que_vienen_de_python(demo_html):
    """Rangos, unidades y signos esperados se LEEN de los `.js`, no se teclean."""
    for clave in ("dominio_entrenamiento", "margen_extrapolacion", "unidades_residuos",
                  "residuo_ruidoso", "ruido_malla", "firmas_esperadas",
                  "residuo_caracteristico", "capacidad_minima_compresor"):
        assert clave in demo_html, f"la demo no lee `{clave}`"
    # Ninguna lista de residuos ni de clases escrita a mano.
    assert "res_SH_evap" not in demo_html, "hay nombres de residuo escritos a mano"
    assert "condensador_sucio" not in demo_html.split("<script>")[0], (
        "hay nombres de clase escritos a mano en el marcado")


def test_la_demo_no_clasifica_cuando_diagnosticar_se_niega(demo_html):
    """La regla que impide que la página deshaga lo corregido en el JS.

    `FDD.predecir(d.residuos_limpios)` existe en la página para la columna
    limpia. Tiene que quedar DESPUÉS del early return que atiende
    `d.diagnostico === null`, o la demo volvería a diagnosticar donde el modelo
    no sabe nada.
    """
    corte = demo_html.index("if (d.diagnostico === null) {")
    predecir = demo_html.index("FDD.predecir(d.residuos_limpios)")
    assert corte < predecir, (
        "`predecir()` sobre los residuos limpios aparece antes del rechazo: la "
        "demo clasificaría puntos que `diagnosticar()` se niega a clasificar")
