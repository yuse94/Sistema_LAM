"""Archivos de las evaluaciones (fotos y overlays) bajo settings.storage_dir.

En la base de datos se guardan rutas relativas, para poder mover la carpeta.
Las fotos son datos personales de salud: storage_dir no debe quedar dentro de una
carpeta pública ni versionarse (backend/data/ está en .gitignore).
"""
from __future__ import annotations

import shutil
from pathlib import Path, PurePosixPath

from app.core.config import get_settings


def root() -> Path:
    return get_settings().storage_dir


def evaluation_folder(evaluation_id: int) -> PurePosixPath:
    return PurePosixPath("evaluaciones") / str(evaluation_id)


def write(rel: PurePosixPath | str, data: bytes) -> str:
    path = root() / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return str(PurePosixPath(rel))


def path_of(rel: str) -> Path:
    path = (root() / rel).resolve()
    if not path.is_relative_to(root().resolve()):
        raise ValueError("Ruta fuera de la carpeta de almacenamiento")
    return path


def read(rel: str) -> bytes:
    return path_of(rel).read_bytes()


def remove_evaluation(evaluation_id: int) -> None:
    shutil.rmtree(root() / evaluation_folder(evaluation_id), ignore_errors=True)
