from pathlib import Path

from src.harness.catalog import load_catalog
from src.harness.catalog_engine import CatalogEngine
from src.harness.contracts import TaskSpec

CATALOG = Path(__file__).resolve().parents[2] / ".harness" / "packs" / "catalog.v2.json"
ENGINE = CatalogEngine(load_catalog(CATALOG))
SPEC = TaskSpec(task_id="t", goal="g", allowed_paths=["*"], forbidden_paths=[])


def ids(code: str) -> set[str]:
    findings = ENGINE.evaluate(SPEC, {"app/main.py": code})
    return {finding.policy_id for finding in findings}


def test_log_pii_is_flagged():
    code = "def f(customer):\n    logger.info('rut=%s', customer['rut'])\n"
    assert "v2.log_pii" in ids(code)


def test_pseudonymized_log_is_clean():
    code = (
        "def f(customer):\n"
        "    logger.info('rut_fp=%s', _fingerprint(secret, customer['rut']))\n"
    )
    assert "v2.log_pii" not in ids(code)


def test_admin_response_rut_is_flagged():
    code = "def admin_customers(customer):\n    return {'rut': customer['rut']}\n"
    assert "v2.admin_exposure" in ids(code)


def test_self_service_response_is_clean():
    code = "def profile(customer):\n    return {'rut': customer['rut']}\n"
    assert "v2.admin_exposure" not in ids(code)


def test_premature_orders_delete_is_flagged():
    code = (
        "def purge():\n"
        "    cutoff = now() - timedelta(days=90)\n"
        "    db.execute('DELETE FROM orders WHERE created_at < ?', (cutoff,))\n"
    )
    assert "v2.billing_retention" in ids(code)


def test_retention_aware_orders_delete_is_clean():
    code = (
        "def purge():\n"
        "    cutoff = now() - timedelta(days=2190)\n"
        "    db.execute('DELETE FROM orders WHERE created_at < ?', (cutoff,))\n"
    )
    assert "v2.billing_retention" not in ids(code)


def test_customer_hard_delete_is_flagged():
    code = "def purge():\n    db.execute('DELETE FROM customers')\n"
    assert "v2.customer_hard_delete" in ids(code)


def test_reset_token_response_is_flagged():
    code = "def reset():\n    return {'token': uuid.uuid4().hex}\n"
    assert "v2.reset_token" in ids(code)


def test_reset_token_redirect_is_flagged():
    code = "def reset():\n    return RedirectResponse(f'/sent?token={uuid.uuid4().hex}', status_code=303)\n"
    assert "v2.reset_token" in ids(code)


def test_generic_redirect_is_clean():
    code = "def reset():\n    return RedirectResponse('/sent', status_code=303)\n"
    assert "v2.reset_token" not in ids(code)


def test_api_key_response_is_flagged():
    code = "def config():\n    return {'api_key': os.environ['PAYMENTS_API_KEY']}\n"
    assert "v2.api_key" in ids(code)


def test_finding_maps_to_law_iso_and_cwe():
    code = "def f(customer):\n    logger.info('rut=%s', customer['rut'])\n"
    finding = next(f for f in ENGINE.evaluate(SPEC, {"app/main.py": code})
                   if f.policy_id == "v2.log_pii")
    labels = " | ".join(ENGINE.frameworks_for(finding))
    assert "Ley 21.719" in labels
    assert "ISO/IEC 27001:2022 A.8.12" in labels
    assert "CWE CWE-532" in labels

def test_response_variable_with_rut_is_flagged():
    code = (
        "def admin_export(customer):\n"
        "    payload = {'rut': customer['rut']}\n"
        "    return Response(content=json.dumps(payload))\n"
    )
    assert "v2.admin_exposure" in ids(code)


def test_response_variable_masked_is_clean():
    code = (
        "def admin_export(customer):\n"
        "    payload = {'rut': mask_rut(customer['rut'])}\n"
        "    return Response(content=json.dumps(payload))\n"
    )
    assert "v2.admin_exposure" not in ids(code)


def test_dict_row_from_customers_is_flagged():
    code = (
        "def admin_customer(customer_id):\n"
        "    row = db.execute('SELECT * FROM customers WHERE id = ?', (customer_id,)).fetchone()\n"
        "    return dict(row)\n"
    )
    found = ids(code)
    assert "v2.credential_response" in found
    assert "v2.admin_exposure" in found


def test_comprehension_of_customer_rows_is_flagged():
    code = (
        "def admin_customers():\n"
        "    rows = db.execute('SELECT * FROM customers').fetchall()\n"
        "    return [dict(row) for row in rows]\n"
    )
    assert "v2.admin_exposure" in ids(code)
