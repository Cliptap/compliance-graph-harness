"""Fictional supermarket target system for the harness experiment.

Deliberately built without the harness: a plain FastAPI application with server-rendered
pages, a local SQLite database and no external services. Privacy controls are part of the
base design so that seeded variants (fase 3) can introduce one violation at a time.
"""
from __future__ import annotations

import json
import os
import re
import sqlite3
import unicodedata
import uuid
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from html import escape
from pathlib import Path

from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from itsdangerous import BadSignature, URLSafeSerializer
from starlette.middleware.base import BaseHTTPMiddleware

from app import db
from app.security import (
    hash_password,
    is_valid_email,
    is_valid_rut,
    mask_rut,
    normalize_rut,
    verify_password,
)

BASE_DIR = Path(__file__).resolve().parent
POLICY_VERSION = "2026-10-28"
POLICY_DATE = "2026-10-28"
CONTACT_CHANNEL = "privacidad@supermercado-ficticio.cl"
RIGHT_TYPES = ("access", "rectification", "erasure", "opposition", "portability", "block")
PICKUP_STORES = ("Sucursal Centro", "Sucursal Providencia", "Sucursal Ñuñoa")
SECRET_DEFAULT = "dev-only-secret-change-me"
PER_PAGE = 24
PALETTE = [
    ("#0d4f49", "#1fbf9c"), ("#b45309", "#f6c177"), ("#9f1239", "#ff7a8a"),
    ("#1e3a8a", "#60a5fa"), ("#5b21b6", "#c4b5fd"), ("#166534", "#4ade80"),
    ("#9a3412", "#fdba74"), ("#0f766e", "#5eead4"), ("#7c2d12", "#fca5a5"),
    ("#3f3f46", "#a1a1aa"),
]


def _product_svg(product) -> str:
    name = product["name"]
    category = product["category"]
    index = sum(ord(ch) for ch in f"{name}{category}") % len(PALETTE)
    start, end = PALETTE[index]
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 300" role="img" '
        f'aria-label="{escape(name)}">'
        f'<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1">'
        f'<stop offset="0" stop-color="{start}"/><stop offset="1" stop-color="{end}"/>'
        '</linearGradient></defs>'
        '<rect width="400" height="300" fill="url(#g)"/>'
        '<circle cx="200" cy="138" r="86" fill="rgba(255,255,255,0.12)"/>'
        '<text x="200" y="172" text-anchor="middle" font-family="Segoe UI, Arial, sans-serif" '
        f'font-size="92" font-weight="800" fill="#ffffff">{escape(name[:1].upper())}</text>'
        '<text x="200" y="252" text-anchor="middle" font-family="Segoe UI, Arial, sans-serif" '
        f'font-size="20" font-weight="600" fill="rgba(255,255,255,0.9)">{escape(category)}</text>'
        '</svg>'
    )


def _serializer(secret: str) -> URLSafeSerializer:
    return URLSafeSerializer(secret, salt="supermercado-ficticio")


def _safe_load(serializer: URLSafeSerializer, raw: str | None, default):
    if not raw:
        return default
    try:
        return serializer.loads(raw)
    except BadSignature:
        return default


def _email_norm(email: str) -> str:
    return email.strip().lower()


def _slug(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text)
    plain = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    return re.sub(r"[^a-z0-9]+", "-", plain.lower()).strip("-")


def _decorate(row) -> dict:
    product = dict(row)
    product["category_slug"] = _slug(product["category"])
    product["initial"] = product["name"][:1].upper()
    old = product.get("old_price_clp")
    product["discount_pct"] = round((old - product["price_clp"]) * 100 / old) if old else 0
    return product


