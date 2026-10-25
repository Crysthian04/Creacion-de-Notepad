// Texto de la Parada 1 · M6. Única fuente: Word final del M6 (y su ficha para las páginas de las obras).
// Citas con la forma exacta del Word; la sigla DOE/AMCA se define solo en la tarjeta de apertura.
const IMP = '<i>Improving fan system performance: A sourcebook for industry</i>';
const DOEAMCA = 'U.S. Department of Energy y Air Movement and Control Association International';
export const FIG = {
  1: { src: 'assets/img/m6_fig01.jpg', title: 'Figura 1. <i>Example Fan System Components</i>', credit: `Tomado de ${IMP} (p. 10), por ${DOEAMCA}, 2003.` },
  2: { src: 'assets/img/m6_fig02.jpg', title: 'Figura 2. Secuencia del proceso TAB, desde la contratación hasta la verificación', credit: 'Elaboración propia a partir de Yale Facilities (2025) y Guzmán Solano (2025).' },
  3: { src: 'assets/img/m6_fig03.jpg', title: 'Figura 3. <i>(a) Proper Belt Tension; (b) Improper Alignment</i>', credit: `Tomado de ${IMP} (pp. 49–50), por ${DOEAMCA}, 2003.` },
  4: { src: 'assets/img/m6_fig04.jpg', title: 'Figura 4. <i>Alternative Methods of Measuring Fan Pressure</i>', credit: `Tomado de ${IMP} (p. 58), por ${DOEAMCA}, 2003.` },
  5: { src: 'assets/img/m6_fig05.jpg', title: 'Figura 5. <i>(a) Schematic layout of the reference air distribution network; (b) Scheme of the control loop</i>', credit: 'Tomado de "A non-iterative method for testing, adjusting and balancing (TAB) air ducts systems: Theory, practical procedure and validation" (p. 326), por F. Pedranzini, L. P. M. Colombo y C. M. Joppolo, 2013, <i>Energy and Buildings, 65</i>.' },
  6: { src: 'assets/img/m6_fig06.jpg', title: 'Figura 6. Imágenes de las diferentes mediciones que se realizaron en el proceso de validación', credit: 'Tomado de <i>Diseño y validación del sistema de renovación de aire de un laboratorio farmacéutico ubicado en Bogotá D.C., Colombia</i> (p. 132), por J. S. Cristiano Mendivelso y K. C. Hernández Romero, 2023, Universidad Distrital Francisco José de Caldas.' },
  7: { src: 'assets/img/m6_fig07.jpg', title: 'Figura 7. Caudal, presión y potencia del ventilador en función de su velocidad', credit: `Elaboración propia con las leyes de los ventiladores de ${DOEAMCA} (2003, p. 4).` },
  8: { src: 'assets/img/m6_fig08.jpg', title: 'Figura 8. <i>System Effect for a Typical Fan and System</i>', credit: `Tomado de ${IMP} (p. 9), por ${DOEAMCA}, 2003.` },
  9: { src: 'assets/img/m6_fig09.jpg', title: 'Figura 9. Desviación del caudal medido respecto al de diseño en las 33 rejillas de suministro', credit: 'Elaboración propia con datos de la Tabla 29 de Cristiano Mendivelso y Hernández Romero (2023, pp. 137–138). El signo indica si la rejilla entregó más (+) o menos (−) aire que el de diseño; la barra de ASC está recortada en 20&nbsp;% por escala.' },
  10: { src: 'assets/img/m6_fig10.jpg', title: 'Figura 10. <i>Pre-CC and post-CC heating water consumption at the Kleberg Building vs. daily average outdoor temperature</i>', credit: 'Tomado de <i>Commissioning of existing buildings: State of the technology and its implementation</i> (Figura 1), por D. E. Claridge, M. Liu y W. D. Turner, 2003.' },
  11: { src: 'assets/img/m6_fig11.jpg', title: 'Figura 11. Modelo energético del Edificio N°1 antes de simulación', credit: 'Tomado de "Análisis energético del edificio N°1 de la Universidad Tecnológica de Panamá: simulación y optimización del consumo de energía eléctrica a través de soluciones de eficiencia energética" (p. 143), por C. Gollini-Mihalopoulos, A. Berbey-Alvarez y F. Henríquez, 2023, <i>Tecnología en Marcha, 36</i>(1).' },
};
const link = n => ({ ...FIG[n], link: true });

