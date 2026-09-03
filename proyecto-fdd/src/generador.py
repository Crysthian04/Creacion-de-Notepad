"""Barrido de condiciones, inyección de fallas, ruido y construcción del dataset.

Tres puntos de diseño que este módulo hace cumplir:

1. DOS BARRIDOS INDEPENDIENTES. El conjunto de prevalencia realista NO se obtiene
   submuestreando el barrido de entrenamiento: se genera con su propio motor de
   hipercubo latino y su propio flujo de semilla (pool A y pool B). Una prueba
   verifica que los pools no se solapan.

2. CONVERGENCIA VERIFICADA Y CONTABILIZADA. Ningún punto entra al dataset sin que
   el solver haya cerrado el balance de energía. Los descartes se cuentan por
   clase y por causa, y quedan registrados en `resultados/metricas.json`
   (sección 3.2).

3. RUIDO TRAZABLE. sigma = exactitud/2 de la hoja `Instrumentos`, nunca un número
   inventado (sección 5).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import qmc

from config.params import (FLUJOS_ALEATORIOS, N_COND_ENTRENAMIENTO,
                           N_MUESTRAS_PREVALENCIA, RangosContorno, SIGMA_RUIDO,
                           TOL_BALANCE)
from .ciclo import VARIABLES_MEDIBLES, AjustesCiclo, CondicionContorno, resolver_ciclo
from .fallas import CLASE_A_ID, CLASES, NIVELES, ajustes_de_falla
from .features import calcular_residuos, derivadas_desde_medicion

RAIZ = Path(__file__).resolve().parents[1]

# Prevalencia de campo (sección 6.2). Suma 1,00.
PREVALENCIA_CAMPO: dict[str, float] = {
    "sano": 0.700,
    "condensador_sucio": 0.080,
    "evaporador_sucio": 0.060,
    "carga_baja": 0.050,
    "txv_restringida": 0.030,
    "compresor_desgastado": 0.030,
    "restriccion_linea_liquido": 0.020,
    "incondensables": 0.015,
    "sobrecarga": 0.010,
    "txv_sobrealimenta": 0.005,
}
assert abs(sum(PREVALENCIA_CAMPO.values()) - 1.0) < 1e-12
assert set(PREVALENCIA_CAMPO) == set(CLASES)


# ---------------------------------------------------------------------------
# Semillas: una sola raíz, flujos derivados con nombre
# ---------------------------------------------------------------------------
def rng_desde(semilla: np.random.SeedSequence) -> np.random.Generator:
    """Generador reproducible a partir de un SeedSequence.

    NO se usa `np.random.default_rng(seed_sequence)` directamente: en NumPy >= 2
    esa llamada deriva un hijo NUEVO en cada invocación —el SeedSequence lleva la
    cuenta de los hijos ya generados—, de modo que dos llamadas con el mismo
    objeto producen secuencias DISTINTAS. Reconstruir el SeedSequence a partir de
    su entropía y su `spawn_key` sí es estable, y es lo que hace esta función.

    Lo detectó `tests/test_particion.py::test_muestreo_reproducible_con_la_misma_semilla`.
    Es exactamente el tipo de fallo silencioso que la auditoría de la Etapa 1
    señaló en el defecto D10: la semilla estaba puesta y aun así el resultado no
    era reproducible.
    """
    return np.random.default_rng(
        np.random.SeedSequence(semilla.entropy, spawn_key=semilla.spawn_key))


def semillas_hijas(semilla: np.random.SeedSequence, n: int,
                   marca: tuple = ()) -> list[np.random.SeedSequence]:
    """`n` semillas hijas deterministas, con una marca opcional que separa usos."""
    base = np.random.SeedSequence(semilla.entropy, spawn_key=(*semilla.spawn_key, *marca))
    return base.spawn(n)


def semillas_derivadas(semilla_maestra: int) -> dict[str, np.random.SeedSequence]:
    """Un SeedSequence por flujo, derivado de la semilla maestra.

    El orden de FLUJOS_ALEATORIOS es parte de la definición de reproducibilidad:
    cambiarlo cambia todos los resultados del proyecto.
    """
    hijos = np.random.SeedSequence(semilla_maestra).spawn(len(FLUJOS_ALEATORIOS))
    return dict(zip(FLUJOS_ALEATORIOS, hijos))


# ---------------------------------------------------------------------------
# Barrido de condiciones de contorno (hipercubo latino)
# ---------------------------------------------------------------------------
def muestrear_condiciones(n: int, semilla: np.random.SeedSequence, p,
                          rangos: RangosContorno | None = None,
                          prefijo: str = "A") -> pd.DataFrame:
    """Hipercubo latino sobre (T_amb, HR_amb, Q_load_frac) — sección 6.1.

    Se usa LHS y no una malla regular: cubre mejor el espacio y evita que el
    modelo memorice una rejilla. `T_space` queda en el setpoint del panel de
    control, tal como opera el equipo.
    """
    rangos = rangos or RangosContorno()
    motor = qmc.LatinHypercube(d=3, seed=rng_desde(semilla))
    u = motor.random(n)
    lo = np.array([rangos.T_amb_min, rangos.HR_amb_min, rangos.Q_load_frac_min])
    hi = np.array([rangos.T_amb_max, rangos.HR_amb_max, rangos.Q_load_frac_max])
    x = qmc.scale(u, lo, hi)
    return pd.DataFrame({
        "cond_id": [f"{prefijo}{i:05d}" for i in range(n)],
        "T_amb": x[:, 0],
        "HR_amb": x[:, 1],
        "T_space": np.full(n, p.T_space_sp),
        "Q_load_frac": x[:, 2],
    })


# ---------------------------------------------------------------------------
# Ruido de sensor (sección 5)
# ---------------------------------------------------------------------------
def aplicar_ruido(medible: dict[str, float], rng: np.random.Generator,
                  factor: float = 1.0) -> dict[str, float]:
    """Ruido gaussiano aditivo con sigma = exactitud/2 de la hoja `Instrumentos`.

    `factor` escala todas las sigmas a la vez: se usa en el estudio de
    sensibilidad al ruido (0,5× y 2×) de la sección 5.
    """
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
    descartes_por_clase: dict = None
    descartes_por_motivo: dict = None
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
        clave = motivo.split(":")[0] if motivo else "desconocido"
        self.descartes_por_motivo[clave] = self.descartes_por_motivo.get(clave, 0) + 1

    @property
    def fraccion_descartada(self) -> float:
        return self.descartados / self.intentos if self.intentos else 0.0

    def informe(self) -> str:
        l = ["Convergencia del solver del ciclo",
             "-" * 60,
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
                l.append(f"      {m[:44]:46s} {n}")
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
def _fila(cond_row, cond: CondicionContorno, clase: str, f: float, nivel: str,
          estado_deg, medible_ref: dict, derivadas_ref: dict,
          rng_ruido: np.random.Generator, p, factor_ruido: float,
          muestra_id: str) -> dict:
    medido = aplicar_ruido(estado_deg.dict_medible(), rng_ruido, factor_ruido)
    derivadas_med = derivadas_desde_medicion(medido, p)
    residuos = calcular_residuos(derivadas_med, derivadas_ref)

    fila = {
        # condiciones de contorno
        "T_amb": cond.T_amb, "HR_amb": cond.HR_amb,
        "T_space": cond.T_space, "Q_load_frac": cond.Q_load_frac,
    }
    fila.update({k: medido[k] for k in VARIABLES_MEDIBLES})                 # crudas
    fila.update({f"{k}_ref": medible_ref[k] for k in VARIABLES_MEDIBLES})   # referencia sana
    fila.update(residuos)                                                    # residuos
    fila.update({"clase": clase, "clase_id": CLASE_A_ID[clase],
                 "severidad_f": f, "nivel": nivel,
                 "cond_id": cond_row["cond_id"], "muestra_id": muestra_id})
    return fila


def _referencia_sana(cond: CondicionContorno, p):
    """Predicción del modelo SANO a las mismas condiciones, SIN ruido."""
    estado = resolver_ciclo(cond, p, AjustesCiclo(), tol=TOL_BALANCE)
    if not estado.convergio:
        return None, None, None
    medible_ref = estado.dict_medible()
    derivadas_ref = derivadas_desde_medicion(medible_ref, p)
    return estado, medible_ref, derivadas_ref


def residuos_sin_ruido(cond: CondicionContorno, clase: str, f: float, p) -> dict | None:
    """Residuos de un punto SIN ruido de sensor.

    Es el instrumento de verificación física del proyecto: aísla la firma de la
    falla del ruido de medición, de modo que los signos sean deterministas. Lo
    usan `tests/test_firmas.py` y el mapa de firmas (figura 7).

    Devuelve None si el ciclo sano o el degradado no convergen en ese punto.
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
    derivadas_med = derivadas_desde_medicion(estado_deg.dict_medible(), p)
    return calcular_residuos(derivadas_med, derivadas_ref)


