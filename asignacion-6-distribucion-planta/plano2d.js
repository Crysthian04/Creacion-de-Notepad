/* ============================================================
   Pestaña 1 — Plano 2D de Distribución de Planta (SVG)
   Terreno 100 × 100 m · escala 1:250 · cotas en metros
   ============================================================ */

const Plano2D = {
  panZoom: null,
  inicializado: false,

  init() {
    if (this.inicializado) return;
    this.inicializado = true;
    const cont = document.getElementById('vista2d');

    // Toolbar
    const tb = document.createElement('div');
    tb.className = 'toolbar';
    tb.innerHTML = `
      <button id="btnAjustar2d">⤢ Ajustar vista</button>
      <label class="toggle on" id="tgCotas">📏 Mostrar/ocultar cotas</label>
      <label class="toggle" id="tgFlujo">①→⑩ Flujo de proceso</label>
      <label class="toggle" id="tgQc">🧪 Puertas QC y retornos</label>
      <label class="toggle" id="tgDist">ℹ Tipo de distribución</label>`;
    cont.appendChild(tb);

    const svg = svgEl('svg', { class: 'lienzo-svg', preserveAspectRatio: 'xMidYMid meet' });
    cont.appendChild(svg);
    this.svg = svg;
    this.panZoom = instalarPanZoom(svg, { x: -10, y: -7, w: 124, h: 116 });
    document.getElementById('btnAjustar2d').onclick = () => this.panZoom.ajustar();

    this.dibujar();

    document.getElementById('tgCotas').onclick = (e) => {
      e.currentTarget.classList.toggle('on');
      this.gCotas.style.display = e.currentTarget.classList.contains('on') ? '' : 'none';
    };
    document.getElementById('tgFlujo').onclick = (e) => {
      e.currentTarget.classList.toggle('on');
      this.gFlujo.style.display = e.currentTarget.classList.contains('on') ? '' : 'none';
    };
    document.getElementById('tgQc').onclick = (e) => {
      e.currentTarget.classList.toggle('on');
      this.gQc.style.display = e.currentTarget.classList.contains('on') ? '' : 'none';
    };

    // Panel de justificación del tipo de distribución (Asignación #6)
    const pd = document.createElement('div');
    pd.className = 'mini-panel';
    pd.style.display = 'none';
    pd.style.maxWidth = '380px';
    pd.style.top = '92px'; // debajo de la barra de herramientas, sin sobreponerse
    pd.style.maxHeight = 'calc(100% - 110px)';
    pd.style.overflowY = 'auto';
    const PR = PLANT_DATA.principios;
    pd.innerHTML = `<h4>Tipo de distribución de planta</h4>
      <table>
        <tr><th>Tipo</th><th>¿Aplica?</th></tr>
        <tr><td><b>Por producto (en línea)</b></td><td><span class="chip ok">SÍ — Principal</span></td></tr>
        <tr><td>Por proceso (funcional)</td><td><span class="chip" style="background:#f9a825">Parcial — Soporte</span></td></tr>
        <tr><td>Tecnología de grupos</td><td><span class="chip" style="background:#90a4ae">No aplica</span></td></tr>
        <tr><td>Por posición fija</td><td><span class="chip" style="background:#90a4ae">No aplica</span></td></tr>
      </table>
      <div style="margin-top:6px;line-height:1.5">
        <b>Principal:</b> los equipos siguen el orden exacto del proceso ①→⑩ sin retrocesos — la naturaleza
        continua de la GEA NIRO® (24/7) exige distribución en línea: mínimo manejo de materiales, QC integrado
        y máxima utilización del cuello de botella.<br>
        <b>Complementaria:</b> áreas de soporte (laboratorio QC, taller, calderas, SCADA) agrupadas por función
        en los Edificios C y D.<br>
        <b>No aplican:</b> no hay familias de partes (producto único) y el producto nunca es estacionario.
      </div>
      <h4 style="margin-top:12px">Principios básicos de distribución — jerarquización (parte b)</h4>
      <div style="line-height:1.45;color:#555;margin-bottom:7px">${PR.criterio}</div>
      ${PR.lista.map((p) => `
        <div style="margin-bottom:8px">
          <div style="display:flex;justify-content:space-between;align-items:center;gap:6px">
            <b>${p.n}. ${p.nombre}</b><span class="chip info" style="flex-shrink:0">${p.pct} %</span>
          </div>
          <div style="height:7px;background:#eee;border-radius:4px;overflow:hidden;margin:3px 0 4px">
            <div style="width:${p.pct * 3.5}%;height:100%;background:${p.n <= 2 ? '#1565c0' : p.n === 3 ? '#d32f2f' : '#78909c'};border-radius:4px"></div>
          </div>
          <div style="line-height:1.45"><b>Por qué:</b> ${p.porQue}</div>
          <div style="line-height:1.45;color:#555"><b>Cómo se aplicó:</b> ${p.como}</div>
        </div>`).join('')}
      <div style="border-top:1px solid #e8e6dd;padding-top:6px;margin-top:4px;line-height:1.5">
        <b>Regla de oro (suma 100 % ✓):</b> ${PR.reglaDeOro}
      </div>`;
    cont.appendChild(pd);
    document.getElementById('tgDist').onclick = (e) => {
      e.currentTarget.classList.toggle('on');
      pd.style.display = e.currentTarget.classList.contains('on') ? '' : 'none';
    };

    Bus.on('tick', () => this.actualizarEstado());
  },

  // Línea de cota con flechas y texto
  cota(g, x1, y1, x2, y2, texto, tam = 1.3) {
    const dx = x2 - x1, dy = y2 - y1;
    const len = Math.hypot(dx, dy);
    const ux = dx / len, uy = dy / len;
    const px = -uy, py = ux; // perpendicular
    g.appendChild(svgEl('line', { x1, y1, x2, y2, class: 'cota-linea' }));
    for (const [cx, cy, s] of [[x1, y1, 1], [x2, y2, -1]]) {
      g.appendChild(svgEl('path', {
        d: `M ${cx} ${cy} l ${s * ux * 1 + px * 0.35} ${s * uy * 1 + py * 0.35} l ${-px * 0.7} ${-py * 0.7} z`,
        fill: '#9c27b0',
      }));
      g.appendChild(svgEl('line', { x1: cx + px * 0.8, y1: cy + py * 0.8, x2: cx - px * 0.8, y2: cy - py * 0.8, class: 'cota-linea' }));
    }
    const tx = (x1 + x2) / 2 + px * 1.1, ty = (y1 + y2) / 2 + py * 1.1;
    const ang = (Math.atan2(dy, dx) * 180) / Math.PI;
    g.appendChild(svgEl('text', {
      x: tx, y: ty, class: 'cota-texto', 'font-size': tam, 'text-anchor': 'middle',
      transform: Math.abs(ang) > 45 ? `rotate(${ang > 0 ? ang - 180 : ang} ${tx} ${ty})` : '',
    }, texto));
  },

  cotasRect(g, p, tam = 1.3, off = 1.6) {
    this.cota(g, p.x, p.y - off, p.x + p.w, p.y - off, `${p.w.toFixed(p.w % 1 ? 2 : 0)} m`, tam);
    this.cota(g, p.x - off, p.y + p.h, p.x - off, p.y, `${p.h.toFixed(p.h % 1 ? 2 : 0)} m`, tam);
  },

  dibujar() {
    const svg = this.svg;
    const T = PLANT_DATA.proyecto.terreno;

    // ---- Terreno y vial perimetral ----
    svg.appendChild(svgEl('rect', { id: 'terreno2d', x: 0, y: 0, width: T.w, height: T.h, fill: '#eef2e8', stroke: '#1a3a5c', 'stroke-width': 0.5 }));
    svg.appendChild(svgEl('rect', { x: 1, y: 1, width: T.w - 2, height: T.h - 2, fill: 'none', stroke: '#888', 'stroke-width': 7, opacity: 0.35 })); // vial 7 m
    svg.appendChild(svgEl('rect', { x: 1, y: 1, width: T.w - 2, height: T.h - 2, fill: 'none', stroke: '#555', 'stroke-width': 0.15, 'stroke-dasharray': '2 1.2' }));
    svg.appendChild(svgEl('text', { x: 50, y: 3.6, class: 'etiq-svg', 'font-size': 1.6, 'text-anchor': 'middle', 'font-weight': 700 }, '⬆ ACCESO CAMIONES DE MATERIA PRIMA (NORTE) — Vial perimetral 7.00 m · R 15.00'));
    svg.appendChild(svgEl('text', { x: 50, y: 98.4, class: 'etiq-svg', 'font-size': 1.6, 'text-anchor': 'middle', 'font-weight': 700 }, '⬇ SALIDA DE PRODUCTO TERMINADO (SUR) — 4 bahías de despacho'));

    // Norte
    const gn = svgEl('g', {});
    gn.appendChild(svgEl('path', { d: 'M 105 8 l 2 6 l -2 -1.6 l -2 1.6 z', fill: '#1a3a5c' }));
    gn.appendChild(svgEl('text', { x: 105, y: 6.8, class: 'etiq-svg', 'font-size': 2.2, 'text-anchor': 'middle', 'font-weight': 700 }, 'N'));
    svg.appendChild(gn);

    // ---- Pasillos (leyenda de circulación) ----
    const gPas = svgEl('g', { fill: 'none' });
    // peatonal 2.00 m (verde discontinuo)
    const peat = [
      'M 19 19 L 19 33', 'M 48 44 L 52 44', 'M 29 14 L 31 14',
      'M 55 58 L 55 64', 'M 40 71 L 43 71', 'M 64 46 L 70 46',
    ];
    peat.forEach((d) => gPas.appendChild(svgEl('path', { d, stroke: '#2e7d32', 'stroke-width': 2, 'stroke-dasharray': '1.6 1', opacity: 0.6 })));
    // montacargas 3.50 m (naranja discontinuo)
    const monta = [
      'M 53.5 31 L 53.5 34', 'M 44 54 L 44 62', 'M 26 80 L 26 84', 'M 61 26 L 67 26 L 67 60',
    ];
    monta.forEach((d) => gPas.appendChild(svgEl('path', { d, stroke: '#ef6c00', 'stroke-width': 3.5, 'stroke-dasharray': '2 1.2', opacity: 0.55 })));
    // área de giro peatonal 1.50 × 1.50
    gPas.appendChild(svgEl('rect', { x: 18.25, y: 25, width: 1.5, height: 1.5, fill: 'none', stroke: '#2e7d32', 'stroke-width': 0.18, 'stroke-dasharray': '0.5 0.4' }));
    svg.appendChild(gPas);

    // ---- Edificios ----
    const gCotas = svgEl('g', {});
    this.gCotas = gCotas;
    for (const ed of Object.values(PLANT_DATA.edificios)) {
      const g = svgEl('g', {});
      const p = ed.pos;
      const r = svgEl('rect', { x: p.x, y: p.y, width: p.w, height: p.h, fill: ed.color, class: 'edif-rect cuerpo', rx: 0.3 });
      if (ed.id === 'expansion') { r.setAttribute('stroke-dasharray', '1.5 1'); r.setAttribute('opacity', 0.8); }
      g.appendChild(r);
      const lineas = ed.nombre.split(' — ');
      lineas.forEach((ln, i) => {
        g.appendChild(svgEl('text', {
          x: p.x + p.w / 2, y: p.y + (ed.id === 'naveA' || ed.id === 'naveB' ? 1.9 : p.h / 2) + i * 2 - (lineas.length - 1),
          class: 'etiq-svg', 'font-size': Math.min(1.7, p.w / 13), 'text-anchor': 'middle', 'font-weight': 700,
        }, ln));
      });
      hacerInteractivo(g, ed.id);
      svg.appendChild(g);
      if (ed.id !== 'expansion') this.cotasRect(gCotas, p);
    }

    // Pasarela de interconexión Nave A ↔ Nave B (3.00 m)
    const gPasarela = svgEl('g', {});
    gPasarela.appendChild(svgEl('rect', { x: 23.5, y: 54, width: 3, height: 8, fill: '#cfd8dc', class: 'edif-rect cuerpo' }));
    gPasarela.appendChild(svgEl('text', { x: 27.4, y: 58.4, class: 'etiq-svg', 'font-size': 1, 'font-weight': 600 }, 'Pasillo técnico 3.00 m'));
    svg.appendChild(gPasarela);
    this.cota(gCotas, 23.5, 60.5, 26.5, 60.5, '3.00 m', 0.9);

    // ---- Estacionamiento: puestos ----
    const gEst = svgEl('g', { stroke: '#90a4ae', 'stroke-width': 0.12 });
    for (let i = 0; i < 15; i++) {
      gEst.appendChild(svgEl('line', { x1: 31 + i * 2, y1: 9, x2: 31 + i * 2, y2: 13.5 }));
      gEst.appendChild(svgEl('line', { x1: 31 + i * 2, y1: 14.5, x2: 31 + i * 2, y2: 19 }));
    }
    gEst.appendChild(svgEl('text', { x: 32.2, y: 11.7, 'font-size': 1.5, fill: '#01579b', stroke: 'none', 'font-weight': 700 }, '♿'));
    gEst.appendChild(svgEl('text', { x: 32.2, y: 17, 'font-size': 1.5, fill: '#01579b', stroke: 'none', 'font-weight': 700 }, '♿'));
    svg.appendChild(gEst);

    // ---- Bahías de despacho (4) ----
    const gBah = svgEl('g', {});
    for (let i = 0; i < 4; i++) {
      gBah.appendChild(svgEl('rect', { x: 13.5 + i * 6.5, y: 84.5, width: 5, height: 6, fill: '#b0bec5', stroke: '#37474f', 'stroke-width': 0.2 }));
      gBah.appendChild(svgEl('text', { x: 16 + i * 6.5, y: 88, class: 'etiq-svg', 'font-size': 1.3, 'text-anchor': 'middle', 'font-weight': 700 }, `B-${i + 1}`));
    }
    svg.appendChild(gBah);

    // ---- Silos (4 × Ø2.50 m) ----
    const gSilos = svgEl('g', {});
    for (let i = 0; i < 4; i++) {
      const cx = 48.7 + i * 3.4;
      gSilos.appendChild(svgEl('circle', { cx, cy: 26.5, r: 1.25, fill: '#cfd8dc', class: 'equipo-rect cuerpo' }));
      gSilos.appendChild(svgEl('text', { x: cx, y: 26.9, class: 'etiq-svg', 'font-size': 0.9, 'text-anchor': 'middle' }, `S${i + 1}`));
    }
    gSilos.appendChild(svgEl('text', { x: 53.5, y: 30, class: 'etiq-svg', 'font-size': 0.9, 'text-anchor': 'middle' }, '4 silos Ø2.50 m + elevadores de cangilones'));
    hacerInteractivo(gSilos, 'silos');
    svg.appendChild(gSilos);
    this.cota(gCotas, 47.45, 23.4, 49.95, 23.4, 'Ø2.50', 0.8);

    // ---- Equipos dentro de naves ----
    this.nodosEquipo = {};
    for (const eq of Object.values(PLANT_DATA.equipos)) {
      if (eq.id === 'silos') continue;
      const g = svgEl('g', {});
      const p = eq.pos;
      const esTanque = eq.id === 'tk101' || eq.id === 'tk102';
      let forma;
      if (esTanque) {
        forma = svgEl('circle', { cx: p.x + p.w / 2, cy: p.y + p.h / 2, r: p.w / 2, fill: '#b3d3ee', class: 'equipo-rect cuerpo' });
      } else {
        const colores = { torre: '#ffd180', enfriador: '#fff59d', postadicion: '#fff59d', tolvas: '#ffe082', vffs: '#c8e6c9', ensacadora: '#c8e6c9', paletizador: '#c8e6c9', distribuidor: '#e1bee7', checkweigher: '#b2dfdb', bc101: '#d7ccc8', bc102: '#d7ccc8', p101: '#b3d3ee', p102: '#b3d3ee', cuarentena: '#ffcdd2' };
        forma = svgEl('rect', { x: p.x, y: p.y, width: p.w, height: p.h, fill: colores[eq.id] || '#e0e0e0', class: 'equipo-rect cuerpo', rx: 0.15 });
      }
      if (eq.id === 'cuarentena') {
        forma.setAttribute('stroke', '#b71c1c');
        forma.setAttribute('stroke-dasharray', '0.7 0.45');
        forma.setAttribute('stroke-width', '0.35');
      }
      g.appendChild(forma);
      this.nodosEquipo[eq.id] = forma;

      // etiqueta corta + dimensiones al lado del equipo
      const cortos = { tk101: 'TK-101', tk102: 'TK-102', p101: 'P-101', p102: 'P-102', torre: 'TORRE GEA NIRO®', enfriador: 'VIBRO-FLUIDIZER', postadicion: 'POST-ADICIÓN', tolvas: 'TOLVAS BUFFER 3×5,000 kg', distribuidor: 'DISTRIBUIDOR', vffs: 'VFFS ROVEMA (Mód. A)', ensacadora: 'ENSACADORA H&B (Mód. B)', checkweigher: 'CW + DM', bc101: 'BC-101', bc102: 'BC-102', paletizador: 'PALETIZADOR', cuarentena: '🔴 CUARENTENA QC' };
      const dimsCortas = { tk101: 'Ø3.0 m', tk102: 'Ø3.0 m', p101: '2.0×1.2', p102: '2.0×1.2', torre: '12×14 m · h 15–20 m', enfriador: '4×2 m', postadicion: '4×2.5 m', tolvas: '6.00×3.00 m', distribuidor: '2×1.5', vffs: '1.8×1.2 · h 2.8', ensacadora: '2.5×2.0 · h 2.8', checkweigher: '1.6×1.0', bc101: '6.0 m', bc102: '6.0 m', paletizador: '2.2×2.2', cuarentena: '5.0×3.0 m' };
      g.appendChild(svgEl('text', { x: p.x + p.w / 2, y: p.y + p.h / 2 + (eq.id === 'torre' ? -0.5 : 0.2), class: 'etiq-svg', 'font-size': eq.id === 'torre' ? 1.3 : 0.75, 'text-anchor': 'middle', 'font-weight': 700 }, cortos[eq.id]));
      g.appendChild(svgEl('text', { x: p.x + p.w / 2, y: p.y + p.h + 0.9, class: 'cota-texto', 'font-size': 0.7, 'text-anchor': 'middle' }, dimsCortas[eq.id]));
      hacerInteractivo(g, eq.id);
      svg.appendChild(g);
      if (eq.id === 'torre' || eq.id === 'tolvas') this.cotasRect(gCotas, p, 0.9, 1.1);
    }

    // ---- Elementos de seguridad ----
    const gSeg = svgEl('g', {});
    [[48.5, 33], [42, 61], [8.5, 55], [41, 81]].forEach(([x, y]) => {
      gSeg.appendChild(svgEl('circle', { cx: x, cy: y, r: 0.55, fill: '#fff', stroke: '#0277bd', 'stroke-width': 0.18 }));
      gSeg.appendChild(svgEl('text', { x, y: y + 0.32, 'font-size': 0.75, 'text-anchor': 'middle', fill: '#0277bd', 'font-weight': 700 }, '◐'));
    });
    [[53.5, 32.5], [44, 61.5]].forEach(([x, y]) => {
      gSeg.appendChild(svgEl('rect', { x: x - 0.4, y: y - 1, width: 0.8, height: 2, fill: '#37474f', rx: 0.2 }));
      gSeg.appendChild(svgEl('circle', { cx: x, cy: y - 0.55, r: 0.26, fill: '#e53935' }));
      gSeg.appendChild(svgEl('circle', { cx: x, cy: y + 0.55, r: 0.26, fill: '#43a047' }));
    });
    // portones doble hoja 2.40 m
    [[28, 34], [28, 80], [52, 40]].forEach(([x, y]) => {
      gSeg.appendChild(svgEl('line', { x1: x - 1.2, y1: y, x2: x + 1.2, y2: y, stroke: '#b71c1c', 'stroke-width': 0.45 }));
    });
    svg.appendChild(gSeg);

    // ---- Capa de flujo de proceso ①→⑩ ----
    const gFlujo = svgEl('g', { style: 'display:none' });
    this.gFlujo = gFlujo;
    const defs = svgEl('defs', {});
    const marker = svgEl('marker', { id: 'flecha2d', viewBox: '0 0 10 10', refX: 9, refY: 5, markerWidth: 5, markerHeight: 5, orient: 'auto-start-reverse' });
    marker.appendChild(svgEl('path', { d: 'M 0 0 L 10 5 L 0 10 z', fill: '#c62828' }));
    defs.appendChild(marker);
    svg.appendChild(defs);

    const puntosFlujo = [
      [53.5, 26.5], [50, 33], [11.5, 38], [16, 39.5], [26, 44],
      [36, 40], [36, 45.2], [43, 42.5], [17, 70], [31, 71.5],
    ];
    this.puntosFlujo = puntosFlujo;
    for (let i = 0; i < puntosFlujo.length - 1; i++) {
      const [x1, y1] = puntosFlujo[i], [x2, y2] = puntosFlujo[i + 1];
      const f = PLANT_DATA.flujo[i];
      gFlujo.appendChild(svgEl('path', {
        d: i === 7 ? `M ${x1} ${y1} L 44 54 L 25 58 L 25 63 L ${x2} ${y2}` : `M ${x1} ${y1} L ${x2} ${y2}`,
        stroke: f.color, 'stroke-width': 0.5, fill: 'none', 'marker-end': 'url(#flecha2d)', opacity: 0.9,
      }));
    }
    const nums = '①②③④⑤⑥⑦⑧⑨⑩';
    puntosFlujo.forEach(([x, y], i) => {
      gFlujo.appendChild(svgEl('circle', { cx: x, cy: y, r: 1.3, fill: '#fff', stroke: PLANT_DATA.flujo[i].color, 'stroke-width': 0.35 }));
      gFlujo.appendChild(svgEl('text', { x, y: y + 0.65, 'font-size': 1.8, 'text-anchor': 'middle', fill: '#1a3a5c', 'font-weight': 700 }, nums[i]));
    });
    svg.appendChild(gFlujo);

    // ---- Capa QC: puertas de calidad + retornos de no conforme ----
    const gQc = svgEl('g', { style: 'display:none' });
    this.gQc = gQc;
    // líneas de retorno (rojas discontinuas)
    const retornosQc = [
      ['M 33 40 L 26 36 L 14 36 L 12 37.5', 'retrabajo de gránulos (QC-3) → mezclado', 18, 35.2],   // enfriador → TK
      ['M 16 39 C 14 39 13.5 38.5 13 38.4', 'reformular slurry (QC-2)', 0, 0],                      // bomba → TK
      ['M 36.5 76.5 L 43 76.5 L 43 47 L 45 44.5', '♻ reproceso (QC-4) → tolvas', 44, 60],          // cuarentena → tolvas
      ['M 51 24 L 51 14 L 48 9', '↩ devolución a proveedor (QC-1)', 39, 12],                       // silos → norte
    ];
    for (const [d, etiq, ex, ey] of retornosQc) {
      gQc.appendChild(svgEl('path', { d, fill: 'none', stroke: '#b71c1c', 'stroke-width': 0.45, 'stroke-dasharray': '1.2 0.8', 'marker-end': 'url(#flecha2d)', opacity: 0.9 }));
      if (ex) gQc.appendChild(svgEl('text', { x: ex, y: ey, 'font-size': 0.95, fill: '#b71c1c', 'font-weight': 600 }, etiq));
    }
    // diamantes QC clicables
    const puertasPos = { qc1: [51, 30], qc2: [17.8, 43.5], qc3: [33, 41.5], qc4: [21.3, 71.7] };
    this.nodosQc = {};
    for (const [id, [qx, qy]] of Object.entries(puertasPos)) {
      const def = PLANT_DATA.qc.puertas[id];
      const gd = svgEl('g', { class: 'clicable' });
      const dia = svgEl('path', { d: `M ${qx} ${qy - 1.3} L ${qx + 1.3} ${qy} L ${qx} ${qy + 1.3} L ${qx - 1.3} ${qy} Z`, fill: '#fff', stroke: '#b71c1c', 'stroke-width': 0.28 });
      gd.appendChild(dia);
      gd.appendChild(svgEl('text', { x: qx, y: qy + 0.4, 'font-size': 0.85, 'text-anchor': 'middle', 'font-weight': 700, fill: '#b71c1c' }, def.tag));
      gd.addEventListener('mouseenter', (e) => mostrarTooltip(e, `<b>${def.tag}</b> — ${def.pregunta}<br>NO → ${def.camino}`));
      gd.addEventListener('mousemove', moverTooltip);
      gd.addEventListener('mouseleave', ocultarTooltip);
      gd.addEventListener('click', (e) => {
        e.stopPropagation();
        abrirFichaLibre(`${def.tag} — Puerta de control de calidad`, def.pregunta, [
          ['Ubicación', def.ubicacion], ['Criterio', def.pregunta],
          ['Camino de no conformidad', def.camino], ['Acción', def.accion],
          ['Programa QC', '4 puertas · 4 caminos (Devolución · Reformular · Retrabajo · Cuarentena) · meta <2 % no conforme'],
        ]);
      });
      gQc.appendChild(gd);
      this.nodosQc[id] = dia;
    }
    svg.appendChild(gQc);

    // ---- Leyenda ----
    const gLey = svgEl('g', {});
    gLey.appendChild(svgEl('rect', { x: 44, y: 92.2, width: 54, height: 7.2, fill: '#fff', stroke: '#1a3a5c', 'stroke-width': 0.25 }));
    gLey.appendChild(svgEl('text', { x: 45, y: 93.9, class: 'etiq-svg', 'font-size': 1.1, 'font-weight': 700 }, 'LEYENDA'));
    const items = [
      [45, 95.5, '#2e7d32', '1.6 1', 'Pasillo peatonal 2.00 m'],
      [45, 97.2, '#ef6c00', '2 1.2', 'Pasillo montacargas 3.50 m'],
      [62, 95.5, '#b71c1c', '', 'Portón doble hoja 2.40 m c/ sello cortafuego'],
      [62, 97.2, '#0277bd', '', '◐ Espejo convexo · 🚦 semáforo acústico-luminoso'],
      [45, 98.8, '#9c27b0', '', '⟷ Cotas en metros · Escala 1:250 · Área giro peatonal 1.50×1.50'],
    ];
    for (const [x, y, color, dash, texto] of items) {
      if (dash) gLey.appendChild(svgEl('line', { x1: x, y1: y - 0.35, x2: x + 3.5, y2: y - 0.35, stroke: color, 'stroke-width': 0.6, 'stroke-dasharray': dash }));
      else gLey.appendChild(svgEl('rect', { x, y: y - 0.7, width: 3.5, height: 0.7, fill: color, opacity: 0.8 }));
      gLey.appendChild(svgEl('text', { x: x + 4.2, y, class: 'etiq-svg', 'font-size': 1 }, texto));
    }
    svg.appendChild(gLey);

    // Cotas del terreno
    this.cota(gCotas, 0, -3.5, 100, -3.5, '100.00 m', 1.8);
    this.cota(gCotas, -4.5, 100, -4.5, 0, '100.00 m (10,000 m²)', 1.8);
    svg.appendChild(gCotas);

    // Complementos: recorrido narrado, checklist, mezzanines y temas
    Recorrido.init();
  },

  // Sinergia: reflejar alertas de la simulación
  actualizarEstado() {
    if (!this.inicializado) return;
    const torre = this.nodosEquipo.torre, tolvas = this.nodosEquipo.tolvas, cuar = this.nodosEquipo.cuarentena;
    if (torre) torre.classList.toggle('alerta-parpadeo', !!Sim.alertas.torre);
    if (tolvas) {
      tolvas.classList.toggle('alerta-parpadeo', !!(Sim.alertas.tolvas && Sim.alertas.tolvas.nivel === 'roja'));
      tolvas.classList.toggle('alerta-amarilla-parpadeo', !!(Sim.alertas.tolvas && Sim.alertas.tolvas.nivel === 'amarilla'));
    }
    if (cuar) cuar.classList.toggle('alerta-parpadeo', Sim.qcStats.cuarentena > 0);
    if (this.nodosQc) {
      for (const [id, dia] of Object.entries(this.nodosQc)) {
        dia.classList.toggle('alerta-parpadeo', !!(Sim.qcEvento && Sim.qcEvento.puerta === id));
      }
    }
  },
};
