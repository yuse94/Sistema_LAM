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

from ..image_processing import candidate_thresholds, ensure_rgb, green_filter, markers, scale_image, straighten_img
from ..types import AssessmentConfig, MarkerCountError, ResultRow, ResultTable, View


@dataclass
class MarkerDetection:
    image: np.ndarray  # imagen enderezada y recortada
    points: list[np.ndarray]  # (y, x) en orden de etiquetado (de arriba hacia abajo)
    reference_1: np.ndarray
    reference_2: np.ndarray
    scale_ratio: float  # cm por píxel
    threshold: float  # umbral del filtro verde con el que se detectaron los marcadores


def _detect_at(img: np.ndarray, threshold: float):
    straight = straighten_img(img, threshold)
    return straight, markers(green_filter(straight, threshold))


def detect_markers(view: View, image: np.ndarray, config: AssessmentConfig, expected: int) -> MarkerDetection:
    """Detector de marcadores verdes (algoritmo de la tesis).

    Primero usa el umbral configurado. Si no aparece la cantidad esperada de marcadores
    y config.auto_threshold está activo, busca otro umbral: con las fotos de validación
    ningún valor fijo sirvió para todas (dependen de la iluminación de cada foto).
    """
    img = scale_image(ensure_rgb(image))
    tried = {config.filter_threshold}
    try:
        straight, (ref_1, ref_2, ys, xs, scale) = _detect_at(img, config.filter_threshold)
        first_error = None if len(xs) == expected else MarkerCountError(
            view, expected, [(float(x), float(y)) for y, x in zip(ys, xs)], straight)
    except (ValueError, IndexError, ZeroDivisionError) as err:  # sin referencias con este umbral
        first_error = err
    threshold = config.filter_threshold

    if first_error is not None and config.auto_threshold:
        for th in candidate_thresholds(img, expected):
            if th in tried:
                continue
            tried.add(th)
            try:
                straight, (ref_1, ref_2, ys, xs, scale) = _detect_at(img, th)
            except (ValueError, IndexError, ZeroDivisionError):
                continue
            if len(xs) == expected:
                first_error, threshold = None, th
                break

    if first_error is not None:
        if isinstance(first_error, MarkerCountError):
            raise first_error
        raise ValueError(str(first_error) or "No se encontraron los marcadores de referencia") from first_error

    points = [np.array([y, x]) for y, x in zip(ys, xs)]
    return MarkerDetection(straight, points, ref_1, ref_2, float(scale), threshold)


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
