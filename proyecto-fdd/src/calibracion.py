"""Calibración de los coeficientes UA de los intercambiadores.

Los `UA` NO se asumen: se ajustan para que el modelo reproduzca las mediciones
de campo del equipo en condición SANA (sección 9 de la especificación). Ese
ajuste es lo que convierte el modelo genérico en un gemelo digital de *ese*
equipo.

Este módulo está separado del solver a propósito: la calibración se va a repetir
cuando lleguen las tres corridas por circuito de la Fase 1 (hoja `Registro
Campo`). Cuando eso ocurra, lo único que cambia es el argumento `mediciones`.

Uso previsto con datos reales
-----------------------------
    mediciones = [
        Medicion(cond=CondicionContorno(T_amb=33.1, HR_amb=78, T_space=24.5,
                                        Q_load_frac=1.0),
                 objetivo={"P_suc": 132.0, "P_des": 405.0}),   # de la hoja
        ...                                                    # una por corrida
    ]
    res = calibrar_UA(mediciones, ParametrosEquipo())

Cualquier atributo de `EstadoCiclo` sirve como variable objetivo: temperaturas
de saturación, presiones manométricas, potencia o capacidad. Se eligen las que
el equipo haya medido con menor incertidumbre.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

import numpy as np
from scipy.optimize import least_squares

from .ciclo import AjustesCiclo, CondicionContorno, resolver_ciclo


@dataclass(frozen=True)
class Medicion:
    """Una corrida de campo en condición sana: contorno + valores observados."""

    cond: CondicionContorno
    objetivo: dict[str, float]
    peso: float = 1.0


@dataclass
class ResultadoCalibracion:
    UA_ev: float
    UA_cd: float
    convergio: bool
    rmse_relativo: float
    residuos: dict[str, float]
    n_evaluaciones: int
    x0: tuple[float, float]
    cotas: tuple[tuple[float, float], tuple[float, float]]
    origen_datos: str
    provisional: bool
    fecha: str = field(default_factory=lambda: date.today().isoformat())

    def informe(self) -> str:
        lineas = [
            "Calibración de los coeficientes UA",
            "-" * 60,
            f"  origen de los datos : {self.origen_datos}",
            f"  provisional         : {'SÍ' if self.provisional else 'no'}",
            f"  UA_ev               : {self.UA_ev:9.1f} W/K   (inicial {self.x0[0]:.1f})",
            f"  UA_cd               : {self.UA_cd:9.1f} W/K   (inicial {self.x0[1]:.1f})",
            f"  convergió           : {'sí' if self.convergio else 'NO'}",
            f"  RMSE relativo       : {self.rmse_relativo:.3e}",
            f"  evaluaciones        : {self.n_evaluaciones}",
            "  residuos por variable objetivo:",
        ]
        for nombre, r in self.residuos.items():
            lineas.append(f"      {nombre:22s} {r:+.4f}")
        return "\n".join(lineas)

    def a_dict(self) -> dict:
        return {
            "UA_ev": self.UA_ev, "UA_cd": self.UA_cd,
            "convergio": self.convergio, "rmse_relativo": self.rmse_relativo,
            "residuos": self.residuos, "n_evaluaciones": self.n_evaluaciones,
            "x0": list(self.x0), "cotas": [list(c) for c in self.cotas],
            "origen_datos": self.origen_datos, "provisional": self.provisional,
            "fecha": self.fecha,
        }


# Escalas de normalización de los residuos, por variable objetivo. Evitan que
# una presión en psig domine sobre una temperatura en K por puro tamaño.
_ESCALA = {
    "T_evap": 1.0, "T_cond": 1.0, "T_liq": 1.0, "T_des": 1.0,
    "T_air_out_ev": 1.0, "T_air_out_cd": 1.0,
    "P_suc": 10.0, "P_des": 25.0,
    "Q_L": 1000.0, "W_elec": 200.0, "I_avg": 1.0,
}


def calibrar_UA(mediciones: list[Medicion],
                params,
                pesos: dict[str, float] | None = None,
                cotas: tuple[tuple[float, float], tuple[float, float]] = ((300.0, 8000.0),
                                                                          (500.0, 12000.0)),
                x0: tuple[float, float] | None = None,
                origen_datos: str = "no declarado",
                provisional: bool = True,
                verbose: bool = False) -> ResultadoCalibracion:
    """Ajusta (UA_ev, UA_cd) por mínimos cuadrados contra las mediciones sanas.

    Parámetros
    ----------
    mediciones : lista de `Medicion`. Una por corrida de campo.
    params     : `ParametrosEquipo`. Solo se modifican UA_ev y UA_cd.
    pesos      : peso por variable objetivo, p. ej. {"P_des": 2.0}. Sirve para
                 dar más importancia a los instrumentos más exactos.
    cotas      : ((UA_ev_min, UA_ev_max), (UA_cd_min, UA_cd_max)) en W/K.
    x0         : valores iniciales. Por defecto, los de `params`.
    """
    if not mediciones:
        raise ValueError("Se necesita al menos una medición para calibrar.")

    pesos = pesos or {}
    x0 = x0 or (params.UA_ev, params.UA_cd)
    contador = {"n": 0}
    # Se ajusta en el logaritmo: los UA son positivos y varían en orden de magnitud.
    log_x0 = np.log(np.array(x0, dtype=float))
    log_cotas = (np.log([cotas[0][0], cotas[1][0]]), np.log([cotas[0][1], cotas[1][1]]))

    etiquetas: list[str] = []

    def residuos(log_x, guardar_etiquetas=False):
        contador["n"] += 1
        ua_ev, ua_cd = np.exp(log_x)
        p = params.con(UA_ev=float(ua_ev), UA_cd=float(ua_cd))
        out = []
        for i, m in enumerate(mediciones):
            estado = resolver_ciclo(m.cond, p, AjustesCiclo())
            for nombre, valor_obj in m.objetivo.items():
                obtenido = getattr(estado, nombre)
                escala = _ESCALA.get(nombre, max(abs(valor_obj), 1.0))
                w = m.peso * pesos.get(nombre, 1.0)
                # Un punto que no converge se penaliza en lugar de abortar:
                # el optimizador se aleja solo de esa zona.
                penalizacion = 0.0 if estado.convergio else 10.0
                out.append(w * ((obtenido - valor_obj) / escala + penalizacion))
                if guardar_etiquetas:
                    etiquetas.append(f"corrida{i}:{nombre}")
        return np.array(out)

    residuos(log_x0, guardar_etiquetas=True)  # fija el orden de las etiquetas

    sol = least_squares(residuos, log_x0, bounds=log_cotas,
                        xtol=1e-12, ftol=1e-12, gtol=1e-12,
                        verbose=2 if verbose else 0)

    ua_ev, ua_cd = (float(v) for v in np.exp(sol.x))
    r_final = residuos(sol.x)
    rmse = float(np.sqrt(np.mean(r_final ** 2)))

    return ResultadoCalibracion(
        UA_ev=ua_ev, UA_cd=ua_cd,
        convergio=bool(sol.success and rmse < 1e-3),
        rmse_relativo=rmse,
        residuos={e: float(r) for e, r in zip(etiquetas, r_final)},
        n_evaluaciones=contador["n"], x0=tuple(x0), cotas=cotas,
        origen_datos=origen_datos, provisional=provisional,
    )


# ---------------------------------------------------------------------------
# Persistencia
# ---------------------------------------------------------------------------
RUTA_CALIBRACION = Path(__file__).resolve().parents[1] / "config" / "ua_calibrado.json"


def guardar_calibracion(res: ResultadoCalibracion, ruta: Path = RUTA_CALIBRACION) -> Path:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(json.dumps(res.a_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
    return ruta


def cargar_calibracion(ruta: Path = RUTA_CALIBRACION) -> dict | None:
    if not ruta.exists():
        return None
    return json.loads(ruta.read_text(encoding="utf-8"))


def aplicar_calibracion(params, ruta: Path = RUTA_CALIBRACION):
    """Devuelve los parámetros con los UA calibrados, si existe el archivo."""
    datos = cargar_calibracion(ruta)
    if datos is None:
        return params
    return params.con(UA_ev=datos["UA_ev"], UA_cd=datos["UA_cd"])


# ---------------------------------------------------------------------------
# Objetivo provisional mientras no existan las mediciones de campo
# ---------------------------------------------------------------------------
def mediciones_provisionales(params) -> list[Medicion]:
    """Punto de diseño de catálogo, en el formato de una corrida de campo.

    Se sustituye por las mediciones reales de la hoja `Registro Campo` en cuanto
    estén disponibles: mismo formato, mismo llamado a `calibrar_UA`.
    """
    from config.params import OBJETIVO_CALIBRACION, PUNTO_DISENO
    return [Medicion(cond=CondicionContorno(**PUNTO_DISENO),
                     objetivo=dict(OBJETIVO_CALIBRACION))]


if __name__ == "__main__":
    import sys, pathlib
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
    from config.params import ParametrosEquipo, PUNTO_DISENO

    p = ParametrosEquipo()
    res = calibrar_UA(mediciones_provisionales(p), p,
                      origen_datos="Punto de diseño de catálogo (PROVISIONAL, "
                                   "sustituir por hoja `Registro Campo` de la Fase 1)",
                      provisional=True)
    print(res.informe())
    ruta = guardar_calibracion(res)
    print(f"\nGuardado en {ruta}")

    p_cal = p.con(UA_ev=res.UA_ev, UA_cd=res.UA_cd)
    e = resolver_ciclo(CondicionContorno(**PUNTO_DISENO), p_cal)
    print(f"\nVerificación en el punto de diseño:")
    print(f"  T_evap={e.T_evap:6.2f} °C  T_cond={e.T_cond:6.2f} °C")
    print(f"  Q_L={e.Q_L:8.1f} W ({e.Q_L/3516.85:.2f} TR)  "
          f"W_elec={e.W_elec:7.1f} W  COP={e.Q_L/e.W_elec:4.2f}")
