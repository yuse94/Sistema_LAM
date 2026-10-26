from fastapi import APIRouter

from app.schemas.assessment import AssessmentConfigIn

router = APIRouter(prefix="/config", tags=["configuración"])


@router.get("/defaults", response_model=AssessmentConfigIn)
def default_config() -> AssessmentConfigIn:
    """Valores predeterminados (opción "Restablecer configuración" del menú de consola)."""
    return AssessmentConfigIn()
