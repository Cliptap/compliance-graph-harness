"""Interprocedural effect summary: which parameter reaches a sink.

These tests pin the fixpoint semantics of ``_call_effects``. The function used to
re-run every iteration because it marked ``changed`` even when a set did not
grow; that cost ~250 s per control on a 3 000-line module. Convergence must stay
correct while stopping at the first pass without growth.
"""
from __future__ import annotations

import ast
from pathlib import Path

from src.harness import policy_families as pf
from src.harness.catalog import load_catalog

ROOT = Path(__file__).resolve().parents[2]
CATALOG = load_catalog(ROOT / ".harness" / "packs" / "catalog.full.json")
CATEGORIES = {"IDENTIFIER_RUT"}


def _effects(code: str):
    tree = ast.parse(code)
    summaries = pf._function_summaries(tree, CATALOG, CATEGORIES)
    return pf._call_effects(tree, CATALOG, CATEGORIES, summaries)


def test_param_return_propagates_through_one_hop():
    code = (
        "def inner(value):\n"
        "    return value\n"
    )
    param_returns, _, _, _ = _effects(code)
    assert param_returns["inner"] == {0, "value"}


def test_param_return_propagates_transitively():
    code = (
        "def inner(value):\n"
        "    return value\n"
        "\n"
        "def outer(value):\n"
        "    return inner(value)\n"
    )
    param_returns, _, _, _ = _effects(code)
    assert param_returns["inner"] == {0, "value"}
    assert param_returns["outer"] == {0, "value"}


def test_param_log_maps_the_sink_argument_position():
    code = (
        "def audit(org, key):\n"
        "    logger.info('audit %s %s', org, key)\n"
    )
    _, param_logs, _, _ = _effects(code)
    assert param_logs["audit"] == {0, "org", 1, "key"}


def test_function_without_sink_reports_no_effect():
    code = (
        "def inner(value):\n"
        "    return 42\n"
        "\n"
        "def outer(value):\n"
        "    return inner(value)\n"
    )
    param_returns, param_logs, param_responses, param_redirects = _effects(code)
    assert param_returns == {"inner": set(), "outer": set()}
    assert param_logs == {"inner": set(), "outer": set()}
    assert param_responses == {"inner": set(), "outer": set()}
    assert param_redirects == {"inner": set(), "outer": set()}
