# Compliance Graph Harness

Harness de desarrollo y auditoría para la **Ley 21.719** (Chile): reglas y skills para el agente,
un catálogo de 37 controles, una compuerta estática de cumplimiento y un registro de evidencia
(RoPA, paquete por titular, incidentes).

> **Estado:** prototipo de investigación y herramienta técnica. No es asesoría legal ni una
> certificación de cumplimiento. Un gate limpio no prueba cumplimiento: los controles documentales y
> contractuales quedan fuera del código.

## Qué incluye

| Componente | Dónde | Qué hace |
|---|---|---|
| Reglas y skills | `.agents/`, `AGENTS.md` | 12 skills de pipeline + 3 de compliance, reglas always-on y agentes delegados |
| Catálogo normativo | `.harness/packs/` | 37 controles (21 con detector, 16 gaps declarados) mapeados a ley, ISO y CWE |
| Compuerta | `src/harness/precommit.py` | Analiza el cambio y bloquea violaciones de privacidad y credenciales |
| Evidencia | `src/harness/antecedentes.py` | Mapa de datos, registro de procesamiento, paquete por titular e incidentes |
| Contexto estructural | `src/harness/graph_engine.py`, `data_lineage.py` | Grafo de dependencias, linaje y flujo de datos |
| Experimentos | `experiments/`, `qa_reports/` | Banco de tareas, runner de brazos y resultados reproducibles |
| Instalador de IDE | `harness/install.ps1`, `harness/install.sh` | Copia reglas, skills y agentes a OpenCode, Claude Code, Cursor o Antigravity |

## Inicio rápido

Requisitos: Python 3.12+ y Git. Docker es opcional y solo para la aplicación de demostración.

### Windows

```powershell
git clone https://github.com/Cliptap/compliance-graph-harness.git
cd compliance-graph-harness
.\install.ps1
```

### Linux / macOS

```bash
git clone https://github.com/Cliptap/compliance-graph-harness.git
cd compliance-graph-harness
./install.sh
```

El instalador crea `.venv`, instala el paquete en modo editable, copia `.env.example` a `.env` si
falta y ejecuta el doctor. Verificá el entorno con:

```powershell
harness-doctor
```

## Uso

### Compuerta de cumplimiento

```powershell
compliance-check --files src\harness\doctor.py
compliance-check --install        # hook de pre-commit (opcional)
```

Sin `--files`, evalúa los archivos en stage. El reporte indica política, archivo, línea, severidad y
control asociado. La compuerta es una red de seguridad, no la política completa.

### Evidencia y auditoría

```powershell
harness-antecedentes register --root . --scan src
harness-antecedentes subject --root . --scan src --field email
harness-antecedentes incident --list
```

`register` produce un borrador de RoPA; `subject` ubica un dato, sus flujos, consentimientos y
destinatarios; `incident` mantiene el registro de vulneraciones. El register y el subject comparten
la misma fuente de destinatarios.

### Reglas y skills en el IDE

```powershell
.\harness\install.ps1
```

El instalador pregunta IDE, tipo de proyecto y gobernanza. Es independiente del paquete Python: copia
la estructura nativa (`AGENTS.md`, `CLAUDE.md`, `.cursor/rules/` o `.agents/skills/`).

## Estructura

```text
src/harness/        motor: gate, catálogo, evidencia, grafo, linaje
.harness/packs/     catálogo de controles y pack normativo
.agents/            reglas, skills, agentes y hooks
harness/            instalador multi-IDE (PowerShell/bash)
experiments/        banco de tareas, armas y runner
qa_reports/         resultados experimentales
docs/               informe, definición del proyecto e investigación
tests/              suite de 400+ pruebas
```

La aplicación clínica de demostración vive en `src/backend/`, `src/database/` y `src/frontend/`.
Los archivos `Dockerfile` y `docker-compose.yml` de la raíz corresponden a esa demo, no al harness.

## Resultados

- **Calibración ciega del gate** (7 controles v2): ronda 1 pre-fix 26/36; ronda 2 post-fix 37/42,
  precisión 0.944 [0.742, 0.990], recall 0.810 [0.600, 0.923]. Detalle y límites en
  `docs/research/gate-calibration.md`.
- **Bloque D** (10 trampas, 3 repeticiones, 2 brazos): 30/30 hidden en ambos brazos; el harness no
  mejora la corrección funcional en tareas que el modelo ya resuelve y cuesta ~2.5x el ciclo. Detalle
  en `docs/research/d-block-protocol-results.md`.
- **Dose** (5 brazos, 4 tareas): 8/0 pares discordantes a favor de `rules_skills_gate`, p=0.0078.

## Reproducibilidad

```powershell
python -m pytest tests/harness -q
python harness/eval/catalog_corpus.py
python harness/eval/catalog_corpus.py --corpus harness/eval/catalog_corpus_heldout.json --out qa_reports/catalog-corpus/heldout_metrics.json
```

La suite completa incluye la aplicación de demostración y requiere las dependencias de la app:

```powershell
python -m pip install -r requirements.txt -r requirements-dev.txt
python -m pytest tests -q
```

El runner experimental (`experiments/tasks/opencode_run.py`) requiere credenciales del proveedor y
no forma parte de la CI.

## Documentación

- `docs/`: definición del proyecto, informe acumulativo y notas de investigación.
- `docs/research/gate-calibration.md`: calibración ciega del gate.
- `docs/research/d-block-protocol-results.md`: bloque D y desviaciones del instrumento.
- `harness/README.md`: instalador multi-IDE.

## Seguridad y ética

- No commitees `.env`, claves, bases de datos ni datos personales. Usá `.env.example`.
- Los reportes y issues deben redactar RUT, correos, teléfonos y cualquier dato real.
- Para vulnerabilidades, seguí `SECURITY.md`.

## Licencia

MIT. Ver `LICENSE`.
