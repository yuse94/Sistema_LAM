"""
LAM está en construcción
Versión Consola de python3 0.1
"""

import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

from skimage import (io, filters,
                     morphology, transform, img_as_ubyte)
from skimage.color import rgb2gray
from skimage.measure import label, regionprops
from openpyxl import load_workbook

###############################
from tkinter import *
from tkinter import filedialog
##############################

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import datetime
import os
import time

from reportlab.platypus import PageBreak
from reportlab.platypus import Image
from arrow import utcnow
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.pagesizes import letter
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.lib.colors import black, whitesmoke, cornflowerblue, lightsteelblue
from reportlab.pdfgen import canvas
from reportlab.lib import utils

######## FUNCIONES ##########
def escalarImagen(imagen):
    """
    :param imagen:
    :return img_as_ubyte(imagen):
    """
    if (len(imagen[1]) > 1000 or len(imagen) > 2000):   #Tamaño maximo en X, Y
        imagen = transform.rescale(imagen, 4.0 / 5.0, multichannel=True)
        imagen = escalarImagen(imagen)
    return img_as_ubyte(imagen)

def filtroColorVerde(imagen):
    """
    :param imagen:
    :return imagenFiltrada:
    """

    canalVerde = rgb2gray(imagen[:, :, 1]) / 255.0
    imagenGris = rgb2gray(imagen)

    imagenSoloVerde = np.zeros((len(canalVerde), len(canalVerde[1, :])))

    for i in range(0, len(canalVerde)):
        for j in range(0, len(canalVerde[1, :])):
            imagenSoloVerde[i][j] = canalVerde[i][j] - imagenGris[i][j]
            if imagenSoloVerde[i][j] < 0:
                imagenSoloVerde[i][j] = 0

    if (np.max(imagenSoloVerde)<=1):
            imagenSoloVerde = filters.median(imagenSoloVerde)*255
    else:
            imagenSoloVerde = filters.median(imagenSoloVerde)

    umbralColorVerde = round(np.max(imagenSoloVerde) * 0.32)
    imagenBinariaVerde = imagenSoloVerde > umbralColorVerde
    imagenFiltrada = morphology.remove_small_holes(imagenBinariaVerde)

    return imagenFiltrada

def ajustarImagen(imagen):
    """
    :param imagen:
    :return imagenAjustada:
    """
    imagenFiltrada = filtroColorVerde(imagen)
    referencia1 = etiquetas(imagenFiltrada).referenciaUno
    referencia2 = etiquetas(imagenFiltrada).referenciaDos

    coordenadasReferencia = referencia2 - referencia1
    anguloDeRotacionImagen = np.arctan(coordenadasReferencia[0] / coordenadasReferencia[1])
    imagenRotada = transform.rotate(imagen, anguloDeRotacionImagen * 180 / np.pi)

    etiquetasDeReferencia = [referencia1[1], referencia2[1]]
    etiquetasDeReferencia.sort()

    espacioRecorteImagen = abs(referencia1[1] - referencia2[1]) / 10
    imagenAjustada = imagenRotada[:, int(round(etiquetasDeReferencia[0] - espacioRecorteImagen))
                         : int(round(etiquetasDeReferencia[1] + espacioRecorteImagen))]
    imagenAjustada = img_as_ubyte(imagenAjustada)

    return imagenAjustada

def cuadricula(centroX, centroY, tamanioX, tamanioY, tamanioDivisiones):
    """
    :param centroX:
    :param centroY:
    :param tamanioX:
    :param tamanioY:
    :param tamanioDivisiones:
    :return X, Y, xHorizontal, yHorizontal, xVertical, yVertical:
    """
    x1 = np.arange(centroX, tamanioX, tamanioDivisiones)
    y1 = np.arange(centroY, tamanioY, tamanioDivisiones)
    [X1, Y1] = np.meshgrid(x1, y1)

    x2 = np.arange(centroX, 0, -tamanioDivisiones)
    y2 = np.arange(centroY, 0, -tamanioDivisiones)
    [X2, Y2] = np.meshgrid(x2, y2)

    x3 = np.arange(centroX, tamanioX, tamanioDivisiones)
    y3 = np.arange(centroY, 0, -tamanioDivisiones)
    [X3, Y3] = np.meshgrid(x3, y3)

    x4 = np.arange(centroX, 0, -tamanioDivisiones)
    y4 = np.arange(centroY, tamanioY, tamanioDivisiones)
    [X4, Y4] = np.meshgrid(x4, y4)

    [X, Y] = np.meshgrid(np.hstack((x1, x2, x3, x4)),
                         np.hstack((y1, y2, y3, y4)))

    xHorizontal = np.hstack([X1[0, :], X2[0, :], X3[0, :], X4[0, :]])
    yHorizontal = np.hstack([Y1[0, :], Y2[0, :], Y3[0, :], Y4[0, :]])

    xVertical = np.hstack((X1[:, 0], X2[:, 0], X3[:, 0], X4[:, 0]))
    yVertical = np.hstack((Y1[:, 0], Y2[:, 0], Y3[:, 0], Y4[:, 0]))

    return X, Y, xHorizontal, yHorizontal, xVertical, yVertical

def get_image(path, height=1*mm):
    """
    Obtener la imagen con una altura determinada
    :param path:
    :param height:
    :return Image(path, height=height, width=(height * aspect)):
    """
    img = utils.ImageReader(path)
    iw, ih = img.getSize()
    aspect = iw / float(ih)
    return Image(path, height=height, width=(height * aspect))

# Funciones de la vista Anterior

def tablaAnteriorParteUno(puntoAnatomicoUno, puntoAnatomicoDos):
    """
    :param puntoAnatomicoUno:
    :param puntoAnatomicoDos:
    :return descendido, angulo:

    |||||||||||||||||||||||||||||||||||||||||||||||
    || Segmento Corporal || Descendido || Angulo ||
    |||||||||||||||||||||||||||||||||||||||||||||||
    || Hombros           || xxx        || xx °   ||
    || Pelvis            || xxx        || xx °   ||
    || Rodilla           || xxx        || xx °   ||
    |||||||||||||||||||||||||||||||||||||||||||||||
    """

    distancia = puntoAnatomicoDos - puntoAnatomicoUno
    angulo = -np.angle(complex(distancia[1], distancia[0]), deg=True)

    if angulo > anguloTolerancia:
        descendido = 'Der.'
    elif angulo < -anguloTolerancia:
        descendido = 'Izq.'
    else:
        descendido = 'Alin.'

    angulo = round(angulo, 4) # Número de cifras significativas

    return descendido, angulo

def tablaAnteriorParteDos(puntoAnatomicoUno, puntoAnatomicoDos, escala):
    """
    :param puntoAnatomicoUno:
    :param puntoAnatomicoDos:
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

    distancia = (puntoAnatomicoUno[1] - puntoAnatomicoDos[1]) * escala

    if distancia > distanciaTolerancia:
        direccion = 'Der.'
    elif distancia < -distanciaTolerancia:
        direccion = 'Izq.'
    else:
        direccion = 'Alin.'

    distancia = round(distancia, 4) # Número de cifras significativas

    return direccion, distancia

def tablaAnteriorParteTres(puntoAnatomicoUno, puntoAnatomicoDos):
    """

    :param puntoAnatomicoUno:
    :param puntoAnatomicoDos:
    :return direccion, angulo:

    ||||||||||||||||||||||||||||||||||||||||||||||
    || Segmento Corporal || Direccion || Angulo ||
    ||||||||||||||||||||||||||||||||||||||||||||||
    || Pie Izquierdo     || xxx       || xx °   ||
    || Pie Derecho       || xxx       || xx °   ||
    ||||||||||||||||||||||||||||||||||||||||||||||
    """

    distancia = puntoAnatomicoUno - puntoAnatomicoDos
    angulo = abs(np.angle(complex(distancia[1], distancia[0]), deg=True)) - 90

    if angulo > anguloTolerancia:
        direccion = 'Rot.Ext.'
    elif angulo < -anguloTolerancia:
        direccion = 'Rot.Int.'
    else:
        direccion = 'Alin.'

    angulo = round((angulo), 4)

    return direccion, angulo

# Funciones de la vista Posterior

def tablaPosteriorParteUno(puntoAnatomicoUno, puntoAnatomicoDos):
    """
    :param puntoAnatomicoUno:
    :param puntoAnatomicoDos:
    :return descendido, angulo:

    |||||||||||||||||||||||||||||||||||||||||||||||
    || Segmento Corporal || Descendido || Angulo ||
    |||||||||||||||||||||||||||||||||||||||||||||||
    || Hombros           || xxx        || xx °   ||
    || Pelvis            || xxx        || xx °   ||
    || Rodilla           || xxx        || xx °   ||
    |||||||||||||||||||||||||||||||||||||||||||||||
    """

    distancia = puntoAnatomicoDos - puntoAnatomicoUno
    angulo = np.angle(complex(distancia[1], distancia[0]), deg=True)

    if angulo > anguloTolerancia:
        descendido = 'Der.'
    elif angulo < -anguloTolerancia:
        descendido = 'Izq.'
    else:
        descendido = 'Alin.'

    angulo = round(angulo, 4) # Número de cifras significativas

    return descendido, angulo

def tablaPosteriorParteDos(puntoAnatomicoUno, puntoAnatomicoDos, escala):
    """
    :param puntoAnatomicoUno:
    :param puntoAnatomicoDos:
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

    distancia = (puntoAnatomicoDos[1] - puntoAnatomicoUno[1]) * escala

    if distancia > distanciaTolerancia:
        direccion = 'Der.'
    elif distancia < -distanciaTolerancia:
        direccion = 'Izq.'
    else:
        direccion = 'Alin.'

    distancia = round(distancia, 4) # Número de cifras significativas

    return direccion, distancia

