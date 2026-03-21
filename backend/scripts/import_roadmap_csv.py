"""Import external problem CSV and link rows to roadmap topics.

Example:
    uv run python scripts/import_roadmap_csv.py /path/to/problems.csv
"""

from __future__ import annotations

import argparse
import asyncio
import csv
from pathlib import Path

from sqlalchemy import select

from app.db.connection import AsyncSessionLocal
from app.db.tables import Difficulty, Problem
from app.schemas.problem import ProblemCreate
from app.services.problems import ProblemService
from app.services.roadmaps import RoadmapService


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import roadmap-linked problems from CSV")
    parser.add_argument("csv_path", type=Path)
    parser.add_argument("--roadmap-slug", default="dsa-roadmap")
    parser.add_argument("--user-id", default=None)
    parser.add_argument("--title-column", default="title")
    parser.add_argument("--difficulty-column", default="difficulty")
    parser.add_argument("--topics-column", default="topics")
    parser.add_argument("--url-column", default="source_url")
    parser.add_argument("--solution-column", default="solution")
    parser.add_argument("--notes-column", default="notes")
    parser.add_argument("--delimiter", default=",")
    parser.add_argument("--topic-separator", default="|")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def parse_difficulty(raw: str | None) -> Difficulty:
    value = (raw or "medium").strip().lower()
    if value in {"easy", "e"}:
        return Difficulty.EASY
    if value in {"hard", "h"}:
        return Difficulty.HARD
    return Difficulty.MEDIUM


async def run_import(args: argparse.Namespace) -> int:
    if not args.csv_path.exists():
        raise FileNotFoundError(args.csv_path)

    async with AsyncSessionLocal() as session:
        roadmap_service = RoadmapService(session)
        await roadmap_service.ensure_seed_data()
        problem_service = ProblemService(session)

        created = 0
        linked = 0
        skipped = 0

        with args.csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle, delimiter=args.delimiter)
            for row in reader:
                title = (row.get(args.title_column) or "").strip()
                if not title:
                    skipped += 1
                    continue

                topics = [part.strip() for part in (row.get(args.topics_column) or "").split(args.topic_separator) if part.strip()]
                node_slugs = roadmap_service.resolve_topic_slugs(topics)
                if not node_slugs:
                    skipped += 1
                    continue

                result = await session.execute(select(Problem).where(Problem.title == title))
                problem = result.scalar_one_or_none()
                if not problem:
                    problem = await problem_service.create_custom_problem(
                        ProblemCreate(
                            title=title,
                            url=(row.get(args.url_column) or "").strip() or None,
                            difficulty=parse_difficulty(row.get(args.difficulty_column)),
                            pattern=node_slugs,
                            description=(row.get(args.notes_column) or "Imported from CSV.").strip() or "Imported from CSV.",
                            personal_solution=(row.get(args.solution_column) or "").strip() or None,
                            revision_notes=(row.get(args.notes_column) or "").strip() or None,
                            constraints=["Imported from CSV"],
                            examples=[{"input": "N/A", "output": "N/A", "explanation": "Imported from CSV"}],
                            tags=node_slugs,
                        )
                    )
                    created += 1

                if args.user_id:
                    await problem_service.upsert_user_note(
                        user_id=args.user_id,
                        problem_id=problem.id,
                        source_url=(row.get(args.url_column) or "").strip() or None,
                        personal_solution=(row.get(args.solution_column) or "").strip() or None,
                        revision_notes=(row.get(args.notes_column) or "").strip() or None,
                        is_reference_only=True,
                        tags=node_slugs,
                    )

                await roadmap_service.link_problem_to_nodes(
                    problem_id=problem.id,
                    roadmap_slug=args.roadmap_slug,
                    node_slugs=node_slugs,
                )
                linked += len(node_slugs)

        if args.dry_run:
            await session.rollback()
        else:
            await session.commit()

    print({"created": created, "linked": linked, "skipped": skipped, "dry_run": args.dry_run})
    return 0


def main() -> int:
    args = parse_args()
    return asyncio.run(run_import(args))


if __name__ == "__main__":
    raise SystemExit(main())
