# Blind author pack - v2 gate controls

You are writing a held-out evaluation set. Do **not** read the detector source, the curated
corpora, the gate output, or the test suite. Use only the definitions and rules below.

## Output format

Return one JSON object:

```json
{
  "version": 1,
  "description": "Blind held-out round 1",
  "cases": [
    {
      "id": "short_unique_id",
      "control": "v2.log_pii",
      "expected": "violation",
      "path": "app/module.py",
      "code": "def f(customer):\n    ...\n"
    }
  ]
}
```

Requirements:

- At least **5 cases per control** (7 controls, 35+ total).
- Each control must have **at least 2 `violation` and 2 `clean`** cases.
- `id` unique; `path` under `app/`; `code` valid Python (it must parse).
- Vary the code shape: functions, methods, classes, decorators, dict/attribute access, f-strings,
  SQL/ORM calls. Do not copy the same snippet with one renamed field.
- Clean cases must be realistic near-misses, not trivial no-ops.
- If a case is ambiguous, **exclude it**; do not guess.

## Control definitions

### v2.log_pii - personal data written to logs

Violation: a log or telemetry statement writes a personal identifier in clear text. Personal
identifiers for this control: RUT/run/DNI, email, phone, home address.
Clean: the value is masked, hashed, fingerprinted or aggregated; or the logged value is a
non-personal identifier such as an order id, request id or internal record id.

### v2.admin_exposure - unmasked personal data in an admin response

Violation: an admin-facing endpoint returns a personal identifier (RUT, email, phone, address) in
clear text.
Clean: the admin response masks the value, or projects only safe fields; or the route is the
subject's own self-service route, not an admin route.

### v2.credential_response - credential exposed in a response

Violation: a response returns a credential or credential-derived secret in clear text: password,
password hash, secret, API key, private key.
Clean: the response does not contain any credential field; it returns only non-credential fields.

### v2.customer_hard_delete - customer hard delete inside retention

Policy: customer records have a 730-day retention. A hard delete before that window is a violation.
Violation: `DELETE FROM customers` (or an ORM hard delete) without a retention guard.
Clean: soft delete or anonymisation; or a hard delete gated on a retention window of at least 730
days.

### v2.billing_retention - billing records deleted before retention

Policy: orders and invoices must be kept for 2190 days (6 years) for tax purposes.
Violation: a delete of orders or invoices with a cutoff shorter than 2190 days.
Clean: a delete whose cutoff is at least 2190 days; or no delete at all.

### v2.reset_token - password-reset token returned to the client

Violation: the password-reset token appears in a response body, a redirect URL, or a log.
Clean: the token is sent only out-of-band (email/SMS) and the response is generic (for example
"if the account exists, an email was sent"); or the response contains no token.

### v2.api_key - API key or secret returned to the client

Violation: an API key or secret appears in a response, redirect or log.
Clean: the response exposes only a boolean/configuration flag, a masked suffix, or no secret.

## Labeling rules

- Label the **named control only**. A case may also violate another control; that does not change
  the label for the named one.
- Judge the code as written; do not assume a sanitizer exists if it is not called.
- A field name alone is not a violation: the value must be exposed. For example, a response with a
  `password_hash` key whose value is the stored hash **is** a violation; a response with a boolean
  `api_key_configured` flag is clean.
- Prefer explicit code over prose in comments. Comments must not state the label.
