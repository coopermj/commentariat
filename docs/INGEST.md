# Ingestion Pipeline

## Supported input
The ingest CLI reads a JSON manifest that describes a commentary plus its entries.
Use a list for small datasets or an NDJSON file for large ones.

Manifest example (inline entries):
```
{
  "commentary": {
    "name": "Matthew Henry",
    "slug": "mhenry",
    "description": "Concise commentary on the whole Bible",
    "source": "SWORD: MatthewHenry",
    "license": "Public Domain",
    "language": "en"
  },
  "entries": [
    {"book": "Genesis", "chapter": 1, "verse": 1, "text": "..."}
  ]
}
```

Manifest example (NDJSON):
```
{
  "commentary": {
    "name": "Jamieson-Fausset-Brown",
    "slug": "jfb",
    "description": "Commentary on the whole Bible",
    "source": "SWORD: JFB",
    "license": "Public Domain",
    "language": "en"
  },
  "entries_file": "jfb.ndjson"
}
```

Each NDJSON line is a single entry:
```
{"book": "John", "chapter": 3, "verse": "16", "text": "..."}
{"book": "John", "chapter": 3, "verse_start": 16, "verse_end": 18, "text": "..."}
```

Notes:
- Book names are normalized; common aliases like `Gen`, `Jn`, or `1Cor` work.
- Verse ranges can be provided via `verse_start`/`verse_end` or `verse: "1-3"`.
- `entries_file` is resolved relative to the manifest location.

## Suggested SWORD export flow
SWORD modules typically live under a library containing `mods.d/` and `modules/`.
Export them into NDJSON, then ingest with the JSON manifest.

Recommended approach:
1) Acquire public domain SWORD modules.
2) Use your preferred SWORD tooling (e.g., `diatheke`) to dump verse-by-verse
   entries into NDJSON:
   - Output each line with `book`, `chapter`, `verse`, and `text`.
3) Create a manifest JSON pointing to the NDJSON file.
4) Run the ingest CLI:
```
python scripts/ingest.py init-db
python scripts/ingest.py ingest-json data/manifests/mhenry.json --replace
```

This repo includes a helper for diatheke-based export:
```
PYTHONPATH=. python3 scripts/export_sword.py CalvinCommentaries \
  --sword-path data/sword \
  --output data/entries/calvincommentaries.ndjson
```
