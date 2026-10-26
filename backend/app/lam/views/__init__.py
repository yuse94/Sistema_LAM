"""Análisis por vista fotográfica."""
from __future__ import annotations

import numpy as np

from ..types import AssessmentConfig, View, ViewResult
from . import anterior, lateral, posterior

_ANALYZERS = {
    View.ANTERIOR: anterior.analyze,
    View.POSTERIOR: posterior.analyze,
    View.LATERAL_DERECHA: lateral.analyze,
}


def analyze(view: View, image: np.ndarray, config: AssessmentConfig) -> ViewResult:
    """Punto de entrada único: analiza una fotografía para la vista indicada."""
    return _ANALYZERS[View(view)](image, config)
