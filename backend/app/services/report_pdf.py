"""Reporte PDF de una evaluación postural (porta report_pdf_LAM.py).

Recibe datos planos (ReportData) y devuelve los bytes del PDF: no lee rutas del
disco ni depende de la base de datos, así se puede probar de forma aislada.

Cambios respecto a la versión de consola:
- La fecha del encabezado es la de la evaluación, no la del momento de imprimir.
- Incluye la vista lateral izquierda, el modo de detección y la escala usada.
- Avisa si quedaron puntos estimados sin revisar.
"""
from __future__ import annotations

import io
from dataclasses import dataclass, field
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.platypus import (CondPageBreak, Image, KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer,
                                Table, TableStyle)

from .labels import (DIRECTION_LEGEND, MODE_LABELS, VIEW_TITLES, diagnostic_lines, format_value, table_reference,
                     table_unit)

PRIMARY = colors.HexColor("#0e7c74")
PRIMARY_LIGHT = colors.HexColor("#e6f2f1")
MUTED = colors.HexColor("#5b6670")
RULE = colors.HexColor("#d5dadf")
WARN = colors.HexColor("#b45309")

MONTHS = ("enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre",
          "noviembre", "diciembre")


@dataclass
class ReportView:
    view: str
    diagnostic: dict
    tables: list[dict]  # {key, title, columns, rows: [{item, direction, value}]}
    overlay_jpeg: bytes | None = None
    estimated_points: list[str] = field(default_factory=list)
    scale_ratio: float | None = None
    roll_deg: float = 0.0


@dataclass
class ReportData:
    patient: dict  # name, age, gender, height_cm, weight_kg, occupation
    date: datetime
    mode: str  # pose | markers
    config: dict  # tolerance_angle, tolerance_distance, grid_size...
    views: list[ReportView]
    height_cm: float | None = None
    notes: str | None = None
    evaluation_id: int | None = None
    evaluator: str | None = None
    center: dict | None = None  # name, contact
    logo_png: bytes | None = None


def long_date(d: datetime) -> str:
    return f"{d.day} de {MONTHS[d.month - 1]} de {d.year}"


def _styles():
    base = getSampleStyleSheet()
    ps = lambda name, **kw: ParagraphStyle(name, parent=base["Normal"], **{"fontName": "Helvetica", **kw})  # noqa: E731
    return {
        "title": ps("title", fontName="Helvetica-Bold", fontSize=18, leading=22, spaceAfter=2),
        "subtitle": ps("subtitle", fontSize=10, leading=13, textColor=MUTED, spaceAfter=10),
        "h2": ps("h2", fontName="Helvetica-Bold", fontSize=12.5, leading=16, textColor=PRIMARY, spaceBefore=10,
                 spaceAfter=5),
        "h3": ps("h3", fontName="Helvetica-Bold", fontSize=10, leading=13, spaceBefore=6, spaceAfter=1),
        "body": ps("body", fontSize=9.5, leading=13),
        "small": ps("small", fontSize=8, leading=10.5, textColor=MUTED),
        "cell": ps("cell", fontSize=9, leading=11, alignment=TA_LEFT),
        "cell_b": ps("cell_b", fontName="Helvetica-Bold", fontSize=9, leading=11),
        "head": ps("head", fontName="Helvetica-Bold", fontSize=8.5, leading=10.5, textColor=colors.white),
        "head_r": ps("head_r", fontName="Helvetica-Bold", fontSize=8.5, leading=10.5, textColor=colors.white,
                     alignment=2),
        "center": ps("center", fontName="Helvetica-Bold", fontSize=12, leading=15, alignment=2),
        "center_small": ps("center_small", fontSize=8.5, leading=11, textColor=MUTED, alignment=2),
        "warn": ps("warn", fontSize=9, leading=12, textColor=WARN),
    }


