# PROMPT MAESTRO — REFRESH S.A. · Fuente Única de Verdad
## Asignación #6 — Distribución de Planta · Curso: Selección de Equipos y Trazado de Planta

**INSTRUCCIÓN PARA EL ASISTENTE:** Estás ayudando a redactar el trabajo escrito (y posteriormente una presentación PPT) de la Asignación #6. Ya existe un **simulador web interactivo terminado y aprobado** que es la referencia oficial del proyecto. Este documento contiene TODOS sus datos canónicos. **Usa exactamente estos valores — no inventes, no redondees distinto, no cambies nombres ni tags.** Si algún documento o versión anterior del proyecto contradice estos valores, **estos son los válidos** (ver sección 14: conflictos ya resueltos).

---

## 1. IDENTIDAD DEL PROYECTO

- Empresa: **REFRESH S.A.** — Planta de Detergente en Polvo · Panamá
- Asignación #6 — Parte D: Distribución de planta con equipos
- Encabezado/cajetín oficial: "REFRESH S.A. · Planta de Detergente en Polvo · Asignación #6 — Distribución de Planta · Escala 1:250 · Cotas en metros · Junio 2026"
- Planos de referencia: Plano General (1:250) · P&ID **REF-PRC-PID-001** · Unifilar **ELEC-REF-001**
- El simulador interactivo (5 pestañas: Plano 2D, Plano 3D, P&ID, Unifilar, Simulación) vive en el repo GitHub `Crysthian04/Creacion-de-Notepad`, carpeta `asignacion-6-distribucion-planta/`.

## 2. TERRENO Y EDIFICIOS (cotas en metros)

| Área | Dimensiones | Notas |
|---|---|---|
| Terreno total | **100 × 100 m (10,000 m²)** | Vial perimetral de 7.00 m, radios de giro R 15.00 |
| Nave A — Área de Proceso | **40 × 20 m** | Altura libre 22 m en zona de torre |
| Nave B — Área de Envasado | **30 × 18 m** | Conectada a Nave A por pasillo técnico cerrado de 3.00 m |
| Edificio C — Servicios Industriales | **24 × 12 m** | Sala de calderas (ATEX), compresores + agua desmineralizada (ATEX), sala eléctrica/generador/UPS (ATEX) |
| Edificio D — Operativo | **25 × 12 m** | Laboratorio QC, comedor, baños/lockers H y M, taller mecánico/eléctrico |
| Edificio E — Corporativo | **20 × 10 m** | Recepción, oficinas, sala de juntas |
| Patio de Silos Exterior | **15 × 10 m (techado)** | 4 silos Ø2.50 m + elevadores de cangilones |
| Estacionamientos | **30 puestos** | Incluye puestos accesibles (SENADIS) |
| Bahías de despacho | **4 bahías** | Salida de producto terminado al SUR |
| Área de expansión futura | **3,000 m² (30 % del terreno)** | Lado ESTE |
| Pasillos peatonales | 2.00 m (línea verde discontinua) | Área de giro peatonal 1.50 × 1.50 m |
| Pasillos de montacargas | 3.50 m (línea naranja discontinua) | Con espejos convexos y semáforos acústico-luminosos |
| Portones | Doble hoja 2.40 m con sello cortafuego hermético | |
| Mezzanines (complemento) | Nave A: plataforma técnica a **+4.50 m** · Nave B: a **+3.20 m** | Con tuberías elevadas |

Orientación: norte arriba. **Acceso de camiones de materia prima por el NORTE; despacho de producto terminado por el SUR.**

## 3. EQUIPOS PRINCIPALES (con alimentación eléctrica)

