-- ============================================================
--  ORM vs SQL Benchmark — Schema + Seed
--  Executado automaticamente pelo PostgreSQL na primeira inicialização
-- ============================================================

CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- ── Tabelas ────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS categories (
    id   SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS users (
    id         SERIAL PRIMARY KEY,
    name       VARCHAR(150) NOT NULL,
    email      VARCHAR(255) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS products (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(200) NOT NULL,
    price       NUMERIC(10, 2) NOT NULL,
    stock       INTEGER        NOT NULL DEFAULT 0,
    category_id INTEGER REFERENCES categories(id) ON DELETE SET NULL,
    created_at  TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS orders (
    id         SERIAL PRIMARY KEY,
    user_id    INTEGER        NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    total      NUMERIC(12, 2) NOT NULL DEFAULT 0,
    status     VARCHAR(50)    NOT NULL DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS order_items (
    id         SERIAL PRIMARY KEY,
    order_id   INTEGER        NOT NULL REFERENCES orders(id)   ON DELETE CASCADE,
    product_id INTEGER        NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    quantity   INTEGER        NOT NULL DEFAULT 1,
    unit_price NUMERIC(10, 2) NOT NULL
);

-- ── Índices ────────────────────────────────────────────────────────────────────

CREATE INDEX IF NOT EXISTS idx_orders_user_id         ON orders(user_id);
CREATE INDEX IF NOT EXISTS idx_order_items_order_id   ON order_items(order_id);
CREATE INDEX IF NOT EXISTS idx_order_items_product_id ON order_items(product_id);
CREATE INDEX IF NOT EXISTS idx_products_category_id   ON products(category_id);
CREATE INDEX IF NOT EXISTS idx_users_email            ON users(email);

-- ── Seed ───────────────────────────────────────────────────────────────────────

INSERT INTO categories (name) VALUES
    ('Eletrônicos'), ('Vestuário'), ('Livros'), ('Alimentos'), ('Esportes')
ON CONFLICT DO NOTHING;

-- 1 000 usuários
INSERT INTO users (name, email)
SELECT 'Usuário ' || i, 'user' || i || '@benchmark.com'
FROM generate_series(1, 1000) i
ON CONFLICT DO NOTHING;

-- 500 produtos
INSERT INTO products (name, price, stock, category_id)
SELECT
    'Produto ' || i,
    round((random() * 990 + 10)::NUMERIC, 2),
    (random() * 500)::INTEGER,
    (floor(random() * 5) + 1)::INTEGER
FROM generate_series(1, 500) i;

-- 2 000 pedidos
INSERT INTO orders (user_id, total, status)
SELECT
    (floor(random() * 1000) + 1)::INTEGER,
    round((random() * 5000 + 50)::NUMERIC, 2),
    (ARRAY['pending','confirmed','shipped','delivered','cancelled'])[floor(random()*5+1)]
FROM generate_series(1, 2000) i;

-- 6 000 itens de pedido (~3 por pedido)
INSERT INTO order_items (order_id, product_id, quantity, unit_price)
SELECT
    (floor(random() * 2000) + 1)::INTEGER,
    (floor(random() * 500)  + 1)::INTEGER,
    (floor(random() * 5)    + 1)::INTEGER,
    round((random() * 990 + 10)::NUMERIC, 2)
FROM generate_series(1, 6000) i;

-- ── Usuário de monitoramento para o postgres_exporter ─────────────────────────
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'monitor') THEN
        CREATE USER monitor WITH PASSWORD 'monitor_pass';
    END IF;
END $$;

GRANT pg_monitor TO monitor;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO monitor;
