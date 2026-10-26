"""Modelo de datos. Reemplaza el Excel DB_LAM.xlsx como fuente de verdad;
el Excel pasa a ser una exportación (services/excel_export.py)."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .session import Base


class Patient(Base):
    __tablename__ = "patients"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), index=True)
    age: Mapped[int | None] = mapped_column(Integer)
    gender: Mapped[str | None] = mapped_column(String(1))
    height_cm: Mapped[float | None] = mapped_column(Float)
    weight_kg: Mapped[float | None] = mapped_column(Float)
    occupation: Mapped[str | None] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    evaluations: Mapped[list[Evaluation]] = relationship(back_populates="patient", cascade="all, delete-orphan")


class Evaluation(Base):
    """Una sesión de evaluación postural (hasta tres vistas) y su reporte PDF."""

    __tablename__ = "evaluations"

    id: Mapped[int] = mapped_column(primary_key=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"), index=True)
    config: Mapped[dict] = mapped_column(JSON)  # AssessmentConfig usado
    report_path: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    patient: Mapped[Patient] = relationship(back_populates="evaluations")
    views: Mapped[list[ViewAnalysis]] = relationship(back_populates="evaluation", cascade="all, delete-orphan")


class ViewAnalysis(Base):
    __tablename__ = "view_analyses"

    id: Mapped[int] = mapped_column(primary_key=True)
    evaluation_id: Mapped[int] = mapped_column(ForeignKey("evaluations.id"), index=True)
    view: Mapped[str] = mapped_column(String(20))  # anterior | posterior | lateral_derecha
    original_image_path: Mapped[str] = mapped_column(String(500))
    overlay_image_path: Mapped[str | None] = mapped_column(String(500))
    markers: Mapped[dict] = mapped_column(JSON)
    diagnostic: Mapped[dict] = mapped_column(JSON)
    tables: Mapped[list] = mapped_column(JSON)

    evaluation: Mapped[Evaluation] = relationship(back_populates="views")
