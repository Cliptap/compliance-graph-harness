import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.main import create_app  # noqa: E402


@pytest.fixture()
def app(tmp_path):
    return create_app(tmp_path / "shop.db", secret="test-secret")


@pytest.fixture()
def client(app):
    return TestClient(app)


@pytest.fixture()
def other_client(app):
    return TestClient(app)


def register(client, *, rut="12345678-5", email="ana@example.cl", password="secret123",
             phone="+56911111111", full_name="Ana Pérez", marketing=None):
    data = {"rut": rut, "email": email, "password": password, "phone": phone, "full_name": full_name}
    if marketing:
        data["marketing_opt_in"] = "1"
    return client.post("/register", data=data, follow_redirects=False)


def add_address(client, line1="Av. Siempre Viva 742", commune="Providencia", city="Santiago"):
    return client.post("/addresses", data={"label": "Casa", "line1": line1, "commune": commune, "city": city},
                       follow_redirects=False)
