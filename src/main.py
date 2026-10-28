from contextlib import asynccontextmanager
from datetime import datetime, timezone
import json
import sys
import time
import uuid

from fastapi import Depends, FastAPI, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from src.shared.config import CORS_ORIGINS
from src.shared.database import engine, Base, SessionLocal, get_db
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


@app.middleware("http")
async def observability_middleware(request: Request, call_next) -> Response:
    """Middleware de observabilidad proporcional: correlación X-Request-ID, latencia y log JSON (OBS-001, MET-001, LOG-001, OBS-002)."""
    # OBS-001: Captura o generación determinista de X-Request-ID (UUIDv4)
    request_id = request.headers.get("X-Request-ID")
    if not request_id or not request_id.strip():
        request_id = str(uuid.uuid4())

    start_time = time.perf_counter()

    try:
        response = await call_next(request)
    except Exception as exc:
        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
        log_payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": "ERROR",
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "status_code": 500,
            "duration_ms": duration_ms,
            "message": "Fallo no controlado en el servidor",
        }
        sys.stdout.write(json.dumps(log_payload) + "\n")
        sys.stdout.flush()

        error_dto = ErrorResponse(
            error_code="ERR-500",
            message="Error interno del servidor",
            detail=str(exc),
        )
        error_resp = JSONResponse(status_code=500, content=error_dto.model_dump())
        error_resp.headers["X-Request-ID"] = request_id
        return error_resp

    duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
    response.headers["X-Request-ID"] = request_id

    status_code = response.status_code
    if status_code < 400:
        level = "INFO"
        message = "Solicitud procesada exitosamente"
    elif status_code < 500:
        level = "WARNING"
        message = "Solicitud rechazada o recurso no encontrado"
    else:
        level = "ERROR"
        message = "Fallo en el servidor al procesar la solicitud"

    # LOG-001 y OBS-002: Formato JSON unilínea a stdout sin filtrar credenciales ni datos sensibles (CWE-532)
    log_payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "level": level,
        "request_id": request_id,
        "method": request.method,
        "path": request.url.path,
        "status_code": status_code,
        "duration_ms": duration_ms,
        "message": message,
    }
    sys.stdout.write(json.dumps(log_payload) + "\n")
    sys.stdout.flush()

    return response


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
def health_check(db: Session = Depends(get_db)):
    """Sondeo de salud del servicio y verificación de conectividad relacional SQLite (HC-001)."""
    try:
        db.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "connected"}
    except Exception:
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "database": "disconnected"},
        )

