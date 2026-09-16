---
name: context-driven-development
version: 1.0.0
depends_on: []
stage: meta
governance: all
description: Crea y mantiene artefactos de contexto del proyecto (product.md, tech-stack.md, workflow.md, tracks.md). Soporta greenfield y brownfield.
---


# Desarrollo Basado en Contexto

Guía para implementar y mantener el contexto como un artefacto gestionado junto con el código, permitiendo interacciones consistentes con la IA y la alineación del equipo a través de documentación estructurada del proyecto.

## Cuándo usar esta Habilidad

- Configuración de nuevos proyectos con Conductor.
- Comprender la relación entre los artefactos de contexto.
- Mantener la consistencia en las sesiones de desarrollo asistidas por IA.
- Incorporación (onboarding) de nuevos miembros del equipo a un proyecto existente.
- Decidir cuándo actualizar los documentos de contexto.
- Gestión de contextos en proyectos nuevos (Greenfield) vs. proyectos existentes (Brownfield).

## Filosofía Principal

El Desarrollo Basado en Contexto trata el contexto del proyecto como un artefacto de primera clase gestionado junto al código. En lugar de depender de prompts improvisados o documentación dispersa, establece una base persistente y estructurada que informa todas las interacciones con la IA.

Principios clave:

1. **El contexto precede al código**: Define qué vas a construir y cómo, antes de la implementación.
2. **Documentación viva**: Los artefactos de contexto evolucionan junto con el proyecto.
3. **Única fuente de verdad**: Un lugar canónico para cada tipo de información.
4. **Alineación de la IA**: Un contexto consistente produce un comportamiento consistente de la IA.

## El Flujo de Trabajo

Sigue el flujo **Contexto → Especificación y Planificación → Implementación**:

1. **Fase de Contexto**: Establecer o verificar que los artefactos de contexto del proyecto existen y están actualizados.
2. **Fase de Especificación**: Definir requisitos y criterios de aceptación para las unidades de trabajo.
3. **Fase de Planificación**: Dividir las especificaciones en tareas accionables y por fases.
4. **Fase de Implementación**: Ejecutar las tareas siguiendo los patrones de flujo de trabajo establecidos.

## Relación entre Artefactos

### product.md - Define el QUÉ y el POR QUÉ

Propósito: Captura la visión del producto, objetivos, usuarios objetivo y contexto de negocio.

Contenido:
- Nombre del producto y descripción breve.
- Declaración del problema y enfoque de la solución.
- Perfiles de usuario objetivo (personas).
- Características principales y capacidades.
- Métricas de éxito y KPIs.
- Hoja de ruta del producto (a alto nivel).

Actualizar cuando:
- Cambie la visión o los objetivos del producto.
- Se planifiquen nuevas características importantes.
- Cambie la audiencia objetivo.
- Evolucionen las prioridades de negocio.

### product-guidelines.md - Define CÓMO comunicar

Propósito: Establece la voz de la marca, estándares de mensajería y patrones de comunicación.

Contenido:
- Guías de voz y tono de la marca.
- Terminología y glosario.
- Convenciones de mensajes de error.
- Estándares de redacción de cara al usuario.
- Estilo de documentación.

Actualizar cuando:
- Las guías de marca cambien.
- Se introduzca nueva terminología.
- Se necesite refinar los patrones de comunicación.

### tech-stack.md - Define CON QUÉ

Propósito: Documenta las opciones tecnológicas, dependencias y decisiones arquitectónicas.

Contenido:
- Lenguajes y frameworks principales.
- Dependencias clave con versiones.
- Infraestructura y objetivos de despliegue.
- Herramientas y entorno de desarrollo.
- Frameworks de pruebas (testing).
- Herramientas de calidad de código.

Actualizar cuando:
- Se agreguen nuevas dependencias.
- Se actualicen a versiones mayores (major versions).
- Se cambie la infraestructura.
- Se adopten nuevas herramientas o patrones.

### workflow.md - Define CÓMO trabajar

Propósito: Establece las prácticas de desarrollo, controles de calidad y flujos de trabajo del equipo.

Contenido:
- Metodología de desarrollo (TDD, etc.).
- Flujo de trabajo de Git y convenciones de commits.
- Requisitos de revisión de código (Code Review).
- Requisitos de pruebas y objetivos de cobertura.
- Controles de aseguramiento de calidad (QA gates).
- Procedimientos de despliegue.

Actualizar cuando:
- Las prácticas del equipo evolucionen.
- Los estándares de calidad cambien.
- Se adopten nuevos patrones de flujo de trabajo.

### tracks.md - Rastrea QUÉ ESTÁ SUCEDIENDO

Propósito: Registro de todas las unidades de trabajo con su estado y metadatos.

Contenido:
- Tracks activos con su estado actual.
- Tracks completados con sus fechas de finalización.
- Metadatos del track (tipo, prioridad, responsable).
- Enlaces a los directorios individuales de los tracks.

