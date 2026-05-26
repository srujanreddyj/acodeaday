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
            "x": 860,
            "y": 20,
            "width": 280,
            "height": 110,
            "description": "Top-level roadmap for the major DSA families and the traversal paths between them.",
            "tutorials": [
                {
                    "title": "How to use the roadmap",
                    "body": "Treat each node as a learning container. Add documentation, problems, and flashcards over time. Progress is driven by the items attached to each node, not by the node itself.",
                }
            ],
            "templates": [],
            "problem_titles": [],
        },
        {
            "slug": "array",
            "title": "Array",
            "difficulty": "easy",
            "x": 520,
            "y": 220,
            "width": 190,
            "height": 90,
            "description": "Core array thinking: indexing, iteration, and transform patterns.",
            "tutorials": [],
            "templates": [],
            "problem_titles": ["Two Sum", "Best Time to Buy and Sell Stock"],
        },
        {
            "slug": "linked-list",
            "title": "Linked List",
            "difficulty": "easy",
            "x": 1260,
            "y": 220,
            "width": 210,
            "height": 90,
            "description": "Pointer manipulation, dummy nodes, and slow-fast traversal.",
            "tutorials": [],
            "templates": [],
            "problem_titles": ["Reverse Linked List", "Merge Two Sorted Lists"],
        },
        {
            "slug": "operations",
            "title": "Operations",
            "difficulty": "easy",
            "x": 350,
            "y": 430,
            "width": 250,
            "height": 380,
            "description": "Array preprocessing and representation transforms.",
            "tutorials": [],
            "templates": [],
            "problem_titles": [],
        },
        {
            "slug": "prefix-sum",
            "title": "Prefix Sum",
            "difficulty": "easy",
            "x": 390,
            "y": 480,
            "width": 170,
            "height": 84,
            "description": "Cumulative aggregates for range queries and sum constraints.",
            "tutorials": [],
            "templates": [],
            "problem_titles": ["Subarray Sum Equals K"],
        },
        {
            "slug": "diff-array",
            "title": "Diff Array",
            "difficulty": "easy",
            "x": 390,
            "y": 580,
            "width": 170,
            "height": 84,
            "description": "Range update encoding using differential representation.",
            "tutorials": [],
            "templates": [],
            "problem_titles": [],
        },
        {
            "slug": "two-d-array",
            "title": "2D Array",
            "difficulty": "easy",
            "x": 390,
            "y": 680,
            "width": 170,
            "height": 84,
            "description": "Grid indexing, traversal, and matrix transforms.",
            "tutorials": [],
            "templates": [],
            "problem_titles": ["Set Matrix Zeroes"],
        },
        {
            "slug": "basic-data-structure",
            "title": "Basic Data Structure",
            "difficulty": "easy",
            "x": 820,
            "y": 430,
            "width": 370,
            "height": 330,
            "description": "Foundation buckets for common implementation-level structures.",
            "tutorials": [],
            "templates": [],
            "problem_titles": [],
        },
        {
            "slug": "cycle-array",
            "title": "Cycle Array",
            "difficulty": "easy",
            "x": 860,
            "y": 530,
            "width": 170,
            "height": 84,
            "description": "Circular indexing and wrap-around state handling.",
            "tutorials": [],
            "templates": [],
            "problem_titles": [],
        },
        {
            "slug": "stack-and-queue",
            "title": "Stack & Queue",
            "difficulty": "med",
            "x": 1050,
            "y": 530,
            "width": 170,
            "height": 84,
            "description": "LIFO/FIFO modeling, monotonic stacks, and queue simulation.",
            "tutorials": [],
            "templates": [],
            "problem_titles": ["Valid Parentheses"],
        },
        {
            "slug": "hashing",
            "title": "Hashing",
            "difficulty": "med",
            "x": 860,
            "y": 650,
            "width": 170,
            "height": 84,
            "description": "Hash maps and sets for lookup, counting, and deduplication.",
            "tutorials": [],
            "templates": [],
            "problem_titles": ["Contains Duplicate"],
        },
        {
            "slug": "design",
            "title": "Design",
            "difficulty": "med",
            "x": 1050,
            "y": 650,
            "width": 170,
            "height": 84,
            "description": "Object/state design questions with constrained operations.",
            "tutorials": [],
            "templates": [],
            "problem_titles": ["Min Stack"],
        },
        {
            "slug": "array-two-pointer",
            "title": "Array Two Pointer",
            "difficulty": "easy",
            "x": 360,
            "y": 800,
            "width": 260,
            "height": 500,
            "description": "Sorted/unsorted array scan patterns and moving-window variants.",
            "tutorials": [],
            "templates": [],
            "problem_titles": [],
        },
        {
            "slug": "two-pointer",
            "title": "Two Pointer",
            "difficulty": "easy",
            "x": 400,
            "y": 850,
            "width": 180,
            "height": 84,
            "description": "Bidirectional and fast-slow pointer reasoning.",
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
            "slug": "sliding-window",
            "title": "Sliding Window",
            "difficulty": "med",
            "x": 400,
            "y": 960,
            "width": 180,
            "height": 84,
            "description": "Contiguous window maintenance with expand-shrink logic.",
            "tutorials": [],
            "templates": [],
            "problem_titles": ["Longest Substring Without Repeating Characters"],
        },
        {
            "slug": "binary-search",
            "title": "Binary Search",
            "difficulty": "med",
            "x": 400,
            "y": 1070,
            "width": 180,
            "height": 84,
            "description": "Search on answer space, boundaries, and monotonic predicates.",
            "tutorials": [],
            "templates": [],
            "problem_titles": ["Binary Search", "Search in Rotated Sorted Array"],
        },
        {
            "slug": "randomize",
            "title": "Randomize",
            "difficulty": "med",
            "x": 400,
            "y": 1180,
            "width": 180,
            "height": 84,
            "description": "Reservoir sampling and randomized set/data-structure patterns.",
            "tutorials": [],
            "templates": [],
            "problem_titles": [],
        },
        {
            "slug": "advanced-data-structure",
            "title": "Advanced Data Structure",
            "difficulty": "med",
            "x": 790,
            "y": 760,
            "width": 360,
            "height": 330,
            "description": "Tree-based and graph-based specialized structures.",
            "tutorials": [],
            "templates": [],
            "problem_titles": [],
        },
        {
            "slug": "bst",
            "title": "BST",
            "difficulty": "med",
            "x": 830,
            "y": 810,
            "width": 135,
            "height": 84,
            "description": "Ordered tree search and in-order reasoning.",
            "tutorials": [],
            "templates": [],
            "problem_titles": ["Validate Binary Search Tree"],
        },
        {
            "slug": "heap",
            "title": "Heap",
            "difficulty": "med",
            "x": 990,
            "y": 810,
            "width": 135,
            "height": 84,
            "description": "Priority queues for top-k, streaming, and greedy ordering.",
            "tutorials": [],
            "templates": [],
            "problem_titles": ["Kth Largest Element in an Array"],
        },
        {
            "slug": "trie",
            "title": "Trie",
            "difficulty": "med",
            "x": 830,
            "y": 930,
            "width": 135,
            "height": 84,
            "description": "Prefix trees for string/prefix indexing.",
            "tutorials": [],
            "templates": [],
            "problem_titles": ["Implement Trie (Prefix Tree)"],
        },
        {
            "slug": "graph",
            "title": "Graph",
            "difficulty": "hard",
            "x": 990,
            "y": 930,
            "width": 135,
            "height": 84,
            "description": "General adjacency modeling and traversal/state problems.",
            "tutorials": [],
            "templates": [],
            "problem_titles": ["Clone Graph"],
        },
        {
            "slug": "other",
            "title": "Other",
            "difficulty": "med",
            "x": 740,
            "y": 1160,
            "width": 220,
            "height": 300,
            "description": "Supporting categories that do not sit on the main traversal branches.",
            "tutorials": [],
            "templates": [],
            "problem_titles": [],
        },
        {
            "slug": "math",
            "title": "Math",
            "difficulty": "med",
            "x": 775,
            "y": 1215,
            "width": 150,
            "height": 84,
            "description": "Number manipulation, modular arithmetic, and geometry-lite reasoning.",
            "tutorials": [],
            "templates": [],
            "problem_titles": [],
        },
        {
            "slug": "greedy",
            "title": "Greedy",
            "difficulty": "med",
            "x": 775,
            "y": 1325,
            "width": 150,
            "height": 84,
            "description": "Local-choice optimization with exchange arguments.",
            "tutorials": [],
            "templates": [],
            "problem_titles": ["Jump Game"],
        },
        {
            "slug": "two-pointer-linked-list",
            "title": "Two Pointer",
            "difficulty": "easy",
            "x": 1410,
            "y": 500,
            "width": 180,
            "height": 84,
            "description": "Slow-fast pointer and pointer-meeting patterns on linked structures.",
            "tutorials": [],
            "templates": [],
            "problem_titles": ["Linked List Cycle"],
        },
        {
            "slug": "recursion",
            "title": "Recursion",
            "difficulty": "med",
            "x": 1410,
            "y": 650,
            "width": 180,
            "height": 84,
            "description": "Recursive decomposition before tree/general graph specialization.",
            "tutorials": [],
            "templates": [],
            "problem_titles": [],
        },
        {
            "slug": "binary-tree",
            "title": "Binary Tree",
            "difficulty": "med",
            "x": 1410,
            "y": 800,
            "width": 180,
            "height": 84,
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
            "slug": "recursive-traverse",
            "title": "Recursive Traverse",
            "difficulty": "med",
            "x": 1290,
            "y": 940,
            "width": 220,
            "height": 84,
            "description": "Pre/in/post-order traversal framing and subtree aggregation.",
            "tutorials": [],
            "templates": [],
            "problem_titles": [],
        },
        {
            "slug": "level-traverse",
            "title": "Level Traverse",
            "difficulty": "med",
            "x": 1560,
            "y": 940,
            "width": 210,
            "height": 84,
            "description": "Breadth-first level processing and queue-based traversal.",
            "tutorials": [],
            "templates": [],
            "problem_titles": ["Binary Tree Level Order Traversal"],
        },
        {
            "slug": "traverse-view",
            "title": "Traverse View",
            "difficulty": "hard",
            "x": 1080,
            "y": 1160,
            "width": 230,
            "height": 300,
            "description": "Traversal patterns where the order of visiting drives the solution.",
            "tutorials": [],
            "templates": [],
            "problem_titles": [],
        },
        {
            "slug": "backtracking",
            "title": "Backtracking",
            "difficulty": "hard",
            "x": 1110,
            "y": 1215,
            "width": 180,
            "height": 84,
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
                    "body": """```python
def backtrack(start, path):
    if done(path):
        result.append(path[:])
        return

    for i in range(start, len(nums)):
        path.append(nums[i])
        backtrack(i + 1, path)
        path.pop()
```""",
                    "code_language": "python",
                },
                {
                    "group_key": "dup-no-reuse",
                    "title": "Duplicate & Not Reusable",
                    "body": """```python
def backtrack(start, path):
    if done(path):
        result.append(path[:])
        return

    for i in range(start, len(nums)):
        if i > start and nums[i] == nums[i - 1]:
            continue
        path.append(nums[i])
        backtrack(i + 1, path)
        path.pop()
```""",
                    "code_language": "python",
                },
                {
                    "group_key": "no-dup-reusable",
                    "title": "No Duplicate & Reusable",
                    "body": """```python
def backtrack(start, total, path):
    if total == target:
        result.append(path[:])
        return
    if total > target:
        return

    for i in range(start, len(nums)):
        path.append(nums[i])
        backtrack(i, total + nums[i], path)
        path.pop()
```""",
                    "code_language": "python",
                },
            ],
            "problem_titles": ["Combination Sum", "Subsets"],
        },
        {
            "slug": "dfs",
            "title": "DFS",
            "difficulty": "hard",
            "x": 1110,
            "y": 1325,
            "width": 180,
            "height": 84,
            "description": "Depth-first traversal and search over trees, graphs, and implicit state spaces.",
            "tutorials": [
                {
                    "title": "DFS checklist",
                    "body": "Choose DFS when you need full traversal, connected-component discovery, or recursion-driven state. Mark visited consistently before exploring neighbors.",
                }
            ],
            "templates": [],
            "problem_titles": ["Number of Islands", "Max Area of Island"],
        },
        {
            "slug": "subproblem-view",
            "title": "Subproblem View",
            "difficulty": "hard",
            "x": 1360,
            "y": 1160,
            "width": 230,
            "height": 300,
            "description": "Problems decomposed into overlapping or independent subproblems.",
            "tutorials": [],
            "templates": [],
            "problem_titles": [],
        },
        {
            "slug": "divide-and-conquer",
            "title": "Divide & Conquer",
            "difficulty": "hard",
            "x": 1390,
            "y": 1215,
            "width": 180,
            "height": 84,
            "description": "Split-combine recursive structure where subproblems are mostly independent.",
            "tutorials": [],
            "templates": [],
            "problem_titles": [],
        },
        {
            "slug": "dp",
            "title": "DP",
            "difficulty": "hard",
            "x": 1390,
            "y": 1325,
            "width": 180,
            "height": 84,
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
                    "body": """```python
from functools import cache

@cache
def dp(i):
    if base_case(i):
        return base_value(i)
    return transition(dp, i)
```""",
                    "code_language": "python",
                }
            ],
            "problem_titles": ["Climbing Stairs", "House Robber"],
        },
        {
            "slug": "bfs",
            "title": "BFS",
            "difficulty": "hard",
            "x": 1720,
            "y": 1160,
            "width": 170,
            "height": 84,
            "description": "Breadth-first traversal and shortest path on unweighted state spaces.",
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
                    "body": """```python
from collections import deque

def bfs(start):
    queue = deque([start])
    visited = {start}
    while queue:
        node = queue.popleft()
        for neighbor in neighbors(node):
            if neighbor in visited:
                continue
            visited.add(neighbor)
            queue.append(neighbor)
```""",
                    "code_language": "python",
                }
            ],
            "problem_titles": [],
        },
        {
            "slug": "shortest-path",
            "title": "Shortest Path",
            "difficulty": "hard",
            "x": 1720,
            "y": 1325,
            "width": 190,
            "height": 84,
            "description": "Weighted path search and distance relaxation patterns.",
            "tutorials": [],
            "templates": [],
            "problem_titles": [],
        },
    ],
    "edges": [
        ("data-structure-and-algorithm", "array"),
        ("data-structure-and-algorithm", "linked-list"),
        ("array", "operations"),
        ("operations", "basic-data-structure"),
        ("operations", "array-two-pointer"),
        ("linked-list", "basic-data-structure"),
        ("linked-list", "two-pointer-linked-list"),
        ("two-pointer-linked-list", "recursion"),
        ("recursion", "binary-tree"),
        ("binary-tree", "advanced-data-structure"),
        ("binary-tree", "recursive-traverse"),
        ("binary-tree", "level-traverse"),
        ("recursive-traverse", "traverse-view"),
        ("recursive-traverse", "subproblem-view"),
        ("traverse-view", "dfs"),
        ("level-traverse", "bfs"),
        ("bfs", "shortest-path"),
        ("traverse-view", "backtracking"),
        ("subproblem-view", "divide-and-conquer"),
        ("subproblem-view", "dp"),
    ],
    "topic_aliases": {
        "arrays": "array",
        "prefix sum": "prefix-sum",
        "difference array": "diff-array",
        "2d array": "two-d-array",
        "matrix": "two-d-array",
        "cycle array": "cycle-array",
        "stack": "stack-and-queue",
        "queue": "stack-and-queue",
        "stack and queue": "stack-and-queue",
        "hash map": "hashing",
        "hashing": "hashing",
        "design": "design",
        "bst": "bst",
        "binary search tree": "bst",
        "heap": "heap",
        "priority queue": "heap",
        "trie": "trie",
        "graph": "graph",
        "math": "math",
        "greedy": "greedy",
        "two pointer": "two-pointer",
        "sliding window": "sliding-window",
        "binary search": "binary-search",
        "randomize": "randomize",
        "linked list": "linked-list",
        "recursion": "recursion",
        "tree": "binary-tree",
        "trees": "binary-tree",
        "recursive traverse": "recursive-traverse",
        "level traverse": "level-traverse",
        "traverse view": "traverse-view",
        "backtracking": "backtracking",
        "subproblem view": "subproblem-view",
        "divide and conquer": "divide-and-conquer",
        "dynamic programming": "dp",
        "dp": "dp",
        "depth first search": "dfs",
        "dfs": "dfs",
        "breadth first search": "bfs",
        "bfs": "bfs",
        "shortest path": "shortest-path",
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
        if roadmap and not await self._seed_requires_refresh(roadmap):
            return roadmap
        if roadmap:
            await self.session.delete(roadmap)
            await self.session.flush()

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

    async def _seed_requires_refresh(self, roadmap: Roadmap) -> bool:
        node_result = await self.session.execute(
            select(RoadmapNode).where(RoadmapNode.roadmap_id == roadmap.id)
        )
        existing_nodes = {node.slug: node for node in node_result.scalars().all()}
        seeded_nodes = {node["slug"]: node for node in SEED_ROADMAP["nodes"]}
        if set(existing_nodes) != set(seeded_nodes):
            return True

        for slug, seeded in seeded_nodes.items():
            existing = existing_nodes[slug]
            if (
                existing.title != seeded["title"]
                or existing.description != seeded.get("description")
                or existing.difficulty.value != seeded["difficulty"]
                or existing.x != seeded["x"]
                or existing.y != seeded["y"]
                or existing.width != seeded.get("width", 220)
                or existing.height != seeded.get("height", 96)
            ):
                return True

        edge_result = await self.session.execute(
            select(RoadmapEdge.source_node_id, RoadmapEdge.target_node_id).where(RoadmapEdge.roadmap_id == roadmap.id)
        )
        existing_edge_count = len(edge_result.all())
        return existing_edge_count != len(SEED_ROADMAP["edges"])

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
