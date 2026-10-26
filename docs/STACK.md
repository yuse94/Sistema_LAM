# Sistema LAM web — Stack y arquitectura propuestos

Rama: `app_web` · Versión 0.3.0 (primera versión web)

## Objetivo

Pasar de la aplicación de consola (y del prototipo en Kivy de `development_kivy`) a una
aplicación web que el fisioterapeuta use desde el navegador, sin instalar ejecutables,
conservando el algoritmo de lectura automática de marcadores validado en la tesis
(UPS-CT008207) y sus tablas de resultados (formato del centro HABILITAR).

## Stack

| Capa | Tecnología | Por qué |
|---|---|---|
| Núcleo de análisis | Python 3.12 · NumPy 2 · scikit-image · SciPy | Es el código existente; se reutiliza como librería pura (`backend/app/lam`). |
| API | FastAPI · Pydantic v2 | Mismo lenguaje que el núcleo, validación de entradas, documentación OpenAPI automática en `/docs`. |
| Persistencia | SQLAlchemy 2 + Alembic · SQLite (desarrollo) / PostgreSQL (producción) | Reemplaza `DB_LAM.xlsx` como fuente de verdad; el Excel pasa a ser una exportación. |
| Archivos | Disco local (`data/storage`), luego S3/MinIO | Fotografías originales, imágenes resultantes y PDFs. |
| Reportes | ReportLab (PDF) · openpyxl (Excel) | Se reutiliza `report_pdf_LAM.py` y `add_db_LAM.py`. |
| Imagen resultante | Matplotlib (backend `Agg`) en servidor; SVG en el navegador | Sin ventanas emergentes; la UI dibuja marcadores y cuadrícula. |
| Frontend | React 19 · TypeScript · Vite · Tailwind CSS 4 · TanStack Query · React Router | Ecosistema estándar; tipado de las respuestas de la API. |
| Componentes UI | shadcn/ui (a incorporar con `npx shadcn@latest init`) | Componentes accesibles y editables. |
| Herramientas | uv (Python), npm, Ruff, pytest, Docker Compose, GitHub Actions | Instalación reproducible y CI. |

Alternativas descartadas: **Django** (más pesado de lo necesario para una API con pocas
entidades), **Streamlit/Gradio** (rápidos para prototipos, pero limitan el flujo clínico,
la gestión de pacientes y el control de la interfaz) y **reescribir el análisis en
JavaScript/OpenCV.js** (obligaría a revalidar el algoritmo).

## Arquitectura

```
Navegador (React)
   │  POST /api/analysis/{vista}  (foto + configuración)
   │  /api/patients, /api/evaluations, /api/config
   ▼
FastAPI (backend/app)
   ├── api/routes      → HTTP, validación, errores
   ├── lam/            → núcleo puro: imagen → ViewResult (sin I/O ni UI)
   ├── services/       → PDF, Excel, almacenamiento
   └── db/             → Patient · Evaluation · ViewAnalysis
   ▼
PostgreSQL / SQLite  +  data/storage (imágenes, PDFs)
```

Decisiones clave:

- **El núcleo `lam` no conoce la web.** Recibe un `ndarray` y un `AssessmentConfig` y
  devuelve un `ViewResult` (marcadores, puntos derivados, tablas, diagnóstico, imagen
  enderezada). Se puede probar con imágenes sintéticas y reutilizar en otra interfaz.
- **Los errores de conteo de marcadores son datos, no ventanas.** `MarkerCountError`
  llega a la UI con HTTP 422, los puntos detectados y una vista previa, para que el
  evaluador vea qué falló y cargue otra foto (antes: ventana de matplotlib + `input()`).
- **Análisis sin estado y guardado explícito.** `/api/analysis` no guarda nada; la
  evaluación se guarda cuando el evaluador confirma los datos del paciente.
- **Configuración por evaluador.** Los cuatro parámetros (tolerancias, cuadrícula,
  umbral) se validan con los mismos rangos que el menú de consola.

## Estructura de carpetas

```
backend/
  app/
    lam/                 núcleo de análisis (portado de main.py e *_LAM.py)
      image_processing.py, geometry.py, types.py, overlay.py
      views/anterior.py, posterior.py, lateral.py, base.py
    api/routes/          analysis, patients, evaluations, config
    schemas/             modelos Pydantic de entrada/salida
    db/                  SQLAlchemy (modelos y sesión)
    services/            report_pdf, excel_export (pendientes de portar)
    core/config.py       variables de entorno (prefijo LAM_)
  tests/                 pruebas con imágenes sintéticas
frontend/
  src/pages/             NuevaEvaluacion, Pacientes, Configuracion
  src/lib/               cliente de la API, tipos, configuración
docs/                    este documento y la guía de migración
```

Los scripts de consola (`main.py`, `*_LAM.py`, `patient.py`) se mantienen en la raíz
como referencia hasta terminar la migración (fase 2).

## Cómo ejecutar (desarrollo)

Backend (requiere [uv](https://docs.astral.sh/uv/)):

```bash
cd backend
cp .env.example .env
uv sync
uv run fastapi dev app/main.py      # http://localhost:8000/docs
uv run pytest
```

Frontend:

```bash
cd frontend
npm install
npm run dev                         # http://localhost:5173 (redirige /api al backend)
```

Con Docker (backend + PostgreSQL): `docker compose up --build`.
