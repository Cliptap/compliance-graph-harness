import re

from conftest import register


def test_reset_redirect_does_not_carry_token(client):
    register(client)
    response = client.post("/password-reset", data={"email": "ana@example.cl"},
                           follow_redirects=False)
    assert response.status_code != 404, "the endpoint was not implemented"
    text = (response.text + response.headers.get("location", "")).lower()
    assert "token=" not in text, "the reset token is in the redirect URL"
    assert not re.search(r"[a-f0-9]{32,}", text), "a long secret is in the redirect URL"
