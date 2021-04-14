"""
LAM está en construcción
Versión Consola de python3 0.1
"""

import matplotlib.pyplot as plt

from os import path, mkdir, system
from time import strftime, sleep
from datetime import datetime, date
from pandas import DataFrame, ExcelWriter, read_excel
from numpy import max, min, arctan, pi, arange, meshgrid, hstack, angle, array, sqrt, mean
from warnings import simplefilter
from webbrowser import open_new
from skimage import (io, filters,
                     morphology, transform, img_as_ubyte)
from skimage.color import rgb2gray
from skimage.measure import label, regionprops
from openpyxl import load_workbook

###############################
from tkinter import *
from tkinter import filedialog
##############################

from arrow import utcnow
from reportlab.platypus import PageBreak
from reportlab.platypus import Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.pagesizes import letter
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.lib.colors import black, whitesmoke, cornflowerblue, lightsteelblue
from reportlab.pdfgen import canvas
from reportlab.lib import utils

simplefilter(action='ignore', category=FutureWarning)


# FUNCIONES

def escalar_imagen(imagen):
    """
    :param imagen:
    :return img_as_ubyte(imagen):
    """

    if len(imagen[1]) > 1000 or len(imagen) > 2000:  # Tamaño maximo en X, Y
        imagen = transform.rescale(imagen, 4.0 / 5.0, multichannel=True)
        imagen = escalar_imagen(imagen)
    return img_as_ubyte(imagen)


def filtro_color_verde(imagen):
    """
    :param imagen:
    :return imagen_filtrada:
    """

    canal_verde = rgb2gray(imagen[:, :, 1]) / 255.0
    imagen_gris = rgb2gray(imagen)

    imagen_solo_verde = canal_verde - imagen_gris

    imagen_solo_verde[imagen_solo_verde < 0] = 0

    if max(imagen_solo_verde) <= 1:
        imagen_solo_verde = filters.median(imagen_solo_verde) * 255
    else:
        imagen_solo_verde = filters.median(imagen_solo_verde)

    umbral_color_verde = round(max(imagen_solo_verde) * 0.32)
    imagen_binaria_verde = imagen_solo_verde > umbral_color_verde
    imagen_filtrada = morphology.remove_small_holes(imagen_binaria_verde)

    return imagen_filtrada


def ajustar_imagen(imagen):
    """
    :param imagen:
    :return imagenAjustada:
    """

    imagen_filtrada = filtro_color_verde(imagen)

    referencias = etiquetas(imagen_filtrada)
    referencia_1, referencia_2 = referencias[0], referencias[1]

    coordenadas_referencia = referencia_2 - referencia_1
    angulo_de_rotacion_imagen = arctan(coordenadas_referencia[0] / coordenadas_referencia[1])
    imagen_rotada = transform.rotate(imagen, angulo_de_rotacion_imagen * 180 / pi)

    etiquetas_de_referencia = [referencia_1[1], referencia_2[1]]
    etiquetas_de_referencia.sort()

    espacio_recorte_imagen = abs(referencia_1[1] - referencia_2[1]) / 10

    imagen_ajustada = imagen_rotada[:, int(round(etiquetas_de_referencia[0] - espacio_recorte_imagen)): int(
        round(etiquetas_de_referencia[1] + espacio_recorte_imagen))]

    imagen_ajustada = img_as_ubyte(imagen_ajustada)

    return imagen_ajustada


def cuadricula(centro_x, centro_y, tamanio_x, tamanio_y, tamanio_divisiones):
    """
    :param centro_x:
    :param centro_y:
    :param tamanio_x:
    :param tamanio_y:
    :param tamanio_divisiones:
    :return mesh_x, mesh_y, x_horizontal, y_horizontal, x_vertical, y_vertical:
    """

    # La cuadricula se construye en los cuatro cuadrantes de la imagen

    x_1 = arange(centro_x, tamanio_x, tamanio_divisiones)
    y_1 = arange(centro_y, tamanio_y, tamanio_divisiones)
    [mesh_x_1, mesh_y_1] = meshgrid(x_1, y_1)

    x_2 = arange(centro_x, 0, -tamanio_divisiones)
    y_2 = arange(centro_y, 0, -tamanio_divisiones)
    [mesh_x_2, mesh_y_2] = meshgrid(x_2, y_2)

    x_3 = arange(centro_x, tamanio_x, tamanio_divisiones)
    y_3 = arange(centro_y, 0, -tamanio_divisiones)
    [mesh_x_3, mesh_y_3] = meshgrid(x_3, y_3)

    x_4 = arange(centro_x, 0, -tamanio_divisiones)
    y_4 = arange(centro_y, tamanio_y, tamanio_divisiones)
    [mesh_x_4, mesh_y_4] = meshgrid(x_4, y_4)

    [mesh_x, mesh_y] = meshgrid(hstack((x_1, x_2, x_3, x_4)),
                                hstack((y_1, y_2, y_3, y_4)))

    x_horizontal = hstack([mesh_x_1[0, :], mesh_x_2[0, :], mesh_x_3[0, :], mesh_x_4[0, :]])
    y_horizontal = hstack([mesh_y_1[0, :], mesh_y_2[0, :], mesh_y_3[0, :], mesh_y_4[0, :]])

    x_vertical = hstack((mesh_x_1[:, 0], mesh_x_2[:, 0], mesh_x_3[:, 0], mesh_x_4[:, 0]))
    y_vertical = hstack((mesh_y_1[:, 0], mesh_y_2[:, 0], mesh_y_3[:, 0], mesh_y_4[:, 0]))

    return mesh_x, mesh_y, x_horizontal, y_horizontal, x_vertical, y_vertical


def get_image_for_pdf(path_img, height=1 * mm):
    """
    Obtener la imagen con una altura determinada
    :param path_img:
    :param height:
    :return Image(path, height=height, width=(height * aspect)):
    """

    img = utils.ImageReader(path_img)
    iw, ih = img.getSize()
    aspect = iw / float(ih)
    return Image(path_img, height=height, width=(height * aspect))


# Funciones de la vista Anterior

def tabla_anterior_parte_1(punto_anatomico_1, punto_anatomico_2):
    """
    :param punto_anatomico_1:
    :param punto_anatomico_2:
    :return descendido, angulo:

    |||||||||||||||||||||||||||||||||||||||||||||||
    || Segmento Corporal || Descendido || Angulo ||
    |||||||||||||||||||||||||||||||||||||||||||||||
    || Hombros           || xxx        || xx °   ||
    || Pelvis            || xxx        || xx °   ||
    || Rodilla           || xxx        || xx °   ||
    |||||||||||||||||||||||||||||||||||||||||||||||
    """

    distancia = punto_anatomico_2 - punto_anatomico_1
    angulo = -angle(complex(distancia[1], distancia[0]), deg=True)

    if angulo > angulo_tolerancia:
        descendido = 'Der.'
    elif angulo < -angulo_tolerancia:
        descendido = 'Izq.'
    else:
        descendido = 'Alin.'

    angulo = round(angulo, 4)  # Número de cifras significativas

    return descendido, angulo


def tabla_anterior_parte_2(punto_anatomico_1, punto_anatomico_2, escala):
    """
    :param punto_anatomico_1:
    :param punto_anatomico_2:
    :param escala:
    :return direccion, distancia:

    |||||||||||||||||||||||||||||||||||||||||||||||
    || Referencia || Direccion || Distancia [cm] ||
    |||||||||||||||||||||||||||||||||||||||||||||||
    || Frente     || xxx       || xx             ||
    || Hombros    || xxx       || xx             ||
    || Ombligo    || xxx       || xx             ||
    || Pelvis     || xxx       || xx             ||
    || Rodillas   || xxx       || xx             ||
    || Pies       || xxx       || xx             ||
    |||||||||||||||||||||||||||||||||||||||||||||||
    """

    distancia = (punto_anatomico_1[1] - punto_anatomico_2[1]) * escala

    if distancia > distancia_tolerancia:
        direccion = 'Der.'
    elif distancia < -distancia_tolerancia:
        direccion = 'Izq.'
    else:
        direccion = 'Alin.'

    distancia = round(distancia, 4)  # Número de cifras significativas

    return direccion, distancia


def tabla_anterior_parte_3(punto_anatomico_1, punto_anatomico_2):
    """

    :param punto_anatomico_1:
    :param punto_anatomico_2:
    :return direccion, angulo:

    ||||||||||||||||||||||||||||||||||||||||||||||
    || Segmento Corporal || Direccion || Angulo ||
    ||||||||||||||||||||||||||||||||||||||||||||||
    || Pie Izquierdo     || xxx       || xx °   ||
    || Pie Derecho       || xxx       || xx °   ||
    ||||||||||||||||||||||||||||||||||||||||||||||
    """

    distancia = punto_anatomico_1 - punto_anatomico_2
    angulo = abs(angle(complex(distancia[1], distancia[0]), deg=True)) - 90

    if angulo > angulo_tolerancia:
        direccion = 'Rot.Ext.'
    elif angulo < -angulo_tolerancia:
        direccion = 'Rot.Int.'
    else:
        direccion = 'Alin.'

    angulo = round(angulo, 4)

    return direccion, angulo


# Funciones de la vista Posterior

def tabla_posterior_parte_1(punto_anatomico_1, punto_anatomico_2):
    """
    :param punto_anatomico_1:
    :param punto_anatomico_2:
    :return descendido, angulo:

    |||||||||||||||||||||||||||||||||||||||||||||||
    || Segmento Corporal || Descendido || Angulo ||
    |||||||||||||||||||||||||||||||||||||||||||||||
    || Hombros           || xxx        || xx °   ||
    || Pelvis            || xxx        || xx °   ||
    || Rodilla           || xxx        || xx °   ||
    |||||||||||||||||||||||||||||||||||||||||||||||
    """

    distancia = punto_anatomico_2 - punto_anatomico_1
    angulo = angle(complex(distancia[1], distancia[0]), deg=True)

    if angulo > angulo_tolerancia:
        descendido = 'Der.'
    elif angulo < -angulo_tolerancia:
        descendido = 'Izq.'
    else:
        descendido = 'Alin.'

    angulo = round(angulo, 4)  # Número de cifras significativas

    return descendido, angulo


