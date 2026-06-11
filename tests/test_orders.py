import pytest

from db.database import order_exists, validate_order_total

ORDER_REQUIRED_KEYS = {"id", "user_id", "date", "products", "total"}
ORDER_ITEM_REQUIRED_KEYS = {"product_id", "quantity", "unit_price"}


def assert_order_schema(order: dict) -> None:
    assert ORDER_REQUIRED_KEYS.issubset(order.keys())
    assert isinstance(order["id"], int)
    assert isinstance(order["user_id"], int)
    assert isinstance(order["date"], str)
    assert isinstance(order["products"], list)
    assert isinstance(order["total"], (int, float))
    assert len(order["products"]) > 0

    for item in order["products"]:
        assert ORDER_ITEM_REQUIRED_KEYS.issubset(item.keys())
        assert isinstance(item["product_id"], int)
        assert isinstance(item["quantity"], int)
        assert isinstance(item["unit_price"], (int, float))


def test_create_order(api_client):
    payload = {
        "user_id": 1,
        "products": [
            {"product_id": 1, "quantity": 2},
            {"product_id": 5, "quantity": 1},
        ],
    }
    response = api_client.create_order(payload)

    assert response.status_code == 201
    order = response.json()
    assert_order_schema(order)
    assert order["user_id"] == payload["user_id"]
    assert order["total"] == pytest.approx(283.9, rel=1e-2)


def test_created_order_exists_in_db(api_client, test_db):
    payload = {
        "user_id": 2,
        "products": [{"product_id": 4, "quantity": 3}],
    }
    response = api_client.create_order(payload)

    assert response.status_code == 201
    order_id = response.json()["id"]
    assert order_exists(order_id, test_db)


def test_order_total_price_consistency(api_client, test_db):
    payload = {
        "user_id": 3,
        "products": [
            {"product_id": 2, "quantity": 2},
            {"product_id": 3, "quantity": 1},
        ],
    }
    response = api_client.create_order(payload)

    assert response.status_code == 201
    order = response.json()
    stored_total, computed_total = validate_order_total(order["id"], test_db)
    assert order["total"] == pytest.approx(stored_total, rel=1e-2)
    assert stored_total == pytest.approx(computed_total, rel=1e-2)


def test_create_order_invalid_product_id(api_client):
    payload = {
        "user_id": 1,
        "products": [{"product_id": 99999, "quantity": 1}],
    }
    response = api_client.create_order(payload)

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_get_all_orders_status_code(api_client):
    response = api_client.get_orders()

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_order_response_schema(api_client):
    payload = {
        "user_id": 1,
        "products": [{"product_id": 1, "quantity": 1}],
    }
    response = api_client.create_order(payload)

    assert response.status_code == 201
    assert_order_schema(response.json())
