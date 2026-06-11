/* ============================================================
   Motor de Simulación de Producción — estado GLOBAL compartido
   Calendario exacto de la Asignación #4 (21 turnos, setups 1 h,
   miércoles de mantenimiento con torre 24/7).
   ============================================================ */

const Sim = {
  // ----- Parámetros por defecto (estado "planta eficiente") -----
  DEFAULTS: {
    alimentacionKgH: 1125,   // capacidad real 75 %
    velEnvasadoPct: 100,
    tolvaPct0: 40,
    velocidad: 60,           // 1 s real = 1 min simulado
  },

  corriendo: false,
  velocidad: 60,
  tMin: 0,                   // minutos simulados desde Lunes 06:00
  alimentacionKgH: 1125,
  velEnvasadoPct: 100,
  tolvaKg: 6000,
  kgDia: 0,
  kgSemanaTotal: 0,
  horasTranscurridas: 0,
  ultimoFormato: '50kg',     // formato que queda montado tras el sábado
  log: [],

  // valores instantáneos calculados
  torreOutKgH: 0,
  envasadoKgH: 0,
  envasadoUdsH: 0,
  formatoActivo: null,
  moduloActivo: null,        // 'A' | 'B' | null
  actividadTexto: '',
  enSetup: false,
  enMantenimiento: false,
  alertas: {},               // id → {nivel:'roja'|'amarilla'|'info', texto}
  _alertasPrevias: {},
  _timer: null,

  // ---------------- Tiempo y calendario ----------------
  infoTiempo() {
    const diaIdx = Math.floor(this.tMin / 1440) % 7;
    const minDia = ((this.tMin % 1440) + 1440) % 1440;        // min desde 06:00
    const turnoIdx = Math.floor(minDia / 480);                // 0..2
    const minTurno = minDia % 480;
    const minReloj = (6 * 60 + minDia) % 1440;
    const hh = String(Math.floor(minReloj / 60)).padStart(2, '0');
    const mm = String(Math.floor(minReloj % 60)).padStart(2, '0');
    return {
      diaIdx, turnoIdx, minTurno,
      dia: PLANT_DATA.calendario[diaIdx].dia,
      turno: 'T' + (turnoIdx + 1),
      hora: `${hh}:${mm}`,
      turnoDef: PLANT_DATA.calendario[diaIdx].turnos[turnoIdx],
    };
  },

  // Actividad efectiva del turno actual (resuelve setups de 1 h)
  actividadActual() {
    const t = this.infoTiempo();
    const def = t.turnoDef;
    if (def.act === 'mant') {
      return { modo: 'mant', texto: 'MANTENIMIENTO — torre operando 24/7, tolvas acumulando', formato: null };
    }
    if (def.act === 'libre') {
      // Domingo: gestión de buffer — envasa el último formato si las tolvas superan el 30 %
      if (this.tolvaKg > 0.30 * PLANT_DATA.tolvasCapacidadKg) {
        const f = PLANT_DATA.formatos[this.ultimoFormato];
        return { modo: 'pack', texto: `Libre/buffer — drenando tolvas con ${f.nombre} (Módulo ${f.modulo})`, formato: this.ultimoFormato };
      }
      return { modo: 'libre', texto: 'Libre / buffer — línea de envasado en espera, torre operando', formato: null };
    }
    if (def.act === 'setup') {
      if (t.minTurno < 60) {
        return { modo: 'setup', texto: `SETUP ${PLANT_DATA.formatos[def.de].nombre} → ${PLANT_DATA.formatos[def.a].nombre} (1 h de cambio de formato)`, formato: null, setupA: def.a };
      }
      const f = PLANT_DATA.formatos[def.a];
      return { modo: 'pack', texto: `Envasando ${f.nombre} — Módulo ${f.modulo} ${f.modulo === 'A' ? '(VFFS ROVEMA)' : '(Ensacadora H&B)'}`, formato: def.a };
    }
    const f = PLANT_DATA.formatos[def.formato];
    return { modo: 'pack', texto: `Envasando ${f.nombre} — Módulo ${f.modulo} ${f.modulo === 'A' ? '(VFFS ROVEMA)' : '(Ensacadora H&B)'}`, formato: def.formato };
  },

  // ---------------- Dinámica por paso ----------------
  paso(dtMin) {
    const tPrev = this.infoTiempo();
    this.tMin += dtMin;
    const t = this.infoTiempo();
    if (t.dia !== tPrev.dia) this.kgDia = 0;
    if (t.turno !== tPrev.turno || t.dia !== tPrev.dia) {
      this.registrar(`Cambio de turno → ${t.dia} ${t.turno}`, 'turno');
    }

    const act = this.actividadActual();
    this.actividadTexto = act.texto;
    this.enSetup = act.modo === 'setup';
    this.enMantenimiento = act.modo === 'mant';
    this.formatoActivo = act.formato;
    if (act.formato) this.ultimoFormato = act.formato;
    this.moduloActivo = act.formato ? PLANT_DATA.formatos[act.formato].modulo : null;

    const dtH = dtMin / 60;
    const cap = PLANT_DATA.tolvasCapacidadKg;

    // Torre: nunca se detiene; limitada a 1,500 kg/h (cuello de botella)
    let torreOut = Math.min(this.alimentacionKgH, PLANT_DATA.torreMaxKgH);

    // Capacidad de envasado del módulo activo
    let packCap = 0;
    if (act.formato) {
      const f = PLANT_DATA.formatos[act.formato];
      packCap = f.udsH * f.kgUd * (this.velEnvasadoPct / 100);
    }

    // Balance de tolvas: entra torre, sale envasado (limitado por material disponible)
    const disponible = this.tolvaKg + torreOut * dtH;
    const packOut = Math.min(packCap * dtH, disponible) / dtH || 0;

    // Tolvas llenas → la torre debe reducir carga (sobreproducción)
    let nuevaTolva = this.tolvaKg + (torreOut - packOut) * dtH;
    if (nuevaTolva > cap) {
      const exceso = (nuevaTolva - cap) / dtH;
      torreOut = Math.max(0, torreOut - exceso);
      nuevaTolva = cap;
    }
    this.tolvaKg = Math.max(0, nuevaTolva);
    this.torreOutKgH = torreOut;
    this.envasadoKgH = packOut;
    this.envasadoUdsH = act.formato ? packOut / PLANT_DATA.formatos[act.formato].kgUd : 0;
    this.kgDia += packOut * dtH;
    this.kgSemanaTotal += torreOut * dtH;
    this.horasTranscurridas += dtH;

    this.evaluarAlertas(act, packCap, torreOut);
  },

  evaluarAlertas(act, packCap, torreOut) {
    const cap = PLANT_DATA.tolvasCapacidadKg;
    const pct = (this.tolvaKg / cap) * 100;
    const a = {};

    if (this.alimentacionKgH > PLANT_DATA.torreMaxKgH) {
      a.torre = { nivel: 'roja', texto: `⛔ LIMITANTE DE PRODUCCIÓN: la torre GEA NIRO® es el cuello de botella (máx 1,500 kg/h). Se piden ${fmt(this.alimentacionKgH)} kg/h — el exceso de slurry se recircula (FCV-402).` };
    }
    if (pct >= 99.9) {
      a.tolvas = { nivel: 'roja', texto: '⛔ Tolvas llenas: SOBREPRODUCCIÓN — la torre debe reducir carga. Gestión activa del nivel de tolvas requerida (Asignación #4).' };
    } else if (pct >= 80) {
      a.tolvas = { nivel: 'amarilla', texto: `⚠️ Tolvas al ${pct.toFixed(0)} % — riesgo de SOBREPRODUCCIÓN (autonomía restante ${((cap - this.tolvaKg) / Math.max(torreOut, 1)).toFixed(1)} h al ritmo actual).` };
    }
    if (act.modo === 'pack' && packCap > torreOut * 1.02 && this.tolvaKg < 0.05 * cap) {
      const util = packCap > 0 ? (this.envasadoKgH / packCap) * 100 : 0;
      a.envasado = { nivel: 'info', texto: `ℹ️ Envasado sub-utilizado (cuello de botella aguas arriba): el módulo ${this.moduloActivo} opera al ${util.toFixed(0)} % de su capacidad (${fmt(packCap)} kg/h posibles vs ${fmt(torreOut)} kg/h de la torre).` };
    }
    if (this.enMantenimiento) {
      a.mant = { nivel: 'info', texto: 'ℹ️ Miércoles de MANTENIMIENTO: envasado detenido y MCC-B desenergizado. La torre GEA NIRO® sigue 24/7 — autonomía de tolvas 13.3 h a 1,125 kg/h.' };
    }

    // Registrar transiciones en el log
    for (const [id, al] of Object.entries(a)) {
      const prev = this._alertasPrevias[id];
      if (!prev || prev.nivel !== al.nivel) {
        this.registrar(al.texto, al.nivel === 'roja' ? 'rojo' : al.nivel === 'amarilla' ? 'amar' : 'info');
      }
    }
    this._alertasPrevias = a;
    this.alertas = a;
  },

  registrar(texto, clase) {
    const t = this.infoTiempo();
    this.log.unshift({ marca: `${t.dia} ${t.turno} ${t.hora}`, texto, clase });
    if (this.log.length > 400) this.log.pop();
    Bus.emit('log');
  },

  // ---------------- Control ----------------
  iniciar() {
    if (this.corriendo) return;
    this.corriendo = true;
    this.registrar('▶ Simulación iniciada', 'info');
    this._timer = setInterval(() => {
      const dtMin = (0.1 * this.velocidad) / 60; // 100 ms reales → minutos simulados
      // subdividir pasos grandes para no saltarse límites de turno/tolva
      const sub = Math.max(1, Math.ceil(dtMin / 2));
      for (let i = 0; i < sub; i++) this.paso(dtMin / sub);
      Bus.emit('tick');
    }, 100);
    Bus.emit('tick');
  },

  pausar() {
    this.corriendo = false;
    clearInterval(this._timer);
    Bus.emit('tick');
  },

  reset() {
    this.pausar();
    const D = this.DEFAULTS;
    this.tMin = 0;
    this.alimentacionKgH = D.alimentacionKgH;
    this.velEnvasadoPct = D.velEnvasadoPct;
    this.velocidad = D.velocidad;
    this.tolvaKg = (D.tolvaPct0 / 100) * PLANT_DATA.tolvasCapacidadKg;
    this.kgDia = 0; this.kgSemanaTotal = 0; this.horasTranscurridas = 0;
    this.ultimoFormato = '50kg';
    this.alertas = {}; this._alertasPrevias = {};
    this.log = [];
    this.paso(0.0001); // recalcular estado instantáneo sin avanzar tiempo
    this.alertas = {}; this._alertasPrevias = {}; // estado eficiente: sin alertas
    this.log = [{ marca: 'Lunes T1 06:00', texto: '🔄 RESET — estado "planta eficiente": 1,125 kg/h (capacidad real 75 %), tolvas al 40 %, Lunes T1 06:00, sin alertas.', clase: 'info' }];
    Bus.emit('tick');
    Bus.emit('log');
  },

  // OEE estimado: producción real vs capacidad de diseño en el tiempo transcurrido
  oee() {
    if (this.horasTranscurridas < 0.01) return 75;
    return Math.min(100, (this.kgSemanaTotal / (this.horasTranscurridas * PLANT_DATA.torreMaxKgH)) * 100);
  },

  // ---------------- Estado en vivo por equipo (para fichas) ----------------
  estadoEquipo(id) {
    const item = getItem(id);
    if (!item) return null;
    const chips = [];
    let texto = '';
    let alerta = false;
    const pctTolva = (this.tolvaKg / PLANT_DATA.tolvasCapacidadKg) * 100;

    const enMant = this.enMantenimiento;
    switch (id) {
      case 'torre':
        chips.push({ tipo: this.alertas.torre || this.alertas.tolvas ? 'err' : 'ok', texto: this.alertas.torre ? '⛔ CUELLO DE BOTELLA ACTIVO' : 'Operando 24/7' });
        chips.push({ tipo: 'info', texto: `${fmt(this.torreOutKgH)} kg/h` });
        texto = `Produciendo ${fmt(this.torreOutKgH)} kg/h (utilización ${((this.torreOutKgH / 1500) * 100).toFixed(0)} % de 1,500 kg/h máx). ` +
          (this.alertas.torre ? this.alertas.torre.texto : 'Dentro de capacidad.');
        alerta = !!(this.alertas.torre || this.alertas.tolvas);
        break;
      case 'tolvas':
        chips.push({ tipo: pctTolva >= 100 ? 'err' : pctTolva >= 80 ? 'warn' : 'ok', texto: `Nivel ${pctTolva.toFixed(0)} %` });
        chips.push({ tipo: 'info', texto: `${fmt(this.tolvaKg)} / 15,000 kg` });
        texto = this.alertas.tolvas ? this.alertas.tolvas.texto : `Acumulado ${fmt(this.tolvaKg)} kg. Autonomía de diseño 13.3 h a 1,125 kg/h.`;
        alerta = !!this.alertas.tolvas;
        break;
      case 'vffs': case 'ensacadora': {
        const esA = id === 'vffs';
        const activo = this.moduloActivo === (esA ? 'A' : 'B');
        chips.push({ tipo: activo ? 'ok' : enMant ? 'err' : 'info', texto: activo ? 'ACTIVO' : enMant ? 'MANTENIMIENTO' : 'En espera (regla: un solo módulo)' });
        if (activo) {
          chips.push({ tipo: 'info', texto: `${fmt(this.envasadoUdsH)} uds/h · ${fmt(this.envasadoKgH)} kg/h` });
          texto = `Envasando ${PLANT_DATA.formatos[this.formatoActivo].nombre} a ${fmt(this.envasadoUdsH)} uds/h.`;
        } else {
          texto = enMant ? 'MCC-B desenergizado durante mantenimiento del miércoles.' : 'Solo un módulo (A o B) opera a la vez — bifurcación del distribuidor de flujo.';
        }
        break;
      }
      case 'tk101': case 'tk102': case 'p101': case 'p102':
        chips.push({ tipo: 'ok', texto: 'Operando (la torre no para)' });
        chips.push({ tipo: 'info', texto: `${fmt(Math.min(this.alimentacionKgH, 2000))} kg/h slurry` });
        texto = `Alimentación de slurry configurada: ${fmt(this.alimentacionKgH)} kg/h hacia la torre.` + (id === 'p102' ? ' (P-102 en reserva caliente N+1).' : '');
        break;
      case 'enfriador': case 'postadicion':
        chips.push({ tipo: 'ok', texto: 'Operando' });
        chips.push({ tipo: 'info', texto: `${fmt(this.torreOutKgH)} kg/h` });
        texto = `Procesando ${fmt(this.torreOutKgH)} kg/h aguas abajo de la torre.`;
        break;
      case 'bc101': case 'bc102': case 'checkweigher': case 'paletizador': case 'distribuidor': {
        const activo = this.moduloActivo !== null;
        chips.push({ tipo: activo ? 'ok' : enMant ? 'err' : 'info', texto: activo ? `Activo — línea Módulo ${this.moduloActivo}` : enMant ? 'MANTENIMIENTO' : 'En espera' });
        texto = activo ? `Flujo actual: ${fmt(this.envasadoKgH)} kg/h (${fmt(this.envasadoUdsH)} uds/h).` : 'Sin flujo de producto envasado en este momento.';
        break;
      }
      case 'silos':
        chips.push({ tipo: 'ok', texto: 'Suministrando MP' });
        texto = `Dosificación continua de materias primas para ${fmt(this.alimentacionKgH)} kg/h de slurry.`;
        break;
      default:
        if (item.tipo === 'edificio') {
          if (id === 'naveB') {
            chips.push({ tipo: enMant ? 'err' : 'ok', texto: enMant ? 'MCC-B DESENERGIZADO (mantenimiento)' : 'MCC-B energizado' });
            texto = this.actividadTexto;
          } else if (id === 'naveA') {
            chips.push({ tipo: 'ok', texto: 'MCC-A energizado — torre 24/7' });
            texto = `Torre produciendo ${fmt(this.torreOutKgH)} kg/h.`;
          } else {
            chips.push({ tipo: 'info', texto: this.corriendo ? 'Simulación en curso' : 'Simulación pausada' });
            texto = this.actividadTexto || '—';
          }
        }
    }
    if (!chips.length) return null;
    return { chips, texto, alerta };
  },
};
