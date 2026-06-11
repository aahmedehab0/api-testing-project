import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH = PROJECT_ROOT / "data" / "ecommerce.db"
TEST_DATA_PATH = PROJECT_ROOT / "data" / "test_data.json"


def get_connection(db_path: Path | str | None = None) -> sqlite3.Connection:
    path = Path(db_path) if db_path else DEFAULT_DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def _create_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            price REAL NOT NULL,
            category TEXT NOT NULL,
            image TEXT NOT NULL,
            rating_rate REAL NOT NULL,
            rating_count INTEGER NOT NULL
        );

        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            email TEXT NOT NULL,
            username TEXT NOT NULL,
            firstname TEXT NOT NULL,
            lastname TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            total REAL NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        );

        CREATE TABLE IF NOT EXISTS order_items (
            order_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            unit_price REAL NOT NULL,
            PRIMARY KEY (order_id, product_id),
            FOREIGN KEY (order_id) REFERENCES orders (id),
            FOREIGN KEY (product_id) REFERENCES products (id)
        );
        """
    )


def _load_test_data() -> dict:
    with open(TEST_DATA_PATH, encoding="utf-8") as f:
        return json.load(f)


def _seed_products(conn: sqlite3.Connection, products: list[dict]) -> None:
    for product in products:
        conn.execute(
            """
            INSERT OR IGNORE INTO products
            (id, title, price, category, image, rating_rate, rating_count)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                product["id"],
                product["title"],
                product["price"],
                product["category"],
                product["image"],
                product["rating"]["rate"],
                product["rating"]["count"],
            ),
        )


def _seed_users(conn: sqlite3.Connection, users: list[dict]) -> None:
    for user in users:
        conn.execute(
            """
            INSERT OR IGNORE INTO users (id, email, username, firstname, lastname)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                user["id"],
                user["email"],
                user["username"],
                user["firstname"],
                user["lastname"],
            ),
        )


def _compute_order_total(conn: sqlite3.Connection, products: list[dict]) -> float:
    total = 0.0
    for item in products:
        row = conn.execute(
            "SELECT price FROM products WHERE id = ?", (item["product_id"],)
        ).fetchone()
        if row is None:
            raise ValueError(f"Product {item['product_id']} not found")
        total += row["price"] * item["quantity"]
    return round(total, 2)


def _seed_orders(conn: sqlite3.Connection, orders: list[dict]) -> None:
    for order in orders:
        total = _compute_order_total(conn, order["products"])
        date = datetime.now(timezone.utc).isoformat()
        cursor = conn.execute(
            "INSERT INTO orders (user_id, date, total) VALUES (?, ?, ?)",
            (order["user_id"], date, total),
        )
        order_id = cursor.lastrowid
        for item in order["products"]:
            price_row = conn.execute(
                "SELECT price FROM products WHERE id = ?", (item["product_id"],)
            ).fetchone()
            conn.execute(
                """
                INSERT INTO order_items (order_id, product_id, quantity, unit_price)
                VALUES (?, ?, ?, ?)
                """,
                (order_id, item["product_id"], item["quantity"], price_row["price"]),
            )


def init_db(db_path: Path | str | None = None, force_seed: bool = False) -> Path:
    path = Path(db_path) if db_path else DEFAULT_DB_PATH
    if force_seed and path.exists():
        path.unlink()

    conn = get_connection(path)
    try:
        _create_tables(conn)
        product_count = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
        if product_count == 0 or force_seed:
            if force_seed:
                conn.executescript(
                    """
                    DELETE FROM order_items;
                    DELETE FROM orders;
                    DELETE FROM products;
                    DELETE FROM users;
                    """
                )
            data = _load_test_data()
            _seed_products(conn, data["products"])
            _seed_users(conn, data["users"])
            if product_count == 0 or force_seed:
                _seed_orders(conn, data["orders"])
        conn.commit()
    finally:
        conn.close()
    return path


def get_all_orders(db_path: Path | str | None = None) -> list[sqlite3.Row]:
    conn = get_connection(db_path)
    try:
        return conn.execute("SELECT * FROM orders").fetchall()
    finally:
        conn.close()


def get_order_by_id(order_id: int, db_path: Path | str | None = None) -> sqlite3.Row | None:
    conn = get_connection(db_path)
    try:
        return conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
    finally:
        conn.close()


def order_exists(order_id: int, db_path: Path | str | None = None) -> bool:
    conn = get_connection(db_path)
    try:
        count = conn.execute(
            "SELECT COUNT(*) FROM orders WHERE id = ?", (order_id,)
        ).fetchone()[0]
        return count > 0
    finally:
        conn.close()


def get_product_price(product_id: int, db_path: Path | str | None = None) -> float | None:
    conn = get_connection(db_path)
    try:
        row = conn.execute(
            "SELECT price FROM products WHERE id = ?", (product_id,)
        ).fetchone()
        return row["price"] if row else None
    finally:
        conn.close()


def get_product_by_id(product_id: int, db_path: Path | str | None = None) -> sqlite3.Row | None:
    conn = get_connection(db_path)
    try:
        return conn.execute(
            "SELECT * FROM products WHERE id = ?", (product_id,)
        ).fetchone()
    finally:
        conn.close()


def get_product_count(db_path: Path | str | None = None) -> int:
    conn = get_connection(db_path)
    try:
        return conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
    finally:
        conn.close()


def validate_order_total(order_id: int, db_path: Path | str | None = None) -> tuple[float, float]:
    conn = get_connection(db_path)
    try:
        order = conn.execute(
            "SELECT total FROM orders WHERE id = ?", (order_id,)
        ).fetchone()
        computed = conn.execute(
            """
            SELECT SUM(unit_price * quantity) AS computed_total
            FROM order_items
            WHERE order_id = ?
            """,
            (order_id,),
        ).fetchone()
        stored_total = order["total"] if order else 0.0
        computed_total = computed["computed_total"] or 0.0
        return round(stored_total, 2), round(computed_total, 2)
    finally:
        conn.close()
