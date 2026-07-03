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
| Zona de Descarga de Materia Prima | **15 × 6 m (techado)** | 2 posiciones de descarga (camión cisterna/tolva) + fosa de recepción + filtro colector de polvo (ATEX 22). Al norte/oeste del patio de silos. Subproceso ① |
| Estacionamientos | **30 puestos** | Incluye puestos accesibles (SENADIS) |
| Bahías de despacho | **4 bahías** | Salida de producto terminado al SUR |
| Área de expansión futura | **3,000 m² (30 % del terreno)** | Lado ESTE |
| Pasillos peatonales | 2.00 m (línea verde discontinua) | Área de giro peatonal 1.50 × 1.50 m |
| Pasillos de montacargas | 3.50 m (línea naranja discontinua) | Con espejos convexos y semáforos acústico-luminosos |
| Portones | Doble hoja 2.40 m con sello cortafuego hermético | |
| Entradas de personal (planos v2) | Administrativo: puerta peatonal en Edificio E (lado sur, desde estacionamientos) · Técnico: fachada oeste del Edificio D junto a lockers/vestidores → Nave A | Leyenda: "recorrido peatonal de personal" (verde punteada) y "puerta peatonal". Ver sección 15.1 |
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
| 13 | Zona de Descarga de Materia Prima | Fosa de recepción + filtro colector de polvo + 2 posiciones de descarga | 15 × 6 m (techado), al norte del patio de silos | 480 V 3Ø (filtro colector y compuertas neumáticas). Etapa ① del flujo: camiones cisterna/tolva → fosa → elevadores de cangilones → 4 silos |

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

## 10-B. PRINCIPIOS BÁSICOS DE DISTRIBUCIÓN EN PLANTA (Asignación #6 — parte b)

Terminología oficial de la PPT del curso: 1. Principio de la Integración de Conjunto · 2. Principio de la Mínima Distancia Recorrida · 3. Principio de la Circulación o Recorrido · 4. Principio del Espacio Cúbico · 5. Principio de Satisfacción y Seguridad · 6. Principio de Flexibilidad.

**Criterio general de jerarquización:** REFRESH S.A. es una planta de PROCESO QUÍMICO CONTINUO con un cuello de botella físico (torre de secado, 1,500 kg/h, opera 24/7 y nunca se detiene). En este tipo de planta, el material fluye permanentemente y cualquier desorden en la secuencia, retroceso o cruce de flujos genera pérdidas directas de capacidad en el cuello de botella — que son irrecuperables. Por eso los principios asociados al FLUJO DEL MATERIAL (Circulación + Mínima Distancia = 45 % combinado) dominan la jerarquía, seguidos por SEGURIDAD (20 %) debido al riesgo ATEX inherente al polvo de detergente. Los principios de optimización espacial y adaptabilidad (Espacio Cúbico, Flexibilidad) cierran la lista no por ser menos válidos, sino porque en esta planta ya quedaron resueltos por diseño y no condicionaron el trazado.

**Jerarquización 1–6 (suma 100 % ✓):**

**1. PRINCIPIO DE LA CIRCULACIÓN O RECORRIDO — 25 %**
POR QUÉ ES EL #1: En un proceso continuo, la secuencia de transformación es inalterable (slurry → secado → enfriado → post-adición → envasado). El layout DEBE seguir ese orden o la planta simplemente no funciona. Este principio no se "aplicó" al diseño: DICTÓ el diseño.
CÓMO SE APLICÓ: Las áreas de trabajo están ordenadas en la misma secuencia en que se transforma el material: silos (norte) → Nave A proceso ①→⑧ → pasarela técnica → Nave B envasado ⑨ → paletizado ⑩ → bahías de despacho (sur). Ningún material retrocede en ninguna etapa (única excepción: retorno de finos QC-3, línea neumática dedicada que no cruza el flujo principal).

