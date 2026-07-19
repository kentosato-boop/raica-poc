from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from . import models
from .api import router
from .config import get_settings, validate_runtime_settings
from .database import Base, SessionLocal, engine
from .matching import run_matching
from .models import Job
from .seed import seed_database


settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    validate_runtime_settings(settings)
    if settings.bootstrap_schema_enabled:
        Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        if settings.demo_seed_enabled:
            seed_database(db)
        if settings.startup_matching_enabled:
            for job in db.query(Job).all():
                if job.status != "closed":
                    run_matching(db, job.id, "startup")
    yield


app = FastAPI(
    title=settings.app_name,
    version="2.0.0",
    description="RA/CA workflow API with matching, integration outbox, and audit trail.",
    lifespan=lifespan,
    docs_url=None if settings.is_production else "/docs",
    redoc_url=None if settings.is_production else "/redoc",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "OPTIONS"],
    allow_headers=["Content-Type", "X-RAICA-Key"],
)


@app.middleware("http")
async def api_key_guard(request: Request, call_next):
    if settings.api_key and request.url.path.startswith("/api/"):
        if request.headers.get("X-RAICA-Key") != settings.api_key:
            return JSONResponse({"detail": "invalid API key"}, status_code=401)
    return await call_next(request)


@app.get("/health")
def health() -> dict:
    return {"ok": True, "service": settings.app_name, "version": "2.0.0", "environment": settings.environment}


app.include_router(router)

frontend_dist = Path(__file__).resolve().parents[2] / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend")
