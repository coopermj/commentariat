"""Pytest fixtures for Commentariat tests."""

from __future__ import annotations

import os

import pytest

from app.db import init_db, get_connection


@pytest.fixture
def temp_db(tmp_path):
    """Create a temporary database for testing."""
    db_path = tmp_path / "test.db"
    os.environ["DATABASE_PATH"] = str(db_path)
    init_db()
    yield db_path


@pytest.fixture
def sample_commentary(temp_db):
    """Insert a sample commentary for testing."""
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO commentaries (slug, name, description, source, license, language)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            ("test-comm", "Test Commentary", "A test", "test", "PD", "en"),
        )
        commentary_id = cursor.lastrowid
        conn.execute(
            """
            INSERT INTO entries (commentary_id, book, chapter, verse_start, verse_end, text)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (commentary_id, "Genesis", 1, 1, 1, "In the beginning..."),
        )
        conn.execute(
            """
            INSERT INTO entries (commentary_id, book, chapter, verse_start, verse_end, text)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (commentary_id, "Genesis", 1, 2, 3, "Commentary on verses 2-3"),
        )
        conn.commit()
    return commentary_id
