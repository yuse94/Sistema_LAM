"""Pacientes: ficha, historial de evaluaciones y comparación en el tiempo."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.db.models import Evaluation, Patient
from app.db.session import get_db
from app.lam import View
from app.schemas.evaluation import HistoryOut
from app.schemas.patient import PatientCreate, PatientListItem, PatientOut
from app.services import storage
from app.services.history import HistoryEntry, build_history

router = APIRouter(prefix="/patients", tags=["pacientes"])


def _get(db: Session, patient_id: int) -> Patient:
    patient = db.get(Patient, patient_id)
    if not patient:
        raise HTTPException(404, "Paciente no encontrado")
    return patient


@router.get("", response_model=list[PatientListItem])
def list_patients(q: str | None = None, db: Session = Depends(get_db)):
    """Pacientes con su número de evaluaciones; primero los de actividad más reciente."""
    count = func.count(Evaluation.id)
    last = func.max(Evaluation.created_at)
    stmt = (select(Patient, count, last).outerjoin(Evaluation).group_by(Patient.id)
            .order_by(func.coalesce(last, Patient.created_at).desc()))
    if q:
        stmt = stmt.where(Patient.name.ilike(f"%{q.strip()}%"))
    return [PatientListItem(**PatientOut.model_validate(p).model_dump(), evaluation_count=n, last_evaluation_at=d)
            for p, n, d in db.execute(stmt.limit(500))]


@router.post("", response_model=PatientOut, status_code=201)
def create_patient(data: PatientCreate, db: Session = Depends(get_db)):
    patient = Patient(**data.model_dump())
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient


@router.get("/{patient_id}", response_model=PatientOut)
def get_patient(patient_id: int, db: Session = Depends(get_db)):
    return _get(db, patient_id)


@router.put("/{patient_id}", response_model=PatientOut)
def update_patient(patient_id: int, data: PatientCreate, db: Session = Depends(get_db)):
    patient = _get(db, patient_id)
    for k, v in data.model_dump().items():
        setattr(patient, k, v)
    db.commit()
    db.refresh(patient)
    return patient


@router.delete("/{patient_id}", status_code=204)
def delete_patient(patient_id: int, db: Session = Depends(get_db)):
    """Elimina al paciente con sus evaluaciones y fotografías (derecho de supresión, LOPDP)."""
    patient = _get(db, patient_id)
    ids = [e.id for e in patient.evaluations]
    db.delete(patient)
    db.commit()
    for evaluation_id in ids:
        storage.remove_evaluation(evaluation_id)
    return Response(status_code=204)


@router.get("/{patient_id}/history", response_model=HistoryOut)
def patient_history(patient_id: int, view: View, db: Session = Depends(get_db)):
    """Mediciones de una vista en todas las evaluaciones del paciente, en orden cronológico."""
    _get(db, patient_id)
    stmt = (select(Evaluation).where(Evaluation.patient_id == patient_id)
            .options(selectinload(Evaluation.views)).order_by(Evaluation.created_at))
    entries = [HistoryEntry(e.id, e.created_at, v.diagnostic, v.tables)
               for e in db.scalars(stmt) for v in e.views if v.view == view.value]
    return HistoryOut(view=view, **build_history(entries))