# ---------------------------------------------------------------------------
# Conjunto balanceado (sección 6.1)
# ---------------------------------------------------------------------------
def generar_balanceado(p, semillas: dict, n_cond: int = N_COND_ENTRENAMIENTO,
                       factor_ruido: float = 1.0, verbose: bool = True
                       ) -> tuple[pd.DataFrame, ContabilidadSolver]:
    """10 clases × 3 niveles × n_cond condiciones, balanceado por diseño."""
    conds = muestrear_condiciones(n_cond, semillas["lhs_entrenamiento"], p, prefijo="A")
    hijas_ruido = semillas_hijas(semillas["ruido"], n_cond)
    hijas_sev = semillas_hijas(semillas["severidad"], n_cond)

    cont = ContabilidadSolver()
    filas: list[dict] = []

    for i, cond_row in conds.iterrows():
        cond = CondicionContorno(T_amb=cond_row["T_amb"], HR_amb=cond_row["HR_amb"],
                                 T_space=cond_row["T_space"],
                                 Q_load_frac=cond_row["Q_load_frac"])
        estado_ref, medible_ref, derivadas_ref = _referencia_sana(cond, p)
        if estado_ref is None:
            cont.condiciones_descartadas += 1
            continue

        rng_ruido = np.random.default_rng(hijas_ruido[i])
        rng_sev = np.random.default_rng(hijas_sev[i])

        for clase in CLASES:
            for nivel, (lo, hi) in NIVELES.items():
                if clase == "sano":
                    f, nivel_fila = 0.0, "sano"
                    estado_deg = estado_ref
                else:
                    f = float(rng_sev.uniform(lo, hi))
                    nivel_fila = nivel
                    aj = ajustes_de_falla(clase, f, p)
                    estado_deg = resolver_ciclo(cond, p, aj, tol=TOL_BALANCE)
                cont.registrar(estado_deg.convergio, clase, estado_deg.motivo)
                if not estado_deg.convergio:
                    continue
                filas.append(_fila(cond_row, cond, clase, f, nivel_fila, estado_deg,
                                   medible_ref, derivadas_ref, rng_ruido, p, factor_ruido,
                                   muestra_id=f"{cond_row['cond_id']}-{clase}-{nivel_fila}"))
        if verbose and (i + 1) % 50 == 0:
            print(f"  condiciones procesadas: {i + 1}/{n_cond}  "
                  f"(filas={len(filas)}, descartes={cont.descartados})", flush=True)

    return pd.DataFrame(filas), cont


