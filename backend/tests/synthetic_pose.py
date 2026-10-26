"""Poses sintéticas con el formato de MediaPipe (33 puntos en píxeles).

Paciente de pie, simétrico: vértice en y=100 y suelo en y=1800 (1700 px = 170 cm).
"""
import math

from app.lam import PosePoint
from app.lam import pose as mp

CX = 500.0  # eje vertical del cuerpo en las vistas frontales

# (dx desde el eje, y) del lado derecho del paciente en la vista ANTERIOR
# (el lado derecho del paciente queda a la izquierda de la imagen: dx negativo).
_FRONT_RIGHT = {
    "eye": (-30, 260), "ear": (-70, 270), "mouth": (-25, 330), "shoulder": (-190, 460),
    "elbow": (-210, 760), "wrist": (-220, 1000), "pinky": (-225, 1050), "index": (-220, 1060),
    "thumb": (-205, 1040), "hip": (-110, 950), "knee": (-100, 1380), "ankle": (-95, 1740),
    "heel": (-95, 1790), "foot": (-115, 1800),
}

_INDEX = {  # (índice izquierdo, índice derecho) en MediaPipe
    "eye": (2, 5), "ear": (7, 8), "mouth": (9, 10), "shoulder": (11, 12), "elbow": (13, 14),
    "wrist": (15, 16), "pinky": (17, 18), "index": (19, 20), "thumb": (21, 22), "hip": (23, 24),
    "knee": (25, 26), "ankle": (27, 28), "heel": (29, 30), "foot": (31, 32),
}


def frontal_pose(facing_camera: bool = True) -> list[PosePoint]:
    """Vista anterior (facing_camera) o posterior: en la posterior los lados se invierten."""
    pts = [PosePoint(CX, 300.0)] * 33
    pts = list(pts)
    pts[1] = pts[4] = pts[3] = pts[6] = PosePoint(CX, 260.0)  # ojos internos/externos
    pts[mp.NOSE] = PosePoint(CX, 300.0)
    sign = 1 if facing_camera else -1
    for name, (dx, y) in _FRONT_RIGHT.items():
        left_i, right_i = _INDEX[name]
        pts[right_i] = PosePoint(CX + sign * dx, y)
        pts[left_i] = PosePoint(CX - sign * dx, y)
    return pts


def lateral_pose(facing_right: bool = True) -> list[PosePoint]:
    """Vista lateral; el lado hacia la cámara tiene visibilidad 1 y el otro 0.2."""
    s = 1 if facing_right else -1
    near = {"ear": (0, 270), "eye": (40, 260), "mouth": (45, 330), "shoulder": (0, 460), "elbow": (5, 760),
            "wrist": (10, 1000), "pinky": (10, 1050), "index": (15, 1060), "thumb": (15, 1040),
            "hip": (0, 950), "knee": (0, 1380), "ankle": (0, 1740), "heel": (-30, 1790), "foot": (110, 1800)}
    pts = [PosePoint(CX, 300.0, 0.2) for _ in range(33)]
    pts[mp.NOSE] = PosePoint(CX + s * 60, 300.0)
    for name, (dx, y) in near.items():
        left_i, right_i = _INDEX[name]
        near_i, far_i = (right_i, left_i) if facing_right else (left_i, right_i)
        pts[near_i] = PosePoint(CX + s * dx, y, 1.0)
        pts[far_i] = PosePoint(CX + s * dx + s * 5, y, 0.2)
    return pts


def rotate_pose(pose, degrees, center=(CX, 1000.0)):
    a = math.radians(degrees)
    c, s = math.cos(a), math.sin(a)
    out = []
    for p in pose:
        x, y = p.x - center[0], p.y - center[1]
        out.append(PosePoint(center[0] + x * c - y * s, center[1] + x * s + y * c, p.visibility))
    return out


def rotate_point(p, degrees, center=(CX, 1000.0)):
    q = rotate_pose([PosePoint(*p)], degrees, center)[0]
    return q.x, q.y
