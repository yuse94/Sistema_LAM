"""Evaluaciones guardadas, reporte PDF y exportación a Excel.

Flujo: la interfaz envía las fotos y los puntos tal como quedaron en el editor
(POST /evaluations, multipart). El servidor vuelve a evaluar cada vista, guarda
la foto y el overlay en storage_dir y los resultados en la base de datos. El PDF
y el Excel se generan a pedido a partir de lo guardado.
"""
from __future__ import annotations

from datetime import datetime
from typing import Literal
from urllib.parse import quote

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import FileResponse, Response
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.config import get_settings
from app.db.models import Evaluation, Patient, ViewAnalysis
from app.db.session import get_db
from app.lam import View, evaluate_landmarks, height_scale
from app.lam.catalog import view_shape
from app.lam.overlay import render_overlay
from app.schemas.assessment import AssessmentConfigIn, CalibrationIn, Point, ResultTableOut, vertical_line_tuple
from app.schemas.common import as_utc
from app.schemas.evaluation import EvaluationCreate, EvaluationOut, EvaluationSummary, ViewAnalysisOut, ViewSubmission
from app.schemas.patient import PatientOut
from app.services import images, storage
from app.services.excel_export import ExcelRow, SheetLayout, TableLayout, build_workbook
from app.services.report_pdf import ReportData, ReportView, build_report

router = APIRouter(prefix="/evaluations", tags=["evaluaciones"])

VIEW_ORDER = {v: i for i, v in enumerate(View)}


# --- Conversión ORM -> esquemas ------------------------------------------------------------

def _file_url(evaluation_id: int, view: str, kind: str) -> str:
    return f"/api/evaluations/{evaluation_id}/views/{view}/{kind}"


def _pt(p) -> Point:
    return Point(x=p[0], y=p[1])


def _summary(e: Evaluation) -> EvaluationSummary:
    return EvaluationSummary(
        id=e.id, patient_id=e.patient_id, created_at=e.created_at, mode=e.mode, height_cm=e.height_cm,
        views=[v.view for v in e.views], diagnostic={v.view: v.diagnostic for v in e.views},
        pending_points=sum(len(v.estimated_points or []) for v in e.views),
        report_url=f"/api/evaluations/{e.id}/report.pdf",
    )


def _view_out(e: Evaluation, v: ViewAnalysis) -> ViewAnalysisOut:
    cal = v.calibration
    return ViewAnalysisOut(
        view=v.view, image_url=_file_url(e.id, v.view, "image"), overlay_url=_file_url(e.id, v.view, "overlay"),
        image_width=v.image_width, image_height=v.image_height,
        markers={k: _pt(p) for k, p in v.markers.items()},
        derived_points={k: _pt(p) for k, p in v.derived_points.items()},
        calibration=CalibrationIn(vertex=_pt(cal["vertex"]), floor=_pt(cal["floor"])) if cal else None,
        vertical_line=(_pt(v.vertical_line[0]), _pt(v.vertical_line[1])) if v.vertical_line else None,
        scale_ratio=v.scale_ratio, roll_deg=v.roll_deg, grid_origin=_pt(v.grid_origin), grid_step_px=v.grid_step_px,
        estimated_points=v.estimated_points or [], diagnostic=v.diagnostic,
        tables=[ResultTableOut(**t) for t in v.tables],
    )


def _out(e: Evaluation) -> EvaluationOut:
    return EvaluationOut(
        **_summary(e).model_dump(), age=e.age, weight_kg=e.weight_kg, config=AssessmentConfigIn(**e.config),
        notes=e.notes, patient=PatientOut.model_validate(e.patient), results=[_view_out(e, v) for v in e.views],
    )


def _get(db: Session, evaluation_id: int) -> Evaluation:
    e = db.get(Evaluation, evaluation_id, options=[selectinload(Evaluation.views), selectinload(Evaluation.patient)])
    if not e:
        raise HTTPException(404, "Evaluación no encontrada")
    return e


def _local(d: datetime) -> datetime:
    """Fecha guardada (UTC) en la hora local del servidor, para reportes y Excel."""
    return as_utc(d).astimezone()


# --- Guardar --------------------------------------------------------------------------------

