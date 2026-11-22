"""Genera las proyecciones del harness por runtime desde una única fuente (`harness/`).

Uso:
    python -m harness.render            # escribe las proyecciones
    python -m harness.render --check    # sale con 1 si alguna proyección difiere de la fuente

Los archivos generados no se editan a mano: se edita la fuente en `harness/` y se vuelve a
renderizar. `tests/harness/test_render.py` falla si el repositorio queda desincronizado.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

PLACEHOLDER = re.compile(rb"\{\{([A-Z0-9_]+)\}\}")


class RenderError(Exception):
    pass


@dataclass(frozen=True)
class Copy:
    source_glob: str
    dest_dir: str


@dataclass(frozen=True)
class Template:
    source: str
    dest: str
    values: dict[str, str] = field(default_factory=dict)


TARGETS: dict[str, tuple[Copy | Template, ...]] = {
    "antigravity": (
        Copy("rules/common/*.md", ".agents/rules"),
        Copy("rules/stacks/*.md", ".agents/rules/stacks"),
        Copy("contexts/*.md", ".agents/contexts/vibecoding"),
        Copy("agents/*.md", ".agents/agents"),
        Copy("hooks/scripts/*.js", ".agents/hooks/scripts"),
        Template("templates/AGENTS.md", "AGENTS.md", {
            "RUNTIME_NAME": "Antigravity",
            "RUNTIME_STRUCTURE": "\n".join((
                "- Skills nativas: `.agents/skills/`",
                "- Agentes delegados: `.agents/agents/`",
                "- Reglas detalladas: `.agents/rules/`",
                "- Hooks de sesión: `.agents/hooks/`",
                "- Estado y Grafos de Cumplimiento: `.harness/`",
            )),
        }),
    ),
}


def plan(root: Path, target: str) -> dict[str, bytes]:
    """Devuelve {ruta destino relativa: bytes} sin escribir nada."""
    source_root = root / "harness"
    outputs: dict[str, bytes] = {}
    for item in TARGETS[target]:
        if isinstance(item, Copy):
            for src in sorted(source_root.glob(item.source_glob)):
                outputs[f"{item.dest_dir}/{src.name}"] = src.read_bytes()
        else:
            outputs[item.dest] = _fill(source_root / item.source, item.values)
    return outputs


def _fill(path: Path, values: dict[str, str]) -> bytes:
    raw = path.read_bytes()
    # Los valores multilínea adoptan el EOL de la plantilla (CRLF tras un checkout con autocrlf).
    newline = "\r\n" if b"\r\n" in raw else "\n"
    encoded = {k: v.replace("\n", newline).encode() for k, v in values.items()}
    data = PLACEHOLDER.sub(lambda m: encoded.get(m.group(1).decode(), m.group(0)), raw)
    missing = sorted({m.decode() for m in PLACEHOLDER.findall(data)})
    if missing:
        raise RenderError(f"placeholders sin resolver en {path.name}: {', '.join(missing)}")
    return data


def render(root: Path, target: str, check: bool = False) -> list[str]:
    """Escribe las proyecciones, o con `check=True` devuelve las que difieren de la fuente."""
    outputs = plan(root, target)
    changed = sorted(rel for rel, data in outputs.items() if _current(root / rel) != data)
    if not check:
        for rel in changed:
            dest = root / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(outputs[rel])
    return changed


def _current(path: Path) -> bytes | None:
    return path.read_bytes() if path.is_file() else None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--target", choices=sorted(TARGETS), default="antigravity")
    parser.add_argument("--root", default=str(Path(__file__).resolve().parents[1]), help="raíz del repositorio")
    parser.add_argument("--check", action="store_true", help="no escribe; falla si hay diferencias")
    args = parser.parse_args(argv)
    try:
        changed = render(Path(args.root), args.target, check=args.check)
    except RenderError as err:
        print(f"ERROR: {err}", file=sys.stderr)
        return 2
    verb = "desincronizado" if args.check else "escrito"
    for rel in changed:
        print(f"{verb}: {rel}")
    return 1 if args.check and changed else 0


if __name__ == "__main__":
    sys.exit(main())
