// Texto de la Parada 3 · M8 (District Cooling). Autor: Manuel Jiménez. Única fuente: Word del M8.
// Solo se usa texto con cita en el Word; ninguna cifra del Word se muestra (temperaturas, porcentajes, COP, vida útil).
// Citas con la forma exacta del Word. Sin marcas comerciales.
export const M8 = {
  stop: { kicker: 'Parada 3 · M8', short: 'M8', author: 'Manuel Jiménez', title: 'Aplicaciones Avanzadas de Refrigeración y Aire Acondicionado', lead: 'District Cooling: refrigeración centralizada para grandes complejos urbanos.' },
  note: 'Modelo conceptual, no a escala. Ciudad genérica e ilustrativa: no es Panamá ni un lugar real.',
  steps: [
    { id: 'fund', n: '3.0', title: 'Fundamentos', ref: 'M8 · Fundamentos del District Cooling',
      cards: [{ ref: 'M8 · Fundamentos del District Cooling', stamp: 'df', cite: 'ASHRAE, 2024', title: 'Una planta, muchos usuarios',
        body: '<p>District Cooling es un sistema de refrigeración centralizada que suministra energía térmica de enfriamiento a múltiples usuarios desde una única planta. Genera agua fría con enfriadores industriales (chillers) y la distribuye por una red de tuberías subterráneas hacia edificios comerciales, hospitales, universidades, aeropuertos y complejos residenciales.</p><p>Dentro de cada edificio, el agua fría pasa por intercambiadores de calor que transfieren la energía necesaria para enfriar el aire interior. Después, el agua retorna a la planta central para ser enfriada nuevamente y reiniciar el ciclo.</p><p>La capacidad de refrigeración suele expresarse en toneladas de refrigeración (TR) o en megavatios térmicos (MWt).</p>' }] },
    { id: 'planta', n: '3.1', title: 'Componentes de la planta central', ref: 'M8 · Componentes principales · Planta central',
      cards: [{ ref: 'M8 · Componentes principales · Planta central', title: 'El corazón del sistema',
        body: '<p>La planta central contiene:</p><ul><li>chillers centrífugos de alta eficiencia;</li><li>torres de enfriamiento;</li><li>bombas de circulación;</li><li>sistemas de almacenamiento térmico;</li><li>equipos de control y automatización.</li></ul><p class="small"><span class="st il">Ilustrativo</span> Los equipos del modelo son genéricos; su número y su tamaño no son del informe.</p>' }] },
    { id: 'red', n: '3.2', title: 'Red de distribución', ref: 'M8 · Red de distribución',
      cards: [{ ref: 'M8 · Red de distribución', stamp: 'df', cite: 'IDEA, 2023', title: 'Tuberías aisladas: ida y vuelta',
        body: '<p>Consiste en tuberías aisladas térmicamente que transportan agua fría hacia los edificios y retornan el agua caliente a la planta.</p><p class="small"><span class="st il">Ilustrativo</span> Azul: suministro de agua fría. Rojo: retorno más caliente. La red se dibuja bajo el suelo, sin escala de temperatura.</p>' }] },
    { id: 'control', n: '3.3', title: 'Sistema de control (SCADA)', ref: 'M8 · Sistema de control',
      cards: [{ ref: 'M8 · Sistema de control', stamp: 'df', cite: 'TRABEED, 2024', title: 'Supervisión de toda la red',
        body: '<p>Utiliza plataformas SCADA y automatización industrial para:</p><ul><li>regular caudales;</li><li>monitorear temperaturas;</li><li>detectar fugas;</li><li>optimizar el consumo energético.</li></ul>' }] },
    { id: 'dubai', n: '3.4', title: 'Caso de estudio: Dubái', ref: 'M8 · Casos de estudio internacionales',
      cards: [{ ref: 'M8 · Casos de estudio internacionales · Dubái', stamp: 'df', cite: 'EMPOWER, 2024', title: 'Dubái',
        body: '<p>Dubái posee uno de los mayores sistemas District Cooling del mundo. Sus empresas de District Cooling suministran refrigeración a miles de edificios, centros comerciales y desarrollos inmobiliarios de gran escala.</p><p class="small"><span class="st il">Ilustrativo</span> El modelo no representa Dubái: la ciudad es genérica.</p>' }] },
    { id: 'panama', n: '3.5', title: 'Potencial en Panamá', ref: 'M8 · Potencial de implementación en Panamá',
      cards: [{ ref: 'M8 · Potencial de implementación en Panamá', stamp: 'pr', title: 'Propuesta del informe',
        body: '<p>Panamá presenta condiciones favorables: temperaturas elevadas durante todo el año, alto crecimiento urbano, gran concentración de edificios comerciales y demanda constante de climatización.</p><ul><li><b>Área Bancaria:</b> la alta densidad de torres comerciales permitiría compartir infraestructura de enfriamiento.</li><li><b>Ciudad de la Salud:</b> hospitales y centros médicos requieren refrigeración continua.</li><li><b>Aeropuerto Internacional de Tocumen:</b> la gran superficie climatizada podría beneficiarse de una planta central de alta eficiencia.</li><li><b>Ciudad del Saber:</b> podría funcionar como proyecto piloto para edificios educativos y de investigación.</li></ul><p>La implementación contribuiría a reducir costos energéticos, aumentar la confiabilidad operativa y apoyar las metas nacionales de sostenibilidad.</p>' }] },
  ],
  refs: [
    'ASHRAE. (2024). Obtenido de ASHRAE handbook: HVAC systems and equipment. American Society of Heating, Refrigerating and Air-Conditioning Engineers.',
    'EMPOWER. (2024). Obtenido de Empower. (2024). District cooling systems and sustainable cities. Emirates Central Cooling Systems Corporation. https://www.empower.ae',
    'IDEA. (2023). Obtenido de District cooling guide. IDEA. https://www.districtenergy.org',
    'TRABEED. (2024). Obtenido de District cooling technology and applications. National Central Cooling Company PJSC. https://www.tabreed.ae',
  ],
};
// Ruta principal: 4 escenas con rótulo breve; los pasos 3.0–3.5 quedan en la profundización (chips «Detalle»)
export const SC8 = [
  { id: 'E1', n: 'E1', level: 'RP', title: 'Una planta para muchos edificios', chips: ['fund', 'planta'],
    rot: { ref: 'M8 · Fundamentos · Componentes', stamp: 'df', f: 'Una planta central enfría agua con chillers y la distribuye por una red de tuberías a varios edificios', fc: 'ASHRAE, 2024',
      extra: '<span class="st il">Ilustrativo</span> Chillers, torres de enfriamiento, bombas, tanque de almacenamiento térmico y sala de control: equipos genéricos.' } },
  { id: 'E2', n: 'E2', level: 'RP', title: 'Frío que sale, calor que vuelve', chips: ['red'],
    rot: { ref: 'M8 · Red de distribución', stamp: 'df', f: 'El agua fría viaja por tuberías aisladas y regresa más caliente a la planta, donde se enfría de nuevo', fc: 'ASHRAE, 2024; IDEA, 2023',
      extra: '<span class="st il">Ilustrativo</span> Azul: suministro de agua fría. Rojo: retorno más caliente. Sin escala de temperatura.' } },
  { id: 'E3', n: 'E3', level: 'RP', title: 'La estación de cada edificio', chips: ['control'],
    rot: { ref: 'M8 · Fundamentos · Estaciones de intercambio', stamp: 'df', f: 'En cada edificio, el agua fría absorbe el calor en un intercambiador y retorna a la planta', fc: 'ASHRAE, 2024',
      extra: '<span class="st il">Ilustrativo</span> Corte de un edificio: intercambiador de placas, válvulas de control y medidor de energía térmica.' } },
  { id: 'E4', n: 'E4', level: 'RP', title: '¿Y en Panamá?', chips: ['dubai', 'panama'],
    rot: { replay: true, ref: 'M8 · Potencial de implementación en Panamá', stamp: 'pr', stampText: 'Propuesta · M8', f: 'El informe propone zonas de alta densidad y demanda continua: Área Bancaria, Ciudad de la Salud, Tocumen y Ciudad del Saber',
      extra: '<span class="st il">Ilustrativo</span> Ciudad genérica con cuatro zonas rotuladas: no es un mapa real.' } },
];
