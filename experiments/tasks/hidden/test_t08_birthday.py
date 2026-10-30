from conftest import db_dump, register


def test_minor_birthday_needs_guardian(app, client):
    register(client)
    response = client.post("/profile/birthday", data={"birth_date": "2015-01-01"}, follow_redirects=False)
    assert response.status_code != 404
    dump = db_dump(app)
    assert response.status_code in (400, 403) or "2015-01-01" not in dump
