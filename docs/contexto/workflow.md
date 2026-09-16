# Flujo de Trabajo y Reglas de Desarrollo

## Metodología
- Desarrollo enfocado en la estabilidad técnica, seguridad de datos (HIPAA) y una calidad visual suprema.
- El trabajo se divide en *tracks* documentados para mantener trazabilidad y enfoque.

## Reglas de IA e Integración (Vibecoding)
- Uso intensivo de Habilidades (Skills) para tareas especializadas.
- La memoria del proyecto vive en estos archivos de contexto en `docs/contexto/`. Si surge una nueva dependencia, decisión arquitectónica o hito del proyecto, los archivos correspondientes **deben** ser actualizados inmediatamente.

## Flujo de Trabajo del Código
1. **Especificación:** Definir claramente los requerimientos de la tarea o el *track* activo.
2. **Implementación:** 
   - Modificar código de `src/frontend` o `src/backend` manteniendo el aislamiento de capas.
   - Todo código nuevo debe ser compatible con la ejecución dentro de contenedores de Docker (`docker-compose`).
3. **Validación:** 
   - Backend: Tests y revisión de vulnerabilidades (seguridad).
   - Frontend: Asegurar que el diseño luzca "Premium", utilizando componentes pulidos y sin caer en apariencias genéricas o básicas.
4. **Actualización de Contexto:** Completar el track en `tracks.md` y actualizar `product.md` o `tech-stack.md` si hubo cambios en la visión o herramientas.
