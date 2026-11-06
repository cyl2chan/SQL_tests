"""
Database Tests — these connect DIRECTLY to PostgreSQL, bypassing the API.

WHY test at the database level?
  - API tests tell you: "The API said it worked."
  - DB tests tell you:  "The data is ACTUALLY there."

These are your 'receipts' — verifying the API didn't just return 201
but actually wrote the row to the database.

IMPORTANT: These tests use the db_connection and db_cursor fixtures
from conftest.py. You don't need to import them — pytest finds them
automatically.
"""
import pytest
import requests
import os
from decimal import Decimal

BASE_URL = os.environ.get("API_URL", "http://api:5000")


# ═══════════════════════════════════════════════════════════
#  PART 1: SQL Basics — Reading data with SELECT
# ═══════════════════════════════════════════════════════════

class TestSQLBasics:
    """
    These tests teach fundamental SQL by running queries against the
    seeded test data. Each test demonstrates a different SQL concept.
    """

    def test_select_all_products(self, db_cursor):
        """
        SELECT * FROM products;
        The most basic query — get everything from a table.
        """
        db_cursor.execute("SELECT * FROM products")
        rows = db_cursor.fetchall()

        # We seeded 4 products in server.py's init_db()
        assert len(rows) >= 4

    def test_select_specific_columns(self, db_cursor):
        """
        SELECT name, price FROM products;
        You don't always need every column — select only what you need.
        """
        db_cursor.execute("SELECT name, price FROM products")
        rows = db_cursor.fetchall()

        # Each row is a tuple: (name, price)
        names = [row[0] for row in rows]
        assert "Sauce Labs Backpack" in names

    def test_select_with_where(self, db_cursor):
        """
        SELECT * FROM products WHERE name = 'Sauce Labs Backpack';
        WHERE filters rows — like a search.
        """
        db_cursor.execute(
            "SELECT name, price FROM products WHERE name = %s",
            ("Sauce Labs Backpack",)
        )
        row = db_cursor.fetchone()

        assert row is not None
        assert row[0] == "Sauce Labs Backpack"
        assert row[1] == Decimal("29.99")   # PostgreSQL returns Decimal for NUMERIC

    def test_select_with_comparison(self, db_cursor):
        """
        SELECT name, price FROM products WHERE price > 20.00;
        Comparison operators: >, <, >=, <=, =, != (or <>)
        """
        db_cursor.execute("SELECT name, price FROM products WHERE price > 20.00")
        rows = db_cursor.fetchall()

        # Only Backpack (29.99) and Fleece Jacket (49.99) cost > $20
        names = [row[0] for row in rows]
        assert "Sauce Labs Backpack" in names
        assert "Sauce Labs Fleece Jacket" in names
        assert "Sauce Labs Bike Light" not in names  # 9.99, should NOT appear

    def test_select_with_count(self, db_cursor):
        """
        SELECT COUNT(*) FROM products;
        COUNT returns the number of rows matching the query.
        """
        db_cursor.execute("SELECT COUNT(*) FROM products")
        count = db_cursor.fetchone()[0]

        assert count >= 4

    def test_select_with_order_by(self, db_cursor):
        """
        SELECT name, price FROM products ORDER BY price ASC;
        ORDER BY sorts results. ASC = cheapest first. DESC = most expensive first.
        """
        db_cursor.execute("SELECT name, price FROM products ORDER BY price ASC")
        rows = db_cursor.fetchall()

        prices = [row[1] for row in rows]
        assert prices == sorted(prices)   # Verify ascending order

    def test_select_with_in_stock_filter(self, db_cursor):
        """
        SELECT name FROM products WHERE in_stock = TRUE;
        Boolean filters — find products that are available.
        """
        db_cursor.execute("SELECT name FROM products WHERE in_stock = TRUE")
        in_stock = [row[0] for row in db_cursor.fetchall()]

        db_cursor.execute("SELECT name FROM products WHERE in_stock = FALSE")
        out_of_stock = [row[0] for row in db_cursor.fetchall()]

        assert "Sauce Labs Backpack" in in_stock
        assert "Sauce Labs Fleece Jacket" in out_of_stock


