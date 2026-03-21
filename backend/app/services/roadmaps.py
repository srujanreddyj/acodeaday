"""Services for roadmap data, progress computation, and personal-use seeding."""

from __future__ import annotations

import uuid
from collections import defaultdict
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.db.tables import (
    Problem,
    Roadmap,
    RoadmapEdge,
    RoadmapItem,
    RoadmapItemType,
    RoadmapNode,
    RoadmapNodeDifficulty,
    RoadmapNodeFlashcard,
    RoadmapNodeProblem,
    UserFlashcard,
    UserProblemNote,
    UserProgress,
    UserRoadmapItemProgress,
)
from app.schemas.roadmaps import (
    RoadmapEdgeSchema,
    RoadmapFlashcardItem,
    RoadmapLegendCounts,
    RoadmapListItem,
    RoadmapListResponse,
    RoadmapNodeDetailResponse,
    RoadmapNodeSummary,
    RoadmapOverviewResponse,
    RoadmapPracticeItem,
    RoadmapTemplateGroup,
    RoadmapTemplateItem,
    RoadmapTutorialItem,
)


SEED_ROADMAP: dict[str, Any] = {
    "slug": "dsa-roadmap",
    "title": "Data Structure & Algorithm",
    "description": "Personal roadmap for tutorials, code templates, practice, and flashcards.",
    "total_problem_goal": 170,
    "nodes": [
        {
            "slug": "data-structure-and-algorithm",
            "title": "Data Structure & Algorithm",
            "difficulty": "easy",
            "x": 740,
            "y": 20,
            "width": 260,
            "height": 108,
            "description": "Top-level map for the topics you want to revise.",
            "tutorials": [
                {
                    "title": "How to use this roadmap",
                    "body": "Pick one node at a time. Review the tutorial, scan the templates, solve or revisit a practice problem, then review the flashcards linked to that topic.",
                }
            ],
            "templates": [],
            "problem_titles": [],
        },
        {
            "slug": "array",
            "title": "Array",
            "difficulty": "easy",
            "x": 430,
            "y": 180,
            "description": "Array traversal, indexing, and transform patterns.",
            "tutorials": [
                {
                    "title": "Array fundamentals",
                    "body": "Arrays are about positional access. Most mistakes come from off-by-one handling, mutation during iteration, or missing a prefix/precompute opportunity.",
                }
            ],
            "templates": [],
            "problem_titles": ["Two Sum", "Best Time to Buy and Sell Stock"],
        },
        {
            "slug": "linked-list",
            "title": "Linked List",
            "difficulty": "easy",
            "x": 1100,
            "y": 180,
            "description": "Pointer mutation, traversal invariants, and dummy-node patterns.",
            "tutorials": [
                {
                    "title": "Linked list pointers",
                    "body": "Track `prev`, `curr`, and `next` explicitly. A dummy head removes many edge cases when the head itself can change.",
                }
            ],
            "templates": [],
            "problem_titles": ["Reverse Linked List", "Merge Two Sorted Lists"],
        },
        {
            "slug": "two-pointer",
            "title": "Two Pointer",
            "difficulty": "easy",
            "x": 430,
            "y": 340,
            "description": "Opposite-end and fast-slow pointer techniques.",
            "tutorials": [
                {
                    "title": "Two pointer invariant",
                    "body": "Define what each pointer means before coding. If the pointers move conditionally, write down the elimination rule that justifies the move.",
                }
            ],
            "templates": [],
            "problem_titles": ["Valid Palindrome", "Container With Most Water"],
        },
        {
            "slug": "binary-tree",
            "title": "Binary Tree",
            "difficulty": "med",
            "x": 1100,
            "y": 500,
            "description": "Recursive structure, state passing, and traversal selection.",
            "tutorials": [
                {
                    "title": "Binary tree framing",
                    "body": "Decide whether the return value is a property of the subtree or whether you need shared state outside recursion.",
                }
            ],
            "templates": [],
            "problem_titles": ["Maximum Depth of Binary Tree", "Invert Binary Tree"],
        },
        {
            "slug": "dfs",
            "title": "DFS",
            "difficulty": "hard",
            "x": 760,
            "y": 860,
            "description": "Depth-first traversal on trees, graphs, and implicit state spaces.",
            "tutorials": [
                {
                    "title": "DFS checklist",
                    "body": "Pick recursion or an explicit stack. Define visited/state transitions first, then define the base case and the work done before or after recursion.",
                }
            ],
            "templates": [
                {
                    "group_key": "tree-dfs",
                    "title": "Tree DFS template",
                    "body": "```python\ndef dfs(node):\n    if not node:\n        return\n    # pre-order work\n    dfs(node.left)\n    dfs(node.right)\n    # post-order work\n```",
                    "code_language": "python",
                }
            ],
            "problem_titles": ["Same Tree", "Subtree of Another Tree"],
        },
        {
            "slug": "bfs",
            "title": "BFS",
            "difficulty": "hard",
            "x": 1390,
            "y": 860,
            "description": "Level-order traversal and shortest-path traversal on unweighted graphs.",
            "tutorials": [
                {
                    "title": "BFS checklist",
                    "body": "BFS is about frontier expansion. Queue initialization and visited timing matter more than the loop body.",
                }
            ],
            "templates": [
                {
                    "group_key": "queue-bfs",
                    "title": "Queue BFS template",
                    "body": "```python\nfrom collections import deque\n\ndef bfs(start):\n    queue = deque([start])\n    visited = {start}\n    while queue:\n        node = queue.popleft()\n        for neighbor in neighbors(node):\n            if neighbor in visited:\n                continue\n            visited.add(neighbor)\n            queue.append(neighbor)\n```",
                    "code_language": "python",
                }
            ],
            "problem_titles": ["Binary Tree Level Order Traversal"],
        },
        {
            "slug": "backtracking",
            "title": "Backtracking",
            "difficulty": "hard",
            "x": 760,
            "y": 1030,
            "description": "State-space exploration with choose, recurse, unchoose.",
            "tutorials": [
                {
                    "title": "Backtracking framework",
                    "body": "Backtracking is exhaustive search with pruning. Make the mutable path and the undo step explicit before optimizing.",
                }
            ],
            "templates": [
                {
                    "group_key": "no-dup-no-reuse",
                    "title": "No Duplicate & Not Reusable",
                    "body": "```python\ndef backtrack(start, path):\n    if done(path):\n        result.append(path[:])\n        return\n\n    for i in range(start, len(nums)):\n        path.append(nums[i])\n        backtrack(i + 1, path)\n        path.pop()\n```",
                    "code_language": "python",
                },
                {
                    "group_key": "dup-no-reuse",
                    "title": "Duplicate & Not Reusable",
                    "body": "```python\ndef backtrack(start, path):\n    if done(path):\n        result.append(path[:])\n        return\n\n    for i in range(start, len(nums)):\n        if i > start and nums[i] == nums[i - 1]:\n            continue\n        path.append(nums[i])\n        backtrack(i + 1, path)\n        path.pop()\n```",
                    "code_language": "python",
                },
            ],
            "problem_titles": ["Combination Sum", "Subsets"],
        },
        {
            "slug": "dp",
            "title": "DP",
            "difficulty": "hard",
            "x": 1080,
            "y": 1030,
            "description": "State design, transitions, and memoization/tabulation tradeoffs.",
            "tutorials": [
                {
                    "title": "DP checklist",
                    "body": "Write the state in plain English first. Then define the transition and the base case. Memoization is usually the fastest way to validate the recurrence.",
                }
            ],
            "templates": [
                {
                    "group_key": "memo-dp",
                    "title": "Memoization template",
                    "body": "```python\nfrom functools import cache\n\n@cache\ndef dp(i):\n    if base_case(i):\n        return base_value(i)\n    return transition(dp, i)\n```",
                    "code_language": "python",
                }
            ],
            "problem_titles": ["Climbing Stairs", "House Robber"],
        },
    ],
    "edges": [
        ("data-structure-and-algorithm", "array"),
        ("data-structure-and-algorithm", "linked-list"),
        ("array", "two-pointer"),
        ("linked-list", "binary-tree"),
        ("binary-tree", "dfs"),
        ("binary-tree", "bfs"),
        ("dfs", "backtracking"),
        ("dfs", "dp"),
    ],
    "topic_aliases": {
        "arrays": "array",
        "hash map": "array",
        "tree": "binary-tree",
        "trees": "binary-tree",
        "depth first search": "dfs",
        "breadth first search": "bfs",
        "dynamic programming": "dp",
    },
}


