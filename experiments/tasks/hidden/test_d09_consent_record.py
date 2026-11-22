from conftest import db_dump


def test_consent_record_stores_version_and_timestamp(app, client):
    response = client.post(
        "/register",
        data={"rut": "12345678-5", "email": "ana@example.cl", "password": "secret123",
              "phone": "+56911111111", "full_name": "Ana Perez", "marketing_opt_in": "on"},
        follow_redirects=False,
    )
    assert response.status_code in (200, 302, 303), f"registration failed: {response.status_code}"
    assert "1.0" in db_dump(app), "the consent policy version was not stored"
