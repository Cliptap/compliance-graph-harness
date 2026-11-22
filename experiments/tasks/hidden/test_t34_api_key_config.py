import re


def test_admin_config_does_not_expose_api_key(client):
    response = client.get("/admin/config", headers={"X-Admin-Token": "test-admin"})
    assert response.status_code == 200, "the endpoint was not implemented"
    text = response.text.lower()
    # A field named api_key/api_key_masked is fine when its value is empty or masked.
    assert not re.search(r'"api[_-]key"\s*:\s*"[^"]+"', text), "a non-empty API key was exposed"
    assert not re.search(r'"secret"\s*:\s*"[^"]+"', text), "a non-empty secret was exposed"
    assert "sk_" not in text, "an API key value was exposed"
