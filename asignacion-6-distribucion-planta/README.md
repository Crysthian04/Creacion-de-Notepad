# REFRESH S.A. — Planta de Detergente en Polvo · Panamá
## Asignación #6 — Parte D: Distribución de Planta con Equipos (App Web Interactiva)

Aplicación web de una sola página (HTML + CSS + JavaScript vanilla, sin frameworks) para el curso **Selección de Equipos y Trazado de Planta**.

## Cómo abrir

**Opción 1 (doble clic):** abrir `index.html` directamente en el navegador (Chrome/Edge/Firefox). Se requiere conexión a internet solo para cargar Three.js desde CDN (pestaña 3D).

**Opción 2 (servidor local):**
```bash
cd asignacion-6-distribucion-planta
python -m http.server 8000
# abrir http://localhost:8000
```

Resolución recomendada: 1280 px de ancho o más.

## Qué hace cada pestaña

| # | Pestaña | Contenido |
|---|---|---|
| 1 | **Plano 2D — Distribución de Planta** | Terreno 100×100 m (escala 1:250) con Naves A/B, Edificios C/D/E, patio de silos, estacionamientos (30 puestos, accesibles SENADIS), 4 bahías de despacho y área de expansión (3,000 m²). Cotas en metros activables, zoom/pan, capa de flujo ①→⑩, leyenda de circulación (peatonal 2.00 m / montacargas 3.50 m). **Cada edificio y máquina es clicable** → ficha técnica con dimensiones, peso, voltaje/potencia, consumos, materiales y sinergia aguas arriba/abajo. |
| 2 | **Plano 3D — Vista Isométrica/Orbital** | Escena Three.js (r128, CDN) con controles orbitales propios. La torre GEA NIRO® (cilindro + cono, 20 m) destaca como el elemento más alto. Raycasting con clic → la misma ficha técnica. **Animación del flujo:** partículas azules (líquido/slurry por tuberías), ámbar (gránulo/polvo por transportadores) y cajas verdes (producto envasado), con velocidad proporcional al throughput de la simulación. Cámaras predefinidas: General / Nave A / Nave B / Servicios. |
| 3 | **P&ID — REF-PRC-PID-001** | Servicios S-1 (vapor 8 barg), S-2 (aire 7 barg), S-3 (agua DI RO+EDI) → rack aéreo → Nave A: intercambiador HX-101, TK-101/TK-102, P-101/P-102, filtro Y F-401, torre con boquilla y ciclones, CIP y recirculación (FCV-402). Instrumentos ISA-5.1 clicables (PT/PI/TT/TC/FT/FIT/PCV/FCV/XV/LT/ST), leyenda de líneas y símbolos, animación de flujo por tipo de fluido y cajetín completo. |
| 4 | **Unifilar Eléctrico — ELEC-REF-001** | Desde la acometida Naturgy 13.8 kV (cortacircuitos M.O.V. + pararrayos, medición), transformador 1,500 kVA 13.8 kV Δ–480Y/277 V, generador AES 1,500 kW + ATS 1600 A, capacitores 600 kVAr, UPS 100 kVA, AHF-01/02, MCC-A (1600 A) y MCC-B (600/800 A) con todos los motores y VFDs, paneles PD-D/PD-E y circuito típico 120 V hasta la varilla Copperweld. Capas: **fronteras de arco eléctrico** (NFPA 70E) y **estado energizado** (miércoles: MCC-B en gris, MCC-A vivo). Mini-panel IEEE 519 (THDv y FP antes/después). Cada elemento clicable muestra kAIC, energía incidente y EPP. |
| 5 | **Simulación de Producción** | Slider maestro 0–2,000 kg/h (predeterminado 1,125 = capacidad real 75 %), velocidad de envasado, nivel de tolvas, velocidades 1×/60×/600×, ▶/⏸/🔄 RESET. Reloj de planta (día/hora/turno) que recorre los 21 turnos del calendario exacto de la Asignación #4 (setups de 1 h, miércoles de mantenimiento con torre 24/7). Línea de proceso de 10 etapas con fase del producto por color (🔵 slurry → 🟠 gránulo en la torre → 🟡 polvo → 🟢 envasado), tolvas con nivel animado, lógica TOC de cuellos de botella con alertas, KPIs en vivo y registro de eventos. |

