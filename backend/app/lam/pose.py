"""Puntos LAM a partir de la estimación de pose de MediaPipe (modo sin marcadores).

MediaPipe Pose Landmarker devuelve 33 puntos (centros articulares y rasgos de la
cara). Varios puntos de LAM no existen en el modelo (EIAS, EIPS, C7, T5, ombligo,
manubrio, mentón, entrecejo, tuberosidad tibial, tarso); se estiman por proporciones corporales y se marcan
como "estimados" para que el fisioterapeuta los revise y arrastre.

Decisiones:
- Los pares izquierdo/derecho se asignan por su posición en la imagen, no por la
  etiqueta de MediaPipe, que a veces se invierte cuando el paciente está de espaldas.
- Los desplazamientos se ajustaron con fotos de validación con marcadores (error medio
  1.9 cm en validación cruzada); siguen siendo estimaciones y el evaluador debe revisar
  los puntos marcados como estimados.

Coordenadas en píxeles de la imagen: (x, y), con y hacia abajo.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from .types import View

Point = tuple[float, float]

# Índices de MediaPipe Pose Landmarker
NOSE = 0
LEFT_EYE, RIGHT_EYE = 2, 5
LEFT_EAR, RIGHT_EAR = 7, 8
MOUTH_LEFT, MOUTH_RIGHT = 9, 10
LEFT_SHOULDER, RIGHT_SHOULDER = 11, 12
LEFT_HIP, RIGHT_HIP = 23, 24
LEFT_KNEE, RIGHT_KNEE = 25, 26
LEFT_ANKLE, RIGHT_ANKLE = 27, 28
LEFT_HEEL, RIGHT_HEEL = 29, 30
LEFT_FOOT, RIGHT_FOOT = 31, 32
N_LANDMARKS = 33


@dataclass(frozen=True)
class PosePoint:
    x: float
    y: float
    visibility: float = 1.0


@dataclass
class PoseLandmarks:
    landmarks: dict[str, Point]  # punto LAM -> (x, y)
    estimated: list[str]  # puntos sin equivalente en el modelo: el evaluador debe revisarlos


@dataclass
class Calibration:
    vertex: Point  # parte superior de la cabeza
    floor: Point  # apoyo de los talones


# ---------------------------------------------------------------- utilidades

def _p(pose: list[PosePoint], i: int) -> Point:
    return pose[i].x, pose[i].y


def _mid(a: Point, b: Point) -> Point:
    return (a[0] + b[0]) / 2, (a[1] + b[1]) / 2


def _add(a: Point, dx: float = 0.0, dy: float = 0.0) -> Point:
    return a[0] + dx, a[1] + dy


def _lerp(a: Point, b: Point, t: float) -> Point:
    return a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t


def _dist(a: Point, b: Point) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def _by_x(pose: list[PosePoint], i: int, j: int) -> tuple[Point, Point]:
    """Par de puntos ordenado de izquierda a derecha en la imagen."""
    a, b = _p(pose, i), _p(pose, j)
    return (a, b) if a[0] <= b[0] else (b, a)


def _validate(pose: list[PosePoint]) -> None:
    if len(pose) != N_LANDMARKS:
        raise ValueError(f"Se esperaban {N_LANDMARKS} puntos de MediaPipe y llegaron {len(pose)}")


# ---------------------------------------------------------------- vistas
#
# Desplazamientos ajustados con las fotos de validación (10 adultos, 30 fotos con
# marcadores; ver docs/VALIDACION.md). Cada punto es: ancla de MediaPipe + (cx · Sx, cy · Sy).
# - Vistas frontales: Sx = ancho de hombros y Sy = largo del tronco (hombros → caderas).
#   En los pares, cx positivo = hacia afuera del cuerpo; los dos lados usan el mismo valor
#   en espejo para que un paciente simétrico siga saliendo alineado.
# - Vista lateral: Sx = Sy = largo del muslo; cx positivo = hacia adelante.
# Los puntos de la línea media usan cx = 0. Los puntos sin corrección (F1, F6, F11–F14, L5)
# no mejoraban con el ajuste en la validación cruzada (dejando una persona fuera).

def _shift(anchor: Point, cx: float, cy: float, sx: float, sy: float, outward: int = 1) -> Point:
    return anchor[0] + outward * cx * sx, anchor[1] + cy * sy


def _anterior(pose: list[PosePoint]) -> PoseLandmarks:
    # De frente, el lado derecho del paciente queda a la izquierda de la imagen.
    eye_mid = _mid(_p(pose, LEFT_EYE), _p(pose, RIGHT_EYE))
    mouth_mid = _mid(_p(pose, MOUTH_LEFT), _p(pose, MOUTH_RIGHT))
    face = max(mouth_mid[1] - eye_mid[1], 1.0)

    sh_r, sh_l = _by_x(pose, LEFT_SHOULDER, RIGHT_SHOULDER)  # derecho del paciente = izquierda de la imagen
    hip_r, hip_l = _by_x(pose, LEFT_HIP, RIGHT_HIP)
    sh_mid, hip_mid = _mid(sh_r, sh_l), _mid(hip_r, hip_l)
    w = max(abs(sh_l[0] - sh_r[0]), 1.0)
    t = max(hip_mid[1] - sh_mid[1], 1.0)

    knee_r, knee_l = _by_x(pose, LEFT_KNEE, RIGHT_KNEE)
    f11, f12 = _by_x(pose, LEFT_ANKLE, RIGHT_ANKLE)
    f13, f14 = _by_x(pose, LEFT_FOOT, RIGHT_FOOT)

    landmarks = {
        "F1": _add(eye_mid, dy=-0.35 * face),  # entrecejo
        "F2": _shift(mouth_mid, 0, 0.091, w, t),  # mentón
        "F3": _shift(sh_r, 0.081, -0.083, w, t, -1),  # acromioclavicular: más arriba y afuera que el hombro
        "F4": _shift(sh_l, 0.081, -0.083, w, t, +1),
        "F5": _shift(sh_mid, 0, -0.051, w, t),  # horquilla esternal
        "F6": _lerp(sh_mid, hip_mid, 0.72),  # ombligo
        "F7": _shift(hip_r, 0.086, -0.189, w, t, -1),  # EIAS: por encima y afuera del centro de la cadera
        "F8": _shift(hip_l, 0.086, -0.189, w, t, +1),
        "F9": _shift(knee_r, 0.012, -0.038, w, t, -1),  # rótula
        "F10": _shift(knee_l, 0.012, -0.038, w, t, +1),
        "F11": f11, "F12": f12, "F13": f13, "F14": f14,
    }
    return PoseLandmarks(landmarks, ["F1", "F2", "F5", "F6", "F7", "F8"])


def _posterior(pose: list[PosePoint]) -> PoseLandmarks:
    # De espaldas, el lado izquierdo del paciente queda a la izquierda de la imagen.
    sh_l, sh_r = _by_x(pose, LEFT_SHOULDER, RIGHT_SHOULDER)
    hip_l, hip_r = _by_x(pose, LEFT_HIP, RIGHT_HIP)
    sh_mid, hip_mid = _mid(sh_l, sh_r), _mid(hip_l, hip_r)
    w = max(abs(sh_r[0] - sh_l[0]), 1.0)
    t = max(hip_mid[1] - sh_mid[1], 1.0)

    knee_l, knee_r = _by_x(pose, LEFT_KNEE, RIGHT_KNEE)
    ankle_l, ankle_r = _by_x(pose, LEFT_ANKLE, RIGHT_ANKLE)
    heel_l, heel_r = _by_x(pose, LEFT_HEEL, RIGHT_HEEL)

    landmarks = {
        "P1": _shift(sh_mid, 0, -0.174, w, t),  # C7
        "P2": _shift(sh_mid, 0, 0.096, w, t),  # T5
        "P3": _shift(sh_r, 0.063, -0.077, w, t, +1),  # acromioclavicular
        "P4": _shift(sh_l, 0.063, -0.077, w, t, -1),
        "P5": _shift(hip_r, -0.134, -0.248, w, t, +1),  # EIPS: por encima y hacia la línea media
        "P6": _shift(hip_l, -0.134, -0.248, w, t, -1),
        "P7": _shift(knee_r, -0.018, 0.025, w, t, +1),  # hueco poplíteo
        "P8": _shift(knee_l, -0.018, 0.025, w, t, -1),
        "P9": _shift(ankle_r, -0.034, 0.044, w, t, +1),  # tendón de Aquiles
        "P10": _shift(ankle_l, -0.034, 0.044, w, t, -1),
        "P11": _shift(heel_r, -0.008, 0.052, w, t, +1),  # calcáneo
        "P12": _shift(heel_l, -0.008, 0.052, w, t, -1),
    }
    return PoseLandmarks(landmarks, ["P1", "P2", "P5", "P6"])


_SIDES = {
    "right": (RIGHT_EAR, RIGHT_SHOULDER, RIGHT_HIP, RIGHT_KNEE, RIGHT_ANKLE, RIGHT_HEEL, RIGHT_FOOT),
    "left": (LEFT_EAR, LEFT_SHOULDER, LEFT_HIP, LEFT_KNEE, LEFT_ANKLE, LEFT_HEEL, LEFT_FOOT),
}


def _visible_side(pose: list[PosePoint], default: str) -> str:
    """Lado del cuerpo más visible (el que está hacia la cámara)."""
    score = {side: sum(pose[i].visibility for i in idx) for side, idx in _SIDES.items()}
    other = "left" if default == "right" else "right"
    return other if score[other] > score[default] + 0.5 else default


def _lateral(pose: list[PosePoint], forward: int, default_side: str) -> PoseLandmarks:
    """forward = +1 si el paciente mira a la derecha de la imagen, -1 si mira a la izquierda."""
    ear, shoulder, hip, knee, ankle, _heel, _foot = (_p(pose, i) for i in _SIDES[_visible_side(pose, default_side)])
    th = max(_dist(hip, knee), 1.0)  # largo del muslo

    landmarks = {
        "L1": _shift(ear, -0.076, 0.007, th, th, forward),  # trago: algo por detrás del punto de la oreja
        "L2": _shift(shoulder, 0.016, -0.141, th, th, forward),  # acromioclavicular
        "L3": _shift(hip, 0.232, -0.228, th, th, forward),  # EIAS
        "L4": _shift(hip, -0.266, -0.322, th, th, forward),  # EIPS
        "L5": hip,  # trocánter mayor
        "L6": _shift(knee, -0.004, 0.025, th, th, forward),  # tuberosidad tibial
        "L7": _shift(ankle, -0.017, 0.222, th, th, forward),  # articulación transversal del tarso
    }
    return PoseLandmarks(landmarks, ["L3", "L4", "L6", "L7"])


def landmarks_from_pose(view: View, pose: list[PosePoint]) -> PoseLandmarks:
    _validate(pose)
    view = View(view)
    if view is View.ANTERIOR:
        return _anterior(pose)
    if view is View.POSTERIOR:
        return _posterior(pose)
    if view is View.LATERAL_DERECHA:
        return _lateral(pose, forward=1, default_side="right")
    return _lateral(pose, forward=-1, default_side="left")


def estimate_calibration(pose: list[PosePoint]) -> Calibration:
    """Vértice y suelo aproximados, para cuando la silueta no está disponible.

    El vértice se estima desde los ojos: la distancia ojos-boca es ~0.27 de la altura
    de la cabeza y los ojos están a media altura, por lo que el vértice queda a
    ~1.9 veces esa distancia sobre los ojos.
    """
    _validate(pose)
    eyes = [_p(pose, LEFT_EYE), _p(pose, RIGHT_EYE)]
    eye_mid = _mid(*eyes)
    mouth_mid = _mid(_p(pose, MOUTH_LEFT), _p(pose, MOUTH_RIGHT))
    face = max(mouth_mid[1] - eye_mid[1], 1.0)
    vertex = (eye_mid[0], eye_mid[1] - 1.9 * face)

    feet = [_p(pose, i) for i in (LEFT_HEEL, RIGHT_HEEL, LEFT_FOOT, RIGHT_FOOT)]
    heels = _mid(_p(pose, LEFT_HEEL), _p(pose, RIGHT_HEEL))
    floor = (heels[0], max(p[1] for p in feet))
    return Calibration(vertex, floor)
