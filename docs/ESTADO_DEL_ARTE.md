# Estado del arte: evaluación postural por fotografía (2026)

Revisión hecha para decidir cómo modernizar el Sistema LAM: pasar de marcadores verdes
a análisis directo de la imagen, con ajuste manual de puntos y cuatro vistas.

## 1. Cómo trabajan las aplicaciones comerciales actuales

**PostureScreen / ROMScreen (PostureCo).** Es la referencia del sector en apps de postura.
- Analiza 1, 2 o 4 vistas (frente, derecha, espalda, izquierda).
- La visión por computador ubica los puntos automáticamente ("auto-digitization"), pero
  el profesional debe revisar y validar cada punto; tiene una guía específica para mover
  los puntos detectados.
- Reporta ángulos y desplazamientos lineales de cada segmento, con líneas de nivel y
  plomada, reportes PDF para el paciente y para el profesional, y comparación entre
  evaluaciones (hasta seis).
- ROMScreen (rango de movimiento: cervical, toraco-lumbar y hombro) dibuja el ángulo sobre
  la foto del paciente, lo calcula automáticamente y el profesional corrige arrastrando
  los puntos. Solo iPhone/iPad, por suscripción.
- Su evidencia publicada es de confiabilidad entre evaluadores (2016, 2018) y validez en
  escoliosis frente a Cobb (2021). El propio fabricante aclara que no es un dispositivo
  médico y que el profesional es responsable de validar las marcas.
