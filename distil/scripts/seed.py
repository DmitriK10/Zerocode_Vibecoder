"""Load test inputs into the database.

Usage (inside Docker):
    docker compose exec app python -m scripts.seed

Usage (local venv):
    python -m scripts.seed --file tests_data/inputs.jsonl

Each line of the input file is a JSON object with at least:
    {"source": "email", "raw_text": "..."}

Idempotent by default: a text is skipped if an identical ``raw_text``
already exists in the database.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Any

from app.db.session import session_scope
from app.domain.enums import TextSource, TextStatus
from app.logging_config import configure_logging, get_logger
from app.repositories.postgres import PostgresTextRepository

log = get_logger("seed")

DEFAULT_FILE = Path("tests_data") / "inputs.jsonl"


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        raise FileNotFoundError(f"Input file not found: {path}")
    items: list[dict[str, Any]] = []
    for lineno, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        raw = raw.strip()
        if not raw or raw.startswith("#"):
            continue
        try:
            obj = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON on line {lineno}: {exc}") from exc
        if "source" not in obj or "raw_text" not in obj:
            raise ValueError(
                f"Line {lineno}: missing required keys 'source' and 'raw_text'"
            )
        items.append(obj)
    return items


async def _seed(path: Path, *, skip_duplicates: bool) -> tuple[int, int]:
    items = _read_jsonl(path)
    created = 0
    skipped = 0

    async with session_scope() as session:
        repo = PostgresTextRepository(session)

        # Load existing raw_texts once for cheap duplicate detection.
        existing: set[str] = set()
        if skip_duplicates:
            rows = await repo.list_with_stats(limit=10_000)
            existing = {row.text.raw_text for row in rows}

        for item in items:
            source = TextSource(item["source"])
            raw_text = str(item["raw_text"])
            if skip_duplicates and raw_text in existing:
                skipped += 1
                continue
            await repo.create(source=source, raw_text=raw_text)
            existing.add(raw_text)
            created += 1

    return created, skipped


async def _count_texts() -> int:
    async with session_scope() as session:
        repo = PostgresTextRepository(session)
        return await repo.count()


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Seed Distil with test inputs.")
    parser.add_argument(
        "--file",
        type=Path,
        default=DEFAULT_FILE,
        help=f"Path to JSONL file (default: {DEFAULT_FILE})",
    )
    parser.add_argument(
        "--allow-duplicates",
        action="store_true",
        help="Insert even if the same raw_text already exists.",
    )
    return parser.parse_args(argv)


async def _main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    configure_logging(level="INFO", json_output=False)

    log.info("seeding", file=str(args.file))
    created, skipped = await _seed(
        args.file, skip_duplicates=not args.allow_duplicates
    )
    total = await _count_texts()

    log.info(
        "done",
        created=created,
        skipped=skipped,
        total_texts=total,
    )
    return 0


def main() -> None:
    try:
        raise SystemExit(asyncio.run(_main()))
    except KeyboardInterrupt:
        raise SystemExit(130) from None
    except Exception as exc:  # noqa: BLE001 — CLI top-level
        print(f"seed failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()