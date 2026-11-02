from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field


class RootResponse(BaseModel):
    app_name: str
    version: str
    status: str
    documentation: str


class HealthStatus(BaseModel):
    status: str = Field(..., description="Overall service status ('ok' or 'unhealthy')")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp of the check",
    )


class LivenessResponse(HealthStatus):
    service: str = "backend"


class ReadinessResponse(HealthStatus):
    service: str = "backend"
    database: str = Field(..., description="'connected' or 'disconnected'")
    details: Optional[str] = None

