"""Modelo de datos. Reemplaza el Excel DB_LAM.xlsx como fuente de verdad;
el Excel pasa a ser una exportación (services/excel_export.py)."""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .session import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Patient(Base):
    __tablename__ = "patients"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), index=True)
    age: Mapped[int | None] = mapped_column(Integer)
    gender: Mapped[str | None] = mapped_column(String(1))
    height_cm: Mapped[float | None] = mapped_column(Float)
    weight_kg: Mapped[float | None] = mapped_column(Float)
    occupation: Mapped[str | None] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, server_default=func.now())

    evaluations: Mapped[list[Evaluation]] = relationship(back_populates="patient", cascade="all, delete-orphan",
                                                         order_by="Evaluation.created_at")


class Evaluation(Base):
    """Una sesión de evaluación postural (de una a cuatro vistas).

    Edad, estatura y peso se copian del paciente al guardar: el reporte de una
    evaluación antigua debe mostrar los datos de ese momento.
    """

    __tablename__ = "evaluations"

    id: Mapped[int] = mapped_column(primary_key=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, server_default=func.now(),
                                                 index=True)
    mode: Mapped[str] = mapped_column(String(10))  # pose | markers
    age: Mapped[int | None] = mapped_column(Integer)
    height_cm: Mapped[float | None] = mapped_column(Float)
    weight_kg: Mapped[float | None] = mapped_column(Float)
    config: Mapped[dict] = mapped_column(JSON)  # AssessmentConfig usado
    notes: Mapped[str | None] = mapped_column(Text)
    evaluator: Mapped[str | None] = mapped_column(String(150))
    # El paciente autorizó el uso de sus fotografías (se exige al guardar; None en evaluaciones antiguas)
    photo_consent: Mapped[bool | None] = mapped_column(Boolean)

    patient: Mapped[Patient] = relationship(back_populates="evaluations")
    views: Mapped[list[ViewAnalysis]] = relationship(back_populates="evaluation", cascade="all, delete-orphan",
                                                     order_by="ViewAnalysis.id")


class ViewAnalysis(Base):
    """Una vista evaluada: foto, puntos revisados por el evaluador y resultados.

    Con la foto, los puntos, la calibración y la línea vertical se puede volver a
    evaluar la vista (por ejemplo con otras tolerancias) sin repetir la detección.
    """

    __tablename__ = "view_analyses"

    id: Mapped[int] = mapped_column(primary_key=True)
    evaluation_id: Mapped[int] = mapped_column(ForeignKey("evaluations.id"), index=True)
    view: Mapped[str] = mapped_column(String(20))  # anterior | posterior | lateral_derecha | lateral_izquierda
    image_path: Mapped[str] = mapped_column(String(500))  # relativo a storage_dir
    overlay_path: Mapped[str] = mapped_column(String(500))
    image_width: Mapped[int] = mapped_column(Integer)
    image_height: Mapped[int] = mapped_column(Integer)
    markers: Mapped[dict] = mapped_column(JSON)  # id -> [x, y] en píxeles de la foto
    derived_points: Mapped[dict] = mapped_column(JSON)
    calibration: Mapped[dict | None] = mapped_column(JSON)  # {vertex: [x, y], floor: [x, y]}
    vertical_line: Mapped[list | None] = mapped_column(JSON)  # [[x, y], [x, y]]
    scale_ratio: Mapped[float] = mapped_column(Float)  # cm por píxel
    roll_deg: Mapped[float] = mapped_column(Float, default=0.0)
    grid_origin: Mapped[list] = mapped_column(JSON)
    grid_step_px: Mapped[float] = mapped_column(Float)
    estimated_points: Mapped[list] = mapped_column(JSON, default=list)  # estimados que no se revisaron
    diagnostic: Mapped[dict] = mapped_column(JSON)
    tables: Mapped[list] = mapped_column(JSON)

    evaluation: Mapped[Evaluation] = relationship(back_populates="views")
