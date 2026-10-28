from pydantic import BaseModel, ConfigDict, Field


class ProductResponse(BaseModel):
    """Esquema de respuesta unitaria de producto (DTO-PROD-RES-001)."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="Identificador numérico único del producto")
    name: str = Field(..., description="Denominación comercial del producto")
    description: str | None = Field(default=None, description="Resumen descriptivo de características")
    price: float = Field(..., ge=0.0, description="Precio unitario en moneda base (INV-001)")


class ProductListResponse(BaseModel):
    """Envelope estructurado para colecciones de catálogo (DTO-PROD-LIST-001)."""

    items: list[ProductResponse] = Field(default_factory=list, description="Lista de productos del catálogo")
    total: int = Field(..., ge=0, description="Cantidad total de elementos contenidos en el listado")


class ErrorResponse(BaseModel):
    """Envelope estructurado para respuestas de error estándar (DTO-ERR-001)."""

    error_code: str = Field(..., description="Código de error de negocio machine-readable (ERR-xxx)")
    message: str = Field(..., description="Explicación concisa y clara del motivo del rechazo")
    detail: str | None = Field(default=None, description="Detalle complementario de la falla")
