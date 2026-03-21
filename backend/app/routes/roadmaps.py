"""API routes for roadmap graph and node detail views."""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.connection import get_db
from app.middleware.auth import get_current_user
from app.schemas.roadmaps import (
    RoadmapItemCompletionRequest,
    RoadmapListResponse,
    RoadmapNodeDetailResponse,
    RoadmapOverviewResponse,
)
from app.services.roadmaps import RoadmapService

router = APIRouter(prefix="/api/roadmaps", tags=["roadmaps"])


@router.get("", response_model=RoadmapListResponse)
async def list_roadmaps(
    db: AsyncSession = Depends(get_db),
):
    service = RoadmapService(db)
    await service.ensure_seed_data()
    return await service.list_roadmaps()


@router.get("/{slug}", response_model=RoadmapOverviewResponse)
async def get_roadmap(
    slug: str,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = RoadmapService(db)
    try:
        await service.ensure_seed_data()
        return await service.get_overview(slug, user_id=user["id"])
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/{slug}/nodes/{node_slug}", response_model=RoadmapNodeDetailResponse)
async def get_roadmap_node(
    slug: str,
    node_slug: str,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = RoadmapService(db)
    try:
        await service.ensure_seed_data()
        return await service.get_node_detail(slug, node_slug, user_id=user["id"])
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.put("/items/{item_id}/completion")
async def set_item_completion(
    item_id: uuid.UUID,
    payload: RoadmapItemCompletionRequest,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = RoadmapService(db)
    await service.set_item_completion(item_id=item_id, user_id=user["id"], completed=payload.completed)
    return {"success": True}