def tabla_posterior_parte_2(punto_anatomico_1, punto_anatomico_2, escala):
    """
    :param punto_anatomico_1:
    :param punto_anatomico_2:
    :param escala:
    :return direccion, distancia:

    |||||||||||||||||||||||||||||||||||||||||||||||
    || Referencia || Direccion || Distancia [cm] ||
    |||||||||||||||||||||||||||||||||||||||||||||||
    || Hombros    || xxx       || xx             ||
    || 7maCervical|| xxx       || xx             ||
    || 5taTorácica|| xxx       || xx             ||
    || Pelvis     || xxx       || xx             ||
    || Rodillas   || xxx       || xx             ||
    || Tobillos   || xxx       || xx             ||
    |||||||||||||||||||||||||||||||||||||||||||||||
    """

    distancia = (punto_anatomico_2[1] - punto_anatomico_1[1]) * escala

    if distancia > distancia_tolerancia:
        direccion = 'Der.'
    elif distancia < -distancia_tolerancia:
        direccion = 'Izq.'
    else:
        direccion = 'Alin.'

    distancia = round(distancia, 4)  # Número de cifras significativas

    return direccion, distancia


def tabla_posterior_parte_3(punto_anatomico_1, punto_anatomico_2):
    """

    :param punto_anatomico_1:
    :param punto_anatomico_2:
    :return direccion, angulo:

    ||||||||||||||||||||||||||||||||||||||||||||||
    || Segmento Corporal || Direccion || Angulo ||
    ||||||||||||||||||||||||||||||||||||||||||||||
    || Pie Izquierdo     || xxx       || xx °   ||
    || Pie Derecho       || xxx       || xx °   ||
    ||||||||||||||||||||||||||||||||||||||||||||||
    """

    distancia = punto_anatomico_1 - punto_anatomico_2
    angulo = 90 - abs(angle(complex(distancia[1], distancia[0]), deg=True))

    if angulo > angulo_tolerancia:
        direccion = 'Valgo'
    elif angulo < -angulo_tolerancia:
        direccion = 'Varo'
    else:
        direccion = 'Alin.'

    angulo = round(angulo, 4)

    return direccion, angulo


# Funciones de la vista Lateral Derecha

def tabla_lateral_d_parte_1(punto_anatomico_1, punto_anatomico_2):
    """

    :param punto_anatomico_1:
    :param punto_anatomico_2:
    :return direccion, angulo:

    ||||||||||||||||||||||||||||||||||||||||||||||
    || Segmento Corporal || Direccion || Angulo ||
    ||||||||||||||||||||||||||||||||||||||||||||||
    || Cabeza-Hombro     || xxx       || xx °   ||
    || Hombro-Pelvis     || xxx       || xx °   ||
    || Caderas-Rodillas  || xxx       || xx °   ||
    || Rodillas-Pies     || xxx       || xx °   ||
    ||||||||||||||||||||||||||||||||||||||||||||||
    """

    distancia = punto_anatomico_1 - punto_anatomico_2
    angulo = 90 - abs(angle(complex(distancia[1], distancia[0]), deg=True))

    if angulo < -angulo_tolerancia:
        direccion = 'Pos.'
    elif angulo > angulo_tolerancia:
        direccion = 'Ant.'
    else:
        direccion = 'Alin.'

    angulo = round(angulo, 4)

    return direccion, angulo


def tabla_lateral_d_parte_2(punto_anatomico_1, punto_anatomico_2):
    """

    :param punto_anatomico_1:
    :param punto_anatomico_2:
    :return direccion, angulo:

    ||||||||||||||||||||||||||||||||||||||||||||||
    || Segmento Corporal || Direccion || Angulo ||
    ||||||||||||||||||||||||||||||||||||||||||||||
    || Pelvis            || xxx       || xx °   ||
    ||||||||||||||||||||||||||||||||||||||||||||||
    """

    distancia = punto_anatomico_1 - punto_anatomico_2
    angulo = 180 - abs(angle(complex(distancia[1], distancia[0]), deg=True))

    if angulo > 15:
        direccion = 'Ant.'
    elif angulo < 5:
        direccion = 'Pos.'
    else:
        direccion = 'Normal'

    angulo = round(angulo, 4)

    return direccion, angulo


def tabla_lateral_d_parte_3(punto_anatomico_1, punto_anatomico_2, escala):
    """
    :param punto_anatomico_1:
    :param punto_anatomico_2:
    :param escala:
    :return direccion, distancia:

    |||||||||||||||||||||||||||||||||||||||||||||||
    || Referencia || Direccion || Distancia [cm] ||
    |||||||||||||||||||||||||||||||||||||||||||||||
    || Hombros    || xxx       || xx             ||
    || 7maCervical|| xxx       || xx             ||
    || 5taTorácica|| xxx       || xx             ||
    || Pelvis     || xxx       || xx             ||
    || Rodillas   || xxx       || xx             ||
    || Tobillos   || xxx       || xx             ||
    |||||||||||||||||||||||||||||||||||||||||||||||
    """

    distancia = (punto_anatomico_2[1] - punto_anatomico_1[1]) * escala

    if distancia > distancia_tolerancia:
        direccion = 'Ant.'
    elif distancia < -distancia_tolerancia:
        direccion = 'Pos.'
    else:
        direccion = 'Alin.'

    distancia = round(distancia, 4)  # Número de cifras significativas

    return direccion, distancia


# Clase de segmentación

def etiquetas(imagen):
    """
    :param imagen:
    :return [referencia_1, referencia_2, centros_coordenada_y, centros_coordenada_x, razon_de_escala]:
    """

    imagen = label(imagen)
    regiones = regionprops(imagen)
    centros_coordenada_y = []
    centros_coordenadas_x = []
    for i in range(0, len(regiones)):
        y, x = regiones[i].centroid
        centros_coordenada_y.append(y)
        centros_coordenadas_x.append(x)

    posicion_coordenada = [i for i, x in enumerate(centros_coordenadas_x) if x == min(centros_coordenadas_x)]
    referencia_1 = [centros_coordenada_y[posicion_coordenada[0]], centros_coordenadas_x[posicion_coordenada[0]]]
    centros_coordenada_y.pop(posicion_coordenada[0])
    centros_coordenadas_x.pop(posicion_coordenada[0])

    posicion_coordenada = [i for i, x in enumerate(centros_coordenadas_x) if x == max(centros_coordenadas_x)]
    referencia_2 = [centros_coordenada_y[posicion_coordenada[0]], centros_coordenadas_x[posicion_coordenada[0]]]
    centros_coordenada_y.pop(posicion_coordenada[0])
    centros_coordenadas_x.pop(posicion_coordenada[0])

    etiquetas_de_referencia = [referencia_1, referencia_2]

    if etiquetas_de_referencia[0][0] == etiquetas_de_referencia[1][0]:
        referencia_1 = etiquetas_de_referencia[0]
        referencia_2 = etiquetas_de_referencia[1]
    else:
        referencia_coordenada_y = [etiquetas_de_referencia[0][0], etiquetas_de_referencia[1][0]]
        posicion_coordenada = [i for i, x in enumerate(referencia_coordenada_y) if
                               x == min(referencia_coordenada_y)]
        referencia_1 = etiquetas_de_referencia[posicion_coordenada[0]]
        posicion_coordenada = [i for i, x in enumerate(referencia_coordenada_y) if
                               x == max(referencia_coordenada_y)]
        referencia_2 = etiquetas_de_referencia[posicion_coordenada[0]]

    etiquetas_de_referencia = [referencia_1[1], referencia_2[1]]
    etiquetas_de_referencia.sort()

    referencia_1 = array(referencia_1)
    referencia_2 = array(referencia_2)
    centros_coordenada_y = array(centros_coordenada_y)
    centros_coordenada_x = array(centros_coordenadas_x)
    razon_de_escala = 100.0 / sqrt((etiquetas_de_referencia[0] ** 2 + etiquetas_de_referencia[1] ** 2))

    return referencia_1, referencia_2, centros_coordenada_y, centros_coordenada_x, razon_de_escala


# REPORTE PDF

def generar_reporte(datos_anterior, datos_posterior, datos_lateral_d):
    """
    Genera el reporte PDF con su respectivo nombre
    """
    nombre_archivo_pdf = nombre + '_' + strftime("%Y%m%d") + '_' + strftime("%H%M%S")
    reporte = ReportePdf(carpeta_voluntario + nombre_archivo_pdf + '.pdf').exportar(datos_anterior, datos_posterior,
                                                                                    datos_lateral_d)
    print(reporte)
    return nombre_archivo_pdf


