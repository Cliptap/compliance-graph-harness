"""SQLite access and schema bootstrap for the target system."""
from __future__ import annotations

import os
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SCHEMA_PATH = BASE_DIR / "schema.sql"

PRODUCTS = [
    ("Plátano Extra Granel", "Frutas y verduras", "Dumbo", 725, 40, "500 g aprox", None),
    ("Bebida Cola Zero 1.5 L", "Bebidas", "Brisa", 1590, 50, "1.5 L", 1890),
    ("Palta Hass Chilena", "Frutas y verduras", "Campo", 3245, 25, "2 un aprox", 3790),
    ("Pan Ciabatta Granel", "Panadería", "Cocina", 1745, 30, "1 un", None),
    ("Limón Malla 1 kg", "Frutas y verduras", "Campo", 1590, 35, "1 kg", None),
    ("Papa Malla 2 kg", "Frutas y verduras", "Campo", 3450, 20, "2 kg", None),
    ("Leche Entera 1 L", "Lácteos", "Campo", 1290, 45, "1 L", 1490),
    ("Arroz Grado 1 1 kg", "Despensa", "Cocina", 1490, 60, "1 kg", None),
    ("Aceite Vegetal 1 L", "Despensa", "Cocina", 2790, 28, "1 L", None),
    ("Fideos Spaghetti 500 g", "Despensa", "Cocina", 990, 55, "500 g", None),
    ("Azúcar 1 kg", "Despensa", "Cocina", 1390, 40, "1 kg", None),
    ("Café Molido 250 g", "Despensa", "Andino", 3990, 22, "250 g", 4590),
    ("Huevos Color 12 un", "Lácteos", "Campo", 3490, 36, "12 un", None),
    ("Queso Gauda 250 g", "Lácteos", "Campo", 2890, 18, "250 g", None),
    ("Yogur Natural 1 L", "Lácteos", "Campo", 1890, 24, "1 L", None),
    ("Mantequilla 250 g", "Lácteos", "Campo", 2490, 16, "250 g", None),
    ("Pan Marraqueta 1 kg", "Panadería", "Cocina", 1990, 32, "1 kg", None),
    ("Hallulla 1 kg", "Panadería", "Cocina", 1790, 30, "1 kg", None),
    ("Bebida Naranja 1.5 L", "Bebidas", "Brisa", 1490, 48, "1.5 L", None),
    ("Agua Mineral 1.5 L", "Bebidas", "Fresco", 890, 70, "1.5 L", None),
    ("Cerveza Lager 6 un", "Bebidas", "Andino", 5490, 18, "6 un", 5990),
    ("Detergente 3 L", "Limpieza", "Casa", 6990, 14, "3 L", None),
    ("Papel Higiénico 12 un", "Limpieza", "Casa", 5990, 20, "12 un", 6990),
    ("Lavaloza 750 ml", "Limpieza", "Casa", 2290, 26, "750 ml", None),
    ("Limpiador Multiuso 1 L", "Limpieza", "Casa", 1990, 22, "1 L", None),
    ("Shampoo 750 ml", "Cuidado personal", "Brisa", 3490, 15, "750 ml", None),
    ("Pasta Dental 90 g", "Cuidado personal", "Brisa", 1890, 30, "90 g", None),
    ("Desodorante 150 ml", "Cuidado personal", "Brisa", 2990, 18, "150 ml", None),
    ("Carne Molida 1 kg", "Carnes", "Fresco", 6990, 12, "1 kg", None),
    ("Pechuga de Pollo 1 kg", "Carnes", "Fresco", 5490, 16, "1 kg", None),
    ("Salchichas 500 g", "Carnes", "Fresco", 2490, 24, "500 g", None),
    ("Jamón 200 g", "Carnes", "Fresco", 1990, 20, "200 g", None),
]


def default_db_path() -> Path:
    return Path(os.environ.get("SHOP_DB", BASE_DIR / "data" / "shop.db"))


def connect(db_path: Path | str) -> sqlite3.Connection:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(db_path: Path | str) -> None:
    with connect(db_path) as conn:
        conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        columns = {row["name"] for row in conn.execute("PRAGMA table_info(products)")}
        if "unit" not in columns:
            conn.execute("ALTER TABLE products ADD COLUMN unit TEXT NOT NULL DEFAULT 'un'")
        if "old_price_clp" not in columns:
            conn.execute("ALTER TABLE products ADD COLUMN old_price_clp INTEGER")
        seed_products(conn)


def seed_products(conn: sqlite3.Connection) -> None:
    existing = {row["name"] for row in conn.execute("SELECT name FROM products")}
    for product in PRODUCTS:
        if product[0] in existing:
            continue
        conn.execute(
            "INSERT INTO products (name, category, brand, price_clp, stock, unit, old_price_clp) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            product,
        )


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def add_business_days(start: datetime, days: int) -> datetime:
    current = start
    added = 0
    while added < days:
        current += timedelta(days=1)
        if current.weekday() < 5:
            added += 1
    return current
