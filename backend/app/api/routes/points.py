"""Diccionario de puntos anatómicos."""
from fastapi import APIRouter, HTTPException

from app.lam.catalog import catalog
from app.schemas.points import PointOut

router = APIRouter(prefix="/points", tags=["diccionario de puntos"])


@router.get("", response_model=list[PointOut])
def list_points():
    """Todos los puntos: definición, cómo localizarlos, silueta y mediciones en las que intervienen."""
    return [PointOut.from_domain(p) for p in catalog()]


@router.get("/{point_id}", response_model=PointOut)
def get_point(point_id: str):
    for p in catalog():
        if p.id.upper() == point_id.upper():
            return PointOut.from_domain(p)
    raise HTTPException(404, f"No existe el punto {point_id}")
