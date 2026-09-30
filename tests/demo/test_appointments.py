import pytest
from httpx import AsyncClient
import pytest_asyncio

from datetime import datetime, timezone, timedelta

pytestmark = [pytest.mark.asyncio, pytest.mark.demo]

@pytest_asyncio.fixture(loop_scope="function")
async def setup_data(async_client: AsyncClient, admin_token: str):
    headers = {"Authorization": f"Bearer {admin_token}"}
    # Create patient
    p_payload = {"id": "pat-1", "identifier": "PAT-111", "name": "Test Patient"}
    await async_client.post("/api/v1/patients/", json=p_payload, headers=headers)
    # Create practitioner
    dr_payload = {"id": "dr-1", "identifier": "DR-111", "name": "Dr. Test", "specialty": "General"}
    await async_client.post("/api/v1/practitioners/", json=dr_payload, headers=headers)
    return {"patient_id": "pat-1", "practitioner_id": "dr-1"}

async def test_create_appointment_success(async_client: AsyncClient, admin_token: str, setup_data):
    headers = {"Authorization": f"Bearer {admin_token}"}
    now = datetime.now(timezone.utc)
    start_t = (now + timedelta(days=5)).replace(microsecond=0).isoformat()
    end_t = (now + timedelta(days=5, minutes=30)).replace(microsecond=0).isoformat()
    payload = {
        "id": "app-1",
        "status": "booked",
        "start_time": start_t,
        "end_time": end_t,
        "patient_id": setup_data["patient_id"],
        "practitioner_id": setup_data["practitioner_id"]
    }
    res = await async_client.post("/api/v1/appointments/", json=payload, headers=headers)
    assert res.status_code == 201

async def test_read_appointment(async_client: AsyncClient, admin_token: str, reader_token: str, setup_data):
    headers_admin = {"Authorization": f"Bearer {admin_token}"}
    now = datetime.now(timezone.utc)
    start_t = (now + timedelta(days=6)).replace(microsecond=0).isoformat()
    end_t = (now + timedelta(days=6, minutes=30)).replace(microsecond=0).isoformat()
    payload = {
        "id": "app-2",
        "status": "booked",
        "start_time": start_t,
        "end_time": end_t,
        "patient_id": setup_data["patient_id"],
        "practitioner_id": setup_data["practitioner_id"]
    }
    await async_client.post("/api/v1/appointments/", json=payload, headers=headers_admin)
    
    headers_reader = {"Authorization": f"Bearer {reader_token}"}
    res = await async_client.get("/api/v1/appointments/app-2", headers=headers_reader)
    assert res.status_code == 200
    assert res.json()["status"] == "booked"

