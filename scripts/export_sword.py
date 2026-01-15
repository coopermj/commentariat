"""Export a SWORD commentary module to NDJSON using diatheke."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from app.ingest.sword_utils import iter_sword_entries
from app.logging import configure_logging, get_logger

logger = get_logger(__name__)


def export_module(
    sword_path: Path,
    module: str,
    output_path: Path,
    conf_path: Path | None = None,
) -> int:
    """Export SWORD module to NDJSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    inserted = 0

    with output_path.open("w", encoding="utf-8") as handle:
        for entry in iter_sword_entries(sword_path, module, conf_path):
            record = {
                "book": entry["book"],
                "chapter": entry["chapter"],
                "verse": entry["verse"],
                "text": entry["text"],
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
    configure_logging()
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
        logger.error("Export failed: %s", exc)
        print(f"Export failed: {exc}", file=sys.stderr)
        return 1
    print(f"Wrote {count} entries to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
