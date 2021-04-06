# Lectura Automática de Marcadores (LAM) para realizar evaluaciones posturales V0.1

![](https://i.imgur.com/KRPTibG.png)

En la práctica clínica, las evaluaciones de la postura se realizan como parte del examen físico. Cuando se realizan en la clínica, las evaluaciones posturales son a menudo subjetivas, y las anormalidades son inspeccionadas visualmente. Esta forma de evaluación cualitativa tiene baja sensibilidad, así como baja confiabilidad. Depende en gran medida de experiencias pasadas y de interpretaciones subjetivas. En consecuencia, se requieren instrumentos estandarizados y validados para realizar evaluaciones más precisas y sistemáticas. La postura puede evaluarse cualitativa y cuantitativamente a través de la interpretación rigurosa de imágenes fotográficas que también pueden usarse para monitorear los resultados del tratamiento. Las mediciones cuantitativas permiten a los médicos e investigadores no sólo realizar una evaluación precisa de los cambios posturales, sino también controlar la mejoría. Sin embargo, más estudios son necesarios para validar y estimar la fiabilidad de cada uno de estos sistemas.

**Tabla de contenidos**

[TOC]

## Descripción
La finalidad de este proyecto es proponer un sistema para realizar evaluaciones posturales que, a diferencia del método tradicional donde los fisioterapeutas miden o estiman manualmente las alineaciones de los segmentos corporales, el resultado de la evaluación no esté condicionado por la subjetividad del evaluador. Se desarrolló una aplicación de evaluación postural mediante el uso de la fotogrametría en el plano, con la finalidad de automatizar el registro, cuantificación y evaluación de parámetros posturales. El desarrollo de la aplicación se realizó usando Python 3.8. Para el análisis fotogramétrico se consideró el plano frontal en la vista anterior y en la vista posterior, y el plano sagital en la vista lateral derecha. El sistema desarrollado realiza una “lectura automática de marcadores” (LAM) mediante la filtración y segmentación de marcadores en imágenes fotográficas. Una vez ubicados los marcadores en el plano con el uso de las funciones se obtienen los resultados en tablas, donde se encuentra la información de interés para que el fisioterapeuta pueda dar un diagnóstico.

# Metodología
Las etapas de las cuales consta el proyecto son la definición de los puntos anatómicos, la captura de fotografías, el desarrollo de la aplicación y la forma en la cual se presenta la información.

![](https://i.imgur.com/tATWCAx.png)

Se definieron los puntos anatómicos de interés para realizar evaluaciones posturales, además de definir la información requerida por el fisioterapeuta para dar un diagnóstico. En la siguiente etapa se establece el protocolo para la captura de fotografías, donde los principales recursos que se analizaron son la altura de la cámara, distancia entre el participante y la cámara, y la iluminación del espacio. En la etapa de desarrollo se realizó principalmente la preparación de las imágenes incluyendo esto la filtración y segmentación, posteriormente se desarrollaron las funciones que permiten la obtención de los parámetros posturales. Por último, en la etapa final se estableció presentar los parámetros posturales en un formato de informe PDF, además de adjuntar los mismos en una base de datos de Excel.
## Definición de Puntos Anatómicos
Una vez realizado el estado del arte sobre aplicaciones y métodos que existen para llevar a cabo una evaluación postural, en especial los artículos donde se definieron qué puntos anatómicos son considerados importantes en una evaluación fotogramétrica de la postura, los puntos anatómicos que se consideraron para el desarrollo del sistema LAM son:

![](https://i.imgur.com/UNplCes.jpg)

| Vista anterior del plano frontal | Vista posterior del plano frontal | Vista lateral derecha | 
| :--------|:---------------| :-----|
| F1: Entrecejo | P1: Apófisis espinosa de la 7ma vértebra cervical | L1: Oído |
| F2: Mentón | P2: Apófisis espinosa de la 5ta vértebra dorsal | L2: Articulación acromioclavicular |
| F3: Articulación acromioclavicular derecha | P3: Articulación acromioclavicular derecha | L3: Espina ilíaca anterosuperior |
| F4: Articulación acromioclavicular izquierda | P4: Articulación acromioclavicular izquierda | L4: Espina ilíaca posterosuperior |
| F5: Horquilla del manubrio esternal | P5: Espina ilíaca posterosuperior derecha | L5: Trocánter mayor del fémur |
| F6: Ombligo | P6: Espina ilíaca posterosuperior izquierda | L6: Tuberosidad tibial |
| F7: Espina ilíaca anterosuperior derecha | P7: Hueco poplíteo derecho | L7: Articulación transversal del tarso |
| F8: Espina ilíaca anterosuperior izquierda | P8: Hueco poplíteo izquierdo |   
| F9: Rótula derecha | P9: Tendón de Aquiles derecho |   
| F10: Rótula izquierda | P10: Tendón de Aquiles izquierdo |  
| F11: Tobillo derecho | P11: Calcáneo derecho |   
| F12: Tobillo izquierdo | P12: Calcáneo izquierdo | 
| F13: Dedo gordo derecho | 
| F14: Dedo gordo izquierdo |

Se ubicaron dos marcadores adicionales que sirven como referencia al momento de cuadrar la imagen y obtener el factor de escala para transformar los píxeles a centímetros. Estos puntos adicionales están ubicados uno a cada lado de la persona y separados con una distancia de 100 centímetros (R1 y R2).
## Captura de Fotografías
Para la captura de fotografías, los principales aspectos que se deben analizar son la altura de la cámara, distancia entre el participante y la cámara, y la iluminación del espacio

![](https://i.imgur.com/6C6T9Qo.png)

Se colocan los marcadores sobre la persona (etiquetas verdes circulares) junto con los dos marcadores de referencia. La cámara se posicionó de forma paralela a la persona a una distancia de 2.50 metros y colocando el lente de la cámara a una altura de 1.10 metros. Las fotografías deben ser tomadas con una iluminación mínima de 200 lux. La resolución de la cámara a utilizar tiene que ser superior o igual a los 12 megapíxeles (Mpx) y el modo de configuración estar en automático.
## Tablas de resultados
Con los puntos anatómicos definidos se establecieron los resultados requeridos por el fisioterapeuta para que este pueda dar un diagnóstico. Los datos requeridos se muestran en tablas, los formatos de las tablas de resultados para cada una de las vistas a analizar fueron propuestos por el centro **HABILITAR Cuenca-Ecuador**.
**Tabla de resultados para la vista anterior, plano frontal**
Para los resultados de esta tabla, en la primera parte el parámetro descendido representa cuál de los dos lados de la vista anterior (derecho o izquierdo) esta descendido o si estos se encuentran alineados. En la segunda parte el parámetro dirección representa la inclinación del segmento corporal o la del punto de referencia, si este está a la derecha, izquierda o alineado con respecto a la línea vertical de referencia. Por último, el parámetro dirección de la tercera parte representa si el pie tiene una rotación externa o interna.

| Segmento Corporal | Descendido | Ángulo | 
| :--------|:---------------| :-----|
| Hombros |||
| Pelvis |||
| Rodilla |||
| **Referencia** | **Dirección** | ** Distancia ** |
| Frente|||
| Hombros|||
| Ombligo|||
| Pelvis|||
| Rodillas|||
| Pies|||
| ** Segmento Corporal ** | **Dirección** | **Ángulo** |
| Pie Izquierdo|||
| Pie Derecho||||

** Tabla de resultados para la vista posterior, plano frontal**

Los parámetros de la parte uno y dos de esta tabla, se representan de igual manera que la tabla anterior. En la tercera parte de esta tabla se indica si la persona tiene un pie varo o valgo.

| Segmento Corporal | Descendido | Ángulo | 
| :--------|:---------------| :-----|
| Hombros |||
| Pelvis |||
| Rodilla |||
| **Referencia** | **Dirección** | ** Distancia ** |
| Hombros |||
| 7ma Cervical |||
| 5ta Torácica |||
| Pelvis |||
| Rodillas |||
| Tobillos |||
| ** Segmento Corporal ** | **Dirección** | **Ángulo** |
| Pie Izquierdo|||
| Pie Derecho||||


**Tabla de resultados para la vista lateral derecha, plano sagital**
En los resultados de esta tabla el parámetro dirección representan si la inclinación del segmento corporal o la del punto de referencia es anterior, posterior o está alineada con respecto a la línea vertical de referencia. Los ángulos de todas las tablas se muestran en grados y las distancias en centímetros.

| Segmento Corporal | Dirección | Ángulo | 
| :--------|:---------------| :-----|
| Cabeza-Hombro |||
| Hombro-Pelvis |||
| Caderas-Rodillas |||
| Rodillas-Pies |||
| ** Segmento Corporal ** | **Dirección** | ** Ángulo ** |
| Pelvis |||
| ** Referencia ** | **Dirección** | ** Distancia ** |
| Cabeza |||
| Hombro |||
| Pelvis |||
| Cadera |||
| Rodilla ||||

Nota: Para un mejor análisis cuantitativo los resultados mostrados en la tabla cuentan con signos. Los signos negativos representan valores con inclinación a la izquierda, posteriores, de rotación interna y pie varo. Independientemente de los valores de tolerancia de ángulos y distancias que se hayan asignado.

## Recomendaciones
- La colocación de los marcadores se debe realizar manualmente por un evaluador experimentado, debido a que hay ciertos puntos anatómicos difíciles de ubicar para una persona inexperta en el tema, como son los puntos F7, F8, P6, P5 y L5 por mencionar algunos. Para otros puntos como F3, F4, F7 y P5 se recomienda que en vez de usar marcadores adhesivos se usen bolitas plásticas de color verde, debido a que estos puntos están presentes en más de una vista.
- Se recomienda que el protocolo de colocación de la cámara dependa del tipo de lente que se utilice, y que para posicionar la cámara se use niveladores, de preferencia alguno que venga integrado en la cámara, o aplicaciones que permitan ajustar el nivel de la cámara en el caso de utilizar celular. Para el correcto posicionamiento de la cámara y una toma de fotografías correcta se recomienda posicionar la cámara a una distancia prudente (alrededor de los 2.50 y 3.00 metros) y el lente a una altura donde se aprecie de manera clara todos los marcadores. Los marcadores de referencia deben ubicarse a una altura media de la persona que se va a realizar la evaluación. La resolución de la cámara deberá ser mayor a los 12 Mpx y no se debe utilizar ningún tipo de lente que genere alguna distorsión, como es el caso de los lentes de las cámaras deportivas. 
- De preferencia se recomienda usar un fondo blanco para la toma de fotografías, tomarlas en un lugar bien iluminado y de ser necesario tomar las fotos con flash o ajustar la cámara en modo automático. El ambiente en el cual se tomen las fotografías no tiene que tener ninguna tonalidad de verde.
- Las personas que se vayan a realizar la evaluación postural mediante el sistema propuesto tienen que usar prendas ajustadas al cuerpo, en caso de ser hombres una licra negra corta, y en el caso de las mujeres un top negro y una licra negra corta, en caso de tener el cabello largo este deberá ser recogido. Los participantes no pueden tener ningún tipo de prenda u objeto con colores fluorescentes, debido a que algunos de estos pueden contener un alto contenido del canal verde, como es el caso del celeste, y pueden presentarse problemas al momento de realizar las evaluaciones. 
- Las personas que se sometan a esta evaluación deben mantener una postura en la cual se sientan cómodos y no forzar una postura correcta. Hacer eso provocaría una distorsión de los resultados de la evaluación.

# Instalación
El sistema LAM fue realizado en Python 3.8 con el uso de las siguientes librerías:
                    
Liberia   | Versión
------------- | -------------
arrow | 1.0.3
matplotlib | 3.3.3
numpy | 1.19.4
openpyxl | 3.0.7
scikit-image | 0.18.1
pandas | 1.2.3
reportlab | 3.5.65  
tkinter | 8.6

Y las librerías estándar de Python 3.8: **warnings, datetime, time, os.**
Para crea un ejecutable se utilizó la librería **pyinstaller 4.2** agregando los **hooks** faltantes de la librería **scikit-image** para su correcta ejecución.
# Cómo usar
Actualmente el sistema se ejecuta en la consola usando ventanas emergentes para realizar el cargado de las fotografías, y en caso de existir algún error mostrar la fotografía para que el usuario pueda visualizar el error en la lectura de los marcadores.
1. Una vez ejecutado el programa primeramente se debe llenar la información de la persona sometida a la evaluación.
2. Se ingresan las evaluaciones que se van a realizar.
3. Se Ingresa la tolerancia para etiquetar un segmento corporal o referencia como alineada:

	![](https://i.imgur.com/7TkPLqH.jpg)
	
4. Se muestran las ventanas emergentes para cargar cada una de las fotografías a procesar. En caso de que exista algún error, el sistema nos mostrara cual es el error y si deseamos cargar otra imagen o descartar esa evaluación:

	![](https://i.imgur.com/ZiAIvXe.jpg)
	
5. Una vez terminado el proceso los archivos finales son generados en: 
6. 

> C:\Users\Nombre_de_Usuario\Documents\LAM

Donde se encuentra un archivo con el nombre* DB_LAM.xlsx*  que guarda toda la información y hipervínculos de las evaluaciones realizadas con éxito. Además, se generan las carpetas con los nombres de las diferentes personas que se realizaron las evaluaciones, que en su interior contienen con sus reportes en PDF y las fotografías analizadas.

![](https://i.imgur.com/EdmMuJM.png)

El reporte PDF contendrá la siguiente información:

![](https://i.imgur.com/nzLttwb.jpg)
![](https://i.imgur.com/6Eh22Xk.jpg)
![](https://i.imgur.com/5kagcT3.jpg)
![](https://i.imgur.com/D2VTmDP.jpg)

# Licencia

Las condiciones de uso de este código se encuentran el archivo LICENSE.

