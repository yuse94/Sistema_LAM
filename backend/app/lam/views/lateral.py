"""Vista lateral derecha del plano sagital (7 marcadores, L1-L7)."""
from __future__ import annotations

from .. import geometry as g
from ..types import AssessmentConfig, View, ViewResult
from .base import center, prepare, sort_by_x, table, xy

EXPECTED_MARKERS = 7
LABELS = {
    "L1": "Oído", "L2": "Acromioclavicular", "L3": "EIPS", "L4": "EIAS",
    "L5": "Trocánter mayor", "L6": "Tuberosidad tibial", "L7": "Articulación transversal del tarso",
}


def classify_posture(t1, pelvis_dir, t3) -> tuple[str, str]:
    """Reglas de diagnóstico del script original (lateral_r_assessment)."""
    head_shoulder_angle = t1.rows[0].value
    shoulder_pelvis_dir = t1.rows[1].direction
    head_dir, head_dis = t3.rows[0].direction, t3.rows[0].value
    shoulder_dis = t3.rows[1].value
    pelvis_dir_t3 = t3.rows[2].direction
    hip_dis, knee_dis = t3.rows[3].value, t3.rows[4].value

    # FIXME(HALLAZGO-3): el original compara distancias con signo (<= 0.5);
    # valores negativos grandes (posteriores) cuentan como "Ideal". ¿Debería ser abs()?
    if pelvis_dir == "Normal" and head_dis <= 0.5 and shoulder_dis <= 0.5 and hip_dis <= 0.5 and knee_dis <= 0.5:
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


def analyze(image, config: AssessmentConfig) -> ViewResult:
    prep = prepare(View.LATERAL_DERECHA, image, config, EXPECTED_MARKERS)
    p = prep.points
    ta, td, s = config.tolerance_angle, config.tolerance_distance, prep.scale_ratio

    l1, l2 = p[0], p[1]
    l3, l4 = sort_by_x(p[2:4])  # posterior (izq. de la imagen), anterior (der.)
    l5, l6, l7 = p[4], p[5], p[6]
    c_pelvis = center(l3, l4)

    t1 = table("table_1", "Grados con respecto a la vertical", ("Segmento Corporal", "Dirección", "Ángulo"),
               ("Cabeza-Hombro", "Hombro-Pelvis", "Cadera-Rodilla", "Rodilla-Pies"),
               [g.lateral_angle_from_vertical(l1, l2, ta),
                g.lateral_angle_from_vertical(l2, c_pelvis, ta),
                g.lateral_angle_from_vertical(l5, l6, ta),
                g.lateral_angle_from_vertical(l6, l7, ta)])
    pelvis_dir, pelvis_angle = g.lateral_angle_from_horizontal(l3, l4)
    t2 = table("table_2", "Grados con respecto a la horizontal (normal 10° ± 5°)",
               ("Segmento Corporal", "Dirección", "Ángulo"), ("Pelvis",), [(pelvis_dir, pelvis_angle)])
    t3 = table("table_3", "Distancia con respecto a la vertical", ("Referencia", "Dirección", "Distancia"),
               ("Cabeza", "Hombros", "Pelvis", "Caderas", "Rodillas"),
               [g.lateral_distance_from_vertical(l7, ref, s, td) for ref in (l1, l2, c_pelvis, l5, l6)])

    posture, projection = classify_posture(t1, pelvis_dir, t3)

    named = dict(zip(LABELS, (l1, l2, l3, l4, l5, l6, l7)))
    return ViewResult(
        view=View.LATERAL_DERECHA,
        markers={k: xy(v) for k, v in named.items()},
        derived_points={"centro_pelvis": xy(c_pelvis)},
        references=(xy(prep.reference_1), xy(prep.reference_2)),
        scale_ratio=s,
        grid_origin=(float(l7[1]), float(c_pelvis[0])),
        grid_step_px=prep.grid_step_px,
        diagnostic={"postura": posture, "proyeccion_postural": projection},
        tables=[t1, t2, t3],
        image=prep.image,
    )
