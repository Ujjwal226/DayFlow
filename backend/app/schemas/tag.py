import re
import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator

HEX_COLOR_REGEX = re.compile(r"^#[0-9a-fA-F]{6}$")


class TagCreateRequest(BaseModel):
    """Schema for creating a tag."""
    name: str = Field(..., min_length=1, max_length=50, description="Tag name")
    color: Optional[str] = Field(default="#0D9488", description="Optional 6-character hex color code")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("Tag name cannot be empty or whitespace only.")
        if len(trimmed) > 50:
            raise ValueError("Tag name cannot exceed 50 characters.")
        return trimmed

    @field_validator("color")
    @classmethod
    def validate_color(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            trimmed = v.strip()
            if not HEX_COLOR_REGEX.match(trimmed):
                raise ValueError("Color must be a valid 6-character hexadecimal color code (e.g. #0D9488).")
            return trimmed.upper()
        return None


class TagUpdateRequest(BaseModel):
    """Schema for updating a tag."""
    name: Optional[str] = Field(None, min_length=1, max_length=50, description="Updated name")
    color: Optional[str] = Field(None, description="Updated 6-character hex color code")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            trimmed = v.strip()
            if not trimmed:
                raise ValueError("Tag name cannot be empty or whitespace only.")
            if len(trimmed) > 50:
                raise ValueError("Tag name cannot exceed 50 characters.")
            return trimmed
        return None

    @field_validator("color")
    @classmethod
    def validate_color(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            trimmed = v.strip()
            if not HEX_COLOR_REGEX.match(trimmed):
                raise ValueError("Color must be a valid 6-character hexadecimal color code (e.g. #0D9488).")
            return trimmed.upper()
        return None


class TagResponse(BaseModel):
    """Schema returned for a tag."""
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    color: Optional[str] = None
    task_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

