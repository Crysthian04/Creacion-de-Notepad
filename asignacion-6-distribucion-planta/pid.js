/* ============================================================
   Pestaña 3 — P&ID REF-PRC-PID-001 (SVG)
   Norma ISA-5.1 / ISO 10628 / DIN 28000
   ============================================================ */

const PID = {
  inicializado: false,

  // Estilos de línea por tipo de fluido (leyenda)
  ESTILOS: {
    vapor:    { stroke: '#d32f2f', w: 3,   dash: '',     nombre: 'Vapor 8 barg · 185 °C' },
    cond:     { stroke: '#d32f2f', w: 1.5, dash: '8 4',  nombre: 'Condensado / retorno' },
    aire:     { stroke: '#00acc1', w: 2.5, dash: '',     nombre: 'Aire comprimido 7 barg' },
    aguadi:   { stroke: '#1565c0', w: 2.5, dash: '',     nombre: 'Agua desmineralizada (RO+EDI)' },
    proceso:  { stroke: '#2e7d32', w: 4,   dash: '',     nombre: 'Pasta húmeda (proceso) 100–250 bar' },
    retorno:  { stroke: '#7b1fa2', w: 2.5, dash: '10 5', nombre: 'Retorno / recirculación' },
    dren:     { stroke: '#757575', w: 1.5, dash: '4 4',  nombre: 'Drenajes / condensados' },
    caliente: { stroke: '#ef6c00', w: 4,   dash: '',     nombre: 'Aire caliente de secado' },
  },

  // Base de datos de instrumentos (ISA-5.1)
  INSTR: {
    'PT-101': ['Transmisor de presión', 'Vapor saturado', '0–16 barg (operación 8 barg)', 'Supervisa presión de la línea de vapor desde S-1'],
    'PI-101': ['Indicador de presión (manómetro local)', 'Vapor', '0–16 barg', 'Indicación local en campo'],
    'XV-101': ['Válvula on/off automatizada', 'Vapor', 'Todo/nada', 'Aislamiento de la línea de vapor'],
    'ST-101': ['Trampa de vapor (termodinámica)', 'Condensado', '8 barg', 'Purga de condensado y retorno al sistema'],
    'TT-101': ['Transmisor de temperatura', 'Aire caliente de secado', '0–350 °C', 'Mide temperatura del aire al ingreso de la torre'],
    'TC-101': ['Controlador de temperatura', 'Aire caliente', 'SP 200–300 °C', 'Modula XV-102 para controlar temperatura (lazo TT→TC→XV)'],
    'XV-102': ['Válvula de control con actuador neumático', 'Vapor a intercambiador', '0–100 %', 'Elemento final del lazo de temperatura'],
    'PT-201': ['Transmisor de presión', 'Aire comprimido', '0–12 barg (operación 7 barg)', 'Supervisión del anillo de aire'],
    'PI-201': ['Indicador de presión local', 'Aire comprimido', '0–12 barg', 'Indicación en sala de compresores'],
    'F-201':  ['Filtro coalescente', 'Aire comprimido', '7 barg', 'Retira aceite/partículas del aire de instrumentos'],
    'PT-301': ['Transmisor de presión', 'Agua desmineralizada', '0–10 barg', 'Supervisión de la red de agua DI'],
    'PI-301': ['Indicador de presión local', 'Agua DI', '0–10 barg', 'Indicación local'],
    'F-301':  ['Filtro de pulido', 'Agua DI', '5 µm', 'Protección de tanques de mezcla y CIP'],
    'FT-301': ['Transmisor de flujo', 'Agua DI a CIP', '0–20 m³/h', 'Totaliza agua de limpieza CIP de la torre'],
    'XV-302': ['Válvula on/off CIP', 'Agua DI', 'Todo/nada', 'Habilita ciclo CIP de la torre de secado'],
    'LT-101': ['Transmisor de nivel (radar)', 'Slurry TK-101', '0–100 % (10,000 L)', 'Nivel del tanque de Mezcla 1'],
    'LT-102': ['Transmisor de nivel (radar)', 'Slurry TK-102', '0–100 % (10,000 L)', 'Nivel del tanque de Mezcla 2'],
    'PT-401': ['Transmisor de presión', 'Pasta húmeda alta presión', '0–300 bar (operación 100–250 bar)', 'Protección y control de la línea de atomización'],
    'FT-402': ['Transmisor de flujo másico (Coriolis)', 'Pasta húmeda', '0–2,000 kg/h', 'Mide la alimentación real a la torre — variable del slider de simulación'],
    'PCV-401': ['Válvula de control de presión (actuador neumático)', 'Pasta húmeda', '100–250 bar', 'Mantiene presión constante en la boquilla atomizadora'],
    'FCV-402': ['Válvula de control de flujo (actuador neumático)', 'Recirculación de pasta', '0–100 %', 'Recircula el exceso de slurry cuando se supera el límite de la torre (1,500 kg/h)'],
    'FIT-402': ['Indicador-transmisor de flujo', 'Recirculación', '0–1,000 kg/h', 'Mide el caudal recirculado a TK-101/TK-102'],
    'XV-201': ['Válvula de pulso (aire)', 'Limpieza ciclón 1', 'Pulsos 7 barg', 'Descarga de polvo del ciclón 1'],
    'XV-202': ['Válvula de pulso (aire)', 'Limpieza ciclón 2', 'Pulsos 7 barg', 'Descarga de polvo del ciclón 2'],
    'PI-202': ['Indicador de presión diferencial', 'Ciclón 1', '0–50 mbar', 'Supervisa pérdida de carga del ciclón 1'],
    'PI-203': ['Indicador de presión diferencial', 'Ciclón 2', '0–50 mbar', 'Supervisa pérdida de carga del ciclón 2'],
  },

  init() {
    if (this.inicializado) return;
    this.inicializado = true;
    const cont = document.getElementById('vistaPid');

    const tb = document.createElement('div');
    tb.className = 'toolbar';
    tb.innerHTML = `
      <button id="btnAjustarPid">⤢ Ajustar vista</button>
      <label class="toggle" id="tgAnimPid">≈ Animación de flujo</label>`;
    cont.appendChild(tb);

    const svg = svgEl('svg', { class: 'lienzo-svg' });
    cont.appendChild(svg);
    this.svg = svg;
    this.lineas = [];
    this.panZoom = instalarPanZoom(svg, { x: 0, y: 0, w: 1520, h: 980 });
    document.getElementById('btnAjustarPid').onclick = () => this.panZoom.ajustar();
    document.getElementById('tgAnimPid').onclick = (e) => {
      e.currentTarget.classList.toggle('on');
      this.animar(e.currentTarget.classList.contains('on'));
    };

    this.dibujar();
    Bus.on('tick', () => {
      if (this.nodoTorre) this.nodoTorre.classList.toggle('alerta-parpadeo', !!Sim.alertas.torre);
    });
  },

  linea(d, tipo, etiqueta, ex, ey) {
    const s = this.ESTILOS[tipo];
    const p = svgEl('path', { d, fill: 'none', stroke: s.stroke, 'stroke-width': s.w, 'stroke-dasharray': s.dash, 'marker-end': 'url(#flechaPid)' });
    this.svg.appendChild(p);
    this.lineas.push({ p, dash: s.dash });
    if (etiqueta) this.svg.appendChild(svgEl('text', { x: ex, y: ey, 'font-size': 11, fill: s.stroke, 'font-weight': 600 }, etiqueta));
    return p;
  },

  // Instrumento ISA-5.1: círculo con tag (montado en campo = sin línea interna)
  instr(x, y, tag) {
    const g = svgEl('g', { class: 'clicable' });
    const [letras, num] = tag.split('-');
    g.appendChild(svgEl('circle', { cx: x, cy: y, r: 17, fill: '#fff', stroke: '#1a3a5c', 'stroke-width': 1.6 }));
    g.appendChild(svgEl('line', { x1: x - 17, y1: y, x2: x + 17, y2: y, stroke: '#1a3a5c', 'stroke-width': 0.8 }));
    g.appendChild(svgEl('text', { x, y: y - 4, 'font-size': 10.5, 'text-anchor': 'middle', 'font-weight': 700, fill: '#1a3a5c' }, letras));
    g.appendChild(svgEl('text', { x, y: y + 12, 'font-size': 10.5, 'text-anchor': 'middle', fill: '#1a3a5c' }, num));
    const d = this.INSTR[tag];
    g.addEventListener('mouseenter', (e) => mostrarTooltip(e, `<b>${tag}</b> — ${d ? d[0] : ''}<br>${d ? d[1] : ''}`));
    g.addEventListener('mousemove', moverTooltip);
    g.addEventListener('mouseleave', ocultarTooltip);
    g.addEventListener('click', (e) => {
      e.stopPropagation();
      abrirFichaLibre(tag + ' — ' + (d ? d[0] : 'Instrumento'), 'P&ID REF-PRC-PID-001', [
        ['Tag (ISA-5.1)', tag],
        ['Variable medida / servicio', d ? d[1] : '—'],
        ['Rango típico', d ? d[2] : '—'],
        ['Función', d ? d[3] : '—'],
        ['Norma de simbología', 'ISA-5.1 (identificación y símbolos de instrumentación) · ISO 10628 / DIN 28000 (diagramas de flujo de plantas de proceso)'],
      ]);
    });
    this.svg.appendChild(g);
    return g;
  },

  // Válvula (bowtie); tipo: bola | globo | check | control (con actuador) | pulso
  valvula(x, y, tipo, tag) {
    const g = svgEl('g', { class: tag ? 'clicable' : '' });
    g.appendChild(svgEl('path', { d: `M ${x - 11} ${y - 8} L ${x + 11} ${y + 8} L ${x + 11} ${y - 8} L ${x - 11} ${y + 8} Z`, fill: tipo === 'check' ? '#1a3a5c' : '#fff', stroke: '#1a3a5c', 'stroke-width': 1.6 }));
    if (tipo === 'bola') g.appendChild(svgEl('circle', { cx: x, cy: y, r: 3.5, fill: '#1a3a5c' }));
    if (tipo === 'globo') g.appendChild(svgEl('circle', { cx: x, cy: y, r: 3.5, fill: '#fff', stroke: '#1a3a5c', 'stroke-width': 1.4 }));
    if (tipo === 'control' || tipo === 'pulso') {
      g.appendChild(svgEl('line', { x1: x, y1: y, x2: x, y2: y - 16, stroke: '#1a3a5c', 'stroke-width': 1.4 }));
      g.appendChild(svgEl('path', { d: `M ${x - 10} ${y - 16} A 10 10 0 0 1 ${x + 10} ${y - 16} Z`, fill: '#fff', stroke: '#1a3a5c', 'stroke-width': 1.4 })); // actuador neumático
    }
    if (tag) {
      const d = this.INSTR[tag];
      g.addEventListener('mouseenter', (e) => mostrarTooltip(e, `<b>${tag}</b> — ${d ? d[0] : 'Válvula'}`));
      g.addEventListener('mousemove', moverTooltip);
      g.addEventListener('mouseleave', ocultarTooltip);
      g.addEventListener('click', (e) => {
        e.stopPropagation();
        abrirFichaLibre(tag + ' — ' + (d ? d[0] : 'Válvula'), 'P&ID REF-PRC-PID-001', [
          ['Tag', tag], ['Servicio', d ? d[1] : '—'], ['Rango', d ? d[2] : '—'], ['Función', d ? d[3] : '—'],
          ['Norma', 'ISA-5.1 · ISO 10628'],
        ]);
      });
    }
    this.svg.appendChild(g);
    return g;
  },

  cajaEquipo(x, y, w, h, titulo, sub, fichaId, filasLibres) {
    const g = svgEl('g', { class: 'clicable' });
    g.appendChild(svgEl('rect', { x, y, width: w, height: h, fill: '#f3f6fa', stroke: '#1a3a5c', 'stroke-width': 1.8, rx: 4, class: 'cuerpo' }));
    g.appendChild(svgEl('text', { x: x + w / 2, y: y + 18, 'font-size': 12, 'text-anchor': 'middle', 'font-weight': 700, fill: '#1a3a5c' }, titulo));
    if (sub) g.appendChild(svgEl('text', { x: x + w / 2, y: y + 33, 'font-size': 10, 'text-anchor': 'middle', fill: '#555' }, sub));
    if (fichaId) hacerInteractivo(g, fichaId);
    else if (filasLibres) {
      g.addEventListener('click', (e) => { e.stopPropagation(); abrirFichaLibre(titulo, sub, filasLibres); });
      g.addEventListener('mouseenter', (e) => mostrarTooltip(e, `<b>${titulo}</b><br>${sub || ''}`));
      g.addEventListener('mousemove', moverTooltip);
      g.addEventListener('mouseleave', ocultarTooltip);
    }
    this.svg.appendChild(g);
    return g;
  },

  dibujar() {
    const svg = this.svg;
    const defs = svgEl('defs', {});
    const m = svgEl('marker', { id: 'flechaPid', viewBox: '0 0 10 10', refX: 9, refY: 5, markerWidth: 4.5, markerHeight: 4.5, orient: 'auto-start-reverse' });
    m.appendChild(svgEl('path', { d: 'M 0 0 L 10 5 L 0 10 z', fill: '#444' }));
    defs.appendChild(m);
    svg.appendChild(defs);

    // ---- Marco general: Edificio C / rack / Nave A ----
    svg.appendChild(svgEl('rect', { x: 20, y: 40, width: 320, height: 740, fill: 'none', stroke: '#90a4ae', 'stroke-width': 1.5, 'stroke-dasharray': '10 6' }));
    svg.appendChild(svgEl('text', { x: 30, y: 60, 'font-size': 14, 'font-weight': 700, fill: '#546e7a' }, 'EDIFICIO C — SERVICIOS INDUSTRIALES'));
    svg.appendChild(svgEl('rect', { x: 360, y: 40, width: 130, height: 740, fill: '#eceff1', stroke: '#90a4ae', 'stroke-width': 1 }));
    svg.appendChild(svgEl('text', { x: 425, y: 410, 'font-size': 13, 'font-weight': 700, fill: '#546e7a', 'text-anchor': 'middle', transform: 'rotate(-90 425 410)' }, 'RACK DE TUBERÍAS AÉREO'));
    svg.appendChild(svgEl('rect', { x: 520, y: 40, width: 960, height: 740, fill: 'none', stroke: '#90a4ae', 'stroke-width': 1.5, 'stroke-dasharray': '10 6' }));
    svg.appendChild(svgEl('text', { x: 540, y: 60, 'font-size': 14, 'font-weight': 700, fill: '#546e7a' }, 'NAVE A — ÁREA DE PROCESO'));

    // ---- S-1 Caldera ----
    this.cajaEquipo(40, 90, 170, 130, 'S-1 CALDERA DE VAPOR', 'Vapor 8 barg · 185 °C · ATEX', null, [
      ['Servicio', 'Generación de vapor saturado 8 barg, 185 °C'],
      ['Uso', 'Calefaccionamiento del aire de secado vía intercambiador de calor'],
      ['Sala', 'Edificio C — sala de calderas (clasificada ATEX)'],
      ['Norma', 'ISO 10628 / DIN 28000'],
    ]);
    svg.appendChild(svgEl('path', { d: 'M 90 90 v -22 h 14 v 22', fill: 'none', stroke: '#1a3a5c', 'stroke-width': 2 })); // chimenea
    svg.appendChild(svgEl('text', { x: 118, y: 200, 'font-size': 18 }, '🔥'));
    // línea de vapor
    this.linea('M 210 140 H 560', 'vapor', 'VAPOR 8 barg · 185 °C', 230, 128);
    this.instr(255, 95, 'PT-101'); svg.appendChild(svgEl('line', { x1: 255, y1: 112, x2: 255, y2: 140, stroke: '#1a3a5c', 'stroke-width': 1 }));
    this.instr(305, 95, 'PI-101'); svg.appendChild(svgEl('line', { x1: 305, y1: 112, x2: 305, y2: 140, stroke: '#1a3a5c', 'stroke-width': 1 }));
    this.valvula(340, 140, 'bola', 'XV-101');
    // trampa de vapor ST-101 (símbolo cuadrado con S)
    const st = svgEl('g', { class: 'clicable' });
    st.appendChild(svgEl('rect', { x: 545, y: 127, width: 26, height: 26, fill: '#fff', stroke: '#1a3a5c', 'stroke-width': 1.6 }));
    st.appendChild(svgEl('text', { x: 558, y: 145, 'font-size': 12, 'text-anchor': 'middle', 'font-weight': 700, fill: '#1a3a5c' }, 'S'));
    st.addEventListener('click', (e) => { e.stopPropagation(); abrirFichaLibre('ST-101 — Trampa de vapor', 'P&ID REF-PRC-PID-001', [['Función', this.INSTR['ST-101'][3]], ['Servicio', this.INSTR['ST-101'][1]], ['Norma', 'ISA-5.1 · ISO 10628']]); });
    svg.appendChild(st);
    svg.appendChild(svgEl('text', { x: 558, y: 170, 'font-size': 9.5, 'text-anchor': 'middle', fill: '#1a3a5c' }, 'ST-101'));
    // XV-102 control + HX
    this.linea('M 571 140 H 645', 'vapor');
    this.valvula(615, 140, 'control', 'XV-102');
    const hx = svgEl('g', { class: 'clicable' });
    hx.appendChild(svgEl('circle', { cx: 700, cy: 150, r: 45, fill: '#fff', stroke: '#1a3a5c', 'stroke-width': 2, class: 'cuerpo' }));
    hx.appendChild(svgEl('path', { d: 'M 660 150 l 20 -18 l 20 36 l 20 -36 l 20 18', fill: 'none', stroke: '#1a3a5c', 'stroke-width': 2 }));
    hx.appendChild(svgEl('text', { x: 700, y: 215, 'font-size': 11, 'text-anchor': 'middle', 'font-weight': 700, fill: '#1a3a5c' }, 'INTERCAMBIADOR HX-101'));
    hx.appendChild(svgEl('text', { x: 700, y: 229, 'font-size': 9.5, 'text-anchor': 'middle', fill: '#555' }, 'Calefaccionamiento de aire'));
    hx.addEventListener('click', (e) => { e.stopPropagation(); abrirFichaLibre('HX-101 — Intercambiador de calor', 'Vapor → aire de secado', [
      ['Función', 'Calienta el aire de secado de la torre con vapor de S-1 (lazo TT-101 → TC-101 → XV-102)'],
      ['Lado caliente', 'Vapor 8 barg · 185 °C'], ['Lado frío', 'Aire filtrado → 200–300 °C'],
      ['Condensado', 'Retorna vía ST-101 al sistema de recuperación'], ['Norma', 'ISO 10628'],
    ]); });
    svg.appendChild(hx);
    this.instr(770, 80, 'TT-101'); svg.appendChild(svgEl('line', { x1: 757, y1: 91, x2: 728, y2: 122, stroke: '#1a3a5c', 'stroke-width': 1, 'stroke-dasharray': '3 3' }));
    this.instr(830, 80, 'TC-101'); svg.appendChild(svgEl('line', { x1: 787, y1: 80, x2: 813, y2: 80, stroke: '#1a3a5c', 'stroke-width': 1, 'stroke-dasharray': '3 3' }));
    svg.appendChild(svgEl('path', { d: 'M 830 97 V 118 H 615 V 126', fill: 'none', stroke: '#1a3a5c', 'stroke-width': 1, 'stroke-dasharray': '3 3' })); // señal TC→XV-102
    // aire caliente a torre
    this.linea('M 745 150 H 960 V 250 H 1048', 'caliente', 'AIRE CALIENTE A TORRE', 790, 168);
    // condensado de HX
    this.linea('M 700 195 V 268 H 220 ', 'cond', 'condensado a retorno', 380, 260);

    // ---- S-2 Compresores ----
    this.cajaEquipo(40, 330, 170, 120, 'S-2 COMPRESORES', 'Aire comprimido 7 barg · ATEX', null, [
      ['Servicio', 'Aire comprimido de planta e instrumentos, 7 barg'],
      ['Uso', 'Actuadores neumáticos (XV/PCV/FCV), pulsos de ciclones, fluidización'],
      ['Sala', 'Edificio C — sala de compresores + planta de agua DI (ATEX)'],
    ]);
    this.linea('M 210 395 H 985 V 95 H 1290', 'aire', 'AIRE COMPRIMIDO 7 barg', 230, 383);
    this.instr(255, 350, 'PT-201'); svg.appendChild(svgEl('line', { x1: 255, y1: 367, x2: 255, y2: 395, stroke: '#1a3a5c', 'stroke-width': 1 }));
    this.instr(305, 350, 'PI-201'); svg.appendChild(svgEl('line', { x1: 305, y1: 367, x2: 305, y2: 395, stroke: '#1a3a5c', 'stroke-width': 1 }));
    // filtro F-201
    const f201 = svgEl('g', {});
    f201.appendChild(svgEl('rect', { x: 330, y: 383, width: 24, height: 24, fill: '#fff', stroke: '#1a3a5c', 'stroke-width': 1.6 }));
    f201.appendChild(svgEl('line', { x1: 330, y1: 407, x2: 354, y2: 383, stroke: '#1a3a5c', 'stroke-width': 1.4 }));
    svg.appendChild(f201);
    svg.appendChild(svgEl('text', { x: 342, y: 422, 'font-size': 9.5, 'text-anchor': 'middle', fill: '#1a3a5c' }, 'F-201'));

    // ---- S-3 Agua desmineralizada ----
    this.cajaEquipo(40, 560, 170, 120, 'S-3 AGUA DESMINERALIZADA', 'RO + EDI', null, [
      ['Servicio', 'Agua desmineralizada por ósmosis inversa (RO) + electrodesionización (EDI)'],
      ['Uso', 'Tanques de mezcla TK-101/TK-102 y sistema CIP de la torre'],
      ['Sala', 'Edificio C — junto a compresores'],
    ]);
    this.linea('M 210 625 H 540 V 470 H 558', 'aguadi', 'AGUA DI', 230, 613);
    this.linea('M 540 625 V 690 H 900 V 320 H 1048', 'aguadi', 'AGUA DI a CIP torre', 700, 682);
    this.instr(255, 580, 'PT-301'); svg.appendChild(svgEl('line', { x1: 255, y1: 597, x2: 255, y2: 625, stroke: '#1a3a5c', 'stroke-width': 1 }));
    this.instr(305, 580, 'PI-301'); svg.appendChild(svgEl('line', { x1: 305, y1: 597, x2: 305, y2: 625, stroke: '#1a3a5c', 'stroke-width': 1 }));
    const f301 = svgEl('g', {});
    f301.appendChild(svgEl('rect', { x: 330, y: 613, width: 24, height: 24, fill: '#fff', stroke: '#1a3a5c', 'stroke-width': 1.6 }));
    f301.appendChild(svgEl('line', { x1: 330, y1: 637, x2: 354, y2: 613, stroke: '#1a3a5c', 'stroke-width': 1.4 }));
    svg.appendChild(f301);
    svg.appendChild(svgEl('text', { x: 342, y: 652, 'font-size': 9.5, 'text-anchor': 'middle', fill: '#1a3a5c' }, 'F-301'));
    this.instr(845, 650, 'FT-301'); svg.appendChild(svgEl('line', { x1: 845, y1: 667, x2: 845, y2: 690, stroke: '#1a3a5c', 'stroke-width': 1 }));
    this.valvula(900, 360, 'bola', 'XV-302');
    svg.appendChild(svgEl('text', { x: 952, y: 312, 'font-size': 10, fill: '#1565c0', 'font-weight': 600 }, 'CIP'));

    // ---- Tanques TK-101 / TK-102 ----
    const dibTanque = (x, y, id, nombre, lt) => {
      const g = svgEl('g', {});
      g.appendChild(svgEl('path', { d: `M ${x} ${y + 12} A 40 12 0 0 1 ${x + 80} ${y + 12} V ${y + 88} A 40 12 0 0 1 ${x} ${y + 88} Z`, fill: '#e3f0fb', stroke: '#1a3a5c', 'stroke-width': 2, class: 'cuerpo' }));
      // agitador
      g.appendChild(svgEl('line', { x1: x + 40, y1: y - 8, x2: x + 40, y2: y + 60, stroke: '#1a3a5c', 'stroke-width': 2 }));
      g.appendChild(svgEl('path', { d: `M ${x + 25} ${y + 60} h 30`, stroke: '#1a3a5c', 'stroke-width': 3 }));
      g.appendChild(svgEl('rect', { x: x + 28, y: y - 26, width: 24, height: 18, fill: '#fff', stroke: '#1a3a5c', 'stroke-width': 1.6 }));
      g.appendChild(svgEl('text', { x: x + 40, y: y - 13, 'font-size': 8.5, 'text-anchor': 'middle', fill: '#1a3a5c' }, 'M'));
      g.appendChild(svgEl('text', { x: x + 40, y: y + 105, 'font-size': 11, 'text-anchor': 'middle', 'font-weight': 700, fill: '#1a3a5c' }, nombre));
      g.appendChild(svgEl('text', { x: x + 40, y: y + 118, 'font-size': 9, 'text-anchor': 'middle', fill: '#555' }, 'SS 316L · 10,000 L'));
      hacerInteractivo(g, id);
      this.svg.appendChild(g);
      this.instr(x - 35, y + 40, lt);
      this.svg.appendChild(svgEl('line', { x1: x - 18, y1: y + 40, x2: x, y2: y + 40, stroke: '#1a3a5c', 'stroke-width': 1 }));
    };
    dibTanque(558, 430, 'tk101', 'TK-101 (Mezcla 1)', 'LT-101');
    dibTanque(558, 590, 'tk102', 'TK-102 (Mezcla 2)', 'LT-102');

    // ---- Bombas P-101/P-102 ----
    const dibBomba = (x, y, id, nombre) => {
      const g = svgEl('g', {});
      g.appendChild(svgEl('circle', { cx: x, cy: y, r: 22, fill: '#fff', stroke: '#1a3a5c', 'stroke-width': 2, class: 'cuerpo' }));
      g.appendChild(svgEl('path', { d: `M ${x - 12} ${y - 12} L ${x + 22} ${y} L ${x - 12} ${y + 12}`, fill: 'none', stroke: '#1a3a5c', 'stroke-width': 2 }));
      g.appendChild(svgEl('text', { x, y: y + 42, 'font-size': 10.5, 'text-anchor': 'middle', 'font-weight': 700, fill: '#1a3a5c' }, nombre));
      hacerInteractivo(g, id);
      this.svg.appendChild(g);
    };
    this.linea('M 638 500 H 720 V 520', 'proceso');
    this.linea('M 638 660 H 720 V 640', 'proceso');
    dibBomba(742, 530, 'p101', 'P-101 (ppal)');
    dibBomba(742, 630, 'p102', 'P-102 (resv)');
    // checks tras bombas y unión
    this.linea('M 764 530 H 830 V 575', 'proceso');
    this.linea('M 764 630 H 830 V 585', 'proceso');
    this.valvula(800, 530, 'check');
    this.valvula(800, 630, 'check');

    // filtro Y F-401
    const fy = svgEl('g', { class: 'clicable' });
    fy.appendChild(svgEl('path', { d: 'M 845 565 h 30 l 18 18 m -18 -18 l -8 22 h 16', fill: 'none', stroke: '#1a3a5c', 'stroke-width': 2 }));
    fy.appendChild(svgEl('text', { x: 868, y: 612, 'font-size': 9.5, 'text-anchor': 'middle', fill: '#1a3a5c' }, 'F-401 (filtro Y)'));
    fy.addEventListener('click', (e) => { e.stopPropagation(); abrirFichaLibre('F-401 — Filtro en Y (strainer)', 'Línea de alta presión', [
      ['Función', 'Protege la boquilla atomizadora de partículas gruesas del slurry'],
      ['Servicio', 'Pasta húmeda 100–250 bar'], ['Material', 'AISI 316L'], ['Norma', 'ISO 10628'],
    ]); });
    svg.appendChild(fy);

    // línea alta presión a boquilla
    this.linea('M 875 575 H 1150 V 120 H 1148', 'proceso', 'PASTA HÚMEDA ALTA PRESIÓN 100–250 bar', 915, 562);
    this.instr(940, 520, 'PT-401'); svg.appendChild(svgEl('line', { x1: 940, y1: 537, x2: 940, y2: 575, stroke: '#1a3a5c', 'stroke-width': 1 }));
    this.instr(1000, 520, 'FT-402'); svg.appendChild(svgEl('line', { x1: 1000, y1: 537, x2: 1000, y2: 575, stroke: '#1a3a5c', 'stroke-width': 1 }));
    this.valvula(1060, 575, 'control', 'PCV-401');

    // recirculación
    this.linea('M 1110 575 V 730 H 640 V 678', 'retorno', 'RETORNO / RECIRCULACIÓN de pasta', 760, 722);
    this.valvula(990, 730, 'control', 'FCV-402');
    this.instr(905, 760, 'FIT-402'); svg.appendChild(svgEl('line', { x1: 905, y1: 743, x2: 905, y2: 730, stroke: '#1a3a5c', 'stroke-width': 1 }));

    // ---- Torre GEA NIRO® + boquilla + ciclones ----
    const torre = svgEl('g', {});
    torre.appendChild(svgEl('path', { d: 'M 1060 130 H 1240 V 380 L 1150 540 Z', fill: '#fff3e0', stroke: '#1a3a5c', 'stroke-width': 2.5, class: 'cuerpo' }));
    torre.appendChild(svgEl('path', { d: 'M 1148 120 l 4 14 m -10 4 l 6 -18 l 6 18', stroke: '#1a3a5c', 'stroke-width': 2, fill: 'none' })); // boquilla
    torre.appendChild(svgEl('text', { x: 1150, y: 230, 'font-size': 13, 'text-anchor': 'middle', 'font-weight': 700, fill: '#1a3a5c' }, 'TORRE DE SECADO'));
    torre.appendChild(svgEl('text', { x: 1150, y: 247, 'font-size': 11, 'text-anchor': 'middle', fill: '#1a3a5c' }, 'GEA NIRO® Spray Dryer'));
    torre.appendChild(svgEl('text', { x: 1150, y: 264, 'font-size': 9.5, 'text-anchor': 'middle', fill: '#b71c1c', 'font-weight': 700 }, 'CUELLO DE BOTELLA · máx 1,500 kg/h'));
    torre.appendChild(svgEl('text', { x: 1150, y: 280, 'font-size': 9, 'text-anchor': 'middle', fill: '#555' }, 'Boquilla atomizadora (rociador)'));
    hacerInteractivo(torre, 'torre');
    svg.appendChild(torre);
    this.nodoTorre = torre.querySelector('.cuerpo');

    // ciclones
    const ciclon = (x, xv, pi) => {
      const g = svgEl('g', {});
      g.appendChild(svgEl('path', { d: `M ${x} 150 h 56 v 36 l -28 58 z`, fill: '#fff', stroke: '#1a3a5c', 'stroke-width': 2 }));
      svg.appendChild(g);
      this.valvula(x + 28, 122, 'pulso', xv);
      this.instr(x + 28, 290, pi);
      svg.appendChild(svgEl('line', { x1: x + 28, y1: 244, x2: x + 28, y2: 273, stroke: '#1a3a5c', 'stroke-width': 1 }));
    };
    this.linea('M 1240 165 H 1290', 'caliente');
    this.linea('M 1346 165 H 1370', 'caliente');
    ciclon(1290, 'XV-201', 'PI-202');
    ciclon(1370, 'XV-202', 'PI-203');
    svg.appendChild(svgEl('text', { x: 1395, y: 330, 'font-size': 10, fill: '#546e7a', 'font-weight': 600 }, 'CICLONES 1 y 2'));
    // finos de ciclones retornan
    this.linea('M 1318 244 V 470 H 1252', 'retorno', 'finos a torre (línea neumática)', 1280, 488);

    // salida de producto
    this.linea('M 1150 540 V 600 H 1330', 'caliente', 'GRÁNULO 60–80 °C → VIBRO-FLUIDIZER (Etapa ⑥)', 1170, 622);

    // ---- Leyendas ----
    const gl = svgEl('g', {});
    gl.appendChild(svgEl('rect', { x: 20, y: 800, width: 500, height: 160, fill: '#fff', stroke: '#1a3a5c', 'stroke-width': 1.5 }));
    gl.appendChild(svgEl('text', { x: 32, y: 822, 'font-size': 12, 'font-weight': 700, fill: '#1a3a5c' }, 'LEYENDA DE LÍNEAS'));
    Object.values(this.ESTILOS).forEach((s, i) => {
      const y = 842 + (i % 4) * 28, x = 32 + Math.floor(i / 4) * 250;
      gl.appendChild(svgEl('line', { x1: x, y1: y, x2: x + 50, y2: y, stroke: s.stroke, 'stroke-width': s.w, 'stroke-dasharray': s.dash }));
      gl.appendChild(svgEl('text', { x: x + 58, y: y + 4, 'font-size': 10 }, s.nombre));
    });
    svg.appendChild(gl);

    const gs = svgEl('g', {});
    gs.appendChild(svgEl('rect', { x: 540, y: 800, width: 420, height: 160, fill: '#fff', stroke: '#1a3a5c', 'stroke-width': 1.5 }));
    gs.appendChild(svgEl('text', { x: 552, y: 822, 'font-size': 12, 'font-weight': 700, fill: '#1a3a5c' }, 'LEYENDA DE SÍMBOLOS (ISA-5.1 / ISO 10628)'));
    const simbolos = [
      ['Válvula de bola', (x, y) => this._miniValv(gs, x, y, 'bola')],
      ['Válvula de globo', (x, y) => this._miniValv(gs, x, y, 'globo')],
      ['Válvula check', (x, y) => this._miniValv(gs, x, y, 'check')],
      ['Válvula de control (act. neumático)', (x, y) => this._miniValv(gs, x, y, 'control')],
      ['Filtro en Y (strainer)', (x, y) => gs.appendChild(svgEl('path', { d: `M ${x - 10} ${y} h 14 l 9 9 m -9 -9 l -4 11 h 8`, fill: 'none', stroke: '#1a3a5c', 'stroke-width': 1.6 }))],
      ['Trampa de vapor', (x, y) => { gs.appendChild(svgEl('rect', { x: x - 9, y: y - 9, width: 18, height: 18, fill: '#fff', stroke: '#1a3a5c', 'stroke-width': 1.4 })); gs.appendChild(svgEl('text', { x, y: y + 4, 'font-size': 9, 'text-anchor': 'middle', fill: '#1a3a5c', 'font-weight': 700 }, 'S')); }],
      ['Brida', (x, y) => { gs.appendChild(svgEl('line', { x1: x - 4, y1: y - 9, x2: x - 4, y2: y + 9, stroke: '#1a3a5c', 'stroke-width': 2.2 })); gs.appendChild(svgEl('line', { x1: x + 4, y1: y - 9, x2: x + 4, y2: y + 9, stroke: '#1a3a5c', 'stroke-width': 2.2 })); }],
      ['Instrumento en campo (PT/PI/TT/TC/FT/LT…)', (x, y) => { gs.appendChild(svgEl('circle', { cx: x, cy: y, r: 10, fill: '#fff', stroke: '#1a3a5c', 'stroke-width': 1.4 })); gs.appendChild(svgEl('line', { x1: x - 10, y1: y, x2: x + 10, y2: y, stroke: '#1a3a5c', 'stroke-width': 0.7 })); }],
    ];
    simbolos.forEach(([nombre, draw], i) => {
      const y = 845 + (i % 4) * 28, x = 565 + Math.floor(i / 4) * 210;
      draw(x, y);
      gs.appendChild(svgEl('text', { x: x + 20, y: y + 4, 'font-size': 9.5 }, nombre));
    });
    svg.appendChild(gs);

    // ---- Cajetín (title block) ----
    const cj = svgEl('g', {});
    cj.appendChild(svgEl('rect', { x: 980, y: 800, width: 500, height: 160, fill: '#fff', stroke: '#1a3a5c', 'stroke-width': 2.5 }));
    cj.appendChild(svgEl('line', { x1: 980, y1: 845, x2: 1480, y2: 845, stroke: '#1a3a5c', 'stroke-width': 1.2 }));
    cj.appendChild(svgEl('line', { x1: 980, y1: 905, x2: 1480, y2: 905, stroke: '#1a3a5c', 'stroke-width': 1.2 }));
    cj.appendChild(svgEl('line', { x1: 1230, y1: 905, x2: 1230, y2: 960, stroke: '#1a3a5c', 'stroke-width': 1.2 }));
    cj.appendChild(svgEl('text', { x: 1230, y: 828, 'font-size': 17, 'text-anchor': 'middle', 'font-weight': 800, fill: '#1a3a5c', 'letter-spacing': 2 }, 'REFRESH S.A.'));
    cj.appendChild(svgEl('text', { x: 1230, y: 868, 'font-size': 11.5, 'text-anchor': 'middle', 'font-weight': 700 }, 'Planta de Detergente en Polvo · Diagrama de Tuberías e Instrumentación (P&ID)'));
    cj.appendChild(svgEl('text', { x: 1230, y: 888, 'font-size': 11, 'text-anchor': 'middle' }, 'Servicios Industriales y Proceso — Nave A'));
    cj.appendChild(svgEl('text', { x: 1000, y: 930, 'font-size': 10.5 }, 'P&ID No.: REF-PRC-PID-001'));
    cj.appendChild(svgEl('text', { x: 1000, y: 948, 'font-size': 10.5 }, 'Normas: ISA-5.1 · ISO 10628 · DIN 28000'));
    cj.appendChild(svgEl('text', { x: 1250, y: 930, 'font-size': 10.5 }, 'Hoja 1 de 1 · Escala N.T.S.'));
    cj.appendChild(svgEl('text', { x: 1250, y: 948, 'font-size': 10.5 }, 'Junio 2026 · Panamá'));
    svg.appendChild(cj);
  },

  _miniValv(g, x, y, tipo) {
    g.appendChild(svgEl('path', { d: `M ${x - 9} ${y - 6} L ${x + 9} ${y + 6} L ${x + 9} ${y - 6} L ${x - 9} ${y + 6} Z`, fill: tipo === 'check' ? '#1a3a5c' : '#fff', stroke: '#1a3a5c', 'stroke-width': 1.4 }));
    if (tipo === 'bola') g.appendChild(svgEl('circle', { cx: x, cy: y, r: 2.6, fill: '#1a3a5c' }));
    if (tipo === 'globo') g.appendChild(svgEl('circle', { cx: x, cy: y, r: 2.6, fill: '#fff', stroke: '#1a3a5c', 'stroke-width': 1.2 }));
    if (tipo === 'control') {
      g.appendChild(svgEl('line', { x1: x, y1: y, x2: x, y2: y - 11, stroke: '#1a3a5c', 'stroke-width': 1.2 }));
      g.appendChild(svgEl('path', { d: `M ${x - 7} ${y - 11} A 7 7 0 0 1 ${x + 7} ${y - 11} Z`, fill: '#fff', stroke: '#1a3a5c', 'stroke-width': 1.2 }));
    }
  },

  animar(on) {
    this.lineas.forEach(({ p, dash }) => {
      if (on) {
        p.setAttribute('stroke-dasharray', dash || '12 8');
        p.classList.add('linea-flujo-anim');
      } else {
        p.setAttribute('stroke-dasharray', dash);
        p.classList.remove('linea-flujo-anim');
      }
    });
  },
};
