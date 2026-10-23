# Plan y metodología de refinamiento incremental de las Agent Skills

## 1. Contexto y propósito

El objetivo actual no es simplemente completar la normalización de las 12 skills.

El objetivo es construir progresivamente un **workflow de desarrollo gobernado**, en el que las skills:

* consuman información producida por etapas anteriores;
* produzcan artefactos estructurados que puedan ser utilizados por etapas posteriores;
* eviten volver a preguntar decisiones ya resueltas;
* diferencien requisitos, decisiones, restricciones, supuestos y preguntas abiertas;
* respeten el alcance definido;
* puedan ser utilizadas realmente por un agente de programación;
* permitan validar que el workflow funciona en la práctica y no solamente sobre documentación estática.

Por lo tanto, el desarrollo debe realizarse mediante ciclos iterativos:

**Diseño → implementación en Antigravity → pruebas → uso real con agente → revisión en ChatGPT → corrección → nueva prueba → decisión de avanzar.**

ChatGPT actúa como instancia de revisión metodológica y de coherencia del diseño; Antigravity actúa como instancia de implementación y experimentación sobre el repositorio.

No se debe asumir que una skill está terminada simplemente porque sus archivos, tests o documentación existen.

---

# 2. Regla fundamental de avance

Para cada skill se utilizarán cuatro estados:

### IMPLEMENTACIÓN

La estructura de la skill y sus artefactos han sido modificados.

### VALIDACIÓN TÉCNICA

Los tests deterministas y de integración básica pasan.

### VALIDACIÓN CON AGENTE

Un agente real utiliza la skill en un caso controlado y se verifica que respeta su contrato.

### APROBADA PARA SIGUIENTE SKILL

Después de revisar los resultados, ChatGPT y el equipo consideran que el comportamiento observado es suficientemente estable para comenzar la siguiente skill.

Una skill puede estar en IMPLEMENTACIÓN o VALIDACIÓN TÉCNICA y aun así requerir cambios.

Nunca utilizar:

> “Skill X completada”

cuando solamente se hayan ejecutado tests deterministas.

Usar en cambio formulaciones como:

* Implementada.
* Validación técnica superada.
* Validación con agente pendiente.
* Observaciones pendientes.
* Aprobada para continuar.

---

# 3. Bucle de desarrollo que debe repetirse

Cada skill debe seguir aproximadamente este ciclo.

## Etapa A — Auditoría

Antes de modificar una skill:

1. leer la skill actual;
2. identificar qué hace actualmente;
3. identificar qué artefactos produce;
4. identificar qué información debería consumir;
5. identificar qué problemas tiene;
6. identificar dependencias con otras skills;
7. revisar los tests existentes;
8. revisar cualquier resultado previo de experimentos.

No modificar inmediatamente.

Primero producir un diagnóstico.

---

## Etapa B — Definición del contrato

Para cada skill debe quedar explícito:

### Inputs

Qué información recibe.

Ejemplo:

```text
01-prd
    ↓
02-architecture
```

significa que 02 debe consumir el PRD existente y no volver a pedir al usuario información que ya fue resuelta allí.

### Outputs

Qué artefactos produce.

### Invariantes

Qué nunca debería ocurrir.

### Preguntas abiertas

Qué puede permanecer sin resolver.

### Decisiones

Qué puede proponer, heredar o registrar.

### Dependencias

Qué otras skills necesitan su salida.

---

## Etapa C — Implementación

Antigravity modifica exclusivamente la skill en cuestión y los tests necesarios.

No debe:

* normalizar otras skills simultáneamente;
* reorganizar todo el repositorio;
* introducir infraestructura nueva sin justificación;
* introducir JSON como segunda fuente de verdad;
* crear MCP, RAG, bases vectoriales o arquitecturas multiagente por anticipación;
* cerrar decisiones que el contrato todavía considera abiertas.

---

# 4. Cuatro niveles de prueba

Cada skill deberá probarse en cuatro niveles.

## Nivel 1 — Prueba estructural

Comprueba que la skill tiene la estructura esperada.

Ejemplos:

* existe `SKILL.md`;
* tiene metadata;
* define Inputs;
* define Outputs;
* define Workflow;
* define Constraints;
* define Verification;
* utiliza IDs correctamente cuando corresponda.

Esto demuestra que el artefacto está bien construido.

No demuestra que el workflow funcione.

---

## Nivel 2 — Prueba de interoperabilidad

Comprueba que la salida de una skill puede utilizarse como entrada de la siguiente.

Ejemplo:

```text
PRD
 ↓
Architecture
```

