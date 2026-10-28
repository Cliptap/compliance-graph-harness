from fastapi import APIRouter, Depends, Query, Path
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from src.catalog import service, schemas
from src.shared.database import get_db

router = APIRouter(prefix="/products", tags=["catalog"])


@router.get(
    "",
    response_model=schemas.ProductListResponse,
    responses={
        200: {"model": schemas.ProductListResponse, "description": "Consulta exitosa del catálogo"},
        400: {"model": schemas.ErrorResponse, "description": "Parámetro de búsqueda inválido"},
    },
    summary="Listar productos del catálogo con soporte de búsqueda textual (EP-001)",
)
def list_products(
    q: str | None = Query(default=None, description="Término de búsqueda opcional por nombre"),
    db: Session = Depends(get_db),
):
    """Retorna la colección de productos disponibles en el catálogo comercial (EP-001).

    Cumple con REQ-001, REQ-002, AC-001, AC-002 y AC-003.
    """
    if q is not None and len(q) > 100:
        error_dto = schemas.ErrorResponse(
            error_code="ERR-002",
            message="Parámetro inválido",
            detail="El parámetro de búsqueda 'q' no puede exceder 100 caracteres",
        )
        return JSONResponse(status_code=400, content=error_dto.model_dump())

    items, total = service.list_products(db=db, search_term=q)
    return schemas.ProductListResponse(items=items, total=total)


@router.get(
    "/{product_id}",
    response_model=schemas.ProductResponse,
    responses={
        200: {"model": schemas.ProductResponse, "description": "Producto encontrado"},
        400: {"model": schemas.ErrorResponse, "description": "Identificador de producto inválido"},
        404: {"model": schemas.ErrorResponse, "description": "Producto no encontrado"},
    },
    summary="Obtener detalle unitario de producto por identificador (EP-002)",
)
def get_product_by_id(
    product_id: int = Path(..., description="Identificador numérico del producto"),
    db: Session = Depends(get_db),
):
    """Retorna los datos comerciales de un producto identificado por su ID (EP-002).

    Cumple con REQ-001, AC-001, AD-003 y soporte para verificación de precios.
    """
    if product_id < 1:
        error_dto = schemas.ErrorResponse(
            error_code="ERR-002",
            message="Parámetro inválido",
            detail="El identificador del producto debe ser un entero positivo mayor o igual a 1",
        )
        return JSONResponse(status_code=400, content=error_dto.model_dump())

    product = service.get_product_by_id(db=db, product_id=product_id)
    if not product:
        error_dto = schemas.ErrorResponse(
            error_code="ERR-001",
            message="Producto no encontrado",
            detail=f"No existe un producto con el identificador {product_id}",
        )
        return JSONResponse(status_code=404, content=error_dto.model_dump())

    return product
