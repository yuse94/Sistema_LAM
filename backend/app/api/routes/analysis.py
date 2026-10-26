"""Análisis por vista. Reemplaza load_image() + *_assessment() del script de consola.

Flujo en la interfaz:
1. POST /analysis/{vista} con la foto -> puntos detectados, tablas e imagen enderezada.
2. El evaluador revisa y arrastra los puntos que hagan falta.
3. POST /analysis/{vista}/evaluate con los puntos corregidos -> tablas recalculadas.
"""
from __future__ import annotations

import base64
import io

import numpy as np
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import JSONResponse
from PIL import Image, ImageOps, UnidentifiedImageError

from app.core.config import get_settings
from app.lam import SPECS, MarkerCountError, View, analyze, evaluate_landmarks
from app.schemas.assessment import (
    AssessmentConfigIn,
    EvaluateIn,
    MarkerCountErrorOut,
    Point,
    ViewInfo,
    ViewResultOut,
)

router = APIRouter(prefix="/analysis", tags=["análisis"])


def _to_data_url(img: np.ndarray) -> str:
    buf = io.BytesIO()
    Image.fromarray(img).convert("RGB").save(buf, format="JPEG", quality=90)
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
    return ViewResultOut.from_domain(result, _to_data_url(result.image))


@router.get("/views", response_model=list[ViewInfo])
def list_views():
    """Puntos anatómicos de cada vista, con su nombre, para mostrarlos en la interfaz."""
    return [ViewInfo(view=v, labels=s.labels, expected_markers=s.expected_markers) for v, s in SPECS.items()]


@router.post("/{view}", response_model=ViewResultOut,
             responses={422: {"model": MarkerCountErrorOut, "description": "Cantidad de marcadores incorrecta"}})
async def analyze_view(view: View, file: UploadFile = File(...),
                       config: AssessmentConfigIn = Depends()):
    """Detecta los marcadores de la fotografía y devuelve puntos, tablas, diagnóstico e imagen.

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


@router.post("/{view}/evaluate", response_model=ViewResultOut)
def evaluate_view(view: View, data: EvaluateIn):
    """Recalcula tablas y diagnóstico con puntos ajustados manualmente (sin volver a subir la foto)."""
    landmarks = {k: (p.x, p.y) for k, p in data.landmarks.items()}
    try:
        result = evaluate_landmarks(view, landmarks, data.scale_ratio, data.config.to_domain())
    except ValueError as err:
        raise HTTPException(422, str(err)) from err
    return ViewResultOut.from_domain(result)
