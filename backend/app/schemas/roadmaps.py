"""Schemas for roadmap graph and node detail APIs."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class RoadmapNodeSummary(BaseModel):
    slug: str
    title: str
    difficulty: str
    x: int
    y: int
    width: int
    height: int
    completed_count: int
    total_count: int


class RoadmapEdgeSchema(BaseModel):
    source_node_slug: str
    target_node_slug: str


class RoadmapLegendCounts(BaseModel):
    easy: int = 0
    med: int = 0
    hard: int = 0


class RoadmapOverviewResponse(BaseModel):
    slug: str
    title: str
    description: str | None = None
    total_problem_goal: int
    completed_problem_count: int
    total_problem_count: int
    legend_counts: RoadmapLegendCounts
    nodes: list[RoadmapNodeSummary]
    edges: list[RoadmapEdgeSchema]


class RoadmapListItem(BaseModel):
    slug: str
    title: str
    description: str | None = None


class RoadmapListResponse(BaseModel):
    roadmaps: list[RoadmapListItem]


class RoadmapTutorialItem(BaseModel):
    id: UUID
    title: str
    body: str | None = None
    resource_url: str | None = None
    completed: bool


class RoadmapTemplateItem(BaseModel):
    id: UUID
    title: str
    body: str | None = None
    code_language: str | None = None
    completed: bool


class RoadmapTemplateGroup(BaseModel):
    key: str
    title: str
    items: list[RoadmapTemplateItem]


class RoadmapPracticeItem(BaseModel):
    problem_id: UUID
    slug: str
    title: str
    difficulty: str
    source_url: str | None = None
    completed: bool
    has_personal_solution: bool


class RoadmapFlashcardItem(BaseModel):
    id: UUID
    front: str
    back: str
    tags: list[str] = Field(default_factory=list)
    problem_slug: str | None = None
    source_url: str | None = None
    last_reviewed_at: datetime | None = None


class RoadmapNodeDetailResponse(BaseModel):
    roadmap_slug: str
    node_slug: str
    title: str
    description: str | None = None
    difficulty: str
    completed_count: int
    total_count: int
    tutorials: list[RoadmapTutorialItem]
    template_groups: list[RoadmapTemplateGroup]
    practice: list[RoadmapPracticeItem]
    flashcards: list[RoadmapFlashcardItem]


class RoadmapItemCompletionRequest(BaseModel):
    completed: bool
