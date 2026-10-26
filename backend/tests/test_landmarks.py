"""Evaluación desde puntos (ajuste manual) y vista lateral izquierda."""
import pytest

from app.lam import AssessmentConfig, View, analyze, evaluate_landmarks
from tests.synthetic import ANTERIOR, LATERAL, make_image

CFG = AssessmentConfig(tolerance_angle=1.0, tolerance_distance=1.0)


def _rows(result):
    return [[(r.item, r.direction, r.value) for r in t.rows] for t in result.tables]


def test_evaluate_landmarks_reproduces_marker_analysis():
    auto = analyze(View.ANTERIOR, make_image(ANTERIOR), CFG)
    manual = evaluate_landmarks(View.ANTERIOR, auto.markers, auto.scale_ratio, CFG)
    assert _rows(manual) == _rows(auto)
    assert manual.diagnostic == auto.diagnostic


def test_moving_a_point_updates_results():
    auto = analyze(View.ANTERIOR, make_image(ANTERIOR), CFG)
    moved = dict(auto.markers)
    x, y = moved["F4"]
    moved["F4"] = (x, y + 30)  # hombro izquierdo del paciente más bajo
    result = evaluate_landmarks(View.ANTERIOR, moved, auto.scale_ratio, CFG)
    assert result.tables[0].rows[0].direction == "Izq."


def test_missing_landmark_is_reported():
    auto = analyze(View.ANTERIOR, make_image(ANTERIOR), CFG)
    incomplete = {k: v for k, v in auto.markers.items() if k != "F7"}
    with pytest.raises(ValueError):
        evaluate_landmarks(View.ANTERIOR, incomplete, auto.scale_ratio, CFG)


def test_left_lateral_mirrors_right_lateral():
    # La misma persona fotografiada desde el lado izquierdo = imagen reflejada
    tilted = list(LATERAL)
    tilted[0] = (100, 530)  # cabeza adelantada
    right = analyze(View.LATERAL_DERECHA, make_image(tilted), CFG)
    left = analyze(View.LATERAL_IZQUIERDA, make_image(tilted)[:, ::-1].copy(), CFG)
    for t_left, t_right in zip(left.tables, right.tables):
        for a, b in zip(t_left.rows, t_right.rows):
            assert (a.item, a.direction) == (b.item, b.direction)
            assert a.value == pytest.approx(b.value, abs=0.05)  # diferencias de redondeo de píxeles
    assert left.diagnostic == right.diagnostic
    assert right.tables[2].rows[0].direction == "Ant."
    # La EIPS (L3) queda del lado de la espalda: derecha de la imagen en la vista izquierda
    assert left.markers["L3"][0] > left.markers["L4"][0]
