"""Núcleo de análisis postural LAM (Lectura Automática de Marcadores).

Librería pura: no depende de FastAPI, base de datos ni interfaz gráfica.
- analyze(view, imagen, config): detecta los marcadores verdes y evalúa la vista.
- analyze_pose(view, pose, estatura, config): modo sin marcadores, desde los 33
  puntos de MediaPipe; la escala sale de la estatura del paciente.
- evaluate_landmarks(view, puntos, escala, config): evalúa puntos ya ubicados
  (ajustados a mano), con nivelación opcional por una línea vertical.
Portado desde los scripts de consola (main.py, image_processing_LAM.py,
functions_for_assessment.py).
"""
from .level import height_scale
from .pose import Calibration, PosePoint
from .types import AssessmentConfig, MarkerCountError, ResultRow, ResultTable, View, ViewResult
from .views import SPECS, PoseAnalysis, analyze, analyze_pose, evaluate_landmarks

__all__ = [
    "SPECS",
    "AssessmentConfig",
    "Calibration",
    "MarkerCountError",
    "PoseAnalysis",
    "PosePoint",
    "ResultRow",
    "ResultTable",
    "View",
    "ViewResult",
    "analyze",
    "analyze_pose",
    "evaluate_landmarks",
    "height_scale",
]
