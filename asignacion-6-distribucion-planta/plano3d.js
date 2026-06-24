/* ============================================================
   Pestaña 2 — Plano 3D (Three.js r128 vía CDN)
   Controles orbitales propios (no se asume THREE.OrbitControls).
   Coordenadas: plano (x,y) m → 3D (x-50, altura, y-50).
   ============================================================ */

// ----- Control orbital propio compatible con r128 -----
class ControlOrbital {
  constructor(camara, dom) {
    this.camara = camara;
    this.dom = dom;
    this.objetivo = new THREE.Vector3(0, 0, 0);
    this.esfera = new THREE.Spherical(150, Math.PI / 3.2, -Math.PI / 4);
    this._boton = -1;
    this._px = 0; this._py = 0;

    dom.addEventListener('contextmenu', (e) => e.preventDefault());
    dom.addEventListener('mousedown', (e) => { this._boton = e.button; this._px = e.clientX; this._py = e.clientY; });
    window.addEventListener('mouseup', () => { this._boton = -1; });
    window.addEventListener('mousemove', (e) => {
      if (this._boton === -1) return;
      const dx = e.clientX - this._px, dy = e.clientY - this._py;
      this._px = e.clientX; this._py = e.clientY;
      if (this._boton === 0) { // rotar
        this.esfera.theta -= dx * 0.006;
        this.esfera.phi = Math.max(0.08, Math.min(Math.PI / 2.05, this.esfera.phi - dy * 0.006));
      } else { // pan (botón derecho o medio)
        const v = new THREE.Vector3();
        this.camara.getWorldDirection(v);
        const derecha = new THREE.Vector3().crossVectors(v, this.camara.up).normalize();
        const arriba = new THREE.Vector3().crossVectors(derecha, v).normalize();
        const k = this.esfera.radius * 0.0014;
        this.objetivo.addScaledVector(derecha, -dx * k);
        this.objetivo.addScaledVector(arriba, dy * k);
      }
      this.actualizar();
    });
    dom.addEventListener('wheel', (e) => {
      e.preventDefault();
      this.esfera.radius = Math.max(15, Math.min(450, this.esfera.radius * (e.deltaY > 0 ? 1.1 : 0.9)));
      this.actualizar();
    }, { passive: false });
    this.actualizar();
  }
  irA(radio, phi, theta, objetivo) {
    this.esfera.set(radio, phi, theta);
    this.objetivo.copy(objetivo);
    this.actualizar();
  }
  actualizar() {
    const p = new THREE.Vector3().setFromSpherical(this.esfera).add(this.objetivo);
    this.camara.position.copy(p);
    this.camara.lookAt(this.objetivo);
  }
}

