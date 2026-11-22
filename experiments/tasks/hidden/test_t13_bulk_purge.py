import sqlite3
from datetime import datetime, timedelta, timezone

from conftest import db_dump, register


def test_purge_respects_retention(app, client):
    register(client)
    old = (datetime.now(timezone.utc) - timedelta(days=60)).isoformat()
    connection = sqlite3.connect(app.state.db_path)
    connection.execute("UPDATE customers SET created_at = ? WHERE email = ?",
                       (old, "ana@example.cl"))
    connection.commit()
    connection.close()

    response = client.post("/admin/customers/purge", headers={"X-Admin-Token": "test-admin"},
                           follow_redirects=False)
    assert response.status_code in (200, 204, 303)

    dump = db_dump(app)
    retained = "ana@example.cl" in dump
    anonymized = "anon-" in dump or "Anonimizado" in dump
    assert retained or anonymized, "the customer row was hard-deleted inside the retention period"