class _NumberedCanvas(rl_canvas.Canvas):
    """Canvas que conoce el total de páginas para imprimir "Página x de y"."""

    def __init__(self, *args, header: tuple[str, str, str] = ("", "", ""), **kwargs):
        super().__init__(*args, **kwargs)
        self._states: list[dict] = []
        self._header = header

    def showPage(self):  # noqa: N802 (API de ReportLab)
        self._states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        total = len(self._states)
        for state in self._states:
            self.__dict__.update(state)
            self._decorate(total)
            super().showPage()
        super().save()

    def _decorate(self, total: int):
        w, h = A4
        left, right = 18 * mm, w - 18 * mm
        self.saveState()
        self.setStrokeColor(RULE)
        self.setLineWidth(0.6)
        # Encabezado
        self.setFont("Helvetica-Bold", 8.5)
        self.setFillColor(PRIMARY)
        self.drawString(left, h - 12 * mm, self._header[0][:80])
        self.setFont("Helvetica", 8.5)
        self.setFillColor(MUTED)
        self.drawRightString(right, h - 12 * mm, f"{self._header[1]} · {self._header[2]}")
        self.line(left, h - 14 * mm, right, h - 14 * mm)
        # Pie
        self.line(left, 14 * mm, right, 14 * mm)
        self.drawString(left, 10 * mm, "Sistema LAM · Lectura Automática de Marcadores")
        self.drawRightString(right, 10 * mm, f"Página {self._pageNumber} de {total}")
        self.restoreState()


def _kv_table(rows: list[tuple[str, str]], st, widths) -> Table:
    data = [[Paragraph(k, st["cell_b"]), Paragraph(v, st["cell"])] for k, v in rows]
    t = Table(data, colWidths=widths, hAlign="LEFT")
    t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LINEBELOW", (0, 0), (-1, -1), 0.4, RULE),
        ("TOPPADDING", (0, 0), (-1, -1), 2.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
    ]))
    return t


def _grid_table(pairs: list[tuple[str, str]], st, total_width: float, columns: int = 4) -> Table:
    """Datos en rejilla: etiqueta pequeña arriba, valor debajo."""
    cells = [[Paragraph(k, st["small"]), Paragraph(v or "—", st["cell_b"])] for k, v in pairs]
    rows = [cells[i:i + columns] for i in range(0, len(cells), columns)]
    rows[-1] += [""] * (columns - len(rows[-1]))
    t = Table(rows, colWidths=[total_width / columns] * columns, hAlign="LEFT")
    t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    return t


