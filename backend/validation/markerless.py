# /// script
# requires-python = ">=3.10,<3.13"
# dependencies = [
#     "mediapipe>=0.10.14",
#     "scikit-image>=0.22",
#     "pillow>=10",
# ]
# ///
"""Validación del modo sin marcadores contra el detector de marcadores verdes.

Las fotos de validación tienen marcadores, así que en cada foto se obtiene:
- la referencia: puntos detectados por los marcadores verdes (algoritmo de la tesis);
- la estimación: puntos que entrega el modo sin marcadores (MediaPipe + proporciones).

Se mide, en la misma imagen y con la misma escala (la de los marcadores R1/R2):
- el error de cada punto anatómico en centímetros;
- la diferencia en cada fila de las tablas de resultados y si coincide la dirección;
- la estatura que implica la silueta de MediaPipe (para revisar la escala por estatura).

Uso, desde la carpeta backend:

    uv run validation/markerless.py
    uv run validation/markerless.py --estaturas validation/estaturas.csv

Resultados en validation/resultados/ (no se suben al repositorio: contienen fotos de pacientes).
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import re
import statistics
import sys
import urllib.request
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageOps

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from app.lam import AssessmentConfig, MarkerCountError, PosePoint, View, analyze, evaluate_landmarks  # noqa: E402
from app.lam.pose import landmarks_from_pose  # noqa: E402

MODEL_URL = ("https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_full/"
             "float16/latest/pose_landmarker_full.task")
OUT = Path(__file__).resolve().parent / "resultados"


# ------------------------------------------------------------------ fotos

def view_of(name: str) -> View:
    n = name.lower()
    if "anterior" in n:
        return View.ANTERIOR
    if "posterior" in n:
        return View.POSTERIOR
    return View.LATERAL_DERECHA if "derecha" in n else View.LATERAL_IZQUIERDA


def person_of(name: str) -> str:
    return re.split(r"[- ](?=anterior|posterior|lateral)", name, maxsplit=1)[0]


def load(path: Path) -> np.ndarray:
    return np.asarray(ImageOps.exif_transpose(Image.open(path)).convert("RGB"))


# ------------------------------------------------------------------ MediaPipe

@dataclass
class PoseDetection:
    pose: list[PosePoint]
    vertex: tuple[float, float] | None
    floor: tuple[float, float] | None


class MediaPipeDetector:
    def __init__(self, model_dir: Path):
        import mediapipe as mp
        from mediapipe.tasks import python as mp_python
        from mediapipe.tasks.python import vision

        model_dir.mkdir(parents=True, exist_ok=True)
        model = model_dir / "pose_landmarker_full.task"
        if not model.exists():
            print(f"Descargando el modelo de pose en {model} …")
            urllib.request.urlretrieve(MODEL_URL, model)
        options = vision.PoseLandmarkerOptions(
            base_options=mp_python.BaseOptions(model_asset_path=str(model)),
            running_mode=vision.RunningMode.IMAGE, num_poses=1, output_segmentation_masks=True)
        self._mp = mp
        self._landmarker = vision.PoseLandmarker.create_from_options(options)

    def __call__(self, rgb: np.ndarray) -> PoseDetection | None:
        h, w = rgb.shape[:2]
        image = self._mp.Image(image_format=self._mp.ImageFormat.SRGB, data=np.ascontiguousarray(rgb))
        res = self._landmarker.detect(image)
        if not res.pose_landmarks:
            return None
        pose = [PosePoint(p.x * w, p.y * h, getattr(p, "visibility", 1.0) or 1.0) for p in res.pose_landmarks[0]]
        vertex = floor = None
        if res.segmentation_masks:
            mask = np.squeeze(res.segmentation_masks[0].numpy_view())
            vertex, floor = calibration_from_mask(mask, w / mask.shape[1], h / mask.shape[0])
        return PoseDetection(pose, vertex, floor)


def calibration_from_mask(mask: np.ndarray, sx: float, sy: float):
    """Fila más alta y más baja de la silueta (misma lógica que frontend/src/lib/pose.ts)."""
    rows = np.flatnonzero((mask > 0.5).sum(axis=1) >= 2)
    if rows.size == 0:
        return None, None
    top, bottom = rows[0], rows[-1]
    cx = lambda r: float(np.flatnonzero(mask[r] > 0.5).mean())  # noqa: E731
    return (cx(top) * sx, top * sy), (cx(bottom) * sx, (bottom + 1) * sy)


# ------------------------------------------------------------------ comparación

def compare(path: Path, detect, config: AssessmentConfig):
    view = view_of(path.name)
    ref = analyze(view, load(path), config)  # referencia: marcadores
    det = detect(ref.image)  # MediaPipe sobre la misma imagen enderezada
    if det is None:
        return None
    mapped = landmarks_from_pose(view, det.pose)
    est = evaluate_landmarks(view, mapped.landmarks, ref.scale_ratio, config)  # misma escala que la referencia

    points = []
    for k, (rx, ry) in ref.markers.items():
        ex, ey = mapped.landmarks[k]
        dx, dy = (ex - rx) * ref.scale_ratio, (ey - ry) * ref.scale_ratio
        points.append({"punto": k, "estimado": k in mapped.estimated, "dx_cm": dx, "dy_cm": dy,
                       "error_cm": math.hypot(dx, dy)})

    rows = []
    for t_ref, t_est in zip(ref.tables, est.tables):
        unit = "°" if t_ref.columns[2] == "Ángulo" else "cm"
        for a, b in zip(t_ref.rows, t_est.rows):
            rows.append({"tabla": t_ref.title, "fila": a.item, "unidad": unit, "marcadores": a.value,
                         "sin_marcadores": b.value, "diferencia": b.value - a.value,
                         "dir_marcadores": a.direction, "dir_sin_marcadores": b.direction,
                         "coincide": a.direction == b.direction})

    height = None
    if det.vertex and det.floor:
        height = (det.floor[1] - det.vertex[1]) * ref.scale_ratio
    raw = {"vista": view.value, "ancho": int(ref.image.shape[1]), "alto": int(ref.image.shape[0]),
           "escala_marcadores": ref.scale_ratio, "marcadores": ref.markers,
           "pose": [[p.x, p.y, p.visibility] for p in det.pose], "vertice": det.vertex, "suelo": det.floor}
    return view, ref, mapped, points, rows, height, raw


def overlay(path: Path, ref, mapped, out: Path):
    im = Image.fromarray(ref.image)
    d = ImageDraw.Draw(im)
    for k, (x, y) in ref.markers.items():
        ex, ey = mapped.landmarks[k]
        d.line((x, y, ex, ey), fill=(255, 255, 0), width=2)
        d.ellipse((x - 5, y - 5, x + 5, y + 5), outline=(255, 0, 255), width=2)
        color = (255, 150, 0) if k in mapped.estimated else (0, 220, 255)
        d.rectangle((ex - 4, ey - 4, ex + 4, ey + 4), outline=color, width=2)
        d.text((x + 7, y - 6), k, fill=(255, 255, 255), stroke_width=2, stroke_fill=(0, 0, 0))
    out.mkdir(parents=True, exist_ok=True)
    im.save(out / f"{path.stem}.jpg", quality=88)


def summarize(all_points, all_rows, heights, real_heights) -> str:
    lines = ["# Validación del modo sin marcadores", "",
             "Referencia: detector de marcadores verdes en las mismas fotos y con la misma escala.",
             "Puntos *estimados*: no existen en MediaPipe y se ubican por proporciones (el evaluador los ajusta).", ""]

    lines += ["## Error por punto anatómico", "",
              "| Punto | Origen | Fotos | Error medio (cm) | Mediana (cm) | P90 (cm) | Sesgo horizontal (cm) | Sesgo vertical (cm) |",
              "|---|---|---|---|---|---|---|---|"]
    by_point: dict[str, list[dict]] = {}
    for p in all_points:
        by_point.setdefault(p["punto"], []).append(p)
    order = sorted(by_point, key=lambda k: ("FPL".index(k[0]), int(k[1:])))
    for k in order:
        ps = by_point[k]
        errs = sorted(p["error_cm"] for p in ps)
        p90 = errs[min(len(errs) - 1, int(round(0.9 * (len(errs) - 1))))]
        lines.append(f"| {k} | {'estimado' if ps[0]['estimado'] else 'MediaPipe'} | {len(ps)} | "
                     f"{statistics.mean(errs):.1f} | {statistics.median(errs):.1f} | {p90:.1f} | "
                     f"{statistics.mean(p['dx_cm'] for p in ps):+.1f} | {statistics.mean(p['dy_cm'] for p in ps):+.1f} |")

    lines += ["", "## Diferencia en las tablas de resultados", "",
              "| Tabla | Fila | Fotos | Diferencia media absoluta | Coincide la dirección |", "|---|---|---|---|---|"]
    by_row: dict[tuple[str, str], list[dict]] = {}
    for r in all_rows:
        by_row.setdefault((r["tabla"], r["fila"]), []).append(r)
    for (table, row), rs in by_row.items():
        lines.append(f"| {table} | {row} | {len(rs)} | {statistics.mean(abs(r['diferencia']) for r in rs):.2f} "
                     f"{rs[0]['unidad']} | {100 * sum(r['coincide'] for r in rs) / len(rs):.0f} % |")

    if heights:
        lines += ["", "## Estatura según la silueta de MediaPipe", "",
                  "La escala por estatura usa el vértice y el suelo de la silueta. Aquí se mide qué estatura "
                  "implica la silueta con la escala de los marcadores. Si se conoce la estatura real, la "
                  "diferencia es el error de escala que tendría el modo sin marcadores.", "",
                  "| Persona | Estatura por silueta (cm, mediana de las vistas) | Estatura real (cm) | Diferencia |",
                  "|---|---|---|---|"]
        for person, hs in sorted(heights.items()):
            med = statistics.median(hs)
            real = real_heights.get(person)
            diff = f"{100 * (med - real) / real:+.1f} %" if real else "—"
            lines.append(f"| {person} | {med:.1f} | {real if real else '—'} | {diff} |")
    return "\n".join(lines) + "\n"


def main(argv=None, detect=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--fotos", type=Path, default=BACKEND.parent / "Pruebas_adultos")
    ap.add_argument("--estaturas", type=Path, help="CSV con columnas persona,estatura_cm (opcional)")
    ap.add_argument("--salida", type=Path, default=OUT)
    ap.add_argument("--incluir-espejos", action="store_true",
                    help="Incluir las laterales izquierdas (en las fotos actuales son espejos de la derecha)")
    args = ap.parse_args(argv)

    real_heights = {}
    if args.estaturas:
        with open(args.estaturas, newline="", encoding="utf-8") as f:
            real_heights = {r["persona"].strip(): float(r["estatura_cm"].replace(",", "."))
                            for r in csv.DictReader(f) if (r.get("estatura_cm") or "").strip()}

    detect = detect or MediaPipeDetector(Path(__file__).resolve().parent / "modelos")
    config = AssessmentConfig()
    photos = sorted(p for p in args.fotos.iterdir() if p.suffix.lower() in (".jpg", ".jpeg", ".png"))
    if not args.incluir_espejos:
        photos = [p for p in photos if view_of(p.name) is not View.LATERAL_IZQUIERDA]

    all_points, all_rows, heights, raw_poses = [], [], {}, {}
    for path in photos:
        try:
            out = compare(path, detect, config)
        except MarkerCountError as err:
            print(f"{path.name}: sin referencia ({err})")
            continue
        if out is None:
            print(f"{path.name}: MediaPipe no detectó a la persona")
            continue
        view, ref, mapped, points, rows, height, raw = out
        raw_poses[path.name] = raw
        person = person_of(path.name)
        for p in points:
            p.update(foto=path.name, persona=person, vista=view.value)
        for r in rows:
            r.update(foto=path.name, persona=person, vista=view.value)
        all_points += points
        all_rows += rows
        if height:
            heights.setdefault(person, []).append(height)
        overlay(path, ref, mapped, args.salida / "imagenes")
        print(f"{path.name}: error medio {statistics.mean(p['error_cm'] for p in points):.1f} cm")

    args.salida.mkdir(parents=True, exist_ok=True)
    for name, data in (("puntos.csv", all_points), ("tablas.csv", all_rows)):
        if data:
            with open(args.salida / name, "w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=list(data[0]))
                w.writeheader()
                w.writerows(data)
    # Solo coordenadas (sin imágenes): sirven para ajustar las proporciones de los puntos estimados
    (args.salida / "poses.json").write_text(json.dumps(raw_poses, ensure_ascii=False), encoding="utf-8")
    report = summarize(all_points, all_rows, heights, real_heights)
    (args.salida / "resumen.md").write_text(report, encoding="utf-8")
    print(f"\nResumen: {args.salida / 'resumen.md'}")
    return all_points, all_rows, heights


if __name__ == "__main__":
    main()
