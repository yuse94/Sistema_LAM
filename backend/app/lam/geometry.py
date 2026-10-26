"""Funciones de evaluación (ángulos y distancias).

Portado sin cambios de lógica desde functions_for_assessment.py.
Los puntos son arrays numpy (y, x) en píxeles.
"""
from __future__ import annotations

from numpy import angle


def anterior_angle_from_horizontal(right_point, left_point, tolerance):
    d = left_point - right_point
    a = round(-angle(complex(d[1], d[0]), deg=True), 2)
    if a > tolerance:
        return "Der.", a
    if a < -tolerance:
        return "Izq.", a
    return "Alin.", a


def posterior_angle_from_horizontal(left_point, right_point, tolerance):
    d = right_point - left_point
    a = round(-angle(complex(d[1], d[0]), deg=True), 2)
    # HALLAZGO-2 (corregido): en la versión de consola las condiciones eran
    # `a < tol` y `a > -tol`, por lo que "Alin." nunca se alcanzaba.
    # En la foto posterior un ángulo negativo indica el lado derecho descendido.
    if a < -tolerance:
        return "Der.", a
    if a > tolerance:
        return "Izq.", a
    return "Alin.", a


def angle_from_vertical(first_point, second_point, tolerance):
    d = first_point - second_point
    a = round(90 - abs(angle(complex(d[1], d[0]), deg=True)), 2)
    if a < -tolerance:
        return "Izq.", a
    if a > tolerance:
        return "Der.", a
    return "Alin.", a


def lateral_angle_from_vertical(top_point, bottom_point, tolerance):
    d = top_point - bottom_point
    a = round(90 - abs(angle(complex(d[1], d[0]), deg=True)), 2)
    if a < -tolerance:
        return "Pos.", a
    if a > tolerance:
        return "Ant.", a
    return "Alin.", a


def lateral_angle_from_horizontal(posterior_point, anterior_point):
    d = posterior_point - anterior_point
    a = round(180 - abs(angle(complex(d[1], d[0]), deg=True)), 2)
    if a > 15:
        return "Ant.", a
    if a < 5:
        return "Pos.", a
    return "Normal", a


def _classify_distance(distance, tolerance, positive, negative):
    distance = round(distance, 2)
    if distance > tolerance:
        return positive, distance
    if distance < -tolerance:
        return negative, distance
    return "Alin.", distance


def anterior_distance_from_vertical(center_point, reference_point, scale, tolerance):
    return _classify_distance((center_point[1] - reference_point[1]) * scale, tolerance, "Der.", "Izq.")


def posterior_distance_from_vertical(center_point, reference_point, scale, tolerance):
    return _classify_distance((reference_point[1] - center_point[1]) * scale, tolerance, "Der.", "Izq.")


def lateral_distance_from_vertical(center_point, reference_point, scale, tolerance):
    return _classify_distance((reference_point[1] - center_point[1]) * scale, tolerance, "Ant.", "Pos.")


def anterior_rotation(first_point, second_point, tolerance):
    d = first_point - second_point
    a = round(abs(angle(complex(d[1], d[0]), deg=True)) - 90, 2)
    if a > tolerance:
        return "Rot.Ext.", a
    if a < -tolerance:
        return "Rot.Int.", a
    return "Alin.", a


def valgus_or_varus(first_point, second_point, tolerance):
    d = first_point - second_point
    a = round(90 - abs(angle(complex(d[1], d[0]), deg=True)), 2)
    if a > tolerance:
        return "Valgo", a
    if a < -tolerance:
        return "Varo", a
    return "Alin.", a