def tablaPosteriorParteTres(puntoAnatomicoUno, puntoAnatomicoDos):
    """

    :param puntoAnatomicoUno:
    :param puntoAnatomicoDos:
    :return direccion, angulo:

    ||||||||||||||||||||||||||||||||||||||||||||||
    || Segmento Corporal || Direccion || Angulo ||
    ||||||||||||||||||||||||||||||||||||||||||||||
    || Pie Izquierdo     || xxx       || xx °   ||
    || Pie Derecho       || xxx       || xx °   ||
    ||||||||||||||||||||||||||||||||||||||||||||||
    """

    distancia = puntoAnatomicoUno - puntoAnatomicoDos
    angulo = 90 - abs(np.angle(complex(distancia[1], distancia[0]), deg=True))

    if angulo > anguloTolerancia:
        direccion = 'Valgo'
    elif angulo < -anguloTolerancia:
        direccion = 'Varo'
    else:
        direccion = 'Alin.'

    angulo = round((angulo), 4)

    return direccion, angulo

# Funciones de la vista Lateral Derecha

def tablaLateralDParteUno(puntoAnatomicoUno, puntoAnatomicoDos):
    """

    :param puntoAnatomicoUno:
    :param puntoAnatomicoDos:
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

    distancia = puntoAnatomicoUno - puntoAnatomicoDos
    angulo = 90 - abs(np.angle(complex(distancia[1], distancia[0]), deg=True))

    if angulo < -anguloTolerancia:
        direccion = 'Pos.'
    elif angulo > anguloTolerancia:
        direccion = 'Ant.'
    else:
        direccion = 'Alin.'

    angulo = round((angulo), 4)

    return direccion, angulo

def tablaLateralDParteDos(puntoAnatomicoUno, puntoAnatomicoDos):
    """

    :param puntoAnatomicoUno:
    :param puntoAnatomicoDos:
    :return direccion, angulo:

    ||||||||||||||||||||||||||||||||||||||||||||||
    || Segmento Corporal || Direccion || Angulo ||
    ||||||||||||||||||||||||||||||||||||||||||||||
    || Pelvis            || xxx       || xx °   ||
    ||||||||||||||||||||||||||||||||||||||||||||||
    """

    distancia = puntoAnatomicoUno - puntoAnatomicoDos
    angulo = 180 - abs(np.angle(complex(distancia[1], distancia[0]), deg=True))

    if angulo > 15:
        direccion = 'Ant.'
    elif angulo < 5:
        direccion = 'Pos.'
    else:
        direccion = 'Normal'

    angulo = round((angulo), 4)

    return direccion, angulo

def tablaLateralDParteTres(puntoAnatomicoUno, puntoAnatomicoDos, escala):
    """
    :param puntoAnatomicoUno:
    :param puntoAnatomicoDos:
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

    distancia = (puntoAnatomicoDos[1] - puntoAnatomicoUno[1]) * escala

    if distancia > distanciaTolerancia:
        direccion = 'Ant.'
    elif distancia < -distanciaTolerancia:
        direccion = 'Pos.'
    else:
        direccion = 'Alin.'

    distancia = round(distancia, 4) # Número de cifras significativas

    return direccion, distancia

###### Clase de segmentación ############

class etiquetas():
    """
    Realiza la segmentacion de las etiquetas ayuda a indentificar:
    self.referenciaUno => Punto de refercia uno
    self.referenciaDos => Punto de refercia dos
    self.centrosCoordenadaY; self.centrosCoordenadaX => Devuelte las cordenadas
    ordenadas de arriba a abajo conforme aparecen
    self.razonDeEscala => Escala segun los puntos de referencia para obtener valores en cm
    """
    def __init__(self, imagen):
        etiquetas = label(imagen)
        regiones = regionprops(etiquetas)
        centrosCoordenadaY = []
        centrosCoordenadasX = []
        for i in range(0, len(regiones)):
            y, x = regiones[i].centroid
            centrosCoordenadaY.append(y)
            centrosCoordenadasX.append(x)

        posicionCoordenada = [i for i, x in enumerate(centrosCoordenadasX) if x == min(centrosCoordenadasX)]
        referenciaUno = [centrosCoordenadaY[posicionCoordenada[0]], centrosCoordenadasX[posicionCoordenada[0]]]
        centrosCoordenadaY.pop(posicionCoordenada[0])
        centrosCoordenadasX.pop(posicionCoordenada[0])

        posicionCoordenada = [i for i, x in enumerate(centrosCoordenadasX) if x == max(centrosCoordenadasX)]
        referenciaDos = [centrosCoordenadaY[posicionCoordenada[0]], centrosCoordenadasX[posicionCoordenada[0]]]
        centrosCoordenadaY.pop(posicionCoordenada[0])
        centrosCoordenadasX.pop(posicionCoordenada[0])

        etiquetasDeReferencia = [referenciaUno, referenciaDos]

        if etiquetasDeReferencia[0][0] == etiquetasDeReferencia[1][0]:
            referenciaUno = etiquetasDeReferencia[0]
            referenciaDos = etiquetasDeReferencia[1]
        else:
            referenciaCoordenadaY = [etiquetasDeReferencia[0][0], etiquetasDeReferencia[1][0]]
            posicionCoordenada = [i for i, x in enumerate(referenciaCoordenadaY) if x == min(referenciaCoordenadaY)]
            referenciaUno = etiquetasDeReferencia[posicionCoordenada[0]]
            posicionCoordenada = [i for i, x in enumerate(referenciaCoordenadaY) if x == max(referenciaCoordenadaY)]
            referenciaDos = etiquetasDeReferencia[posicionCoordenada[0]]

        etiquetasDeReferencia = [referenciaUno[1], referenciaDos[1]]
        etiquetasDeReferencia.sort()

        self.referenciaUno = np.array(referenciaUno)
        self.referenciaDos = np.array(referenciaDos)
        self.centrosCoordenadaY = np.array(centrosCoordenadaY)
        self.centrosCoordenadaX = np.array(centrosCoordenadasX)
        self.razonDeEscala = 100.0 / np.sqrt((etiquetasDeReferencia[0] ** 2 + etiquetasDeReferencia[1] ** 2))

############# REPORTE PDF ###################3

def generarReporte(datosAnterior, datosPosterior, datosLateralD):
    """
    Genera el reporte PDF con su respectivo nombre
    """
    nombrePDF = nombre + '_' + time.strftime("%Y%m%d")+'_'+time.strftime("%H%M%S")
    reporte = reportePDF(carpetaVoluntario + nombrePDF + '.pdf').Exportar(datosAnterior, datosPosterior, datosLateralD)
    print(reporte)
    return nombrePDF

