# Mapa de extracción: Gentle-AI → harness de cumplimiento

Fuente: `gentle-ai` commit `3604b5e` (licencia MIT), clonado en `C:\Users\andre\Documents\VSC Projects\gentle-ai-src`.
Las rutas `GA:` son relativas a ese clon. Criterio: portar **conceptos y contratos** a Python, no copiar código Go.
Si se copia texto o código literal, conservar el aviso de copyright MIT. "Gentle AI" y "Engram" son marcas registradas.

## Resumen por paso del sprint

| Paso | Adoptar | Adaptar | Descartar |
|---|---|---|---|
| 1. Limpieza y fuente única | Render desde una sola fuente con placeholders que fallan si quedan sin resolver; goldens sha256 por salida | Registro de skills generado (tabla nombre/trigger/alcance/ruta) con columnas `depends_on` y `stage` | Adaptadores por runtime, capability manifest, migraciones legacy |
| 2. Paquete normativo | Congelar hash de la política aplicada en cada evaluación | Catálogo de sinks peligrosos (regex por lenguaje → CWE) reorientado a ley → artículo → control → detección → remediación → evidencia | — |
| 3. Detección y score | Etiqueta `derivation` por métrica (`measured` / `proxy` / `unobservable` = `null`); nunca publicar solo un score compuesto | Clasificador de riesgo determinista (señales y rutas sensibles, nunca el tamaño); el agente solo puede **subir** el nivel | Lentes 4R genéricas (reemplazar por lentes normativas) |
| 4. Validación del detector | Corpus "ciego": defectos sembrados + controles limpios, verdad nunca visible para agente ni detector; recall y falsos positivos en limpios por separado | Fixtures que prueban su propia etiqueta; manifiesto de verdad versionado con checksums y doble etiquetado | — |
| 5. Skills Ley 21.719 | Estilo de skill (activación, reglas duras, decisiones, pasos, contrato de salida; 180-450 tokens; extractos legales en `references/`) | Modos: auditoría = solo lectura; parchado = tarea chica; desarrollo nuevo = tarea grande con documento; jueces ciegos (Judgment Day) para auditoría con campo `article` | `agentbuilder` |
| 6. Contexto y memoria | Engram vía MCP (`engram mcp --tools=agent`); documento de tarea + espejo en Engram | CodeGraph para recuperar contexto + grafo AST propio para linaje (ver abajo); hooks que recuerdan `mem_context` / resumen de sesión | Instalador del binario de Engram |
| 7. Experimento formal | Subconjunto comparable con excluidos nombrados; `failed`/`unsupported` nunca cuentan como 0; brazos que difieren en **un solo factor** | Objetos de cobertura de tokens `{reported, unavailable, unsupported, sum}`; presupuesto y pronóstico antes de cada corrida paga; N preregistrado con diseño pareado | Shim de proceso de `bench/`, telemetría remota |

## Hallazgos que cambian decisiones

1. **`bench/` no es el benchmark con agentes reales.** Mide fricción del CLI sin modelos (`GA:bench/README.md`). La tabla "Measured" del README viene de `gentle-shell` y no es reproducible desde este repositorio. Lo útil del lado LLM está en el logbook `GA:odd/tasks/rdd-risk-gated.md` (corpus ciego, recall, falsos positivos, USD).
2. **Score compuesto rechazado explícitamente** (`GA:bench/README.md:260-263`): una suma ponderada puede mejorar mientras empeora la dimensión crítica. El `compliance_score` del piloto debe publicarse siempre junto a sus componentes y con pesos fijados antes de correr.
3. **RDD no deja recibo.** Congela el candidato, revisa y "quema" la autorización (`GA:docs/architecture/organic-rdd.md:8,28`). El harness necesita lo contrario: un **recibo de cumplimiento por cambio** que se conserve.
4. **Ninguna herramienta de grafo hace taint.** Ni CodeGraph ni graphify analizan flujo de datos; el linaje para la Ley 21.719 es aporte propio.

