import logging

from conftest import register


def test_checkout_does_not_log_raw_pii(client, capsys, caplog):
    caplog.set_level(logging.DEBUG)
    register(client)
    client.post("/cart/add/1", data={"quantity": "1"}, follow_redirects=False)
    caplog.clear()
    client.post("/checkout",
                data={"delivery_mode": "pickup", "pickup_store": "Sucursal Centro"},
                follow_redirects=False)
    captured = capsys.readouterr()
    text = (captured.out + captured.err + caplog.text).lower()
    assert "12345678-5" not in text and "123456785" not in text, "the raw RUT was logged"
    assert "ana@example.cl" not in text, "the raw email was logged"
