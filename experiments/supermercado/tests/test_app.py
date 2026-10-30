import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import pytest

from app.retention import purge_expired
from conftest import add_address, register

PHOTOS_DIR = Path(__file__).resolve().parents[1] / "app" / "static" / "photos"


def _db(app):
    conn = sqlite3.connect(app.state.db_path)
    conn.row_factory = sqlite3.Row
    return conn


def test_catalog_and_search(client):
    assert client.get("/catalog").status_code == 200
    assert "Plátano" in client.get("/catalog?q=plátano").text
    response = client.get("/catalog?q=palta")
    assert "Palta" in response.text and "Plátano" not in response.text
    assert "Bebida" in client.get("/catalog?category=Bebidas").text


def test_seed_catalog_has_varied_categories_and_offers(client):
    page = client.get("/").text
    assert "dumbo" in page
    assert "Ofertas de la semana" in page and "Lo más vendido" in page
    assert "Nuevos ingresos" in page and "Frescos de la semana" in page
    with _db(client.app) as conn:
        total = conn.execute("SELECT COUNT(*) AS n FROM products").fetchone()["n"]
        categories = conn.execute("SELECT COUNT(DISTINCT category) AS n FROM products").fetchone()["n"]
        offers = conn.execute("SELECT COUNT(*) AS n FROM products WHERE old_price_clp IS NOT NULL").fetchone()["n"]
    assert total >= 120
    assert categories >= 18
    assert offers >= 10


def test_offers_filter_returns_only_discounted_products(client):
    page = client.get("/catalog?ofertas=1").text
    assert "Leche Entera 1 L" in page
    assert "Arroz Grado 1 1 kg" not in page


def test_product_detail_image_and_description(client):
    page = client.get("/product/1")
    assert page.status_code == 200
    assert "Plátano Extra Granel" in page.text
    assert "Fresco y seleccionado" in page.text
    image = client.get("/img/1.svg")
    assert image.status_code == 200
    assert image.headers["content-type"].startswith("image/svg+xml")
    assert image.text.startswith("<svg")


def test_catalog_pagination(client):
    first = client.get("/catalog?page=1")
    second = client.get("/catalog?page=2")
    assert first.status_code == 200 and second.status_code == 200
    assert "Página 1 de" in first.text
    assert "Página 2 de" in second.text


def test_category_catalog_filters_products(client):
    page = client.get("/catalog?category=Lácteos").text
    assert "Leche Entera" in page and "Plátano Extra Granel" not in page


def test_protected_views_redirect_to_login(client):
    for path in ("/account", "/orders", "/addresses", "/rights", "/checkout", "/consent/marketing"):
        response = client.get(path, follow_redirects=False)
        assert response.status_code == 303, path
        assert response.headers["location"].startswith("/login?next="), path


