"""Tests for storage layer."""

import pytest

from app.storage import (
    list_commentaries,
    get_commentary,
    list_entries_for_chapter,
    list_entries_for_verse,
)


def test_list_commentaries_empty(temp_db):
    """Empty database should return empty list."""
    assert list_commentaries() == []


def test_list_commentaries(sample_commentary):
    """Should return all commentaries."""
    result = list_commentaries()
    assert len(result) == 1
    assert result[0]["slug"] == "test-comm"
    assert result[0]["name"] == "Test Commentary"


def test_get_commentary_by_slug(sample_commentary):
    """Should find commentary by slug."""
    result = get_commentary("test-comm")
    assert result is not None
    assert result["slug"] == "test-comm"


def test_get_commentary_by_name(sample_commentary):
    """Should find commentary by name."""
    result = get_commentary("Test Commentary")
    assert result is not None
    assert result["slug"] == "test-comm"


def test_get_commentary_case_insensitive(sample_commentary):
    """Lookup should be case-insensitive."""
    result = get_commentary("TEST-COMM")
    assert result is not None


def test_get_commentary_not_found(sample_commentary):
    """Should return None for unknown commentary."""
    result = get_commentary("nonexistent")
    assert result is None


def test_list_entries_for_chapter(sample_commentary):
    """Should return all entries for a chapter."""
    result = list_entries_for_chapter(sample_commentary, "Genesis", 1)
    assert len(result) == 2


def test_list_entries_for_verse(sample_commentary):
    """Should return entries covering a specific verse."""
    # Verse 1 is covered by entry with verse_start=1, verse_end=1
    result = list_entries_for_verse(sample_commentary, "Genesis", 1, 1)
    assert len(result) == 1
    assert result[0]["text"] == "In the beginning..."

    # Verse 2 is covered by entry with verse_start=2, verse_end=3
    result = list_entries_for_verse(sample_commentary, "Genesis", 1, 2)
    assert len(result) == 1
    assert "verses 2-3" in result[0]["text"]


def test_list_entries_empty_chapter(sample_commentary):
    """Should return empty list for chapter with no entries."""
    result = list_entries_for_chapter(sample_commentary, "Genesis", 99)
    assert result == []
