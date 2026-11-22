# Metricas de Evaluacion del Harness

## Objetivo
Medir la calidad del output de un LLM usando el harness de VibeCoding (con skills)
vs usando un prompt libre (sin skills), para cuantificar el valor agregado.

## Metricas

### 1. Tasa de Alucinaciones (HA — Hallucination Rate)

**Definicion:** Porcentaje de imports, llamadas a API, nombres de librerias o comandos
que no existen en la realidad.

**Medicion:**
```
HA = (items inventados / total de items de codigo) * 100
```

**Ejemplos de items inventados:**
- `import { useQuantumState } from 'react'` — no existe
- `app.useFingerprintAuth()` — metodo inventado
- `pip install superfastapi` — paquete inexistente
- `docker compose hyperbuild` — comando inventado

**Target:** Con harness < 2%. Sin harness: tipicamente 8-15%.

### 2. Indice de Goldplating (GI — Goldplating Index)

**Definicion:** Porcentaje de features, endpoints, componentes o configuraciones
generados que NO estaban en el PRD ni fueron solicitados.

**Medicion:**
```
GI = (features no solicitadas / total de features implementadas) * 100
```

**Ejemplos de goldplating:**
- Agregar panel de admin sin que este en el PRD
- Implementar dark mode sin solicitarlo
- Agregar i18n con 3 idiomas
- Crear CI/CD sin que se pida
- Agregar health checks sin solicitarlos
- Implementar paginacion en endpoints que no la necesitan

**Target:** Con harness < 5%. Sin harness: tipicamente 20-40%.

### 3. Desviacion del MVP (MD — MVP Deviation)

**Definicion:** Porcentaje de lineas de codigo que implementan funcionalidad
fuera del alcance del PRD.

**Medicion:**
```
MD = (lineas fuera de scope / total de lineas) * 100
```

**Target:** Con harness < 10%. Sin harness: tipicamente 25-50%.

### 4. Tasa de Decisiones No Consultadas (UD — Unconsulted Decisions)

**Definicion:** Numero de decisiones tecnicas (stack, arquitectura, librerias,
patrones) que el modelo tomo sin preguntar al desarrollador.

**Medicion:**
```
UD = count(decisiones_no_consultadas)
```

**Ejemplos:**
- Eligio PostgreSQL sin preguntar SQL vs NoSQL
- Uso TypeScript sin preguntar
- Agrego Docker sin preguntar
- Eligio JWT sin preguntar metodo de auth
- Uso bcrypt sin preguntar algoritmo de hashing

**Target:** Con harness < 2 decisiones. Sin harness: tipicamente 5-15.

---

## Metodologia de Evaluacion

### Caso Base (Sin Harness)

Prompt: "Crea una API REST para gestionar productos con CRUD basico."

Se evalua el output sin ninguna regla ni skill cargada.

### Caso con Harness (Con Skills)

Se carga el harness completo (reglas always-on + skills) y se hace el mismo prompt.

La skill 01_prd deberia activarse y empezar a preguntar en vez de generar codigo.

### Proceso

1. Ejecutar el caso base → medir las 4 metricas
2. Ejecutar el caso con harness → medir las 4 metricas
3. Comparar y generar reporte

### Reporte Esperado

| Metrica | Sin Harness | Con Harness | Mejora |
|---------|-------------|-------------|--------|
| Alucinaciones (HA) | X% | Y% | Δ% |
| Goldplating (GI) | X% | Y% | Δ% |
| Desviacion MVP (MD) | X% | Y% | Δ% |
| Decisiones no consultadas (UD) | N | N | Δ |

---

## Interpretacion

- **HA > 5% con harness:** Las skills no estan previniendo alucinaciones. Revisar regla 03.
- **GI > 10% con harness:** Las skills no estan previniendo goldplating. Revisar regla 02.
- **MD > 15% con harness:** El modelo esta generando codigo sin preguntar. Revisar regla 01.
- **UD > 3 con harness:** Las skills no estan forzando el patron pregunta-respuesta.
  Revisar que las skills tengan preguntas obligatorias que bloqueen el avance.

## Mejora Continua

Cada vez que se detecte una metrica fuera de target, se debe:
1. Identificar la skill o regla que fallo
2. Agregar preguntas o restricciones adicionales
3. Re-evaluar para verificar la mejora

## Piloto Cursor SDK (3 brazos)

Runner: `harness/eval/cursor_runner.py`. Usa el runtime local de `cursor-sdk` con el plan
del usuario y un modelo fijo (nunca `auto`). Dependencia: `harness/eval/requirements-eval.txt`.

```powershell
python -m pip install -r harness/eval/requirements-eval.txt
python -m harness.eval.cursor_runner --dry-run          # valida workspaces sin API key
# CURSOR_API_KEY en el entorno o en .env (raiz del repo, ignorado por git)
python -m harness.eval.cursor_runner --model composer-2.5 --reps 1
```

El runner usa la API asincrona del SDK: en Windows, el bridge sincrono de `cursor-sdk` 1.0.40
falla al esperar el pipe con `select` (`WinError 10038`).

### Brazos

| Brazo | Workspace | Configuracion cargada |
|---|---|---|
| `baseline` | Solo la app clinica (`src/backend`, `src/database`, `tests/demo`) | Ninguna (`setting_sources` vacio, sin system prompt) |
| `harness` | App + `AGENTS.md` como regla `.cursor/rules` + 12 skills del pipeline en `.cursor/skills` | `project` |
| `harness_compliance` | `harness` + regla de compuerta | `project` + herramienta `compliance_check` + retroalimentacion de hallazgos |

