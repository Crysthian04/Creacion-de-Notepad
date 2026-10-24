// Genera dist/Modelo3D_Labs_M6_M14_offline.html: UN solo archivo, sin internet,
// que abre con doble clic (file://). Empaqueta three.js, la app, el componente <three-d-stage> y las fuentes.
import * as esbuild from 'esbuild';
import { readFile, writeFile, mkdir } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
const root = join(dirname(fileURLToPath(import.meta.url)), '..');
const r = p => join(root, p);
const alias = {
  'three': r('vendor/three.module.js'),
  'three/core': r('vendor/three.core.js'),
  'three/addons/controls/OrbitControls.js': r('vendor/addons/controls/OrbitControls.js'),
  'three/addons/exporters/OBJExporter.js': r('vendor/addons/exporters/OBJExporter.js'),
  'three/addons/exporters/GLTFExporter.js': r('vendor/addons/exporters/GLTFExporter.js'),
};
const resolver = {
  name: 'import-map',
  setup(b) {
    b.onResolve({ filter: /^three(\/|$)/ }, a => alias[a.path] ? { path: alias[a.path] } : { errors: [{ text: 'Sin alias: ' + a.path }] });
    b.onResolve({ filter: /^app\// }, a => ({ path: r('src/' + a.path) }));
  },
};
const bundle = async contents => (await esbuild.build({
  stdin: { contents, resolveDir: root, sourcefile: 'offline-entry.js' }, bundle: true, format: 'esm', target: 'es2022', minify: true, write: false,
  plugins: [resolver], legalComments: 'none', charset: 'utf8',
})).outputFiles[0].text;
// Una sola entrada → una sola copia de three.js. three-d-stage.js usa import('three') dinámico:
// esbuild lo resuelve e incrusta (sin code-splitting). El componente se define antes que la app.
const app = await bundle(`import './src/stage/three-d-stage.js';\nimport 'app/labs-app.js';`);
let html = await readFile(r('index.html'), 'utf8');
// Fuentes → data URI
html = await replaceAsync(html, /url\("(assets\/fonts\/[^"]+\.woff2)"\)/g, async (_, p) =>
  `url("data:font/woff2;base64,${(await readFile(r(p))).toString('base64')}")`);
const esc = s => s.replace(/<\/script/gi, '<\\/script');
const start = html.indexOf('<!-- DEV:'), end = html.indexOf('</script>', html.indexOf('src="./src/main.js"')) + 9;
if (start < 0 || end < 9) throw new Error('No se encontró el bloque DEV en index.html');
html = html.slice(0, start) + `<script type="module">${esc(app)}</script>` + html.slice(end);
await mkdir(r('dist'), { recursive: true });
const out = r('dist/Modelo3D_Labs_M6_M14_offline.html');
await writeFile(out, html);
console.log(`OK → ${out} (${(html.length / 1048576).toFixed(2)} MB)`);
async function replaceAsync(s, re, fn) { const ps = []; s.replace(re, (...a) => { ps.push(fn(...a)); return ''; }); const rs = await Promise.all(ps); return s.replace(re, () => rs.shift()); }
