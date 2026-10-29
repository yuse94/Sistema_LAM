// Prepara los archivos de MediaPipe en public/mediapipe para servirlos desde la propia app,
// sin depender de internet al usarla (necesario para el uso local en un centro):
// - los archivos WebAssembly del paquete instalado (misma versión);
// - el modelo de pose, que se descarga una sola vez (unos 9 MB) y queda en caché.
import { cpSync, existsSync, mkdirSync, renameSync, statSync, writeFileSync } from "node:fs";

const src = "node_modules/@mediapipe/tasks-vision/wasm";
const dest = "public/mediapipe";
const MODEL_URL =
  "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_full/float16/latest/pose_landmarker_full.task";
const model = `${dest}/pose_landmarker_full.task`;

if (!existsSync(src)) {
  console.error("Falta @mediapipe/tasks-vision. Ejecute: npm install");
  process.exit(1);
}
mkdirSync(dest, { recursive: true });
cpSync(src, `${dest}/wasm`, { recursive: true });
console.log(`MediaPipe: ${src} -> ${dest}/wasm`);

if (existsSync(model) && statSync(model).size > 1_000_000) {
  console.log(`MediaPipe: modelo ya descargado (${model})`);
} else {
  console.log("MediaPipe: descargando el modelo de pose (solo la primera vez)…");
  try {
    const res = await fetch(MODEL_URL);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = Buffer.from(await res.arrayBuffer());
    writeFileSync(`${model}.part`, data);
    renameSync(`${model}.part`, model);
    console.log(`MediaPipe: modelo guardado (${(data.length / 1e6).toFixed(1)} MB)`);
  } catch (err) {
    console.error(`No se pudo descargar el modelo de pose: ${err.message}`);
    console.error(`Descárguelo manualmente de ${MODEL_URL} y guárdelo como frontend/${model}`);
    process.exit(1);
  }
}
