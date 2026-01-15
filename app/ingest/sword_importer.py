"""Import commentaries directly from SWORD modules."""

from __future__ import annotations

from pathlib import Path
from typing import Dict

from app.db import get_connection
from app.ingest.json_importer import IngestError
from app.ingest.sword_utils import (
    iter_sword_entries,
    load_module_config,
)
from app.logging import get_logger

logger = get_logger(__name__)


def _build_commentary_metadata(
    module: str,
    conf_path: Path,
) -> Dict[str, str | None]:
    """Build commentary metadata from SWORD module config."""
    config = load_module_config(conf_path)

    return {
        "slug": module.lower(),
        "name": config.get("Description", module),
        "description": config.get("About", "")[:500] if config.get("About") else None,
        "source": f"SWORD: {module}",
        "license": config.get("DistributionLicense", "Unknown"),
        "language": config.get("Lang", "en"),
    }


def _upsert_commentary(connection, meta: Dict[str, str | None]) -> int:
    """Insert or update commentary metadata, returning the commentary ID."""
    slug = meta["slug"]
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
            (
                meta["name"],
                meta["description"],
                meta["source"],
                meta["license"],
                meta["language"],
                commentary_id,
            ),
        )
        logger.info("Updated existing commentary: %s (id=%d)", slug, commentary_id)
        return commentary_id

    cursor = connection.execute(
        """
        INSERT INTO commentaries (slug, name, description, source, license, language)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            slug,
            meta["name"],
            meta["description"],
            meta["source"],
            meta["license"],
            meta["language"],
        ),
    )
    commentary_id = int(cursor.lastrowid)
    logger.info("Created new commentary: %s (id=%d)", slug, commentary_id)
    return commentary_id


def ingest_sword(
    sword_path: Path,
    module: str,
    replace: bool = False,
    conf_path: Path | None = None,
) -> int:
    """
    Ingest a SWORD commentary module directly into the database.

    Args:
        sword_path: Path to the SWORD library directory (containing mods.d/)
        module: SWORD module name (e.g., "MatthewHenry")
        replace: If True, delete existing entries before import
        conf_path: Optional explicit path to module .conf file

    Returns:
        Number of entries inserted

    Raises:
        IngestError: If the module cannot be processed
    """
    if conf_path is None:
        conf_path = sword_path / "mods.d" / f"{module.lower()}.conf"

    if not conf_path.exists():
        raise IngestError(f"Module config not found: {conf_path}")

    if not sword_path.exists():
        raise IngestError(f"SWORD path does not exist: {sword_path}")

    logger.info("Starting SWORD ingestion: %s from %s", module, sword_path)

    try:
        meta = _build_commentary_metadata(module, conf_path)
    except Exception as exc:
        raise IngestError(f"Failed to read module config: {exc}") from exc

    inserted = 0
    with get_connection() as connection:
        try:
            commentary_id = _upsert_commentary(connection, meta)

            if replace:
                connection.execute(
                    "DELETE FROM entries WHERE commentary_id = ?",
                    (commentary_id,),
                )
                logger.info("Deleted existing entries for commentary %d", commentary_id)

            buffer = []
            for entry in iter_sword_entries(sword_path, module, conf_path):
                buffer.append((
                    commentary_id,
                    entry["book"],
                    entry["chapter"],
                    entry["verse"],
                    entry["verse"],  # verse_end = verse_start for single verses
                    entry["text"],
                ))

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
                    logger.debug("Inserted batch of %d entries (total: %d)", len(buffer), inserted)
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
            logger.info("SWORD ingestion complete: %d entries inserted", inserted)

        except Exception as exc:
            logger.error("SWORD ingestion failed: %s", exc)
            raise IngestError(f"SWORD ingestion failed: {exc}") from exc

    return inserted
