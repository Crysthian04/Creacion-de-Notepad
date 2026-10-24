# Módulo 14 — Digitalización, BIM y Gestión Inteligente de Instalaciones (MEP)
**Estado: INFORME CERRADO (24/10/2026).** La Prof. Doris de León confirmó que REFRESH S.A. es válido como "proyecto de la carrera" (22/10). Cristian revisó y aprobó el Word sin ajustes (24/10). Archivo: `M14_Digitalizacion_BIM_MEP_BORRADOR.docx` (13 págs.: portada + ~10 de contenido + referencias). Falta solo el nombre final del archivo para el compendio (`M14_Digitalizacion_BIM_Gestion_MEP`).
Asignatura: Mantenimiento de Sistemas de Refrigeración y Aire Acondicionado (0251) · Grupo A · Entrega 28 oct. 2026 (compendio) · Presentación conjunta de labs en 1–2 semanas.
Título del informe: **Digitalización, BIM y Gestión Inteligente de Instalaciones (MEP)** — los títulos de los módulos no se cambian.

## Decisiones tomadas
- Proyecto para la propuesta y la instalación tipo de la Figura 3: **REFRESH S.A.** (planta ficticia diseñada en Selección de Equipos y Trazado de Planta, 2026). Se declara como "proyecto académico de la carrera", no como planta real. **Aprobado por la profesora el 22/10/2026.**
- REFRESH no tiene climatización diseñada: la propuesta es conceptual (LOD, información y puntos de monitoreo). **No se inventan capacidades** (toneladas, kW).
- Sistema de climatización: **VRF** para los Edificios D (laboratorio de calidad, comedor) y E (recepción, oficinas, sala de juntas), con unidad separada de aire exterior. La sala eléctrica (Edificio C, ATEX) se incluye solo como punto de monitoreo de temperatura.
- Medición de energía: el texto propone un **medidor en los tableros de D y E** (el PDF de REFRESH no trae medidores en esos tableros; la potencia del VRF es calculada).
- Integración: los equipos de REFRESH se especificaron con Profibus/Profinet/EtherNet-IP; la pasarela BACnet → SCADA queda como condición por confirmar.
- Datos de REFRESH: el PDF del proyecto final es la versión oficial (en el simulador, S-3 aparece por error como sala eléctrica; en el PDF es agua desmineralizada).
- Daikin se cita como **(2019)** por decisión de Cristian (código "DG_DCM014A51_02-19" visto solo en un resumen web; la ficha "PF-iTMSERV 02-25" es otro documento).
- Para evitar autoplagio con la Investigación 3: no se usan Hosamo et al. (2022), Shaban et al. (2025) ni el caso del Edificio 2 de la UTP.
- Reglas de redacción: cada párrafo lleva su cita APA entre paréntesis; no se usa la palabra "según" en ningún sentido; las cifras solo salen de fuentes leídas completas; las figuras solo si la licencia lo permite, con la fuente debajo.

## Fuentes verificadas contra el PDF original (8 + datos de REFRESH)
| Fuente | Qué aporta (página) | Figuras |
|---|---|---|
| BIMForum (2024), Parte I, trad. Vera y Santacruz | Definiciones LOD 100–400 (pp. 12–13); LOD 500 = as-built verificado en campo, no superior al 400 (p. 13); el LOD es solo geometría y los datos de mantenimiento van por COBie/IDS (p. 11); "no existe un modelo LOD ###" (p. 195); VRF → D3030.10 (p. 127), D3050.50 (p. 130), D3060 (p. 133), D8010 (p. 161) — esta asignación es nuestra | CC BY-NC-ND 4.0: se reproduce sin modificar (Figura 1 = p. 128) |
| Khanzode, Fischer y Reed (2008), ITcon 13 | El contratista de HVAC lideró la coordinación (p. 328); nivel de detalle decidido entre todos (p. 329); 2 de 233 RFI por conflictos en obra, de sistemas no modelados; 0 órdenes de cambio (p. 336); modelo as-built usado para administrar el edificio (p. 337); USD 9 M y 6 meses = BIM **más** entrega colaborativa (Fig. 10, p. 337); USD 500 mil devueltos por el contratista mecánico (p. 338); retrabajo de 40/25,000 h (p. 339); lecciones: acabados y mobiliario sin modelar, soportes misceláneos (pp. 339–340). NO usar el rango de 200–300 RFI ni el 20–30 % del resumen | No (licencia de 2008 no confirmada) |
| Gallaher, O'Connor, Dettbarn y Gilday (2004), NIST GCR 04-867 | USD 15,824 M al año (2002); propietarios y operadores USD 10,648 M (~2/3) (p. ES-6); fase de operación y mantenimiento USD 9,093.3 M (Tabla ES-2, p. ES-7) | — |
| Lu, Xie, Parlikad y Schooling (2020), Autom. Constr. 118 | Caso real: gemelo digital de 2 bombas de agua helada, edificio IfM (Cambridge); Revit → IFC4 extendido; tabla de correspondencia BIM–BMS–sensores; CUSUM con 2 falsas alarmas y ~1 semana de retraso vs. el método bayesiano. NO usar el "98 %" de la introducción | CC BY-NC-ND (manuscrito en el repositorio de Cambridge) |
| Hu, Ou, Liu, Ni y Chang (2026), Build. Environ. 288 | Marco de 5 capas (Sección 6.1, Fig. 8); IFC/COBie/JSON; datos aislados y pocos estudios más allá de prototipos. Cita a Hosamo: no tomarlo | CC BY (Figura 2 = Fig. 8) |
| Soto y Manríquez (2023), CAF | Panamá solo tiene iniciativa privada (BIM Fórum Panamá, con la cámara de la construcción) (p. 17); no está entre los 9 países con iniciativa pública (p. 18); datos de ene–may 2022 | No (todos los derechos reservados) |
| Thornton y Wagner (2012), PNNL-21548 | Componentes y aire exterior por unidad separada (p. 4); autodiagnóstico y puntos de monitoreo (p. 5); mantenimiento de cada fan coil: filtros y condensado (p. 7); ~doble de refrigerante (p. 8); evaluación basada en literatura (p. 11); fugas, ASHRAE 15, productos no intercambiables (p. 12); condensado (p. 18); BACnet/LonWorks (pp. 19, 23); mantenimiento regular (p. 24); "Finding leaks is difficult" (p. 25). NO usar cifras de ahorro | No (Figs. 1 y 3 con permiso de terceros) |
| Daikin Comfort Technologies North America (2019), iTM BACnet Server Gateway Design Guide (DCM014A51) | Composición del sistema y BMS (p. 8); paro forzado por emergencia (p. 24); puntos de la unidad interior (pp. 25–26); puntos de la unidad exterior, potencia **calculada** (pp. 30–31); solo se generan los puntos que existen y los habilitados (pp. 25, 33) | No |

