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
    image_width: int
    image_height: int
    markers: dict[str, Point]
    derived_points: dict[str, Point]
    references: tuple[Point, Point]
    scale_ratio: float
    grid_origin: Point
    grid_step_px: float
    diagnostic: dict[str, str | float | None]
    tables: list[ResultTableOut]
    overlay_image: str | None = Field(None, description="Imagen resultante como data URL (JPEG)")

    @classmethod
    def from_domain(cls, r: ViewResult, overlay_image: str | None = None) -> "ViewResultOut":
        pt = lambda p: Point(x=p[0], y=p[1])  # noqa: E731
        return cls(
            view=r.view,
            image_width=r.image.shape[1],
            image_height=r.image.shape[0],
            markers={k: pt(v) for k, v in r.markers.items()},
            derived_points={k: pt(v) for k, v in r.derived_points.items()},
            references=(pt(r.references[0]), pt(r.references[1])),
            scale_ratio=r.scale_ratio,
            grid_origin=pt(r.grid_origin),
            grid_step_px=r.grid_step_px,
            diagnostic=r.diagnostic,
            tables=[ResultTableOut(key=t.key, title=t.title, columns=t.columns,
                                   rows=[ResultRowOut(**vars(row)) for row in t.rows]) for t in r.tables],
            overlay_image=overlay_image,
        )


class MarkerCountErrorOut(BaseModel):
    """Se devuelve con HTTP 422 para que la UI muestre los puntos detectados."""

    message: str
    view: View
    expected: int
    found: int
    points: list[Point]
    preview_image: str | None = None
