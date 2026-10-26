"""Nivelación con una línea vertical de referencia y escala por estatura.

Sin los marcadores R1/R2 la imagen ya no se endereza sola. El evaluador marca dos
puntos sobre algo que sabe que es vertical (marco de puerta, esquina de pared,
plomada) y los puntos anatómicos se rotan para que esa línea quede vertical antes
de evaluar. Un giro de la cámara de θ grados se sumaría, sin esta corrección, a
todos los ángulos respecto a la horizontal y a la vertical.

Coordenadas en píxeles de la imagen: (x, y), con y hacia abajo.
"""
from __future__ import annotations

import math
from collections.abc import Mapping

Point = tuple[float, float]

MAX_ROLL_DEG = 20.0  # una inclinación mayor indica una línea mal marcada


def roll_from_vertical(top: Point, bottom: Point) -> float:
    """Ángulo (radianes) entre la línea de referencia y la vertical de la imagen.

    Positivo cuando la parte baja de la línea queda a la derecha de la alta.
    """
    dx, dy = bottom[0] - top[0], bottom[1] - top[1]
    if math.hypot(dx, dy) < 1e-6:
        raise ValueError("Los dos puntos de la línea vertical no pueden coincidir")
    if dy < 0:  # el usuario marcó primero el punto inferior
        dx, dy = -dx, -dy
    roll = math.atan2(dx, dy)
    if abs(math.degrees(roll)) > MAX_ROLL_DEG:
        raise ValueError(f"La línea vertical está inclinada más de {MAX_ROLL_DEG:.0f}°; revísela")
    return roll


def rotate(p: Point, angle: float, center: Point) -> Point:
    """Rota un punto alrededor de center (en coordenadas de imagen, y hacia abajo)."""
    c, s = math.cos(angle), math.sin(angle)
    x, y = p[0] - center[0], p[1] - center[1]
    return center[0] + x * c - y * s, center[1] + x * s + y * c


def level_points(points: Mapping[str, Point], angle: float, center: Point) -> dict[str, Point]:
    return {k: rotate(p, angle, center) for k, p in points.items()}


def scale_from_height(height_cm: float, vertex: Point, floor: Point) -> float:
    """Centímetros por píxel a partir de la estatura del paciente.

    vertex: parte superior de la cabeza; floor: apoyo de los talones en el suelo.
    Los puntos deben estar ya nivelados: se usa solo la distancia vertical.
    """
    if not 50 <= height_cm <= 250:
        raise ValueError("La estatura debe estar entre 50 y 250 cm")
    height_px = floor[1] - vertex[1]
    if height_px <= 0:
        raise ValueError("El punto del suelo debe estar por debajo del vértice de la cabeza")
    return height_cm / height_px


def height_scale(height_cm: float, vertex: Point, floor: Point,
                 vertical_line: tuple[Point, Point] | None = None) -> float:
    """Escala por estatura, nivelando antes el vértice y el suelo si hay línea vertical."""
    if vertical_line:
        angle, center = roll_from_vertical(*vertical_line), vertical_line[0]
        vertex, floor = rotate(vertex, angle, center), rotate(floor, angle, center)
    return scale_from_height(height_cm, vertex, floor)