# ---------------------------------------------------------------------------
# Conjunto de prevalencia realista (sección 6.2) — POOL B, INDEPENDIENTE
# ---------------------------------------------------------------------------
def generar_prevalencia(p, semillas: dict, n_muestras: int = N_MUESTRAS_PREVALENCIA,
                        factor_ruido: float = 1.0, verbose: bool = True
                        ) -> tuple[pd.DataFrame, ContabilidadSolver]:
    """Segundo conjunto INDEPENDIENTE con proporciones plausibles de campo.

    Sus condiciones de contorno provienen de un barrido LHS propio (pool B). No
    comparte ninguna condición con el conjunto balanceado.
    """
    conds = muestrear_condiciones(n_muestras, semillas["lhs_prevalencia"], p, prefijo="B")
    # La marca (99,) separa el uso del pool B del uso del pool A dentro del
    # mismo flujo, sin que uno consuma el estado del otro.
    hijas_ruido = semillas_hijas(semillas["ruido"], n_muestras, marca=(99,))
    rng_clase = rng_desde(semillas_hijas(semillas["severidad"], 1, marca=(99,))[0])

    nombres = list(PREVALENCIA_CAMPO)
    probs = np.array([PREVALENCIA_CAMPO[c] for c in nombres])
    clases_sorteadas = rng_clase.choice(nombres, size=n_muestras, p=probs)
    niveles = list(NIVELES)

    cont = ContabilidadSolver()
    filas: list[dict] = []

    for i, cond_row in conds.iterrows():
        cond = CondicionContorno(T_amb=cond_row["T_amb"], HR_amb=cond_row["HR_amb"],
                                 T_space=cond_row["T_space"],
                                 Q_load_frac=cond_row["Q_load_frac"])
        estado_ref, medible_ref, derivadas_ref = _referencia_sana(cond, p)
        if estado_ref is None:
            cont.condiciones_descartadas += 1
            continue

        rng_ruido = np.random.default_rng(hijas_ruido[i])
        clase = str(clases_sorteadas[i])
        if clase == "sano":
            f, nivel_fila, estado_deg = 0.0, "sano", estado_ref
        else:
            nivel_fila = str(rng_clase.choice(niveles))
            lo, hi = NIVELES[nivel_fila]
            f = float(rng_clase.uniform(lo, hi))
            estado_deg = resolver_ciclo(cond, p, ajustes_de_falla(clase, f, p), tol=TOL_BALANCE)

        cont.registrar(estado_deg.convergio, clase, estado_deg.motivo)
        if not estado_deg.convergio:
            continue
        filas.append(_fila(cond_row, cond, clase, f, nivel_fila, estado_deg,
                           medible_ref, derivadas_ref, rng_ruido, p, factor_ruido,
                           muestra_id=f"{cond_row['cond_id']}-{clase}"))
        if verbose and (i + 1) % 500 == 0:
            print(f"  muestras procesadas: {i + 1}/{n_muestras}", flush=True)

    return pd.DataFrame(filas), cont


