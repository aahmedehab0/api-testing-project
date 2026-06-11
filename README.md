# E-Commerce API Test Automation

This project implements automated testing for a RESTful e-commerce API using Python, Pytest, and a local FastAPI-based mock service backed by SQLite.



## Why this project

This project simulates a real-world QA automation scenario where APIs and databases must remain consistent. It demonstrates how automated testing can detect data mismatches, invalid API behavior, and ensure backend reliability in CI environments.

## Project Description

The project tests typical e-commerce workflows such as products and orders through HTTP API calls. It validates response status codes, schemas, and business logic, and cross-checks API data against a SQLite database to ensure consistency.

The system runs locally without external dependencies, making it suitable for repeatable test execution and CI environments.

## Tech Stack

| Tool | Purpose |
|------|---------|
| **Python 3.10+** | Core language |
| **Pytest** | Test framework and fixtures |
| **Requests** | HTTP client for API calls |
| **FastAPI** | Local mock REST API |
| **SQLite** | Data storage and validation |
| **Uvicorn** | ASGI server for the mock API |

## Project Structure

```
api_testing_project/
├── mock_api/
│   └── main.py              # FastAPI app: products, orders, users
├── tests/
│   ├── test_products.py     # Product endpoint tests
│   └── test_orders.py       # Order endpoint tests
├── utils/
│   └── api_client.py        # Reusable HTTP client
├── db/
│   ├── database.py          # Schema, seeding, query helpers
│   └── queries.sql          # Reference SQL queries
├── data/
│   └── test_data.json       # Seed data for products, users, orders
├── conftest.py              # Pytest fixtures (DB + API server)
├── requirements.txt
└── README.md
```

## Architecture

```
┌─────────────┐     HTTP      ┌──────────────┐
│  Pytest     │ ────────────► │  FastAPI     │
│  Tests      │               │  Mock API    │
└──────┬──────┘               └──────┬───────┘
       │                             │
       │ SQL validation              │ CRUD
       ▼                             ▼
┌─────────────────────────────────────────────┐
│              SQLite (ecommerce.db)           │
└─────────────────────────────────────────────┘
```

## Test Strategy

- API contract validation
- Database consistency checks
- Negative testing for invalid inputs
- End-to-end order flow validation

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/aahmedehab0/api-testing-project.git
cd api-testing-project
```

### 2. Create a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate   # Linux/macOS
# .venv\Scripts\activate    # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run tests

```bash
pytest -v
```
This project is fully deterministic and designed for CI pipelines with no external dependencies.

That's it — no manual server start required. The test session automatically:

1. Creates a fresh SQLite test database seeded from `data/test_data.json`
2. Starts the mock API on `http://127.0.0.1:8765`
3. Runs all test cases
4. Tears down the server and database file

## Example Test Output

```
tests/test_products.py::test_get_all_products PASSED
tests/test_products.py::test_get_single_product PASSED
tests/test_products.py::test_get_invalid_product_id PASSED
tests/test_products.py::test_product_schema_validation PASSED
tests/test_products.py::test_product_price_matches_db PASSED
tests/test_orders.py::test_create_order PASSED
tests/test_orders.py::test_created_order_exists_in_db PASSED
tests/test_orders.py::test_order_total_price_consistency PASSED
tests/test_orders.py::test_create_order_invalid_product_id PASSED
tests/test_orders.py::test_get_all_orders_status_code PASSED
tests/test_orders.py::test_order_response_schema PASSED

======================== 12 passed in 2.5s ========================
```

## API Endpoints

| Method | Endpoint | Description | Status Codes |
|--------|----------|-------------|--------------|
| GET | `/health` | Health check | 200 |
| GET | `/products` | List all products | 200 |
| GET | `/products/{id}` | Get product by ID | 200, 404 |
| GET | `/users` | List all users | 200 |
| GET | `/users/{id}` | Get user by ID | 200, 404 |
| GET | `/orders` | List all orders | 200 |
| GET | `/orders/{id}` | Get order by ID | 200, 404 |
| POST | `/orders` | Create a new order | 201, 404, 422 |

### Sample Requests

**GET /products/1**

```json
{
  "id": 1,
  "title": "Fjallraven - Foldsack No. 1 Backpack",
  "price": 109.95,
  "category": "men's clothing",
  "image": "https://fakestoreapi.com/img/81fPKd-2AYL._AC_SL1500_.jpg",
  "rating": {"rate": 3.9, "count": 120}
}
```

**POST /orders**

```json
{
  "user_id": 1,
  "products": [
    {"product_id": 1, "quantity": 2},
    {"product_id": 5, "quantity": 1}
  ]
}
```

## Test Coverage

| Test Case | File | What It Validates |
|-----------|------|-------------------|
| GET all products | `test_products.py` | Status 200, non-empty list, schema |
| Product count vs DB | `test_products.py` | API count matches `SELECT COUNT(*) FROM products` |
| GET single product | `test_products.py` | Status 200, fields match DB record |
| Invalid product ID | `test_products.py` | Status 404 for non-existent ID |
| Product schema | `test_products.py` | Required keys and data types |
| Price consistency | `test_products.py` | API price matches DB `products.price` |
| Create order | `test_orders.py` | Status 201, response schema, correct total |
| Order exists in DB | `test_orders.py` | `SELECT COUNT(*) FROM orders WHERE id = ?` |
| Order total consistency | `test_orders.py` | API total matches sum of line items |
| Invalid product in order | `test_orders.py` | Status 404 for bad product ID |
| GET all orders | `test_orders.py` | Status 200 |
| Order response schema | `test_orders.py` | Required keys and data types |

## SQL Validation Examples

Reference queries live in `db/queries.sql`. Tests use helpers from `db/database.py`:

```python
from db.database import order_exists, validate_order_total, get_product_price

# Verify order was persisted after POST
assert order_exists(order_id)

# Verify total matches line items
stored, computed = validate_order_total(order_id)
assert stored == computed

# Verify product price consistency
db_price = get_product_price(product_id)
assert api_price == db_price
```


## License

MIT — free to use for learning and portfolio purposes.
