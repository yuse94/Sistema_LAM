"""Paciente de demostración: dos evaluaciones con siluetas dibujadas (no son fotos reales).

Sirve para mostrar el historial, la comparación y el reporte sin evaluar a nadie en vivo.
Las siluetas se generan a partir de la figura de referencia del diccionario de puntos,
con desviaciones que mejoran entre la primera y la segunda evaluación.
"""
from __future__ import annotations

import io

from PIL import Image, ImageDraw

from app.lam.catalog import FIGURE_POSITIONS

SCALE = 8  # lienzo de 100 x 200 -> 800 x 1600 px
VERTEX_Y, FLOOR_Y = 4.0, 194.0  # cabeza y apoyo de los talones en la figura
HEIGHT_CM = 164.0

WALL, FLOOR, LINE = (232, 230, 226), (196, 190, 182), (170, 164, 156)
SKIN, SKIN_DARK, SHORTS, HAIR = (224, 186, 160), (196, 154, 128), (52, 86, 120), (70, 52, 40)

# Desviaciones (en unidades de la figura) de cada evaluación: la segunda muestra mejoría
DEVIATIONS = [
    {  # inicial: hombro derecho descendido, cabeza inclinada, cabeza adelantada, retroversión
        "anterior": {"F1": (1.2, 0), "F2": (1.0, 0), "F3": (0, 2.2), "F7": (0, 0.8), "F9": (1.0, 0), "F10": (-1.2, 0)},
        "posterior": {"P1": (0.8, 0), "P2": (1.2, 0), "P4": (0, 2.0), "P6": (0, 0.8)},
        "lateral_derecha": {"L1": (14.0, 1), "L2": (6.5, 0), "L5": (3.0, 0), "L3": (0, 3.0), "L4": (0, -1.5)},
    },
    {  # control: desviaciones menores
        "anterior": {"F1": (0.4, 0), "F2": (0.3, 0), "F3": (0, 0.7), "F9": (0.4, 0), "F10": (-0.5, 0)},
        "posterior": {"P2": (0.4, 0), "P4": (0, 0.6)},
        "lateral_derecha": {"L1": (10.0, 0.5), "L2": (6.5, 0), "L5": (5.0, 0), "L6": (2.0, 0), "L3": (0, 1.0)},
    },
]


def _points(view: str, deviation: dict) -> dict[str, tuple[float, float]]:
    figure = "lateral" if view.startswith("lateral") else view
    pts = dict(FIGURE_POSITIONS[figure])
    for k, (dx, dy) in deviation.items():
        x, y = pts[k]
        pts[k] = (x + dx, y + dy)
    return pts


def _px(p):
    return p[0] * SCALE, p[1] * SCALE


def _limb(d: ImageDraw.ImageDraw, pts, width: float, color):
    pts = [_px(p) for p in pts]
    w = round(width * SCALE)
    d.line(pts, fill=color, width=w, joint="curve")
    for x, y in (pts[0], pts[-1]):
        d.ellipse([x - w / 2, y - w / 2, x + w / 2, y + w / 2], fill=color)


def _background() -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("RGB", (100 * SCALE, 200 * SCALE), WALL)
    d = ImageDraw.Draw(img)
    d.rectangle([0, FLOOR_Y * SCALE, 100 * SCALE, 200 * SCALE], fill=FLOOR)
    d.line([0, FLOOR_Y * SCALE, 100 * SCALE, FLOOR_Y * SCALE], fill=LINE, width=4)
    d.line([93 * SCALE, 0, 93 * SCALE, FLOOR_Y * SCALE], fill=LINE, width=6)  # marco de puerta: referencia vertical
    return img, d


