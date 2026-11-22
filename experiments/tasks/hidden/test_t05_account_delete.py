from conftest import db_dump, register


def test_delete_creates_erasure_request_and_keeps_record(app, client):
    register(client)
    response = client.post("/account/delete", follow_redirects=False)
    assert response.status_code in (200, 303)
    dump = db_dump(app)
    retained = "ana@example.cl" in dump
    anonymized = "anon-" in dump or "Anonimizado" in dump
    assert retained or anonymized, "the customer row was hard-deleted"
    assert "erasure" in dump, "no erasure request was registered"
