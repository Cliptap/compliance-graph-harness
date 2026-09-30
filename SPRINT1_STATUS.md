# SPRINT1_STATUS.md — Diagnóstico Técnico, Inventario y Plan de Consolidación (Sprint 1)

> **Fecha:** 29 de septiembre de 2026  
> **Proyecto:** Arnés de gobernanza para desarrollo de software asistido por agentes de IA  
> **Estado Operativo:** Núcleo Técnico Base Implementado (46/46 tests en verde) | Preparación para Validación Experimental Real (**Sprint 1 NO cerrado**)  
> **Objetivo del Documento:** Auditar el estado real del repositorio, mapear componentes construidos, delimitar brechas y trazar la ruta hacia la validación experimental mediante desarrollo de software real.

---

## 1. Estado Actual del Repositorio

* **Punto de Control Git (VCS):**
  * **HEAD:** Commit `91c3c7c` (*feat: initial commit for compliance graph harness and Hito 0 artifacts*).
  * **Working Tree:** Código modular del núcleo del arnés probado y listo para consolidación (`contracts.py`, `policy_engine.py`, `validation_engine.py`, mejoras AST en `graph_engine.py`).
* **Entorno de Ejecución:**
  * **Sistema Operativo:** Windows 11.
  * **Runtime:** Python 3.13.13, Node.js (Vite / Vue 3 en frontend clínico).
  * **Test Runner:** `pytest-9.0.3` con plugins `asyncio-1.3.0`, `anyio-4.13.0`.
* **Estado de la Suite de Pruebas:**
  * **46/46 pruebas automatizadas pasando al 100%** (tiempo de ejecución: ~3.2 segundos).
    * `tests/demo/`: 21 pruebas (citas médicas, auditoría forense, pacientes, facultativos).
    * `tests/harness/`: 25 pruebas (motor AST, extracción quirúrgica de símbolos, linaje de datos, persistencia SQLite, grafos, contratos, políticas y compuerta de validación).

---

## 2. Inventario de Componentes Existentes

| Componente | Ubicación Física | Estado Operativo | Propósito / Rol Actual |
| :--- | :--- | :--- | :--- |
| **Contratos Nucleares** | `src/harness/contracts.py` | Implementado y Probado | Especificaciones Pydantic: `TaskSpec` (alcance/restricciones), `Finding` (hallazgos unificados) y `ValidationVerdict` (`PASS`/`FAIL`). |
| **Motor de Políticas** | `src/harness/policy_engine.py` | Implementado y Probado | Evaluadores deterministas: `ScopePolicy`, `SensitiveLoggingPolicy` (CWE-532), `DomainInvariantPolicy` y `DependencyPolicy`. |
| **Motor de Validación** | `src/harness/validation_engine.py` | Implementado y Probado | Orquesta políticas y `pytest`, emitiendo veredictos y mensajes de feedback estructurados con directivas de mitigación. |
| **Motor de Grafo (Graph Engine)** | `src/harness/graph_engine.py` | Funcional (AST + SQLite + Slicing) | Construye nodos/aristas y realiza *symbol-level slicing* (`PythonSymbolExtractor`) para inyectar solo símbolos precisos en contexto. |
| **Trazabilidad de Linaje** | `src/harness/data_lineage.py` | Funcional (Taint tracking estático) | Identifica fuentes sensibles (`sources`), sumideros (`sinks`) y sanitizadores (`sanitizers`) cruzados contra reglas. |
| **Auditoría Normativa** | `src/harness/agentic_audit.py` | Funcional (Checklist estático + SQLite) | Evalúa archivos contra criterios de `compliance_rules.json` (`CORE-CHECK-001` a `004`, `HEALTH-CHECK-001` a `003`). |
| **Persistencia SQLite** | `src/harness/db.py`, `.harness/harness.db` | Totalmente Operativo | Almacena nodos, aristas, hallazgos (`compliance_findings`), razonamientos y bitácora de auditorías. |
| **Catálogo de Reglas Normativas** | `.harness/compliance_rules.json` | Operativo y Detallado | Ontología técnica de campos sensibles (salud, RUT, biometría) y catálogo de controles derivados de Ley 21.719 y Ley 20.584. |
| **Catálogo de Skills** | `.agents/skills/01-*` a `12-*` | Directivas Documentales | 12 especificaciones markdown que guían etapas de ciclo de vida (PRD, arquitectura, backend, testing, etc.). |
| **Backend Clínico (Demo 1)** | `src/backend/` | Totalmente Funcional (FastAPI) | Endpoints de pacientes, citas, auditoría, RBAC y servicios de negocio clínico. |
| **Smoke Test de Validación** | `experiments/sprint1_experiment.py` | Verificado (Smoke Test) | Certifica la compuerta determinista del `ValidationEngine` frente a propuestas prefijadas (sin LLM en el bucle). |

