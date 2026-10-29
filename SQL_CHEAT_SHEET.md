# SQL Cheat Sheet for QE

## Reading Data (SELECT)

```sql
-- Get everything from a table
SELECT * FROM products;

-- Get specific columns
SELECT name, price FROM products;

-- Filter with WHERE
SELECT * FROM products WHERE price > 20.00;
SELECT * FROM products WHERE name = 'Sauce Labs Backpack';
SELECT * FROM products WHERE in_stock = TRUE;

-- Multiple conditions (AND / OR)
SELECT * FROM products WHERE price > 10.00 AND in_stock = TRUE;
SELECT * FROM products WHERE name = 'Backpack' OR name = 'Bike Light';

-- Count rows
SELECT COUNT(*) FROM products;
SELECT COUNT(*) FROM products WHERE in_stock = TRUE;

-- Sort results
SELECT * FROM products ORDER BY price ASC;   -- cheapest first
SELECT * FROM products ORDER BY price DESC;  -- most expensive first

-- Limit results
SELECT * FROM products ORDER BY price DESC LIMIT 3;  -- top 3 most expensive

-- Check for NULL
SELECT * FROM products WHERE in_stock IS NULL;
SELECT * FROM products WHERE in_stock IS NOT NULL;
```

## Writing Data

```sql
-- INSERT a new row
INSERT INTO products (name, price, in_stock) VALUES ('New Item', 9.99, TRUE);

-- INSERT and get the new ID back (PostgreSQL)
INSERT INTO products (name, price) VALUES ('New Item', 9.99) RETURNING id;

-- UPDATE existing rows
UPDATE products SET price = 24.99 WHERE id = 1;
UPDATE products SET in_stock = FALSE WHERE name = 'Sauce Labs Fleece Jacket';

-- DELETE rows
DELETE FROM products WHERE id = 5;
DELETE FROM products WHERE name = 'Test Product';
```

## Python + psycopg2 Patterns

```python
import psycopg2

# Connect
conn = psycopg2.connect(host="db", dbname="testdb", user="testuser", password="testpass")
cur = conn.cursor()

# READ (no commit needed)
cur.execute("SELECT name, price FROM products WHERE id = %s", (1,))
row = cur.fetchone()     # Single row: ('Sauce Labs Backpack', Decimal('29.99'))
rows = cur.fetchall()    # All rows: list of tuples

# WRITE (commit required!)
cur.execute("INSERT INTO products (name, price) VALUES (%s, %s)", ("New", 5.99))
conn.commit()            # <-- Without this, the insert doesn't persist!

# ALWAYS use %s placeholders, NEVER f-strings (SQL injection risk)
# ❌ DANGEROUS: cur.execute(f"SELECT * FROM products WHERE name = '{user_input}'")
# ✅ SAFE:      cur.execute("SELECT * FROM products WHERE name = %s", (user_input,))

# Cleanup
cur.close()
conn.close()
```

## Key Concepts

| Concept | Meaning |
|---------|---------|
| TABLE | Like a spreadsheet — rows and columns |
| ROW | One record (one product) |
| COLUMN | One field (name, price, etc.) |
| PRIMARY KEY | Unique ID for each row (like a serial number) |
| NULL | Empty / no value (different from 0 or empty string) |
| COMMIT | Save your changes (writes don't persist without it) |
| ROLLBACK | Undo changes since last commit |
