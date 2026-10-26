"""Tipos de datos del núcleo LAM."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

import numpy as np


class View(str, Enum):
    ANTERIOR = "anterior"
    POSTERIOR = "posterior"
    LATERAL_DERECHA = "lateral_derecha"


@dataclass(frozen=True)
class AssessmentConfig:
    """Parámetros del análisis (antes configuration.json)."""

    tolerance_angle: float = 0.0  # grados, rango 0-5
    tolerance_distance: float = 0.0  # cm, rango 0-3
    grid_size: float = 5.0  # cm, rango 1-10
    filter_threshold: float = 0.32  # rango 0.20-0.80


@dataclass
class ResultRow:
    item: str  # segmento corporal o referencia
    direction: str  # Der./Izq./Alin./Ant./Pos./Rot.Ext./...
    value: float  # grados o centímetros según la tabla


@dataclass
class ResultTable:
    key: str  # table_1, table_2, table_3 (compatibles con el Excel/PDF actuales)
    title: str
    columns: tuple[str, str, str]
    rows: list[ResultRow]


@dataclass
class ViewResult:
    view: View
    markers: dict[str, tuple[float, float]]  # id anatómico (F1, P3, L7...) -> (x, y) en px
    derived_points: dict[str, tuple[float, float]]  # centros calculados -> (x, y)
    references: tuple[tuple[float, float], tuple[float, float]]  # R1, R2 -> (x, y)
    scale_ratio: float  # cm por píxel
    grid_origin: tuple[float, float]  # (x, y) del cruce de la cuadrícula
    grid_step_px: float
    diagnostic: dict[str, str | float | None]
    tables: list[ResultTable]
    image: np.ndarray = field(repr=False)  # imagen enderezada y recortada (uint8 RGB)


class MarkerCountError(ValueError):
    """La cantidad de marcadores detectados no coincide con la esperada.

    Reemplaza las ventanas de matplotlib del script de consola: la API devuelve
    los puntos detectados para que la interfaz web los muestre sobre la imagen.
    """

    def __init__(self, view: View, expected: int, points: list[tuple[float, float]],
                 image: np.ndarray | None = None):
        self.view = view
        self.expected = expected
        self.found = len(points)
        self.points = points  # (x, y)
        self.image = image
        kind = "demasiados" if self.found > expected else "menos"
        super().__init__(f"Existen {kind} puntos en la imagen: {self.found} puntos de {expected}")