Los workspaces se crean fuera del repositorio (temp del SO) con un commit base, y el motor
de cumplimiento nunca se copia. Todos los brazos reciben el mismo prompt y la misma respuesta
estandar si terminan sin cambios (cuenta como correccion requerida).

### Metricas del reporte (`qa_reports/pilot/pilot_<fecha>.json`)

- **Eficiencia:** `cycle_time_s`, `latency_ms` (suma de `duration_ms` del SDK), `rounds`, `tool_calls`, `turns`, `tokens`, `usage_reported`.
- **Calidad:** `tests` (suite `tests/demo` en el workspace), `files_changed`, `lines_added`, `lines_deleted`, `unrequested_changes`.
- **Gobernanza:** `policy_violations`, `scope_violations`, `privacy_findings`, `compliance_score`, `findings` (PolicyEngine sobre el diff) y `gate_rounds` (retroalimentaciones automaticas de la compuerta).
- **Contexto:** `files_read`, `relevance_ratio` contra `relevant_paths` del sidecar `.scope.json` de la tarea.
- **Revision:** `required_corrections` (respuestas estandar enviadas porque el agente termino sin cambios; las rondas de la compuerta no cuentan).

El diff se mide con `git diff --no-renames -z` contra el commit base del workspace, y el
`.gitattributes` (`* text=auto`) evita que reescrituras CRLF/LF cuenten como lineas modificadas.

### Formula de `compliance_score` (v2, preregistrada para T7)

`compliance_score = max(0, 100 - [sum(peso(severidad) por hallazgo VIOLATION) + 1 por hallazgo WARNING])`

| Estado | Peso |
|--------|------|
| VIOLATION CRITICAL | 25 |
| VIOLATION HIGH | 10 |
| VIOLATION MEDIUM | 5 |
| VIOLATION LOW | 2 |
| WARNING (riesgo potencial) | 1 |

- Cuenta un hallazgo por (politica, archivo, linea); los hallazgos de alcance (`scope.*`) se excluyen y se reportan aparte como `scope_violations`.
- El score nunca se publica solo: se reportan siempre sus componentes (`findings` por severidad y por politica, `privacy_findings`, y los `WARNING` por politica).
- La formula y los pesos quedan fijos antes del experimento formal (T7); cambiarlos exige una nueva version (v3) y reportar ambas. Las corridas con v1 no son comparables con v2.
- Politicas deterministas activas y control del pack al que responden:
  `privacy.cwe_532` (CORE-CHECK-002, CL-DATAPROT-001), `privacy.api_exposure` (CORE-CHECK-002), `privacy.payment_data_storage` (ECOM-CHECK-003), `domain.prohibited_deletion` (HEALTH-CHECK-001, CL-DATAPROT-004), `privacy.rights_reachability` (CORE-CHECK-006), `privacy.consent_transparency` (CORE-CHECK-005/007, ECOM-CHECK-001), `privacy.minors_and_sensitive` (CORE-CHECK-012, ECOM-CHECK-007), `privacy.retention_minimization` (CORE-CHECK-013), `privacy.third_party_transfers` (CORE-CHECK-010/011, ECOM-CHECK-005). Todas se cuentan en `privacy_findings` por el prefijo `privacy.`.
- Alcance del score: mide solo lo que el codigo puede probar. Los controles documentales del pack (`detection.implemented: false`: licitud documental, incidentes, evaluacion de impacto, PCI DSS, conservacion tributaria y los heuristicos del auditor legacy) devuelven `NOT_APPLICABLE` en la auditoria y **no suman ni restan**. Un score de 100 significa "ningun hallazgo detectable en codigo", no "cumple la ley". Se reporta aparte la lista de controles documentales aplicables sin evidencia.
- Los detectores de dimension (T16-T20) son conservadores: emiten `WARNING` cuando falta un artefacto y `VIOLATION` solo si el codigo contradice una salvaguarda explicita (consentimiento premarcado, plantilla biometrica cruda). Ese `WARNING` resta 1 punto, no equivale a una infraccion confirmada.
- Precision y recall de cada detector se publican con el corpus etiquetado (`python -m harness.eval.corpus`); los falsos negativos conocidos estan en `harness/eval/corpus/cases.json` como `seeded-hard`. Los detectores que solo emiten `WARNING` se miden aparte (`score_warnings`) con casos etiquetados `expected_warnings` / `warning_clean`: cada politica participa solo en los casos que la nombran, para que un caso limpio de una dimension no cuente como falso positivo de otra. Corte 2026-10-28: `privacy.rights_reachability`, `privacy.consent_transparency`, `privacy.minors_and_sensitive`, `privacy.retention_minimization` y `privacy.third_party_transfers` dan precision 1.0 y recall 1.0 con 1 caso sembrado y 1 limpio por politica. Es una muestra minima escrita por el mismo autor del detector: no es ciega y no reemplaza el oraculo de T7.
- `privacy.retention_minimization`, `privacy.rights_reachability` y `privacy.third_party_transfers` no tienen regla de `VIOLATION`: por diseño no pueden producir una violacion confirmada, solo riesgo potencial. T7 debe sembrar trampas de riesgo potencial para esas dimensiones y reportarlas en el resultado secundario, no en `oracle_violations`.
- `privacy.cwe_532` incluye desde `feat/call-level-taint` un pase de flujo por llamadas (`src/harness/taint_flow.py`). La comparacion con el detector local y con el linaje por archivo (`DataLineageEngine`) sobre los mismos casos se publica con `python -m harness.eval.flow_bench`. Es un cambio de detector, no de formula: las corridas antes y despues de el no son comparables sin reportar la version del detector.

Las metricas aun no medibles se reportan `null` y su motivo queda
en `metadata.null_reasons`.
