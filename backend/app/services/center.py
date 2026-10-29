"""Datos del centro que usa la app: nombre, contacto, evaluador por defecto y logo.

Se guardan en storage_dir (centro.json y centro_logo.png), junto a las fotografías,
para que viajen con la carpeta de datos. Aparecen en el encabezado del reporte PDF.
"""
from __future__ import annotations

import io
import json

from PIL import Image, ImageOps, UnidentifiedImageError
from pydantic import BaseModel, Field, field_validator

from . import storage

CENTER_FILE = "centro.json"
LOGO_FILE = "centro_logo.png"
LOGO_MAX_PX = 800


class CenterInfo(BaseModel):
    name: str = Field("", max_length=150, description="Nombre del centro (encabezado del reporte)")
    contact: str = Field("", max_length=250, description="Dirección, teléfono o correo")
    evaluator: str = Field("", max_length=150, description="Evaluador que se propone en cada evaluación")

    @field_validator("name", "contact", "evaluator")
    @classmethod
    def clean(cls, v: str) -> str:
        return " ".join(v.split())


def load() -> CenterInfo:
    try:
        return CenterInfo.model_validate_json(storage.read(CENTER_FILE))
    except (OSError, ValueError):
        return CenterInfo()


def save(info: CenterInfo) -> CenterInfo:
    storage.write(CENTER_FILE, json.dumps(info.model_dump(), ensure_ascii=False, indent=2).encode())
    return info


def logo() -> bytes | None:
    try:
        return storage.read(LOGO_FILE)
    except OSError:
        return None


def save_logo(data: bytes) -> None:
    """Normaliza el logo a PNG (máx. 800 px, conserva la transparencia)."""
    try:
        img = ImageOps.exif_transpose(Image.open(io.BytesIO(data)))
    except (UnidentifiedImageError, OSError) as exc:
        raise ValueError("El archivo no es una imagen válida") from exc
    img = img.convert("RGBA")
    img.thumbnail((LOGO_MAX_PX, LOGO_MAX_PX))
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    storage.write(LOGO_FILE, buf.getvalue())


def delete_logo() -> None:
    try:
        storage.path_of(LOGO_FILE).unlink(missing_ok=True)
    except ValueError:
        pass
