// i.1 · Una falla de punta a punta: escenas con personas para los pasos 1–6.
// Reutiliza person() y los materiales de tour-layers.js, la oficina con el monitor CMMS de la Parada 2,
// el candado y la tarjeta del tablero de la Parada 1, la cámara termográfica de la 5.2 y las válvulas de las bombas.
// El compendio no dice el método de reparación: solo se retira el aislamiento dañado y se coloca uno nuevo (sin llamas).
import * as THREE from 'three';
import { person, P, box, cyl } from 'app/tour-layers.js';

const V = (x, y, z) => new THREE.Vector3(x, y, z);
const mat = (name, color, o = {}) => new THREE.MeshStandardMaterial({ name, color, roughness: o.r ?? 0.7, metalness: o.m ?? 0.05 });
const ramp = (a, b, x) => Math.min(1, Math.max(0, (x - a) / (b - a)));
const Y1 = 3.6 + 0.25; // piso del primer alto (oficina de la Parada 2)

// Brazo hacia una mano en coordenadas locales de la persona (adelante = +x)
function reach(p, side, hx, hy, hz) {
  const arm = p.children.filter(o => /_brazo$/.test(o.name))[side], glove = p.children.filter(o => /_guante$/.test(o.name))[side];
  const sz = side ? 0.29 : -0.29, sh = V(0.02, 1.38, sz), hand = V(hx, hy, hz ?? sz * 0.75), d = hand.clone().sub(sh), len = d.length();
  arm.position.copy(sh).add(hand).multiplyScalar(0.5); arm.scale.y = len / 0.56;
  arm.quaternion.setFromUnitVectors(V(0, 1, 0), d.normalize());
  glove.position.copy(hand); return glove;
}
// Persona sentada: muslos horizontales y piernas hacia abajo; la silla la pone la escena
function sit(p) {
  p.children.filter(o => /_pierna$/.test(o.name)).forEach(l => {
    const z = l.position.z; l.position.set(0.2, 0.82, z); l.rotation.z = Math.PI / 2; l.scale.y = 0.42 / 0.82;
    box(p, p.name + '_pantorrilla', 0.15, 0.45, 0.16, P.pants, 0.41, 0.595, z);
  });
  return p;
}
function worker(name, o = {}) {
  const p = person(name, o); p.userData.person = true;
  if (o.suit) p.traverse(c => { if (c.material === P.vest) c.material = o.suit; if (c.material === P.glove && o.gloves) c.material = o.gloves; });
  return p;
}

