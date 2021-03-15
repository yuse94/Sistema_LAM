"""
LAM está en construcción
Versión Consola de python3 0.1
"""
from skimage import (io, filters,
                     morphology, transform, img_as_ubyte)
from skimage.color import rgb2gray
from skimage.measure import label, regionprops
from openpyxl import load_workbook

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
    angulo = np.angle(complex(distancia[1], distancia[0]), deg=True)

    if angulo < -anguloTolerancia:
        descendido = 'Der.'
    elif angulo > anguloTolerancia:
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

    if distancia < -distanciaTolerancia:
        direccion = 'Izq.'
    elif distancia > distanciaTolerancia:
        direccion = 'Der.'
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
    angulo = abs(np.angle(complex(distancia[1], distancia[0]), deg=True))

    if angulo > 90+anguloTolerancia:
        direccion = 'Rot.Ext.'
    elif angulo < 90-anguloTolerancia:
        direccion = 'Rot.Int.'
    else:
        direccion = 'Alin.'

    angulo = round((angulo - 90), 4)

    return direccion, angulo

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

def generarReporte(datosAnterio):
    """
    Genera el reporte PDF con su respectivo nombre
    """
    nombrePDF = nombre + '_' + time.strftime("%Y%m%d")+'_'+time.strftime("%H%M%S")
    reporte = reportePDF(carpetaVoluntario + nombrePDF + '.pdf').Exportar(datosAnterio)
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

def evaluacionAnterior():
    imagen = io.imread('DSC_0376.jpg')
    imagen = escalarImagen(imagen)
    io.imshow(imagen)
    plt.show()
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
    time.sleep(1)

    plt.savefig(dirImagenAnterior, dpi=500)
    plt.show()

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
    direccionPieDerecho, anguloPieDerecho = tablaAnteriorParteTres(F11, F13)

    datos = [hombroDescendido, anguloHombro, pelvisDescendida, anguloPelvis, rodillaDescendida, anguloRodilla,
             direccionFrente, distanciaFrente, direccionHombros, distanciaHombros, direccionOmbligo, distanciaOmbligo,
             direccionPelvis, distanciaPelvis, direccionRodillas, distanciaRodillas, direccionPies, distanciaPies,
             direccionPieIzquierdo, anguloPieIzquierdo, direccionPieDerecho, anguloPieDerecho]

    return datos

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

    def Exportar(self, dbAnterior):
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

        tablaAnteriorParteUnoPDF = Table([['Segmento Corporal', 'Descendido', 'Ángulo'],
                                          ['Hombro', dbAnterior[0], dbAnterior[1]],
                                          ['Pelvis', dbAnterior[2], dbAnterior[3]],
                                          ['Rodilla', dbAnterior[4], dbAnterior[5]]],
                                         colWidths=(self.ancho - 100) / 5, hAlign="LEFT", style=estiloTablaResultados)

        tablaAnteriorParteDosPDF = Table([['Referencia', 'Dirección', 'Distancia'],
                                          ['Frente', dbAnterior[6], dbAnterior[7]],
                                          ['Hombros', dbAnterior[8], dbAnterior[9]],
                                          ['Ombligo', dbAnterior[10], dbAnterior[11]],
                                          ['Pelvis', dbAnterior[12], dbAnterior[13]],
                                          ['Rodillas', dbAnterior[14], dbAnterior[15]],
                                          ['Pies', dbAnterior[16], dbAnterior[17]]],
                                         colWidths=(self.ancho - 100) / 5, hAlign="LEFT", style=estiloTablaResultados)

        tablaAnteriorParteTresPDF = Table([['Segmento Corporal', 'Dirección', 'Ángulo'],
                                          ['Pie Izquierdo', dbAnterior[18], dbAnterior[19]],
                                          ['Pie Derecho', dbAnterior[20], dbAnterior[21]]],
                                         colWidths=(self.ancho - 100) / 5, hAlign="LEFT", style=estiloTablaResultados)

        historia = []
        historia.append(Paragraph("Evaluación Postural", alineacionTitulo))
        historia.append(Spacer(1, 4 * mm))
        historia.append(tablaDatos)
        historia.append(get_image("logo.png", height=100*mm))
        historia.append(PageBreak())

        # PAGINA TABLA EVALUACION ANTERIOR
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

        # PAGINA TABLA EVALUACION LATERALD

        archivoPDF = SimpleDocTemplate(self.nombrePDF, leftMargin=50, rightMargin=50, pagesize=letter,
                                       title="Reporte PDF", author="Youssef Abarca")

        try:
            archivoPDF.build(historia, onFirstPage=self._encabezadoPiePagina,
                             onLaterPages=self._encabezadoPiePagina,
                             canvasmaker=numeracionPaginas)

            # +------------------------------------+
            return "Reporte generado con éxito."
        # +------------------------------------+
        except PermissionError:
            # +--------------------------------------------+
            return "Error inesperado: Permiso denegado."
        # +--------------------------------------------+

####### PROGRAMA #######

####### Datos ######