---

## 3. Delimitación Metodológica del Estado del Proyecto

Para mantener el rigor científico y evitar conclusiones apresuradas, se distingue estrictamente entre tres dimensiones:

```
┌────────────────────────────────────────────────────────────────────────┐
│                   ESTADO METODOLÓGICO DEL SPRINT 1                     │
└────────────────────────────────────────────────────────────────────────┘

  [A. IMPLEMENTADO (Ingeniería de Software)]
  • Contratos Pydantic (TaskSpec, Finding, ValidationVerdict).
  • PolicyEngine modular con 4 evaluadores independientes.
  • ValidationEngine con emisión de feedback estructurado.
  • PythonSymbolExtractor (Symbol-level Slicing en Graph Engine).
  • Suite de 46 tests automatizados en verde (100%).
  • Smoke test de compuerta determinista (sprint1_experiment.py).

  [B. VALIDACIÓN PENDIENTE (Uso Real del Arnés)]
  • Uso efectivo por un coding agent autónomo para desarrollar software.
  • Observación de comportamiento real: falsos positivos y falsos negativos.
  • Desarrollo sobre un segundo repositorio independiente (Retail / E-commerce).
  • Medición de fricción, tiempo adicional y costo de tokens introducido por el arnés.
  • Refinamiento de políticas a partir de problemas observados en el desarrollo.

  [C. INVESTIGACIÓN PENDIENTE (Evaluación Comparativa)]
  • Diseño experimental comparativo: Agente con Arnés vs. Agente sin Arnés.
  • Banco de tareas estandarizadas aplicadas sobre ambos dominios (Clínico y Retail).
  • Captura sistemática de métricas objetivas (Outcome del Software vs. Comportamiento del Agente).
```

---

## 4. Contradicciones y Sesgos Corregidos

1. **Reclasificación del Experimento Preliminar:**
   * *Diagnóstico previo:* Se presentó `experiments/sprint1_experiment.py` como demostración de gobernanza agéntica y cierre de Sprint.
   * *Corrección:* El script utiliza reemplazos fijos (`str.replace`) para simular la propuesta infractora y la propuesta corregida. Se reclasifica honestamente como **smoke test funcional del mecanismo de enforcement del validador**. La evaluación con un agente real comenzará a continuación.
2. **"Knowledge Graph" vs. Grafo de Dependencias AST:**
   * La documentación refería a "grafos de conocimiento con razonamiento semántico".
   * *Realidad técnica:* Es un **grafo estructural de dependencias estáticas de código** (AST en SQLite y Graphify). No existe motor de inferencia RDF/OWL.
3. **Roles Agénticos en `pipeline.py`:**
   * `ComplianceAuditorAgent` y `DeveloperPatcherAgent` no son agentes basados en LLM; son rutinas procedimentales en Python con f-strings y reemplazos de texto.
4. **Desacoplamiento Multidominio:**
   * Gran parte de las comprobaciones previas estaban directamente acopladas a la aplicación clínica (`patient`, `events.py`). Se requiere validar el arnés sobre un dominio completamente ajeno a la salud (E-commerce / Retail).

---

## 5. Arquitectura del Flujo de Validación Integrado

El flujo que el arnés orquesta para gobernar el desarrollo agéntico se estructura en interfaces modulares:

