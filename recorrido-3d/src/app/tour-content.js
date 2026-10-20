export const STAMP = {
  real: '<span class="st real">Dato real – Edificio 2</span>',
  ilus: '<span class="st ilus">Ilustrativo</span>',
  inv2: '<span class="st ilus">Ilustrativo – plan de la INV2</span>',
};
const tri = '<path d="M10 1.8 L19 17.2 H1 Z" fill="rgba(242,193,78,.12)" stroke="#F2C14E" stroke-width="1.6" stroke-linejoin="round"/>';
const svg = p => `<svg width="20" height="18" viewBox="0 0 20 18" aria-hidden="true">${tri}${p}</svg>`;
export const ICON = {
  elec: svg('<path d="M10.8 6 L7.6 11.2 H10 L9.2 15 L12.4 9.6 H10 Z" fill="#F2C14E"/>'),
  pres: svg('<circle cx="10" cy="11.8" r="3.2" fill="none" stroke="#F2C14E" stroke-width="1.3"/><path d="M10 11.8 L12 10" stroke="#F2C14E" stroke-width="1.3"/>'),
  term: svg('<rect x="9" y="6" width="2" height="6.4" rx="1" fill="#F2C14E"/><circle cx="10" cy="13.4" r="1.8" fill="#F2C14E"/>'),
  alt: svg('<path d="M10 6.4 V12.6 M7.7 10.4 L10 12.9 L12.3 10.4" fill="none" stroke="#F2C14E" stroke-width="1.5"/><path d="M6 15 H14" stroke="#F2C14E" stroke-width="1.3"/>'),
};

export const STOPS = {
  g: { pose: null },
  1: {
    name: 'Seguridad', inv: 'INV4', loc: 'Tablero eléctrico del chiller y azotea',
    pose: { pos: [-33, 15, -36], tgt: [-9, 6, -11] },
    bullets: [
      ['EPP: gafas herméticas, guantes y casco con barboquejo', 'ilus'],
      ['En azotea: arnés con línea de vida', 'ilus'],
      ['LOTO (OSHA 29 CFR 1910.147): 6 pasos antes de intervenir', 'ilus'],
      ['NFPA 70E: riesgo de arco eléctrico en el tablero', 'ilus'],
      ['Refrigerantes por clase ASHRAE 34: A1, A2L y A3', 'ilus'],
    ],
  },
  2: {
    name: 'Planificación', inv: 'INV2', loc: 'Oficina del primer alto con mini-split',
    pose: { pos: [-7, 9.5, 15], tgt: [-20.5, 5.3, 2.8] },
    bullets: [
      ['Mini-splits inverter de 12,000 a 60,000 BTU/h', 'real'],
      ['Plan de referencia: split de 12,000 BTU/h', 'ilus'],
      ['Tareas semanales, mensuales, trimestrales, semestrales y anual', 'ilus'],
      ['CMMS: planificar → programar → ejecutar → cerrar', 'ilus'],
      ['Disponibilidad = MTBF / (MTBF + MTTR)', 'ilus'],
    ],
  },
  3: {
    name: 'Refrigerantes', inv: 'INV1', loc: 'Condensadora del mini-split y atmósfera',
    pose: { pos: [-47, 10, 22], tgt: [-26, 4.8, 2.5] },
    bullets: [
      ['El vapor es más denso que el aire: se acumula a ras de piso', 'ilus'],
      ['Al diluirse, termina en la atmósfera y suma al efecto invernadero', 'ilus'],
      ['GWP: R-410A 2,088 · R-32 675 · R-290 3', 'ilus'],
      ['Recuperar → Reciclar → Regenerar', 'ilus'],
      ['Montreal 1987 → Kigali 2016 → −80 % de HFC en 2045', 'ilus'],
      ['En Panamá no hay instalaciones de recuperación y reciclaje', 'ilus'],
    ],
  },
  4: {
    name: 'Energía', inv: 'INV5', loc: 'Una UMA del edificio (caso ilustrativo)',
    pose: { pos: [-19, 12, -31], tgt: [-11, 1.4, -5.5] },
    bullets: [
      ['VFD: la potencia baja con el cubo de la velocidad', 'ilus'],
      ['Al 80 %: 48.8 % de ahorro teórico', 'ilus'],
      ['Indicadores: EER, SEER, COP e IPLV', 'ilus'],
      ['Filtros sucios, fugas o termostatos mal calibrados suben el consumo', 'ilus'],
      ['BMS/EMS y auditoría energética (Ley 69 de 2012)', 'ilus'],
    ],
  },
  5: {
    name: 'Innovación', inv: 'INV3', loc: 'Chiller, UMA y tubería de agua fría',
    pose: { pos: [-36, 22, 38], tgt: [-2, 9, -3] },
    bullets: [
      ['Chiller enfriado por aire de 155 TR y 16 UMA', 'real'],
      ['Climatización: 69 % del consumo del edificio', 'real'],
      ['Deterioro en uniones de agua fría (termografía)', 'real'],
      ['Propuesta: sensores IoT → pantalla BMS', 'ilus'],
      ['Detección de anomalías y gemelo digital / BIM', 'ilus'],
    ],
  },
  i: {
    name: 'Vista integrada', inv: '', loc: 'Las 5 investigaciones sobre un mismo sistema',
    pose: { pos: [6, 24, 46], tgt: [-12, 12, -3] },
    bullets: [
      ['1 Seguridad (INV4): para intervenir', 'flow'],
      ['2 Planificación (INV2): para programar', 'flow'],
      ['3 Refrigerantes (INV1): bien manejados', 'flow'],
      ['4 Energía (INV5): optimizada', 'flow'],
      ['5 Innovación (INV3): tecnología que lo monitorea', 'flow'],
    ],
  },
};

