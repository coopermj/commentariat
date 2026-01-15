"""CLI for ingesting commentary sources."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from app.db import init_db
from app.ingest.json_importer import IngestError, ingest_json
from app.ingest.sword_importer import ingest_sword
from app.logging import configure_logging


def _cmd_init_db(_args: argparse.Namespace) -> int:
    init_db()
    print("Database initialized")
    return 0


def _cmd_ingest_json(args: argparse.Namespace) -> int:
    try:
        inserted = ingest_json(Path(args.path), replace=args.replace)
    except IngestError as exc:
        print(f"Ingest failed: {exc}", file=sys.stderr)
        return 1
    print(f"Inserted {inserted} entries")
    return 0


def _cmd_ingest_sword(args: argparse.Namespace) -> int:
    try:
        inserted = ingest_sword(Path(args.sword_path), args.module, replace=args.replace)
    except IngestError as exc:
        print(f"Ingest failed: {exc}", file=sys.stderr)
        return 1
    print(f"Inserted {inserted} entries")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Commentariat ingestion CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_db_parser = subparsers.add_parser("init-db", help="Initialize database")
    init_db_parser.set_defaults(func=_cmd_init_db)

    ingest_json_parser = subparsers.add_parser(
        "ingest-json", help="Ingest a commentary from JSON or NDJSON"
    )
    ingest_json_parser.add_argument("path", help="Path to JSON manifest")
    ingest_json_parser.add_argument(
        "--replace",
        action="store_true",
        help="Delete existing entries for this commentary before import",
    )
    ingest_json_parser.set_defaults(func=_cmd_ingest_json)

    ingest_sword_parser = subparsers.add_parser(
        "ingest-sword", help="Ingest a SWORD commentary module directly"
    )
    ingest_sword_parser.add_argument("sword_path", help="Path to SWORD library")
    ingest_sword_parser.add_argument("module", help="SWORD module name")
    ingest_sword_parser.add_argument(
        "--replace",
        action="store_true",
        help="Delete existing entries for this commentary before import",
    )
    ingest_sword_parser.set_defaults(func=_cmd_ingest_sword)

    return parser


def main() -> int:
    configure_logging()
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
