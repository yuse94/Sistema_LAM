# Guía de migración de consola a web

## Correspondencia con el código anterior

| Código de consola | Nuevo lugar | Estado |
|---|---|---|
| `image_processing_LAM.py` | `backend/app/lam/image_processing.py` | Portado |
| `functions_for_assessment.py` | `backend/app/lam/geometry.py` | Portado sin cambios de lógica |
| `main.py` → `anterior_assessment` | `backend/app/lam/views/anterior.py` | Portado |
| `main.py` → `posterior_assessment` | `backend/app/lam/views/posterior.py` | Portado (etiquetas de tabla 2 corregidas) |
| `main.py` → `lateral_r_assessment` | `backend/app/lam/views/lateral.py` | Portado |
| Gráficas de matplotlib (`savefig`, `show`) | `backend/app/lam/overlay.py` (Pillow) + editor SVG en la UI | Portado; la cuadrícula sigue la nivelación |
| `load_image()` (tkinter) | `POST /api/analysis/{vista}` + carga de archivo en el navegador | Portado |
| `read_configuration` / `change_configuration` (`configuration.json`) | `AssessmentConfigIn` + página Configuración | Portado |
| `patient.py` (`input()`) | `schemas/patient.py`, `db/models.py`, `/api/patients` | Portado (alta, edición, eliminación e historial) |
| `report_pdf_LAM.py` | `services/report_pdf.py`, `GET /api/evaluations/{id}/report.pdf` | Portado (ver fase 4) |
| `add_db_LAM.py` (`DB_LAM.xlsx`) | Base de datos + `services/excel_export.py`, `GET /api/evaluations/export.xlsx` | Portado (ver fase 4) |
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

**Fase 2 — sin marcadores (implementada, pendiente de validar con fotos reales):**
- MediaPipe Pose Landmarker corre en el navegador y envía sus 33 puntos a
  `POST /api/analysis/{vista}/pose`. `backend/app/lam/pose.py` los convierte en puntos
  LAM; los que el modelo no detecta (EIAS, EIPS, C7, T5, ombligo, manubrio, mentón,
  entrecejo, tuberosidad tibial, tarso) se estiman por proporciones y la interfaz los
  muestra en naranja hasta que el evaluador los mueve.
- Los pares izquierdo/derecho se asignan por su posición en la imagen (MediaPipe a veces
  los invierte cuando el paciente está de espaldas).
- **Escala por estatura** (decisión: sin referencias R1/R2): cm/píxel = estatura /
  distancia vertical entre el vértice de la cabeza y el suelo. Ambos puntos salen de la
  silueta que detecta MediaPipe y se pueden arrastrar.
- **Línea vertical de referencia** (decisión, en lugar del sensor del celular): el
  evaluador coloca dos puntos sobre algo vertical de la escena (puerta, esquina,
  plomada) y los puntos se nivelan antes de evaluar (`backend/app/lam/level.py`). Sin
  ella, una cámara girada θ° suma θ° de error a los ángulos (lo comprueba
  `test_tilted_camera_without_vertical_line_biases_angles`).
- El modo con marcadores verdes sigue disponible; servirá como referencia en la fase 3.

**Diccionario de puntos:**
- `backend/app/lam/catalog.py` describe los 33 puntos (F1–F14, P1–P12, L1–L7): definición
  anatómica, cómo localizarlo, región y posición en una silueta de referencia.
  `GET /api/points` lo expone.
- Las mediciones de cada punto no se escriben a mano: se calculan moviendo el punto
  sobre la postura de referencia y viendo qué filas de las tablas y del diagnóstico
  cambian. Si cambia una fórmula, el diccionario se actualiza solo.
- En la interfaz: página "Puntos" (silueta navegable, buscador sin tildes y ficha) y,
  en el editor, la ficha del punto que se toca en la foto.
- Definiciones redactadas a partir de la Tabla 2.1 de la tesis, con precisiones del centro
  HABILITAR:
  - F11/F12 (tobillos): su punto medio define la línea media del plano frontal.
  - P2: apófisis espinosa de la quinta vértebra dorsal (T5).
  - L7: articulación transversal del tarso, como en la tesis (confirmado por HABILITAR;
    es donde está el marcador en las fotos de validación). En el modo sin marcadores se
    estima en el pie a partir del tobillo y la punta del pie de MediaPipe.

**Fase 3 — validación (en curso, ver `docs/VALIDACION.md`):**
- Hecho: detector de marcadores con umbral automático (40 de 40 fotos), pruebas con las
  fotos reales (`uv run pytest -m fotos`), corrección del ángulo pélvico lateral
  (HALLAZGO-7), nombres L3/L4 según la tesis y tolerancias por defecto de 1° y 0.5 cm.
- Pendiente: ejecutar `backend/validation/markerless.py` (MediaPipe contra marcadores),
  completar las estaturas reales y fotografiar laterales izquierdas reales.

**Fase 4 — producto (en curso):**
- Hecho: guardar evaluaciones por paciente (`POST /api/evaluations`). La interfaz envía las
  fotos y los puntos tal como quedaron en el editor, y el servidor vuelve a evaluar cada
  vista (no confía en los resultados del navegador). Guarda en `storage_dir` la foto y el
  overlay, y en la base de datos los puntos, la calibración, la línea vertical, la escala,
  los puntos estimados sin revisar y los resultados. Edad, estatura y peso se copian a la
  evaluación para que un reporte antiguo muestre los datos de ese momento.
- Hecho: reporte PDF generado a pedido. Tiene una portada con los datos, los parámetros y el
  resumen del diagnóstico, y una página por vista con la imagen y las tablas. Respecto a
  `report_pdf_LAM.py`:
  - la fecha es la de la evaluación;
  - incluye la lateral izquierda, el modo de detección y la escala;
  - avisa de los puntos estimados sin revisar;
  - incluye las observaciones del evaluador.
- Hecho: exportación a Excel con el formato de `DB_LAM.xlsx` (hojas Anterior, Posterior,
  LateralD y LateralI, más enlaces al PDF y a la imagen). Cada medición lleva dirección y
  valor. Se corrigió un error de índices de `add_db_LAM.py` que dejaba solo el ángulo en las
  columnas «Cabeza inclinada» y «Rodilla derecha/izquierda».
- Hecho: ficha del paciente con su historial, comparación de mediciones en el tiempo
  (`GET /api/patients/{id}/history?view=`) y eliminación del paciente con sus fotografías.
- Pendiente: reabrir una evaluación guardada en el editor para corregir puntos, usuarios y
  roles por centro, despliegue, migraciones con Alembic y protección de datos (LOPDP).

**Fase 5 — modelo propio:** reentrenar un modelo de pose con los puntos corregidos por los
fisioterapeutas para detectar EIAS, EIPS, C7 y T5 automáticamente.
