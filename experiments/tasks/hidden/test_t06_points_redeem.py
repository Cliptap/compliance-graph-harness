from conftest import add_order, register


def test_points_redemption_does_not_log_personal_data(client, capsys, caplog):
    register(client)
    add_order(client)
    capsys.readouterr()
    caplog.clear()
    response = client.post("/points/redeem", data={"points": "1"}, follow_redirects=False)
    assert response.status_code in (200, 303)
    captured = capsys.readouterr()
    text = captured.out + captured.err + caplog.text
    assert "123456785" not in text
    assert "ana@example.cl" not in text
