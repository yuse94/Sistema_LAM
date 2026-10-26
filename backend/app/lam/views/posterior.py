"""Vista posterior del plano frontal (12 marcadores, P1-P12)."""
from __future__ import annotations

from .. import geometry as g
from ..types import AssessmentConfig, View, ViewResult
from .base import center, prepare, sort_by_x, table, xy

EXPECTED_MARKERS = 12
LABELS = {
    "P1": "7ma vértebra cervical", "P2": "5ta vértebra dorsal", "P3": "Acromioclavicular derecha",
    "P4": "Acromioclavicular izquierda", "P5": "EIPS derecha", "P6": "EIPS izquierda",
    "P7": "Hueco poplíteo derecho", "P8": "Hueco poplíteo izquierdo", "P9": "Tendón de Aquiles derecho",
    "P10": "Tendón de Aquiles izquierdo", "P11": "Calcáneo derecho", "P12": "Calcáneo izquierdo",
}


def analyze(image, config: AssessmentConfig) -> ViewResult:
    prep = prepare(View.POSTERIOR, image, config, EXPECTED_MARKERS)
    p = prep.points
    ta, td, s = config.tolerance_angle, config.tolerance_distance, prep.scale_ratio

    # En la foto posterior el lado izquierdo del paciente queda a la izquierda de la imagen.
    p4, p1, p3 = sort_by_x(p[0:3])
    p2 = p[3]
    p6, p5 = sort_by_x(p[4:6])
    p8, p7 = sort_by_x(p[6:8])
    p10, p9 = sort_by_x(p[8:10])
    p12, p11 = sort_by_x(p[10:12])

    c_shoulders = center(p4, p3)
    c_pelvis = center(p6, p5)  # centro Y de la cuadrícula
    c_knees = center(p8, p7)
    c_ankles = center(p10, p9)
    c_soles = center(p12, p11)  # centro X de la cuadrícula

    t1 = table("table_1", "Grados con respecto a la horizontal", ("Segmento Corporal", "Descendido", "Ángulo"),
               ("Hombros", "Pelvis", "Rodillas"),
               [g.posterior_angle_from_horizontal(p4, p3, ta),
                g.posterior_angle_from_horizontal(p6, p5, ta),
                g.posterior_angle_from_horizontal(p8, p7, ta)])
    # Etiquetas corregidas según el README (el script de consola reutilizaba las de la vista anterior).
    t2 = table("table_2", "Distancia con respecto a la vertical", ("Referencia", "Dirección", "Distancia"),
               ("Hombros", "7ma Cervical", "5ta Torácica", "Pelvis", "Rodillas", "Tobillos"),
               [g.posterior_distance_from_vertical(c_soles, ref, s, td)
                for ref in (c_shoulders, p1, p2, c_pelvis, c_knees, c_ankles)])
    t3 = table("table_3", "Pie varo o valgo", ("Segmento Corporal", "Dirección", "Ángulo"),
               ("Pie Izquierdo", "Pie Derecho"),
               [g.valgus_or_varus(p10, p12, ta), g.valgus_or_varus(p11, p9, ta)])

    dorsal_rot, _ = g.angle_from_vertical(c_pelvis, c_shoulders, ta)
    pelvis_rot, _ = g.angle_from_vertical(c_knees, c_pelvis, ta)
    diagnostic = {
        "rotacion_dorsal": dorsal_rot,
        "rotacion_pelvica": pelvis_rot,
        "pie_izquierdo": t3.rows[0].direction,
        "pie_derecho": t3.rows[1].direction,
    }

    named = dict(zip(LABELS, (p1, p2, p3, p4, p5, p6, p7, p8, p9, p10, p11, p12)))
    return ViewResult(
        view=View.POSTERIOR,
        markers={k: xy(v) for k, v in named.items()},
        derived_points={"centro_hombros": xy(c_shoulders), "centro_pelvis": xy(c_pelvis),
                        "centro_rodillas": xy(c_knees), "centro_tobillos": xy(c_ankles),
                        "centro_calcaneos": xy(c_soles)},
        references=(xy(prep.reference_1), xy(prep.reference_2)),
        scale_ratio=s,
        grid_origin=(float(c_soles[1]), float(c_pelvis[0])),
        grid_step_px=prep.grid_step_px,
        diagnostic=diagnostic,
        tables=[t1, t2, t3],
        image=prep.image,
    )
