from conftest import register


def test_admin_customers_requires_token_and_masks_data(client):
    register(client)
    assert client.get("/admin/customers").status_code in (401, 403)
    response = client.get("/admin/customers", headers={"X-Admin-Token": "test-admin"})
    assert response.status_code == 200
    assert "password_hash" not in response.text
    assert "pbkdf2" not in response.text
    assert "123456785" not in response.text