| # | Equipo | Marca/Modelo | Huella | Potencia / alimentación |
|---|---|---|---|---|
| 1 | Torre de Secado por Atomización | **GEA NIRO® Conventional Spray Dryer** | Base 12 × 14 m, cámara 15–20 m de alto, 80–120 t | Ventilador tiro inducido EF-101: **150 HP, 480 V 3Ø** (VFD-103, MCC-A) |
| 2 | Tanques de mezcla TK-101/TK-102 | SS 316L, **10,000 L** c/u, con agitadores | Ø3.0 m × 4.5 m | Mezclador M-101: **75 HP** (VFD-101) · slurry 35–45 % sólidos a 65–75 °C |
| 3 | Bombas P-101 (principal) / P-102 (reserva N+1) | Alta presión **100–250 bar** | 2.0 × 1.2 m | **50 HP c/u, 480 V 3Ø** (P-101 con VFD-102) · sellos mecánicos dobles |
| 4 | Enfriador/Tamizador | **GEA VIBRO-FLUIDIZER®** | ~4 × 2 m, h 1.8 m, 3–5 t | 20–45 kW, 480 V 3Ø |
| 5 | Post-adición | Ribbon blender + dosificadores | 4 × 2.5 m | 480 V 3Ø (enzimas, fragancias, perlas) |
| 6 | Tolvas Buffer | **3 × 5,000 kg = 15,000 kg** | 6.00 × 3.00 m, plataforma elevada | Tornillos de descarga 480 V |
| 7 | Envasadora VFFS (Módulo A — hogar) | **ROVEMA BVC 600** | 1.8 × 1.2 m, h 2.8 m, <1.5 t | **75 HP** en MCC-B (VFD-201) |
| 8 | Ensacadora (Módulo B — industrial) | **HAVER & BOECKER INTEGRA® IV** | 2.5 × 2.0 m, h 2.8 m, 2–3 t | **75 HP** (VFD-202) · breaker local 75 A/18 kAIC |
| 9 | Bandas BC-101 y BC-102 | — | 6.0 m c/u | **10 HP c/u** (VFD-203/204) |
| 10 | Paletizador Robot | Brazo robótico | 2.2 × 2.2 m | **75 HP, 480 V 3Ø** · pallets 1.20 × 1.00 m |
| 11 | Checkweigher + Detector de metales | Compartidos en línea | 1.6 × 1.0 m | **120/208 V** desde TTD |
| 12 | Estación de Cuarentena QC | Área de bloqueo de lote | 5.0 × 3.0 m, Nave B | 120/208 V (báscula de verificación) |

**Regla operativa clave:** la línea de envasado es UNA sola con bifurcación final (distribuidor de flujo). **Solo UN módulo (A o B) opera a la vez, nunca simultáneo.**

## 4. FLUJO DEL PROCESO — 10 SUBPROCESOS Y FASES DEL PRODUCTO

1. Recepción MP (silos exteriores) → sólido/líquido a granel
2. Dosificación y pesado (transporte neumático) → sólido en polvo
3. Mezclado fase húmeda TK-101/TK-102 → 🔵 **SLURRY LÍQUIDO 35–45 % sólidos, 65–75 °C**
4. Bombeo y filtrado P-101/P-102 a 100–250 bar → 🔵 líquido presurizado
5. **Torre GEA NIRO® (CUELLO DE BOTELLA, 1,500 kg/h máx)** → 🟠 **CAMBIO DE FASE líquido → gránulo sólido, humedad <5 %, sale a 60–80 °C**
6. Enfriador/tamizador VIBRO-FLUIDIZER → 🟡 gránulo <35 °C clasificado (finos retornan a torre por línea neumática)
7. Post-adición → 🟡 polvo terminado
8. Tolvas buffer (tornillo helicoidal) → 🟡 polvo almacenado
9. Envasado: distribuidor → Módulo A o B → checkweigher → detector de metales → 🟢 producto envasado
10. Paletizado robot → despacho (4 bahías sur) → 🟢 pallets

Código de colores de fase (usar igual en escrito y PPT): 🔵 azul líquido/slurry · 🟠 naranja gránulo caliente · 🟡 amarillo polvo frío · 🟢 verde envasado/pallets.

## 5. CAPACIDADES (Asignación #4 — base de todo)

| Tipo | kg/h | kg/día | kg/mes |
|---|---|---|---|
| Diseño (100 %) | **1,500** | 36,000 | 1,080,000 |
| Sistema (85 %) | **1,275** | 30,600 | 918,000 |
| **Real (75 %) — valor operativo** | **1,125** | **27,000** | **810,000** |

Velocidades de envasado: VFFS 500 g: **3,600 uds/h** · 1 kg: **2,400** · 3 kg: **900** · Ensacadora 5 kg: **540** · 20 kg: **180** · 50 kg: **90 uds/h**.

