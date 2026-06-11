/* ============================================================
   Utilidades compartidas: SVG, zoom/pan, tooltip, drawer, bus
   ============================================================ */

const SVG_NS = 'http://www.w3.org/2000/svg';

// Crear elemento SVG con atributos y texto opcional
function svgEl(tag, attrs = {}, texto) {
  const el = document.createElementNS(SVG_NS, tag);
  for (const [k, v] of Object.entries(attrs)) el.setAttribute(k, v);
  if (texto !== undefined) el.textContent = texto;
  return el;
}

// Bus de eventos global (sinergia de línea entre pestañas)
const Bus = {
  _subs: {},
  on(ev, fn) { (this._subs[ev] = this._subs[ev] || []).push(fn); },
  emit(ev, datos) { (this._subs[ev] || []).forEach((fn) => fn(datos)); },
};

/* ---------- Zoom (rueda) + Pan (arrastre) para SVG ---------- */
function instalarPanZoom(svg, vista0) {
  const estado = { ...vista0 }; // {x, y, w, h}
  const inicial = { ...vista0 };
  function aplicar() {
    svg.setAttribute('viewBox', `${estado.x} ${estado.y} ${estado.w} ${estado.h}`);
  }
  aplicar();

  svg.addEventListener('wheel', (e) => {
    e.preventDefault();
    const factor = e.deltaY > 0 ? 1.15 : 1 / 1.15;
    const r = svg.getBoundingClientRect();
    const mx = estado.x + ((e.clientX - r.left) / r.width) * estado.w;
    const my = estado.y + ((e.clientY - r.top) / r.height) * estado.h;
    estado.w *= factor; estado.h *= factor;
    estado.x = mx - (mx - estado.x) * factor;
    estado.y = my - (my - estado.y) * factor;
    aplicar();
  }, { passive: false });

  let arrastrando = false, px = 0, py = 0;
  svg.addEventListener('mousedown', (e) => { arrastrando = true; px = e.clientX; py = e.clientY; });
  window.addEventListener('mousemove', (e) => {
    if (!arrastrando) return;
    const r = svg.getBoundingClientRect();
    estado.x -= ((e.clientX - px) / r.width) * estado.w;
    estado.y -= ((e.clientY - py) / r.height) * estado.h;
    px = e.clientX; py = e.clientY;
    aplicar();
  });
  window.addEventListener('mouseup', () => { arrastrando = false; });

  return {
    ajustar() { Object.assign(estado, inicial); aplicar(); },
  };
}

/* ---------- Tooltip ---------- */
const tooltipEl = () => document.getElementById('tooltip');
function mostrarTooltip(e, html) {
  const t = tooltipEl();
  t.innerHTML = html;
  t.style.display = 'block';
  moverTooltip(e);
}
function moverTooltip(e) {
  const t = tooltipEl();
  const x = Math.min(e.clientX + 14, window.innerWidth - 300);
  const y = Math.min(e.clientY + 14, window.innerHeight - 90);
  t.style.left = x + 'px';
  t.style.top = y + 'px';
}
function ocultarTooltip() { tooltipEl().style.display = 'none'; }

// Conectar interactividad estándar (hover + clic) a un nodo que representa un item
function hacerInteractivo(nodo, id) {
  const item = getItem(id);
  if (!item) return;
  nodo.classList.add('clicable');
  nodo.addEventListener('mouseenter', (e) => {
    const volt = item.alimentacion || (item.ficha && item.ficha.alimentacion) || '';
    mostrarTooltip(e, `<b>${item.nombre}</b><br><span class="tt-volt">⚡ ${volt}</span>`);
  });
  nodo.addEventListener('mousemove', moverTooltip);
  nodo.addEventListener('mouseleave', ocultarTooltip);
  nodo.addEventListener('click', (e) => { e.stopPropagation(); abrirFicha(id); });
}

/* ---------- Drawer de ficha técnica ---------- */
function abrirFicha(id) {
  const item = getItem(id);
  if (!item) return;
  document.getElementById('drawerTitulo').textContent = item.nombre;
  document.getElementById('drawerMarca').textContent = item.marca || item.dims || '';
  const cuerpo = document.getElementById('drawerCuerpo');
  cuerpo.innerHTML = '';

  // Estado operativo en vivo (sinergia con la simulación)
  const vivo = Sim.estadoEquipo(id);
  if (vivo) {
    const div = document.createElement('div');
    div.className = 'estado-vivo' + (vivo.alerta ? ' en-alerta' : '');
    div.innerHTML = `<div class="etiq">Estado operativo actual (simulación)</div>
      <div>${vivo.chips.map((c) => `<span class="chip ${c.tipo}">${c.texto}</span>`).join('')}</div>
      <div style="margin-top:5px">${vivo.texto}</div>`;
    cuerpo.appendChild(div);
  }

  const filas = [];
  if (item.tipo === 'equipo') {
    filas.push(['Marca / Modelo', item.marca]);
    filas.push(['Función en el proceso', `Etapa ${'①②③④⑤⑥⑦⑧⑨⑩'[item.etapa - 1]} — ${(PLANT_DATA.flujo[item.etapa - 1] || {}).nombre || ''}`]);
    filas.push(['Dimensiones (huella)', item.dims]);
    filas.push(['Peso', item.peso]);
    filas.push(['⚡ Alimentación eléctrica', item.alimentacion, 'volt']);
    filas.push(['Consumos', item.consumos]);
    filas.push(['Materiales', item.materiales]);
    filas.push(['Velocidad / capacidad', item.velocidad]);
    filas.push(['Fase del producto', item.faseProducto]);
    filas.push(['⬆ Aguas arriba (sinergia)', item.conexiones.aguasArriba]);
    filas.push(['⬇ Aguas abajo (sinergia)', item.conexiones.aguasAbajo]);
  } else {
    filas.push(['Dimensiones', item.dims]);
    filas.push(['Función', item.ficha.funcion]);
    filas.push(['⚡ Alimentación eléctrica', item.ficha.alimentacion, 'volt']);
    filas.push(['Detalles', item.ficha.detalles.map((d) => '• ' + d).join('<br>')]);
  }
  for (const [etiq, val, clase] of filas) {
    if (!val) continue;
    const f = document.createElement('div');
    f.className = 'ficha-fila';
    f.innerHTML = `<div class="etiq">${etiq}</div><div class="valor ${clase || ''}">${val}</div>`;
    cuerpo.appendChild(f);
  }
  document.getElementById('drawer').classList.add('abierto');
}
function cerrarDrawer() {
  document.getElementById('drawer').classList.remove('abierto');
}

// Ficha libre (instrumentos P&ID, elementos del unifilar, etc.)
function abrirFichaLibre(titulo, subtitulo, filas) {
  document.getElementById('drawerTitulo').textContent = titulo;
  document.getElementById('drawerMarca').textContent = subtitulo || '';
  const cuerpo = document.getElementById('drawerCuerpo');
  cuerpo.innerHTML = '';
  for (const [etiq, val, clase] of filas) {
    if (!val) continue;
    const f = document.createElement('div');
    f.className = 'ficha-fila';
    f.innerHTML = `<div class="etiq">${etiq}</div><div class="valor ${clase || ''}">${val}</div>`;
    cuerpo.appendChild(f);
  }
  document.getElementById('drawer').classList.add('abierto');
}

// Formateo numérico es-PA
const fmt = (n, dec = 0) => Number(n).toLocaleString('es-PA', { minimumFractionDigits: dec, maximumFractionDigits: dec });
