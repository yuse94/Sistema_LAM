// Copia los archivos WebAssembly de MediaPipe a public/ para servirlos desde la propia app
// (misma versión que el paquete instalado, sin depender de un CDN).
import { cpSync, existsSync, mkdirSync } from "node:fs";

const src = "node_modules/@mediapipe/tasks-vision/wasm";
const dest = "public/mediapipe/wasm";

if (!existsSync(src)) {
  console.error("Falta @mediapipe/tasks-vision. Ejecute: npm install @mediapipe/tasks-vision");
  process.exit(1);
}
mkdirSync(dest, { recursive: true });
cpSync(src, dest, { recursive: true });
console.log(`MediaPipe: ${src} -> ${dest}`);
