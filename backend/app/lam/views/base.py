"""Pasos comunes a todas las vistas.

El análisis se divide en dos etapas independientes:

1. Detección: imagen -> puntos anatómicos con nombre (F1..F14, P1..P12, L1..L7).
   Hoy la hace el detector de marcadores verdes (detect_markers + assign de cada
   vista); a futuro, un detector sin marcadores (estimación de pose).
2. Evaluación: puntos -> tablas y diagnóstico (evaluate de cada vista).

Como la evaluación solo necesita los puntos y la escala, el evaluador puede
corregir cualquier punto en la interfaz y recalcular sin volver a procesar la foto.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from ..image_processing import ensure_rgb, green_filter, markers, scale_image, straighten_img
from ..types import AssessmentConfig, MarkerCountError, ResultRow, ResultTable, View


@dataclass
class MarkerDetection:
    image: np.ndarray  # imagen enderezada y recortada
    points: list[np.ndarray]  # (y, x) en orden de etiquetado (de arriba hacia abajo)
    reference_1: np.ndarray
    reference_2: np.ndarray
    scale_ratio: float  # cm por píxel


def detect_markers(view: View, image: np.ndarray, config: AssessmentConfig, expected: int) -> MarkerDetection:
    """Detector de marcadores verdes (algoritmo de la tesis)."""
    img = scale_image(ensure_rgb(image))
    straight = straighten_img(img, config.filter_threshold)
    ref_1, ref_2, ys, xs, scale = markers(green_filter(straight, config.filter_threshold))

    if len(xs) != expected:
        raise MarkerCountError(view, expected, [(float(x), float(y)) for y, x in zip(ys, xs)], straight)

    points = [np.array([y, x]) for y, x in zip(ys, xs)]
    return MarkerDetection(straight, points, ref_1, ref_2, float(scale))


def sort_by_x(points: list[np.ndarray]) -> list[np.ndarray]:
    """Ordena puntos de izquierda a derecha en la imagen (equivale a los min/max del original)."""
    return sorted(points, key=lambda p: p[1])


def center(*points: np.ndarray) -> np.ndarray:
    return np.mean(points, axis=0)


def xy(p: np.ndarray) -> tuple[float, float]:
    return float(p[1]), float(p[0])


def yx(p: tuple[float, float]) -> np.ndarray:
    """(x, y) de la API -> (y, x) interno."""
    return np.array([float(p[1]), float(p[0])])


def table(key: str, title: str, columns: tuple[str, str, str], items, results) -> ResultTable:
    rows = [ResultRow(item, d, float(v)) for item, (d, v) in zip(items, results)]
    return ResultTable(key, title, columns, rows)


def require(points: dict[str, np.ndarray], labels: dict[str, str]) -> None:
    missing = [k for k in labels if k not in points]
    if missing:
        raise ValueError(f"Faltan puntos anatómicos: {', '.join(missing)}")
