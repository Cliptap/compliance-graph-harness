"""Context-retrieval benchmark: which files must an agent read before editing a seed file?

Gold for each seed = the seed plus the repository files it imports (1 hop), resolved
by an independent AST pass (not by the graph under test). A retriever receives the seed
file and returns a set of files; we report recall, precision and returned size.
Strategies are pluggable so graphify, the native AST graph and CodeGraph can be compared
on the same tasks. Metrics are reported per strategy, never as a single composite.
"""
from __future__ import annotations

import ast
import tempfile
from pathlib import Path
from typing import Callable

Retriever = Callable[[str], set[str]]


def resolve_module(root: Path, dotted: str) -> str | None:
    """Map `a.b.c` to a repo file (`a/b/c.py` or `a/b/c/__init__.py`), trying parent modules for symbols."""
    parts = dotted.split(".")
    while parts:
        base = root.joinpath(*parts)
        if base.with_suffix(".py").is_file():
            return base.with_suffix(".py").relative_to(root).as_posix()
        if (base / "__init__.py").is_file():
            return (base / "__init__.py").relative_to(root).as_posix()
        parts.pop()
    return None


def gold_files(root: Path, seed: str) -> set[str]:
    tree = ast.parse((root / seed).read_text(encoding="utf-8"))
    gold = {seed}
    for node in ast.walk(tree):
        names: list[str] = []
        if isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            names = [node.module]
        elif isinstance(node, ast.Import):
            names = [a.name for a in node.names]
        for dotted in names:
            if dotted.split(".")[0] == "src":
                found = resolve_module(root, dotted)
                if found:
                    gold.add(found)
    return gold


def seeds(root: Path) -> list[str]:
    return sorted(p.relative_to(root).as_posix() for p in (root / "src/backend/api").glob("*.py")
                  if p.name != "__init__.py")


def evaluate(root: Path, retriever: Retriever) -> dict:
    rows = []
    for seed in seeds(root):
        gold, got = gold_files(root, seed), retriever(seed)
        hit = len(gold & got)
        rows.append({
            "seed": seed, "gold": len(gold), "returned": len(got),
            "recall": hit / len(gold), "precision": hit / len(got) if got else None,
        })
    precisions = [r["precision"] for r in rows if r["precision"] is not None]
    return {
        "tasks": len(rows),
        "mean_recall": sum(r["recall"] for r in rows) / len(rows),
        "mean_precision": sum(precisions) / len(precisions) if precisions else None,
        "mean_returned": sum(r["returned"] for r in rows) / len(rows),
        "rows": rows,
    }


def seed_only(seed: str) -> set[str]:
    return {seed}


def native_graph_retriever(root: Path, depth: int) -> Retriever:
    """Native AST graph + subgraph_slice (no external tools), built once in a temp DB."""
    from src.harness.graph_engine import build_repository_graph, subgraph_slice

    db = Path(tempfile.mkdtemp(prefix="ctxbench_")) / "g.db"
    build_repository_graph(root_dir=root, db_path=db, use_graphify=False)

    def retrieve(seed: str) -> set[str]:
        return set(subgraph_slice(f"file::{seed}", depth=depth, db_path=db)["involved_files"])

    return retrieve


def native_context_retriever(root: Path, depth: int) -> Retriever:
    """Native AST graph + context_files (outgoing imports resolved to defining files)."""
    from src.harness.graph_engine import build_repository_graph, context_files

    db = Path(tempfile.mkdtemp(prefix="ctxbench_")) / "g.db"
    build_repository_graph(root_dir=root, db_path=db, use_graphify=False)
    return lambda seed: context_files(seed, depth=depth, db_path=db, root=root)


def main(root: Path | None = None) -> None:
    root = root or Path(__file__).resolve().parents[2]
    strategies: dict[str, Retriever] = {"seed_only": seed_only}
    for depth in (1, 2):
        strategies[f"native_slice_d{depth}"] = native_graph_retriever(root, depth)
        strategies[f"native_context_d{depth}"] = native_context_retriever(root, depth)
    for name, retriever in strategies.items():
        r = evaluate(root, retriever)
        print(f"{name}: recall={r['mean_recall']:.2f} precision={r['mean_precision']} "
              f"returned={r['mean_returned']:.1f} tasks={r['tasks']}")


if __name__ == "__main__":
    main()
