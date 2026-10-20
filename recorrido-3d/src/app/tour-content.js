export const STAMP = {
  real: '<span class="st real">Dato real – Edificio 2</span>',
  ilus: '<span class="st ilus">Ilustrativo</span>',
  inv2: '<span class="st ilus">Ilustrativo – plan de la INV2</span>',
  prop: '<span class="st ilus">Propuesta del grupo (ilustrativa)</span>',
  split: '<span class="st ilus">Ilustrativo – plan de la INV2 (split de referencia de 12,000 BTU/h)</span>',
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
      ['Tablero: guantes dieléctricos clase 00, gafas de seguridad, calzado dieléctrico y ropa ignífuga contra arco', 'ilus'],
      ['Azotea: arnés con línea de vida de doble amortiguador y casco con barboquejo de 4 puntos', 'ilus'],
      ['Cilindros: gafas herméticas y guantes criogénicos o de nitrilo grueso', 'ilus'],
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
    name: 'Innovación', sub: 'Monitoreo IoT y BMS', short: 'Monitoreo IoT', inv: 'INV3', loc: 'Chiller, UMA y tubería de agua fría',
    pose: { pos: [-36, 22, 38], tgt: [-2, 9, -3] },
    bullets: [
      ['Chiller enfriado por aire de 155 TR y 16 UMA', 'real'],
      ['Climatización: 69 % del consumo del edificio', 'real'],
      ['Deterioro en uniones de agua fría (termografía)', 'real'],
      ['Propuesta: sensores IoT → pantalla BMS', 'ilus'],
      ['Detección de anomalías y gemelo digital / BIM', 'ilus'],
    ],
  },
  // Subventanas de la Parada 5 (herramientas del modelo "Herramientas HVAC 3D" del grupo)
  '5.2': {
    name: 'Innovación', sub: 'Termografía infrarroja', short: 'Termografía', inv: 'INV3', loc: 'Tubería de agua helada entre el chiller y el edificio',
    pose: { pos: [-5.6, 5.4, -18.5], tgt: [-13.4, 0.9, -7.6] },
    bullets: [
      ['Usada en la auditoría energética del Edificio 2', 'real'],
      ['Detectó deterioro en uniones de la tubería de agua fría', 'real'],
      ['Una sola inspección, sin monitoreo permanente', 'real'],
      ['Vista termográfica cualitativa: sin temperaturas medidas', 'ilus'],
      ['Sin monitoreo permanente: los sensores IoT (5.1) le darían seguimiento', 'ilus'],
    ],
  },
  '5.3': {
    name: 'Innovación', sub: 'Realidad aumentada', short: 'Realidad aumentada', inv: 'INV3', loc: 'Un salón del primer alto (caso hipotético)',
    pose: { pos: [19.6, 6.5, -4.1], tgt: [13.4, 4.8, 2.0] },
    bullets: [
      ['El técnico ve los datos de los sensores IoT sobre el espacio real', 'ilus'],
      ['Temperatura y humedad por zona, en la tableta', 'ilus'],
      ['Ajusta el sistema desde la misma interfaz', 'ilus'],
      ['Campo simulado y cualitativo: no son lecturas del Edificio 2', 'ilus'],
    ],
  },
  '5.4': {
    name: 'Innovación', sub: 'Dron en ductos', short: 'Dron en ductos', inv: 'INV3', loc: 'Ducto de suministro sobre el cielo raso (caso hipotético)',
    pose: { pos: [-7.6, 8.3, 4.6], tgt: [-10.9, 6.75, 0.7] },
    bullets: [
      ['Cuadricóptero en una jaula esférica: rueda por el piso del ducto', 'ilus'],
      ['Vuela para pasar el codo', 'ilus'],
      ['Una cámara térmica barre las paredes', 'ilus'],
      ['Detecta fugas en las uniones sin desmontar el ducto', 'ilus'],
    ],
  },
  // Vista integrada: 3 sub-vistas. Internamente 'i' es la i.1.
  i: {
    name: 'Vista integrada', sub: 'Una falla de punta a punta', short: 'Una falla', inv: '', loc: 'Uniones de la tubería de agua fría',
    pose: { pos: [-6.5, 4.6, -13.5], tgt: [-10.8, 0.9, -6.2] },
    bullets: [
      ['1 · INV3 · Detectar', 'flow'],
      ['2 · INV2 · Registrar, planificar y programar', 'flow'],
      ['3 · INV4 · Ejecutar con seguridad', 'flow'],
      ['4 · INV1 · Refrigerante', 'flow'],
      ['5 · INV5 · Energía', 'flow'],
      ['6 · INV2 · Probar y cerrar', 'flow'],
    ],
  },
  'i.2': {
    name: 'Vista integrada', sub: 'Antes / después', short: 'Antes / después', inv: '', loc: 'Del estado de 2021 al caso hipotético de la INV3',
    pose: { pos: [-36, 22, 38], tgt: [-2, 9, -3] },
    bullets: [
      ['Antes: mediciones puntuales y una sola inspección termográfica', 'real'],
      ['Etapa 1: sensores IoT en el chiller y las 16 UMA, integrados al BMS', 'ilus'],
      ['Etapa 2: detección de anomalías', 'ilus'],
      ['Etapa 3: datos vinculados a un modelo BIM', 'ilus'],
      ['Sin ahorros esperados: no hay mediciones en HVAC que los respalden', 'ilus'],
    ],
  },
  'i.3': {
    name: 'Vista integrada', sub: 'Plan de 2 años', short: 'Plan de 2 años', inv: '', loc: 'Calendario de 104 semanas',
    pose: { pos: [-36, 22, 38], tgt: [-2, 9, -3] },
    bullets: [
      ['Mini-split: plan del split de referencia de la INV2', 'ilus'],
      ['Chiller, 16 UMA y bombas: frecuencia según el manual del fabricante', 'ilus'],
      ['Evaluación trimestral del plan', 'ilus'],
      ['Hoja de ruta en el orden del compendio', 'ilus'],
      ['Correctivo: con indicios de falla, orden correctiva', 'ilus'],
    ],
  },
};

