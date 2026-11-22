from conftest import register


def test_my_data_returns_the_stored_email(client):
    register(client, email="ana@example.cl")
    response = client.get("/account/my-data")
    assert response.status_code == 200, f"my-data failed: {response.status_code}"
    assert "ana@example.cl" in response.text, "the stored email is not shown"
