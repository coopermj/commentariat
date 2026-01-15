#!/usr/bin/env python3
"""Startup script that initializes database and ingests commentaries if needed."""

from __future__ import annotations

import multiprocessing
import os
import subprocess
import sys
from pathlib import Path

from app.db import init_db, get_connection
from app.logging import configure_logging, get_logger

configure_logging()
logger = get_logger(__name__)


def count_entries() -> int:
    """Count total entries in database."""
    with get_connection() as conn:
        row = conn.execute("SELECT COUNT(*) as count FROM entries").fetchone()
        return row["count"] if row else 0


def ingest_sword_module(sword_path: str, module: str) -> None:
    """Run SWORD ingestion for a module."""
    from app.ingest.sword_importer import ingest_sword
    from app.ingest.json_importer import IngestError

    try:
        count = ingest_sword(Path(sword_path), module)
        logger.info("Ingested %s: %d entries", module, count)
    except IngestError as e:
        logger.error("Failed to ingest %s: %s", module, e)


def run_ingestion() -> None:
    """Run ingestion for all available SWORD modules."""
    # Reconfigure logging in subprocess
    configure_logging()

    sword_path = "/app/data/sword"

    # Test KJV access from our bundled modules
    import subprocess
    test_env = dict(os.environ)
    test_env["SWORD_PATH"] = sword_path
    result = subprocess.run(
        ["diatheke", "-b", "KJV", "-f", "plain", "-k", "Genesis 1:1"],
        capture_output=True,
        text=True,
        env=test_env,
    )
    logger.info("KJV test - returncode: %d, stdout: %s, stderr: %s",
                result.returncode, result.stdout[:200] if result.stdout else "empty", result.stderr[:200] if result.stderr else "empty")
    mods_dir = Path(sword_path) / "mods.d"

    if not mods_dir.exists():
        logger.warning("No SWORD modules found at %s", mods_dir)
        return

    # Get commentary modules (exclude KJV which is a Bible text)
    modules = [f.stem for f in mods_dir.glob("*.conf") if f.stem.lower() != "kjv"]
    logger.info("Ingesting commentary modules: %s", modules)

    for module in modules:
        logger.info("Starting ingestion of %s...", module)
        ingest_sword_module(sword_path, module)

    logger.info("All ingestion complete! Total entries: %d", count_entries())


def main() -> int:
    logger.info("Initializing database...")
    init_db()

    entry_count = count_entries()
    logger.info("Current entry count: %d", entry_count)

    # Start ingestion in background process if database is empty
    ingestion_process = None
    if entry_count == 0:
        logger.info("No entries found - starting background ingestion process...")
        ingestion_process = multiprocessing.Process(target=run_ingestion)
        ingestion_process.start()
    else:
        logger.info("Database has entries, skipping ingestion")

    # Start uvicorn as subprocess (not exec, so ingestion can continue)
    port = os.environ.get("PORT", "8000")
    logger.info("Starting uvicorn on port %s", port)

    try:
        process = subprocess.Popen([
            "uvicorn",
            "app.main:app",
            "--host", "0.0.0.0",
            "--port", port,
        ])
        process.wait()
    finally:
        if ingestion_process and ingestion_process.is_alive():
            logger.info("Waiting for ingestion to complete...")
            ingestion_process.join(timeout=60)

    return process.returncode


if __name__ == "__main__":
    sys.exit(main())
