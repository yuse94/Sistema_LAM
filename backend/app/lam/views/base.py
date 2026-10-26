"""Pasos comunes a las tres vistas."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from ..image_processing import ensure_rgb, green_filter, markers, scale_image, straighten_img
from ..types import AssessmentConfig, MarkerCountError, ResultRow, ResultTable, View


@dataclass
class Prepared:
    image: np.ndarray
    points: list[np.ndarray]  # (y, x) en orden de etiquetado
    reference_1: np.ndarray
    reference_2: np.ndarray
    scale_ratio: float
    grid_step_px: float


def prepare(view: View, image: np.ndarray, config: AssessmentConfig, expected: int) -> Prepared:
    img = scale_image(ensure_rgb(image))
    straight = straighten_img(img, config.filter_threshold)
    ref_1, ref_2, ys, xs, scale = markers(green_filter(straight, config.filter_threshold))

    if len(xs) != expected:
        raise MarkerCountError(view, expected, [(float(x), float(y)) for y, x in zip(ys, xs)], straight)

    grid_step = float(np.linalg.norm(ref_2 - ref_1)) * config.grid_size / 100
    points = [np.array([y, x]) for y, x in zip(ys, xs)]
    return Prepared(straight, points, ref_1, ref_2, float(scale), grid_step)


def sort_by_x(points: list[np.ndarray]) -> list[np.ndarray]:
    """Ordena puntos de izquierda a derecha en la imagen (equivale a los min/max del original)."""
    return sorted(points, key=lambda p: p[1])


def center(*points: np.ndarray) -> np.ndarray:
    return np.mean(points, axis=0)


def xy(p: np.ndarray) -> tuple[float, float]:
    return float(p[1]), float(p[0])


def table(key: str, title: str, columns: tuple[str, str, str], items, results) -> ResultTable:
    rows = [ResultRow(item, d, float(v)) for item, (d, v) in zip(items, results)]
    return ResultTable(key, title, columns, rows)
