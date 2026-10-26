# Guía de migración de consola a web

## Correspondencia con el código anterior

| Código de consola | Nuevo lugar | Estado |
|---|---|---|
| `image_processing_LAM.py` | `backend/app/lam/image_processing.py` | Portado |
| `functions_for_assessment.py` | `backend/app/lam/geometry.py` | Portado sin cambios de lógica |
| `main.py` → `anterior_assessment` | `backend/app/lam/views/anterior.py` | Portado |
| `main.py` → `posterior_assessment` | `backend/app/lam/views/posterior.py` | Portado (etiquetas de tabla 2 corregidas) |
| `main.py` → `lateral_r_assessment` | `backend/app/lam/views/lateral.py` | Portado |
| Gráficas de matplotlib (`savefig`, `show`) | `backend/app/lam/overlay.py` + imagen en la UI | Portado |
| `load_image()` (tkinter) | `POST /api/analysis/{vista}` + carga de archivo en el navegador | Portado |
| `read_configuration` / `change_configuration` (`configuration.json`) | `AssessmentConfigIn` + página Configuración | Portado |
| `patient.py` (`input()`) | `schemas/patient.py`, `db/models.py`, `/api/patients` | Parcial (alta y listado) |
| `report_pdf_LAM.py` | `services/report_pdf.py` | **Pendiente** |
| `add_db_LAM.py` (`DB_LAM.xlsx`) | Base de datos + `services/excel_export.py` | **Pendiente** |
| Fecha de caducidad de prueba (`due_date`) | — | Eliminado (el acceso se controlará con usuarios) |
| `pyinstaller`, `hook-skimage.filters.py`, `icon.ico` | — | Ya no se necesitan en la versión web |

## Hallazgos en el código heredado

Errores encontrados durante el portado. Los tres primeros cambiaban resultados y están
**corregidos** (rama `app_web`, con pruebas en `backend/tests`):

1. **Factor de escala (cm/píxel).** `markers()` calculaba `100 / sqrt(x_R1² + x_R2²)` en
   lugar de `100 / distancia(R1, R2)`. Con imágenes sintéticas daba 0.1062 cm/px cuando
   el valor real es 0.1136 (≈7 % menos), así que todas las distancias en cm salían
   subestimadas. Corregido a `100 / |R2 − R1|`.
2. **Descenso en la vista posterior.** Las condiciones de
   `posterior_angle_from_horizontal` (`a < tol → Der.`, `a > -tol → Izq.`) hacían que
   "Alin." nunca se alcanzara: unos hombros nivelados se reportaban como "Der.".
   Corregido a `a < -tol → Der.`, `a > tol → Izq.`.
3. **Postura "Ideal" en la vista lateral.** Comparaba distancias con signo (`<= 0.5`), por
   lo que desplazamientos posteriores grandes también contaban como ideales. Corregido
   con valor absoluto.
4. **Etiquetas de la tabla 2 posterior.** Reutilizaban las de la vista anterior (Frente,
   Ombligo…). Corregido a las del README (Hombros, 7ma Cervical, 5ta Torácica, Pelvis,
   Rodillas, Tobillos).
5. **Límite de tamaño.** `scale_image` comparaba `len(img[1])` y `len(img[0])`, que son
   ambos el ancho; en la práctica solo se limita el ancho a 1000 px (se mantiene así).
6. **Asignación de marcadores por orden.** Depende del orden de etiquetado de
   scikit-image (de arriba hacia abajo). Si un marcador queda más alto de lo esperado
   (p. ej. F5 sobre los hombros) se asigna mal sin avisar. Ahora el evaluador ve cada
   punto con su nombre y puede corregirlo arrastrándolo.

Los resultados obtenidos con la versión de consola **no son comparables** con los nuevos
en distancias (punto 1) ni en el descenso posterior (punto 2).

## Detección y evaluación separadas

El núcleo `backend/app/lam` ya no está atado a los marcadores:

- **Detección** (imagen → puntos con nombre F1…F14, P1…P12, L1…L7): hoy, el detector de
  marcadores verdes; luego, un detector sin marcadores (ver `ESTADO_DEL_ARTE.md`).
- **Evaluación** (puntos + escala → tablas y diagnóstico): `evaluate_landmarks()` y
  `POST /api/analysis/{vista}/evaluate`. La interfaz la llama cada vez que el evaluador
  suelta un punto arrastrado.
- **Vista lateral izquierda:** usa los mismos puntos L1–L7 y reglas que la derecha,
  reflejando la imagen horizontalmente. Con marcadores, la EIPS (L3) se toma del lado
  derecho de la imagen.

## Hoja de ruta

**Fase 1 (hecho):** núcleo portado y probado, errores corregidos, cuatro vistas, API de
análisis y recálculo, editor de puntos arrastrables, pacientes básicos.

**Fase 2 — sin marcadores:** detector MediaPipe en el navegador para los puntos que cubre,
preposicionamiento de los demás por proporciones, escala por referencia en la escena o
estatura, y modo manual.

**Fase 3 — validación:** fotos de la tesis y nuevas fotos con marcadores; comparar el modo
sin marcadores contra el detector de marcadores (error, ICC, Bland-Altman). Pruebas de
regresión con esas fotos en `backend/tests/fotos/` (fuera del repositorio si contienen
pacientes identificables).

**Fase 4 — producto:** guardar evaluaciones, reporte PDF y exportación Excel, historial y
comparación entre evaluaciones, usuarios y roles por centro, despliegue y protección de
datos.

**Fase 5 — modelo propio:** reentrenar un modelo de pose con los puntos corregidos por los
fisioterapeutas para detectar EIAS, EIPS, C7 y T5 automáticamente.
