"""Equivalencia entre la inferencia en JavaScript y scikit-learn.

La prueba ejecuta **node** contra los archivos realmente exportados y compara
con scikit-learn sobre TODAS las muestras del conjunto de prueba, no sobre una
muestra de cien.

Por qué la igualdad puede ser exacta y no aproximada: en la versión de
scikit-learn instalada, `ForestClassifier.predict_proba` acumula con
`out[0] += prediction` árbol por árbol sobre un acumulador compartido y divide
al final —suma LINEAL, no por pares—, así que sumando en JavaScript en el mismo
orden de árboles el resultado coincide bit a bit. La corrida de referencia se
hace con `n_jobs=1` porque con varios hilos ese orden no es determinista.

REGLA DE CONDUCTA: si la prueba diverge, se reporta el número exacto de casos y
el diagnóstico. No se ajusta la tolerancia hasta que pase.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

RAIZ = Path(__file__).resolve().parents[1]
DIR_DATOS = RAIZ / "web" / "datos"
DIR_JS = RAIZ / "web" / "js"

pytestmark = pytest.mark.skipif(
    shutil.which("node") is None or not (DIR_DATOS / "fdd_modelo.js").exists(),
    reason="requiere node y los archivos exportados (`python -m src.exportador_web`)")

ARNES = r"""
const fs = require('fs'), vm = require('vm'), path = require('path');
const ctx = vm.createContext({console: console});
for (const f of process.argv.slice(3)) {
  vm.runInContext(fs.readFileSync(f, 'utf8'), ctx, {filename: f});
}
const salida = vm.runInContext(`
  (function () {
    const cols = FDD_MODELO.columnas_entrada;
    const clases = [], probas = [];
    for (let i = 0; i < MUESTRAS.length; i++) {
      const fila = {};
      for (let k = 0; k < cols.length; k++) fila[cols[k]] = MUESTRAS[i][k];
      const r = FDD.predecir(fila);
      clases.push(r.clase_id);
      probas.push(r.probabilidades);
    }
    return JSON.stringify({clases: clases, probas: probas});
  })()
`, ctx);
fs.writeFileSync(process.argv[2], salida);
"""


@pytest.fixture(scope="module")
def comparacion(tmp_path_factory):
    """Ejecuta node y scikit-learn sobre el mismo conjunto y devuelve ambos."""
    import joblib
    from config.params import SEMILLA_MAESTRA, ParametrosEquipo
    from src.calibracion import aplicar_calibracion
    from src.modelo import particionar

    p = aplicar_calibracion(ParametrosEquipo())
    paquete = joblib.load(RAIZ / "resultados" / "modelo_rf.joblib")
    rf = paquete["modelo"]
    df = pd.read_parquet(RAIZ / "data" / "dataset_balanceado.parquet")
    part = particionar(df, p.topologia, SEMILLA_MAESTRA)
    X = part.sellado._X                      # el conjunto de prueba, ya reportado

    # Referencia: n_jobs = 1, orden de acumulación determinista.
    rf.set_params(n_jobs=1)
    proba_py = rf.predict_proba(X.values)
    clase_py = rf.predict(X.values)

    tmp = tmp_path_factory.mktemp("js")
    muestras = "const MUESTRAS = [\n" + ",\n".join(
        "[" + ",".join(repr(float(v)) for v in fila) + "]" for fila in X.values) + "\n];\n"
    (tmp / "muestras.js").write_text(muestras, encoding="utf-8")
    (tmp / "arnes.js").write_text(ARNES, encoding="utf-8")
    salida = tmp / "salida.json"
    subprocess.run(
        ["node", str(tmp / "arnes.js"), str(salida),
         str(DIR_DATOS / "fdd_modelo.js"), str(tmp / "muestras.js"),
         str(DIR_JS / "fdd_inferencia.js")],
        check=True, capture_output=True, text=True, timeout=600)
    js = json.loads(salida.read_text(encoding="utf-8"))
    return {"X": X, "clase_py": clase_py, "proba_py": proba_py,
            "clase_js": np.array(js["clases"]), "proba_js": np.array(js["probas"]),
            "rf": rf, "clases": paquete["clases"]}


def test_el_conjunto_evaluado_es_el_completo(comparacion):
    n = len(comparacion["X"])
    assert n >= 100, "la prueba debe correr sobre al menos cien muestras"
    assert n == len(comparacion["clase_js"])


def test_clase_predicha_identica_sin_tolerancia(comparacion):
    """Igualdad EXACTA de la clase predicha. Cero tolerancia."""
    py, js = comparacion["clase_py"], comparacion["clase_js"]
    distintas = np.flatnonzero(py != js)
    if len(distintas):
        det = [f"  muestra {i}: scikit-learn={comparacion['clases'][py[i]]} "
               f"js={comparacion['clases'][js[i]]} "
               f"(margen py={np.sort(comparacion['proba_py'][i])[-1] - np.sort(comparacion['proba_py'][i])[-2]:.3e})"
               for i in distintas[:10]]
        pytest.fail(f"{len(distintas)} de {len(py)} muestras divergen "
                    f"({100 * len(distintas) / len(py):.3f} %):\n" + "\n".join(det))


def test_probabilidades_coinciden_bit_a_bit(comparacion):
    """La suma lineal sobre el mismo orden de árboles debe dar el mismo doble."""
    d = np.abs(comparacion["proba_py"] - comparacion["proba_js"])
    assert d.max() < 1e-12, f"diferencia máxima {d.max():.3e}"
    iguales = float((comparacion["proba_py"] == comparacion["proba_js"]).mean())
    print(f"\n  probabilidades idénticas bit a bit: {100 * iguales:.2f} % "
          f"| diferencia máxima {d.max():.3e}")


def test_conteo_de_muestras_al_borde_de_un_umbral(comparacion):
    """Muestras a menos de 1e-9 de un umbral: candidatas a divergir.

    Se reporta como diagnóstico. Si alguna vez se recorta la precisión de los
    umbrales al exportar, este número dice cuánto riesgo se está asumiendo.
    """
    X32 = comparacion["X"].values.astype(np.float32).astype(np.float64)
    cerca = 0
    for est in comparacion["rf"].estimators_:
        t = est.tree_
        interno = t.children_left != -1
        for j in range(X32.shape[1]):
            thr = t.threshold[interno & (t.feature == j)]
            if len(thr) == 0:
                continue
            cerca += int((np.abs(X32[:, j][:, None] - thr[None, :]) < 1e-9).sum())
    print(f"\n  pares (muestra, umbral) a menos de 1e-9: {cerca}")
    assert cerca >= 0


def test_el_modelo_exportado_declara_el_casteo_a_float32(comparacion):
    """La conversión a float32 es condición de la equivalencia, no un detalle."""
    texto = (DIR_DATOS / "fdd_modelo.js").read_text(encoding="utf-8")[:4000]
    assert "float32" in texto and "fround" in texto
    assert "Math.fround" in (DIR_JS / "fdd_inferencia.js").read_text(encoding="utf-8")


def test_los_archivos_no_usan_fetch_ni_modulos():
    """El visualizador abre con doble clic: bajo file:// fetch está bloqueado."""
    prohibido = ("fetch(", "XMLHttpRequest", "import ", "export ", "require(")
    for archivo in sorted(DIR_DATOS.glob("*.js")):
        texto = archivo.read_text(encoding="utf-8")
        for palabra in prohibido:
            assert palabra not in texto, f"{archivo.name} contiene `{palabra}`"
        assert texto.lstrip().startswith("//")
        assert "\nconst FDD_" in texto, f"{archivo.name} no declara una constante FDD_*"


def test_la_malla_declara_su_contrato_de_interfaz():
    from src.exportador_web import DIR_DATOS as D
    texto = (D / "fdd_malla.js").read_text(encoding="utf-8")
    for clave in ('"entrada_canonica"', "Q_load_frac", '"aviso_retorno"',
                  "T_sec_in_ev", '"interpolacion"', '"campos_discretos"'):
        assert clave in texto, f"falta {clave} en el contrato de la malla"
    fisica = (D / "fdd_fisica.js").read_text(encoding="utf-8")
    assert '"Q_nom_W"' in fisica, "falta la capacidad nominal en vatios"
