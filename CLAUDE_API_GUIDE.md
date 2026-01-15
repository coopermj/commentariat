# Commentariat API Guide

API for retrieving Biblical commentary text from classic commentators.

## Base URL

```
https://commentariat-production.up.railway.app
```

## Available Commentaries

| Slug | Name | Coverage |
|------|------|----------|
| `mhc` | Matthew Henry's Complete Commentary | All 66 books |
| `calvincommentaries` | Calvin's Collected Commentaries | Genesis, Exodus, Leviticus, Numbers, Deuteronomy, Joshua, Psalms, Isaiah-Malachi (Prophets), Matthew-Revelation (NT) |

## Endpoints

### List All Commentaries

```
GET /commentaries
```

Response:
```json
{
  "commentaries": [
    {
      "slug": "mhc",
      "name": "Matthew Henry's Complete Commentary on the Whole Bible",
      "description": "...",
      "source": "SWORD: mhc",
      "license": "Public Domain",
      "language": "en"
    }
  ]
}
```

### Get Commentary Metadata

```
GET /commentaries/{slug}
```

Example: `GET /commentaries/mhc`

### Get Chapter Commentary

```
GET /commentaries/{slug}/{book}/{chapter}
```

Example: `GET /commentaries/mhc/Romans/8`

Response:
```json
{
  "commentary": { "slug": "mhc", "name": "...", ... },
  "book": "Romans",
  "chapter": 8,
  "count": 39,
  "entries": [
    {
      "verse_start": 1,
      "verse_end": 1,
      "text": "Commentary text for verse 1..."
    },
    {
      "verse_start": 2,
      "verse_end": 2,
      "text": "Commentary text for verse 2..."
    }
  ]
}
```

### Get Verse Commentary

```
GET /commentaries/{slug}/{book}/{chapter}/{verse}
```

Example: `GET /commentaries/mhc/John/3/16`

Response:
```json
{
  "commentary": { "slug": "mhc", "name": "...", ... },
  "book": "John",
  "chapter": 3,
  "verse": 16,
  "count": 1,
  "entries": [
    {
      "verse_start": 16,
      "verse_end": 16,
      "text": "Commentary text..."
    }
  ]
}
```

### List Available Books

```
GET /books
```

Returns canonical book names to use in URLs.

## Book Name Formats

The API accepts various book name formats and normalizes them:

| Accepted Formats | Canonical Name |
|------------------|----------------|
| `Genesis`, `Gen`, `Ge` | Genesis |
| `1Kings`, `1 Kings`, `1Kgs`, `I Kings` | 1 Kings |
| `Psalms`, `Psalm`, `Ps`, `Psa` | Psalms |
| `Matthew`, `Matt`, `Mt` | Matthew |
| `1Corinthians`, `1 Cor`, `I Corinthians` | 1 Corinthians |
| `Revelation`, `Rev`, `Apocalypse` | Revelation |

## Python Example

```python
import httpx

BASE_URL = "https://commentariat-production.up.railway.app"

def get_chapter_commentary(slug: str, book: str, chapter: int) -> dict:
    """Fetch all commentary entries for a chapter."""
    response = httpx.get(f"{BASE_URL}/commentaries/{slug}/{book}/{chapter}")
    response.raise_for_status()
    return response.json()

def get_verse_commentary(slug: str, book: str, chapter: int, verse: int) -> str | None:
    """Fetch commentary text for a specific verse."""
    response = httpx.get(f"{BASE_URL}/commentaries/{slug}/{book}/{chapter}/{verse}")
    response.raise_for_status()
    data = response.json()
    if data["entries"]:
        return data["entries"][0]["text"]
    return None

# Usage
chapter_data = get_chapter_commentary("mhc", "Romans", 8)
for entry in chapter_data["entries"]:
    print(f"Verse {entry['verse_start']}: {entry['text'][:100]}...")

verse_text = get_verse_commentary("mhc", "John", 3, 16)
print(verse_text)
```

## Fetching Multiple Commentaries

To get commentary from all available sources for a verse:

```python
def get_all_commentaries_for_verse(book: str, chapter: int, verse: int) -> dict[str, str]:
    """Get commentary from all sources for a single verse."""
    commentaries = httpx.get(f"{BASE_URL}/commentaries").json()["commentaries"]
    results = {}

    for comm in commentaries:
        slug = comm["slug"]
        resp = httpx.get(f"{BASE_URL}/commentaries/{slug}/{book}/{chapter}/{verse}")
        if resp.status_code == 200:
            data = resp.json()
            if data["entries"]:
                results[comm["name"]] = data["entries"][0]["text"]

    return results

# Get all available commentary on John 1:1
commentaries = get_all_commentaries_for_verse("John", 1, 1)
for name, text in commentaries.items():
    print(f"=== {name} ===")
    print(text[:500])
    print()
```

## Processing Commentary Text

The commentary text may contain:
- Verse markers like `* 1 *` indicating verse numbers
- `\par` for paragraph breaks (from SWORD format)
- Plain text commentary

To clean the text:

```python
import re

def clean_commentary_text(text: str) -> str:
    """Remove SWORD formatting artifacts from commentary text."""
    # Remove verse markers like * 1 *
    text = re.sub(r'\*\s*\d+\s*\*', '', text)
    # Replace \par with newlines
    text = text.replace('\\par', '\n')
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text
```

## Error Handling

| Status | Meaning |
|--------|---------|
| 200 | Success |
| 400 | Invalid book name or chapter/verse must be positive |
| 404 | Commentary not found |
| 500 | Server error |

Example error response:
```json
{"detail": "Unknown book: NotABook"}
```

## Rate Limits

No rate limits currently enforced. Be respectful with request volume.