export function buildFalla({ m, halos, haloMat, irCam }) {
  const g = new THREE.Group(); g.name = 'falla_punta_a_punta';
  const U = m.thermalPts.map(p => p.clone()); // uniones con deterioro (x = −10.5, a lo largo de z)
  const steps = [[], [], [], [], [], []], A = {};
  const at = (k, ...objs) => objs.forEach(o => k.forEach(i => steps[i].push(o)));

  // Paso 1 y 5 · inspector con la cámara termográfica (la cámara es la de la 5.2)
  const insp = worker('inspector_termografia'); g.add(insp); at([0, 4], insp);
  const hR = reach(insp, 1, 0.42, 1.3, 0.12); reach(insp, 0, 0.36, 1.22, -0.05); hR.visible = true;

  // Pasos 2 y 6 · oficina del primer alto con el monitor CMMS (como en la Parada 2)
  const office = new THREE.Group(); office.name = 'oficina_cmms'; g.add(office); at([1, 5], office);
  box(office, 'escritorio', 1.4, 0.06, 0.7, P.desk, -18.2, Y1 + 0.75, 2.1);
  [[-0.62, -0.28], [0.62, -0.28], [-0.62, 0.28], [0.62, 0.28]].forEach(([dx, dz], i) => box(office, 'escritorio_pata_' + i, 0.05, 0.72, 0.05, P.dark, -18.2 + dx, Y1 + 0.36, 2.1 + dz));
  box(office, 'monitor_CMMS', 0.62, 0.38, 0.04, P.dark, -18.2, Y1 + 1.03, 1.86);
  box(office, 'monitor_pie', 0.06, 0.2, 0.06, P.dark, -18.2, Y1 + 0.85, 1.84);
  box(office, 'teclado', 0.42, 0.02, 0.14, P.dark, -18.2, Y1 + 0.79, 2.3);
  box(office, 'silla_asiento', 0.46, 0.06, 0.46, P.dark, -18.2, Y1 + 0.45, 2.92);
  box(office, 'silla_respaldo', 0.46, 0.5, 0.05, P.dark, -18.2, Y1 + 0.75, 3.16);
  cyl(office, 'silla_base', 0.03, 0.42, P.steel, -18.2, Y1 + 0.21, 2.92);
  const cv = document.createElement('canvas'); cv.width = 512; cv.height = 316; const cx = cv.getContext('2d');
  const tex = new THREE.CanvasTexture(cv); tex.colorSpace = THREE.SRGBColorSpace;
  const scr = new THREE.Mesh(new THREE.PlaneGeometry(0.58, 0.35), new THREE.MeshBasicMaterial({ map: tex })); scr.name = 'pantalla_CMMS'; scr.position.set(-18.2, Y1 + 1.03, 1.882); office.add(scr);
  let screenState = '';
  function drawCMMS(closed) {
    const key = closed ? 'c' : 'a'; if (screenState === key) return; screenState = key;
    cx.fillStyle = '#0F1A22'; cx.fillRect(0, 0, 512, 316);
    cx.fillStyle = '#7FB4D6'; cx.font = '600 24px "IBM Plex Mono", monospace'; cx.fillText('CMMS · Orden de trabajo', 20, 40);
    cx.font = '500 19px "IBM Plex Mono", monospace';
    [['Código', '—'], ['Síntoma', 'deterioro en uniones'], ['', 'de la tubería de agua fría'], ['Prioridad', 'según el planificador'], ['Ventana', 'coordinada con usuarios']]
      .forEach(([k, v], i) => { cx.fillStyle = '#8B949B'; cx.fillText(k, 20, 88 + i * 34); cx.fillStyle = '#E6EBEF'; cx.fillText(v, 150, 88 + i * 34); });
    cx.fillStyle = closed ? '#4FAE5B' : '#F2C14E'; cx.fillRect(20, 262, 200, 38);
    cx.fillStyle = '#0F1A22'; cx.font = '600 20px "IBM Plex Sans", sans-serif'; cx.fillText(closed ? 'Estado: Cerrada' : 'Estado: Abierta', 34, 288);
    tex.needsUpdate = true;
  }
  document.fonts && document.fonts.ready.then(() => { screenState = ''; });
  const planner = sit(worker('planificador_CMMS')); planner.position.set(-18.2, Y1 - 0.37, 2.86); planner.rotation.y = Math.PI / 2; office.add(planner);
  const typing = [reach(planner, 0, 0.5, 0.97, -0.12), reach(planner, 1, 0.5, 0.97, 0.12)];
  A.cmms = V(-18.2, Y1 + 1.25, 1.86);

  // Paso 3 · LOTO: técnico eléctrico en el tablero (overol oscuro, guantes dieléctricos) y técnico mecánico en la válvula
  const overol = mat('overol_ignifugo', 0x27313C, { r: 0.85 }), dielec = mat('guantes_dielectricos', 0xB0282A, { r: 0.7 });
  const elec = worker('tecnico_electrico_LOTO', { suit: overol, gloves: dielec }); elec.position.set(-13.62, 0, -10.4); elec.rotation.y = Math.PI; g.add(elec); at([2], elec);
  const elecHand = reach(elec, 1, 0.5, 0.66, 0.1); reach(elec, 0, 0.12, 0.95, -0.3);
  const lock = new THREE.Group(); lock.name = 'candado_y_tarjeta'; lock.position.set(-14.24, 0.56, -10.28); g.add(lock); at([2, 3, 4], lock);
  box(lock, 'candado_cuerpo', 0.09, 0.1, 0.08, P.red, 0, 0, 0);
  const shk = new THREE.Mesh(new THREE.TorusGeometry(0.035, 0.01, 6, 14, Math.PI), P.steel); shk.position.set(0, 0.05, 0); shk.rotation.y = Math.PI / 2; lock.add(shk);
  box(lock, 'tarjeta_bloqueo', 0.01, 0.17, 0.1, P.white, -0.01, -0.14, 0.12);
  box(lock, 'tarjeta_bloqueo_franja', 0.012, 0.04, 0.1, P.red, -0.01, -0.07, 0.12);
  const wheel = m.root.getObjectByName('bomba_operacion_valvula_corte_succion_volante'), wheel0 = wheel.rotation.z;
  const mech = worker('tecnico_mecanico_valvula'); mech.position.set(-16.1, 0, -8.12); mech.rotation.y = -Math.PI / 2; g.add(mech); at([2], mech);
  reach(mech, 0, 0.5, 1.3, -0.1); reach(mech, 1, 0.5, 1.3, 0.1);
  const drips = new THREE.InstancedMesh(new THREE.SphereGeometry(0.025, 6, 4), new THREE.MeshBasicMaterial({ color: 0x8FC3F0 }), 10);
  drips.name = 'purga_de_presion'; drips.frustumCulled = false; g.add(drips); at([2], drips);
  cyl(g, 'llave_de_purga', 0.025, 0.2, P.steel, -15.75, 0.75, -7.5); at([2], g.children[g.children.length - 1]);
  A.lock = V(-14.24, 0.6, -10.28); A.valve = V(-16.1, 1.35, -7.5);

  // Paso 4 · reparación en las dos uniones: se retira el aislamiento dañado y se coloca uno nuevo
  const repA = worker('tecnico_reparacion_a', { suit: overol }); repA.position.set(-11.25, 0, U[0].z - 0.1); g.add(repA);
  const repB = worker('tecnico_reparacion_b'); repB.position.set(-11.25, 0, U[1].z + 0.15); g.add(repB); at([3], repA, repB);
  [repA, repB].forEach(p => { reach(p, 0, 0.62, 0.95, -0.12); reach(p, 1, 0.62, 0.95, 0.12); });
  const oldM = mat('aislamiento_danado', 0x6B5A44, { r: 0.95 }), newM = mat('aislamiento_nuevo', 0xE9E6DD, { r: 0.85 });
  const ins = U.map((u, i) => {
    const old = [-1, 1].map(s => { const c = new THREE.Mesh(new THREE.CylinderGeometry(0.22, 0.2, 0.32, 14), oldM); c.name = `aislamiento_danado_${i}`; c.rotation.x = Math.PI / 2; c.position.set(u.x, u.y, u.z + s * 0.36); c.userData.p0 = c.position.clone(); g.add(c); return c; });
    const fresh = new THREE.Mesh(new THREE.CylinderGeometry(0.24, 0.24, 1.0, 16), newM); fresh.name = `aislamiento_nuevo_${i}`; fresh.rotation.x = Math.PI / 2; fresh.position.copy(u); g.add(fresh);
    return { old, fresh };
  });
  const sparks = m.root.getObjectByName('punto_termico_0') ? [0, 1].map(i => m.root.getObjectByName('punto_termico_' + i)) : [];
  A.repair = U[0].clone().setY(1.2);

  const persons = [insp, planner, elec, mech, repA, repB];
  let k = 0;
  function setStep(n) { k = n; g.children.forEach(o => { o.visible = !steps.some(s => s.includes(o)) || steps[k].includes(o); }); }
  // repaired: 0 = con deterioro, 1 = reparado; f = avance del paso 4
  function tick(t, ts) {
    // ts: segundos desde que empezó el paso
    const repaired = k > 3 ? 1 : k === 3 ? ramp(4.2, 4.8, ts) : 0;
    ins.forEach(({ old, fresh }) => {
      const out = k > 3 ? 1 : k === 3 ? ramp(1.0, 2.4, ts) : 0, put = k > 3 ? 1 : k === 3 ? ramp(2.6, 4.2, ts) : 0;
      old.forEach(c => { c.visible = out < 1; c.position.copy(c.userData.p0).add(V(-0.7 * out, -0.75 * out, 0)); });
      fresh.visible = put > 0; fresh.scale.set(1, Math.max(0.001, put), 1);
    });
    haloMat.opacity = 1 - repaired; halos.forEach(h => { h.visible = repaired < 1; });
    sparks.forEach(s => { if (s) s.visible = repaired < 1; });
    if (k === 0 || k === 4) { // el inspector sostiene la cámara termográfica
      const c = irCam.group.position, d = irCam.group.getWorldDirection(V()).setY(0).normalize();
      insp.position.set(c.x - d.x * 0.45, 0, c.z - d.z * 0.45); insp.rotation.y = Math.atan2(-d.z, d.x);
    }
    if (k === 1 || k === 5) { drawCMMS(k === 5); typing.forEach((h, i) => { h.position.y = 0.97 + (k === 1 ? 0.015 * Math.max(0, Math.sin(t * 16 + i * 2.1)) : 0); }); }
    // candado: aparece en el paso 3, sigue en el 4 y se retira al empezar el 5
    const ls = k === 2 ? ramp(1.2, 2.2, ts) : k === 3 ? 1 : k === 4 ? 1 - ramp(0.3, 1.3, ts) : 0;
    lock.scale.setScalar(Math.max(0.001, ls));
    elecHand.position.x = 0.5 + 0.06 * Math.sin(Math.min(ts, 2.2) * 3);
    wheel.rotation.z = k === 2 ? wheel0 + Math.min(ts, 4) * 2.2 : wheel0;
    if (k === 2) {
      const tmp = new THREE.Object3D(), on = ts > 3.2;
      for (let i = 0; i < 10; i++) { const f = (t * 0.9 + i / 10) % 1; tmp.position.set(-15.75, 0.64 - f * 0.55, -7.5); tmp.scale.setScalar(on ? 1 : 0.001); tmp.updateMatrix(); drips.setMatrixAt(i, tmp.matrix); }
      drips.instanceMatrix.needsUpdate = true;
    }
    return repaired;
  }
  function reset() { haloMat.opacity = 1; wheel.rotation.z = wheel0; sparks.forEach(s => { if (s) s.visible = true; }); }
  setStep(0); tick(0, 0);
  return { group: g, setStep, tick, reset, A, persons, steps };
}
