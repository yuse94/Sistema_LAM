"""Comparación de las evaluaciones de un paciente para una vista.

Arma una matriz medición x fecha a partir de las tablas guardadas, para ver cómo
cambia cada valor entre evaluaciones.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from .labels import diagnostic_lines, table_unit


@dataclass
class HistoryEntry:
    evaluation_id: int
    date: datetime
    diagnostic: dict
    tables: list[dict]  # {title, columns, rows: [{item, direction, value}]}


def build_history(entries: list[HistoryEntry]) -> dict:
    """Evaluaciones en orden cronológico; las mediciones se emparejan por tabla y nombre."""
    entries = sorted(entries, key=lambda e: (e.date, e.evaluation_id))
    out: dict = {"evaluations": [{"id": e.evaluation_id, "date": e.date} for e in entries], "tables": [],
                 "diagnostic": []}
    if not entries:
        return out

    reference = entries[-1]  # la estructura de la evaluación más reciente manda
    for ti, table in enumerate(reference.tables):
        rows = []
        for item in (r["item"] for r in table["rows"]):
            values = []
            for e in entries:
                found = None
                if ti < len(e.tables):
                    found = next((r for r in e.tables[ti]["rows"] if r["item"] == item), None)
                values.append({"direction": found["direction"], "value": found["value"]} if found else None)
            nums = [v["value"] for v in values if v is not None]
            change = round(nums[-1] - nums[0], 2) if len(nums) >= 2 else None
            rows.append({"item": item, "values": values, "change": change})
        out["tables"].append({"key": table.get("key", f"table_{ti + 1}"), "title": table["title"],
                              "unit": table_unit(table["columns"]), "rows": rows})

    per_entry = [{k: (label, text) for k, label, text in diagnostic_lines(e.diagnostic)} for e in entries]
    for key, label, _ in diagnostic_lines(reference.diagnostic):
        out["diagnostic"].append({"key": key, "label": label,
                                  "values": [d[key][1] if key in d else None for d in per_entry]})
    return out
