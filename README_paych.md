# SQLite JSON1/FTS5 memory API v2

## Run

```bash
pip install fastapi uvicorn pydantic
uvicorn app:app --reload --app-dir .
```

## Endpoints
- `POST /save_memory`
- `GET /search?q=...`
- `GET /fetch/{memory_id}`

## Search examples
- `text:"aggregate split" role:decision project:HVDC entity:DSV limit:5`
- `topic:invoice topic:storage entity:DSV status:active after:2026-03-01 limit:10`
