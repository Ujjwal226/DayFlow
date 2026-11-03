import re
import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator

HEX_COLOR_REGEX = re.compile(r"^#[0-9a-fA-F]{6}$")


class CategoryCreateRequest(BaseModel):
    """Schema for creating a category."""
    name: str = Field(..., min_length=1, max_length=100, description="Category name")
    description: Optional[str] = Field(None, max_length=1000, description="Optional description")
    color: str = Field(default="#10B981", description="6-character hex color starting with #")
    icon: Optional[str] = Field(None, max_length=50, description="Icon identifier")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("Category name cannot be empty or whitespace only.")
        if len(trimmed) > 100:
            raise ValueError("Category name cannot exceed 100 characters.")
        return trimmed

    @field_validator("color")
    @classmethod
    def validate_color(cls, v: str) -> str:
        trimmed = v.strip()
        if not HEX_COLOR_REGEX.match(trimmed):
            raise ValueError("Color must be a valid 6-character hexadecimal color code (e.g. #10B981).")
        return trimmed.upper()


class CategoryUpdateRequest(BaseModel):
    """Schema for updating a category."""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Updated name")
    description: Optional[str] = Field(None, max_length=1000, description="Updated description")
    color: Optional[str] = Field(None, description="Updated 6-character hex color code")
    icon: Optional[str] = Field(None, max_length=50, description="Updated icon identifier")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            trimmed = v.strip()
            if not trimmed:
                raise ValueError("Category name cannot be empty or whitespace only.")
            if len(trimmed) > 100:
                raise ValueError("Category name cannot exceed 100 characters.")
            return trimmed
        return None

    @field_validator("color")
    @classmethod
    def validate_color(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            trimmed = v.strip()
            if not HEX_COLOR_REGEX.match(trimmed):
                raise ValueError("Color must be a valid 6-character hexadecimal color code (e.g. #10B981).")
            return trimmed.upper()
        return None


class CategoryResponse(BaseModel):
    """Schema returned for a category."""
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    description: Optional[str] = None
    color: str
    icon: Optional[str] = None
    task_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