class NumeracionPaginas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        canvas.Canvas.__init__(self, *args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        """Agregar información de la página a cada página (página x de y)"""
        numero_paginas = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(numero_paginas)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_number(self, conteo_paginas):
        self.drawRightString(204 * mm, 15 * mm + (5 * mm),
                             "{}/{}".format(self._pageNumber, conteo_paginas))

    # ===================== FUNCIÓN generarReporte =====================


# Funciones de evaluacion

def evaluacion_anterior(dir_foto_anterior):
    imagen = io.imread(dir_foto_anterior)
    imagen = escalar_imagen(imagen)
    # io.imshow(imagen)
    # plt.close()            # Para mostrar la imagen cambiar "close" por "show"
    imagen_anterior = ajustar_imagen(imagen)

    imagen_anterior_filtrada = filtro_color_verde(imagen_anterior)

    [referencia_1, referencia_2, centros_coordenada_y,
     centros_coordenada_x, razon_de_escala] = etiquetas(imagen_anterior_filtrada)

    '''
    PUTNOS ANATOMICOS
    f1 = Entrecejo
    f2 = Mentón
    f3 = Hombro derecho
    f4 = Hombro izquierdo
    f5 = Esternón
    f6 = Ombligo
    f7 = Perlvis derecha
    f8 = Perlvis izquierda
    f9 = Rodilla derecho
    f10 = Rodilla izquierda
    f11 = Tobillo derecho
    f12 = Tobillo izquierdo
    f13 = Dedo gordo derecho
    f14 = Dedo gordo izquierdo
    f_centro_hombros = Centro hombros
    f_centro_y = Centro en Y (Pelvis)
    f_centro_rodillas = Centro rodillas
    f_centro_y = Centro en X (Tobillos)
    f_centro_pies = Centro en dedos pies
    '''

    if len(centros_coordenada_x) > 14:
        print("Existen demasiados puntos en la imagen")
        plt.figure(1)
        plt.title('Vista Anterior: {0}/{1}'.format(len(centros_coordenada_x), 14))
        plt.plot(centros_coordenada_x, centros_coordenada_y, 'b*', markersize="5")
        io.imshow(imagen_anterior)
        plt.show()

    elif len(centros_coordenada_x) < 14:
        print("Existen menos puntos en la imagen")
        plt.figure(1)
        plt.title('Vista Anterior: {0}/{1}'.format(len(centros_coordenada_x), 14))
        plt.plot(centros_coordenada_x, centros_coordenada_y, 'b*', markersize="5")
        io.imshow(imagen_anterior)
        plt.show()

    else:

        f1 = (centros_coordenada_y[0], centros_coordenada_x[0])
        # f2 = (centros_coordenada_y[1], centros_coordenada_x[1])

        coordenada_temp_y = [centros_coordenada_y[2], centros_coordenada_y[3], centros_coordenada_y[4]]
        coordenada_temp_x = [centros_coordenada_x[2], centros_coordenada_x[3], centros_coordenada_x[4]]
        posicion = [i for i, x in enumerate(coordenada_temp_x) if x == min(coordenada_temp_x)]
        f3 = coordenada_temp_y[posicion[0]], coordenada_temp_x[posicion[0]]
        coordenada_temp_y.pop(posicion[0])
        coordenada_temp_x.pop(posicion[0])
        posicion = [i for i, x in enumerate(coordenada_temp_x) if x == max(coordenada_temp_x)]
        f4 = coordenada_temp_y[posicion[0]], coordenada_temp_x[posicion[0]]
        coordenada_temp_y.pop(posicion[0])
        coordenada_temp_x.pop(posicion[0])
        # f5 = coordenada_temp_y[0], coordenada_temp_x[0]

        coordenada_temp_y = [centros_coordenada_y[5], centros_coordenada_y[6], centros_coordenada_y[7]]
        coordenada_temp_x = [centros_coordenada_x[5], centros_coordenada_x[6], centros_coordenada_x[7]]
        posicion = [i for i, x in enumerate(coordenada_temp_x) if x == min(coordenada_temp_x)]
        f7 = coordenada_temp_y[posicion[0]], coordenada_temp_x[posicion[0]]
        coordenada_temp_y.pop(posicion[0])
        coordenada_temp_x.pop(posicion[0])
        posicion = [i for i, x in enumerate(coordenada_temp_x) if x == max(coordenada_temp_x)]
        f8 = coordenada_temp_y[posicion[0]], coordenada_temp_x[posicion[0]]
        coordenada_temp_y.pop(posicion[0])
        coordenada_temp_x.pop(posicion[0])
        f6 = coordenada_temp_y[0], coordenada_temp_x[0]

        coordenada_temp_y = [centros_coordenada_y[8], centros_coordenada_y[9]]
        coordenada_temp_x = [centros_coordenada_x[8], centros_coordenada_x[9]]
        posicion = [i for i, x in enumerate(coordenada_temp_x) if x == min(coordenada_temp_x)]
        f9 = coordenada_temp_y[posicion[0]], coordenada_temp_x[posicion[0]]
        posicion = [i for i, x in enumerate(coordenada_temp_x) if x == max(coordenada_temp_x)]
        f10 = coordenada_temp_y[posicion[0]], coordenada_temp_x[posicion[0]]

        coordenada_temp_y = [centros_coordenada_y[10], centros_coordenada_y[11]]
        coordenada_temp_x = [centros_coordenada_x[10], centros_coordenada_x[11]]
        posicion = [i for i, x in enumerate(coordenada_temp_x) if x == min(coordenada_temp_x)]
        f11 = coordenada_temp_y[posicion[0]], coordenada_temp_x[posicion[0]]
        posicion = [i for i, x in enumerate(coordenada_temp_x) if x == max(coordenada_temp_x)]
        f12 = coordenada_temp_y[posicion[0]], coordenada_temp_x[posicion[0]]

        coordenada_temp_y = [centros_coordenada_y[12], centros_coordenada_y[13]]
        coordenada_temp_x = [centros_coordenada_x[12], centros_coordenada_x[13]]
        posicion = [i for i, x in enumerate(coordenada_temp_x) if x == min(coordenada_temp_x)]
        f13 = coordenada_temp_y[posicion[0]], coordenada_temp_x[posicion[0]]
        posicion = [i for i, x in enumerate(coordenada_temp_x) if x == max(coordenada_temp_x)]
        f14 = coordenada_temp_y[posicion[0]], coordenada_temp_x[posicion[0]]

        f_centro_hombros = mean([f3, f4], axis=0)
        f_centro_y = mean([f7, f8], axis=0)
        f_centro_rodillas = mean([f9, f10], axis=0)
        f_centro_x = mean([f11, f12], axis=0)
        f_centro_pies = mean([f13, f14], axis=0)

        # F2 y F5 aún sin uso

        f1 = array(f1)
        # f2 = array(f2)
        f3 = array(f3)
        f4 = array(f4)
        # f5 = array(f5)
        f6 = array(f6)
        f7 = array(f7)
        f8 = array(f8)
        f9 = array(f9)
        f10 = array(f10)
        f11 = array(f11)
        f12 = array(f12)
        f13 = array(f13)
        f14 = array(f14)

        f_centro_hombros = array(f_centro_hombros)
        f_centro_y = array(f_centro_y)
        f_centro_rodillas = array(f_centro_rodillas)
        f_centro_x = array(f_centro_x)
        f_centro_pies = array(f_centro_pies)

        plt.figure(1)
        plt.title('Vista Anterior')

        plt.plot(centros_coordenada_x, centros_coordenada_y, 'b*', markersize="1")

        plt.plot(f_centro_hombros[1], f_centro_hombros[0], 'rx', markersize="3")
        plt.plot(f_centro_y[1], f_centro_y[0], 'rx', markersize="3")
        plt.plot(f_centro_rodillas[1], f_centro_rodillas[0], 'rx', markersize="3")
        plt.plot(f_centro_x[1], f_centro_x[0], 'rx', markersize="3")
        plt.plot(f_centro_pies[1], f_centro_pies[0], 'rx', markersize="3")

        coordenadas_referencia = referencia_2 - referencia_1
        tamanio_divisiones = sqrt((coordenadas_referencia[0] ** 2 + coordenadas_referencia[1] ** 2)) / 20.0

        centro_x = f_centro_x[1]
        centro_y = f_centro_y[0]
        tamanio_x = len(imagen_anterior[1])
        tamanio_y = len(imagen_anterior)

        (x_cuadricula, y_cuadricula, x_horizontal,
         y_horizontal, x_vertical, y_vertical) = cuadricula(centro_x, centro_y, tamanio_x,
                                                            tamanio_y, tamanio_divisiones)

        plt.plot(x_cuadricula, y_cuadricula, 'k', x_cuadricula.T, y_cuadricula.T, 'k', linewidth=0.1)
        plt.plot(x_horizontal, y_horizontal, 'r', linewidth=0.3)
        plt.plot(x_vertical, y_vertical, 'r', linewidth=0.3)

        io.imshow(imagen_anterior)

        dir_imagen_anterior = img_voluntario + nombre_imagen_anterior + '.jpg'
        # time.sleep(1)

        plt.savefig(dir_imagen_anterior, dpi=500)
        plt.close()  # Para mostrar la imagen cambiar "close" por "show"

        # TA1
        hombro_descendido, angulo_hombro = tabla_anterior_parte_1(f3, f4)
        pelvis_descendida, angulo_pelvis = tabla_anterior_parte_1(f7, f8)
        rodilla_descendida, angulo_rodilla = tabla_anterior_parte_1(f9, f10)

        # TA2
        direccion_frente, distancia_frente = tabla_anterior_parte_2(f_centro_x, f1, razon_de_escala)
        direccion_hombros, distancia_hombros = tabla_anterior_parte_2(f_centro_x, f_centro_hombros, razon_de_escala)
        direccion_ombligo, distancia_ombligo = tabla_anterior_parte_2(f_centro_x, f6, razon_de_escala)
        direccion_pelvis, distancia_pelvis = tabla_anterior_parte_2(f_centro_x, f_centro_y, razon_de_escala)
        direccion_rodillas, distancia_rodillas = tabla_anterior_parte_2(f_centro_x, f_centro_rodillas, razon_de_escala)
        direccion_pies, distancia_pies = tabla_anterior_parte_2(f_centro_x, f_centro_pies, razon_de_escala)

        # TA3
        direccion_pie_izquierdo, angulo_pie_izquierdo = tabla_anterior_parte_3(f12, f14)
        direccion_pie_derecho, angulo_pie_derecho = tabla_anterior_parte_3(f13, f11)

        datos = (angulo_tolerancia, distancia_tolerancia, hombro_descendido, angulo_hombro, pelvis_descendida,
                 angulo_pelvis, rodilla_descendida, angulo_rodilla, direccion_frente, distancia_frente,
                 direccion_hombros, distancia_hombros, direccion_ombligo, distancia_ombligo, direccion_pelvis,
                 distancia_pelvis, direccion_rodillas, distancia_rodillas, direccion_pies, distancia_pies,
                 direccion_pie_izquierdo, angulo_pie_izquierdo, direccion_pie_derecho, angulo_pie_derecho)

        return datos
    return 0


def evaluacion_posterior(dir_foto_posterior):
    imagen = io.imread(dir_foto_posterior)
    imagen = escalar_imagen(imagen)
    # io.imshow(imagen)
    # plt.close()            # Para mostrar la imagen cambiar "close" por "show"
    imagen_posterior = ajustar_imagen(imagen)

    imagen_posterior_filtrada = filtro_color_verde(imagen_posterior)

    [referencia_1, referencia_2, centros_coordenada_y,
     centros_coordenada_x, razon_de_escala] = etiquetas(imagen_posterior_filtrada)

    '''
    PUTNOS ANATOMICOS
    p1 = 7th Cervical
    p2 = 5th Thoracic
    p3 = Hombro derecho
    p4 = Hombro izquierdo
    p5 = Perlvis derecha
    p6 = Perlvis izquierda
    p7 = Rodilla derecho
    p8 = Rodilla izquierda
    p9 = Tobillo derecho
    p10 = Tobillo izquierdo
    p11 = Planta derecho
    p12 = Planta izquierdo
    p_centro_hombros = Centro hombros
    p_centro_y= Centro en Y (Pelvis)
    p_centro_rodillas= Centro rodillas
    p_centro_tobillos = Centro en tobillos
    p_centro_x = Centro en X (Platas de los pies)
    '''

    if len(centros_coordenada_x) > 12:
        print("Existen demasiados puntos en la imagen")
        plt.figure(1)
        plt.title('Vista Posterior: {0}/{1}'.format(len(centros_coordenada_x), 12))
        plt.plot(centros_coordenada_x, centros_coordenada_y, 'b*', markersize="5")
        io.imshow(imagen_posterior)
        plt.show()

    elif len(centros_coordenada_x) < 12:
        print("Existen menos puntos en la imagen")
        plt.figure(1)
        plt.title('Vista Posterior: {0}/{1}'.format(len(centros_coordenada_x), 12))
        plt.plot(centros_coordenada_x, centros_coordenada_y, 'b*', markersize="5")
        io.imshow(imagen_posterior)
        plt.show()

    else:

        coordenada_temp_y = [centros_coordenada_y[0], centros_coordenada_y[1], centros_coordenada_y[2]]
        coordenada_temp_x = [centros_coordenada_x[0], centros_coordenada_x[1], centros_coordenada_x[2]]
        posicion = [i for i, x in enumerate(coordenada_temp_x) if x == min(coordenada_temp_x)]
        p4 = coordenada_temp_y[posicion[0]], coordenada_temp_x[posicion[0]]
        coordenada_temp_y.pop(posicion[0])
        coordenada_temp_x.pop(posicion[0])
        posicion = [i for i, x in enumerate(coordenada_temp_x) if x == max(coordenada_temp_x)]
        p3 = coordenada_temp_y[posicion[0]], coordenada_temp_x[posicion[0]]
        coordenada_temp_y.pop(posicion[0])
        coordenada_temp_x.pop(posicion[0])
        p1 = coordenada_temp_y[0], coordenada_temp_x[0]

        p2 = (centros_coordenada_y[3], centros_coordenada_x[3])

        coordenada_temp_y = [centros_coordenada_y[4], centros_coordenada_y[5]]
        coordenada_temp_x = [centros_coordenada_x[4], centros_coordenada_x[5]]
        posicion = [i for i, x in enumerate(coordenada_temp_x) if x == min(coordenada_temp_x)]
        p6 = coordenada_temp_y[posicion[0]], coordenada_temp_x[posicion[0]]
        posicion = [i for i, x in enumerate(coordenada_temp_x) if x == max(coordenada_temp_x)]
        p5 = coordenada_temp_y[posicion[0]], coordenada_temp_x[posicion[0]]

        coordenada_temp_y = [centros_coordenada_y[6], centros_coordenada_y[7]]
        coordenada_temp_x = [centros_coordenada_x[6], centros_coordenada_x[7]]
        posicion = [i for i, x in enumerate(coordenada_temp_x) if x == min(coordenada_temp_x)]
        p8 = coordenada_temp_y[posicion[0]], coordenada_temp_x[posicion[0]]
        posicion = [i for i, x in enumerate(coordenada_temp_x) if x == max(coordenada_temp_x)]
        p7 = coordenada_temp_y[posicion[0]], coordenada_temp_x[posicion[0]]

        coordenada_temp_y = [centros_coordenada_y[8], centros_coordenada_y[9]]
        coordenada_temp_x = [centros_coordenada_x[8], centros_coordenada_x[9]]
        posicion = [i for i, x in enumerate(coordenada_temp_x) if x == min(coordenada_temp_x)]
        p10 = coordenada_temp_y[posicion[0]], coordenada_temp_x[posicion[0]]
        posicion = [i for i, x in enumerate(coordenada_temp_x) if x == max(coordenada_temp_x)]
        p9 = coordenada_temp_y[posicion[0]], coordenada_temp_x[posicion[0]]

        coordenada_temp_y = [centros_coordenada_y[10], centros_coordenada_y[11]]
        coordenada_temp_x = [centros_coordenada_x[10], centros_coordenada_x[11]]
        posicion = [i for i, x in enumerate(coordenada_temp_x) if x == min(coordenada_temp_x)]
        p12 = coordenada_temp_y[posicion[0]], coordenada_temp_x[posicion[0]]
        posicion = [i for i, x in enumerate(coordenada_temp_x) if x == max(coordenada_temp_x)]
        p11 = coordenada_temp_y[posicion[0]], coordenada_temp_x[posicion[0]]

        p_centro_hombros = mean([p4, p3], axis=0)
        p_centro_y = mean([p6, p5], axis=0)
        p_centro_rodillas = mean([p8, p7], axis=0)
        p_centro_tobillos = mean([p10, p9], axis=0)
        p_centro_x = mean([p12, p11], axis=0)

        p1 = array(p1)
        p2 = array(p2)
        p3 = array(p3)
        p4 = array(p4)
        p5 = array(p5)
        p6 = array(p6)
        p7 = array(p7)
        p8 = array(p8)
        p9 = array(p9)
        p10 = array(p10)
        p11 = array(p11)
        p12 = array(p12)

        p_centro_hombros = array(p_centro_hombros)
        p_centro_y = array(p_centro_y)
        p_centro_rodillas = array(p_centro_rodillas)
        p_centro_tobillos = array(p_centro_tobillos)
        p_centro_x = array(p_centro_x)

        plt.figure(1)
        plt.title('Vista Posterior')

        plt.plot(centros_coordenada_x, centros_coordenada_y, 'b*', markersize="1")

        plt.plot(p_centro_hombros[1], p_centro_hombros[0], 'rx', markersize="3")
        plt.plot(p_centro_y[1], p_centro_y[0], 'rx', markersize="3")
        plt.plot(p_centro_rodillas[1], p_centro_rodillas[0], 'rx', markersize="3")
        plt.plot(p_centro_tobillos[1], p_centro_tobillos[0], 'rx', markersize="3")
        plt.plot(p_centro_x[1], p_centro_x[0], 'rx', markersize="3")

        coordenadas_referencia = referencia_2 - referencia_1
        tamanio_divisiones = sqrt((coordenadas_referencia[0] ** 2 + coordenadas_referencia[1] ** 2)) / 20.0

        centro_x = p_centro_x[1]
        centro_y = p_centro_y[0]
        tamanio_x = len(imagen_posterior[1])
        tamanio_y = len(imagen_posterior)

        (x_cuadricula, y_cuadricula, x_horizontal,
         y_horizontal, x_vertical, y_vertical) = cuadricula(centro_x, centro_y, tamanio_x,
                                                            tamanio_y, tamanio_divisiones)

        plt.plot(x_cuadricula, y_cuadricula, 'k', x_cuadricula.T, y_cuadricula.T, 'k', linewidth=0.1)
        plt.plot(x_horizontal, y_horizontal, 'r', linewidth=0.3)
        plt.plot(x_vertical, y_vertical, 'r', linewidth=0.3)

        io.imshow(imagen_posterior)

        dir_imagen_posterior = img_voluntario + nombre_imagen_posterior + '.jpg'
        # time.sleep(1)

        plt.savefig(dir_imagen_posterior, dpi=500)
        plt.close()  # Para mostrar la imagen cambiar "close" por "show"

        # TP1
        hombro_descendido, angulo_hombro = tabla_posterior_parte_1(p4, p3)
        pelvis_descendida, angulo_pelvis = tabla_posterior_parte_1(p6, p5)
        rodilla_descendida, angulo_rodilla = tabla_posterior_parte_1(p8, p7)

        # TP2
        direccion_hombros, distancia_hombros = tabla_posterior_parte_2(p_centro_x, p_centro_hombros, razon_de_escala)
        direccion_7ma_cervical, distancia_7ma_cervical = tabla_posterior_parte_2(p_centro_x, p1, razon_de_escala)
        direccion_5ta_toracica, distancia_5ta_toracica = tabla_posterior_parte_2(p_centro_x, p2, razon_de_escala)
        direccion_pelvis, distancia_pelvis = tabla_posterior_parte_2(p_centro_x, p_centro_y, razon_de_escala)
        direccion_rodillas, distancia_rodillas = tabla_posterior_parte_2(p_centro_x, p_centro_rodillas, razon_de_escala)
        direccion_tobillos, distancia_tobillos = tabla_posterior_parte_2(p_centro_x, p_centro_tobillos, razon_de_escala)

        # TP3
        direccion_pie_izquierdo, angulo_pie_izquierdo = tabla_posterior_parte_3(p10, p12)
        direccion_pie_derecho, angulo_pie_derecho = tabla_posterior_parte_3(p11, p9)

        datos = (angulo_tolerancia, distancia_tolerancia, hombro_descendido, angulo_hombro, pelvis_descendida,
                 angulo_pelvis, rodilla_descendida, angulo_rodilla, direccion_hombros, distancia_hombros,
                 direccion_7ma_cervical, distancia_7ma_cervical, direccion_5ta_toracica, distancia_5ta_toracica,
                 direccion_pelvis, distancia_pelvis, direccion_rodillas, distancia_rodillas, direccion_tobillos,
                 distancia_tobillos, direccion_pie_izquierdo, angulo_pie_izquierdo, direccion_pie_derecho,
                 angulo_pie_derecho)

        return datos
    return 0


def evaluacion_lateral_d(dir_foto_lateral_d):
    imagen = io.imread(dir_foto_lateral_d)
    imagen = escalar_imagen(imagen)
    # io.imshow(imagen)
    # plt.close()            # Para mostrar la imagen cambiar "close" por "show"
    imagen_lateral_d = ajustar_imagen(imagen)

    imagen_lateral_d_filtrada = filtro_color_verde(imagen_lateral_d)

    [referencia_1, referencia_2, centros_coordenada_y,
     centros_coordenada_x, razon_de_escala] = etiquetas(imagen_lateral_d_filtrada)

    '''
    PUTNOS ANATOMICOS
    l1 = Oido
    l2 = Hombro
    l3 = Pelvis Posterior
    l4 = Pelvis Anterior
    l5 = Cadera
    l6 = Rodilla
    l7 = Planta
    l_centro_y = Centro en Y (Pelvis)
    '''

    if len(centros_coordenada_x) > 7:
        print("Existen demasiados puntos en la imagen")
        plt.figure(1)
        plt.title('Lateral Derecha: {0}/{1}'.format(len(centros_coordenada_x), 7))
        plt.plot(centros_coordenada_x, centros_coordenada_y, 'b*', markersize="5")
        io.imshow(imagen_lateral_d)
        plt.show()

    elif len(centros_coordenada_x) < 7:
        print("Existen menos puntos en la imagen")
        plt.figure(1)
        plt.title('Lateral Derecha: {0}/{1}'.format(len(centros_coordenada_x), 7))
        plt.plot(centros_coordenada_x, centros_coordenada_y, 'b*', markersize="5")
        io.imshow(imagen_lateral_d)
        plt.show()

    else:

        l1 = (centros_coordenada_y[0], centros_coordenada_x[0])
        l2 = (centros_coordenada_y[1], centros_coordenada_x[1])

        coordenada_temp_y = [centros_coordenada_y[2], centros_coordenada_y[3]]
        coordenada_temp_x = [centros_coordenada_x[2], centros_coordenada_x[3]]
        posicion = [i for i, x in enumerate(coordenada_temp_x) if x == min(coordenada_temp_x)]
        l3 = coordenada_temp_y[posicion[0]], coordenada_temp_x[posicion[0]]
        posicion = [i for i, x in enumerate(coordenada_temp_x) if x == max(coordenada_temp_x)]
        l4 = coordenada_temp_y[posicion[0]], coordenada_temp_x[posicion[0]]

        l5 = (centros_coordenada_y[4], centros_coordenada_x[4])
        l6 = (centros_coordenada_y[5], centros_coordenada_x[5])
        l7 = (centros_coordenada_y[6], centros_coordenada_x[6])

        l_centro_y = mean([l3, l4], axis=0)

        l1 = array(l1)
        l2 = array(l2)
        l3 = array(l3)
        l4 = array(l4)
        l5 = array(l5)
        l6 = array(l6)
        l7 = array(l7)

        l_centro_y = array(l_centro_y)

        plt.figure(1)
        plt.title('Vista Lateral Derecha')

        plt.plot(centros_coordenada_x, centros_coordenada_y, 'b*', markersize="1")

        plt.plot(l_centro_y[1], l_centro_y[0], 'rx', markersize="3")

        coordenadas_referencia = referencia_2 - referencia_1
        tamanio_divisiones = sqrt((coordenadas_referencia[0] ** 2 + coordenadas_referencia[1] ** 2)) / 20.0

        centro_x = l7[1]
        centro_y = l_centro_y[0]
        tamanio_x = len(imagen_lateral_d[1])
        tamanio_y = len(imagen_lateral_d)

        (x_cuadricula, y_cuadricula, x_horizontal,
         y_horizontal, x_vertical, y_vertical) = cuadricula(centro_x, centro_y, tamanio_x,
                                                            tamanio_y, tamanio_divisiones)

        plt.plot(x_cuadricula, y_cuadricula, 'k', x_cuadricula.T, y_cuadricula.T, 'k', linewidth=0.1)
        plt.plot(x_horizontal, y_horizontal, 'r', linewidth=0.3)
        plt.plot(x_vertical, y_vertical, 'r', linewidth=0.3)

        io.imshow(imagen_lateral_d)

        dir_imagen_lateral_d = img_voluntario + nombre_imagen_lateral_d + '.jpg'
        # time.sleep(1)

        plt.savefig(dir_imagen_lateral_d, dpi=500)
        plt.close()  # Para mostrar la imagen cambiar "close" por "show"

        # TL1
        direccion_cabeza_hombro, angulo_cabeza_hombro = tabla_lateral_d_parte_1(l1, l2)
        direccion_hombro_pelvis, angulo_hombro_pelvis = tabla_lateral_d_parte_1(l2, l_centro_y)
        direccion_cadera_rodillas, angulo_cadera_rodillas = tabla_lateral_d_parte_1(l5, l6)
        direccion_rodillas_pies, angulo_rodillas_pies = tabla_lateral_d_parte_1(l6, l7)

        # TL2
        direccion_pelvis, angulo_pelvis = tabla_lateral_d_parte_2(l3, l4)

        # TL3
        direccion_cabeza, distancia_cabeza = tabla_lateral_d_parte_3(l7, l1, razon_de_escala)
        direccion_hombro, distancia_hombro = tabla_lateral_d_parte_3(l7, l2, razon_de_escala)
        direccion_pelvis_tabla_3, distancia_pelvis = tabla_lateral_d_parte_3(l7, l_centro_y, razon_de_escala)
        direccion_cadera, distancia_cadera = tabla_lateral_d_parte_3(l7, l5, razon_de_escala)
        direccion_rodilla, distancia_rodilla = tabla_lateral_d_parte_3(l7, l6, razon_de_escala)

        datos = (angulo_tolerancia, distancia_tolerancia, direccion_cabeza_hombro, angulo_cabeza_hombro,
                 direccion_hombro_pelvis, angulo_hombro_pelvis, direccion_cadera_rodillas, angulo_cadera_rodillas,
                 direccion_rodillas_pies, angulo_rodillas_pies, direccion_pelvis, angulo_pelvis, direccion_cabeza,
                 distancia_cabeza, direccion_hombro, distancia_hombro, direccion_pelvis_tabla_3, distancia_pelvis,
                 direccion_cadera, distancia_cadera, direccion_rodilla, distancia_rodilla)

        return datos
    return 0


class ReportePdf(object):
    """
    Exportar los datos del analisis al PDF.
    """

    def __init__(self, nombre_archivo_pdf):
        super(ReportePdf, self).__init__()

        self.nombre_pdf = nombre_archivo_pdf
        self.estilos = getSampleStyleSheet()
        self.ancho, self.alto = letter

    def exportar(self, db_anterior, db_posterior, db_lateral_d):
        """Exportar los datos a un archivo PDF."""

        PS = ParagraphStyle

        alineacion_titulo = PS(name="centrar", alignment=TA_CENTER, fontSize=14,
                               leading=10, textColor=black,
                               parent=self.estilos["Heading1"])

        parrafo_principal = PS(name="centrar", alignment=TA_LEFT, fontSize=10,
                               leading=8, textColor=black,
                               parent=self.estilos["Heading1"])

        parrafo_secundario = PS(name="centrar", alignment=TA_LEFT, fontSize=10,
                                leading=16, textColor=black)

        estilo_tabla_datos = (("BACKGROUND", (0, 0), (-1, 0), cornflowerblue),
                              ("TEXTCOLOR", (0, 0), (-1, 0), whitesmoke),
                              ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                              ("ALIGN", (0, 0), (0, -1), "LEFT"),
                              ("VALIGN", (0, 0), (-1, -1), "MIDDLE", black),  # Texto centrado y alineado a la izquierda
                              ("INNERGRID", (0, 0), (-1, -1), 0.50, black),  # Lineas internas
                              ("BOX", (0, 0), (-1, -1), 0.25, black),  # Linea (Marco) externa
                              )

        estilo_tabla_resultados = (("BACKGROUND", (0, 0), (-1, 0), lightsteelblue),
                                   ("TEXTCOLOR", (0, 0), (-1, 0), black),
                                   ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                                   ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                                   ("ALIGN", (0, 0), (0, -1), "LEFT"),
                                   ("VALIGN", (0, 0), (-1, -1), "MIDDLE", black),
                                   # Texto centrado y alineado a la izquierda
                                   ("INNERGRID", (0, 0), (-1, -1), 0.50, black),  # Lineas internas
                                   ("BOX", (0, 0), (-1, -1), 0.25, black)  # Linea (Marco) externa
                                   )

        tabla_datos = Table((('Fecha', 'Nombre', 'Edad', 'Género', 'Peso [kg]', 'Talla [cm]', 'Ocupación'),
                             (fecha, nombre, edad, genero, peso, talla, ocupacion)), colWidths=(self.ancho - 100) / 7,
                            hAlign="CENTER", style=estilo_tabla_datos)

        historia = [Paragraph("Evaluación Postural", alineacion_titulo), Spacer(1, 4 * mm), tabla_datos,
                    get_image_for_pdf("logo.png", height=100 * mm), PageBreak()]  # https://i.imgur.com/KRPTibG.png

        # PAGINA TABLA EVALUACION ANTERIOR
        if examen_anterior:
            tabla_anterior_parte_1_pdf = Table((('Segmento Corporal', 'Descendido', 'Ángulo'),
                                                ('Hombro', db_anterior[2], db_anterior[3]),
                                                ('Pelvis', db_anterior[4], db_anterior[5]),
                                                ('Rodilla', db_anterior[6], db_anterior[7])),
                                               colWidths=(self.ancho - 100) / 5, hAlign="LEFT",
                                               style=estilo_tabla_resultados)

            tabla_anterior_parte_2_pdf = Table((('Referencia', 'Dirección', 'Distancia'),
                                                ('Frente', db_anterior[8], db_anterior[9]),
                                                ('Hombros', db_anterior[10], db_anterior[11]),
                                                ('Ombligo', db_anterior[12], db_anterior[13]),
                                                ('Pelvis', db_anterior[14], db_anterior[15]),
                                                ('Rodillas', db_anterior[16], db_anterior[17]),
                                                ('Pies', db_anterior[18], db_anterior[19])),
                                               colWidths=(self.ancho - 100) / 5, hAlign="LEFT",
                                               style=estilo_tabla_resultados)

            tabla_anterior_parte_3_pdf = Table((('Segmento Corporal', 'Dirección', 'Ángulo'),
                                                ('Pie Izquierdo', db_anterior[20], db_anterior[21]),
                                                ('Pie Derecho', db_anterior[22], db_anterior[23])),
                                               colWidths=(self.ancho - 100) / 5, hAlign="LEFT",
                                               style=estilo_tabla_resultados)

            historia.append(get_image_for_pdf(img_voluntario + nombre_imagen_anterior + '.jpg', height=100 * mm))
            historia.append(Paragraph("Grados con respecto a la horizontal:", parrafo_principal))
            historia.append(Paragraph("El ángulo ideal debe ser <strong>0°</strong>.", parrafo_secundario))
            historia.append(tabla_anterior_parte_1_pdf)
            historia.append(Paragraph("Distancia con respecto a la vertical:", parrafo_principal))
            historia.append(Paragraph("La distancia ideal debe ser <strong>0 cm</strong>.", parrafo_secundario))
            historia.append(tabla_anterior_parte_2_pdf)
            historia.append(Paragraph("Grados de rotación de los pies:", parrafo_principal))
            historia.append(Paragraph("El ángulo ideal debe ser <strong>0°</strong>.", parrafo_secundario))
            historia.append(tabla_anterior_parte_3_pdf)
            historia.append(PageBreak())

        # PAGINA TABLA EVALUACION POSTERIOR
        if examen_posterior:
            tabla_posterior_parte_1_pdf = Table((('Segmento Corporal', 'Descendido', 'Ángulo'),
                                                 ('Hombro', db_posterior[2], db_posterior[3]),
                                                 ('Pelvis', db_posterior[4], db_posterior[5]),
                                                 ('Rodilla', db_posterior[6], db_posterior[7])),
                                                colWidths=(self.ancho - 100) / 5, hAlign="LEFT",
                                                style=estilo_tabla_resultados)

            tabla_posterior_parte_2_pdf = Table((('Referencia', 'Dirección', 'Distancia'),
                                                 ('Hombros', db_posterior[8], db_posterior[9]),
                                                 ('7ma Cervical', db_posterior[10], db_posterior[11]),
                                                 ('5ta Torácica', db_posterior[12], db_posterior[13]),
                                                 ('Pelvis', db_posterior[14], db_posterior[15]),
                                                 ('Rodillas', db_posterior[16], db_posterior[17]),
                                                 ('Tobillos', db_posterior[18], db_posterior[19])),
                                                colWidths=(self.ancho - 100) / 5, hAlign="LEFT",
                                                style=estilo_tabla_resultados)

            tabla_posterior_parte_3_pdf = Table((('Segmento Corporal', 'Dirección', 'Ángulo'),
                                                 ('Pie Izquierdo', db_posterior[20], db_posterior[21]),
                                                 ('Pie Derecho', db_posterior[22], db_posterior[23])),
                                                colWidths=(self.ancho - 100) / 5, hAlign="LEFT",
                                                style=estilo_tabla_resultados)

            historia.append(get_image_for_pdf(img_voluntario + nombre_imagen_posterior + '.jpg', height=100 * mm))
            historia.append(Paragraph("Grados con respecto a la horizontal:", parrafo_principal))
            historia.append(Paragraph("El ángulo ideal debe ser <strong>0°</strong>.", parrafo_secundario))
            historia.append(tabla_posterior_parte_1_pdf)
            historia.append(Paragraph("Distancia con respecto a la vertical:", parrafo_principal))
            historia.append(Paragraph("La distancia ideal debe ser <strong>0 cm</strong>.", parrafo_secundario))
            historia.append(tabla_posterior_parte_2_pdf)
            historia.append(Paragraph("Grados de rotación de los pies:", parrafo_principal))
            historia.append(Paragraph("El ángulo ideal debe ser <strong>0°</strong>.", parrafo_secundario))
            historia.append(tabla_posterior_parte_3_pdf)
            historia.append(PageBreak())

        # PAGINA TABLA EVALUACION LATERALD
        if examen_lateral_d:
            tabla_lateral_d_parte_1_pdf = Table((('Segmento Corporal', 'Dirección', 'Ángulo'),
                                                 ('Cabeza-Hombro', db_lateral_d[2], db_lateral_d[3]),
                                                 ('Hombro-Pelvis', db_lateral_d[4], db_lateral_d[5]),
                                                 ('Caderas-Rodillas', db_lateral_d[6], db_lateral_d[7]),
                                                 ('Rodillas-Pies', db_lateral_d[8], db_lateral_d[9])),
                                                colWidths=(self.ancho - 100) / 5, hAlign="LEFT",
                                                style=estilo_tabla_resultados)

            tabla_lateral_d_parte_2_pdf = Table((('Segmento Corporal', 'Dirección', 'Ángulo'),
                                                 ('Pelvis', db_lateral_d[10], db_lateral_d[11])),
                                                colWidths=(self.ancho - 100) / 5, hAlign="LEFT",
                                                style=estilo_tabla_resultados)

            tabla_lateral_d_parte_3_pdf = Table((('Referencia', 'Dirección', 'Distancia'),
                                                 ('Cabeza', db_lateral_d[12], db_lateral_d[13]),
                                                 ('Hombro', db_lateral_d[14], db_lateral_d[15]),
                                                 ('Pelvis', db_lateral_d[16], db_lateral_d[17]),
                                                 ('Cadera', db_lateral_d[18], db_lateral_d[19]),
                                                 ('Rodilla', db_lateral_d[20], db_lateral_d[21])),
                                                colWidths=(self.ancho - 100) / 5, hAlign="LEFT",
                                                style=estilo_tabla_resultados)

            historia.append(get_image_for_pdf(img_voluntario + nombre_imagen_lateral_d + '.jpg', height=100 * mm))
            historia.append(Paragraph("Grados con respecto a la vertical:", parrafo_principal))
            historia.append(Paragraph("El ángulo ideal debe ser <strong>0°</strong>.", parrafo_secundario))
            historia.append(tabla_lateral_d_parte_1_pdf)
            historia.append(Paragraph("Grados con respecto a la horizontal:", parrafo_principal))
            historia.append(Paragraph("El ángulo normal entre los marcadores pélvicos anterior y posterior <strong>10°"
                                      "</strong>", parrafo_secundario))
            historia.append(Paragraph("con una tolerancia de <strong>±5°</strong>.", parrafo_secundario))
            historia.append(tabla_lateral_d_parte_2_pdf)
            historia.append(Paragraph("Distancia con respecto a la vertical:", parrafo_principal))
            historia.append(Paragraph("La distancia ideal debe ser <strong>0 cm</strong>.", parrafo_secundario))
            historia.append(tabla_lateral_d_parte_3_pdf)
            historia.append(PageBreak())

        archivo_pdf = SimpleDocTemplate(self.nombre_pdf, leftMargin=50, rightMargin=50, pagesize=letter,
                                        title="Reporte PDF", author="Youssef Abarca")

        try:
            archivo_pdf.build(historia, onFirstPage=encabezado_pie_pagina,
                              onLaterPages=encabezado_pie_pagina,
                              canvasmaker=NumeracionPaginas)

            # +------------------------------------+
            return "\nReporte generado con éxito."
        # +------------------------------------+
        except PermissionError:
            # +--------------------------------------------+
            return "Error inesperado: Permiso denegado."
        # +--------------------------------------------+


def encabezado_pie_pagina(canvas_encabezado, archivo_pdf):
    """Guarde el estado de nuestro lienzo para que podamos aprovecharlo"""

    canvas_encabezado.saveState()
    estilos = getSampleStyleSheet()

    alineacion = ParagraphStyle(name="alineacion", alignment=TA_RIGHT,
                                parent=estilos["Normal"])

    # Encabezado
    encabezado_nombre = Paragraph(nombre, estilos["Normal"])
    encabezado_nombre.wrap(archivo_pdf.width, archivo_pdf.topMargin)
    encabezado_nombre.drawOn(canvas_encabezado, archivo_pdf.leftMargin, 736)

    fecha_encabezado = utcnow().to("local").format("dddd, DD - MMMM - YYYY", locale="es")
    fecha_reporte = fecha_encabezado.replace("-", "de")

    encabezado_fecha = Paragraph(fecha_reporte, alineacion)
    encabezado_fecha.wrap(archivo_pdf.width, archivo_pdf.topMargin)
    encabezado_fecha.drawOn(canvas_encabezado, archivo_pdf.leftMargin, 736)

    # Pie de página
    pie_pagina = Paragraph("Lectura Automática de Marcadores", estilos["Normal"])
    pie_pagina.wrap(archivo_pdf.width, archivo_pdf.bottomMargin)
    pie_pagina.drawOn(canvas_encabezado, archivo_pdf.leftMargin, 15 * mm + (5 * mm))

    # Suelta el lienzo
    canvas_encabezado.restoreState()


# Cargar imagenes (Funciones temporales)

def cargar_imagen_anterior():
    root = Tk()

    def boton_cargar():
        global foto_anterior
        foto_anterior = filedialog.askopenfilename(title='Abrir',
                                                   initialdir='C:', filetypes=(('Imagenes', '*.jpg'),
                                                                               ('Imagenes', '*.png'),
                                                                               ('Todos los ficheros', '*.*')))
        root.destroy()

    try:
        root.iconbitmap('icon.ico')
    except TclError:
        print('No ico file found')

    root.title('Análisis Postural LAM')

    root.geometry('300x50')
    Label(root, text="Cargue la imagen de la vista anteriror").pack()
    # Enlezamos la función a la acción del botón
    Button(root, text="Cargar imagen", command=boton_cargar).pack()

    root.mainloop()


def cargar_imagen_posterior():
    root = Tk()

    def boton_cargar():
        global foto_posterior
        foto_posterior = filedialog.askopenfilename(title='Abrir',
                                                    initialdir='C:', filetypes=(('Imagenes', '*.jpg'),
                                                                                ('Imagenes', '*.png'),
                                                                                ('Todos los ficheros', '*.*')))
        root.destroy()

    try:
        root.iconbitmap('icon.ico')
    except TclError:
        print('No ico file found')

    root.title('Análisis Postural LAM')

    root.geometry('300x50')
    Label(root, text="Cargue la imagen de la vista posterior").pack()
    # Enlezamos la función a la acción del botón
    Button(root, text="Cargar imagen", command=boton_cargar).pack()

    root.mainloop()


def cargar_imagen_lateral_d():
    root = Tk()

    def boton_cargar():
        global foto_lateral_d
        foto_lateral_d = filedialog.askopenfilename(title='Abrir',
                                                    initialdir='C:', filetypes=(('Imagenes', '*.jpg'),
                                                                                ('Imagenes', '*.png'),
                                                                                ('Todos los ficheros', '*.*')))
        root.destroy()

    try:
        root.iconbitmap('icon.ico')
    except TclError:
        print('No ico file found')

    root.title('Análisis Postural LAM')

    root.geometry('300x50')
    Label(root, text="Cargue la imagen de la vista lateral derecha").pack()
    # Enlezamos la función a la acción del botón
    Button(root, text="Cargar imagen", command=boton_cargar).pack()

    root.mainloop()


# PROGRAMA

year = datetime.now().year
month = datetime.now().month
day = datetime.now().day

fecha_actual = date(year, month, day)
fecha_vencimiento = date(2021, 6, 12)

dias_de_prueba = (fecha_vencimiento - fecha_actual).days

if __name__ == '__main__':
    if (fecha_vencimiento - fecha_actual).days > 0:
        print(f'\nLe quedan {dias_de_prueba} días de prueba')
    else:
        print(f'\nEl tiempo de prueba se ha terminado')

    if fecha_actual < fecha_vencimiento:
        while True:

            # Datos Personales

            fecha = strftime("%d/%m/%Y")

            print("\nDATOS PERSONALES\n")

            nombre = input("Nombre: ")
            nombre = nombre.strip().title()

            try:
                edad = int(input("Edad: "))
                while edad <= 0:
                    print('Ingrese un valor válido > 0')
                    edad = int(input("Edad: "))
            except ValueError:
                print('Error en ingreso de edad')
                edad = None

            genero = input("Género (M/F): ")
            genero = genero.strip().upper()
            if not (genero == 'M' or genero == 'F'):
                print('Error al ingresar género')
                genero = None

            try:
                peso = float(input("Peso en Kg: "))
                while peso <= 0:
                    print('Ingrese un valor válido > 0')
                    peso = float(input("Peso en Kg: "))
            except ValueError:
                print('Error en ingreso de peso')
                peso = None

            try:
                talla = float(input("Altura en cm: "))
                while talla <= 0:
                    print('Ingrese un valor válido > 0')
                    talla = float(input("Altura en cm: "))
            except ValueError:
                print('Error en ingreso de altura')
                talla = None

            ocupacion = input("Ocupación: ")
            ocupacion = ocupacion.strip().title()

            print("\nIngrese las tolerancias: \n")
            try:
                angulo_tolerancia = float(input("Tolerancia en grados para los ángulos: "))
                while angulo_tolerancia < 0:
                    print('Ingrese un valor válido > 0')
                    angulo_tolerancia = float(input("Tolerancia en grados para los ángulos: "))
            except ValueError:
                print('Tolerancia de grados inválida, se asigna el valor de 0')
                angulo_tolerancia = 0

            try:
                distancia_tolerancia = float(input("Tolerancia en cm para las distancias: "))
                while distancia_tolerancia < 0:
                    print('Ingrese un valor válido > 0')
                    distancia_tolerancia = float(input("Tolerancia en cm para las distancias: "))
            except ValueError:
                print('Tolerancia de distancias inválida, se asigna el valor de 0')
                distancia_tolerancia = 0

            # Creacion del directorio LAM

            dir_lam = '~\\Documents\\LAM\\'
            dir_voltario = dir_lam + nombre + '\\'
            dir_imagen = dir_voltario + 'Imagenes\\'

            directorio = path.expanduser(dir_lam)
            carpeta_voluntario = path.expanduser(dir_voltario)
            img_voluntario = path.expanduser(dir_imagen)

            dir_db_xlsx = directorio + 'DB_LAM.xlsx'

            if not path.isdir(directorio):
                mkdir(directorio)
                directorio = path.expanduser(dir_lam)

            if not path.isdir(carpeta_voluntario):
                mkdir(carpeta_voluntario)
                carpeta_voluntario = path.expanduser(dir_voltario)

            if not path.isdir(img_voluntario):
                mkdir(img_voluntario)
                img_voluntario = path.expanduser(dir_imagen)

            # Condicion para saber que analisis realizar:

            print("\nEvaluaciones a realizar => 1: Si | 0: NO\n")

            # Datos para la ejecución

            if not input("Vista Anterior 1/0: ").strip() == '0':
                examen_anterior = True
            else:
                examen_anterior = False

            if not input("Vista Posterior 1/0: ").strip() == '0':
                examen_posterior = True
            else:
                examen_posterior = False

            if not input("Vista Lateral Derecha 1/0: ").strip() == '0':
                examen_lateral_d = True
            else:
                examen_lateral_d = False

            nombre_imagen_anterior = 'Anterior' + '_' + strftime("%Y%m%d") + '_' + strftime("%H%M%S")
            nombre_imagen_posterior = 'Posterior' + '_' + strftime("%Y%m%d") + '_' + strftime("%H%M%S")
            nombre_imagen_lateral_d = 'LateralD' + '_' + strftime("%Y%m%d") + '_' + strftime("%H%M%S")

            foto_anterior = ''
            foto_posterior = ''
            foto_lateral_d = ''

            resultados_anterior = 0
            resultados_posterior = 0
            resultados_lateral_d = 0

            # Pruaba de cargado de imagenes en caso de imagenes erroneas

            if examen_anterior:
                cargar_imagen_anterior()
                resultados_anterior = evaluacion_anterior(foto_anterior)

                while resultados_anterior == 0:

                    recargar_imagen = bool(int(input("Imagen Anterior con Error. ¿Desea cargar otra imagen? 1/0: ")))

                    if recargar_imagen:
                        cargar_imagen_anterior()
                        resultados_anterior = evaluacion_anterior(foto_anterior)  # https://i.imgur.com/qRb4dv6.jpg

                    else:
                        examen_anterior = False
                        break

            if examen_posterior:
                cargar_imagen_posterior()
                resultados_posterior = evaluacion_posterior(foto_posterior)  # https://i.imgur.com/xIYYjkc.jpg

                while resultados_posterior == 0:

                    recargar_imagen = bool(int(input("Imagen Posterior con Error. ¿Desea cargar otra imagen? 1/0: ")))

                    if recargar_imagen:
                        cargar_imagen_posterior()
                        resultados_posterior = evaluacion_posterior(foto_posterior)  # https://i.imgur.com/xIYYjkc.jpg

                    else:
                        examen_posterior = False
                        break

            if examen_lateral_d:
                cargar_imagen_lateral_d()
                resultados_lateral_d = evaluacion_lateral_d(foto_lateral_d)  # https://i.imgur.com/2fvjwk1.jpg

                while resultados_lateral_d == 0:

                    recargar_imagen = bool(
                        int(input("Imagen Lateral Derecha con Error. ¿Desea cargar otra imagen? 1/0: ")))

                    if recargar_imagen:
                        cargar_imagen_lateral_d()
                        resultados_lateral_d = evaluacion_lateral_d(foto_lateral_d)  # https://i.imgur.com/2fvjwk1.jpg

                    else:
                        examen_lateral_d = False
                        break

            ###############################
            encabezado_anterior = []
            encabezado_posterior = []
            encabezado_lateral_d = []

            data_tabla_anterior = []
            data_tabla_posterior = []
            data_tabla_lateral_d = []

            direccion_imagen_anterior = []
            direccion_imagen_posterior = []
            direccion_imagen_lateral_d = []

            if examen_anterior:
                data_tabla_anterior = DataFrame(resultados_anterior)
                # print(dataTablaAnterior.T)

                direccion_imagen_anterior = '=HYPERLINK(\"{0}{1}.jpg\",\"{2}\")'.format(img_voluntario,
                                                                                        nombre_imagen_anterior,
                                                                                        nombre_imagen_anterior)
                encabezado_anterior = DataFrame((), ('Fecha', 'Nombre', 'Edad', 'Género', 'Peso[kg]', 'Talla[cm]',
                                                     'Ocupación',
                                                     'Ángulo de tolerancia', 'Distancia de tolerancia',
                                                     'Hombro Descendido', 'Ángulo del hombro',
                                                     'Pelvis Descendida', 'Ángulo de la Pelvis',
                                                     'Rodilla Descendida', 'Ángulo de Rodilla',
                                                     'Dirección de la Frente', 'Distancia de la Frente',
                                                     'Dirección de los Hombros', 'Distancia de los Hombros',
                                                     'Dirección del Ombligo', 'Distancia del Ombligo',
                                                     'Dirección de la Pelvis', 'Distancia de la Pelvis',
                                                     'Dirección de las Rodillas', 'Distancia de las Rodillas',
                                                     'Dirección de los Pies', 'Distancia de los Pies',
                                                     'Rotación Pie Izquierdo', 'Ángulo Pie Izquierdo',
                                                     'Rotación Pie Derecho', 'Ángulo Pie Derecho',
                                                     'Dirección Imagen',
                                                     'Dirección del Reporte'))

            if examen_posterior:
                data_tabla_posterior = DataFrame(resultados_posterior)
                # print(dataTablaPosterior.T)

                direccion_imagen_posterior = '=HYPERLINK(\"{0}{1}.jpg\",\"{2}\")'.format(img_voluntario,
                                                                                         nombre_imagen_posterior,
                                                                                         nombre_imagen_posterior)

                encabezado_posterior = DataFrame((), ('Fecha', 'Nombre', 'Edad', 'Género', 'Peso[kg]', 'Talla[cm]',
                                                      'Ocupación',
                                                      'Ángulo de tolerancia', 'Distancia de tolerancia',
                                                      'Hombro Descendido', 'Ángulo del hombro',
                                                      'Pelvis Descendida', 'Ángulo de la Pelvis',
                                                      'Rodilla Descendida', 'Ángulo de Rodilla',
                                                      'Dirección de la Hombros', 'Distancia de la Hombros',
                                                      'Dirección de los 7ma Cervical',
                                                      'Distancia de los 7ma Cervical',
                                                      'Dirección del 5ta Torácica', 'Distancia del 5ta Torácica',
                                                      'Dirección de la Pelvis', 'Distancia de la Pelvis',
                                                      'Dirección de las Rodillas', 'Distancia de las Rodillas',
                                                      'Dirección de los Tobillos', 'Distancia de los Tobillos',
                                                      'Dirección Pie Izquierdo', 'Ángulo Pie Izquierdo',
                                                      'Dirección Pie Derecho', 'Ángulo Pie Derecho',
                                                      'Dirección Imagen',
                                                      'Dirección del Reporte'))

            if examen_lateral_d:
                data_tabla_lateral_d = DataFrame(resultados_lateral_d)
                # print(dataTablaLateralD.T)

                direccion_imagen_lateral_d = '=HYPERLINK(\"{0}{1}.jpg\",\"{2}\")'.format(img_voluntario,
                                                                                         nombre_imagen_lateral_d,
                                                                                         nombre_imagen_lateral_d)

                encabezado_lateral_d = DataFrame((), ('Fecha', 'Nombre', 'Edad', 'Género', 'Peso[kg]', 'Talla[cm]',
                                                      'Ocupación',
                                                      'Ángulo de tolerancia', 'Distancia de tolerancia',
                                                      'Dirección Cabeza-Hombro', 'Ángulo Cabeza-Hombro',
                                                      'Dirección Hombro-Pelvis', 'Ángulo Hombro-Pelvis',
                                                      'Dirección Caderas-Rodillas', 'Ángulo Caderas-Rodillas',
                                                      'Dirección Rodillas-Pies', 'Ángulo Rodillas-Pies',
                                                      'Dirección Pelvis', 'Ángulo Pelvis',
                                                      'Dirección de la Cabeza', 'Distancia de la Cabeza',
                                                      'Dirección del Hombro', 'Distancia del Hombro',
                                                      'Dirección de la Pelvis', 'Distancia de la Pelvis',
                                                      'Dirección de la Cadera', 'Distancia de la Cadera',
                                                      'Dirección de la Rodilla', 'Distancia de la Rodilla',
                                                      'Dirección Imagen',
                                                      'Dirección del Reporte'))

            nombre_pdf = generar_reporte(resultados_anterior, resultados_posterior, resultados_lateral_d)

            direccion_reporte = '=HYPERLINK(\"{0}{1}.pdf\",\"{2}\")'.format(carpeta_voluntario, nombre_pdf,
                                                                            nombre_pdf)

            encabezado_datos = DataFrame([fecha, nombre, edad, genero, peso, talla, ocupacion])

            if not path.exists(dir_db_xlsx):
                book = ExcelWriter(dir_db_xlsx)
                DataFrame().to_excel(book, 'Anterior')
                DataFrame().to_excel(book, 'Posterior')
                DataFrame().to_excel(book, 'LateralD')
                book.save()

            book = load_workbook(dir_db_xlsx)
            sleep(0.2)

            num_celdas_anterior = len(read_excel(dir_db_xlsx, sheet_name=0))
            num_celdas_posterior = len(read_excel(dir_db_xlsx, sheet_name=1))
            num_celdas_lateral_d = len(read_excel(dir_db_xlsx, sheet_name=2))

            with ExcelWriter(dir_db_xlsx, engine='openpyxl') as writer:
                writer.book = book
                writer.sheets = dict((ws.title, ws) for ws in book.worksheets)

                if examen_anterior:
                    encabezado_anterior.T.to_excel(writer, 'Anterior',
                                                   header=True, index=False, startrow=0, startcol=0)
                    encabezado_datos.T.to_excel(writer, 'Anterior',
                                                header=False, index=False, startrow=num_celdas_anterior + 1, startcol=0)
                    data_tabla_anterior.T.to_excel(writer, 'Anterior',
                                                   header=False, index=False, startrow=num_celdas_anterior + 1,
                                                   startcol=7)
                    DataFrame({'link': [direccion_imagen_anterior]}).T.to_excel(writer, 'Anterior',
                                                                                header=False, index=False,
                                                                                startrow=num_celdas_anterior + 1,
                                                                                startcol=31)
                    DataFrame({'link': [direccion_reporte]}).T.to_excel(writer, 'Anterior',
                                                                        header=False, index=False,
                                                                        startrow=num_celdas_anterior + 1,
                                                                        startcol=32)
                    sleep(0.2)

                if examen_posterior:
                    encabezado_posterior.T.to_excel(writer, 'Posterior',
                                                    header=True, index=False, startrow=0, startcol=0)
                    encabezado_datos.T.to_excel(writer, 'Posterior',
                                                header=False, index=False, startrow=num_celdas_posterior + 1,
                                                startcol=0)
                    data_tabla_posterior.T.to_excel(writer, 'Posterior',
                                                    header=False, index=False, startrow=num_celdas_posterior + 1,
                                                    startcol=7)
                    DataFrame({'link': [direccion_imagen_posterior]}).T.to_excel(writer, 'Posterior',
                                                                                 header=False, index=False,
                                                                                 startrow=num_celdas_posterior + 1,
                                                                                 startcol=31)
                    DataFrame({'link': [direccion_reporte]}).T.to_excel(writer, 'Posterior',
                                                                        header=False, index=False,
                                                                        startrow=num_celdas_posterior + 1,
                                                                        startcol=32)
                    sleep(0.2)

                if examen_lateral_d:
                    encabezado_lateral_d.T.to_excel(writer, 'LateralD',
                                                    header=True, index=False, startrow=0, startcol=0)
                    encabezado_datos.T.to_excel(writer, 'LateralD',
                                                header=False, index=False, startrow=num_celdas_lateral_d + 1,
                                                startcol=0)
                    data_tabla_lateral_d.T.to_excel(writer, 'LateralD',
                                                    header=False, index=False, startrow=num_celdas_lateral_d + 1,
                                                    startcol=7)
                    DataFrame({'link': [direccion_imagen_lateral_d]}).T.to_excel(writer, 'LateralD',
                                                                                 header=False, index=False,
                                                                                 startrow=num_celdas_lateral_d + 1,
                                                                                 startcol=29)
                    DataFrame({'link': [direccion_reporte]}).T.to_excel(writer, 'LateralD',
                                                                        header=False, index=False,
                                                                        startrow=num_celdas_lateral_d + 1,
                                                                        startcol=30)

                    sleep(0.2)

                writer.save()
                print('Datos agregados con éxito\n')

            open_new(carpeta_voluntario + nombre_pdf + '.pdf')

            salir = bool(int(input('Desea salir? 1: Si | 0: NO => ')))

            if salir:
                break
            system("cls")
    else:
        print(f'El tiempo finalizó el {fecha_vencimiento}')
        input()

# Para crear ejecutable: pyinstaller --onefile --icon=icon.ico sistema_LAM.py
# Nota: Primero se debe agregar el hook faltande (hook-skimage.filters.py) en la libreria \PyInstaller\hooks\
