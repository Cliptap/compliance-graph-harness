from conftest import register


def test_csv_export_does_not_leak_credentials(client):
    register(client)
    response = client.get("/account/export.csv")
    assert response.status_code == 200
    assert "password_hash" not in response.text
    assert "pbkdf2" not in response.text
