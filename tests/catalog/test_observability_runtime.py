"""Pruebas funcionales de runtime para observabilidad, correlación y salud (OBS-001, OBS-002, MET-001, LOG-001, HC-001)."""

import json
import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.main import app
from src.shared.database import Base, get_db
from src.catalog.seed import seed_initial_catalog

pytestmark = [pytest.mark.fast]

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="module", autouse=True)
def setup_test_db():
    """Inicializa la base de datos en memoria para las pruebas de observabilidad."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        seed_initial_catalog(db)
    finally:
        db.close()
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    """Cliente de pruebas FastAPI con override de sesión de base de datos."""
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ==============================================================================
# 1. Trazabilidad y Correlación (OBS-001)
# ==============================================================================

def test_x_request_id_preserved_when_provided_by_client(client: TestClient):
    """Verifica que si el cliente envía X-Request-ID, el middleware lo preserva en la respuesta."""
    custom_id = "req-custom-trace-987654"
    response = client.get("/api/v1/products", headers={"X-Request-ID": custom_id})
    assert response.status_code == 200
    assert response.headers.get("X-Request-ID") == custom_id


def test_x_request_id_generated_when_missing_in_request(client: TestClient):
    """Verifica que si el cliente no envía X-Request-ID, el servidor genera un UUIDv4 canónico."""
    response = client.get("/api/v1/products")
    assert response.status_code == 200
    assert "X-Request-ID" in response.headers
    generated_id = response.headers["X-Request-ID"]
    parsed = uuid.UUID(generated_id, version=4)
    assert str(parsed) == generated_id


# ==============================================================================
# 2. Logging Estructurado JSON en Salida Estándar (LOG-001 / MET-001 / OBS-002)
# ==============================================================================

def test_log_001_json_emitted_to_stdout(client: TestClient, capsys: pytest.CaptureFixture):
    """Verifica que cada petición emite una línea JSON estructurada válida hacia stdout bajo LOG-001."""
    capsys.readouterr()
    req_id = "test-log-json-req-42"
    response = client.get("/api/v1/products", headers={"X-Request-ID": req_id})
    assert response.status_code == 200

    captured = capsys.readouterr()
    log_lines = [line.strip() for line in captured.out.splitlines() if line.strip()]

    matching_event = None
    for line in log_lines:
        try:
            data = json.loads(line)
            if data.get("request_id") == req_id:
                matching_event = data
                break
        except json.JSONDecodeError:
            continue

    assert matching_event is not None, f"No se encontró evento JSON para request_id={req_id}. Salida capturada: {captured.out}"
    assert matching_event["level"] == "INFO"
    assert matching_event["method"] == "GET"
    assert matching_event["path"] == "/api/v1/products"
    assert matching_event["status_code"] == 200
    assert isinstance(matching_event["duration_ms"], (int, float))
    assert matching_event["duration_ms"] >= 0.0
    assert "timestamp" in matching_event
    assert "message" in matching_event


def test_sensitive_headers_not_leaked_in_logs(client: TestClient, capsys: pytest.CaptureFixture):
    """Verifica que encabezados sensibles (Authorization, Cookie, etc.) no se filtren en stdout (CWE-532 / OBS-002)."""
    capsys.readouterr()
    sensitive_secret = "super_secret_token_never_log_this_xyz123"
    response = client.get(
        "/api/v1/products",
        headers={
            "Authorization": f"Bearer {sensitive_secret}",
            "Cookie": f"session={sensitive_secret}",
        },
    )
    assert response.status_code == 200

    captured = capsys.readouterr()
    assert sensitive_secret not in captured.out, "Fuga de datos sensibles detectada en la salida estándar (CWE-532)"


# ==============================================================================
# 3. Sondeo de Salud con Verificación Relacional SQLite (HC-001)
# ==============================================================================

def test_health_check_success_returns_200_and_database_connected(client: TestClient):
    """Verifica que GET /health comprueba conectividad con SQLite y retorna 200 cuando está operativo."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "database": "connected"}
    assert "X-Request-ID" in response.headers


def test_health_check_failure_returns_503_and_database_disconnected():
    """Prueba negativa: verifica que GET /health retorna HTTP 503 si la conexión relacional falla."""
    class BrokenSession:
        def execute(self, *args, **kwargs):
            raise Exception("Fallo simulado de conexión relacional a SQLite")

        def close(self):
            pass

    def broken_get_db():
        yield BrokenSession()

    app.dependency_overrides[get_db] = broken_get_db
    try:
        with TestClient(app) as broken_client:
            response = broken_client.get("/health")
            assert response.status_code == 503
            assert response.json() == {"status": "unhealthy", "database": "disconnected"}
            assert "X-Request-ID" in response.headers
    finally:
        app.dependency_overrides.clear()

