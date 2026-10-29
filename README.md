# SQL & Database Testing Demo

## What This Is
Extends the Docker Compose demo with **direct database testing** using psycopg2.
The test-runner now connects to BOTH the API and PostgreSQL directly.

## Architecture
```
┌─────────────┐     ┌─────────────┐     ┌──────────────┐
│     db      │     │     api     │     │  test-runner  │
│  PostgreSQL │◄────│  Flask API  │◄────│    pytest     │
│  Port 5432  │     │  Port 5000  │     │              │
└──────┬──────┘     └─────────────┘     └──────┬───────┘
       │                                        │
       └────────────────────────────────────────┘
           test-runner ALSO connects directly to DB
```

## Run Everything
```bash
docker compose up --build --abort-on-container-exit
```

## Test Files
- `tests/test_product_api.py` — API-level tests (from last session)
- `tests/test_database.py` — Database-level tests (NEW)
- `tests/conftest.py` — Shared fixtures for API and DB connections

## Connect to DB Manually (for practice)
While containers are running (`docker compose up` without --abort-on-container-exit):
```bash
docker compose exec db psql -U testuser -d testdb
```

Then try:
```sql
SELECT * FROM products;
SELECT name, price FROM products WHERE price > 20;
SELECT COUNT(*) FROM products;
\q   -- quit
```

## View Test Report
After tests finish: `reports/report.html`
