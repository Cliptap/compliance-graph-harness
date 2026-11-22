import os
import re
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault("ADMIN_TOKEN", "test-admin")

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture()
def app(tmp_path):
    return create_app(tmp_path / "test.db", secret="test")


@pytest.fixture()
def client(app):
    return TestClient(app)


@pytest.fixture()
def other_client(app):
    return TestClient(app)


def register(client, email="ana@example.cl", rut="12345678-5", password="secret123"):
    return client.post(
        "/register",
        data={"rut": rut, "email": email, "password": password,
              "phone": "+56911111111", "full_name": "Ana Pérez"},
        follow_redirects=False,
    )


def add_order(client):
    client.post("/cart/add/1", data={"quantity": "2"}, follow_redirects=False)
    return client.post("/checkout", data={"delivery_mode": "pickup", "pickup_store": "Sucursal Centro"},
                       follow_redirects=False)


def db_dump(app):
    connection = sqlite3.connect(app.state.db_path)
    connection.row_factory = sqlite3.Row
    rows = []
    try:
        tables = [row["name"] for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'").fetchall()]
        for table in tables:
            for row in connection.execute(f'SELECT * FROM "{table}"').fetchall():
                rows.append(str(dict(row)))
    finally:
        connection.close()
    return "\n".join(rows)


def card_columns(app):
    connection = sqlite3.connect(app.state.db_path)
    connection.row_factory = sqlite3.Row
    values = []
    try:
        tables = [row["name"] for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'").fetchall()]
        for table in tables:
            columns = [row["name"] for row in connection.execute(f'PRAGMA table_info("{table}")').fetchall()]
            for column in columns:
                if not re.search(r"(?i)cvv|cvc|card|pan|security", column):
                    continue
                for row in connection.execute(f'SELECT "{column}" FROM "{table}"').fetchall():
                    if row[0] is not None:
                        values.append(str(row[0]))
    finally:
        connection.close()
    return "\n".join(values)