## Recibo de cumplimiento (subconjunto mínimo estimado: 5 módulos, 600-900 líneas)

Basado en `GA:internal/reviewtransaction` (`snapshot.go:65-82`, `risk.go:220-238`, `receipt.go:29-48`), sin concurrencia, multi-runtime ni compatibilidad histórica:

- `candidate.py`: identidad del cambio = SHA-256 con separación de dominio sobre árbol base, árbol candidato (`git write-tree` con índice temporal) y digest de rutas.
- `risk.py`: nivel por categorías de dato personal/sensible y rutas sensibles; catálogo normativo; el agente solo escala.
- `admission.py`: admisión estricta de hallazgos del modelo (esquema cerrado, `path:line` obligatorio, sin relleno tipo "N/A"; afirmaciones causales no verificables bajan a "causa desconocida").
- `transaction.py`: ~6 estados y **una** corrección; después, "necesita tu decisión". Si la identidad cambia tras el veredicto, el estado queda invalidado.
- `receipt.py`: registro JSONL de solo agregado con hashes encadenados: hallazgos por artículo, score calculado por código (nunca por el modelo), versión de reglas, hash de política, versión de cada detector, comandos ejecutados con exit code.

## CodeGraph vs graphify

| | CodeGraph | graphify + ingesta actual |
|---|---|---|
| Paquete | `@colbymchenry/codegraph` (MIT), Node, tree-sitter en Rust | `graphifyy` 0.9.55 (Apache-2.0), tree-sitter en Python |
| Granularidad | Símbolos con aristas calls/imports/extends y rutas HTTP (FastAPI) | Símbolos con calls/imports/inherits; solo línea de inicio |
| Consulta | MCP (`codegraph serve --mcp`) y CLI con `--json` | CLI `query`/`path`/`explain`, MCP con `--mcp` |
| Incremental | Watcher y `codegraph sync` | `--update`/`--watch` disponibles, pero la ingesta del harness reconstruye todo |
| Telemetría | Sí; apagar con `CODEGRAPH_TELEMETRY=0` | No documentada |
| Taint | No | No |

Defectos confirmados en la ingesta actual (`src/harness/graph_engine.py`):
- El modo símbolo filtra `function|class|endpoint` (`:523`), pero la ingesta produce `callable|symbol` (`:270-278`); además graphify nombra las funciones con `()` (590 de 1.223 nodos), así que la comparación por nombre (`:483`) nunca coincide. Resultado: solo se renderizan clases.
- El "% de ahorro de tokens" es una razón de nodos (`:602`).
- La ingesta excluye `tests/` (`:208-209`): en la tarea 02 el recall máximo es 4/6.
- `tests/harness/test_graph_engine.py:114-122` construye a mano un nodo `function` que producción no genera, por eso el test pasa.

Recomendación: **combinar**. CodeGraph para la recuperación de contexto del agente; el grafo AST propio en SQLite para linaje y cumplimiento (subir de linaje por archivo a linaje por llamada); evaluar Semgrep en modo taint para flujo entre funciones. Validar antes con el experimento barato: tarea 02, mismas consultas en harness actual, harness parcheado y CodeGraph; medir precisión y recall contra `relevant_paths`, símbolos, tokens reales de contexto (tokenizer) y si el parche resultante pasa `tests/demo/`.

## Fuentes de los exploradores

- Benchmark y métricas: `GA:bench/`, `GA:internal/telemetry`, `GA:contracts/telemetry`.
- RDD: `GA:internal/reviewtransaction`, `GA:contracts/review-integration`, `GA:docs/architecture/organic-rdd.md`.
- Skills y memoria: `GA:internal/components/agentguidance/orchestrator.go:251`, `GA:internal/skillregistry/registry.go`, `GA:internal/assets/skills/_shared/skill-resolver.md`, `GA:internal/assets/engram/protocol.md`.
- CodeGraph: `GA:internal/components/communitytool/tool.go`, README upstream de `colbymchenry/codegraph`.