def _process(sub: ViewSubmission, raw: bytes, payload: EvaluationCreate) -> dict:
    """Vuelve a evaluar una vista con los puntos del editor y prepara los archivos."""
    image = images.decode(raw)
    h, w = image.shape[:2]
    line = vertical_line_tuple(sub.vertical_line)
    if payload.mode == "pose":
        cal = sub.calibration.to_domain()
        scale = height_scale(payload.height_cm, cal.vertex, cal.floor, line)
    else:
        scale = sub.scale_ratio
    landmarks = {k: p.as_tuple() for k, p in sub.landmarks.items()}
    result = evaluate_landmarks(sub.view, landmarks, scale, payload.config.to_domain(), image=image,
                                vertical_line=line)
    estimated = [p for p in sub.estimated_points if p in result.markers]
    return {
        "result": result, "estimated": estimated, "width": w, "height": h,
        "image_jpeg": images.encode_jpeg(image), "overlay_jpeg": render_overlay(result, estimated=estimated),
    }


def _process_all(payload: EvaluationCreate, raws: list[bytes]) -> list[dict]:
    out = []
    for sub, raw in zip(payload.views, raws):
        try:
            out.append(_process(sub, raw, payload))
        except ValueError as err:  # imagen inválida, faltan puntos, escala imposible...
            raise HTTPException(422, f"{sub.view.value}: {err}") from err
    return out


@router.post("", response_model=EvaluationOut, status_code=201)
async def create_evaluation(data: str = Form(..., description="EvaluationCreate en JSON"),
                            images_: list[UploadFile] = File(..., alias="images",
                                                             description="Una foto por vista, en el orden de views"),
                            db: Session = Depends(get_db)):
    try:
        payload = EvaluationCreate.model_validate_json(data)
    except ValidationError as err:
        detail = [{"loc": e["loc"], "msg": e["msg"].removeprefix("Value error, "), "type": e["type"]}
                  for e in err.errors(include_url=False)]
        raise HTTPException(422, detail) from err
    if len(images_) != len(payload.views):
        raise HTTPException(422, "Debe enviarse una fotografía por cada vista")
    patient = db.get(Patient, payload.patient_id)
    if not patient:
        raise HTTPException(404, "Paciente no encontrado")

    max_bytes = get_settings().max_upload_mb * 1024 * 1024
    raws = []
    for f in images_:
        raw = await f.read()
        if len(raw) > max_bytes:
            raise HTTPException(413, "Una de las imágenes supera el tamaño máximo permitido")
        raws.append(raw)
    processed = await run_in_threadpool(_process_all, payload, raws)

    evaluation = Evaluation(
        patient=patient, mode=payload.mode, age=patient.age, height_cm=payload.height_cm or patient.height_cm,
        weight_kg=patient.weight_kg, config=payload.config.model_dump(),
        notes=(payload.notes or "").strip() or None,
    )
    db.add(evaluation)
    db.flush()  # asigna el id para la carpeta de archivos
    folder = storage.evaluation_folder(evaluation.id)
    storage.remove_evaluation(evaluation.id)  # restos de un intento fallido con el mismo id
    try:
        for sub, pr in sorted(zip(payload.views, processed), key=lambda x: VIEW_ORDER[x[0].view]):
            r = pr["result"]
            name = sub.view.value
            evaluation.views.append(ViewAnalysis(
                view=name,
                image_path=storage.write(folder / f"{name}.jpg", pr["image_jpeg"]),
                overlay_path=storage.write(folder / f"{name}_overlay.jpg", pr["overlay_jpeg"]),
                image_width=pr["width"], image_height=pr["height"],
                markers={k: list(p) for k, p in r.markers.items()},
                derived_points={k: list(p) for k, p in r.derived_points.items()},
                calibration=({"vertex": list(sub.calibration.vertex.as_tuple()),
                              "floor": list(sub.calibration.floor.as_tuple())} if sub.calibration else None),
                vertical_line=[list(p.as_tuple()) for p in sub.vertical_line] if sub.vertical_line else None,
                scale_ratio=r.scale_ratio, roll_deg=r.roll_deg, grid_origin=list(r.grid_origin),
                grid_step_px=r.grid_step_px, estimated_points=pr["estimated"], diagnostic=r.diagnostic,
                tables=[{"key": t.key, "title": t.title, "columns": list(t.columns),
                         "rows": [vars(row) for row in t.rows]} for t in r.tables],
            ))
        if payload.mode == "pose" and payload.height_cm:
            patient.height_cm = payload.height_cm  # la estatura más reciente queda en la ficha
        db.commit()
    except Exception:
        db.rollback()
        storage.remove_evaluation(evaluation.id)
        raise
    return _out(_get(db, evaluation.id))


# --- Consultar ------------------------------------------------------------------------------

@router.get("", response_model=list[EvaluationSummary])
def list_evaluations(patient_id: int | None = None, db: Session = Depends(get_db)):
    stmt = select(Evaluation).options(selectinload(Evaluation.views)).order_by(Evaluation.created_at.desc())
    if patient_id is not None:
        stmt = stmt.where(Evaluation.patient_id == patient_id)
    return [_summary(e) for e in db.scalars(stmt.limit(500))]


