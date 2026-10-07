# SKILL_INTEROPERABILITY_CONTRACT.md — Contrato de Interoperabilidad, Linaje Contractual y Tránsito de Decisiones

> **Fecha:** 30 de septiembre de 2026  
> **Proyecto:** Arnés de Gobernanza para Desarrollo de Software Asistido por Agentes de IA  
> **Objetivo del Documento:** Formalizar el contrato de interoperabilidad entre skills, el linaje contractual de decisiones (*Contractual Lineage*), el ciclo de vida de decisiones versionadas y la cobertura de aceptación (*Acceptance Coverage*), aplicándolo conceptualmente a la cadena troncal:  
> `01-prd ──► 02-architecture ──► (03-data / 04-api / 08-test-plan) ──► (05-backend / 06-frontend) ──► 08-testing`

---

## 1. Fundamento: La Interacción y el Linaje Contractual

Un conjunto de 12 skills con plantillas correctas no constituye un sistema de gobernanza si operan como silos aislados. El verdadero objeto de estudio del arnés es **la interacción gobernada y la trazabilidad de extremo a extremo**.

Para que un cambio en el código fuente sea legítimo, debe existir una cadena causal ininterrumpida que justifique su existencia:

```text
┌────────────────────────────────────────────────────────────────────────┐
│               CADENA DE LINAJE CONTRACTUAL (TRACEABILITY CHAIN)        │
└────────────────────────────────────────────────────────────────────────┘

    Intención del Negocio / Problema
                  │
                  ▼
         Requisito Funcional (PRD)
                  │
                  ▼
     Criterio de Aceptación (AC-xxx)
                  │
                  ▼
     Decisión Arquitectónica (AD-xxx)
                  │
                  ▼
      Componente / Capa Afectada
                  │
                  ▼
          TaskSpec Atómico (TS-xxx)
                  │
                  ▼
          Cambio en Código (Diff)
                  │
                  ▼
        Prueba Unitaria (T-xxx)
                  │
                  ▼
     Veredicto de Validación / Finding
```

### Detección de "Cambios sin Linaje" (*Orphan Changes*):
Este modelo permite al arnés responder objetivamente a la pregunta: **¿Por qué existe este archivo o esta línea de código?**
* Si un agente crea `src/backend/services/redis_cache.py`:
  1. El arnés busca el `TaskSpec` activo $\to$ `TS-012: Implementar consulta de pacientes`.
  2. Busca la decisión arquitectónica que respalda el componente $\to$ `AD-003: Persistencia relacional directa`.
  3. Comprueba el PRD $\to$ "Caché externa" no existe o figura explícitamente en `OUT OF SCOPE`.
  4. **Veredicto:** `FAIL`. Finding emitido por el arnés:
     > `[CRITICAL] governance.orphan_change: El artefacto 'redis_cache.py' carece de linaje contractual hacia el PRD aprobado.`

---

## 2. Esquema Formal del Contrato de Interoperabilidad

Para evitar la amnesia del agente y eliminar la re-negociación no autorizada de decisiones, toda skill debe implementar el siguiente contrato de interfaces:

```yaml
# ==============================================================================
# ESQUEMA FORMAL: SKILL INTEROPERABILITY CONTRACT v2.0
# ==============================================================================
skill_id: string                      # Ej: "02-architecture"
stage_name: string                    # Ej: "architectural_design"
produces_artifact:                    # Artefacto generado y versionado
  path: string                        # Ej: "docs/ARCHITECTURE.md"
  version: integer                    # Ej: 1
  status: "DRAFT" | "APPROVED" | "SUPERSEDED"

# 1. CONTRATOS HEREDADOS AGUAS ARRIBA (UPSTREAM CONTRACTS)
inherited_contracts:
  requirements:                       # Requerimientos de negocio originados en PRD
    - req_id: string                  # Ej: "REQ-001"
      description: string
      scope_category: "IN_SCOPE" | "OUT_OF_SCOPE"

  decisions:                          # Decisiones técnicas heredadas y activas
    - decision_id: string             # Ej: "AD-001"
      origin_skill: string            # Ej: "01-prd" o "02-architecture"
      decision_key: string            # Ej: "system.pattern"
      value: any                      # Ej: "modular_monolith"
      version: integer                # Ej: 1
      status: "ACTIVE" | "SUPERSEDED"
      supersedes: string | null       # ID de decisión previa si hubo cambio
      rationale: string               # Justificación técnica registrada

  constraints:                        # Restricciones operativas duras
    - constraint_id: string           # Ej: "CONST-001"
      rule: string                    # Ej: "CWE-532: No PII/health in plain logs"
      policy_id: string               # Ej: "privacy.cwe_532"

  acceptance_criteria:                # Criterios de aceptación verificables
    - ac_id: string                   # Ej: "AC-001"
      statement: string
      verification_type: "DETERMINISTIC_TEST" | "INSPECTION"

# 2. AUTORIDAD LOCAL DE LA SKILL
local_authority:
  authorized_decisions: [string]      # Categorías de decisión que esta etapa TIENE potestad de resolver
  forbidden_decisions: [string]       # Decisiones que NO PUEDE tomar (delegadas o prohibidas)

# 3. GARANTÍAS ENTREGADAS AGUAS ABAJO
downstream_guarantees:
  exported_artifacts: [string]        # Archivos concretos generados para consumo posterior
  exported_decisions: [string]        # Decisiones nuevas selladas en esta fase
  exported_tags: [string]             # IDs para trazabilidad (ej: "COMP-001", "EP-001")

# 4. COMPUERTA DE CALIDAD Y CONGELAMIENTO LÓGICO
quality_gate:
  deterministic_checks: [string]      # Validaciones automáticas sin intervención humana
  judgment_checks: [string]           # Revisiones de diseño por humano / revisor
  approval_status: "PENDING" | "APPROVED"
```

---

## 3. Topología del Workflow: No es un Waterfall Lineal

Una limitación de los enfoques ingenuos es concebir el desarrollo como una línea secuencial rígida ($01 \to 02 \to \dots \to 12$). La ingeniería de software real opera como un **Grafo Acíclico Dirigido (DAG) de dependencias**, donde existen fases paralelas y transversales:

```text
                           ┌───────────────────────────┐
                           │          01 PRD           │
                           │   (Alcance y Criterios)   │
                           └─────────────┬─────────────┘
                                         │
                                         ▼
                           ┌───────────────────────────┐
                           │      02 ARCHITECTURE      │
                           │    (Patrón y Módulos)     │
                           └─────────────┬─────────────┘
                                         │
                 ┌───────────────────────┼───────────────────────┐
                 │                       │                       │
                 ▼                       ▼                       │
       ┌───────────────────┐   ┌───────────────────┐             │
       │  03 DATA MODEL    │   │  04 API DESIGN    │             │
       │    (Esquema)      │   │    (Contrato)     │             │
       └─────────┬─────────┘   └─────────┬─────────┘             │
                 │                       │                       │
                 └───────────┬───────────┘                       │
                             │                                   │
                             ├──────────────────────────┐        │
                             ▼                          ▼        ▼
                   ┌───────────────────┐      ┌─────────────────────────┐
                   │   05 BACKEND      │ ◄──► │   08 TEST PLANNING      │
                   │ (Implementación)  │      │  (Matriz AC -> Tests)   │
                   └─────────┬─────────┘      └────────────┬────────────┘
                             │ (Paralelo)                  │
                             ▼                             │
                   ┌───────────────────┐                   │
                   │   06 FRONTEND     │                   │
                   │ (Implementación)  │                   │
                   └─────────┬─────────┘                   │
                             │                             │
                             ▼                             ▼
                   ┌───────────────────┐      ┌─────────────────────────┐
                   │     07 AUTH       │      │   08 TEST EXECUTION     │
                   │   (Seguridad)     │ ───► │ (Validación de Código)  │
                   └─────────┬─────────┘      └────────────┬────────────┘
                             │                             │
                             └──────────────┬──────────────┘
                                            │
                                            ▼
                        ┌───────────────────────────────────────┐
                        │  09 CI / 10 DEPLOY / 11 OBSERVABILITY │
                        └───────────────────┬───────────────────┘
                                            │
                                            ▼
                        ┌───────────────────────────────────────┐
                        │           12 DOCUMENTATION            │
                        └───────────────────────────────────────┘
```

### Principios de Concurrencia y Transversalidad:
1. **Desarrollo Paralelo Backend/Frontend:** Una vez congelado el contrato de interfaz en `04-api-design`, `05-backend` y `06-frontend` pueden desarrollarse de forma concurrente consumiendo los mismos schemas DTO.
2. **Testing Transversal:** `08-testing` no es un evento final tardío.
   * *Fase temprana (Planificación):* Se alimenta de los `AC-xxx` de `01-prd` y de los contratos de `04-api-design` para estructurar la matriz de pruebas antes de escribir el código.
   * *Fase activa (Ejecución):* Acompaña a `05-backend` y `06-frontend` validando contra los criterios de aceptación.

