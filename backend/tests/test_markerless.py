"""Modo sin marcadores: puntos de MediaPipe, escala por estatura y línea vertical."""
import pytest

from app.lam import AssessmentConfig, Calibration, View, analyze_pose, evaluate_landmarks, height_scale
from app.lam.level import roll_from_vertical
from app.lam.pose import estimate_calibration, landmarks_from_pose
from tests.synthetic_pose import frontal_pose, lateral_pose, rotate_point, rotate_pose

CFG = AssessmentConfig(tolerance_angle=1.0, tolerance_distance=1.0)
CAL = Calibration(vertex=(500.0, 100.0), floor=(500.0, 1800.0))  # 1700 px
VERTICAL = ((900.0, 200.0), (900.0, 1700.0))  # p. ej. el marco de una puerta


def _rows(result):
    return [(r.item, r.direction, r.value) for t in result.tables for r in t.rows]


def test_anterior_mapping_has_all_points_and_flags_estimated():
    mapped = landmarks_from_pose(View.ANTERIOR, frontal_pose())
    assert set(mapped.landmarks) == {f"F{i}" for i in range(1, 15)}
    assert set(mapped.estimated) == {"F1", "F2", "F5", "F6", "F7", "F8"}
    # Lado derecho del paciente a la izquierda de la imagen
    assert mapped.landmarks["F3"][0] < mapped.landmarks["F4"][0]


def test_posterior_pairs_by_image_position_even_if_labels_are_swapped():
    pose = frontal_pose(facing_camera=False)
    swapped = list(pose)
    for left_i, right_i in [(11, 12), (23, 24), (25, 26), (27, 28), (29, 30)]:
        swapped[left_i], swapped[right_i] = pose[right_i], pose[left_i]
    assert landmarks_from_pose(View.POSTERIOR, swapped).landmarks == \
        landmarks_from_pose(View.POSTERIOR, pose).landmarks


def test_symmetric_patient_is_aligned():
    r = analyze_pose(View.ANTERIOR, frontal_pose(), 170, CFG, CAL).result
    assert [row.direction for row in r.tables[0].rows] == ["Alin.", "Alin.", "Alin."]
    assert all(row.direction == "Alin." for row in r.tables[1].rows)
    r = analyze_pose(View.POSTERIOR, frontal_pose(facing_camera=False), 170, CFG, CAL).result
    assert [row.direction for row in r.tables[0].rows] == ["Alin.", "Alin.", "Alin."]


def test_scale_from_height():
    assert height_scale(170, CAL.vertex, CAL.floor) == pytest.approx(0.1)
    analysis = analyze_pose(View.ANTERIOR, frontal_pose(), 170, CFG, CAL)
    assert analysis.result.scale_ratio == pytest.approx(0.1)
    with pytest.raises(ValueError):
        height_scale(170, CAL.floor, CAL.vertex)  # invertidos


def test_tilted_camera_without_vertical_line_biases_angles():
    tilted = rotate_pose(frontal_pose(), 4)
    r = analyze_pose(View.ANTERIOR, tilted, 170, CFG, CAL).result
    assert r.tables[0].rows[0].direction != "Alin."  # los hombros "caen" por el giro de la cámara
    assert abs(r.tables[0].rows[0].value) == pytest.approx(4, abs=0.1)


def test_vertical_line_corrects_camera_tilt():
    straight = analyze_pose(View.ANTERIOR, frontal_pose(), 170, CFG, CAL).result
    tilted_pose = rotate_pose(frontal_pose(), 4)
    tilted_cal = Calibration(rotate_point(CAL.vertex, 4), rotate_point(CAL.floor, 4))
    tilted_line = (rotate_point(VERTICAL[0], 4), rotate_point(VERTICAL[1], 4))
    fixed = analyze_pose(View.ANTERIOR, tilted_pose, 170, CFG, tilted_cal, tilted_line).result
    for a, b in zip(_rows(fixed), _rows(straight)):
        assert a[:2] == b[:2]
        assert a[2] == pytest.approx(b[2], abs=0.05)
    assert fixed.scale_ratio == pytest.approx(straight.scale_ratio, rel=1e-6)
    assert abs(fixed.roll_deg) == pytest.approx(4, abs=1e-6)
    # Los puntos se devuelven donde están en la foto (sin nivelar): F3 es un hombro detectado
    assert fixed.markers["F3"][0] == pytest.approx(tilted_pose[12].x)
    assert fixed.markers["F3"][1] == pytest.approx(tilted_pose[12].y)


def test_vertical_line_order_does_not_matter():
    a = roll_from_vertical((100, 0), (110, 100))
    b = roll_from_vertical((110, 100), (100, 0))
    assert a == pytest.approx(b)
    with pytest.raises(ValueError):
        roll_from_vertical((0, 0), (100, 100))  # 45°: línea mal marcada


def test_manual_adjustment_keeps_leveling():
    tilted_pose = rotate_pose(frontal_pose(), 4)
    tilted_line = (rotate_point(VERTICAL[0], 4), rotate_point(VERTICAL[1], 4))
    landmarks = landmarks_from_pose(View.ANTERIOR, tilted_pose).landmarks
    r = evaluate_landmarks(View.ANTERIOR, landmarks, 0.1, CFG, vertical_line=tilted_line)
    assert r.tables[0].rows[0].direction == "Alin."


def test_lateral_pose_normal_pelvis_and_left_mirrors_right():
    right = analyze_pose(View.LATERAL_DERECHA, lateral_pose(facing_right=True), 170, CFG, CAL)
    left = analyze_pose(View.LATERAL_IZQUIERDA, lateral_pose(facing_right=False), 170, CFG, CAL)
    assert right.result.tables[1].rows[0].direction == "Normal"  # pelvis estimada con ~10°
    for a, b in zip(_rows(left.result), _rows(right.result)):
        assert a[:2] == b[:2]
        assert a[2] == pytest.approx(b[2], abs=0.05)
    assert set(right.estimated) == {"L3", "L4", "L6"}  # L7 (maléolo externo) lo detecta MediaPipe


def test_estimated_calibration_is_plausible():
    cal = estimate_calibration(frontal_pose())
    assert 60 < cal.vertex[1] < 200  # el vértice real está en y=100
    assert cal.floor[1] == pytest.approx(1800)
