import logging
import sqlite3

from conftest import register


def test_checkout_logs_without_personal_data(app, client, capsys, caplog):
    caplog.set_level(logging.DEBUG)
    register(client)
    client.post("/cart/add/1", data={"quantity": "1"}, follow_redirects=False)
    caplog.clear()
    client.post("/checkout",
                data={"delivery_mode": "pickup", "pickup_store": "Sucursal Centro"},
                follow_redirects=False)
    captured = capsys.readouterr()
    text = captured.out + captured.err + caplog.text

    connection = sqlite3.connect(app.state.db_path)
    total = connection.execute(
        "SELECT subtotal_clp FROM orders ORDER BY id DESC LIMIT 1").fetchone()[0]
    connection.close()
    assert str(total) in text, "the checkout total was not logged"

    lowered = text.lower()
    assert "12345678-5" not in lowered and "123456785" not in lowered, "the RUT was logged"
    assert "ana@example.cl" not in lowered, "the email was logged"
