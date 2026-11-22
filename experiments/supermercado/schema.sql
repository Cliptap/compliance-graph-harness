PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS customers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rut TEXT UNIQUE,
    email TEXT NOT NULL UNIQUE,
    phone TEXT,
    full_name TEXT,
    password_hash TEXT NOT NULL,
    blocked INTEGER NOT NULL DEFAULT 0,
    marketing_opt_in INTEGER NOT NULL DEFAULT 0,
    retention_days INTEGER NOT NULL DEFAULT 730,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS addresses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL REFERENCES customers(id),
    label TEXT,
    line1 TEXT NOT NULL,
    commune TEXT NOT NULL,
    city TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    brand TEXT,
    price_clp INTEGER NOT NULL,
    stock INTEGER NOT NULL DEFAULT 0,
    unit TEXT NOT NULL DEFAULT 'un',
    old_price_clp INTEGER,
    description TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL REFERENCES customers(id),
    status TEXT NOT NULL DEFAULT 'pending',
    delivery_mode TEXT NOT NULL CHECK (delivery_mode IN ('delivery', 'pickup')),
    address_id INTEGER REFERENCES addresses(id),
    pickup_store TEXT,
    subtotal_clp INTEGER NOT NULL,
    points_earned INTEGER NOT NULL DEFAULT 0,
    payment_token TEXT,
    retention_days INTEGER NOT NULL DEFAULT 2190,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS order_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL REFERENCES orders(id),
    product_id INTEGER NOT NULL REFERENCES products(id),
    quantity INTEGER NOT NULL,
    unit_price_clp INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS points_ledger (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL REFERENCES customers(id),
    order_id INTEGER REFERENCES orders(id),
    points INTEGER NOT NULL,
    reason TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS consents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL REFERENCES customers(id),
    purpose TEXT NOT NULL,
    policy_version TEXT NOT NULL,
    granted_at TEXT NOT NULL,
    withdrawn_at TEXT
);

CREATE TABLE IF NOT EXISTS rights_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL REFERENCES customers(id),
    right_type TEXT NOT NULL CHECK (right_type IN ('access', 'rectification', 'erasure', 'opposition', 'portability', 'block')),
    status TEXT NOT NULL DEFAULT 'received',
    requested_at TEXT NOT NULL,
    due_at TEXT NOT NULL,
    responded_at TEXT,
    notes TEXT
);

CREATE TABLE IF NOT EXISTS cookie_consents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER REFERENCES customers(id),
    necessary INTEGER NOT NULL DEFAULT 1,
    functionality INTEGER NOT NULL DEFAULT 0,
    performance INTEGER NOT NULL DEFAULT 0,
    targeting INTEGER NOT NULL DEFAULT 0,
    recorded_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS incidents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    occurred_at TEXT NOT NULL,
    nature TEXT NOT NULL,
    data_categories TEXT NOT NULL,
    affected_subjects INTEGER,
    measures TEXT,
    notified_at TEXT
);

CREATE TABLE IF NOT EXISTS third_parties (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    purpose TEXT NOT NULL,
    region TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS marketing_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL REFERENCES customers(id),
    subject TEXT NOT NULL,
    sent_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_orders_customer ON orders(customer_id);
CREATE INDEX IF NOT EXISTS idx_rights_customer ON rights_requests(customer_id);
CREATE INDEX IF NOT EXISTS idx_consents_customer ON consents(customer_id);