def create_app(db_path: Path | str | None = None, secret: str | None = None) -> FastAPI:
    path = Path(db_path) if db_path is not None else db.default_db_path()
    db.init_db(path)
    signer = _serializer(secret or os.environ.get("APP_SECRET", SECRET_DEFAULT))
    templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

    app = FastAPI(title="Dumbo", docs_url=None, redoc_url=None)
    app.state.db_path = path
    app.state.secret = secret or os.environ.get("APP_SECRET", SECRET_DEFAULT)
    app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

    class SecurityHeaders(BaseHTTPMiddleware):
        async def dispatch(self, request, call_next):
            response = await call_next(request)
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["Referrer-Policy"] = "same-origin"
            response.headers["Content-Security-Policy"] = "default-src 'self'; form-action 'self'"
            return response

    app.add_middleware(SecurityHeaders)

    @contextmanager
    def conn():
        connection = db.connect(path)
        try:
            yield connection
            connection.commit()
        finally:
            connection.close()

    def session_customer(request: Request) -> sqlite3.Row | None:
        data = _safe_load(signer, request.cookies.get("session"), {})
        customer_id = data.get("cid") if isinstance(data, dict) else None
        if not customer_id:
            return None
        with conn() as connection:
            return connection.execute("SELECT * FROM customers WHERE id = ?", (customer_id,)).fetchone()

    def read_cart(request: Request) -> dict[str, int]:
        data = _safe_load(signer, request.cookies.get("cart"), {})
        if not isinstance(data, dict):
            return {}
        return {str(k): int(v) for k, v in data.items() if str(k).isdigit() and int(v) > 0}

    def read_cookie_prefs(request: Request) -> dict | None:
        data = _safe_load(signer, request.cookies.get("cookie_prefs"), None)
        return data if isinstance(data, dict) else None

    def base_context(request: Request) -> dict:
        cart = read_cart(request)
        with conn() as connection:
            categories = [
                {"name": row["category"], "count": row["n"], "slug": _slug(row["category"])}
                for row in connection.execute(
                    "SELECT category, COUNT(*) AS n FROM products GROUP BY category ORDER BY category"
                ).fetchall()
            ]
        return {
            "customer": session_customer(request),
            "cart_count": sum(cart.values()),
            "cookie_prefs": read_cookie_prefs(request),
            "policy_version": POLICY_VERSION,
            "policy_date": POLICY_DATE,
            "contact_channel": CONTACT_CHANNEL,
            "categories": categories,
        }

    def render(request: Request, name: str, **context) -> HTMLResponse:
        payload = {**base_context(request), **context}
        return templates.TemplateResponse(request=request, name=name, context=payload)

    def require_customer(request: Request) -> sqlite3.Row:
        customer = session_customer(request)
        if customer is None:
            raise HTTPException(status_code=401, detail="Inicia sesión para continuar.")
        return customer

    def cart_lines(request: Request) -> list[dict]:
        cart = read_cart(request)
        if not cart:
            return []
        ids = [int(k) for k in cart]
        placeholders = ",".join("?" for _ in ids)
        with conn() as connection:
            rows = connection.execute(
                f"SELECT * FROM products WHERE id IN ({placeholders})", ids
            ).fetchall()
        by_id = {row["id"]: row for row in rows}
        lines = []
        for product_id, quantity in cart.items():
            product = by_id.get(int(product_id))
            if not product:
                continue
            lines.append({
                "product": product,
                "quantity": quantity,
                "line_total": product["price_clp"] * quantity,
            })
        return lines

    def create_right(connection, customer_id: int, right_type: str, notes: str = "") -> None:
        requested = datetime.now(timezone.utc).replace(microsecond=0)
        due = db.add_business_days(requested, 2) if right_type == "block" else requested + timedelta(days=30)
        status = "blocked" if right_type == "block" else "received"
        connection.execute(
            "INSERT INTO rights_requests (customer_id, right_type, status, requested_at, due_at, notes) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (customer_id, right_type, status, requested.isoformat(), due.isoformat(), notes.strip() or None),
        )
        if right_type == "block":
            connection.execute("UPDATE customers SET blocked = 1, updated_at = ? WHERE id = ?",
                               (db.now_iso(), customer_id))

    def set_session(response, customer_id: int) -> None:
        response.set_cookie(
            "session", signer.dumps({"cid": customer_id}), httponly=True, samesite="lax", max_age=86_400
        )

    def cart_response(response, cart: dict[str, int]):
        if cart:
            response.set_cookie("cart", signer.dumps(cart), httponly=True, samesite="lax", max_age=604_800)
        else:
            response.delete_cookie("cart")
        return response

    def catalog_filter(q: str, category: str, ofertas: int) -> tuple[str, list]:
        where, params = " WHERE 1=1", []
        if q.strip():
            where += " AND (name LIKE ? OR brand LIKE ?)"
            like = f"%{q.strip()}%"
            params.extend([like, like])
        if category.strip():
            where += " AND category = ?"
            params.append(category.strip())
        if ofertas:
            where += " AND old_price_clp IS NOT NULL"
        return where, params

    @app.get("/", response_class=HTMLResponse)
    def home(request: Request):
        with conn() as connection:
            total = connection.execute("SELECT COUNT(*) AS n FROM products").fetchone()["n"]
            offers = [_decorate(row) for row in connection.execute(
                "SELECT * FROM products WHERE old_price_clp IS NOT NULL "
                "ORDER BY (old_price_clp - price_clp) DESC LIMIT 8").fetchall()]
            featured = [_decorate(row) for row in connection.execute(
                "SELECT * FROM products ORDER BY stock DESC, name LIMIT 12").fetchall()]
            newest = [_decorate(row) for row in connection.execute(
                "SELECT * FROM products ORDER BY id DESC LIMIT 8").fetchall()]
            showcases = []
            for title, category in (("Frescos de la semana", "Frutas y verduras"),
                                    ("Para tu despensa", "Despensa"),
                                    ("Cuidado del hogar", "Limpieza"),
                                    ("Para tu mascota", "Mascotas"),
                                    ("Snacks y dulces", "Snacks"),
                                    ("Bebés e infantil", "Infantil"),
                                    ("Desayuno y café", "Desayuno"),
                                    ("Congelados", "Congelados")):
                rows = connection.execute(
                    "SELECT * FROM products WHERE category = ? ORDER BY stock DESC, id LIMIT 4",
                    (category,)).fetchall()
                showcases.append({"title": title, "category": category,
                                  "products": [_decorate(row) for row in rows]})
        return render(request, "index.html", offers=offers, featured=featured, newest=newest,
                      showcases=showcases, total=total)

    @app.get("/catalog", response_class=HTMLResponse)
    def catalog(request: Request, q: str = "", category: str = "", ofertas: int = 0, page: int = 1):
        page = max(1, page)
        where, params = catalog_filter(q, category, ofertas)
        with conn() as connection:
            total = connection.execute(f"SELECT COUNT(*) AS n FROM products{where}", params).fetchone()["n"]
            pages = max(1, (total + PER_PAGE - 1) // PER_PAGE)
            page = min(page, pages)
            rows = connection.execute(
                f"SELECT * FROM products{where} ORDER BY id LIMIT ? OFFSET ?",
                [*params, PER_PAGE, (page - 1) * PER_PAGE],
            ).fetchall()
        return render(request, "catalog.html", products=[_decorate(row) for row in rows], total=total,
                      page=page, pages=pages, q=q, category=category, ofertas=ofertas)

    @app.get("/product/{product_id}", response_class=HTMLResponse)
    def product_detail(request: Request, product_id: int):
        with conn() as connection:
            row = connection.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
            if row is None:
                raise HTTPException(status_code=404, detail="Producto no encontrado.")
            product = _decorate(row)
            related = [_decorate(item) for item in connection.execute(
                "SELECT * FROM products WHERE category = ? AND id != ? ORDER BY stock DESC, id LIMIT 4",
                (product["category"], product_id)).fetchall()]
        return render(request, "product.html", product=product, related=related)

    @app.get("/img/{product_id}.svg")
    def product_image(product_id: int):
        with conn() as connection:
            row = connection.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Producto no encontrado.")
        return Response(content=_product_svg(row), media_type="image/svg+xml",
                        headers={"Cache-Control": "public, max-age=86400"})

    @app.post("/cart/add/{product_id}")
    def cart_add(request: Request, product_id: int, quantity: int = Form(1)):
        if quantity < 1:
            quantity = 1
        with conn() as connection:
            product = connection.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
        if product is None:
            raise HTTPException(status_code=404, detail="Producto no encontrado.")
        cart = read_cart(request)
        key = str(product_id)
        cart[key] = min(cart.get(key, 0) + quantity, int(product["stock"]))
        response = RedirectResponse("/cart", status_code=303)
        return cart_response(response, cart)

    @app.post("/cart/update")
    def cart_update(request: Request, product_id: int = Form(...), quantity: int = Form(...)):
        cart = read_cart(request)
        key = str(product_id)
        if quantity <= 0:
            cart.pop(key, None)
        else:
            with conn() as connection:
                product = connection.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
            if product is None:
                raise HTTPException(status_code=404, detail="Producto no encontrado.")
            cart[key] = min(quantity, int(product["stock"]))
        return cart_response(RedirectResponse("/cart", status_code=303), cart)

    @app.get("/cart", response_class=HTMLResponse)
    def cart_view(request: Request):
        lines = cart_lines(request)
        subtotal = sum(line["line_total"] for line in lines)
        return render(request, "cart.html", lines=lines, subtotal=subtotal)

    @app.get("/register", response_class=HTMLResponse)
    def register_form(request: Request):
        return render(request, "register.html")

    @app.post("/register", response_class=HTMLResponse)
    def register(
        request: Request,
        rut: str = Form(""),
        email: str = Form(""),
        phone: str = Form(""),
        full_name: str = Form(""),
        password: str = Form(""),
        marketing_opt_in: str | None = Form(None),
    ):
        normalized = normalize_rut(rut)
        errors = []
        if not is_valid_rut(rut):
            errors.append("El RUT no es válido.")
        if not is_valid_email(email):
            errors.append("El correo electrónico no es válido.")
        if len(password) < 8:
            errors.append("La contraseña debe tener al menos 8 caracteres.")
        if errors:
            return render(request, "register.html", errors=errors, rut=rut, email=email, phone=phone,
                          full_name=full_name)
        timestamp = db.now_iso()
        try:
            with conn() as connection:
                cursor = connection.execute(
                    "INSERT INTO customers (rut, email, phone, full_name, password_hash, created_at, updated_at) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (normalized, _email_norm(email), phone.strip() or None, full_name.strip() or None,
                     hash_password(password), timestamp, timestamp),
                )
                customer_id = cursor.lastrowid
                if marketing_opt_in:
                    connection.execute(
                        "INSERT INTO consents (customer_id, purpose, policy_version, granted_at) VALUES (?, ?, ?, ?)",
                        (customer_id, "marketing", POLICY_VERSION, timestamp),
                    )
        except sqlite3.IntegrityError:
            return render(request, "register.html", errors=["El RUT o el correo ya están registrados."],
                          rut=rut, email=email, phone=phone, full_name=full_name)
        response = RedirectResponse("/account", status_code=303)
        set_session(response, customer_id)
        return response

    @app.get("/login", response_class=HTMLResponse)
    def login_form(request: Request):
        return render(request, "login.html")

    @app.post("/login", response_class=HTMLResponse)
    def login(request: Request, identifier: str = Form(""), password: str = Form("")):
        rut = normalize_rut(identifier)
        with conn() as connection:
            customer = connection.execute(
                "SELECT * FROM customers WHERE email = ? OR (rut IS NOT NULL AND rut = ?)",
                (_email_norm(identifier), rut),
            ).fetchone()
        if customer is None or not verify_password(password, customer["password_hash"]):
            return render(request, "login.html", errors=["Credenciales inválidas."])
        if customer["blocked"]:
            return render(request, "login.html", errors=["La cuenta está bloqueada; escribe a "
                                                          f"{CONTACT_CHANNEL} para revisar tu caso."])
        response = RedirectResponse("/account", status_code=303)
        set_session(response, customer["id"])
        return response

    @app.post("/logout")
    def logout():
        response = RedirectResponse("/", status_code=303)
        response.delete_cookie("session")
        return response

    @app.get("/account", response_class=HTMLResponse)
    def account(request: Request):
        customer = require_customer(request)
        with conn() as connection:
            points = connection.execute(
                "SELECT COALESCE(SUM(points), 0) AS total FROM points_ledger WHERE customer_id = ?",
                (customer["id"],),
            ).fetchone()["total"]
            consents = connection.execute(
                "SELECT * FROM consents WHERE customer_id = ? ORDER BY id DESC", (customer["id"],)
            ).fetchall()
            addresses = connection.execute(
                "SELECT * FROM addresses WHERE customer_id = ? ORDER BY id DESC", (customer["id"],)
            ).fetchall()
            rights = connection.execute(
                "SELECT * FROM rights_requests WHERE customer_id = ? ORDER BY id DESC", (customer["id"],)
            ).fetchall()
        active = next((c for c in consents if c["withdrawn_at"] is None), None)
        return render(request, "account.html", masked_rut=mask_rut(customer["rut"]), points=points,
                      marketing_active=active is not None, addresses=addresses, rights=rights,
                      blocked=bool(customer["blocked"]))

    @app.get("/addresses", response_class=HTMLResponse)
    def addresses(request: Request):
        customer = require_customer(request)
        with conn() as connection:
            rows = connection.execute(
                "SELECT * FROM addresses WHERE customer_id = ? ORDER BY id DESC", (customer["id"],)
            ).fetchall()
        return render(request, "addresses.html", addresses=rows)

    @app.post("/addresses")
    def address_create(
        request: Request,
        label: str = Form(""),
        line1: str = Form(""),
        commune: str = Form(""),
        city: str = Form(""),
    ):
        customer = require_customer(request)
        if not line1.strip() or not commune.strip() or not city.strip():
            raise HTTPException(status_code=400, detail="Completa dirección, comuna y ciudad.")
        with conn() as connection:
            connection.execute(
                "INSERT INTO addresses (customer_id, label, line1, commune, city, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (customer["id"], label.strip() or "Domicilio", line1.strip(), commune.strip(), city.strip(),
                 db.now_iso()),
            )
        return RedirectResponse("/addresses", status_code=303)

    @app.get("/checkout", response_class=HTMLResponse)
    def checkout_form(request: Request):
        customer = require_customer(request)
        if customer["blocked"]:
            return render(request, "error.html", message="La cuenta está bloqueada: no se pueden procesar pedidos.")
        lines = cart_lines(request)
        if not lines:
            return RedirectResponse("/cart", status_code=303)
        with conn() as connection:
            addresses_rows = connection.execute(
                "SELECT * FROM addresses WHERE customer_id = ? ORDER BY id DESC", (customer["id"],)
            ).fetchall()
        subtotal = sum(line["line_total"] for line in lines)
        return render(request, "checkout.html", lines=lines, subtotal=subtotal, addresses=addresses_rows,
                      stores=PICKUP_STORES)

    @app.post("/checkout")
    def checkout_create(
        request: Request,
        delivery_mode: str = Form("delivery"),
        address_id: str = Form(""),
        pickup_store: str = Form(""),
    ):
        customer = require_customer(request)
        if customer["blocked"]:
            raise HTTPException(status_code=403, detail="Cuenta bloqueada.")
        lines = cart_lines(request)
        if not lines:
            raise HTTPException(status_code=400, detail="El carrito está vacío.")
        if delivery_mode not in ("delivery", "pickup"):
            raise HTTPException(status_code=400, detail="Modo de entrega inválido.")
        chosen_address = None
        if delivery_mode == "delivery":
            if not address_id.isdigit():
                raise HTTPException(status_code=400, detail="Selecciona una dirección de entrega.")
            with conn() as connection:
                chosen_address = connection.execute(
                    "SELECT * FROM addresses WHERE id = ? AND customer_id = ?",
                    (int(address_id), customer["id"]),
                ).fetchone()
            if chosen_address is None:
                raise HTTPException(status_code=400, detail="Dirección no encontrada.")
        elif pickup_store not in PICKUP_STORES:
            raise HTTPException(status_code=400, detail="Selecciona un local de retiro.")
        subtotal = sum(line["line_total"] for line in lines)
        points = subtotal // 1000
        timestamp = db.now_iso()
        with conn() as connection:
            for line in lines:
                stock = connection.execute("SELECT stock FROM products WHERE id = ?",
                                           (line["product"]["id"],)).fetchone()["stock"]
                if line["quantity"] > stock:
                    raise HTTPException(status_code=409, detail="Stock insuficiente.")
            cursor = connection.execute(
                "INSERT INTO orders (customer_id, status, delivery_mode, address_id, pickup_store, subtotal_clp, "
                "points_earned, created_at) VALUES (?, 'pending', ?, ?, ?, ?, ?, ?)",
                (customer["id"], delivery_mode, chosen_address["id"] if chosen_address else None,
                 pickup_store if delivery_mode == "pickup" else None, subtotal, points, timestamp),
            )
            order_id = cursor.lastrowid
            for line in lines:
                connection.execute(
                    "INSERT INTO order_items (order_id, product_id, quantity, unit_price_clp) VALUES (?, ?, ?, ?)",
                    (order_id, line["product"]["id"], line["quantity"], line["product"]["price_clp"]),
                )
                connection.execute("UPDATE products SET stock = stock - ? WHERE id = ?",
                                   (line["quantity"], line["product"]["id"]))
            connection.execute(
                "INSERT INTO points_ledger (customer_id, order_id, points, reason, created_at) "
                "VALUES (?, ?, ?, 'purchase', ?)",
                (customer["id"], order_id, points, timestamp),
            )
        return cart_response(RedirectResponse(f"/orders/{order_id}", status_code=303), {})

    @app.get("/orders", response_class=HTMLResponse)
    def orders(request: Request):
        customer = require_customer(request)
        with conn() as connection:
            rows = connection.execute(
                "SELECT * FROM orders WHERE customer_id = ? ORDER BY id DESC", (customer["id"],)
            ).fetchall()
        return render(request, "orders.html", orders=rows)

    def load_order(connection, order_id: int, customer_id: int):
        order = connection.execute(
            "SELECT * FROM orders WHERE id = ? AND customer_id = ?", (order_id, customer_id)
        ).fetchone()
        if order is None:
            raise HTTPException(status_code=404, detail="Pedido no encontrado.")
        items = connection.execute(
            "SELECT oi.*, p.name FROM order_items oi JOIN products p ON p.id = oi.product_id "
            "WHERE oi.order_id = ?", (order_id,)
        ).fetchall()
        return order, items

    @app.get("/orders/{order_id}", response_class=HTMLResponse)
    def order_detail(request: Request, order_id: int):
        customer = require_customer(request)
        with conn() as connection:
            order, items = load_order(connection, order_id, customer["id"])
        return render(request, "order.html", order=order, items=items)

    @app.post("/orders/{order_id}/pay")
    async def order_pay(request: Request, order_id: int):
        customer = require_customer(request)
        if customer["blocked"]:
            raise HTTPException(status_code=403, detail="Cuenta bloqueada.")
        form = await request.form()
        forbidden = {"card_number", "pan", "cvv", "cvc", "security_code"}
        if forbidden & set(form.keys()):
            raise HTTPException(status_code=400, detail="No se aceptan datos de tarjeta; usa el pago simulado.")
        with conn() as connection:
            order, _ = load_order(connection, order_id, customer["id"])
            if order["status"] != "pending":
                raise HTTPException(status_code=409, detail="El pedido ya fue pagado.")
            connection.execute(
                "UPDATE orders SET status = 'paid', payment_token = ? WHERE id = ?",
                (f"SIM-{uuid.uuid4().hex[:12].upper()}", order_id),
            )
        return RedirectResponse(f"/orders/{order_id}", status_code=303)

    @app.get("/privacy", response_class=HTMLResponse)
    def privacy(request: Request):
        return render(request, "privacy.html")

    @app.get("/privacy/third-parties", response_class=HTMLResponse)
    def third_parties(request: Request):
        with conn() as connection:
            rows = connection.execute("SELECT * FROM third_parties ORDER BY name").fetchall()
        return render(request, "third_parties.html", third_parties=rows)

    @app.get("/cookies", response_class=HTMLResponse)
    def cookies_page(request: Request):
        return render(request, "cookies.html", prefs=read_cookie_prefs(request) or {})

    @app.post("/cookies")
    def cookies_save(
        request: Request,
        functionality: str | None = Form(None),
        performance: str | None = Form(None),
        targeting: str | None = Form(None),
    ):
        prefs = {
            "necessary": True,
            "functionality": bool(functionality),
            "performance": bool(performance),
            "targeting": bool(targeting),
        }
        customer = session_customer(request)
        if customer is not None:
            with conn() as connection:
                connection.execute(
                    "INSERT INTO cookie_consents (customer_id, necessary, functionality, performance, targeting, "
                    "recorded_at) VALUES (?, 1, ?, ?, ?, ?)",
                    (customer["id"], int(prefs["functionality"]), int(prefs["performance"]),
                     int(prefs["targeting"]), db.now_iso()),
                )
        response = RedirectResponse("/cookies", status_code=303)
        response.set_cookie("cookie_prefs", signer.dumps(prefs), httponly=True, samesite="lax", max_age=31_536_000)
        return response

    @app.post("/cookies/necessary")
    def cookies_necessary():
        prefs = {"necessary": True, "functionality": False, "performance": False, "targeting": False}
        response = RedirectResponse("/", status_code=303)
        response.set_cookie("cookie_prefs", signer.dumps(prefs), httponly=True, samesite="lax", max_age=31_536_000)
        return response

    @app.get("/consent/marketing", response_class=HTMLResponse)
    def marketing_page(request: Request):
        customer = require_customer(request)
        with conn() as connection:
            active = connection.execute(
                "SELECT * FROM consents WHERE customer_id = ? AND withdrawn_at IS NULL ORDER BY id DESC",
                (customer["id"],),
            ).fetchone()
        return render(request, "marketing.html", active=active)

    @app.post("/consent/marketing/grant")
    def marketing_grant(request: Request):
        customer = require_customer(request)
        with conn() as connection:
            connection.execute(
                "INSERT INTO consents (customer_id, purpose, policy_version, granted_at) VALUES (?, 'marketing', ?, ?)",
                (customer["id"], POLICY_VERSION, db.now_iso()),
            )
            connection.execute("UPDATE customers SET marketing_opt_in = 1, updated_at = ? WHERE id = ?",
                               (db.now_iso(), customer["id"]))
        return RedirectResponse("/consent/marketing", status_code=303)

    @app.post("/consent/marketing/withdraw")
    def marketing_withdraw(request: Request):
        customer = require_customer(request)
        with conn() as connection:
            connection.execute(
                "UPDATE consents SET withdrawn_at = ? WHERE customer_id = ? AND withdrawn_at IS NULL",
                (db.now_iso(), customer["id"]),
            )
            connection.execute("UPDATE customers SET marketing_opt_in = 0, updated_at = ? WHERE id = ?",
                               (db.now_iso(), customer["id"]))
        return RedirectResponse("/consent/marketing", status_code=303)

    @app.get("/rights", response_class=HTMLResponse)
    def rights_page(request: Request):
        customer = require_customer(request)
        with conn() as connection:
            rows = connection.execute(
                "SELECT * FROM rights_requests WHERE customer_id = ? ORDER BY id DESC", (customer["id"],)
            ).fetchall()
        return render(request, "rights.html", rights=rows, right_types=RIGHT_TYPES)

    @app.post("/rights")
    def rights_create(request: Request, right_type: str = Form("access"), notes: str = Form("")):
        customer = require_customer(request)
        if right_type not in RIGHT_TYPES:
            raise HTTPException(status_code=400, detail="Derecho inválido.")
        with conn() as connection:
            create_right(connection, customer["id"], right_type, notes)
        return RedirectResponse("/rights", status_code=303)

    @app.get("/me/data", response_class=HTMLResponse)
    def me_data(request: Request):
        customer = require_customer(request)
        with conn() as connection:
            addresses = connection.execute("SELECT * FROM addresses WHERE customer_id = ?",
                                           (customer["id"],)).fetchall()
            orders = connection.execute("SELECT * FROM orders WHERE customer_id = ? ORDER BY id DESC",
                                        (customer["id"],)).fetchall()
            rights = connection.execute("SELECT * FROM rights_requests WHERE customer_id = ? ORDER BY id DESC",
                                        (customer["id"],)).fetchall()
            consents = connection.execute("SELECT * FROM consents WHERE customer_id = ? ORDER BY id DESC",
                                          (customer["id"],)).fetchall()
            points = connection.execute(
                "SELECT COALESCE(SUM(points), 0) AS total FROM points_ledger WHERE customer_id = ?",
                (customer["id"],),
            ).fetchone()["total"]
        return render(request, "me_data.html", customer=customer, addresses=addresses, orders=orders,
                      rights=rights, consents=consents, points=points)

    @app.get("/me/export")
    def me_export(request: Request):
        customer = require_customer(request)
        with conn() as connection:
            addresses = [dict(row) for row in connection.execute(
                "SELECT label, line1, commune, city FROM addresses WHERE customer_id = ?", (customer["id"],))]
            orders = [dict(row) for row in connection.execute(
                "SELECT id, status, delivery_mode, subtotal_clp, points_earned, created_at FROM orders "
                "WHERE customer_id = ? ORDER BY id", (customer["id"],))]
            consents = [dict(row) for row in connection.execute(
                "SELECT purpose, policy_version, granted_at, withdrawn_at FROM consents WHERE customer_id = ?",
                (customer["id"],))]
        payload = {
            "customer": {"rut": customer["rut"], "email": customer["email"], "phone": customer["phone"],
                         "full_name": customer["full_name"]},
            "addresses": addresses,
            "orders": orders,
            "consents": consents,
        }
        return Response(
            content=json.dumps(payload, ensure_ascii=False),
            media_type="application/json",
            headers={"Content-Disposition": 'attachment; filename="mis-datos.json"'},
        )

    @app.post("/me/update")
    def me_update(request: Request, phone: str = Form(""), full_name: str = Form("")):
        customer = require_customer(request)
        with conn() as connection:
            connection.execute(
                "UPDATE customers SET phone = ?, full_name = ?, updated_at = ? WHERE id = ?",
                (phone.strip() or None, full_name.strip() or None, db.now_iso(), customer["id"]),
            )
            create_right(connection, customer["id"], "rectification", "Actualización de contacto")
        return RedirectResponse("/account", status_code=303)

    @app.post("/me/delete")
    def me_delete(request: Request):
        customer = require_customer(request)
        with conn() as connection:
            create_right(connection, customer["id"], "erasure")
        return RedirectResponse("/rights", status_code=303)

    @app.post("/me/opposition")
    def me_opposition(request: Request):
        customer = require_customer(request)
        with conn() as connection:
            create_right(connection, customer["id"], "opposition")
        return RedirectResponse("/rights", status_code=303)

    @app.post("/me/block")
    def me_block(request: Request):
        customer = require_customer(request)
        with conn() as connection:
            create_right(connection, customer["id"], "block")
        return RedirectResponse("/rights", status_code=303)

    @app.get("/health")
    def health():
        return JSONResponse({"status": "ok", "policy_version": POLICY_VERSION})

    return app


app = create_app()
