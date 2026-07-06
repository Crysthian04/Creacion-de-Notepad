# Comparativo de Proveedores — PSN-LAC-LAC-F-009

Herramienta para generar el formato "Selección de Proveedores LAC" de Bimbo
(PSN-LAC-LAC-F-009) a partir de un archivo de datos simple, sin tocar código
cada vez.

Genera:
- **PDF** con el mismo diseño del formato original (logo, colores, bordes).
- **Excel (.xlsx)** editable con la misma información y estructura, por si
  necesitas ajustar algo a mano.

> Nota: como plantilla de referencia se usó el PDF `COMP_DISCOS_REBANADORES_DE_LA_UBE.pdf`
> (no había un .xlsx original). El PDF que genera esta herramienta reproduce
> visualmente ese formato con las coordenadas, colores y bordes medidos sobre
> el original. El Excel es una versión editable equivalente (misma estructura
> y colores), no una copia de un libro de Excel preexistente.

## 1. Instalación (una sola vez)

Necesitas Python 3.9 o superior instalado. Luego, desde esta carpeta
(`comparativo-proveedores`), instala las librerías necesarias:

```bash
pip install -r requirements.txt
```

## 2. Cómo usarlo cada vez que tengas un comparativo nuevo

### Paso 1 — Copia el archivo de ejemplo

Toma el archivo `ejemplos/datos_req_2026_55837.json` como base (ya tiene
cargado el ejemplo real de "Discos Rebanadores de la UBE"). Cópialo con un
nombre nuevo, por ejemplo `datos_req_2026_60000.json`, y edítalo con los
datos de tu nuevo requerimiento. Puedes usar cualquier editor de texto (Bloc
de notas, VS Code, etc.).

### Paso 2 — Completa los campos del archivo

```json
{
  "fecha": "01/07/2026",
  "bien_o_servicio": "BIEN",
  "negociador": "ALDAIR GÓMEZ/CRISTIAN BATISTA",
  "req_numero": "REQ-2026-55837",
  "req_descripcion": "DISCOS REBANADORES DE LA UBE",

  "proveedores": [
    {
      "nombre": "BOX TO BOX",
      "legalmente_constituido": "SI",
      "legalmente_constituido_ponderado": 20,
      "cumplimiento_especificaciones": "SI",
      "cumplimiento_especificaciones_ponderado": 25,
      "precio": 6998.90,
      "precio_ponderado": 10,
      "terminos_pago": "60 días",
      "terminos_pago_ponderado": 20,
      "tiempo_respuesta": "15 días",
      "tiempo_respuesta_ponderado": 5
    }
  ],

  "proveedor_sugerido": "BOX TO BOX",
  "proveedor_autorizado": "BOX TO BOX",
  "observaciones": "Texto de justificación de la decisión..."
}
```

Notas importantes:

- **`proveedores`** puede tener entre **1 y 3** elementos (nunca más). Si
  agregas o quitas proveedores, la tabla del PDF/Excel ajusta sola el ancho
  de las columnas, sin dejar espacios vacíos.
- **`bien_o_servicio`** debe ser `"BIEN"` o `"SERVICIO"`.
- **`legalmente_constituido`** y **`cumplimiento_especificaciones`** deben
  ser `"SI"` o `"NO"`.
- Los pesos por criterio (Legalmente Constituido 20%, Cumplimiento de
  Especificaciones 25%, Precio 20%, Términos de pago 20%, Tiempo de
  respuesta 15%) son **fijos** y los pone la herramienta automáticamente; no
  hace falta indicarlos.
- **Los campos `..._ponderado` (el "% Ponderado" de cada criterio, incluido
  Precio) los defines tú a mano**, según tu propio criterio de evaluación.
  La herramienta **no inventa ninguna fórmula de puntaje**: solo coloca en
  el PDF/Excel el número que tú escribiste en el JSON.
- La fila de totales (100% de peso) se calcula sola sumando los
  `..._ponderado` de cada proveedor. Si la suma de un proveedor no da
  exactamente el 100% del peso total, la herramienta te avisa con una
  **advertencia en la consola** (no bloquea la generación del archivo — a
  veces es intencional, como en el ejemplo real donde los totales dan
  80/90/85%).

### Paso 3 — Ejecuta la herramienta

Desde la carpeta `comparativo-proveedores`, corre:

```bash
python llenar_comparativo.py datos_req_2026_60000.json
```

Esto genera, en la misma carpeta:

- `Comparativo_REQ-2026-60000.pdf`
- `Comparativo_REQ-2026-60000.xlsx`

(el nombre lo arma automáticamente a partir del campo `req_numero`).

Si quieres guardar los archivos en otra carpeta:

```bash
python llenar_comparativo.py datos_req_2026_60000.json -o C:\ruta\donde\guardar
```

Si solo quieres el PDF (sin el Excel):

```bash
python llenar_comparativo.py datos_req_2026_60000.json --solo-pdf
```

### Paso 4 — Revisa los avisos en pantalla

Si falta algún campo obligatorio o hay más de 3 proveedores, la herramienta
se detiene y te dice exactamente qué falta corregir, por ejemplo:

```
ERROR: Falta el campo 'precio_ponderado' en el proveedor 'LO TRADING'.
```

Si los datos son válidos pero algún proveedor no suma 100% de %Ponderado,
verás una advertencia (no impide generar el archivo):

```
ADVERTENCIA: El proveedor 'LO TRADING' suma 90% de %Ponderado, pero el peso
total de los criterios es 100%. Revisa los valores manuales de %Ponderado.
```

## 3. Archivos YAML (opcional)

Si prefieres editar en YAML en vez de JSON, guarda el archivo con extensión
`.yaml` y usa la misma estructura (mismos nombres de campo). Necesitas
además `pip install pyyaml` (ya incluido en `requirements.txt`).

## 4. Estructura de la carpeta

```
comparativo-proveedores/
  llenar_comparativo.py         <- el script que ejecutas
  requirements.txt
  comparativo/
    layout.py                   <- coordenadas/colores medidos de la plantilla
    modelos.py                  <- carga y validación de los datos de entrada
    pdf_generator.py            <- dibuja el PDF final
    excel_generator.py          <- arma el Excel editable
    assets/logo_bimbo.png
  ejemplos/
    datos_req_2026_55837.json   <- ejemplo ya completado (Discos Rebanadores de la UBE)
```

No necesitas tocar nada dentro de `comparativo/`: solo crea/edita archivos
JSON en la carpeta donde quieras (o dentro de `ejemplos/`) y ejecuta el
script apuntando a ese archivo.
