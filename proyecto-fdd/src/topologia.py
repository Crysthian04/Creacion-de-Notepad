"""Topología del sistema: qué fluido intercambia en cada lado.

El proyecto soporta tres configuraciones seleccionables. La topología NO es un
supuesto disperso en el código: es un objeto que viaja dentro de
`ParametrosEquipo`, y de él se derivan las variables medidas, las
características del clasificador y el catálogo de modos de falla.

    chiller_cond_aire   evaporador AGUA  / condensador AIRE   <- caso base
    chiller_cond_agua   evaporador AGUA  / condensador AGUA + torre
    expansion_directa   evaporador AIRE  / condensador AIRE   <- respaldo

`expansion_directa` se conserva íntegro: si el acceso a la enfriadora se
complica y hay que cambiar de equipo de estudio, esa topología reproduce el
modelo de expansión directa sin tocar el resto del pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Topologia:
    nombre: str
    fluido_evaporador: str        # "agua" | "aire"
    fluido_condensador: str       # "agua" | "aire"
    control_capacidad: bool       # el compresor modula para sostener el setpoint
    descripcion: str = ""

    @property
    def evap_es_agua(self) -> bool:
        return self.fluido_evaporador == "agua"

    @property
    def cond_es_agua(self) -> bool:
        return self.fluido_condensador == "agua"


TOPOLOGIAS: dict[str, Topologia] = {
    "chiller_cond_aire": Topologia(
        nombre="chiller_cond_aire",
        fluido_evaporador="agua", fluido_condensador="aire",
        control_capacidad=True,
        descripcion="Enfriadora de agua con condensador enfriado por aire. "
                    "Distribución hidrónica hacia manejadoras y fan-coils."),
    "chiller_cond_agua": Topologia(
        nombre="chiller_cond_agua",
        fluido_evaporador="agua", fluido_condensador="agua",
        control_capacidad=True,
        descripcion="Enfriadora de agua con condensador enfriado por agua y "
                    "torre de enfriamiento."),
    "expansion_directa": Topologia(
        nombre="expansion_directa",
        fluido_evaporador="aire", fluido_condensador="aire",
        control_capacidad=False,
        descripcion="Equipo de expansión directa aire-aire, velocidad fija. "
                    "Configuración de respaldo."),
}


# ---------------------------------------------------------------------------
# Variables medidas en campo, por topología (sección 2.2)
# ---------------------------------------------------------------------------
_COMUNES = ("P_suc", "P_des", "T_ev_out", "T_suc", "T_des", "T_liq", "I_avg", "W_elec")


def variables_medibles(topo: Topologia) -> tuple[str, ...]:
    """Solo lo que el equipo puede medir con el inventario de instrumentos."""
    if topo.evap_es_agua:
        evap = ("T_agua_in_ev", "T_agua_out_ev", "V_agua_ev")
    else:
        evap = ("T_air_in_ev", "T_air_out_ev", "V_air_ev")
    if topo.cond_es_agua:
        cond = ("T_agua_in_cd", "T_agua_out_cd", "V_agua_cd")
    else:
        cond = ("T_air_in_cd", "T_air_out_cd")
    return _COMUNES + evap + cond


def nombre_entrada_evaporador(topo: Topologia) -> str:
    return "T_agua_in_ev" if topo.evap_es_agua else "T_air_in_ev"


def nombre_salida_evaporador(topo: Topologia) -> str:
    return "T_agua_out_ev" if topo.evap_es_agua else "T_air_out_ev"


def nombre_entrada_condensador(topo: Topologia) -> str:
    return "T_agua_in_cd" if topo.cond_es_agua else "T_air_in_cd"


def nombre_salida_condensador(topo: Topologia) -> str:
    return "T_agua_out_cd" if topo.cond_es_agua else "T_air_out_cd"


def nombre_caudal_evaporador(topo: Topologia) -> str:
    return "V_agua_ev" if topo.evap_es_agua else "V_air_ev"
