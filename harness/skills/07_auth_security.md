---
name: auth-governance
version: 2.0.0
stage: 6
depends_on: [prd-generation, architecture-design, data-modeling, api-design, backend-implementation, frontend-implementation]
project_types: [web_app, api, mobile]
governance: [bajo, medio, alto]
produces_artifact: docs/SECURITY.md
description: Gobernanza de autenticación, autorización y seguridad baseline. Implementa derivación condicional (invariante negativa ante proyectos sin auth o de baja gobernanza) y auditoría de controles mínimos (sanitización, CORS, no hardcoded secrets, prevención CWE-532).
---

# Skill: Gobernanza de Autenticación y Seguridad (auth-governance)

## 1. Overview
Esta skill define y formaliza la postura de seguridad, control de identidades y controles técnicos defensivos del sistema.
A diferencia de aproximaciones tradicionales que fuerzan la implementación de capas complejas de autenticación (JWT, RBAC, OAuth2) de manera indiscriminada en todo proyecto, esta skill opera bajo el **Principio de Derivación Condicional (Conditional Governance)**:
- En proyectos con gobernanza media o alta y autenticación en alcance, diseña e implementa mecanismos robustos de control de acceso y protección de credenciales.
- En proyectos con gobernanza baja y autenticación expresamente sentenciada en `OUT OF SCOPE` (por ejemplo, sitios informativos de acceso público o herramientas internas de solo lectura), opera en **Modo de Auditoría e Invariante Negativa**: prohíbe tajantemente el goldplating (cero login, cero usuarios, cero tokens), audita que se cumplan los controles mínimos de seguridad proporcional (baseline security) y emite el dictamen formal en `docs/SECURITY.md`.

---

## 2. Cuándo Usar
- Se ejecuta en la **Etapa 6** del pipeline de desarrollo, inmediatamente después de haber implementado y verificado físicamente el backend (`05-backend`) y el frontend (`06-frontend`).
- Se utiliza para formalizar el modelo de seguridad del sistema antes de diseñar la estrategia integral de testing (`08-testing`).
- Se activa tanto si el proyecto requiere autenticación activa como si requiere certificar documental y técnicamente su exclusión deliberada.

---

## 3. Precondiciones
1. **Artefactos Previos Sellados:**
   - `docs/PRD.md` en estado `APPROVED`, con declaración explícita de `governance_level` y límites de alcance (`IN SCOPE` vs. `OUT OF SCOPE`).
   - `docs/ARCHITECTURE.md` en estado `APPROVED`, con las decisiones estructurales (`AD-xxx`) y componentes (`COMP-xxx`).
   - `docs/DATA_MODEL.md` en estado `APPROVED`, con las entidades de datos autorizadas (`ENT-xxx`).
   - `docs/API_DESIGN.md` en estado `APPROVED`, con los contratos de endpoints autorizados (`EP-xxx`).
2. **Código Base Implementado:**
   - Backend funcional en los módulos de los contextos acotados declarados en `docs/ARCHITECTURE.md` (`src/<bounded_context>/`) y capa de presentación funcional en la ruta declarada por la arquitectura (`src/<frontend_module>/`), aprobados por sus respectivas suites de tests deterministas.

---

## 4. Entradas
La skill consume de forma estricta y exclusiva:
- **Desde `docs/PRD.md`:**
  - `governance_level`: Determina la rama del árbol de decisión (`"bajo"`, `"medio"` o `"alto"`).
  - Cláusula `OUT OF SCOPE`: Lista de funcionalidades prohibidas (ej. registro, login, contraseñas, tokens JWT, perfiles, pagos).
  - Restricciones (`CONST-xxx`): Simplicidad técnica, límites de recursos, restricciones de privacidad y normativa de protección de datos aplicable.
- **Desde `docs/ARCHITECTURE.md`:**
  - Decisiones `AD-xxx` con impacto en la superficie de seguridad: patrón arquitectónico, estrategia de persistencia y de estado (servidor o cliente), stack de presentación y runtime.
  - Componentes del sistema (`COMP-xxx`) y confirmación de ausencia o presencia de módulo auth.
- **Desde `docs/DATA_MODEL.md`:**
  - Inventario de entidades (`ENT-xxx`). Validación de que no existan tablas de credenciales ni usuarios si auth está fuera de alcance.
- **Desde `docs/API_DESIGN.md`:**
  - Inventario de endpoints autorizados (`EP-xxx`). Validación de ausencia de rutas `/auth/*`.
