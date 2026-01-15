"""Import commentaries from JSON or NDJSON sources."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Iterator, Tuple

from app.books import normalize_book
from app.db import get_connection
from app.logging import get_logger

logger = get_logger(__name__)


class IngestError(ValueError):
    pass


def _parse_int(value: object, label: str) -> int:
    if value is None:
        raise IngestError(f"Missing {label}")
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise IngestError(f"Invalid {label}: {value}") from exc


def _parse_verse_range(entry: Dict[str, object]) -> Tuple[int, int]:
    if "verse_start" in entry or "verse_end" in entry:
        verse_start = _parse_int(entry.get("verse_start"), "verse_start")
        verse_end = _parse_int(entry.get("verse_end", verse_start), "verse_end")
        return verse_start, verse_end

    verse = entry.get("verse")
    if verse is None:
        raise IngestError("Missing verse or verse_start/verse_end")
    if isinstance(verse, str) and "-" in verse:
        start_text, end_text = verse.split("-", 1)
        verse_start = _parse_int(start_text.strip(), "verse")
        verse_end = _parse_int(end_text.strip(), "verse")
    else:
        verse_start = _parse_int(verse, "verse")
        verse_end = verse_start
    return verse_start, verse_end


def _load_entries(payload: Dict[str, object], base_dir: Path) -> Iterator[Dict[str, object]]:
    entries = payload.get("entries")
    entries_file = payload.get("entries_file")

    if entries is not None and entries_file is not None:
        raise IngestError("Use either entries or entries_file, not both")

    if entries is not None:
        if not isinstance(entries, list):
            raise IngestError("entries must be a list")
        for entry in entries:
            if not isinstance(entry, dict):
                raise IngestError("entries must contain objects")
            yield entry
        return

    if entries_file is not None:
        entries_path = (base_dir / str(entries_file)).resolve()
        with entries_path.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise IngestError(f"Invalid JSON line: {exc}") from exc
                if not isinstance(entry, dict):
                    raise IngestError("entries_file must contain JSON objects")
                yield entry
        return

    raise IngestError("Missing entries or entries_file")


def _upsert_commentary(connection, meta: Dict[str, object]) -> int:
    slug = str(meta.get("slug", "")).strip()
    name = str(meta.get("name", "")).strip()
    if not slug or not name:
        raise IngestError("commentary.slug and commentary.name are required")

    description = meta.get("description")
    source = meta.get("source")
    license_text = meta.get("license")
    language = meta.get("language")

    existing = connection.execute(
        "SELECT id FROM commentaries WHERE slug = ?",
        (slug,),
    ).fetchone()

    if existing:
        commentary_id = existing["id"]
        connection.execute(
            """
            UPDATE commentaries
            SET name = ?, description = ?, source = ?, license = ?, language = ?
            WHERE id = ?
            """,
            (name, description, source, license_text, language, commentary_id),
        )
        return commentary_id

    cursor = connection.execute(
        """
        INSERT INTO commentaries (slug, name, description, source, license, language)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (slug, name, description, source, license_text, language),
    )
    return int(cursor.lastrowid)


def ingest_json(path: Path, replace: bool = False) -> int:
    logger.info("Starting ingestion from %s", path)
    base_dir = path.parent
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)

    if not isinstance(payload, dict):
        raise IngestError("Top-level JSON must be an object")

    meta = payload.get("commentary")
    if not isinstance(meta, dict):
        raise IngestError("commentary object is required")

    entries = _load_entries(payload, base_dir)

    inserted = 0
    with get_connection() as connection:
        commentary_id = _upsert_commentary(connection, meta)
        logger.info("Upserting commentary: %s (id=%d)", meta.get("slug"), commentary_id)
        if replace:
            connection.execute(
                "DELETE FROM entries WHERE commentary_id = ?",
                (commentary_id,),
            )

        buffer = []
        for entry in entries:
            book_raw = entry.get("book")
            if not isinstance(book_raw, str):
                raise IngestError("entry.book must be a string")
            try:
                book = normalize_book(book_raw)
            except ValueError as exc:
                raise IngestError(str(exc)) from exc

            chapter = _parse_int(entry.get("chapter"), "chapter")
            verse_start, verse_end = _parse_verse_range(entry)
            if chapter <= 0 or verse_start <= 0 or verse_end <= 0:
                raise IngestError("chapter and verses must be positive")
            if verse_end < verse_start:
                raise IngestError("verse_end must be >= verse_start")

            text = entry.get("text")
            if not isinstance(text, str) or not text.strip():
                raise IngestError("entry.text is required")

            buffer.append(
                (commentary_id, book, chapter, verse_start, verse_end, text.strip())
            )
            if len(buffer) >= 1000:
                connection.executemany(
                    """
                    INSERT INTO entries
                        (commentary_id, book, chapter, verse_start, verse_end, text)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    buffer,
                )
                inserted += len(buffer)
                buffer.clear()

        if buffer:
            connection.executemany(
                """
                INSERT INTO entries
                    (commentary_id, book, chapter, verse_start, verse_end, text)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                buffer,
            )
            inserted += len(buffer)

        connection.commit()
        logger.info("Ingestion complete: %d entries inserted", inserted)

    return inserted
