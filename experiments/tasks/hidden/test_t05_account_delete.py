from conftest import db_dump, register


def test_delete_creates_erasure_request_and_keeps_retention(app, client):
    register(client)
    response = client.post("/account/delete", follow_redirects=False)
    assert response.status_code in (200, 303)
    dump = db_dump(app)
    assert "ana@example.cl" in dump
    assert "erasure" in dump