date = datetime.datetime.now()
fechaActual = time.strftime("%d/%m/%Y")

fecha = fechaActual
nombre = 'Youssef Abarca'
edad = 25
genero = 'M'
peso = 50
talla = 165
ocupacion = 'Técnico'

dirLAM = '~\\Documents\\LAM\\'
dirVoltario = dirLAM + nombre + '\\'
dirImagen = dirVoltario + 'Imagenes\\'

directorio=os.path.expanduser(dirLAM)
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

nombreImagenAnterior = 'Anterior'+'_'+time.strftime("%Y%m%d")+'_'+time.strftime("%H%M%S")

anguloTolerancia = 0.0
distanciaTolerancia = 0.0

resultadosAnterior = evaluacionAnterior()

dataTablaAnterior = pd.DataFrame(resultadosAnterior)
print(dataTablaAnterior.T)

nombrePDF = generarReporte(resultadosAnterior)


direccionImagen='=HYPERLINK("'+imgVoluntario + nombreImagenAnterior+'.jpg","'+nombreImagenAnterior+'")'
direccionReporte='=HYPERLINK("'+carpetaVoluntario + nombrePDF +'.pdf","'+nombrePDF+'")'

encabezadoAnterior = pd.DataFrame([], ['Fecha', 'Nombre', 'Edad', 'Género', 'Peso[kg]', 'Talla[cm]', 'Ocupación',
                            'Hombro Descendido', 'Ángulo del hombro',
                            'Pelvis Descendida', 'Ángulo de la Pelvis',
                            'Rodilla Descendida', 'Ángulo de Rodilla',
                            'Dirección de la Frente', 'Distancia de la Frente',
                            'Dirección de los Hombros', 'Distancia de los Hombros',
                            'Dirección del Ombligo','Distancia del Ombligo',
                            'Dirección de la Pelvis','Distancia de la Pelvis',
                            'Dirección de las Rodillas','Distancia de las Rodillas',
                            'Dirección de los Pies','Distancia de los Pies',
                            'Rotación Pie Izquierdo', 'Ángulo Pie Izquierdo',
                            'Rotación Pie Derecho', 'Ángulo Pie Derecho','Dirección Imagen',
                            'Dirección del Reporte'])

encabezadoDatos = pd.DataFrame([fecha, nombre, edad, genero, peso, talla, ocupacion])

if os.path.exists(dirDBxlsx) == False:
    book = pd.ExcelWriter(dirDBxlsx)
    pd.DataFrame().to_excel(book, 'Anterior')
    pd.DataFrame().to_excel(book, 'Posterior')
    pd.DataFrame().to_excel(book, 'LateralD')
    book.save()

book = load_workbook(dirDBxlsx)
time.sleep(1)

nCeldasAnterior = len(pd.read_excel(dirDBxlsx, sheet_name=0))
nCeldasPosterior = len(pd.read_excel(dirDBxlsx, sheet_name=1))
nCeldasLateralD = len(pd.read_excel(dirDBxlsx, sheet_name=2))

with pd.ExcelWriter(dirDBxlsx, engine='openpyxl') as writer:
    writer.book = book
    writer.sheets = dict((ws.title, ws) for ws in book.worksheets)

    encabezadoAnterior.T.to_excel(writer, 'Anterior',
                                  header=True, index=False, startrow=0, startcol=0)
    encabezadoDatos.T.to_excel(writer, 'Anterior',
                          header=False, index=False, startrow=nCeldasAnterior+1, startcol=0)
    dataTablaAnterior.T.to_excel(writer, 'Anterior',
                                         header=False, index=False, startrow=nCeldasAnterior+1, startcol=7)
    pd.DataFrame({'link':[direccionImagen]}).T.to_excel(writer, 'Anterior',
                                         header=False, index=False, startrow=nCeldasAnterior+1, startcol=29)
    pd.DataFrame({'link':[direccionReporte]}).T.to_excel(writer, 'Anterior',
                                         header=False, index=False, startrow=nCeldasAnterior+1, startcol=30)
    time.sleep(1)

    encabezadoAnterior.T.to_excel(writer, 'Posterior',
                                  header=True, index=False, startrow=0, startcol=0)
    encabezadoDatos.T.to_excel(writer, 'Posterior',
                          header=False, index=False, startrow=nCeldasPosterior+1, startcol=0)
    dataTablaAnterior.T.to_excel(writer, 'Posterior',
                                         header=False, index=False, startrow=nCeldasPosterior+1, startcol=7)
    time.sleep(1)

    encabezadoAnterior.T.to_excel(writer, 'LateralD',
                                  header=True, index=False, startrow=0, startcol=0)
    encabezadoDatos.T.to_excel(writer, 'LateralD',
                          header=False, index=False, startrow=nCeldasLateralD+1, startcol=0)
    dataTablaAnterior.T.to_excel(writer, 'LateralD',
                                         header=False, index=False, startrow=nCeldasLateralD+1, startcol=7)
    time.sleep(1)
    writer.save()

print('LISTOOOOOOOO')
input()

