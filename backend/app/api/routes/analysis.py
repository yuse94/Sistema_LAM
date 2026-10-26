"""Análisis por vista. Reemplaza load_image() + *_assessment() del script de consola.

Flujo en la interfaz:
1. Detección:
   - sin marcadores: MediaPipe corre en el navegador y envía sus 33 puntos a
     POST /analysis/{vista}/pose junto con la estatura del paciente;
   - con marcadores verdes: POST /analysis/{vista} con la foto.
2. El evaluador revisa y arrastra los puntos (los estimados aparecen resaltados),
   ajusta el vértice y el suelo, y marca la línea vertical de referencia.
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
from app.lam import SPECS, MarkerCountError, View, analyze, analyze_pose, evaluate_landmarks, height_scale
from app.schemas.assessment import (
    AssessmentConfigIn,
    CalibrationIn,
    EvaluateIn,
    MarkerCountErrorOut,
    Point,
    PoseIn,
    ViewInfo,
    ViewResultOut,
    vertical_line_tuple,
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


@router.post("/{view}/pose", response_model=ViewResultOut)
def analyze_view_from_pose(view: View, data: PoseIn):
    """Modo sin marcadores: puntos de MediaPipe + estatura -> puntos LAM, tablas y diagnóstico.

    Los puntos sin equivalente en MediaPipe se estiman y se listan en estimated_points.
    """
    try:
        analysis = analyze_pose(view, data.pose_points(), data.height_cm, data.config.to_domain(),
                                data.calibration.to_domain() if data.calibration else None,
                                vertical_line_tuple(data.vertical_line))
    except ValueError as err:
        raise HTTPException(422, str(err)) from err
    out = ViewResultOut.from_domain(analysis.result)
    out.estimated_points = analysis.estimated
    cal = analysis.calibration
    out.calibration = CalibrationIn(vertex=Point(x=cal.vertex[0], y=cal.vertex[1]),
                                    floor=Point(x=cal.floor[0], y=cal.floor[1]))
    return out


@router.post("/{view}/evaluate", response_model=ViewResultOut)
def evaluate_view(view: View, data: EvaluateIn):
    """Recalcula tablas y diagnóstico con puntos ajustados manualmente (sin volver a subir la foto)."""
    landmarks = {k: p.as_tuple() for k, p in data.landmarks.items()}
    line = vertical_line_tuple(data.vertical_line)
    try:
        if data.height_cm is not None and data.calibration is not None:
            cal = data.calibration.to_domain()
            scale = height_scale(data.height_cm, cal.vertex, cal.floor, line)
        else:
            scale = data.scale_ratio
        result = evaluate_landmarks(view, landmarks, scale, data.config.to_domain(), vertical_line=line)
    except ValueError as err:
        raise HTTPException(422, str(err)) from err
    out = ViewResultOut.from_domain(result)
    out.calibration = data.calibration
    return out
