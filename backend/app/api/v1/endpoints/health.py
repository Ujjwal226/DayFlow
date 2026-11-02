from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.health import LivenessResponse, ReadinessResponse
from app.services.health_service import HealthService

router = APIRouter(prefix="/health", tags=["Health"])


@router.get(
    "/live",
    response_model=LivenessResponse,
    status_code=status.HTTP_200_OK,
    summary="Application Liveness Check",
    description="Check whether the backend application process is alive.",
)
def get_liveness() -> LivenessResponse:
    return LivenessResponse(status="ok", service="backend")


@router.get(
    "/ready",
    response_model=ReadinessResponse,
    status_code=status.HTTP_200_OK,
    responses={
        503: {
            "model": ReadinessResponse,
            "description": "Database or dependency is not ready",
        }
    },
    summary="Application Readiness Check",
    description="Check whether the backend and its dependencies (PostgreSQL) are ready to accept traffic.",
)
def get_readiness(db: Session = Depends(get_db)):
    is_ready = HealthService.check_database_readiness(db)

    if not is_ready:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=ReadinessResponse(
                status="unhealthy",
                service="backend",
                database="disconnected",
                details="Could not establish connection to PostgreSQL.",
            ).model_dump(mode="json"),
        )

    return ReadinessResponse(
        status="ok",
        service="backend",
        database="connected",
        details="Database connection verified.",
    )

