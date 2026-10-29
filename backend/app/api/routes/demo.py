"""Paciente de demostración para presentar la app sin evaluar a nadie en vivo."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.routes.evaluations import VIEW_ORDER, _evaluate_view, _fill
from app.db.models import Evaluation, Patient, ViewAnalysis
from app.db.session import get_db
from app.lam import View
from app.schemas.assessment import AssessmentConfigIn, CalibrationIn, Point
from app.schemas.patient import PatientOut
from app.services import images, storage
from app.services.demo import HEIGHT_CM, demo_views

router = APIRouter(prefix="/demo", tags=["demostración"])

DEMO_NAME = "Paciente De Demostración"
NOTES = ("Datos de ejemplo generados por la aplicación con siluetas dibujadas; no corresponden a una "
         "persona real. {}")


@router.post("", response_model=PatientOut)
def create_demo(db: Session = Depends(get_db)):
    """Crea (una sola vez) un paciente con dos evaluaciones separadas por tres meses."""
    existing = db.scalar(select(Patient).where(Patient.name == DEMO_NAME))
    if existing:
        return existing
    patient = Patient(name=DEMO_NAME, age=34, gender="F", height_cm=HEIGHT_CM, weight_kg=61,
                      occupation="Oficinista")
    db.add(patient)
    db.flush()
    now = datetime.now(timezone.utc)
    config = AssessmentConfigIn()
    plans = [(now - timedelta(days=91), "Evaluación inicial: molestias cervicales al final de la jornada."),
             (now - timedelta(days=1), "Control después de 12 sesiones de ejercicios posturales.")]
    created: list[int] = []
    try:
        for index, (date, note) in enumerate(plans):
            ev = Evaluation(patient=patient, mode="pose", age=patient.age, height_cm=HEIGHT_CM,
                            weight_kg=patient.weight_kg, config=config.model_dump(), notes=NOTES.format(note),
                            evaluator="Evaluador de demostración", photo_consent=True, created_at=date)
            db.add(ev)
            db.flush()
            created.append(ev.id)
            folder = storage.evaluation_folder(ev.id)
            for v in sorted(demo_views(index), key=lambda x: VIEW_ORDER[View(x["view"])]):
                cal = v["calibration"]
                result = _evaluate_view(
                    View(v["view"]), images.decode(v["image_jpeg"]),
                    {k: Point(x=x, y=y) for k, (x, y) in v["landmarks"].items()}, mode="pose", height_cm=HEIGHT_CM,
                    calibration=CalibrationIn(vertex=Point(x=cal["vertex"][0], y=cal["vertex"][1]),
                                              floor=Point(x=cal["floor"][0], y=cal["floor"][1])),
                    vertical_line=None, scale_ratio=None, config=config, estimated=[])
                row = ViewAnalysis(
                    view=v["view"], image_width=800, image_height=1600,
                    image_path=storage.write(folder / f"{v['view']}.jpg", v["image_jpeg"]),
                    overlay_path=storage.write(folder / f"{v['view']}_overlay.jpg", result["overlay_jpeg"]),
                )
                _fill(row, result)
                ev.views.append(row)
        db.commit()
    except Exception:
        db.rollback()
        for evaluation_id in created:
            storage.remove_evaluation(evaluation_id)
        raise
    db.refresh(patient)
    return patient
