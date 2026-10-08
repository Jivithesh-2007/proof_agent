import shutil
from fastapi import APIRouter
from backend.config import settings

router = APIRouter(tags=["Health"])

@router.get("/health")
def health_check():
    docker_avail = shutil.which("docker") is not None
    
    return {
        "status": "healthy",
        "backend": "healthy",
        "storage": "ready",
        "dataset_subsystem": "ready",
        "analytics_engine": "ready",
        "verification": "ready",
        "app_name": settings.APP_NAME,
        "environment": settings.APP_ENV,
        "mode": "deterministic_rule_analyst",
        "docker": "available" if docker_avail else "unavailable"
    }
