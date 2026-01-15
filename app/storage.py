"""Data access helpers for the API."""

from __future__ import annotations

from typing import Dict, List, Optional

from app.db import get_connection


def list_commentaries() -> List[Dict[str, object]]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT slug, name, description, source, license, language
            FROM commentaries
            ORDER BY name
            """
        ).fetchall()
    return [dict(row) for row in rows]


def get_commentary(name_or_slug: str) -> Optional[Dict[str, object]]:
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT *
            FROM commentaries
            WHERE lower(slug) = lower(?) OR lower(name) = lower(?)
            """,
            (name_or_slug, name_or_slug),
        ).fetchone()
    return dict(row) if row else None


def list_entries_for_chapter(
    commentary_id: int, book: str, chapter: int
) -> List[Dict[str, object]]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT verse_start, verse_end, text
            FROM entries
            WHERE commentary_id = ? AND book = ? AND chapter = ?
            ORDER BY verse_start, verse_end
            """,
            (commentary_id, book, chapter),
        ).fetchall()
    return [dict(row) for row in rows]


def list_entries_for_verse(
    commentary_id: int, book: str, chapter: int, verse: int
) -> List[Dict[str, object]]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT verse_start, verse_end, text
            FROM entries
            WHERE commentary_id = ?
              AND book = ?
              AND chapter = ?
              AND verse_start <= ?
              AND verse_end >= ?
            ORDER BY verse_start, verse_end
            """,
            (commentary_id, book, chapter, verse, verse),
        ).fetchall()
    return [dict(row) for row in rows]
