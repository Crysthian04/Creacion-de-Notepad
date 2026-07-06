"""Genera el PDF final del comparativo, replicando el layout de la plantilla
PSN-LAC-LAC-F-009 medido en comparativo/layout.py."""

from __future__ import annotations

import os

from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

from . import layout as L
from .modelos import Comparativo


def _centrar_texto(c, texto, x0, x1, y_top, fuente=L.FUENTE, tam=L.TAM_TABLA):
    c.setFont(fuente, tam)
    c.setFillColor(L.NEGRO)
    ancho = c.stringWidth(texto, fuente, tam)
    x = x0 + (x1 - x0 - ancho) / 2
    c.drawString(x, L.y(y_top), texto)


def _dibujar_celda(c, x0, x1, y0_top, y1_top, relleno=None, borde=L.NEGRO,
                    ancho_borde=0.6):
    x0, x1 = sorted((x0, x1))
    y_bot = L.y(y1_top)
    y_top = L.y(y0_top)
    if relleno is not None:
        c.setFillColor(relleno)
        c.rect(x0, y_bot, x1 - x0, y_top - y_bot, stroke=0, fill=1)
    if borde is not None:
        c.setStrokeColor(borde)
        c.setLineWidth(ancho_borde)
        c.rect(x0, y_bot, x1 - x0, y_top - y_bot, stroke=1, fill=0)


def _envolver_lineas(c, texto, x0, x1, fuente, tam):
    palabras = texto.split()
    lineas = []
    actual = ""
    for palabra in palabras:
        prueba = (actual + " " + palabra).strip()
        if c.stringWidth(prueba, fuente, tam) <= (x1 - x0):
            actual = prueba
        else:
            if actual:
                lineas.append(actual)
            actual = palabra
    if actual:
        lineas.append(actual)
    return lineas


def _texto_multilinea_centrado_v(c, texto, x0, x1, y0_top, y1_top, fuente, tam_inicial):
    """Centra un texto (word-wrap) vertical y horizontalmente dentro de una celda,
    reduciendo el tamaño de fuente si hace falta más de 2 líneas para que quepa."""
    tam = tam_inicial
    interlineado = tam + 1.8
    lineas = _envolver_lineas(c, texto, x0, x1, fuente, tam)
    alto_disponible = y1_top - y0_top
    while len(lineas) * interlineado > alto_disponible and tam > 5.5:
        tam -= 0.5
        interlineado = tam + 1.8
        lineas = _envolver_lineas(c, texto, x0, x1, fuente, tam)

    c.setFont(fuente, tam)
    c.setFillColor(L.NEGRO)
    alto_total = len(lineas) * interlineado
    y = (y0_top + y1_top) / 2 - alto_total / 2 + tam
    for linea in lineas:
        ancho = c.stringWidth(linea, fuente, tam)
        x = x0 + (x1 - x0 - ancho) / 2
        c.drawString(x, L.y(y), linea)
        y += interlineado
    return lineas


