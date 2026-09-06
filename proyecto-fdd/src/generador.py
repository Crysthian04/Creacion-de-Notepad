"""Barrido de condiciones, inyección de fallas, ruido y construcción del dataset.

Cuatro puntos de diseño que este módulo hace cumplir:

1. DOS BARRIDOS INDEPENDIENTES. El conjunto de prevalencia realista NO se
   obtiene submuestreando el barrido de entrenamiento: se genera con su propio
   motor de hipercubo latino y su propio flujo de semilla (pool A y pool B).

2. DISCREPANCIA ENTRE MODELO Y PLANTA. Los datos se generan con `theta_planta`;
   la predicción sana que se resta se calcula con
   `theta_modelo = theta_planta·(1 + epsilon)`. Representa el error de
   calibración del gemelo digital, que en una instalación real es la fuente de
   error DOMINANTE, muy por encima del ruido de los instrumentos.

   Consecuencia directa: las filas de clase `sano` dejan de tener residuo nulo.
   Sin discrepancia, el residuo sano es puro ruido de sensor y la separación
   entre clases resulta trivial por construcción.

3. CONVERGENCIA VERIFICADA Y CONTABILIZADA. Ningún punto entra al dataset sin
   que el solver haya cerrado los balances. Los descartes se cuentan por clase y
   por causa (sección 3.2).

4. RUIDO TRAZABLE. sigma = exactitud/2 de la hoja `Instrumentos` (sección 5).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from joblib import Parallel, delayed
from scipy.stats import qmc

from config.params import (DISTRIBUCION_DISCREPANCIA, FLUJOS_ALEATORIOS,
                           MODO_DISCREPANCIA, NIVEL_DISCREPANCIA,
                           N_COND_ENTRENAMIENTO, N_MUESTRAS_PREVALENCIA,
                           RangosContorno, SIGMA_RUIDO, TOL_BALANCE,
                           parametros_con_discrepancia)
from .ciclo import AjustesCiclo, CondicionContorno, resolver_ciclo
from .fallas import NIVELES, ajustes_de_falla, clase_a_id, clases
from .features import calcular_residuos, derivadas_desde_medicion
from .topologia import Topologia, variables_medibles

RAIZ = Path(__file__).resolve().parents[1]

# Prevalencia de campo (sección 6.2). Plausible, NO medida: se ajusta cuando el
# historial de mantenimiento de la instalación esté disponible.
_PREVALENCIA_COMUN = {
    "carga_baja": 0.040,
    "txv_restringida": 0.030,
    "compresor_desgastado": 0.025,
    "restriccion_linea_liquido": 0.015,
    "incondensables": 0.010,
    "sobrecarga": 0.007,
    "txv_sobrealimenta": 0.003,
}


def prevalencia_campo(topo: Topologia) -> dict[str, float]:
    p = {"sano": 0.68}
    p["incrustacion_condensador" if topo.cond_es_agua else "condensador_sucio"] = 0.08
    if topo.evap_es_agua:
        p["incrustacion_evaporador"] = 0.06
        p["caudal_agua_bajo"] = 0.05
    else:
        p["evaporador_sucio"] = 0.11
    p.update(_PREVALENCIA_COMUN)
    assert abs(sum(p.values()) - 1.0) < 1e-9, sum(p.values())
    assert set(p) == set(clases(topo))
    return p


# ---------------------------------------------------------------------------
# Semillas
# ---------------------------------------------------------------------------
def rng_desde(semilla: np.random.SeedSequence) -> np.random.Generator:
    """Generador reproducible a partir de un SeedSequence.

    NO se usa `np.random.default_rng(seed_sequence)` directamente: en NumPy >= 2
    esa llamada deriva un hijo NUEVO en cada invocación, de modo que dos llamadas
    con el mismo objeto producen secuencias DISTINTAS. Reconstruir el
    SeedSequence desde su entropía y su `spawn_key` sí es estable.
    """
    return np.random.default_rng(
        np.random.SeedSequence(semilla.entropy, spawn_key=semilla.spawn_key))


def semillas_hijas(semilla: np.random.SeedSequence, n: int,
                   marca: tuple = ()) -> list[np.random.SeedSequence]:
    base = np.random.SeedSequence(semilla.entropy, spawn_key=(*semilla.spawn_key, *marca))
    return base.spawn(n)


def semillas_derivadas(semilla_maestra: int) -> dict[str, np.random.SeedSequence]:
    hijos = np.random.SeedSequence(semilla_maestra).spawn(len(FLUJOS_ALEATORIOS))
    return dict(zip(FLUJOS_ALEATORIOS, hijos))


# ---------------------------------------------------------------------------
# Barrido de condiciones (hipercubo latino)
# ---------------------------------------------------------------------------
def muestrear_condiciones(n: int, semilla: np.random.SeedSequence, p,
                          rangos: RangosContorno | None = None,
                          prefijo: str = "A") -> pd.DataFrame:
    """Hipercubo latino sobre (T_amb, HR_amb, Q_load_frac) — sección 6.1."""
    rangos = rangos or RangosContorno()
    motor = qmc.LatinHypercube(d=3, seed=rng_desde(semilla))
    u = motor.random(n)
    lo = np.array([rangos.T_amb_min, rangos.HR_amb_min, rangos.Q_load_frac_min])
    hi = np.array([rangos.T_amb_max, rangos.HR_amb_max, rangos.Q_load_frac_max])
    x = qmc.scale(u, lo, hi)
    return pd.DataFrame({
        "cond_id": [f"{prefijo}{i:05d}" for i in range(n)],
        "T_amb": x[:, 0], "HR_amb": x[:, 1], "Q_load_frac": x[:, 2],
    })


# ---------------------------------------------------------------------------
# Discrepancia entre modelo y planta
# ---------------------------------------------------------------------------
def muestrear_discrepancia(p, semilla: np.random.SeedSequence, n: int,
                           nivel: float = NIVEL_DISCREPANCIA,
                           modo: str = MODO_DISCREPANCIA) -> list[dict[str, float]]:
    """Un vector de error de calibración por condición (o uno para toda la corrida).

    `por_condicion` — cada condición ve un gemelo desafinado distinto. Mide el
        efecto PROMEDIO del nivel de discrepancia.
    `por_corrida`   — un único error de calibración para todo el dataset, que es
        lo que le ocurre a UNA implantación concreta. Repetir la corrida con
        semillas distintas mide cuán distinto le puede ir a cada instalación.
    """
    nombres = parametros_con_discrepancia(p)
    rng = rng_desde(semilla)
    if nivel <= 0.0:
        return [{k: 0.0 for k in nombres} for _ in range(n)]
    if DISTRIBUCION_DISCREPANCIA != "uniforme":
        raise ValueError(f"Distribución no soportada: {DISTRIBUCION_DISCREPANCIA}")
    if modo == "por_corrida":
        eps = {k: float(rng.uniform(-nivel, nivel)) for k in nombres}
        return [dict(eps) for _ in range(n)]
    if modo != "por_condicion":
        raise ValueError(f"Modo de discrepancia desconocido: {modo}")
    return [{k: float(v) for k, v in zip(nombres, rng.uniform(-nivel, nivel, len(nombres)))}
            for _ in range(n)]


def aplicar_discrepancia(p, eps: dict[str, float]):
    """`theta_modelo` = `theta_planta`·(1 + epsilon)."""
    if not eps or all(v == 0.0 for v in eps.values()):
        return p
    return p.con(**{k: getattr(p, k) * (1.0 + v) for k, v in eps.items()})


# ---------------------------------------------------------------------------
# Ruido de sensor (sección 5)
# ---------------------------------------------------------------------------
def aplicar_ruido(medible: dict[str, float], rng: np.random.Generator,
                  factor: float = 1.0) -> dict[str, float]:
    ruidoso = {}
    for k, v in medible.items():
        sigma, tipo = SIGMA_RUIDO.get(k, (0.0, "absoluto"))
        s = sigma * factor if tipo == "absoluto" else sigma * factor * abs(v)
        ruidoso[k] = float(v + rng.normal(0.0, s)) if s > 0 else float(v)
    return ruidoso


# ---------------------------------------------------------------------------
# Contabilidad de convergencia
# ---------------------------------------------------------------------------
@dataclass
class ContabilidadSolver:
    intentos: int = 0
    convergidos: int = 0
    descartados: int = 0
    descartes_por_clase: dict | None = None
    descartes_por_motivo: dict | None = None
    condiciones_descartadas: int = 0

    def __post_init__(self):
        self.descartes_por_clase = self.descartes_por_clase or {}
        self.descartes_por_motivo = self.descartes_por_motivo or {}

    def registrar(self, convergio: bool, clase: str, motivo: str = "") -> None:
        self.intentos += 1
        if convergio:
            self.convergidos += 1
            return
        self.descartados += 1
        self.descartes_por_clase[clase] = self.descartes_por_clase.get(clase, 0) + 1
        clave = motivo.split("(")[0].strip() if motivo else "desconocido"
        self.descartes_por_motivo[clave] = self.descartes_por_motivo.get(clave, 0) + 1

    def fusionar(self, otra: "ContabilidadSolver") -> None:
        self.intentos += otra.intentos
        self.convergidos += otra.convergidos
        self.descartados += otra.descartados
        self.condiciones_descartadas += otra.condiciones_descartadas
        for k, v in otra.descartes_por_clase.items():
            self.descartes_por_clase[k] = self.descartes_por_clase.get(k, 0) + v
        for k, v in otra.descartes_por_motivo.items():
            self.descartes_por_motivo[k] = self.descartes_por_motivo.get(k, 0) + v

    @property
    def fraccion_descartada(self) -> float:
        return self.descartados / self.intentos if self.intentos else 0.0

    def informe(self) -> str:
        l = ["Convergencia del solver del ciclo", "-" * 62,
             f"  puntos intentados       : {self.intentos}",
             f"  convergidos             : {self.convergidos}",
             f"  DESCARTADOS             : {self.descartados} "
             f"({100 * self.fraccion_descartada:.2f} %)",
             f"  condiciones descartadas : {self.condiciones_descartadas} "
             f"(la referencia sana no convergió)"]
        if self.descartes_por_clase:
            l.append("  descartes por clase:")
            for c, n in sorted(self.descartes_por_clase.items(), key=lambda kv: -kv[1]):
                l.append(f"      {c:28s} {n}")
            l.append("  descartes por motivo:")
            for m, n in sorted(self.descartes_por_motivo.items(), key=lambda kv: -kv[1]):
                l.append(f"      {m[:46]:48s} {n}")
        return "\n".join(l)

    def a_dict(self) -> dict:
        return {"intentos": self.intentos, "convergidos": self.convergidos,
                "descartados": self.descartados,
                "fraccion_descartada": self.fraccion_descartada,
                "condiciones_descartadas": self.condiciones_descartadas,
                "descartes_por_clase": self.descartes_por_clase,
                "descartes_por_motivo": self.descartes_por_motivo}


# ---------------------------------------------------------------------------
# Construcción de una fila
# ---------------------------------------------------------------------------
def _fila(cond_row, cond, clase, f, nivel, estado_deg, medible_ref, derivadas_ref,
          rng_ruido, p, factor_ruido, muestra_id) -> dict:
    topo = p.topologia
    medido = aplicar_ruido(estado_deg.dict_medible(), rng_ruido, factor_ruido)
    derivadas_med = derivadas_desde_medicion(medido, p)
    residuos = calcular_residuos(derivadas_med, derivadas_ref, topo)

    fila = {"T_amb": cond.T_amb, "HR_amb": cond.HR_amb, "Q_load_frac": cond.Q_load_frac}
    fila.update({k: medido[k] for k in variables_medibles(topo)})
    fila.update({f"{k}_ref": medible_ref[k] for k in variables_medibles(topo)})
    fila.update(residuos)
    fila.update({
        "clase": clase, "clase_id": clase_a_id(topo)[clase],
        "severidad_f": f, "nivel": nivel,
        "cond_id": cond_row["cond_id"], "muestra_id": muestra_id,
        # Banderas del control: metadatos de análisis, EXCLUIDAS de la matriz X
        # (ver features.EXCLUIDAS_Y_MOTIVO) porque están correlacionadas con la
        # severidad de la falla y entrenar con ellas sería fuga.
        "capacidad_saturada": bool(estado_deg.capacidad_saturada),
        "ciclado": bool(estado_deg.ciclado),
        "retorno_liquido": bool(estado_deg.retorno_liquido),
        "regimen": estado_deg.regimen,
        "desviacion_setpoint": float(estado_deg.desviacion_setpoint),
        "y_capacidad": float(estado_deg.y_capacidad),
    })
    return fila


def _referencia_sana(cond, p_modelo):
    """Predicción del modelo SANO a las mismas condiciones, SIN ruido.

    Se calcula con `theta_modelo`, que difiere de la planta en el error de
    calibración del gemelo digital.
    """
    estado = resolver_ciclo(cond, p_modelo, AjustesCiclo(), tol=TOL_BALANCE)
    if not estado.convergio:
        return None, None, None
    medible_ref = estado.dict_medible()
    return estado, medible_ref, derivadas_desde_medicion(medible_ref, p_modelo)


def residuos_sin_ruido(cond, clase: str, f: float, p) -> dict | None:
    """Residuos de un punto SIN ruido de sensor y SIN discrepancia.

    Instrumento de verificación física del proyecto: aísla la firma de la falla
    del ruido de medición y del error de calibración, de modo que los signos sean
    deterministas. Lo usan `tests/test_firmas.py` y el mapa de firmas.
    """
    estado_ref, medible_ref, derivadas_ref = _referencia_sana(cond, p)
    if estado_ref is None:
        return None
    if clase == "sano":
        estado_deg = estado_ref
    else:
        estado_deg = resolver_ciclo(cond, p, ajustes_de_falla(clase, f, p), tol=TOL_BALANCE)
        if not estado_deg.convergio:
            return None
    return calcular_residuos(derivadas_desde_medicion(estado_deg.dict_medible(), p),
                             derivadas_ref, p.topologia)


# ---------------------------------------------------------------------------
# Generación por condición (unidad de paralelismo)
# ---------------------------------------------------------------------------
def _procesar_condicion_balanceado(cond_row, eps, semilla_ruido, semilla_sev, p,
                                   factor_ruido):
    topo = p.topologia
    cond = CondicionContorno(T_amb=cond_row["T_amb"], HR_amb=cond_row["HR_amb"],
                             Q_load_frac=cond_row["Q_load_frac"])
    cont = ContabilidadSolver()
    p_modelo = aplicar_discrepancia(p, eps)
    estado_ref_modelo, medible_ref, derivadas_ref = _referencia_sana(cond, p_modelo)
    if estado_ref_modelo is None:
        cont.condiciones_descartadas += 1
        return [], cont
    # El estado SANO DE LA PLANTA es distinto del que predice el modelo.
    estado_sano_planta = resolver_ciclo(cond, p, AjustesCiclo(), tol=TOL_BALANCE)
    if not estado_sano_planta.convergio:
        cont.condiciones_descartadas += 1
        return [], cont

    rng_ruido = np.random.default_rng(semilla_ruido)
    rng_sev = np.random.default_rng(semilla_sev)
    filas = []
    for clase in clases(topo):
        for nivel, (lo, hi) in NIVELES.items():
            if clase == "sano":
                f, nivel_fila, estado_deg = 0.0, "sano", estado_sano_planta
            else:
                f = float(rng_sev.uniform(lo, hi))
                nivel_fila = nivel
                estado_deg = resolver_ciclo(cond, p, ajustes_de_falla(clase, f, p),
                                            tol=TOL_BALANCE)
            cont.registrar(estado_deg.convergio, clase, estado_deg.motivo)
            if not estado_deg.convergio:
                continue
            filas.append(_fila(cond_row, cond, clase, f, nivel_fila, estado_deg,
                               medible_ref, derivadas_ref, rng_ruido, p, factor_ruido,
                               f"{cond_row['cond_id']}-{clase}-{nivel_fila}"))
    return filas, cont


def _procesar_condicion_prevalencia(cond_row, eps, semilla_ruido, semilla_sorteo, p,
                                    factor_ruido, prevalencia):
    cond = CondicionContorno(T_amb=cond_row["T_amb"], HR_amb=cond_row["HR_amb"],
                             Q_load_frac=cond_row["Q_load_frac"])
    cont = ContabilidadSolver()
    p_modelo = aplicar_discrepancia(p, eps)
    estado_ref_modelo, medible_ref, derivadas_ref = _referencia_sana(cond, p_modelo)
    if estado_ref_modelo is None:
        cont.condiciones_descartadas += 1
        return [], cont
    estado_sano_planta = resolver_ciclo(cond, p, AjustesCiclo(), tol=TOL_BALANCE)
    if not estado_sano_planta.convergio:
        cont.condiciones_descartadas += 1
        return [], cont

    rng = np.random.default_rng(semilla_sorteo)
    nombres = list(prevalencia)
    clase = str(rng.choice(nombres, p=np.array([prevalencia[c] for c in nombres])))
    if clase == "sano":
        f, nivel_fila, estado_deg = 0.0, "sano", estado_sano_planta
    else:
        nivel_fila = str(rng.choice(list(NIVELES)))
        lo, hi = NIVELES[nivel_fila]
        f = float(rng.uniform(lo, hi))
        estado_deg = resolver_ciclo(cond, p, ajustes_de_falla(clase, f, p), tol=TOL_BALANCE)
    cont.registrar(estado_deg.convergio, clase, estado_deg.motivo)
    if not estado_deg.convergio:
        return [], cont
    fila = _fila(cond_row, cond, clase, f, nivel_fila, estado_deg, medible_ref,
                 derivadas_ref, np.random.default_rng(semilla_ruido), p, factor_ruido,
                 f"{cond_row['cond_id']}-{clase}")
    return [fila], cont


# ---------------------------------------------------------------------------
# Conjuntos
# ---------------------------------------------------------------------------
def generar_balanceado(p, semillas, n_cond=N_COND_ENTRENAMIENTO, factor_ruido=1.0,
                       nivel_discrepancia=NIVEL_DISCREPANCIA,
                       modo_discrepancia=MODO_DISCREPANCIA, n_jobs=-1, verbose=True):
    """Clases × 3 niveles × n_cond condiciones, balanceado por diseño."""
    conds = muestrear_condiciones(n_cond, semillas["lhs_entrenamiento"], p, prefijo="A")
    hijas_ruido = semillas_hijas(semillas["ruido"], n_cond)
    hijas_sev = semillas_hijas(semillas["severidad"], n_cond)
    eps = muestrear_discrepancia(p, semillas["discrepancia"], n_cond,
                                 nivel_discrepancia, modo_discrepancia)

    resultados = Parallel(n_jobs=n_jobs, verbose=5 if verbose else 0)(
        delayed(_procesar_condicion_balanceado)(
            conds.iloc[i], eps[i], hijas_ruido[i], hijas_sev[i], p, factor_ruido)
        for i in range(n_cond))

    filas, cont = [], ContabilidadSolver()
    for f_i, c_i in resultados:
        filas.extend(f_i)
        cont.fusionar(c_i)
    return pd.DataFrame(filas), cont


def generar_prevalencia(p, semillas, n_muestras=N_MUESTRAS_PREVALENCIA, factor_ruido=1.0,
                        nivel_discrepancia=NIVEL_DISCREPANCIA,
                        modo_discrepancia=MODO_DISCREPANCIA, n_jobs=-1, verbose=True):
    """Segundo conjunto INDEPENDIENTE con proporciones plausibles de campo."""
    conds = muestrear_condiciones(n_muestras, semillas["lhs_prevalencia"], p, prefijo="B")
    hijas_ruido = semillas_hijas(semillas["ruido"], n_muestras, marca=(99,))
    hijas_sorteo = semillas_hijas(semillas["severidad"], n_muestras, marca=(99,))
    eps = muestrear_discrepancia(p, semillas_hijas(semillas["discrepancia"], 1, (99,))[0],
                                 n_muestras, nivel_discrepancia, modo_discrepancia)
    prev = prevalencia_campo(p.topologia)

    resultados = Parallel(n_jobs=n_jobs, verbose=5 if verbose else 0)(
        delayed(_procesar_condicion_prevalencia)(
            conds.iloc[i], eps[i], hijas_ruido[i], hijas_sorteo[i], p, factor_ruido, prev)
        for i in range(n_muestras))

    filas, cont = [], ContabilidadSolver()
    for f_i, c_i in resultados:
        filas.extend(f_i)
        cont.fusionar(c_i)
    return pd.DataFrame(filas), cont


# ---------------------------------------------------------------------------
# Orquestación
# ---------------------------------------------------------------------------
def generar_todo(p, semilla_maestra, n_cond=N_COND_ENTRENAMIENTO,
                 n_prev=N_MUESTRAS_PREVALENCIA, factor_ruido=1.0,
                 nivel_discrepancia=NIVEL_DISCREPANCIA,
                 modo_discrepancia=MODO_DISCREPANCIA, destino=None, sufijo="",
                 verbose=True) -> dict:
    destino = destino or (RAIZ / "data")
    destino.mkdir(parents=True, exist_ok=True)
    semillas = semillas_derivadas(semilla_maestra)

    if verbose:
        print(f"\n[1/2] Conjunto BALANCEADO — {n_cond} condiciones (pool A), "
              f"discrepancia {nivel_discrepancia:.0%} ({modo_discrepancia})")
    df_bal, cont_bal = generar_balanceado(p, semillas, n_cond, factor_ruido,
                                          nivel_discrepancia, modo_discrepancia,
                                          verbose=verbose)
    if verbose:
        print(f"\n[2/2] Conjunto de PREVALENCIA — {n_prev} muestras (pool B, independiente)")
    df_prev, cont_prev = generar_prevalencia(p, semillas, n_prev, factor_ruido,
                                             nivel_discrepancia, modo_discrepancia,
                                             verbose=verbose)

    ruta_bal = destino / f"dataset_balanceado{sufijo}.parquet"
    ruta_prev = destino / f"dataset_prevalencia{sufijo}.parquet"
    df_bal.to_parquet(ruta_bal, index=False)
    df_prev.to_parquet(ruta_prev, index=False)

    meta = {
        "topologia": p.topologia.nombre,
        "semilla_maestra": semilla_maestra,
        "factor_ruido": factor_ruido,
        "nivel_discrepancia": nivel_discrepancia,
        "modo_discrepancia": modo_discrepancia,
        "n_cond_entrenamiento": n_cond,
        "n_muestras_prevalencia": n_prev,
        "filas_balanceado": len(df_bal), "filas_prevalencia": len(df_prev),
        "convergencia_balanceado": cont_bal.a_dict(),
        "convergencia_prevalencia": cont_prev.a_dict(),
        "prevalencia_objetivo": prevalencia_campo(p.topologia),
        "prevalencia_obtenida": (df_prev["clase"].value_counts(normalize=True).to_dict()
                                 if len(df_prev) else {}),
        "banderas": {
            "capacidad_saturada": int(df_bal["capacidad_saturada"].sum()) if len(df_bal) else 0,
            "ciclado": int(df_bal["ciclado"].sum()) if len(df_bal) else 0,
            "retorno_liquido": int(df_bal["retorno_liquido"].sum()) if len(df_bal) else 0,
        },
        "rutas": {"balanceado": str(ruta_bal), "prevalencia": str(ruta_prev)},
    }
    if verbose:
        print("\n" + cont_bal.informe())
        print("\n" + cont_prev.informe())
        print(f"\nBanderas del control en el conjunto balanceado: {meta['banderas']}")
    return {"balanceado": df_bal, "prevalencia": df_prev, "meta": meta}


if __name__ == "__main__":
    import argparse, sys
    sys.path.insert(0, str(RAIZ))
    from config.params import SEMILLA_MAESTRA, ParametrosEquipo, advertir_provisionales
    from .calibracion import aplicar_calibracion

    ap = argparse.ArgumentParser(description="Genera los dos datasets del proyecto FDD.")
    ap.add_argument("--n-cond", type=int, default=N_COND_ENTRENAMIENTO)
    ap.add_argument("--n-prev", type=int, default=N_MUESTRAS_PREVALENCIA)
    ap.add_argument("--factor-ruido", type=float, default=1.0)
    ap.add_argument("--discrepancia", type=float, default=NIVEL_DISCREPANCIA)
    ap.add_argument("--modo-discrepancia", default=MODO_DISCREPANCIA)
    ap.add_argument("--sufijo", type=str, default="")
    args = ap.parse_args()

    advertir_provisionales()
    p = aplicar_calibracion(ParametrosEquipo())
    print(f"Topología: {p.topologia.nombre} | refrigerante {p.refrigerante} | "
          f"UA_ev={p.UA_ev:.0f} UA_cd={p.UA_cd:.0f} W/K")

    out = generar_todo(p, SEMILLA_MAESTRA, args.n_cond, args.n_prev, args.factor_ruido,
                       args.discrepancia, args.modo_discrepancia, sufijo=args.sufijo)
    ruta_meta = RAIZ / "resultados" / f"generacion{args.sufijo}.json"
    ruta_meta.parent.mkdir(parents=True, exist_ok=True)
    ruta_meta.write_text(json.dumps(out["meta"], indent=2, ensure_ascii=False),
                         encoding="utf-8")
    print(f"\nMetadatos -> {ruta_meta}")
