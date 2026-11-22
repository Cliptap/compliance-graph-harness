from conftest import register


def test_consent_withdrawal_returns_timestamp(client):
    register(client)
    response = client.post("/account/consent/withdraw")
    assert response.status_code == 200, f"withdrawal failed: {response.status_code}"
    payload = response.json()
    assert payload.get("withdrawn_at"), "response has no withdrawn_at timestamp"
