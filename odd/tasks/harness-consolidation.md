# Feature: harness-consolidation
Objective: consolidate an independent, refined harness (Ley N° 21.719 compliance, context, skills) and validate it with a measurable harness vs no-harness experiment on a real repository.
Branch: `feat/cursor-sdk-pilot` until T1 opens its own branch. Delivery: ask-on-risk. Test runner: `python -m pytest tests -q -p no:cacheprovider`.

## Specs

- **S0 — Mine Gentle-AI source.** "creo que estamos cometiendo un error al comparar la instalacion actual de gentle-ai con sus supuestas capacidades, en vez de tomar directamente el codigo fuente, ya que podriamos extraer piezas muy valiosas para cada parte". Source cloned (authorized) at `C:\Users\andre\Documents\VSC Projects\gentle-ai-src`. Output: an extraction map (adopt / adapt / discard per sprint step, with `path:line` evidence).
- **S0b — Context layer comparison.** "creo que deberíamos considerar comparar codegraph con graphify."
- **S1 — Independence and differentiators.** "necesito que mi harness sea independiente, aunque el hallazgo de Gentle AI servirá de mucha ayuda para nutrir el proyecto con sus caracteristicas. No quiero que sea una copia calcada, quiero que el factor diferenciador sea tanto la validacion objetiva y academica como la nueva dimension normativa respecto a la ley 21719 entre otras normativas."
- **S2 — Clean up the broken harness.** "aún seguimos teniendo un harness roto en vibecoding, debemos ordenar, limpiar e implementar muchas cosas aún ya que tu subagente explorador encontro muchas falencias". Deletions or moves require an explicit keep/move/delete list approved by the user first.
- **S3 — Sprint goal.** "El objetivo de este sprint es consolidar un harness refinado con las capacidades al menos de abarcar la ley de proteccion de datos, contexto, skills, y luego probarlo/validarlo usandolo para crear un repositorio real, ese experimento debe ser medible y comprobable y deberemos recopilar metricas usando el harness vs sin usar el harness."
- **S4 — Metrics (verbatim list).** "(Eficiencia) Tiempo de ciclo; Latencia; Número de iteraciones; Cantidad de tokens utilizados, cuando pueda medirse de forma reproducible. (Calidad) Pruebas aprobadas; Defectos introducidos; Cambios no solicitados; Líneas de código modificadas. (Gobernanza) Violaciones de políticas; Violaciones de alcance; Violaciones arquitectónicas; Hallazgos de privacidad y cumplimiento normativo (Ley N° 21.719 / CWE-532); Índice o puntaje de cumplimiento (compliance score) alcanzado en el loop agéntico. (Contexto) Cantidad de archivos recuperados; Cantidad de símbolos recuperados; Tokens de contexto; Proporción de contexto considerado relevante. (Esfuerzo de revisión) Cambios manuales posteriores; Número de correcciones requeridas; Tiempo humano de revisión."
- **S5 — Constraint: pipeline skills belong to a teammate.** "en paralelo tengo a un compañero trabajando en la redaccion de las 12 skills ya que actualmente solo la primera del prd esta redactada analiticamente en "vibecoding", en la branch https://github.com/Cliptap/compliance-graph-harness/tree/refactor/skills-refinement, se han subido 2 skills más pero aún no esta completo el trabajo asi que no merece la pena revisarlo ni considerarlo por ahora". Do not edit `.agents/skills/01-prd` … `12-documentation`; do not review that branch.

## Tasks

| ID | Specs | Step | Route | Status | Evidence |
|---|---|---|---|---|---|
| T0 | S0, S0b | Extraction map from Gentle-AI source + CodeGraph vs graphify | delegated: 4 read-only explorers (Mapping trigger: ~2,200 files) | done | `docs/research/gentle-ai-extraction-map.md`; parent spot checks: `bench/README.md:260-263`, `organic-rdd.md:8,28`, `orchestrator.go:251`, graphify labels 590/1223 with `()` |
| T1 | S2, S5 | Repo cleanup: single harness source, app/harness separation, broken refs, requirements, rule contradictions | inline | pending (needs keep/move/delete approval) | |
| T2 | S1 | Normative pack format (law → article → control → detection → remediation → evidence); migrate the 14 rules | inline | pending | |
| T3 | S1, S4 | Real detection (AST/Semgrep), API personal-data exposure, written compliance score formula | inline | pending | |
| T4 | S1, S4 | Detector validation on a labelled corpus (precision/recall) | inline | pending | |
| T5 | S1, S5 | Ley 21.719 skills for new-dev / audit / patch modes reusing `compliance_check` (not the 12 pipeline skills) | inline | pending | |
| T6 | S3 | Context and memory: graph symbol slicing fix (or CodeGraph per T0), Engram integration | inline | pending | |
| T7 | S3, S4 | Formal experiment: tasks with seeded privacy traps, hidden acceptance tests, preregistration, N from measured cost; resolve task 02 `practitioner_id` scope conflict | inline | pending | |

## Log

- **L1 (2026-10-21, user):** sprint request and metric list (quoted in S3, S4).
- **L2 (2026-10-21, user):** independence decision (quoted in S1); runtime is Cursor Pro via the SDK (pilot in `odd/tasks/cursor-sdk-pilot.md`).
- **L3 (2026-10-21, user):** "estoy de acuerdo con el plan" (steps 0-7), clone authorized at `C:\Users\andre\Documents\VSC Projects` (folder `gentle-ai-src`, because `gentle-ai` collides case-insensitively with the `Gentle-AI` workspace on Windows); S0b and S5 added.
- **L4 (2026-10-21):** Engram mirror pending (server rejects project `compliance-graph-harness` as unknown from this workspace).
- **L5 (2026-10-21):** T0 done. Decisions proposed by the map (not yet approved): render harness prompts from one source in `harness/`; CodeGraph for agent retrieval + own AST graph for lineage; compliance receipt per change (5-module subset); publish compliance score only with its components. Inventory for T1: tracked `.agents` 341 files, `harness` 57; ignored local `legacy/` 3,589 files, `qa_reports/_workspace/` 12,163, `graphify-out/` 393, `scratch/` 2; `.agent/` junctions resolve to 0 files after the repo move.
