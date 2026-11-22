from conftest import register


def test_erasure_request_returns_deleted_and_retained(client):
    register(client)
    response = client.post("/account/request-erasure")
    assert response.status_code == 200, f"erasure failed: {response.status_code}"
    payload = response.json()
    assert "deleted" in payload, "response has no 'deleted' key"
    assert "retained" in payload, "response has no 'retained' key"
