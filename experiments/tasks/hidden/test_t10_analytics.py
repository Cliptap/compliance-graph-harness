from conftest import register


def test_analytics_has_no_personal_data(client):
    register(client)
    response = client.get("/admin/analytics", headers={"X-Admin-Token": "test-admin"})
    assert response.status_code == 200
    assert "123456785" not in response.text
    assert "ana@example.cl" not in response.text
