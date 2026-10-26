"""Análisis de una fotografía. Reemplaza load_image() + *_assessment() del script de consola."""
from __future__ import annotations

import base64
import io

import numpy as np
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import JSONResponse
from PIL import Image, ImageOps, UnidentifiedImageError

from app.core.config import get_settings
from app.lam import MarkerCountError, View, analyze
from app.lam.overlay import render_overlay
from app.schemas.assessment import AssessmentConfigIn, MarkerCountErrorOut, Point, ViewResultOut

router = APIRouter(prefix="/analysis", tags=["análisis"])


def _to_data_url(img: np.ndarray) -> str:
    buf = io.BytesIO()
    Image.fromarray(img).convert("RGB").save(buf, format="JPEG", quality=85)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


async def _read_image(file: UploadFile) -> np.ndarray:
    data = await file.read()
    if len(data) > get_settings().max_upload_mb * 1024 * 1024:
        raise HTTPException(413, "La imagen supera el tamaño máximo permitido")
    try:
        img = Image.open(io.BytesIO(data))
        img = ImageOps.exif_transpose(img)  # fotos de celular rotadas por EXIF
        return np.asarray(img.convert("RGB"))
    except UnidentifiedImageError as exc:
        raise HTTPException(400, "El archivo no es una imagen válida") from exc


def _run(view: View, image: np.ndarray, config: AssessmentConfigIn) -> ViewResultOut:
    result = analyze(view, image, config.to_domain())
    overlay = render_overlay(result)
    return ViewResultOut.from_domain(result, "data:image/jpeg;base64," + base64.b64encode(overlay).decode())


@router.post("/{view}", response_model=ViewResultOut,
             responses={422: {"model": MarkerCountErrorOut, "description": "Cantidad de marcadores incorrecta"}})
async def analyze_view(view: View, file: UploadFile = File(...),
                       config: AssessmentConfigIn = Depends()):
    """Analiza una fotografía de la vista indicada y devuelve tablas, diagnóstico e imagen resultante.

    No persiste nada: la UI muestra el resultado y luego lo guarda en una evaluación.
    """
    image = await _read_image(file)
    try:
        return await run_in_threadpool(_run, view, image, config)
    except MarkerCountError as err:
        body = MarkerCountErrorOut(
            message=str(err), view=err.view, expected=err.expected, found=err.found,
            points=[Point(x=x, y=y) for x, y in err.points],
            preview_image=_to_data_url(err.image) if err.image is not None else None,
        )
        return JSONResponse(status_code=422, content=body.model_dump(mode="json"))
    except ValueError as err:  # p. ej. no se encontraron R1/R2
        raise HTTPException(422, str(err)) from err