- **Desde el Código Fuente Físico:**
  - Archivos en `src/<bounded_context>/**`, en la capa de presentación (`src/<frontend_module>/**`) y en el punto de entrada de la aplicación declarado en la arquitectura (p. ej. `src/main.py`).

---

## 5. Taxonomía Formal
Toda directiva, decisión o control emitido por esta skill debe utilizar identificadores estables y trazables:
- **`SEC-DEC-xxx` (Security Decision):** Decisiones de gobernanza de seguridad y justificaciones formales de derivación (ej. `SEC-DEC-001`: "Autenticación formalmente excluida del alcance MVP según PRD").
- **`SEC-CTRL-xxx` (Security Control):** Controles técnicos de seguridad aplicados o auditados (ej. `SEC-CTRL-001` para sanitización de inputs, `SEC-CTRL-002` para CORS, `SEC-CTRL-003` para cero hardcoded secrets, `SEC-CTRL-004` para prevención de CWE-532, `SEC-CTRL-005` para mitigación de XSS).
- **`SEC-VULN-xxx` (Vulnerability/Residual Risk):** Identificación y evaluación de riesgos residuales o límites de exposición del sistema.

---

## 6. Regla de Oro Anti-Amnesia y Prohibición de Goldplating
1. **Invariante Negativa Absoluta:**
   Si `governance_level == "bajo"` y la autenticación está listada en `OUT OF SCOPE` en `docs/PRD.md`:
   - El agente **TIENE ESTRICTAMENTE PROHIBIDO** crear:
     - Endpoints de autenticación (`/auth/login`, `/auth/register`, `/auth/refresh`, `/auth/me`, `/login`, `/oauth`).
     - Tablas o modelos de datos de usuarios (`users`, `accounts`, `sessions`, `credentials`, `roles`).
     - Middlewares de tokens JWT, cookies de sesión o encabezados `Authorization: Bearer`.
     - Formularios, campos de contraseña o modales de inicio de sesión en el frontend.
     - Dependencias de autenticación o criptografía pesada en manifiestos (p. ej. en Python: `python-jose`, `passlib`, `bcrypt`, `oauthlib`).
2. **Definición de Amnesia de Scope en Seguridad:**
   Asumir que "todo software serio necesita login" o agregar endpoints de autenticación "por seguridad" cuando el PRD definió un sistema de acceso público anónimo constituye una violación grave de gobernanza. El rol del agente es **certificar la invariante negativa y auditar la seguridad proporcional**, no inventar capas de acceso.
3. **La Seguridad No es Cero:**
   Prescindir de login no significa prescindir de seguridad. El sistema debe contar con controles defensivos mínimos verificables en su transporte, parsing y renderizado.

---

## 7. Workflow de Implementación (Árbol de Derivación Condicional)

```text
INICIO: Cargar docs/PRD.md, docs/ARCHITECTURE.md, docs/DATA_MODEL.md, docs/API_DESIGN.md
  │
  ▼
¿Cuál es el governance_level y la postura de auth en docs/PRD.md?
  │
  ├── RAMA A: governance_level == "bajo" Y auth in PRD.out_of_scope
  │     │
  │     ├── Paso A1: Dictamen de Derivación Condicional (SEC-DEC-001)
  │     │     Formalizar que el sistema es de acceso público anónimo por diseño.
  │     │
  │     ├── Paso A2: Aplicación del TaskSpec Perimetral (TS-AUTH-001)
  │     │     allowed_paths: ["docs/SECURITY.md"]
  │     │     forbidden_paths: ["src/auth/**", "src/users/**", "src/tokens/**",
  │     │                       "src/<out_of_scope_module>/**"]
  │     │     (un patrón por cada módulo excluido en PRD.out_of_scope)
  │     │
  │     ├── Paso A3: Auditoría y Verificación de Controles Técnicos Mínimos (SEC-CTRL-xxx)
  │     │     1. SEC-CTRL-001: Sanitización estricta de entradas en la capa de API (límites de longitud, tipado estricto).
  │     │     2. SEC-CTRL-002: CORS y políticas de transporte restrictivas.
  │     │     3. SEC-CTRL-003: Cero secrets, tokens o credenciales hardcodeadas en disco.
  │     │     4. SEC-CTRL-004: Prevención de fugas de PII y trazas de error desnudas (CWE-532).
  │     │     5. SEC-CTRL-005: Prevención de XSS en frontend (codificación de salida; p. ej. textContent / setAttribute en DOM).
  │     │
  │     └── Paso A4: Emisión del Artefacto Formal
  │           Generar docs/SECURITY.md certificando la postura y controles auditados.
  │
  └── RAMA B: governance_level in ["medio", "alto"] Y auth in PRD.in_scope
        │
        ├── Diseñar RBAC, esquema de tokens (access/refresh), algoritmo de hashing (argon2id/bcrypt).
        └── Implementar middlewares de autenticación, protegiendo rutas sensibles con 401/403.
```

