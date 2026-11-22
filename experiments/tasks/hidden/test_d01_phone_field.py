from conftest import db_dump


def test_secondary_phone_is_stored_and_shown(app, client):
    response = client.post(
        "/register",
        data={"rut": "12345678-5", "email": "ana@example.cl", "password": "secret123",
              "phone": "+56911111111", "secondary_phone": "+56922223333",
              "full_name": "Ana Perez"},
        follow_redirects=False,
    )
    assert response.status_code in (200, 302, 303), f"registration failed: {response.status_code}"
    assert "+56922223333" in db_dump(app), "the secondary phone was not stored"
    assert "+56922223333" in client.get("/account").text, "the secondary phone is not on the account page"
