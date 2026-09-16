---
name: stack-python
type: rule
priority: medium
always_on: true
---

# Reglas Especificas para Python

## Estilo de Codigo

1. **Seguir PEP 8** — maximo 88 caracteres por linea (Black default).
2. **Type hints en TODAS las funciones publicas** — usar `def func(x: int) -> str`.
3. **Docstrings en funciones publicas** — formato Google style o numpy.
4. **Imports ordenados**: stdlib → terceros → locales. Usar `isort` o `ruff`.
5. **No usar `from module import *`** — siempre imports explicitos.

## Estructura

- `pyproject.toml` o `setup.py` en la raiz.
- `requirements.txt` o `pyproject.toml [dependencies]` para dependencias.
- `.venv/` en `.gitignore`.
- `__init__.py` en todos los paquetes.

## Buenas Practicas

- Preferir `pathlib` sobre `os.path`.
- Usar f-strings para interpolacion.
- Usar `dataclasses` o `Pydantic` para estructuras de datos.
- Usar `contextlib` para context managers.
- No usar `except Exception` generico — capturar excepciones especificas.

## Anti-Patrones a Evitar

- Mutables como default arguments: `def f(items=[])` → usar `def f(items=None)`.
- List comprehensions anidadas de mas de 2 niveles.
- `type()` para comparar tipos → usar `isinstance()`.
- Comparar con `True`/`False` con `is` → usar truthiness.
