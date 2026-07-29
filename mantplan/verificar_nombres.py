"""COMPROBACIÓN ESTRUCTURAL DEL XML de los rangos con nombre.

No es una comprobación de CÁLCULO: se lee `xl/workbook.xml` en crudo, sin
openpyxl, porque el defecto que caza vive en el XML y no en el resultado.

Motivo: en `xl/workbook.xml` la definición de un nombre va como EXPRESIÓN
DESNUDA. Si se escribe con un "=" delante, LibreOffice lo tolera (y por eso el
recálculo no detectaba nada), pero Excel considera corrupto el libro, avisa de
«Registros quitados: Rango con nombre de /xl/workbook.xml» y BORRA el nombre al
reparar: los desplegables que dependían de él se quedan sin lista.

Falla si algún definedName:
  · empieza por "="
  · contiene #REF!
  · está vacío
  · está duplicado (mismo nombre y mismo ámbito)
y además, por higiene, si usa una función prohibida en este proyecto
(OFFSET / INDIRECT), que es la otra forma de que un nombre se rompa solo.

Uso:  python verificar_nombres.py libro1.xlsx [libro2.xlsx ...]
"""
import re
import sys
import zipfile

NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
PROHIBIDAS = ("OFFSET(", "INDIRECT(", "DESREF(", "INDIRECTO(")


def nombres_de(ruta):
    """[(nombre, ámbito, definición)] leídos del XML crudo del libro."""
    import xml.etree.ElementTree as ET
    with zipfile.ZipFile(ruta) as z:
        raiz = ET.fromstring(z.read("xl/workbook.xml"))
    fuera = []
    for dn in raiz.iter(f"{NS}definedName"):
        fuera.append((dn.get("name"), dn.get("localSheetId"), (dn.text or "")))
    return fuera


def revisar(ruta):
    fallos = []
    nombres = nombres_de(ruta)
    vistos = {}
    for nombre, ambito, definicion in nombres:
        clave = (nombre, ambito)
        if clave in vistos:
            fallos.append(f"DUPLICADO: {nombre} (ámbito {ambito})")
        vistos[clave] = definicion
        if definicion.startswith("="):
            fallos.append(f"EMPIEZA POR '=': {nombre} → {definicion[:70]}")
        if not definicion.strip():
            fallos.append(f"VACÍO: {nombre}")
        if "#REF!" in definicion:
            fallos.append(f"#REF!: {nombre} → {definicion[:70]}")
        may = definicion.upper()
        for fn in PROHIBIDAS:
            if fn in may:
                fallos.append(f"FUNCIÓN PROHIBIDA {fn[:-1]}: {nombre} → {definicion[:70]}")
    # Los nombres a los que apunta una validación de lista deben existir: si
    # Excel borrase uno, el desplegable quedaría mudo. Se comprueba el enlace.
    declarados = {n for n, _a, _d in nombres}
    usados = set()
    with zipfile.ZipFile(ruta) as z:
        for item in z.namelist():
            if not re.match(r"xl/worksheets/sheet\d+\.xml$", item):
                continue
            txt = z.read(item).decode("utf-8", "replace")
            for m in re.finditer(r"<formula1>([^<]*)</formula1>", txt):
                f1 = m.group(1).strip()
                if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_.]*", f1):
                    usados.add(f1)
    for u in sorted(usados - declarados):
        fallos.append(f"VALIDACIÓN HUÉRFANA: la lista apunta a «{u}», que no existe")
    return nombres, sorted(usados), fallos


def main(rutas):
    total_fallos = 0
    for ruta in rutas:
        nombres, usados, fallos = revisar(ruta)
        marca = "OK " if not fallos else "✗✗ "
        print(f"{marca}{ruta.split('/')[-1]:38s} definedName {len(nombres):3d} · "
              f"usados por validaciones {len(usados):2d} · fallos {len(fallos)}")
        for f in fallos:
            print(f"      ✗ {f}")
        total_fallos += len(fallos)
    print(f"\nTOTAL DE FALLOS ESTRUCTURALES: {total_fallos}")
    return 1 if total_fallos else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