def normalize_topic_slug(value: str) -> str:
    normalized = "-".join(value.strip().lower().replace("/", " ").split())
    return normalized


class RoadmapService:
    """Roadmap query and seed service."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_roadmaps(self) -> RoadmapListResponse:
        result = await self.session.execute(
            select(Roadmap).where(Roadmap.is_active.is_(True)).order_by(Roadmap.title)
        )
        items = [
            RoadmapListItem(slug=roadmap.slug, title=roadmap.title, description=roadmap.description)
            for roadmap in result.scalars().all()
        ]
        return RoadmapListResponse(roadmaps=items)

    async def get_roadmap_by_slug(self, slug: str) -> Roadmap | None:
        result = await self.session.execute(select(Roadmap).where(Roadmap.slug == slug))
        return result.scalar_one_or_none()

    async def ensure_seed_data(self) -> Roadmap:
        roadmap = await self.get_roadmap_by_slug(SEED_ROADMAP["slug"])
        if roadmap:
            return roadmap

        roadmap = Roadmap(
            slug=SEED_ROADMAP["slug"],
            title=SEED_ROADMAP["title"],
            description=SEED_ROADMAP["description"],
            total_problem_goal=SEED_ROADMAP["total_problem_goal"],
            is_active=True,
        )
        self.session.add(roadmap)
        await self.session.flush()

        node_ids: dict[str, uuid.UUID] = {}
        for node_data in SEED_ROADMAP["nodes"]:
            node = RoadmapNode(
                roadmap_id=roadmap.id,
                slug=node_data["slug"],
                title=node_data["title"],
                description=node_data.get("description"),
                difficulty=RoadmapNodeDifficulty(node_data["difficulty"]),
                x=node_data["x"],
                y=node_data["y"],
                width=node_data.get("width", 220),
                height=node_data.get("height", 96),
            )
            self.session.add(node)
            await self.session.flush()
            node_ids[node.slug] = node.id

            sort_order = 0
            for tutorial in node_data.get("tutorials", []):
                self.session.add(
                    RoadmapItem(
                        roadmap_node_id=node.id,
                        item_type=RoadmapItemType.TUTORIAL,
                        title=tutorial["title"],
                        body=tutorial.get("body"),
                        resource_url=tutorial.get("resource_url"),
                        sort_order=sort_order,
                    )
                )
                sort_order += 1

            for template in node_data.get("templates", []):
                self.session.add(
                    RoadmapItem(
                        roadmap_node_id=node.id,
                        item_type=RoadmapItemType.TEMPLATE,
                        title=template["title"],
                        body=template.get("body"),
                        code_language=template.get("code_language"),
                        group_key=template.get("group_key"),
                        sort_order=sort_order,
                    )
                )
                sort_order += 1

        for source_slug, target_slug in SEED_ROADMAP["edges"]:
            self.session.add(
                RoadmapEdge(
                    roadmap_id=roadmap.id,
                    source_node_id=node_ids[source_slug],
                    target_node_id=node_ids[target_slug],
                )
            )

        await self.session.flush()
        await self._link_seed_problems(roadmap.id)
        await self.session.commit()
        await self.session.refresh(roadmap)
        return roadmap

    async def _link_seed_problems(self, roadmap_id: uuid.UUID) -> None:
        node_result = await self.session.execute(
            select(RoadmapNode).where(RoadmapNode.roadmap_id == roadmap_id)
        )
        nodes = {node.slug: node for node in node_result.scalars().all()}

        title_to_problem: dict[str, Problem] = {}
        problem_result = await self.session.execute(select(Problem))
        for problem in problem_result.scalars().all():
            title_to_problem[problem.title.lower()] = problem

        for node_data in SEED_ROADMAP["nodes"]:
            node = nodes[node_data["slug"]]
            for index, title in enumerate(node_data.get("problem_titles", [])):
                problem = title_to_problem.get(title.lower())
                if not problem:
                    continue
                self.session.add(
                    RoadmapNodeProblem(
                        roadmap_node_id=node.id,
                        problem_id=problem.id,
                        sort_order=index,
                    )
                )

    async def get_overview(self, roadmap_slug: str, user_id: str) -> RoadmapOverviewResponse:
        roadmap = await self._require_roadmap(roadmap_slug)
        node_result = await self.session.execute(
            select(RoadmapNode).where(RoadmapNode.roadmap_id == roadmap.id).order_by(RoadmapNode.y, RoadmapNode.x)
        )
        nodes = node_result.scalars().all()
        node_counts = await self._compute_node_counts(nodes, user_id)

        target_node = aliased(RoadmapNode)
        edge_result = await self.session.execute(
            select(RoadmapEdge, RoadmapNode.slug, target_node.slug)
            .join(RoadmapNode, RoadmapNode.id == RoadmapEdge.source_node_id)
            .join(target_node, target_node.id == RoadmapEdge.target_node_id)
            .where(RoadmapEdge.roadmap_id == roadmap.id)
        )
        edges = [
            RoadmapEdgeSchema(source_node_slug=source_slug, target_node_slug=target_slug)
            for _, source_slug, target_slug in edge_result.all()
        ]

        legend = RoadmapLegendCounts()
        total_problem_count = 0
        completed_problem_count = 0
        node_summaries: list[RoadmapNodeSummary] = []
        for node in nodes:
            if node.difficulty == RoadmapNodeDifficulty.EASY:
                legend.easy += 1
            elif node.difficulty == RoadmapNodeDifficulty.MEDIUM:
                legend.med += 1
            else:
                legend.hard += 1

            counts = node_counts[node.id]
            total_problem_count += counts["practice_total"]
            completed_problem_count += counts["practice_completed"]
            node_summaries.append(
                RoadmapNodeSummary(
                    slug=node.slug,
                    title=node.title,
                    difficulty=node.difficulty.value,
                    x=node.x,
                    y=node.y,
                    width=node.width,
                    height=node.height,
                    completed_count=counts["completed"],
                    total_count=counts["total"],
                )
            )

        return RoadmapOverviewResponse(
            slug=roadmap.slug,
            title=roadmap.title,
            description=roadmap.description,
            total_problem_goal=roadmap.total_problem_goal,
            completed_problem_count=completed_problem_count,
            total_problem_count=total_problem_count,
            legend_counts=legend,
            nodes=node_summaries,
            edges=edges,
        )

    async def get_node_detail(self, roadmap_slug: str, node_slug: str, user_id: str) -> RoadmapNodeDetailResponse:
        roadmap = await self._require_roadmap(roadmap_slug)
        result = await self.session.execute(
            select(RoadmapNode).where(RoadmapNode.roadmap_id == roadmap.id, RoadmapNode.slug == node_slug)
        )
        node = result.scalar_one_or_none()
        if not node:
            raise ValueError(f"Roadmap node '{node_slug}' not found")

        counts = (await self._compute_node_counts([node], user_id))[node.id]
        tutorials = await self._get_tutorials(node.id, user_id)
        template_groups = await self._get_template_groups(node.id, user_id)
        practice = await self._get_practice(node.id, user_id)
        flashcards = await self._get_flashcards(node.id, user_id)

        return RoadmapNodeDetailResponse(
            roadmap_slug=roadmap.slug,
            node_slug=node.slug,
            title=node.title,
            description=node.description,
            difficulty=node.difficulty.value,
            completed_count=counts["completed"],
            total_count=counts["total"],
            tutorials=tutorials,
            template_groups=template_groups,
            practice=practice,
            flashcards=flashcards,
        )

    async def set_item_completion(self, item_id: uuid.UUID, user_id: str, completed: bool) -> None:
        result = await self.session.execute(
            select(UserRoadmapItemProgress).where(
                UserRoadmapItemProgress.user_id == user_id,
                UserRoadmapItemProgress.roadmap_item_id == item_id,
            )
        )
        record = result.scalar_one_or_none()
        if not record:
            record = UserRoadmapItemProgress(
                user_id=user_id,
                roadmap_item_id=item_id,
                completed=completed,
                completed_at=datetime.now(UTC).replace(tzinfo=None) if completed else None,
            )
            self.session.add(record)
        else:
            record.completed = completed
            record.completed_at = datetime.now(UTC).replace(tzinfo=None) if completed else None
        await self.session.commit()

    async def link_flashcard_to_node(self, *, flashcard_id: uuid.UUID, node_slug: str, roadmap_slug: str) -> None:
        roadmap = await self._require_roadmap(roadmap_slug)
        node_result = await self.session.execute(
            select(RoadmapNode).where(RoadmapNode.roadmap_id == roadmap.id, RoadmapNode.slug == node_slug)
        )
        node = node_result.scalar_one_or_none()
        if not node:
            raise ValueError(f"Roadmap node '{node_slug}' not found")

        existing = await self.session.execute(
            select(RoadmapNodeFlashcard).where(
                RoadmapNodeFlashcard.roadmap_node_id == node.id,
                RoadmapNodeFlashcard.flashcard_id == flashcard_id,
            )
        )
        if not existing.scalar_one_or_none():
            self.session.add(RoadmapNodeFlashcard(roadmap_node_id=node.id, flashcard_id=flashcard_id))
            await self.session.flush()

    async def replace_flashcard_topics(self, *, flashcard_id: uuid.UUID, roadmap_slug: str, node_slugs: list[str]) -> None:
        roadmap = await self._require_roadmap(roadmap_slug)
        await self.session.execute(delete(RoadmapNodeFlashcard).where(RoadmapNodeFlashcard.flashcard_id == flashcard_id))
        if not node_slugs:
            await self.session.flush()
            return
        result = await self.session.execute(
            select(RoadmapNode).where(RoadmapNode.roadmap_id == roadmap.id, RoadmapNode.slug.in_(node_slugs))
        )
        for node in result.scalars().all():
            self.session.add(RoadmapNodeFlashcard(roadmap_node_id=node.id, flashcard_id=flashcard_id))
        await self.session.flush()

    async def _require_roadmap(self, slug: str) -> Roadmap:
        roadmap = await self.get_roadmap_by_slug(slug)
        if not roadmap:
            roadmap = await self.ensure_seed_data()
        if roadmap.slug != slug:
            roadmaps = await self.list_roadmaps()
            raise ValueError(f"Roadmap '{slug}' not found. Available: {[item.slug for item in roadmaps.roadmaps]}")
        return roadmap

    async def _get_tutorials(self, node_id: uuid.UUID, user_id: str) -> list[RoadmapTutorialItem]:
        result = await self.session.execute(
            select(RoadmapItem, UserRoadmapItemProgress)
            .outerjoin(
                UserRoadmapItemProgress,
                (UserRoadmapItemProgress.roadmap_item_id == RoadmapItem.id)
                & (UserRoadmapItemProgress.user_id == user_id),
            )
            .where(RoadmapItem.roadmap_node_id == node_id)
            .where(RoadmapItem.item_type == RoadmapItemType.TUTORIAL)
            .order_by(RoadmapItem.sort_order, RoadmapItem.title)
        )
        items: list[RoadmapTutorialItem] = []
        for item, progress in result.all():
            items.append(
                RoadmapTutorialItem(
                    id=item.id,
                    title=item.title,
                    body=item.body,
                    resource_url=item.resource_url,
                    completed=bool(progress and progress.completed),
                )
            )
        return items

    async def _get_template_groups(self, node_id: uuid.UUID, user_id: str) -> list[RoadmapTemplateGroup]:
        result = await self.session.execute(
            select(RoadmapItem, UserRoadmapItemProgress)
            .outerjoin(
                UserRoadmapItemProgress,
                (UserRoadmapItemProgress.roadmap_item_id == RoadmapItem.id)
                & (UserRoadmapItemProgress.user_id == user_id),
            )
            .where(RoadmapItem.roadmap_node_id == node_id)
            .where(RoadmapItem.item_type == RoadmapItemType.TEMPLATE)
            .order_by(RoadmapItem.group_key, RoadmapItem.sort_order, RoadmapItem.title)
        )
        grouped: dict[str, list[RoadmapTemplateItem]] = defaultdict(list)
        titles: dict[str, str] = {}
        for item, progress in result.all():
            key = item.group_key or item.title
            titles.setdefault(key, item.title)
            grouped[key].append(
                RoadmapTemplateItem(
                    id=item.id,
                    title=item.title,
                    body=item.body,
                    code_language=item.code_language,
                    completed=bool(progress and progress.completed),
                )
            )
        return [RoadmapTemplateGroup(key=key, title=titles[key], items=items) for key, items in grouped.items()]

    async def _get_practice(self, node_id: uuid.UUID, user_id: str) -> list[RoadmapPracticeItem]:
        result = await self.session.execute(
            select(RoadmapNodeProblem, Problem, UserProgress, UserProblemNote)
            .join(Problem, Problem.id == RoadmapNodeProblem.problem_id)
            .outerjoin(
                UserProgress,
                (UserProgress.problem_id == Problem.id) & (UserProgress.user_id == user_id),
            )
            .outerjoin(
                UserProblemNote,
                (UserProblemNote.problem_id == Problem.id) & (UserProblemNote.user_id == user_id),
            )
            .where(RoadmapNodeProblem.roadmap_node_id == node_id)
            .order_by(RoadmapNodeProblem.sort_order, Problem.sequence_number)
        )
        items: list[RoadmapPracticeItem] = []
        for _, problem, progress, note in result.all():
            items.append(
                RoadmapPracticeItem(
                    problem_id=problem.id,
                    slug=problem.slug,
                    title=problem.title,
                    difficulty=problem.difficulty.value,
                    source_url=note.source_url if note else None,
                    completed=bool(progress and progress.times_solved > 0),
                    has_personal_solution=bool(note and note.personal_solution),
                )
            )
        return items

    async def _get_flashcards(self, node_id: uuid.UUID, user_id: str) -> list[RoadmapFlashcardItem]:
        result = await self.session.execute(
            select(RoadmapNodeFlashcard, UserFlashcard, Problem.slug)
            .join(UserFlashcard, UserFlashcard.id == RoadmapNodeFlashcard.flashcard_id)
            .outerjoin(Problem, Problem.id == UserFlashcard.problem_id)
            .where(RoadmapNodeFlashcard.roadmap_node_id == node_id)
            .where(UserFlashcard.user_id == user_id)
            .where(UserFlashcard.is_active.is_(True))
            .order_by(UserFlashcard.updated_at.desc())
        )
        return [
            RoadmapFlashcardItem(
                id=flashcard.id,
                front=flashcard.front,
                back=flashcard.back,
                tags=flashcard.tags or [],
                problem_slug=problem_slug,
                source_url=flashcard.source_url,
                last_reviewed_at=flashcard.last_reviewed_at,
            )
            for _, flashcard, problem_slug in result.all()
        ]

    async def _compute_node_counts(self, nodes: list[RoadmapNode], user_id: str) -> dict[uuid.UUID, dict[str, int]]:
        node_ids = [node.id for node in nodes]
        counts = {
            node.id: {"completed": 0, "total": 0, "practice_total": 0, "practice_completed": 0}
            for node in nodes
        }
        if not node_ids:
            return counts

        item_result = await self.session.execute(
            select(RoadmapItem, UserRoadmapItemProgress)
            .outerjoin(
                UserRoadmapItemProgress,
                (UserRoadmapItemProgress.roadmap_item_id == RoadmapItem.id)
                & (UserRoadmapItemProgress.user_id == user_id),
            )
            .where(RoadmapItem.roadmap_node_id.in_(node_ids))
        )
        for item, progress in item_result.all():
            counts[item.roadmap_node_id]["total"] += 1
            if progress and progress.completed:
                counts[item.roadmap_node_id]["completed"] += 1

        practice_result = await self.session.execute(
            select(RoadmapNodeProblem.roadmap_node_id, UserProgress.times_solved)
            .join(Problem, Problem.id == RoadmapNodeProblem.problem_id)
            .outerjoin(
                UserProgress,
                (UserProgress.problem_id == Problem.id) & (UserProgress.user_id == user_id),
            )
            .where(RoadmapNodeProblem.roadmap_node_id.in_(node_ids))
        )
        for node_id, times_solved in practice_result.all():
            counts[node_id]["total"] += 1
            counts[node_id]["practice_total"] += 1
            if times_solved and times_solved > 0:
                counts[node_id]["completed"] += 1
                counts[node_id]["practice_completed"] += 1

        flashcard_result = await self.session.execute(
            select(RoadmapNodeFlashcard.roadmap_node_id, UserFlashcard.last_reviewed_at)
            .join(UserFlashcard, UserFlashcard.id == RoadmapNodeFlashcard.flashcard_id)
            .where(RoadmapNodeFlashcard.roadmap_node_id.in_(node_ids))
            .where(UserFlashcard.user_id == user_id)
            .where(UserFlashcard.is_active.is_(True))
        )
        for node_id, last_reviewed_at in flashcard_result.all():
            counts[node_id]["total"] += 1
            if last_reviewed_at is not None:
                counts[node_id]["completed"] += 1

        return counts

    def resolve_topic_slugs(self, raw_topics: list[str]) -> list[str]:
        aliases = {normalize_topic_slug(k): v for k, v in SEED_ROADMAP["topic_aliases"].items()}
        valid = {node["slug"] for node in SEED_ROADMAP["nodes"]}
        resolved: list[str] = []
        for value in raw_topics:
            normalized = normalize_topic_slug(value)
            slug = aliases.get(normalized, normalized)
            if slug in valid and slug not in resolved:
                resolved.append(slug)
        return resolved

    async def link_problem_to_nodes(self, *, problem_id: uuid.UUID, roadmap_slug: str, node_slugs: list[str]) -> None:
        roadmap = await self._require_roadmap(roadmap_slug)
        if not node_slugs:
            return
        result = await self.session.execute(
            select(RoadmapNode).where(RoadmapNode.roadmap_id == roadmap.id, RoadmapNode.slug.in_(node_slugs))
        )
        existing_result = await self.session.execute(
            select(RoadmapNodeProblem).where(RoadmapNodeProblem.problem_id == problem_id)
        )
        existing_node_ids = {row.roadmap_node_id for row in existing_result.scalars().all()}
        sort_order = 0
        for node in result.scalars().all():
            if node.id in existing_node_ids:
                continue
            self.session.add(
                RoadmapNodeProblem(
                    roadmap_node_id=node.id,
                    problem_id=problem_id,
                    sort_order=sort_order,
                )
            )
            sort_order += 1
        await self.session.flush()
