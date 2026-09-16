# Observabilidad — Iteración 4: Trazabilidad Alta Gobernanza

> **Fecha:** 2026-06-11

## Nivel

**Básico** — logs estructurados en consola (existente). Sin métricas ni tracing para esta iteración.

## Novedades para Trazabilidad

- Los event listeners de auditoría (`events.py`) deben loguear `WARNING` si falla la inserción en `audit_logs` y la operación hace rollback
- Los logs de aplicación NUNCA deben contener valores de `audit_logs.old_value` o `audit_logs.new_value` (eso va a la BD)
- `GET /health` sigue funcionando sin cambios
