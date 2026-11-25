import logging
import sqlite3

from conftest import add_order, register


def test_payment_failure_log_does_not_expose_the_customer_or_the_token(app, client, caplog):
    register(client)
    add_order(client)
    connection = sqlite3.connect(app.state.db_path)
    order_id = connection.execute("SELECT id FROM orders ORDER BY id DESC LIMIT 1").fetchone()[0]
    connection.close()

    with caplog.at_level(logging.DEBUG):
        first = client.post(f"/orders/{order_id}/pay", data={}, follow_redirects=False)
        assert first.status_code not in (404, 405), "the payment route was not implemented"
        second = client.post(f"/orders/{order_id}/pay", data={}, follow_redirects=False)
        assert second.status_code == 409, "the failure path was not reached"

    connection = sqlite3.connect(app.state.db_path)
    token = connection.execute("SELECT payment_token FROM orders WHERE id = ?",
                               (order_id,)).fetchone()[0]
    connection.close()

    # Only the application's own records: httpx and asyncio log the requests too.
    messages = [record.getMessage() for record in caplog.records
                if record.name.startswith("app")]
    assert messages, "no diagnostic was logged on the failure path"
    text = "\n".join(messages)
    assert "ana@example.cl" not in text, "the log exposes the customer email"
    assert "12345678-5" not in text, "the log exposes the RUT"
    if token:
        assert token not in text, "the log exposes the payment token"
