import * as THREE from 'three';

// Cielo, sol (posición astronómica real para 9.025° N, 79.530° O, UTC−5), clima y respuesta
// cualitativa ILUSTRATIVA del sistema. No usa datos de carga del Edificio 2.
const LAT = 9.0247, LON = -79.5299, RAD = Math.PI / 180;
export function sunPosition(month, day, hour) {
  const N = Math.floor(30.6 * month - 30.4) + day; // día del año aprox.
  const B = (360 / 365) * (N - 81) * RAD;
  const decl = 23.44 * Math.sin(B) * RAD;
  const eot = 9.87 * Math.sin(2 * B) - 7.53 * Math.cos(B) - 1.5 * Math.sin(B);
  const solar = hour + (4 * (LON - -75) + eot) / 60;
  const h = 15 * (solar - 12) * RAD, lat = LAT * RAD;
  const el = Math.asin(Math.sin(lat) * Math.sin(decl) + Math.cos(lat) * Math.cos(decl) * Math.cos(h));
  const az = Math.atan2(-Math.sin(h), Math.tan(decl) * Math.cos(lat) - Math.sin(lat) * Math.cos(h)); // desde el norte, horario
  return { el, az: (az + 2 * Math.PI) % (2 * Math.PI) };
}
// rumbo -> mundo. La fachada frontal (+z) mira hacia el rumbo `front`.
export function bearingToWorld(az, el, front) {
  const p = az + Math.PI - front * RAD;
  return new THREE.Vector3(Math.cos(el) * Math.sin(p), Math.sin(el), -Math.cos(el) * Math.cos(p));
}

const lerp = (a, b, t) => a + (b - a) * t, clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
const mix = (c1, c2, t) => new THREE.Color(c1).lerp(new THREE.Color(c2), clamp(t));
const WX = { soleado: { clear: 1, cloud: 3, rain: 0 }, nublado: { clear: 0.45, cloud: 11, rain: 0 }, lluvioso: { clear: 0.12, cloud: 16, rain: 1 } };

