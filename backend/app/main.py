"""Punto de entrada de la API web del Sistema LAM.

Desarrollo:  uv run fastapi dev app/main.py   (docs en http://localhost:8000/docs)
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import inspect

from app.api.router import api_router
from app.core.config import get_settings
from app.db import models  # noqa: F401  (registra las tablas)
from app.db.session import Base, engine

settings = get_settings()


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
