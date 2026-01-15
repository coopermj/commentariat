"""Export a SWORD commentary module to NDJSON using diatheke."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import os
from pathlib import Path
from typing import Dict, List, Tuple

from app.books import normalize_book

ROMAN_PREFIXES = {
    "III ": "3 ",
    "II ": "2 ",
    "I ": "1 ",
}


def _run_diatheke(args: List[str], env: Dict[str, str] | None = None) -> str:
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


def _load_about_text(conf_path: Path) -> str:
    lines = conf_path.read_text(encoding="utf-8").splitlines()
    collecting = False
    parts: List[str] = []
    for line in lines:
        if not collecting:
            if line.startswith("About="):
                collecting = True
                parts.append(_normalize_conf_line(line[len("About=") :]))
            continue
        if line.startswith("#") or "=" in line:
            break
        parts.append(_normalize_conf_line(line))
    return "".join(parts)


def _extract_books(conf_path: Path) -> List[str]:
    about = _load_about_text(conf_path)
    if not about:
        return []
    parts = [part.strip() for part in about.split("\\par")]
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


def _roman_to_number_prefix(name: str) -> str:
    for roman, replacement in ROMAN_PREFIXES.items():
        if name.startswith(roman):
            return replacement + name[len(roman) :]
    return name


def _list_verses_for_book(book: str) -> List[Tuple[int, int]]:
    output = _run_diatheke(["-b", "KJV", "-f", "plain", "-k", book])
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
    return refs


def _strip_diatheke_prefix(text: str, module: str) -> str:
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
        cleaned[0] = first[match.end() :].lstrip()
    return "\n".join([line for line in cleaned if line.strip()]).strip()


def export_module(
    sword_path: Path,
    module: str,
    output_path: Path,
    conf_path: Path | None = None,
) -> int:
    if conf_path is None:
        conf_path = sword_path / "mods.d" / f"{module.lower()}.conf"
    books_raw = _extract_books(conf_path)
    if not books_raw:
        raise RuntimeError("No book list found in module config")

    env = dict(**os.environ)
    env["SWORD_PATH"] = str(sword_path)

    inserted = 0
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        for raw_name in books_raw:
            canonical_name = _roman_to_number_prefix(raw_name)
            try:
                canonical_name = normalize_book(canonical_name)
            except ValueError:
                print(f"Skipping unknown book: {raw_name}", file=sys.stderr)
                continue
            refs = _list_verses_for_book(canonical_name)
            for chapter, verse in refs:
                key = f"{canonical_name} {chapter}:{verse}"
                text = _run_diatheke(
                    ["-b", module, "-f", "plain", "-k", key], env=env
                )
                stripped = _strip_diatheke_prefix(text, module)
                if not stripped:
                    continue
                record = {
                    "book": canonical_name,
                    "chapter": chapter,
                    "verse": verse,
                    "text": stripped,
                }
                handle.write(json.dumps(record, ensure_ascii=True) + "\n")
                inserted += 1
    return inserted


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Export SWORD commentary to NDJSON")
    parser.add_argument("module", help="SWORD module name")
    parser.add_argument(
        "--sword-path",
        default="data/sword",
        help="Path to the SWORD library containing mods.d and modules",
    )
    parser.add_argument(
        "--output",
        default="data/entries/export.ndjson",
        help="Output NDJSON path",
    )
    parser.add_argument(
        "--conf",
        default=None,
        help="Optional path to a module .conf file",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    conf_path = Path(args.conf) if args.conf else None
    try:
        count = export_module(
            Path(args.sword_path),
            args.module,
            Path(args.output),
            conf_path=conf_path,
        )
    except Exception as exc:
        print(f"Export failed: {exc}", file=sys.stderr)
        return 1
    print(f"Wrote {count} entries to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