const TABLA1 = `<div class="ft" style="font-weight:600;margin-bottom:8px">Tabla 1. Comparación de los métodos de balanceo de proporción y de flujo progresivo</div>
<table class="t1"><tr><th>Criterio</th><th>Método de proporción (<i>ratio method</i>)</th><th>Método de flujo progresivo</th></tr>
<tr><td>Principio</td><td>Se calcula la relación caudal medido/caudal de diseño en cada terminal y se igualan las relaciones por pares, empezando por los dos terminales más desfavorecidos</td><td>Se ajusta un terminal a la vez, directamente a su caudal de diseño, desde el último terminal hacia el ventilador</td></tr>
<tr><td>¿Es iterativo?</td><td>Sí: cada ajuste de compuerta cambia las relaciones de los demás terminales</td><td>No: el número de operaciones no depende de la tolerancia ni de la habilidad del operador</td></tr>
<tr><td>Pasos en el banco de 8 terminales</td><td>14</td><td>10</td></tr>
<tr><td>Mediciones</td><td>Mínimo de n + 2(n + b − 1) + 1 para n terminales y b ramales</td><td>Se evitan 2n + b − 1 mediciones: entre 57&nbsp;% y 67&nbsp;% menos</td></tr>
<tr><td>Equipo necesario</td><td>Instrumentos de medición convencionales y ajuste final de la velocidad del ventilador</td><td>Ventilador con variador, lazo de control y sonda de referencia</td></tr>
<tr><td>Limitación</td><td>La duración no se puede prever y el resultado depende de la experiencia del operador</td><td>Validado en un banco de laboratorio a escala, no en un edificio</td></tr></table>
<div class="cr" style="margin-top:8px">Elaboración propia con datos de Pedranzini et al. (2013, pp. 323–329).</div>`;

