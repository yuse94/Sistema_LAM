"""Evaluaciones, reporte PDF y exportación a Excel.

TODO (fase 2, ver docs/MIGRACION.md):
- POST /evaluations: guarda paciente + resultados de las vistas + imágenes en storage.
- GET  /evaluations/{id}/report.pdf: porta report_pdf_LAM.py a services/report_pdf.py.
- GET  /evaluations/export.xlsx: porta add_db_LAM.py a services/excel_export.py.
"""
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/evaluations", tags=["evaluaciones"])


@router.get("/{evaluation_id}/report.pdf")
def report_pdf(evaluation_id: int):
    raise HTTPException(501, "Reporte PDF pendiente de portar (report_pdf_LAM.py)")


@router.get("/export.xlsx")
def export_xlsx():
    raise HTTPException(501, "Exportación a Excel pendiente de portar (add_db_LAM.py)")
