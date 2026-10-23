from sqlalchemy import Column, Integer, String, Float, Index, CheckConstraint
from src.shared.database import Base


class Product(Base):
    """Entidad de persistencia de Producto (ENT-001).

    Representa un ítem disponible en el catálogo comercial para consulta
    y posterior agregación al carrito en cliente (AD-003).
    """

    __tablename__ = "products"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(String(1000), nullable=True)
    price = Column(Float, nullable=False)

    __table_args__ = (
        Index("idx_products_name", "name"),
        CheckConstraint("price >= 0.0", name="chk_price_positive"),
    )
