-- Schema creation script for the billing system.
-- Execute against the PostgreSQL database referenced by DATABASE_URL.

CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    product_code VARCHAR(64) NOT NULL UNIQUE,
    available_stocks INTEGER NOT NULL DEFAULT 0,
    unit_price NUMERIC(12, 2) NOT NULL,
    tax_percentage NUMERIC(5, 2) NOT NULL
);

CREATE TABLE IF NOT EXISTS customers (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS purchases (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers (id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    subtotal NUMERIC(12, 2) NOT NULL,
    tax_total NUMERIC(12, 2) NOT NULL,
    grand_total NUMERIC(12, 2) NOT NULL,
    rounded_total INTEGER NOT NULL,
    paid_amount NUMERIC(12, 2) NOT NULL
);

CREATE TABLE IF NOT EXISTS purchase_items (
    id SERIAL PRIMARY KEY,
    purchase_id INTEGER NOT NULL REFERENCES purchases (id) ON DELETE CASCADE,
    product_id INTEGER NOT NULL REFERENCES products (id) ON DELETE RESTRICT,
    product_code VARCHAR(64) NOT NULL,
    product_name VARCHAR(255) NOT NULL,
    quantity INTEGER NOT NULL,
    unit_price NUMERIC(12, 2) NOT NULL,
    tax_percentage NUMERIC(5, 2) NOT NULL,
    line_subtotal NUMERIC(12, 2) NOT NULL,
    line_tax NUMERIC(12, 2) NOT NULL,
    line_total NUMERIC(12, 2) NOT NULL
);

CREATE TABLE IF NOT EXISTS denomination_stocks (
    id SERIAL PRIMARY KEY,
    value INTEGER NOT NULL UNIQUE,
    available_count INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS payment_breakdowns (
    id SERIAL PRIMARY KEY,
    purchase_id INTEGER NOT NULL UNIQUE REFERENCES purchases (id) ON DELETE CASCADE,
    details_json JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS change_breakdowns (
    id SERIAL PRIMARY KEY,
    purchase_id INTEGER NOT NULL UNIQUE REFERENCES purchases (id) ON DELETE CASCADE,
    details_json JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS ix_products_product_code ON products (product_code);

CREATE INDEX IF NOT EXISTS ix_customers_email ON customers (email);

CREATE INDEX IF NOT EXISTS ix_purchases_customer_created
    ON purchases (customer_id, created_at);

CREATE INDEX IF NOT EXISTS ix_purchase_items_purchase_product
    ON purchase_items (purchase_id, product_id);

CREATE INDEX IF NOT EXISTS ix_denomination_value_desc
    ON denomination_stocks (value DESC);
