from sqlalchemy.orm import Session
from src.catalog.models import Product

SEED_PRODUCTS = [
    {
        "id": 1,
        "name": "Cuaderno Universitario",
        "description": "Cuaderno espiral de 100 hojas cuadriculadas",
        "price": 2500.00,
    },
    {
        "id": 2,
        "name": "Bolígrafo Tinta Negra",
        "description": "Bolígrafo retráctil con tinta gel de secado rápido",
        "price": 800.00,
    },
    {
        "id": 3,
        "name": "Organizador de Escritorio",
        "description": "Organizador modular de tres compartimentos para papelería",
        "price": 8500.00,
    },
    {
        "id": 4,
        "name": "Lámpara LED de Mesa",
        "description": "Lámpara de bajo consumo con brazo ajustable y luz cálida",
        "price": 15000.00,
    },
    {
        "id": 5,
        "name": "Mochila Urbana Multiuso",
        "description": "Mochila resistente con compartimento interior acolchado",
        "price": 22000.00,
    },
]


def seed_initial_catalog(db: Session) -> None:
    """Precarga declarativa e idempotente de datos semilla iniciales (SEED-001)."""
    for item in SEED_PRODUCTS:
        existing = db.query(Product).filter(Product.id == item["id"]).first()
        if not existing:
            product = Product(
                id=item["id"],
                name=item["name"],
                description=item["description"],
                price=item["price"],
            )
            db.add(product)
    db.commit()