class numeracionPaginas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        canvas.Canvas.__init__(self, *args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        """Agregar información de la página a cada página (página x de y)"""
        numeroPaginas = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(numeroPaginas)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_number(self, conteoPaginas):
        self.drawRightString(204 * mm, 15 * mm + (5 * mm),
                             "Página {} de {}".format(self._pageNumber, conteoPaginas))

    # ===================== FUNCIÓN generarReporte =====================

# Funciones de evaluacion

def evaluacionAnterior(fotoAnterior):
    imagen = io.imread(fotoAnterior)
    imagen = escalarImagen(imagen)
    #io.imshow(imagen)
    #plt.close()            # Para mostrar la imagen cambiar "close" por "show"
    imagenAnterior = ajustarImagen(imagen)

    imagenAnteriorFiltrada = filtroColorVerde(imagenAnterior)
    referenciaUno = etiquetas(imagenAnteriorFiltrada).referenciaUno
    referenciaDos = etiquetas(imagenAnteriorFiltrada).referenciaDos
    centrosCoordenadaY = etiquetas(imagenAnteriorFiltrada).centrosCoordenadaY
    centrosCoordenadaX = etiquetas(imagenAnteriorFiltrada).centrosCoordenadaX
    razonDeEscala = etiquetas(imagenAnteriorFiltrada).razonDeEscala

    '''
    PUTNOS ANATOMICOS
    F1 = Entrecejo
    F2 = Mentón
    F3 = Hombro derecho
    F4 = Hombro izquierdo
    F5 = Esternón
    F6 = Ombligo
    F7 = Perlvis derecha
    F8 = Perlvis izquierda
    F9 = Rodilla derecho
    F10= Rodilla izquierda
    F11= Tobillo derecho
    F12= Tobillo izquierdo
    F13= Dedo gordo derecho
    F14= Dedo gordo izquierdo
    FcH= Centro hombros
    FcY= Centro en Y (Pelvis)
    FcR= Centro rodillas
    FcX= Centro en X (Tobillos)
    FcP= Centro en dedos pies
    '''

    if (len(centrosCoordenadaX) > 14):
        print("Existen demasiados puntos en la imagen")
        plt.figure(1)
        plt.title('Vista Anterior: {0}/{1}'.format(len(centrosCoordenadaX), 14))
        plt.plot(centrosCoordenadaX, centrosCoordenadaY, 'b*', markersize="5")
        io.imshow(imagenAnterior)
        plt.show()

    elif (len(centrosCoordenadaX) < 14):
        print("Existen menos puntos en la imagen")
        plt.figure(1)
        plt.title('Vista Anterior: {0}/{1}'.format(len(centrosCoordenadaX), 14))
        plt.plot(centrosCoordenadaX, centrosCoordenadaY, 'b*', markersize="5")
        io.imshow(imagenAnterior)
        plt.show()

    else:

        F1 = (centrosCoordenadaY[0], centrosCoordenadaX[0])
        F2 = (centrosCoordenadaY[1], centrosCoordenadaX[1])

        coordenadaTempY = [centrosCoordenadaY[2], centrosCoordenadaY[3], centrosCoordenadaY[4]]
        coordenadaTempX = [centrosCoordenadaX[2], centrosCoordenadaX[3], centrosCoordenadaX[4]]
        posicion = [i for i, x in enumerate(coordenadaTempX) if x == min(coordenadaTempX)]
        F3 = coordenadaTempY[posicion[0]], coordenadaTempX[posicion[0]]
        coordenadaTempY.pop(posicion[0])
        coordenadaTempX.pop(posicion[0])
        posicion = [i for i, x in enumerate(coordenadaTempX) if x == max(coordenadaTempX)]
        F4 = coordenadaTempY[posicion[0]], coordenadaTempX[posicion[0]]
        coordenadaTempY.pop(posicion[0])
        coordenadaTempX.pop(posicion[0])
        F5 = coordenadaTempY[0], coordenadaTempX[0]

        coordenadaTempY = [centrosCoordenadaY[5], centrosCoordenadaY[6], centrosCoordenadaY[7]]
        coordenadaTempX = [centrosCoordenadaX[5], centrosCoordenadaX[6], centrosCoordenadaX[7]]
        posicion = [i for i, x in enumerate(coordenadaTempX) if x == min(coordenadaTempX)]
        F7 = coordenadaTempY[posicion[0]], coordenadaTempX[posicion[0]]
        coordenadaTempY.pop(posicion[0])
        coordenadaTempX.pop(posicion[0])
        posicion = [i for i, x in enumerate(coordenadaTempX) if x == max(coordenadaTempX)]
        F8 = coordenadaTempY[posicion[0]], coordenadaTempX[posicion[0]]
        coordenadaTempY.pop(posicion[0])
        coordenadaTempX.pop(posicion[0])
        F6 = coordenadaTempY[0], coordenadaTempX[0]

        coordenadaTempY = [centrosCoordenadaY[8], centrosCoordenadaY[9]]
        coordenadaTempX = [centrosCoordenadaX[8], centrosCoordenadaX[9]]
        posicion = [i for i, x in enumerate(coordenadaTempX) if x == min(coordenadaTempX)]
        F9 = coordenadaTempY[posicion[0]], coordenadaTempX[posicion[0]]
        posicion = [i for i, x in enumerate(coordenadaTempX) if x == max(coordenadaTempX)]
        F10 = coordenadaTempY[posicion[0]], coordenadaTempX[posicion[0]]

        coordenadaTempY = [centrosCoordenadaY[10], centrosCoordenadaY[11]]
        coordenadaTempX = [centrosCoordenadaX[10], centrosCoordenadaX[11]]
        posicion = [i for i, x in enumerate(coordenadaTempX) if x == min(coordenadaTempX)]
        F11 = coordenadaTempY[posicion[0]], coordenadaTempX[posicion[0]]
        posicion = [i for i, x in enumerate(coordenadaTempX) if x == max(coordenadaTempX)]
        F12 = coordenadaTempY[posicion[0]], coordenadaTempX[posicion[0]]

        coordenadaTempY = [centrosCoordenadaY[12], centrosCoordenadaY[13]]
        coordenadaTempX = [centrosCoordenadaX[12], centrosCoordenadaX[13]]
        posicion = [i for i, x in enumerate(coordenadaTempX) if x == min(coordenadaTempX)]
        F13 = coordenadaTempY[posicion[0]], coordenadaTempX[posicion[0]]
        posicion = [i for i, x in enumerate(coordenadaTempX) if x == max(coordenadaTempX)]
        F14 = coordenadaTempY[posicion[0]], coordenadaTempX[posicion[0]]

        FcH = np.mean([F3, F4], axis=0)
        FcY = np.mean([F7, F8], axis=0)
        FcR = np.mean([F9, F10], axis=0)
        FcX = np.mean([F11, F12], axis=0)
        FcP = np.mean([F13, F14], axis=0)

        # F2 y F5 aún sin uso

        F1 = np.array(F1)
        F2 = np.array(F2)
        F3 = np.array(F3)
        F4 = np.array(F4)
        F5 = np.array(F5)
        F6 = np.array(F6)
        F7 = np.array(F7)
        F8 = np.array(F8)
        F9 = np.array(F9)
        F10 = np.array(F10)
        F11 = np.array(F11)
        F12 = np.array(F12)
        F13 = np.array(F13)
        F14 = np.array(F14)

        FcH = np.array(FcH)
        FcY = np.array(FcY)
        FcR = np.array(FcR)
        FcX = np.array(FcX)
        FcP = np.array(FcP)

        plt.figure(1)
        plt.title('Vista Anterior')

        plt.plot(centrosCoordenadaX, centrosCoordenadaY, 'b*', markersize="1")

        plt.plot(FcH[1], FcH[0], 'rx', markersize="3")
        plt.plot(FcY[1], FcY[0], 'rx', markersize="3")
        plt.plot(FcR[1], FcR[0], 'rx', markersize="3")
        plt.plot(FcX[1], FcX[0], 'rx', markersize="3")
        plt.plot(FcP[1], FcP[0], 'rx', markersize="3")

        coordenadasReferencia = referenciaDos - referenciaUno
        tamanioDivisiones = np.sqrt((coordenadasReferencia[0] ** 2 + coordenadasReferencia[1] ** 2)) / 20.0

        centroX = FcX[1]
        centroY = FcY[0]
        tamanioX = len(imagenAnterior[1])
        tamanioY = len(imagenAnterior)

        (xCuadricula, yCuadricula, xHorizontal, yHorizontal, xVertical, yVertical) = cuadricula(centroX, centroY, tamanioX,
                                                                                                tamanioY, tamanioDivisiones)

        plt.plot(xCuadricula, yCuadricula, 'k', xCuadricula.T, yCuadricula.T, 'k', linewidth=0.1)
        plt.plot(xHorizontal, yHorizontal, 'r', linewidth=0.3)
        plt.plot(xVertical, yVertical, 'r', linewidth=0.3)

        io.imshow(imagenAnterior)

        dirImagenAnterior = imgVoluntario + nombreImagenAnterior + '.jpg'
        #time.sleep(1)

        plt.savefig(dirImagenAnterior, dpi=500)
        plt.close()     # Para mostrar la imagen cambiar "close" por "show"

        # TA1
        hombroDescendido, anguloHombro = tablaAnteriorParteUno(F3, F4)
        pelvisDescendida, anguloPelvis = tablaAnteriorParteUno(F7, F8)
        rodillaDescendida, anguloRodilla = tablaAnteriorParteUno(F9, F10)

        # TA2
        direccionFrente, distanciaFrente = tablaAnteriorParteDos(FcX, F1, razonDeEscala)
        direccionHombros, distanciaHombros = tablaAnteriorParteDos(FcX, FcH, razonDeEscala)
        direccionOmbligo, distanciaOmbligo = tablaAnteriorParteDos(FcX, F6, razonDeEscala)
        direccionPelvis, distanciaPelvis = tablaAnteriorParteDos(FcX, FcY, razonDeEscala)
        direccionRodillas, distanciaRodillas = tablaAnteriorParteDos(FcX, FcR, razonDeEscala)
        direccionPies, distanciaPies = tablaAnteriorParteDos(FcX, FcP, razonDeEscala)

        # TA3
        direccionPieIzquierdo, anguloPieIzquierdo = tablaAnteriorParteTres(F12, F14)
        direccionPieDerecho, anguloPieDerecho = tablaAnteriorParteTres(F13, F11)

        datos = [anguloTolerancia, distanciaTolerancia, hombroDescendido, anguloHombro, pelvisDescendida, anguloPelvis,
                 rodillaDescendida, anguloRodilla,direccionFrente, distanciaFrente, direccionHombros, distanciaHombros,
                 direccionOmbligo, distanciaOmbligo, direccionPelvis, distanciaPelvis, direccionRodillas,
                 distanciaRodillas, direccionPies, distanciaPies, direccionPieIzquierdo, anguloPieIzquierdo,
                 direccionPieDerecho, anguloPieDerecho]

        return datos
    return 0

def evaluacionPosterior(fotoPosterior):
    imagen = io.imread(fotoPosterior)
    imagen = escalarImagen(imagen)
    #io.imshow(imagen)
    #plt.close()            # Para mostrar la imagen cambiar "close" por "show"
    imagenPosterior = ajustarImagen(imagen)

    imagenPosteriorFiltrada = filtroColorVerde(imagenPosterior)
    referenciaUno = etiquetas(imagenPosteriorFiltrada).referenciaUno
    referenciaDos = etiquetas(imagenPosteriorFiltrada).referenciaDos
    centrosCoordenadaY = etiquetas(imagenPosteriorFiltrada).centrosCoordenadaY
    centrosCoordenadaX = etiquetas(imagenPosteriorFiltrada).centrosCoordenadaX
    razonDeEscala = etiquetas(imagenPosteriorFiltrada).razonDeEscala

    '''
    PUTNOS ANATOMICOS
    P1 = 7th Cervical
    P2 = 5th Thoracic
    P3 = Hombro derecho
    P4 = Hombro izquierdo
    P5 = Perlvis derecha
    P6 = Perlvis izquierda
    P7 = Rodilla derecho
    P8 = Rodilla izquierda
    P9 = Tobillo derecho
    P10= Tobillo izquierdo
    P11= Planta derecho
    P12= Planta izquierdo
    PcH= Centro hombros
    PcY= Centro en Y (Pelvis)
    PcR= Centro rodillas
    PcT= Centro en tobillos
    PcX= Centro en X (Platas de los pies)
    '''

    if (len(centrosCoordenadaX) > 12):
        print("Existen demasiados puntos en la imagen")
        plt.figure(1)
        plt.title('Vista Posterior: {0}/{1}'.format(len(centrosCoordenadaX), 12))
        plt.plot(centrosCoordenadaX, centrosCoordenadaY, 'b*', markersize="5")
        io.imshow(imagenPosterior)
        plt.show()

    elif (len(centrosCoordenadaX) < 12):
        print("Existen menos puntos en la imagen")
        plt.figure(1)
        plt.title('Vista Posterior: {0}/{1}'.format(len(centrosCoordenadaX), 12))
        plt.plot(centrosCoordenadaX, centrosCoordenadaY, 'b*', markersize="5")
        io.imshow(imagenPosterior)
        plt.show()

    else:

        coordenadaTempY = [centrosCoordenadaY[0], centrosCoordenadaY[1], centrosCoordenadaY[2]]
        coordenadaTempX = [centrosCoordenadaX[0], centrosCoordenadaX[1], centrosCoordenadaX[2]]
        posicion = [i for i, x in enumerate(coordenadaTempX) if x == min(coordenadaTempX)]
        P4 = coordenadaTempY[posicion[0]], coordenadaTempX[posicion[0]]
        coordenadaTempY.pop(posicion[0])
        coordenadaTempX.pop(posicion[0])
        posicion = [i for i, x in enumerate(coordenadaTempX) if x == max(coordenadaTempX)]
        P3 = coordenadaTempY[posicion[0]], coordenadaTempX[posicion[0]]
        coordenadaTempY.pop(posicion[0])
        coordenadaTempX.pop(posicion[0])
        P1 = coordenadaTempY[0], coordenadaTempX[0]

        P2 = (centrosCoordenadaY[3], centrosCoordenadaX[3])

        coordenadaTempY = [centrosCoordenadaY[4], centrosCoordenadaY[5]]
        coordenadaTempX = [centrosCoordenadaX[4], centrosCoordenadaX[5]]
        posicion = [i for i, x in enumerate(coordenadaTempX) if x == min(coordenadaTempX)]
        P6 = coordenadaTempY[posicion[0]], coordenadaTempX[posicion[0]]
        posicion = [i for i, x in enumerate(coordenadaTempX) if x == max(coordenadaTempX)]
        P5 = coordenadaTempY[posicion[0]], coordenadaTempX[posicion[0]]

        coordenadaTempY = [centrosCoordenadaY[6], centrosCoordenadaY[7]]
        coordenadaTempX = [centrosCoordenadaX[6], centrosCoordenadaX[7]]
        posicion = [i for i, x in enumerate(coordenadaTempX) if x == min(coordenadaTempX)]
        P8 = coordenadaTempY[posicion[0]], coordenadaTempX[posicion[0]]
        posicion = [i for i, x in enumerate(coordenadaTempX) if x == max(coordenadaTempX)]
        P7 = coordenadaTempY[posicion[0]], coordenadaTempX[posicion[0]]

        coordenadaTempY = [centrosCoordenadaY[8], centrosCoordenadaY[9]]
        coordenadaTempX = [centrosCoordenadaX[8], centrosCoordenadaX[9]]
        posicion = [i for i, x in enumerate(coordenadaTempX) if x == min(coordenadaTempX)]
        P10 = coordenadaTempY[posicion[0]], coordenadaTempX[posicion[0]]
        posicion = [i for i, x in enumerate(coordenadaTempX) if x == max(coordenadaTempX)]
        P9 = coordenadaTempY[posicion[0]], coordenadaTempX[posicion[0]]

        coordenadaTempY = [centrosCoordenadaY[10], centrosCoordenadaY[11]]
        coordenadaTempX = [centrosCoordenadaX[10], centrosCoordenadaX[11]]
        posicion = [i for i, x in enumerate(coordenadaTempX) if x == min(coordenadaTempX)]
        P12 = coordenadaTempY[posicion[0]], coordenadaTempX[posicion[0]]
        posicion = [i for i, x in enumerate(coordenadaTempX) if x == max(coordenadaTempX)]
        P11 = coordenadaTempY[posicion[0]], coordenadaTempX[posicion[0]]

        PcH = np.mean([P4, P3], axis=0)
        PcY = np.mean([P6, P5], axis=0)
        PcR = np.mean([P8, P7], axis=0)
        PcT = np.mean([P10, P9], axis=0)
        PcX = np.mean([P12, P11], axis=0)

        P1 = np.array(P1)
        P2 = np.array(P2)
        P3 = np.array(P3)
        P4 = np.array(P4)
        P5 = np.array(P5)
        P6 = np.array(P6)
        P7 = np.array(P7)
        P8 = np.array(P8)
        P9 = np.array(P9)
        P10 = np.array(P10)
        P11 = np.array(P11)
        P12 = np.array(P12)

        PcH = np.array(PcH)
        PcY = np.array(PcY)
        PcR = np.array(PcR)
        PcT = np.array(PcT)
        PcX = np.array(PcX)

        plt.figure(1)
        plt.title('Vista Posterior')

        plt.plot(centrosCoordenadaX, centrosCoordenadaY, 'b*', markersize="1")

        plt.plot(PcH[1], PcH[0], 'rx', markersize="3")
        plt.plot(PcY[1], PcY[0], 'rx', markersize="3")
        plt.plot(PcR[1], PcR[0], 'rx', markersize="3")
        plt.plot(PcT[1], PcT[0], 'rx', markersize="3")
        plt.plot(PcX[1], PcX[0], 'rx', markersize="3")

        coordenadasReferencia = referenciaDos - referenciaUno
        tamanioDivisiones = np.sqrt((coordenadasReferencia[0] ** 2 + coordenadasReferencia[1] ** 2)) / 20.0

        centroX = PcX[1]
        centroY = PcY[0]
        tamanioX = len(imagenPosterior[1])
        tamanioY = len(imagenPosterior)

        (xCuadricula, yCuadricula, xHorizontal, yHorizontal, xVertical, yVertical) = cuadricula(centroX, centroY, tamanioX,
                                                                                                tamanioY, tamanioDivisiones)

        plt.plot(xCuadricula, yCuadricula, 'k', xCuadricula.T, yCuadricula.T, 'k', linewidth=0.1)
        plt.plot(xHorizontal, yHorizontal, 'r', linewidth=0.3)
        plt.plot(xVertical, yVertical, 'r', linewidth=0.3)

        io.imshow(imagenPosterior)

        dirImagenPosterior = imgVoluntario + nombreImagenPosterior + '.jpg'
        #time.sleep(1)

        plt.savefig(dirImagenPosterior, dpi=500)
        plt.close()     # Para mostrar la imagen cambiar "close" por "show"

        # TP1
        hombroDescendido, anguloHombro = tablaPosteriorParteUno(P4, P3)
        pelvisDescendida, anguloPelvis = tablaPosteriorParteUno(P6, P5)
        rodillaDescendida, anguloRodilla = tablaPosteriorParteUno(P8, P7)

        # TP2
        direccionHombros, distanciaHombros = tablaPosteriorParteDos(PcX, PcH, razonDeEscala)
        direccion7maCervical, distancia7maCervical = tablaPosteriorParteDos(PcX, P1, razonDeEscala)
        direccion5taToracica, distancia5taToracica = tablaPosteriorParteDos(PcX, P2, razonDeEscala)
        direccionPelvis, distanciaPelvis = tablaPosteriorParteDos(PcX, PcY, razonDeEscala)
        direccionRodillas, distanciaRodillas = tablaPosteriorParteDos(PcX, PcR, razonDeEscala)
        direccionTobillos, distanciaTobillos = tablaPosteriorParteDos(PcX, PcT, razonDeEscala)

        # TP3
        direccionPieIzquierdo, anguloPieIzquierdo = tablaPosteriorParteTres(P10, P12)
        direccionPieDerecho, anguloPieDerecho = tablaPosteriorParteTres(P11, P9)

        datos = [anguloTolerancia, distanciaTolerancia, hombroDescendido, anguloHombro, pelvisDescendida, anguloPelvis,
                 rodillaDescendida, anguloRodilla, direccionHombros, distanciaHombros, direccion7maCervical,
                 distancia7maCervical, direccion5taToracica, distancia5taToracica, direccionPelvis, distanciaPelvis,
                 direccionRodillas, distanciaRodillas, direccionTobillos, distanciaTobillos, direccionPieIzquierdo,
                 anguloPieIzquierdo, direccionPieDerecho, anguloPieDerecho]

        return datos
    return 0

def evaluacionLateralD(fotoLateralD):
    imagen = io.imread(fotoLateralD)
    imagen = escalarImagen(imagen)
    #io.imshow(imagen)
    #plt.close()            # Para mostrar la imagen cambiar "close" por "show"
    imagenLateralD = ajustarImagen(imagen)

    imagenLateralDFiltrada = filtroColorVerde(imagenLateralD)
    referenciaUno = etiquetas(imagenLateralDFiltrada).referenciaUno
    referenciaDos = etiquetas(imagenLateralDFiltrada).referenciaDos
    centrosCoordenadaY = etiquetas(imagenLateralDFiltrada).centrosCoordenadaY
    centrosCoordenadaX = etiquetas(imagenLateralDFiltrada).centrosCoordenadaX
    razonDeEscala = etiquetas(imagenLateralDFiltrada).razonDeEscala

    '''
    PUTNOS ANATOMICOS
    L1 = Oido
    L2 = Hombro
    L3 = Pelvis Posterior
    L4 = Pelvis Anterior
    L5 = Cadera
    L6 = Rodilla
    L7 = Planta
    LcY= Centro en Y (Pelvis)
    '''

    if (len(centrosCoordenadaX) > 7):
        print("Existen demasiados puntos en la imagen")
        plt.figure(1)
        plt.title('Lateral Derecha: {0}/{1}'.format(len(centrosCoordenadaX), 7))
        plt.plot(centrosCoordenadaX, centrosCoordenadaY, 'b*', markersize="5")
        io.imshow(imagenLateralD)
        plt.show()

    elif (len(centrosCoordenadaX) < 7):
        print("Existen menos puntos en la imagen")
        plt.figure(1)
        plt.title('Lateral Derecha: {0}/{1}'.format(len(centrosCoordenadaX), 7))
        plt.plot(centrosCoordenadaX, centrosCoordenadaY, 'b*', markersize="5")
        io.imshow(imagenLateralD)
        plt.show()

    else:

        L1 = (centrosCoordenadaY[0], centrosCoordenadaX[0])
        L2 = (centrosCoordenadaY[1], centrosCoordenadaX[1])

        coordenadaTempY = [centrosCoordenadaY[2], centrosCoordenadaY[3]]
        coordenadaTempX = [centrosCoordenadaX[2], centrosCoordenadaX[3]]
        posicion = [i for i, x in enumerate(coordenadaTempX) if x == min(coordenadaTempX)]
        L3 = coordenadaTempY[posicion[0]], coordenadaTempX[posicion[0]]
        posicion = [i for i, x in enumerate(coordenadaTempX) if x == max(coordenadaTempX)]
        L4 = coordenadaTempY[posicion[0]], coordenadaTempX[posicion[0]]

        L5 = (centrosCoordenadaY[4], centrosCoordenadaX[4])
        L6 = (centrosCoordenadaY[5], centrosCoordenadaX[5])
        L7 = (centrosCoordenadaY[6], centrosCoordenadaX[6])

        LcY = np.mean([L3, L4], axis=0)

        L1 = np.array(L1)
        L2 = np.array(L2)
        L3 = np.array(L3)
        L4 = np.array(L4)
        L5 = np.array(L5)
        L6 = np.array(L6)
        L7 = np.array(L7)

        LcY = np.array(LcY)

        plt.figure(1)
        plt.title('Vista Lateral Derecha')

        plt.plot(centrosCoordenadaX, centrosCoordenadaY, 'b*', markersize="1")

        plt.plot(LcY[1], LcY[0], 'rx', markersize="3")

        coordenadasReferencia = referenciaDos - referenciaUno
        tamanioDivisiones = np.sqrt((coordenadasReferencia[0] ** 2 + coordenadasReferencia[1] ** 2)) / 20.0

        centroX = L7[1]
        centroY = LcY[0]
        tamanioX = len(imagenLateralD[1])
        tamanioY = len(imagenLateralD)

        (xCuadricula, yCuadricula, xHorizontal, yHorizontal, xVertical, yVertical) = cuadricula(centroX, centroY, tamanioX,
                                                                                                tamanioY, tamanioDivisiones)

        plt.plot(xCuadricula, yCuadricula, 'k', xCuadricula.T, yCuadricula.T, 'k', linewidth=0.1)
        plt.plot(xHorizontal, yHorizontal, 'r', linewidth=0.3)
        plt.plot(xVertical, yVertical, 'r', linewidth=0.3)

        io.imshow(imagenLateralD)

        dirImagenLateralD = imgVoluntario + nombreImagenLateralD + '.jpg'
        #time.sleep(1)

        plt.savefig(dirImagenLateralD, dpi=500)
        plt.close()     # Para mostrar la imagen cambiar "close" por "show"

        # TL1
        direccionCabezaHombro, anguloCabezaHombro = tablaLateralDParteUno(L1, L2)
        direccionHombroPelvis, anguloHombroPelvis = tablaLateralDParteUno(L2, LcY)
        direccionCaderaRodillas, anguloCaderaRodillas = tablaLateralDParteUno(L5, L6)
        direccionRodillasPies, anguloRodillasPies = tablaLateralDParteUno(L6, L7)

        # TL2
        direccionPelvis, anguloPelvis = tablaLateralDParteDos(L3, L4)

        # TL3
        direccionCabeza, distanciaCabeza = tablaLateralDParteTres(L7, L1, razonDeEscala)
        direccionHombro, distanciaHombro = tablaLateralDParteTres(L7, L2, razonDeEscala)
        direccionPelvisL3, distanciaPelvis = tablaLateralDParteTres(L7, LcY, razonDeEscala)
        direccionCadera, distanciaCadera = tablaLateralDParteTres(L7, L5, razonDeEscala)
        direccionRodilla, distanciaRodilla = tablaLateralDParteTres(L7, L6, razonDeEscala)


        datos = [anguloTolerancia, distanciaTolerancia,direccionCabezaHombro, anguloCabezaHombro, direccionHombroPelvis,
                 anguloHombroPelvis, direccionCaderaRodillas, anguloCaderaRodillas, direccionRodillasPies,
                 anguloRodillasPies, direccionPelvis, anguloPelvis, direccionCabeza, distanciaCabeza, direccionHombro,
                 distanciaHombro, direccionPelvisL3, distanciaPelvis, direccionCadera, distanciaCadera,
                 direccionRodilla, distanciaRodilla]

        return datos
    return 0

class reportePDF(object):

    """
    Exportar los datos del analisis al PDF.
    """
    def __init__(self, nombrePDF):
        super(reportePDF, self).__init__()

        self.nombrePDF = nombrePDF
        self.estilos = getSampleStyleSheet()

    @staticmethod
    def _encabezadoPiePagina(canvas, archivoPDF):
        """Guarde el estado de nuestro lienzo para que podamos aprovecharlo"""

        canvas.saveState()
        estilos = getSampleStyleSheet()

        alineacion = ParagraphStyle(name="alineacion", alignment=TA_RIGHT,
                                    parent=estilos["Normal"])

        # Encabezado
        encabezadoNombre = Paragraph(nombre, estilos["Normal"])
        encabezadoNombre.wrap(archivoPDF.width, archivoPDF.topMargin)
        encabezadoNombre.drawOn(canvas, archivoPDF.leftMargin, 736)

        fecha = utcnow().to("local").format("dddd, DD - MMMM - YYYY", locale="es")
        fechaReporte = fecha.replace("-", "de")

        encabezadoFecha = Paragraph(fechaReporte, alineacion)
        encabezadoFecha.wrap(archivoPDF.width, archivoPDF.topMargin)
        encabezadoFecha.drawOn(canvas, archivoPDF.leftMargin, 736)

        # Pie de página
        piePagina = Paragraph("Lectura automatica de marcadores", estilos["Normal"])
        piePagina.wrap(archivoPDF.width, archivoPDF.bottomMargin)
        piePagina.drawOn(canvas, archivoPDF.leftMargin, 15 * mm + (5 * mm))

        # Suelta el lienzo
        canvas.restoreState()

    def Exportar(self, dbAnterior, dbPosterior, dbLateralD):
        """Exportar los datos a un archivo PDF."""

        PS = ParagraphStyle

        alineacionTitulo = PS(name="centrar", alignment=TA_CENTER, fontSize=14,
                                          leading=10, textColor=black,
                                          parent=self.estilos["Heading1"])

        parrafoPrincipal = PS(name="centrar", alignment=TA_LEFT, fontSize=10,
                                          leading=8, textColor=black,
                                          parent=self.estilos["Heading1"])

        parrafoSecundario = PS(name="centrar", alignment=TA_LEFT, fontSize=10,
                                          leading=16, textColor=black)

        self.ancho, self.alto = letter

        estiloTablaDatos = [("BACKGROUND", (0, 0), (-1, 0), cornflowerblue),
                            ("TEXTCOLOR", (0, 0), (-1, 0), whitesmoke),
                            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                            ("ALIGN", (0, 0), (0, -1), "LEFT"),
                            ("VALIGN", (0, 0), (-1, -1), "MIDDLE", black),  # Texto centrado y alineado a la izquierda
                            ("INNERGRID", (0, 0), (-1, -1), 0.50, black),  # Lineas internas
                            ("BOX", (0, 0), (-1, -1), 0.25, black),  # Linea (Marco) externa
                            ]

        estiloTablaResultados = [("BACKGROUND", (0, 0), (-1, 0), lightsteelblue),
                                 ("TEXTCOLOR", (0, 0), (-1, 0), black),
                                 ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                                 ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                                 ("ALIGN", (0, 0), (0, -1), "LEFT"),
                                 ("VALIGN", (0, 0), (-1, -1), "MIDDLE", black),  # Texto centrado y alineado a la izquierda
                                 ("INNERGRID", (0, 0), (-1, -1), 0.50, black),  # Lineas internas
                                 ("BOX", (0, 0), (-1, -1), 0.25, black)  # Linea (Marco) externa
                                 ]

        tablaDatos = Table([['Fecha', 'Nombre', 'Edad', 'Género', 'Peso [kg]', 'Talla [cm]', 'Ocupación'],
                            [fecha, nombre, edad, genero, peso, talla, ocupacion]], colWidths=(self.ancho - 100) / 7,
                           hAlign="CENTER",style=estiloTablaDatos)

        tablaDatos._argW[1] = 38 * mm

        historia = []
        historia.append(Paragraph("Evaluación Postural", alineacionTitulo))
        historia.append(Spacer(1, 4 * mm))
        historia.append(tablaDatos)
        historia.append(get_image("logo.png", height=100*mm)) # https://i.imgur.com/KRPTibG.png
        historia.append(PageBreak())

        # PAGINA TABLA EVALUACION ANTERIOR
        if (examenAnterior):
            tablaAnteriorParteUnoPDF = Table([['Segmento Corporal', 'Descendido', 'Ángulo'],
                                              ['Hombro', dbAnterior[2], dbAnterior[3]],
                                              ['Pelvis', dbAnterior[4], dbAnterior[5]],
                                              ['Rodilla', dbAnterior[6], dbAnterior[7]]],
                                             colWidths=(self.ancho - 100) / 5, hAlign="LEFT", style=estiloTablaResultados)

            tablaAnteriorParteDosPDF = Table([['Referencia', 'Dirección', 'Distancia'],
                                              ['Frente', dbAnterior[8], dbAnterior[9]],
                                              ['Hombros', dbAnterior[10], dbAnterior[11]],
                                              ['Ombligo', dbAnterior[12], dbAnterior[13]],
                                              ['Pelvis', dbAnterior[14], dbAnterior[15]],
                                              ['Rodillas', dbAnterior[16], dbAnterior[17]],
                                              ['Pies', dbAnterior[18], dbAnterior[19]]],
                                             colWidths=(self.ancho - 100) / 5, hAlign="LEFT", style=estiloTablaResultados)

            tablaAnteriorParteTresPDF = Table([['Segmento Corporal', 'Dirección', 'Ángulo'],
                                              ['Pie Izquierdo', dbAnterior[20], dbAnterior[21]],
                                              ['Pie Derecho', dbAnterior[22], dbAnterior[23]]],
                                             colWidths=(self.ancho - 100) / 5, hAlign="LEFT", style=estiloTablaResultados)

            historia.append(get_image(imgVoluntario + nombreImagenAnterior+'.jpg', height=100*mm))
            historia.append(Paragraph("Grados con respecto a la horizontal:", parrafoPrincipal))
            historia.append(Paragraph("El ángulo ideal debe ser <strong>0°</strong>.", parrafoSecundario))
            historia.append(tablaAnteriorParteUnoPDF)
            historia.append(Paragraph("Distancia con respecto a la vertical:", parrafoPrincipal))
            historia.append(Paragraph("La distancia ideal debe ser <strong>0 cm</strong>.", parrafoSecundario))
            historia.append(tablaAnteriorParteDosPDF)
            historia.append(Paragraph("Grados de rotación de los pies:", parrafoPrincipal))
            historia.append(Paragraph("El ángulo ideal debe ser <strong>0°</strong>.", parrafoSecundario))
            historia.append(tablaAnteriorParteTresPDF)
            historia.append(PageBreak())

        # PAGINA TABLA EVALUACION POSTERIOR
        if (examenPosterior):
            tablaPosteriorParteUnoPDF = Table([['Segmento Corporal', 'Descendido', 'Ángulo'],
                                              ['Hombro', dbPosterior[2], dbPosterior[3]],
                                              ['Pelvis', dbPosterior[4], dbPosterior[5]],
                                              ['Rodilla', dbPosterior[6], dbPosterior[7]]],
                                             colWidths=(self.ancho - 100) / 5, hAlign="LEFT", style=estiloTablaResultados)

            tablaPosteriorParteDosPDF = Table([['Referencia', 'Dirección', 'Distancia'],
                                              ['Hombros', dbPosterior[8], dbPosterior[9]],
                                              ['7ma Cervical', dbPosterior[10], dbPosterior[11]],
                                              ['5ta Torácica', dbPosterior[12], dbPosterior[13]],
                                              ['Pelvis', dbPosterior[14], dbPosterior[15]],
                                              ['Rodillas', dbPosterior[16], dbPosterior[17]],
                                              ['Tobillos', dbPosterior[18], dbPosterior[19]]],
                                             colWidths=(self.ancho - 100) / 5, hAlign="LEFT", style=estiloTablaResultados)

            tablaPosteriorParteTresPDF = Table([['Segmento Corporal', 'Dirección', 'Ángulo'],
                                              ['Pie Izquierdo', dbPosterior[20], dbPosterior[21]],
                                              ['Pie Derecho', dbPosterior[22], dbPosterior[23]]],
                                             colWidths=(self.ancho - 100) / 5, hAlign="LEFT", style=estiloTablaResultados)

            historia.append(get_image(imgVoluntario + nombreImagenPosterior+'.jpg', height=100*mm))
            historia.append(Paragraph("Grados con respecto a la horizontal:", parrafoPrincipal))
            historia.append(Paragraph("El ángulo ideal debe ser <strong>0°</strong>.", parrafoSecundario))
            historia.append(tablaPosteriorParteUnoPDF)
            historia.append(Paragraph("Distancia con respecto a la vertical:", parrafoPrincipal))
            historia.append(Paragraph("La distancia ideal debe ser <strong>0 cm</strong>.", parrafoSecundario))
            historia.append(tablaPosteriorParteDosPDF)
            historia.append(Paragraph("Grados de rotación de los pies:", parrafoPrincipal))
            historia.append(Paragraph("El ángulo ideal debe ser <strong>0°</strong>.", parrafoSecundario))
            historia.append(tablaPosteriorParteTresPDF)
            historia.append(PageBreak())

        # PAGINA TABLA EVALUACION LATERALD
        if (examenLateralD):
            tablaLateralDParteUnoPDF = Table([['Segmento Corporal', 'Dirección', 'Ángulo'],
                                              ['Cabeza-Hombro', dbLateralD[2], dbLateralD[3]],
                                              ['Hombro-Pelvis', dbLateralD[4], dbLateralD[5]],
                                              ['Caderas-Rodillas', dbLateralD[6], dbLateralD[7]],
                                              ['Rodillas-Pies', dbLateralD[8], dbLateralD[9]]],
                                             colWidths=(self.ancho - 100) / 5, hAlign="LEFT", style=estiloTablaResultados)

            tablaLateralDParteDosPDF = Table([['Segmento Corporal', 'Dirección', 'Ángulo'],
                                              ['Pelvis', dbLateralD[10], dbLateralD[11]]],
                                             colWidths=(self.ancho - 100) / 5, hAlign="LEFT", style=estiloTablaResultados)

            tablaLateralDParteTresPDF = Table([['Referencia', 'Dirección', 'Distancia'],
                                              ['Cabeza', dbLateralD[12], dbLateralD[13]],
                                              ['Hombro', dbLateralD[14], dbLateralD[15]],
                                              ['Pelvis', dbLateralD[16], dbLateralD[17]],
                                              ['Cadera', dbLateralD[18], dbLateralD[19]],
                                              ['Rodilla', dbLateralD[20], dbLateralD[21]]],
                                             colWidths=(self.ancho - 100) / 5, hAlign="LEFT", style=estiloTablaResultados)

            historia.append(get_image(imgVoluntario + nombreImagenLateralD+'.jpg', height=100*mm))
            historia.append(Paragraph("Grados con respecto a la vertical:", parrafoPrincipal))
            historia.append(Paragraph("El ángulo ideal debe ser <strong>0°</strong>.", parrafoSecundario))
            historia.append(tablaLateralDParteUnoPDF)
            historia.append(Paragraph("Grados con respecto a la horizontal:", parrafoPrincipal))
            historia.append(Paragraph("El ángulo normal entre los marcadores pélvicos anterior y posterior <strong>10°"
                                      "</strong>", parrafoSecundario))
            historia.append(Paragraph("con una tolerancia de <strong>±5°</strong>.", parrafoSecundario))
            historia.append(tablaLateralDParteDosPDF)
            historia.append(Paragraph("Distancia con respecto a la vertical:", parrafoPrincipal))
            historia.append(Paragraph("La distancia ideal debe ser <strong>0 cm</strong>.", parrafoSecundario))
            historia.append(tablaLateralDParteTresPDF)
            historia.append(PageBreak())

        archivoPDF = SimpleDocTemplate(self.nombrePDF, leftMargin=50, rightMargin=50, pagesize=letter,
                                       title="Reporte PDF", author="Youssef Abarca")

        try:
            archivoPDF.build(historia, onFirstPage=self._encabezadoPiePagina,
                             onLaterPages=self._encabezadoPiePagina,
                             canvasmaker=numeracionPaginas)

            # +------------------------------------+
            return "\nReporte generado con éxito."
        # +------------------------------------+
        except PermissionError:
            # +--------------------------------------------+
            return "Error inesperado: Permiso denegado."
        # +--------------------------------------------+

# Cargar imagenes (Funciones temporales)

def cargarImagenAnterior():
    root = Tk()

    def botonCargar():
        global fotoAnterior
        fotoAnterior=filedialog.askopenfilename(title='Abrir',
                initialdir='C:',filetypes=(('Imagenes','*.jpg'),
                ('Imagenes','*.png'),('Todos los ficheros','*.*')))
        root.destroy()

    try:
        root.iconbitmap('icon.ico')
    except TclError:
        print ('No ico file found')

    root.title('Análisis Postural LAM')

    root.geometry('300x50')
    Label(root, text="Cargue la imagen de la vista anteriror").pack()
    # Enlezamos la función a la acción del botón
    fichero = Button(root, text="Cargar imagen", command=botonCargar).pack()

    root.mainloop()

def cargarImagenPosterior():
    root = Tk()

    def botonCargar():
        global fotoPosterior
        fotoPosterior=filedialog.askopenfilename(title='Abrir',
                initialdir='C:',filetypes=(('Imagenes','*.jpg'),
                ('Imagenes','*.png'),('Todos los ficheros','*.*')))
        root.destroy()

    try:
        root.iconbitmap('icon.ico')
    except TclError:
        print ('No ico file found')

    root.title('Análisis Postural LAM')

    root.geometry('300x50')
    Label(root, text="Cargue la imagen de la vista posterior").pack()
    # Enlezamos la función a la acción del botón
    fichero = Button(root, text="Cargar imagen", command=botonCargar).pack()

    root.mainloop()

def cargarImagenLateralD():
    root = Tk()

    def botonCargar():
        global fotoLateralD
        fotoLateralD=filedialog.askopenfilename(title='Abrir',
                initialdir='C:',filetypes=(('Imagenes','*.jpg'),
                ('Imagenes','*.png'),('Todos los ficheros','*.*')))
        root.destroy()

    try:
        root.iconbitmap('icon.ico')
    except TclError:
        print ('No ico file found')

    root.title('Análisis Postural LAM')

    root.geometry('300x50')
    Label(root, text="Cargue la imagen de la vista lateral derecha").pack()
    # Enlezamos la función a la acción del botón
    fichero = Button(root, text="Cargar imagen", command=botonCargar).pack()

    root.mainloop()

####### PROGRAMA #######

year = datetime.datetime.now().year
month = datetime.datetime.now().month
day = datetime.datetime.now().day

if(datetime.date(year,month,day)<=datetime.date(2021,6,1)):

    while True:

        # Datos Personales

        date = datetime.datetime.now()
        fechaActual = time.strftime("%d/%m/%Y")

        fecha = fechaActual

        print("\nDATOS PERSONALES\n")

        nombre = input("Nombre: ")
        edad = int(input("Edad: "))
        genero = input("Genero (M/F): ")
        peso = float(input("Peso en Kg: "))
        talla = float(input("Altura en cm: "))
        ocupacion = input("Ocupación: ")

        print("\nIngrese las tolerancias: \n")

        anguloTolerancia = float(input("Tolerancia en grados para los ángulos:  "))
        distanciaTolerancia = float(input("Tolerancia en cm para las distancias: "))

        # Creacion del directorio LAM

        dirLAM = '~\\Documents\\LAM\\'
        dirVoltario = dirLAM + nombre + '\\'
        dirImagen = dirVoltario + 'Imagenes\\'

        directorio = os.path.expanduser(dirLAM)
        carpetaVoluntario = os.path.expanduser(dirVoltario)
        imgVoluntario = os.path.expanduser(dirImagen)

        dirDBxlsx = directorio + 'DB_LAM.xlsx'

        if (os.path.isdir(directorio)==False):
            os.mkdir(directorio)
            directorio=os.path.expanduser(dirLAM)


        if (os.path.isdir(carpetaVoluntario) == False):
            os.mkdir(carpetaVoluntario)
            carpetaVoluntario = os.path.expanduser(dirVoltario)

        if (os.path.isdir(imgVoluntario) == False):
            os.mkdir(imgVoluntario)
            imgVoluntario = os.path.expanduser(dirImagen)

        # Datos para la ejecución

        examenAnterior = True
        examenPosterior = True
        examenLateralD = True

        # Condicion para saber que analisis realizar:

        print("\nEvaluaciones a realizar => 1: Si | 0: NO\n")

        examenAnterior = bool(int(input("Vista Anterior 1/0: ")))
        examenPosterior = bool(int(input("Vista Posterior 1/0: ")))
        examenLateralD = bool(int(input("Vista Lateral Derecha 1/0: ")))

        nombreImagenAnterior = 'Anterior'+'_'+time.strftime("%Y%m%d")+'_'+time.strftime("%H%M%S")
        nombreImagenPosterior = 'Posterior'+'_'+time.strftime("%Y%m%d")+'_'+time.strftime("%H%M%S")
        nombreImagenLateralD = 'LateralD'+'_'+time.strftime("%Y%m%d")+'_'+time.strftime("%H%M%S")

        fotoAnterior=''
        fotoPosterior=''
        fotoLateralD=''

        resultadosAnterior = 0
        resultadosPosterior = 0
        resultadosLateralD = 0

        # Pruaba de cargado de imagenes en caso de imagenes erroneas

        if (examenAnterior):
            cargarImagenAnterior()
            resultadosAnterior = evaluacionAnterior(fotoAnterior)

            while (resultadosAnterior == 0):

                recargarImagen = bool(int(input("Imagen Anterior con Error. ¿Desea cargar otra imagen? 1/0: ")))

                if recargarImagen == True:
                    cargarImagenAnterior()
                    resultadosAnterior = evaluacionAnterior(fotoAnterior)  # https://i.imgur.com/qRb4dv6.jpg

                else:
                    examenAnterior = False
                    break

        if (examenPosterior):
            cargarImagenPosterior()
            resultadosPosterior = evaluacionPosterior(fotoPosterior)    # https://i.imgur.com/xIYYjkc.jpg

            while (resultadosPosterior == 0):

                recargarImagen = bool(int(input("Imagen Posterior con Error. ¿Desea cargar otra imagen? 1/0: ")))

                if recargarImagen == True:
                    cargarImagenPosterior()
                    resultadosPosterior = evaluacionPosterior(fotoPosterior)  # https://i.imgur.com/xIYYjkc.jpg

                else:
                    examenPosterior = False
                    break

        if (examenLateralD):
            cargarImagenLateralD()
            resultadosLateralD = evaluacionLateralD(fotoLateralD)      # https://i.imgur.com/2fvjwk1.jpg

            while (resultadosLateralD == 0):

                recargarImagen = bool(int(input("Imagen Lateral Derecha con Error. ¿Desea cargar otra imagen? 1/0: ")))

                if recargarImagen == True:
                    cargarImagenLateralD()
                    resultadosLateralD = evaluacionLateralD(fotoLateralD)  # https://i.imgur.com/2fvjwk1.jpg

                else:
                    examenLateralD = False
                    break

        ###############################

        if(examenAnterior):
            dataTablaAnterior = pd.DataFrame(resultadosAnterior)
            #print(dataTablaAnterior.T)

            direccionImagenAnterior = '=HYPERLINK("' + imgVoluntario + nombreImagenAnterior + '.jpg","' + nombreImagenAnterior + '")'
            encabezadoAnterior = pd.DataFrame([], ['Fecha', 'Nombre', 'Edad', 'Género', 'Peso[kg]', 'Talla[cm]', 'Ocupación',
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
                                                   'Rotación Pie Derecho', 'Ángulo Pie Derecho', 'Dirección Imagen',
                                                   'Dirección del Reporte'])

        if(examenPosterior):
            dataTablaPosterior = pd.DataFrame(resultadosPosterior)
            #print(dataTablaPosterior.T)

            direccionImagenPosterior = '=HYPERLINK("' + imgVoluntario + nombreImagenPosterior + '.jpg","' + nombreImagenPosterior + '")'

            encabezadoPosterior = pd.DataFrame([], ['Fecha', 'Nombre', 'Edad', 'Género', 'Peso[kg]', 'Talla[cm]', 'Ocupación',
                                                    'Ángulo de tolerancia', 'Distancia de tolerancia',
                                                    'Hombro Descendido', 'Ángulo del hombro',
                                                    'Pelvis Descendida', 'Ángulo de la Pelvis',
                                                    'Rodilla Descendida', 'Ángulo de Rodilla',
                                                    'Dirección de la Hombros', 'Distancia de la Hombros',
                                                    'Dirección de los 7ma Cervical', 'Distancia de los 7ma Cervical',
                                                    'Dirección del 5ta Torácica', 'Distancia del 5ta Torácica',
                                                    'Dirección de la Pelvis', 'Distancia de la Pelvis',
                                                    'Dirección de las Rodillas', 'Distancia de las Rodillas',
                                                    'Dirección de los Tobillos', 'Distancia de los Tobillos',
                                                    'Dirección Pie Izquierdo', 'Ángulo Pie Izquierdo',
                                                    'Dirección Pie Derecho', 'Ángulo Pie Derecho', 'Dirección Imagen',
                                                    'Dirección del Reporte'])

        if(examenLateralD):
            dataTablaLateralD = pd.DataFrame(resultadosLateralD)
            #print(dataTablaLateralD.T)

            direccionImagenLateralD = '=HYPERLINK("' + imgVoluntario + nombreImagenLateralD + '.jpg","' + nombreImagenLateralD + '")'

            encabezadoLateralD = pd.DataFrame([], ['Fecha', 'Nombre', 'Edad', 'Género', 'Peso[kg]', 'Talla[cm]', 'Ocupación',
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
                                                   'Dirección de la Rodilla', 'Distancia de la Rodilla', 'Dirección Imagen',
                                                   'Dirección del Reporte'])

        nombrePDF = generarReporte(resultadosAnterior, resultadosPosterior, resultadosLateralD)
        direccionReporte='=HYPERLINK("'+carpetaVoluntario + nombrePDF +'.pdf","'+nombrePDF+'")'

        encabezadoDatos = pd.DataFrame([fecha, nombre, edad, genero, peso, talla, ocupacion])

        if os.path.exists(dirDBxlsx) == False:
            book = pd.ExcelWriter(dirDBxlsx)
            pd.DataFrame().to_excel(book, 'Anterior')
            pd.DataFrame().to_excel(book, 'Posterior')
            pd.DataFrame().to_excel(book, 'LateralD')
            book.save()

        book = load_workbook(dirDBxlsx)
        time.sleep(0.2)

        nCeldasAnterior = len(pd.read_excel(dirDBxlsx, sheet_name=0))
        nCeldasPosterior = len(pd.read_excel(dirDBxlsx, sheet_name=1))
        nCeldasLateralD = len(pd.read_excel(dirDBxlsx, sheet_name=2))

        with pd.ExcelWriter(dirDBxlsx, engine='openpyxl') as writer:
            writer.book = book
            writer.sheets = dict((ws.title, ws) for ws in book.worksheets)

            if (examenAnterior):

                encabezadoAnterior.T.to_excel(writer, 'Anterior',
                                              header=True, index=False, startrow=0, startcol=0)
                encabezadoDatos.T.to_excel(writer, 'Anterior',
                                      header=False, index=False, startrow=nCeldasAnterior+1, startcol=0)
                dataTablaAnterior.T.to_excel(writer, 'Anterior',
                                                     header=False, index=False, startrow=nCeldasAnterior+1, startcol=7)
                pd.DataFrame({'link':[direccionImagenAnterior]}).T.to_excel(writer, 'Anterior',
                                                                            header=False, index=False, startrow=nCeldasAnterior+1, startcol=31)
                pd.DataFrame({'link':[direccionReporte]}).T.to_excel(writer, 'Anterior',
                                                     header=False, index=False, startrow=nCeldasAnterior+1, startcol=32)
                time.sleep(0.2)

            if (examenPosterior):

                encabezadoPosterior.T.to_excel(writer, 'Posterior',
                                              header=True, index=False, startrow=0, startcol=0)
                encabezadoDatos.T.to_excel(writer, 'Posterior',
                                      header=False, index=False, startrow=nCeldasPosterior+1, startcol=0)
                dataTablaPosterior.T.to_excel(writer, 'Posterior',
                                                     header=False, index=False, startrow=nCeldasPosterior+1, startcol=7)
                pd.DataFrame({'link':[direccionImagenPosterior]}).T.to_excel(writer, 'Posterior',
                                                                            header=False, index=False, startrow=nCeldasPosterior+1, startcol=31)
                pd.DataFrame({'link':[direccionReporte]}).T.to_excel(writer, 'Posterior',
                                                     header=False, index=False, startrow=nCeldasPosterior+1, startcol=32)
                time.sleep(0.2)

            if (examenLateralD):

                encabezadoLateralD.T.to_excel(writer, 'LateralD',
                                              header=True, index=False, startrow=0, startcol=0)
                encabezadoDatos.T.to_excel(writer, 'LateralD',
                                      header=False, index=False, startrow=nCeldasLateralD+1, startcol=0)
                dataTablaLateralD.T.to_excel(writer, 'LateralD',
                                                     header=False, index=False, startrow=nCeldasLateralD+1, startcol=7)
                pd.DataFrame({'link':[direccionImagenLateralD]}).T.to_excel(writer, 'LateralD',
                                                                            header=False, index=False, startrow=nCeldasLateralD+1, startcol=29)
                pd.DataFrame({'link':[direccionReporte]}).T.to_excel(writer, 'LateralD',
                                                     header=False, index=False, startrow=nCeldasLateralD+1, startcol=30)

                time.sleep(0.2)

            writer.save()
            print('Datos agregados con éxito\n')

        salir = bool(int(input('Desea salir? 1: Si | 0: NO => ')))

        if salir:
            break
        os.system("cls")

else:
    print('El tiempo de uso a finalizado el: ', datetime.date(2021,6,1))
    input()
# Para crear ejecutable: pyinstaller --onefile --icon=icon.ico sistema_LAM.py