Distribución por presentación (base 27,000 kg/día): 500 g 15 % (4,050 kg/día) · 1 kg 25 % (6,750) · 3 kg 20 % (5,400) · 5 kg 15 % (4,050) · 20 kg 15 % (4,050) · 50 kg 10 % (2,700). Segmentos: Hogar (bolsas) / Industrial (sacos).

Verificación de metas mensuales (4 ciclos × 7 días): 500 g: 345,600 vs meta 243,000 (**CUMPLE +42 %**) · 1 kg: 230,400 vs 202,500 (+14 %) · 3 kg: 57,600 vs 54,000 (+7 %) · 5 kg: 34,560 vs 24,300 (+42 %) · 20 kg: 11,520 vs 6,075 (+90 %) · 50 kg: 2,880 vs 1,620 (+78 %). El excedente = stock de seguridad.

**Tolvas buffer:** 15,000 kg → autonomía = 15,000 / 1,125 = **13.3 horas**. **La torre GEA NIRO® NUNCA se detiene (24/7)** — opera como caldera industrial; paro mayor 1 vez/año (7–14 días), ya descontado en el 85 %.

## 6. CALENDARIO SEMANAL (21 turnos: T1 06:00–14:00 · T2 14:00–22:00 · T3 22:00–06:00)

| Día | T1 | T2 | T3 |
|---|---|---|---|
| Lunes | Bolsa 500 g | Bolsa 500 g | SETUP 500 g → 1 kg |
| Martes | Bolsa 1 kg | Bolsa 1 kg | Bolsa 1 kg |
| Miércoles | MANTENIMIENTO | MANTENIMIENTO | MANTENIMIENTO (solo envasado; torre sigue 24/7, tolvas acumulan) |
| Jueves | SETUP 1 kg → 3 kg | Bolsa 3 kg | Bolsa 3 kg |
| Viernes | SETUP 3 kg → 5 kg | Saco 5 kg | SETUP 5 kg → 20 kg |
| Sábado | Saco 20 kg | SETUP 20 kg → 50 kg | Saco 50 kg |
| Domingo | Libre/buffer | Libre/buffer | Libre/buffer |

Balance: **13 turnos productivos + 5 setups (1 h c/u) + 3 mantenimiento + 3 libres**. Régimen de mantenimiento GEA NIRO®: diario/semanal y trimestral sin paro; ANUAL paro mayor 7–14 días; el miércoles es solo de la línea de envasado (preventivo VFFS + CIP).

## 7. CONTROL DE CALIDAD — 4 PUERTAS QC · 4 CAMINOS (meta <2 % no conforme)

| Puerta | Pregunta | Ubicación | Camino si NO conforme |
|---|---|---|---|
| **QC-1** | ¿MP cumple ficha técnica? | Recepción (silos) | **Devolución a proveedor** (sale del sistema) |
| **QC-2** | ¿Slurry OK? (densidad/viscosidad/% sólidos) | Salida de mezclado | **Reformular + re-mezclar** (torre en recirculación ~1 h) |
| **QC-3** | ¿Humedad ≤ 5 %? | Salida torre/enfriado | **Retrabajo de gránulos** → retornan al mezclado (~1 h) |
| **QC-4** | ¿Peso · sello · metales OK? | Checkweigher + detector | **CUARENTENA** (bloqueo de lote, auditoría QA) → disposición final: ♻ Reproceso (≈80 %, retorna a tolvas/post-adición) o ✗ Desecho |

Cobertura total del flujo desde MP hasta envasado. Cada camino con responsable, registro y trazabilidad. **Meta: <2 % de producto no conforme — la mayoría se recupera vía reproceso.** Existe una Estación de Cuarentena física (5×3 m) en Nave B junto al paletizador.

## 8. P&ID REF-PRC-PID-001 (ISA-5.1 / ISO 10628 / DIN 28000)

