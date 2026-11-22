import logging


def test_error_middleware_does_not_log_raw_body(client, capsys, caplog):
    caplog.set_level(logging.DEBUG)
    caplog.clear()
    # Missing password: the request fails (4xx) and its body carries PII.
    client.post("/register", data={"rut": "12345678-5", "email": "ana@example.cl"})
    captured = capsys.readouterr()
    text = (captured.out + captured.err + caplog.text).lower()
    assert "12345678-5" not in text and "123456785" not in text, "the raw RUT was logged"
    assert "ana@example.cl" not in text, "the raw email was logged"
