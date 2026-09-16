# CI/CD — Iteración 4: Trazabilidad Alta Gobernanza

> **Fecha:** 2026-06-11

## Decisión

El PRD 04 no requiere CI/CD. El proyecto usa Docker Compose local. Se mantiene el pipeline manual actual: `docker compose up --build`.

Si en el futuro se requiere CI/CD, el pipeline mínimo sería:
```
[lint: ruff] → [test: pytest --cov] → [build: docker compose build]
```
