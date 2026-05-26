"""Import a DSA export bundle into acodeaday.

The bundle is expected to contain:
- a title-oriented CSV export
- a URL-oriented CSV export
- a directory of Markdown notes for individual problems

Example:
    uv run python scripts/import_dsa_bundle.py \
      --bundle-root ~/Downloads/dsa \
      --user-id <supabase-user-id> \
      --create-flashcards
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import re
import sys
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from sqlalchemy import func, select, text

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.db.connection import AsyncSessionLocal
from app.db.tables import (
    Difficulty,
    Problem,
    RoadmapNode,
    RoadmapNodeFlashcard,
    RoadmapNodeProblem,
    UserFlashcard,
    UserProblemNote,
    UserProgress,
)
from app.services.roadmaps import RoadmapService

DEFAULT_BUNDLE_ROOT = Path("~/Downloads/dsa").expanduser()
TITLE_CSV_GLOB = "LeetCode DSA*.csv"
ALL_CSV_SUFFIX = "_all.csv"
MARKDOWN_DIR_PREFIX = "LeetCode DSA"
LOCAL_TOPIC_HINTS = {
    "two pointers": ["two-pointer"],
    "top k elements": ["heap"],
    "top-k elements": ["heap"],
    "hash map": ["hashing"],
    "hash maps": ["hashing"],
    "fast slow pointers": ["two-pointer", "linked-list"],
    "monotonic stack": ["stack-and-queue"],
    "stack": ["stack-and-queue"],
    "queue": ["stack-and-queue"],
    "intervals": ["array"],
    "trees": ["binary-tree"],
    "tree bfs": ["level-traverse", "bfs", "binary-tree"],
    "tree dfs": ["dfs", "binary-tree"],
    "topological sort": ["graph", "bfs"],
    "union find": ["graph"],
    "prefix sum": ["prefix-sum"],
    "backtracking": ["backtracking"],
    "dynamic programming": ["dp"],
    "binary tree": ["binary-tree"],
    "linked list": ["linked-list"],
    "string": ["array"],
    "hash table": ["hashing"],
    "sorting": ["array"],
    "sort": ["array"],
}
SKIP_MARKDOWN_TITLES = {"notes of solved questions"}


@dataclass
class BundleRecord:
    title: str
    normalized_title: str
    source_url: str | None = None
    topic_values: set[str] = field(default_factory=set)
    template_values: set[str] = field(default_factory=set)
    companies: set[str] = field(default_factory=set)
    comments: list[str] = field(default_factory=list)
    difficulty_raw: str | None = None
    solved_on_first_try: str | None = None
    revise: bool = False
    solved_at: datetime | None = None
    markdown_body: str | None = None
    markdown_path: str | None = None
    flashcard_front: str | None = None
    flashcard_back: str | None = None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import DSA bundle into acodeaday")
    parser.add_argument("--bundle-root", type=Path, default=DEFAULT_BUNDLE_ROOT)
    parser.add_argument("--roadmap-slug", default="dsa-roadmap")
    parser.add_argument("--user-id", default=None, help="Optional single user id. If omitted, the importer applies personal data to all known users.")
    parser.add_argument("--create-flashcards", action="store_true")
    parser.add_argument("--flashcards-from", choices=["revise", "all"], default="revise")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def normalize_title(value: str) -> str:
    value = value.strip()
    value = re.sub(r"\s+[0-9a-f]{32}$", "", value, flags=re.IGNORECASE)
    value = re.sub(r"\s+\([^)]*\)$", "", value)
    value = re.sub(r"[^a-zA-Z0-9]+", "-", value.lower()).strip("-")
    return value


def slugify_title(title: str) -> str:
    return normalize_title(title)


def parse_difficulty(raw: str | None) -> Difficulty:
    value = (raw or "").strip().lower()
    if "hard" in value:
        return Difficulty.HARD
    if "easy" in value:
        return Difficulty.EASY
    return Difficulty.MEDIUM


def parse_date_solved(raw: str | None) -> datetime | None:
    value = (raw or "").strip()
    if not value:
        return None
    for fmt in ("%B %d, %Y", "%b %d, %Y"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return None


def split_multi(value: str | None) -> list[str]:
    if not value:
        return []
    parts = re.split(r"\s*(?:,|/|\||&|;)\s*", value)
    return [part.strip() for part in parts if part.strip()]


def extract_title_from_url(url: str) -> str | None:
    match = re.search(r"leetcode\.com/problems/([^/]+)/", url)
    if not match:
        return None
    slug = match.group(1).strip("/")
    if not slug:
        return None
    return " ".join(word.capitalize() for word in slug.split("-"))


def resolve_csv_paths(bundle_root: Path) -> tuple[Path, Path, Path]:
    if not bundle_root.exists():
        raise FileNotFoundError(bundle_root)

    csv_paths = sorted(path for path in bundle_root.glob(TITLE_CSV_GLOB) if path.suffix.lower() == ".csv")
    title_csv = next((path for path in csv_paths if not path.name.endswith(ALL_CSV_SUFFIX)), None)
    all_csv = next((path for path in csv_paths if path.name.endswith(ALL_CSV_SUFFIX)), None)
    markdown_dir = next((path for path in bundle_root.iterdir() if path.is_dir() and path.name.startswith(MARKDOWN_DIR_PREFIX)), None)

    if not title_csv or not all_csv or not markdown_dir:
        raise FileNotFoundError(
            f"Expected title csv, all csv, and markdown directory under {bundle_root}"
        )
    return title_csv, all_csv, markdown_dir


def parse_markdown_file(path: Path) -> BundleRecord | None:
    text = path.read_text(encoding="utf-8", errors="ignore")
    lines = text.splitlines()
    if not lines or not lines[0].startswith("# "):
        return None
    title = lines[0][2:].strip()
    if normalize_title(title) in SKIP_MARKDOWN_TITLES:
        return None

    metadata: dict[str, str] = {}
    body_start = 1
    for index, line in enumerate(lines[1:], start=1):
        stripped = line.strip()
        if not stripped:
            body_start = index + 1
            continue
        if stripped.startswith("#") and not re.match(r"^[A-Za-z][A-Za-z ]*:\s*", stripped):
            body_start = index
            break
        if ":" in stripped:
            key, value = stripped.split(":", 1)
            if key.strip() and value.strip():
                metadata[key.strip().lower()] = value.strip()
                body_start = index + 1
                continue
        body_start = index
        break

    body = "\n".join(lines[body_start:]).strip() or None
    normalized = normalize_title(title)
    front = title
    back = body or "Imported from DSA notes."
    return BundleRecord(
        title=title,
        normalized_title=normalized,
        topic_values=set(split_multi(metadata.get("topic"))),
        template_values=set(split_multi(metadata.get("template"))),
        companies=set(split_multi(metadata.get("companies"))),
        comments=[],
        difficulty_raw=metadata.get("difficulty"),
        solved_on_first_try=metadata.get("solved on first try"),
        revise=(metadata.get("revise", "").strip().lower() == "y"),
        solved_at=parse_date_solved(metadata.get("date solved")),
        markdown_body=body,
        markdown_path=str(path),
        flashcard_front=front,
        flashcard_back=back,
    )


def upsert_record(records: dict[str, BundleRecord], incoming: BundleRecord) -> None:
    existing = records.get(incoming.normalized_title)
    if existing is None:
        records[incoming.normalized_title] = incoming
        return

    existing.source_url = existing.source_url or incoming.source_url
    existing.topic_values.update(incoming.topic_values)
    existing.template_values.update(incoming.template_values)
    existing.companies.update(incoming.companies)
    existing.comments.extend(x for x in incoming.comments if x)
    existing.difficulty_raw = existing.difficulty_raw or incoming.difficulty_raw
    existing.solved_on_first_try = existing.solved_on_first_try or incoming.solved_on_first_try
    existing.revise = existing.revise or incoming.revise
    existing.solved_at = existing.solved_at or incoming.solved_at
    existing.markdown_body = existing.markdown_body or incoming.markdown_body
    existing.markdown_path = existing.markdown_path or incoming.markdown_path
    existing.flashcard_front = existing.flashcard_front or incoming.flashcard_front
    existing.flashcard_back = existing.flashcard_back or incoming.flashcard_back


def load_bundle_records(title_csv: Path, all_csv: Path, markdown_dir: Path) -> dict[str, BundleRecord]:
    records: dict[str, BundleRecord] = {}

    with title_csv.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            title = (row.get("Question") or "").strip()
            if not title or normalize_title(title) in SKIP_MARKDOWN_TITLES:
                continue
            record = BundleRecord(
                title=title,
                normalized_title=normalize_title(title),
                topic_values=set(split_multi(row.get("Topic"))),
                template_values=set(split_multi(row.get("Template"))),
                companies=set(split_multi(row.get("Companies"))),
                comments=[(row.get("Other Comments") or "").strip()] if (row.get("Other Comments") or "").strip() else [],
                difficulty_raw=(row.get("Difficulty") or "").strip() or None,
                solved_on_first_try=(row.get("Solved on first try") or "").strip() or None,
                revise=(row.get("Revise", "").strip().lower() == "y"),
                solved_at=parse_date_solved(row.get("Date Solved")),
            )
            upsert_record(records, record)

    with all_csv.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            url = (row.get("Question") or "").strip()
            title = extract_title_from_url(url) or url
            if not title or normalize_title(title) in SKIP_MARKDOWN_TITLES:
                continue
            record = BundleRecord(
                title=title,
                normalized_title=normalize_title(title),
                source_url=url if url.startswith("http") else None,
                topic_values=set(split_multi(row.get("Topic"))),
                template_values=set(split_multi(row.get("Template"))),
                companies=set(split_multi(row.get("Companies"))),
                comments=[(row.get("Other Comments") or "").strip()] if (row.get("Other Comments") or "").strip() else [],
                difficulty_raw=(row.get("Difficulty") or "").strip() or None,
                solved_on_first_try=(row.get("Solved on first try") or "").strip() or None,
                revise=(row.get("Revise", "").strip().lower() == "y"),
                solved_at=parse_date_solved(row.get("Date Solved")),
            )
            upsert_record(records, record)

    for path in sorted(markdown_dir.glob("*.md")):
        record = parse_markdown_file(path)
        if record:
            upsert_record(records, record)

    reparsed: dict[str, BundleRecord] = {}
    for record in records.values():
        if record.title.startswith("http") and record.source_url:
            parsed_title = extract_title_from_url(record.source_url)
            if parsed_title:
                record.title = parsed_title
                record.normalized_title = normalize_title(parsed_title)
        upsert_record(reparsed, record)

    return reparsed


def topic_candidates(record: BundleRecord) -> list[str]:
    values: list[str] = []
    values.extend(record.topic_values)
    values.extend(record.template_values)
    for raw in list(record.topic_values) + list(record.template_values):
        normalized = raw.strip().lower()
        values.extend(LOCAL_TOPIC_HINTS.get(normalized, []))

    title = record.title.lower()
    if "binary tree" in title or title.startswith("tree traversal"):
        values.append("binary-tree")
    if "bst" in title or "binary search tree" in title:
        values.append("bst")
    if "linked list" in title:
        values.append("linked-list")

    return [value for value in values if value]


def build_description(record: BundleRecord) -> str:
    if record.markdown_body:
        return record.markdown_body[:8000]
    parts = []
    if record.template_values:
        parts.append(f"Templates: {', '.join(sorted(record.template_values))}")
    if record.comments:
        parts.append("Notes: " + " ".join(record.comments))
    return "\n\n".join(parts) or "Imported from DSA bundle."


def build_revision_notes(record: BundleRecord) -> str | None:
    parts: list[str] = []
    if record.markdown_body:
        parts.append(record.markdown_body)
    if record.comments:
        parts.append("Other Comments: " + " | ".join(record.comments))
    if record.template_values:
        parts.append("Templates: " + ", ".join(sorted(record.template_values)))
    if record.companies:
        parts.append("Companies: " + ", ".join(sorted(record.companies)))
    return "\n\n".join(part for part in parts if part).strip() or None


async def resolve_target_user_ids(session, explicit_user_id: str | None) -> list[str]:
    if explicit_user_id:
        return [explicit_user_id]

    user_ids: set[str] = set()

    auth_result = await session.execute(text("select id::text from auth.users"))
    user_ids.update(row[0] for row in auth_result if row[0])

    for model in (UserProblemNote, UserProgress, UserFlashcard):
        result = await session.execute(select(model.user_id).distinct())
        user_ids.update(value for value in result.scalars().all() if value)

    return sorted(user_ids)


async def next_sequence_number(session) -> int:
    result = await session.execute(select(func.max(Problem.sequence_number)))
    return int(result.scalar() or 0) + 1


async def ensure_problem(session, record: BundleRecord, node_slugs: list[str]) -> tuple[Problem, bool]:
    result = await session.execute(
        select(Problem).where((Problem.title == record.title) | (Problem.slug == slugify_title(record.title)))
    )
    problem = result.scalar_one_or_none()
    if problem:
        updated = False
        if record.source_url and record.source_url not in problem.description:
            updated = True
        merged_patterns = list(dict.fromkeys(problem.pattern + node_slugs))
        if merged_patterns != problem.pattern:
            problem.pattern = merged_patterns
            updated = True
        if updated:
            await session.flush()
        return problem, False

    slug = slugify_title(record.title)
    existing_slug = await session.execute(select(Problem.id).where(Problem.slug == slug))
    suffix = 2
    while existing_slug.scalar_one_or_none() is not None:
        slug = f"{slugify_title(record.title)}-{suffix}"
        existing_slug = await session.execute(select(Problem.id).where(Problem.slug == slug))
        suffix += 1

    problem = Problem(
        title=record.title,
        slug=slug,
        description=build_description(record),
        difficulty=parse_difficulty(record.difficulty_raw),
        pattern=node_slugs or ["imported"],
        sequence_number=await next_sequence_number(session),
        constraints=["Imported from DSA bundle"],
        examples={"examples": [{"input": "N/A", "output": "N/A", "explanation": "Imported from DSA bundle"}]},
    )
    session.add(problem)
    await session.flush()
    return problem, True


async def upsert_user_note(session, *, user_id: str, problem_id: uuid.UUID, record: BundleRecord, node_slugs: list[str]) -> None:
    result = await session.execute(
        select(UserProblemNote).where(UserProblemNote.user_id == user_id, UserProblemNote.problem_id == problem_id)
    )
    note = result.scalar_one_or_none()
    revision_notes = build_revision_notes(record)
    tags = list(dict.fromkeys(node_slugs + sorted(record.template_values)))
    if note is None:
        session.add(
            UserProblemNote(
                user_id=user_id,
                problem_id=problem_id,
                source_url=record.source_url,
                personal_solution=record.markdown_body,
                revision_notes=revision_notes,
                is_reference_only=True,
                send_flashcard_to_telegram=False,
                flashcard_front=record.flashcard_front,
                flashcard_back=record.flashcard_back,
                tags=tags,
            )
        )
    else:
        note.source_url = record.source_url or note.source_url
        note.personal_solution = record.markdown_body or note.personal_solution
        note.revision_notes = revision_notes or note.revision_notes
        note.is_reference_only = True
        note.flashcard_front = record.flashcard_front or note.flashcard_front
        note.flashcard_back = record.flashcard_back or note.flashcard_back
        note.tags = list(dict.fromkeys((note.tags or []) + tags))
    await session.flush()


async def upsert_user_progress(session, *, user_id: str, problem_id: uuid.UUID, solved_at: datetime | None) -> bool:
    if solved_at is None:
        return False
    result = await session.execute(
        select(UserProgress).where(UserProgress.user_id == user_id, UserProgress.problem_id == problem_id)
    )
    progress = result.scalar_one_or_none()
    if progress is None:
        session.add(
            UserProgress(
                user_id=user_id,
                problem_id=problem_id,
                times_solved=1,
                last_solved_at=solved_at,
                next_review_date=solved_at.date(),
                is_mastered=False,
                show_again=False,
                ease_factor=2.5,
                interval_days=0,
                review_count=1,
            )
        )
        await session.flush()
        return True

    if progress.times_solved <= 0:
        progress.times_solved = 1
    progress.review_count = max(progress.review_count, 1)
    if progress.last_solved_at is None or solved_at > progress.last_solved_at:
        progress.last_solved_at = solved_at
    progress.next_review_date = progress.next_review_date or solved_at.date()
    await session.flush()
    return False


async def ensure_flashcard(session, *, user_id: str, problem_id: uuid.UUID, record: BundleRecord, node_ids: list[uuid.UUID]) -> bool:
    result = await session.execute(
        select(UserFlashcard).where(UserFlashcard.user_id == user_id, UserFlashcard.problem_id == problem_id)
    )
    flashcard = result.scalar_one_or_none()
    tags = list(dict.fromkeys(sorted(record.topic_values) + sorted(record.template_values)))
    created = False
    if flashcard is None:
        flashcard = UserFlashcard(
            user_id=user_id,
            problem_id=problem_id,
            front=record.flashcard_front or record.title,
            back=record.flashcard_back or record.markdown_body or build_description(record),
            tags=tags,
            source_url=record.source_url,
            is_active=True,
        )
        session.add(flashcard)
        await session.flush()
        created = True
    else:
        flashcard.front = flashcard.front or record.flashcard_front or record.title
        flashcard.back = flashcard.back or record.flashcard_back or record.markdown_body or build_description(record)
        flashcard.tags = list(dict.fromkeys((flashcard.tags or []) + tags))
        flashcard.source_url = flashcard.source_url or record.source_url
        await session.flush()

    for node_id in node_ids:
        exists = await session.execute(
            select(RoadmapNodeFlashcard).where(
                RoadmapNodeFlashcard.roadmap_node_id == node_id,
                RoadmapNodeFlashcard.flashcard_id == flashcard.id,
            )
        )
        if exists.scalar_one_or_none() is None:
            session.add(RoadmapNodeFlashcard(roadmap_node_id=node_id, flashcard_id=flashcard.id))
    await session.flush()
    return created


async def run_import(args: argparse.Namespace) -> int:
    title_csv, all_csv, markdown_dir = resolve_csv_paths(args.bundle_root)
    records = load_bundle_records(title_csv, all_csv, markdown_dir)

    async with AsyncSessionLocal() as session:
        roadmap_service = RoadmapService(session)
        roadmap = await roadmap_service.ensure_seed_data()
        node_result = await session.execute(select(RoadmapNode).where(RoadmapNode.roadmap_id == roadmap.id))
        node_by_slug = {node.slug: node for node in node_result.scalars().all()}

        target_user_ids = await resolve_target_user_ids(session, args.user_id)

        created_problems = 0
        linked_problems = 0
        updated_progress = 0
        created_flashcards = 0
        skipped = 0

        for record in records.values():
            node_slugs = roadmap_service.resolve_topic_slugs(topic_candidates(record))
            if not node_slugs:
                skipped += 1
                continue

            problem, created = await ensure_problem(session, record, node_slugs)
            created_problems += int(created)

            existing_links = await session.execute(select(RoadmapNodeProblem).where(RoadmapNodeProblem.problem_id == problem.id))
            existing_node_ids = {link.roadmap_node_id for link in existing_links.scalars().all()}
            sort_order = 0
            for slug in node_slugs:
                node = node_by_slug.get(slug)
                if not node or node.id in existing_node_ids:
                    continue
                session.add(RoadmapNodeProblem(roadmap_node_id=node.id, problem_id=problem.id, sort_order=sort_order))
                linked_problems += 1
                sort_order += 1
            await session.flush()

            if target_user_ids:
                node_ids = [node_by_slug[slug].id for slug in node_slugs if slug in node_by_slug]
                should_make_flashcard = args.create_flashcards and (
                    args.flashcards_from == "all" or record.revise
                )
                for user_id in target_user_ids:
                    await upsert_user_note(session, user_id=user_id, problem_id=problem.id, record=record, node_slugs=node_slugs)
                    progress_created_or_updated = await upsert_user_progress(
                        session,
                        user_id=user_id,
                        problem_id=problem.id,
                        solved_at=record.solved_at,
                    )
                    updated_progress += int(progress_created_or_updated)

                    if should_make_flashcard:
                        created_flashcards += int(
                            await ensure_flashcard(
                                session,
                                user_id=user_id,
                                problem_id=problem.id,
                                record=record,
                                node_ids=node_ids,
                            )
                        )

        if args.dry_run:
            await session.rollback()
        else:
            await session.commit()

    print(
        {
            "title_csv": str(title_csv),
            "all_csv": str(all_csv),
            "markdown_dir": str(markdown_dir),
            "records": len(records),
            "created_problems": created_problems,
            "linked_problems": linked_problems,
            "updated_progress": updated_progress,
            "target_users": len(target_user_ids),
            "created_flashcards": created_flashcards,
            "skipped": skipped,
            "dry_run": args.dry_run,
        }
    )
    return 0


def main() -> int:
    args = parse_args()
    return asyncio.run(run_import(args))


if __name__ == "__main__":
    raise SystemExit(main())