**Sinergia global:** el estado de la simulación se comparte entre pestañas — la torre en alerta parpadea en el 2D, pulsa en rojo en el 3D y el P&ID, y el unifilar muestra MCC-B desenergizado durante el mantenimiento. Las fichas técnicas incluyen el estado operativo actual (kg/h, % de utilización, alertas).

## Control de calidad — producto no conforme (4 puertas QC · 4 caminos)

- **QC-1** (¿MP cumple ficha técnica?) → Devolución a proveedor · **QC-2** (¿Slurry OK?) → Reformular + re-mezclar · **QC-3** (¿Humedad ≤5 %?) → Retrabajo de gránulos · **QC-4** (¿Peso·sello·metales OK?) → Cuarentena con disposición final ♻ Reproceso / ✗ Desecho.
- **Modo automático:** durante la simulación normal se detectan no conformes ocasionales (meta <2 %) y se disponen solos (≈80 % reproceso). **Modo manual:** botones QC-1 a QC-4 en la pestaña 5; en QC-4 tú decides la disposición.
- Estación de Cuarentena visible y clicable en el plano 2D/3D, puertas QC y líneas de retorno en la capa "🧪 Puertas QC y retornos" del 2D, retorno de retrabajo en el P&ID, y KPIs de % no conforme / reproceso / desecho en vivo.

## Datos clave del modelo

- Torre GEA NIRO®: **cuello de botella, máx 1,500 kg/h**, opera 24/7 (nunca se detiene).
- Tolvas buffer: 3 × 5,000 kg = 15,000 kg → autonomía 15,000 / 1,125 = **13.3 h**.
- Línea de envasado única con bifurcación: **solo un módulo (A o B) opera a la vez**.
- Capacidades: Diseño 1,500 kg/h · Sistema 1,275 kg/h · **Real 1,125 kg/h (predeterminado)**.

## Normas aplicadas

- **ISA-5.1** — identificación y símbolos de instrumentación (P&ID).
- **ISO 10628 / DIN 28000** — diagramas de flujo de plantas de proceso.
- **NEC 2023 (NFPA 70)** y **Código Eléctrico de Panamá (RIE)** — diseño del unifilar, conductores THHN/THWN 600 V 75 °C, NEC 110/210/250/430/700.
- **NFPA 70E** — energías incidentes, fronteras de arco (restringida/limitada) y EPP Categoría 2 (ATPV 8.0 cal/cm²).
- **IEEE 519** — calidad de energía: THDv 18.7→3.2 % (Nave A), 15.3→2.9 % (Nave B), FP 0.82→0.96.
- **SENADIS (Panamá)** — puestos de estacionamiento accesibles y accesibilidad peatonal.

## Estructura del código

```
index.html    — estructura de pestañas, encabezado-cajetín, drawer
styles.css    — estética de plano de ingeniería
data.js       — PLANT_DATA: modelo de datos maestro (equipos, edificios, calendario, eléctrico)
common.js     — utilidades SVG, zoom/pan, tooltip, fichas (drawer), bus de eventos
sim.js        — motor de simulación (estado global compartido)
simui.js      — interfaz de la pestaña 5 (controles, KPIs, Sankey, log)
plano2d.js    — pestaña 1 (SVG con cotas)
pid.js        — pestaña 3 (P&ID ISA-5.1)
unifilar.js   — pestaña 4 (NEC/NFPA 70E/IEEE 519)
plano3d.js    — pestaña 2 (Three.js + control orbital propio)
app.js        — arranque, pestañas y reloj global
```
