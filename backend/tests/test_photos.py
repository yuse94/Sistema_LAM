"""Pruebas con las fotografías reales de validación (Pruebas_adultos y tipos_de_postura).

Las fotos no están en el repositorio (contienen pacientes identificables). Se buscan
en la raíz del proyecto, o en la carpeta indicada por LAM_PHOTOS_DIR.

    uv run pytest -m fotos
"""
import os
import re
from pathlib import Path

import numpy as np
import pytest
from PIL import Image, ImageOps

from app.lam import AssessmentConfig, View, analyze

ROOT = Path(os.environ.get("LAM_PHOTOS_DIR", Path(__file__).resolve().parents[2]))
ADULTS = ROOT / "Pruebas_adultos"
TYPES = ROOT / "tipos_de_postura"

pytestmark = pytest.mark.fotos


def _photos():
    return sorted(ADULTS.glob("*.[jJ][pP][gG]")) if ADULTS.is_dir() else []


def _view(name: str) -> View:
    n = name.lower()
    if "anterior" in n:
        return View.ANTERIOR
    if "posterior" in n:
        return View.POSTERIOR
    return View.LATERAL_DERECHA if "derecha" in n else View.LATERAL_IZQUIERDA


def _person(name: str) -> str:
    return re.split(r"[- ](?=anterior|posterior|lateral)", name, maxsplit=1)[0]


def _load(path: Path) -> np.ndarray:
    # Igual que la API: se respeta la orientación EXIF (las laterales izquierdas son espejos por EXIF)
    return np.asarray(ImageOps.exif_transpose(Image.open(path)).convert("RGB"))


@pytest.fixture(scope="module")
def results():
    if not _photos():
        pytest.skip(f"No se encontraron fotos en {ADULTS}")
    return {p.name: analyze(_view(p.name), _load(p), AssessmentConfig()) for p in _photos()}


def test_markers_detected_in_every_photo(results):
    # analyze lanza MarkerCountError si falta o sobra algún marcador
    assert len(results) == len(_photos())


def test_scale_is_consistent_across_views_of_each_person(results):
    by_person: dict[str, list[float]] = {}
    for name, r in results.items():
        by_person.setdefault(_person(name), []).append(r.scale_ratio)
    for person, scales in by_person.items():
        spread = (max(scales) - min(scales)) / np.mean(scales)
        # Entre tomas la cámara o las referencias pueden moverse un poco (máximo observado: 3.8 %)
        assert spread < 0.05, f"{person}: escalas {scales}"


def test_left_lateral_equals_mirrored_right_lateral(results):
    pairs = 0
    for name, right in results.items():
        if _view(name) is not View.LATERAL_DERECHA:
            continue
        person = _person(name)
        left = next((r for n, r in results.items() if _person(n) == person and _view(n) is View.LATERAL_IZQUIERDA), None)
        if left is None:
            continue
        pairs += 1
        for t_left, t_right in zip(left.tables, right.tables):
            for a, b in zip(t_left.rows, t_right.rows):
                assert a.value == pytest.approx(b.value, abs=0.1), f"{person} {a.item}"
        assert left.diagnostic == right.diagnostic, person
    assert pairs > 0


EXPECTED_POSTURES = {
    "cabeza-delante": "Cabeza hacia delante",
    "cifolordotica": "Cifolordótica",
    "espalda-arqueada": "Espalda arqueada",
    "espalda-plana": "Espalda plana",
    "ideal": "Ideal",
    "lordotica": "Lordótica o tipo militar",
}


@pytest.mark.parametrize("name", sorted(EXPECTED_POSTURES))
def test_posture_type_illustrations_are_classified(name):
    path = TYPES / f"{name}.jpg"
    if not path.exists():
        pytest.skip(f"No se encontró {path}")
    # Con la configuración por defecto (1° y 0.5 cm). Con 0° y 0 cm cualquier desviación
    # de un píxel cuenta y "cabeza adelante" se clasifica mal (ver docs/VALIDACION.md).
    r = analyze(View.LATERAL_DERECHA, _load(path), AssessmentConfig())
    assert r.diagnostic["postura"] == EXPECTED_POSTURES[name]