Servicios (Edificio C → rack de tuberías aéreo → Nave A):
- **S-1 Caldera:** vapor **8 barg, 185 °C** → PT-101, PI-101, XV-101 → trampa ST-101 → intercambiador **HX-101** (calefaccionamiento del aire, lazo TT-101 → TC-101 → XV-102 neumática) → aire caliente 200–300 °C a torre. Condensado retorna. (Complemento: HX ≈380 kW, ≈78 m².)
- **S-2 Compresores:** aire **7 barg** → PT-201, PI-201, filtro F-201 (actuadores y pulsos de ciclones).
- **S-3 Agua desmineralizada (RO + EDI):** → PT-301, PI-301, F-301 → tanques de mezcla y CIP de la torre (FT-301, XV-302).
- **Línea de proceso:** TK-101/TK-102 (LT-101/LT-102) → P-101/P-102 con válvulas check → filtro Y F-401 → línea alta presión con PT-401, FT-402 (Coriolis 0–2,000 kg/h), PCV-401 neumática → boquilla atomizadora (tipo lanza, Delavan). Ciclones 1 y 2 (XV-201/XV-202 pulsos, PI-202/PI-203, captura ≈99.2 %). Recirculación de exceso: FCV-402 + FIT-402. Retorno de retrabajo QC-3 a mezclado.
- Tipos de línea: vapor · condensado · aire comprimido · agua DI · pasta húmeda (proceso) · retorno/recirculación · drenajes.
- Cajetín: "REFRESH S.A. — Diagrama de Tuberías e Instrumentación (P&ID) · Servicios Industriales y Proceso — Nave A · P&ID No.: REF-PRC-PID-001 · Hoja 1 de 1 · Escala N.T.S."

## 9. UNIFILAR ELÉCTRICO ELEC-REF-001 (NEC 2023/NFPA 70 · Código Eléctrico de Panamá)

1. **Acometida:** Red Naturgy Panamá **13.8 kV, 3Ø, 60 Hz** → cortacircuitos de expulsión (M.O.V.) + pararrayos → acometida MT subterránea **3×1/0 AWG, 15 kV XLPE** → banco de medición (kWh/kW/kVArh).
2. **Transformador T-1:** **1,500 kVA, 13.8 kV Δ – 480Y/277 V**, 3Ø, pad-mounted (I sec ≈ 1,804 A).
3. **Generador AES gas natural: 1,500 kW, 480 V** con post-tratamiento de escape → **ATS 1600 A, 3P**.
4. **Calidad de energía:** banco de capacitores automático **600 kVAr** · UPS industrial **100 kVA** (480→120 V) → tablero UPS crítico · tablero PLC/DCS · filtros activos **AHF-01 y AHF-02 (300 A)**.
5. **MCC-A (Nave A): 1600 A, 65 kAIC** — M-101 75 HP, P-101 50 HP, P-102 50 HP, EF-101 150 HP (VFD-101/102/103).
6. **MCC-B (Nave B): 600 A nominal / 800 A frame, 35 kAIC** — VFFS 75 HP, Ensacadora 75 HP, BC-101/102 10 HP c/u, Paletizador 75 HP (VFD-201 a 204).
7. **Baja tensión:** PD-D y PD-E 480Y/277 V, 3Ø, 4W, **400 A** → TLD (277 V, 225 A) y TTD (120/208 V, 225 A). Circuito típico: ITM 15 A 1P → EMT Ø3/4" → THHN F+N+T 12 AWG → dúplex + GFCI → varilla Copperweld 5/8" × 2.40 m, **puesta a tierra ≤ 5 Ω**.
8. **IEEE 519:** THDv Nave A **18.7 % → 3.2 %** · Nave B **15.3 % → 2.9 %** · FP **0.82 → 0.96** (armónicos característicos de VFD 6 pulsos: 5º, 7º, 11º, 13º). PFC: con 1,200 kW de carga, llevar FP 0.82→0.96 requiere ≈487 kVAr → el banco de 600 kVAr es suficiente ✓.
9. **NFPA 70E (energías incidentes):** Main Edif. C: **5.8 cal/cm² (frontera restringida 1.52 m)** · ATS: **4.1 (1.37 m)** · MCC-A: **3.2 (1.22 m)** · MCC-B: **2.0 (1.07 m)**. EPP **Categoría 2 (ATPV 8.0 cal/cm²)**.
10. **Selectividad:** falla en ensacadora Mod. B → dispara SOLO el breaker local (75 A, 18 kAIC) sin afectar niveles superiores (NEC 700 / IEC 60947). Coordinación: Main 1600 A/65 kAIC · ATS 1600 A/85 kAIC · MCC-A 1600 A/65 kAIC · MCC-B 800 A/35 kAIC · local 75 A/18 kAIC.
11. Conductores Cu THHN/THWN 600 V 75 °C mín. · bandejas escalerilla cal. 14 galvanizadas en caliente · alturas según NEC 110. Colores: rojo = fuerza 480 V 3Ø · azul = 120/208 V · negro discontinuo = control (Cat 6A/fibra) · verde = tierra.

