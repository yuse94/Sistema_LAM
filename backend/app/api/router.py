from fastapi import APIRouter

from app.api.routes import analysis, config, evaluations, patients, points

api_router = APIRouter(prefix="/api")
api_router.include_router(analysis.router)
api_router.include_router(config.router)
api_router.include_router(patients.router)
api_router.include_router(evaluations.router)
api_router.include_router(points.router)


@api_router.get("/health", tags=["sistema"])
def health():
    return {"status": "ok"}