# ═══════════════════════════════════════════════════════════
#  PART 2: API + DB Validation — The 'Receipts' Pattern
# ═══════════════════════════════════════════════════════════

class TestAPIWithDBValidation:
    """
    These tests call the API, then check the DATABASE directly
    to verify the data was actually written/deleted correctly.

    This is the 'receipts over claims' pattern:
      - The API says 201 Created? Check the DB to confirm.
      - The API says 200 Deleted? Check the DB row is gone.
    """

    def test_create_product_appears_in_database(self, db_cursor, db_connection):
        """
        POST to API → then SELECT from DB to verify the row exists.
        The API could return 201 but fail to write — this catches that.
        """
        # Step 1: Create via API
        payload = {"name": "DB Verification Widget", "price": 19.99, "in_stock": True}
        response = requests.post(f"{BASE_URL}/api/products", json=payload)
        assert response.status_code == 201
        product_id = response.json()["id"]

        # Step 2: Verify DIRECTLY in the database
        db_cursor.execute(
            "SELECT name, price, in_stock FROM products WHERE id = %s",
            (product_id,)
        )
        row = db_cursor.fetchone()

        assert row is not None, f"Product {product_id} not found in database!"
        assert row[0] == "DB Verification Widget"
        assert row[1] == Decimal("19.99")
        assert row[2] is True

        # Cleanup: delete via API
        requests.delete(f"{BASE_URL}/api/products/{product_id}")

    def test_delete_product_removed_from_database(self, db_cursor, db_connection):
        """
        POST to create → DELETE via API → SELECT to confirm row is gone.
        """
        # Setup: create a product to delete
        payload = {"name": "Delete Me", "price": 1.00}
        response = requests.post(f"{BASE_URL}/api/products", json=payload)
        product_id = response.json()["id"]

        # Act: delete via API
        delete_response = requests.delete(f"{BASE_URL}/api/products/{product_id}")
        assert delete_response.status_code == 200

        # Verify: row is gone from the database
        db_cursor.execute(
            "SELECT * FROM products WHERE id = %s",
            (product_id,)
        )
        row = db_cursor.fetchone()
        assert row is None, f"Product {product_id} still exists in DB after API delete!"

    def test_api_product_count_matches_db_count(self, db_cursor):
        """
        GET /api/products count should match SELECT COUNT(*) FROM products.
        If these don't match, the API is filtering or hiding data.
        """
        # Count from API
        api_response = requests.get(f"{BASE_URL}/api/products")
        api_count = len(api_response.json())

        # Count from DB
        db_cursor.execute("SELECT COUNT(*) FROM products")
        db_count = db_cursor.fetchone()[0]

        assert api_count == db_count, \
            f"API returned {api_count} products but DB has {db_count}"

    def test_api_prices_match_db_prices(self, db_cursor):
        """
        Verify the API isn't transforming or rounding prices.
        The price in the API response should exactly match the database.
        """
        # Get from API
        api_response = requests.get(f"{BASE_URL}/api/products/1")
        api_price = api_response.json()["price"]

        # Get from DB
        db_cursor.execute("SELECT price FROM products WHERE id = 1")
        db_price = float(db_cursor.fetchone()[0])

        assert api_price == db_price, \
            f"API price {api_price} doesn't match DB price {db_price}"


    # Homework 14. (a) Verify that after creating 2 products via API, the DB count increased by exactly 2.
    def test_create_2_products_DB_count_increase_2(self, db_cursor):
        """
        POST 2 products to API → then SELECT from DB to verify count increased by 2.
        The API could return 201 but fail to write — this catches that.
        """
        # Step 1: Check count in DB
        db_cursor.execute("SELECT COUNT(*) FROM products")
        db_count_before = db_cursor.fetchone()[0]

        # Step 2: Create 2 products via API
        payload = {"name": "DB Added Widget 1", "price": 39.99, "in_stock": True}
        response = requests.post(f"{BASE_URL}/api/products", json=payload)
        assert response.status_code == 201
        product1_id = response.json()["id"]

        payload = {"name": "DB Added Widget 2", "price": 99.99, "in_stock": True}
        response = requests.post(f"{BASE_URL}/api/products", json=payload)
        assert response.status_code == 201
        product2_id = response.json()["id"]

        # Step 3: Check count in DB, verify count in DB increased by 2
        db_cursor.execute("SELECT COUNT(*) FROM products")
        db_count_after = db_cursor.fetchone()[0]

        assert db_count_after - db_count_before == 2

        # Cleanup: delete via API
        requests.delete(f"{BASE_URL}/api/products/{product1_id}")
        requests.delete(f"{BASE_URL}/api/products/{product2_id}")

    # Homework 14. (b) Verify that updating a product's price via a new PUT endpoint is reflected in the DB.
    def test_update_product_price_PUT_reflected_in_DB(self, db_cursor):
        # Step 1: update product's price via PUT
        product_id = 1
        payload = {"name": "Sauce Labs Backpack", "price":99.99}
        response_PUT = requests.put(f"{BASE_URL}/api/products/{product_id}", json=payload)
        api_price = response_PUT.json()["price"]    # Decimal
        assert response_PUT.status_code == 200, \
            f"response body: {response_PUT.text}; response header: {response_PUT.headers}"

        # Step 2: verify it's reflected in DB
        db_cursor.execute("SELECT price FROM products WHERE id = 1")
        db_price = db_cursor.fetchone()[0]  # float
        print("db_price:", db_price, "api_price:", api_price)
        assert db_price == Decimal(str(api_price))

        # Step 3: restore price back to original $29.99
        product_id = 1
        payload = {"product_id": 1, "name": "Sauce Labs Backpack", "price":29.99}
        response_PUT = requests.put(f"{BASE_URL}/api/products/{product_id}", json=payload)
        api_original_price = response_PUT.json()["price"]
        assert response_PUT.status_code == 200, \
            f"response body: {response_PUT.text}; response header: {response_PUT.headers}"
        
        db_cursor.execute("SELECT price FROM products WHERE id = 1")
        db_original_price = db_cursor.fetchone()[0]
        assert db_original_price == Decimal(str(api_original_price)) == Decimal(str(29.99)), \
            f"db_original_price: {db_original_price}; api_original_price: {api_original_price}"


    # Homework 14. (c) Verify that the 'in_stock' field in the DB matches what the API returns for each product.
    def test_in_stock_field_in_DB_matches_API_return(self, db_cursor):
        # Step 1: Get from API
        api_response = requests.get(f"{BASE_URL}/api/products")
        assert api_response.status_code == 200, api_response.text

        #in_stocks = [api_in_stock["in_stock"] for api_in_stock in api_in_stocks] # [True, True, True, False,
        api_in_stock = sorted(
            (product["id"], product["in_stock"])
            for product in api_response.json()
        )

        # Step 2: Get from DB
        db_cursor.execute("SELECT id, in_stock FROM products ORDER by id")
        db_in_stock = db_cursor.fetchall()

        assert api_in_stock == db_in_stock, f"api_in_stock: {api_in_stock}, db_in_stock: {db_in_stock}"

    
