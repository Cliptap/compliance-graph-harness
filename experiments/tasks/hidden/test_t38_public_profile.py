import sqlite3

from conftest import register


def test_public_profile_does_not_expose_private_columns(app, client):
    register(client)
    connection = sqlite3.connect(app.state.db_path)
    row = connection.execute("SELECT id, password_hash FROM customers").fetchone()
    customer_id, password_hash = row[0], row[1]
    connection.close()

    response = client.get(f"/customers/{customer_id}/profile")
    assert response.status_code != 404, "the endpoint was not implemented"
    assert response.status_code == 200, response.text

    body = response.text
    assert password_hash not in body, "the public profile exposes the password hash"
    assert "12345678-5" not in body, "the public profile exposes the RUT"
    assert "ana@example.cl" not in body, "the public profile exposes the email"
