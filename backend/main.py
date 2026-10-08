from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.config import settings
from backend.logging_config import logger
from backend.api.routes import (
    health_router,
    upload_router,
    datasets_router,
    documents_router,
    analysis_router,
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.APP_NAME} Backend (Env: {settings.APP_ENV})")
    logger.info("Deterministic Analytical Engine & Verification System initialized successfully.")
    yield
    logger.info(f"Shutting down {settings.APP_NAME} Backend")

app = FastAPI(
    title=settings.APP_NAME,
    description="ProofAI — Deterministic Foundation for Proof-Carrying Data Analysis",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers (Both /api prefix and root level for UI compatibility)
app.include_router(health_router)
app.include_router(health_router, prefix="/api")

app.include_router(upload_router)
app.include_router(upload_router, prefix="/api")
app.include_router(upload_router, prefix="/dataset")

app.include_router(datasets_router)
app.include_router(datasets_router, prefix="/api")
app.include_router(datasets_router, prefix="/dataset")

app.include_router(documents_router)
app.include_router(documents_router, prefix="/api")

app.include_router(analysis_router)
app.include_router(analysis_router, prefix="/api")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host=settings.BACKEND_HOST,
        port=settings.BACKEND_PORT,
        reload=settings.DEBUG
    )
