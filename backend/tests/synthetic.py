"""Imágenes sintéticas con marcadores verdes para pruebas sin fotos reales."""
import numpy as np
from skimage.draw import disk

REFS = [(500, 60), (500, 940)]  # R1, R2 (y, x) separados 880 px = 100 cm

# Marcadores en orden de arriba hacia abajo; postura simétrica e ideal.
ANTERIOR = [(100, 500), (150, 500), (250, 350), (250, 650), (270, 500), (420, 500), (450, 380),
            (450, 620), (650, 420), (650, 580), (850, 440), (850, 560), (900, 430), (900, 570)]
POSTERIOR = [(240, 500), (250, 350), (250, 650), (330, 500), (450, 400), (450, 600), (650, 420),
             (650, 580), (820, 440), (820, 560), (900, 440), (900, 560)]
LATERAL = [(100, 500), (250, 500), (450, 420), (452, 580), (520, 500), (700, 500), (900, 500)]


def make_image(points, size=(1000, 1000), radius=8):
    img = np.full((*size, 3), 255, dtype=np.uint8)
    for y, x in [*REFS, *points]:
        rr, cc = disk((y, x), radius, shape=size)
        img[rr, cc] = (0, 200, 0)
    return img
