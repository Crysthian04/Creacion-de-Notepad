#!/usr/bin/env python3
"""
Une los PDF de un portafolio estudiantil, ordenándolos automáticamente.
Versión para Claude Code: suelta los PDF en la carpeta y ejecuta el script.

Materia: Selección de Equipos y Trazado de Planta

Flujo:
    1. Detecta todos los .pdf de CARPETA_ENTRADA.
    2. Los clasifica por tipo (portada, notas, exámenes, asignaciones,
       laboratorios, diapositivas, problemas...) y los ordena.
    3. Los une en un solo PDF con marcadores navegables.

Requisito:  pip install pypdf
Ejecutar:   python unir_portafolio.py           (une)
            python unir_portafolio.py --preview  (solo muestra el orden)
"""

import sys
from pathlib import Path
from pypdf import PdfWriter

# ------------------------- CONFIGURACIÓN -------------------------

CARPETA_ENTRADA = Path(".")  # carpeta donde subes los PDF
NOMBRE_SALIDA = Path("Portafolio_Seleccion_Equipos_Trazado_Planta.pdf")
AGREGAR_MARCADORES = True

# Orden de secciones del portafolio. Cada archivo se asigna a la primera
# sección cuyas palabras clave aparezcan en su nombre. Ajusta libremente.
SECCIONES = [
    ("Portada",        ["portada", "caratula", "carátula", "portafolio", "batista"]),
    ("Notas de clase", ["notas de clase", "apuntes", "notas del profesor"]),
    ("Exámenes",       ["examen", "parcial", "clave", "quiz"]),
    ("Asignaciones",   ["asignacion", "asignación", "tarea", "trabajo"]),
    ("Laboratorios",   ["laboratorio", "informe", "lab "]),
    ("Diapositivas",   ["diapositiva", "tema ", "presentacion", "presentación", "ppt"]),
    ("Problemas",      ["problema", "ejercicio", "practica", "práctica"]),
]
SECCION_OTROS = "Otros"  # todo lo que no encaje va al final

# -----------------------------------------------------------------


def clasificar(ruta):
    """Devuelve (indice_seccion, nombre_seccion) según el nombre del archivo."""
    nombre = ruta.name.lower()
    for i, (seccion, claves) in enumerate(SECCIONES):
        if any(clave in nombre for clave in claves):
            return i, seccion
    return len(SECCIONES), SECCION_OTROS


def ordenar_pdfs(carpeta):
    """Detecta y ordena los PDF: por sección y, dentro de cada una, alfabético."""
    pdfs = [p for p in carpeta.glob("*.pdf") if p.resolve() != NOMBRE_SALIDA.resolve()]
    # Ordena por (índice de sección, nombre en minúsculas)
    return sorted(pdfs, key=lambda p: (clasificar(p)[0], p.name.lower()))


def mostrar_orden(rutas):
    print(f"\nOrden detectado ({len(rutas)} archivos):\n")
    seccion_actual = None
    for ruta in rutas:
        _, seccion = clasificar(ruta)
        if seccion != seccion_actual:
            print(f"\n  [{seccion}]")
            seccion_actual = seccion
        print(f"     • {ruta.name}")
    print()


def unir_pdfs(rutas, salida):
    if not rutas:
        print("❌ No se encontró ningún PDF en la carpeta.")
        return

    combinador = PdfWriter()
    unidos = 0
    for ruta in rutas:
        try:
            marcador = ruta.stem if AGREGAR_MARCADORES else None
            combinador.append(str(ruta), outline_item=marcador)
            print(f"  ✅ {ruta.name}")
            unidos += 1
        except Exception as e:
            print(f"  ⚠️  Error en {ruta.name}: {e}")

    if unidos == 0:
        print("\n❌ No se unió ningún archivo.")
        return

    salida.parent.mkdir(parents=True, exist_ok=True)
    with open(salida, "wb") as f:
        combinador.write(f)
    combinador.close()

    print(f"\n✅ ¡Listo! {unidos} archivos unidos.")
    print(f"   Archivo final: {salida.resolve()}")


if __name__ == "__main__":
    rutas = ordenar_pdfs(CARPETA_ENTRADA)
    mostrar_orden(rutas)

    if "--preview" in sys.argv:
        print("Modo vista previa: no se unió nada. Quita --preview para generar el PDF.")
    else:
        unir_pdfs(rutas, NOMBRE_SALIDA)
