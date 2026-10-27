"""Puntos LAM a partir de la estimación de pose de MediaPipe (modo sin marcadores).

MediaPipe Pose Landmarker devuelve 33 puntos (centros articulares y rasgos de la
cara). Varios puntos de LAM no existen en el modelo (EIAS, EIPS, C7, T5, ombligo,
manubrio, mentón, entrecejo, tuberosidad tibial); se estiman por proporciones corporales y se marcan
como "estimados" para que el fisioterapeuta los revise y arrastre.

Decisiones:
- Los pares izquierdo/derecho se asignan por su posición en la imagen, no por la
  etiqueta de MediaPipe, que a veces se invierte cuando el paciente está de espaldas.
- Las proporciones son aproximaciones iniciales, no mediciones: el objetivo es que el
  punto aparezca cerca del lugar correcto para que el ajuste manual sea corto.

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

def _anterior(pose: list[PosePoint]) -> PoseLandmarks:
    # De frente, el lado derecho del paciente queda a la izquierda de la imagen.
    eye_mid = _mid(_p(pose, LEFT_EYE), _p(pose, RIGHT_EYE))
    mouth_mid = _mid(_p(pose, MOUTH_LEFT), _p(pose, MOUTH_RIGHT))
    nose = _p(pose, NOSE)
    face = max(mouth_mid[1] - eye_mid[1], 1.0)

    f3, f4 = _by_x(pose, LEFT_SHOULDER, RIGHT_SHOULDER)
    hip_r, hip_l = _by_x(pose, LEFT_HIP, RIGHT_HIP)
    sh_mid, hip_mid = _mid(f3, f4), _mid(hip_r, hip_l)
    shoulder_width = abs(f4[0] - f3[0])
    trunk = hip_mid[1] - sh_mid[1]

    f9, f10 = _by_x(pose, LEFT_KNEE, RIGHT_KNEE)
    f11, f12 = _by_x(pose, LEFT_ANKLE, RIGHT_ANKLE)
    f13, f14 = _by_x(pose, LEFT_FOOT, RIGHT_FOOT)

    landmarks = {
        "F1": _add(eye_mid, dy=-0.35 * face),  # entrecejo: algo sobre la línea de los ojos
        "F2": _lerp(nose, mouth_mid, 2.5),  # mentón: debajo de la boca
        "F3": f3, "F4": f4,
        "F5": _add(sh_mid, dy=0.10 * shoulder_width),  # horquilla esternal
        "F6": _lerp(sh_mid, hip_mid, 0.72),  # ombligo
        "F7": _add(hip_r, dy=-0.12 * trunk),  # EIAS: por encima del centro de la cadera
        "F8": _add(hip_l, dy=-0.12 * trunk),
        "F9": f9, "F10": f10, "F11": f11, "F12": f12, "F13": f13, "F14": f14,
    }
    return PoseLandmarks(landmarks, ["F1", "F2", "F5", "F6", "F7", "F8"])


def _posterior(pose: list[PosePoint]) -> PoseLandmarks:
    # De espaldas, el lado izquierdo del paciente queda a la izquierda de la imagen.
    p4, p3 = _by_x(pose, LEFT_SHOULDER, RIGHT_SHOULDER)
    hip_l, hip_r = _by_x(pose, LEFT_HIP, RIGHT_HIP)
    sh_mid, hip_mid = _mid(p4, p3), _mid(hip_l, hip_r)
    shoulder_width = abs(p3[0] - p4[0])
    trunk = hip_mid[1] - sh_mid[1]

    p8, p7 = _by_x(pose, LEFT_KNEE, RIGHT_KNEE)
    p10, p9 = _by_x(pose, LEFT_ANKLE, RIGHT_ANKLE)
    p12, p11 = _by_x(pose, LEFT_HEEL, RIGHT_HEEL)

    landmarks = {
        "P1": _add(sh_mid, dy=-0.10 * shoulder_width),  # C7: algo sobre la línea de hombros
        "P2": _lerp(sh_mid, hip_mid, 0.25),  # T5
        "P3": p3, "P4": p4,
        # EIPS: hoyuelos sacros, más cerca de la línea media que el centro de la cadera
        "P5": _add(_lerp(hip_mid, hip_r, 0.35), dy=-0.12 * trunk),
        "P6": _add(_lerp(hip_mid, hip_l, 0.35), dy=-0.12 * trunk),
        "P7": p7, "P8": p8, "P9": p9, "P10": p10, "P11": p11, "P12": p12,
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
    thigh = max(_dist(hip, knee), 1.0)

    pelvis = _add(hip, dy=-0.22 * thigh)  # centro entre EIAS y EIPS, sobre el trocánter
    landmarks = {
        "L1": ear,
        "L2": shoulder,
        # Con ±0.17 y -0.06 la pelvis queda con ~10° de inclinación (valor normal)
        "L3": _add(pelvis, dx=forward * 0.17 * thigh),  # EIAS
        "L4": _add(pelvis, dx=-forward * 0.17 * thigh, dy=-0.06 * thigh),  # EIPS
        "L5": hip,  # trocánter mayor (aprox. centro de la cadera del modelo)
        "L6": _add(_lerp(knee, ankle, 0.12), dx=forward * 0.04 * thigh),  # tuberosidad tibial
        "L7": ankle,  # maléolo externo: el tobillo de MediaPipe está a su altura
    }
    return PoseLandmarks(landmarks, ["L3", "L4", "L6"])


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
