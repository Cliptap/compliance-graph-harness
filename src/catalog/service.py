from sqlalchemy.orm import Session
from src.catalog import repository
from src.catalog.models import Product


def list_products(db: Session, search_term: str | None = None) -> tuple[list[Product], int]:
    """Servicio de dominio para consulta y búsqueda en catálogo (COMP-001, REQ-001, REQ-002)."""
    return repository.get_products(db, search_term=search_term)


def get_product_by_id(db: Session, product_id: int) -> Product | None:
    """Servicio de dominio para consulta de producto unitario por ID (COMP-001, REQ-001)."""
    return repository.get_product_by_id(db, product_id=product_id)
