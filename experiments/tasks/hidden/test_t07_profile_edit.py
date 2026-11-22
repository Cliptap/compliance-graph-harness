from conftest import register


def test_profile_edit_does_not_expose_password_hash(client):
    register(client)
    page = client.get("/profile")
    assert page.status_code == 200
    update = client.post("/profile", data={"full_name": "Ana P.", "phone": "+56922222222",
                                           "email": "ana@example.cl"}, follow_redirects=False)
    assert update.status_code in (200, 303)
    for response in (page, update):
        assert "password_hash" not in response.text
        assert "pbkdf2" not in response.text
