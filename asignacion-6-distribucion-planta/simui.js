/* ============================================================
   Pestaña 5 — Simulación de Producción (interfaz)
   Incluye: panel QC / producto no conforme (4 puertas · 4 caminos),
   capacidades con barras, distribución por presentación, verificación
   de metas mensuales, calendario con chips y régimen de mantenimiento.
   ============================================================ */

const SimUI = {
  inicializado: false,

  init() {
    if (this.inicializado) return;
    this.inicializado = true;
    const cont = document.getElementById('vistaSim');
    cont.innerHTML = `
    <div class="sim-grid">
      <div>
        <div class="panel">
          <h3>⚙ Controles de simulación</h3>
          <div class="ctrl-fila">
            <label>Alimentación de slurry a la torre: <span class="lectura" id="lecFeed">1,125 kg/h</span></label>
            <input type="range" id="slFeed" min="0" max="2000" step="25" value="1125">
            <div style="display:flex;justify-content:space-between;font-size:10px;color:#7a8a99"><span>0</span><span>1,500 (máx torre)</span><span>2,000</span></div>
          </div>
          <div class="ctrl-fila">
            <label>Velocidad de envasado del módulo activo: <span class="lectura" id="lecVelEnv">100 %</span></label>
            <input type="range" id="slVelEnv" min="40" max="120" step="5" value="100">
          </div>
          <div class="ctrl-fila">
            <label>Nivel inicial de tolvas: <span class="lectura" id="lecTolva0">40 %</span></label>
            <input type="range" id="slTolva0" min="0" max="100" step="5" value="40">
          </div>
          <div class="ctrl-fila">
            <label>Velocidad de simulación</label>
            <div class="vel-sim">
              <button data-vel="1">1×</button>
              <button data-vel="60" class="on">60× (1 s = 1 min)</button>
              <button data-vel="600">600×</button>
            </div>
          </div>
          <div class="botones-sim">
            <button id="btnIniciar" class="primario">▶ Iniciar</button>
            <button id="btnPausar">⏸ Pausar</button>
            <button id="btnReset" class="reset">🔄 RESET</button>
          </div>
          <div style="font-size:10.5px;color:#7a8a99;margin-top:8px">RESET restaura el estado "planta eficiente": 1,125 kg/h (capacidad real 75 %), tolvas al 40 %, Lunes T1 06:00, sin alertas.</div>
        </div>

        <div class="panel" id="panelQC">
          <h3>🧪 Control de calidad — producto no conforme</h3>
          <div style="font-size:11px;color:#56646f;margin-bottom:8px">
            <b>4 puertas QC · 4 caminos.</b> En modo automático la planta detecta no conformes ocasionales
            (meta &lt;2 %) y los dispone sola (≈80 % reproceso). Con los botones declaras tú el no conforme
            y, en QC-4, decides la disposición final.
          </div>
          <div class="qc-botones">
            <button data-qc="qc1" title="¿MP cumple ficha técnica?">QC-1 · MP</button>
            <button data-qc="qc2" title="¿Slurry OK?">QC-2 · Slurry</button>
            <button data-qc="qc3" title="¿Humedad ≤5 %?">QC-3 · Gránulo</button>
            <button data-qc="qc4" title="¿Peso·sello·metales OK?">QC-4 · Envasado</button>
          </div>
          <div id="qcEstado" class="qc-estado"></div>
          <div id="qcDecision" style="display:none">
            <div style="font-size:11.5px;font-weight:700;margin:8px 0 6px;color:#b71c1c">⚖ Disposición final del lote en cuarentena:</div>
            <div class="botones-sim">
              <button id="btnReprocesar" style="border-color:#2e7d32;color:#2e7d32">♻ Reprocesar</button>
              <button id="btnDesechar" style="border-color:#b71c1c;color:#b71c1c">✗ Desechar</button>
            </div>
          </div>
          <div class="qc-stats" id="qcStats"></div>
        </div>

        <div class="panel">
          <h3>📅 Calendario del ciclo semanal (21 turnos)</h3>
          <div class="cal-resumen">
            <span class="chip ok">13 productivos</span>
            <span class="chip" style="background:#f9a825">5 setup (1 h c/u)</span>
            <span class="chip err">3 mantenimiento</span>
            <span class="chip" style="background:#90a4ae">3 libres/buffer</span>
          </div>
          <table class="cal" id="tablaCal"></table>
          <div style="font-size:10px;color:#7a8a99;margin-top:6px">T1 06:00–14:00 · T2 14:00–22:00 · T3 22:00–06:00 · La torre GEA NIRO® nunca se detiene (24/7).</div>
        </div>

        <div class="panel">
          <h3>📜 Registro de eventos</h3>
          <div id="logEventos"></div>
        </div>
      </div>

      <div>
        <div id="alertas"></div>

        <div class="panel">
          <h3>📊 KPIs en vivo</h3>
          <div class="kpis" id="kpis"></div>
        </div>

        <div class="panel">
          <h3>🏭 Línea de proceso — 10 etapas + 4 puertas QC</h3>
          <div class="ctrl-fila" style="margin-bottom:6px">
            <div class="vel-sim" id="filtrosFlujo">
              <button data-filtro="todo" class="on">Todo</button>
              <button data-filtro="liquido">🔵 Líquido/Slurry</button>
              <button data-filtro="solido">🟡 Sólido/Polvo</button>
              <button data-filtro="empaque">🟢 Empaque</button>
            </div>
          </div>
          <div id="sankey"></div>
          <div style="font-size:10.5px;margin-top:6px">
            <span class="chip" style="background:#2196f3">🔵 Líquido / slurry (65–75 °C)</span>
            <span class="chip" style="background:#ff9800">🟠 Gránulo caliente 60–80 °C (cambio de fase en la torre)</span>
            <span class="chip" style="background:#fbc02d;color:#5d4a00">🟡 Polvo frío &lt;35 °C</span>
            <span class="chip" style="background:#4caf50">🟢 Producto envasado / pallets</span>
            <span class="chip" style="background:#b71c1c">◆ Puerta QC · - - retorno no conforme</span>
          </div>
        </div>

        <div class="panel">
          <div class="torre-banner"><span class="punto-pulso"></span>
            <div><b>GEA NIRO® en operación continua 24/7</b> — como una caldera industrial: no se detiene por cambios de formato ni por el mantenimiento del miércoles (solo línea de envasado). Paro mayor planificado <b>1 vez al año</b> (7–14 días), ya descontado en el factor 85 % de capacidad de sistema.</div>
          </div>
          <h3 style="margin-top:10px">📦 Capacidades (Asignación #4) — cuello de botella TOC (Goldratt, 1984)</h3>
          <div class="cap-grid">
            <div class="cap-card">
              <div class="ct" style="color:#1565c0">Diseño (100 %)</div>
              <div class="cn" style="color:#1565c0">1,500 <small>kg/h</small></div>
              <div class="cs">36,000 kg/día · 1,080,000 kg/mes</div>
              <div class="barra"><div style="width:100%;background:#1565c0"></div></div>
              <div class="cap-nota">Máxima teórica: GEA NIRO® a plena carga 24 h sin paradas (Chase, Jacobs &amp; Aquilano, 2006).</div>
            </div>
            <div class="cap-card">
              <div class="ct" style="color:#b8860b">Sistema (85 %)</div>
              <div class="cn" style="color:#b8860b">1,275 <small>kg/h</small></div>
              <div class="cs">30,600 kg/día · 918,000 kg/mes</div>
              <div class="barra"><div style="width:85%;background:#d4961f"></div></div>
              <div class="cap-nota">Descuenta paro anual (7–14 días), mantenimientos, CIP y arranques. Factor 0.85 estándar industrial.</div>
            </div>
            <div class="cap-card" style="border-color:#2e7d32">
              <div class="ct" style="color:#2e7d32">Real (75 %) — predeterminado</div>
              <div class="cn" style="color:#2e7d32">1,125 <small>kg/h</small></div>
              <div class="cs">27,000 kg/día · 810,000 kg/mes</div>
              <div class="barra"><div style="width:75%;background:#3a8c4e"></div></div>
              <div class="cap-nota">Efectiva año 1: curva de aprendizaje y ajustes. Rango 65–85 % documentado.</div>
            </div>
          </div>
        </div>

        <div class="panel">
          <h3>🧺 Distribución por presentación — base 27,000 kg/día (capacidad real)</h3>
          <table class="cal" id="tablaDist"></table>
        </div>

        <div class="panel">
          <h3>🎯 Verificación de metas mensuales — 4 ciclos × 7 días</h3>
          <table class="cal" id="tablaMetas"></table>
          <div style="font-size:10px;color:#7a8a99;margin-top:6px">El excedente sobre la meta = stock de seguridad para picos de demanda. Balance del ciclo: 13 turnos productivos + 5 setup + 3 mantenimiento + 3 libres.</div>
        </div>

        <div class="panel">
          <h3>🔧 Régimen de mantenimiento GEA NIRO® — principio de caldera industrial</h3>
          <div class="mant-grid">
            <div class="mant-card">
              <div class="mh"><span class="chip ok">Diario/Semanal</span> sin paro de torre</div>
              <ul><li>Boquillas, presiones y temperaturas</li><li>Vibración en ventiladores/ciclones</li><li>Nivel de tolvas buffer y SCADA</li><li>Filtros de mangas (sin parar)</li></ul>
            </div>
            <div class="mant-card">
              <div class="mh"><span class="chip info">Trimestral</span> sin paro de torre</div>
              <ul><li>Inspección externa de cámara</li><li>Ciclones por desgaste exterior</li><li>Calibración de combustión</li><li>Integridad del aislante térmico</li></ul>
            </div>
            <div class="mant-card mant-rojo">
              <div class="mh"><span class="chip err">Anual</span> <b>paro mayor 7–14 días</b></div>
              <ul><li>Inspección interna de cámara</li><li>Reemplazo de boquillas</li><li>Refractario y aislante interno</li><li>Limpieza profunda + calibración PLC/SCADA</li></ul>
            </div>
            <div class="mant-card">
              <div class="mh"><span class="chip" style="background:#f9a825">Miércoles semanal</span> solo envasado</div>
              <ul><li>Paro de línea de envasado (3 turnos)</li><li>Preventivo VFFS + CIP de envasadoras</li><li>GEA NIRO® sigue — tolvas acumulan</li><li>Autonomía 13.3 h → gestión activa del nivel</li></ul>
            </div>
          </div>
        </div>
      </div>
    </div>`;

    // ---- Controles ----
    document.getElementById('slFeed').oninput = (e) => {
      Sim.alimentacionKgH = +e.target.value;
      document.getElementById('lecFeed').textContent = fmt(Sim.alimentacionKgH) + ' kg/h';
      if (!Sim.corriendo) { Sim.paso(0.0001); Bus.emit('tick'); }
    };
    document.getElementById('slVelEnv').oninput = (e) => {
      Sim.velEnvasadoPct = +e.target.value;
      document.getElementById('lecVelEnv').textContent = Sim.velEnvasadoPct + ' %';
    };
    document.getElementById('slTolva0').oninput = (e) => {
      document.getElementById('lecTolva0').textContent = e.target.value + ' %';
      Sim.tolvaKg = (+e.target.value / 100) * PLANT_DATA.tolvasCapacidadKg;
      Bus.emit('tick');
    };
    cont.querySelectorAll('.vel-sim button[data-vel]').forEach((b) => {
      b.onclick = () => {
        cont.querySelectorAll('.vel-sim button[data-vel]').forEach((x) => x.classList.remove('on'));
        b.classList.add('on');
        Sim.velocidad = +b.dataset.vel;
      };
    });
    document.getElementById('btnIniciar').onclick = () => Sim.iniciar();
    document.getElementById('btnPausar').onclick = () => Sim.pausar();
    document.getElementById('btnReset').onclick = () => {
      Sim.reset();
      document.getElementById('slFeed').value = 1125;
      document.getElementById('lecFeed').textContent = '1,125 kg/h';
      document.getElementById('slVelEnv').value = 100;
      document.getElementById('lecVelEnv').textContent = '100 %';
      document.getElementById('slTolva0').value = 40;
      document.getElementById('lecTolva0').textContent = '40 %';
      cont.querySelectorAll('.vel-sim button[data-vel]').forEach((x) => x.classList.toggle('on', x.dataset.vel === '60'));
    };

    // ---- QC: declarar no conforme + disposición ----
    cont.querySelectorAll('.qc-botones button').forEach((b) => {
      b.onclick = () => Sim.declararNoConforme(b.dataset.qc, true);
    });
    document.getElementById('btnReprocesar').onclick = () => Sim.decidirCuarentena('reprocesar');
    document.getElementById('btnDesechar').onclick = () => Sim.decidirCuarentena('desechar');

    // ---- Filtros de resaltado de flujo ----
    this.filtroFlujo = 'todo';
    cont.querySelectorAll('#filtrosFlujo button').forEach((b) => {
      b.onclick = () => {
        cont.querySelectorAll('#filtrosFlujo button').forEach((x) => x.classList.remove('on'));
        b.classList.add('on');
        this.filtroFlujo = b.dataset.filtro;
        this.actualizar();
      };
    });

    this.construirCalendario();
    this.construirTablas();
    this.construirSankey();
    Bus.on('tick', () => this.actualizar());
    Bus.on('log', () => this.pintarLog());
    this.actualizar();
    this.pintarLog();
  },

  construirCalendario() {
    const chipsFmt = { '500g': 'cc-500', '1kg': 'cc-1kg', '3kg': 'cc-3kg', '5kg': 'cc-5kg', '20kg': 'cc-20kg', '50kg': 'cc-50kg' };
    const cambios = ['500 g → 1 kg', 'Producción continua', 'Mant. preventivo + CIP envasadora · torre sigue 24/7', '1 kg → 3 kg', '3 kg → 5 kg · 5 kg → 20 kg', '20 kg → 50 kg', 'Buffer · absorbe atrasos'];
    const tabla = document.getElementById('tablaCal');
    let html = '<tr><th>Día</th><th>T1</th><th>T2</th><th>T3</th><th>Cambio de formato</th></tr>';
    PLANT_DATA.calendario.forEach((d, di) => {
      html += `<tr><td><b>${d.dia}</b></td>`;
      d.turnos.forEach((tu, ti) => {
        let chip;
        if (tu.act === 'pack') chip = `<span class="cal-chip ${chipsFmt[tu.formato]}">${PLANT_DATA.formatos[tu.formato].nombre}</span>`;
        else if (tu.act === 'setup') chip = '<span class="cal-chip cc-setup">SETUP 1 h</span>';
        else if (tu.act === 'mant') chip = '<span class="cal-chip cc-mant">Mantenim.</span>';
        else chip = '<span class="cal-chip cc-libre">Libre</span>';
        html += `<td id="cal-${di}-${ti}">${chip}</td>`;
      });
      html += `<td style="text-align:left;font-size:10px;color:#8d6e00">${cambios[di]}</td></tr>`;
    });
    tabla.innerHTML = html;
  },

  construirTablas() {
    // distribución por presentación
    let h = '<tr><th>Presentación</th><th>Segmento</th><th>%</th><th>kg/día</th><th>Uds/día</th><th>Uds/mes</th></tr>';
    let totKg = 0, totUd = 0, totUm = 0;
    for (const d of PLANT_DATA.distribucionPresentaciones) {
      const f = PLANT_DATA.formatos[d.formato];
      const seg = d.seg === 'Hogar' ? '<span class="chip info">Hogar</span>' : '<span class="chip ok">Industrial</span>';
      h += `<tr><td>${f.nombre}</td><td>${seg}</td><td>${d.pct} %</td><td>${fmt(d.kgDia)}</td><td>${fmt(d.udsDia)}</td><td>${fmt(d.udsMes)}</td></tr>`;
      totKg += d.kgDia; totUd += d.udsDia; totUm += d.udsMes;
    }
    h += `<tr style="font-weight:700;background:#eef3f8"><td>TOTAL</td><td>—</td><td>100 %</td><td>${fmt(totKg)}</td><td>${fmt(totUd)}</td><td>${fmt(totUm)}</td></tr>`;
    document.getElementById('tablaDist').innerHTML = h;

    // verificación de metas
    let m = '<tr><th>Presentación</th><th>Equipo · velocidad</th><th>T/ciclo</th><th>h/mes</th><th>Prod./mes</th><th>Meta/mes</th><th>Resultado</th></tr>';
    for (const d of PLANT_DATA.metasMensuales) {
      const f = PLANT_DATA.formatos[d.formato];
      const pct = Math.round(((d.prodMes - d.metaMes) / d.metaMes) * 100);
      m += `<tr><td>${f.nombre}</td><td style="font-size:10px">${d.equipo}</td><td>${d.turnosCiclo}</td><td>${d.hMes}</td><td><b>${fmt(d.prodMes)}</b></td><td>${fmt(d.metaMes)}</td><td><span class="chip ok">CUMPLE +${pct} %</span></td></tr>`;
    }
    document.getElementById('tablaMetas').innerHTML = m;
  },

  construirSankey() {
    const W = 1180, H = 330;
    const svg = svgEl('svg', { viewBox: `0 0 ${W} ${H}`, width: '100%' });
    document.getElementById('sankey').appendChild(svg);
    this.nodos = [];
    const nx = (i) => 14 + i * 117;

    // conectores
    this.conectores = [];
    for (let i = 0; i < 9; i++) {
      const linea = svgEl('line', { x1: nx(i) + 100, y1: 120, x2: nx(i + 1), y2: 120, 'stroke-width': 7, stroke: '#ccc' });
      svg.appendChild(linea);
      const etiqFase = svgEl('text', { x: nx(i) + 108, y: 102, 'font-size': 9, fill: '#555', 'text-anchor': 'middle' }, '');
      const etiqTemp = svgEl('text', { x: nx(i) + 108, y: 138, 'font-size': 8.5, fill: '#888', 'text-anchor': 'middle' }, '');
      svg.appendChild(etiqFase); svg.appendChild(etiqTemp);
      this.conectores.push({ linea, etiqFase, etiqTemp });
    }

    // líneas de retorno de no conformes (rojas discontinuas)
    this.retornos = {};
    const defsR = [
      // QC-2: del conector ③→④ de vuelta al mezclado (nodo 3)
      ['qc2', `M ${nx(2) + 108} 112 C ${nx(2) + 108} 50 ${nx(2) + 60} 50 ${nx(2) + 50} 80`],
      // QC-3: del conector ⑤→⑥ de vuelta al mezclado (nodo 3)
      ['qc3', `M ${nx(4) + 108} 112 C ${nx(4) + 108} 30 ${nx(2) + 70} 30 ${nx(2) + 60} 80`],
      // QC-4: del conector ⑨→⑩ hacia cuarentena (abajo)
      ['qc4', `M ${nx(8) + 108} 128 L ${nx(8) + 108} 235`],
      // QC-1: devolución a proveedor (sale del sistema)
      ['qc1', `M ${nx(0) + 108} 112 C ${nx(0) + 108} 60 ${nx(0) + 60} 55 ${nx(0) + 30} 60`],
    ];
    for (const [id, d] of defsR) {
      const p = svgEl('path', { d, fill: 'none', stroke: '#b71c1c', 'stroke-width': 2, 'stroke-dasharray': '6 4', opacity: 0.25 });
      svg.appendChild(p);
      this.retornos[id] = p;
    }
    svg.appendChild(svgEl('text', { x: nx(0) + 8, y: 52, 'font-size': 8.5, fill: '#b71c1c' }, '↩ devolución a proveedor (QC-1)'));
    svg.appendChild(svgEl('text', { x: nx(2) + 64, y: 24, 'font-size': 8.5, fill: '#b71c1c' }, 'retrabajo de gránulos (QC-3) · reformular (QC-2) → mezclado'));

    // diamantes QC sobre los conectores
    this.qcDiamantes = {};
    const gates = [['qc1', 0], ['qc2', 2], ['qc3', 4], ['qc4', 8]];
    for (const [id, ci] of gates) {
      const x = nx(ci) + 108, y = 120;
      const g = svgEl('g', { class: 'clicable' });
      const dia = svgEl('path', { d: `M ${x} ${y - 11} L ${x + 11} ${y} L ${x} ${y + 11} L ${x - 11} ${y} Z`, fill: '#fff', stroke: '#b71c1c', 'stroke-width': 2 });
      g.appendChild(dia);
      g.appendChild(svgEl('text', { x, y: y + 3.5, 'font-size': 7.5, 'text-anchor': 'middle', 'font-weight': 700, fill: '#b71c1c' }, id.toUpperCase().replace('QC', 'QC')));
      const def = PLANT_DATA.qc.puertas[id];
      g.addEventListener('mouseenter', (e) => mostrarTooltip(e, `<b>${def.tag}</b> — ${def.pregunta}<br>NO → ${def.camino}`));
      g.addEventListener('mousemove', moverTooltip);
      g.addEventListener('mouseleave', ocultarTooltip);
      g.addEventListener('click', (e) => {
        e.stopPropagation();
        abrirFichaLibre(`${def.tag} — Puerta de control de calidad`, def.pregunta, [
          ['Ubicación', def.ubicacion],
          ['Criterio', def.pregunta],
          ['Camino de no conformidad', def.camino],
          ['Acción', def.accion],
          ['Trazabilidad', 'Cada disposición queda con responsable, registro y trazabilidad (4 caminos: Devolución · Reformular · Retrabajo · Cuarentena)'],
        ]);
      });
      svg.appendChild(g);
      this.qcDiamantes[id] = dia;
    }

    PLANT_DATA.flujo.forEach((f, i) => {
      const g = svgEl('g', { class: 'clicable' });
      const x = nx(i);
      const esTolva = f.n === 8;
      const rect = svgEl('rect', { x, y: esTolva ? 60 : 85, width: 100, height: esTolva ? 110 : 70, rx: 6, fill: '#fff', stroke: f.color, 'stroke-width': 2.5 });
      g.appendChild(rect);
      g.appendChild(svgEl('text', { x: x + 50, y: 78, 'font-size': 13, 'text-anchor': 'middle', 'font-weight': 700, fill: '#1a3a5c' }, '①②③④⑤⑥⑦⑧⑨⑩'[i]));
      const nombre = f.nombre.length > 30 ? f.nombre.slice(0, 28) + '…' : f.nombre;
      g.appendChild(svgEl('text', { x: x + 50, y: esTolva ? 175 : 100, 'font-size': 7.8, 'text-anchor': 'middle', fill: '#1a3a5c', 'font-weight': 600 }, nombre));
      const valKg = svgEl('text', { x: x + 50, y: esTolva ? 188 : 116, 'font-size': 11, 'text-anchor': 'middle', 'font-weight': 700, fill: f.color }, '0 kg/h');
      g.appendChild(valKg);
      const barBg = svgEl('rect', { x: x + 12, y: esTolva ? 192 : 132, width: 76, height: 7, rx: 3, fill: '#eee', stroke: '#bbb', 'stroke-width': 0.5 });
      const bar = svgEl('rect', { x: x + 12, y: esTolva ? 192 : 132, width: 0, height: 7, rx: 3, fill: f.color });
      const barTxt = svgEl('text', { x: x + 50, y: esTolva ? 211 : 151, 'font-size': 8, 'text-anchor': 'middle', fill: '#777' }, 'util 0 %');
      g.appendChild(barBg); g.appendChild(bar); g.appendChild(barTxt);

      if (esTolva) {
        g.appendChild(svgEl('rect', { x: x + 25, y: 88, width: 50, height: 75, rx: 4, fill: '#f5f5f5', stroke: '#8d6e63', 'stroke-width': 1.5 }));
        const tanque = svgEl('rect', { x: x + 26.5, y: 161.5, width: 47, height: 0, fill: '#fbc02d' });
        g.appendChild(tanque);
        g.appendChild(svgEl('rect', { x: x + 25, y: 88, width: 50, height: 75, rx: 4, fill: 'none', stroke: '#8d6e63', 'stroke-width': 1.5 }));
        const pctTxt = svgEl('text', { x: x + 50, y: 128, 'font-size': 12, 'text-anchor': 'middle', 'font-weight': 700, fill: '#1a3a5c' }, '40 %');
        g.appendChild(pctTxt);
        this.tolvaPctTxt = pctTxt;
        this.tolvaTanque = tanque;
      }
      g.addEventListener('click', () => abrirFicha(f.equipo));
      svg.appendChild(g);
      this.nodos.push({ rect, valKg, bar, barTxt, f, g });
    });

    // caja de cuarentena (bajo el envasado)
    const xc = nx(8) + 58;
    const gc = svgEl('g', { class: 'clicable' });
    this.cuarRect = svgEl('rect', { x: xc, y: 238, width: 100, height: 62, rx: 6, fill: '#fdecea', stroke: '#b71c1c', 'stroke-width': 2, 'stroke-dasharray': '5 3' });
    gc.appendChild(this.cuarRect);
    gc.appendChild(svgEl('text', { x: xc + 50, y: 256, 'font-size': 9, 'text-anchor': 'middle', 'font-weight': 700, fill: '#b71c1c' }, 'CUARENTENA (QC-4)'));
    this.cuarTxt = svgEl('text', { x: xc + 50, y: 272, 'font-size': 10, 'text-anchor': 'middle', 'font-weight': 700, fill: '#b71c1c' }, '0 kg');
    gc.appendChild(this.cuarTxt);
    gc.appendChild(svgEl('text', { x: xc + 50, y: 288, 'font-size': 8, 'text-anchor': 'middle', fill: '#8d4a4a' }, '♻ reproceso · ✗ desecho'));
    gc.addEventListener('click', () => abrirFicha('cuarentena'));
    svg.appendChild(gc);
    // retorno de reproceso: cuarentena → tolvas (nodo 8)
    this.retornoReproceso = svgEl('path', { d: `M ${xc} 268 C ${nx(7) + 50} 268 ${nx(7) + 50} 230 ${nx(7) + 50} 175`, fill: 'none', stroke: '#2e7d32', 'stroke-width': 2, 'stroke-dasharray': '6 4', opacity: 0.25 });
    svg.appendChild(this.retornoReproceso);
    svg.appendChild(svgEl('text', { x: nx(7) - 40, y: 290, 'font-size': 8.5, fill: '#2e7d32' }, '♻ reproceso → tolvas/post-adición'));

    svg.appendChild(svgEl('text', { x: 14, y: 20, 'font-size': 11, fill: '#7a8a99' }, 'Flujo del producto →   (clic en nodos y diamantes ◆QC para fichas)'));
  },

  actualizar() {
    const pctTolva = (Sim.tolvaKg / PLANT_DATA.tolvasCapacidadKg) * 100;
    const f = Sim.formatoActivo ? PLANT_DATA.formatos[Sim.formatoActivo] : null;
    const cuello = Sim.alimentacionKgH > 1500 ? 'TORRE (⛔ activo)' : pctTolva >= 100 ? 'TOLVAS LLENAS' : 'Torre GEA NIRO® (1,500 kg/h)';
    const pctNC = Sim.pctNoConforme();
    const kpis = [
      ['kg/h instantáneo (torre)', fmt(Sim.torreOutKgH), 'salida de polvo', ''],
      ['kg acumulados del día', fmt(Sim.kgDia), 'envasados desde 06:00', ''],
      ['uds/h formato activo', f ? `${fmt(Sim.envasadoUdsH)}` : '—', f ? f.nombre + ' · Módulo ' + f.modulo : Sim.enMantenimiento ? 'mantenimiento' : 'sin envasado', ''],
      ['OEE estimado', Sim.oee().toFixed(1) + ' %', 'vs capacidad de diseño', ''],
      ['Nivel de tolvas', pctTolva.toFixed(0) + ' %', fmt(Sim.tolvaKg) + ' / 15,000 kg', pctTolva >= 100 ? 'err' : pctTolva >= 80 ? 'warn' : ''],
      ['Cuello de botella', cuello.split(' (')[0], cuello.includes('⛔') ? 'límite excedido' : 'restricción del sistema (TOC)', Sim.alertas.torre || pctTolva >= 100 ? 'err' : ''],
      ['% no conforme', pctNC.toFixed(1) + ' %', `meta <${PLANT_DATA.qc.metaPct} % · ${fmt(Sim.qcStats.noConforme)} kg NC`, pctNC >= PLANT_DATA.qc.metaPct && Sim.qcStats.noConforme > 0 ? 'warn' : ''],
      ['Recuperado vía reproceso', fmt(Sim.qcStats.reproceso) + ' kg', `✗ desecho: ${fmt(Sim.qcStats.desecho)} kg · ↩ devuelto: ${fmt(Sim.qcStats.devuelto)} kg`, ''],
    ];
    document.getElementById('kpis').innerHTML = kpis.map(([e, v, s, c]) =>
      `<div class="kpi ${c}"><div class="k-etiq">${e}</div><div class="k-val">${v}</div><div class="k-sub">${s}</div></div>`).join('');

    // Alertas
    const cont = document.getElementById('alertas');
    const al = Object.values(Sim.alertas);
    cont.innerHTML = al.length
      ? al.map((a) => `<div class="alerta ${a.nivel}">${a.texto}</div>`).join('')
      : '<div class="alerta info" style="animation:none">✅ Planta eficiente — sin alertas. Torre y envasado balanceados según el calendario semanal.</div>';

    // Estado del panel QC
    const ev = Sim.qcEvento;
    const est = document.getElementById('qcEstado');
    if (ev) {
      const def = PLANT_DATA.qc.puertas[ev.puerta];
      const restMin = Math.max(0, Math.round(ev.tFin - Sim.tMin));
      const faseTxt = ev.fase === 'inspeccion' ? `🔍 Verificación de calidad en curso (~${restMin} min sim restantes)`
        : ev.fase === 'decision' ? '⚖ Lote en CUARENTENA — esperando tu disposición final'
        : `🔧 ${def.camino} (~${restMin} min sim restantes)`;
      est.innerHTML = `<b>${def.tag} activo</b> · lote ${fmt(ev.kgLote)} kg · ${ev.manual ? 'declarado manualmente' : 'detección automática'}<br>${faseTxt}`;
      est.className = 'qc-estado activo';
    } else {
      est.innerHTML = '✅ Sin eventos de calidad activos. Las 4 puertas QC verifican en línea (modo automático activo).';
      est.className = 'qc-estado';
    }
    document.getElementById('qcDecision').style.display = ev && ev.fase === 'decision' ? '' : 'none';
    document.getElementById('qcStats').innerHTML =
      `<span class="chip ${pctNC >= 2 && Sim.qcStats.noConforme > 0 ? 'warn' : 'ok'}">NC: ${pctNC.toFixed(1)} % (meta <2 %)</span>
       <span class="chip info">♻ ${fmt(Sim.qcStats.reproceso)} kg</span>
       <span class="chip err">✗ ${fmt(Sim.qcStats.desecho)} kg</span>
       <span class="chip" style="background:#8d6e63">↩ ${fmt(Sim.qcStats.devuelto)} kg</span>
       <span class="chip ${Sim.qcStats.cuarentena > 0 ? 'err' : 'ok'}">⏸ cuarentena: ${fmt(Sim.qcStats.cuarentena)} kg</span>`;

    // Calendario: celda actual
    const t = Sim.infoTiempo();
    document.querySelectorAll('#tablaCal td.actual').forEach((td) => td.classList.remove('actual'));
    const celda = document.getElementById(`cal-${t.diaIdx}-${t.turnoIdx}`);
    if (celda) celda.classList.add('actual');

    // Sankey
    if (!this.nodos) return;
    const valores = [Sim.alimentacionKgH, Sim.alimentacionKgH, Math.min(Sim.alimentacionKgH, 2000), Math.min(Sim.alimentacionKgH, 2000),
      Sim.torreOutKgH, Sim.torreOutKgH, Sim.torreOutKgH, Sim.tolvaKg, Sim.envasadoKgH, Sim.envasadoKgH];
    const capacidades = [2000, 2000, 2000, 2000, 1500, 1500, 1500, 15000,
      f ? f.udsH * f.kgUd : 1, f ? f.udsH * f.kgUd : 1];
    const fases = [
      ['granel', 'amb.'], ['polvo MP', 'amb.'], ['🔵 slurry 35–45 %', '65–75 °C'], ['🔵 líquido presurizado', '100–250 bar'],
      ['🟠 gránulo (cambio de fase)', '60–80 °C'], ['🟡 gránulo frío', '<35 °C'], ['🟡 polvo terminado', 'amb.'],
      ['🟡 polvo → distribuidor', 'amb.'], ['🟢 envasado', 'amb.'], ['🟢 pallets', 'amb.'],
    ];
    // filtro de resaltado: etapas por categoría (índices 0..9)
    const categorias = { liquido: [2, 3], solido: [0, 1, 4, 5, 6, 7], empaque: [8, 9] };
    const enFiltro = (i) => this.filtroFlujo === 'todo' || categorias[this.filtroFlujo].includes(i);

    this.nodos.forEach((n, i) => {
      const esTolva = i === 7;
      n.valKg.textContent = esTolva ? fmt(valores[i]) + ' kg' : fmt(valores[i]) + ' kg/h';
      const util = Math.min(100, (valores[i] / capacidades[i]) * 100) || 0;
      n.bar.setAttribute('width', (util / 100) * 76);
      n.barTxt.textContent = 'util ' + util.toFixed(0) + ' %';
      if (i === 4) n.rect.classList.toggle('alerta-parpadeo', !!Sim.alertas.torre);
      if (esTolva) {
        n.rect.classList.toggle('alerta-parpadeo', !!(Sim.alertas.tolvas && Sim.alertas.tolvas.nivel === 'roja'));
        n.rect.classList.toggle('alerta-amarilla-parpadeo', !!(Sim.alertas.tolvas && Sim.alertas.tolvas.nivel === 'amarilla'));
      }
      const apagado = (i === 8 || i === 9) && !Sim.moduloActivo;
      n.g.setAttribute('opacity', !enFiltro(i) ? 0.18 : apagado ? 0.4 : 1);
    });
    if (this.tolvaTanque) {
      const h = (pctTolva / 100) * 72;
      this.tolvaTanque.setAttribute('height', h);
      this.tolvaTanque.setAttribute('y', 161.5 - h);
      this.tolvaTanque.setAttribute('fill', pctTolva >= 100 ? '#d32f2f' : pctTolva >= 80 ? '#f9a825' : '#fbc02d');
      this.tolvaPctTxt.textContent = pctTolva.toFixed(0) + ' %';
    }
    const coloresTramo = ['#8d6e63', '#8d6e63', '#2196f3', '#2196f3', '#ff9800', '#fbc02d', '#fbc02d', '#fbc02d', '#4caf50'];
    const catTramo = (i) => (i <= 1 ? 'solido' : i <= 3 ? 'liquido' : i <= 7 ? 'solido' : 'empaque');
    this.conectores.forEach((c, i) => {
      const activo = i >= 7 ? Sim.envasadoKgH > 1 : i >= 4 ? Sim.torreOutKgH > 1 : Sim.alimentacionKgH > 1;
      c.linea.setAttribute('stroke', activo ? coloresTramo[i] : '#ddd');
      const dim = this.filtroFlujo !== 'todo' && catTramo(i) !== this.filtroFlujo;
      c.linea.setAttribute('opacity', dim ? 0.15 : 1);
      c.etiqFase.textContent = fases[i + 1][0];
      c.etiqTemp.textContent = fases[i + 1][1];
    });

    // QC en sankey: diamante activo + retorno animado
    for (const [id, dia] of Object.entries(this.qcDiamantes)) {
      const activo = ev && ev.puerta === id;
      dia.classList.toggle('alerta-parpadeo', !!activo);
      dia.setAttribute('fill', activo ? '#ffcdd2' : '#fff');
      const ret = this.retornos[id];
      if (ret) {
        ret.setAttribute('opacity', activo ? 1 : 0.25);
        ret.classList.toggle('linea-flujo-anim', !!(activo && ev.fase === 'accion'));
      }
    }
    if (this.cuarRect) {
      const kgC = Sim.qcStats.cuarentena;
      this.cuarTxt.textContent = fmt(kgC) + ' kg';
      this.cuarRect.classList.toggle('alerta-parpadeo', kgC > 0);
      this.retornoReproceso.setAttribute('opacity', kgC > 0 ? 0.8 : 0.25);
    }
  },

  pintarLog() {
    const el = document.getElementById('logEventos');
    if (!el) return;
    el.innerHTML = Sim.log.slice(0, 120).map((l) =>
      `<div class="lg-${l.clase === 'rojo' ? 'rojo' : l.clase === 'amar' ? 'amar' : l.clase === 'turno' ? 'turno' : 'info'}">[${l.marca}] ${l.texto}</div>`).join('');
  },
};
