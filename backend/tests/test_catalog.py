"""Diccionario de puntos: cobertura y mediciones calculadas desde el núcleo."""
from app.lam import SPECS, View
from app.lam.catalog import catalog


def _by_id():
    return {p.id: p for p in catalog()}


def test_every_point_of_every_view_is_in_the_dictionary():
    ids = set(_by_id())
    for spec in SPECS.values():
        assert set(spec.labels) <= ids
    assert len(catalog()) == 14 + 12 + 7


def test_every_point_has_text_position_and_usage():
    for p in catalog():
        assert p.name and p.definition and p.location and p.region
        assert 0 <= p.position[0] <= 100 and 0 <= p.position[1] <= 200
        assert p.measurements or p.diagnostics, f"{p.id} no interviene en ninguna medición"


def test_measurements_match_the_evaluation_code():
    points = _by_id()
    assert {(m.table.split(" (")[0], m.item) for m in points["F7"].measurements} >= {
        ("Grados con respecto a la horizontal", "Pelvis"), ("Distancia con respecto a la vertical", "Pelvis")}
    assert "linea_pelvica_descendida" in points["F7"].diagnostics
    assert "cabeza_rotada" in points["F5"].diagnostics  # F5 no aparece en tablas, solo en el diagnóstico
    assert {m.item for m in points["P1"].measurements} == {"7ma Cervical"}
    # Los tobillos (F11/F12) son la vertical de referencia: intervienen en todas las distancias
    assert len([m for m in points["F11"].measurements if m.table.startswith("Distancia")]) == 6


def test_lateral_points_cover_both_lateral_views_and_posture():
    for p in catalog():
        if p.figure == "lateral":
            assert p.views == (View.LATERAL_DERECHA, View.LATERAL_IZQUIERDA)
            assert "postura" in p.diagnostics
