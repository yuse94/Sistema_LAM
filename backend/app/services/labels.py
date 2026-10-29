"""Textos legibles para reportes y exportaciones (mismos que usa la interfaz web).

Sin dependencias del núcleo LAM: lo usan el PDF, el Excel y el historial.
"""
from __future__ import annotations

VIEWS = ("anterior", "posterior", "lateral_derecha", "lateral_izquierda")

VIEW_TITLES = {
    "anterior": "Vista anterior",
    "posterior": "Vista posterior",
    "lateral_derecha": "Vista lateral derecha",
    "lateral_izquierda": "Vista lateral izquierda",
}

# Nombres de hoja del Excel (los tres primeros, como en DB_LAM.xlsx)
VIEW_SHEETS = {
    "anterior": "Anterior",
    "posterior": "Posterior",
    "lateral_derecha": "LateralD",
    "lateral_izquierda": "LateralI",
}

MODE_LABELS = {
    "pose": "Sin marcadores (estimación de pose)",
    "markers": "Marcadores verdes",
}

DIAGNOSTIC_LABELS = {
    "linea_escapular_descendida": "Línea escapular descendida",
    "linea_pelvica_descendida": "Línea pélvica descendida",
    "cabeza_inclinada": "Cabeza inclinada",
    "cabeza_rotada": "Cabeza rotada",
    "rodilla_derecha": "Rodilla derecha",
    "rodilla_izquierda": "Rodilla izquierda",
    "rotacion_dorsal": "Rotación dorsal",
    "rotacion_pelvica": "Rotación pélvica",
    "pie_izquierdo": "Pie izquierdo",
    "pie_derecho": "Pie derecho",
    "postura": "Postura",
    "proyeccion_postural": "Proyección postural",
}

DIRECTION_LEGEND = ("Der.: derecha · Izq.: izquierda · Alin.: alineado · Ant.: anterior · Pos.: posterior · "
                    "Rot.Ext./Rot.Int.: rotación externa/interna")


def diagnostic_label(key: str) -> str:
    return DIAGNOSTIC_LABELS.get(key, key.replace("_", " ").capitalize())


def diagnostic_lines(diagnostic: dict) -> list[tuple[str, str, str]]:
    """(clave, etiqueta, texto) del diagnóstico, con el ángulo unido a su clasificación.

    Ej.: cabeza_inclinada="Der." + cabeza_inclinada_angulo=2.4 -> "Der. (2.4°)".
    """
    lines = []
    for key, value in diagnostic.items():
        if key.endswith("_angulo") and key.removesuffix("_angulo") in diagnostic:
            continue
        text = "—" if value is None else str(value)
        angle = diagnostic.get(f"{key}_angulo")
        if isinstance(angle, (int, float)) and value not in (None, "N/A"):
            text = f"{text} ({angle:.1f}°)"
        lines.append((key, diagnostic_label(key), text))
    return lines


def table_unit(columns) -> str:
    """Unidad de la columna de valores de una tabla de resultados."""
    return "cm" if "distancia" in str(columns[2]).lower() else "°"


def table_reference(title: str, columns) -> str | None:
    """Valor de referencia que se imprime bajo el título de cada tabla."""
    if "normal" in title.lower():
        return None  # el título ya trae la referencia (pelvis lateral 10° ± 5°)
    return f"Valor ideal: 0 {table_unit(columns)}".replace("0 °", "0°")


def format_value(value: float | None, unit: str, decimals: int = 1) -> str:
    if value is None:
        return "—"
    return f"{value:.{decimals}f}°" if unit == "°" else f"{value:.{decimals}f} {unit}"
