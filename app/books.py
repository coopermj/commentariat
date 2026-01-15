"""Canonical book names and alias normalization."""

from __future__ import annotations

from typing import Dict, Iterable, List

BOOK_ALIASES: Dict[str, List[str]] = {
    "Genesis": ["gen", "ge", "gn"],
    "Exodus": ["exod", "exo", "ex"],
    "Leviticus": ["lev", "lv", "levit"],
    "Numbers": ["num", "nm", "nb"],
    "Deuteronomy": ["deut", "dt", "deu"],
    "Joshua": ["josh", "jos", "jsh"],
    "Judges": ["judg", "jdg", "jdgs", "jgs"],
    "Ruth": ["ruth", "ru", "rth"],
    "1 Samuel": ["1sam", "1samuel", "1sa", "1sm", "isamuel", "firstsamuel"],
    "2 Samuel": ["2sam", "2samuel", "2sa", "2sm", "iisamuel", "secondsamuel"],
    "1 Kings": ["1kgs", "1kings", "1ki", "1k", "ikings", "firstkings"],
    "2 Kings": ["2kgs", "2kings", "2ki", "2k", "iikings", "secondkings"],
    "1 Chronicles": [
        "1chr",
        "1chron",
        "1chronicles",
        "1ch",
        "ichronicles",
        "firstchronicles",
    ],
    "2 Chronicles": [
        "2chr",
        "2chron",
        "2chronicles",
        "2ch",
        "iichronicles",
        "secondchronicles",
    ],
    "Ezra": ["ezra", "ezr"],
    "Nehemiah": ["neh", "ne", "nehemiah"],
    "Esther": ["esth", "est", "es"],
    "Job": ["job", "jb"],
    "Psalms": ["ps", "psa", "psalm", "psalms"],
    "Proverbs": ["prov", "pr", "prv"],
    "Ecclesiastes": ["eccl", "ecc", "ec", "qoh"],
    "Song of Solomon": [
        "song",
        "songofsolomon",
        "songofsongs",
        "cant",
        "canticles",
        "sos",
    ],
    "Isaiah": ["isa", "is", "isaiah"],
    "Jeremiah": ["jer", "je", "jeremiah"],
    "Lamentations": ["lam", "la", "lamentations"],
    "Ezekiel": ["ezek", "eze", "ezk"],
    "Daniel": ["dan", "da", "dn"],
    "Hosea": ["hos", "ho"],
    "Joel": ["joel", "joe", "jl"],
    "Amos": ["amos", "am"],
    "Obadiah": ["obad", "ob", "oba"],
    "Jonah": ["jonah", "jon", "jh"],
    "Micah": ["mic", "mc"],
    "Nahum": ["nah", "na"],
    "Habakkuk": ["hab", "hb"],
    "Zephaniah": ["zeph", "zep", "zp"],
    "Haggai": ["hag", "hg"],
    "Zechariah": ["zech", "zec", "zc"],
    "Malachi": ["mal", "ml"],
    "Matthew": ["matt", "mt", "mat"],
    "Mark": ["mark", "mr", "mk"],
    "Luke": ["luke", "lk", "lu"],
    "John": ["john", "jn", "jhn"],
    "Acts": ["acts", "ac"],
    "Romans": ["rom", "ro", "rm"],
    "1 Corinthians": [
        "1cor",
        "1corinthians",
        "1co",
        "1cor",
        "icor",
        "firstcorinthians",
    ],
    "2 Corinthians": [
        "2cor",
        "2corinthians",
        "2co",
        "2cor",
        "iicor",
        "secondcorinthians",
    ],
    "Galatians": ["gal", "ga"],
    "Ephesians": ["eph", "ep"],
    "Philippians": ["phil", "php", "phl"],
    "Colossians": ["col", "co"],
    "1 Thessalonians": [
        "1thess",
        "1thessalonians",
        "1th",
        "ithess",
        "firstthessalonians",
    ],
    "2 Thessalonians": [
        "2thess",
        "2thessalonians",
        "2th",
        "iithess",
        "secondthessalonians",
    ],
    "1 Timothy": ["1tim", "1timothy", "1ti", "itimothy", "firsttimothy"],
    "2 Timothy": ["2tim", "2timothy", "2ti", "iitimothy", "secondtimothy"],
    "Titus": ["titus", "tit", "ti"],
    "Philemon": ["phlm", "phm", "philemon"],
    "Hebrews": ["heb", "he"],
    "James": ["jas", "jam", "jm"],
    "1 Peter": ["1pet", "1peter", "1pe", "ipeter", "firstpeter"],
    "2 Peter": ["2pet", "2peter", "2pe", "iipeter", "secondpeter"],
    "1 John": ["1john", "1jn", "1jo", "ijohn", "firstjohn"],
    "2 John": ["2john", "2jn", "2jo", "iijohn", "secondjohn"],
    "3 John": ["3john", "3jn", "3jo", "iiijohn", "thirdjohn"],
    "Jude": ["jude", "jud"],
    "Revelation": ["rev", "re", "revelation", "apocalypse"],
}


def _normalize(token: str) -> str:
    return "".join(ch for ch in token.lower() if ch.isalnum())


ALIAS_TO_CANONICAL: Dict[str, str] = {}
for canonical, aliases in BOOK_ALIASES.items():
    for alias in [canonical, *aliases]:
        ALIAS_TO_CANONICAL[_normalize(alias)] = canonical


CANONICAL_BOOKS: List[str] = list(BOOK_ALIASES.keys())


def normalize_book(value: str) -> str:
    if not value:
        raise ValueError("Book name is required")
    normalized = _normalize(value)
    canonical = ALIAS_TO_CANONICAL.get(normalized)
    if not canonical:
        raise ValueError(f"Unknown book: {value}")
    return canonical


def list_books() -> List[Dict[str, Iterable[str]]]:
    return [
        {
            "canonical": canonical,
            "aliases": sorted(set(BOOK_ALIASES[canonical])),
        }
        for canonical in CANONICAL_BOOKS
    ]
