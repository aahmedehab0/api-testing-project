import os
import sqlite3
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = Path(os.environ.get("ECOMMERCE_DB_PATH", PROJECT_ROOT / "data" / "ecommerce.db"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    from db.database import init_db

    init_db(DB_PATH)
    yield


app = FastAPI(title="E-Commerce Mock API", version="1.0.0", lifespan=lifespan)


class Rating(BaseModel):
    rate: float
    count: int


class Product(BaseModel):
    id: int
    title: str
    price: float
    category: str
    image: str
    rating: Rating


class User(BaseModel):
    id: int
    email: str
    username: str
    firstname: str
    lastname: str


class OrderItemRequest(BaseModel):
    product_id: int = Field(..., gt=0)
    quantity: int = Field(..., gt=0)


class OrderCreateRequest(BaseModel):
    user_id: int = Field(..., gt=0)
    products: list[OrderItemRequest] = Field(..., min_length=1)


class OrderItemResponse(BaseModel):
    product_id: int
    quantity: int
    unit_price: float


class Order(BaseModel):
    id: int
    user_id: int
    date: str
    products: list[OrderItemResponse]
    total: float


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _row_to_product(row: sqlite3.Row) -> dict:
    return {
        "id": row["id"],
        "title": row["title"],
        "price": row["price"],
        "category": row["category"],
        "image": row["image"],
        "rating": {"rate": row["rating_rate"], "count": row["rating_count"]},
    }


def _row_to_user(row: sqlite3.Row) -> dict:
    return {
        "id": row["id"],
        "email": row["email"],
        "username": row["username"],
        "firstname": row["firstname"],
        "lastname": row["lastname"],
    }


def _fetch_order(conn: sqlite3.Connection, order_id: int) -> dict | None:
    order_row = conn.execute(
        "SELECT * FROM orders WHERE id = ?", (order_id,)
    ).fetchone()
    if order_row is None:
        return None

    items = conn.execute(
        """
        SELECT product_id, quantity, unit_price
        FROM order_items
        WHERE order_id = ?
        """,
        (order_id,),
    ).fetchall()

    return {
        "id": order_row["id"],
        "user_id": order_row["user_id"],
        "date": order_row["date"],
        "total": order_row["total"],
        "products": [
            {
                "product_id": item["product_id"],
                "quantity": item["quantity"],
                "unit_price": item["unit_price"],
            }
            for item in items
        ],
    }


@app.get("/health")
def health_check() -> dict:
    return {"status": "ok"}


@app.get("/products", response_model=list[Product])
def get_products() -> list[dict]:
    conn = get_connection()
    try:
        rows = conn.execute("SELECT * FROM products ORDER BY id").fetchall()
        return [_row_to_product(row) for row in rows]
    finally:
        conn.close()


@app.get("/products/{product_id}", response_model=Product)
def get_product(product_id: int) -> dict:
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM products WHERE id = ?", (product_id,)
        ).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Product not found")
        return _row_to_product(row)
    finally:
        conn.close()


@app.get("/users", response_model=list[User])
def get_users() -> list[dict]:
    conn = get_connection()
    try:
        rows = conn.execute("SELECT * FROM users ORDER BY id").fetchall()
        return [_row_to_user(row) for row in rows]
    finally:
        conn.close()


@app.get("/users/{user_id}", response_model=User)
def get_user(user_id: int) -> dict:
    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="User not found")
        return _row_to_user(row)
    finally:
        conn.close()


@app.get("/orders", response_model=list[Order])
def get_orders() -> list[dict]:
    conn = get_connection()
    try:
        order_ids = conn.execute(
            "SELECT id FROM orders ORDER BY id"
        ).fetchall()
        return [
            order
            for row in order_ids
            if (order := _fetch_order(conn, row["id"])) is not None
        ]
    finally:
        conn.close()


@app.get("/orders/{order_id}", response_model=Order)
def get_order(order_id: int) -> dict:
    conn = get_connection()
    try:
        order = _fetch_order(conn, order_id)
        if order is None:
            raise HTTPException(status_code=404, detail="Order not found")
        return order
    finally:
        conn.close()


@app.post("/orders", response_model=Order, status_code=201)
def create_order(payload: OrderCreateRequest) -> dict:
    conn = get_connection()
    try:
        user = conn.execute(
            "SELECT id FROM users WHERE id = ?", (payload.user_id,)
        ).fetchone()
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")

        line_items: list[dict] = []
        total = 0.0

        for item in payload.products:
            product = conn.execute(
                "SELECT id, price FROM products WHERE id = ?",
                (item.product_id,),
            ).fetchone()
            if product is None:
                raise HTTPException(
                    status_code=404,
                    detail=f"Product {item.product_id} not found",
                )
            line_total = product["price"] * item.quantity
            total += line_total
            line_items.append(
                {
                    "product_id": item.product_id,
                    "quantity": item.quantity,
                    "unit_price": product["price"],
                }
            )

        total = round(total, 2)
        date = datetime.now(timezone.utc).isoformat()
        cursor = conn.execute(
            "INSERT INTO orders (user_id, date, total) VALUES (?, ?, ?)",
            (payload.user_id, date, total),
        )
        order_id = cursor.lastrowid

        for item in line_items:
            conn.execute(
                """
                INSERT INTO order_items (order_id, product_id, quantity, unit_price)
                VALUES (?, ?, ?, ?)
                """,
                (
                    order_id,
                    item["product_id"],
                    item["quantity"],
                    item["unit_price"],
                ),
            )

        conn.commit()
        order = _fetch_order(conn, order_id)
        if order is None:
            raise HTTPException(status_code=500, detail="Failed to create order")
        return order
    finally:
        conn.close()