# ═══════════════════════════════════════════════════════════
#  PART 3: Data Integrity Tests
# ═══════════════════════════════════════════════════════════

class TestDataIntegrity:
    """
    These tests validate the DATABASE RULES themselves.
    Not about the API — about whether the schema constraints are correct.
    """

    def test_product_ids_are_unique(self, db_cursor):
        """Every product should have a unique ID (enforced by PRIMARY KEY)."""
        db_cursor.execute("SELECT id FROM products")
        ids = [row[0] for row in db_cursor.fetchall()]
        assert len(ids) == len(set(ids)), "Duplicate product IDs found!"

    def test_product_names_are_not_empty(self, db_cursor):
        """No product should have an empty or NULL name."""
        db_cursor.execute(
            "SELECT id, name FROM products WHERE name IS NULL OR name = ''"
        )
        bad_rows = db_cursor.fetchall()
        assert len(bad_rows) == 0, f"Products with empty names: {bad_rows}"

    def test_product_prices_are_positive(self, db_cursor):
        """No product should have a zero or negative price."""
        db_cursor.execute("SELECT id, name, price FROM products WHERE price <= 0")
        bad_rows = db_cursor.fetchall()
        assert len(bad_rows) == 0, f"Products with non-positive prices: {bad_rows}"

    def test_in_stock_is_not_null(self, db_cursor):
        """Every product should have an explicit in_stock value (not NULL)."""
        db_cursor.execute("SELECT id, name FROM products WHERE in_stock IS NULL")
        bad_rows = db_cursor.fetchall()
        assert len(bad_rows) == 0, f"Products with NULL in_stock: {bad_rows}"


