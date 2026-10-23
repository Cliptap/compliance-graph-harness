import os

# Configuración obligatoria de base de datos desacoplada en memoria (AD-005)
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.main import app
from src.shared.database import Base, get_db
from src.catalog.seed import seed_initial_catalog

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="module", autouse=True)
def setup_test_db():
    """Inicializa el esquema y precarga los datos semilla en la base de datos en memoria."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        seed_initial_catalog(db)
    finally:
        db.close()
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="module")
def client():
    """Cliente de pruebas FastAPI con override de base de datos a SQLite en memoria."""
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
# PRUEBAS DE LISTADO Y BÚSQUEDA (EP-001 / REQ-001, REQ-002, AC-001, AC-002, AC-003)
# ==============================================================================

def test_list_all_products_returns_seed_envelope(client: TestClient):
    """Verifica que GET /api/v1/products retorna la colección de 5 productos de SEED-001 (AC-001)."""
    response = client.get("/api/v1/products")
    assert response.status_code == 200
    data = response.json()

    assert "items" in data
    assert "total" in data
    assert data["total"] == 5
    assert len(data["items"]) == 5

    # Validación del primer ítem del catálogo
    first_item = data["items"][0]
    assert first_item["id"] == 1
    assert first_item["name"] == "Cuaderno Universitario"
    assert first_item["price"] == 2500.00
    assert "description" in first_item


def test_search_products_case_insensitive_match(client: TestClient):
    """Verifica filtrado insensible a mayúsculas con coincidencia sobre el nombre (AC-002)."""
    # Minúsculas
    res1 = client.get("/api/v1/products?q=cuaderno")
    assert res1.status_code == 200
    data1 = res1.json()
    assert data1["total"] == 1
    assert data1["items"][0]["name"] == "Cuaderno Universitario"

    # Mayúsculas completas
    res2 = client.get("/api/v1/products?q=CUADERNO")
    assert res2.status_code == 200
    assert res2.json()["total"] == 1

    # Búsqueda parcial de bolígrafo
    res3 = client.get("/api/v1/products?q=bolígrafo")
    assert res3.status_code == 200
    assert res3.json()["total"] == 1
    assert res3.json()["items"][0]["id"] == 2

    # Búsqueda parcial de lámpara
    res4 = client.get("/api/v1/products?q=mesa")
    assert res4.status_code == 200
    assert res4.json()["total"] == 1
    assert res4.json()["items"][0]["name"] == "Lámpara LED de Mesa"


def test_search_products_no_match_returns_empty_list(client: TestClient):
    """Verifica que término sin coincidencias retorna 200 con items vacío y total 0 (AC-003)."""
    response = client.get("/api/v1/products?q=termino_inexistente_xyz")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["items"] == []


def test_search_products_query_too_long_returns_400(client: TestClient):
    """Verifica que un término de búsqueda superior a 100 caracteres genera 400 estructurado."""
    long_query = "a" * 101
    response = client.get(f"/api/v1/products?q={long_query}")
    assert response.status_code == 400
    data = response.json()
    assert data["error_code"] == "ERR-002"
    assert "Parámetro inválido" in data["message"]


# ==============================================================================
# PRUEBAS DE DETALLE UNITARIO POR ID (EP-002 / REQ-001, AC-001, AC-004, AD-003)
# ==============================================================================

def test_get_product_by_id_success(client: TestClient):
    """Verifica que GET /api/v1/products/{id} retorna el producto solicitado (AC-001)."""
    response = client.get("/api/v1/products/3")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 3
    assert data["name"] == "Organizador de Escritorio"
    assert data["price"] == 8500.00


def test_get_product_by_id_not_found_returns_404(client: TestClient):
    """Verifica que un ID inexistente genera HTTP 404 estructurado con ERR-001."""
    response = client.get("/api/v1/products/999")
    assert response.status_code == 404
    data = response.json()
    assert data["error_code"] == "ERR-001"
    assert data["message"] == "Producto no encontrado"
    assert "999" in data["detail"]


def test_get_product_by_id_invalid_id_returns_400(client: TestClient):
    """Verifica que identificadores no positivos o inválidos retornan 400 con ERR-002."""
    res_zero = client.get("/api/v1/products/0")
    assert res_zero.status_code == 400
    assert res_zero.json()["error_code"] == "ERR-002"

    res_neg = client.get("/api/v1/products/-5")
    assert res_neg.status_code == 400
    assert res_neg.json()["error_code"] == "ERR-002"

    res_str = client.get("/api/v1/products/abc")
    assert res_str.status_code == 400
    assert res_str.json()["error_code"] == "ERR-002"


# ==============================================================================
# PRUEBAS DE INVARIANTES ARQUITECTÓNICAS (SOLO LECTURA, AD-003, ANTI-AMNESIA)
# ==============================================================================

def test_backend_invariants_strictly_read_only(client: TestClient):
    """Verifica que los métodos de mutación (POST/PUT/DELETE) en productos son rechazados."""
    res_post = client.post("/api/v1/products", json={"name": "Invasor", "price": 100})
    assert res_post.status_code == 405

    res_put = client.put("/api/v1/products/1", json={"price": 999})
    assert res_put.status_code == 405

    res_del = client.delete("/api/v1/products/1")
    assert res_del.status_code == 405


def test_backend_invariants_no_server_cart_nor_auth(client: TestClient):
    """Verifica que no existen endpoints de servidor para carrito (AD-003) ni autenticación."""
    res_cart = client.get("/api/v1/carts")
    assert res_cart.status_code == 404

    res_cart_post = client.post("/api/v1/carts", json={"items": []})
    assert res_cart_post.status_code == 404

    res_auth = client.post("/api/v1/auth/login", json={"user": "admin"})
    assert res_auth.status_code == 404
