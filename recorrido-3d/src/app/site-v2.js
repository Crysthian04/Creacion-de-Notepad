import * as THREE from 'three';

// Entorno ampliado (ilustrativo, según vista aérea): loma boscosa detrás, Edificio 1 al noreste,
// kiosco en la rotonda, autos, postes de luz, balcones y alero del Edificio 2.
export function enrichSite(m) {
  const site = m.site, bld = m.root.getObjectByName('edificio');
  const std = (name, color, o = {}) => new THREE.MeshStandardMaterial({ name, color, roughness: o.r ?? 0.85, metalness: o.m ?? 0, emissive: o.e ?? 0, emissiveIntensity: o.ei ?? 0 });
  const add = (g, geo, mat, x, y, z, name) => { const o = new THREE.Mesh(geo, mat); o.name = name; o.position.set(x, y, z); o.castShadow = o.receiveShadow = true; g.add(o); return o; };
  const shell = n => m.shell.mats.find(s => s.mat.name === n)?.mat;
  const cream = shell('muro_crema'), band = shell('franja_clara'), tower = shell('bloque_posterior');
  if (tower) tower.color.set(0xE3D3AE);

  // Balcones y alero (fachada frontal de las alas)
  const nb = [];
  if (bld && band && cream) {
    [-1, 1].forEach(s => {
      [1, 2].forEach(f => {
        const o = add(bld, new THREE.BoxGeometry(17, 0.18, 1.1), band, s * 13.25, f * 3.6 + 0.1, 5.6, `balcon_${s < 0 ? 'izq' : 'der'}_${f}`); nb.push(o);
        const r = add(bld, new THREE.BoxGeometry(17, 0.9, 0.06), cream, s * 13.25, f * 3.6 + 0.6, 6.12, `baranda_${s < 0 ? 'izq' : 'der'}_${f}`); nb.push(r);
      });
      nb.push(add(bld, new THREE.BoxGeometry(19.8, 0.14, 1.6), cream, s * 13.25, 3 * 3.6 + 0.05, 5.8, `alero_${s < 0 ? 'izq' : 'der'}`));
    });
    nb.forEach(o => { o.castShadow = false; m.shell.meshes.push(o); });
  }

  // Loma boscosa detrás
  const hillM = std('loma', 0x24331F, { r: 1 });
  const hill = add(site, new THREE.SphereGeometry(1, 28, 14, 0, Math.PI * 2, 0, Math.PI / 2), hillM, 0, 0, -62, 'loma_posterior');
  hill.scale.set(70, 14, 28); hill.castShadow = false;
  const crownM = std('bosque', 0x2E4A27, { r: 1 }), crownG = new THREE.IcosahedronGeometry(1, 0);
  const rnd = (s => () => (s = (s * 16807) % 2147483647) / 2147483647)(7);
  const forest = new THREE.InstancedMesh(crownG, crownM, 140); forest.name = 'bosque_loma';
  const t = new THREE.Object3D();
  for (let i = 0; i < 140; i++) {
    const a = rnd() * Math.PI, rr = 0.15 + rnd() * 0.8;
    const x = Math.cos(a) * 70 * rr * (rnd() > 0.5 ? 1 : -1), z = -62 - Math.sin(a) * 28 * rr * (rnd() > 0.3 ? 1 : -0.6);
    const nx = x / 70, nz = (z + 62) / 28, h = 14 * Math.sqrt(Math.max(0, 1 - nx * nx - nz * nz));
    if (z > -30) { t.scale.setScalar(0); } else { const s = 2.4 + rnd() * 2.6; t.scale.set(s, s * 0.85, s); }
    t.position.set(x, h + 1.2, z); t.rotation.y = rnd() * 6; t.updateMatrix(); forest.setMatrixAt(i, t.matrix);
  }
  site.add(forest);

  // Edificio 1 (volumen ilustrativo, noreste)
  const e1 = new THREE.Group(); e1.name = 'edificio_1_ilustrativo'; e1.position.set(58, 0, -26); e1.rotation.y = -0.5; site.add(e1);
  const brick = std('e1_ladrillo', 0x8F4A36), roof = std('e1_teja', 0x7E3628), bnd = std('e1_franja', 0xCDBF9F);
  add(e1, new THREE.BoxGeometry(30, 7.2, 11), brick, 0, 3.6, 0, 'e1_cuerpo');
  [0.1, 3.6, 7.1].forEach((y, i) => add(e1, new THREE.BoxGeometry(30.3, 0.3, 11.3), bnd, 0, y + 0.15, 0, 'e1_franja_' + i));
  const r1 = add(e1, new THREE.ConeGeometry(1, 1, 4, 1), roof, 0, 8.6, 0, 'e1_techo'); r1.rotation.y = Math.PI / 4; r1.scale.set(23, 2.6, 8.6);
  add(e1, new THREE.BoxGeometry(12, 7.2, 10), brick, 10, 3.6, 10, 'e1_ala');
  const r2 = add(e1, new THREE.ConeGeometry(1, 1, 4, 1), roof, 10, 8.4, 10, 'e1_ala_techo'); r2.rotation.y = Math.PI / 4; r2.scale.set(9.5, 2.3, 8);

  // Kiosco en la rotonda
  const kio = new THREE.Group(); kio.name = 'rotonda_kiosco'; kio.position.set(0, 0, 30); site.add(kio);
  const white = std('kiosco_blanco', 0xE9E4D8), kroof = std('kiosco_techo', 0x8E3B2B);
  add(kio, new THREE.CylinderGeometry(2.6, 2.8, 0.35, 16), white, 0, 0.17, 0, 'kiosco_base');
  for (let i = 0; i < 6; i++) { const a = i / 6 * Math.PI * 2; add(kio, new THREE.CylinderGeometry(0.1, 0.1, 2.6, 6), white, Math.cos(a) * 2.1, 1.6, Math.sin(a) * 2.1, 'kiosco_columna_' + i); }
  add(kio, new THREE.ConeGeometry(3.1, 1.5, 6), kroof, 0, 3.6, 0, 'kiosco_techo');

  // Autos en el estacionamiento
  const carCols = [0xC9CED3, 0x2E3A4A, 0x8C2F2A, 0xE6E2D6, 0x4A525A, 0x5C6E7E];
  const carG = new THREE.Group(); carG.name = 'autos'; site.add(carG);
  [[-12, 8.6], [-9.2, 8.6], [-6.4, 8.6], [7.6, 8.6], [10.4, 8.6], [-11, 16.4], [9.2, 16.4], [12, 16.4]].forEach(([x, z], i) => {
    const c = std('auto_' + i, carCols[i % carCols.length], { r: 0.4, m: 0.3 });
    add(carG, new THREE.BoxGeometry(1.8, 0.7, 4.1), c, x, 0.55, z, 'auto_' + i + '_cuerpo');
    add(carG, new THREE.BoxGeometry(1.6, 0.55, 2.1), std('auto_vidrio', 0x1E2A33, { r: 0.2, m: 0.5 }), x, 1.15, z - 0.2, 'auto_' + i + '_cabina');
  });

  // Postes de luz
  const poleM = std('poste', 0x6E767E, { r: 0.5, m: 0.5 }), lampM = std('luminaria', 0xFFF3D6, { e: 0xFFD48A, ei: 0 });
  const poles = new THREE.Group(); poles.name = 'postes_luz'; site.add(poles);
  const lampPts = [];
  [[-15, 19.5], [15, 19.5], [-14, 6.6], [14, 6.6], [12.5, 30], [-12.5, 30], [0, 42.5], [4.5, 50], [4.5, 62]].forEach(([x, z], i) => {
    add(poles, new THREE.CylinderGeometry(0.08, 0.11, 5, 6), poleM, x, 2.5, z, 'poste_' + i);
    add(poles, new THREE.SphereGeometry(0.28, 10, 8), lampM, x, 5.1, z, 'luminaria_' + i).castShadow = false;
    lampPts.push(new THREE.Vector3(x, 5.1, z));
  });
  return { lampM, lampPts };
}
