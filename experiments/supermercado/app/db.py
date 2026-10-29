"""SQLite access, schema bootstrap and the Dumbo catalog seed."""
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

GENERATED_CATALOG = {
    "Congelados": ["Arvejas congeladas", "Papas fritas congeladas", "Helado de vainilla", "Pizza congelada",
                   "Hamburguesas de vacuno", "Pollo congelado", "Frambuesas congeladas", "Empanadas de pino",
                   "Verduras para saltear", "Postre de chocolate"],
    "Snacks": ["Papas fritas", "Galletas de agua", "Ramitas", "Frutos secos", "Chocolate", "Cabritas",
               "Barra de cereal", "Maní salado", "Nachos", "Galletas de avena"],
    "Infantil": ["Papilla de frutas", "Leche de crecimiento", "Pañales talla M", "Toallitas húmedas",
                 "Cereal infantil", "Jugo infantil", "Shampoo infantil", "Crema para bebé", "Cucharas de bebé",
                 "Mamadera"],
    "Mascotas": ["Alimento perro adulto", "Alimento gato adulto", "Arena sanitaria", "Snacks perro",
                 "Shampoo mascota", "Juguete mordedor", "Alimento cachorro", "Arena aglomerante",
                 "Premios gato", "Cepillo mascota"],
    "Hogar": ["Bolsas de basura", "Servilletas", "Papel aluminio", "Film plástico", "Escoba", "Paño multiuso",
              "Ambientador", "Velas", "Fósforos", "Guantes de limpieza"],
    "Belleza": ["Crema facial", "Protector solar", "Labial", "Esmalte", "Agua micelar", "Serum facial",
                "Máscara de pestañas", "Jabón facial", "Loción corporal", "Algodón"],
    "Desayuno": ["Avena", "Mermelada", "Manjar", "Cereal de maíz", "Té", "Café instantáneo", "Azúcar rubia",
                 "Pan de molde", "Miel", "Chocolate en polvo"],
    "Comidas preparadas": ["Lasagna", "Empanada de queso", "Ensalada César", "Sushi", "Pizza margarita",
                           "Pastel de choclo", "Sopa", "Arroz preparado", "Pollo asado", "Tarta de verduras"],
    "Bebés": ["Pañales talla P", "Toallitas sin perfume", "Crema antipañalitis", "Biberón", "Leche fórmula",
              "Jabón líquido bebé", "Colonia bebé", "Cepillo dental bebé", "Babero", "Chupete"],
    "Licores": ["Vino tinto", "Vino blanco", "Cerveza artesanal", "Pisco", "Ron", "Vodka", "Espumante", "Gin",
                "Whisky", "Sidra"],
    "Conservas": ["Atún en agua", "Tomate pelado", "Choclo en grano", "Aceitunas", "Palmitos", "Duraznos",
                  "Mermelada de frutilla", "Salsa de tomate", "Frijoles", "Lentejas"],
    "Salsas": ["Mayonesa", "Ketchup", "Mostaza", "Salsa de soya", "Salsa BBQ", "Salsa picante", "Vinagre",
               "Aliño completo", "Salsa de ajo", "Chimichurri"],
}

