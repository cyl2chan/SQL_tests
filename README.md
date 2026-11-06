# SQL & Database Testing Demo

## Project Description
The database in this project contains products with different product ID, names, and whether they are in stock. 

I did the following:
- **Wrote 3 new database tests**: (a) Verified that after creating 2 products via API, the DB count increased by exactly 2. (b) Verified that updating a product's price via a new PUT endpoint is reflected in the DB. (c) Verified that the 'in_stock' field in the DB matches what the API returns for each product.
- **Added a PUT endpoint to server.py**: The API originally had GET, POST, DELETE but no UPDATE. I added a PUT /api/products/<id> endpoint that updates name, price, or in_stock. I have written both an API test and a DB test for it.
- **Added a second table ('Orders')** and **wrote a test** that validates a product referenced in an order actually exists in the products table.

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
