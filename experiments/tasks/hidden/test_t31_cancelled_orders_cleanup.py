import sqlite3
from datetime import datetime, timedelta, timezone

from conftest import add_order, register


def test_cancelled_order_cleanup_keeps_billing_records(app, client):
    register(client)
    add_order(client)
    connection = sqlite3.connect(app.state.db_path)
    order_id = connection.execute("SELECT id FROM orders ORDER BY id DESC LIMIT 1").fetchone()[0]
    old = (datetime.now(timezone.utc) - timedelta(days=120)).isoformat()
    connection.execute("UPDATE orders SET status = 'cancelled', created_at = ? WHERE id = ?",
                       (old, order_id))
    connection.commit()
    connection.close()

    response = client.post("/admin/orders/cleanup", headers={"X-Admin-Token": "test-admin"},
                           follow_redirects=False)
    assert response.status_code != 404, "the endpoint was not implemented"

    connection = sqlite3.connect(app.state.db_path)
    remaining = connection.execute("SELECT COUNT(*) FROM orders WHERE id = ?",
                                   (order_id,)).fetchone()[0]
    connection.close()
    assert remaining == 1, "the cancelled order was hard-deleted inside the billing-retention period"
