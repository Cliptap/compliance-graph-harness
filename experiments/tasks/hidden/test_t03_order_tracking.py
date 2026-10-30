from conftest import add_order, register


def test_tracking_is_owner_only(client, other_client):
    register(client)
    order = add_order(client)
    order_id = order.headers["location"].rsplit("/", 1)[-1]
    register(other_client, email="beto@example.cl", rut="11111111-1")
    assert other_client.get(f"/orders/{order_id}/tracking").status_code in (401, 403, 404)
    assert client.get(f"/orders/{order_id}/tracking").status_code == 200
