import re

from conftest import register


def test_password_reset_does_not_return_token(client):
    register(client)
    response = client.post("/password-reset", data={"email": "ana@example.cl"},
                           follow_redirects=False)
    assert response.status_code != 404, "the endpoint was not implemented"
    text = response.text + response.headers.get("location", "")
    lowered = text.lower()
    assert not re.search(r'["\'](reset_)?token["\']\s*:', lowered), "the reset token was returned"
    assert not re.search(r"[a-f0-9]{32,}", lowered), "a long secret was returned"
