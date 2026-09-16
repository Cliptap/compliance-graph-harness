# Stack Tecnológico

Este documento define las tecnologías, frameworks y herramientas usadas en el proyecto.

## Backend
- **Framework Principal:** FastAPI (Python)
- **Base de Datos:** PostgreSQL (con migraciones vía Alembic)
- **Orquestación:** Docker y Docker Compose
- **Scripting y Utils:** Python (scripts en la carpeta `analytics` y backend)

## Frontend
- **Framework Principal:** Vue.js (Vue 3)
- **Bundler:** Vite
- **Estilos:** CSS Moderno / TailwindCSS (dependiendo del requerimiento específico)
- **UI/UX:** Prioridad máxima en diseño Premium, animaciones fluidas y accesibilidad.

## Calidad y Herramientas
- **Testing:** Pytest (Backend)
- **Gestión de Entornos:** Contenedores aislados en Docker
- **Control de Versiones:** Git

## Arquitectura
- Separación clara por directorios: `src/frontend`, `src/backend`, `src/database`, `src/analytics`.
- Arquitectura de microservicios o contenedores independientes conectados por red Docker.
