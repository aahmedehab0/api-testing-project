import pytest

from db.database import get_product_by_id, get_product_count, get_product_price

PRODUCT_REQUIRED_KEYS = {"id", "title", "price", "category", "image", "rating"}
RATING_REQUIRED_KEYS = {"rate", "count"}


def assert_product_schema(product: dict) -> None:
    assert PRODUCT_REQUIRED_KEYS.issubset(product.keys())
    assert isinstance(product["id"], int)
    assert isinstance(product["title"], str)
    assert isinstance(product["price"], (int, float))
    assert isinstance(product["category"], str)
    assert isinstance(product["image"], str)
    assert isinstance(product["rating"], dict)
    assert RATING_REQUIRED_KEYS.issubset(product["rating"].keys())
    assert isinstance(product["rating"]["rate"], (int, float))
    assert isinstance(product["rating"]["count"], int)


def test_get_all_products(api_client, test_db):
    response = api_client.get_products()

    assert response.status_code == 200
    products = response.json()
    assert isinstance(products, list)
    assert len(products) > 0

    for product in products:
        assert_product_schema(product)


def test_get_all_products_count_matches_db(api_client, test_db):
    response = api_client.get_products()

    assert response.status_code == 200
    assert len(response.json()) == get_product_count(test_db)


def test_get_single_product(api_client, test_db):
    product_id = 1
    response = api_client.get_product(product_id)

    assert response.status_code == 200
    product = response.json()
    assert_product_schema(product)

    db_product = get_product_by_id(product_id, test_db)
    assert db_product is not None
    assert product["id"] == db_product["id"]
    assert product["title"] == db_product["title"]
    assert product["price"] == db_product["price"]


def test_get_invalid_product_id(api_client):
    response = api_client.get_product(99999)

    assert response.status_code == 404
    assert response.json()["detail"] == "Product not found"


def test_product_schema_validation(api_client):
    response = api_client.get_product(2)

    assert response.status_code == 200
    assert_product_schema(response.json())


def test_product_price_matches_db(api_client, test_db):
    for product_id in [1, 3, 5]:
        response = api_client.get_product(product_id)

        assert response.status_code == 200
        api_price = response.json()["price"]
        db_price = get_product_price(product_id, test_db)
        assert api_price == db_price
