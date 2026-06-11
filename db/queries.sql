-- Reference SQL queries used by the test automation suite.
-- These are executed via helpers in db/database.py.

-- Get all orders
-- SELECT * FROM orders;

-- Get a single order by ID
-- SELECT * FROM orders WHERE id = ?;

-- Get line items for an order
-- SELECT * FROM order_items WHERE order_id = ?;

-- Get product price for consistency checks
-- SELECT price FROM products WHERE id = ?;

-- Check if an order exists
-- SELECT COUNT(*) FROM orders WHERE id = ?;

-- Validate order total against line items
-- SELECT SUM(unit_price * quantity) AS computed_total
-- FROM order_items
-- WHERE order_id = ?;

-- Count all products
-- SELECT COUNT(*) FROM products;

-- Get product by ID
-- SELECT * FROM products WHERE id = ?;
