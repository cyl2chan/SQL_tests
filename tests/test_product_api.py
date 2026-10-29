"""
API Tests — these test the API endpoints from the outside.
They tell us: 'Does the API respond correctly?'
They do NOT tell us: 'Is the data actually in the database?'
That's what test_database.py is for.
"""
import pytest
import requests
import os

BASE_URL = os.environ.get("API_URL", "http://api:5000")


# ─── GET Tests ───────────────────────────────────────────

class TestGetProducts:
    """Tests for the GET /api/products endpoint."""

    def test_get_all_products_returns_200(self):
        response = requests.get(f"{BASE_URL}/api/products")
        assert response.status_code == 200

    def test_get_all_products_returns_list(self):
        response = requests.get(f"{BASE_URL}/api/products")
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 4

    def test_product_has_required_fields(self):
        """Validate the response schema — every product must have these keys."""
        response = requests.get(f"{BASE_URL}/api/products")
        data = response.json()
        required_fields = {"id", "name", "price", "in_stock"}
        for product in data:
            assert required_fields.issubset(product.keys()), \
                f"Product missing fields: {required_fields - product.keys()}"

    def test_get_single_product(self):
        response = requests.get(f"{BASE_URL}/api/products/1")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Sauce Labs Backpack"
        assert data["price"] == 29.99

    def test_get_nonexistent_product_returns_404(self):
        response = requests.get(f"{BASE_URL}/api/products/9999")
        assert response.status_code == 404


# ─── Parametrized Price Validation ───────────────────────

@pytest.mark.parametrize("product_id, expected_name, expected_price", [
    (1, "Sauce Labs Backpack", 29.99),
    (2, "Sauce Labs Bike Light", 9.99),
    (3, "Sauce Labs Bolt T-Shirt", 15.99),
])
def test_product_prices_match_catalog(product_id, expected_name, expected_price):
    response = requests.get(f"{BASE_URL}/api/products/{product_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == expected_name
    assert data["price"] == expected_price


# ─── POST Tests ──────────────────────────────────────────

class TestCreateProduct:
    def test_create_product_returns_201(self):
        payload = {"name": "Test Widget", "price": 5.99, "in_stock": True}
        response = requests.post(f"{BASE_URL}/api/products", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Widget"
        assert "id" in data

    def test_create_product_missing_name_returns_400(self):
        payload = {"price": 5.99}
        response = requests.post(f"{BASE_URL}/api/products", json=payload)
        assert response.status_code == 400

    def test_create_product_missing_price_returns_400(self):
        payload = {"name": "No Price Item"}
        response = requests.post(f"{BASE_URL}/api/products", json=payload)
        assert response.status_code == 400


# ─── Chained Test: Create → Read → Delete → Verify ──────

class TestProductLifecycle:
    def test_full_product_lifecycle(self):
        # 1) CREATE
        payload = {"name": "Lifecycle Test Item", "price": 42.00, "in_stock": True}
        create_resp = requests.post(f"{BASE_URL}/api/products", json=payload)
        assert create_resp.status_code == 201
        product_id = create_resp.json()["id"]

        # 2) READ
        read_resp = requests.get(f"{BASE_URL}/api/products/{product_id}")
        assert read_resp.status_code == 200
        assert read_resp.json()["name"] == "Lifecycle Test Item"

        # 3) DELETE
        delete_resp = requests.delete(f"{BASE_URL}/api/products/{product_id}")
        assert delete_resp.status_code == 200

        # 4) VERIFY GONE
        verify_resp = requests.get(f"{BASE_URL}/api/products/{product_id}")
        assert verify_resp.status_code == 404


# ─── Health Check ────────────────────────────────────────

def test_health_endpoint():
    response = requests.get(f"{BASE_URL}/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database"] == "connected"
