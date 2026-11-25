# Analyst Console — API (FastAPI)

OLTP API over the `ops` schema: alerts, agent tickets, and the analyst decision
audit trail. OpenAPI spec is served at `/docs` and `/openapi.json` (used to
generate the front-end TypeScript types in Step 2).

## Layout
```
app/
  main.py            FastAPI app + /health
  config.py          env (DATABASE_URL, CORS_ORIGINS)
  db.py              psycopg3 connection pool + get_conn dependency
  logic.py           pure action->status mapping (unit-tested)
  models.py          Pydantic schemas
  routers/
    alerts.py        GET /alerts, GET /alerts/{id}, POST /alerts/{id}/decision
    stats.py         GET /stats
tests/test_api.py    offline unit tests (no DB needed)
db/ops_schema.sql    operational schema
```

## Run locally
```bash
python -m venv .venv && source .venv/bin/activate   # fish: source .venv/bin/activate.fish
pip install -r requirements.txt

# apply the schema once (serving PostgreSQL must be up)
psql "$DATABASE_URL" -f db/ops_schema.sql

uvicorn app.main:app --reload
# -> http://localhost:8000/docs
```

## Test
```bash
pytest -q          # offline: mapping + /health
```

## Docker
```bash
docker build -t soc-console-api .
docker run --rm -p 8000:8000 --env-file .env soc-console-api
```

## Routes
| Method | Path | Purpose |
|---|---|---|
| GET  | `/alerts` | list with `severity, status, from, to, q, page, size` |
| GET  | `/alerts/{id}` | alert + ticket + decision history |
| POST | `/alerts/{id}/decision` | `{ action, analyst?, comment? }` → updates status, appends a decision |
| GET  | `/stats` | severity-over-time, agreement rate, detection coverage |
| GET  | `/health` | liveness |
