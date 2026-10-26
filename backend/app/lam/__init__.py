"""Núcleo de análisis postural LAM (Lectura Automática de Marcadores).

Librería pura: no depende de FastAPI, base de datos ni interfaz gráfica.
- analyze(view, imagen, config): detecta los marcadores verdes y evalúa la vista.
- evaluate_landmarks(view, puntos, escala, config): evalúa puntos ya ubicados
  (ajustados a mano o provenientes de otro detector).
Portado desde los scripts de consola (main.py, image_processing_LAM.py,
functions_for_assessment.py).
"""
from .types import AssessmentConfig, MarkerCountError, ResultRow, ResultTable, View, ViewResult
from .views import SPECS, analyze, evaluate_landmarks

__all__ = [
    "SPECS",
    "AssessmentConfig",
    "MarkerCountError",
    "ResultRow",
    "ResultTable",
    "View",
    "ViewResult",
    "analyze",
    "evaluate_landmarks",
]