const head = (t, st) => `<div class="ch"><h4>${t}</h4>${STAMP[st]}</div>`;
// [html, anchorKey]
export const CARDS = {
  1: [[head('LOTO – OSHA 29 CFR 1910.147', 'ilus') + `<p class="fn" style="margin:0 0 6px">Candado y tarjeta en el tablero del chiller</p><ol>
      <li>Preparar</li><li>Apagar</li><li>Aislar</li><li>Bloquear y etiquetar</li><li>Disipar energía residual</li><li>Verificar</li></ol>`, 'lock'],
    [head('Riesgos', 'ilus') + `<div class="rk"><span>${ICON.elec}Eléctrico</span><span>${ICON.pres}Presión</span><span>${ICON.term}Térmico</span><span>${ICON.alt}Alturas</span></div>`, 'hot']],
  2: [
    [head('Plan · split de referencia de 12,000 BTU/h', 'inv2') + `<div class="tl">
      <b>Semanal</b><span>Revisar filtro, ruidos y goteos</span>
      <b>Mensual</b><span>Limpiar filtro</span>
      <b>Cada 3 meses</b><span>Serpentín evaporador, turbina, bandeja y drenaje</span>
      <b>Cada 6 meses</b><span>Conexiones eléctricas y ventiladores (equipo aislado de la energía); temperaturas y corriente</span>
      <b>Anual</b><span>Evaluación integral</span></div>`, 'split2'],
    [head('CMMS · orden de trabajo', 'ilus') + `<div class="flow"><span>Planificar</span><i>→</i><span>Programar</span><i>→</i><span>Ejecutar</span><i>→</i><span>Cerrar</span></div>`, 'cmms'],
    [head('KPI · ejemplo de la INV2', 'ilus') + `<div class="kpi"><div>MTBF<b>360 h</b></div><div>MTTR<b>5 h</b></div></div>
      <div class="kv"><span>MTBF / (MTBF + MTTR)</span><b>98.63 %</b></div>`, 'cmms'],
    [head('Tipos de mantenimiento', 'ilus') + `<div class="cmp"><div><b>Correctivo</b>después de la falla</div><div><b>Preventivo</b>por calendario</div><div><b>Predictivo</b>por condición</div></div>`, 'cond2'],
  ],
  3: [
    [head('Comportamiento de una fuga', 'ilus') + `Vapor de R-410A ≈ 3 veces más denso que el aire: desplaza el oxígeno y se acumula en zonas bajas <span style="color:#A9B4BE">(Honeywell, 2014)</span>.`, 'leak'],
    [head('GWP a 100 años', 'ilus') + `<div class="bars">
      ${[['R-22', 1810, '1,810'], ['R-410A', 2088, '2,088'], ['R-32', 675, '675'], ['R-290', 3, '3']].map(([n, v, t]) => `<span>${n}</span><div class="bar" style="width:${(v / 2088 * 100).toFixed(1)}%"></div><span class="v">${t}</span>`).join('')}
      </div><p class="fn">ODP: R-22 = 0.055; los demás = 0.</p>`, 'atmos'],
    [head('Protocolos', 'ilus') + `<div class="vt">
      <div><span><b>1987</b>Montreal</span></div><div><span><b>2016</b>Kigali</span></div>
      <div><span><b>2017</b>Panamá ratifica Kigali (Ley 87)</span></div><div><span><b>2045</b>Meta: −80 % de HFC</span></div></div>`, 'atmos'],
    [head('Dato país', 'ilus') + `En Panamá no existen instalaciones de recuperación y reciclaje de refrigerantes.<p class="fn">Plan de Enfriamiento de Panamá, 2020</p>`, 'machine'],
  ],
  4: [
    [head('Variador de frecuencia (VFD)', 'ilus') + `<div class="sl"><span>Velocidad del ventilador</span><output id="vfdV">100 %</output></div>
      <input type="range" id="vfdR" min="50" max="100" step="1" value="100" aria-label="Velocidad del ventilador">
      <div class="qs"><button class="btn" data-v="100">100 %</button><button class="btn" data-v="80">80 %</button><button class="btn" data-v="50">50 %</button></div>
      <div class="kv"><span>Potencia = 15 kW × v³</span><b id="vfdP"></b></div>
      <div class="kv"><span>Energía = P × 360 h/mes</span><b id="vfdE"></b></div>
      <div class="kv"><span>Ahorro = 1 − v³</span><b id="vfdS"></b></div>
      <div class="kv"><span>Ahorro × B/. 0.18 por kWh*</span><b id="vfdB"></b></div>
      <p class="fn">*Tarifa hipotética. Resultado teórico: no incluye pérdidas del VFD; hay que verificar que se mantenga la ventilación.</p>`, 'vfd'],
    [head('Factores que suben el consumo', 'ilus') + `<ul><li>Filtros sucios</li><li>Carga incorrecta de refrigerante</li><li>Fugas en ductos</li><li>Aislamiento dañado</li><li>Termostatos mal calibrados</li></ul>`, 'filter'],
  ],
  5: [
    [head('Consumo del edificio', 'real') + `<div class="big">69 %</div>climatización · de ella: chiller 38&nbsp;% · UMA&nbsp;38&nbsp;%`, 'chiller'],
    [head('Propuesta (caso hipotético)', 'ilus') + `<div class="flow"><span>Sensores IoT</span><i>→</i><span>Pantalla BMS</span><i>→</i><span>Detección de anomalías</span><i>→</i><span>Gemelo digital / BIM</span></div>`, 'bms'],
  ],
  i: [[`<div class="ch"><h4>Recorrido</h4></div><div class="vt">
      <div><span><b>1</b>Seguridad para intervenir</span></div><div><span><b>2</b>Plan para programar</span></div>
      <div><span><b>3</b>Refrigerante bien manejado</span></div><div><span><b>4</b>Energía optimizada</span></div>
      <div><span><b>5</b>Tecnología que lo monitorea</span></div></div>
      <div class="big" style="font:600 19px/1.3 'IBM Plex Sans',sans-serif;margin-top:8px;text-wrap:balance">Las 5 investigaciones describen un mismo sistema</div>`, null]],
};

