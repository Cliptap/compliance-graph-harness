# Implementación Frontend — Iteración 4: Trazabilidad Alta Gobernanza

> **PRD:** `docs/prd/04_trazabilidad_alta_gobernanza_prd.md`
> **Arquitectura:** `docs/arquitectura/04_trazabilidad_alta_gobernanza.md`
> **Fecha:** 2026-06-11

## 1. Framework

**Vue 3 + Vite + Tailwind CSS** (existente). Sin cambios.

## 2. Estilos

**Tailwind CSS** (existente). Sin cambios.

## 3. Estados UI (OBLIGATORIO)

La nueva vista de auditoría debe implementar los 3 estados:

| Estado | Qué muestra |
|--------|------------|
| **Empty** | "No hay registros de auditoría" + icono |
| **Loading** | Skeleton con 5 filas simuladas |
| **Error** | "Error al cargar auditoría" + botón "Reintentar" |

Estados adicionales:
- **Éxito post-borrado:** Toast "150 registros de auditoría eliminados"
- **Confirmación borrado:** Modal "¿Estás seguro? Escribe DELETE para confirmar"

## 4. Pantalla Nueva: Vista de Auditoría

**Ruta:** `/audit` (protegida, solo admin)

**Componentes:**
```
src/frontend/src/
├── components/
│   └── audit/
│       ├── AuditView.vue        ← NUEVO: vista principal
│       ├── AuditFilters.vue     ← NUEVO: barra de filtros
│       ├── AuditTable.vue       ← NUEVO: tabla de resultados
│       └── AuditDeleteModal.vue ← NUEVO: modal de confirmación
```

**Filtros disponibles:**
- Select: tipo de entidad (paciente/médico/cita/todos)
- Input: usuario (changed_by)
- Select: operación (CREATE/UPDATE/DELETE/todas)
- Date picker: desde / hasta

**Tabla de resultados:**
| Fecha | Entidad | ID | Campo | Valor Anterior | Valor Nuevo | Operación | Usuario |

Con paginación (offset-based, controles anterior/siguiente).

## 5. Navegación

Se agrega ítem "Auditoría" en el menú/sidebar, visible solo para admin.

## 6. Consumo de API

- Axios (existente) — interceptor JWT ya configurado
- Nuevo archivo `src/frontend/src/api/audit.js` con:
  - `fetchAuditLogs(params)` → GET /api/v1/audit
  - `deleteAuditLogs()` → DELETE /api/v1/audit

## 7. Responsive

Mobile-first con Tailwind. La tabla de auditoría colapsa a cards en mobile.

## 8. Accesibilidad

Básica: HTML semántico, labels en filtros, `aria-label` en botones, focus management en modal de confirmación.

## 9. Flujo de Usuario — Vista de Auditoría

```
Admin hace clic en "Auditoría" (sidebar)
         │
         ▼
Carga AuditView.vue
         │
    ┌────┴────┐
    │ LOADING │ ← Skeleton 5 filas
    └────┬────┘
         │
    ┌────┴────┐
    │  EMPTY  │ ← "No hay registros" (si total=0)
    │  DATA   │ ← Tabla con resultados (si total>0)
    └────┬────┘
         │
   Admin aplica filtros → refetch
         │
   Admin hace clic en "Eliminar logs"
         │
         ▼
   Modal: "Escribe DELETE para confirmar"
         │
   Input "DELETE" → botón habilita
         │
   Clic en "Confirmar" → DELETE /api/v1/audit
         │
   Toast: "N registros eliminados"
         │
   Refetch → tabla vacía
```