Los módulos excluidos (`src/<out_of_scope_module>/**`) se derivan de la cláusula `OUT OF SCOPE` de `docs/PRD.md` y de los componentes diferidos en `docs/ARCHITECTURE.md`; nunca se fijan de antemano en esta skill.

---

## 8. Señales de Alerta
Si el agente o desarrollador exhibe alguna de las siguientes señales, el arnés debe intervenir y detener la acción:
- Proponer "crear un usuario administrador por defecto para pruebas".
- Añadir parámetros `password`, `token` o `api_key` en llamadas a endpoints públicos.
- Dejar credenciales o cadenas sospechosas de secrets en archivos de código fuente.
- Utilizar `innerHTML` con datos no confiables en el frontend, introduciendo vectores de XSS.
- Responder al requerimiento de seguridad agregando librerías de autenticación (p. ej. paquetes JWT u OAuth del framework web) sin autorización en el PRD.

---

## 9. Contrato de Salida Formal: `docs/SECURITY.md`
En el modo de Derivación Condicional (Gobernanza Baja), la skill produce obligatoriamente el artefacto canónico `docs/SECURITY.md`.

### Estructura y Esquema Obligatorio
El archivo debe contener el siguiente frontmatter y secciones normalizadas:

```markdown
---
status: "APPROVED" | "DRAFT"
version: 1
governance_level: "bajo"
derivation_decision: "SEC-DEC-001"
last_audit: "YYYY-MM-DD"
---

# docs/SECURITY.md — Postura de Seguridad y Gobernanza de Identidades

## 1. Identidad del Sistema y Alcance
Resumen del sistema, nivel de gobernanza asignado en PRD.md y justificación del modelo de acceso.

## 2. Dictamen de Derivación Condicional (SEC-DEC-xxx)
- SEC-DEC-001: Justificación formal de la exclusión de autenticación, login y gestión de usuarios.
Trazabilidad directa con PRD.md (OUT OF SCOPE) y ARCHITECTURE.md (KISS / YAGNI).

## 3. Matriz de Controles Técnicos Mínimos Proporcionales (SEC-CTRL-xxx)
Tabla detallada con:
- SEC-CTRL-001: Sanitización y validación estricta de parámetros en API pública.
- SEC-CTRL-002: Política de CORS restrictivo y encabezados defensivos HTTP.
- SEC-CTRL-003: Ausencia total de secrets o credenciales hardcodeadas (escaneo determinista).
- SEC-CTRL-004: Prevención de fuga de información en logs y errores (CWE-532 / normativa de protección de datos aplicable, CONST-xxx).
- SEC-CTRL-005: Mitigación de Cross-Site Scripting (XSS) en la interfaz gráfica.

## 4. Análisis de Superficie de Ataque y Límites de Exposición
Identificación de los endpoints expuestos (EP-xxx), clasificación de los datos expuestos (p. ej. datos públicos sin PII) y mecanismos de mitigación contra abusos o payloads excesivos.

## 5. Auditoría de Cero Secrets y Privacidad
Evidencia del análisis estático de código verificando que no se registren tokens, claves privadas ni datos sensibles en texto plano.

## 6. Hoja de Ruta para Escalamiento de Gobernanza (Futuro)
Condiciones técnicas y arquitectónicas bajo las cuales se requeriría evolucionar a autenticación activa (ej. introducción de transacciones persistentes por usuario, paneles administrativos o datos personales).
```

---

## 10. Verificación del Artefacto
El arnés verifica el cumplimiento del contrato mediante pruebas deterministas en `tests/harness/test_auth_governance_skill.py`:
1. **Verificación Estructural:** `docs/SECURITY.md` existe, tiene frontmatter válido y contiene todas las secciones obligatorias.
2. **Validación de Identificadores:** Contiene al menos un `SEC-DEC-xxx` y todos los controles mínimos `SEC-CTRL-001` a `SEC-CTRL-005`.
3. **Verificación de Invariante Negativa:**
   - Cero archivos o directorios en rutas prohibidas (`src/auth/`, `src/users/`, `src/tokens/` y los módulos excluidos por `OUT OF SCOPE`).
   - Cero menciones en código a endpoints `/auth/` o formularios de login.