const head = (t, st) => `<div class="ch"><h4>${t}</h4>${STAMP[st]}</div>`;
// [html, anchorKey]
export const CARDS = {
  // Vista general = introducción (INV3, p. 36; contexto de Panamá, p. 33 y p. 9)
  g: [[`<div class="ch"><h4>Introducción</h4></div>
      <div class="ib" style="border:0;margin:0;padding:0">${STAMP.real}<b>El Edificio 2 (Postgrado)</b>Chiller enfriado por aire de 155&nbsp;TR · 16&nbsp;UMA en sus tres pisos · mini-splits inverter de 12,000 a 60,000&nbsp;BTU/h, instalados por modificaciones posteriores al diseño original.<p class="fn">(Henríquez Espinosa et al., 2021)</p></div>
      <div class="ib">${STAMP.ilus}<b>Por qué importa</b>En Panamá, el aire acondicionado es el mayor consumidor de energía en muchas edificaciones, y el sector RAC representa el 42&nbsp;% del consumo eléctrico nacional.<p class="fn">(Chen Austin et al., 2021; Henríquez Espinosa et al., 2021; MINSA/UNO y PNUD, 2020)</p></div>
      <div class="ib"><b>El recorrido</b><div class="route"><span><b>1</b>Seguridad</span><span><b>2</b>Planificación</span><span><b>3</b>Refrigerantes</span><span><b>4</b>Energía</span><span><b>5</b>Innovación</span></div></div>`, null, 'intro']],
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
    [head('CMMS · orden de trabajo', 'ilus') + `<div class="flow"><span>Planificar</span><i>→</i><span>Programar</span><i>→</i><span>Ejecutar</span><i>→</i><span>Cerrar</span></div><p class="fn">Detalle de 7 pasos en la vista integrada.</p>`, 'cmms'],
    [head('KPI · ejemplo de la INV2', 'ilus') + `<div class="kpi"><div>MTBF<b>360 h</b></div><div>MTTR<b>5 h</b></div></div>
      <div class="kv"><span>MTBF / (MTBF + MTTR)</span><b>98.63 %</b></div>`, 'cmms'],
    [head('Tipos de mantenimiento', 'ilus') + `<div class="cmp"><div><b>Correctivo</b>después de la falla</div><div><b>Preventivo</b>por calendario</div><div><b>Predictivo</b>por condición</div></div>`, 'cond2'],
  ],
  3: [
    [head('Comportamiento de una fuga', 'ilus') + `Los refrigerantes son más densos que el aire: desplazan el oxígeno y se acumulan en zonas bajas <span style="color:#A9B4BE">(National Refrigerants, s.&nbsp;f.)</span>.`, 'leak'],
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
  '5.2': [
    [head('Termografía infrarroja', 'real') + `Se usó en la auditoría energética del Edificio 2 y permitió detectar deterioro en las uniones de la tubería de agua fría que alimenta el edificio, en una sola inspección, sin monitoreo permanente.<p class="fn">(Henríquez Espinosa et al., 2021)</p>`, 'thermal'],
    [head('Cómo se inspecciona', 'ilus') + `Una cámara termográfica portátil recorre la tubería de agua helada, del chiller al edificio, y apunta a cada unión. La vista termográfica de este modelo es cualitativa.<p class="fn">Escena tomada del modelo «Herramientas HVAC 3D» del grupo.</p>`, 'irCam'],
    [head('Limitación', 'ilus') + `Una sola inspección: no hay monitoreo permanente. Los sensores IoT de la 5.1 darían seguimiento continuo a estas uniones.`, null],
  ],
  '5.3': [
    [head('Control desde la tableta', 'ilus') + `<div class="arst" id="arSt">—</div><div class="qs"><button class="btn" id="arCtl">Aplicar ajuste</button></div><p class="fn">Campo simulado y cualitativo (más cálido / más fresco): no son lecturas del Edificio 2, por eso no se muestran valores de temperatura ni de humedad.</p>`, 'arAc'],
    [head('Realidad aumentada · caso hipotético', 'ilus') + `En un salón, el técnico ve sobre el espacio real los datos de los sensores IoT por zona y ajusta el sistema desde la tableta.<p class="fn">(Mohammadi et al., 2024)</p>`, 'arTablet'],
  ],
  '5.4': [
    [head('Estado del recorrido', 'ilus') + `<div class="arst" id="droneSt">—</div><p class="fn">La fuga es un caso hipotético para mostrar la detección; no es un hallazgo del Edificio 2.</p>`, 'droneLeak'],
    [head('Dron en ductos · caso hipotético', 'ilus') + `Un cuadricóptero dentro de una jaula esférica recorre un ducto rectangular: rueda por el piso, vuela para pasar el codo y barre las paredes con una cámara térmica.<p class="fn">(Khalil et al., 2024)</p>`, 'drone'],
  ],
  // i.1: la tarjeta se llena con FALLA[paso] desde tour-app (sin anclaje, para que siga visible en el modo «al pasar»)
  i: [[`<div class="ch"><h4>Una falla de punta a punta</h4></div><div id="falla"></div>
      <div class="fctl"><button class="btn" id="fPrev" aria-label="Paso anterior">◀</button><button class="btn pl" id="fPlay">Reproducir</button><button class="btn" id="fNext" aria-label="Paso siguiente">▶</button><span class="fdots" id="fDots"></span></div>`, null]],
  'i.2': [
    [`<div class="ch"><h4>Antes / después</h4></div><input type="range" id="abR" min="0" max="3" step="1" value="0" aria-label="Antes / después">
      <div class="abl"><span>Antes</span><span>Etapa 1</span><span>Etapa 2</span><span>Etapa 3</span></div><div id="abS"></div>
      <p class="fn">«Después» es el caso hipotético de la INV3 (p. 37).</p>`, null],
    [head('Barrera y forma de empezar', 'ilus') + `La mezcla de equipos de distintas épocas y fabricantes dificulta integrarlos en una sola plataforma (Shaban et al., 2025). Conviene iniciar con un piloto en las UMA y capacitar al personal antes de ampliar (Appau, 2026; Henríquez Espinosa et al., 2021).<p class="fn">INV3, p. 37</p>`, null],
    [head('Límite documentado · otro edificio', 'ilus') + `En otro edificio educativo con 4 UMA, las predicciones a 1 mes acertaron entre 80 y 100&nbsp;%; a 4.5 meses, dos tipos de falla tuvieron 0&nbsp;% de acierto (Hosamo et al., 2022).<p class="fn">INV3, p. 35. El modelo no muestra ahorros esperados: el compendio aclara que las cifras generales de reducción de costos y averías no provienen de mediciones en sistemas HVAC (p. 36).</p>`, null],
  ],
  'i.3': [],
};

