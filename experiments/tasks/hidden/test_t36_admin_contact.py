import sqlite3

from conftest import register


def test_admin_contact_masks_the_email_and_the_rut(app, client):
    register(client)
    connection = sqlite3.connect(app.state.db_path)
    customer_id = connection.execute("SELECT id FROM customers").fetchone()[0]
    connection.close()

    response = client.get(f"/admin/customers/{customer_id}/contact",
                          headers={"X-Admin-Token": "test-admin"})
    assert response.status_code != 404, "the endpoint was not implemented"
    assert response.status_code == 200, response.text

    body = response.text
    assert "ana@example.cl" not in body, "the email is not masked in an admin response"
    assert "12345678-5" not in body, "the full RUT is exposed in an admin response"
    assert "Ana" in body, "the endpoint does not return the customer name"
