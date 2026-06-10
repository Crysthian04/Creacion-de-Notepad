/* ============================================================
   Arranque de la aplicación: pestañas, reloj global, init
   ============================================================ */

(function () {
  // Cambio de pestañas (inicialización perezosa de cada vista)
  const inits = {
    vista2d: () => Plano2D.init(),
    vista3d: () => Plano3D.init(),
    vistaPid: () => PID.init(),
    vistaUni: () => Unifilar.init(),
    vistaSim: () => SimUI.init(),
  };

  document.querySelectorAll('nav.tabs button').forEach((btn) => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('nav.tabs button').forEach((b) => b.classList.remove('activo'));
      btn.classList.add('activo');
      document.querySelectorAll('.vista').forEach((v) => v.classList.remove('activa'));
      const id = btn.dataset.vista;
      document.getElementById(id).classList.add('activa');
      inits[id]();
      if (id === 'vista3d') Plano3D.redimensionar();
      cerrarDrawer();
    });
  });

  // Reloj de planta global (siempre visible en el encabezado)
  function actualizarReloj() {
    const t = Sim.infoTiempo();
    document.getElementById('rjDia').textContent = t.dia;
    document.getElementById('rjHora').textContent = t.hora;
    document.getElementById('rjTurno').textContent = t.turno;
    document.getElementById('rjAct').textContent = Sim.corriendo
      ? Sim.actividadTexto
      : (Sim.actividadTexto ? '⏸ ' + Sim.actividadTexto : 'Simulación pausada — ▶ Iniciar en pestaña 5');
    document.getElementById('relojPlanta').classList.toggle('parado', !Sim.corriendo);
  }
  Bus.on('tick', actualizarReloj);

  // Cerrar drawer con Escape o clic fuera
  document.addEventListener('keydown', (e) => { if (e.key === 'Escape') cerrarDrawer(); });

  // Estado inicial: planta eficiente, sin alertas
  Sim.reset();
  Plano2D.init();
  SimUI.init();
  actualizarReloj();
})();
