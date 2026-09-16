import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio

async def test_create_practitioner_admin(async_client: AsyncClient, admin_token: str):
    headers = {"Authorization": f"Bearer {admin_token}"}
    payload = {"id": "prac-1", "identifier": "MED-001", "name": "Dr. Vibe", "specialty": "Cardiology"}
    res = await async_client.post("/api/v1/practitioners/", json=payload, headers=headers)
    assert res.status_code == 201

async def test_create_practitioner_forbidden(async_client: AsyncClient, reader_token: str):
    headers = {"Authorization": f"Bearer {reader_token}"}
    payload = {"id": "prac-2", "identifier": "MED-002", "name": "Dr. Evil"}
    res = await async_client.post("/api/v1/practitioners/", json=payload, headers=headers)
    assert res.status_code == 403

async def test_read_practitioner(async_client: AsyncClient, admin_token: str, reader_token: str):
    headers_admin = {"Authorization": f"Bearer {admin_token}"}
    await async_client.post("/api/v1/practitioners/", json={"id": "prac-3", "identifier": "MED-003", "name": "Dr. Good", "specialty": "Pediatrics"}, headers=headers_admin)
    
    headers_reader = {"Authorization": f"Bearer {reader_token}"}
    res = await async_client.get("/api/v1/practitioners/prac-3", headers=headers_reader)
    assert res.status_code == 200
    assert res.json()["name"] == "Dr. Good"
