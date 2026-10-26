"""Núcleo de análisis postural LAM (Lectura Automática de Marcadores).

Librería pura: no depende de FastAPI, base de datos ni interfaz gráfica.
Recibe una imagen (ndarray RGB) y una configuración y devuelve un ViewResult.
Portado desde los scripts de consola (main.py, image_processing_LAM.py,
functions_for_assessment.py) manteniendo la misma lógica numérica.
"""
from .types import AssessmentConfig, MarkerCountError, ResultRow, ResultTable, View, ViewResult
from .views import analyze

__all__ = [
    "AssessmentConfig",
    "MarkerCountError",
    "ResultRow",
    "ResultTable",
    "View",
    "ViewResult",
    "analyze",
]