// Inspector por clic (vista general y Parada 5). Sin lecturas numéricas: no hay datos medidos por equipo.
const FLOORS = ['Planta baja', 'Primer alto', 'Segundo alto'];
const isec = (t, st, body) => `<div class="is"><div class="ish">${t}${STAMP[st]}</div>${body}</div>`;
const vars = list => list.map(v => `<div class="iv"><span>${v}</span><b>Sin dato medido</b></div>`).join('');
const MONITOR = 'Variables a monitorear (propuesta INV3)';
// Predictivo de la INV2 (p. 17): va aparte de las 3 variables de la etapa 1 de la INV3 (p. 37)
const PREDICTIVO = isec('Predictivo (INV2, p. 17)', 'ilus', vars(['Vibración y temperatura de rodamientos', 'Corriente', 'Temperaturas y presiones']));
// Matriz equipo × investigación (Fase 2.6): una línea por investigación, con su fuente (docs/FUENTES_COMPENDIO.md)
const MATRIZ = {
  chiller: [
    ['INV3', '155&nbsp;TR y 38&nbsp;% de la climatización; sensores IoT en la etapa 1 (Henríquez Espinosa et al., 2021; Sivasankari y Rathika, 2025)', 'pp. 36–37'],
    ['INV2', 'Preventivo riguroso, monitoreo de condición, alarmas y repuestos críticos (ASHRAE &amp; U.S. Department of Energy, s.&nbsp;f.)', 'p. 18'],
    ['INV4', 'NFPA 70E: protección contra arco eléctrico al intervenir sus tableros de control (NFPA, 2026)', 'p. 45'],
    ['INV5', 'IPLV: importante en chillers, porque no operan siempre al 100&nbsp;% (AHRI, 2023)', 'pp. 57–58'],
    ['INV1', 'Si se abre su circuito de refrigerante: recuperar con máquina certificada, sin ventear', 'INV4 p. 49 · INV1 p. 8'],
  ],
  uma: [
    ['INV3', '16 UMA y 38&nbsp;% de la climatización; el piloto empieza aquí (Henríquez Espinosa et al., 2021; Appau, 2026)', 'pp. 36–37'],
    ['INV2', 'Filtros, serpentines, drenajes y correas; el CMMS la registra y genera sus tareas', 'pp. 17, 21–22'],
    ['INV4', 'NFPA 70E en los tableros de control de las manejadoras (AHU) (NFPA, 2026)', 'p. 45'],
    ['INV5', 'Caso VFD ilustrativo (Parada 4); filtros y serpentines sucios suben el consumo (ASHRAE, 2018)', 'pp. 59, 62'],
  ],
  split: [
    ['INV2', 'Plan del split de referencia de 12,000&nbsp;BTU/h (ASHRAE, s.&nbsp;f.; ASHRAE &amp; ACCA, 2018)', 'pp. 27–29'],
    ['INV1', 'Si se interviene el circuito: recuperar → reciclar → regenerar', 'p. 8'],
    ['INV3', 'Instalados por modificaciones posteriores al diseño original (Henríquez Espinosa et al., 2021)', 'p. 36'],
    ['INV5', 'Indicadores EER y SEER: mayor valor = más eficiente (AHRI, 2023)', 'p. 58'],
  ],
  pump: [
    ['INV5', 'Los VFD regulan la velocidad de los motores de bombas y ventiladores según la demanda', 'p. 60'],
    ['INV2', 'El CMMS registra cada bomba y genera sus tareas periódicas (FEMP, 2010)', 'pp. 21–22'],
    ['INV4', 'LOTO: identificar la energía hidráulica, cerrar válvulas y purgar presiones', 'p. 48'],
  ],
  pipe: [
    ['INV3', 'La termografía de la auditoría energética detectó deterioro en las uniones, en una sola inspección (Henríquez Espinosa et al., 2021)', 'pp. 35–36'],
    ['INV5', '«El deterioro del aislamiento térmico genera pérdidas energéticas y aumenta la carga de enfriamiento» (ASHRAE, 2018)', 'p. 59'],
  ],
};
const matriz = t => `<div class="is"><div class="ish">Investigaciones que lo tocan</div>${MATRIZ[t].map(([inv, txt, pg]) => `<div class="im"><b>${inv}</b><span>${txt}<small>Compendio, ${pg}</small></span></div>`).join('')}</div>`;
export function inspectorHTML(e) {
  const r = inspectorBase(e); r.body += matriz(e.type); return r;
}
function inspectorBase(e) {
  const nn = String(e.n).padStart(2, '0');
  if (e.type === 'pipe') return {
    title: 'Tubería de agua fría', st: 'real', sub: 'Suministro y retorno entre el chiller y el edificio (trazado ilustrativo)',
    body: isec('Dato real', 'real', '<p>Deterioro en las uniones, detectado en una sola inspección termográfica, sin monitoreo permanente</p>'),
  };
  if (e.type === 'uma') return {
    title: `UMA ${nn} · ${FLOORS[e.f]}`, st: 'ilus', sub: 'Piso según la distribución ilustrativa del modelo',
    body: isec('Dato real del conjunto', 'real', '<p>16 UMA · 38&nbsp;% del consumo de climatización</p>')
      + isec(MONITOR, 'ilus', vars(['Temperaturas de suministro y retorno', 'Presión diferencial en filtros', 'Corriente de ventiladores'])) + PREDICTIVO,
  };
  if (e.type === 'chiller') return {
    title: 'Chiller', st: 'real', sub: 'Exterior · parte posterior izquierda',
    body: isec('Dato real', 'real', '<p>155&nbsp;TR · enfriado por aire · 38&nbsp;% del consumo de climatización</p>')
      + isec(MONITOR, 'ilus', vars(['Temperaturas de suministro y retorno', 'Corriente de ventiladores'])) + PREDICTIVO,
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

// ---------------------------------------------------------------- Vista integrada (Fase 2.6)
// i.1 · Una falla de punta a punta: 6 pasos, cada uno con su investigación y su fuente (docs/FUENTES_COMPENDIO.md)
const ol = items => `<ol class="fol">${items.map(t => `<li>${t}</li>`).join('')}</ol>`;
export const FALLA = [
  { inv: 'INV3', t: 'Detectar', st: 'real', pose: { pos: [-6.5, 4.6, -13.5], tgt: [-10.8, 0.9, -6.2] },
    html: 'La termografía infrarroja de la auditoría energética detectó deterioro en las uniones de la tubería de agua fría, en una sola inspección y sin monitoreo permanente.',
    src: '(Henríquez Espinosa et al., 2021) · INV3, pp. 35–36' },
  { inv: 'INV2', t: 'Registrar, planificar y programar', st: 'ilus', pose: { pos: [-15.5, 5.2, -13.5], tgt: [-10.6, 0.9, -6.4] },
    html: 'Flujo de la orden de trabajo, pasos 1 a 4:' + ol(['<b>Detectar</b>: inspección, alarma, solicitud o tendencia anormal.', '<b>Registrar</b>: código, síntoma, ubicación y prioridad (crítica / alta / media / baja, según el criterio del planificador).', '<b>Planificar</b>: alcance, riesgos, instrumentos, repuestos y tiempo; revisar manuales.', '<b>Programar</b>: ventana de parada coordinada con los usuarios.']),
    src: 'INV2, p. 20' },
  { inv: 'INV4', t: 'Ejecutar con seguridad', st: 'ilus', pose: { pos: [-12.8, 2.8, -10.5], tgt: [-12.6, 0.9, -6.6] },
    html: 'LOTO de 6 pasos: preparar (reconocer los tipos de energía) → apagar → aislar → candado y tarjeta por técnico → disipar la energía residual → verificar.<br>Para esta falla, la lista de verificación pide identificar la energía <b>hidráulica</b> y <b>térmica</b> además de la eléctrica, <b>cerrar válvulas</b> y <b>purgar presiones</b>. EPP según la tarea.',
    src: 'OSHA 1910.147 · INV4, pp. 46–48' },
  { inv: 'INV1', t: 'Refrigerante', st: 'ilus', pose: { pos: [-20.5, 5.4, -16.5], tgt: [-13.5, 1.0, -8.5] },
    html: 'Esta reparación es en el circuito de agua fría y no abre el circuito de refrigerante. Si la falla estuviera en el chiller: recuperar con máquina certificada, cilindro sin superar el 80&nbsp;%, sin ventear (INV4, p. 49) → reciclar → regenerar (INV1, p. 8). En Panamá no hay instalaciones de reciclaje (MINSA/UNO y PNUD, 2020).',
    src: 'INV4, p. 49 · INV1, p. 8 · p. 9' },
  { inv: 'INV5', t: 'Energía', st: 'ilus', pose: { pos: [-5.5, 7.2, -16], tgt: [-12.4, 0.9, -7.2] },
    html: '«El deterioro del aislamiento térmico genera pérdidas energéticas y aumenta la carga de enfriamiento» (ASHRAE, 2018). Después de la reparación, verificar con mediciones posteriores (ASHRAE, 2023).',
    src: 'INV5, pp. 59–61' },
  { inv: 'INV2', t: 'Probar y cerrar', st: 'ilus', pose: { pos: [-8.6, 3.2, -10.4], tgt: [-10.5, 0.9, -5.6] },
    html: 'Paso 6: probar y registrar mediciones. Paso 7: cerrar la orden (causa probable, materiales, tiempo real y recomendaciones) y actualizar el historial en el CMMS.<div class="qs" style="margin-top:6px"><button class="btn" data-go="i.3">Ver el plan de 2 años (i.3) →</button></div>',
    src: 'INV2, p. 20' },
];

// i.2 · Antes / después: el deslizador recorre el estado de 2021 y las 3 etapas del caso hipotético de la INV3 (p. 37)
export const ANTES_DESPUES = [
  { st: 'real', t: 'Antes', html: 'Inventario publicado en 2021: mediciones puntuales y una sola inspección termográfica, sin monitoreo permanente (Henríquez Espinosa et al., 2021).' },
  { st: 'ilus', t: 'Etapa 1 · Sensores IoT', html: 'Sensores IoT en el chiller y las 16 UMA: temperaturas de suministro y retorno, presión diferencial en filtros y corriente de ventiladores, integrados al BMS (Sivasankari y Rathika, 2025).' },
  { st: 'ilus', t: 'Etapa 2 · Detección de anomalías', html: 'Algoritmos de detección de anomalías, que no requieren un historial completo de fallas (Es-sakali et al., 2022).' },
  { st: 'ilus', t: 'Etapa 3 · Modelo BIM', html: 'Vincular los datos a un modelo BIM del edificio (Hosamo et al., 2022).' },
];

// i.3 · Plan de 2 años (104 semanas)
// Mini-split: exactamente la tabla de la INV2 (pp. 27–29). every = cada cuántas semanas (null = sin fecha fija)
export const PLAN_SPLIT = [
  { f: 'Semanal (usuario)', a: 'Revisar filtro; observar ruidos, olores, vibración o goteos', r: 'Usuario; lista de observación', every: 1 },
  { f: 'Mensual', a: 'Limpiar filtro reutilizable; entrada y salida de aire libres', r: 'Usuario o técnico; registro de limpieza', perYear: 12 },
  { f: 'Cada 3 meses', a: 'Inspeccionar serpentín evaporador, turbina, bandeja y drenaje; fijaciones, aislamiento visible y unidad exterior', r: 'Técnico; orden de trabajo', every: 13 },
  { f: 'Cada 6 meses', a: 'Limpiar serpentines si hace falta; conexiones eléctricas, terminales, soportes y ventiladores, con el equipo aislado de la energía', r: 'Técnico calificado; checklist', every: 26 },
  { f: 'Cada 6 meses o según condición', a: 'Medir temperaturas de retorno e impulsión, ambiente, corriente del compresor y ventiladores', r: 'Técnico; hoja de mediciones', every: 26, off: 13 },
  { f: 'Anual', a: 'Evaluación integral: rendimiento, serpentines, drenaje, aislamiento, controles, consumo', r: 'Supervisor/técnico; informe anual', every: 52 },
];
export const PLAN_TEXT = {
  splitNote: 'Ajustar al manual de cada equipo; el edificio tiene de 12,000 a 60,000&nbsp;BTU/h. El plan «es una propuesta de planificación inicial, no un sustituto del manual del fabricante» (INV2, p. 27).',
  counter: 'Por mini-split y por año: <b>52</b> semanales (usuario) · <b>12</b> mensuales · <b>4</b> trimestrales · <b>2</b> semestrales · <b>2</b> mediciones · <b>1</b> anual',
  big: 'Chiller, 16 UMA y bombas',
  bigTasks: 'Filtros, serpentines, drenajes, condensadoras, correas, ventiladores, motores y rodamientos, conexiones eléctricas, calibración de sensores y controles, aislamiento, carga de refrigerante y fugas (INV2, p. 17; INV5, pp. 59–60).',
  bigBand: 'Frecuencia según el manual del fabricante; el compendio no la define (INV2, p. 17)',
  chiller: 'Chiller: preventivo riguroso, monitoreo de condición, alarmas y repuestos críticos (ASHRAE &amp; U.S. Department of Energy, s.&nbsp;f.; INV2, p. 18).',
  evalT: 'Evaluación trimestral del plan',
  evalNote: 'Cumplimiento = tareas completadas / tareas programadas × 100. Sin dato: se mide al ejecutar (INV2, p. 30).',
  roadT: 'Hoja de ruta',
  roadNote: 'El orden sale del compendio; repartirlo en «Año 1 / Año 2» es decisión del grupo.',
  corrT: 'Correctivo',
  corr: 'Con indicios de falla → diagnóstico y orden correctiva; no añadir refrigerante sin diagnóstico (INV2, pp. 27–29).',
};
// Hoja de ruta: [desde, hasta) en semanas; el reparto por años es propuesta del grupo
export const ROADMAP = [
  [0, 26, 'Depurar los activos y cargar los planes en el CMMS con un grupo piloto', 'INV2, p. 22'],
  [26, 52, 'Piloto IoT en las UMA y capacitación', 'INV3, p. 37'],
  [52, 70, 'Detección de anomalías', 'INV3, p. 37'],
  [70, 91, 'Ampliar al chiller y las 16 UMA, y BIM', 'INV3, p. 37'],
  [91, 104, 'Auditoría energética con mediciones posteriores', 'INV5, p. 61'],
];
