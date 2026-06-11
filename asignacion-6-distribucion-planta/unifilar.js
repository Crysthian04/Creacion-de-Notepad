/* ============================================================
   Pestaña 4 — Diagrama Unifilar Eléctrico ELEC-REF-001 (SVG)
   NEC 2023 (NFPA 70) · NFPA 70E · IEEE 519 · Código Eléctrico de Panamá
   Convención: rojo = fuerza 480 V 3Ø · azul = corriente/retorno ·
   negro discontinuo = control/comunicaciones · verde = tierra
   ============================================================ */

const Unifilar = {
  inicializado: false,
  ROJO: '#c62828', AZUL: '#1565c0', VERDE: '#2e7d32', NEGRO: '#263238',

  init() {
    if (this.inicializado) return;
    this.inicializado = true;
    const cont = document.getElementById('vistaUni');

    const tb = document.createElement('div');
    tb.className = 'toolbar';
    tb.innerHTML = `
      <button id="btnAjustarUni">⤢ Ajustar vista</button>
      <label class="toggle" id="tgArco">⚡ Fronteras de arco eléctrico</label>
      <label class="toggle on" id="tgEnerg">🔌 Estado energizado</label>`;
    cont.appendChild(tb);

    // Mini-panel IEEE 519
    const ip = document.createElement('div');
    ip.className = 'mini-panel';
    const e5 = PLANT_DATA.electrico.ieee519;
    ip.innerHTML = `<h4>IEEE 519 — Calidad de energía</h4>
      <table>
        <tr><th></th><th>THDv antes</th><th>THDv después</th></tr>
        <tr><td>Nave A</td><td>${e5.naveA.thdvAntes}</td><td class="mejora">${e5.naveA.thdvDespues}</td></tr>
        <tr><td>Nave B</td><td>${e5.naveB.thdvAntes}</td><td class="mejora">${e5.naveB.thdvDespues}</td></tr>
        <tr><td>Factor de potencia</td><td>${e5.fpAntes}</td><td class="mejora">${e5.fpDespues}</td></tr>
      </table>
      <div style="margin-top:5px;color:#555">Con filtros activos AHF-01/AHF-02 (300 A) y banco de capacitores 600 kVAr.</div>
      <div id="estadoMccUni" style="margin-top:6px;font-weight:700"></div>`;
    cont.appendChild(ip);

    const svg = svgEl('svg', { class: 'lienzo-svg' });
    cont.appendChild(svg);
    this.svg = svg;
    this.panZoom = instalarPanZoom(svg, { x: 0, y: 0, w: 1400, h: 1500 });
    document.getElementById('btnAjustarUni').onclick = () => this.panZoom.ajustar();

    this.dibujar();

    document.getElementById('tgArco').onclick = (e) => {
      e.currentTarget.classList.toggle('on');
      this.gArco.style.display = e.currentTarget.classList.contains('on') ? '' : 'none';
    };
    document.getElementById('tgEnerg').onclick = (e) => {
      e.currentTarget.classList.toggle('on');
      this.energizadoVisible = e.currentTarget.classList.contains('on');
      this.actualizarEnergizado();
    };
    this.energizadoVisible = true;
    Bus.on('tick', () => this.actualizarEnergizado());
  },

  // ---------- helpers de símbolos ----------
  cable(d, color, w = 2.5, dash = '') {
    const p = svgEl('path', { d, fill: 'none', stroke: color, 'stroke-width': w, 'stroke-dasharray': dash });
    this.svg.appendChild(p);
    return p;
  },

  breaker(x, y, etiqueta) {
    const g = svgEl('g', {});
    g.appendChild(svgEl('rect', { x: x - 9, y: y - 12, width: 18, height: 24, fill: '#fff', stroke: this.NEGRO, 'stroke-width': 1.8 }));
    g.appendChild(svgEl('line', { x1: x - 6, y1: y + 8, x2: x + 6, y2: y - 8, stroke: this.NEGRO, 'stroke-width': 1.8 }));
    if (etiqueta) g.appendChild(svgEl('text', { x: x + 14, y: y + 4, 'font-size': 10, fill: this.NEGRO, 'font-weight': 600 }, etiqueta));
    this.svg.appendChild(g);
    return g;
  },

  motor(x, y, nombre, hp, vfd) {
    const g = svgEl('g', { class: 'clicable' });
    if (vfd) {
      g.appendChild(svgEl('rect', { x: x - 18, y: y - 58, width: 36, height: 24, fill: '#fff', stroke: this.NEGRO, 'stroke-width': 1.6 }));
      g.appendChild(svgEl('text', { x, y: y - 42, 'font-size': 8.5, 'text-anchor': 'middle', 'font-weight': 700, fill: this.NEGRO }, vfd));
      g.appendChild(svgEl('line', { x1: x, y1: y - 34, x2: x, y2: y - 22, stroke: this.ROJO, 'stroke-width': 2 }));
    }
    g.appendChild(svgEl('circle', { cx: x, cy: y, r: 22, fill: '#fff', stroke: this.NEGRO, 'stroke-width': 2, class: 'cuerpo' }));
    g.appendChild(svgEl('text', { x, y: y - 1, 'font-size': 12, 'text-anchor': 'middle', 'font-weight': 800, fill: this.NEGRO }, 'M'));
    g.appendChild(svgEl('text', { x, y: y + 11, 'font-size': 8, 'text-anchor': 'middle', fill: this.NEGRO }, '3Ø'));
    g.appendChild(svgEl('text', { x, y: y + 40, 'font-size': 9.5, 'text-anchor': 'middle', 'font-weight': 700, fill: this.NEGRO }, nombre));
    g.appendChild(svgEl('text', { x, y: y + 53, 'font-size': 9, 'text-anchor': 'middle', fill: '#b71c1c', 'font-weight': 600 }, hp));
    this.svg.appendChild(g);
    return g;
  },

  fichaClic(g, titulo, sub, filas, tooltip) {
    g.classList.add('clicable');
    g.addEventListener('mouseenter', (e) => mostrarTooltip(e, tooltip || `<b>${titulo}</b><br>${sub || ''}`));
    g.addEventListener('mousemove', moverTooltip);
    g.addEventListener('mouseleave', ocultarTooltip);
    g.addEventListener('click', (e) => { e.stopPropagation(); abrirFichaLibre(titulo, sub, filas); });
  },

  caja(x, y, w, h, lineas, color) {
    const g = svgEl('g', {});
    g.appendChild(svgEl('rect', { x, y, width: w, height: h, fill: '#fff', stroke: color || this.NEGRO, 'stroke-width': 2, rx: 3, class: 'cuerpo' }));
    lineas.forEach((t, i) => {
      g.appendChild(svgEl('text', { x: x + w / 2, y: y + 16 + i * 13, 'font-size': i === 0 ? 10.5 : 9, 'text-anchor': 'middle', 'font-weight': i === 0 ? 700 : 400, fill: this.NEGRO }, t));
    });
    this.svg.appendChild(g);
    return g;
  },

  anilloArco(x, y, info) {
    const g = this.gArco;
    g.appendChild(svgEl('circle', { cx: x, cy: y, r: 70, fill: 'none', stroke: '#fbc02d', 'stroke-width': 2.5, 'stroke-dasharray': '8 5', opacity: 0.9 }));
    g.appendChild(svgEl('circle', { cx: x, cy: y, r: 42, fill: 'none', stroke: '#d32f2f', 'stroke-width': 2.5, 'stroke-dasharray': '5 4', opacity: 0.9 }));
    g.appendChild(svgEl('text', { x, y: y - 76, 'font-size': 9, 'text-anchor': 'middle', fill: '#8d6e00', 'font-weight': 700 }, `Limitada ${info.frontLim || ''}`));
    g.appendChild(svgEl('text', { x, y: y - 48, 'font-size': 9, 'text-anchor': 'middle', fill: '#b71c1c', 'font-weight': 700 }, `Restringida ${info.frontRestr} · ${info.ei}`));
  },

  dibujar() {
    const C = PLANT_DATA.electrico.coordinacion;
    const svg = this.svg;
    const cx = 400;

    // ---------- 1) Acometida y subestación ----------
    const acom = svgEl('g', {});
    acom.appendChild(svgEl('circle', { cx, cy: 50, r: 22, fill: '#fff', stroke: this.NEGRO, 'stroke-width': 2, class: 'cuerpo' }));
    acom.appendChild(svgEl('path', { d: `M ${cx - 9} 56 q 4 -14 9 -6 q 5 8 9 -6`, fill: 'none', stroke: this.NEGRO, 'stroke-width': 1.8 }));
    acom.appendChild(svgEl('text', { x: cx + 35, y: 42, 'font-size': 11, 'font-weight': 700 }, 'RED NATURGY PANAMÁ'));
    acom.appendChild(svgEl('text', { x: cx + 35, y: 56, 'font-size': 10 }, '13.8 kV · 3Ø · 60 Hz'));
    svg.appendChild(acom);
    this.fichaClic(acom, 'Acometida — Red Naturgy Panamá', '13.8 kV, 3Ø, 60 Hz', [
      ['Tensión', '13.8 kV, 3 fases, 60 Hz'],
      ['Acometida MT', 'Subterránea 3×1/0 AWG, 15 kV XLPE'],
      ['Protección', 'Cortacircuitos de expulsión (M.O.V.) + pararrayos 13.8 kV'],
      ['Medición', 'Banco de medición Naturgy: kWh / kW / kVArh (medidor comercial)'],
      ['Norma', 'NEC (NFPA 70) · Código Eléctrico de Panamá'],
    ]);

    this.lnAcometida = this.cable(`M ${cx} 72 V 165`, this.ROJO, 3);
    // cortacircuitos + pararrayos
    const prr = svgEl('g', {});
    prr.appendChild(svgEl('line', { x1: cx - 5, y1: 96, x2: cx + 16, y2: 82, stroke: this.NEGRO, 'stroke-width': 2.2 })); // cuchilla expulsión
    prr.appendChild(svgEl('rect', { x: cx + 28, y: 88, width: 12, height: 26, fill: '#fff', stroke: this.NEGRO, 'stroke-width': 1.6 }));
    prr.appendChild(svgEl('path', { d: `M ${cx + 34} 114 v 12 m -6 0 h 12 m -9 5 h 6 m -4 5 h 2`, stroke: this.VERDE, 'stroke-width': 1.6, fill: 'none' }));
    prr.appendChild(svgEl('line', { x1: cx, y1: 101, x2: cx + 34, y2: 88, stroke: this.ROJO, 'stroke-width': 1.6 }));
    prr.appendChild(svgEl('text', { x: cx + 46, y: 100, 'font-size': 9 }, 'Cortacircuitos M.O.V. + pararrayos 13.8 kV'));
    svg.appendChild(prr);
    this.fichaClic(prr, 'Cortacircuitos de expulsión + Pararrayos', 'Protección de acometida MT', [
      ['Equipo', 'Cortacircuitos de expulsión (M.O.V.) y pararrayos clase distribución 13.8 kV'],
      ['Función', 'Protección contra sobrecorriente y sobretensiones por descargas atmosféricas'],
      ['Puesta a tierra', 'Conectado a malla de tierra ≤ 5 Ω'],
    ]);
    svg.appendChild(svgEl('text', { x: cx - 215, y: 130, 'font-size': 9.5, fill: this.NEGRO }, 'Acometida MT subterránea 3×1/0 AWG · 15 kV XLPE'));

    const med = this.caja(cx + 90, 120, 140, 40, ['MEDICIÓN NATURGY', 'kWh · kW · kVArh']);
    this.cable(`M ${cx} 140 H ${cx + 90}`, this.NEGRO, 1.5, '5 4');
    this.fichaClic(med, 'Banco de medición Naturgy', 'Medidor comercial', [
      ['Medición', 'kWh, kW (demanda), kVArh (reactiva)'],
      ['Ubicación', 'Frontera comercial con Naturgy Panamá'],
    ]);

    // ---------- 2) Transformador ----------
    const tr = svgEl('g', {});
    tr.appendChild(svgEl('circle', { cx, cy: 192, r: 26, fill: '#fff', stroke: this.NEGRO, 'stroke-width': 2.2, class: 'cuerpo' }));
    tr.appendChild(svgEl('circle', { cx, cy: 228, r: 26, fill: '#fff', stroke: this.NEGRO, 'stroke-width': 2.2 }));
    tr.appendChild(svgEl('text', { x: cx, y: 196, 'font-size': 10, 'text-anchor': 'middle', 'font-weight': 700 }, 'Δ'));
    tr.appendChild(svgEl('text', { x: cx, y: 233, 'font-size': 10, 'text-anchor': 'middle', 'font-weight': 700 }, 'Y'));
    tr.appendChild(svgEl('text', { x: cx + 35, y: 205, 'font-size': 11, 'font-weight': 700 }, 'T-1 · 1,500 kVA pad-mounted'));
    tr.appendChild(svgEl('text', { x: cx + 35, y: 220, 'font-size': 10 }, '13.8 kV Δ – 480Y/277 V · 3Ø · 60 Hz'));
    svg.appendChild(tr);
    this.fichaClic(tr, 'Transformador principal T-1', '1,500 kVA pad-mounted', [
      ['Potencia', '1,500 kVA'],
      ['Relación', '13.8 kV Δ (primario) – 480Y/277 V (secundario), 3Ø, 60 Hz'],
      ['Tipo', 'Pad-mounted, frente muerto, en aceite mineral'],
      ['Corriente secundaria', 'I = 1,500,000 / (√3 × 480) ≈ 1,804 A'],
      ['Puesta a tierra', 'Neutro corrido — sistema 480Y/277 V sólidamente aterrizado, ≤ 5 Ω'],
    ]);

    this.lnTrafoMain = this.cable(`M ${cx} 254 V 300`, this.ROJO, 3.5);
    const mainG = svgEl('g', {});
    svg.appendChild(mainG);
    this.breaker(cx, 315, 'MAIN 1600 A · 65 kAIC');
    const mainHit = svgEl('rect', { x: cx - 16, y: 298, width: 200, height: 34, fill: 'transparent' });
    svg.appendChild(mainHit);
    this.fichaClic(mainHit, 'Main Breaker — Edificio C', '1600 A · 65 kAIC · 480 V', [
      ['Tensión / corriente', '480Y/277 V · 1600 A'],
      ['Capacidad interruptiva', C.main.kaic],
      ['⚡ Energía incidente (NFPA 70E)', `${C.main.ei} — frontera restringida ${C.main.frontRestr}`, 'volt'],
      ['EPP requerido', PLANT_DATA.electrico.epp],
      ['Coordinación', 'Selectividad total con ATS, MCC-A y MCC-B (NEC 700 / IEC 60947)'],
    ]);

    // ---------- Generación AES + ATS ----------
    const gen = svgEl('g', {});
    gen.appendChild(svgEl('circle', { cx: 700, cy: 165, r: 30, fill: '#fff', stroke: this.NEGRO, 'stroke-width': 2.2, class: 'cuerpo' }));
    gen.appendChild(svgEl('text', { x: 700, y: 171, 'font-size': 16, 'text-anchor': 'middle', 'font-weight': 800 }, 'G'));
    gen.appendChild(svgEl('text', { x: 740, y: 152, 'font-size': 11, 'font-weight': 700 }, 'GENERADOR AES — GAS NATURAL'));
    gen.appendChild(svgEl('text', { x: 740, y: 167, 'font-size': 10 }, '1,500 kW · 480 V · 3Ø · 60 Hz'));
    gen.appendChild(svgEl('text', { x: 740, y: 181, 'font-size': 9, fill: '#555' }, 'Con sistema de escape y post-tratamiento'));
    svg.appendChild(gen);
    this.fichaClic(gen, 'Generador de respaldo (tecnología AES)', '1,500 kW · gas natural', [
      ['Potencia', '1,500 kW (standby) · 480 V, 3Ø, 60 Hz'],
      ['Combustible', 'Gas natural — tecnología AES'],
      ['Emisiones', 'Sistema de escape y post-tratamiento'],
      ['Transferencia', 'ATS 1600 A, 3P automático (NEC 700/701/702)'],
    ]);
    this.lnGen = this.cable('M 700 195 V 300 H 540', this.ROJO, 3);

    const ats = this.caja(440, 285, 100, 50, ['ATS', '1600 A · 3P']);
    this.fichaClic(ats, 'ATS — Transferencia automática', '1600 A, 3P · 85 kAIC', [
      ['Capacidad', '1600 A, 3 polos · transición abierta'],
      ['Capacidad interruptiva', C.ats.kaic],
      ['⚡ Energía incidente (NFPA 70E)', `${C.ats.ei} — frontera restringida ${C.ats.frontRestr}`, 'volt'],
      ['EPP requerido', PLANT_DATA.electrico.epp],
      ['Fuentes', 'Normal: T-1 1,500 kVA · Emergencia: Generador AES 1,500 kW'],
    ]);
    this.cable(`M ${cx} 332 V 360 H 470 M 470 360 V 335`, this.ROJO, 3); // main → ATS normal (gráfico)
    this.lnAtsOut = this.cable('M 490 335 V 410', this.ROJO, 4);

    // ---------- Bus principal 480 V ----------
    this.busMain = svgEl('line', { x1: 90, y1: 410, x2: 1310, y2: 410, stroke: this.ROJO, 'stroke-width': 7 });
    svg.appendChild(this.busMain);
    svg.appendChild(svgEl('text', { x: 95, y: 400, 'font-size': 11.5, 'font-weight': 700, fill: this.ROJO }, 'BUS PRINCIPAL 480Y/277 V · 3Ø · 4W · 60 Hz — Edificio C'));

    // ---------- 4) Calidad de energía ----------
    // capacitores
    const cap = svgEl('g', {});
    this.cable('M 140 410 V 470', this.ROJO, 2.5);
    cap.appendChild(svgEl('line', { x1: 122, y1: 470, x2: 158, y2: 470, stroke: this.NEGRO, 'stroke-width': 2.5 }));
    cap.appendChild(svgEl('line', { x1: 122, y1: 480, x2: 158, y2: 480, stroke: this.NEGRO, 'stroke-width': 2.5 }));
    cap.appendChild(svgEl('line', { x1: 140, y1: 480, x2: 140, y2: 495, stroke: this.VERDE, 'stroke-width': 2 }));
    cap.appendChild(svgEl('text', { x: 140, y: 515, 'font-size': 9.5, 'text-anchor': 'middle', 'font-weight': 600 }, 'CAPACITORES'));
    cap.appendChild(svgEl('text', { x: 140, y: 528, 'font-size': 9, 'text-anchor': 'middle' }, '600 kVAr · 480 V'));
    svg.appendChild(cap);
    this.fichaClic(cap, 'Banco de capacitores automático', '600 kVAr · 480 V', [
      ['Función', 'Corrección del factor de potencia: 0.82 → 0.96 (IEEE 519)'],
      ['Control', 'Banco automático por pasos con controlador de FP'],
    ]);

    // UPS
    const ups = this.caja(210, 455, 110, 48, ['UPS INDUSTRIAL', '100 kVA · 480→120 V']);
    this.cable('M 265 410 V 455', this.ROJO, 2.5);
    this.fichaClic(ups, 'UPS industrial para PLC/DCS', '100 kVA (480 V → 120 V)', [
      ['Función', 'Respaldo de energía crítica para control de procesos PLC/DCS'],
      ['Salida', 'Tablero UPS de distribución crítica 120 V, 1Ø'],
    ]);
    const tups = this.caja(210, 540, 110, 42, ['TABLERO UPS', '120 V · 1Ø crítico']);
    this.cable('M 265 503 V 540', this.AZUL, 2.5);
    this.fichaClic(tups, 'Tablero UPS — distribución crítica', '120 V, 1Ø', [
      ['Cargas', 'PLC/DCS, instrumentación crítica, servidores de planta'],
    ]);

    // PLC/DCS
    const plc = this.caja(350, 455, 110, 48, ['PLC / DCS', 'Control de procesos', '480 V · 3Ø']);
    this.cable('M 405 410 V 455', this.ROJO, 2.5);
    this.cable('M 405 503 V 530 H 1000 V 503', this.NEGRO, 1.4, '6 4'); // control/comunicaciones
    svg.appendChild(svgEl('text', { x: 600, y: 545, 'font-size': 8.5, fill: this.NEGRO }, 'Control / comunicaciones Cat 6A · fibra (negro discontinuo)'));
    this.fichaClic(plc, 'Tablero de control de procesos PLC/DCS', '480 V, 3Ø', [
      ['Función', 'Control central de proceso (torre, mezclas, envasado) — respaldado por UPS'],
      ['Red', 'Cat 6A / fibra óptica hacia MCC-A y MCC-B'],
    ]);

    // AHF
    const ahf = this.caja(490, 455, 120, 48, ['AHF-01 · AHF-02', 'Filtros activos 300 A']);
    this.cable('M 550 410 V 455', this.ROJO, 2.5);
    this.fichaClic(ahf, 'Filtros activos de armónicos AHF-01 / AHF-02', '300 A c/u · 480 V', [
      ['Resultado Nave A', 'THDv 18.7 % → 3.2 % (IEEE 519)', 'volt'],
      ['Resultado Nave B', 'THDv 15.3 % → 2.9 % (IEEE 519)', 'volt'],
      ['Factor de potencia', '0.82 → 0.96 con banco de capacitores'],
      ['Causa', 'Armónicos generados por VFDs (rectificadores de 6 pulsos)'],
    ]);

    // ---------- 5) MCC-A ----------
    this.lnMccA = this.cable('M 790 410 V 470', this.ROJO, 4);
    this.breaker(790, 445, '1600 A');
    this.busA = svgEl('line', { x1: 660, y1: 490, x2: 1000, y2: 490, stroke: this.ROJO, 'stroke-width': 5.5 });
    svg.appendChild(this.busA);
    const etA = svgEl('text', { x: 660, y: 480, 'font-size': 11, 'font-weight': 700, fill: this.NEGRO }, 'MCC-A — NAVE A · 1600 A · 480 V · 3Ø · 65 kAIC');
    svg.appendChild(etA);
    const hitA = svgEl('rect', { x: 655, y: 460, width: 350, height: 40, fill: 'transparent' });
    svg.appendChild(hitA);
    this.fichaClic(hitA, 'MCC-A — Centro de Carga 1 (Nave A)', '1600 A · 480 V · 3Ø', [
      ['Capacidad', '1600 A · 65 kAIC'],
      ['⚡ Energía incidente (NFPA 70E)', `${C.mccA.ei} — frontera restringida ${C.mccA.frontRestr}`, 'volt'],
      ['EPP requerido', PLANT_DATA.electrico.epp],
      ['Cargas', 'M-101 75 HP · P-101 50 HP · P-102 50 HP · EF-101 150 HP + equipos de proceso'],
      ['VFDs', 'VFD-101 (mezclador) · VFD-102 (bomba) · VFD-103 (ventilador)'],
    ]);

    const motoresA = [
      [690, 'M-101', '75 HP', 'VFD-101', 'Mezclador del tanque TK-101', 'tk101'],
      [770, 'P-101', '50 HP', 'VFD-102', 'Bomba alta presión principal', 'p101'],
      [850, 'P-102', '50 HP', null, 'Bomba alta presión de reserva', 'p102'],
      [935, 'EF-101', '150 HP', 'VFD-103', 'Ventilador de tiro inducido de la torre', 'torre'],
    ];
    this.motoresA = [];
    for (const [x, nom, hp, vfd, desc, eq] of motoresA) {
      const ln = this.cable(`M ${x} 490 V ${vfd ? 532 : 568}`, this.ROJO, 2.2);
      const g = this.motor(x, 612, nom, hp + ' · 480 V 3Ø', vfd);
      this.fichaClic(g, `${nom} — ${desc}`, `${hp} · 480 V, 3Ø, 60 Hz — MCC-A${vfd ? ' (' + vfd + ')' : ''}`, [
        ['Alimentación', `480 V, 3Ø, 60 Hz desde MCC-A — ${hp}`, 'volt'],
        ['Arranque', vfd ? `Variador de frecuencia ${vfd}` : 'Arrancador directo con relé de sobrecarga'],
        ['Protección', 'Breaker de motor + relé térmico (NEC 430)'],
        ['Equipo accionado', desc + ' — ver ficha del equipo en el Plano 2D/3D'],
      ]);
      this.motoresA.push(ln);
    }

    // ---------- 6) MCC-B ----------
    this.lnMccB = this.cable('M 1140 410 V 470', this.ROJO, 4);
    this.breaker(1140, 445, '800 A frame');
    this.busB = svgEl('line', { x1: 1030, y1: 490, x2: 1340, y2: 490, stroke: this.ROJO, 'stroke-width': 5 });
    svg.appendChild(this.busB);
    svg.appendChild(svgEl('text', { x: 1030, y: 480, 'font-size': 11, 'font-weight': 700, fill: this.NEGRO }, 'MCC-B — NAVE B · 600 A nom / 800 A frame · 35 kAIC'));
    const hitB = svgEl('rect', { x: 1025, y: 460, width: 320, height: 40, fill: 'transparent' });
    svg.appendChild(hitB);
    this.fichaClic(hitB, 'MCC-B — Centro de Carga 2 (Nave B)', '600 A nominal / 800 A frame · 480 V · 3Ø', [
      ['Capacidad', '600 A nominal / 800 A frame · 35 kAIC'],
      ['⚡ Energía incidente (NFPA 70E)', `${C.mccB.ei} — frontera restringida ${C.mccB.frontRestr}`, 'volt'],
      ['EPP requerido', PLANT_DATA.electrico.epp],
      ['Cargas', 'VFFS 75 HP · Ensacadora 75 HP · BC-101/BC-102 10 HP c/u · Paletizador 75 HP'],
      ['VFDs', 'VFD-201 a VFD-204'],
      ['Selectividad', 'Falla en ensacadora Mod. B activa solo el breaker local (75 A, 18 kAIC) sin afectar niveles superiores — coordinación NEC 700 / IEC 60947'],
    ]);

    const motoresB = [
      [1060, 'VFFS A', '75 HP', 'VFD-201', 'Envasadora VFFS ROVEMA BVC 600 (Módulo A)', 'vffs'],
      [1135, 'ENSAC B', '75 HP', 'VFD-202', 'Ensacadora HAVER & BOECKER INTEGRA® IV (Módulo B) — breaker local 75 A, 18 kAIC', 'ensacadora'],
      [1210, 'BC-101', '10 HP', 'VFD-203', 'Banda transportadora BC-101', 'bc101'],
      [1280, 'BC-102', '10 HP', 'VFD-204', 'Banda transportadora BC-102', 'bc102'],
      [1350, 'ROBOT', '75 HP', null, 'Paletizador robot', 'paletizador'],
    ];
    this.motoresB = [];
    for (const [x, nom, hp, vfd, desc] of motoresB) {
      const ln = this.cable(`M ${x} 490 V ${vfd ? 532 : 568}`, this.ROJO, 2.2);
      if (x === 1350) this.cable('M 1340 490 H 1350', this.ROJO, 5);
      const g = this.motor(x, 612, nom, hp + ' · 480 V 3Ø', vfd);
      this.fichaClic(g, `${nom} — ${desc.split(' — ')[0]}`, `${hp} · 480 V, 3Ø, 60 Hz — MCC-B${vfd ? ' (' + vfd + ')' : ''}`, [
        ['Alimentación', `480 V, 3Ø, 60 Hz desde MCC-B — ${hp}`, 'volt'],
        ['Arranque', vfd ? `Variador de frecuencia ${vfd}` : 'Arrancador directo'],
        ['Protección', nom === 'ENSAC B' ? 'Breaker local 75 A · 18 kAIC — selectividad: una falla aquí NO afecta niveles superiores (NEC 700 / IEC 60947)' : 'Breaker de motor + relé térmico (NEC 430)'],
        ['Equipo accionado', desc],
      ]);
      this.motoresB.push(ln);
    }
    this.etiqMccB = svgEl('text', { x: 1185, y: 700, 'font-size': 10.5, 'text-anchor': 'middle', 'font-weight': 700, fill: '#9e9e9e' }, '');
    svg.appendChild(this.etiqMccB);

    // ---------- 7) Baja tensión Edificios D y E ----------
    this.cable('M 180 410 V 760', this.ROJO, 2.5);
    this.breaker(180, 740, '400 A');
    const pdD = this.caja(120, 760, 120, 46, ['PD-D · 400 A', '480Y/277 V · 3Ø · 4W', 'Edificio D']);
    this.fichaClic(pdD, 'Panel PD-D — Edificio D (Operativo)', '480Y/277 V, 3Ø, 4W, 400 A', [
      ['Alimenta', 'Laboratorio QC, comedor, baños/lockers, taller de mantenimiento'],
      ['Derivados', 'TLD iluminación 277 V (225 A) · TTD tomacorrientes 120/208 V (225 A)'],
    ]);
    this.cable('M 330 410 V 760', this.ROJO, 2.5);
    this.breaker(330, 740, '400 A');
    const pdE = this.caja(270, 760, 120, 46, ['PD-E · 400 A', '480Y/277 V · 3Ø · 4W', 'Edificio E']);
    this.fichaClic(pdE, 'Panel PD-E — Edificio E (Corporativo)', '480Y/277 V, 3Ø, 4W, 400 A', [
      ['Alimenta', 'Recepción, oficinas corporativas, sala de juntas'],
      ['Derivados', 'TLD iluminación 277 V (225 A) · TTD tomacorrientes 120/208 V (225 A)'],
    ]);

    const tld = this.caja(95, 850, 80, 40, ['TLD', '277 V · 225 A']);
    this.cable('M 150 806 V 850 H 135', this.ROJO, 2);
    this.fichaClic(tld, 'Tablero de iluminación TLD', '277 V, 1Ø, 225 A', [['Cargas', 'Iluminación LED industrial high-bay y exterior 277 V']]);
    const ttd = this.caja(190, 850, 90, 40, ['TTD', '120/208 V · 225 A']);
    this.cable('M 210 806 V 850 H 235', this.AZUL, 2);
    this.fichaClic(ttd, 'Tablero de tomacorrientes TTD', '120/208 V, 1Ø, 225 A', [
      ['Transformación', '480 V → 120/208 V vía transformador seco'],
      ['Cargas', 'Tomacorrientes de uso general y equipos 120 V (checkweigher, detector de metales)'],
    ]);

    // ---------- Circuito típico 120 V ----------
    svg.appendChild(svgEl('rect', { x: 90, y: 930, width: 560, height: 210, fill: '#fff', stroke: this.NEGRO, 'stroke-width': 1.5, 'stroke-dasharray': '8 5' }));
    svg.appendChild(svgEl('text', { x: 105, y: 952, 'font-size': 11.5, 'font-weight': 700 }, 'CIRCUITO TÍPICO 120 V (desde TTD)'));
    const itm = svgEl('g', {});
    svg.appendChild(itm);
    this.cable('M 235 890 V 1000 H 150', this.AZUL, 2);
    this.breaker(150, 1000, 'ITM 15 A · 1P');
    const itmHit = svgEl('rect', { x: 130, y: 985, width: 140, height: 30, fill: 'transparent' });
    svg.appendChild(itmHit);
    this.fichaClic(itmHit, 'ITM 15 A, 1 polo', 'Interruptor termomagnético de circuito ramal', [
      ['Protección', '15 A, 1P, 10 kAIC — circuito ramal 120 V (NEC 210)'],
    ]);
    this.cable('M 159 1000 H 320', this.AZUL, 2);
    svg.appendChild(svgEl('text', { x: 175, y: 990, 'font-size': 9 }, 'Conduit EMT Ø3/4" · THHN F+N+T 12 AWG'));
    // dúplex y GFCI
    const dup = svgEl('g', {});
    dup.appendChild(svgEl('circle', { cx: 350, cy: 1000, r: 16, fill: '#fff', stroke: this.NEGRO, 'stroke-width': 1.8, class: 'cuerpo' }));
    dup.appendChild(svgEl('line', { x1: 344, y1: 994, x2: 344, y2: 1006, stroke: this.NEGRO, 'stroke-width': 2 }));
    dup.appendChild(svgEl('line', { x1: 356, y1: 994, x2: 356, y2: 1006, stroke: this.NEGRO, 'stroke-width': 2 }));
    dup.appendChild(svgEl('text', { x: 350, y: 1032, 'font-size': 9, 'text-anchor': 'middle' }, 'Dúplex 120 V'));
    svg.appendChild(dup);
    this.fichaClic(dup, 'Tomacorriente dúplex 120 V', 'NEMA 5-15R', [['Circuito', 'ITM 15 A · THHN 12 AWG · EMT Ø3/4"']]);
    this.cable('M 366 1000 H 430', this.AZUL, 2);
    const gfci = svgEl('g', {});
    gfci.appendChild(svgEl('circle', { cx: 460, cy: 1000, r: 16, fill: '#fff', stroke: this.NEGRO, 'stroke-width': 1.8, class: 'cuerpo' }));
    gfci.appendChild(svgEl('text', { x: 460, y: 1004, 'font-size': 7.5, 'text-anchor': 'middle', 'font-weight': 700 }, 'GFCI'));
    gfci.appendChild(svgEl('text', { x: 460, y: 1032, 'font-size': 9, 'text-anchor': 'middle' }, 'GFCI 120 V'));
    svg.appendChild(gfci);
    this.fichaClic(gfci, 'Tomacorriente GFCI 120 V', 'Protección de falla a tierra (NEC 210.8)', [
      ['Aplicación', 'Áreas húmedas: baños, exteriores, laboratorio QC'],
    ]);
    // tierra
    const gnd = svgEl('g', {});
    gnd.appendChild(svgEl('path', { d: 'M 555 1000 V 1050 m -18 0 h 36 m -27 8 h 18 m -13 8 h 8', stroke: this.VERDE, 'stroke-width': 2.2, fill: 'none' }));
    gnd.appendChild(svgEl('text', { x: 555, y: 1085, 'font-size': 9, 'text-anchor': 'middle', fill: this.VERDE, 'font-weight': 600 }, 'Varilla Copperweld 5/8" × 2.40 m'));
    gnd.appendChild(svgEl('text', { x: 555, y: 1098, 'font-size': 9, 'text-anchor': 'middle', fill: this.VERDE }, 'Puesta a tierra ≤ 5 Ω'));
    svg.appendChild(gnd);
    this.cable('M 476 1000 H 555', this.VERDE, 2);
    this.fichaClic(gnd, 'Sistema de puesta a tierra', 'Varilla Copperweld 5/8" × 2.40 m', [
      ['Resistencia', '≤ 5 ohmios (medida con telurómetro)'],
      ['Conductor', 'Cobre desnudo + THHN verde (NEC 250)'],
    ]);

    // ---------- Notas generales ----------
    const notas = svgEl('g', {});
    notas.appendChild(svgEl('rect', { x: 700, y: 930, width: 640, height: 300, fill: '#fff', stroke: this.NEGRO, 'stroke-width': 2 }));
    const lineasNotas = [
      'NOTAS GENERALES (NEC 2023 / NFPA 70 / NFPA 70E / IEEE 519):',
      '1. Cumplimiento del NEC (NFPA 70) y del Código Eléctrico de Panamá (RIE).',
      '2. Conductores de cobre THHN/THWN, 600 V, 75 °C mínimo.',
      '3. Bandejas portacables tipo escalerilla calibre 14, galvanizadas en caliente.',
      '4. Sistema de puesta a tierra con resistencia ≤ 5 ohmios.',
      '5. Distancias de trabajo y alturas de montaje según NEC 110.',
      '6. Seguridad NFPA 70E — energías incidentes:',
      '    · Main Breaker Edif. C: 5.8 cal/cm² (frontera restringida 1.52 m)',
      '    · ATS: 4.1 cal/cm² (1.37 m) · MCC-A: 3.2 cal/cm² (1.22 m) · MCC-B: 2.0 cal/cm² (1.07 m)',
      '    · EPP Categoría 2 (ATPV 8.0 cal/cm²) para trabajos energizados.',
      '7. Selectividad: falla en ensacadora Mod. B activa solo el breaker local',
      '    (75 HP, 18 kAIC) sin afectar niveles superiores (NEC 700 / IEC 60947).',
      '8. Colores: ROJO = fuerza 480 V 3Ø · AZUL = corriente/retorno 120/208 V ·',
      '    NEGRO discontinuo = control (Cat 6A/fibra) · VERDE = puesta a tierra.',
      'Plano: ELEC-REF-001 · REFRESH S.A. · Junio 2026 · Escala N.T.S.',
    ];
    lineasNotas.forEach((t, i) => {
      notas.appendChild(svgEl('text', { x: 715, y: 956 + i * 17.5, 'font-size': i === 0 ? 11 : 9.8, 'font-weight': i === 0 || i === lineasNotas.length - 1 ? 700 : 400 }, t));
    });
    svg.appendChild(notas);

    // ---------- Capa: fronteras de arco ----------
    this.gArco = svgEl('g', { style: 'display:none' });
    this.anilloArco(cx, 315, C.main);
    this.anilloArco(490, 310, C.ats);
    this.anilloArco(790, 470, C.mccA);
    this.anilloArco(1140, 470, C.mccB);
    svg.appendChild(this.gArco);
  },

  // Capa "Estado energizado": en mantenimiento del miércoles MCC-B queda en gris
  actualizarEnergizado() {
    if (!this.inicializado) return;
    const vivo = this.energizadoVisible;
    const mccBOff = Sim.enMantenimiento;
    const colB = !vivo ? this.ROJO : mccBOff ? '#9e9e9e' : this.ROJO;
    const brillo = vivo && Sim.corriendo;
    [this.lnMccB, this.busB, ...this.motoresB].forEach((el) => el.setAttribute('stroke', colB));
    [this.busMain, this.busA, this.lnMccA, this.lnAtsOut].forEach((el) => {
      el.setAttribute('stroke', this.ROJO);
      el.setAttribute('filter', brillo ? 'drop-shadow(0 0 4px rgba(198,40,40,0.9))' : '');
    });
    this.busB.setAttribute('filter', brillo && !mccBOff ? 'drop-shadow(0 0 4px rgba(198,40,40,0.9))' : '');
    this.etiqMccB.textContent = mccBOff ? '⚠ MCC-B DESENERGIZADO — MANTENIMIENTO DEL MIÉRCOLES (la torre en MCC-A sigue viva)' : '';
    const est = document.getElementById('estadoMccUni');
    if (est) {
      est.innerHTML = mccBOff
        ? '<span style="color:#b71c1c">MCC-B desenergizado (mantenimiento) · MCC-A vivo — torre 24/7</span>'
        : `<span style="color:#2e7d32">MCC-A y MCC-B energizados</span> · ${Sim.corriendo ? 'simulación en curso' : 'simulación pausada'}`;
    }
  },
};
