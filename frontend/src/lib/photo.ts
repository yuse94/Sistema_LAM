/**
 * Tamaño estándar de las fotos del modo sin marcadores: 1600 px en el lado largo.
 *
 * Las fotos de celular llegan con resoluciones muy distintas (de 2 a 50 MP). Con un
 * tamaño fijo, los puntos, la cuadrícula y la lupa se ven igual en todas las vistas,
 * MediaPipe trabaja más rápido y la subida pesa menos. A 1600 px, una persona de pie
 * ocupa unos 1300 px: alrededor de 1.3 mm por píxel, más fino que la precisión con la
 * que se ubica un punto anatómico.
 */
export const STANDARD_LONG_SIDE = 1600;

export interface StandardPhoto {
  url: string; // object URL de la foto estandarizada (liberar con URL.revokeObjectURL)
  blob: Blob; // JPEG que se sube al guardar
  img: HTMLImageElement;
  width: number;
  height: number;
}

async function decode(src: string) {
  const img = new Image();
  img.src = src;
  await img.decode();
  return img;
}

export async function standardizePhoto(file: Blob): Promise<StandardPhoto> {
  const original = URL.createObjectURL(file);
  try {
    // El navegador ya aplica la orientación EXIF al dibujar la imagen
    const src = await decode(original);
    const s = Math.min(1, STANDARD_LONG_SIDE / Math.max(src.naturalWidth, src.naturalHeight));
    const width = Math.round(src.naturalWidth * s);
    const height = Math.round(src.naturalHeight * s);
    const canvas = document.createElement("canvas");
    canvas.width = width;
    canvas.height = height;
    const ctx = canvas.getContext("2d")!;
    ctx.imageSmoothingQuality = "high";
    ctx.drawImage(src, 0, 0, width, height);
    const blob = await new Promise<Blob>((resolve, reject) =>
      canvas.toBlob((b) => (b ? resolve(b) : reject(new Error("No se pudo procesar la fotografía"))), "image/jpeg", 0.92));
    const url = URL.createObjectURL(blob);
    return { url, blob, img: await decode(url), width, height };
  } finally {
    URL.revokeObjectURL(original);
  }
}
