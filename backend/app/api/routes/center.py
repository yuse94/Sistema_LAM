"""Datos del centro (encabezado del reporte PDF)."""
from __future__ import annotations

from fastapi import APIRouter, File, HTTPException, Response, UploadFile
from pydantic import BaseModel

from app.services import center

router = APIRouter(prefix="/center", tags=["centro"])


class CenterOut(center.CenterInfo):
    logo_url: str | None = None


class LogoOut(BaseModel):
    logo_url: str


def _out(info: center.CenterInfo) -> CenterOut:
    has_logo = center.logo() is not None
    return CenterOut(**info.model_dump(), logo_url="/api/center/logo" if has_logo else None)


@router.get("", response_model=CenterOut)
def get_center():
    return _out(center.load())


@router.put("", response_model=CenterOut)
def update_center(data: center.CenterInfo):
    return _out(center.save(data))


@router.get("/logo", response_class=Response, responses={200: {"content": {"image/png": {}}}})
def get_logo():
    data = center.logo()
    if data is None:
        raise HTTPException(404, "El centro no tiene logo")
    return Response(data, media_type="image/png", headers={"Cache-Control": "no-cache"})


@router.put("/logo", response_model=LogoOut)
async def upload_logo(file: UploadFile = File(...)):
    data = await file.read()
    if len(data) > 5 * 1024 * 1024:
        raise HTTPException(413, "El logo debe pesar menos de 5 MB")
    try:
        center.save_logo(data)
    except ValueError as err:
        raise HTTPException(422, str(err)) from err
    return LogoOut(logo_url="/api/center/logo")


@router.delete("/logo", status_code=204)
def delete_logo():
    center.delete_logo()
    return Response(status_code=204)
