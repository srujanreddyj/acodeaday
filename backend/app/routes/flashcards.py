"""API routes for standalone flashcards."""

import uuid
from datetime import UTC, date, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.connection import get_db
from app.db.tables import Problem, RoadmapNode, RoadmapNodeFlashcard, UserFlashcard
from app.middleware.auth import get_current_user
from app.schemas.flashcards import (
    FlashcardCreateRequest,
    FlashcardListResponse,
    FlashcardReviewRequest,
    FlashcardSchema,
    FlashcardUpdateRequest,
)
from app.services.roadmaps import RoadmapService

router = APIRouter(prefix="/api/flashcards", tags=["flashcards"])


def _utc_date() -> date:
    return datetime.now(UTC).date()


async def _get_linked_node_slugs(db: AsyncSession, card_id: uuid.UUID) -> list[str]:
    result = await db.execute(
        select(RoadmapNode.slug)
        .join(RoadmapNodeFlashcard, RoadmapNodeFlashcard.roadmap_node_id == RoadmapNode.id)
        .where(RoadmapNodeFlashcard.flashcard_id == card_id)
        .order_by(RoadmapNode.title)
    )
    return [slug for (slug,) in result.all()]


async def _serialize_flashcard(
    db: AsyncSession,
    card: UserFlashcard,
    problem_slug: str | None = None,
) -> FlashcardSchema:
    return FlashcardSchema(
        id=card.id,
        problem_id=card.problem_id,
        problem_slug=problem_slug,
        roadmap_node_slugs=await _get_linked_node_slugs(db, card.id),
        front=card.front,
        back=card.back,
        tags=card.tags or [],
        source_url=card.source_url,
        is_active=card.is_active,
        last_reviewed_at=card.last_reviewed_at,
        next_review_date=card.next_review_date,
        created_at=card.created_at,
        updated_at=card.updated_at,
    )


