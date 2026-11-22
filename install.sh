#!/usr/bin/env bash
# Compliance Graph Harness - one-command setup (Linux/macOS)
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

PYTHON="${PYTHON:-python3}"
if [ ! -d .venv ]; then
    echo "Creando .venv..."
    "$PYTHON" -m venv .venv
fi
PY=".venv/bin/python"

"$PY" -m pip install --upgrade pip
"$PY" -m pip install -e ".[dev]"

if [ ! -f .env ] && [ -f .env.example ]; then
    cp .env.example .env
    echo "Creado .env desde .env.example (completa las claves)."
fi

"$PY" -m src.harness.doctor

cat <<'EOF'

Listo. Proximos pasos:
  source .venv/bin/activate
  python -m pytest tests/harness -q
  # suite completa: pip install -r requirements.txt -r requirements-dev.txt; luego pytest tests -q
  compliance-check --files src/harness/doctor.py
  harness-antecedentes register --root . --scan src
  ./harness/install.sh   # opcional: instalar reglas y skills en el IDE
EOF
