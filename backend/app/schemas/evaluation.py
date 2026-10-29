"""Esquemas de las evaluaciones guardadas, el historial y los reportes."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator

from app.lam import View
from app.schemas.assessment import AssessmentConfigIn, CalibrationIn, Point, ResultTableOut, VerticalLine
from app.schemas.common import UTCDatetime
from app.schemas.patient import PatientOut

Mode = Literal["pose", "markers"]


class ViewSubmission(BaseModel):
    """Una vista lista para guardar: los puntos tal como quedaron en el editor.

    El servidor vuelve a evaluar con estos puntos; no confía en los resultados
    calculados por el navegador.
    """

    view: View
    landmarks: dict[str, Point]
    scale_ratio: float | None = Field(None, gt=0, description="cm/px (modo con marcadores)")
    calibration: CalibrationIn | None = Field(None, description="Vértice y suelo (modo sin marcadores)")
    vertical_line: VerticalLine | None = None
    estimated_points: list[str] = Field(default_factory=list, description="Estimados que el evaluador no movió")


class EvaluationCreate(BaseModel):
    patient_id: int
    mode: Mode
    height_cm: float | None = Field(None, ge=50, le=250)
    config: AssessmentConfigIn = AssessmentConfigIn()
    notes: str | None = Field(None, max_length=4000)
    evaluator: str | None = Field(None, max_length=150)
    photo_consent: bool = Field(False, description="El paciente autorizó el uso de sus fotografías")
    views: list[ViewSubmission] = Field(min_length=1, max_length=4)

    @model_validator(mode="after")
    def check(self):
        if not self.photo_consent:
            raise ValueError("Se requiere el consentimiento del paciente para guardar sus fotografías")
        names = [v.view for v in self.views]
        if len(set(names)) != len(names):
            raise ValueError("Cada vista puede enviarse una sola vez")
        for v in self.views:
            if self.mode == "pose" and (self.height_cm is None or v.calibration is None):
                raise ValueError(f"{v.view.value}: el modo sin marcadores requiere la estatura y la calibración")
            if self.mode == "markers" and v.scale_ratio is None:
                raise ValueError(f"{v.view.value}: el modo con marcadores requiere scale_ratio")
        return self


class ViewUpdate(BaseModel):
    """Puntos corregidos de una vista guardada (la foto y la escala R1-R2 ya están en el servidor)."""

    view: View
    landmarks: dict[str, Point]
    calibration: CalibrationIn | None = None
    vertical_line: VerticalLine | None = None
    estimated_points: list[str] = Field(default_factory=list)


class EvaluationUpdate(BaseModel):
    height_cm: float | None = Field(None, ge=50, le=250, description="Solo modo sin marcadores")
    notes: str | None = Field(None, max_length=4000)
    evaluator: str | None = Field(None, max_length=150)
    views: list[ViewUpdate] = Field(default_factory=list, max_length=4)

    @model_validator(mode="after")
    def check(self):
        names = [v.view for v in self.views]
        if len(set(names)) != len(names):
            raise ValueError("Cada vista puede enviarse una sola vez")
        return self


class ViewAnalysisOut(BaseModel):
    view: View
    image_url: str
    overlay_url: str
    image_width: int
    image_height: int
    markers: dict[str, Point]
    derived_points: dict[str, Point]
    calibration: CalibrationIn | None
    vertical_line: VerticalLine | None
    scale_ratio: float
    roll_deg: float
    grid_origin: Point
    grid_step_px: float
    estimated_points: list[str]
    diagnostic: dict[str, str | float | None]
    tables: list[ResultTableOut]


class EvaluationSummary(BaseModel):
    id: int
    patient_id: int
    created_at: UTCDatetime
    mode: Mode
    height_cm: float | None
    views: list[View]
    diagnostic: dict[View, dict[str, str | float | None]] = Field(description="Diagnóstico por vista")
    pending_points: int = Field(0, description="Puntos estimados sin revisar en todas las vistas")
    report_url: str


class EvaluationOut(EvaluationSummary):
    age: int | None
    weight_kg: float | None
    config: AssessmentConfigIn
    notes: str | None
    evaluator: str | None
    photo_consent: bool | None
    patient: PatientOut
    results: list[ViewAnalysisOut]


class HistoryValue(BaseModel):
    direction: str
    value: float


class HistoryRow(BaseModel):
    item: str
    values: list[HistoryValue | None]
    change: float | None = Field(None, description="Último valor menos el primero")


class HistoryTable(BaseModel):
    key: str
    title: str
    unit: str
    rows: list[HistoryRow]


class HistoryDiagnostic(BaseModel):
    key: str
    label: str
    values: list[str | None]


class HistoryEvaluation(BaseModel):
    id: int
    date: UTCDatetime


class HistoryOut(BaseModel):
    view: View
    evaluations: list[HistoryEvaluation]
    tables: list[HistoryTable]
    diagnostic: list[HistoryDiagnostic]
