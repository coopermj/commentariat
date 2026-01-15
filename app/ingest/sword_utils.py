"""Utilities for working with SWORD modules via diatheke."""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path
from typing import Dict, Iterator, List, Tuple

from app.books import normalize_book, CANONICAL_BOOKS
from app.logging import get_logger

logger = get_logger(__name__)

ROMAN_PREFIXES = {
    "III ": "3 ",
    "II ": "2 ",
    "I ": "1 ",
}


def run_diatheke(args: List[str], env: Dict[str, str] | None = None) -> str:
    """Execute diatheke with the given arguments."""
    result = subprocess.run(
        ["diatheke", *args],
        capture_output=True,
        text=True,
        env=env,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "diatheke failed")
    return result.stdout


def _normalize_conf_line(line: str) -> str:
    return line.rstrip().rstrip("\\")


def load_about_text(conf_path: Path) -> str:
    """Load the About text from a SWORD module .conf file."""
    lines = conf_path.read_text(encoding="utf-8").splitlines()
    collecting = False
    parts: List[str] = []
    for line in lines:
        if not collecting:
            if line.startswith("About="):
                collecting = True
                parts.append(_normalize_conf_line(line[len("About="):]))
            continue
        if line.startswith("#") or "=" in line:
            break
        parts.append(_normalize_conf_line(line))
    return "".join(parts)


def load_module_config(conf_path: Path) -> Dict[str, str]:
    """Parse a SWORD module .conf file into a dictionary.

    Also extracts the module name from the [ModuleName] header.
    """
    config: Dict[str, str] = {}
    lines = conf_path.read_text(encoding="utf-8").splitlines()
    current_key: str | None = None
    current_value: List[str] = []

    for line in lines:
        line_stripped = line.rstrip()
        if line.startswith("#"):
            continue
        # Extract module name from [ModuleName] header
        if line_stripped.startswith("[") and line_stripped.endswith("]"):
            config["_module_name"] = line_stripped[1:-1]
            continue
        if "=" in line and not line.startswith(" ") and not line.startswith("\t"):
            if current_key:
                config[current_key] = "".join(current_value)
            key, value = line_stripped.split("=", 1)
            current_key = key.strip()
            current_value = [value.rstrip("\\")]
        elif current_key and line_stripped:
            current_value.append(line_stripped.rstrip("\\"))

    if current_key:
        config[current_key] = "".join(current_value)

    return config


def extract_books_from_about(about_text: str) -> List[str]:
    """Extract book list from About text in .conf file."""
    if not about_text:
        return []
    parts = [part.strip() for part in about_text.split("\\par")]
    books: List[str] = []
    recording = False
    for part in parts:
        if not part:
            continue
        if part.lower().startswith("books with commentary"):
            recording = True
            continue
        if recording:
            books.append(part)
    return books


def roman_to_number_prefix(name: str) -> str:
    """Convert Roman numeral prefix to number (e.g., 'II Kings' -> '2 Kings')."""
    for roman, replacement in ROMAN_PREFIXES.items():
        if name.startswith(roman):
            return replacement + name[len(roman):]
    return name


def list_verses_for_book(book: str, env: Dict[str, str] | None = None) -> List[Tuple[int, int]]:
    """Get all chapter:verse references for a book using KJV versification.

    Note: Uses system SWORD path for KJV (not custom env) since KJV is typically
    installed system-wide, not bundled with commentary modules.
    """
    try:
        output = run_diatheke(["-b", "KJV", "-f", "plain", "-k", book], env=env)
    except RuntimeError as e:
        logger.error("Failed to list verses for %s: %s", book, e)
        return []

    if not output.strip():
        logger.warning("Empty output from KJV for book: %s", book)
        return []

    refs: List[Tuple[int, int]] = []
    pattern = re.compile(r"^.+?\s+(\d+):(\d+):")
    for line in output.splitlines():
        line = line.strip()
        if not line:
            continue
        match = pattern.match(line)
        if not match:
            continue
        chapter = int(match.group(1))
        verse = int(match.group(2))
        refs.append((chapter, verse))

    if not refs:
        logger.warning("No verse refs parsed for %s (output: %s...)", book, output[:200])

    return refs


def strip_diatheke_prefix(text: str, module: str) -> str:
    """Remove diatheke output formatting (verse reference prefix, module name)."""
    lines = [line.rstrip() for line in text.splitlines()]
    cleaned: List[str] = []
    for line in lines:
        if line.strip() == f"({module})":
            continue
        cleaned.append(line)
    if not cleaned:
        return ""
    first = cleaned[0]
    match = re.match(r"^.+?\s+\d+:\d+:", first)
    if match:
        cleaned[0] = first[match.end():].lstrip()
    return "\n".join([line for line in cleaned if line.strip()]).strip()


def iter_sword_entries(
    sword_path: Path,
    module: str,
    conf_path: Path | None = None,
) -> Iterator[Dict[str, object]]:
    """
    Iterate over all entries in a SWORD commentary module.

    Yields dicts with keys: book, chapter, verse, text
    """
    if conf_path is None:
        conf_path = sword_path / "mods.d" / f"{module.lower()}.conf"

    if not conf_path.exists():
        raise FileNotFoundError(f"Module config not found: {conf_path}")

    # Load config and get actual module name
    config = load_module_config(conf_path)
    actual_module_name = config.get("_module_name", module)
    if actual_module_name != module:
        logger.info("Using module name '%s' from config (filename was '%s')", actual_module_name, module)
    module = actual_module_name

    about_text = load_about_text(conf_path)
    books_raw = extract_books_from_about(about_text)

    # If no book list in config, use all 66 canonical books
    if books_raw:
        canonical_books = []
        for raw_name in books_raw:
            name = roman_to_number_prefix(raw_name)
            try:
                canonical_books.append(normalize_book(name))
            except ValueError:
                logger.warning("Skipping unknown book: %s", raw_name)
    else:
        logger.info("No book list in config, using all 66 canonical books")
        canonical_books = CANONICAL_BOOKS

    # Environment for querying the commentary module (custom SWORD_PATH)
    module_env = dict(**os.environ)
    module_env["SWORD_PATH"] = str(sword_path)

    logger.info("Processing %d books from %s", len(canonical_books), module)

    for canonical_name in canonical_books:

        logger.debug("Processing book: %s", canonical_name)
        # Use same SWORD_PATH for KJV (now bundled with other modules)
        refs = list_verses_for_book(canonical_name, env=module_env)

        if not refs:
            logger.warning("No refs for book %s", canonical_name)
            continue

        # Log first verse as debug sample
        first_key = f"{canonical_name} {refs[0][0]}:{refs[0][1]}"
        sample = run_diatheke(["-b", module, "-f", "plain", "-k", first_key], env=module_env)
        logger.info("Sample query %s returned %d chars", first_key, len(sample))

        for chapter, verse in refs:
            key = f"{canonical_name} {chapter}:{verse}"
            text = run_diatheke(["-b", module, "-f", "plain", "-k", key], env=module_env)
            stripped = strip_diatheke_prefix(text, module)
            if not stripped:
                continue

            yield {
                "book": canonical_name,
                "chapter": chapter,
                "verse": verse,
                "text": stripped,
            }
