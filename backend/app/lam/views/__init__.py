"""Análisis por vista fotográfica.

- analyze(): detección con marcadores verdes + evaluación (flujo de la tesis).
- evaluate_landmarks(): evaluación a partir de puntos ya ubicados, por ejemplo
  después de que el evaluador los ajustó en la interfaz o de un detector sin marcadores.
"""
from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass

import numpy as np

from ..types import AssessmentConfig, Evaluation, View, ViewResult
from . import anterior, lateral, posterior
from .base import detect_markers, xy, yx


@dataclass(frozen=True)
class ViewSpec:
    labels: dict[str, str]
    expected_markers: int
    assign: Callable[[list[np.ndarray]], dict[str, np.ndarray]]
    evaluate: Callable[[dict[str, np.ndarray], float, AssessmentConfig], Evaluation]


SPECS: dict[View, ViewSpec] = {
    View.ANTERIOR: ViewSpec(anterior.LABELS, anterior.EXPECTED_MARKERS, anterior.assign, anterior.evaluate),
    View.POSTERIOR: ViewSpec(posterior.LABELS, posterior.EXPECTED_MARKERS, posterior.assign, posterior.evaluate),
    View.LATERAL_DERECHA: ViewSpec(lateral.LABELS, lateral.EXPECTED_MARKERS, lateral.assign_right,
                                   lateral.evaluate_right),
    View.LATERAL_IZQUIERDA: ViewSpec(lateral.LABELS, lateral.EXPECTED_MARKERS, lateral.assign_left,
                                     lateral.evaluate_left),
}


def _result(view: View, points: dict[str, np.ndarray], scale: float, config: AssessmentConfig,
            image: np.ndarray | None, references=None) -> ViewResult:
    spec = SPECS[view]
    ev = spec.evaluate(points, scale, config)
    return ViewResult(
        view=view,
        markers={k: xy(points[k]) for k in spec.labels},
        derived_points={k: xy(v) for k, v in ev.derived_points.items()},
        references=references,
        scale_ratio=scale,
        grid_origin=xy(ev.grid_origin),
        grid_step_px=config.grid_size / scale,  # cm de la cuadrícula / (cm por píxel)
        diagnostic=ev.diagnostic,
        tables=ev.tables,
        image=image,
    )


def analyze(view: View, image: np.ndarray, config: AssessmentConfig) -> ViewResult:
    """Detecta los marcadores verdes en la fotografía y evalúa la vista."""
    view = View(view)
    spec = SPECS[view]
    det = detect_markers(view, image, config, spec.expected_markers)
    return _result(view, spec.assign(det.points), det.scale_ratio, config, det.image,
                   (xy(det.reference_1), xy(det.reference_2)))


def evaluate_landmarks(view: View, landmarks: Mapping[str, tuple[float, float]], scale_ratio: float,
                       config: AssessmentConfig, image: np.ndarray | None = None) -> ViewResult:
    """Evalúa una vista a partir de puntos (x, y) en píxeles y la escala en cm/píxel."""
    if scale_ratio <= 0:
        raise ValueError("La escala debe ser mayor que cero")
    view = View(view)
    points = {k: yx(v) for k, v in landmarks.items()}
    return _result(view, points, scale_ratio, config, image)
