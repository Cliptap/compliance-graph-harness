---
name: observability
version: 2.0.0
depends_on: [prd-generation, backend-implementation]
stage: cross-cutting
project_types: [web_app, api, data_pipeline]
governance: [medio, alto]
description: Implementacion de observabilidad. Define logging estructurado, metricas, health checks, alerts y tracing.
---

# Skill: Observabilidad

## Objetivo
Configurar logging, metricas y monitoreo para entender que hace el sistema en
produccion y detectar problemas tempranamente.

## Instrucciones
- **NO implementar observabilidad avanzada si la gobernanza es baja.**
- Preguntar que nivel de observabilidad necesita el proyecto AHORA.
- Preguntar por seccion.
- Al final, generar la configuracion de observabilidad.

---

## Flujo de Interaccion

### 1. Nivel de Observabilidad

```
? Que nivel de observabilidad necesita el proyecto en esta etapa?

a) Minimo — solo logs en consola (print / console.log)
   Mejor para: MVPs, prototipos, desarrollo local

b) Basico — logs estructurados (JSON) con niveles (DEBUG, INFO, WARNING, ERROR)
   [RECOMENDADO para cualquier proyecto que vaya a produccion]

c) Intermedio — logs estructurados + health checks + metricas basicas
   Metricas: latencia de endpoints, tasa de errores, uso de DB

d) Avanzado — logs + metricas + tracing distribuido + alertas
   Tracing: OpenTelemetry, propagacion de trace_id entre servicios
   Alertas: notificacion cuando algo falla (email, Slack, Discord)

⏳ Esperando tu respuesta.
```

### 2. Logging Estructurado

```
? Como implementamos el logging?

Python:
a) structlog — [RECOMENDADO] Logging estructurado, contexto encadenable
b) logging + python-json-logger — standard library con formato JSON
c) loguru — API simple, colores en desarrollo

TypeScript:
a) pino — [RECOMENDADO] El mas rapido, JSON nativo
b) winston — Flexible, muchos transports

Go:
a) slog — [RECOMENDADO] Standard library desde Go 1.21, estructurado
b) zerolog — Zero allocation, muy rapido
c) zap — Rapido, estructurado, popular

? Que datos debe incluir cada log?
  - timestamp (ISO 8601)
  - level (debug, info, warning, error)
  - message (descripcion)
  - request_id (para correlacionar logs de un mismo request)
  - user_id (si esta autenticado, NUNCA loguear informacion sensible)
  - duration_ms (para operaciones que toman tiempo)
```

### 3. Metricas

```
? Que metricas necesitas exponer?

a) Metricas de aplicacion:
   - http_requests_total (contador de requests por endpoint, metodo, status)
   - http_request_duration_seconds (histograma de latencia)
   - db_query_duration_seconds (latencia de queries)

b) Metricas de negocio:
   - usuarios_registrados_total
   - ordenes_creadas_total
   - errores_validacion_total

c) Sin metricas — no necesario en esta etapa

? Como se exponen las metricas?
  - Endpoint /metrics en formato Prometheus
  - Libreria: prometheus_client (Python), prom-client (TypeScript)

? Necesitas un dashboard?
  - Grafana con dashboards predefinidos
  - Solo el endpoint de metricas, dashboard despues
```

### 4. Health Checks

```
? Que health checks implementamos?

a) Liveness: GET /health → 200 OK si la app esta viva
   [MINIMO RECOMENDADO]

b) Readiness: GET /health/ready → verifica DB, Redis, servicios externos
   Solo 200 si todo esta listo para recibir trafico

c) Startup: GET /health/startup → verifica inicializacion lenta
   (migraciones, carga de modelos ML, warmup de cache)

d) Sin health checks — solo para MVPs sin orquestador

⏳ Esperando tu respuesta.
```

### 5. Tracing (Opcional, Avanzado)

```
? Necesitas tracing distribuido?

a) No — el proyecto es un monolitico o no necesita tracing

b) Si — OpenTelemetry para propagar trace_id entre servicios
   Exporters: Jaeger, Zipkin, Grafana Tempo, Datadog

? Auto-instrumentacion o manual?
  Auto: otel CLI o agent que inyecta tracing automaticamente
  Manual: decorators/middleware en endpoints y servicios
```

### 6. Alertas (Gobernanza Alta)

```
Gobernanza {nivel}. ?Necesitas alertas?

? Que condiciones deberian disparar una alerta?

- Tasa de errores 5xx > 1% en 5 minutos
- Latencia p95 > 500ms por 10 minutos
- Health check fallando por mas de 1 minuto
- DB sin conexion
- Disco lleno (>90%)
- Certificado SSL por expirar

? A donde se envian las alertas?
  - Email
  - Slack / Discord webhook
  - PagerDuty / OpsGenie (on-call)
```

---

## Verificacion Post-Generacion

- [ ] El formato de log esta definido (campos y niveles)
- [ ] Todos los logs usan el formato estructurado acordado
- [ ] NO se loguean secrets, passwords ni datos sensibles
- [ ] El health check basico esta implementado (GET /health)
- [ ] Las metricas estan expuestas (si se solicito)
- [ ] El tracing esta configurado (si se solicito)
- [ ] Las alertas estan configuradas (si se solicito)

## Condicion de Cierre

```
Voy a generar la configuracion de observabilidad.
¿Confirmas que el nivel de observabilidad es el adecuado?

⏳ Esperando tu confirmacion.
```
