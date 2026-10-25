# Plan — Modelo 3D de los laboratorios M6 + M14 (Cristian Batista, Grupo A)
Acordado el 23/10/2026 (última actualización 24/10, 16:40). Se construye en un chat exclusivo para el modelo. Este documento es el traspaso: leerlo completo antes de empezar.

## Contexto de uso
- La sustentación de los laboratorios es **una presentación conjunta del grupo, igual que la de las investigaciones**, en 1–2 semanas (fecha por confirmar). Cada integrante tiene ≈ 7–8 min para sus labs; Cristian cubre M6 y M14.
- **Decisión de Cristian (23/10): el modelo NO se recorta por tiempo.** Debe quedar completo, de modo que el 3D se sustente con los labs y los labs con el 3D.
- Para que quede completo sin depender del tiempo del día: **dos niveles de navegación** en cada parada:
  - **Ruta principal**: el recorrido que siempre se presenta (escenas y animaciones clave).
  - **Profundización**: tarjetas y vistas adicionales que se abren si hay tiempo o si hay preguntas. Saltarlas no debe dejar el modelo "incompleto".

## Principio central: trazabilidad en los dos sentidos
1. **Cada elemento del 3D remite a su informe**: toda escena, animación o tarjeta indica la sección, figura o tabla del laboratorio que la respalda (por ejemplo, "M14 · Figura 3" o "M6 · Tabla 1"), además del sello y la cita.
2. **Cada sección del informe tiene su escena o tarjeta en el 3D**: ninguna sección del Desarrollo queda sin representación.
3. El chat del modelo debe construir primero la **matriz de trazabilidad** (sección del informe ↔ elemento del 3D) a partir de los Word finales y validarla con Cristian antes de programar.

## Decisión y alcance
- **Solo M6 y M14** (los dos labs de Cristian). No se hace un modelo de los 15 laboratorios: 13 son de otros integrantes y su contenido no está cerrado.
- **Un solo archivo HTML, sin internet**, con pantalla de inicio y dos paradas (teclas 1 y 2), cada una con su ruta principal y su profundización. Cada parada refleja **solo su propio informe**.
- **No se mezcla el M6 dentro de REFRESH.** El informe del M6 no menciona REFRESH.
- **Arranque (24/10):** la defensa de investigaciones del 28/10 ya está lista, así que el modelo **empieza en cuanto Cristian cierre la revisión del Word del M6**; no espera al 28/10 ni al compendio de labs (no depende de ellos).
- **Plantilla:** si el modelo se hace en Claude Code, puede usarse `recorrido-3d-v3.zip` (recorrido de las investigaciones) **solo como plantilla visual y técnica** (armado offline, sellos, teclas, prueba de capturas). No se reutilizan paradas, textos, cifras ni el Edificio 2 de la UTP (el M14 lo excluye para evitar autoplagio con la Investigación 3).
- **Eficiencia:** trabajar sobre código fuente editable (como el recorrido de las investigaciones en Claude Code) y hacer cambios por partes, en vez de regenerar el HTML completo en cada ajuste. La matriz de trazabilidad va primero para evitar rehacer escenas.

## Parada 1 · M6 — Mantenimiento de Ventiladores y Sistemas de Distribución
Contenido tomado solo de `M6_Ficha_Fuentes_BORRADOR.md` y del Word final del M6 (completar la matriz con las 11 figuras y la Tabla 1 del Word).
- **Ruta principal**
  - Ventilador y red de ductos con compuertas y terminales (ilustrativo, inspirado en el banco de 8 terminales de Pedranzini et al., 2013, p. 325).
  - Antes del TAB: filtros limpios y prueba de fugas de ductos (DALT) antes del balanceo (Yale Facilities, 2025).
  - Animación de los **dos métodos de balanceo** (corregido el 25/10 con el texto del Word): el **método de proporción** iguala por pares las relaciones caudal medido/caudal de diseño, empezando por los dos terminales más desfavorecidos, y ajusta al final la velocidad del ventilador (iterativo); el **método de flujo progresivo** ajusta un terminal a la vez, desde el último hacia el ventilador, con variador y lazo de control. Meta: dentro de ±5 % de los caudales de diseño (Pedranzini et al., 2013, p. 323; Yale Facilities, 2025, §4.3A). Contador de pasos: "10 pasos frente a 14 del método de proporción" (Pedranzini et al., 2013, p. 328).
  - **Leyes de ventiladores**: control interactivo de velocidad; −20 % de velocidad = −50 % de potencia (U.S. DOE y AMCA, 2003, pp. 4, 18).
  - **Aplicación a Panamá**: Edificio N.° 1 de la UTP: 72.90 % del consumo; −35 % en el motor de la UMA; −14.10 %; 352,224 kWh; B/. 53,777.56 (Gollini-Mihalopoulos et al., 2023, pp. 143–148).