def generar_pdf(comparativo: Comparativo, ruta_salida: str) -> None:
    c = canvas.Canvas(ruta_salida, pagesize=(L.PAGE_W, L.PAGE_H))

    n = len(comparativo.proveedores)
    ancho_prov = (L.PROV_AREA_RIGHT - L.PROV_AREA_LEFT) / n
    prov_bounds = [
        (L.PROV_AREA_LEFT + i * ancho_prov, L.PROV_AREA_LEFT + (i + 1) * ancho_prov)
        for i in range(n)
    ]

    # ------------------------------------------------------------------
    # Fondo general muy claro para toda la hoja de contenido (igual al original)
    # ------------------------------------------------------------------
    margen_top = 90.0
    margen_bottom = 495.0
    c.setFillColor(L.GRIS_FONDO)
    c.rect(40, L.y(margen_bottom), L.PAGE_W - 80, margen_bottom - margen_top,
           stroke=0, fill=1)
    c.setFillColor(L.NEGRO)

    # ------------------------------------------------------------------
    # Bloque superior: logo, título, código
    # ------------------------------------------------------------------
    _dibujar_celda(c, L.LOGO_LEFT, L.CODIGO_RIGHT, L.TOP_BOX_TOP, L.TOP_BOX_BOTTOM,
                   relleno=L.BLANCO)
    _dibujar_celda(c, L.LOGO_LEFT, L.TITULO_LEFT, L.TOP_BOX_TOP, L.TOP_BOX_BOTTOM)
    _dibujar_celda(c, L.TITULO_LEFT, L.CODIGO_LEFT, L.TOP_BOX_TOP, L.TOP_BOX_BOTTOM)
    _dibujar_celda(c, L.CODIGO_LEFT, L.CODIGO_RIGHT, L.TOP_BOX_TOP, L.CODIGO_MID_Y)
    _dibujar_celda(c, L.CODIGO_LEFT, L.CODIGO_MID_X, L.CODIGO_MID_Y, L.TOP_BOX_BOTTOM)
    _dibujar_celda(c, L.CODIGO_MID_X, L.CODIGO_RIGHT, L.CODIGO_MID_Y, L.TOP_BOX_BOTTOM)

    # Logo
    try:
        img = ImageReader(L.LOGO_PATH)
        iw, ih = img.getSize()
        max_w = L.TITULO_LEFT - L.LOGO_LEFT - 12
        max_h = L.TOP_BOX_BOTTOM - L.TOP_BOX_TOP - 12
        escala = min(max_w / iw, max_h / ih)
        w, h = iw * escala, ih * escala
        x = L.LOGO_LEFT + (L.TITULO_LEFT - L.LOGO_LEFT - w) / 2
        y_top_img = L.TOP_BOX_TOP + (L.TOP_BOX_BOTTOM - L.TOP_BOX_TOP - h) / 2
        c.drawImage(img, x, L.y(y_top_img + h), w, h, mask="auto")
    except Exception:
        pass

    # Título
    c.setFillColor(L.NEGRO)
    _centrar_texto(c, "SELECCIÓN DE PROVEEDORES LAC", L.TITULO_LEFT, L.CODIGO_LEFT,
                   137, fuente=L.FUENTE_TITULO, tam=L.TAM_TITULO)

    # Código / versión / página
    _centrar_texto(c, "CÓDIGO", L.CODIGO_LEFT, L.CODIGO_RIGHT, 122,
                    fuente=L.FUENTE_BOLD, tam=L.TAM_CODIGO)
    _centrar_texto(c, "PSN-LAC-LAC-F-009", L.CODIGO_LEFT, L.CODIGO_RIGHT, 133,
                    fuente=L.FUENTE_BOLD, tam=L.TAM_CODIGO)
    _centrar_texto(c, "VERSION", L.CODIGO_LEFT, L.CODIGO_MID_X, 143,
                    fuente=L.FUENTE_BOLD, tam=L.TAM_CODIGO)
    _centrar_texto(c, "3", L.CODIGO_LEFT, L.CODIGO_MID_X, 157,
                    fuente=L.FUENTE, tam=L.TAM_CODIGO)
    _centrar_texto(c, "PAGINA", L.CODIGO_MID_X, L.CODIGO_RIGHT, 143,
                    fuente=L.FUENTE_BOLD, tam=L.TAM_CODIGO)
    _centrar_texto(c, "1 de 1", L.CODIGO_MID_X, L.CODIGO_RIGHT, 157,
                    fuente=L.FUENTE, tam=L.TAM_CODIGO)

    # ------------------------------------------------------------------
    # Fecha / Bien-Servicio / Negociador
    # ------------------------------------------------------------------
    campos = [
        ("Fecha", comparativo.fecha, L.FECHA_ROW),
        ("Bien/Servicio", comparativo.bien_o_servicio, L.BIEN_ROW),
        ("Negociador/ Comprador Funcional", comparativo.negociador, L.NEGOCIADOR_ROW),
    ]
    for etiqueta, valor, (y0, y1) in campos:
        _dibujar_celda(c, L.CAMPO_LABEL_LEFT, L.CAMPO_VALOR_RIGHT, y0, y1, borde=None)
        c.setFillColor(L.NEGRO)
        c.setFont(L.FUENTE, L.TAM_CAMPO)
        c.drawString(L.CAMPO_LABEL_LEFT + 2, L.y((y0 + y1) / 2 + 3), etiqueta)
        c.line(L.CAMPO_LABEL_RIGHT, L.y(y0), L.CAMPO_LABEL_RIGHT, L.y(y1))
        _dibujar_celda(c, L.CAMPO_VALOR_LEFT, L.CAMPO_VALOR_RIGHT, y0, y1,
                       relleno=L.BLANCO)
        _centrar_texto(c, valor, L.CAMPO_VALOR_LEFT, L.CAMPO_VALOR_RIGHT,
                        (y0 + y1) / 2 + 3, tam=L.TAM_CAMPO)

    # ------------------------------------------------------------------
    # Encabezado de la tabla (CRITERIOS / Peso / Proveedores)
    # ------------------------------------------------------------------
    _dibujar_celda(c, L.TABLA_LEFT, L.CRITERIOS_RIGHT, L.HEADER_TOP, L.HEADER_BOTTOM,
                   relleno=L.GRIS_ENCABEZADO)
    _centrar_texto(c, "CRITERIOS", L.TABLA_LEFT, L.CRITERIOS_RIGHT,
                    (L.HEADER_TOP + L.HEADER_BOTTOM) / 2 + 3,
                    fuente=L.FUENTE_BOLD, tam=L.TAM_TABLA_BOLD)

    _dibujar_celda(c, L.CRITERIOS_RIGHT, L.PESO_RIGHT, L.HEADER_TOP, L.HEADER_BOTTOM,
                   relleno=L.GRIS_ENCABEZADO)
    _centrar_texto(c, "Peso", L.CRITERIOS_RIGHT, L.PESO_RIGHT,
                    (L.HEADER_TOP + L.HEADER_BOTTOM) / 2 + 3,
                    fuente=L.FUENTE_BOLD, tam=L.TAM_TABLA_BOLD)

    for (x0, x1), prov in zip(prov_bounds, comparativo.proveedores):
        _dibujar_celda(c, x0, x1, L.HEADER_TOP, L.HEADER_BOTTOM, relleno=L.GRIS_ENCABEZADO)
        _texto_multilinea_centrado_v(c, prov.nombre.upper(), x0 + 2, x1 - 2,
                                      L.HEADER_TOP, L.HEADER_BOTTOM,
                                      L.FUENTE_BOLD, L.TAM_TABLA_BOLD)

    # Subencabezado Cot. / % Ponderado
    for x0, x1 in prov_bounds:
        xm = (x0 + x1) / 2
        _dibujar_celda(c, x0, xm, L.HEADER_BOTTOM, L.SUBHEADER_BOTTOM)
        _centrar_texto(c, "Cot.", x0, xm, L.SUBHEADER_BOTTOM - 3, tam=L.TAM_TABLA)
        _dibujar_celda(c, xm, x1, L.HEADER_BOTTOM, L.SUBHEADER_BOTTOM)
        _centrar_texto(c, "% Ponderado", xm, x1, L.SUBHEADER_BOTTOM - 3, tam=L.TAM_TABLA)
    _dibujar_celda(c, L.TABLA_LEFT, L.PESO_RIGHT, L.HEADER_BOTTOM, L.SUBHEADER_BOTTOM)

    # ------------------------------------------------------------------
    # Filas de criterios
    # ------------------------------------------------------------------
    valores_crudos = {
        "legalmente_constituido": lambda p: p.legalmente_constituido,
        "cumplimiento_especificaciones": lambda p: p.cumplimiento_especificaciones,
        "precio": lambda p: f"$ {p.precio:,.2f}",
        "terminos_pago": lambda p: p.terminos_pago,
        "tiempo_respuesta": lambda p: p.tiempo_respuesta,
    }
    ponderados = {
        "legalmente_constituido": lambda p: p.legalmente_constituido_ponderado,
        "cumplimiento_especificaciones": lambda p: p.cumplimiento_especificaciones_ponderado,
        "precio": lambda p: p.precio_ponderado,
        "terminos_pago": lambda p: p.terminos_pago_ponderado,
        "tiempo_respuesta": lambda p: p.tiempo_respuesta_ponderado,
    }

    y0 = L.CRITERIA_ROW_TOP
    for clave, etiqueta, peso in L.CRITERIOS:
        y1 = y0 + L.CRITERIA_ROW_HEIGHT
        yc = (y0 + y1) / 2 + 3

        _dibujar_celda(c, L.TABLA_LEFT, L.CRITERIOS_RIGHT, y0, y1, relleno=L.BLANCO)
        c.setFont(L.FUENTE, L.TAM_TABLA)
        c.setFillColor(L.NEGRO)
        c.drawString(L.TABLA_LEFT + 2, L.y(yc), etiqueta)

        _dibujar_celda(c, L.CRITERIOS_RIGHT, L.PESO_RIGHT, y0, y1, relleno=L.BLANCO)
        _centrar_texto(c, f"{peso:g}%", L.CRITERIOS_RIGHT, L.PESO_RIGHT, yc,
                        fuente=L.FUENTE_BOLD, tam=L.TAM_TABLA_BOLD)

        for (x0, x1), prov in zip(prov_bounds, comparativo.proveedores):
            xm = (x0 + x1) / 2
            _dibujar_celda(c, x0, xm, y0, y1, relleno=L.BLANCO)
            _centrar_texto(c, str(valores_crudos[clave](prov)), x0, xm, yc, tam=L.TAM_TABLA)
            _dibujar_celda(c, xm, x1, y0, y1, relleno=L.BLANCO)
            _centrar_texto(c, f"{ponderados[clave](prov):g}%", xm, x1, yc,
                            fuente=L.FUENTE_BOLD, tam=L.TAM_TABLA_BOLD)

        y0 = y1

    # ------------------------------------------------------------------
    # Fila REQ + totales
    # ------------------------------------------------------------------
    _dibujar_celda(c, L.TABLA_LEFT, L.CRITERIOS_RIGHT, L.REQ_ROW_TOP, L.REQ_ROW_BOTTOM,
                   relleno=L.BLANCO)
    _centrar_texto(
        c,
        f"{comparativo.req_numero} {comparativo.req_descripcion}",
        L.TABLA_LEFT, L.CRITERIOS_RIGHT,
        (L.REQ_ROW_TOP + L.REQ_ROW_BOTTOM) / 2 + 3,
        tam=L.TAM_TABLA,
    )

    yc_total = (L.REQ_ROW_TOP + L.REQ_ROW_BOTTOM) / 2 + 3
    _dibujar_celda(c, L.CRITERIOS_RIGHT, L.PESO_RIGHT, L.REQ_ROW_TOP, L.REQ_ROW_BOTTOM,
                   relleno=L.BLANCO)
    _centrar_texto(c, f"{L.PESO_TOTAL:g}%", L.CRITERIOS_RIGHT, L.PESO_RIGHT, yc_total,
                    fuente=L.FUENTE_BOLD, tam=L.TAM_TABLA_BOLD)

    for (x0, x1), prov in zip(prov_bounds, comparativo.proveedores):
        xm = (x0 + x1) / 2
        _dibujar_celda(c, x0, xm, L.REQ_ROW_TOP, L.REQ_ROW_BOTTOM, relleno=L.BLANCO)
        _dibujar_celda(c, xm, x1, L.REQ_ROW_TOP, L.REQ_ROW_BOTTOM, relleno=L.BLANCO)
        _centrar_texto(c, f"{prov.total_ponderado():g}%", xm, x1, yc_total,
                        fuente=L.FUENTE_BOLD, tam=L.TAM_TABLA_BOLD)

    # ------------------------------------------------------------------
    # Proveedor sugerido / autorizado / firma
    # ------------------------------------------------------------------
    for etiqueta, valor, (y0, y1) in [
        ("Proveedor Sugerido", comparativo.proveedor_sugerido, L.SUGERIDO_ROW),
        ("Proveedor Autorizado", comparativo.proveedor_autorizado, L.AUTORIZADO_ROW),
    ]:
        _dibujar_celda(c, L.CAMPO_LABEL_LEFT, L.CRITERIOS_RIGHT, y0, y1, borde=None)
        c.setFillColor(L.NEGRO)
        c.setFont(L.FUENTE, L.TAM_CAMPO)
        c.drawString(L.CAMPO_LABEL_LEFT + 2, L.y((y0 + y1) / 2 + 3), etiqueta)
        c.line(L.CAMPO_LABEL_RIGHT, L.y(y0), L.CAMPO_LABEL_RIGHT, L.y(y1))
        c.drawString(L.CAMPO_VALOR_LEFT + 2, L.y((y0 + y1) / 2 + 3), valor)

    c.setStrokeColor(L.NEGRO)
    c.setLineWidth(0.6)
    c.line(L.FIRMA_LEFT, L.y(L.FIRMA_LINE_Y), L.FIRMA_RIGHT, L.y(L.FIRMA_LINE_Y))
    c.setFont(L.FUENTE, L.TAM_CAMPO)
    c.drawString(L.FIRMA_LEFT + 2, L.y(L.FIRMA_LINE_Y + 7), "Firma del Jefe Inmediato")

    # ------------------------------------------------------------------
    # Observaciones relevantes
    # ------------------------------------------------------------------
    _dibujar_celda(c, L.OBS_LEFT, L.OBS_RIGHT, L.OBS_TOP, L.OBS_BOTTOM,
                   relleno=L.BLANCO, ancho_borde=1.0)
    c.setFillColor(L.NEGRO)
    c.setFont(L.FUENTE_BOLD, L.TAM_OBS_TITULO)
    c.drawString(L.OBS_LEFT + 3, L.y(L.OBS_TOP + 10), "Observaciones Relevantes:")

    palabras = comparativo.observaciones.split()
    fuente, tam = L.FUENTE, L.TAM_OBS_TEXTO
    max_ancho = L.OBS_RIGHT - L.OBS_LEFT - 8
    lineas, actual = [], ""
    c.setFont(fuente, tam)
    for palabra in palabras:
        prueba = (actual + " " + palabra).strip()
        if c.stringWidth(prueba, fuente, tam) <= max_ancho:
            actual = prueba
        else:
            if actual:
                lineas.append(actual)
            actual = palabra
    if actual:
        lineas.append(actual)

    y_obs = L.OBS_TOP + 21
    for linea in lineas:
        ancho = c.stringWidth(linea, fuente, tam)
        x = L.OBS_LEFT + (L.OBS_RIGHT - L.OBS_LEFT - ancho) / 2
        c.drawString(x, L.y(y_obs), linea)
        y_obs += 9.3
        if y_obs > L.OBS_BOTTOM - 4:
            break

    c.showPage()
    c.save()
