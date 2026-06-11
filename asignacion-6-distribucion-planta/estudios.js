/* ============================================================
   Estudios Eléctricos — sub-paneles de la pestaña Unifilar
   (complementos del repo "Distribución Eléctrica": armónicos,
   selectividad, calculadora NEC y monitoreo ISO 50001)
   Los datos base de ELEC-REF-001 son la referencia válida.
   ============================================================ */

const Estudios = {
  sub: 'diagrama',
  kwhAcum: { ats: 0, mccA: 0, mccB: 0 },
  _ultimaHora: 0,

  init(cont, toolbar, miniPanel) {
    this.cont = cont;
    this.miniPanel = miniPanel;

    // barra de sub-pestañas dentro del Unifilar
    const bar = document.createElement('div');
    bar.className = 'subtabs';
    bar.innerHTML = `
      <button data-sub="diagrama" class="on">Diagrama unifilar</button>
      <button data-sub="armonicos">〜 Armónicos (IEEE 519)</button>
      <button data-sub="selectividad">⚡ Selectividad</button>
      <button data-sub="calculadora">🧮 Calculadora NEC</button>
      <button data-sub="monitoreo">📈 Monitoreo ISO 50001</button>`;
    toolbar.appendChild(bar);
    bar.querySelectorAll('button').forEach((b) => {
      b.onclick = () => {
        bar.querySelectorAll('button').forEach((x) => x.classList.remove('on'));
        b.classList.add('on');
        this.mostrar(b.dataset.sub);
      };
    });

    // contenedores de cada estudio
    this.paneles = {};
    for (const id of ['armonicos', 'selectividad', 'calculadora', 'monitoreo']) {
      const div = document.createElement('div');
      div.className = 'estudio-panel';
      div.style.display = 'none';
      cont.appendChild(div);
      this.paneles[id] = div;
    }
    this.construirArmonicos();
    this.construirSelectividad();
    this.construirCalculadora();
    this.construirMonitoreo();

    Bus.on('tick', () => { if (this.sub === 'monitoreo') this.actualizarMonitoreo(); });
  },

  mostrar(sub) {
    this.sub = sub;
    for (const [id, div] of Object.entries(this.paneles)) div.style.display = id === sub ? '' : 'none';
    this.miniPanel.style.display = sub === 'diagrama' ? '' : 'none';
    if (sub === 'monitoreo') this.actualizarMonitoreo();
    if (sub === 'armonicos') this.pintarArmonicos();
  },

  /* ============ 〜 ARMÓNICOS (IEEE 519) ============ */
  // Espectros escalados a los THDv reales del trabajo base:
  // Nave A 18.7 % → 3.2 % · Nave B 15.3 % → 2.9 % con AHF-01/02
  armNave: 'A',
  armFiltro: false,

  construirArmonicos() {
    const p = this.paneles.armonicos;
    p.innerHTML = `
      <div class="panel" style="max-width:1100px;margin:0 auto 14px">
        <h3>〜 Estudio de armónicos — IEEE 519 (complemento del unifilar ELEC-REF-001)</h3>
        <div style="font-size:11.5px;color:#56646f;margin-bottom:10px">
          Los VFDs (rectificadores de 6 pulsos) de MCC-A y MCC-B inyectan armónicos característicos
          (5º, 7º, 11º, 13º). Los filtros activos <b>AHF-01/AHF-02 (300 A)</b> los cancelan en tiempo real.
          Datos del trabajo base: THDv Nave A 18.7 % → 3.2 % · Nave B 15.3 % → 2.9 % · FP 0.82 → 0.96.
        </div>
        <div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:10px">
          <div class="vel-sim" style="max-width:260px;flex:1">
            <button id="armNaveA" class="on">Nave A (MCC-A)</button>
            <button id="armNaveB">Nave B (MCC-B)</button>
          </div>
          <button id="armToggle" class="btn-ahf">FILTRO AHF: DESACTIVADO ✗</button>
          <div id="armBadge"></div>
        </div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:14px" class="arm-grid">
          <div>
            <div style="font-size:11px;font-weight:700;margin-bottom:4px">Forma de onda de tensión (osciloscopio)</div>
            <svg id="armOsc" viewBox="0 0 520 240" style="width:100%;background:#10202e;border-radius:6px"></svg>
          </div>
          <div>
            <div style="font-size:11px;font-weight:700;margin-bottom:4px">Espectro armónico (% de la fundamental)</div>
            <svg id="armSpec" viewBox="0 0 520 240" style="width:100%;background:#fff;border:1px solid #ccd;border-radius:6px"></svg>
          </div>
        </div>
      </div>`;
    p.querySelector('#armNaveA').onclick = () => { this.armNave = 'A'; this._armBtn(); };
    p.querySelector('#armNaveB').onclick = () => { this.armNave = 'B'; this._armBtn(); };
    p.querySelector('#armToggle').onclick = () => {
      this.armFiltro = !this.armFiltro;
      const b = p.querySelector('#armToggle');
      b.textContent = this.armFiltro ? 'FILTRO AHF: ACTIVADO ✓' : 'FILTRO AHF: DESACTIVADO ✗';
      b.classList.toggle('activo', this.armFiltro);
      this.pintarArmonicos();
    };
  },
  _armBtn() {
    this.paneles.armonicos.querySelector('#armNaveA').classList.toggle('on', this.armNave === 'A');
    this.paneles.armonicos.querySelector('#armNaveB').classList.toggle('on', this.armNave === 'B');
    this.pintarArmonicos();
  },

  espectro() {
    // componentes base (sin filtro) que reproducen el THDv del trabajo base
    const baseA = { 5: 14.0, 7: 8.5, 11: 5.0, 13: 3.5, 17: 2.2, 19: 1.6 };  // ≈18.7 %
    const baseB = { 5: 11.5, 7: 7.0, 11: 4.0, 13: 2.8, 17: 1.8, 19: 1.3 };  // ≈15.3 %
    const base = this.armNave === 'A' ? baseA : baseB;
    const thdvSin = this.armNave === 'A' ? 18.7 : 15.3;
    const thdvCon = this.armNave === 'A' ? 3.2 : 2.9;
    const k = this.armFiltro ? thdvCon / thdvSin : 1;
    const comp = {};
    for (const [h, v] of Object.entries(base)) comp[h] = v * k;
    return { comp, thdv: this.armFiltro ? thdvCon : thdvSin };
  },

  pintarArmonicos() {
    const { comp, thdv } = this.espectro();
    const cumple = thdv < 5;
    document.getElementById('armBadge').innerHTML =
      `<span class="chip ${cumple ? 'ok' : 'err'}" style="font-size:13px;padding:6px 12px">THDv = ${thdv.toFixed(1)} % — ${cumple ? 'CUMPLE' : 'NO CUMPLE'} IEEE 519 (límite 5 %)</span>`;

    // osciloscopio
    const osc = document.getElementById('armOsc');
    osc.innerHTML = '';
    for (let i = 0; i <= 8; i++) {
      osc.appendChild(svgEl('line', { x1: i * 65, y1: 0, x2: i * 65, y2: 240, stroke: '#1e3a50', 'stroke-width': 0.6 }));
      if (i < 5) osc.appendChild(svgEl('line', { x1: 0, y1: i * 60, x2: 520, y2: i * 60, stroke: '#1e3a50', 'stroke-width': 0.6 }));
    }
    const onda = (conArm) => {
      let d = '';
      for (let px = 0; px <= 520; px += 2) {
        const t = (px / 520) * 4 * Math.PI;
        let y = Math.sin(t);
        if (conArm) for (const [h, v] of Object.entries(comp)) y += (v / 100) * Math.sin(h * t);
        d += (px === 0 ? 'M' : 'L') + px + ' ' + (120 - y * 85) + ' ';
      }
      return d;
    };
    osc.appendChild(svgEl('path', { d: onda(false), fill: 'none', stroke: '#5a7a95', 'stroke-width': 1.2, 'stroke-dasharray': '5 4' }));
    osc.appendChild(svgEl('path', { d: onda(true), fill: 'none', stroke: cumple ? '#4ade80' : '#fbbf24', 'stroke-width': 2.2 }));
    osc.appendChild(svgEl('text', { x: 10, y: 20, 'font-size': 11, fill: '#8fb8d8' }, `480 V · 60 Hz · Nave ${this.armNave} — gris: senoidal ideal · color: onda real`));

    // espectro de barras
    const spec = document.getElementById('armSpec');
    spec.innerHTML = '';
    const hs = [1, 5, 7, 11, 13, 17, 19];
    hs.forEach((h, i) => {
      const v = h === 1 ? 100 : comp[h] || 0;
      const alt = (v / 100) * 175;
      const x = 35 + i * 68;
      spec.appendChild(svgEl('rect', { x, y: 200 - alt, width: 38, height: alt, fill: h === 1 ? '#1565c0' : v > 5 ? '#d32f2f' : '#2e7d32', rx: 2 }));
      spec.appendChild(svgEl('text', { x: x + 19, y: 215, 'font-size': 10, 'text-anchor': 'middle', fill: '#333' }, 'H' + h));
      spec.appendChild(svgEl('text', { x: x + 19, y: 195 - alt, 'font-size': 9.5, 'text-anchor': 'middle', 'font-weight': 700, fill: '#333' }, v.toFixed(1) + '%'));
      spec.appendChild(svgEl('text', { x: x + 19, y: 232, 'font-size': 8, 'text-anchor': 'middle', fill: '#888' }, (h * 60) + ' Hz'));
    });
    spec.appendChild(svgEl('line', { x1: 20, y1: 200 - (5 / 100) * 175, x2: 500, y2: 200 - (5 / 100) * 175, stroke: '#d32f2f', 'stroke-width': 1, 'stroke-dasharray': '6 4' }));
    spec.appendChild(svgEl('text', { x: 505, y: 200 - (5 / 100) * 175 + 3, 'font-size': 8, fill: '#d32f2f', 'text-anchor': 'end' }, '5%'));
  },

  /* ============ ⚡ SELECTIVIDAD (cascada de falla) ============ */
  construirSelectividad() {
    const p = this.paneles.selectividad;
    p.innerHTML = `
      <div class="panel" style="max-width:1000px;margin:0 auto 14px">
        <h3>⚡ Simulador de selectividad — coordinación de protecciones (NEC 700 / IEC 60947)</h3>
        <div style="font-size:11.5px;color:#56646f;margin-bottom:10px">
          Demostración del trabajo base: una falla en la ensacadora del Módulo B activa <b>solo el breaker
          local (75 A · 18 kAIC)</b> sin afectar los niveles superiores — la torre GEA NIRO® (MCC-A) nunca se entera.
        </div>
        <div class="botones-sim" style="max-width:480px;margin-bottom:10px">
          <button id="btnFalla" class="primario">⚡ Simular falla en ensacadora Mod. B</button>
          <button id="btnFallaReset">↺ Restablecer</button>
        </div>
        <svg id="svgSelect" viewBox="0 0 900 430" style="width:100%;max-width:950px"></svg>
        <div id="selResultado" style="font-size:12px;margin-top:8px"></div>
      </div>`;
    this.dibujarSelectividad();
    p.querySelector('#btnFalla').onclick = () => this.simularFalla();
    p.querySelector('#btnFallaReset').onclick = () => this.resetFalla();
  },

  dibujarSelectividad() {
    const svg = document.getElementById('svgSelect');
    svg.innerHTML = '';
    const caja = (x, y, w, nombre, sub) => {
      const g = svgEl('g', {});
      const r = svgEl('rect', { x, y, width: w, height: 52, rx: 5, fill: '#fff', stroke: '#1a3a5c', 'stroke-width': 2 });
      g.appendChild(r);
      g.appendChild(svgEl('text', { x: x + w / 2, y: y + 21, 'font-size': 11.5, 'text-anchor': 'middle', 'font-weight': 700, fill: '#1a3a5c' }, nombre));
      g.appendChild(svgEl('text', { x: x + w / 2, y: y + 38, 'font-size': 9.5, 'text-anchor': 'middle', fill: '#666' }, sub));
      const estado = svgEl('text', { x: x + w / 2, y: y + 66, 'font-size': 10, 'text-anchor': 'middle', 'font-weight': 700, fill: '#2e7d32' }, '● CERRADO');
      g.appendChild(estado);
      svg.appendChild(g);
      return { rect: r, estado };
    };
    this.selNodos = {
      main: caja(330, 15, 240, 'MAIN BREAKER — Edif. C', '1600 A · 65 kAIC'),
      ats: caja(330, 110, 240, 'ATS', '1600 A · 85 kAIC'),
      mccA: caja(120, 215, 220, 'MCC-A — Nave A (torre)', '1600 A · 65 kAIC'),
      mccB: caja(560, 215, 220, 'MCC-B — Nave B', '600 A nom / 800 A frame · 35 kAIC'),
      brk: caja(560, 320, 220, 'Breaker local ensacadora', '75 A · 18 kAIC'),
    };
    this.selLineas = [
      svgEl('line', { x1: 450, y1: 67, x2: 450, y2: 110, stroke: '#c62828', 'stroke-width': 4 }),
      svgEl('line', { x1: 450, y1: 162, x2: 230, y2: 215, stroke: '#c62828', 'stroke-width': 3.5 }),
      svgEl('line', { x1: 450, y1: 162, x2: 670, y2: 215, stroke: '#c62828', 'stroke-width': 3.5 }),
      svgEl('line', { x1: 670, y1: 267, x2: 670, y2: 320, stroke: '#c62828', 'stroke-width': 3 }),
    ];
    this.selLineas.forEach((l) => svg.appendChild(l));
    // motor y punto de falla
    svg.appendChild(svgEl('circle', { cx: 670, cy: 405, r: 18, fill: '#fff', stroke: '#1a3a5c', 'stroke-width': 2 }));
    svg.appendChild(svgEl('text', { x: 670, y: 410, 'font-size': 11, 'text-anchor': 'middle', 'font-weight': 800, fill: '#1a3a5c' }, 'M'));
    this.selLineaMotor = svgEl('line', { x1: 670, y1: 372, x2: 670, y2: 387, stroke: '#c62828', 'stroke-width': 2.5 });
    svg.appendChild(this.selLineaMotor);
    svg.appendChild(svgEl('text', { x: 720, y: 410, 'font-size': 10, fill: '#666' }, 'Ensacadora H&B 75 HP'));
    this.selRayo = svgEl('text', { x: 640, y: 398, 'font-size': 22, opacity: 0 }, '⚡');
    svg.appendChild(this.selRayo);
    // torre sigue viva (indicador)
    this.selTorreTxt = svgEl('text', { x: 230, y: 300, 'font-size': 10.5, 'text-anchor': 'middle', fill: '#2e7d32', 'font-weight': 700 }, '');
    svg.appendChild(this.selTorreTxt);
    document.getElementById('selResultado').innerHTML = '';
  },

  simularFalla() {
    this.resetFalla();
    const N = this.selNodos;
    this.selRayo.setAttribute('opacity', 1);
    this.selRayo.innerHTML = '⚡';
    // animación de la corriente de falla subiendo (línea roja parpadeante)
    [this.selLineaMotor, this.selLineas[3]].forEach((l) => {
      l.setAttribute('stroke-dasharray', '8 5');
      l.classList.add('linea-flujo-anim');
      l.setAttribute('stroke', '#ff1744');
      l.setAttribute('stroke-width', 5);
    });
    document.getElementById('selResultado').innerHTML = '<span class="chip warn">⏱ Corriente de falla detectada — curva tiempo-corriente del breaker local…</span>';
    setTimeout(() => {
      // dispara SOLO el breaker local
      N.brk.rect.setAttribute('stroke', '#d32f2f');
      N.brk.rect.setAttribute('fill', '#fdecea');
      N.brk.estado.textContent = '✂ DISPARADO (abierto)';
      N.brk.estado.setAttribute('fill', '#d32f2f');
      [this.selLineaMotor, this.selLineas[3]].forEach((l) => {
        l.classList.remove('linea-flujo-anim');
        l.setAttribute('stroke', '#9e9e9e');
        l.setAttribute('stroke-width', 2);
        l.setAttribute('stroke-dasharray', '4 4');
      });
      this.selRayo.setAttribute('opacity', 0);
      this.selTorreTxt.textContent = '✓ MCC-A y la torre GEA NIRO® siguen operando sin interrupción';
      document.getElementById('selResultado').innerHTML =
        `<span class="chip ok" style="font-size:12px;padding:5px 10px">✓ SELECTIVIDAD TOTAL</span>
         <span style="margin-left:8px">Disparó únicamente el breaker local (75 A · 18 kAIC) en ~25 ms. Main, ATS, MCC-A y MCC-B permanecen cerrados —
         coordinación verificada conforme NEC 700 / IEC 60947 (dato del trabajo base).</span>`;
    }, 1400);
  },

  resetFalla() {
    this.dibujarSelectividad();
  },

  /* ============ 🧮 CALCULADORA NEC ============ */
  // FLC según NEC 430.250 (460 V, 3Ø) · calibre THHN Cu 75 °C al 125 % FLC
  MOTORES: [
    [5, 7.6, '15 A', '14 AWG', 'EMT ½"'], [7.5, 11, '20 A', '14 AWG', 'EMT ½"'],
    [10, 14, '25 A', '12 AWG', 'EMT ½"'], [15, 21, '40 A', '10 AWG', 'EMT ¾"'],
    [20, 27, '50 A', '10 AWG', 'EMT ¾"'], [25, 34, '70 A', '8 AWG', 'EMT ¾"'],
    [30, 40, '80 A', '8 AWG', 'EMT 1"'], [40, 52, '100 A', '6 AWG', 'EMT 1"'],
    [50, 65, '125 A', '4 AWG', 'EMT 1¼"'], [60, 77, '150 A', '3 AWG', 'EMT 1¼"'],
    [75, 96, '200 A', '1 AWG', 'EMT 1½"'], [100, 124, '250 A', '2/0 AWG', 'EMT 2"'],
    [125, 156, '300 A', '3/0 AWG', 'EMT 2"'], [150, 180, '350 A', '4/0 AWG', 'EMT 2½"'],
  ],
  AREAS_THHN: { '14': 0.0097, '12': 0.0133, '10': 0.0211, '8': 0.0366, '6': 0.0507, '4': 0.0824, '2': 0.1158, '1': 0.1562, '1/0': 0.1855, '2/0': 0.2223, '3/0': 0.2679, '4/0': 0.3237 },
  EMT_40: [['½"', 0.122], ['¾"', 0.213], ['1"', 0.346], ['1¼"', 0.598], ['1½"', 0.814], ['2"', 1.342], ['2½"', 2.343], ['3"', 3.538]],

  construirCalculadora() {
    const p = this.paneles.calculadora;
    const filasMotores = this.MOTORES.map(([hp, flc, brk, cal, emt]) => {
      const nuestro = [10, 50, 75, 150].includes(hp);
      return `<tr ${nuestro ? 'style="background:#e8f5e9;font-weight:700"' : ''}><td>${hp} HP${nuestro ? ' ★' : ''}</td><td>${flc} A</td><td>${brk}</td><td>${cal} THHN</td><td>${emt}</td></tr>`;
    }).join('');
    p.innerHTML = `
      <div style="max-width:1100px;margin:0 auto">
      <div class="panel">
        <h3>🧮 Corrección de factor de potencia (kVAr) — verifica el banco de 600 kVAr del trabajo base</h3>
        <div class="calc-fila">
          <label>Carga (kW) <input type="number" id="pfcKw" value="1200" min="50" max="3000"></label>
          <label>FP actual <input type="number" id="pfcFp1" value="0.82" min="0.5" max="0.99" step="0.01"></label>
          <label>FP objetivo <input type="number" id="pfcFp2" value="0.96" min="0.7" max="1" step="0.01"></label>
        </div>
        <div id="pfcOut" class="calc-out"></div>
      </div>
      <div class="panel">
        <h3>⚙ Base de datos de motores 480 V · 3Ø (NEC 430.250 · THHN Cu 75 °C · ★ = motores de REFRESH)</h3>
        <div style="max-height:260px;overflow-y:auto">
        <table class="cal"><tr><th>Motor</th><th>FLC</th><th>Breaker (250 %)</th><th>Calibre (125 % FLC)</th><th>Conduit</th></tr>${filasMotores}</table>
        </div>
      </div>
      <div class="panel">
        <h3>🔧 Llenado de conduit EMT (NEC Cap. 9, Tablas 4 y 5 — máx 40 %)</h3>
        <div class="calc-fila">
          <label>Calibre THHN <select id="cfAwg">${Object.keys(this.AREAS_THHN).map((a) => `<option ${a === '12' ? 'selected' : ''}>${a}</option>`).join('')}</select></label>
          <label># conductores <input type="number" id="cfN" value="3" min="1" max="30"></label>
        </div>
        <div id="cfOut" class="calc-out"></div>
      </div>
      </div>`;
    const calcPfc = () => {
      const P = +p.querySelector('#pfcKw').value || 0;
      const f1 = Math.min(0.99, +p.querySelector('#pfcFp1').value || 0.82);
      const f2 = Math.min(1, +p.querySelector('#pfcFp2').value || 0.96);
      const q = P * (Math.tan(Math.acos(f1)) - Math.tan(Math.acos(f2)));
      const i1 = (P * 1000) / (Math.sqrt(3) * 480 * f1);
      const i2 = (P * 1000) / (Math.sqrt(3) * 480 * f2);
      p.querySelector('#pfcOut').innerHTML =
        `<div class="kpi"><div class="k-etiq">kVAr requeridos</div><div class="k-val">${fmt(q)}</div><div class="k-sub">${q <= 600 ? '✓ el banco de 600 kVAr del diseño es suficiente' : '⚠ supera los 600 kVAr instalados'}</div></div>
         <div class="kpi"><div class="k-etiq">Corriente antes</div><div class="k-val">${fmt(i1)} A</div><div class="k-sub">a FP ${f1}</div></div>
         <div class="kpi"><div class="k-etiq">Corriente después</div><div class="k-val">${fmt(i2)} A</div><div class="k-sub">a FP ${f2}</div></div>
         <div class="kpi"><div class="k-etiq">Reducción de corriente</div><div class="k-val">${(100 * (1 - i2 / i1)).toFixed(1)} %</div><div class="k-sub">menos pérdidas I²R y cargos por reactiva</div></div>`;
    };
    const calcCf = () => {
      const awg = p.querySelector('#cfAwg').value;
      const n = +p.querySelector('#cfN').value || 1;
      const area = this.AREAS_THHN[awg] * n;
      const emt = this.EMT_40.find(([, a]) => a >= area);
      p.querySelector('#cfOut').innerHTML =
        `<div class="kpi"><div class="k-etiq">Área total conductores</div><div class="k-val">${area.toFixed(3)} in²</div><div class="k-sub">${n} × THHN ${awg} AWG</div></div>
         <div class="kpi"><div class="k-etiq">Conduit mínimo</div><div class="k-val">${emt ? 'EMT ' + emt[0] : '> 3"'}</div><div class="k-sub">${emt ? `${((area / emt[1]) * 40).toFixed(1)} % de llenado (límite 40 %)` : 'usar bandeja portacables'}</div></div>
         <div class="kpi"><div class="k-etiq">Referencia REFRESH</div><div class="k-val">EMT ¾"</div><div class="k-sub">circuito típico 120 V: 3× THHN 12 AWG (F+N+T) ✓</div></div>`;
    };
    ['pfcKw', 'pfcFp1', 'pfcFp2'].forEach((id) => { p.querySelector('#' + id).oninput = calcPfc; });
    ['cfAwg', 'cfN'].forEach((id) => { p.querySelector('#' + id).oninput = calcCf; });
    calcPfc(); calcCf();
  },

  /* ============ 📈 MONITOREO ISO 50001 ============ */
  construirMonitoreo() {
    const p = this.paneles.monitoreo;
    p.innerHTML = `
      <div class="panel" style="max-width:1100px;margin:0 auto 14px">
        <h3>📈 Monitoreo de energía ISO 50001 — medidores clase 0.5S (alimentados por la simulación en vivo)</h3>
        <div style="font-size:11.5px;color:#56646f;margin-bottom:10px">
          Los valores se calculan con el estado real de la pestaña 5: carga de la torre, módulo de envasado activo
          y mantenimiento del miércoles (MCC-B desenergizado). FP corregido a 0.96 por el banco de capacitores + AHF.
        </div>
        <div class="kpis" id="medidores" style="grid-template-columns:repeat(auto-fit,minmax(230px,1fr))"></div>
        <h3 style="margin-top:16px">🌡 Termografía de barras (bus R/S/T/N)</h3>
        <div id="termo" style="display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:10px"></div>
      </div>`;
    this.actualizarMonitoreo();
  },

  actualizarMonitoreo() {
    const med = document.getElementById('medidores');
    if (!med) return;
    // potencias estimadas desde el estado real de la simulación
    const kwA = 85 + 295 * (Sim.torreOutKgH / 1500);                       // mezclado+bombas+EF-101
    const kwB = Sim.enMantenimiento ? 0 : Sim.moduloActivo ? 65 + 85 * (Sim.envasadoKgH / 2700) : 18;
    const kwServ = 95;                                                      // Edif. C/D/E + iluminación
    const kwAts = kwA + kwB + kwServ;
    // integrar kWh con el reloj simulado
    const dH = Math.max(0, Sim.horasTranscurridas - this._ultimaHora);
    this._ultimaHora = Sim.horasTranscurridas;
    this.kwhAcum.ats += kwAts * dH; this.kwhAcum.mccA += kwA * dH; this.kwhAcum.mccB += kwB * dH;

    const tarjeta = (nombre, kw, kwh, off) => `
      <div class="kpi" style="${off ? 'opacity:.55' : ''}">
        <div class="k-etiq">${nombre} · clase 0.5S</div>
        <div class="k-val">${fmt(kw)} kW</div>
        <div class="k-sub">FP 0.96 · ${fmt(kwh)} kWh acumulados · ${off ? '⚠ DESENERGIZADO (mantenimiento)' : '● energizado'}</div>
      </div>`;
    med.innerHTML =
      tarjeta('ATS — totalizador planta', kwAts, this.kwhAcum.ats, false) +
      tarjeta('MCC-A — Nave A (torre 24/7)', kwA, this.kwhAcum.mccA, false) +
      tarjeta('MCC-B — Nave B (envasado)', kwB, this.kwhAcum.mccB, Sim.enMantenimiento);

    // termografía: temperatura ∝ carga
    const termo = document.getElementById('termo');
    const barras = (nombre, kw, max) => {
      const fases = ['R', 'S', 'T', 'N'].map((f, i) => {
        const t = f === 'N' ? 32 + (kw / max) * 6 : 35 + (kw / max) * 28 + i * 1.3;
        const color = t > 60 ? '#d32f2f' : t > 50 ? '#f9a825' : '#2e7d32';
        return `<div style="display:flex;align-items:center;gap:6px;font-size:10.5px">
          <b style="width:14px">${f}</b>
          <div style="flex:1;height:9px;background:#eee;border-radius:4px;overflow:hidden"><div style="width:${Math.min(100, (t / 75) * 100)}%;height:100%;background:${color}"></div></div>
          <span style="width:48px;text-align:right;font-variant-numeric:tabular-nums">${t.toFixed(1)} °C</span></div>`;
      }).join('');
      return `<div class="kpi"><div class="k-etiq">${nombre}</div>${fases}<div class="k-sub" style="margin-top:4px">límite de alarma 60 °C · conexiones verificadas</div></div>`;
    };
    termo.innerHTML = barras('Barras MCC-A', kwA, 380) + barras('Barras MCC-B', kwB, 150) + barras('Barras ATS', kwAts, 620);
  },
};