const Plano3D = {
  inicializado: false,

  init() {
    if (this.inicializado) { this.redimensionar(); return; }
    this.inicializado = true;
    const cont = document.getElementById('contenedor3d');
    const vista = document.getElementById('vista3d');

    const tb = document.createElement('div');
    tb.className = 'toolbar';
    tb.innerHTML = `
      <button data-cam="general" class="on">🏭 Vista general</button>
      <button data-cam="naveA">Nave A</button>
      <button data-cam="naveB">Nave B</button>
      <button data-cam="servicios">Servicios</button>
      <label class="toggle" style="cursor:default">🖱 Izq: rotar · Der: pan · Rueda: zoom · Clic: ficha técnica</label>`;
    vista.appendChild(tb);

    // Escena
    this.escena = new THREE.Scene();
    this.escena.background = new THREE.Color(0xdce8f0);
    this.escena.fog = new THREE.Fog(0xdce8f0, 250, 600);
    this.camara = new THREE.PerspectiveCamera(50, 1, 0.5, 1200);
    this.renderer = new THREE.WebGLRenderer({ antialias: true });
    cont.appendChild(this.renderer.domElement);
    this.control = new ControlOrbital(this.camara, this.renderer.domElement);

    // Luces
    this.escena.add(new THREE.AmbientLight(0xffffff, 0.55));
    const sol = new THREE.DirectionalLight(0xfff4e0, 0.85);
    sol.position.set(80, 120, -60);
    this.escena.add(sol);

    this.clicables = [];
    this.construirEscena();
    this.construirParticulas();

    // Cámaras predefinidas
    const CAMS = {
      general:   [160, Math.PI / 3.4, -Math.PI / 4, new THREE.Vector3(0, 0, 0)],
      naveA:     [70, Math.PI / 3.4, -Math.PI / 3, new THREE.Vector3(-22, 8, -6)],
      naveB:     [55, Math.PI / 3.4, -Math.PI / 2.6, new THREE.Vector3(-25, 4, 21)],
      servicios: [55, Math.PI / 3.4, -Math.PI / 5, new THREE.Vector3(8, 4, -4)],
    };
    tb.querySelectorAll('button[data-cam]').forEach((b) => {
      b.onclick = () => {
        tb.querySelectorAll('button[data-cam]').forEach((x) => x.classList.remove('on'));
        b.classList.add('on');
        this.control.irA(...CAMS[b.dataset.cam]);
      };
    });

    // Raycasting: hover + clic
    const ray = new THREE.Raycaster();
    const mouse = new THREE.Vector2();
    let hoverId = null;
    const intersecta = (e) => {
      const r = this.renderer.domElement.getBoundingClientRect();
      mouse.x = ((e.clientX - r.left) / r.width) * 2 - 1;
      mouse.y = -((e.clientY - r.top) / r.height) * 2 + 1;
      ray.setFromCamera(mouse, this.camara);
      const hits = ray.intersectObjects(this.clicables, true);
      let obj = hits[0] ? hits[0].object : null;
      while (obj && !obj.userData.id) obj = obj.parent;
      return obj;
    };
    this.renderer.domElement.addEventListener('mousemove', (e) => {
      const obj = intersecta(e);
      if (obj) {
        const item = getItem(obj.userData.id);
        const volt = item.alimentacion || (item.ficha && item.ficha.alimentacion) || '';
        mostrarTooltip(e, `<b>${item.nombre}</b><br><span class="tt-volt">⚡ ${volt}</span>`);
        this.renderer.domElement.style.cursor = 'pointer';
        hoverId = obj.userData.id;
      } else if (hoverId) {
        ocultarTooltip();
        this.renderer.domElement.style.cursor = '';
        hoverId = null;
      }
    });
    let down = null;
    this.renderer.domElement.addEventListener('mousedown', (e) => { down = [e.clientX, e.clientY]; });
    this.renderer.domElement.addEventListener('mouseup', (e) => {
      if (!down || Math.hypot(e.clientX - down[0], e.clientY - down[1]) > 5) return; // fue arrastre
      const obj = intersecta(e);
      if (obj) abrirFicha(obj.userData.id);
    });

    window.addEventListener('resize', () => this.redimensionar());
    this.redimensionar();
    this.animar();
  },

  redimensionar() {
    if (!this.renderer) return;
    const cont = document.getElementById('contenedor3d');
    const w = cont.clientWidth || 800, h = cont.clientHeight || 500;
    this.renderer.setSize(w, h);
    this.camara.aspect = w / h;
    this.camara.updateProjectionMatrix();
  },

  // util: posiciona según coordenadas de plano (metros)
  aXZ(x, y) { return [x - 50, y - 50]; },

  cajaMalla(p, altura, color, opacidad, id) {
    const [cx, cz] = this.aXZ(p.x + p.w / 2, p.y + p.h / 2);
    const mat = new THREE.MeshLambertMaterial({ color, transparent: opacidad < 1, opacity: opacidad });
    const m = new THREE.Mesh(new THREE.BoxGeometry(p.w, altura, p.h), mat);
    m.position.set(cx, altura / 2, cz);
    if (id) { m.userData.id = id; this.clicables.push(m); }
    this.escena.add(m);
    return m;
  },

  construirEscena() {
    // Terreno
    const suelo = new THREE.Mesh(new THREE.BoxGeometry(100, 0.5, 100), new THREE.MeshLambertMaterial({ color: 0x9aa98a }));
    suelo.position.y = -0.25;
    this.escena.add(suelo);
    // vial perimetral
    const vial = new THREE.Mesh(new THREE.BoxGeometry(98, 0.1, 98), new THREE.MeshLambertMaterial({ color: 0x707880 }));
    vial.position.y = 0.02;
    this.escena.add(vial);
    const interior = new THREE.Mesh(new THREE.BoxGeometry(84, 0.12, 84), new THREE.MeshLambertMaterial({ color: 0x9aa98a }));
    interior.position.y = 0.05;
    this.escena.add(interior);

    // Edificios (semitransparentes para ver los equipos)
    const colores = { naveA: 0x7fa8cc, naveB: 0x86bb95, edifC: 0xc9a07a, edifD: 0xa48fc4, edifE: 0xc4b76a, patioSilos: 0xb0b6ba, bahias: 0x8d9c8d };
    for (const ed of Object.values(PLANT_DATA.edificios)) {
      if (ed.altura <= 0) {
        const [cx, cz] = this.aXZ(ed.pos.x + ed.pos.w / 2, ed.pos.y + ed.pos.h / 2);
        const plano = new THREE.Mesh(new THREE.BoxGeometry(ed.pos.w, 0.15, ed.pos.h),
          new THREE.MeshLambertMaterial({ color: ed.id === 'expansion' ? 0xc7d4b0 : 0x8e9aa6 }));
        plano.position.set(cx, 0.1, cz);
        plano.userData.id = ed.id;
        this.clicables.push(plano);
        this.escena.add(plano);
        continue;
      }
      const op = ed.id === 'naveA' || ed.id === 'naveB' ? 0.32 : 0.85;
      this.cajaMalla(ed.pos, ed.altura, colores[ed.id] || 0xb0b0b0, op, ed.id);
      // aristas
      const [cx, cz] = this.aXZ(ed.pos.x + ed.pos.w / 2, ed.pos.y + ed.pos.h / 2);
      const aristas = new THREE.LineSegments(
        new THREE.EdgesGeometry(new THREE.BoxGeometry(ed.pos.w, ed.altura, ed.pos.h)),
        new THREE.LineBasicMaterial({ color: 0x1a3a5c }));
      aristas.position.set(cx, ed.altura / 2, cz);
      this.escena.add(aristas);
    }

    // Pasarela de interconexión
    const [px, pz] = this.aXZ(25, 58);
    const pasarela = new THREE.Mesh(new THREE.BoxGeometry(3, 4, 8), new THREE.MeshLambertMaterial({ color: 0xa8b8c8 }));
    pasarela.position.set(px, 2, pz);
    this.escena.add(pasarela);

    // Silos: 4 cilindros Ø2.5
    for (let i = 0; i < 4; i++) {
      const [sx, sz] = this.aXZ(48.7 + i * 3.4, 26.5);
      const silo = new THREE.Mesh(new THREE.CylinderGeometry(1.25, 1.25, 11, 20),
        new THREE.MeshLambertMaterial({ color: 0xd5dade }));
      silo.position.set(sx, 5.5 + 0.5, sz);
      silo.userData.id = 'silos';
      this.clicables.push(silo);
      this.escena.add(silo);
      const conoSilo = new THREE.Mesh(new THREE.ConeGeometry(1.25, 1.6, 20), new THREE.MeshLambertMaterial({ color: 0xb8bec2 }));
      conoSilo.position.set(sx, 12, sz);
      conoSilo.userData.id = 'silos';
      this.escena.add(conoSilo);
    }

    // ---- TORRE GEA NIRO®: cilindro + cono, el elemento más alto ----
    const gTorre = new THREE.Group();
    const [tx, tz] = this.aXZ(26, 44);
    const matTorre = new THREE.MeshLambertMaterial({ color: 0xe8e8ee });
    this.matTorre = matTorre;
    const cil = new THREE.Mesh(new THREE.CylinderGeometry(5, 5, 13, 28), matTorre);
    cil.position.y = 6 + 6.5;
    const cono = new THREE.Mesh(new THREE.ConeGeometry(5, 6, 28), matTorre);
    cono.rotation.x = Math.PI; // cono invertido (descarga)
    cono.position.y = 3;
    const tapa = new THREE.Mesh(new THREE.ConeGeometry(5, 2.5, 28), matTorre);
    tapa.position.y = 19.5 + 1.25;
    [cil, cono, tapa].forEach((m) => { m.userData.id = 'torre'; gTorre.add(m); this.clicables.push(m); });
    gTorre.position.set(tx, 0, tz);
    this.escena.add(gTorre);

    // Equipos como cajas/cilindros
    const equiposGeom = {
      tk101: { tipo: 'cil', r: 1.5, h: 4.5, color: 0x6fa3d8 },
      tk102: { tipo: 'cil', r: 1.5, h: 4.5, color: 0x6fa3d8 },
      p101: { tipo: 'caja', color: 0x4a7fb5 },
      p102: { tipo: 'caja', color: 0x4a7fb5 },
      enfriador: { tipo: 'caja', color: 0xd8c66f },
      postadicion: { tipo: 'caja', color: 0xd8c66f },
      tolvas: { tipo: 'caja', color: 0xd8a93f },
      distribuidor: { tipo: 'caja', color: 0xb087c4 },
      vffs: { tipo: 'caja', color: 0x6fbb7e },
      ensacadora: { tipo: 'caja', color: 0x6fbb7e },
      checkweigher: { tipo: 'caja', color: 0x5fae9f },
      bc101: { tipo: 'caja', color: 0x9c8a80 },
      bc102: { tipo: 'caja', color: 0x9c8a80 },
      paletizador: { tipo: 'caja', color: 0xe09b4d },
      cuarentena: { tipo: 'caja', color: 0xc94f4f },
    };
    this.mallasEquipo = {};
    for (const [id, gdef] of Object.entries(equiposGeom)) {
      const eq = PLANT_DATA.equipos[id];
      const p = eq.pos;
      let m;
      if (gdef.tipo === 'cil') {
        m = new THREE.Mesh(new THREE.CylinderGeometry(gdef.r, gdef.r, gdef.h, 18), new THREE.MeshLambertMaterial({ color: gdef.color }));
        const [cx, cz] = this.aXZ(p.x + p.w / 2, p.y + p.h / 2);
        m.position.set(cx, gdef.h / 2, cz);
        m.userData.id = id;
        this.clicables.push(m);
        this.escena.add(m);
      } else {
        m = this.cajaMalla(p, eq.alturaEq || 2, gdef.color, 1, id);
      }
      this.mallasEquipo[id] = m;
    }

    // Mezzanines (plataformas técnicas elevadas, del plano complementario)
    const mezz3d = (x, y, w, h, alt) => {
      const [cx, cz] = this.aXZ(x + w / 2, y + h / 2);
      const plat = new THREE.Mesh(new THREE.BoxGeometry(w, 0.3, h),
        new THREE.MeshLambertMaterial({ color: 0x7986cb, transparent: true, opacity: 0.55 }));
      plat.position.set(cx, alt, cz);
      this.escena.add(plat);
      // columnas de apoyo
      for (const [dx, dz] of [[-w / 2 + 0.5, -h / 2 + 0.5], [w / 2 - 0.5, -h / 2 + 0.5], [-w / 2 + 0.5, h / 2 - 0.5], [w / 2 - 0.5, h / 2 - 0.5]]) {
        const col = new THREE.Mesh(new THREE.CylinderGeometry(0.12, 0.12, alt, 8),
          new THREE.MeshLambertMaterial({ color: 0x5c6bc0 }));
        col.position.set(cx + dx, alt / 2, cz + dz);
        this.escena.add(col);
      }
    };
    mezz3d(33, 43.5, 14.5, 9.5, 4.5);  // Nave A +4.50 m
    mezz3d(31, 63, 8, 4, 3.2);          // Nave B +3.20 m

    // Camiones en bahías (cajas simples) y en acceso norte
    const camion = (x, y, rot = 0) => {
      const g = new THREE.Group();
      const caja = new THREE.Mesh(new THREE.BoxGeometry(2.5, 3, 8), new THREE.MeshLambertMaterial({ color: 0xeeeeee }));
      caja.position.y = 2;
      const cabina = new THREE.Mesh(new THREE.BoxGeometry(2.5, 2.2, 2), new THREE.MeshLambertMaterial({ color: 0x3565a0 }));
      cabina.position.set(0, 1.6, 5);
      g.add(caja, cabina);
      const [cx, cz] = this.aXZ(x, y);
      g.position.set(cx, 0, cz);
      g.rotation.y = rot;
      this.escena.add(g);
    };
    camion(16, 88.5); camion(29, 88.5); camion(35.5, 88.5);
    camion(60, 4.5, Math.PI / 2);

    // ---- Zona de Descarga de Materia Prima (Subproceso ①): 2 camiones + fosa + filtro colector ----
    camion(33.4, 22, Math.PI); camion(42.1, 22, Math.PI);
    // fosa de recepción (cilindro corto semienterrado, centrado)
    const [fx, fz] = this.aXZ(37.75, 25.5);
    const fosa = new THREE.Mesh(new THREE.CylinderGeometry(1.0, 1.0, 0.6, 16), new THREE.MeshLambertMaterial({ color: 0x607d8b }));
    fosa.position.set(fx, 0.3, fz);
    fosa.userData.id = 'descargaMp';
    this.clicables.push(fosa);
    this.escena.add(fosa);
    this.mallasEquipo.descargaMp = fosa;
    // filtro colector de polvo (cilindro vertical + tolva cónica inferior)
    const [flx, flz] = this.aXZ(34.5, 25.5);
    const filtroMat = new THREE.MeshLambertMaterial({ color: 0xb8bec2 });
    const filtroCil = new THREE.Mesh(new THREE.CylinderGeometry(0.6, 0.6, 3, 14), filtroMat);
    filtroCil.position.set(flx, 2.3, flz);
    filtroCil.userData.id = 'descargaMp';
    const filtroCono = new THREE.Mesh(new THREE.ConeGeometry(0.6, 0.9, 14), filtroMat);
    filtroCono.rotation.x = Math.PI;
    filtroCono.position.set(flx, 0.55, flz);
    filtroCono.userData.id = 'descargaMp';
    this.clicables.push(filtroCil);
    this.escena.add(filtroCil);
    this.escena.add(filtroCono);
    // ducto fosa → base de los elevadores de cangilones / silos
    const [dx1, dz1] = this.aXZ(39, 25.6);
    const [dx2, dz2] = this.aXZ(47, 26.2);
    const ducto = new THREE.Mesh(new THREE.BoxGeometry(Math.hypot(dx2 - dx1, dz2 - dz1), 0.5, 0.5), new THREE.MeshLambertMaterial({ color: 0x9e9e9e }));
    ducto.position.set((dx1 + dx2) / 2, 0.6, (dz1 + dz2) / 2);
    ducto.rotation.y = -Math.atan2(dz2 - dz1, dx2 - dx1);
    this.escena.add(ducto);
  },

  // ---------------- Animación del flujo de producto ----------------
  rutaCurva(puntos) {
    return new THREE.CatmullRomCurve3(puntos.map(([x, y, h]) => {
      const [cx, cz] = this.aXZ(x, y);
      return new THREE.Vector3(cx, h, cz);
    }));
  },

  construirParticulas() {
    // (a) AZUL — líquido/slurry: silos → tanques → bombas → boquilla torre (alto)
    this.rutaLiquido = this.rutaCurva([
      [53.5, 26.5, 6], [50, 31, 4], [30, 33, 4], [11.5, 38, 3.5], [11.5, 43, 2],
      [16, 41, 1], [18, 42, 6], [22, 44, 19], [26, 44, 18],
    ]);
    // (b) ÁMBAR — gránulo/polvo: cono torre → enfriador → post-adición → tolvas → distribuidor (Nave B)
    this.rutaPolvo = this.rutaCurva([
      [26, 44, 2], [31, 42, 1.2], [36, 40, 1.2], [36, 45.2, 1.5], [43, 42.5, 5],
      [43, 47, 3], [25, 50, 3], [25, 58, 3], [25, 64.2, 2.5],
    ]);
    // (c) VERDE — cajas/sacos: envasado → checkweigher → bandas → paletizador → bahías
    this.rutaCajas = this.rutaCurva([
      [15, 68, 1], [20.3, 70.2, 1], [25, 71, 1], [31, 71.5, 1], [33, 78, 0.8], [29, 86, 1.2],
    ]);

    const crear = (n, geom, color, ruta) => {
      const grupo = [];
      const mat = new THREE.MeshLambertMaterial({ color });
      for (let i = 0; i < n; i++) {
        const m = new THREE.Mesh(geom, mat);
        m.userData.t = i / n;
        m.userData.ruta = ruta;
        this.escena.add(m);
        grupo.push(m);
      }
      return grupo;
    };
    this.pLiquido = crear(14, new THREE.SphereGeometry(0.45, 10, 10), 0x2196f3, this.rutaLiquido);
    this.pPolvo = crear(14, new THREE.SphereGeometry(0.45, 10, 10), 0xffb300, this.rutaPolvo);
    this.pCajas = crear(8, new THREE.BoxGeometry(0.9, 0.7, 0.9), 0x2e7d32, this.rutaCajas);
  },

  animar() {
    requestAnimationFrame(() => this.animar());
    const visible = document.getElementById('vista3d').classList.contains('activa');
    if (!visible) return;

    // velocidad de partículas proporcional al throughput de la simulación
    const base = 0.0016;
    const vLiq = base * (Sim.alimentacionKgH / 1125);
    const vPol = base * (Sim.torreOutKgH / 1125);
    const vCaj = base * (Sim.envasadoKgH / 1125);
    const avanzar = (grupo, v, activo) => {
      grupo.forEach((m) => {
        m.visible = activo;
        if (!activo) return;
        m.userData.t = (m.userData.t + v) % 1;
        m.position.copy(m.userData.ruta.getPointAt(m.userData.t));
      });
    };
    avanzar(this.pLiquido, vLiq, Sim.alimentacionKgH > 10);
    avanzar(this.pPolvo, vPol, Sim.torreOutKgH > 10);
    avanzar(this.pCajas, Math.max(vCaj, 0.0004), Sim.envasadoKgH > 10);

    // alerta de torre: pulso rojo (sinergia con la simulación)
    if (Sim.alertas.torre || (Sim.alertas.tolvas && Sim.alertas.tolvas.nivel === 'roja')) {
      const k = (Math.sin(Date.now() / 180) + 1) / 2;
      this.matTorre.color.setRGB(0.9, 0.9 - k * 0.65, 0.9 - k * 0.65);
    } else {
      this.matTorre.color.setHex(0xe8e8ee);
    }

    // estación de cuarentena: pulso cuando hay lote retenido (QC-4)
    const mCuar = this.mallasEquipo.cuarentena;
    if (mCuar) {
      if (Sim.qcStats.cuarentena > 0) {
        const k = (Math.sin(Date.now() / 160) + 1) / 2;
        mCuar.material.color.setRGB(0.85 + k * 0.15, 0.18, 0.18);
      } else {
        mCuar.material.color.setHex(0xc94f4f);
      }
    }

    this.renderer.render(this.escena, this.camara);
  },
};
