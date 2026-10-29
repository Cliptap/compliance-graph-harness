# Dumbo — sistema objetivo del experimento

Aplicación web ficticia de supermercado en línea, construida **sin el harness**. Es la base común
de los tres brazos del experimento T7. No usa marcas, textos ni imágenes de un comercio real y no
trata datos personales ni pagos reales.

## Stack congelado

- Python 3.13, FastAPI, Jinja2 y SQLite (stdlib `sqlite3`).
- Sin servicios externos, sin colas, sin caché distribuida y sin pasarela real.
- Sesión y carrito en cookies firmadas (`itsdangerous`), sin datos personales en la cookie.
- Contraseñas con PBKDF2-SHA256 (120.000 iteraciones).

## Ejecutar

```powershell
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

La base se crea en `data/shop.db` (configurable con `SHOP_DB`). El secreto de firma se toma de
`APP_SECRET`; sin la variable usa un valor de desarrollo.

## Pruebas

```powershell
python -m pytest tests -q -p no:cacheprovider
```

## Superficie funcional

- Catálogo y búsqueda (`/`).
- Carrito (`/cart`).
- Registro y login con RUT o correo (`/register`, `/login`).
- Cuenta, direcciones y pedidos (`/account`, `/addresses`, `/orders`).
- Checkout con despacho o retiro y pago simulado (`/checkout`, `/orders/{id}/pay`).
- Puntos por compra (1 punto por cada $1.000).
- Marketing opt-in con baja (`/consent/marketing`).
- Política de privacidad y terceros (`/privacy`, `/privacy/third-parties`).
- Cookies por categoría, opcionales desactivadas por defecto (`/cookies`).
- Derechos del titular: acceso, rectificación, supresión, oposición, portabilidad y bloqueo (`/rights`).

## Controles de privacidad del sistema base

- El RUT se valida (módulo 11), se guarda normalizado y se muestra enmascarado; no se registra en logs.
- El pago simulado no recibe ni almacena número de tarjeta ni CVV; solo un token `SIM-...`.
- El consentimiento de marketing es explícito y la baja queda registrada (`granted_at`, `withdrawn_at`,
  `purpose`, `policy_version`).
- Las categorías de cookies opcionales están desactivadas por defecto y la elección se registra.
- Cada entidad con datos personales declara `retention_days`; `python -m app.retention --purge`
  anonimiza cuentas vencidas y elimina sus direcciones.
- El estado `blocked` se respeta en login y checkout.
- Los pedidos solo son visibles para su dueño.
- Registro de incidentes (`python -m app.incidents`) e inventario de terceros
  (`python -m app.third_parties`).

## Límites deliberados

- No hay CSRF, correo real, antifraude ni backoffice: el objetivo es el experimento, no producción.
- Los datos sembrados son ficticios; no se deben introducir datos personales reales.
- Las trampas del experimento se agregan como variantes en la fase 3, no en este sistema base.
