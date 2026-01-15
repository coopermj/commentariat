"""Tests for JSON ingestion."""

import json

import pytest

from app.ingest.json_importer import (
    IngestError,
    ingest_json,
    _parse_verse_range,
)


def test_parse_verse_range_single():
    """Single verse should have start == end."""
    entry = {"verse": 5}
    start, end = _parse_verse_range(entry)
    assert start == 5
    assert end == 5


def test_parse_verse_range_string():
    """String verse should parse as integer."""
    entry = {"verse": "5"}
    start, end = _parse_verse_range(entry)
    assert start == 5


def test_parse_verse_range_hyphenated():
    """Hyphenated verse should parse as range."""
    entry = {"verse": "5-7"}
    start, end = _parse_verse_range(entry)
    assert start == 5
    assert end == 7


def test_parse_verse_range_explicit():
    """Explicit start/end should be used."""
    entry = {"verse_start": 3, "verse_end": 5}
    start, end = _parse_verse_range(entry)
    assert start == 3
    assert end == 5


def test_ingest_json_inline_entries(temp_db, tmp_path):
    """Should ingest inline entries."""
    manifest = {
        "commentary": {
            "slug": "inline-test",
            "name": "Inline Test",
        },
        "entries": [
            {"book": "John", "chapter": 3, "verse": 16, "text": "For God so loved..."},
        ],
    }
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest))

    count = ingest_json(manifest_path)
    assert count == 1


def test_ingest_json_ndjson_entries(temp_db, tmp_path):
    """Should ingest entries from NDJSON file."""
    entries_file = tmp_path / "entries.ndjson"
    entries_file.write_text(
        '{"book": "John", "chapter": 3, "verse": 16, "text": "Entry 1"}\n'
        '{"book": "John", "chapter": 3, "verse": 17, "text": "Entry 2"}\n'
    )

    manifest = {
        "commentary": {
            "slug": "ndjson-test",
            "name": "NDJSON Test",
        },
        "entries_file": "entries.ndjson",
    }
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest))

    count = ingest_json(manifest_path)
    assert count == 2


def test_ingest_json_replace_mode(temp_db, tmp_path):
    """Replace mode should delete existing entries."""
    manifest = {
        "commentary": {"slug": "replace-test", "name": "Replace Test"},
        "entries": [{"book": "John", "chapter": 1, "verse": 1, "text": "Original"}],
    }
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest))

    ingest_json(manifest_path)

    # Update with different entries
    manifest["entries"] = [{"book": "John", "chapter": 1, "verse": 2, "text": "New"}]
    manifest_path.write_text(json.dumps(manifest))

    count = ingest_json(manifest_path, replace=True)
    assert count == 1


def test_ingest_json_missing_slug(temp_db, tmp_path):
    """Should raise IngestError for missing slug."""
    manifest = {
        "commentary": {"name": "No Slug"},
        "entries": [],
    }
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest))

    with pytest.raises(IngestError, match="slug"):
        ingest_json(manifest_path)


def test_ingest_json_invalid_book(temp_db, tmp_path):
    """Should raise IngestError for invalid book."""
    manifest = {
        "commentary": {"slug": "bad-book", "name": "Bad Book"},
        "entries": [{"book": "NotABook", "chapter": 1, "verse": 1, "text": "x"}],
    }
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest))

    with pytest.raises(IngestError, match="Unknown book"):
        ingest_json(manifest_path)
