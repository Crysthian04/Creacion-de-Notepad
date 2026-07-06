"""
Coordenadas y estilos medidos directamente sobre la plantilla original
PSN-LAC-LAC-F-009 (PDF de referencia: COMP_DISCOS_REBANADORES_DE_LA_UBE.pdf).

Sistema de coordenadas: puntos PDF (72 pt = 1 in), origen abajo-izquierda
(convención de reportlab). PAGE_W / PAGE_H corresponden a Carta horizontal,
igual que el original (792 x 612 pt).
"""

from reportlab.lib.colors import Color

PAGE_W = 792.0
PAGE_H = 612.0

# ---------------------------------------------------------------------------
# Colores (medidos desde los rellenos del PDF original)
# ---------------------------------------------------------------------------
GRIS_FONDO = Color(0.949, 0.949, 0.949)   # fondo general de la hoja / celdas de etiqueta
GRIS_ENCABEZADO = Color(0.651, 0.651, 0.651)  # encabezado CRITERIOS / Peso / proveedores
NEGRO = Color(0, 0, 0)
BLANCO = Color(1, 1, 1)

# ---------------------------------------------------------------------------
# Fuentes (Calibri no está disponible como fuente base de reportlab; se usa
# Helvetica como sustituto visualmente equivalente sin problemas de licencia)
# ---------------------------------------------------------------------------
FUENTE = "Helvetica"
FUENTE_BOLD = "Helvetica-Bold"
FUENTE_TITULO = "Helvetica-Bold"

TAM_TITULO = 11
TAM_CODIGO = 7.2
TAM_CAMPO = 8
TAM_TABLA = 7.5
TAM_TABLA_BOLD = 7.5
TAM_OBS_TITULO = 8
TAM_OBS_TEXTO = 7.5

# ---------------------------------------------------------------------------
# Convención: todas las coordenadas Y se miden en el sistema "PDF top-down"
# (y crece hacia abajo, como en la extracción con PyMuPDF) y se convierten
# a reportlab con la función y().
# ---------------------------------------------------------------------------


def y(y_top: float) -> float:
    """Convierte una coordenada Y medida desde arriba (top-down) a reportlab (bottom-up)."""
    return PAGE_H - y_top


# ---------------------------------------------------------------------------
# Bloque superior: logo, título y caja de código
# ---------------------------------------------------------------------------
TOP_BOX_TOP = 105.1
TOP_BOX_BOTTOM = 163.6

LOGO_LEFT = 64.0
LOGO_RIGHT = 185.5

TITULO_LEFT = LOGO_RIGHT
TITULO_RIGHT = 638.3

CODIGO_LEFT = 638.3
CODIGO_RIGHT = 740.3
CODIGO_MID_Y = 136.3   # separa fila CÓDIGO (arriba) de fila VERSION/PAGINA (abajo)
CODIGO_MID_X = 689.3   # separa columna VERSION de columna PAGINA

# ---------------------------------------------------------------------------
# Filas Fecha / Bien-Servicio / Negociador
# ---------------------------------------------------------------------------
CAMPO_LABEL_LEFT = 64.0
CAMPO_LABEL_RIGHT = 188.0
CAMPO_VALOR_LEFT = 188.0
CAMPO_VALOR_RIGHT = 428.7

FECHA_ROW = (163.6, 181.6)
BIEN_ROW = (181.6, 197.4)
NEGOCIADOR_ROW = (197.4, 221.8)

# ---------------------------------------------------------------------------
# Tabla de criterios
# ---------------------------------------------------------------------------
TABLA_LEFT = 63.5
CRITERIOS_RIGHT = 379.0     # borde entre columna Criterios y columna Peso
PESO_RIGHT = 428.7          # borde entre columna Peso y área de proveedores
PROV_AREA_LEFT = 433.6
PROV_AREA_RIGHT = 740.3

HEADER_TOP = 221.8          # encabezado CRITERIOS / Peso / nombres de proveedor
HEADER_BOTTOM = 250.7
SUBHEADER_BOTTOM = 260.6    # fila con etiquetas "Cot." / "% Ponderado"

CRITERIA_ROW_TOP = 260.6
CRITERIA_ROW_HEIGHT = 14.8
N_CRITERIOS = 5             # Legal, Cumplimiento, Precio, Términos, Tiempo

REQ_ROW_TOP = CRITERIA_ROW_TOP + N_CRITERIOS * CRITERIA_ROW_HEIGHT   # 335.0
REQ_ROW_BOTTOM = 379.6

# Criterios fijos: (clave, etiqueta, peso %)
CRITERIOS = [
    ("legalmente_constituido", "Legalmente Constituido", 20),
    ("cumplimiento_especificaciones", "Cumplimiento de Especificaciones", 25),
    ("precio", "Precio", 20),
    ("terminos_pago", "Terminos de pago", 20),
    ("tiempo_respuesta", "Tiempo de respuesta", 15),
]
PESO_TOTAL = sum(c[2] for c in CRITERIOS)  # 100

# ---------------------------------------------------------------------------
# Proveedor sugerido / autorizado / firma
# ---------------------------------------------------------------------------
SUGERIDO_ROW = (REQ_ROW_BOTTOM, 390.0)
AUTORIZADO_ROW = (396.9, 407.2)
FIRMA_LINE_Y = 396.9
FIRMA_LEFT = 433.6
FIRMA_RIGHT = 688.0

# ---------------------------------------------------------------------------
# Observaciones
# ---------------------------------------------------------------------------
OBS_TOP = 413.1
OBS_BOTTOM = 484.3
OBS_LEFT = 64.4
OBS_RIGHT = 740.6

LOGO_PATH = __file__.replace("layout.py", "assets/logo_bimbo.png")
