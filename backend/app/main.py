"""Punto de entrada de la API web del Sistema LAM.

Desarrollo:  uv run fastapi dev app/main.py   (docs en http://localhost:8000/docs)
Uso local:   uv run python -m app.launcher    (API + interfaz compilada, abre el navegador)
"""
import mimetypes
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy import inspect

from app.api.router import api_router
from app.core.config import get_settings
from app.db import models  # noqa: F401  (registra las tablas)
from app.db.session import Base, engine

settings = get_settings()


def _add_missing_columns() -> None:
    """Desarrollo: agrega a las tablas existentes las columnas nuevas (todas admiten nulos).

    Evita perder la base de datos de pruebas al agregar campos; en producción se usará Alembic.
    """
    insp = inspect(engine)
    tables = set(insp.get_table_names())
    with engine.begin() as conn:
        for table in Base.metadata.sorted_tables:
            if table.name not in tables:
                continue
            existing = {c["name"] for c in insp.get_columns(table.name)}
            for col in table.columns:
                if col.name not in existing and col.nullable:
                    conn.exec_driver_sql(
                        f'ALTER TABLE {table.name} ADD COLUMN "{col.name}" {col.type.compile(engine.dialect)}')


def _drop_outdated_evaluation_tables() -> None:
    """Las tablas de evaluaciones de la v0.3 nunca se usaron (la ruta era un stub): si la base
    de desarrollo las tiene con el esquema viejo, se recrean. Los pacientes no se tocan."""
    insp = inspect(engine)
    if "evaluations" in insp.get_table_names() and "mode" not in {c["name"] for c in insp.get_columns("evaluations")}:
        models.ViewAnalysis.__table__.drop(engine, checkfirst=True)
        models.Evaluation.__table__.drop(engine, checkfirst=True)


@asynccontextmanager
async def lifespan(_: FastAPI):
    settings.storage_dir.mkdir(parents=True, exist_ok=True)
    if settings.database_url.startswith("sqlite"):
        settings.storage_dir.parent.mkdir(parents=True, exist_ok=True)
    # Solo para desarrollo; en producción se usarán migraciones con Alembic.
    _drop_outdated_evaluation_tables()
    _add_missing_columns()
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title=settings.app_name, version="0.4.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(api_router)


# --- Interfaz compilada ---------------------------------------------------------------------
# Windows no siempre registra estos tipos; MediaPipe necesita application/wasm.
mimetypes.add_type("application/wasm", ".wasm")
mimetypes.add_type("text/javascript", ".mjs")


def _mount_frontend(app: FastAPI, folder: Path) -> None:
    root = folder.resolve()
    if not (root / "index.html").is_file():
        return  # en desarrollo la interfaz la sirve Vite (npm run dev)

    @app.get("/{path:path}", include_in_schema=False)
    def frontend(path: str):
        if path.startswith("api/"):
            raise HTTPException(404, "Ruta no encontrada")
        file = (root / path).resolve()
        if path and file.is_file() and file.is_relative_to(root):
            cache = "public, max-age=31536000, immutable" if path.startswith("assets/") else "no-cache"
            return FileResponse(file, headers={"Cache-Control": cache})
        # Rutas de la aplicación (/pacientes/3, /evaluaciones/7...): las resuelve React
        return FileResponse(root / "index.html", headers={"Cache-Control": "no-cache"})


_mount_frontend(app, settings.frontend_dir)
