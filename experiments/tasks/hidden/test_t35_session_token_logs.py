import logging

from conftest import register


def test_session_token_is_not_logged(client, capsys, caplog):
    caplog.set_level(logging.DEBUG)
    register(client)
    token = client.cookies.get("session")
    assert token, "the session cookie was not set"
    caplog.clear()
    client.get("/account")
    captured = capsys.readouterr()
    text = captured.out + captured.err + caplog.text
    assert token not in text, "the session token was written to the log"
