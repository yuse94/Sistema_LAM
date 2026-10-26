"""Esquemas de entrada/salida del análisis postural."""
from __future__ import annotations

from pydantic import BaseModel, Field, model_validator

from app.lam import AssessmentConfig, Calibration, PosePoint, View, ViewResult


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

    def as_tuple(self) -> tuple[float, float]:
        return self.x, self.y


class CalibrationIn(BaseModel):
    """Puntos para la escala por estatura, en píxeles de la imagen."""

    vertex: Point = Field(description="Parte superior de la cabeza")
    floor: Point = Field(description="Apoyo de los talones en el suelo")

    def to_domain(self) -> Calibration:
        return Calibration(self.vertex.as_tuple(), self.floor.as_tuple())


VerticalLine = tuple[Point, Point]


def vertical_line_tuple(line: VerticalLine | None):
    return (line[0].as_tuple(), line[1].as_tuple()) if line else None


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
    roll_deg: float = Field(0.0, description="Inclinación de la vertical real; la cuadrícula se dibuja rotada -roll_deg")
    estimated_points: list[str] = Field(default_factory=list,
                                        description="Puntos estimados por proporciones: revisar y ajustar")
    calibration: CalibrationIn | None = None

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
            roll_deg=r.roll_deg,
        )


class EvaluateIn(BaseModel):
    """Puntos ajustados por el evaluador para recalcular una vista.

    La escala se da directamente (scale_ratio, modo con marcadores) o con la
    estatura del paciente y los puntos de calibración (modo sin marcadores).
    """

    landmarks: dict[str, Point] = Field(description="Punto anatómico (F1, P3, L7...) -> coordenadas en píxeles")
    scale_ratio: float | None = Field(None, gt=0, description="Centímetros por píxel")
    height_cm: float | None = Field(None, ge=50, le=250, description="Estatura del paciente")
    calibration: CalibrationIn | None = None
    vertical_line: VerticalLine | None = Field(None, description="Dos puntos sobre algo vertical en la escena")
    config: AssessmentConfigIn = AssessmentConfigIn()

    @model_validator(mode="after")
    def check_scale(self):
        if self.scale_ratio is None and (self.height_cm is None or self.calibration is None):
            raise ValueError("Indique scale_ratio, o height_cm junto con calibration")
        return self


class PosePointIn(BaseModel):
    x: float
    y: float
    visibility: float = 1.0


class PoseIn(BaseModel):
    """Resultado de MediaPipe Pose Landmarker (33 puntos) convertido a píxeles de la imagen."""

    pose: list[PosePointIn] = Field(min_length=33, max_length=33)
    height_cm: float = Field(ge=50, le=250, description="Estatura del paciente")
    calibration: CalibrationIn | None = Field(None, description="Vértice y suelo; si falta, se estiman")
    vertical_line: VerticalLine | None = None
    config: AssessmentConfigIn = AssessmentConfigIn()

    def pose_points(self) -> list[PosePoint]:
        return [PosePoint(p.x, p.y, p.visibility) for p in self.pose]


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
