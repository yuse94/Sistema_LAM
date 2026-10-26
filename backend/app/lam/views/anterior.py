"""Vista anterior del plano frontal (14 puntos, F1-F14)."""
from __future__ import annotations

import numpy as np

from .. import geometry as g
from ..types import AssessmentConfig, Evaluation
from .base import center, require, sort_by_x, table

EXPECTED_MARKERS = 14
LABELS = {
    "F1": "Entrecejo", "F2": "Mentón", "F3": "Acromioclavicular derecha",
    "F4": "Acromioclavicular izquierda", "F5": "Horquilla del manubrio esternal",
    "F6": "Ombligo", "F7": "EIAS derecha", "F8": "EIAS izquierda", "F9": "Rótula derecha",
    "F10": "Rótula izquierda", "F11": "Tobillo derecho", "F12": "Tobillo izquierdo",
    "F13": "Dedo gordo derecho", "F14": "Dedo gordo izquierdo",
}


def assign(p: list[np.ndarray]) -> dict[str, np.ndarray]:
    """Asigna los marcadores verdes (orden de arriba hacia abajo) a cada punto anatómico.

    En la foto anterior el lado derecho del paciente queda a la izquierda de la imagen.
    """
    f3, f5, f4 = sort_by_x(p[2:5])
    f7, f6, f8 = sort_by_x(p[5:8])
    f9, f10 = sort_by_x(p[8:10])
    f11, f12 = sort_by_x(p[10:12])
    f13, f14 = sort_by_x(p[12:14])
    return dict(zip(LABELS, (p[0], p[1], f3, f4, f5, f6, f7, f8, f9, f10, f11, f12, f13, f14)))


def evaluate(pts: dict[str, np.ndarray], scale: float, config: AssessmentConfig) -> Evaluation:
    require(pts, LABELS)
    f1, f2, f3, f4, f5, f6, f7, f8, f9, f10, f11, f12, f13, f14 = (pts[k] for k in LABELS)
    ta, td = config.tolerance_angle, config.tolerance_distance

    c_shoulders = center(f3, f4)
    c_pelvis = center(f7, f8)  # centro Y de la cuadrícula
    c_knees = center(f9, f10)
    c_ankles = center(f11, f12)  # centro X de la cuadrícula
    c_feet = center(f13, f14)

    t1 = table("table_1", "Grados con respecto a la horizontal", ("Segmento Corporal", "Descendido", "Ángulo"),
               ("Hombros", "Pelvis", "Rodillas"),
               [g.anterior_angle_from_horizontal(f3, f4, ta),
                g.anterior_angle_from_horizontal(f7, f8, ta),
                g.anterior_angle_from_horizontal(f9, f10, ta)])
    t2 = table("table_2", "Distancia con respecto a la vertical", ("Referencia", "Dirección", "Distancia"),
               ("Frente", "Hombros", "Ombligo", "Pelvis", "Rodillas", "Pies"),
               [g.anterior_distance_from_vertical(c_ankles, ref, scale, td)
                for ref in (f1, c_shoulders, f6, c_pelvis, c_knees, c_feet)])
    t3 = table("table_3", "Grados de rotación de los pies", ("Segmento Corporal", "Dirección", "Ángulo"),
               ("Pie Izquierdo", "Pie Derecho"),
               [g.anterior_rotation(f12, f14, ta), g.anterior_rotation(f13, f11, ta)])

    head_tilt, head_angle = g.angle_from_vertical(f1, f2, ta)
    head_rot, _ = g.angle_from_vertical(f2, f5, ta)
    right_knee_dir, right_knee_angle = g.valgus_or_varus(f9, f11, ta)
    left_knee_dir, left_knee_angle = g.valgus_or_varus(f12, f10, ta)

    diagnostic = {
        "linea_escapular_descendida": t1.rows[0].direction,
        "linea_pelvica_descendida": t1.rows[1].direction,
        "cabeza_inclinada": "N/A" if head_tilt == "Alin." else head_tilt,
        "cabeza_inclinada_angulo": float(head_angle),
        "cabeza_rotada": "N/A" if head_rot == "Alin." else head_rot,
        "rodilla_derecha": right_knee_dir,
        "rodilla_derecha_angulo": float(right_knee_angle),
        "rodilla_izquierda": left_knee_dir,
        "rodilla_izquierda_angulo": float(left_knee_angle),
    }

    return Evaluation(
        derived_points={"centro_hombros": c_shoulders, "centro_pelvis": c_pelvis, "centro_rodillas": c_knees,
                        "centro_tobillos": c_ankles, "centro_pies": c_feet},
        grid_origin=np.array([c_pelvis[0], c_ankles[1]]),
        diagnostic=diagnostic,
        tables=[t1, t2, t3],
    )