Debe verificarse que Architecture:

* reconoce los requisitos del PRD;
* utiliza sus decisiones;
* mantiene sus restricciones;
* no vuelve a preguntar decisiones ya resueltas;
* no transforma automáticamente el alcance funcional en detalles técnicos no autorizados.

---

## Nivel 3 — Prueba con agente real

Esta es la prueba más importante en esta etapa.

Debe utilizarse un coding agent real en Antigravity.

Idealmente:

* contexto nuevo;
* instrucciones mínimas;
* artefactos previamente generados;
* tarea concreta;
* observación de qué pregunta;
* observación de qué asume;
* observación de qué produce;
* revisión del resultado.

Esto permite detectar problemas que los tests deterministas no pueden detectar.

Por ejemplo:

```text
PRD dice:
OUT OF SCOPE = pagos

↓

Architecture propone:
Stripe Payment Service
```

Un test de estructura puede pasar perfectamente.

Un agente real debería revelar que existe una violación conceptual del contrato.

---

## Nivel 4 — Regresión

Cada vez que una skill sea aprobada y se avance a la siguiente, deben seguir ejecutándose los tests anteriores.

La evolución debe ser acumulativa:

```text
01
↓
01 + 02
↓
01 + 02 + 03
↓
01 + 02 + 03 + 04
...
```

Así se evita que corregir 04 rompa el comportamiento conseguido con 01–03.

---

# 5. La primera decisión inmediata: probar 01-prd

No recomiendo comenzar todavía con `02-architecture`.

Primero debe realizarse una **prueba real de 01-prd**.

La prueba debe utilizar un caso pequeño y controlado, distinto de la implementación del proyecto principal para evitar que el conocimiento previo del agente contamine el resultado.

Por ejemplo:

### Caso

Sistema de catálogo y carrito de compras.

El usuario solicita:

* catálogo;
* búsqueda de productos;
* carrito;
* modificación de cantidades.

Y explícitamente establece:

```text
Fuera de alcance:
- pagos
- autenticación
- recomendaciones
```

La prueba debe verificar si el agente:

1. transforma la intención en requisitos;
2. genera IDs coherentes;
3. establece IN SCOPE;
4. establece OUT OF SCOPE;
5. genera criterios de aceptación;
6. mantiene preguntas realmente abiertas;
7. evita decidir tecnologías todavía;
8. no genera `allowed_paths`;
9. no confunde alcance funcional con alcance físico del repositorio;
10. puede dejar el PRD en estado DRAFT;
11. requiere confirmación humana para APPROVED.

---

# 6. Fire Tests obligatorios para 01-prd

## Fire Test 1 — Anti-amnesia

Debe existir una decisión o requisito explícito en la entrada.

Después se continúa el workflow sin volver a proporcionar esa información.

Resultado esperado:

El agente debe utilizar la información existente y no volver a preguntar lo mismo sin una razón válida.

Ejemplo:

```text
REQ-001:
El usuario debe poder agregar productos al carrito.
```

Posteriormente, el agente que consume el PRD debe utilizar ese requisito.

No debería preguntar:

> “¿El sistema debe permitir agregar productos al carrito?”

---

## Fire Test 2 — IN/OUT Scope

Debe verificarse que:

```text
IN SCOPE
```

y

```text
OUT OF SCOPE
```

sean interpretados como alcance funcional, no como lista de archivos que el agente puede modificar.

Esto es especialmente importante porque:

```text
PRD Scope ≠ allowed_paths
```

---

## Fire Test 3 — No decisión técnica prematura

El usuario solicita una capacidad funcional pero no define:

* framework;
* ORM;
* base de datos;
* proveedor cloud;
* arquitectura concreta.

El agente no debe inventar que esas decisiones ya estaban aprobadas.

Puede proponer alternativas en una etapa apropiada, pero deben distinguirse de decisiones heredadas.

---

## Fire Test 4 — DRAFT / APPROVED

Debe comprobarse que:

```text
DRAFT
```

no se convierta automáticamente en:

```text
APPROVED
```

sin una confirmación humana explícita.

---

## Fire Test 5 — Preguntas realmente abiertas

Debe comprobarse que `OPEN-*`:

* aparezcan solamente cuando existe una incertidumbre real;
* no se utilicen como reemplazo de requisitos ya definidos;
* no sean inventadas artificialmente para llenar el documento.

---

# 7. Gate de decisión después de 01-prd

Después de ejecutar las pruebas, no se debe decidir automáticamente continuar.

Se debe realizar una revisión conjunta:

### Resultado A — 01 funciona

Si:

* tests deterministas pasan;
* Fire Tests pasan;
* agente real respeta el contrato;
* no aparecen problemas conceptuales importantes;

entonces:

**Aprobada 01-prd → comenzar 02-architecture.**

### Resultado B — problemas menores

Si:

* el modelo funciona;
* aparecen pequeñas ambigüedades;
* no hay problemas arquitectónicos;

entonces:

**corregir 01 → repetir pruebas → volver a evaluar.**

### Resultado C — problema conceptual

Si el agente:

* reinterpreta requisitos;
* pierde restricciones;
* inventa decisiones;
* confunde scope con paths;
* modifica el significado del contrato;

entonces:

**no avanzar a 02.**

Primero se corrige el contrato de 01.

Este punto es importante: un fallo de interoperabilidad se considera evidencia de que la skill aún no está madura.

---

# 8. Orden recomendado para las skills restantes

El orden base es:

```text
01 PRD
 ↓
02 Architecture
 ↓
03 Data Model
 ↓
04 API Design
 ↓
05 Backend
 ↓
06 Frontend
 ↓
07 Auth / Governance
 ↓
08 Testing
 ↓
09 CI/CD
 ↓
10 Deployment
 ↓
11 Observability
 ↓
12 Documentation
```

Sin embargo, esto debe entenderse como una **dependencia lógica**, no como un waterfall rígido.

Por ejemplo, Testing debe tener influencia transversal sobre las etapas anteriores.

La skill 08 no debería convertirse simplemente en “la que se ejecuta al final”.

---

# 9. Metodología de refinamiento por skill

## 02 — Architecture

### Debe consumir

* PRD aprobado;
* requisitos;
* criterios de aceptación;
* restricciones;
* supuestos;
* preguntas abiertas.

### Debe producir

* componentes;
* responsabilidades;
* relaciones;
* decisiones arquitectónicas;
* trade-offs;
* restricciones técnicas;
* preguntas todavía abiertas.

### Debe evitar

Convertir automáticamente propuestas del agente en decisiones aprobadas.

Debe distinguir:

```text
Inherited
Decision
Proposed
Constraint
Open Question
```

### Pruebas especiales

**No contradicción con PRD**

Un requisito explícito del PRD no puede desaparecer.

**No expansión silenciosa de scope**

El agente no puede incorporar funcionalidades fuera del PRD como si fueran necesarias.

**No re-pregunta**

No debería solicitar nuevamente información disponible.

**Decisiones heredadas**

Debe poder identificar qué venía decidido desde PRD y qué fue decidido por Architecture.

---

# 10. 03 — Data Model

### Debe consumir

PRD + Architecture.

### Debe producir

* entidades;
* relaciones;
* atributos;
* reglas de integridad;
* restricciones de datos;
* decisiones de persistencia cuando correspondan.

### Debe evitar

Inventar entidades sin relación con requisitos.

### Pruebas

Cada entidad importante debe poder rastrearse hasta uno o más requisitos.

Debe poder detectarse:

```text
Entity sin requisito asociado
```

como posible cambio huérfano.

También:

```text
Requirement sin representación razonable en el modelo
```

como posible cobertura incompleta.

---

# 11. 04 — API Design

### Debe consumir

PRD + Architecture + Data Model.

### Debe producir

* contratos API;
* operaciones;
* entradas;
* salidas;
* errores;
* validaciones;
* reglas de acceso pertinentes.

### Pruebas

Cada endpoint debe poder relacionarse con una capacidad o requisito.

Debe verificarse que:

* no existan endpoints para features fuera de scope;
* las entidades utilizadas existan;
* las operaciones sean coherentes con la arquitectura;
* las reglas de aceptación puedan traducirse posteriormente a tests.

---

# 12. 05 — Backend

Esta skill ya pasa del diseño a la construcción.

### Debe consumir

Los artefactos anteriores.

### Debe producir

Cambios reales en código.

Aquí empieza a ser especialmente importante distinguir:

```text
Instruction
↓
Task
↓
Allowed technical scope
↓
Implementation
↓
Validation
```

### Pruebas

No basta con verificar que el código compila.

Debe comprobarse:

* trazabilidad requisito → implementación;
* respeto de restricciones;
* tests asociados;
* ausencia de cambios fuera de alcance;
* validación funcional.

Aquí el concepto de **orphan change** comienza a ser especialmente útil.

---

# 13. 06 — Frontend

Debe consumir principalmente:

* PRD;
* API Contract;
* Architecture;
* criterios de aceptación.

Debe producir:

* UI;
* interacción;
* integración API;
* manejo de estados;
* validación de comportamiento.