@router.get("", response_model=FlashcardListResponse)
async def list_flashcards(
    due_only: bool = Query(False),
    tag: str | None = Query(None),
    include_inactive: bool = Query(False),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List flashcards with optional due/tag filters."""
    filters = [UserFlashcard.user_id == user["id"]]

    if not include_inactive:
        filters.append(UserFlashcard.is_active.is_(True))

    if due_only:
        filters.append(
            (UserFlashcard.next_review_date.is_(None))
            | (UserFlashcard.next_review_date <= _utc_date())
        )

    if tag:
        filters.append(UserFlashcard.tags.any(tag.strip()))

    result = await db.execute(
        select(UserFlashcard, Problem.slug)
        .outerjoin(Problem, Problem.id == UserFlashcard.problem_id)
        .where(and_(*filters))
        .order_by(UserFlashcard.updated_at.desc())
    )

    rows = result.all()
    cards = [await _serialize_flashcard(db, card, problem_slug=slug) for card, slug in rows]
    return FlashcardListResponse(cards=cards, total=len(cards))


@router.get("/today", response_model=FlashcardListResponse)
async def list_due_flashcards_today(
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List due flashcards for today (independent of problem solved flow)."""
    result = await db.execute(
        select(UserFlashcard, Problem.slug)
        .outerjoin(Problem, Problem.id == UserFlashcard.problem_id)
        .where(UserFlashcard.user_id == user["id"])
        .where(UserFlashcard.is_active.is_(True))
        .where(
            (UserFlashcard.next_review_date.is_(None))
            | (UserFlashcard.next_review_date <= _utc_date())
        )
        .order_by(UserFlashcard.updated_at.desc())
    )

    rows = result.all()
    cards = [await _serialize_flashcard(db, card, problem_slug=slug) for card, slug in rows]
    return FlashcardListResponse(cards=cards, total=len(cards))


@router.post("", response_model=FlashcardSchema)
async def create_flashcard(
    payload: FlashcardCreateRequest,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new standalone flashcard."""
    problem_id = None
    if payload.problem_slug:
        result = await db.execute(select(Problem).where(Problem.slug == payload.problem_slug))
        problem = result.scalar_one_or_none()
        if not problem:
            raise HTTPException(status_code=404, detail=f"Problem '{payload.problem_slug}' not found")
        problem_id = problem.id

    tags = [tag.strip() for tag in payload.tags if tag.strip()]

    card = UserFlashcard(
        id=uuid.uuid4(),
        user_id=user["id"],
        problem_id=problem_id,
        front=payload.front,
        back=payload.back,
        tags=tags,
        source_url=payload.source_url,
        next_review_date=payload.next_review_date,
        is_active=True,
    )
    db.add(card)
    await db.flush()
    if payload.roadmap_node_slugs:
        roadmap_service = RoadmapService(db)
        await roadmap_service.ensure_seed_data()
        await roadmap_service.replace_flashcard_topics(
            flashcard_id=card.id,
            roadmap_slug="dsa-roadmap",
            node_slugs=payload.roadmap_node_slugs,
        )
    await db.commit()
    await db.refresh(card)

    return await _serialize_flashcard(db, card, problem_slug=payload.problem_slug)


@router.patch("/{card_id}", response_model=FlashcardSchema)
async def update_flashcard(
    card_id: uuid.UUID,
    payload: FlashcardUpdateRequest,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update flashcard content/tags/status."""
    result = await db.execute(
        select(UserFlashcard, Problem.slug)
        .outerjoin(Problem, Problem.id == UserFlashcard.problem_id)
        .where(UserFlashcard.id == card_id)
        .where(UserFlashcard.user_id == user["id"])
    )
    row = result.one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Flashcard not found")

    card, problem_slug = row

    if payload.front is not None:
        card.front = payload.front
    if payload.back is not None:
        card.back = payload.back
    if payload.tags is not None:
        card.tags = [tag.strip() for tag in payload.tags if tag.strip()]
    if payload.source_url is not None:
        card.source_url = payload.source_url
    if payload.next_review_date is not None:
        card.next_review_date = payload.next_review_date
    if payload.is_active is not None:
        card.is_active = payload.is_active
    if payload.roadmap_node_slugs is not None:
        roadmap_service = RoadmapService(db)
        await roadmap_service.ensure_seed_data()
        await roadmap_service.replace_flashcard_topics(
            flashcard_id=card.id,
            roadmap_slug="dsa-roadmap",
            node_slugs=payload.roadmap_node_slugs,
        )

    await db.commit()
    await db.refresh(card)

    return await _serialize_flashcard(db, card, problem_slug=problem_slug)


@router.post("/{card_id}/review", response_model=FlashcardSchema)
async def mark_flashcard_reviewed(
    card_id: uuid.UUID,
    payload: FlashcardReviewRequest,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Mark flashcard reviewed and optionally set next due date."""
    result = await db.execute(
        select(UserFlashcard, Problem.slug)
        .outerjoin(Problem, Problem.id == UserFlashcard.problem_id)
        .where(UserFlashcard.id == card_id)
        .where(UserFlashcard.user_id == user["id"])
    )
    row = result.one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Flashcard not found")

    card, problem_slug = row
    card.last_reviewed_at = datetime.now(UTC).replace(tzinfo=None)
    card.next_review_date = payload.next_review_date or (_utc_date() + timedelta(days=1))

    await db.commit()
    await db.refresh(card)
    return await _serialize_flashcard(db, card, problem_slug=problem_slug)


@router.delete("/{card_id}")
async def delete_flashcard(
    card_id: uuid.UUID,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Soft-delete a flashcard by marking inactive."""
    result = await db.execute(
        select(UserFlashcard)
        .where(UserFlashcard.id == card_id)
        .where(UserFlashcard.user_id == user["id"])
    )
    card = result.scalar_one_or_none()
    if not card:
        raise HTTPException(status_code=404, detail="Flashcard not found")

    card.is_active = False
    await db.commit()
    return {"success": True}
