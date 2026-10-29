---
title: "Sistema LAM"
subtitle: "Guía de uso del aplicativo de evaluación postural"
lang: es
date: "Versión 0.4 · octubre de 2026"
toc: true
toc-title: "Contenido"
---

# Qué es el Sistema LAM

El Sistema LAM (Lectura Automática de Marcadores) es una aplicación para hacer **evaluaciones posturales por
fotogrametría en el plano**. A partir de fotografías del paciente en cuatro vistas (anterior, posterior, lateral
derecha y lateral izquierda), ubica los puntos anatómicos de referencia y calcula los ángulos y las distancias de
cada segmento corporal respecto a la horizontal y a la vertical.

El objetivo es que el resultado no dependa de la estimación visual del evaluador. El fisioterapeuta revisa y,
si hace falta, corrige la ubicación de los puntos, y el sistema hace las mediciones de forma reproducible.

La aplicación ofrece dos formas de detectar los puntos:

- **Sin marcadores:** un modelo de inteligencia artificial (MediaPipe) reconoce el cuerpo en la foto y propone los
  puntos. Los puntos que no se pueden ver directamente se estiman y aparecen resaltados para que el evaluador los
  revise. La escala se calcula con la estatura del paciente.
- **Con marcadores verdes:** el método original de la tesis. Se colocan marcadores adhesivos verdes sobre los
  puntos anatómicos y dos referencias (R1 y R2) separadas 100 cm, y el sistema los detecta por color.

Con los resultados, la aplicación genera un **reporte PDF**, guarda un **historial por paciente** que permite
comparar evaluaciones en el tiempo, y exporta todo a **Excel**.

> El Sistema LAM es una herramienta de apoyo. La interpretación clínica y el diagnóstico corresponden al
> fisioterapeuta.

# Requisitos

| Elemento | Requisito |
|---|---|
| Computador | Windows 10 u 11, 8 GB de RAM recomendados |
| Navegador | Google Chrome o Microsoft Edge actualizados |
| Internet | Solo la primera vez que se inicia la aplicación (descarga de componentes) |
| Cámara | Celular o cámara de fotos, idealmente en trípode |
| Espacio | Fondo liso, buena luz, 3 m libres entre la cámara y el paciente |

# Instalar e iniciar la aplicación

## En un equipo nuevo (paquete portable)

1. Copie la carpeta **SistemaLAM** (o descomprima **SistemaLAM.zip**) en el equipo, por ejemplo en
   `C:\SistemaLAM`. Evite carpetas sincronizadas con la nube, como OneDrive.
2. Haga doble clic en **Iniciar LAM.bat**.
3. La primera vez se abre una ventana negra que descarga los componentes necesarios. Puede tardar unos minutos y
   requiere internet. Las siguientes veces arranca en segundos y sin internet.
4. El navegador se abre solo en `http://localhost:8000`. Si no se abre, escriba esa dirección en Chrome o Edge.

> **No cierre la ventana negra mientras usa la aplicación.** Es el servidor de la app. Para terminar, cierre esa
> ventana.

La aplicación funciona solo en ese equipo: no se publica en internet. Los datos se guardan en la carpeta
**datos**, junto a **Iniciar LAM.bat**.

## En el equipo de desarrollo

