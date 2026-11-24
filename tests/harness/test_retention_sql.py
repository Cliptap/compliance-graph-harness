"""Raw SQL inside a Python string must reach the retention detector.

The ORM analysis only sees ``session.delete(...)`` style calls. A ``DELETE FROM orders`` executed
through a driver is the same destructive operation and was invisible before this check.
"""
from __future__ import annotations

from pathlib import Path

from src.harness.catalog import load_catalog
from src.harness.catalog_engine import CatalogEngine
from src.harness.contracts import TaskSpec

ROOT = Path(__file__).resolve().parents[2]
ENGINE = CatalogEngine(load_catalog(ROOT / ".harness" / "packs" / "catalog.full.json"),
                       include_legacy=False)
SPEC = TaskSpec(task_id="retention", goal="retention", allowed_paths=["*"], forbidden_paths=[])


def ids(code: str) -> set[str]:
    return {finding.policy_id for finding in ENGINE.evaluate(SPEC, {"app/main.py": code})}


def test_raw_sql_delete_in_python_is_flagged():
    code = (
        "def purge(connection, order):\n"
        "    connection.execute(\"DELETE FROM orders WHERE id = ?\", (order['id'],))\n"
        "    return 1\n"
    )
    assert "v2.billing_retention" in ids(code)


def test_raw_sql_delete_after_the_retention_window_is_clean():
    code = (
        "from datetime import timedelta\n\n\n"
        "def purge(connection, order):\n"
        "    cutoff = timedelta(days=2190)\n"
        "    connection.execute(\"DELETE FROM orders WHERE created_at < ?\", (cutoff,))\n"
    )
    assert "v2.billing_retention" not in ids(code)


def test_raw_sql_delete_of_a_customer_is_flagged():
    code = (
        "def purge(connection, customer):\n"
        "    connection.execute('DELETE FROM customers WHERE id = ?', (customer['id'],))\n"
    )
    assert "v2.customer_hard_delete" in ids(code)


def test_a_select_is_not_a_delete():
    code = (
        "def read(connection, order):\n"
        "    return connection.execute('SELECT * FROM orders WHERE id = ?', (order['id'],))\n"
    )
    assert "v2.billing_retention" not in ids(code)
