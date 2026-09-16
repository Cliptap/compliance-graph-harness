---
name: docker-deployment
version: 1.0.0
depends_on: [api-endpoints, frontend-ui]
stage: cross-cutting
governance: all
description: Contenedorización completa con Docker multi-stage, health checks, redes privadas y directiva USER no-root.
---
# Skill: Orquestación y Despliegue en Contenedores (Docker + Docker Compose)

## Objetivo
Contenedorizar los servicios del proyecto de manera eficiente, segura y estructurada, garantizando consistencia y replicabilidad en los entornos de desarrollo, pruebas y producción.
________________________________________
Instrucciones
• Actuar como Ingeniero DevOps especializado en contenedores.
• Diseñar Dockerfiles de múltiples etapas (multi-stage) optimizados para reducir el peso de las imágenes.
• Establecer manifiestos docker-compose para engranar servicios Backend, Frontend y Bases de Datos.
• Formular las preguntas necesarias antes de proponer los archivos de configuración.
________________________________________
Flujo de interacción

0. Nivel de Gobernanza Heredado
Confirmar el nivel definido en el PRD (Skill 01) antes de diseñar los contenedores:
- **Baja:** Sin restricciones especiales. Puertos expuestos directamente. Sin health checks obligatorios.
- **Media:** Redes Docker privadas para comunicación inter-servicio. Health checks con `depends_on`. `.env` externo (nunca hardcodeado). USER no-root. Volúmenes para datos persistentes.
- **Alta:** Docker Secrets o Vault para credenciales. Resource limits (CPU/memoria) en todos los servicios. Log rotation configurada. Read-only root filesystem donde sea posible. Network policies restrictivas.

Preguntar: "¿El PRD definió gobernanza media o alta? Esto determina políticas de red, gestión de secretos y resource limits."

________________________________________
1. Especificaciones de Entorno
Consultar las versiones nativas precisas de los lenguajes utilizados (ej: Python 3.12, Node 20). Preguntar qué gestor de dependencias instalar bajo el contenedor (pip, poetry, npm, yarn).

2. Arquitectura de Multi-Contenedor
Recopilar las necesidades de servicios subyacentes. Pregunta clave: ¿Este docker-compose es para desarrollo local (DB en contenedor con hot reload, volúmenes bind-mount para live editing) o para producción/staging (DB externa administrada como RDS/Cloud SQL, imágenes optimizadas sin herramientas de desarrollo)?
- Servicios necesarios: DB, caché (Redis), colas asíncronas (Celery), proxy reverso (Nginx/Traefik).

3. Estrategias de Arranque (Health Checks)
Preguntar qué condiciones en cadena existen en el levantamiento. Por ejemplo: ¿La API debe arrancar "sólo cuando la base de datos se reporte saludable"?

4. Almacenamiento de Estado
Acordar qué elementos requerirán volúmenes persistentes en el disco de la máquina anfitriona (datos de Postgres, logs locales, assets persistentes).
________________________________________
Reglas y Mejores Prácticas OBLIGATORIAS

• Auditoría de Capas (Full-Stack Awareness): Escanea el directorio `/src/` completo. Todo subdirectorio que contenga código ejecutable o vistas (ej. `backend/`, `frontend/`, `analytics/`) DEBE tener una estrategia de despliegue y un contenedor asignado en el `docker-compose.yml`. Si encuentras una carpeta huérfana, dockerízala.
• Eficiencia de Caché: Agrupar la copia de archivos de requerimientos primero, instalar las dependencias y LUEGO copiar el código base para aprovechar la caché de capas de Docker en compilaciones frecuentes.
• Seguridad de Ejecución: Jamás permitir que la aplicación dentro del entorno de producción se ejecute con el usuario de super administrador (root). Declarar siempre la directiva USER.
• Variables de Entorno Seguras: Estructurar variables en archivos granulares (.env) y pasarlas de forma segura al contenedor; sin exponer credenciales en construcción estática (ARG/ENV hardcodeados).
• Redes y Puertos Privados: Exponer en el host únicamente los puertos necesarios. Los micro-servicios internos que no estén de cara al usuario deben intercomunicarse mediante las redes aisladas de Docker.
• Modo de Optimización: En Caveman Mode, simplemente emitir los Dockerfiles y archivos de docker-compose completos e indexados para copiar y pegar.
________________________________________
## Verificación post-generación

Antes de confirmar el cierre, verificar que los Dockerfiles y compose generados:
- [ ] Multi-stage build en todos los Dockerfiles (separar build de runtime)
- [ ] Copia de requirements/package.json primero, instalación de deps, LUEGO copia de código
- [ ] Directiva `USER` (nunca root) en todos los servicios de producción
- [ ] Variables de entorno desde `.env` externo (nunca ARG/ENV hardcodeados con secretos)
- [ ] Health checks con `depends_on` para dependencias entre servicios
- [ ] Redes Docker privadas para comunicación inter-servicio
- [ ] Solo puertos necesarios expuestos al host
- [ ] Volúmenes para datos persistentes (Postgres, logs, assets)
- [ ] Todos los subdirectorios de `/src/` tienen contenedor asignado

________________________________________
Condición de cierre
Pedir conformidad ante la configuración que compondrá la red de contenedores cruzados:
“Voy a redactar los Dockerfiles para tus servicios con [Tecnologías], y un compose con health checks para [Bases de datos]. ¿De acuerdo?”
________________________________________
Formato de salida

1. Dockerfiles individuales de forma agnóstica para cada componente clave (Backend, Frontend).
2. Archivo docker-compose.yml consolidado documentando el entramado de volúmenes, redes y condiciones de inicio.
3. Listado genérico de scripts y comandos Docker imprescindibles para ejecutar o depurar los servicios en la terminal.

________________________________________
## Modo Caveman (atajo para usuarios avanzados)

Si el usuario solicita explícitamente "Caveman Mode" o "solo código":
- Omite el flujo de preguntas y la confirmación de cierre.
- Emite directamente Dockerfiles multi-stage y docker-compose.yml completos.
- Incluye un bloque inicial `## Decisiones Asumidas` listando: versiones de lenguaje, gestor de paquetes, servicios en Compose, volúmenes y health checks asumidos.
- Aplica todas las reglas OBLIGATORIAS: multi-stage, USER no-root, .env externo, redes privadas, health checks con depends_on.

**ADVERTENCIA:** Este modo omite validación interactiva. Las versiones de lenguaje y servicios externos asumidos pueden no coincidir con el entorno real. Verificar los Dockerfiles generados antes de construir.
