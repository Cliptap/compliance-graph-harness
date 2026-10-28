from sqlalchemy import func
from sqlalchemy.orm import Session
from src.catalog.models import Product


def get_products(db: Session, search_term: str | None = None) -> tuple[list[Product], int]:
    """Recupera la lista de productos del catálogo con soporte de filtrado textual insensible a mayúsculas."""
    query = db.query(Product)
    if search_term and search_term.strip():
        cleaned = search_term.strip().lower()
        query = query.filter(func.lower(Product.name).contains(cleaned))
    query = query.order_by(Product.id.asc())
    items = query.all()
    return items, len(items)


def get_product_by_id(db: Session, product_id: int) -> Product | None:
    """Recupera un producto del catálogo por su clave primaria."""
    return db.query(Product).filter(Product.id == product_id).first()
