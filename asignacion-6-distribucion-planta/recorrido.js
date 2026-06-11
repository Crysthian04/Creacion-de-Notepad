/* ============================================================
   Complementos del Plano 2D (del repo "Proyecto-Refresh"):
   - Recorrido narrado de 10 pasos con partícula animada
   - Checklist de cumplimiento normativo (7 verificaciones)
   - Capa de mezzanines con tuberías elevadas
   - Temas de color (Claro / Blueprint / Oscuro)
   Los datos narrados son los del trabajo base (Asignación #6).
   ============================================================ */

const Recorrido = {
  paso: 0,
  reproduciendo: false,
  _timer: null,

  PASOS: [
    { t: 'Recepción de materia prima', n: 'Los camiones ingresan por el vial norte (7.00 m) y descargan en los 4 silos exteriores Ø2.50 m del patio techado de 15×10 m. Los elevadores de cangilones suben el material a granel. Aquí opera la puerta QC-1: ¿la MP cumple ficha técnica?' },
    { t: 'Dosificación y pesado', n: 'El transporte neumático lleva cada ingrediente a las básculas dosificadoras controladas por PLC/SCADA. La receta se pesa con precisión y se transfiere a la Nave A de proceso (40×20 m).' },
    { t: 'Mezclado fase húmeda', n: 'En los tanques TK-101 y TK-102 (SS 316L, 10,000 L, con agitadores de 75 HP) se prepara el SLURRY: 35–45 % de sólidos a 65–75 °C, calentado con vapor de S-1 y agua desmineralizada de S-3. Trabajan alternados: uno alimenta mientras el otro prepara. Puerta QC-2: ¿slurry en especificación?' },
    { t: 'Bombeo y filtrado a alta presión', n: 'La bomba P-101 (50 HP, con P-102 de reserva N+1) eleva el slurry a 100–250 bar. El filtro en Y F-401 protege la boquilla atomizadora de partículas gruesas. La línea cuenta con PT-401, FT-402 y la válvula de control PCV-401.' },
    { t: 'Torre de secado GEA NIRO® — CUELLO DE BOTELLA', n: 'El corazón de la planta (base 12×14 m, cámara de 15–20 m, hasta 120 t): el slurry se atomiza en aire caliente y ocurre el CAMBIO DE FASE de líquido a gránulo sólido con humedad <5 %, saliendo a 60–80 °C. Capacidad máxima 1,500 kg/h — limita toda la planta (TOC) y NUNCA se detiene (24/7).' },
    { t: 'Enfriado y tamizado', n: 'El VIBRO-FLUIDIZER® (4×2 m) enfría el gránulo a <35 °C y lo clasifica por mallas. Los finos retornan a la torre por línea neumática. Puerta QC-3: ¿humedad ≤5 %? Si no, el gránulo va a retrabajo hacia el mezclado.' },
    { t: 'Post-adición', n: 'El ribbon blender incorpora los componentes termosensibles que no pueden pasar por la torre: enzimas, fragancias y perlas de color. El polvo queda terminado.' },
    { t: 'Tolvas buffer', n: '3 tolvas de 5,000 kg (15,000 kg totales) en plataforma elevada desacoplan la torre del envasado: autonomía de 13.3 h a 1,125 kg/h. Acumulan durante setups y el miércoles de mantenimiento. El polvo cruza al envasado por el pasillo técnico cerrado de 3.00 m.' },
    { t: 'Envasado — línea única con bifurcación', n: 'El distribuidor de flujo dirige el polvo a UN solo módulo a la vez: Módulo A (VFFS ROVEMA — bolsas 500 g/1 kg/3 kg para hogar) o Módulo B (ensacadora HAVER & BOECKER — sacos 5/20/50 kg industriales). Checkweigher + detector de metales verifican cada unidad (puerta QC-4 → cuarentena si falla).' },
    { t: 'Paletizado y despacho', n: 'El robot paletizador (75 HP) arma los mosaicos sobre pallets de 1.20×1.00 m. Los montacargas (pasillos de 3.50 m) llevan el producto a las 4 bahías de despacho del sur, donde sale al mercado nacional. Fin del recorrido ①→⑩.' },
  ],

  CHECKS: [
    ['Vial perimetral ≥ 7.00 m', '7.00 m con radios de giro R 15.00', true],
    ['Área de expansión ≥ 30 %', '3,000 m² al este = 30 % del terreno', true],
    ['Pasillos peatonales ≥ 2.00 m (SENADIS)', '2.00 m + giro peatonal 1.50×1.50 m + puestos accesibles', true],
    ['Pasillos de montacargas ≥ 3.50 m', '3.50 m con espejos convexos y semáforos', true],
    ['Silos Ø 2.50 m', '4 silos Ø2.50 m + elevadores de cangilones', true],
    ['Zonificación ATEX', 'Edificio C (calderas, compresores, eléctrica) y zonas de polvo en Nave A', true],
    ['Portones cortafuego 2.40 m', 'Doble hoja con sello hermético entre áreas', true],
  ],

  init() {
    const cont = document.getElementById('vista2d');
    const svg = Plano2D.svg;
    const tb = cont.querySelector('.toolbar');

    // ---- botones de la barra ----
    tb.insertAdjacentHTML('beforeend', `
      <label class="toggle" id="tgRecorrido">🎬 Recorrido del proceso</label>
      <label class="toggle" id="tgChecks">✓ Cumplimiento normativo</label>
      <label class="toggle" id="tgMezz">🏗 Mezzanines</label>
      <button id="btnTema">🎨 Tema: Claro</button>`);

    // ---- capa de mezzanines (plataformas elevadas + tuberías) ----
    this.gMezz = svgEl('g', { style: 'display:none' });
    const defs = svgEl('defs', {});
    const patron = svgEl('pattern', { id: 'hatchMezz', width: 1.4, height: 1.4, patternUnits: 'userSpaceOnUse', patternTransform: 'rotate(45)' });
    patron.appendChild(svgEl('line', { x1: 0, y1: 0, x2: 0, y2: 1.4, stroke: '#5c6bc0', 'stroke-width': 0.25 }));
    defs.appendChild(patron);
    svg.appendChild(defs);
    const mezz = (x, y, w, h, etiq) => {
      const g = svgEl('g', {});
      g.appendChild(svgEl('rect', { x, y, width: w, height: h, fill: 'url(#hatchMezz)', 'fill-opacity': 0.55, stroke: '#3949ab', 'stroke-width': 0.3, rx: 0.3 }));
      g.appendChild(svgEl('rect', { x, y, width: w, height: h, fill: '#9fa8da', opacity: 0.18 }));
      g.appendChild(svgEl('text', { x: x + w / 2, y: y - 0.5, 'font-size': 1.05, 'text-anchor': 'middle', fill: '#3949ab', 'font-weight': 700 }, etiq));
      // escalera (símbolo)
      g.appendChild(svgEl('rect', { x: x + 0.4, y: y + 0.4, width: 1.2, height: 2.4, fill: 'none', stroke: '#3949ab', 'stroke-width': 0.18 }));
      for (let i = 1; i <= 4; i++) g.appendChild(svgEl('line', { x1: x + 0.4, y1: y + 0.4 + i * 0.48, x2: x + 1.6, y2: y + 0.4 + i * 0.48, stroke: '#3949ab', 'stroke-width': 0.14 }));
      g.appendChild(svgEl('text', { x: x + 1, y: y + 3.6, 'font-size': 0.6, 'text-anchor': 'middle', fill: '#3949ab' }, 'SUBE'));
      this.gMezz.appendChild(g);
    };
    mezz(33, 43.5, 14.5, 9.5, 'MEZZANINE NAVE A · +4.50 m (plataforma técnica)');
    mezz(31, 63, 8, 4, 'MEZZANINE NAVE B · +3.20 m');
    // tuberías elevadas animadas sobre los mezzanines
    const tuberias = [
      ['M 34 45 H 46.5', '#00acc1'],                 // agua/CIP elevada
      ['M 34 47 H 46.5', '#ab47bc'],                 // slurry/retorno elevado
      ['M 33.5 49 H 40 L 40 51.5', '#ef6c00'],       // aire caliente
      ['M 31.5 64.5 H 38.5', '#43a047'],             // producto envasado elevado
    ];
    for (const [d, color] of tuberias) {
      this.gMezz.appendChild(svgEl('path', { d, fill: 'none', stroke: color, 'stroke-width': 0.4, 'stroke-dasharray': '1.4 0.9', class: 'linea-flujo-anim', opacity: 0.9 }));
    }
    svg.appendChild(this.gMezz);
    document.getElementById('tgMezz').onclick = (e) => {
      e.currentTarget.classList.toggle('on');
      this.gMezz.style.display = e.currentTarget.classList.contains('on') ? '' : 'none';
    };

    // ---- partícula del recorrido ----
    this.particula = svgEl('g', { style: 'display:none' });
    this.partHalo = svgEl('circle', { cx: 0, cy: 0, r: 2.2, fill: 'none', stroke: '#e53935', 'stroke-width': 0.3, opacity: 0.7 });
    this.partNucleo = svgEl('circle', { cx: 0, cy: 0, r: 1, fill: '#e53935', stroke: '#fff', 'stroke-width': 0.22 });
    this.particula.appendChild(this.partHalo);
    this.particula.appendChild(this.partNucleo);
    svg.appendChild(this.particula);

    // ---- panel del recorrido ----
    const panel = document.createElement('div');
    panel.className = 'recorrido-panel';
    panel.style.display = 'none';
    panel.innerHTML = `
      <div class="rec-cabecera"><span id="recNum">①</span> <b id="recTitulo">—</b></div>
      <div id="recTexto" class="rec-texto"></div>
      <div class="rec-dots" id="recDots"></div>
      <div class="rec-controles">
        <button id="recPrev">⏮ Anterior</button>
        <button id="recPlay" class="primario">▶ Reproducir</button>
        <button id="recNext">Siguiente ⏭</button>
      </div>`;
    cont.appendChild(panel);
    this.panel = panel;
    const dots = panel.querySelector('#recDots');
    this.PASOS.forEach((_, i) => {
      const d = document.createElement('button');
      d.className = 'rec-dot';
      d.textContent = i + 1;
      d.onclick = () => this.irA(i);
      dots.appendChild(d);
    });
    panel.querySelector('#recPrev').onclick = () => this.irA(Math.max(0, this.paso - 1));
    panel.querySelector('#recNext').onclick = () => this.irA(Math.min(9, this.paso + 1));
    panel.querySelector('#recPlay').onclick = () => this.togglePlay();
    document.getElementById('tgRecorrido').onclick = (e) => {
      e.currentTarget.classList.toggle('on');
      const on = e.currentTarget.classList.contains('on');
      panel.style.display = on ? '' : 'none';
      this.particula.style.display = on ? '' : 'none';
      if (on) { Plano2D.gFlujo.style.display = ''; this.irA(0); }
      else this.pausar();
    };

    // ---- checklist normativo ----
    const chk = document.createElement('div');
    chk.className = 'mini-panel';
    chk.style.display = 'none';
    chk.style.top = 'auto';
    chk.style.bottom = '10px';
    chk.innerHTML = `<h4>✓ Cumplimiento normativo del trazado</h4>` + this.CHECKS.map(([titulo, det, ok]) =>
      `<div style="display:flex;gap:6px;margin-bottom:5px;font-size:10.5px;line-height:1.35">
        <span style="color:${ok ? '#2e7d32' : '#d32f2f'};font-weight:800">${ok ? '✓' : '✗'}</span>
        <div><b>${titulo}</b><br><span style="color:#7a8a99">${det}</span></div>
      </div>`).join('') +
      `<div style="font-size:9.5px;color:#7a8a99;border-top:1px solid #e8e6dd;padding-top:5px;margin-top:4px">7/7 verificaciones cumplidas · SENADIS · ATEX · NFPA</div>`;
    cont.appendChild(chk);
    document.getElementById('tgChecks').onclick = (e) => {
      e.currentTarget.classList.toggle('on');
      chk.style.display = e.currentTarget.classList.contains('on') ? '' : 'none';
    };

    // ---- temas de color ----
    this.temas = ['claro', 'blueprint', 'oscuro'];
    this.temaIdx = 0;
    document.getElementById('btnTema').onclick = () => {
      this.temaIdx = (this.temaIdx + 1) % 3;
      const tema = this.temas[this.temaIdx];
      cont.classList.remove('tema-blueprint', 'tema-oscuro');
      if (tema !== 'claro') cont.classList.add('tema-' + tema);
      document.getElementById('btnTema').textContent = '🎨 Tema: ' + ({ claro: 'Claro', blueprint: 'Blueprint', oscuro: 'Oscuro' })[tema];
    };
  },

  irA(i) {
    this.paso = i;
    const [x, y] = Plano2D.puntosFlujo[i];
    // animar la partícula hacia el punto del paso
    const x0 = +this.partNucleo.getAttribute('cx') || Plano2D.puntosFlujo[0][0];
    const y0 = +this.partNucleo.getAttribute('cy') || Plano2D.puntosFlujo[0][1];
    const t0 = performance.now();
    const dur = 1100;
    const anim = (t) => {
      const k = Math.min(1, (t - t0) / dur);
      const e = 1 - Math.pow(1 - k, 3); // ease-out
      const cx = x0 + (x - x0) * e, cy = y0 + (y - y0) * e;
      [this.partNucleo, this.partHalo].forEach((c) => { c.setAttribute('cx', cx); c.setAttribute('cy', cy); });
      this.partHalo.setAttribute('r', 1.6 + Math.sin(t / 160) * 0.6);
      if (k < 1 && this.panel.style.display !== 'none') requestAnimationFrame(anim);
    };
    requestAnimationFrame(anim);

    const p = this.PASOS[i];
    this.panel.querySelector('#recNum').textContent = '①②③④⑤⑥⑦⑧⑨⑩'[i];
    this.panel.querySelector('#recTitulo').textContent = p.t;
    this.panel.querySelector('#recTexto').textContent = p.n;
    this.panel.querySelectorAll('.rec-dot').forEach((d, j) => d.classList.toggle('on', j === i));
  },

  togglePlay() {
    if (this.reproduciendo) this.pausar();
    else {
      this.reproduciendo = true;
      this.panel.querySelector('#recPlay').textContent = '⏸ Pausar';
      this._timer = setInterval(() => {
        if (this.paso >= 9) { this.pausar(); return; }
        this.irA(this.paso + 1);
      }, 5000);
    }
  },

  pausar() {
    this.reproduciendo = false;
    clearInterval(this._timer);
    if (this.panel) this.panel.querySelector('#recPlay').textContent = '▶ Reproducir';
  },
};
