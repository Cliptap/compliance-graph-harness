---
status: "APPROVED"
version: 1
governance_level: "bajo"
derivation_decision: "SEC-DEC-001"
last_audit: "2026-10-21"
---

# docs/SECURITY.md — Postura de Seguridad y Gobernanza de Identidades

## 1. Identidad del Sistema y Alcance
El sistema **Catálogo Comercial y Carrito de Compras Desacoplado** (`catalogo-carrito-web`) es una aplicación web transaccional ligera diseñada bajo los principios de arquitectura KISS y YAGNI. De acuerdo con lo establecido en [docs/PRD.md](file:///c:/Users/Bastian/OneDrive/Documentos/GitHub/compliance-graph-harness/docs/PRD.md), el proyecto opera bajo un nivel de gobernanza formalmente clasificado como:

$$\text{governance\_level} = \text{"bajo"}$$

El modelo de acceso al sistema es **100% público y anónimo**: cualquier usuario visitante puede consultar el catálogo de productos y gestionar un carrito de compras interactivo local sin necesidad de identificarse, registrarse ni iniciar sesión.

---

## 2. Dictamen de Derivación Condicional (SEC-DEC-xxx)

### SEC-DEC-001: Exclusión Formal de Autenticación y Cero Goldplating
* **Decisión:** Se dictamina formalmente la **omisión y exclusión total** de mecanismos de autenticación (login, registro, contraseñas, hashing criptográfico), autorización basada en roles (RBAC), gestión de sesiones en servidor y emisión de tokens (JWT o API keys).
* **Fundamentación Contractual:**
  1. **Trazabilidad con PRD.md:** La cláusula `OUT OF SCOPE` de [docs/PRD.md](file:///c:/Users/Bastian/OneDrive/Documentos/GitHub/compliance-graph-harness/docs/PRD.md) sentencia taxativamente:
     > *"Autenticación y autorización: No habrá registro de usuarios, login, passwords, tokens JWT, OAuth ni perfiles de usuario. Todo el acceso es público y anónimo."*
  2. **Trazabilidad con ARCHITECTURE.md:** La decisión `AD-003` sellada en [docs/ARCHITECTURE.md](file:///c:/Users/Bastian/OneDrive/Documentos/GitHub/compliance-graph-harness/docs/ARCHITECTURE.md) establece que el carrito reside íntegramente en Web Storage (`localStorage`) en el cliente, eliminando la necesidad de persistencia transaccional en backend o correlación de identidades de usuario.
  3. **Principio Anti-Amnesia y No-Goldplating:** Introducir capas de autenticación "por si acaso" o "por buenas prácticas estándar" en un sistema de catálogo público viola la Regla 1 y Regla 2 de `AGENTS.md`, añadiendo complejidad accidental y superficies de ataque innecesarias.

---

## 3. Matriz de Controles Técnicos Mínimos Proporcionales (SEC-CTRL-xxx)

Aunque la autenticación de usuarios está excluida por diseño, la postura de seguridad no es nula. Se implementan y auditan deterministamente 5 controles defensivos proporcionales:

| Control | Nombre del Control | Mecanismo Técnico Implementado | Evidencia en Repositorio | Estado |
| :--- | :--- | :--- | :--- | :--- |
| **SEC-CTRL-001** | Sanitización y Validación Estricta de Parámetros | Tipado estricto en FastAPI (`product_id: int`) y límite duro de longitud en búsqueda textual (`len(q) > 100` retorna HTTP 400). Previene inyecciones y DoS por buffer overflow. | `src/catalog/router.py`, `src/catalog/schemas.py` | **CERTIFICADO** |
| **SEC-CTRL-002** | Política de CORS y Transporte Restrictivo | Configuración explícita de `CORSMiddleware` restringida a métodos seguros (`GET`) en endpoints de catálogo, prohibiendo operaciones no autorizadas. | `src/main.py`, `src/catalog/router.py` | **CERTIFICADO** |
| **SEC-CTRL-003** | Auditoría de Cero Secrets Hardcodeados | Escaneo determinista sobre el 100% del código fuente (`.py`, `.js`). Ausencia absoluta de claves privadas, API keys, passwords o tokens en texto plano. | Auditoría estática en `test_auth_governance_skill.py` | **CERTIFICADO** |
| **SEC-CTRL-004** | Prevención de Fugas de Información y PII (CWE-532) | Manejo de excepciones normalizado con `DTO-ERR-001`. Ningún endpoint expone trazas de stack trace desnudas ni datos sensibles en logs. | `src/catalog/router.py`, `src/harness/policy_engine.py` | **CERTIFICADO** |
| **SEC-CTRL-005** | Mitigación de Cross-Site Scripting (XSS) en Frontend | Renderizado del catálogo y carrito utilizando asignación segura (`textContent`, `setAttribute`) en Vanilla DOM, bloqueando inyección de scripts. | `src/frontend/app.js`, `src/frontend/cart.js` | **CERTIFICADO** |

---

## 4. Análisis de Superficie de Ataque y Límites de Exposición

### 4.1 Inventario de Superficie Expuesta
La superficie de ataque del sistema está delimitada exclusivamente a dos operaciones de solo lectura:
- `EP-001`: `GET /api/v1/products?q={searchTerm}`
- `EP-002`: `GET /api/v1/products/{id}`

### 4.2 Evaluación de Vectores de Amenaza y Mitigaciones
1. **Inyección SQL / ORM Injection:**
   - *Riesgo:* Alteración de sentencias SQL mediante el parámetro `q` en `EP-001`.
   - *Mitigación:* Se utiliza SQLAlchemy ORM parametrizado con `func.lower(Product.name).contains(...)` y tipado estricto en repositorio (`src/catalog/repository.py`), impidiendo concatenación directa de strings SQL.
2. **Denegación de Servicio (DoS por Payload Excesivo):**
   - *Riesgo:* Envío de cadenas de búsqueda de varios megabytes para saturar CPU/memoria.
   - *Mitigación:* Validación temprana en `src/catalog/router.py`: si `len(q) > 100`, la petición es rechazada de inmediato con HTTP 400 (`ERR-002: Parámetro inválido`).
3. **Manipulación de Identificador (ID Tampering / Parameter Pollution):**
   - *Riesgo:* Inyección de caracteres no numéricos o negativos en `EP-002`.
   - *Mitigación:* FastAPI valida el tipo `int` en la ruta. Adicionalmente se rechazan IDs $< 1$ con HTTP 400.
4. **Manipulación del Carrito en Cliente:**
   - *Riesgo:* Modificación de los valores almacenados en `localStorage` por parte del usuario.
   - *Mitigación:* Al ser un MVP de catálogo sin procesamiento de pagos en backend (Stripe/PayPal en `OUT OF SCOPE`), el carrito es un estado volátil exclusivamente para la experiencia del usuario. No existe riesgo financiero ni persistencia en base de datos (`AD-003`).

---

## 5. Auditoría de Cero Secrets y Privacidad

Se certifica mediante análisis estático de código determinista:
- **Ausencia de Claves Criptográficas:** Cero certificados PEM, claves privadas RSA/EC, o tokens de acceso en el código fuente.
- **Ausencia de Datos Personales Identificables (PII):** El catálogo solo maneja datos comerciales de productos escolares/papelería (`id`, `name`, `description`, `price`). Ninguna tabla almacena correos, nombres de personas ni direcciones.
- **Conformidad con CWE-532:** No se loguean objetos de solicitud no sanitizados en consola ni en almacenamiento persistente.

---

## 6. Hoja de Ruta para Escalamiento de Gobernanza (Futuro)

Cualquier incorporación de autenticación, control de accesos o persistencia de usuarios en ciclos futuros requerirá una modificación formal previa del PRD y la arquitectura del sistema.
El diseño actual se mantiene 100% enfocado en el alcance MVP público y anónimo, evitando dependencias o abstracciones prematuras no solicitadas.

---

## 7. Matriz de Linaje y Trazabilidad Contractual

| ID de Control / Decisión | Requisito Origen (PRD) | Decisión de Arquitectura | Entidad / Endpoint Afectado | Verificación Técnica |
| :--- | :--- | :--- | :--- | :--- |
| **SEC-DEC-001** | `PRD.out_of_scope` (Auth) | `AD-001`, `AD-003` | N/A (Exclusión sistémica) | `test_auth_physical_scope_enforcement` |
| **SEC-CTRL-001** | `REQ-002`, `CONST-003` | `AD-001` | `EP-001`, `EP-002` | `test_active_repository_security_compliance` |
| **SEC-CTRL-002** | `CONST-003` | `AD-001` | Router de Catálogo | `test_backend_invariants_strictly_read_only` |
| **SEC-CTRL-003** | `CONST-003` | `AD-001` | Totalidad de `src/` | `test_active_repository_security_compliance` |
| **SEC-CTRL-004** | `CONST-003`, CWE-532 | `AD-001` | `DTO-ERR-001` | `test_sensitive_logging_policy_detects_cwe_532` |
| **SEC-CTRL-005** | `REQ-001`, `REQ-003` | `AD-005` | `src/frontend/app.js` | `test_html_semantic_markup_and_ids` |
