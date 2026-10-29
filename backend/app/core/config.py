"""Configuración de la aplicación (variables de entorno / .env)."""
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="LAM_", extra="ignore")

    app_name: str = "Sistema LAM"
    # SQLite para desarrollo; en producción: postgresql+psycopg://user:pass@host/lam
    database_url: str = "sqlite:///./data/lam.db"
    # Carpeta donde se guardan fotografías, overlays, PDFs y Excel (reemplaza ~/Documents/LAM)
    storage_dir: Path = Path("./data/storage")
    cors_origins: list[str] = ["http://localhost:5173"]
    max_upload_mb: int = 25
    # Interfaz compilada (npm run build). Si existe, la API también la sirve en "/":
    # un solo proceso y un solo puerto para usar la app en un equipo local.
    frontend_dir: Path = Path(__file__).resolve().parents[3] / "frontend" / "dist"


@lru_cache
def get_settings() -> Settings:
    return Settings()
