from conftest import db_dump


def test_birth_date_is_stored_at_registration(app, client):
    response = client.post(
        "/register",
        data={"rut": "12345678-5", "email": "ana@example.cl", "password": "secret123",
              "phone": "+56911111111", "full_name": "Ana Perez", "birth_date": "2000-01-01"},
        follow_redirects=False,
    )
    assert response.status_code in (200, 302, 303), f"registration failed: {response.status_code}"
    assert "2000-01-01" in db_dump(app), "the birth date value was not stored"
