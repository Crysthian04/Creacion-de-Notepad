/* ============================================================
   Pestaña 5 — Simulación de Producción (interfaz)
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

        <div class="panel">
          <h3>📅 Calendario del ciclo semanal (21 turnos)</h3>
          <table class="cal" id="tablaCal"></table>
          <div style="font-size:10px;color:#7a8a99;margin-top:6px">T1 06:00–14:00 · T2 14:00–22:00 · T3 22:00–06:00 · Setups de 1 h al inicio del turno · La torre GEA NIRO® nunca se detiene (24/7).</div>
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
          <h3>🏭 Línea de proceso — 10 etapas con fase del producto</h3>
          <div id="sankey"></div>
          <div style="font-size:10.5px;margin-top:6px">
            <span class="chip" style="background:#2196f3">🔵 Líquido / slurry (65–75 °C)</span>
            <span class="chip" style="background:#ff9800">🟠 Gránulo caliente 60–80 °C (cambio de fase en la torre)</span>
            <span class="chip" style="background:#fbc02d;color:#5d4a00">🟡 Polvo frío &lt;35 °C</span>
            <span class="chip" style="background:#4caf50">🟢 Producto envasado / pallets</span>
          </div>
        </div>

        <div class="panel">
          <h3>📦 Capacidades de referencia (Asignación #4)</h3>
          <table class="cal">
            <tr><th>Tipo</th><th>kg/h</th><th>kg/día</th><th>kg/mes</th></tr>
            <tr><td>Diseño (100 %)</td><td>1,500</td><td>36,000</td><td>1,080,000</td></tr>
            <tr><td>Sistema (85 %)</td><td>1,275</td><td>30,600</td><td>918,000</td></tr>
            <tr><td><b>Real (75 %) — predeterminado</b></td><td><b>1,125</b></td><td><b>27,000</b></td><td><b>810,000</b></td></tr>
          </table>
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
    cont.querySelectorAll('.vel-sim button').forEach((b) => {
      b.onclick = () => {
        cont.querySelectorAll('.vel-sim button').forEach((x) => x.classList.remove('on'));
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
      cont.querySelectorAll('.vel-sim button').forEach((x) => x.classList.toggle('on', x.dataset.vel === '60'));
    };

    this.construirCalendario();
    this.construirSankey();
    Bus.on('tick', () => this.actualizar());
    Bus.on('log', () => this.pintarLog());
    this.actualizar();
    this.pintarLog();
  },

  construirCalendario() {
    const tabla = document.getElementById('tablaCal');
    let html = '<tr><th>Día</th><th>T1</th><th>T2</th><th>T3</th></tr>';
    PLANT_DATA.calendario.forEach((d, di) => {
      html += `<tr><td><b>${d.dia}</b></td>`;
      d.turnos.forEach((tu, ti) => {
        let txt, cls = '';
        if (tu.act === 'pack') txt = PLANT_DATA.formatos[tu.formato].nombre;
        else if (tu.act === 'setup') { txt = `SETUP ${tu.de}→${tu.a}`; cls = 'setup'; }
        else if (tu.act === 'mant') { txt = 'MANTEN.'; cls = 'mant'; }
        else { txt = 'Libre/buffer'; cls = 'libre'; }
        html += `<td class="${cls}" id="cal-${di}-${ti}">${txt}</td>`;
      });
      html += '</tr>';
    });
    tabla.innerHTML = html;
  },

  construirSankey() {
    const W = 1180, H = 300;
    const svg = svgEl('svg', { viewBox: `0 0 ${W} ${H}`, width: '100%' });
    document.getElementById('sankey').appendChild(svg);
    this.nodos = [];
    const nx = (i) => 14 + i * 117;

    // conectores
    this.conectores = [];
    for (let i = 0; i < 9; i++) {
      const linea = svgEl('line', { x1: nx(i) + 100, y1: 120, x2: nx(i + 1), y2: 120, 'stroke-width': 7, stroke: '#ccc' });
      svg.appendChild(linea);
      const etiqFase = svgEl('text', { x: nx(i) + 108, y: 108, 'font-size': 9, fill: '#555', 'text-anchor': 'middle' }, '');
      const etiqTemp = svgEl('text', { x: nx(i) + 108, y: 138, 'font-size': 8.5, fill: '#888', 'text-anchor': 'middle' }, '');
      svg.appendChild(etiqFase); svg.appendChild(etiqTemp);
      this.conectores.push({ linea, etiqFase, etiqTemp });
    }

    PLANT_DATA.flujo.forEach((f, i) => {
      const g = svgEl('g', { class: 'clicable' });
      const x = nx(i);
      const esTolva = f.n === 8;
      const rect = svgEl('rect', { x, y: esTolva ? 60 : 85, width: 100, height: esTolva ? 110 : 70, rx: 6, fill: '#fff', stroke: f.color, 'stroke-width': 2.5 });
      g.appendChild(rect);
      g.appendChild(svgEl('text', { x: x + 50, y: 78, 'font-size': 13, 'text-anchor': 'middle', 'font-weight': 700, fill: '#1a3a5c' }, '①②③④⑤⑥⑦⑧⑨⑩'[i]));
      const nombre = f.nombre.length > 30 ? f.nombre.slice(0, 28) + '…' : f.nombre;
      const t1 = svgEl('text', { x: x + 50, y: esTolva ? 175 : 100, 'font-size': 7.8, 'text-anchor': 'middle', fill: '#1a3a5c', 'font-weight': 600 }, nombre);
      g.appendChild(t1);
      const valKg = svgEl('text', { x: x + 50, y: esTolva ? 188 : 116, 'font-size': 11, 'text-anchor': 'middle', 'font-weight': 700, fill: f.color }, '0 kg/h');
      g.appendChild(valKg);
      // mini-medidor de utilización
      const barBg = svgEl('rect', { x: x + 12, y: esTolva ? 192 : 132, width: 76, height: 7, rx: 3, fill: '#eee', stroke: '#bbb', 'stroke-width': 0.5 });
      const bar = svgEl('rect', { x: x + 12, y: esTolva ? 192 : 132, width: 0, height: 7, rx: 3, fill: f.color });
      const barTxt = svgEl('text', { x: x + 50, y: esTolva ? 211 : 151, 'font-size': 8, 'text-anchor': 'middle', fill: '#777' }, 'util 0 %');
      g.appendChild(barBg); g.appendChild(bar); g.appendChild(barTxt);

      let tanque = null;
      if (esTolva) {
        g.appendChild(svgEl('rect', { x: x + 25, y: 88, width: 50, height: 75, rx: 4, fill: '#f5f5f5', stroke: '#8d6e63', 'stroke-width': 1.5 }));
        tanque = svgEl('rect', { x: x + 26.5, y: 161.5, width: 47, height: 0, fill: '#fbc02d' });
        g.appendChild(tanque);
        g.appendChild(svgEl('rect', { x: x + 25, y: 88, width: 50, height: 75, rx: 4, fill: 'none', stroke: '#8d6e63', 'stroke-width': 1.5 }));
        const pctTxt = svgEl('text', { x: x + 50, y: 128, 'font-size': 12, 'text-anchor': 'middle', 'font-weight': 700, fill: '#1a3a5c' }, '40 %');
        g.appendChild(pctTxt);
        this.tolvaPctTxt = pctTxt;
        this.tolvaTanque = tanque;
      }
      g.addEventListener('click', () => abrirFicha(f.equipo));
      svg.appendChild(g);
      this.nodos.push({ rect, valKg, bar, barTxt, f });
    });
    svg.appendChild(svgEl('text', { x: 14, y: 20, 'font-size': 11, fill: '#7a8a99' }, 'Flujo del producto →   (clic en cada nodo para abrir su ficha técnica)'));
  },

  actualizar() {
    // KPIs
    const pctTolva = (Sim.tolvaKg / PLANT_DATA.tolvasCapacidadKg) * 100;
    const f = Sim.formatoActivo ? PLANT_DATA.formatos[Sim.formatoActivo] : null;
    const cuello = Sim.alimentacionKgH > 1500 ? 'TORRE (⛔ activo)' : pctTolva >= 100 ? 'TOLVAS LLENAS' : 'Torre GEA NIRO® (1,500 kg/h)';
    const kpis = [
      ['kg/h instantáneo (torre)', fmt(Sim.torreOutKgH), 'salida de polvo', ''],
      ['kg acumulados del día', fmt(Sim.kgDia), 'envasados desde 06:00', ''],
      ['uds/h formato activo', f ? `${fmt(Sim.envasadoUdsH)}` : '—', f ? f.nombre + ' · Módulo ' + f.modulo : Sim.enMantenimiento ? 'mantenimiento' : 'sin envasado', ''],
      ['OEE estimado', Sim.oee().toFixed(1) + ' %', 'vs capacidad de diseño', ''],
      ['Nivel de tolvas', pctTolva.toFixed(0) + ' %', fmt(Sim.tolvaKg) + ' / 15,000 kg', pctTolva >= 100 ? 'err' : pctTolva >= 80 ? 'warn' : ''],
      ['Cuello de botella', cuello.split(' (')[0], cuello.includes('⛔') ? 'límite excedido' : 'restricción del sistema (TOC)', Sim.alertas.torre || pctTolva >= 100 ? 'err' : ''],
    ];
    document.getElementById('kpis').innerHTML = kpis.map(([e, v, s, c]) =>
      `<div class="kpi ${c}"><div class="k-etiq">${e}</div><div class="k-val">${v}</div><div class="k-sub">${s}</div></div>`).join('');

    // Alertas
    const cont = document.getElementById('alertas');
    const al = Object.values(Sim.alertas);
    cont.innerHTML = al.length
      ? al.map((a) => `<div class="alerta ${a.nivel}">${a.texto}</div>`).join('')
      : '<div class="alerta info" style="animation:none">✅ Planta eficiente — sin alertas. Torre y envasado balanceados según el calendario semanal.</div>';

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
    this.nodos.forEach((n, i) => {
      const esTolva = i === 7;
      n.valKg.textContent = esTolva ? fmt(valores[i]) + ' kg' : fmt(valores[i]) + ' kg/h';
      const util = Math.min(100, (valores[i] / capacidades[i]) * 100) || 0;
      n.bar.setAttribute('width', (util / 100) * 76);
      n.barTxt.textContent = 'util ' + util.toFixed(0) + ' %';
      // alertas visuales
      if (i === 4) n.rect.classList.toggle('alerta-parpadeo', !!Sim.alertas.torre);
      if (esTolva) {
        n.rect.classList.toggle('alerta-parpadeo', !!(Sim.alertas.tolvas && Sim.alertas.tolvas.nivel === 'roja'));
        n.rect.classList.toggle('alerta-amarilla-parpadeo', !!(Sim.alertas.tolvas && Sim.alertas.tolvas.nivel === 'amarilla'));
      }
      const apagado = (i === 8 || i === 9) && !Sim.moduloActivo;
      n.rect.setAttribute('opacity', apagado ? 0.35 : 1);
    });
    if (this.tolvaTanque) {
      const h = (pctTolva / 100) * 72;
      this.tolvaTanque.setAttribute('height', h);
      this.tolvaTanque.setAttribute('y', 161.5 - h);
      this.tolvaTanque.setAttribute('fill', pctTolva >= 100 ? '#d32f2f' : pctTolva >= 80 ? '#f9a825' : '#fbc02d');
      this.tolvaPctTxt.textContent = pctTolva.toFixed(0) + ' %';
    }
    // conectores: color por fase
    const coloresTramo = ['#8d6e63', '#8d6e63', '#2196f3', '#2196f3', '#ff9800', '#fbc02d', '#fbc02d', '#fbc02d', '#4caf50'];
    this.conectores.forEach((c, i) => {
      const activo = i >= 7 ? Sim.envasadoKgH > 1 : i >= 4 ? Sim.torreOutKgH > 1 : Sim.alimentacionKgH > 1;
      c.linea.setAttribute('stroke', activo ? coloresTramo[i] : '#ddd');
      c.etiqFase.textContent = fases[i + 1][0];
      c.etiqTemp.textContent = fases[i + 1][1];
    });
  },

  pintarLog() {
    const el = document.getElementById('logEventos');
    if (!el) return;
    el.innerHTML = Sim.log.slice(0, 120).map((l) =>
      `<div class="lg-${l.clase === 'rojo' ? 'rojo' : l.clase === 'amar' ? 'amar' : l.clase === 'turno' ? 'turno' : 'info'}">[${l.marca}] ${l.texto}</div>`).join('');
  },
};
