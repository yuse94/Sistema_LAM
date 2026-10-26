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

Durante el portado se encontraron comportamientos que parecen errores. Para no alterar
los resultados clínicos sin aprobación, **se conservaron tal cual** y están marcados con
`FIXME(HALLAZGO-n)` en el código. Conviene validarlos contra la versión MATLAB de la
tesis, que fue la que se comparó con Kinovea.

1. **Factor de escala (cm/píxel).** `markers()` calcula
   `100 / sqrt(x_R1² + x_R2²)` en lugar de `100 / distancia(R1, R2)`. Con imágenes
   sintéticas da 0.1062 cm/px cuando el valor real es 0.1136 (≈7 % menos), así que
   **todas las distancias en cm salen subestimadas**. La cuadrícula sí usa la distancia
   correcta.
2. **Descenso en la vista posterior.** En `posterior_angle_from_horizontal` las
   condiciones (`a < tol → Der.`, `a > -tol → Izq.`) hacen que "Alin." nunca se alcance:
   unos hombros perfectamente nivelados se reportan como "Der.".
3. **Postura "Ideal" en la vista lateral.** Compara distancias con signo (`<= 0.5`), por
   lo que desplazamientos posteriores grandes también cuentan como ideales.
4. **Etiquetas de la tabla 2 posterior.** El script reutilizaba las de la vista anterior
   (Frente, Ombligo…). **Corregido** a las del README (Hombros, 7ma Cervical, 5ta
   Torácica, Pelvis, Rodillas, Tobillos), porque solo afecta el texto.
5. **Límite de tamaño.** `scale_image` comparaba `len(img[1])` y `len(img[0])`, que son
   ambos el ancho; en la práctica solo se limita el ancho a 1000 px (se mantiene así).
6. El orden de los marcadores depende del orden de etiquetado de scikit-image (de arriba
   hacia abajo). Si un marcador queda más alto de lo esperado (p. ej. F5 sobre los
   hombros), se asigna mal sin avisar. A futuro conviene permitir que el evaluador
   corrija la asignación en la interfaz.

## Hoja de ruta

**Fase 1 (esta rama):** núcleo portado y probado, API de análisis, pacientes básicos,
interfaz de carga por vista con tablas, diagnóstico e imagen resultante.

**Fase 2:** guardar evaluaciones (paciente + vistas + imágenes), reporte PDF desde el
navegador, exportación a Excel con el formato de `DB_LAM.xlsx`, migraciones con Alembic.

**Fase 3:** usuarios y roles (fisioterapeuta/administrador), historial y comparación
entre evaluaciones de un paciente, corrección manual de marcadores sobre la imagen,
despliegue (Docker + HTTPS) y respaldo de datos (información clínica sensible).

**Fase 4 (opcional):** captura con la cámara del celular desde el navegador con guía de
nivelación, y pruebas de regresión con las fotografías de validación de la tesis.
