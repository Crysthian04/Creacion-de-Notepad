"""Carga y validación del archivo de entrada (JSON o YAML) con los datos
de un comparativo de proveedores."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any

from .layout import CRITERIOS, PESO_TOTAL

CAMPOS_TEXTO_PROVEEDOR = [
    "nombre",
    "legalmente_constituido",
    "cumplimiento_especificaciones",
    "terminos_pago",
    "tiempo_respuesta",
]

CAMPOS_PONDERADO_PROVEEDOR = [f"{clave}_ponderado" for clave, _, _ in CRITERIOS]


class ErrorValidacion(Exception):
    """Error de datos de entrada, con mensaje pensado para un usuario no programador."""


@dataclass
class Proveedor:
    nombre: str
    legalmente_constituido: str
    legalmente_constituido_ponderado: float
    cumplimiento_especificaciones: str
    cumplimiento_especificaciones_ponderado: float
    precio: float
    precio_ponderado: float
    terminos_pago: str
    terminos_pago_ponderado: float
    tiempo_respuesta: str
    tiempo_respuesta_ponderado: float

    def total_ponderado(self) -> float:
        return (
            self.legalmente_constituido_ponderado
            + self.cumplimiento_especificaciones_ponderado
            + self.precio_ponderado
            + self.terminos_pago_ponderado
            + self.tiempo_respuesta_ponderado
        )


@dataclass
class Comparativo:
    fecha: str
    bien_o_servicio: str
    negociador: str
    req_numero: str
    req_descripcion: str
    proveedores: list[Proveedor]
    proveedor_sugerido: str
    proveedor_autorizado: str
    observaciones: str
    advertencias: list[str] = field(default_factory=list)


def _cargar_datos_crudos(ruta: str) -> dict:
    if not os.path.isfile(ruta):
        raise ErrorValidacion(f"No se encontró el archivo de entrada: {ruta}")

    with open(ruta, "r", encoding="utf-8") as f:
        contenido = f.read()

    ext = os.path.splitext(ruta)[1].lower()
    if ext == ".json":
        try:
            return json.loads(contenido)
        except json.JSONDecodeError as e:
            raise ErrorValidacion(
                f"El archivo '{ruta}' no es un JSON válido: {e}"
            ) from e
    elif ext in (".yaml", ".yml"):
        try:
            import yaml
        except ImportError as e:
            raise ErrorValidacion(
                "Para usar archivos .yaml necesitas instalar PyYAML: pip install pyyaml"
            ) from e
        try:
            return yaml.safe_load(contenido)
        except yaml.YAMLError as e:
            raise ErrorValidacion(
                f"El archivo '{ruta}' no es un YAML válido: {e}"
            ) from e
    else:
        raise ErrorValidacion(
            f"Extensión no soportada '{ext}'. Usa un archivo .json o .yaml"
        )


def _requerir(datos: dict, campo: str, contexto: str = "") -> Any:
    if campo not in datos or datos[campo] in (None, ""):
        raise ErrorValidacion(
            f"Falta el campo obligatorio '{campo}'{(' en ' + contexto) if contexto else ''}."
        )
    return datos[campo]


def _requerir_numero(datos: dict, campo: str, contexto: str = "") -> float:
    valor = _requerir(datos, campo, contexto)
    try:
        return float(valor)
    except (TypeError, ValueError):
        raise ErrorValidacion(
            f"El campo '{campo}'{(' en ' + contexto) if contexto else ''} debe ser numérico, "
            f"se recibió: {valor!r}"
        )


def _validar_si_no(valor: str, campo: str, contexto: str) -> str:
    valor_norm = str(valor).strip().upper()
    if valor_norm not in ("SI", "NO", "SÍ"):
        raise ErrorValidacion(
            f"El campo '{campo}' en {contexto} debe ser 'SI' o 'NO' (se recibió: {valor!r})."
        )
    return "SI" if valor_norm in ("SI", "SÍ") else "NO"


def _parsear_proveedor(datos: dict, indice: int) -> Proveedor:
    contexto = f"el proveedor #{indice + 1}"
    for campo in CAMPOS_TEXTO_PROVEEDOR + CAMPOS_PONDERADO_PROVEEDOR:
        if campo not in datos or datos[campo] in (None, ""):
            raise ErrorValidacion(f"Falta el campo '{campo}' en {contexto}.")

    nombre = str(_requerir(datos, "nombre", contexto)).strip()
    contexto = f"el proveedor '{nombre}'"

    return Proveedor(
        nombre=nombre,
        legalmente_constituido=_validar_si_no(
            datos["legalmente_constituido"], "legalmente_constituido", contexto
        ),
        legalmente_constituido_ponderado=_requerir_numero(
            datos, "legalmente_constituido_ponderado", contexto
        ),
        cumplimiento_especificaciones=_validar_si_no(
            datos["cumplimiento_especificaciones"],
            "cumplimiento_especificaciones",
            contexto,
        ),
        cumplimiento_especificaciones_ponderado=_requerir_numero(
            datos, "cumplimiento_especificaciones_ponderado", contexto
        ),
        precio=_requerir_numero(datos, "precio", contexto),
        precio_ponderado=_requerir_numero(datos, "precio_ponderado", contexto),
        terminos_pago=str(_requerir(datos, "terminos_pago", contexto)).strip(),
        terminos_pago_ponderado=_requerir_numero(
            datos, "terminos_pago_ponderado", contexto
        ),
        tiempo_respuesta=str(_requerir(datos, "tiempo_respuesta", contexto)).strip(),
        tiempo_respuesta_ponderado=_requerir_numero(
            datos, "tiempo_respuesta_ponderado", contexto
        ),
    )


def cargar_comparativo(ruta: str) -> Comparativo:
    datos = _cargar_datos_crudos(ruta)
    if not isinstance(datos, dict):
        raise ErrorValidacion(
            "El archivo de entrada debe contener un objeto/mapa en la raíz "
            "(en JSON: '{ ... }')."
        )

    for campo in (
        "fecha",
        "bien_o_servicio",
        "negociador",
        "req_numero",
        "req_descripcion",
        "proveedor_sugerido",
        "proveedor_autorizado",
        "observaciones",
    ):
        _requerir(datos, campo)

    bien_o_servicio = str(datos["bien_o_servicio"]).strip().upper()
    if bien_o_servicio not in ("BIEN", "SERVICIO"):
        raise ErrorValidacion(
            f"'bien_o_servicio' debe ser 'BIEN' o 'SERVICIO' (se recibió: "
            f"{datos['bien_o_servicio']!r})."
        )

    proveedores_raw = datos.get("proveedores")
    if not isinstance(proveedores_raw, list) or len(proveedores_raw) == 0:
        raise ErrorValidacion(
            "Debes indicar una lista 'proveedores' con entre 1 y 3 proveedores."
        )
    if len(proveedores_raw) > 3:
        raise ErrorValidacion(
            f"Solo se permiten entre 1 y 3 proveedores (se recibieron "
            f"{len(proveedores_raw)})."
        )

    proveedores = [
        _parsear_proveedor(p, i) for i, p in enumerate(proveedores_raw)
    ]

    comparativo = Comparativo(
        fecha=str(datos["fecha"]).strip(),
        bien_o_servicio=bien_o_servicio,
        negociador=str(datos["negociador"]).strip(),
        req_numero=str(datos["req_numero"]).strip(),
        req_descripcion=str(datos["req_descripcion"]).strip(),
        proveedores=proveedores,
        proveedor_sugerido=str(datos["proveedor_sugerido"]).strip(),
        proveedor_autorizado=str(datos["proveedor_autorizado"]).strip(),
        observaciones=str(datos["observaciones"]).strip(),
    )

    # Advertencia (no bloqueante): el total ponderado de cada proveedor debería
    # sumar el 100% del peso total de los criterios.
    for prov in comparativo.proveedores:
        total = prov.total_ponderado()
        if abs(total - PESO_TOTAL) > 0.01:
            comparativo.advertencias.append(
                f"El proveedor '{prov.nombre}' suma {total:g}% de %Ponderado, "
                f"pero el peso total de los criterios es {PESO_TOTAL:g}%. "
                f"Revisa los valores manuales de %Ponderado."
            )

    return comparativo
