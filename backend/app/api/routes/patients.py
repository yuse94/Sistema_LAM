from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Patient
from app.db.session import get_db
from app.schemas.patient import PatientCreate, PatientOut

router = APIRouter(prefix="/patients", tags=["pacientes"])


@router.get("", response_model=list[PatientOut])
def list_patients(q: str | None = None, db: Session = Depends(get_db)):
    stmt = select(Patient).order_by(Patient.created_at.desc())
    if q:
        stmt = stmt.where(Patient.name.ilike(f"%{q}%"))
    return db.scalars(stmt).all()


@router.post("", response_model=PatientOut, status_code=201)
def create_patient(data: PatientCreate, db: Session = Depends(get_db)):
    patient = Patient(**data.model_dump())
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient


@router.get("/{patient_id}", response_model=PatientOut)
def get_patient(patient_id: int, db: Session = Depends(get_db)):
    patient = db.get(Patient, patient_id)
    if not patient:
        raise HTTPException(404, "Paciente no encontrado")
    return patient
