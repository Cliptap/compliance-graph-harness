# Changelog

Todas las fechas son ISO 8601. El formato sigue Keep a Changelog y el proyecto usa versionado
semántico.

## [Unreleased]

### Agregado

- `harness-doctor` para verificar Python, dependencias, packs, gate y entorno.
- `pyproject.toml` con instalación editable y console scripts (`compliance-check`,
  `harness-antecedentes`, `harness-doctor`).
- `install.ps1` e `install.sh` de un comando, con `.env.example`.
- CI de GitHub Actions (Linux/Windows, Python 3.12/3.13) con doctor, suite y corpus de calibración.
- Templates de issue y pull request.

### Cambiado

- README raíz reescrito para describir el harness, no la aplicación de demostración.
- Referencias de instalación corregidas (`harness/install.ps1`).

### Corregido

- `format_gate_feedback` resolvía el catálogo con el loader del pack normativo y fallaba en la
  primera violación real.
- Register y subject calculaban destinatarios con mecanismos distintos.
- Detectores: `log.*`, contexto admin por clase, `private_key`, máscaras f-string, proyecciones
  booleanas, deletes ORM, intervalos SQL, dumps de objetos, tokens en logs y secretos bajo claves
  genéricas.

### Experimentos

- Bloque D (10 trampas) y comparación `baseline` vs `rules_skills_gate`.
- Calibración ciega del gate: ronda 1 26/36, ronda 2 37/42; ver
  `docs/research/gate-calibration.md`.

## [0.1.0] - 2026-11-22

- Fundación pública del repositorio: harness, catálogo, gate, evidencia, experimentos y
  documentación.
