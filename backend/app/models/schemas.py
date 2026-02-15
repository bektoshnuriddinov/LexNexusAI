from pydantic import BaseModel, Field
from datetime import datetime
from typing import Literal


class DocumentMetadata(BaseModel):
    """Structured metadata extracted from document content."""

    document_type: Literal[
        "tutorial", "guide", "reference", "blog_post",
        "research_paper", "documentation", "report", "other"
    ] = Field(description="Type of document")

    topics: list[str] = Field(
        default_factory=list,
        description="Main topics/subjects covered (max 5)",
        max_length=5
    )

    programming_languages: list[str] = Field(
        default_factory=list,
        description="Programming languages mentioned (if any)"
    )

    frameworks_tools: list[str] = Field(
        default_factory=list,
        description="Frameworks, libraries, or tools mentioned (max 5)",
        max_length=5
    )

    date_references: str | None = Field(
        default=None,
        description="Any date or time period mentioned in content (e.g., '2023', 'Q3 2024', 'January 2025')"
    )

    key_entities: list[str] = Field(
        default_factory=list,
        description="Important people, companies, or organizations mentioned (max 5)",
        max_length=5
    )

    summary: str = Field(
        default="",
        description="One-sentence summary of document content",
        max_length=200
    )

    technical_level: Literal["beginner", "intermediate", "advanced", "expert"] = Field(
        default="intermediate",
        description="Technical difficulty level"
    )


class ThreadCreate(BaseModel):
    title: str | None = "New Chat"


class ThreadResponse(BaseModel):
    id: str
    user_id: str
    title: str
    created_at: datetime
    updated_at: datetime


class ThreadUpdate(BaseModel):
    title: str


class MessageCreate(BaseModel):
    content: str


class MessageResponse(BaseModel):
    id: str
    thread_id: str
    user_id: str
    role: str
    content: str
    created_at: datetime


class DocumentResponse(BaseModel):
    id: str
    user_id: str
    filename: str
    file_type: str
    file_size: int
    storage_path: str
    status: str
    error_message: str | None = None
    chunk_count: int = 0
    content_hash: str | None = None
    metadata: dict | None = None
    created_at: datetime
    updated_at: datetime
