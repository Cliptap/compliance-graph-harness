# Registro de Chat - Etapa 4: Implementación Frontend

**Usuario:**
> Terminamos el backend e hicimos el commit. Ahora seguimos con el siguiente skill: Frontend. Usa `frontend_ui.md` para armar un dashboard básico. Que no use frameworks complicados (Ni React, ni NPM), que se comunique directo con el `localhost:8000`.

**Agente:**
> ¡Perfecto! Para un proyecto de gobernanza técnica baja con una experiencia limpia y sin overhead, utilizaremos Vanilla JS y Tailwind CSS vía CDN.
> 
> Archivos creados:
> - `src/frontend/index.html`: Estructura principal, listado de pacientes tipo tabla y un modal para crear/editar registros.
> - `src/frontend/app.js`: Script nativo con la gestión del DOM (Document Object Model) y llamadas mediante `fetch()` directo a la API de FastAPI.
> 
> Implementando responsividad para la recepcionista.

**Usuario:**
> Se ve bien, ¡Abre el Simple Browser para validar que corra!

**Agente:**
> Listo, he corrido `python -m http.server 8080 --directory src/frontend` en segundo plano para servir los estáticos y he abierto el "Simple Browser". ¿Algún detalle visual a pulir?

**Usuario:**
> Cuando pulso el menú de tres puntitos en la fila de un paciente, el dropdown queda oculto bajo el borde de la tabla y no se ve bien.

**Agente:**
> Entendido. Removiendo la clase `overflow-hidden` del contenedor de la tabla y ajustando las clases de Tailwind en `index.html` para `overflow-visible`. Refresca el panel y verás el menú flotante sobresaliendo del div sin ser cortado.