**2. PRINCIPIO DE LA MÍNIMA DISTANCIA RECORRIDA — 20 %**
POR QUÉ ES EL #2: Cada metro extra de transporte de slurry caliente (65–75 °C) o gránulo es pérdida térmica, riesgo de taponamiento y costo de bombeo. En proceso continuo el material recorre esa distancia MILES de veces al año — un sobrecosto de distancia se multiplica brutalmente.
CÓMO SE APLICÓ: Flujo lineal Norte→Sur sin cruces: MP entra por el norte directo a silos; producto terminado sale por el sur directo a bahías. La pasarela A–B es RECTA (se evaluó una "L" y se descartó: rompía la caída por gravedad de las tolvas y agregaba un transportador). Equipos consecutivos del proceso son físicamente adyacentes. La bifurcación de envasado está al FINAL para que ambos módulos compartan el 100 % de la línea aguas arriba.

**3. PRINCIPIO DE SATISFACCIÓN Y SEGURIDAD — 20 %** (empatado en peso con el #2)
POR QUÉ ES EL #3: El polvo de detergente es ATEX (atmósfera explosiva). Un layout que mezcle fuentes de ignición (caldera, generador) con zonas de polvo es un riesgo inaceptable — la seguridad aquí no es un "extra", condiciona qué puede ir junto a qué.
CÓMO SE APLICÓ: Segregación en 5 edificios independientes (caldera y generador en Edificio C, separados de las naves con polvo). Pasillos peatonales de 2.00 m físicamente segregados de corredores de montacargas de 3.50 m. Cumplimiento SENADIS: áreas de giro 1.50×1.50 m, puestos de estacionamiento accesibles. Semáforos acústico-luminosos y espejos convexos en cruces. Portones doble hoja 2.40 m con sello cortafuego. Trabajadores seguros = trabajo satisfactorio (definición textual del principio en la PPT).

**4. PRINCIPIO DE LA INTEGRACIÓN DE CONJUNTO — 15 %**
POR QUÉ ES EL #4: La planta funciona como UN solo organismo (hombres + máquinas + servicios + materiales), pero esta integración es CONSECUENCIA de haber aplicado bien los principios 1–3, no la causa del trazado.
CÓMO SE APLICÓ: Los 5 edificios + patio de silos operan integrados: rack de tuberías aéreo lleva los servicios del Edificio C a la Nave A (vapor 8 barg, aire 7 barg, agua DI); SCADA central integra los PLC de todos los equipos; el Edificio D (laboratorio QC, taller, comedor) está posicionado equidistante de ambas naves para servir a todo el personal (65 personas pico/turno); el taller tiene portón directo a Nave A.

**5. PRINCIPIO DEL ESPACIO CÚBICO — 12 %**
POR QUÉ ES EL #5: Se aprovechó intensivamente la vertical, pero como HERRAMIENTA para servir al flujo (gravedad), no como objetivo en sí. El espacio horizontal no era una restricción (terreno de 10,000 m²).
CÓMO SE APLICÓ: Nave A con 22 m de altura libre para la torre; mezzanines técnicos a +4.50 m (Nave A) y +3.20 m (Nave B); tolvas buffer en plataforma elevada descargando POR GRAVEDAD a los módulos de envasado (cero energía de transporte); transportadores aéreos suspendidos a +8 m dejando el piso libre; elevadores de cangilones que suben la MP 14 m para que luego TODO el proceso descienda por gravedad — la planta usa la altura como motor gratuito del flujo.

**6. PRINCIPIO DE FLEXIBILIDAD — 8 %**
POR QUÉ ES EL #6: En una planta de proceso continuo dedicada a UN solo producto (detergente en polvo), la reordenación interna de equipos es inherentemente baja — la torre de 80–120 toneladas no se va a mover. La flexibilidad se resolvió por RESERVA DE ESPACIO, no por movilidad de equipos, y por eso no condicionó el trazado interno.
CÓMO SE APLICÓ: Área de expansión futura del 30 % del terreno (3,000 m²) en el lado ESTE, colindante con ambas naves — permite duplicar la capacidad (segunda torre o segunda línea de envasado) sin demoler ni reordenar nada de lo existente. La línea de envasado bifurcada admite un tercer módulo. Los servicios (generador 1,500 kW, transformador 1,500 kVA, banco 600 kVAr) están dimensionados con margen del 40 %+ para absorber la expansión. La demanda de los 6 formatos se ajusta con el calendario de turnos (flexibilidad operativa) sin tocar el layout.

**REGLA DE ORO PARA DEFENDER EL ORDEN:** "El orden refleja la naturaleza de la planta: en un proceso químico continuo con cuello de botella, el flujo manda (45 %), la seguridad ATEX condiciona (20 %), la integración ejecuta (15 %) y la optimización espacial y la flexibilidad se resuelven por diseño (20 %). En una planta de taller (job shop) el orden sería casi el inverso — la flexibilidad sería #1. La jerarquía no es universal: depende del tipo de proceso."

## 11. TEORÍA DE RESTRICCIONES (TOC)

Cuello de botella = **Torre GEA NIRO® a 1,500 kg/h** (Goldratt, 1984). Todos los equipos se dimensionaron alrededor de esta restricción. Si se pide >1,500 kg/h, el exceso de slurry se recircula (FCV-402). Si las tolvas llegan a 80 % → riesgo de sobreproducción; a 100 % → la torre debe reducir carga. El miércoles valida la regla: con 13.3 h de autonomía y 24 h de mantenimiento se requiere **gestión activa del nivel de tolvas antes del paro**. Referencias usadas: Goldratt (1984), Chase, Jacobs & Aquilano (2006), factor 85 % estándar industrial.

## 12. NORMAS APLICADAS (citarlas igual)

ISA-5.1 · ISO 10628 · DIN 28000 (P&ID) — NEC 2023/NFPA 70 y Código Eléctrico de Panamá (RIE) — NFPA 70E — IEEE 519 — ISO 50001 (monitoreo de energía, medidores clase 0.5S) — SENADIS Panamá (accesibilidad) — ATEX (zonificación de áreas con polvo/gas) — NFPA 110 (transferencia) — NEC 110/210/250/430/700.

## 13. EL SIMULADOR (para citarlo en el escrito/PPT)

App web de 5 pestañas (HTML/CSS/JS + Three.js + SVG): (1) Plano 2D con cotas, capas de flujo/QC/mezzanines, recorrido narrado de 10 pasos, checklist normativo 7/7, panel de principios de distribución (parte b), la Zona de Descarga de Materia Prima (Subproceso ①) y las entradas de personal administrativo/técnico con recorridos peatonales verdes y puertas clicables (alineado a planos v2); (2) Plano 3D orbital con animación de partículas por fase, mezzanines, zona de descarga (camiones, fosa, filtro colector) y puertas peatonales con recorridos verdes; (3) P&ID interactivo con variables de proceso en vivo y mando de válvulas; (4) Unifilar con 4 estudios (armónicos IEEE 519, selectividad, calculadora NEC, monitoreo ISO 50001); (5) Simulación de producción con calendario de 21 turnos, lógica TOC, sistema QC automático/manual y KPIs (incluye % no conforme y OEE). Todos los elementos son clickeables con ficha técnica. Verificado con 70 pruebas automatizadas. Repo: `Crysthian04/Creacion-de-Notepad`, carpeta `asignacion-6-distribucion-planta/`.

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

## 15. ACTUALIZACIÓN DEL PROYECTO FINAL (WORD) — DOCUMENTACIÓN OFICIAL ADICIONAL

**NOTA:** Todo lo de esta sección es DOCUMENTACIÓN del proyecto final Word. NO modifica layout, dimensiones ni valores canónicos existentes. **Los planos 2D/3D v2 (con entradas de personal) son ahora los oficiales.**

### 15.1 ENTRADAS DE PERSONAL (respuesta a observaciones de la profesora — YA en planos v2)

- **Entrada Personal Administrativo:** puerta peatonal en Edificio E (Corporativo), lado sur hacia estacionamientos, con recorrido peatonal verde desde el parking. El personal administrativo NO cruza zonas de proceso.
- **Entrada Personal Técnico:** puerta peatonal en fachada oeste del Edificio D, junto a Baños/Lockers. Flujo: ingresa → se cambia en lockers/vestidores → accede a Nave A.
- Leyenda nueva en planos: **"recorrido peatonal de personal"** (línea verde punteada) y **"puerta peatonal"**.

### 15.2 MÉTODO DE DESCARGA DE MP (explícito)

Sólidos a granel (carbonato, sulfato, silicato) llegan en camión → descargan en la **fosa de recepción** (zona de descarga 15×6 m techada, ATEX 22, con filtro colector de polvo) → **elevadores de cangilones** → 4 silos exteriores. Tensoactivos líquidos (LAS/AES): llegan en cisterna → se bombean a tanques.

### 15.3 JUSTIFICACIÓN PASARELA A-B (defensa ante observación de la profesora)

La pasarela de 3.00 m es un **corredor técnico cerrado dedicado al transporte del producto** (banda + servidumbre de mantenimiento de 1.2 m), NO una vía de circulación general de personas. El tránsito de personal usa los pasillos peatonales de 2.00 m.

### 15.4 PARTE E — PRESUPUESTO (Asignación #7, aprobado por la profesora)

**CAPEX total: USD $12,859,000** = Subtotal $11,690,000 + contingencia 10 %.
Por categoría: Mano de obra **$3.0M (25.7 %)** · Instalaciones y equipos **$5.38M (46.0 %**, torre GEA $3.2M la mayor partida) · Instalaciones externas **$1.98M (16.9 %)** · Logística **$0.5M (4.3 %)** · Ambiental y seguridad **$0.83M (7.1 %)**.
Nota: es CAPEX; el OPEX se proyecta por separado.

### 15.5 PARTE E — 15 ACTIVIDADES DE SEGURIDAD (con norma y responsable)

1. Inspección ATEX diaria (NFPA 652) · 2. EPP obligatorio (NFPA 70E/COPANIT) · 3. LOTO (NEC/OSHA) · 4. Capacitación y simulacros (Ley 67) · 5. Mantenimiento preventivo de críticos (ISO 55000) · 6. Señalización de pasillos (SENADIS) · 7. Control de tráfico de montacargas · 8. Sistema contra incendios (NFPA 10/654) · 9. Monitoreo de emisiones (MiAmbiente) · 10. Químicos y SDS (GHS) · 11. Puesta a tierra ≤5 Ω (NEC 250) · 12. Control de visitantes · 13. Ergonomía (ISO 45001) · 14. Recipientes a presión — caldera 8 barg (ASME/NFPA 85) · 15. Residuos y 5S (ISO 14001).

### 15.6 ORGANIGRAMA OFICIAL (de Asignación #2, conservado en el proyecto final)

**Director de Planta → 8 gerencias:** Operaciones (supervisores de turno, operadores, auxiliares, ings. de procesos, analistas de mejora continua) · Seguridad y Salud Ocupacional (supervisores de seguridad) · Ingeniería (jefe de mantenimiento, planeador, ing. confiabilidad, supervisores, técnicos, automatizadores) · Proyectos (supervisor) · Calidad (ing. calidad, analistas de fórmulas, inspectores) · Logística y Cadena de Suministro (compras, distribución y ventas, almacén) · RR.HH. (gente, planilla) · Gestión (analista de gestión y procesos).

### 15.7 MISIÓN / VISIÓN / VALORES OFICIALES (versión final mejorada)

- **Misión:** "Fabricar productos de limpieza de alta calidad al mejor precio del mercado, con compromiso en higiene, sostenibilidad y eficiencia."
- **Visión:** "Ser una empresa líder en la fabricación de productos de limpieza y cuidado de la ropa a nivel nacional en Panamá."
- **Valores (6 pilares):** Innovación aplicada · Responsabilidad ambiental · Integridad · Accesibilidad · Confiabilidad · Transparencia en la fórmula.

### 15.8 CONCLUSIONES Y RECOMENDACIONES DEL PROYECTO (6+6, resumen)

**Conclusiones clave:** 81 % hogares panameños año 1 · torre como decisión determinante · selección GEA/ROVEMA/H&B por integración y soporte LATAM · distribución por producto en 10,000 m²/5 edificios · seguridad integral SENADIS+ATEX · CAPEX $12.9M viable.
**Recomendaciones clave:** monitorear aire comprimido S-2 (91 % de uso, primer servicio a ampliar) · expansión planificada (2ª línea de envasado → 2º spray dryer año 3–5) · activar mantenimiento predictivo (QUAT²RO®) · gestión activa de tolvas pre-miércoles · contratos de largo plazo con proveedores LATAM · certificación progresiva ISO 9001/14001/50001.
