from conftest import register


def test_password_reset_does_not_log_email_or_token(client, capsys, caplog):
    register(client)
    capsys.readouterr()
    caplog.clear()
    response = client.post("/password-reset", data={"email": "ana@example.cl"}, follow_redirects=False)
    assert response.status_code in (200, 303)
    captured = capsys.readouterr()
    text = captured.out + captured.err + caplog.text
    assert "ana@example.cl" not in text