## 10. TIPO DE DISTRIBUCIÓN DE PLANTA (justificación oficial)

- **Principal: POR PRODUCTO (en línea)** — los equipos siguen el orden exacto del proceso ①→⑩ sin retrocesos; la naturaleza continua de la GEA NIRO® (24/7) lo exige. Ventajas: mínimo manejo de materiales, QC integrado en línea, máxima utilización del cuello de botella.
- **Complementaria: POR PROCESO (funcional)** — áreas de soporte (laboratorio QC, taller, calderas, SCADA) agrupadas por función en Edificios C y D.
- **NO aplican:** tecnología de grupos (producto único, sin familias de partes) ni posición fija (el producto avanza continuamente).

## 11. TEORÍA DE RESTRICCIONES (TOC)

Cuello de botella = **Torre GEA NIRO® a 1,500 kg/h** (Goldratt, 1984). Todos los equipos se dimensionaron alrededor de esta restricción. Si se pide >1,500 kg/h, el exceso de slurry se recircula (FCV-402). Si las tolvas llegan a 80 % → riesgo de sobreproducción; a 100 % → la torre debe reducir carga. El miércoles valida la regla: con 13.3 h de autonomía y 24 h de mantenimiento se requiere **gestión activa del nivel de tolvas antes del paro**. Referencias usadas: Goldratt (1984), Chase, Jacobs & Aquilano (2006), factor 85 % estándar industrial.

## 12. NORMAS APLICADAS (citarlas igual)

ISA-5.1 · ISO 10628 · DIN 28000 (P&ID) — NEC 2023/NFPA 70 y Código Eléctrico de Panamá (RIE) — NFPA 70E — IEEE 519 — ISO 50001 (monitoreo de energía, medidores clase 0.5S) — SENADIS Panamá (accesibilidad) — ATEX (zonificación de áreas con polvo/gas) — NFPA 110 (transferencia) — NEC 110/210/250/430/700.

## 13. EL SIMULADOR (para citarlo en el escrito/PPT)

App web de 5 pestañas (HTML/CSS/JS + Three.js + SVG): (1) Plano 2D con cotas, capas de flujo/QC/mezzanines, recorrido narrado de 10 pasos y checklist normativo 7/7; (2) Plano 3D orbital con animación de partículas por fase; (3) P&ID interactivo con variables de proceso en vivo y mando de válvulas; (4) Unifilar con 4 estudios (armónicos IEEE 519, selectividad, calculadora NEC, monitoreo ISO 50001); (5) Simulación de producción con calendario de 21 turnos, lógica TOC, sistema QC automático/manual y KPIs (incluye % no conforme y OEE). Verificado con 65 pruebas automatizadas.

## 14. ⚠ CONFLICTOS YA RESUELTOS — VALORES CANÓNICOS (no usar los antiguos)

Existieron versiones previas del proyecto (repos viejos) con valores distintos. **Estos quedaron DESCARTADOS.** Los válidos son:

| Concepto | ✅ VALOR OFICIAL | ❌ NO usar |
|---|---|---|
| Generador de respaldo | **1,500 kW (AES, gas natural)** | 800 kW / 1000 kVA |
| Presión de caldera S-1 | **8 barg · 185 °C** | 15.5 bar |
| Main breaker | **1600 A · 65 kAIC** | 2000 A |
| UPS | **100 kVA** | 120 kVA |
| Tanques de mezcla | **TK-101/TK-102 · 10,000 L** | V-101/V-102 · 3,500 L |
| Centros de carga | **MCC-A 1600 A · MCC-B 600/800 A** | CC-1 600 A / CC-2 400 A |
| Ciclones | **2 ciclones (1 y 2)** | 1 ciclón (CY-201) |
| Bombas | **P-101 (ppal) y P-102 (reserva)** | P-101A/P-101B |
| Banco de capacitores | **600 kVAr** | 350 kVAr |
| THDv | **18.7→3.2 % (A) · 15.3→2.9 % (B)** | 24.5→2.8 % (THD-I) |

**Si la persona te comparte documentos viejos con los valores de la columna ❌, corrígelos a la columna ✅.**
