-- Risky Migration Example: Multiple locking anti-patterns

-- 1. ACCESS EXCLUSIVE lock: CREATE INDEX without CONCURRENTLY
CREATE INDEX idx_users_email ON users (email);

-- 2. ACCESS EXCLUSIVE lock: ADD COLUMN with NOT NULL and non-constant default
ALTER TABLE orders ADD COLUMN updated_at TIMESTAMP NOT NULL DEFAULT now();

-- 3. Foreign key added without index on referencing column
ALTER TABLE order_items ADD CONSTRAINT fk_order_items_product FOREIGN KEY (product_id) REFERENCES products (id);

-- 4. Dropping a column on a live table without deprecation
ALTER TABLE accounts DROP COLUMN legacy_auth_hash;

-- 5. Unbounded row lock
SELECT * FROM payments WHERE status = 'pending' FOR UPDATE;