def _excel_layouts() -> dict[str, SheetLayout]:
    layouts = {}
    for view in View:
        tables, diag_keys = view_shape(view)
        layouts[view.value] = SheetLayout(tuple(TableLayout(t.title, t.columns, t.items) for t in tables), diag_keys)
    return layouts


@router.get("/export.xlsx", response_class=Response,
            responses={200: {"content": {"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": {}}}})
def export_xlsx(request: Request, patient_id: int | None = None, db: Session = Depends(get_db)):
    """Libro con una hoja por vista y una fila por evaluación (todas, o las de un paciente)."""
    stmt = select(Evaluation).options(selectinload(Evaluation.views), selectinload(Evaluation.patient))
    if patient_id is not None:
        stmt = stmt.where(Evaluation.patient_id == patient_id)
    base = str(request.base_url).rstrip("/")
    rows = []
    for e in db.scalars(stmt):
        p = e.patient
        patient = {"name": p.name, "age": e.age, "gender": p.gender, "weight_kg": e.weight_kg,
                   "occupation": p.occupation}
        for v in e.views:
            rows.append(ExcelRow(
                view=v.view, evaluation_id=e.id, date=_local(e.created_at), mode=e.mode, patient=patient,
                diagnostic=v.diagnostic, tables=v.tables, height_cm=e.height_cm,
                report_url=f"{base}/api/evaluations/{e.id}/report.pdf",
                image_url=f"{base}{_file_url(e.id, v.view, 'overlay')}",
            ))
    content = build_workbook(rows, _excel_layouts())
    name = f"DB_LAM_{datetime.now():%Y%m%d}.xlsx"
    return Response(content, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    headers={"Content-Disposition": f'attachment; filename="{name}"'})


@router.get("/{evaluation_id}", response_model=EvaluationOut)
def get_evaluation(evaluation_id: int, db: Session = Depends(get_db)):
    return _out(_get(db, evaluation_id))


@router.delete("/{evaluation_id}", status_code=204)
def delete_evaluation(evaluation_id: int, db: Session = Depends(get_db)):
    e = _get(db, evaluation_id)
    db.delete(e)
    db.commit()
    storage.remove_evaluation(evaluation_id)
    return Response(status_code=204)


@router.get("/{evaluation_id}/views/{view}/{kind}", response_class=FileResponse)
def view_file(evaluation_id: int, view: View, kind: Literal["image", "overlay"], db: Session = Depends(get_db)):
    """Foto original (orientada) u overlay con puntos y cuadrícula."""
    v = db.scalar(select(ViewAnalysis).where(ViewAnalysis.evaluation_id == evaluation_id,
                                             ViewAnalysis.view == view.value))
    if not v:
        raise HTTPException(404, "Vista no encontrada")
    path = storage.path_of(v.image_path if kind == "image" else v.overlay_path)
    if not path.is_file():
        raise HTTPException(404, "Archivo no encontrado")
    return FileResponse(path, media_type="image/jpeg", headers={"Cache-Control": "private, max-age=86400"})


def _content_disposition(filename: str, download: bool) -> str:
    ascii_name = filename.encode("ascii", "ignore").decode() or "reporte.pdf"
    kind = "attachment" if download else "inline"
    return f'{kind}; filename="{ascii_name}"; filename*=UTF-8\'\'{quote(filename)}'


@router.get("/{evaluation_id}/report.pdf", response_class=Response,
            responses={200: {"content": {"application/pdf": {}}}})
def report_pdf(evaluation_id: int, download: bool = False, db: Session = Depends(get_db)):
    e = _get(db, evaluation_id)
    p = e.patient
    data = ReportData(
        patient={"name": p.name, "age": e.age, "gender": p.gender, "height_cm": e.height_cm,
                 "weight_kg": e.weight_kg, "occupation": p.occupation},
        date=_local(e.created_at), mode=e.mode, config=e.config, height_cm=e.height_cm, notes=e.notes,
        evaluation_id=e.id,
        views=[ReportView(view=v.view, diagnostic=v.diagnostic, tables=v.tables,
                          overlay_jpeg=storage.read(v.overlay_path), estimated_points=v.estimated_points or [],
                          scale_ratio=v.scale_ratio, roll_deg=v.roll_deg) for v in e.views],
    )
    pdf = build_report(data)
    filename = f"LAM_{p.name.replace(' ', '_')}_{data.date:%Y%m%d}.pdf"
    return Response(pdf, media_type="application/pdf",
                    headers={"Content-Disposition": _content_disposition(filename, download)})
