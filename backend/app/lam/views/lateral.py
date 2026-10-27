"""Vistas laterales del plano sagital (7 puntos, L1-L7).

La vista lateral derecha es la de la tesis: el paciente mira hacia la derecha de
la imagen. La lateral izquierda se evalúa reflejando horizontalmente los puntos,
con lo que las mismas reglas (Ant./Pos.) siguen siendo válidas.
"""
from __future__ import annotations

import numpy as np

from .. import geometry as g
from ..types import AssessmentConfig, Evaluation
from .base import center, require, sort_by_x, table

EXPECTED_MARKERS = 7
LABELS = {
    "L1": "Oído", "L2": "Acromioclavicular", "L3": "EIAS", "L4": "EIPS",
    "L5": "Trocánter mayor", "L6": "Tuberosidad tibial", "L7": "Articulación transversal del tarso",
}


def assign_right(p: list[np.ndarray]) -> dict[str, np.ndarray]:
    """Lateral derecha: el paciente mira a la derecha; la EIPS (L4) queda a la izquierda de la imagen.

    L3 = EIAS y L4 = EIPS según la Tabla 2.1 de la tesis (la versión de consola los nombraba al revés).
    """
    l4, l3 = sort_by_x(p[2:4])
    return dict(zip(LABELS, (p[0], p[1], l3, l4, p[4], p[5], p[6])))


def assign_left(p: list[np.ndarray]) -> dict[str, np.ndarray]:
    """Lateral izquierda: el paciente mira a la izquierda; la EIPS (L4) queda a la derecha de la imagen."""
    l3, l4 = sort_by_x(p[2:4])
    return dict(zip(LABELS, (p[0], p[1], l3, l4, p[4], p[5], p[6])))


def classify_posture(t1, pelvis_dir, t3) -> tuple[str, str]:
    """Reglas de diagnóstico del script original (lateral_r_assessment)."""
    head_shoulder_angle = t1.rows[0].value
    shoulder_pelvis_dir = t1.rows[1].direction
    head_dir, head_dis = t3.rows[0].direction, t3.rows[0].value
    shoulder_dis = t3.rows[1].value
    pelvis_dir_t3 = t3.rows[2].direction
    hip_dis, knee_dis = t3.rows[3].value, t3.rows[4].value

    # HALLAZGO-3 (corregido): la versión de consola comparaba distancias con signo,
    # así que desplazamientos posteriores grandes contaban como postura ideal.
    ideal_distances = all(abs(d) <= 0.5 for d in (head_dis, shoulder_dis, hip_dis, knee_dis))
    if pelvis_dir == "Normal" and ideal_distances:
        posture = "Ideal"
    elif head_shoulder_angle > 13 and head_dir == "Ant." and shoulder_pelvis_dir != "Ant." and pelvis_dir == "Ant.":
        posture = "Cifolordótica"
    elif head_dir == "Ant." and shoulder_pelvis_dir != "Pos." and pelvis_dir_t3 != "Pos." and pelvis_dir == "Pos.":
        posture = "Espalda plana"
    elif head_dir == "Ant." and shoulder_pelvis_dir == "Pos." and pelvis_dir_t3 != "Pos." and pelvis_dir == "Pos.":
        posture = "Espalda arqueada"
    elif pelvis_dir == "Normal" and head_dir == "Ant." and shoulder_pelvis_dir != "Ant.":
        posture = "Cabeza hacia delante"
    elif pelvis_dir == "Ant." and shoulder_pelvis_dir != "Ant.":
        posture = "Lordótica o tipo militar"
    elif pelvis_dir == "Ant.":
        posture = "Pelvis en Anteversión"
    elif pelvis_dir == "Pos.":
        posture = "Pelvis en Retroversión"
    else:
        posture = "Pelvis en posición normal"

    projection = {"Alin.": "Centrada", "Ant.": "Anterior"}.get(head_dir, "Posterior")
    return posture, projection


def evaluate_right(pts: dict[str, np.ndarray], scale: float, config: AssessmentConfig) -> Evaluation:
    require(pts, LABELS)
    l1, l2, l3, l4, l5, l6, l7 = (pts[k] for k in LABELS)
    ta, td = config.tolerance_angle, config.tolerance_distance
    c_pelvis = center(l3, l4)

    t1 = table("table_1", "Grados con respecto a la vertical", ("Segmento Corporal", "Dirección", "Ángulo"),
               ("Cabeza-Hombro", "Hombro-Pelvis", "Cadera-Rodilla", "Rodilla-Pies"),
               [g.lateral_angle_from_vertical(l1, l2, ta),
                g.lateral_angle_from_vertical(l2, c_pelvis, ta),
                g.lateral_angle_from_vertical(l5, l6, ta),
                g.lateral_angle_from_vertical(l6, l7, ta)])
    pelvis_dir, pelvis_angle = g.lateral_angle_from_horizontal(posterior_point=l4, anterior_point=l3)
    t2 = table("table_2", "Grados con respecto a la horizontal (normal 10° ± 5°)",
               ("Segmento Corporal", "Dirección", "Ángulo"), ("Pelvis",), [(pelvis_dir, pelvis_angle)])
    t3 = table("table_3", "Distancia con respecto a la vertical", ("Referencia", "Dirección", "Distancia"),
               ("Cabeza", "Hombros", "Pelvis", "Caderas", "Rodillas"),
               [g.lateral_distance_from_vertical(l7, ref, scale, td) for ref in (l1, l2, c_pelvis, l5, l6)])

    posture, projection = classify_posture(t1, pelvis_dir, t3)
    return Evaluation(
        derived_points={"centro_pelvis": c_pelvis},
        grid_origin=np.array([c_pelvis[0], l7[1]]),
        diagnostic={"postura": posture, "proyeccion_postural": projection},
        tables=[t1, t2, t3],
    )


def _mirror(p: np.ndarray) -> np.ndarray:
    """Refleja horizontalmente un punto (y, x). Solo importan las diferencias entre puntos."""
    return np.array([p[0], -p[1]])


def evaluate_left(pts: dict[str, np.ndarray], scale: float, config: AssessmentConfig) -> Evaluation:
    ev = evaluate_right({k: _mirror(v) for k, v in pts.items()}, scale, config)
    return Evaluation(
        derived_points={k: _mirror(v) for k, v in ev.derived_points.items()},
        grid_origin=_mirror(ev.grid_origin),
        diagnostic=ev.diagnostic,
        tables=ev.tables,
    )