---

## 4. El Puente Funcional $\to$ Técnico: PRD Scope Global vs. TaskSpec Scope Atómico

Debe preservarse con rigor la distinción entre el **alcance funcional global** y el **alcance técnico de una tarea de desarrollo**:

* **PRD Scope:** Define fronteras de capacidades del sistema (ej: "Soporte de carritos de compra", "Prohibición de pagos externos"). No menciona archivos.
* **TaskSpec Scope:** Delimita el perímetro exacto de modificación de archivos (`allowed_paths`) para una unidad de trabajo atómica realizable en una sola sesión por un agente.

Una única capacidad funcional del PRD se descompone típicamente en múltiples `TaskSpecs` con perímetros acotados e independientes:

```text
[CAPACIDAD FUNCIONAL EN PRD]
  Feature: "Registro de Eventos de Acceso a Pacientes (Ley 21.719)"
    │
    ├──► TaskSpec 1 (TS-01): "Crear modelo y migración de persistencia para eventos"
    │    • allowed_paths: ["src/database/models/audit.py", "alembic/versions/*"]
    │    • forbidden_paths: ["src/backend/api/**", "src/frontend/**"]
    │    • constraints: ["soft-delete only", "no external dependencies"]
    │
    ├──► TaskSpec 2 (TS-02): "Instrumentar middleware de auditoría en la API"
    │    • allowed_paths: ["src/backend/api/patients.py", "src/backend/services/audit.py"]
    │    • forbidden_paths: ["src/database/models/**", "src/frontend/**"]
    │    • constraints: ["CWE-532: Enmascarar RUT en logs"]
    │
    └──► TaskSpec 3 (TS-03): "Suite de pruebas automatizadas del flujo de auditoría"
         • allowed_paths: ["tests/demo/test_audit.py"]
         • forbidden_paths: ["src/**"]
         • test_targets: ["tests/demo/test_audit.py"]
```

---

## 5. Trazabilidad y Cobertura de Aceptación (*Acceptance Coverage*)

### El Fallo de Confiar Únicamente en `pytest == 0`:
Un agente puede presentar 50 pruebas automatizadas pasando al 100% que solo verifiquen funciones auxiliares de formato de cadenas o mocks superficiales, mientras que la regla de negocio crítica quedó sin probar.

El arnés trasciende la tasa bruta de tests implementando la **Métrica de Cobertura de Aceptación (*Acceptance Coverage*)**:

$$\text{Acceptance Coverage} = \frac{\sum \text{Criterios } AC\text{ con prueba asociada aprobada}}{\text{Total de Criterios } AC\text{ en PRD}}$$

```text
MATRIZ DE COBERTURA DE ACEPTACIÓN:

[AC-001] Consulta exitosa por ID retorna 200 con payload válido
         └── Asociado a: tests/demo/test_patients.py::test_get_patient_success
         └── Resultado: PASS (Verificado)

[AC-002] Consulta de paciente no registrado retorna 404 estructurado
         └── Asociado a: tests/demo/test_patients.py::test_get_patient_not_found
         └── Resultado: PASS (Verificado)

[AC-003] Deber de confidencialidad: El log de auditoría no expone RUT en texto plano (Ley 21.719)
         └── Asociado a: tests/demo/test_patients.py::test_audit_log_rut_masking
         └── Resultado: PASS (Verificado con PolicyEngine CWE-532)

[AC-004] Retención decenal: La baja de ficha clínica debe ser soft-delete (Ley 20.584)
         └── Asociado a: [SIN TEST ASOCIADO - BRECHA DETECTADA]
         └── Resultado: FAIL (El arnés bloquea la promoción por falta de evidencia)
```

---

## 6. Ciclo de Vida de Decisiones y Congelamiento Lógico

Las decisiones no se bloquean mediante mecanismos físicos destructivos (`chmod` de solo lectura en el sistema operativo). Se gestionan mediante un **Registro de Decisiones Versionado (*Decision Registry*)**:

### Estados de una Decisión:
* **`ACTIVE`:** Decisión vigente, aprobada y vinculante para todas las etapas descendentes.
* **`SUPERSEDED`:** Decisión previa que fue reemplazada por una nueva decisión formal mediante un *Change Request*.
* **`PROPOSED`:** Decisión en deliberación que aún no cuenta con aprobación humana.

### Protocolo de Solicitud de Cambio (*Change Request*):
Si durante `05-backend` se descubre que una decisión previa debe cambiar (por ejemplo, el PRD estableció almacenamiento en memoria, pero el volumen de datos requiere persistencia en disco):

```text
1. El Agente detecta el impedimento técnico.
2. NO PUEDE modificar silenciosamente el código en contradicción con la decisión activa.
3. Emite formalmente una Solicitud de Cambio (Change Request):
   • Decisión a modificar: AD-002 (storage.engine)
   • Valor actual: "in_memory" (ACTIVE)
   • Valor propuesto: "sqlite_relational"
   • Justificación técnica (Rationale): "El volumen de transacciones excede la memoria del proceso local."
   • Artefactos afectados: ["docs/PRD.md", "docs/ARCHITECTURE.md", "src/database/schema.sql"]
4. El Desarrollador Humano aprueba la solicitud.
5. El Arnés marca AD-002 como SUPERSEDED y sella AD-005 con status ACTIVE.
6. Se re-validan únicamente los componentes del árbol afectados por el cambio.
```

---

## 7. Aplicación Conceptual Agnóstica al Camino Crítico

Para garantizar que el arnés sea **generalizable a cualquier lenguaje y stack**, los contratos de interoperabilidad no predefinen librerías concretas. Operan mediante **variables de decisión tipadas**:

```text
Paso 1: 01-prd
  • Define frontera: IN SCOPE = {entidad_principal, consulta_detalle}, OUT OF SCOPE = {pagos_externos, microservicios}
  • Define criterios: AC-001, AC-002, AC-003
  • Estado del PRD: APPROVED (v1.0)

Paso 2: 02-architecture
  • Consume: PRD v1.0
  • Decisión sellada: architecture.pattern = "modular_monolith" (AD-001)
  • Decisión sellada: communication.style = "synchronous_api" (AD-002)
  • Componentes exportados: ["core_api", "domain_service", "storage_gateway"]

Paso 3: 03-data-modeling
  • Consume: AD-001, AD-002 y entidades de REQ-001
  • Decisión sellada: storage.engine_type = "relational_sql" (AD-003)
  • Decisión sellada: storage.deletion_strategy = "soft_delete" (AD-004)
  • Artefacto exportado: DDL estructurado y modelos de persistencia

Paso 4: 04-api-design
  • Consume: AD-002, AD-003 y criterios AC-001/002
  • Decisión sellada: api.contract_format = "openapi_spec" (o "markdown_spec") (AD-005)
  • Schemas exportados: DTOs de entrada y salida con políticas de enmascaramiento

Paso 5: 08-testing (Planificación y Validación)
  • Consume: AC-001, AC-002, AC-003 y api.contract_format
  • Mapea: Matriz de cobertura AC-xxx -> Test-xxx
  • Validación: Acceptance Coverage == 100% y cero violaciones deterministas en PolicyEngine
```

---

## 8. Criterios de Evaluación para la Normalización de `01-prd`

Antes de intervenir las demás skills, la normalización de `01-prd` deberá superar dos pruebas de fuego técnicas para considerarse exitosa:

* **Prueba de Fuego 1 (Consumo sin Amnesia ni Re-interrogación):**
  > *¿Puede una skill posterior (`02-architecture` o `03-data-modeling`) inicializarse y extraer toda la información requerida directamente desde el `PRD.md` aprobado sin volver a preguntarle al desarrollador el tipo de proyecto, los roles, las restricciones ni las tecnologías descartadas?*

* **Prueba de Fuego 2 (Puente hacia `TaskSpec` sin Rigidez Prematura):**
  > *¿Puede el resultado del PRD alimentar la formulación de `TaskSpecs` atómicos delimitando su alcance funcional sin convertir prematuramente los requisitos de negocio en rutas de archivos físicas inexistentes?*

Si ambas pruebas son satisfactorias, el modelo de interoperabilidad quedará validado empíricamente y habilitará la normalización progresiva y segura del resto del pipeline.

---
*Especificación v2.0 completada. Marco formal de interoperabilidad listo para su aplicación en la normalización de la Skill 01.*