Aquí se deberá recuperar posteriormente uno de los temas del Sprint 2 del profesor:

**cómo incorporar una metodología de creación/revisión agentic de UI/UX que evite resultados de baja calidad o “vibecoded”.**

No es necesario resolverlo durante la normalización inicial de la skill.

Primero debe existir un workflow básico reproducible.

---

# 14. 07 — Auth / Governance

Esta skill debe tener carácter **condicional**.

No todos los proyectos necesitan exactamente el mismo nivel de autenticación o gobernanza.

Debe consumir las restricciones y nivel de gobierno establecidos anteriormente.

### Pruebas importantes

Debe comprobarse que:

* no se introduce autenticación innecesariamente;
* si existe un requisito de seguridad, éste no desaparece;
* las decisiones de acceso tengan trazabilidad;
* los datos personales sensibles sean tratados bajo las restricciones correspondientes.

En el proyecto de investigación esta skill también deberá eventualmente conectarse con las restricciones derivadas de la Ley 21.719.

No conviene todavía convertirla en un mecanismo jurídico completo.

---

# 15. 08 — Testing

Esta skill es especial porque no debe tratarse únicamente como otra etapa.

Su función debe ser transversal.

Debe consumir:

```text
Acceptance Criteria
+
Architecture
+
API
+
Implementation
```

y producir una correspondencia:

```text
AC-001 → Test-001
AC-002 → Test-002
...
```

Esto permite introducir posteriormente una métrica como:

**Acceptance Coverage**

Por ejemplo:

```text
Acceptance Coverage =
AC con test aprobado
---------------------
AC totales
```

### Pruebas

Debe detectarse:

* AC sin test;
* test sin AC;
* requisitos críticos sin validación;
* tests que no prueban realmente el criterio declarado.

---

# 16. 09 — CI/CD

La skill debe encargarse de automatizar la validación ya definida.

Debe consumir principalmente:

* tests;
* validaciones;
* restricciones;
* estructura del proyecto.

Debe evitar que CI/CD se convierta en una colección arbitraria de herramientas.

### Pruebas

Debe existir al menos un flujo reproducible:

```text
Change
→ Build
→ Tests
→ Validation
→ PASS / FAIL
```

y comprobarse que un fallo real produce un estado claramente detectable.

---

# 17. 10 — Deployment

Debe transformar el resultado validado en una unidad desplegable.

Debe separar:

```text
desarrollo
validación
deployment
```

### Pruebas

Debe poder reproducirse un deployment controlado y verificarse que no introduce cambios no previstos.

No se debe convertir todavía en una plataforma DevOps completa.

---

# 18. 11 — Observability

Debe capturar evidencia útil del comportamiento del sistema.

La finalidad dentro del proyecto no es “tener logs porque sí”.

Debe responder:

> ¿Qué ocurrió, qué cambio lo provocó y cómo puedo reproducirlo?

Debe considerar:

* cambios;
* validaciones;
* resultados;
* errores;
* evidencia relevante;
* eventualmente métricas del harness.

---

# 19. 12 — Documentation

Esta skill debería aparecer al final del workflow porque tiene acceso a la información consolidada.

Debe generar documentación derivada de:

* PRD;
* Architecture;
* Model;
* API;
* implementación;
* pruebas;
* deployment;
* observabilidad.

Debe evitar convertirse en otra fuente de verdad.

La documentación debe **reflejar los artefactos existentes**, no inventarlos.

---

# 20. Qué debe probarse después de cada nueva skill

Cuando se incorpore una nueva skill, deben existir como mínimo:

### Tests estructurales

¿La skill cumple su contrato documental?

### Tests de interoperabilidad

¿Puede consumir correctamente el output de la skill anterior?

### Tests de no regresión

¿Sigue funcionando el workflow anterior?

### Fire Test

¿El agente falla de manera visible cuando viola una restricción?

### Prueba real con agente

¿El comportamiento observado coincide con el comportamiento esperado?

---

# 21. Prueba acumulativa

A medida que avanza el workflow, los experimentos deben crecer:

### Etapa 1

```text
01
```

### Etapa 2

```text
01 → 02
```

### Etapa 3

```text
01 → 02 → 03
```

### Etapa 4

```text
01 → 02 → 03 → 04
```

y así sucesivamente.

Esto permite identificar exactamente dónde apareció una regresión.

---

# 22. Rol de ChatGPT y Antigravity

El proyecto debe mantener deliberadamente una separación entre ambos roles.

## Antigravity

Responsable de:

* inspeccionar el repositorio;
* implementar cambios;
* ejecutar tests;
* realizar experimentos con agentes;
* reportar evidencia;
* documentar resultados.

## ChatGPT

Responsable de:

* revisar si el diseño sigue siendo coherente;
* detectar overengineering;
* cuestionar afirmaciones demasiado fuertes;
* revisar contratos entre skills;
* analizar resultados experimentales;
* decidir, junto al equipo, si una skill debe modificarse o si puede avanzar.

ChatGPT no debe reemplazar las pruebas reales.

Antigravity tampoco debe decidir unilateralmente que una skill está “validada” cuando solamente existen tests deterministas.

---

# 23. Formato de entrega de Antigravity después de cada ciclo

Después de cada skill debería entregar algo parecido a:

```text
## Skill
02-architecture

## Estado
VALIDACIÓN CON AGENTE PENDIENTE

## Cambios realizados
...

## Tests ejecutados
X passed

## Pruebas de interoperabilidad
PASS / FAIL

## Fire Tests
FT-01 PASS
FT-02 PASS
...

## Prueba con agente
Resultado:
...

## Problemas encontrados
...

## Hipótesis
...

## Decisiones propuestas
...

## Cambios que requieren revisión
...

## Recomendación
CONTINUAR / REFINAR

## Evidencia
...
```

Esto evita frases genéricas como:

> “Skill completada exitosamente.”

---

# 24. Criterio para decidir entre “corregir” y “continuar”

Después de cada ciclo se debe clasificar cada hallazgo.

### Tipo A — Bug de implementación

La idea es correcta, pero el código/documentación está mal.

→ Corregir.

### Tipo B — Ambigüedad contractual

El contrato no deja claro qué debería ocurrir.

→ Revisar el diseño de la skill.

### Tipo C — Problema de interoperabilidad

La skill funciona sola, pero no funciona con la anterior.

→ No avanzar. Corregir contrato.

### Tipo D — Problema de comportamiento del agente

El contrato es correcto, pero el agente no lo sigue consistentemente.

→ Diseñar una estrategia de prompts/instrucciones/validación y volver a probar.

### Tipo E — Limitación experimental

El workflow funciona, pero la evidencia todavía es insuficiente para afirmar que aporta valor.

→ Continuar desarrollo, pero no declarar impacto.

---

# 25. Principio de investigación

Durante esta etapa todavía no se está intentando demostrar:

> “El harness mejora el desarrollo de software.”

Se está intentando demostrar primero:

> **“Es posible construir un workflow de skills interoperables que un agente de programación pueda seguir y que permita gobernar, verificar y rastrear sus cambios.”**

Una vez que esto esté suficientemente consolidado, recién tiene sentido realizar la evaluación comparativa:

```text
Agente sin Harness
        VS
Agente con Harness
```

y eventualmente estudiar dimensiones como:

* cumplimiento de requisitos;
* cambios fuera de alcance;
* defectos;
* cobertura de aceptación;
* tiempo;
* iteraciones;
* trazabilidad;
* incidentes relacionados con datos personales.

---

# 26. Estado inmediato del proyecto

El siguiente paso concreto es:

```text
01-PRD
   ↓
PRUEBA REAL CON AGENTE
   ↓
REVISIÓN DE RESULTADOS
   ↓
¿Contrato adecuado?
   ├── NO → modificar 01 → repetir
   └── SÍ
        ↓
02-Architecture
```

Por ahora **no se debe normalizar 02 automáticamente**.

Primero hay que obtener evidencia real de cómo se comporta 01 cuando un agente la utiliza en un contexto nuevo.

Ese resultado será precisamente la primera fuente empírica para decidir cómo debe evolucionar el contrato de las skills siguientes.

---

# 27. Regla general para todo el trabajo restante

La regla que debe guiar las próximas semanas es:

> **Una skill no se diseña completamente de antemano. Se diseña una primera versión, se utiliza con un agente real, se observan sus fallos, se revisa el contrato y recién entonces se estabiliza.**

Por eso el workflow de investigación debe ser:

```text
Hipótesis
   ↓
Diseño
   ↓
Implementación en Antigravity
   ↓
Prueba determinista
   ↓
Prueba de integración
   ↓
Uso con agente real
   ↓
Observaciones
   ↓
Revisión crítica en ChatGPT
   ↓
Refinamiento
   ↓
Nueva prueba
   ↓
Decisión de avanzar
```

Este ciclo debe repetirse para cada skill.

La calidad del proyecto no estará determinada por cuántas skills existan, sino por cuánto de ese workflow pueda demostrarse que funciona realmente.