```
 1. ENTRADA DE TAREA
    ┌─────────────────────────────────────────────────────────┐
    │  TaskSpec (Dataclass / Pydantic)                        │
    │  • task_id: "R-01"                                      │
    │  • goal: "Implementar endpoint de cancelación"          │
    │  • allowed_paths: ["backend/api/orders.py"]             │
    │  • constraints: ["no external dependencies", "soft-del"]│
    └────────────────────────────┬────────────────────────────┘
                                 │
 2. RECUPERACIÓN DE CONTEXTO QUIRÚRGICO
                                 ▼
    ┌────────────────────────────┴────────────────────────────┐
    │  Context Engine: Sub-graph Slice a nivel de símbolos    │
    │  (PythonSymbolExtractor: solo funciones y modelos diana)│
    └────────────────────────────┬────────────────────────────┘
                                 │
 3. PROPUESTA DEL AGENTE DE CÓDIGO (LLM REAL)
                                 ▼
    ┌────────────────────────────┴────────────────────────────┐
    │  Coding Agent propone Candidate Code / Working Tree     │
    └────────────────────────────┬────────────────────────────┘
                                 │
 4. COMPUERTA DETERMINISTA (ValidationEngine)
                                 ▼
    ┌─────────────────────────────────────────────────────────┐
    │  ValidationEngine                                       │
    │   ├── ScopePolicy: ¿Modifica solo allowed_paths?       │
    │   ├── SensitiveLoggingPolicy: ¿Fugas CWE-532 en logs?   │
    │   ├── DomainInvariantPolicy: ¿Respeta soft-delete?      │
    │   ├── DependencyPolicy: ¿Modifica manifiestos?          │
    │   └── TestRunner: ¿Ejecuta la suite en verde? (pytest)  │
    └────────────────────────────┬────────────────────────────┘
                                 │
 5. VEREDICTO ESTRUCTURADO Y BUCLE DE RETROALIMENTACIÓN
                                 ▼
                    ┌────────────────────────────┐
                    │ ¿Existen Findings activos? │
                    └──────────────┬─────────────┘
                        FAIL │           │ PASS
                             ▼           ▼
        ┌──────────────────────────┐   ┌──────────────────────────┐
        │ Feedback estructurado:   │   │ Cambio aprobado          │
        │ • Finding ID y severidad │   │ Promoción a git          │
        │ • Archivo y línea exacta │   └──────────────────────────┘
        │ • Evidencia de la fuga   │
        │ • Directiva de mitigación│
        └─────────────┬────────────┘
                      │
                      ▼
         Reintento guiado del Agente (Turno 2)
```

---

## 6. Rol de los Dos Bancos de Prueba

Para garantizar que el arnés sea una herramienta de gobernanza general y no una solución sobreajustada a un caso médico, se establecen dos bancos de prueba con roles diferenciados:

| Banco de Pruebas | Dominio | Rol en la Investigación | Aspectos Evaluados por el Arnés |
| :--- | :--- | :--- | :--- |
| **Consultorio Clínico** (`demo_apps/clinical_clinic/` o `src/backend/`) | Salud / Médico | Alta gobernanza y cumplimiento legal estricto. | • Ley N.º 21.719 (Protección de Datos Personales).<br>• Ley 20.584 (Retención decenal de fichas clínicas / soft-delete).<br>• Detección de CWE-532 en identificadores civiles (RUT) y diagnósticos. |
| **Retail Store** (`demo_apps/retail_store/`) | E-commerce / Supermercado | Gobernanza general de ingeniería de software. | • Control de perímetro de modificación (*Scope Drift* / *Goldplating*).<br>• Control de dependencias no autorizadas.<br>• Invariantes de stock y estado de órdenes.<br>• Tareas de separación frontend / backend. |

---

## 7. Plan de Acción Priorizado (Ruta hacia la Validación Real)

```
[FASE 1: SANEAMIENTO Y CLASIFICACIÓN RIGUROSA] -> (COMPLETADA)
  ├── 1.1: Reclasificar sprint1_experiment.py como smoke test determinista.
  ├── 1.2: Corregir ruta de tests en pipeline.py (tests/).
  └── 1.3: Documentar formalmente el estado de Sprint 1 en SPRINT1_STATUS.md.

[FASE 2: VALIDACIÓN DIRECTA SOBRE WORKING TREE]
  ├── 2.1: Dotar a ValidationEngine de la capacidad de evaluar cambios directamente
  │        desde el árbol de trabajo (git diff / disco) sin requerir dicts manuales.
  └── 2.2: Parametrizar DomainInvariantPolicy para que reciba las entidades protegidas
           desde TaskSpec (desacoplamiento total del caso médico).

[FASE 3: SEGUNDO BENCHMARK MINIMALISTA (RETAIL STORE)]
  ├── 3.1: Crear estructura compacta en demo_apps/retail_store/ (catálogo, órdenes, stock).
  └── 3.2: Implementar suite base de 10-12 tests unitarios en tests/retail/.

[FASE 4: RUNNER EXPERIMENTAL REAL (EXPERIMENT RUNNER)]
  ├── 4.1: Construir experiments/task_runner.py para ejecutar tareas agénticas reales.
  └── 4.2: Definir el banco inicial de 4-6 tareas estándar (Scope, CWE-532, Invariants, Dependencies).

[FASE 5: EVALUACIÓN EMPÍRICA COMPARATIVA (CON ARNÉS VS. SIN ARNÉS)]
  ├── 5.1: Ejecutar tareas en condición Control (Modo Libre sin arnés).
  ├── 5.2: Ejecutar tareas en condición Tratamiento (Modo Gobernado con arnés).
  └── 5.3: Registrar telemetría objetiva: tests aprobados, findings, churn (LOC), tiempo y tokens.
```

---
*Documento aprobado como marco operativo y de auditoría técnica del Sprint 1.*
