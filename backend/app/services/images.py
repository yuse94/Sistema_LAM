"""Lectura de fotografías subidas por la interfaz."""
from __future__ import annotations

import io

import numpy as np
from PIL import Image, ImageOps, UnidentifiedImageError


class InvalidImage(ValueError):
    pass


def decode(data: bytes) -> np.ndarray:
    """Bytes de la foto -> RGB uint8, aplicando la orientación EXIF (fotos de celular).

    El navegador muestra la foto ya orientada, así que los puntos que envía la
    interfaz están en estas coordenadas.
    """
    try:
        img = Image.open(io.BytesIO(data))
        img = ImageOps.exif_transpose(img)
        return np.asarray(img.convert("RGB"))
    except (UnidentifiedImageError, OSError) as exc:
        raise InvalidImage("El archivo no es una imagen válida") from exc


def encode_jpeg(img: np.ndarray, quality: int = 92) -> bytes:
    buf = io.BytesIO()
    Image.fromarray(img).save(buf, format="JPEG", quality=quality)
    return buf.getvalue()
