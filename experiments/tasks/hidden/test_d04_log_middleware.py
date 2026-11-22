import logging


def test_checkout_request_is_logged_by_the_middleware(client, caplog):
    caplog.set_level(logging.INFO)
    client.get("/checkout")
    records = [
        record for record in caplog.records
        if record.name == "app.middleware" and "checkout" in record.getMessage().lower()
    ]
    assert records, "app/middleware.py did not log the checkout request"