BRANDS = ["Dumbo", "Campo", "Cocina", "Brisa", "Andino", "Casa", "Fresco", "Sol", "Raíz", "Nube"]
UNITS = ["1 un", "500 g", "1 kg", "1 L", "pack 6", "250 g", "750 ml", "12 un"]
CATEGORY_UNITS = {
    "Frutas y verduras": ["1 kg", "500 g", "1 un", "2 un"],
    "Lácteos": ["1 L", "250 g", "12 un", "1 un"],
    "Panadería": ["1 kg", "500 g", "1 un"],
    "Bebidas": ["1.5 L", "1 L", "6 un", "500 ml"],
    "Despensa": ["1 kg", "500 g", "1 L", "250 g"],
    "Carnes": ["1 kg", "500 g", "200 g"],
    "Limpieza": ["1 L", "750 ml", "3 L", "12 un"],
    "Cuidado personal": ["750 ml", "90 g", "150 ml", "1 un"],
    "Congelados": ["500 g", "1 kg", "1 un", "6 un"],
    "Snacks": ["150 g", "250 g", "1 un", "pack 6"],
    "Infantil": ["1 un", "12 un", "250 g", "1 L"],
    "Mascotas": ["3 kg", "10 kg", "1 un", "500 g"],
    "Hogar": ["1 un", "12 un", "30 un", "50 ml"],
    "Belleza": ["200 ml", "400 ml", "1 un", "50 g"],
    "Desayuno": ["500 g", "1 kg", "250 g", "1 L"],
    "Comidas preparadas": ["1 un", "350 g", "500 g", "1 kg"],
    "Bebés": ["1 un", "12 un", "250 ml", "1 L"],
    "Licores": ["750 ml", "1 L", "6 un", "500 ml"],
    "Conservas": ["200 g", "300 g", "1 un", "400 g"],
    "Salsas": ["250 ml", "1 L", "500 ml", "1 un"],
}
BLURBS = {
    "Frutas y verduras": "Fresco y seleccionado para tu semana.",
    "Lácteos": "Fuente de calcio para tu día a día.",
    "Panadería": "Recién horneado, listo para tu mesa.",
    "Bebidas": "Para acompañar tus comidas y tu día.",
    "Despensa": "Un básico que no puede faltar en tu cocina.",
    "Carnes": "Corte seleccionado y envasado con cuidado.",
    "Limpieza": "Práctico para mantener tu hogar impecable.",
    "Cuidado personal": "Tu rutina diaria, simple y efectiva.",
    "Congelados": "Listo para guardar y preparar cuando quieras.",
    "Snacks": "El gusto de siempre, en porciones prácticas.",
    "Infantil": "Pensado para acompañar el crecimiento.",
    "Mascotas": "Cuidado diario para tu compañero.",
    "Hogar": "Un aliado para la vida diaria en casa.",
    "Belleza": "Para tu rutina de cuidado personal.",
    "Desayuno": "El mejor comienzo para tu mañana.",
    "Comidas preparadas": "Rápido, rico y listo para servir.",
    "Bebés": "Suave y seguro para el cuidado del bebé.",
    "Licores": "Para brindar en una ocasión especial.",
    "Conservas": "Práctico y duradero para tu despensa.",
    "Salsas": "El toque que tu comida estaba esperando.",
}


def description_for(name: str, brand: str, category: str) -> str:
    return f"{name} de {brand}. {BLURBS.get(category, 'Calidad Dumbo para tu día a día.')}"


def _entry(name, category, brand, price, stock, unit, old_price=None):
    return (name, category, brand, price, stock, unit, old_price,
            description_for(name, brand, category))


def all_products() -> list[tuple]:
    entries = [_entry(*product) for product in PRODUCTS]
    for index, (category, names) in enumerate(GENERATED_CATALOG.items()):
        for position, name in enumerate(names):
            brand = BRANDS[(index + position) % len(BRANDS)]
            price = 590 + ((index * 37 + position * 53) % 60) * 150
            old_price = price + 200 + (position % 4) * 100 if (index + position) % 6 == 0 else None
            stock = 5 + (index * 3 + position * 7) % 45
            units = CATEGORY_UNITS.get(category, UNITS)
            unit = units[position % len(units)]
            entries.append(_entry(name, category, brand, price, stock, unit, old_price))
    return entries


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
        if "description" not in columns:
            conn.execute("ALTER TABLE products ADD COLUMN description TEXT NOT NULL DEFAULT ''")
        seed_products(conn)


def seed_products(conn: sqlite3.Connection) -> None:
    existing = {(row["name"], row["category"]) for row in conn.execute(
        "SELECT name, category FROM products").fetchall()}
    for entry in all_products():
        key = (entry[0], entry[1])
        if key in existing:
            conn.execute(
                "UPDATE products SET description = ? WHERE name = ? AND category = ? "
                "AND (description IS NULL OR description = '')",
                (entry[7], entry[0], entry[1]),
            )
            continue
        conn.execute(
            "INSERT INTO products (name, category, brand, price_clp, stock, unit, old_price_clp, description) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            entry,
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
