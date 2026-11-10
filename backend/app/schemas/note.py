import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator

from app.schemas.category import CategoryResponse
from app.schemas.tag import TagResponse


class NoteCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=255, description="Note title")
    content: str = Field(default="", description="Note Markdown content")
    is_pinned: bool = Field(default=False, description="Whether the note is pinned")
    category_id: Optional[uuid.UUID] = Field(default=None, description="Optional category ID")
    project_id: Optional[uuid.UUID] = Field(default=None, description="Optional associated project ID")
    task_id: Optional[uuid.UUID] = Field(default=None, description="Optional associated task ID")
    tag_ids: Optional[List[uuid.UUID]] = Field(default=None, description="List of tag IDs")

    @field_validator("title")
    @classmethod
    def validate_title_not_empty(cls, v: str) -> str:
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("Note title cannot be blank or whitespace only")
        return trimmed


class NoteUpdateRequest(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=255, description="Note title")
    content: Optional[str] = Field(default=None, description="Note Markdown content")
    is_pinned: Optional[bool] = Field(default=None, description="Whether the note is pinned")
    is_archived: Optional[bool] = Field(default=None, description="Whether the note is archived")
    category_id: Optional[uuid.UUID] = Field(default=None, description="Category ID or None to detach")
    project_id: Optional[uuid.UUID] = Field(default=None, description="Project ID or None to detach")
    task_id: Optional[uuid.UUID] = Field(default=None, description="Task ID or None to detach")
    tag_ids: Optional[List[uuid.UUID]] = Field(default=None, description="New complete list of tag IDs")

    @field_validator("title")
    @classmethod
    def validate_title_not_empty(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            trimmed = v.strip()
            if not trimmed:
                raise ValueError("Note title cannot be blank or whitespace only")
            return trimmed
        return v


class NoteProjectReference(BaseModel):
    id: uuid.UUID
    name: str
    color: Optional[str] = None

    model_config = {"from_attributes": True}


class NoteTaskReference(BaseModel):
    id: uuid.UUID
    title: str
    status: str
    priority: str

    model_config = {"from_attributes": True}


class NoteResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    title: str
    content: str
    is_pinned: bool
    is_archived: bool
    category_id: Optional[uuid.UUID] = None
    category: Optional[CategoryResponse] = None
    project_id: Optional[uuid.UUID] = None
    project: Optional[NoteProjectReference] = None
    task_id: Optional[uuid.UUID] = None
    task: Optional[NoteTaskReference] = None
    tags: List[TagResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class NoteListResponse(BaseModel):
    items: List[NoteResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

