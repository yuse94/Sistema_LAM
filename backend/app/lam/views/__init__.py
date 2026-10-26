"""Análisis por vista fotográfica.

- analyze(): detección con marcadores verdes + evaluación (flujo de la tesis).
- analyze_pose(): modo sin marcadores, a partir de los puntos de MediaPipe y la estatura.
- evaluate_landmarks(): evaluación a partir de puntos ya ubicados, por ejemplo
  después de que el evaluador los ajustó en la interfaz.
"""
from __future__ import annotations

import math
from collections.abc import Callable, Mapping
from dataclasses import dataclass

import numpy as np

from ..level import height_scale, level_points, roll_from_vertical, rotate
from ..pose import Calibration, PosePoint, estimate_calibration, landmarks_from_pose
from ..types import AssessmentConfig, Evaluation, View, ViewResult
from . import anterior, lateral, posterior
from .base import detect_markers, xy, yx

Point = tuple[float, float]


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


def evaluate_landmarks(view: View, landmarks: Mapping[str, Point], scale_ratio: float,
                       config: AssessmentConfig, image: np.ndarray | None = None,
                       vertical_line: tuple[Point, Point] | None = None) -> ViewResult:
    """Evalúa una vista a partir de puntos (x, y) en píxeles y la escala en cm/píxel.

    Con vertical_line (dos puntos sobre algo vertical en la escena) los puntos se
    nivelan antes de evaluar. Los puntos devueltos siguen en coordenadas de la imagen.
    """
    if scale_ratio <= 0:
        raise ValueError("La escala debe ser mayor que cero")
    view = View(view)
    if not vertical_line:
        return _result(view, {k: yx(v) for k, v in landmarks.items()}, scale_ratio, config, image)

    angle, center = roll_from_vertical(*vertical_line), vertical_line[0]
    leveled = level_points(landmarks, angle, center)
    result = _result(view, {k: yx(v) for k, v in leveled.items()}, scale_ratio, config, image)
    back = lambda p: rotate(p, -angle, center)  # noqa: E731
    result.markers = {k: (float(landmarks[k][0]), float(landmarks[k][1])) for k in result.markers}
    result.derived_points = {k: back(v) for k, v in result.derived_points.items()}
    result.grid_origin = back(result.grid_origin)
    result.roll_deg = math.degrees(angle)
    return result


@dataclass
class PoseAnalysis:
    result: ViewResult
    estimated: list[str]  # puntos sin equivalente en MediaPipe, a revisar por el evaluador
    calibration: Calibration


def analyze_pose(view: View, pose: list[PosePoint], height_cm: float, config: AssessmentConfig,
                 calibration: Calibration | None = None,
                 vertical_line: tuple[Point, Point] | None = None) -> PoseAnalysis:
    """Modo sin marcadores: puntos de MediaPipe -> puntos LAM -> evaluación.

    calibration (vértice y suelo) normalmente viene de la silueta detectada en el
    navegador; si falta, se estima desde la cara y los pies.
    """
    if vertical_line:
        # Los puntos estimados se ubican con direcciones "arriba/abajo" del cuerpo: se
        # estiman sobre la pose nivelada y luego se devuelven a coordenadas de la imagen.
        angle, center = roll_from_vertical(*vertical_line), vertical_line[0]
        leveled = [PosePoint(*rotate((p.x, p.y), angle, center), p.visibility) for p in pose]
        mapped = landmarks_from_pose(view, leveled)
        mapped.landmarks = {k: rotate(v, -angle, center) for k, v in mapped.landmarks.items()}
        if calibration is None:
            est = estimate_calibration(leveled)
            calibration = Calibration(rotate(est.vertex, -angle, center), rotate(est.floor, -angle, center))
    else:
        mapped = landmarks_from_pose(view, pose)
        calibration = calibration or estimate_calibration(pose)
    scale = height_scale(height_cm, calibration.vertex, calibration.floor, vertical_line)
    result = evaluate_landmarks(view, mapped.landmarks, scale, config, vertical_line=vertical_line)
    return PoseAnalysis(result, mapped.estimated, calibration)
