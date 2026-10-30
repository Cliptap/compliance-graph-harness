from conftest import card_columns, db_dump, register


def test_payment_method_does_not_persist_pan_or_cvv(app, client):
    register(client)
    response = client.post("/account/payment-methods",
                           data={"label": "Visa", "card_number": "4111111111111111",
                                 "cvv": "937", "expiry": "12/30"},
                           follow_redirects=False)
    assert response.status_code in (200, 303)
    page = client.get("/account/payment-methods")
    assert page.status_code == 200
    assert "4111111111111111" not in page.text
    assert "4111111111111111" not in db_dump(app)
    assert "937" not in card_columns(app)