// Ruta principal: 4 escenas con rótulo breve; los pasos de siempre quedan en la profundización (chips «Detalle»)
export const SC6 = [
  { id: 'E1', n: 'E1', level: 'RP', title: 'La red y su criterio', chips: ['red', 'marco', 'previas', 'nebb', 'fugas', 'correas', 'presion'],
    rot: { ref: 'M6 · El TAB y su marco normativo', stamp: 'df', f: 'Un balanceo se acepta cuando el caudal de cada terminal queda dentro de ±5&nbsp;% del caudal de diseño', fc: 'Yale Facilities, 2025, §4.3A, p. 23' } },
  { id: 'E2', n: 'E2', level: 'RP', title: 'Cerrar una compuerta mueve a todas', chips: ['proporcion', 'progresivo', 'medir'],
    rot: { ref: 'M6 · Métodos de balanceo · Tabla 1', stamp: 'df', f: 'Cada ajuste de una compuerta cambia el caudal de los demás ramales; por eso el método de proporción es iterativo', fc: 'Pedranzini et al., 2013, p. 323',
      c: 'Banco de 8 terminales: 14 pasos por proporción, 10 por flujo progresivo', cc: 'Pedranzini et al., 2013, p. 328',
      extra: '<span class="st il">Simulación ilustrativa · ΔP = R·Q² (Pedranzini et al., 2013, p. 323) · sin valores</span> Clic en una compuerta: abierta → media → cerrada.',
      ui: '<div class="cmp"><button class="btn" id="cmpBtn">Comparar métodos</button><div class="cmprow" hidden><span>Proporción</span><i data-cmp="p"></i><b data-cmpn="p">0 de 14</b></div><div class="cmprow" hidden><span>Flujo progresivo</span><i data-cmp="f"></i><b data-cmpn="f">0 de 10</b></div></div>' } },
  { id: 'E3', n: 'E3', level: 'RP', title: 'Abrir compuertas y bajar el ventilador', chips: ['apertura', 'leyes', 'efecto'],
    rot: { ref: 'M6 · Del balanceo al consumo de energía · Figura 7', stamp: 'df', f: 'Después del balanceo, el último ajuste es el ventilador: compuertas abiertas y menor velocidad para el mismo caudal', fc: 'Pedranzini et al., 2013',
      c: '−20&nbsp;% de velocidad = −50&nbsp;% de potencia', cc: 'DOE y AMCA, 2003, p. 18',
      ui: '<div class="laws"><label class="lw">Velocidad del ventilador<input type="range" id="spd" min="50" max="100" value="100" step="1"><span class="mk"></span></label><div class="bar"><span>Caudal ∝ N</span><i data-law="1"></i></div><div class="bar"><span>Presión ∝ N²</span><i data-law="2"></i></div><div class="bar"><span>Potencia ∝ N³</span><i data-law="3"></i></div><button class="btn" id="spd80">−20&nbsp;% de velocidad</button></div><p class="small"><span class="st il">Ilustrativo</span> barras sin escala.</p>' } },
  { id: 'E4', n: 'E4', level: 'RP', title: 'Panamá', chips: ['panama', 'cierre', 'kleberg', 'bogota', 'normas'],
    rot: { ref: 'M6 · Aplicación al contexto panameño · Figura 11', stamp: 'df', f: 'En el Edificio N.° 1 de la UTP, la climatización es el 72.90&nbsp;% del consumo eléctrico teórico', fc: 'Gollini-Mihalopoulos et al., 2023, p. 143',
      c: 'Volumen variable: −14.10&nbsp;% en la simulación', cc: 'Gollini-Mihalopoulos et al., 2023, pp. 146, 148', extra: '<span class="st il">Ilustrativo</span> variador y cajas VAV en la red del modelo; el edificio no se modela.' } },
];
export const M6 = {
  stop: { kicker: 'Parada 1 · M6', short: 'M6', title: 'Mantenimiento de Ventiladores y Sistemas de Distribución', lead: 'Métodos de balanceo de aire (TAB) y su impacto en la eficiencia energética.' },
  note: 'Modelo conceptual, no a escala. La red de ductos es ilustrativa.',
  steps: [
    { id: 'red', n: '1.0', level: 'RP', title: 'Ventilador y red de ductos', ref: 'M6 · Introducción · Figura 1', cards: [
      { ref: 'M6 · Introducción', stamp: 'df', cite: 'Consejo de Gabinete, 2022, p. 34; U.S. Department of Energy [DOE] y Air Movement and Control Association International [AMCA], 2003', title: 'El ventilador también consume',
        body: '<p>En Panamá, casi el 60&nbsp;% de la electricidad se concentra en el sector comercial y en las oficinas públicas. En los sistemas centrales, parte de la energía la consume el ventilador que mueve el aire por filtros, serpentines, ductos y compuertas hasta cada difusor; sus motores son una porción importante del costo energético de la climatización.</p>' },
      { ref: 'M6 · Introducción', stamp: 'df', cite: 'Pedranzini et al., 2013, p. 322', title: 'TAB: <i>Testing, Adjusting and Balancing</i>',
        body: '<p>Un sistema de ductos recién instalado difícilmente entrega el caudal especificado en cada local. <b>Prueba</b>: medir los caudales. <b>Ajuste</b>: modificar la posición de las compuertas junto con la velocidad del ventilador. <b>Balanceo</b>: repartir el caudal entre ramales y terminales con la menor restricción posible.</p>' },
      { ref: 'M6 · Figura 1', stamp: 'il', title: 'La red de este modelo',
        body: '<p>Filtro, serpentín, ventilador con transmisión por correas, ducto principal, 4 ramales, compuertas y 8 terminales, como el banco de prueba de 8 terminales (Pedranzini et al., 2013, p. 325). La disposición y las medidas son ilustrativas.</p>', fig: link(1) },
    ] },
    { id: 'marco', n: '1.1', level: 'RP', title: 'Quién hace el TAB y cuándo se acepta', ref: 'M6 · El TAB y su marco normativo · Figura 2', cards: [
      { ref: 'M6 · El TAB y su marco normativo', stamp: 'df', cite: 'Yale Facilities, 2025', title: 'Una empresa especializada y certificada',
        body: '<p>Miembro de AABC o certificada por NEBB o por TABB, y contratada por separado del contratista mecánico. Procedimientos reconocidos: AABC MN-1, los <i>Procedural Standards</i> de NEBB o el manual SMACNA 1780, base de TABB.</p>' },
      { ref: 'M6 · El TAB y su marco normativo', stamp: 'df', cite: 'Yale Facilities, 2025, §4.3A, p. 23', title: 'Criterio de aceptación: ±5&nbsp;%',
        body: '<p>El TAB se repite hasta que los caudales medidos de aire y agua queden dentro de ±5&nbsp;% de los caudales de diseño. En el modelo, la franja verde sobre cada terminal marca ese ±5&nbsp;%.</p>' },
      { ref: 'M6 · Figura 2', stamp: 'df', cite: 'Yale Facilities, 2025; Guzmán Solano, 2025', title: 'La secuencia completa', body: '<p>Contratación → pruebas previas → balanceo → reporte → verificación.</p>', fig: link(2) },
    ] },
    { id: 'previas', n: '1.2', level: 'RP', title: 'Antes del TAB: filtros, fugas y correas', ref: 'M6 · Pruebas previas', cards: [
      { ref: 'M6 · Pruebas previas', stamp: 'df', cite: 'Yale Facilities, 2025', title: 'El TAB empieza antes de medir',
        body: '<p>El trabajo de campo del balanceo no puede iniciar hasta que la prueba de fugas de los ductos esté completa y aprobada, y los filtros deben estar limpios durante las mediciones.</p>' },
      { ref: 'M6 · Pruebas previas', stamp: 'df', cite: 'DOE y AMCA, 2003', title: 'Un camino de baja resistencia',
        body: '<p>Un ramal con una compuerta trabada en posición abierta o con una fuga grande le roba caudal a los demás puntos de entrega. El ventilador también se revisa antes: correas, poleas, rodamientos y limpieza.</p>' },
      { stamp: 'il', title: 'Animación', body: '<p>① Filtro sucio → filtro limpio. ② Prueba de fugas: se revisan las uniones del ducto. ③ Una compuerta trabada abierta se lleva más aire. ④ Revisión de correas y poleas.</p>' },
    ] },
    { id: 'proporcion', n: '1.3', level: 'RP', title: 'Balanceo: método de proporción', ref: 'M6 · Métodos de balanceo', cards: [
      { ref: 'M6 · Métodos de balanceo', stamp: 'df', cite: 'Pedranzini et al., 2013, p. 323; Yale Facilities, 2025, p. 26', title: 'Método de proporción',
        body: '<ol><li>Se abren todas las compuertas.</li><li>En cada terminal se calcula la relación caudal medido/caudal de diseño.</li><li>Se igualan las relaciones por pares, empezando por los dos terminales más desfavorecidos; cada ramal balanceado se trata como un solo terminal.</li><li>Al final se ajusta la velocidad del ventilador para que la relación de toda la red sea igual a uno.</li></ol><p>Es iterativo: cada ajuste de compuerta cambia las relaciones de los demás terminales. En campo, la especificación pide un balanceo proporcional.</p>' },
      { ref: 'M6 · Métodos de balanceo · Tabla 1', stamp: 'df', cite: 'Pedranzini et al., 2013, p. 328', title: 'Contador de pasos',
        body: '<p class="counter"><b class="n" data-cnt>0</b> de <b class="n">14</b> pasos</p><p>En el banco de prueba de 8 terminales, el método de proporción necesitó 14 pasos.</p><p><span class="st il">Ilustrativo</span> barras, compuertas y ritmo del contador. La franja es ±5&nbsp;% del diseño (Yale Facilities, 2025).</p>' },
    ] },
    { id: 'progresivo', n: '1.4', level: 'RP', title: 'Balanceo: flujo progresivo', ref: 'M6 · Métodos de balanceo · Tabla 1 · Figura 5', cards: [
      { ref: 'M6 · Métodos de balanceo', stamp: 'df', cite: 'Pedranzini et al., 2013, pp. 325, 328', title: 'Método de flujo progresivo',
        body: '<p>Ajusta un terminal a la vez, directamente a su caudal de diseño, desde el último terminal de la red hacia el ventilador. El ventilador funciona con variador de frecuencia y un lazo de control con una sonda de referencia mantiene constante el caudal del primer terminal mientras se ajustan los demás.</p><p class="counter"><b class="n" data-cnt>0</b> de <b class="n">10</b> pasos</p><p>En el banco de 8 terminales (100 a 200&nbsp;m³/h; 200 a 650&nbsp;Pa), el método necesitó 10 pasos frente a 14 del método de proporción.</p><p><span class="st il">Ilustrativo</span> barras y ritmo del contador.</p>', fig: link(5) },
      { ref: 'M6 · Tabla 1', stamp: 'df', cite: 'Pedranzini et al., 2013, pp. 322, 328–329', title: 'Tabla 1 · lo esencial',
        body: '<table><tr><th></th><th>Proporción</th><th>Flujo progresivo</th></tr><tr><td>¿Iterativo?</td><td>Sí</td><td>No</td></tr><tr><td>Pasos (banco de 8 terminales)</td><td>14</td><td>10</td></tr><tr><td>Mediciones</td><td colspan="2">Flujo progresivo: 2n + b − 1 menos (57&nbsp;% a 67&nbsp;%)</td></tr></table>', popup: { label: 'Ver Tabla 1 completa', html: TABLA1 } },
    ] },
    { id: 'apertura', n: '1.5', level: 'RP', title: 'Compuertas abiertas y velocidad del ventilador', ref: 'M6 · Del balanceo al consumo de energía', cards: [
      { ref: 'M6 · Del balanceo al consumo de energía', stamp: 'df', cite: 'Pedranzini et al., 2013, pp. 323–324', title: 'ΔP = R·Q²',
        body: '<p>En cada tramo, la caída de presión crece con el cuadrado del caudal; R es el factor de pérdidas, que aumenta cuando una compuerta se cierra. Para un mismo caudal de diseño hay infinitas combinaciones de presión del ventilador y posición de compuertas: la de menor consumo es la de máxima apertura posible de la compuerta.</p>' },
      { ref: 'M6 · Del balanceo al consumo de energía', stamp: 'df', cite: 'Pedranzini et al., 2013; Yale Facilities, 2025', title: 'El último paso es el ventilador',
        body: '<p>Un balanceo que logra los caudales cerrando compuertas, sin ajustar después el ventilador, cumple el diseño pero desperdicia energía. El paso final del TAB corrige el caudal total en el ventilador: velocidad, poleas o variador.</p><p><span class="st il">Ilustrativo</span> la animación alterna los dos casos con el mismo caudal.</p>' },
    ] },
    { id: 'leyes', n: '1.6', level: 'RP', title: 'Leyes de los ventiladores', ref: 'M6 · Del balanceo al consumo de energía · Figura 7', cards: [
      { ref: 'M6 · Del balanceo al consumo de energía', stamp: 'df', cite: 'DOE y AMCA, 2003, p. 4', title: 'Caudal ∝ N · presión ∝ N² · potencia ∝ N³',
        body: `<p>El caudal varía con la velocidad, la presión con su cuadrado y la potencia con su cubo. Mueve el control:</p>
<div class="laws"><label class="lw">Velocidad del ventilador<input type="range" id="spd" min="50" max="100" value="100" step="1"><span class="mk" title="−20 %"></span></label>
<div class="bar"><span>Caudal ∝ N</span><i data-law="1"></i></div><div class="bar"><span>Presión ∝ N²</span><i data-law="2"></i></div><div class="bar"><span>Potencia ∝ N³</span><i data-law="3"></i></div>
<button class="btn" id="spd80">Llevar al −20&nbsp;% de velocidad</button></div>
<p class="rot" id="rot"><span class="st df">Dato de fuente</span> «Reducir la velocidad del ventilador un 20&nbsp;% disminuye su potencia un 50&nbsp;%» <span class="cite">(DOE y AMCA, 2003, p. 18)</span></p>
<p>A velocidades bajas, la eficiencia y el factor de potencia del motor pueden caer y justificar un cambio de motor o un variador de frecuencia (DOE y AMCA, 2003).</p><p><span class="st il">Ilustrativo</span> barras sin escala.</p>`, fig: link(7) },
    ] },
    { id: 'panama', n: '1.7', level: 'RP', title: 'Panamá: Edificio N.° 1 de la UTP', ref: 'M6 · Aplicación al contexto panameño · Figura 11', cards: [
      { ref: 'M6 · Aplicación al contexto panameño', stamp: 'df', cite: 'Gollini-Mihalopoulos et al., 2023, p. 143', title: 'El peso de la distribución de aire',
        body: '<p>Chiller con distribución de volumen constante y torre de enfriamiento. La climatización representa el <b class="n">72.90&nbsp;%</b> de su consumo eléctrico teórico de <b class="n">2,404,170.72&nbsp;kWh</b> al año.</p>' },
      { ref: 'M6 · Aplicación al contexto panameño', stamp: 'df', cite: 'Gollini-Mihalopoulos et al., 2023, pp. 146, 148', title: 'Simulación: de volumen constante a variable',
        body: '<p>Con variadores de frecuencia en los ventiladores de las manejadoras y cajas VAV en las derivaciones, el consumo del motor de una manejadora bajó <b class="n">35&nbsp;%</b>. En todas las manejadoras y bombas: <b class="n">14.10&nbsp;%</b>, es decir, <b class="n">352,224&nbsp;kWh</b> y <b class="n">B/.&nbsp;53,777.56</b> al año.</p><p>Es una simulación y un cambio de sistema, no un TAB; pero un sistema VAV exige verificar el caudal de sus cajas terminales, que entran en la verificación del 25&nbsp;% (Yale Facilities, 2025).</p><p><span class="st il">Ilustrativo</span> variador y cajas VAV en la red del modelo; el edificio no se modela.</p>', fig: link(11) },
    ] },
    { id: 'cierre', n: '1.8', level: 'RP', title: 'Conclusiones', ref: 'M6 · Conclusiones', cards: [
      { ref: 'M6 · Conclusiones', stamp: 'df', title: 'Cinco conclusiones', wide: true,
        body: '<ol><li>El TAB es verificable solo con una tolerancia definida por terminal y una verificación independiente: con ±5&nbsp;%, un balanceo aceptable por su promedio puede tener más de la mitad de las rejillas fuera de tolerancia (Yale Facilities, 2025; Cristiano Mendivelso y Hernández Romero, 2023). → 1.1</li><li>El balanceo empieza con mantenimiento: sin filtros limpios, correas en buen estado y fugas controladas, las mediciones no representan el sistema (DOE y AMCA, 2003; Yale Facilities, 2025). → 1.2</li><li>El método de proporción sigue siendo el estándar de campo, pero es iterativo y depende del operador; el de flujo progresivo reduce las mediciones entre 57&nbsp;% y 67&nbsp;%, a cambio de variador y lazo de control (Pedranzini et al., 2013). → 1.3 y 1.4</li><li>El impacto energético se explica por la apertura de las compuertas y la reducción posterior de la velocidad del ventilador; en campo se observa en paquetes de comisionamiento, cuyos ahorros se pierden sin seguimiento (DOE y AMCA, 2003; Claridge et al., 2003). → 1.5 y 1.6</li><li>En Panamá, la normativa cubre las edificaciones nuevas pero no el balanceo de los sistemas existentes; el plan de gestión energética de la Ley 69 es el lugar práctico para un TAB periódico (Gollini-Mihalopoulos et al., 2023; Asamblea Nacional, 2012). → 1.7</li></ol>' },
    ] },
    // ---------- Profundización ----------
    { id: 'nebb', n: 'P1', level: 'PR', title: 'NEBB: antes de medir, reporte y verificación', ref: 'M6 · El TAB y su marco normativo', cards: [
      { ref: 'M6 · El TAB y su marco normativo', stamp: 'df', cite: 'NEBB, 2019, como se citó en Guzmán Solano, 2025', title: 'Antes de medir',
        body: '<ul><li>Edificio cerrado y sellado: puertas, ventanas, cielos y rejillas instalados.</li><li>Pruebas de fugas en ductos y verificación de los equipos, hechas.</li><li>Controles calibrados y listos para ajustar válvulas, compuertas y cajas VAV.</li><li>Puertos de prueba instalados y accesibles.</li><li>Documentación actualizada, como los planos <i>as built</i>.</li></ul>' },
      { ref: 'M6 · El TAB y su marco normativo', stamp: 'df', cite: 'Guzmán Solano, 2025, pp. 51–52', title: 'El reporte TAB',
        body: '<p>Instrumentos, condiciones de prueba, comparación entre el diseño y lo medido, ajustes realizados, deficiencias y certificación firmada por la empresa balanceadora.</p>' },
      { ref: 'M6 · El TAB y su marco normativo', stamp: 'df', cite: 'Yale Facilities, 2025, pp. 1, 29', title: 'Verificación independiente',
        body: '<p>El representante del propietario vuelve a medir todas las manejadoras y el 25&nbsp;% de las cajas VAV, rejillas, ventiladores y bombas. Si el 10&nbsp;% o más de los puntos se desvía 10&nbsp;% o más de lo reportado, el reporte se rechaza y se balancea de nuevo sin costo para el propietario.</p>' },
    ] },
    { id: 'fugas', n: 'P2', level: 'PR', title: 'Hermeticidad de los ductos', ref: 'M6 · Pruebas previas', cards: [
      { ref: 'M6 · Pruebas previas', stamp: 'df', cite: 'DOE y AMCA, 2003, pp. 12, 38', title: 'Clase de fuga (CL)',
        body: '<table><tr><th>CL</th><th>Condición</th></tr><tr><td>48</td><td>Promedio para ductos rectangulares sin sellar</td></tr><tr><td>24 (12 en redondos)</td><td>Uniones transversales selladas</td></tr><tr><td>6 (3 en redondos)</td><td>Todas las uniones, costuras y penetraciones selladas</td></tr></table><p>Las fugas pueden consumir una parte significativa de la capacidad del ventilador; se recomiendan pruebas de hermeticidad en sistemas que superan 2 o 3&nbsp;in&nbsp;wg.</p><p><span class="st il">Ilustrativo</span> las uniones del ducto cambian de color con los tres estados.</p>' },
    ] },
    { id: 'correas', n: 'P3', level: 'PR', title: 'Correas y lista de mantenimiento', ref: 'M6 · Pruebas previas · Figura 3', cards: [
      { ref: 'M6 · Pruebas previas', stamp: 'df', cite: 'DOE y AMCA, 2003, p. 25', title: 'La parte que más mantenimiento requiere',
        body: '<p>Aun nuevas y bien ajustadas, las correas pierden de 5&nbsp;% a 10&nbsp;% de la potencia transmitida, y las pérdidas aumentan con el desgaste. En un ventilador de 200&nbsp;hp, una caída de 5&nbsp;% en la eficiencia de transmisión equivale a 10&nbsp;hp, unos USD&nbsp;3,270 al año si opera de forma continua a USD&nbsp;0.05/kWh.</p><ul><li>Correas y poleas: estado, tensión y alineación.</li><li>Rodamientos: ruido, temperatura o análisis de vibraciones.</li><li>Limpieza de ventiladores y componentes.</li><li>Fugas en ductos y aislamiento del motor.</li></ul>', fig: link(3) },
    ] },
    { id: 'presion', n: 'P4', level: 'PR', title: 'Medición de presión del ventilador', ref: 'M6 · Pruebas previas · Figura 4', cards: [
      { ref: 'M6 · Pruebas previas', stamp: 'df', cite: 'DOE y AMCA, 2003, p. 57', title: 'Presión y curva del fabricante',
        body: '<p>Se mide la presión del aire y con la curva del fabricante se obtiene la potencia correspondiente. La forma correcta de medir depende de si la entrada y la salida del ventilador están conectadas a ductos.</p><p><span class="st il">Ilustrativo</span> tomas de presión en la entrada y la salida.</p>', fig: link(4) },
    ] },
    { id: 'medir', n: 'P5', level: 'PR', title: 'Medir el caudal no es trivial', ref: 'M6 · Métodos de balanceo · Figura 6', cards: [
      { ref: 'M6 · Métodos de balanceo', stamp: 'df', cite: 'Pedranzini et al., 2013', title: 'Varias lecturas y un promedio',
        body: '<p>La velocidad del aire rara vez es uniforme en la sección: los anemómetros de aspas y los tubos de Pitot requieren varias lecturas y un promedio, un procedimiento lento y propenso a errores.</p>' },
      { ref: 'M6 · Métodos de balanceo', stamp: 'df', cite: 'Cristiano Mendivelso y Hernández Romero, 2023', title: 'Prebalanceo en un laboratorio de Bogotá',
        body: '<p>Un anemómetro toma varias lecturas de velocidad en la salida de cada rejilla, las promedia y las multiplica por el área; después se ajustan a mano las compuertas hasta el caudal de diseño.</p><p><span class="st il">Ilustrativo</span> instrumento en un terminal del modelo.</p>', fig: link(6) },
    ] },
    { id: 'efecto', n: 'P6', level: 'PR', title: 'Efecto de sistema', ref: 'M6 · Del balanceo al consumo de energía · Figura 8', cards: [
      { ref: 'M6 · Del balanceo al consumo de energía', stamp: 'df', cite: 'DOE y AMCA, 2003, p. 9', title: 'Un codo junto a la salida',
        body: '<p>Una mala configuración de los ductos cerca del ventilador puede reducir el caudal entregado hasta en 30&nbsp;%, lo que obliga a aumentar la velocidad y la potencia. Muchos diseñadores compensan con ventiladores sobredimensionados, lo que eleva el costo de energía y de mantenimiento.</p><p><span class="st il">Ilustrativo</span> codo en rojo junto a la salida.</p>', fig: link(8) },
    ] },
    { id: 'kleberg', n: 'P7', level: 'PR', title: 'Evidencia de campo: edificio Kleberg', ref: 'M6 · Evidencia de campo · Figura 10', cards: [
      { ref: 'M6 · Evidencia de campo', stamp: 'df', cite: 'Claridge et al., 2003', title: 'Universidad Texas A&amp;M, ≈ 165,030&nbsp;ft²',
        body: '<p>Primeras medidas: consigna de presión estática de 1.5 a 1.0&nbsp;in&nbsp;wg (0.5&nbsp;in&nbsp;wg en la noche), con cambios en el precalentamiento y en la temperatura del aire frío. Con el paquete completo, normalizado por clima: agua helada −63.6&nbsp;% y agua caliente −84.2&nbsp;%.</p><p>1998–1999: balance de aire de 12 zonas de laboratorio, reprogramación de la extracción y calibración de cajas VAV, actuadores, compuertas y campanas: cerca de −7&nbsp;% de electricidad, unos 30,000&nbsp;kWh al mes.</p>' },
      { ref: 'M6 · Evidencia de campo', stamp: 'df', cite: 'Claridge et al., 2003; Gregerson, 1997, como se citó en Claridge et al., 2003', title: 'Sin seguimiento, el ahorro se pierde',
        body: '<p>Hacia 2000, el ahorro de agua helada había bajado a 37.7&nbsp;%: alta resistencia al aire en filtros y serpentines y consignas de presión estática elevadas. En 44 edificios comisionados, el consumo bajó entre 2&nbsp;% y 49&nbsp;% (promedio de 17.5&nbsp;%; retorno de 0.1 a 4.2 años). Son paquetes de medidas: ninguna fuente aísla el ahorro del TAB por sí solo.</p>', fig: link(10) },
    ] },
    { id: 'bogota', n: 'P8', level: 'PR', title: 'Evidencia de campo: laboratorio de Bogotá', ref: 'M6 · Evidencia de campo · Figura 9', cards: [
      { ref: 'M6 · Evidencia de campo', stamp: 'df', cite: 'Cristiano Mendivelso y Hernández Romero, 2023', title: 'El promedio oculta la dispersión',
        body: '<p>En las 33 rejillas de suministro, la tesis reporta un error promedio de 7.8&nbsp;% y lo considera aceptable.</p><p>Con el criterio de ±5&nbsp;% por terminal: <b class="n">17 de 33</b> rejillas fuera de tolerancia y <b class="n">6</b> por encima del 10&nbsp;%. El mayor desvío, <b class="n">74&nbsp;%</b>, es un terminal de 60&nbsp;CFM que entregó 105&nbsp;CFM; sin ese caso, el promedio baja a 5.7&nbsp;% (elaboración propia con datos de Cristiano Mendivelso y Hernández Romero, 2023, pp. 137–138).</p>', fig: link(9) },
    ] },
    { id: 'normas', n: 'P9', level: 'PR', title: 'Marco panameño', ref: 'M6 · Aplicación al contexto panameño', cards: [
      { ref: 'M6 · Aplicación al contexto panameño', stamp: 'df', cite: 'Secretaría Nacional de Energía, 2016, p. 21', title: 'Resolución N.° 3142 de 2016',
        body: '<p>Para nuevas edificaciones; recomienda ahorros graduales de 15&nbsp;% y luego de 20&nbsp;% frente a una línea base. Incluye variadores en el motor del ventilador de las manejadoras, pero no requisitos sobre ductos, filtros, balanceo ni comisionamiento.</p>' },
      { ref: 'M6 · Aplicación al contexto panameño', stamp: 'df', cite: 'Consejo de Gabinete, 2022, pp. 58, 60', title: 'ENUREE',
        body: '<p>Reconoce la necesidad de ampliar el Reglamento de Edificación Sostenible a los edificios existentes, con criterios de desempeño energético y el sector público como ejemplo.</p>' },
      { ref: 'M6 · Aplicación al contexto panameño', stamp: 'df', cite: 'Asamblea Nacional, 2012, arts. 8 y 23', title: 'Ley 69 de 2012',
        body: '<p>Cada institución pública constituye un comité de energía coordinado por un administrador energético, con un plan de gestión de la eficiencia energética de al menos cinco años, revisado cada año. Incluir en ese plan un TAB periódico (NEBB, AABC o TABB), precedido por limpieza de filtros, revisión de correas y prueba de fugas, haría del mantenimiento de ventiladores una medida de eficiencia verificable (Asamblea Nacional, 2012; Yale Facilities, 2025).</p>' },
    ] },
  ],
  refs: [
    'Asamblea Nacional. (2012, 18 de octubre). Ley 69 de 12 de octubre de 2012, que establece los lineamientos generales de la política nacional para el uso racional y eficiente de la energía en el territorio nacional. <i>Gaceta Oficial Digital</i>, (27145-A).',
    'Claridge, D. E., Liu, M., y Turner, W. D. (2003). <i>Commissioning of existing buildings: State of the technology and its implementation</i> [Ponencia]. International Institute of Refrigeration, base Fridoc. https://iifiir.org/en/fridoc/commissioning-of-existing-buildings-state-of-the-technology-and-its-22660',
    'Consejo de Gabinete. (2022, 1 de junio). Resolución de Gabinete N.° 66, que aprueba la Estrategia Nacional de Uso Racional y Eficiente de la Energía (ENUREE) y crea la Comisión Interinstitucional de Uso Racional y Eficiente de la Energía (CIUREE). <i>Gaceta Oficial Digital</i>, (29549-B).',
    'Cristiano Mendivelso, J. S., y Hernández Romero, K. C. (2023). <i>Diseño y validación del sistema de renovación de aire de un laboratorio farmacéutico ubicado en Bogotá D.C., Colombia</i> [Trabajo de grado, Universidad Distrital Francisco José de Caldas].',
    'Gollini-Mihalopoulos, C., Berbey-Alvarez, A., y Henríquez, F. (2023). Análisis energético del edificio N°1 de la Universidad Tecnológica de Panamá: simulación y optimización del consumo de energía eléctrica a través de soluciones de eficiencia energética. <i>Tecnología en Marcha, 36</i>(1), 140–151. https://doi.org/10.18845/tm.v36i1.5874',
    'Guzmán Solano, D. (2025). <i>Propuesta para la estandarización y aplicación de buenas prácticas para la construcción de cuartos limpios: Calidad, programación y metodología constructiva</i> [Trabajo final de graduación, Instituto Tecnológico de Costa Rica].',
    'Pedranzini, F., Colombo, L. P. M., y Joppolo, C. M. (2013). A non-iterative method for testing, adjusting and balancing (TAB) air ducts systems: Theory, practical procedure and validation. <i>Energy and Buildings, 65</i>, 322–330. https://doi.org/10.1016/j.enbuild.2013.06.017',
    'Secretaría Nacional de Energía. (2016, 24 de noviembre). Resolución N.° 3142 de 17 de noviembre de 2016, que adopta la Guía de construcción sostenible para el ahorro de energía en edificaciones y medidas para el uso racional y eficiente de la energía, para la construcción de nuevas edificaciones en la República de Panamá. <i>Gaceta Oficial Digital</i>, (28165). https://www.gacetaoficial.gob.pa/pdfTemp/28165/58747.pdf',
    'U.S. Department of Energy y Air Movement and Control Association International. (2003). <i>Improving fan system performance: A sourcebook for industry</i>.',
    'Yale Facilities. (2025). <i>Requirements for testing, adjusting, and balancing for HVAC</i> (Design Standard 23 05 93). Yale University. https://facilities.yale.edu/sites/default/files/files/Design%20Standards/Updated%20Design%20Standards/23%20HVAC/23%2005%2093%20Testing%2C%20Adjusting%2C%20and%20Balancing%20for%20HVAC_20250110_FINAL%20V1.pdf',
  ],
};
