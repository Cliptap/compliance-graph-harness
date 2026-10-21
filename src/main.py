from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from src.shared.config import CORS_ORIGINS
from src.shared.database import engine, Base, SessionLocal
from src.catalog.router import router as catalog_router
from src.catalog.seed import seed_initial_catalog
from src.catalog.schemas import ErrorResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Inicialización del ciclo de vida de la aplicación: crea tablas y precarga datos semilla."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_initial_catalog(db)
    finally:
        db.close()
    yield


app = FastAPI(
    title="Sistema Web Básico de Catálogo y Carrito de Compras",
    description="API REST de solo lectura para consulta y búsqueda de catálogo comercial",
    version="1.0.0",
    lifespan=lifespan,
)

# Configuración de CORS para clientes web locales
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "OPTIONS"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Manejo Fail-Fast estructurado de errores de validación de parámetros (AD-006, ERR-002)."""
    error_dto = ErrorResponse(
        error_code="ERR-002",
        message="Parámetro inválido",
        detail=str(exc.errors()[0].get("msg") if exc.errors() else str(exc)),
    )
    return JSONResponse(status_code=400, content=error_dto.model_dump())


# Montaje del router de catálogo bajo el prefijo canónico /api/v1 (AD-002)
app.include_router(catalog_router, prefix="/api/v1")


@app.get("/health", tags=["system"])
def health_check():
    """Endpoint básico de salud del servicio."""
    return {"status": "healthy"}
