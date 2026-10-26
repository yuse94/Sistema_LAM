"""Imagen resultante con marcadores y cuadrícula (para el PDF y la vista web).

La interfaz web dibuja la cuadrícula en SVG a partir de grid_origin/grid_step_px;
esta función genera la versión rasterizada que se guarda y se inserta en el PDF.
"""
from __future__ import annotations

import io

import matplotlib

matplotlib.use("Agg")  # sin ventanas: entorno servidor
import matplotlib.pyplot as plt  # noqa: E402

from .image_processing import img_grid  # noqa: E402
from .types import ViewResult  # noqa: E402

TITLES = {"anterior": "VISTA ANTERIOR", "posterior": "VISTA POSTERIOR", "lateral_derecha": "VISTA LATERAL DERECHA",
          "lateral_izquierda": "VISTA LATERAL IZQUIERDA"}


def render_overlay(result: ViewResult, fmt: str = "jpg", dpi: int = 200) -> bytes:
    img = result.image
    if img is None:
        raise ValueError("El resultado no incluye la imagen")
    h, w = img.shape[:2]
    gx, gy = result.grid_origin
    xs, ys = img_grid(gx, gy, w, h, result.grid_step_px)

    fig, ax = plt.subplots(figsize=(w / 100, h / 100))
    ax.imshow(img)
    for x in xs:
        ax.axvline(x, color="k", linewidth=0.1)
    for y in ys:
        ax.axhline(y, color="k", linewidth=0.1)
    ax.axvline(gx, color="r", linewidth=0.3)
    ax.axhline(gy, color="r", linewidth=0.3)
    mx, my = zip(*result.markers.values())
    ax.plot(mx, my, "b*", markersize=1)
    if result.derived_points:
        dx, dy = zip(*result.derived_points.values())
        ax.plot(dx, dy, "rx", markersize=3)
    ax.set_title(TITLES[result.view.value])
    ax.set_xlim(0, w)
    ax.set_ylim(h, 0)
    ax.axis("off")

    buf = io.BytesIO()
    fig.savefig(buf, format=fmt, dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    return buf.getvalue()