- **Profundización**
  - Efecto de sistema (hasta −30 %), fugas, correas 5–10 % y lista de mantenimiento (U.S. DOE y AMCA, 2003, pp. 9–25).
  - Medición de presión (U.S. DOE y AMCA, 2003, pp. 57–58).
  - Caso Kleberg: presión estática de 1.5 a 1.0 in wg; balance de aire con −7 % de electricidad (Claridge, Liu y Turner, 2003).
  - Caso Bogotá (Cristiano Mendivelso y Hernández Romero, 2023) con el cálculo propio del informe (17 de 33 fuera de ±5 %).
  - Marco panameño: Ley 69 de 2012, Res. 3142 de 2016 y ENUREE (Res. de Gabinete 66 de 2022).

## Parada 2 · M14 — Digitalización, BIM y Gestión Inteligente de Instalaciones (MEP)
Contenido tomado solo de `M14_Ficha_Fuentes_y_Esquema_BORRADOR.md` y del Word final del M14 (revisado y aprobado por Cristian el 24/10).
- **Escena base**: planta REFRESH S.A. con dimensiones del PDF del proyecto (terreno 100 × 100 m; Nave A 40 × 20 m; Nave B 30 × 18 m; Edificio C 24 × 12 m; Edificio D 25 × 12 m; Edificio E 20 × 10 m). El modelo 3D del simulador de REFRESH (Three.js r128) puede reutilizarse como base.
- **Ruta principal** (una escena por sección del Desarrollo)
  1. *Metodología BIM*: los modelos de cada especialidad se superponen y se resaltan interferencias (ilustrativo; Khanzode et al., 2008). → M14 · sección "La metodología BIM aplicada a sistemas HVAC-R".
  2. *Niveles LOD*: la unidad exterior del VRF evoluciona en 3D de LOD 100 (volumen de reserva) → 200 → 300 → 350 → 400 → 500 (as-built), con el texto de la Tabla 1 en cada paso (BIMForum, 2024). → M14 · Figura 1 y Tabla 1.
  3. *Ventajas cuantificadas*: tarjeta con las cifras de la Tabla 2 (Khanzode et al., 2008; Gallaher et al., 2004). → M14 · Tabla 2.
  4. *Del BIM al gemelo digital*: vista de capas (datos → procesamiento → modelos → visualización → nube) y tarjeta del caso IfM (Lu et al., 2020; Hu et al., 2026). El caso IfM se muestra como tarjeta o esquema; **no se modela el edificio de Cambridge**. → M14 · Figura 2.
  5. *Sistema MEP integrado*: VRF de los Edificios D y E, unidad de aire exterior, tableros con medidor **propuesto**, sala eléctrica del Edificio C con sensor de temperatura; puntos M1–M6 y C1–C4; animación de un aviso de filtro (M3) → controlador → pasarela BACnet/IP → SCADA → tablero → orden de trabajo en el CMMS; paro forzado (C3) desde el SCADA (Daikin Comfort Technologies North America, 2019; Thornton y Wagner, 2012). → M14 · Figura 3.
  6. *Propuesta para REFRESH*: de documentos separados (3D, P&ID, unifilar) a un modelo coordinado con entrega COBie (Batista et al., 2026; BIMForum, 2024). → M14 · sección "Propuesta de aplicación".
- **Profundización**
  - Inspector de cada punto M/C con lo que entrega el VRF y sus condiciones (potencia **calculada**; solo los puntos que existen y se habilitan).
  - Mantenimiento del VRF: filtros y serpentines, condensado, fugas difíciles de localizar, repuestos no intercambiables (Thornton y Wagner, 2012).
  - Panamá: sin iniciativa pública de BIM; BIM Fórum Panamá (Soto y Manríquez, 2023). → M14 · Conclusiones.
  - Condición de integración: los equipos de REFRESH usan Profibus/Profinet/EtherNet-IP; la compatibilidad BACnet ↔ SCADA queda por confirmar.

## Reglas obligatorias
- Cada tarjeta lleva un sello: **"Dato de fuente"** (con la cita APA) o **"Ilustrativo"**, y su referencia al informe (sección, figura o tabla).
- La distribución interna de las salas de D y E **no está en el proyecto REFRESH**: va marcada como ilustrativa.
- Sin capacidades (TR, kW, BTU/h), caudales ni lecturas que no estén en los informes.
- Nota visible: "Modelo conceptual, no a escala" (salvo las dimensiones de los edificios de REFRESH).
- Si Cristian cambia algo al revisar los Word, el modelo se ajusta al texto entregado.

## Insumos que hay que pedir en el chat nuevo
1. Word final del M6 y del M14.
2. Zip del proyecto REFRESH (PDF del proyecto final y la carpeta del simulador con `plano3d.js`, `data.js` y `lib/three.min.js`).
3. Opcional, solo como plantilla: `recorrido-3d-v3.zip`.

## Calendario (actualizado 24/10)
1. Cristian cierra la revisión del Word del M6 (el M14 ya está revisado).
2. **Inicio del chat del 3D**: matriz de trazabilidad → validación con Cristian → v1 → prueba sin internet en la laptop → ajustes. Corre en paralelo con lo siguiente.
3. Entrega del compendio de labs y defensa de investigaciones (28/10).
4. Unir los PDF del compendio de labs y sacar un extracto de datos verificados con páginas (fuente única para la presentación conjunta).
5. Presentación conjunta de labs (fecha por confirmar), en la que se decide en qué momento se muestra el 3D.
