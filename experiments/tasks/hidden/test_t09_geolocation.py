from conftest import db_dump, register


def test_geolocation_needs_consent(app, client):
    register(client)
    response = client.post("/checkout/geolocation",
                           data={"latitude": "33.45", "longitude": "-70.66"}, follow_redirects=False)
    assert response.status_code != 404
    dump = db_dump(app)
    assert "33.45" not in dump
    assert "-70.66" not in dump
