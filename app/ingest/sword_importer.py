"""Stub entrypoint for SWORD-based ingestion."""

from __future__ import annotations

from pathlib import Path

from app.ingest.json_importer import IngestError


def ingest_sword(_sword_path: Path, _module: str) -> None:
    raise IngestError(
        "SWORD ingestion requires an export step. "
        "Convert modules to NDJSON first (see docs/INGEST.md)."
    )