Actualizar cuando:
- Se creen nuevos tracks.
- Cambie el estado de un track.
- Los tracks se completen o archiven.

## Principios de Mantenimiento del Contexto

### Mantener los Artefactos Sincronizados
Asegúrate de que los cambios en un artefacto se reflejen en los documentos relacionados:
- Nueva funcionalidad en `product.md` → Actualizar `tech-stack.md` si se necesitan nuevas dependencias.
- Track completado → Actualizar `product.md` para reflejar nuevas capacidades.
- Cambio en el flujo de trabajo → Actualizar todos los planes de tracks afectados.

### Actualizar tech-stack.md al agregar dependencias
Antes de agregar cualquier nueva dependencia:
1. Verifica si las dependencias existentes pueden resolver la necesidad.
2. Documenta la justificación de las nuevas dependencias.
3. Agrega restricciones de versión.
4. Anota cualquier requerimiento de configuración.

### Actualizar product.md al completar funcionalidades
Después de completar un track de funcionalidad:
1. Mueve la funcionalidad de "planeada" a "implementada" en `product.md`.
2. Actualiza cualquier métrica de éxito afectada.
3. Documenta cualquier cambio de alcance respecto al plan original.

### Verificar el Contexto antes de la Implementación
Antes de iniciar cualquier track:
1. Lee todos los artefactos de contexto.
2. Señala cualquier información desactualizada.
3. Propón actualizaciones antes de proceder.
4. Confirma la precisión del contexto con los interesados (stakeholders).

## Gestión de Proyectos Nuevos vs. Existentes

### Proyectos Nuevos (Greenfield)
Para proyectos nuevos:
1. Ejecuta `/conductor:setup` para crear todos los artefactos de forma interactiva.
2. Responde preguntas sobre la visión del producto, preferencias tecnológicas y flujo de trabajo.
3. Genera guías de estilo iniciales para los lenguajes elegidos.
4. Crea un registro de tracks vacío.

Características:
- Control total sobre la estructura del contexto.
- Se definen estándares antes de que exista el código.
- Establecimiento temprano de patrones.

### Proyectos Existentes (Brownfield)
Para bases de código existentes:
1. Ejecuta `/conductor:setup` con la detección de base de código existente.
2. El sistema analiza el código, las configuraciones y la documentación actuales.
3. Pre-rellena los artefactos basándose en los patrones descubiertos.
4. Revisa y refina el contexto generado.

Características:
- Extraer el contexto implícito del código existente.
- Reconciliar patrones existentes con los patrones deseados.
- Documentar la deuda técnica y los planes de modernización.
- Preservar patrones funcionales mientras se establecen estándares.

## Estructura de Directorios

```
conductor/
├── index.md              # Centro de navegación que enlaza todos los artefactos
├── product.md            # Visión y objetivos del producto
├── product-guidelines.md # Estándares de comunicación
├── tech-stack.md         # Preferencias tecnológicas
├── workflow.md           # Prácticas de desarrollo
├── tracks.md             # Registro de unidades de trabajo
├── setup_state.json      # Estado de configuración reanudable
├── code_styleguides/     # Convenciones específicas de lenguaje
│   ├── python.md
│   ├── typescript.md
│   └── ...
└── tracks/
    └── <track-id>/
        ├── spec.md
        ├── plan.md
        ├── metadata.json
        └── index.md
```

## Verificación post-generación

Antes de confirmar que el contexto está listo, verificar:
- [ ] `product.md` define visión, usuarios, features principales
- [ ] `tech-stack.md` lista lenguajes, frameworks, versiones, herramientas
- [ ] `workflow.md` define metodología, git flow, code review, QA gates
- [ ] `tracks.md` inicializado con tracks activos (o vacío si es greenfield)
- [ ] `index.md` navega correctamente todos los artefactos
- [ ] Los artefactos son consistentes entre sí (no hay contradicciones)
- [ ] Si es brownfield: los patrones extraídos del código coinciden con lo documentado

## Buenas Prácticas

1. **Lee el contexto primero**: Siempre lee los artefactos relevantes antes de comenzar el trabajo.
2. **Actualizaciones pequeñas**: Haz cambios incrementales en el contexto, no reescrituras masivas.
3. **Enlaza decisiones**: Haz referencia al contexto cuando tomes decisiones de implementación.
4. **Versiona el contexto**: Haz commit de los cambios de contexto junto con los cambios de código.
5. **Revisa el contexto**: Incluye la revisión de artefactos de contexto en las revisiones de código (Code Reviews).
6. **Valida regularmente**: Ejecuta la lista de verificación del contexto antes de un trabajo importante.
7. **Comunica los cambios**: Notifica al equipo cuando los artefactos de contexto cambien significativamente.
8. **Preserva la historia**: Usa git para rastrear la evolución del contexto en el tiempo.
9. **Cuestiona la obsolescencia**: Si el contexto parece incorrecto, investiga y actualízalo.
10. **Mantenlo accionable**: Cada ítem del contexto debe informar una decisión o comportamiento.