def _result_table(table: dict, st, width: float) -> list:
    unit = table_unit(table["columns"])
    cols = table["columns"]
    head = [Paragraph(cols[0], st["head"]), Paragraph(cols[1], st["head"]), Paragraph(cols[2], st["head_r"])]
    body = [[Paragraph(r["item"], st["cell"]), r["direction"], format_value(r["value"], unit)] for r in table["rows"]]
    t = Table([head] + body, colWidths=[width * 0.46, width * 0.27, width * 0.27], hAlign="LEFT", repeatRows=1)
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 1), (-1, -1), 9),
        ("ALIGN", (2, 0), (2, -1), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LINEBELOW", (0, 1), (-1, -1), 0.4, RULE),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]
    style += [("BACKGROUND", (0, i), (-1, i), PRIMARY_LIGHT) for i in range(2, len(body) + 1, 2)]
    t.setStyle(TableStyle(style))
    out = [Paragraph(table["title"], st["h3"])]
    ref = table_reference(table["title"], cols)
    if ref:
        out.append(Paragraph(ref, st["small"]))
    # Sin KeepTogether: estas tablas van dentro de una celda y ReportLab no lo admite ahí
    return out + [Spacer(1, 2 * mm), t, Spacer(1, 3 * mm)]


def _image(jpeg: bytes, max_w: float, max_h: float) -> Image:
    iw, ih = ImageReader(io.BytesIO(jpeg)).getSize()
    s = min(max_w / iw, max_h / ih)
    return Image(io.BytesIO(jpeg), width=iw * s, height=ih * s)


def build_report(data: ReportData) -> bytes:
    st = _styles()
    page_w, _ = A4
    margin = 18 * mm
    width = page_w - 2 * margin
    p = data.patient
    gender = {"M": "Masculino", "F": "Femenino"}.get(p.get("gender") or "", "—")
    num = lambda v, u: "—" if v in (None, "") else f"{v:g} {u}"  # noqa: E731

    center = data.center or {}
    story: list = []
    if data.logo_png or center.get("name"):
        # Membrete: logo a la izquierda, nombre y contacto del centro a la derecha
        right = [Paragraph(center.get("name") or "", st["center"])]
        if center.get("contact"):
            right.append(Paragraph(center["contact"], st["center_small"]))
        logo = _image(data.logo_png, 55 * mm, 22 * mm) if data.logo_png else ""
        head = Table([[logo, right]], colWidths=[width * 0.4, width * 0.6], hAlign="LEFT")
        head.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("LEFTPADDING", (0, 0), (-1, -1), 0),
                                  ("RIGHTPADDING", (0, 0), (-1, -1), 0), ("LINEBELOW", (0, 0), (-1, -1), 0.6, RULE),
                                  ("BOTTOMPADDING", (0, 0), (-1, -1), 6)]))
        story += [head, Spacer(1, 6 * mm)]
    story += [
        Paragraph("Reporte de evaluación postural", st["title"]),
        Paragraph(f"{long_date(data.date)} · {data.date:%H:%M}"
                  + (f" · Evaluación N.º {data.evaluation_id}" if data.evaluation_id else ""), st["subtitle"]),
        Paragraph("Paciente", st["h2"]),
        _grid_table([
            ("Nombre", p.get("name") or "Anónimo"), ("Edad", f"{p['age']} años" if p.get("age") else "—"),
            ("Género", gender), ("Ocupación", p.get("occupation") or "—"),
            ("Estatura", num(data.height_cm or p.get("height_cm"), "cm")), ("Peso", num(p.get("weight_kg"), "kg")),
        ], st, width),
        Paragraph("Parámetros de la evaluación", st["h2"]),
    ]
    cfg = data.config
    scale = (f"Estatura del paciente ({data.height_cm:g} cm)" if data.mode == "pose" and data.height_cm
             else "Referencias R1–R2 (100 cm)")
    story.append(_grid_table([
        ("Detección", MODE_LABELS.get(data.mode, data.mode)), ("Escala", scale),
        ("Tolerancia angular", f"{cfg.get('tolerance_angle', 0):g}°"),
        ("Tolerancia de distancia", f"{cfg.get('tolerance_distance', 0):g} cm"),
        ("Evaluador", data.evaluator or "—"),
    ], st, width))

    story.append(Paragraph("Resumen del diagnóstico", st["h2"]))
    for v in data.views:
        block = [Paragraph(VIEW_TITLES.get(v.view, v.view), st["h3"]),
                 _kv_table([(label, text) for _, label, text in diagnostic_lines(v.diagnostic)], st,
                           [width * 0.42, width * 0.58])]
        if v.estimated_points:
            block.append(Paragraph(f"Puntos estimados sin revisar: {', '.join(v.estimated_points)}. "
                                   "Verifique su ubicación antes de interpretar los resultados.", st["warn"]))
        story.append(KeepTogether(block + [Spacer(1, 2 * mm)]))

    if data.notes:
        story += [Paragraph("Observaciones", st["h2"]),
                  Paragraph(data.notes.replace("\n", "<br/>"), st["body"])]

    story += [Spacer(1, 6 * mm), Paragraph(
        "Los valores se obtuvieron por fotogrametría en el plano a partir de los puntos anatómicos revisados por el "
        "evaluador. Este reporte es un apoyo para la valoración fisioterapéutica y no sustituye el criterio clínico.",
        st["small"])]

    # Una página por vista: imagen a la izquierda, tablas a la derecha
    img_w, tables_w, gap = width * 0.46, width * 0.51, width * 0.03
    for v in data.views:
        story.append(PageBreak())
        story.append(Paragraph(VIEW_TITLES.get(v.view, v.view), st["h2"]))
        details = []
        if v.scale_ratio:
            details.append(f"Escala {v.scale_ratio * 10:.2f} mm/px")
        if v.roll_deg:
            details.append(f"Foto nivelada {v.roll_deg:+.1f}° con la línea vertical")
        if details:
            story.append(Paragraph(" · ".join(details), st["small"]))
        story.append(Spacer(1, 3 * mm))
        tables = [f for t in v.tables for f in _result_table(t, st, tables_w)]
        left = _image(v.overlay_jpeg, img_w, 205 * mm) if v.overlay_jpeg else Paragraph("Sin imagen", st["small"])
        layout = Table([[left, "", tables]], colWidths=[img_w, gap, tables_w], hAlign="LEFT")
        layout.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"),
                                    ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0)]))
        story += [layout, CondPageBreak(15 * mm), Paragraph(DIRECTION_LEGEND, st["small"])]

    buf = io.BytesIO()
    header = (center.get("name") or "Sistema LAM · Evaluación postural", p.get("name") or "Anónimo",
              data.date.strftime("%d/%m/%Y"))
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=margin, rightMargin=margin, topMargin=20 * mm,
                            bottomMargin=20 * mm, title=f"Evaluación postural - {header[1]}",
                            author=data.evaluator or center.get("name") or "Sistema LAM",
                            subject="Reporte de evaluación postural")
    doc.build(story, canvasmaker=lambda *a, **k: _NumberedCanvas(*a, header=header, **k))
    return buf.getvalue()
