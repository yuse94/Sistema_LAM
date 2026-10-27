// Solo tipos: la librería (~400 kB) se descarga al analizar la primera foto, no al abrir la app.
import type { PoseLandmarker } from "@mediapipe/tasks-vision";
import type { Calibration, Point, PosePoint } from "./types";

// Modelo "full": buen equilibrio entre precisión y velocidad. El estudio de 2026 en
// Sensors encontró peores resultados con el modelo "heavy" para postura estática.
const MODEL_URL =
  "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_full/float16/latest/pose_landmarker_full.task";
const WASM_PATH = "/mediapipe/wasm"; // copiado por scripts/copy-mediapipe.mjs

let landmarkerPromise: Promise<PoseLandmarker> | null = null;

async function create(delegate: "GPU" | "CPU") {
  const { FilesetResolver, PoseLandmarker } = await import("@mediapipe/tasks-vision");
  const vision = await FilesetResolver.forVisionTasks(WASM_PATH);
  return PoseLandmarker.createFromOptions(vision, {
    baseOptions: { modelAssetPath: MODEL_URL, delegate },
    runningMode: "IMAGE",
    numPoses: 1,
    outputSegmentationMasks: true,
  });
}

function getLandmarker() {
  // Se carga una sola vez; si la GPU no está disponible se usa la CPU.
  landmarkerPromise ??= create("GPU").catch(() => create("CPU"));
  landmarkerPromise.catch(() => (landmarkerPromise = null));
  return landmarkerPromise;
}

export interface PoseDetection {
  pose: PosePoint[]; // 33 puntos en píxeles de la imagen
  calibration: Calibration | null; // vértice y suelo desde la silueta
}

/** Detecta la pose en el navegador: la foto no sale del equipo para este paso. */
export async function detectPose(img: HTMLImageElement): Promise<PoseDetection> {
  const landmarker = await getLandmarker();
  const w = img.naturalWidth;
  const h = img.naturalHeight;
  // Se dibuja en un canvas para que el modelo vea la foto con la misma orientación
  // que se muestra en pantalla (los celulares guardan la rotación en el EXIF).
  const canvas = document.createElement("canvas");
  canvas.width = w;
  canvas.height = h;
  canvas.getContext("2d")!.drawImage(img, 0, 0, w, h);
  const result = landmarker.detect(canvas);

  const landmarks = result.landmarks[0];
  if (!landmarks) {
    result.segmentationMasks?.forEach((m) => m.close());
    throw new Error("No se detectó a ninguna persona en la fotografía");
  }
  const pose = landmarks.map((p) => ({ x: p.x * w, y: p.y * h, visibility: p.visibility ?? 1 }));

  let calibration: Calibration | null = null;
  const mask = result.segmentationMasks?.[0];
  if (mask) {
    calibration = calibrationFromMask(mask.getAsFloat32Array(), mask.width, mask.height, w / mask.width, h / mask.height);
    result.segmentationMasks?.forEach((m) => m.close());
  }
  return { pose, calibration };
}

/** Fila más alta y más baja de la silueta: vértice de la cabeza y apoyo de los pies. */
function calibrationFromMask(data: Float32Array, mw: number, mh: number, sx: number, sy: number): Calibration | null {
  const rowCenter = (y: number): number | null => {
    let sum = 0;
    let n = 0;
    for (let x = 0; x < mw; x++) {
      if (data[y * mw + x] > 0.5) {
        sum += x;
        n++;
      }
    }
    return n >= 2 ? sum / n : null; // al menos 2 píxeles para ignorar ruido aislado
  };
  let vertex: Point | null = null;
  for (let y = 0; y < mh && !vertex; y++) {
    const cx = rowCenter(y);
    if (cx !== null) vertex = { x: cx * sx, y: y * sy };
  }
  let floor: Point | null = null;
  for (let y = mh - 1; y >= 0 && !floor; y--) {
    const cx = rowCenter(y);
    if (cx !== null) floor = { x: cx * sx, y: (y + 1) * sy };
  }
  return vertex && floor ? { vertex, floor } : null;
}
