from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.common import UTCDatetime


class PatientBase(BaseModel):
    name: str = Field("Anónimo", max_length=200)
    age: int | None = Field(None, gt=0, lt=130)
    gender: Literal["M", "F"] | None = None
    height_cm: float | None = Field(None, gt=0, lt=300)
    weight_kg: float | None = Field(None, gt=0, lt=500)
    occupation: str | None = Field(None, max_length=200)

    @field_validator("name")
    @classmethod
    def normalize_name(cls, v: str) -> str:
        v = " ".join(v.split()).title()
        return v or "Anónimo"

    @field_validator("occupation")
    @classmethod
    def normalize_occupation(cls, v: str | None) -> str | None:
        v = " ".join(v.split()) if v else ""
        return v or None


class PatientCreate(PatientBase):
    pass


class PatientOut(PatientBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: UTCDatetime


class PatientListItem(PatientOut):
    evaluation_count: int = 0
    last_evaluation_at: UTCDatetime | None = None