def test_login_returns_to_the_requested_page(client):
    register(client)
    client.post("/logout", follow_redirects=False)
    page = client.get("/login?next=/orders")
    assert 'name="next" value="/orders"' in page.text
    response = client.post("/login", data={"identifier": "ana@example.cl", "password": "secret123",
                                           "next": "/orders"}, follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/orders"


def test_unknown_product_renders_an_html_error(client):
    response = client.get("/product/99999")
    assert response.status_code == 404
    assert response.headers["content-type"].startswith("text/html")
    assert "No se pudo completar" in response.text


def test_favicon_and_asset_version_are_served(client):
    icon = client.get("/favicon.ico")
    assert icon.status_code == 200
    assert icon.headers["content-type"].startswith("image/")
    assert client.get("/static/favicon.svg").status_code == 200
    home = client.get("/")
    assert 'rel="icon"' in home.text
    assert "/static/style.css?v=" in home.text


def test_product_art_is_rendered_inline(client):
    home = client.get("/").text
    assert 'class="product-icon"' in home
    assert 'class="media-category"' in home


@pytest.mark.skipif(not PHOTOS_DIR.exists(), reason="photo assets not included in this workspace")
def test_photos_are_served_and_credited(client):
    home = client.get("/").text
    assert "/static/photos/" in home
    assert "/static/photos/products/" in home
    assert "/credits" in home
    credits = client.get("/credits")
    assert credits.status_code == 200
    assert "Wikimedia Commons" in credits.text
    assert "ATTRIBUTION_PRODUCTS" in credits.text
    photo = client.get("/static/photos/carnes.jpg")
    assert photo.status_code == 200
    assert photo.headers["content-type"].startswith("image/jpeg")
    product = client.get("/static/photos/products/palta-hass-chilena.jpg")
    assert product.status_code == 200
    assert product.headers["content-type"].startswith("image/jpeg")


def test_register_rejects_invalid_rut(client):
    response = client.post("/register", data={"rut": "12345678-0", "email": "x@example.cl",
                                             "password": "secret123"}, follow_redirects=False)
    assert response.status_code == 200
    assert "RUT" in response.text
    with _db(client.app) as conn:
        assert conn.execute("SELECT COUNT(*) AS n FROM customers").fetchone()["n"] == 0


def test_register_masks_rut_in_the_account(client):
    response = register(client)
    assert response.status_code == 303 and response.headers["location"] == "/account"
    account = client.get("/account").text
    assert "12.***.***-5" in account
    assert "12345678-5" not in account


def test_login_with_email_and_rut(app, client, other_client):
    register(client)
    client.post("/logout", follow_redirects=False)
    assert client.post("/login", data={"identifier": "ana@example.cl", "password": "secret123"},
                       follow_redirects=False).status_code == 303

    register(other_client, rut="11111111-1", email="beto@example.cl")
    other_client.post("/logout", follow_redirects=False)
    login = other_client.post("/login", data={"identifier": "11.111.111-1", "password": "secret123"},
                              follow_redirects=False)
    assert login.status_code == 303


def test_cart_subtotal(client):
    register(client)
    client.post("/cart/add/1", data={"quantity": "2"}, follow_redirects=False)
    cart = client.get("/cart").text
    assert "$1450" in cart


def test_checkout_delivery_requires_address_and_pickup_does_not(client):
    register(client)
    client.post("/cart/add/1", data={"quantity": "1"}, follow_redirects=False)
    missing = client.post("/checkout", data={"delivery_mode": "delivery", "address_id": ""}, follow_redirects=False)
    assert missing.status_code == 400

    add_address(client)
    with _db(client.app) as conn:
        address_id = conn.execute("SELECT id FROM addresses").fetchone()["id"]
    ok = client.post("/checkout", data={"delivery_mode": "delivery", "address_id": str(address_id)},
                     follow_redirects=False)
    assert ok.status_code == 303 and ok.headers["location"].startswith("/orders/")

    client.post("/cart/add/1", data={"quantity": "1"}, follow_redirects=False)
    pickup = client.post("/checkout", data={"delivery_mode": "pickup", "pickup_store": "Sucursal Centro"},
                         follow_redirects=False)
    assert pickup.status_code == 303


def test_payment_rejects_card_fields_and_stores_only_a_token(client):
    register(client)
    client.post("/cart/add/1", data={"quantity": "1"}, follow_redirects=False)
    order = client.post("/checkout", data={"delivery_mode": "pickup", "pickup_store": "Sucursal Centro"},
                        follow_redirects=False)
    order_id = order.headers["location"].rsplit("/", 1)[-1]
    rejected = client.post(f"/orders/{order_id}/pay", data={"card_number": "4111111111111111", "cvv": "123"},
                           follow_redirects=False)
    assert rejected.status_code == 400
    paid = client.post(f"/orders/{order_id}/pay", data={}, follow_redirects=False)
    assert paid.status_code == 303
    with _db(client.app) as conn:
        row = conn.execute("SELECT status, payment_token FROM orders WHERE id = ?", (order_id,)).fetchone()
    assert row["status"] == "paid" and row["payment_token"].startswith("SIM-")


def test_order_is_visible_only_to_its_owner(app, client, other_client):
    register(client)
    client.post("/cart/add/1", data={"quantity": "1"}, follow_redirects=False)
    order = client.post("/checkout", data={"delivery_mode": "pickup", "pickup_store": "Sucursal Centro"},
                        follow_redirects=False)
    order_id = order.headers["location"].rsplit("/", 1)[-1]
    register(other_client, rut="11111111-1", email="beto@example.cl")
    assert other_client.get(f"/orders/{order_id}").status_code == 404


def test_points_are_awarded_on_checkout(client):
    register(client)
    client.post("/cart/add/1", data={"quantity": "2"}, follow_redirects=False)
    client.post("/checkout", data={"delivery_mode": "pickup", "pickup_store": "Sucursal Centro"},
                follow_redirects=False)
    with _db(client.app) as conn:
        total = conn.execute("SELECT COALESCE(SUM(points), 0) AS n FROM points_ledger").fetchone()["n"]
    assert total == 1


def test_marketing_is_opt_in_and_can_be_withdrawn(client):
    register(client)
    assert "Inactivo" in client.get("/account").text
    client.post("/consent/marketing/grant", follow_redirects=False)
    assert "Activo" in client.get("/account").text
    client.post("/consent/marketing/withdraw", follow_redirects=False)
    assert "Inactivo" in client.get("/account").text
    with _db(client.app) as conn:
        row = conn.execute("SELECT withdrawn_at FROM consents ORDER BY id DESC").fetchone()
    assert row["withdrawn_at"] is not None


def test_cookie_categories_default_off_and_persist(client):
    page = client.get("/cookies").text
    assert 'name="targeting" value="1" checked' not in page
    client.post("/cookies", data={"targeting": "1"}, follow_redirects=False)
    page = client.get("/cookies").text
    assert 'name="targeting" value="1" checked' in page


def test_all_rights_are_reachable_and_block_prevents_checkout(client):
    register(client)
    for right in ("access", "rectification", "erasure", "opposition", "portability", "block"):
        response = client.post("/rights", data={"right_type": right}, follow_redirects=False)
        assert response.status_code == 303, right
    page = client.get("/rights").text
    for right in ("access", "rectification", "erasure", "opposition", "portability", "block"):
        assert right in page
    with _db(client.app) as conn:
        rows = conn.execute("SELECT * FROM rights_requests").fetchall()
        blocked = conn.execute("SELECT blocked FROM customers").fetchone()["blocked"]
    assert len(rows) == 6
    assert all(row["requested_at"] and row["due_at"] for row in rows)
    assert blocked == 1

    client.post("/cart/add/1", data={"quantity": "1"}, follow_redirects=False)
    assert client.post("/checkout", data={"delivery_mode": "pickup", "pickup_store": "Sucursal Centro"},
                       follow_redirects=False).status_code == 403


def test_retention_purge_anonymises(client):
    with _db(client.app) as conn:
        conn.execute(
            "INSERT INTO customers (rut, email, phone, full_name, password_hash, retention_days, created_at, updated_at) "
            "VALUES ('99999999-9', 'old@example.cl', '+56900000000', 'Old User', 'x', 1, ?, ?)",
            ("2020-01-01T00:00:00+00:00", "2020-01-01T00:00:00+00:00"),
        )
        customer_id = conn.execute("SELECT id FROM customers WHERE email = 'old@example.cl'").fetchone()["id"]
        conn.execute(
            "INSERT INTO addresses (customer_id, label, line1, commune, city, created_at) "
            "VALUES (?, 'Casa', 'Calle 1', 'Santiago', 'Santiago', ?)",
            (customer_id, "2020-01-01T00:00:00+00:00"),
        )
        conn.commit()

    assert purge_expired(client.app.state.db_path, now=datetime(2026, 1, 1, tzinfo=timezone.utc)) == 1
    with _db(client.app) as conn:
        row = conn.execute("SELECT * FROM customers WHERE id = ?", (customer_id,)).fetchone()
        addresses = conn.execute("SELECT COUNT(*) AS n FROM addresses WHERE customer_id = ?",
                                 (customer_id,)).fetchone()["n"]
    assert row["email"] == f"anon-{customer_id}@invalid"
    assert row["rut"] is None and row["phone"] is None and row["full_name"] == "Anonimizado"
    assert addresses == 0


def test_privacy_pages_and_security_headers(client):
    privacy = client.get("/privacy")
    assert privacy.status_code == 200 and "Versión 2026-10-28" in privacy.text
    assert client.get("/privacy/third-parties").status_code == 200
    assert privacy.headers["x-content-type-options"] == "nosniff"


def test_access_portability_and_rectification_are_reachable(client):
    register(client)
    page = client.get("/me/data")
    assert page.status_code == 200 and "123456785" in page.text

    export = client.get("/me/export")
    assert export.status_code == 200
    assert "attachment" in export.headers["content-disposition"]
    payload = json.loads(export.text)
    assert payload["customer"]["rut"] == "123456785"

    update = client.post("/me/update", data={"phone": "+56922222222", "full_name": "Ana P."},
                         follow_redirects=False)
    assert update.status_code == 303
    with _db(client.app) as conn:
        assert conn.execute("SELECT phone FROM customers").fetchone()["phone"] == "+56922222222"
        types = [row["right_type"] for row in conn.execute("SELECT right_type FROM rights_requests")]
    assert "rectification" in types


def test_block_via_me_route_prevents_processing(client):
    register(client)
    assert client.post("/me/block", follow_redirects=False).status_code == 303
    with _db(client.app) as conn:
        assert conn.execute("SELECT blocked FROM customers").fetchone()["blocked"] == 1
    client.post("/cart/add/1", data={"quantity": "1"}, follow_redirects=False)
    assert client.post("/checkout", data={"delivery_mode": "pickup", "pickup_store": "Sucursal Centro"},
                       follow_redirects=False).status_code == 403
