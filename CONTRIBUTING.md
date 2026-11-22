# Contribuir

Gracias por querer mejorar el Compliance Graph Harness. Este documento describe el entorno, las
pruebas y el flujo de cambios.

## Entorno

```powershell
.\install.ps1          # crea .venv e instala el paquete en modo editable
```

```bash
./install.sh
```

Para correr la suite completa, que incluye la aplicación de demostración:

```powershell
python -m pip install -r requirements.txt -r requirements-dev.txt
```

Verificá el entorno con:

```powershell
harness-doctor
```

## Pruebas

- Antes de abrir un PR: `python -m pytest tests -q`.
- Para un cambio puntual: `python -m pytest tests/harness/test_<area>.py -q`.
- Todo cambio de comportamiento lleva un test que falla antes y pasa después (AAA).
- Todo cambio de cumplimiento normativo lleva un test, además de la evidencia en el informe.

## Estilo

- Python 3.12+, type hints en APIs públicas.
- Funciones cortas y nombres descriptivos; sin números mágicos.
- Sin secretos ni datos personales en código, tests, issues o commits.
- Los detectores y las reglas deben ser deterministas y explicables por control.

## Commits y pull requests

- Commits convencionales (`feat:`, `fix:`, `docs:`, `test:`, `chore:`).
- Sin atribución de IA ni `Co-Authored-By`.
- Un PR por unidad revisable: código y tests juntos; la documentación puede ir en el mismo PR si
  explica el cambio.
- Describí el problema, la solución, las pruebas ejecutadas y las limitaciones.

## Artefactos y datos

No se commitean:

- `.env`, credenciales, claves de API ni bases de datos (`*.db`).
- Workspaces generados (`experiments/tasks/workspaces/`, `qa_reports/_workspace/`).
- Grafos o reportes generados que no sean evidencia deliberada.

Si un reporte experimental es evidencia del informe, va en `qa_reports/` con nombre y fecha, y se
referencia desde `docs/`.

## Experimentos

- Fijá el modelo y la configuración; registrá fecha, arm y tarea.
- No agrupes bloques con instrumentos distintos sin declararlo.
- Los fallos de test o de evidencia se reportan como tales; no se reintentan hasta que "pasen" sin
  documentar la corrección.

## Seguridad

Para vulnerabilidades, seguí `SECURITY.md`; no abras un issue público con datos sensibles.
