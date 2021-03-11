import matplotlib

matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure

import tkinter as tk
from tkinter import *
from tkinter import messagebox
from tkinter import filedialog
import datetime
from skimage import (data, io, filters, data_dir, 
                     morphology, transform, img_as_ubyte)
import matplotlib.pyplot as plt

#---------VariablesGlobales---------

anterior = []
posterior = []
lateralD = []

#-----------FUNCIONES----------------

def botonCalcular():
    toplevel = Toplevel(raiz)
    toplevel.geometry('300x100')
    toplevel.title('Calculando...')
    toplevel.resizable(0,0)
    toplevel.iconbitmap('icon.ico')
    r_lbl = Label(toplevel,text='\n\nCalculando, por favor espere')
    r_lbl.pack()
    
def botonReporte():
    toplevel = Toplevel(raiz)
    toplevel.geometry('250x100')
    toplevel.title('Reportes')
    toplevel.resizable(0,0)
    toplevel.iconbitmap('icon.ico')
    r_lbl = Label(toplevel,text='\n\nGenerando reportes, espere...')
    r_lbl.pack()
    
def botonLimpiar():
    cuadroNombre.set('')
    cuadroFecha.set(fechaActual)
    cuadroEdad.set('')
    cuadroGenero.set('')
    cuadroPeso.set('')
    cuadroTalla.set('')
    cuadroOcupacion.set('')
    #plt.close(plt.figure(2))
    #plt.show()

def botonCargarA():
    global anterior
    
    fichero=filedialog.askopenfilename(title='Abrir',
            initialdir='C:',filetypes=(('Imagenes','*.jpg'),
            ('Imagenes','*.png'),('Todos los ficheros','*.*')))
    anterior = io.imread(fichero)
    plt.figure(1)
    io.imshow(anterior)
    plt.show()

def botonCargarP():
    global posterior
    
    fichero=filedialog.askopenfilename(title='Abrir',
            initialdir='C:',filetypes=(('Imagenes','*.jpg'),
            ('Imagenes','*.png'),('Todos los ficheros','*.*')))
    posterior = io.imread(fichero)
    plt.figure(2)
    io.imshow(posterior)
    plt.show()
    
def botonCargarL():
    global lateralD
    
    fichero=filedialog.askopenfilename(title='Abrir',
            initialdir='C:',filetypes=(('Imagenes','*.jpg'),
            ('Imagenes','*.png'),('Todos los ficheros','*.*')))
    lateralD = io.imread(fichero)
    plt.figure(3)
    io.imshow(lateralD)
    plt.show()
    
def acercaDe():
    a=messagebox.showinfo('LAM',
                          'LAM esta en construcción\n Version 1.0 en Python')

def salir():
    reSalir = messagebox.askyesno('Salir',
                                    '¿Deseas salir de la aplicación?')
    if reSalir==True:
        plt.close('all')
        raiz.destroy()

#---------------INICIO-----------------#

raiz=Tk()
raiz.title('Análisis Postural LAM')
raiz.resizable(0,0)
try:
    raiz.iconbitmap('icon.ico')
except TclError:
    print ('No ico file found')
#raiz.iconbitmap("icon.ico")
#raiz.geometry('1309x530')
miFrame=Frame()
miFrame.pack(side='left',anchor='n')
miFrame.config(width='882',height='362')
miFrame.config(bd=3,relief='groove')
#miFrame.config(cursor='hand2')

fondo=PhotoImage(file='f2.gif')
Label(miFrame,image=fondo).place(x=0,y=0)
#Label(miFrame, text='Por Youssef Abarca', 
#      fg='red',font=('Comic Sans Ms',24)).place(x=300,y=200)
def __init__(self, parent, controller):
    tk.Frame.__init__(self, parent)
    label = tk.Label(self, text="Graph Page!", font=LARGE_FONT)
    label.pack(pady=10, padx=10)

    button1 = ttk.Button(self, text="Back to Home",
                         command=lambda: controller.show_frame(paginaInicio))
    button1.pack()

    f = Figure(figsize=(5, 5), dpi=100)
    a = f.add_subplot(111)
    a.plot([1, 2, 3, 4, 5, 6, 7, 8], [5, 6, 1, 3, 8, 9, 3, 5])

    canvas = FigureCanvasTkAgg(f, self)
    canvas.draw()
    canvas.get_tk_widget().pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

    toolbar = NavigationToolbar2Tk(canvas, self)
    toolbar.update()
    canvas._tkcanvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
#------------------VARIABLES-------------#

cuadroNombre=StringVar()
cuadroFecha=StringVar()
cuadroEdad=StringVar()
cuadroGenero=StringVar()
cuadroPeso=StringVar()
cuadroTalla=StringVar()
cuadroOcupacion=StringVar()


fecha = datetime.datetime.now()
fechaActual = (str(fecha.day)+'-'+str(fecha.month)
               +'-'+str(fecha.year))

cuadroFecha.set(fechaActual)

#----------BARRA - MENU ----------------#

barraMenu=Menu(raiz)
raiz.config(menu=barraMenu)
ayudaMenu=Menu(barraMenu, tearoff=0)
ayudaMenu.add_command(label='Acerca de...',command=acercaDe)
ayudaMenu.add_command(label='Salir',command=salir)

barraMenu.add_cascade(label='Ayuda',menu=ayudaMenu)

#------------------CUADROS---------------#

Entry(miFrame, justify='center',width='18',
    textvariable=cuadroNombre).place(x=85,y=27)
Entry(miFrame, justify='center',width='18',
    textvariable=cuadroFecha).place(x=85,y=50)
Entry(miFrame, justify='center',width='18',
    textvariable=cuadroEdad).place(x=85,y=73)
Entry(miFrame, justify='center',width='18',
    textvariable=cuadroGenero).place(x=263,y=27)
Entry(miFrame, justify='center',width='18',
    textvariable=cuadroTalla).place(x=263,y=50)
Entry(miFrame, justify='center',width='18',
    textvariable=cuadroPeso).place(x=263,y=73)
Entry(miFrame, justify='center',width='18',
    textvariable=cuadroOcupacion).place(x=445,y=27)

##------------------BOTONES---------------#

Button(miFrame, text='Calcular',width='15',
    command=botonCalcular).place(x=605,y=20)

Button(miFrame, text='Reporte',width='15',
    command=botonReporte).place(x=605,y=50)
    
Button(miFrame, text='Limpiar',width='15',
    command=botonLimpiar).place(x=605,y=80)

Button(miFrame, text='Cargar Imagen',width='15',
    command=botonCargarA).place(x=30,y=125)

Button(miFrame, text='Cargar Imagen',width='15',
    command=botonCargarP).place(x=310,y=125)
    
Button(miFrame, text='Cargar Imagen',width='15',
    command=botonCargarL).place(x=575,y=125)

#---------------FIN---------------#

raiz.mainloop()