// Inspector por clic (vista general y Parada 5). Sin lecturas numéricas: no hay datos medidos por equipo.
const FLOORS = ['Planta baja', 'Primer alto', 'Segundo alto'];
const isec = (t, st, body) => `<div class="is"><div class="ish">${t}${STAMP[st]}</div>${body}</div>`;
const vars = list => list.map(v => `<div class="iv"><span>${v}</span><b>Sin dato medido</b></div>`).join('');
const MONITOR = 'Variables a monitorear (propuesta INV3)';
export function inspectorHTML(e) {
  const nn = String(e.n).padStart(2, '0');
  if (e.type === 'uma') return {
    title: `UMA ${nn} · ${FLOORS[e.f]}`, st: 'ilus', sub: 'Piso según la distribución ilustrativa del modelo',
    body: isec('Dato real del conjunto', 'real', '<p>16 UMA · 38&nbsp;% del consumo de climatización</p>')
      + isec(MONITOR, 'ilus', vars(['Temperatura de suministro', 'Temperatura de retorno', 'ΔP del filtro', 'Corriente del ventilador', 'Vibración'])),
  };
  if (e.type === 'chiller') return {
    title: 'Chiller', st: 'real', sub: 'Exterior · parte posterior izquierda',
    body: isec('Dato real', 'real', '<p>155&nbsp;TR · enfriado por aire · 38&nbsp;% del consumo de climatización</p>')
      + isec(MONITOR, 'ilus', vars(['Temperatura de suministro de agua helada', 'Temperatura de retorno de agua helada', 'Corriente'])),
  };
  if (e.type === 'split') return {
    title: `Mini-split ${e.n} · ${FLOORS[e.f]}`, st: 'ilus', sub: 'Ubicación ilustrativa: no se conoce el número de mini-splits',
    body: isec('Dato real del conjunto', 'real', '<p>Inverter · 12,000–60,000&nbsp;BTU/h</p>'),
  };
  return {
    title: 'Bombeo de agua helada', st: 'ilus', sub: 'Configuración ilustrativa: el estudio no la detalla',
    body: isec('Equipo ilustrativo', 'ilus', '<p>Bomba en operación y bomba de respaldo, en paralelo</p>' + vars(['Datos de las bombas del Edificio 2'])),
  };
}

// Vista termográfica cualitativa (vista general y Parada 5). Sin °C: no hay temperaturas medidas en este modelo.
export const THERMO = {
  button: 'Vista termográfica',
  title: 'Vista termográfica',
  cold: 'más frío', hot: 'más caliente',
  note: 'Representación cualitativa. El estudio reporta el deterioro detectado en una inspección termográfica, sin temperaturas en este modelo.',
  classes: 'Colores por clase de componente: suministro de agua helada, retorno, equipos, fachada según la radiación solar del panel Clima y hora, y la anomalía en las uniones.',
};

// Rótulo del botón de exportación GLB: lleva clases IFC como metadatos, no es un modelo BIM ni un archivo IFC
export const GLB_LABEL = 'Descargar GLB (con clases IFC como metadatos)';
