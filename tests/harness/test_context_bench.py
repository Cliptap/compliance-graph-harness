from pathlib import Path

import pytest

from harness.eval.context_bench import (
    evaluate, gold_files, native_context_retriever, native_graph_retriever, resolve_module, seed_only, seeds,
)
from src.harness.graph_engine import resolve_symbol_file

ROOT = Path(__file__).resolve().parents[2]


def test_resolve_symbol_file_maps_import_symbols_to_defining_modules():
    assert resolve_symbol_file("symbol::src.database.models.Appointment", ROOT) == "src/database/models.py"
    assert resolve_symbol_file("symbol::src.database.database.get_db", ROOT) == "src/database/database.py"
    assert resolve_symbol_file("symbol::fastapi.APIRouter", ROOT) is None


def test_gold_is_independent_and_includes_seed_and_local_imports():
    gold = gold_files(ROOT, "src/backend/api/appointments.py")
    assert {"src/backend/api/appointments.py", "src/database/models.py", "src/database/repository.py"} <= gold
    assert resolve_module(ROOT, "src.nope.Missing") is None


@pytest.fixture(scope="module")
def results():
    return {
        "seed": evaluate(ROOT, seed_only),
        "slice": evaluate(ROOT, native_graph_retriever(ROOT, 1)),
        "context": evaluate(ROOT, native_context_retriever(ROOT, 1)),
    }


def test_benchmark_has_tasks(results):
    assert results["seed"]["tasks"] == len(seeds(ROOT)) >= 5


def test_context_files_beats_importer_attributed_slice_on_recall_and_precision(results):
    assert results["context"]["mean_recall"] > results["slice"]["mean_recall"]
    assert results["context"]["mean_precision"] > results["slice"]["mean_precision"]
    assert results["context"]["mean_returned"] < results["slice"]["mean_returned"]


def test_context_files_never_returns_sibling_files_that_only_share_dependencies(results):
    assert results["context"]["mean_precision"] == 1.0
