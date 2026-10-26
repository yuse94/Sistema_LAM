import pytest

from app.lam import AssessmentConfig, MarkerCountError, View, analyze
from app.lam import geometry as g
from tests.synthetic import ANTERIOR, LATERAL, POSTERIOR, make_image

import numpy as np

CFG = AssessmentConfig(tolerance_angle=1.0, tolerance_distance=1.0)


def test_anterior_symmetric_posture_is_aligned():
    r = analyze(View.ANTERIOR, make_image(ANTERIOR), CFG)
    assert set(r.markers) == {f"F{i}" for i in range(1, 15)}
    t1 = r.tables[0]
    assert [row.direction for row in t1.rows] == ["Alin.", "Alin.", "Alin."]
    assert all(abs(row.value) < 0.5 for row in r.tables[1].rows)
    # F3 (hombro derecho del paciente) queda a la izquierda de la imagen
    assert r.markers["F3"][0] < r.markers["F4"][0]


def test_posterior_has_twelve_markers_and_readme_labels():
    r = analyze(View.POSTERIOR, make_image(POSTERIOR), CFG)
    assert len(r.markers) == 12
    assert [row.item for row in r.tables[1].rows][:3] == ["Hombros", "7ma Cervical", "5ta Torácica"]


def test_lateral_returns_posture():
    r = analyze(View.LATERAL_DERECHA, make_image(LATERAL), CFG)
    assert r.diagnostic["postura"]
    assert r.diagnostic["proyeccion_postural"] == "Centrada"


def test_wrong_marker_count_raises_with_points():
    with pytest.raises(MarkerCountError) as exc:
        analyze(View.ANTERIOR, make_image(ANTERIOR[:-1]), CFG)
    assert exc.value.expected == 14 and exc.value.found == 13


def test_tilted_shoulders_detected():
    pts = list(ANTERIOR)
    pts[2] = (240, 350)  # hombro derecho del paciente más alto
    r = analyze(View.ANTERIOR, make_image(pts), CFG)
    assert r.tables[0].rows[0].direction == "Izq."


def test_scale_uses_distance_between_references():
    # R1 y R2 están a 880 px en la imagen sintética = 100 cm
    r = analyze(View.ANTERIOR, make_image(ANTERIOR), CFG)
    assert r.scale_ratio == pytest.approx(100 / 880, rel=1e-3)


def test_posterior_level_shoulders_are_aligned():
    r = analyze(View.POSTERIOR, make_image(POSTERIOR), CFG)
    assert [row.direction for row in r.tables[0].rows] == ["Alin.", "Alin.", "Alin."]


def test_posterior_lowered_side():
    left, right = np.array([100.0, 0.0]), np.array([110.0, 100.0])  # derecho más bajo (y mayor)
    assert g.posterior_angle_from_horizontal(left, right, 1.0)[0] == "Der."
    left, right = np.array([110.0, 0.0]), np.array([100.0, 100.0])  # izquierdo más bajo
    assert g.posterior_angle_from_horizontal(left, right, 1.0)[0] == "Izq."


def test_geometry_matches_legacy_sign_convention():
    right, left = np.array([100.0, 0.0]), np.array([90.0, 100.0])
    direction, value = g.anterior_angle_from_horizontal(right, left, 0.0)
    assert direction == "Der." and value > 0
