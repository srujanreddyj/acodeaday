"""Schemas for standalone flashcards."""

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field


class FlashcardCreateRequest(BaseModel):
    """Create a new flashcard."""

    front: str = Field(..., min_length=1)
    back: str = Field(..., min_length=1)
    tags: list[str] = Field(default_factory=list)
    problem_slug: str | None = None
    roadmap_node_slugs: list[str] = Field(default_factory=list)
    source_url: str | None = None
    next_review_date: date | None = None


class FlashcardUpdateRequest(BaseModel):
    """Update an existing flashcard."""

    front: str | None = None
    back: str | None = None
    tags: list[str] | None = None
    roadmap_node_slugs: list[str] | None = None
    source_url: str | None = None
    next_review_date: date | None = None
    is_active: bool | None = None


class FlashcardSchema(BaseModel):
    """Flashcard response schema."""

    id: UUID
    problem_id: UUID | None
    problem_slug: str | None = None
    roadmap_node_slugs: list[str] = Field(default_factory=list)
    front: str
    back: str
    tags: list[str] = Field(default_factory=list)
    source_url: str | None
    is_active: bool
    last_reviewed_at: datetime | None
    next_review_date: date | None
    created_at: datetime
    updated_at: datetime


class FlashcardListResponse(BaseModel):
    """List response for flashcards."""

    cards: list[FlashcardSchema]
    total: int


class FlashcardReviewRequest(BaseModel):
    """Mark a flashcard as reviewed."""

    next_review_date: date | None = None
