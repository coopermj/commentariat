# commentariat
Captures common Biblical commentaries and exposes them via API.

## API endpoints
- `GET /healthz`
- `GET /books`
- `GET /commentaries`
- `GET /commentaries/{name}`
- `GET /commentaries/{name}/{book}/{chapter}`
- `GET /commentaries/{name}/{book}/{chapter}/{verse}`

Responses are JSON. Book names accept canonical names or aliases (e.g., `Gen`,
`1Cor`, `Song of Solomon`).

## Quickstart
```
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python scripts/ingest.py init-db
python scripts/ingest.py ingest-json data/manifests/example.json --replace

uvicorn app.main:app --reload
```

## Ingestion pipeline
See `docs/INGEST.md` for the JSON manifest format and SWORD export guidance.
Recommended sources are listed in `docs/SOURCES.md`.

## Railway recommendations
- Set `PORT` (Railway provides this automatically).
- Use a persistent volume if you keep SQLite, and set `DATABASE_PATH` to a
  writable location (for example `/data/commentariat.db`).
- If you switch to Postgres, the storage layer will need to be adapted.
