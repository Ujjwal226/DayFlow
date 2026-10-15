"""
DayFlow backend – FastAPI application entry point.
"""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers import analytics, auth, tasks

settings = get_settings()
settings.validate_for_production()

app = FastAPI(
    title="DayFlow API",
    description="Personal task management backend for DayFlow.",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# --------------------------------------------------------------------------- #
# CORS
# --------------------------------------------------------------------------- #
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------------------------------------------------------------- #
# Routers
# --------------------------------------------------------------------------- #
app.include_router(auth.router)
app.include_router(tasks.router)
app.include_router(analytics.router)


# --------------------------------------------------------------------------- #
# Health
# --------------------------------------------------------------------------- #

@app.get("/health", tags=["health"], summary="Health check")
def health_check():
    return {"status": "ok", "version": app.version}
