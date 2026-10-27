"""Regresión del modo sin marcadores con las coordenadas reales de MediaPipe.

Usa validation/resultados/poses.json (generado por validation/markerless.py; no está en el
repositorio). Comprueba que la ubicación de los puntos no empeore respecto al ajuste
documentado en docs/VALIDACION.md.
"""
import json
import math
import statistics
from pathlib import Path

import pytest

from app.lam import PosePoint, View
from app.lam.pose import landmarks_from_pose

POSES = Path(__file__).resolve().parents[1] / "validation" / "resultados" / "poses.json"
pytestmark = pytest.mark.fotos


@pytest.fixture(scope="module")
def errors():
    if not POSES.exists():
        pytest.skip(f"No se encontró {POSES}; ejecutar validation/markerless.py")
    data = json.loads(POSES.read_text(encoding="utf-8"))
    errs: dict[str, list[float]] = {}
    for r in data.values():
        lm = landmarks_from_pose(View(r["vista"]), [PosePoint(*p) for p in r["pose"]]).landmarks
        for k, (x, y) in r["marcadores"].items():
            errs.setdefault(k, []).append(math.hypot(lm[k][0] - x, lm[k][1] - y) * r["escala_marcadores"])
    return errs


def test_mean_point_error(errors):
    mean = statistics.mean(statistics.mean(v) for v in errors.values())
    assert mean < 1.8, f"error medio {mean:.2f} cm (ajuste documentado: 1.65 cm)"


def test_no_point_above_three_centimeters(errors):
    worst = {k: statistics.mean(v) for k, v in errors.items() if statistics.mean(v) >= 3.0}
    assert not worst, f"puntos con error medio ≥ 3 cm: {worst}"