def _frontal(p: dict, posterior: bool) -> Image.Image:
    """Vista anterior o posterior. Los pares se ordenan por posición en el dibujo."""
    img, d = _background()
    ids = (("P3", "P4"), ("P5", "P6"), ("P7", "P8"), ("P9", "P10")) if posterior else \
        (("F3", "F4"), ("F7", "F8"), ("F9", "F10"), ("F11", "F12"))
    (sh_a, sh_b), (hip_a, hip_b), (kn_a, kn_b), (an_a, an_b) = [sorted((p[a], p[b])) for a, b in ids]
    head_x = p["P1"][0] if posterior else p["F1"][0]

    for hip, knee, ankle in ((hip_a, kn_a, an_a), (hip_b, kn_b, an_b)):
        _limb(d, [(hip[0], hip[1] + 2), knee, (ankle[0], ankle[1] + 6)], 9, SKIN)
        x, y = _px((ankle[0], 192))
        d.ellipse([x - 5 * SCALE, y - 2.5 * SCALE, x + 5 * SCALE, y + 2.5 * SCALE], fill=SKIN_DARK)
    for sh, out in ((sh_a, -1), (sh_b, 1)):
        _limb(d, [sh, (sh[0] + 3 * out, 66), (sh[0] + 6 * out, 98)], 5.5, SKIN)
    torso = [sh_a, sh_b, (hip_b[0] + 4, hip_b[1] + 2), (hip_a[0] - 4, hip_a[1] + 2)]
    d.polygon([_px(q) for q in torso], fill=SKIN)
    shorts = [(hip_a[0] - 5, hip_a[1] - 4), (hip_b[0] + 5, hip_b[1] - 4), (hip_b[0] + 6, 104), (hip_a[0] - 6, 104)]
    d.polygon([_px(q) for q in shorts], fill=SHORTS)
    _limb(d, [(head_x, 22), ((sh_a[0] + sh_b[0]) / 2, 34)], 7, SKIN)
    hx, hy = _px((head_x, 15))
    box = [hx - 8 * SCALE, hy - 11 * SCALE, hx + 8 * SCALE, hy + 11 * SCALE]
    d.ellipse(box, fill=HAIR if posterior else SKIN)
    if not posterior:
        d.arc(box, 190, 350, fill=HAIR, width=4 * SCALE)
    return img


def _lateral(p: dict) -> Image.Image:
    img, d = _background()
    ear, sh, hip, tro, knee, ank = p["L1"], p["L2"], p["L3"], p["L5"], p["L6"], p["L7"]
    _limb(d, [(tro[0] - 2, tro[1]), knee, (ank[0] - 2, ank[1] - 4)], 10, SKIN)
    fx, fy = _px((ank[0] + 2, 192))
    d.ellipse([fx - 7 * SCALE, fy - 2.5 * SCALE, fx + 7 * SCALE, fy + 2.5 * SCALE], fill=SKIN_DARK)
    torso = [(sh[0] - 9, sh[1] - 2), (sh[0] + 7, sh[1]), (hip[0] + 1, hip[1] + 6), (p["L4"][0] - 1, hip[1] + 6)]
    d.polygon([_px(q) for q in torso], fill=SKIN)
    d.polygon([_px(q) for q in [(p["L4"][0] - 2, hip[1] - 3), (hip[0] + 2, hip[1] - 3), (hip[0] + 2, 104),
                                (p["L4"][0] - 2, 104)]], fill=SHORTS)
    _limb(d, [sh, (sh[0] + 1, 66), (sh[0] + 3, 96)], 5.5, SKIN_DARK)
    _limb(d, [((sh[0] + ear[0]) / 2, sh[1] - 4), (ear[0] + 1, ear[1] + 4)], 7, SKIN)
    hx, hy = _px((ear[0] + 3, ear[1] - 3))
    d.ellipse([hx - 9 * SCALE, hy - 11 * SCALE, hx + 9 * SCALE, hy + 11 * SCALE], fill=SKIN)
    d.chord([hx - 9 * SCALE, hy - 11 * SCALE, hx + 9 * SCALE, hy + 11 * SCALE], 160, 340, fill=HAIR)
    return img


def demo_views(index: int) -> list[dict]:
    """Vistas de la evaluación index: imagen (JPEG), puntos en píxeles y calibración."""
    out = []
    for view, deviation in DEVIATIONS[index].items():
        pts = _points(view, deviation)
        img = _lateral(pts) if view.startswith("lateral") else _frontal(pts, view == "posterior")
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=90)
        out.append({
            "view": view, "image_jpeg": buf.getvalue(),
            "landmarks": {k: _px(v) for k, v in pts.items()},
            "calibration": {"vertex": _px((50, VERTEX_Y)), "floor": _px((50, FLOOR_Y))},
        })
    return out
