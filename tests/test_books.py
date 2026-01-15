"""Tests for book normalization."""

import pytest

from app.books import normalize_book, list_books, BOOK_ALIASES


def test_normalize_canonical_name():
    """Canonical names should normalize to themselves."""
    assert normalize_book("Genesis") == "Genesis"
    assert normalize_book("1 Corinthians") == "1 Corinthians"
    assert normalize_book("Song of Solomon") == "Song of Solomon"


def test_normalize_aliases():
    """Common aliases should normalize correctly."""
    assert normalize_book("gen") == "Genesis"
    assert normalize_book("Gen") == "Genesis"
    assert normalize_book("GEN") == "Genesis"
    assert normalize_book("1cor") == "1 Corinthians"
    assert normalize_book("firstcorinthians") == "1 Corinthians"
    assert normalize_book("jn") == "John"
    assert normalize_book("rev") == "Revelation"


def test_normalize_removes_spaces():
    """Normalization should ignore spaces and be case-insensitive."""
    assert normalize_book("1 cor") == "1 Corinthians"
    assert normalize_book("song of solomon") == "Song of Solomon"


def test_normalize_unknown_book():
    """Unknown book names should raise ValueError."""
    with pytest.raises(ValueError, match="Unknown book"):
        normalize_book("NotABook")


def test_normalize_empty_string():
    """Empty string should raise ValueError."""
    with pytest.raises(ValueError, match="Book name is required"):
        normalize_book("")


def test_list_books_returns_all_books():
    """list_books should return all canonical books."""
    books = list_books()
    assert len(books) == 66  # Standard Protestant canon
    assert books[0]["canonical"] == "Genesis"
    assert books[-1]["canonical"] == "Revelation"


def test_no_duplicate_aliases():
    """Each book's alias list should have no duplicates."""
    for canonical, aliases in BOOK_ALIASES.items():
        assert len(aliases) == len(set(aliases)), f"Duplicates in {canonical}"