export function createSky({ scene, stage, m, lamps }) {
  const hemi = scene.children.find(o => o.isHemisphereLight), key = stage._key, amb = scene.children.find(o => o.isAmbientLight);
  const fill = scene.children.find(o => o.isDirectionalLight && o !== key);
  const base = { hemi: hemi.intensity, key: key.intensity, amb: amb?.intensity ?? 0, fill: fill?.intensity ?? 0, hc: hemi.color.clone(), hg: hemi.groundColor.clone() };
  const root = new THREE.Group(); root.name = 'cielo_clima'; scene.add(root);
  const S = { hour: 10, month: new Date().getMonth() + 1, wx: 'soleado', front: 45, active: true, factor: 1, sun: null, night: false };

  // Sol y luna
  const sunM = new THREE.MeshBasicMaterial({ color: 0xFFE6A8 }), sun = new THREE.Mesh(new THREE.SphereGeometry(2.6, 20, 14), sunM); root.add(sun);
  const glowC = document.createElement('canvas'); glowC.width = glowC.height = 128;
  const gx = glowC.getContext('2d'), gr = gx.createRadialGradient(64, 64, 0, 64, 64, 64);
  gr.addColorStop(0, 'rgba(255,240,200,.9)'); gr.addColorStop(0.3, 'rgba(255,200,120,.35)'); gr.addColorStop(1, 'rgba(255,180,90,0)');
  gx.fillStyle = gr; gx.fillRect(0, 0, 128, 128);
  const glowT = new THREE.CanvasTexture(glowC);
  const sunGlow = new THREE.Sprite(new THREE.SpriteMaterial({ map: glowT, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending })); sunGlow.scale.setScalar(22); root.add(sunGlow);
  const moon = new THREE.Mesh(new THREE.SphereGeometry(1.8, 20, 14), new THREE.MeshBasicMaterial({ color: 0xDCE6F2 })); root.add(moon);
  const moonGlow = new THREE.Sprite(new THREE.SpriteMaterial({ map: glowT, color: 0x9FB8E6, transparent: true, opacity: 0.5, depthWrite: false, blending: THREE.AdditiveBlending })); moonGlow.scale.setScalar(12); root.add(moonGlow);
  const starG = new THREE.BufferGeometry(), sp = [];
  for (let i = 0; i < 500; i++) { const a = Math.random() * Math.PI * 2, e = Math.asin(0.12 + Math.random() * 0.88); sp.push(Math.cos(e) * Math.cos(a) * 160, Math.sin(e) * 160, Math.cos(e) * Math.sin(a) * 160); }
  starG.setAttribute('position', new THREE.Float32BufferAttribute(sp, 3));
  const stars = new THREE.Points(starG, new THREE.PointsMaterial({ color: 0xE6EEF8, size: 0.9, sizeAttenuation: true, transparent: true, opacity: 0, depthWrite: false })); root.add(stars);

  // Radiación sobre las caras del edificio: tinte proporcional a cos(ángulo de incidencia)
  const hT = 10.8, faces = [];
  const radM = () => new THREE.MeshBasicMaterial({ color: 0xFF8A3D, transparent: true, opacity: 0, depthWrite: false, blending: THREE.AdditiveBlending, side: THREE.DoubleSide });
  function face(w, h, x, y, z, n) {
    const mt = radM(), o = new THREE.Mesh(new THREE.PlaneGeometry(w, h), mt);
    o.position.set(x, y, z); o.lookAt(o.position.clone().add(n)); o.name = 'radiacion_cara'; root.add(o);
    faces.push({ o, n: n.clone().normalize(), mt, w, h });
  }
  const V = (x, y, z) => new THREE.Vector3(x, y, z);
  face(46.4, hT, 0, hT / 2, 5.25, V(0, 0, 1)); face(46.4, hT, 0, hT / 2, -5.25, V(0, 0, -1));
  face(10.4, hT, -23.25, hT / 2, 0, V(-1, 0, 0)); face(10.4, hT, 23.25, hT / 2, 0, V(1, 0, 0));
  face(46.4, 10.4, 0, hT + 1.6, 0, V(0, 1, 0));
  face(9.2, 15.5, 0, 7.75, -10.9, V(0, 0, 1)); face(9.2, 15.5, 0, 7.75, -17.1, V(0, 0, -1));
  face(6.2, 15.5, -4.6, 7.75, -14, V(-1, 0, 0)); face(6.2, 15.5, 4.6, 7.75, -14, V(1, 0, 0)); face(9.2, 6.2, 0, 15.85, -14, V(0, 1, 0));

  // Rayos solares (segmentos que viajan del sol a puntos de las caras iluminadas)
  const RN = 70, rayM = new THREE.MeshBasicMaterial({ color: 0xFFD27A, transparent: true, opacity: 0.85, depthWrite: false, blending: THREE.AdditiveBlending });
  const rays = new THREE.InstancedMesh(new THREE.CylinderGeometry(0.05, 0.05, 3.2, 5), rayM, RN); rays.name = 'rayos_solares'; rays.frustumCulled = false; root.add(rays);
  const rayS = Array.from({ length: RN }, (_, i) => ({ ph: i / RN, u: Math.random(), v: Math.random(), f: Math.floor(Math.random() * 100) }));

  // Calor nocturno liberado por la envolvente (ilustrativo)
  const HN = 90, heatM = new THREE.MeshBasicMaterial({ color: 0xFF7A4A, transparent: true, opacity: 0.45, depthWrite: false, blending: THREE.AdditiveBlending });
  const heat = new THREE.InstancedMesh(new THREE.IcosahedronGeometry(1, 0), heatM, HN); heat.name = 'calor_nocturno'; heat.frustumCulled = false; root.add(heat);
  const heatS = Array.from({ length: HN }, () => ({ ph: Math.random(), x: (Math.random() - 0.5) * 44, z: (Math.random() - 0.5) * 9 }));

  // Nubes y lluvia
  const cloudM = new THREE.MeshStandardMaterial({ color: 0xF2F4F6, roughness: 1, transparent: true, opacity: 0.92, depthWrite: false });
  const clouds = [];
  for (let i = 0; i < 16; i++) {
    const g = new THREE.Group(); g.name = 'nube_' + i;
    for (let k = 0; k < 4; k++) { const c = new THREE.Mesh(new THREE.IcosahedronGeometry(1, 1), cloudM); c.scale.set(3 + Math.random() * 2.5, 1.6 + Math.random(), 2.6 + Math.random() * 1.6); c.position.set(k * 3.2 - 5, Math.random() * 0.8, (Math.random() - 0.5) * 2); g.add(c); }
    g.position.set((Math.random() - 0.5) * 140, 30 + Math.random() * 10, -50 + Math.random() * 90); g.userData.sp = 0.6 + Math.random() * 0.8;
    root.add(g); clouds.push(g);
  }
  const RNN = 900, rainM = new THREE.MeshBasicMaterial({ color: 0xB8D4EC, transparent: true, opacity: 0.55, depthWrite: false });
  const rain = new THREE.InstancedMesh(new THREE.BoxGeometry(0.03, 0.9, 0.03), rainM, RNN); rain.name = 'lluvia'; rain.frustumCulled = false; root.add(rain);
  const rainS = Array.from({ length: RNN }, () => [(Math.random() - 0.5) * 90, Math.random() * 34, (Math.random() - 0.5) * 80, 14 + Math.random() * 6]);
  let flash = 0, nextFlash = 4;

  const ventanas = m.shell.mats.find(s => s.mat.name === 'ventanas')?.mat;
  const tmp = new THREE.Object3D(), up = V(0, 1, 0);
  const stageEl = stage;

  function compute() {
    const { el, az } = sunPosition(S.month, 15, S.hour);
    const sd = bearingToWorld(az, el, S.front).normalize();
    const mp = sunPosition(S.month, 15, (S.hour + 12) % 24), md = bearingToWorld(mp.az, mp.el, S.front).normalize();
    const w = WX[S.wx], day = clamp(Math.sin(el) * 4 + 0.15), twi = clamp(1 - Math.abs(Math.sin(el)) * 5) * (el > -0.12 ? 1 : 0);
    const irr = Math.max(0, Math.sin(el)) * w.clear; // índice relativo 0–1 (no W/m²)
    // Sin fuente para una respuesta del sistema al clima o a la hora: la animación no cambia de ritmo (FUENTES_COMPENDIO, «Lo que el compendio NO reporta»)
    S.factor = 1;
    S.night = el < -0.05; S.el = el; S.az = az; S.irr = irr; S.sd = sd; S.md = md; S.day = day; S.twi = twi; S.w = w;
  }
  function applyLights() {
    const { sd, md, day, twi, w, night } = S;
    key.position.copy(night ? md : sd).multiplyScalar(70);
    const warm = mix(0xFFFFFF, 0xFFB070, twi);
    key.color.copy(night ? new THREE.Color(0xA8BEE8) : warm);
    key.intensity = night ? 0.35 : base.key * (0.25 + 0.75 * day) * (0.35 + 0.65 * w.clear) + flash * 3;
    key.castShadow = !night && w.clear > 0.3;
    hemi.intensity = lerp(0.25, base.hemi, day) * (w.clear < 0.5 ? 0.85 : 1) + flash * 1.5;
    hemi.color.copy(night ? new THREE.Color(0x5A6E94) : mix(0xFFFFFF, 0xC9D2DC, 1 - w.clear));
    if (amb) amb.intensity = lerp(0.35, base.amb, day);
    if (fill) fill.intensity = lerp(0.15, base.fill, day);
    stage._ground.material.opacity = night ? 0.15 : 0.35 * w.clear + 0.05;
    // fondo del cielo
    const top = night ? '#070B14' : S.wx === 'soleado' ? mix(0x1B3550, 0x3F79B0, day).getStyle() : mix(0x22282F, 0x5C6873, day).getStyle();
    const hor = night ? '#141C2B' : twi > 0.2 ? mix(0x6F8FB3, 0xE89A5C, twi * (S.wx === 'soleado' ? 1 : 0.4)).getStyle() : S.wx === 'soleado' ? '#9DC2E2' : mix(0x3A424A, 0x9AA3AB, day).getStyle();
    stageEl.style.setProperty('--stage-bg', `linear-gradient(180deg, ${top} 0%, ${hor} 62%, #1C1F22 100%)`);
    sun.visible = sunGlow.visible = S.el > -0.06;
    sun.position.copy(sd).multiplyScalar(120); sunGlow.position.copy(sun.position);
    sunM.color.copy(mix(0xFFF2CC, 0xFF9A50, twi)); sunGlow.material.opacity = 0.35 + 0.65 * w.clear;
    moon.visible = moonGlow.visible = night; moon.position.copy(md).multiplyScalar(110); moonGlow.position.copy(moon.position);
    stars.material.opacity = night ? (S.wx === 'soleado' ? 0.9 : 0.25) : 0;
    faces.forEach(f => { const c = Math.max(0, f.n.dot(sd)); f.mt.opacity = night ? 0 : 0.42 * c * S.irr; });
    if (ventanas) { ventanas.emissive.set(0xFFC874); ventanas.emissiveIntensity = night ? 0.55 : 0; }
    if (lamps) lamps.lampM.emissiveIntensity = night ? 2.2 : 0;
    clouds.forEach((c, i) => { c.visible = i < w.cloud; });
    cloudM.color.copy(night ? new THREE.Color(0x3A4456) : mix(0xF2F4F6, 0x8E979F, 1 - w.clear));
    rain.visible = !!w.rain;
  }
  compute();

  function update(dt, t) {
    if (!S.active) return;
    dt = Math.max(0, Math.min(0.1, dt));
    if (S.wx === 'lluvioso') { nextFlash -= dt; if (nextFlash < 0) { flash = 1; nextFlash = 5 + Math.random() * 7; } }
    flash = Math.min(1, Math.max(0, flash - dt * 4));
    applyLights();
    // rayos
    const lit = faces.map((f, i) => [i, f.n.dot(S.sd)]).filter(([, c]) => c > 0.08);
    const showRays = !S.night && S.irr > 0.05 && lit.length;
    rays.visible = !!showRays;
    if (showRays) {
      const n = Math.round(RN * clamp(S.irr * 1.2));
      rayM.opacity = 0.35 + 0.5 * S.irr;
      rayS.forEach((r, i) => {
        if (i >= n) { tmp.scale.setScalar(0); tmp.updateMatrix(); rays.setMatrixAt(i, tmp.matrix); return; }
        const f = faces[lit[r.f % lit.length][0]], o = f.o;
        const hit = new THREE.Vector3((r.u - 0.5) * f.w * 0.9, (r.v - 0.5) * f.h * 0.9, 0.05).applyMatrix4(o.matrixWorld);
        const k = (r.ph + t * 0.45) % 1, d = (1 - k) * 34;
        tmp.position.copy(hit).addScaledVector(S.sd, d + 1.6);
        tmp.quaternion.setFromUnitVectors(up, S.sd); tmp.scale.set(1, k > 0.92 ? (1 - k) / 0.08 : 1, 1);
        tmp.updateMatrix(); rays.setMatrixAt(i, tmp.matrix);
      });
      rays.instanceMatrix.needsUpdate = true;
    }
    // calor nocturno: la envolvente libera el calor acumulado del día
    heat.visible = S.night;
    if (heat.visible) {
      heatS.forEach((h, i) => {
        const k = (h.ph + t * 0.12) % 1;
        tmp.position.set(h.x + Math.sin(t + i) * 0.4, hT + 1 + k * 9, h.z); tmp.scale.setScalar(0.12 + 0.28 * (1 - k)); tmp.quaternion.identity();
        tmp.updateMatrix(); heat.setMatrixAt(i, tmp.matrix);
      });
      heatM.opacity = 0.5; heat.instanceMatrix.needsUpdate = true;
    }
    clouds.forEach(c => { if (c.visible) { c.position.x += c.userData.sp * dt; if (c.position.x > 75) c.position.x = -75; } });
    if (rain.visible) {
      rainS.forEach((r, i) => { r[1] -= r[3] * dt; if (r[1] < 0) r[1] = 34; tmp.position.set(r[0], r[1], r[2]); tmp.scale.setScalar(1); tmp.quaternion.identity(); tmp.updateMatrix(); rain.setMatrixAt(i, tmp.matrix); });
      rain.instanceMatrix.needsUpdate = true;
    }
  }
  function setActive(on) {
    S.active = on; root.visible = on;
    if (!on) {
      key.position.set(4, 7, 5).multiplyScalar(8); key.color.set(0xffffff); key.intensity = base.key; key.castShadow = true;
      hemi.intensity = base.hemi; hemi.color.copy(base.hc); if (amb) amb.intensity = base.amb; if (fill) fill.intensity = base.fill;
      stage._ground.material.opacity = 0.35; stageEl.style.removeProperty('--stage-bg');
      if (ventanas) ventanas.emissiveIntensity = 0; if (lamps) lamps.lampM.emissiveIntensity = 0;
    }
  }
  const set = p => { Object.assign(S, p); compute(); };
  // ancla para etiquetas: centro de la cara más iluminada / techo de noche
  const radAnchor = new THREE.Vector3(), heatAnchor = V(14, hT + 4, 0);
  function bestFace() {
    let b = null, bc = 0.1;
    faces.slice(0, 5).forEach(f => { const c = f.n.dot(S.sd); if (c > bc) { bc = c; b = f; } });
    if (b) radAnchor.copy(b.o.position).addScaledVector(b.n, 0.2); return !!b;
  }
  return { S, set, update, setActive, radAnchor, heatAnchor, bestFace, compute };
}
