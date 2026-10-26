"""Diccionario de puntos anatómicos de LAM.

Cada punto tiene su definición, cómo localizarlo, la región del cuerpo, su posición
en una silueta de referencia (para ilustrarlo) y las mediciones en las que interviene.

Las mediciones no se escriben a mano: se calculan moviendo cada punto sobre la
postura de referencia y viendo qué filas de las tablas y del diagnóstico cambian.
Así el diccionario siempre coincide con lo que calcula el núcleo.

Definiciones y localización redactadas a partir de la Tabla 2.1 de la tesis
(UPS-CT008207) y anatomía de superficie de referencia. Deben ser revisadas por el
fisioterapeuta responsable antes del uso clínico.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from functools import cache

import numpy as np

from .types import AssessmentConfig, View
from .views import SPECS

# Silueta de referencia en un lienzo de 100 x 200 (x, y), y hacia abajo.
# Anterior: el lado derecho del paciente queda a la izquierda del dibujo.
# Posterior: el lado izquierdo del paciente queda a la izquierda del dibujo.
# Lateral: paciente mirando hacia la derecha del dibujo (lateral derecha).
FIGURE_POSITIONS: dict[str, dict[str, tuple[float, float]]] = {
    "anterior": {
        "F1": (50, 15), "F2": (50, 28), "F3": (32, 38), "F4": (68, 38), "F5": (50, 37), "F6": (50, 72),
        "F7": (40, 84), "F8": (60, 84), "F9": (43, 128), "F10": (57, 128), "F11": (44, 176), "F12": (56, 176),
        "F13": (41, 192), "F14": (59, 192),
    },
    "posterior": {
        "P1": (50, 33), "P2": (50, 50), "P3": (68, 38), "P4": (32, 38), "P5": (55, 86), "P6": (45, 86),
        "P7": (57, 130), "P8": (43, 130), "P9": (56, 174), "P10": (44, 174), "P11": (56, 190), "P12": (44, 190),
    },
    "lateral": {
        "L1": (48, 18), "L2": (50, 38), "L3": (41, 83), "L4": (59, 86), "L5": (50, 92), "L6": (54, 134),
        "L7": (57, 187),
    },
}

# Postura lateral "ideal": todo sobre la plomada (vertical de L7). Sirve como segunda
# referencia para detectar de qué puntos depende la clasificación de la postura, que en
# la silueta de referencia queda enmascarada por la cabeza adelantada.
_ALIGNED_LATERAL = {**FIGURE_POSITIONS["lateral"], "L1": (57, 18), "L2": (57, 38), "L3": (48, 83),
                    "L4": (66, 86), "L5": (57, 92), "L6": (57, 134)}

FIGURE_OF_VIEW = {
    View.ANTERIOR: "anterior",
    View.POSTERIOR: "posterior",
    View.LATERAL_DERECHA: "lateral",
    View.LATERAL_IZQUIERDA: "lateral",
}


@dataclass(frozen=True)
class _Text:
    name: str
    region: str
    definition: str
    location: str


_AC = _Text(
    "Articulación acromioclavicular", "Hombros y tronco",
    "Unión entre el extremo lateral de la clavícula y el acromion de la escápula.",
    "Siga la clavícula hacia afuera hasta sentir un pequeño escalón justo antes del acromion; "
    "se aprecia mejor si el paciente mueve suavemente el hombro.",
)
_EIAS = _Text(
    "Espina ilíaca anterosuperior (EIAS)", "Pelvis",
    "Prominencia ósea en el extremo anterior de la cresta ilíaca, donde se originan el sartorio "
    "y el ligamento inguinal.",
    "Siga la cresta ilíaca hacia adelante y abajo hasta su punto más anterior. Con el paciente "
    "de pie, palpe con los pulgares desde abajo hacia arriba.",
)
_EIPS = _Text(
    "Espina ilíaca posterosuperior (EIPS)", "Pelvis",
    "Prominencia ósea en el extremo posterior de la cresta ilíaca, aproximadamente a nivel de la "
    "segunda vértebra sacra.",
    "Justo debajo de los hoyuelos de la región lumbar baja (hoyuelos de Venus). Palpe con los "
    "pulgares desde abajo hacia arriba.",
)

_TEXTS: dict[str, _Text] = {
    "F1": _Text("Entrecejo (glabela)", "Cabeza",
                "Punto más prominente del hueso frontal entre las cejas, sobre la raíz de la nariz.",
                "En la línea media, entre las cejas, con el paciente mirando al frente."),
    "F2": _Text("Mentón", "Cabeza",
                "Punto más anterior de la protuberancia mentoniana de la mandíbula, en la línea media.",
                "Palpe el borde inferior de la mandíbula en la línea media y ubique su punto más saliente."),
    "F3": _AC, "F4": _AC,
    "F5": _Text("Horquilla del manubrio esternal (escotadura yugular)", "Hombros y tronco",
                "Escotadura del borde superior del manubrio del esternón, entre los extremos internos "
                "de las clavículas.",
                "Depresión en la base del cuello, en la línea media, por encima del esternón."),
    "F6": _Text("Ombligo", "Hombros y tronco",
                "Cicatriz umbilical, en la línea media del abdomen.",
                "Centro del ombligo."),
    "F7": _EIAS, "F8": _EIAS,
    "F9": _Text("Rótula", "Miembro inferior",
                "Centro de la cara anterior de la rótula.",
                "Con la rodilla extendida y el cuádriceps relajado, ubique el centro de la rótula."),
    "F10": _Text("Rótula", "Miembro inferior",
                 "Centro de la cara anterior de la rótula.",
                 "Con la rodilla extendida y el cuádriceps relajado, ubique el centro de la rótula."),
    "F11": _Text("Tobillo", "Pie",
                 "Punto medio de la cara anterior del tobillo, entre los maléolos interno y externo.",
                 "Punto medio de la línea que une ambos maléolos, por delante de la articulación."),
    "F12": _Text("Tobillo", "Pie",
                 "Punto medio de la cara anterior del tobillo, entre los maléolos interno y externo.",
                 "Punto medio de la línea que une ambos maléolos, por delante de la articulación."),
    "F13": _Text("Dedo gordo del pie", "Pie",
                 "Extremo distal del primer dedo del pie (hallux).",
                 "Punta del dedo gordo, con el paciente descalzo."),
    "F14": _Text("Dedo gordo del pie", "Pie",
                 "Extremo distal del primer dedo del pie (hallux).",
                 "Punta del dedo gordo, con el paciente descalzo."),
    "P1": _Text("Apófisis espinosa de C7 (vértebra prominente)", "Hombros y tronco",
                "Apófisis espinosa de la séptima vértebra cervical, la más saliente en la base del cuello.",
                "Pida al paciente flexionar ligeramente el cuello: C7 sigue palpable mientras que C6 "
                "tiende a desplazarse hacia adelante."),
    "P2": _Text("Apófisis espinosa de T5", "Hombros y tronco",
                "Apófisis espinosa de la quinta vértebra dorsal.",
                "Cuente las apófisis espinosas hacia abajo desde C7 (T1, T2, T3…). Queda entre la altura "
                "de la espina y la del ángulo inferior de la escápula."),
    "P3": _AC, "P4": _AC,
    "P5": _EIPS, "P6": _EIPS,
    "P7": _Text("Hueco poplíteo", "Miembro inferior",
                "Centro de la fosa poplítea, en la cara posterior de la rodilla.",
                "Punto medio del pliegue de flexión posterior de la rodilla."),
    "P8": _Text("Hueco poplíteo", "Miembro inferior",
                "Centro de la fosa poplítea, en la cara posterior de la rodilla.",
                "Punto medio del pliegue de flexión posterior de la rodilla."),
    "P9": _Text("Tendón de Aquiles", "Pie",
                "Tendón calcáneo a la altura de los maléolos.",
                "Línea media posterior del tendón, al nivel de los maléolos."),
    "P10": _Text("Tendón de Aquiles", "Pie",
                 "Tendón calcáneo a la altura de los maléolos.",
                 "Línea media posterior del tendón, al nivel de los maléolos."),
    "P11": _Text("Calcáneo", "Pie",
                 "Cara posterior del calcáneo (talón).",
                 "Punto medio de la cara posterior del talón, cerca del apoyo en el suelo."),
    "P12": _Text("Calcáneo", "Pie",
                 "Cara posterior del calcáneo (talón).",
                 "Punto medio de la cara posterior del talón, cerca del apoyo en el suelo."),
    "L1": _Text("Oído (trago)", "Cabeza",
                "Trago de la oreja, delante del conducto auditivo externo.",
                "Centro del trago del lado que mira a la cámara."),
    "L2": _AC,
    "L3": _EIPS,
    "L4": _EIAS,
    "L5": _Text("Trocánter mayor del fémur", "Pelvis",
                "Prominencia ósea lateral del extremo superior del fémur.",
                "Cara lateral de la cadera; se siente moverse bajo los dedos al rotar la cadera."),
    "L6": _Text("Tuberosidad tibial", "Miembro inferior",
                "Prominencia anterior de la tibia donde se inserta el tendón rotuliano.",
                "Unos centímetros por debajo del borde inferior de la rótula, en la línea media de la pierna."),
    "L7": _Text("Articulación transversal del tarso (de Chopart)", "Pie",
                "Línea articular entre el astrágalo y el calcáneo, por detrás, y el escafoides y el cuboides, "
                "por delante.",
                "En el dorso del pie, por delante del tobillo; por el lado interno queda justo detrás de "
                "la tuberosidad del escafoides."),
}

_SIDES = {
    "F3": "derecha", "F4": "izquierda", "F7": "derecha", "F8": "izquierda", "F9": "derecha", "F10": "izquierda",
    "F11": "derecho", "F12": "izquierdo", "F13": "derecho", "F14": "izquierdo",
    "P3": "derecha", "P4": "izquierda", "P5": "derecha", "P6": "izquierda", "P7": "derecho", "P8": "izquierdo",
    "P9": "derecho", "P10": "izquierdo", "P11": "derecho", "P12": "izquierdo",
}


@dataclass(frozen=True)
class Measurement:
    table: str  # título de la tabla
    item: str  # fila de la tabla


@dataclass(frozen=True)
class PointInfo:
    id: str
    name: str
    side: str | None  # derecho/izquierdo cuando aplica
    region: str
    definition: str
    location: str
    views: tuple[View, ...]
    figure: str  # anterior | posterior | lateral
    position: tuple[float, float]  # en la silueta de 100 x 200
    measurements: tuple[Measurement, ...] = field(default=())
    diagnostics: tuple[str, ...] = field(default=())  # claves del diagnóstico que dependen del punto


def _usage(view: View, point_id: str) -> tuple[tuple[Measurement, ...], tuple[str, ...]]:
    """Mediciones y diagnósticos que cambian al mover el punto en la postura de referencia."""
    spec = SPECS[view]
    figure = FIGURE_OF_VIEW[view]
    references = [FIGURE_POSITIONS[figure]] + ([_ALIGNED_LATERAL] if figure == "lateral" else [])
    config = AssessmentConfig()
    changed_rows: set[tuple[int, int]] = set()
    changed_diag: set[str] = set()
    for positions in references:
        _perturb(spec, positions, point_id, config, changed_rows, changed_diag)

    ref = spec.evaluate(_to_px(FIGURE_POSITIONS[figure]), 0.1, config)
    measurements = tuple(Measurement(ref.tables[ti].title, ref.tables[ti].rows[ri].item)
                         for ti, ri in sorted(changed_rows))
    diagnostics = tuple(k for k in ref.diagnostic if k in changed_diag)
    return measurements, diagnostics


def _to_px(positions: dict[str, tuple[float, float]]) -> dict[str, np.ndarray]:
    # Lienzo x10 para trabajar en "píxeles"; la escala no importa para detectar dependencias.
    return {k: np.array([y * 10.0, x * 10.0]) for k, (x, y) in positions.items()}


def _perturb(spec, positions, point_id, config, changed_rows, changed_diag) -> None:
    base = _to_px(positions)
    ref = spec.evaluate(base, 0.1, config)
    # Movimientos de varios tamaños y en ambos sentidos, en x y en y: los diagnósticos por
    # categoría (p. ej. "Valgo") solo cambian si el movimiento cruza un umbral.
    deltas = [np.array(d) for size in (15.0, 60.0, 200.0)
              for d in ((0.0, size), (0.0, -size), (size, 0.0), (-size, 0.0))]
    for delta in deltas:
        moved = dict(base)
        moved[point_id] = base[point_id] + delta
        ev = spec.evaluate(moved, 0.1, config)
        for ti, (t_ref, t_new) in enumerate(zip(ref.tables, ev.tables)):
            for ri, (a, b) in enumerate(zip(t_ref.rows, t_new.rows)):
                if a.value != b.value:
                    changed_rows.add((ti, ri))
        changed_diag |= {k for k, v in ev.diagnostic.items() if v != ref.diagnostic.get(k)}


@cache
def catalog() -> tuple[PointInfo, ...]:
    """Todos los puntos, en el orden de las vistas (F, P, L)."""
    points: list[PointInfo] = []
    for view, figure in ((View.ANTERIOR, "anterior"), (View.POSTERIOR, "posterior"),
                         (View.LATERAL_DERECHA, "lateral")):
        views = (View.LATERAL_DERECHA, View.LATERAL_IZQUIERDA) if figure == "lateral" else (view,)
        for pid in SPECS[view].labels:
            text = _TEXTS[pid]
            measurements, diagnostics = _usage(view, pid)
            points.append(PointInfo(
                id=pid, name=text.name, side=_SIDES.get(pid), region=text.region,
                definition=text.definition, location=text.location, views=views, figure=figure,
                position=FIGURE_POSITIONS[figure][pid], measurements=measurements, diagnostics=diagnostics,
            ))
    return tuple(points)
