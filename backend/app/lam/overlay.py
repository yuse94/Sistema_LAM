"""Imagen resultante con puntos y cuadrícula (para el PDF y las evaluaciones guardadas).

La interfaz web dibuja lo mismo en SVG (LandmarkEditor); aquí se rasteriza con Pillow.
La cuadrícula se dibuja rotada -roll_deg alrededor de grid_origin, igual que el editor,
para que siga a la vertical real de la escena cuando la foto se niveló.
"""
from __future__ import annotations

import io
import math
from collections.abc import Iterable, Mapping
from typing import TYPE_CHECKING

import numpy as np
from PIL import Image, ImageDraw, ImageFont

if TYPE_CHECKING:
    from .types import ViewResult

Point = tuple[float, float]

TITLES = {"anterior": "VISTA ANTERIOR", "posterior": "VISTA POSTERIOR", "lateral_derecha": "VISTA LATERAL DERECHA",
          "lateral_izquierda": "VISTA LATERAL IZQUIERDA"}

# Mismos colores que el tema de la interfaz (index.css)
DETECTED = (14, 124, 116)  # --point-detected / primary
ESTIMATED = (217, 119, 6)  # --point-estimated
DERIVED = (220, 38, 38)
PLUMB = (220, 38, 38)
GRID = (0, 0, 0, 70)


def _font(size: int):
    for name in ("DejaVuSans-Bold.ttf", "arialbd.ttf", "Arial Bold.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default(size)


def _rotate(p: Point, center: Point, deg: float) -> Point:
    """Rotación con la convención de SVG (ángulo positivo = horario en pantalla, y hacia abajo)."""
    t = math.radians(deg)
    dx, dy = p[0] - center[0], p[1] - center[1]
    return center[0] + dx * math.cos(t) - dy * math.sin(t), center[1] + dx * math.sin(t) + dy * math.cos(t)


def draw_overlay(image: np.ndarray | Image.Image, markers: Mapping[str, Point], *,
                 derived: Mapping[str, Point] | None = None, grid_origin: Point | None = None,
                 grid_step_px: float | None = None, roll_deg: float = 0.0, estimated: Iterable[str] = (),
                 max_side: int = 1600, labels: bool = True) -> Image.Image:
    """Dibuja cuadrícula, plomada, puntos anatómicos (con su id) y centros derivados.

    Las coordenadas están en píxeles de la imagen original; si la imagen supera max_side
    se reduce y las coordenadas se escalan.
    """
    img = image if isinstance(image, Image.Image) else Image.fromarray(np.asarray(image))
    img = img.convert("RGB")
    s = min(1.0, max_side / max(img.size))
    if s < 1.0:
        img = img.resize((round(img.width * s), round(img.height * s)), Image.Resampling.LANCZOS)
    w, h = img.size
    sc = lambda p: (p[0] * s, p[1] * s)  # noqa: E731
    unit = max(w, h) / 1000  # grosor de línea y tamaño de punto proporcionales a la imagen

    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)

    if grid_origin is not None and grid_step_px and grid_step_px > 0:
        o = sc(grid_origin)
        step = grid_step_px * s
        reach = math.hypot(w, h)  # basta para cubrir la imagen en cualquier rotación
        n = int(reach / step) + 1
        rot = lambda p: _rotate(p, o, -roll_deg)  # noqa: E731
        for i in range(-n, n + 1):
            if i == 0:
                continue
            x, y = o[0] + i * step, o[1] + i * step
            d.line([rot((x, o[1] - reach)), rot((x, o[1] + reach))], fill=GRID, width=max(1, round(unit)))
            d.line([rot((o[0] - reach, y)), rot((o[0] + reach, y))], fill=GRID, width=max(1, round(unit)))
        lw = max(2, round(unit * 2))
        d.line([rot((o[0], o[1] - reach)), rot((o[0], o[1] + reach))], fill=PLUMB + (220,), width=lw)
        d.line([rot((o[0] - reach, o[1])), rot((o[0] + reach, o[1]))], fill=PLUMB + (220,), width=lw)

    for p in (derived or {}).values():
        x, y = sc(p)
        r = 5 * unit
        d.line([(x - r, y - r), (x + r, y + r)], fill=DERIVED + (255,), width=max(2, round(unit * 1.6)))
        d.line([(x - r, y + r), (x + r, y - r)], fill=DERIVED + (255,), width=max(2, round(unit * 1.6)))

    pending = set(estimated)
    font = _font(max(11, round(13 * unit)))
    r = 6 * unit
    for pid, p in markers.items():
        x, y = sc(p)
        color = ESTIMATED if pid in pending else DETECTED
        d.ellipse([x - r, y - r, x + r, y + r], fill=color + (255,), outline=(255, 255, 255, 255),
                  width=max(1, round(unit * 1.5)))
        if labels:
            tx, ty = x + r + 3 * unit, y - r - 2 * unit
            d.text((tx, ty), pid, font=font, fill=(255, 255, 255, 255), stroke_width=max(2, round(unit * 2)),
                   stroke_fill=color + (255,))

    return Image.alpha_composite(img.convert("RGBA"), layer).convert("RGB")


def to_jpeg(img: Image.Image, quality: int = 88) -> bytes:
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=quality, optimize=True)
    return buf.getvalue()


def render_overlay(result: ViewResult, fmt: str = "jpg", max_side: int = 1600,
                   estimated: Iterable[str] = ()) -> bytes:
    """Overlay de un ViewResult (requiere result.image)."""
    if result.image is None:
        raise ValueError("El resultado no incluye la imagen")
    img = draw_overlay(result.image, result.markers, derived=result.derived_points, grid_origin=result.grid_origin,
                       grid_step_px=result.grid_step_px, roll_deg=result.roll_deg, estimated=estimated,
                       max_side=max_side)
    if fmt.lower() in ("jpg", "jpeg"):
        return to_jpeg(img)
    buf = io.BytesIO()
    img.save(buf, format=fmt.upper())
    return buf.getvalue()
