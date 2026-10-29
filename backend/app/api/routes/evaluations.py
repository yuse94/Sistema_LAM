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
from app.schemas.evaluation import EvaluationCreate, EvaluationOut, EvaluationSummary, EvaluationUpdate, ViewAnalysisOut
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

def _evaluate_view(view: View, image, landmarks: dict, *, mode: str, height_cm: float | None,
                   calibration: CalibrationIn | None, vertical_line, scale_ratio: float | None,
                   config: AssessmentConfigIn, estimated: list[str]) -> dict:
    """Evalúa una vista con los puntos del editor y dibuja el overlay."""
    line = vertical_line_tuple(vertical_line)
    if mode == "pose":
        if calibration is None or height_cm is None:
            raise ValueError("el modo sin marcadores requiere la estatura y la calibración")
        cal = calibration.to_domain()
        scale = height_scale(height_cm, cal.vertex, cal.floor, line)
    else:
        scale = scale_ratio
    result = evaluate_landmarks(view, {k: p.as_tuple() for k, p in landmarks.items()}, scale, config.to_domain(),
                                image=image, vertical_line=line)
    pending = [p for p in estimated if p in result.markers]
    return {"result": result, "estimated": pending, "overlay_jpeg": render_overlay(result, estimated=pending),
            "calibration": calibration, "vertical_line": vertical_line}


def _fill(v: ViewAnalysis, ev: dict) -> None:
    """Copia a la fila los puntos y resultados de una evaluación de vista."""
    r, cal, line = ev["result"], ev["calibration"], ev["vertical_line"]
    v.markers = {k: list(p) for k, p in r.markers.items()}
    v.derived_points = {k: list(p) for k, p in r.derived_points.items()}
    v.calibration = {"vertex": list(cal.vertex.as_tuple()), "floor": list(cal.floor.as_tuple())} if cal else None
    v.vertical_line = [list(p.as_tuple()) for p in line] if line else None
    v.scale_ratio, v.roll_deg = r.scale_ratio, r.roll_deg
    v.grid_origin, v.grid_step_px = list(r.grid_origin), r.grid_step_px
    v.estimated_points, v.diagnostic = ev["estimated"], r.diagnostic
    v.tables = [{"key": t.key, "title": t.title, "columns": list(t.columns), "rows": [vars(row) for row in t.rows]}
                for t in r.tables]


def _process_all(payload: EvaluationCreate, raws: list[bytes]) -> list[dict]:
    out = []
    for sub, raw in zip(payload.views, raws):
        try:
            image = images.decode(raw)
            ev = _evaluate_view(sub.view, image, sub.landmarks, mode=payload.mode, height_cm=payload.height_cm,
                                calibration=sub.calibration, vertical_line=sub.vertical_line,
                                scale_ratio=sub.scale_ratio, config=payload.config,
                                estimated=sub.estimated_points)
        except ValueError as err:  # imagen inválida, faltan puntos, escala imposible...
            raise HTTPException(422, f"{sub.view.value}: {err}") from err
        ev.update(image_jpeg=images.encode_jpeg(image), width=image.shape[1], height=image.shape[0])
        out.append(ev)
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
        for sub, ev in sorted(zip(payload.views, processed), key=lambda x: VIEW_ORDER[x[0].view]):
            name = sub.view.value
            v = ViewAnalysis(
                view=name,
                image_path=storage.write(folder / f"{name}.jpg", ev["image_jpeg"]),
                overlay_path=storage.write(folder / f"{name}_overlay.jpg", ev["overlay_jpeg"]),
                image_width=ev["width"], image_height=ev["height"],
            )
            _fill(v, ev)
            evaluation.views.append(v)
        if payload.mode == "pose" and payload.height_cm:
            patient.height_cm = payload.height_cm  # la estatura más reciente queda en la ficha
        db.commit()
    except Exception:
        db.rollback()
        storage.remove_evaluation(evaluation.id)
        raise
    return _out(_get(db, evaluation.id))


def _stored_calibration(v: ViewAnalysis) -> CalibrationIn | None:
    c = v.calibration
    return CalibrationIn(vertex=_pt(c["vertex"]), floor=_pt(c["floor"])) if c else None


def _reevaluate(e: Evaluation, data: EvaluationUpdate) -> dict[str, dict]:
    by_view = {v.view: v for v in e.views}
    updates = {u.view.value: u for u in data.views}
    missing = [name for name in updates if name not in by_view]
    if missing:
        raise HTTPException(422, f"La evaluación no tiene la vista: {', '.join(missing)}")
    height = data.height_cm if e.mode == "pose" and data.height_cm else e.height_cm
    # Con otra estatura cambia la escala de todas las vistas del modo sin marcadores
    targets = list(by_view) if e.mode == "pose" and height != e.height_cm else list(updates)
    config = AssessmentConfigIn(**e.config)
    out = {}
    for name in targets:
        v, u = by_view[name], updates.get(name)
        if u:
            landmarks, cal, line, estimated = u.landmarks, u.calibration, u.vertical_line, u.estimated_points
        else:
            landmarks = {k: _pt(p) for k, p in v.markers.items()}
            cal = _stored_calibration(v)
            line = (_pt(v.vertical_line[0]), _pt(v.vertical_line[1])) if v.vertical_line else None
            estimated = v.estimated_points or []
        try:
            image = images.decode(storage.read(v.image_path))
            out[name] = _evaluate_view(View(name), image, landmarks, mode=e.mode, height_cm=height, calibration=cal,
                                       vertical_line=line, scale_ratio=v.scale_ratio, config=config,
                                       estimated=estimated)
        except (ValueError, OSError) as err:
            raise HTTPException(422, f"{name}: {err}") from err
    return out


@router.put("/{evaluation_id}", response_model=EvaluationOut)
def update_evaluation(evaluation_id: int, data: EvaluationUpdate, db: Session = Depends(get_db)):
    """Corrige una evaluación guardada: puntos de una o más vistas, estatura u observaciones.

    Se vuelve a evaluar con la foto guardada, la configuración y, con marcadores, la
    escala R1-R2 de la evaluación original. El reporte PDF y el Excel reflejan el cambio.
    """
    e = _get(db, evaluation_id)
    results = _reevaluate(e, data)
    for v in e.views:
        if v.view in results:
            storage.write(v.overlay_path, results[v.view]["overlay_jpeg"])
            _fill(v, results[v.view])
    if e.mode == "pose" and data.height_cm:
        e.height_cm = data.height_cm
    if "notes" in data.model_fields_set:
        e.notes = (data.notes or "").strip() or None
    db.commit()
    return _out(_get(db, evaluation_id))


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
    """Foto original (orientada) u overlay con puntos y cuadrícula.

    no-cache: el navegador revalida (ETag) porque el overlay cambia al corregir puntos.
    """
    v = db.scalar(select(ViewAnalysis).where(ViewAnalysis.evaluation_id == evaluation_id,
                                             ViewAnalysis.view == view.value))
    if not v:
        raise HTTPException(404, "Vista no encontrada")
    path = storage.path_of(v.image_path if kind == "image" else v.overlay_path)
    if not path.is_file():
        raise HTTPException(404, "Archivo no encontrado")
    return FileResponse(path, media_type="image/jpeg", headers={"Cache-Control": "private, no-cache"})


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
