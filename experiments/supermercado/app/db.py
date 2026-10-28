"""SQLite access and schema bootstrap for the target system."""
from __future__ import annotations

import os
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SCHEMA_PATH = BASE_DIR / "schema.sql"

PRODUCTS = [
    ("Plátano Extra Granel", "Frutas y verduras", "Propias", 725, 40),
    ("Palta Hass Chilena", "Frutas y verduras", "Propias", 3245, 25),
    ("Pan Ciabatta Granel", "Panadería", "Artesanal", 1745, 30),
    ("Bebida Cola Zero 1.5 L", "Bebidas", "Cola", 1590, 50),
    ("Limón Malla 1 kg", "Frutas y verduras", "Propias", 1590, 35),
    ("Papa Malla 2 kg", "Frutas y verduras", "Propias", 3450, 20),
    ("Leche Entera 1 L", "Lácteos", "Campo", 1290, 45),
    ("Arroz Grado 1 1 kg", "Despensa", "Cocina", 1490, 60),
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
        seed_products(conn)


def seed_products(conn: sqlite3.Connection) -> None:
    count = conn.execute("SELECT COUNT(*) AS n FROM products").fetchone()["n"]
    if count:
        return
    conn.executemany(
        "INSERT INTO products (name, category, brand, price_clp, stock) VALUES (?, ?, ?, ?, ?)",
        PRODUCTS,
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
