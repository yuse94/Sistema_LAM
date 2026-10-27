"""Ajuste de los desplazamientos del modo sin marcadores (backend/app/lam/pose.py).

Lee validation/resultados/poses.json (coordenadas de MediaPipe y de los marcadores en
las mismas fotos) y, para cada punto LAM, calcula el desplazamiento desde su ancla de
MediaPipe, normalizado por el tamaño del cuerpo:
- vistas frontales: ancho de hombros (x) y largo del tronco (y);
- vista lateral: largo del muslo (x e y), con x positivo hacia adelante.

Los pares bilaterales se ajustan juntos y en espejo. El error se mide con validación
cruzada dejando una persona fuera, y se compara con la versión actual de pose.py.
No modifica el código: imprime los coeficientes para revisarlos y copiarlos.

    uv run python validation/ajustar_poses.py
"""
from __future__ import annotations

import json
import math
import re
import statistics
import sys
from pathlib import Path

import numpy as np

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from app.lam import PosePoint, View  # noqa: E402
from app.lam.pose import landmarks_from_pose  # noqa: E402

POSES = Path(__file__).resolve().parent / "resultados" / "poses.json"

ANCHORS = {
    "anterior": {"F1": "eye_mid", "F2": "mouth_mid", "F3": "sh_L", "F4": "sh_R", "F5": "sh_mid", "F6": "hip_mid",
                 "F7": "hip_L", "F8": "hip_R", "F9": "knee_L", "F10": "knee_R", "F11": "ankle_L", "F12": "ankle_R",
                 "F13": "foot_L", "F14": "foot_R"},
    "posterior": {"P1": "sh_mid", "P2": "sh_mid", "P3": "sh_R", "P4": "sh_L", "P5": "hip_R", "P6": "hip_L",
                  "P7": "knee_R", "P8": "knee_L", "P9": "ankle_R", "P10": "ankle_L", "P11": "heel_R", "P12": "heel_L"},
    "lateral_derecha": {"L1": "ear", "L2": "sh", "L3": "hip", "L4": "hip", "L5": "hip", "L6": "knee", "L7": "ankle"},
}
# (lado izquierdo de la imagen, lado derecho)
PAIRS = [("F3", "F4"), ("F7", "F8"), ("F9", "F10"), ("F11", "F12"), ("F13", "F14"), ("P4", "P3"), ("P6", "P5"),
         ("P8", "P7"), ("P10", "P9"), ("P12", "P11")]
LEFT_OF_IMAGE = {a for a, _ in PAIRS}
PARTNER = {**{a: b for a, b in PAIRS}, **{b: a for a, b in PAIRS}}


def person_of(name: str) -> str:
    return re.split(r"[- ](?=anterior|posterior|lateral)", name, maxsplit=1)[0]


def _p(pose, i):
    return np.array(pose[i][:2])


def _pair(pose, i, j):
    a, b = _p(pose, i), _p(pose, j)
    return (a, b) if a[0] <= b[0] else (b, a)


def frame(view: str, pose):
    """Anclas de MediaPipe y escalas (Sx, Sy) de una foto."""
    if view in ("anterior", "posterior"):
        sl, sr = _pair(pose, 11, 12)
        hl, hr = _pair(pose, 23, 24)
        sh_mid, hip_mid = (sl + sr) / 2, (hl + hr) / 2
        anchors = {"sh_mid": sh_mid, "hip_mid": hip_mid, "sh_L": sl, "sh_R": sr, "hip_L": hl, "hip_R": hr,
                   "eye_mid": (_p(pose, 2) + _p(pose, 5)) / 2, "mouth_mid": (_p(pose, 9) + _p(pose, 10)) / 2}
        for name, (i, j) in {"knee": (25, 26), "ankle": (27, 28), "heel": (29, 30), "foot": (31, 32)}.items():
            anchors[name + "_L"], anchors[name + "_R"] = _pair(pose, i, j)
        return anchors, (abs(sr[0] - sl[0]), hip_mid[1] - sh_mid[1])
    right = sum(pose[i][2] for i in (8, 12, 24, 26, 28, 30, 32))
    left = sum(pose[i][2] for i in (7, 11, 23, 25, 27, 29, 31))
    idx = (8, 12, 24, 26, 28, 30, 32) if right >= left - 0.5 else (7, 11, 23, 25, 27, 29, 31)
    ear, sh, hip, knee, ankle, heel, foot = (_p(pose, i) for i in idx)
    thigh = float(np.linalg.norm(hip - knee))
    return {"ear": ear, "sh": sh, "hip": hip, "knee": knee, "ankle": ankle}, (thigh, thigh)


def main():
    if not POSES.exists():
        sys.exit(f"No se encontró {POSES}. Ejecute primero validation/markerless.py")
    data = json.loads(POSES.read_text(encoding="utf-8"))
    samples: dict[tuple[str, str], list] = {}
    current: dict[str, list[float]] = {}
    for name, r in data.items():
        if r["vista"] not in ANCHORS:
            continue
        anchors, (sx, sy) = frame(r["vista"], r["pose"])
        lm = landmarks_from_pose(View(r["vista"]), [PosePoint(*p) for p in r["pose"]]).landmarks
        for k, anchor in ANCHORS[r["vista"]].items():
            m = np.array(r["marcadores"][k])
            samples.setdefault((r["vista"], k), []).append((person_of(name), anchors[anchor], sx, sy, m,
                                                            r["escala_marcadores"]))
            current.setdefault(k, []).append(math.hypot(lm[k][0] - m[0], lm[k][1] - m[1]) * r["escala_marcadores"])

    def fit(view, k, exclude=None):
        keys = (k, PARTNER[k]) if k in PARTNER else (k,)
        xs, ys = [], []
        for kk in keys:
            sign = -1 if kk in LEFT_OF_IMAGE else 1
            for p, a, sx, sy, m, _ in samples[(view, kk)]:
                if p != exclude:
                    xs.append((m[0] - a[0]) / sx * (sign if k in PARTNER else 1))
                    ys.append((m[1] - a[1]) / sy)
        cx, cy = float(np.median(xs)), float(np.median(ys))
        if k in PARTNER:
            cx *= -1 if k in LEFT_OF_IMAGE else 1
        return cx, cy

    print("Punto  actual  ajustado(CV)   cx (afuera/adelante)   cy (abajo)")
    for (view, k), rows in sorted(samples.items(), key=lambda kv: ("FPL".index(kv[0][1][0]), int(kv[0][1][1:]))):
        cv = []
        for p in sorted({r[0] for r in rows}):
            cx, cy = fit(view, k, exclude=p)
            for q, a, sx, sy, m, s in rows:
                if q == p:
                    cv.append(float(np.linalg.norm(a + np.array([cx * sx, cy * sy]) - m)) * s)
        cx, cy = fit(view, k)
        out = cx * (-1 if k in LEFT_OF_IMAGE else 1) if k in PARTNER else cx  # positivo = hacia afuera
        print(f"{k:5s} {statistics.mean(current[k]):6.1f} {statistics.mean(cv):12.1f}   {out:+20.3f}   {cy:+10.3f}")
    print("\nError en cm con la escala de los marcadores. 'actual' = pose.py; 'ajustado' = validación cruzada.")


if __name__ == "__main__":
    main()