4. **Verificación de ScopePolicy:**
   - El 100% de los cambios documentales y de código pertenecen a `allowed_paths`.

---

## 11. Criterio de Término
La etapa de `auth-governance` se considera concluida satisfactoriamente cuando:
- [ ] La skill `auth-governance` está normalizada con las 11 secciones canónicas y sincronizada en `.agents/skills/07-auth/SKILL.md` y `harness/skills/07_auth_security.md`.
- [ ] La suite determinista `tests/harness/test_auth_governance_skill.py` está implementada y pasa 100% en verde.
- [ ] El artefacto canónico `docs/SECURITY.md` ha sido validado sin violaciones de linter ni de TaskSpec.
- [ ] La suite completa de pruebas de regresión se ejecuta con cero errores.

---

## Reference Context: Demo Implementation (catalogo-carrito-web)

En la implementación de referencia demostrativa (`catalogo-carrito-web`), los principios metodológicos generales de esta skill se instancian de la siguiente manera:

### 1. Rama Aplicada del Árbol de Derivación
- `governance_level: "bajo"` con autenticación en `OUT OF SCOPE` del PRD: se aplica la **RAMA A** (Modo de Auditoría e Invariante Negativa). La demo es un MVP de catálogo público de solo lectura con acceso anónimo.
- `SEC-DEC-001`: "Autenticación formalmente excluida del alcance MVP según PRD".

### 2. Precondiciones y Entradas Concretas
- Backend funcional en `src/catalog/` y frontend funcional en `src/frontend/`, con punto de entrada `src/main.py`.
- Código fuente auditado: `src/catalog/**`, `src/frontend/**` y `src/main.py`.
- Decisiones de `docs/ARCHITECTURE.md` consumidas: `AD-001` (Monolito modular desacoplado), `AD-003` (Persistencia transaccional del carrito en Web Storage / localStorage del cliente), `AD-005` (Frontend Vanilla).
- Componentes: `COMP-001`, `COMP-002` (sin módulo auth).
- Entidades de `docs/DATA_MODEL.md`: `ENT-001`, `ENT-002` (sin tablas de credenciales ni usuarios).
- Endpoints de `docs/API_DESIGN.md`: `EP-001`, `EP-002` (endpoints públicos de solo lectura del catálogo, sin rutas `/auth/*` ni operaciones de mutación).

### 3. TaskSpec Perimetral Concreto (TS-AUTH-001)
```python
TaskSpec(
    task_id="TS-AUTH-001",
    goal="Emitir la postura de seguridad y dictamen de derivación condicional en docs/SECURITY.md",
    category="compliance",
    allowed_paths=["docs/SECURITY.md"],
    forbidden_paths=[
        "src/auth/**",
        "src/users/**",
        "src/tokens/**",
        "src/cart/**",
        "src/payments/**",
    ],
)
```
`src/cart/**` y `src/payments/**` son los módulos excluidos de la demo: el estado del carrito vive en el cliente (`AD-003`) y los pagos están en `OUT OF SCOPE`.

### 4. Instanciación de Controles SEC-CTRL
- `SEC-CTRL-001`: Sanitización estricta de entradas en FastAPI (`max_length`, tipado `int`) en `src/catalog/router.py`.
- `SEC-CTRL-002`: CORS restrictivo en la aplicación FastAPI.
- `SEC-CTRL-003`: Cero secrets, tokens o credenciales hardcodeadas en disco.
- `SEC-CTRL-004`: Prevención de fuga de PII y trazas de error desnudas (CWE-532 / Ley 21.719).
- `SEC-CTRL-005`: Mitigación de XSS en la interfaz gráfica Vanilla mediante `textContent` / `setAttribute`.

### 5. Señales de Alerta Específicas del Stack
- Agregar paquetes como `fastapi-jwt-auth` sin autorización en el PRD.
- Agregar endpoints de autenticación "por seguridad" a un catálogo público de solo lectura.

### 6. Contenido Esperado de docs/SECURITY.md en la Demo
- Superficie de ataque: catálogo público sin PII, expuesto solo mediante `EP-001` y `EP-002`.
- Hoja de ruta de escalamiento: evolución a RBAC ante la introducción de compras persistentes, paneles administrativos o datos personales.
