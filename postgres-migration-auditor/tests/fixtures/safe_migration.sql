-- Safe Zero-Downtime Migration

-- 1. Index built concurrently outside transaction block
CREATE INDEX CONCURRENTLY idx_users_email ON users (email);

-- 2. Safe Foreign key with matching concurrent index
CREATE INDEX CONCURRENTLY idx_order_items_product_id ON order_items (product_id);
ALTER TABLE order_items ADD CONSTRAINT fk_order_items_product FOREIGN KEY (product_id) REFERENCES products (id);

-- 3. Row lock with LIMIT and SKIP LOCKED
SELECT * FROM payments WHERE status = 'pending' FOR UPDATE LIMIT 50 SKIP LOCKED;
