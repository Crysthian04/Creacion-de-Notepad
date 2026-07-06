#!/usr/bin/env python3
"""
Genera el comparativo de proveedores PSN-LAC-LAC-F-009 a partir de un archivo
de datos (JSON o YAML).

Uso:
    python llenar_comparativo.py datos_req_2026_XXXXX.json

Ver README.md para instrucciones detalladas.
"""

from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from comparativo.excel_generator import generar_excel
from comparativo.modelos import ErrorValidacion, cargar_comparativo
from comparativo.pdf_generator import generar_pdf


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Genera el comparativo de proveedores PSN-LAC-LAC-F-009."
    )
    parser.add_argument(
        "archivo_datos",
        help="Ruta al archivo .json o .yaml con los datos del comparativo",
    )
    parser.add_argument(
        "-o", "--salida",
        help="Carpeta de salida (por defecto: la carpeta actual)",
        default=".",
    )
    parser.add_argument(
        "--solo-pdf",
        action="store_true",
        help="No generar el archivo Excel, solo el PDF",
    )
    args = parser.parse_args()

    try:
        comparativo = cargar_comparativo(args.archivo_datos)
    except ErrorValidacion as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    for advertencia in comparativo.advertencias:
        print(f"ADVERTENCIA: {advertencia}")

    os.makedirs(args.salida, exist_ok=True)
    nombre_base = f"Comparativo_{comparativo.req_numero}"
    ruta_pdf = os.path.join(args.salida, f"{nombre_base}.pdf")
    ruta_xlsx = os.path.join(args.salida, f"{nombre_base}.xlsx")

    generar_pdf(comparativo, ruta_pdf)
    print(f"PDF generado: {ruta_pdf}")

    if not args.solo_pdf:
        generar_excel(comparativo, ruta_xlsx)
        print(f"Excel generado: {ruta_xlsx}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