Descartadas: Salzano et al. (2025), Ma et al. (2025), Lee et al. (2025), Věrný y Žák (2025), LG, Intesis, Mitsubishi y GSA GPG-006.

## Estructura del informe
Introducción · Desarrollo (La metodología BIM aplicada a sistemas HVAC-R · Niveles de desarrollo (LOD) con Figura 1 y Tabla 1 · Ventajas cuantificadas con Tabla 2 · Del modelo BIM al gemelo digital: caso real en climatización con Figura 2 · Sistema MEP integrado para la planta REFRESH S.A. con Figura 3 · Propuesta de aplicación al proyecto REFRESH S.A.) · Conclusiones (4) · Recomendaciones (2) · Referencias (sin salto de página, como en la plantilla).
Formato: Arial 12, interlineado 1.5, márgenes de 2.54 cm, justificado con sangría de 1.27 cm, número arriba a la derecha. Tablas, notas y pies de figura en Arial 10 sencillo (aprobado así por Cristian).

## Figura 3 del informe (base de la escena MEP del modelo 3D)
Cuatro niveles: equipos de campo (Edificios D y E: unidades interiores en recepción, oficinas, sala de juntas, laboratorio QC y comedor; unidad exterior VRF; unidad de aire exterior; tableros de D y E con medidor de energía propuesto; Edificio C, sala eléctrica/UPS) → automatización del VRF (controlador central y pasarela BACnet/IP) → supervisión (SCADA central de REFRESH) → gestión de la información (modelo BIM as-built LOD 500 + COBie, CMMS y tablero/gemelo digital).
Puntos: M1 temperatura de sala · M2 alarma con código de error · M3 aviso de filtro · M4 presiones y velocidad del compresor · M5 energía medida en el tablero · M6 temperatura de la sala eléctrica · C1 consigna y horario por zona · C2 encendido y apagado remoto · C3 paro forzado por señal de emergencia · C4 marcha y paro de la unidad de aire exterior.

## Referencias (APA 7)
- Batista, C., Jiménez, M., Camarena, A., y Stephenson, R. (2026). *REFRESH S.A.: Diseño de una planta de detergente en polvo* [Proyecto final no publicado]. Universidad Tecnológica de Panamá.
- BIMForum. (2024). *Especificación del nivel de desarrollo (LOD), parte I* (C. Vera y H. Santacruz, Trads.). https://bimforum.org/lod
- Daikin Comfort Technologies North America. (2019). *Intelligent Touch Manager (iTM) BACnet server gateway: Design guide* (DCM014A51). https://daikincomfort.com/docs/default-source/itm-bacnet-server-gateway-option/eg-itm_bacnetgatewayguide_v2-0.pdf
- Gallaher, M. P., O'Connor, A. C., Dettbarn, J. L., Jr., y Gilday, L. T. (2004). *Cost analysis of inadequate interoperability in the U.S. capital facilities industry* (NIST GCR 04-867). National Institute of Standards and Technology. https://doi.org/10.6028/NIST.GCR.04-867
- Hu, W., Ou, Y., Liu, H., Ni, P., y Chang, C. (2026). Integrating digital twin technologies for maintenance 4.0 in the building industry: A review and conceptual framework. *Building and Environment, 288*, Artículo 113997. https://doi.org/10.1016/j.buildenv.2025.113997
- Khanzode, A., Fischer, M., y Reed, D. (2008). Benefits and lessons learned of implementing building virtual design and construction (VDC) technologies for coordination of mechanical, electrical, and plumbing (MEP) systems on a large healthcare project. *Journal of Information Technology in Construction, 13*, 324–342. https://www.itcon.org/2008/22
- Lu, Q., Xie, X., Parlikad, A. K., y Schooling, J. M. (2020). Digital twin-enabled anomaly detection for built asset monitoring in operation and maintenance. *Automation in Construction, 118*, Artículo 103277. https://doi.org/10.1016/j.autcon.2020.103277
- Soto, C., y Manríquez, S. (2023). *Panorama general del avance de BIM en América Latina y el Caribe*. CAF.
- Thornton, B., y Wagner, A. (2012). *Variable refrigerant flow systems* (PNNL-21548). Pacific Northwest National Laboratory. https://www.pnnl.gov/main/publications/external/technical_reports/PNNL-21548.pdf

## Pendientes
- Nombre final del archivo para el compendio: `M14_Digitalizacion_BIM_Gestion_MEP`.
- Presentación conjunta de labs (fecha por confirmar) y modelo 3D M6 + M14 (ver `Plan_Modelo3D_Labs_M6_M14.md`).