Quien mantiene el proyecto puede generar el paquete portable con:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\empaquetar.ps1
```

El resultado queda en `dist_portable\SistemaLAM.zip`. Para trabajar en el código se usan dos terminales:

```powershell
cd backend
uv run fastapi dev app/main.py
```

```powershell
cd frontend
npm run dev
```

# Recorrido por la pantalla

La barra superior tiene cinco secciones:

| Sección | Para qué sirve |
|---|---|
| **Evaluación** | Hacer una evaluación nueva: paciente, fotografías, revisión de puntos y guardado. |
| **Guía de captura** | Cómo tomar las fotografías (distancia, altura, ropa, referencias). |
| **Puntos** | Diccionario de los 33 puntos anatómicos: definición, ubicación y mediciones en las que se usa cada uno. |
| **Pacientes** | Fichas de pacientes, historial de evaluaciones, comparación y exportación a Excel. |
| **Configuración** | Datos del centro para el reporte y parámetros del análisis. |

# Primeros pasos: configuración

Antes de la primera evaluación, entre a **Configuración**.

## Datos del centro

Estos datos aparecen en el encabezado del reporte PDF:

- **Logo:** pulse *Subir logo* y elija una imagen PNG o JPG. Se recomienda un logo horizontal con fondo
  transparente.
- **Nombre del centro** y **contacto** (dirección, teléfono o correo).
- **Evaluador por defecto:** el nombre que se propone en cada evaluación. Se puede cambiar en cada una.

Pulse **Guardar datos**.

## Parámetros del análisis

| Parámetro | Valor inicial | Qué hace |
|---|---|---|
| Ángulo de tolerancia | 1° | Las desviaciones angulares menores se informan como «Alin.» (alineado). |
| Distancia de tolerancia | 0,5 cm | Los desplazamientos menores respecto a la vertical se informan como alineados. |
| Tamaño de la cuadrícula | 5 cm | Separación de las líneas de la cuadrícula sobre la foto. |
| Umbral del filtro verde | 0,32 | Solo con marcadores verdes: sensibilidad de la detección de color. |
| Umbral automático | Activado | Si con el umbral configurado faltan o sobran marcadores, el sistema prueba otros valores. |

Estos parámetros se guardan en el navegador y se aplican a las evaluaciones nuevas. Cada evaluación guardada
conserva las tolerancias con las que se hizo.

# Pacientes

## Registrar un paciente

Hay dos formas:

- En **Pacientes**, pulse **Nuevo paciente**.
- Durante una evaluación, pulse **Seleccionar paciente** y luego **Registrar nuevo paciente**.

Complete el nombre, la edad, el género, la estatura, el peso y la ocupación. Solo el nombre es necesario, pero la
**estatura** se usa como escala en el modo sin marcadores, así que conviene medirla.

## Ficha del paciente

En **Pacientes**, pulse el nombre de un paciente para abrir su ficha. Desde ahí puede:

- **Editar** sus datos.
- Iniciar una **Nueva evaluación** con el paciente ya seleccionado.
- Ver sus **evaluaciones**, abrir el **reporte PDF** de cada una o eliminarla.
- **Comparar** sus evaluaciones en el tiempo (ver «Historial y comparación»).
- Exportar sus datos a **Excel**.
- **Eliminar al paciente**, con todas sus evaluaciones y fotografías. Esta acción no se puede deshacer.

## Paciente de demostración

Para conocer la aplicación o presentarla, en **Pacientes** pulse **Cargar paciente de demostración**. Se crea un
paciente ficticio con dos evaluaciones separadas por tres meses, hechas con siluetas dibujadas (no son fotos de una
persona real). Sirve para mostrar el historial, la comparación y el reporte. Puede eliminarlo como cualquier otro
paciente.

# Tomar las fotografías

La calidad de las fotos define la calidad de los resultados. La sección **Guía de captura** de la aplicación tiene
el protocolo completo; en resumen:

**Cámara**

- En trípode, en posición vertical y **sin zoom**.
- A la altura de la cadera del paciente (90–100 cm del suelo) y nivelada.
- A 2,5–3 m del paciente, de modo que el cuerpo entero entre con margen sobre la cabeza y bajo los pies.
- Misma distancia, altura y lugar en todas las vistas y en los controles.

**Espacio**

- Fondo liso y claro, luz pareja, sin contraluz.
- Algo vertical visible en la foto (marco de una puerta, esquina, plomada) para nivelar la imagen.

**Paciente**

- Ropa ajustada o deportiva corta que deje ver hombros, cadera y rodillas. Descalzo y con el cabello recogido.
- Postura habitual y relajada, con los pies separados al ancho de la cadera.
- Debe autorizar la toma y el almacenamiento de sus fotografías.

**Las cuatro vistas**

| Vista | Posición |
|---|---|
| Anterior | De frente a la cámara, mirada al horizonte, brazos relajados. |
| Posterior | De espaldas a la cámara. |
| Lateral derecha | Lado derecho hacia la cámara: el paciente mira hacia la derecha de la foto. |
| Lateral izquierda | Lado izquierdo hacia la cámara: el paciente mira hacia la izquierda de la foto. |

**Con marcadores verdes**, además: marcadores sobre los puntos anatómicos de cada vista y las referencias R1 y R2
separadas exactamente 100 cm, **en el mismo plano que el paciente** (no en la pared del fondo, porque eso exagera
la escala).

# Realizar una evaluación

Entre a **Evaluación**.

## 1. Datos de la sesión

1. **Paciente:** pulse *Seleccionar paciente*, búsquelo por nombre o regístrelo.
2. **Detección:** elija *Sin marcadores* o *Marcadores verdes*.
3. **Estatura** (solo sin marcadores): se completa con la de la ficha del paciente; corríjala si la midió de nuevo.

## 2. Cargar las fotografías

Las vistas están en pestañas: *Anterior*, *Posterior*, *Lateral derecha* y *Lateral izquierda*. No es obligatorio
usar las cuatro.

En cada pestaña, pulse **Cargar fotografía** y elija la foto. El sistema la analiza en unos segundos y muestra los
puntos sobre la imagen, con la cuadrícula y las líneas de referencia en rojo. Al lado aparecen el diagnóstico y las
tablas de resultados.

La marca de cada pestaña indica su estado:

- Círculo vacío: sin fotografía.
- Número en ámbar: puntos estimados por revisar.
- Punto verde: vista revisada.

## 3. Revisar y corregir los puntos

Cada color tiene un significado:

| Color | Significado |
|---|---|
| Verde azulado | Punto detectado. |
| Ámbar | Punto estimado: debe revisarse. |
| Morado (cuadrado) | Vértice (parte superior de la cabeza) y Suelo (apoyo de los talones): definen la escala. |
| Azul (cuadrado) | Extremos de la línea vertical de referencia. |
| Rojo | Plomada y horizontal de referencia de la cuadrícula; las «×» son centros calculados. |

Para corregir un punto, **arrástrelo** hasta la referencia anatómica correcta. Al soltarlo, las tablas se
recalculan. Si toca un punto, se abre su ficha con la definición anatómica, para confirmar dónde debe ir.

Un punto estimado deja de estar en ámbar cuando lo mueve. Si ya estaba bien ubicado, selecciónelo y pulse
**Confirmar ubicación**.

En el modo sin marcadores revise también:

- **Vértice y Suelo:** en lo alto de la cabeza y en el apoyo de los talones. De ellos y de la estatura sale la
  escala en centímetros.
- **Línea vertical:** active *Línea vertical* y coloque sus dos extremos sobre algo vertical de la escena (el marco
  de una puerta, por ejemplo). La aplicación corrige así la inclinación de la cámara, y la cuadrícula se alinea con
  la vertical real.

## 4. Herramientas del visor

| Acción | Cómo hacerla |
|---|---|
| Acercar o alejar | Rueda del mouse sobre la foto, pellizco en pantallas táctiles, o botones − y + |
| Acercar en un punto | Doble clic sobre el fondo |
| Moverse por la foto ampliada | Arrastrar el fondo (no un punto) |
| Ver la foto completa | Botón de pantalla completa o tecla 0 |
| Lupa | Aparece sola al arrastrar un punto: zona ampliada con una mira |
| Ajuste fino | Seleccione un punto y use las flechas: 1 píxel por pulsación, 10 con Mayús |
| Brillo y contraste | Botón de controles deslizantes: ayuda a distinguir relieves óseos |
| Ocultar cuadrícula o nombres | Botones de cuadrícula y de etiqueta |

## 5. Guardar la evaluación

Al final de la página:

1. Escriba las **Observaciones** (motivo de consulta, hallazgos, indicaciones). Aparecen en el reporte.
2. Revise el nombre del **Evaluador**.
3. Marque la casilla de **consentimiento del paciente**. Es obligatoria para guardar.
4. Pulse **Guardar evaluación**.

Se abre la evaluación guardada, con la imagen de cada vista, los resultados y los botones del reporte PDF.

> Si quedan puntos estimados sin revisar, la evaluación igual se puede guardar, pero el reporte lo advierte.

# Interpretar los resultados

## Abreviaturas

| Abreviatura | Significado |
|---|---|
| Der. / Izq. | Desviación hacia la derecha / izquierda del paciente (o lado descendido) |
| Alin. | Alineado: dentro de la tolerancia configurada |
| Ant. / Pos. | Desplazamiento anterior / posterior respecto a la vertical |
| Rot.Ext. / Rot.Int. | Rotación externa / interna del pie |
| Valgo / Varo | Desviación de la rodilla o del pie |

## Tablas por vista

**Vista anterior**

- *Grados con respecto a la horizontal:* hombros, pelvis y rodillas. Valor ideal 0°.
- *Distancia con respecto a la vertical:* frente, hombros, ombligo, pelvis, rodillas y pies respecto a la línea
  media entre los tobillos. Valor ideal 0 cm.
- *Grados de rotación de los pies:* valor ideal 0°.
- Diagnóstico: línea escapular y pélvica descendidas, inclinación y rotación de la cabeza, valgo o varo de rodillas.

**Vista posterior**

- *Grados con respecto a la horizontal:* hombros, pelvis y rodillas.
- *Distancia con respecto a la vertical:* hombros, 7.ª cervical, 5.ª torácica, pelvis, rodillas y tobillos.
- *Pie varo o valgo.*
- Diagnóstico: rotación dorsal y pélvica, y alineación de cada pie.

**Vistas laterales**

- *Grados con respecto a la vertical:* cabeza-hombro, hombro-pelvis, cadera-rodilla y rodilla-pies.
- *Grados con respecto a la horizontal:* inclinación pélvica entre EIAS y EIPS. Normal: 10° ± 5°.
- *Distancia con respecto a la vertical:* cabeza, hombros, pelvis, caderas y rodillas respecto a la plomada que
  pasa por el pie.
- Diagnóstico: tipo de postura (ideal, cifolordótica, espalda plana, espalda arqueada, cabeza hacia delante,
  lordótica o tipo militar, anteversión o retroversión pélvica) y proyección postural.

> En el modo sin marcadores, la inclinación pélvica lateral depende de la ubicación de EIAS y EIPS, que el modelo
> estima. Revise siempre esos dos puntos antes de interpretar el tipo de postura.

# Evaluaciones guardadas

Abra una evaluación desde la ficha del paciente. Verá la imagen de cada vista con los puntos y la cuadrícula, el
diagnóstico, las tablas, las observaciones y el evaluador.

## Reporte PDF

- **Ver reporte:** lo abre en el navegador, desde donde se puede imprimir.
- **Descargar PDF:** lo guarda en el equipo.

El reporte tiene una portada con los datos del centro, del paciente, los parámetros de la evaluación, el resumen
del diagnóstico y las observaciones. Luego trae una página por vista, con la imagen y las tablas. Se genera con los
datos actuales: si se corrige la evaluación, el reporte se actualiza.

## Corregir puntos

Si después de guardar nota que un punto quedó mal ubicado:

1. Abra la evaluación y pulse **Corregir puntos**.
2. Mueva los puntos con las mismas herramientas del visor. También puede cambiar la estatura (sin marcadores), la
   línea vertical, las observaciones y el evaluador.
3. Pulse **Guardar correcciones**.

Se conservan la fecha, la foto y las tolerancias originales (y, con marcadores, la escala de R1 y R2). Los
resultados, la imagen y el reporte se recalculan.

## Eliminar una evaluación

En la ficha del paciente, pulse el ícono de papelera de la evaluación y confirme. Se borran también sus
fotografías.

# Historial y comparación

Cuando un paciente tiene dos o más evaluaciones con la misma vista, su ficha muestra **Comparación en el tiempo**:

1. Elija la vista con los botones (Anterior, Posterior, Lateral derecha…).
2. La tabla muestra cada medición en columnas por fecha y, al final, el **cambio** entre la primera y la última
   evaluación.
3. Las primeras filas comparan el diagnóstico (por ejemplo, el tipo de postura).

Los valores conservan el signo de la medición: un cambio negativo en un ángulo que era positivo indica que se
acercó a 0°.

# Exportar a Excel

- **Todos los pacientes:** en **Pacientes**, pulse **Exportar a Excel**.
- **Un paciente:** en su ficha, pulse **Excel**.

El libro tiene una hoja por vista (Anterior, Posterior, LateralD y LateralI) con una fila por evaluación:

- enlaces al reporte PDF y a la imagen;
- datos de la evaluación (número, fecha, modo, evaluador) y del paciente;
- diagnóstico;
- cada medición con su dirección y su valor.

Los enlaces funcionan mientras la aplicación esté abierta en ese equipo.

# Diccionario de puntos

La sección **Puntos** describe los 33 puntos anatómicos: definición, cómo ubicarlo por palpación u observación,
una figura con su posición y las mediciones y diagnósticos que dependen de él. Es la misma ficha que aparece al
tocar un punto en el visor.

| Vista | Puntos |
|---|---|
| Anterior (F1–F14) | Entrecejo, mentón, acromioclaviculares, horquilla esternal, ombligo, EIAS, rótulas, tobillos (línea media del plano frontal) y dedos gordos |
| Posterior (P1–P12) | 7.ª vértebra cervical, 5.ª vértebra dorsal, acromioclaviculares, EIPS, huecos poplíteos, tendones de Aquiles y calcáneos |
| Laterales (L1–L7) | Oído, acromioclavicular, EIAS, EIPS, trocánter mayor, tuberosidad tibial y articulación transversal del tarso |

# Datos y privacidad

- Todo se guarda **en el equipo**, en la carpeta **datos** junto a **Iniciar LAM.bat**: la base de datos
  (`lam.db`), las fotografías y los datos del centro. Nada se envía a internet. El análisis sin marcadores corre en
  el propio navegador.
- **Respaldo:** cierre la aplicación y copie la carpeta **datos** a un disco externo. Para restaurar, vuelva a
  colocarla junto a **Iniciar LAM.bat**.
- **Borrar todo** (por ejemplo, después de una demostración): cierre la aplicación y elimine la carpeta **datos**.
- Las fotografías son datos personales de salud. Pida siempre el consentimiento del paciente (la aplicación lo
  registra al guardar), proteja el equipo con contraseña y elimine los datos de un paciente cuando lo solicite.

# Solución de problemas

| Problema | Qué hacer |
|---|---|
| No se abre el navegador | Escriba `http://localhost:8000` en Chrome o Edge. Si el puerto está ocupado, la ventana negra indica otra dirección (8001, 8002…). |
| La ventana negra se cierra con error la primera vez | Verifique la conexión a internet y vuelva a abrir **Iniciar LAM.bat**. |
| Windows muestra «Windows protegió su PC» | Pulse *Más información* y luego *Ejecutar de todas formas*. |
| «No se pudo analizar la fotografía» sin marcadores | El cuerpo entero debe verse en la foto, con buena luz y sin otras personas. Pruebe con otra foto. |
| Con marcadores: «Existen menos (o demasiados) puntos» | Revise que se vean todos los marcadores y R1/R2. Ajuste el umbral del filtro verde en Configuración o deje activo el umbral automático. |
| Los resultados en centímetros parecen exagerados | Sin marcadores: verifique la estatura y los puntos Vértice y Suelo. Con marcadores: R1 y R2 deben estar en el plano del paciente. |
| Un punto estimado está lejos de su lugar | Arrástrelo con ayuda del zoom y la lupa. Toque el punto para ver dónde debe ubicarse. |
| La foto se ve inclinada | Active *Línea vertical* y colóquela sobre algo vertical de la escena. |

# Anexo: convertir esta guía a PDF

Con [Pandoc](https://pandoc.org) instalado, desde la carpeta del proyecto:

```powershell
pandoc docs\GUIA_DE_USO.md -s --toc --toc-depth=1 --css docs\guia\estilo.css --embed-resources -o docs\GUIA_DE_USO.html
```

Abra `docs\GUIA_DE_USO.html` en Chrome o Edge y use **Imprimir → Guardar como PDF** (tamaño A4, con «Gráficos de
fondo» activado). Guárdelo como `docs\GUIA_DE_USO.pdf`: el script de empaquetado lo incluye en el paquete
portable.