# ---------------------------------------------------------------------------
# Orquestación
# ---------------------------------------------------------------------------
def generar_todo(p, semilla_maestra: int, n_cond: int = N_COND_ENTRENAMIENTO,
                 n_prev: int = N_MUESTRAS_PREVALENCIA, factor_ruido: float = 1.0,
                 destino: Path | None = None, sufijo: str = "", verbose: bool = True
                 ) -> dict:
    destino = destino or (RAIZ / "data")
    destino.mkdir(parents=True, exist_ok=True)
    semillas = semillas_derivadas(semilla_maestra)

    if verbose:
        print(f"\n[1/2] Conjunto BALANCEADO — {n_cond} condiciones (pool A)")
    df_bal, cont_bal = generar_balanceado(p, semillas, n_cond, factor_ruido, verbose)
    if verbose:
        print(f"\n[2/2] Conjunto de PREVALENCIA — {n_prev} muestras (pool B, independiente)")
    df_prev, cont_prev = generar_prevalencia(p, semillas, n_prev, factor_ruido, verbose)

    ruta_bal = destino / f"dataset_balanceado{sufijo}.parquet"
    ruta_prev = destino / f"dataset_prevalencia{sufijo}.parquet"
    df_bal.to_parquet(ruta_bal, index=False)
    df_prev.to_parquet(ruta_prev, index=False)

    meta = {
        "semilla_maestra": semilla_maestra,
        "factor_ruido": factor_ruido,
        "n_cond_entrenamiento": n_cond,
        "n_muestras_prevalencia": n_prev,
        "filas_balanceado": len(df_bal),
        "filas_prevalencia": len(df_prev),
        "convergencia_balanceado": cont_bal.a_dict(),
        "convergencia_prevalencia": cont_prev.a_dict(),
        "prevalencia_objetivo": PREVALENCIA_CAMPO,
        "prevalencia_obtenida": (df_prev["clase"].value_counts(normalize=True)
                                 .to_dict() if len(df_prev) else {}),
        "rutas": {"balanceado": str(ruta_bal), "prevalencia": str(ruta_prev)},
    }
    if verbose:
        print("\n" + cont_bal.informe())
        print("\n" + cont_prev.informe())
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
    ap.add_argument("--sufijo", type=str, default="")
    args = ap.parse_args()

    advertir_provisionales()
    p = aplicar_calibracion(ParametrosEquipo())
    print(f"UA calibrados en uso: UA_ev={p.UA_ev:.1f} W/K  UA_cd={p.UA_cd:.1f} W/K")

    out = generar_todo(p, SEMILLA_MAESTRA, args.n_cond, args.n_prev,
                       args.factor_ruido, sufijo=args.sufijo)
    ruta_meta = RAIZ / "resultados" / f"generacion{args.sufijo}.json"
    ruta_meta.parent.mkdir(parents=True, exist_ok=True)
    ruta_meta.write_text(json.dumps(out["meta"], indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nMetadatos de generación -> {ruta_meta}")
