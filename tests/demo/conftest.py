import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from src.database.database import Base, get_db
from src.backend.main import app
from src.backend.security.auth import create_access_token

# DB Efímera: SQLite en Memoria Asíncrono para pruebas TDD limpias
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestingSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

@pytest_asyncio.fixture(scope="function", autouse=True)
async def setup_db():
    """Asegura DB limpia por cada Test"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest_asyncio.fixture(scope="function")
async def db_session():
    """Inyecta una sesión real a la DB en memoria"""
    async with TestingSessionLocal() as session:
        yield session

@pytest_asyncio.fixture(scope="function")
async def async_client(db_session):
    """Cliente HTTPx con sobreescritura estricta para usar TestingSessionLocal"""
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client
        
    app.dependency_overrides.clear()

@pytest.fixture
def admin_token():
    """Genera Token JWT real con roles máximos para tests"""
    return create_access_token({"sub": "admin-1", "scopes": ["admin:all"]})

@pytest.fixture
def reader_token():
    """Genera Token JWT real de acceso restringido para tests (solo lectura)"""
    return create_access_token({"sub": "doctor-1", "scopes": ["patients:read", "appointments:read", "practitioners:read"]})