# ═══════════════════════════════════════════════════════════
#  PART 4: INSERT / UPDATE / DELETE from Python
# ═══════════════════════════════════════════════════════════

class TestSQLWriteOperations:
    """
    These tests demonstrate writing to the database directly from Python.
    Each test cleans up after itself using db_connection.rollback().
    """

    def test_insert_and_read_back(self, db_cursor, db_connection):
        """
        INSERT INTO products (name, price) VALUES ('Test', 5.00);
        Then SELECT to verify.
        """
        db_cursor.execute(
            "INSERT INTO products (name, price, in_stock) VALUES (%s, %s, %s) RETURNING id",
            ("Direct Insert Product", 7.77, True)
        )
        new_id = db_cursor.fetchone()[0]
        db_connection.commit()

        # Read it back
        db_cursor.execute("SELECT name, price FROM products WHERE id = %s", (new_id,))
        row = db_cursor.fetchone()
        assert row[0] == "Direct Insert Product"
        assert row[1] == Decimal("7.77")

        # Cleanup
        db_cursor.execute("DELETE FROM products WHERE id = %s", (new_id,))
        db_connection.commit()

    def test_update_product_price(self, db_cursor, db_connection):
        """
        UPDATE products SET price = 99.99 WHERE id = 1;
        Modify an existing row, verify, then restore.
        """
        # Save original price
        db_cursor.execute("SELECT price FROM products WHERE id = 1")
        original_price = db_cursor.fetchone()[0]

        # Update
        db_cursor.execute("UPDATE products SET price = %s WHERE id = 1", (Decimal("99.99"),))
        db_connection.commit()

        # Verify the update
        db_cursor.execute("SELECT price FROM products WHERE id = 1")
        updated_price = db_cursor.fetchone()[0]
        assert updated_price == Decimal("99.99")

        # Restore original price (cleanup)
        db_cursor.execute("UPDATE products SET price = %s WHERE id = 1", (original_price,))
        db_connection.commit()

    def test_delete_and_verify_gone(self, db_cursor, db_connection):
        """
        INSERT a row, DELETE it, verify it's gone.
        """
        # Create
        db_cursor.execute(
            "INSERT INTO products (name, price) VALUES (%s, %s) RETURNING id",
            ("To Be Deleted", 0.01)
        )
        product_id = db_cursor.fetchone()[0]
        db_connection.commit()

        # Delete
        db_cursor.execute("DELETE FROM products WHERE id = %s", (product_id,))
        db_connection.commit()

        # Verify gone
        db_cursor.execute("SELECT * FROM products WHERE id = %s", (product_id,))
        assert db_cursor.fetchone() is None


# Homework 16. Bonus: Write a test that validates a product referenced in an order in table Orders
# actually exists in the products table.
# ═══════════════════════════════════════════════════════════
#  PART 5: validates a product referenced in an order in table Orders
# actually exists in the products table
# ═══════════════════════════════════════════════════════════

class TestSameColumnOrdersProducts:
    def test_product_referenced_in_order_exists_in_products(self, db_cursor, db_connection):
