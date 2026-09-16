import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio

async def test_create_patient_unauthorized(async_client: AsyncClient):
    """Prueba 401 sin Token de Accesso"""
    payload = {"id": "fhir-1", "identifier": "111-1", "name": "Hack Test"}
    response = await async_client.post("/api/v1/patients/", json=payload)
    assert response.status_code == 401

async def test_create_patient_forbidden(async_client: AsyncClient, reader_token: str):
    """Prueba 403 con roles insuficientes (Alta Gobernanza)"""
    headers = {"Authorization": f"Bearer {reader_token}"}
    payload = {"id": "fhir-1", "identifier": "111-1", "name": "Hack Test 2"}
    response = await async_client.post("/api/v1/patients/", json=payload, headers=headers)
    assert response.status_code == 403

async def test_create_patient_admin_success(async_client: AsyncClient, admin_token: str):
    """Validación TDD Exitosa de creación para un usuario admin"""
    headers = {"Authorization": f"Bearer {admin_token}"}
    payload = {"id": "fhir-1", "identifier": "12345", "name": "TDD Patient", "birth_date": "1990-01-01T00:00:00Z"}
    response = await async_client.post("/api/v1/patients/", json=payload, headers=headers)
    
    assert response.status_code == 201
    data = response.json()
    assert data["identifier"] == "12345"
    assert data["is_deleted"] is False

async def test_read_patient_success(async_client: AsyncClient, admin_token: str, reader_token: str):
    """Validación TDD lectura de pacientes para roles limitados"""
    headers_admin = {"Authorization": f"Bearer {admin_token}"}
    await async_client.post("/api/v1/patients/", json={"id": "fhir-2", "identifier": "777", "name": "Reader Test"}, headers=headers_admin)
    
    headers_reader = {"Authorization": f"Bearer {reader_token}"}
    response = await async_client.get("/api/v1/patients/fhir-2", headers=headers_reader)
    
    assert response.status_code == 200
    assert response.json()["name"] == "Reader Test"

async def test_soft_delete_patient_flow(async_client: AsyncClient, admin_token: str, reader_token: str):
    """Flujo completo TDD para Soft Delete y auditoría ORM base"""
    # 1. Creación
    headers_admin = {"Authorization": f"Bearer {admin_token}"}
    await async_client.post("/api/v1/patients/", json={"id": "fhir-3", "identifier": "888", "name": "Delete Test"}, headers=headers_admin)
    
    # 2. Bloqueo 403 para usuarios sin permisos de eliminación (Sólo 'patients:read')
    headers_reader = {"Authorization": f"Bearer {reader_token}"}
    res_forbidden = await async_client.delete("/api/v1/patients/fhir-3", headers=headers_reader)
    assert res_forbidden.status_code == 403
    
    # 3. Soft Delete exitoso (204)
    res_delete = await async_client.delete("/api/v1/patients/fhir-3", headers=headers_admin)
    assert res_delete.status_code == 204
    
    # 4. Lectura post-eliminación debe fallar (404, oculto por el evento do_orm_execute)
    res_read = await async_client.get("/api/v1/patients/fhir-3", headers=headers_admin)
    assert res_read.status_code == 404
