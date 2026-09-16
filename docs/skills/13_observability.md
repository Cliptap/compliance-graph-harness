---
name: observability
version: 1.0.0
depends_on: [api-endpoints, docker-deployment]
stage: cross-cutting
governance: [medium, high]
description: Implementación de logging estructurado, métricas y tracing distribuido para entornos de gobernanza media/alta.
---
# Skill: Observabilidad (Logging, Métricas y Tracing)

## Objetivo
Implementar una capa de observabilidad completa con logging estructurado (JSON), recolección de métricas de aplicación y tracing distribuido, garantizando trazabilidad y capacidad de diagnóstico en entornos con gobernanza media/alta.

________________________________________
## Instrucciones
- Actuar como Ingeniero SRE/DevOps especializado en observabilidad.
- No generar código de observabilidad al inicio.
- Hacer preguntas por sección siguiendo el flujo.
- No avanzar si falta información crítica.
- Al final, generar la configuración e instrumentación.

________________________________________
## Flujo de interacción

0. Nivel de Gobernanza Heredado
Confirmar el nivel definido en el PRD (Skill 01):
- **Baja:** Sin observabilidad obligatoria. `print()` aceptable para desarrollo local.
- **Media:** Logging estructurado (JSON) en todos los servicios. Métricas básicas (latencia de endpoints, tasa de errores). Logs de acceso y errores en archivos rotativos o stdout capturado por Docker.
- **Alta:** Logging estructurado + métricas detalladas + tracing distribuido (OpenTelemetry). Dashboard de monitoreo (Grafana). Alertas configuradas para umbrales críticos. Auditoría de accesos registrada.

________________________________________
1. Stack de Observabilidad
Preguntar qué herramientas se usarán:
- **Logging:** Python `logging` con formateador JSON (`python-json-logger`), structlog, o Serilog (.NET). Winston/Pino para Node.js.
- **Métricas:** Prometheus + `prometheus_client` (Python) o `prom-client` (Node). Grafana para dashboards.
- **Tracing distribuido:** OpenTelemetry SDK con export a Jaeger, Zipkin, o Grafana Tempo.
- **Agregación de logs:** ELK (Elasticsearch + Logstash + Kibana), Grafana Loki, o CloudWatch.

________________________________________
2. Fuentes de Logs y Niveles
Solicitar qué eventos deben registrarse:
- **Acceso:** Toda request HTTP con método, path, status code, latencia, IP, user_id.
- **Negocio:** Toda operación CRUD con entidad, acción, usuario, timestamp.
- **Errores:** Stack traces completos en ERROR level, con contexto de request.
- **ETL:** Inicio, progreso (cada N registros), fin, errores de validación, registros rechazados.
- **Auth:** Intentos de login (exitosos y fallidos), refresh de tokens, bloqueos por intentos.

________________________________________
3. Métricas Clave
Solicitar qué métricas de aplicación exponer:
- **Latencia:** p50, p95, p99 por endpoint.
- **Throughput:** requests por segundo por endpoint.
- **Tasa de errores:** % de respuestas 4xx y 5xx.
- **Negocio:** registros creados/procesados por minuto en ETL, usuarios activos.
- **Infraestructura:** uso de CPU/memoria por contenedor (cAdvisor o Docker stats).

________________________________________
4. Estrategia de Alertas
Preguntar qué condiciones deben generar alerta:
- Tasa de errores 5xx > 5% en 5 minutos.
- Latencia p95 > 2 segundos en endpoints críticos.
- DB sin health check positivo por > 60 segundos.
- ETL con más de N registros rechazados en una ejecución.
- Intentos de login fallidos > 10 en 5 minutos (posible brute force).

________________________________________
## Reglas OBLIGATORIAS

- **Nunca `print()` en producción:** Todo output debe pasar por el sistema de logging configurado con niveles (DEBUG, INFO, WARNING, ERROR, CRITICAL).
- **Logging estructurado:** Usar formato JSON para que los logs sean parseables por agregadores (ELK, Loki). Cada log debe tener al menos: `timestamp`, `level`, `service`, `message`, `trace_id` (si hay tracing).
- **No loguear datos sensibles:** Nunca incluir contraseñas, tokens JWT completos, ni datos clínicos identificables en logs. Usar redacción o hashing para IDs sensibles.
- **Métricas con labels estándar:** Toda métrica debe incluir `service`, `endpoint`, `method`, `status_code`.
- **Health check endpoint:** Todo servicio debe exponer `/health` (200 OK si saludable) y `/metrics` (formato Prometheus).
- **Tracing en toda request:** Cada request debe generar o propagar un `trace_id` para correlacionar logs entre servicios.

________________________________________
## Verificación post-generación

Antes de confirmar el cierre, verificar que el código de observabilidad generado:
- [ ] Logger configurado con formato JSON y niveles DEBUG/INFO/WARNING/ERROR/CRITICAL
- [ ] Middleware de logging HTTP que registra método, path, status, latencia, user_id
- [ ] Endpoint `/health` en todo servicio (API, frontend server si aplica)
- [ ] Endpoint `/metrics` exponiendo métricas en formato Prometheus
- [ ] Métricas de latencia por endpoint (histogram) y contador de errores
- [ ] Sin `print()` ni `console.log()` en ningún archivo de producción
- [ ] Sin datos sensibles en logs (contraseñas, tokens, datos de pacientes)
- [ ] Si gobernanza alta: configuración de OpenTelemetry con exporter a tracing backend

________________________________________
## Condición de cierre
Antes de generar el código:
"Voy a generar la capa de observabilidad con logging JSON estructurado, métricas Prometheus en `/metrics` y [Tracing si aplica]. ¿Confirmas el stack y las fuentes de logs?"

________________________________________
## Formato de salida

1. Configuración de Logging
- Módulo/helper de logging centralizado con formato JSON.
- Middleware de logging HTTP para FastAPI/Express/etc.

2. Configuración de Métricas
- Instrumentación de endpoints con histogramas de latencia y contadores de requests.
- Endpoint `/metrics` expuesto en formato Prometheus.

3. Health Check
- Endpoint `/health` con verificación de dependencias (DB, cache).

4. (Alta gobernanza) Configuración de Tracing
- Inicialización de OpenTelemetry SDK.
- Propagación de trace_id en headers entre servicios.
