"""Preparación de imágenes y segmentación de marcadores verdes.

Portado de image_processing_LAM.py. Cambios respecto al original:
- API de scikit-image actual (channel_axis en lugar de multichannel).
- Soporte de imágenes RGBA y en escala de grises.
- Errores explícitos cuando no se encuentran los marcadores de referencia.
"""
from __future__ import annotations

import numpy as np
from skimage import filters, img_as_ubyte, morphology, transform
from skimage.color import gray2rgb, rgb2gray, rgba2rgb
from skimage.measure import label, regionprops

MAX_WIDTH_PX = 1000


def ensure_rgb(img: np.ndarray) -> np.ndarray:
    if img.ndim == 2:
        return img_as_ubyte(gray2rgb(img))
    if img.shape[-1] == 4:
        return img_as_ubyte(rgba2rgb(img))
    return img


def scale_image(img: np.ndarray) -> np.ndarray:
    """Reduce la imagen al 80 % hasta que su ancho sea <= 1000 px.

    El original comparaba len(img[1]) > 1000 or len(img[0]) > 2000; ambas
    expresiones son el ancho, así que en la práctica solo se limitaba el ancho.
    """
    while img.shape[1] > MAX_WIDTH_PX:
        img = transform.rescale(img, 0.8, channel_axis=-1)
    return img_as_ubyte(img)


def green_filter(img: np.ndarray, threshold: float) -> np.ndarray:
    """Imagen binaria con las zonas donde el canal verde domina."""
    channel_green = img[:, :, 1].astype(float)
    gray_img = rgb2gray(img) * 255
    green_img = channel_green - gray_img
    green_img[green_img < 0] = 0
    green_img = filters.median(green_img)
    filter_threshold = round(np.max(green_img) * threshold)
    green_binary_img = green_img > filter_threshold
    return morphology.remove_small_holes(green_binary_img)


def markers(binary_image: np.ndarray):
    """Centroides de los marcadores.

    Devuelve (reference_1, reference_2, centers_y, centers_x, scale_ratio).
    reference_1 es el marcador más a la izquierda y reference_2 el más a la
    derecha (separados 100 cm). El resto se devuelve en el orden de etiquetado
    de skimage (de arriba hacia abajo), del que dependen las vistas.
    """
    regions = regionprops(label(binary_image))
    if len(regions) < 2:
        raise ValueError("No se encontraron los dos marcadores de referencia (R1 y R2)")

    centers_y = [r.centroid[0] for r in regions]
    centers_x = [r.centroid[1] for r in regions]

    i = int(np.argmin(centers_x))
    reference_1 = np.array([centers_y.pop(i), centers_x.pop(i)])
    i = int(np.argmax(centers_x))
    reference_2 = np.array([centers_y.pop(i), centers_x.pop(i)])

    # FIXME(HALLAZGO-1): se conserva la fórmula original para no alterar los
    # resultados clínicos. La distancia entre referencias debería ser
    # np.linalg.norm(reference_2 - reference_1); la fórmula actual usa solo las
    # coordenadas x de cada referencia (≈10 % de error). Ver docs/MIGRACION.md.
    scale_ratio = 100.0 / np.sqrt(reference_1[1] ** 2 + reference_2[1] ** 2)

    return reference_1, reference_2, np.array(centers_y), np.array(centers_x), scale_ratio


def straighten_img(img: np.ndarray, threshold: float) -> np.ndarray:
    """Rota la imagen para nivelar R1-R2 y recorta un margen alrededor de ellas."""
    reference_1, reference_2, *_ = markers(green_filter(img, threshold))

    pos_reference = reference_2 - reference_1
    rotation_angle = np.degrees(np.arctan(pos_reference[0] / pos_reference[1]))
    rotated = transform.rotate(img, rotation_angle)

    ref_x = sorted([reference_1[1], reference_2[1]])
    margin = abs(reference_1[1] - reference_2[1]) / 10
    x_1 = int(round(ref_x[0] - margin))
    x_2 = int(round(ref_x[1] + margin))

    return img_as_ubyte(rotated[:, max(x_1, 0):x_2])


def img_grid(center_x, center_y, size_x, size_y, step):
    """Cuadrícula en los cuatro cuadrantes a partir del centro (para el overlay)."""
    x_1 = np.arange(center_x, size_x, step)
    y_1 = np.arange(center_y, size_y, step)
    x_2 = np.arange(center_x, 0, -step)
    y_2 = np.arange(center_y, 0, -step)
    xs = np.hstack((x_1, x_2))
    ys = np.hstack((y_1, y_2))
    return xs, ys
