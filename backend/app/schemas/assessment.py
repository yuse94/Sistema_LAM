"""Esquemas de entrada/salida del análisis postural."""
from __future__ import annotations

from pydantic import BaseModel, Field

from app.lam import AssessmentConfig, View, ViewResult


class AssessmentConfigIn(BaseModel):
    """Mismos rangos que validaba el menú de configuración de consola."""

    tolerance_angle: float = Field(0.0, ge=0.0, le=5.0, description="Ángulo de tolerancia (°)")
    tolerance_distance: float = Field(0.0, ge=0.0, le=3.0, description="Distancia de tolerancia (cm)")
    grid_size: float = Field(5.0, ge=1.0, le=10.0, description="Tamaño de cuadrícula (cm)")
    filter_threshold: float = Field(0.32, ge=0.20, le=0.80, description="Umbral del filtro verde")

    def to_domain(self) -> AssessmentConfig:
        return AssessmentConfig(**self.model_dump())


class Point(BaseModel):
    x: float
    y: float


class ResultRowOut(BaseModel):
    item: str
    direction: str
    value: float


class ResultTableOut(BaseModel):
    key: str
    title: str
    columns: tuple[str, str, str]
    rows: list[ResultRowOut]


class ViewResultOut(BaseModel):
    view: View
    image_width: int | None = None
    image_height: int | None = None
    markers: dict[str, Point]
    derived_points: dict[str, Point]
    references: tuple[Point, Point] | None = None
    scale_ratio: float = Field(description="Centímetros por píxel")
    grid_origin: Point
    grid_step_px: float
    diagnostic: dict[str, str | float | None]
    tables: list[ResultTableOut]
    image: str | None = Field(None, description="Imagen enderezada como data URL (JPEG), sin dibujos")

    @classmethod
    def from_domain(cls, r: ViewResult, image: str | None = None) -> "ViewResultOut":
        pt = lambda p: Point(x=p[0], y=p[1])  # noqa: E731
        return cls(
            view=r.view,
            image_width=r.image.shape[1] if r.image is not None else None,
            image_height=r.image.shape[0] if r.image is not None else None,
            markers={k: pt(v) for k, v in r.markers.items()},
            derived_points={k: pt(v) for k, v in r.derived_points.items()},
            references=(pt(r.references[0]), pt(r.references[1])) if r.references else None,
            scale_ratio=r.scale_ratio,
            grid_origin=pt(r.grid_origin),
            grid_step_px=r.grid_step_px,
            diagnostic=r.diagnostic,
            tables=[ResultTableOut(key=t.key, title=t.title, columns=t.columns,
                                   rows=[ResultRowOut(**vars(row)) for row in t.rows]) for t in r.tables],
            image=image,
        )


class EvaluateIn(BaseModel):
    """Puntos ajustados por el evaluador (o de otro detector) para recalcular una vista."""

    landmarks: dict[str, Point] = Field(description="Punto anatómico (F1, P3, L7...) -> coordenadas en píxeles")
    scale_ratio: float = Field(gt=0, description="Centímetros por píxel")
    config: AssessmentConfigIn = AssessmentConfigIn()


class ViewInfo(BaseModel):
    view: View
    labels: dict[str, str]
    expected_markers: int


class MarkerCountErrorOut(BaseModel):
    """Se devuelve con HTTP 422 para que la UI muestre los puntos detectados."""

    message: str
    view: View
    expected: int
    found: int
    points: list[Point]
    preview_image: str | None = None