- Fuentes: [ROMScreen](https://www.postureanalysis.com/romscreen-range-of-motion-assessment-app/),
  [PostureScreen](https://www.postureanalysis.com/posturescreen-posture-movement-body-composition-analysis-assessment/),
  [investigación de PostureScreen](https://www.postureanalysis.com/posturescreen-research-reliability-and-utility/).

**APECS (Saneftec).** Ofrece tres modos en la misma app: detección automática de
marcadores verdes, detección sin marcadores con puntos preposicionados que el usuario
ajusta (semimanual) y marcación manual. Cuatro vistas, video lateral y reportes PDF. Las
reseñas señalan problemas de usabilidad al mover los puntos, lo que muestra que el editor
de puntos es una parte crítica de la experiencia.
[App Store](https://apps.apple.com/app/id1488264106)

**MORA Vu (EverEx).** Software con IA que ubica 24 puntos anatómicos en fotos 2D sin
marcadores ni calibración. En un estudio piloto (72 pacientes, *Diagnostics* 2025) su
postura adelantada de cabeza correlacionó r ≈ 0.7 con radiografías cervicales y el ángulo
cadera-rodilla-tobillo r = 0.75 con radiografía EOS (sesgo 0.89°, límites −2.8° a 4.6°),
con ICC entre evaluadores de 0.84–0.90. Limitaciones: muestra pequeña, puntos de la IA
que no coinciden con los anatómicos clásicos y conflicto de interés de los autores.
[Artículo](https://www.mdpi.com/2075-4418/15/11/1340)

**Apps de marcación manual validadas.** Por ejemplo, la app de Marmara (*Irish Journal of
Medical Sciences*, 2021): el fisioterapeuta marca los puntos en pantalla, 26 variables,
comparada con BioTonix; confiabilidad intraevaluador aceptable en 81 % de las variables y
entre evaluadores solo en 58 %.
[Publicación](https://openaccess.marmara.edu.tr/entities/publication/1ae25eb2-cdcb-4d1a-87a6-1addb1baf052/full)

**Conclusión del mercado:** el estándar actual es *detección automática + validación y
ajuste obligatorio por el profesional*, con cuatro vistas, reportes y seguimiento en el
tiempo. Es exactamente la dirección propuesta para LAM.

## 2. Modelos de estimación de pose disponibles

| Modelo | Puntos | Licencia | Comentario para LAM |
|---|---|---|---|
| [MediaPipe Pose Landmarker](https://developers.google.com/edge/mediapipe/solutions/vision/pose_landmarker) (Google) | 33 | Apache 2.0 | Corre en el navegador (JavaScript), Python, Android. Modelos lite/full/heavy. Opción más práctica para empezar. |
| [RTMW / RTMPose](https://arxiv.org/abs/2407.08634v1) (MMPose) | 133 (cuerpo, cara, manos, pies) | Repositorio de MMPose (verificar licencia de los pesos) | Mejor precisión abierta en COCO-WholeBody (70.2 mAP). Buena base para reentrenar con puntos propios. |
| [Sapiens](https://huggingface.co/facebook/sapiens-pose-0.6b-torchscript/blob/main/README.md) (Meta) | 308 | CC BY-NC 4.0 (no comercial) | Muy preciso y en alta resolución, pero la licencia impide usarlo en un servicio para centros que pagan. |

**Limitación central:** estos modelos detectan *centros articulares* y rasgos de la cara,
no *puntos anatómicos palpables*. Una revisión en *PeerJ* (Wade et al., 2022) lo resume:
los datos de entrenamiento los etiquetó personal sin formación anatómica, la cadera es el
punto con más error sistemático y en 2D los ángulos del miembro inferior difieren
3–11° de los sistemas con marcadores.
[Revisión](https://peerj.com/articles/12995)

Un estudio de 2026 en Parkinson (*Sensors*) comparó MediaPipe con Azure Kinect en postura
de pie: buena concordancia en tronco, hombros y cadera (error < 2°), pero rodillas
subestimadas 10–12°, desfases grandes en la cabeza y peor desempeño del modelo "heavy".
Recomiendan usar la vista lateral para medidas sagitales y validar contra marcadores antes
del uso clínico.
[Artículo](https://pmc.ncbi.nlm.nih.gov/articles/PMC12944656)

## 3. Qué puntos de LAM cubre un modelo genérico (MediaPipe)

| Vista | Puntos LAM | Equivalente en MediaPipe | Calidad esperada |
|---|---|---|---|
| Anterior | F3/F4 acromioclaviculares | hombros (11/12) | Aproximado (centro articular) |
| | F9/F10 rótulas | rodillas (25/26) | Aproximado |
| | F11/F12 tobillos | tobillos (27/28) | Bueno |
| | F13/F14 dedo gordo | punta del pie (31/32) | Aproximado |
| | F1 entrecejo, F2 mentón | ojos y boca | Estimable por geometría |
| | F5 manubrio, F6 ombligo, **F7/F8 EIAS** | — | Manual |
| Posterior | P3/P4 acromioclaviculares | hombros | Aproximado |
| | P7/P8 hueco poplíteo, P9/P10 Aquiles | rodillas, tobillos | Aproximado |
| | P11/P12 calcáneos | talones (29/30) | Bueno |
| | **P1 C7, P2 T5, P5/P6 EIPS** | — | Manual |
| Laterales | L1 oído, L2 hombro | oreja (7/8), hombro | Bueno / aproximado |
| | L5 trocánter, L6 tuberosidad tibial, L7 tarso | cadera, rodilla, tobillo-pie | Aproximado (con desfase) |
| | **L3 EIPS, L4 EIAS** | — | Manual |

Los puntos de la pelvis (EIAS y EIPS), C7 y T5, que son clave en las tablas de LAM, no
existen en ningún modelo genérico. Por eso un enfoque 100 % automático sin marcadores
**no reproduciría hoy los resultados validados en la tesis**.

## 4. Recomendación para LAM

1. **Detección híbrida con validación obligatoria del profesional** (como PostureScreen y
   APECS). Tres modos sobre el mismo flujo:
   - *Sin marcadores (por defecto):* MediaPipe ubica los puntos que cubre, los demás se
     preposicionan por proporciones corporales y el fisioterapeuta los arrastra.
   - *Con marcadores verdes:* el algoritmo actual, que es el validado; se mantiene para
     quien quiera máxima precisión y, sobre todo, para validar el modo sin marcadores.
   - *Manual:* el profesional ubica todos los puntos.
2. **Escala sin marcadores en el cuerpo.** Opciones: una referencia física en la escena
   (R1/R2 a 100 cm o una tarjeta de calibración tipo ArUco) o la estatura del paciente.
   *Decisión del proyecto: estatura del paciente.* Sin escala solo se pueden reportar
   ángulos, no distancias en cm.
3. **Nivelación sin R1/R2.** Opciones: sensor del celular al tomar la foto, línea vertical
   marcada por el evaluador sobre la escena, detección automática de una plomada, o
   trípode con nivel. *Decisión del proyecto: línea vertical de referencia*, porque sirve
   para cualquier foto. La plomada automática queda como mejora futura.
4. **Cuatro vistas** (anterior, posterior, lateral derecha e izquierda), como el estándar.
5. **Validación antes de usarlo clínicamente:** fotografiar pacientes *con* marcadores y
   comparar el modo sin marcadores contra el detector de marcadores en las mismas fotos
   (error en grados y cm, ICC, Bland-Altman). El sistema actual sirve como referencia.
6. **Modelo propio a mediano plazo:** cada corrección que hacen los fisioterapeutas es un
   punto anatómico etiquetado por un experto. Con consentimiento de los pacientes, esas
   fotos permiten reentrenar un modelo (por ejemplo RTMPose) que detecte directamente
   EIAS, EIPS, C7 y T5. Es justamente la carencia que señala la literatura.
7. **Producto:** reportes PDF para paciente y profesional, historial y comparación entre
   evaluaciones, y aviso explícito de que el resultado debe ser validado por el
   profesional. Al ser datos de salud, aplicar la Ley Orgánica de Protección de Datos
   Personales del Ecuador (consentimiento, cifrado, acceso por roles).

**Dónde correr el modelo:** en el navegador con MediaPipe (`@mediapipe/tasks-vision`): no
requiere servidor con GPU y la detección ocurre en el equipo del centro. La evaluación
(tablas y diagnóstico) sigue en el backend en Python, como única fuente de verdad.
