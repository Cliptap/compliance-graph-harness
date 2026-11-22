from conftest import db_dump, register

CARD = "4111111111111111"


def test_payment_method_does_not_store_raw_pan(app, client):
    register(client)
    response = client.post(
        "/account/payment-methods",
        data={"label": "Visa", "card_number": CARD, "cvv": "937", "expiry": "12/30"},
        follow_redirects=False,
    )
    assert response.status_code != 404, "the endpoint was not implemented"
    if response.status_code < 400:
        dump = db_dump(app)
        assert CARD not in dump, "the PAN was persisted in clear text"
