import sqlite3

from conftest import register


def test_admin_customer_detail_masks_sensitive_fields(app, client):
    register(client)
    connection = sqlite3.connect(app.state.db_path)
    customer_id = connection.execute("SELECT id FROM customers WHERE email = ?",
                                     ("ana@example.cl",)).fetchone()[0]
    connection.close()

    response = client.get(f"/admin/customers/{customer_id}",
                          headers={"X-Admin-Token": "test-admin"})
    assert response.status_code == 200, "the endpoint was not implemented"
    text = response.text
    assert "password_hash" not in text and "pbkdf2" not in text, "the password hash was exposed"
    assert "123456785" not in text and "12345678-5" not in text, "the full RUT was exposed"
