"""FastAPI entrypoint for the Commentariat API."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException

from app.books import list_books, normalize_book
from app.db import init_db
from app.logging import configure_logging, get_logger
from app.storage import (
    get_commentary,
    list_commentaries,
    list_entries_for_chapter,
    list_entries_for_verse,
)

logger = get_logger(__name__)

app = FastAPI(title="Commentariat API", version="0.1.0")


@app.on_event("startup")
def startup() -> None:
    configure_logging()
    logger.info("Initializing database")
    init_db()
    logger.info("Commentariat API started")


def _serialize_commentary(raw: dict) -> dict:
    data = dict(raw)
    data.pop("id", None)
    return data


def _require_positive(value: int, label: str) -> None:
    if value <= 0:
        raise HTTPException(status_code=400, detail=f"{label} must be positive")


@app.get("/healthz")
def healthz() -> dict:
    return {"status": "ok"}


@app.get("/books")
def books() -> dict:
    return {"books": list_books()}


@app.get("/commentaries")
def commentaries() -> dict:
    return {"commentaries": list_commentaries()}


@app.get("/commentaries/{name}")
def commentary(name: str) -> dict:
    commentary_row = get_commentary(name)
    if not commentary_row:
        raise HTTPException(status_code=404, detail="Commentary not found")
    return _serialize_commentary(commentary_row)


@app.get("/commentaries/{name}/{book}/{chapter}")
def commentary_chapter(name: str, book: str, chapter: int) -> dict:
    _require_positive(chapter, "chapter")
    commentary_row = get_commentary(name)
    if not commentary_row:
        raise HTTPException(status_code=404, detail="Commentary not found")
    try:
        canonical_book = normalize_book(book)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    entries = list_entries_for_chapter(commentary_row["id"], canonical_book, chapter)
    return {
        "commentary": _serialize_commentary(commentary_row),
        "book": canonical_book,
        "chapter": chapter,
        "count": len(entries),
        "entries": entries,
    }


@app.get("/commentaries/{name}/{book}/{chapter}/{verse}")
def commentary_verse(name: str, book: str, chapter: int, verse: int) -> dict:
    _require_positive(chapter, "chapter")
    _require_positive(verse, "verse")
    commentary_row = get_commentary(name)
    if not commentary_row:
        raise HTTPException(status_code=404, detail="Commentary not found")
    try:
        canonical_book = normalize_book(book)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    entries = list_entries_for_verse(
        commentary_row["id"], canonical_book, chapter, verse
    )
    return {
        "commentary": _serialize_commentary(commentary_row),
        "book": canonical_book,
        "chapter": chapter,
        "verse": verse,
        "count": len(entries),
        "entries": entries,
    }
