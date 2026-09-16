# PRD de Ejemplo — Consultorio Médico (Gobernanza Media)

> Generado siguiendo la skill `01_prd.md`. Este documento sirve como referencia
> para la demo y como input para las skills subsiguientes (DB, API, ETL, Frontend).

---

## 0. Contexto Normativo
- **Regulación aplicable:** Ley 20.584 (Chile) — Derechos del paciente, ficha clínica obligatoria
- **Requisitos específicos:**
  - Retención de datos clínicos: mínimo 15 años
  - Trazabilidad: registrar quién creó y modificó cada registro
  - Acceso: solo personal autorizado con rol definido
  - No se requiere HIPAA ni GDPR por operar solo en Chile

---

## 1. Propósito
- **Problema:** El consultorio maneja citas médicas en papel o Excel. No hay trazabilidad de quién agenda, modifica o cancela citas. No se puede auditar el historial de cambios.
- **Objetivo:** Sistema digital para agendar, consultar y gestionar citas médicas con control de acceso y auditoría básica.

---

## 2. Usuarios
- **Tipos:**
  - Recepcionista: agenda y modifica citas
  - Médico: consulta sus citas del día
  - Administrador: gestiona usuarios y ve reportes
- **Uso:**
  - Carga manual de datos de pacientes y citas vía formulario web
  - Consulta de citas por fecha, médico o paciente
  - Reporte semanal de citas agendadas vs atendidas

---

## 3. Datos
- **Tipo:** Estructurados (tablas relacionales)
- **Dominio:** Salud — pacientes, médicos, citas médicas
- **Volumen:** ~500 pacientes, ~50 citas/día, ~15,000 citas/año

---

## 4. Fuentes
- **Origen:** Ingreso manual vía formulario web (recepcionista)
- **También se contempla:** carga CSV para migración inicial de datos históricos

---

## 5. Arquitectura
- **Base de datos:** SQL (PostgreSQL) — requiere integridad transaccional ACID, relaciones entre pacientes, médicos y citas
- **Infraestructura:** Local (servidor en el consultorio), con opción futura de migrar a nube

---

## 6. Procesamiento de Datos (ETL)
- **Extracción:** Formulario web + carga CSV para datos históricos
- **Frecuencia:** Tiempo real para formulario. Carga CSV solo una vez (migración inicial)
- **Transformación:**
  - RUT: limpieza de puntos y guiones, validación módulo 11
  - Nombres: capitalización (primera letra mayúscula)
  - Fechas: normalización a ISO 8601
  - Teléfonos: limpieza de caracteres no numéricos, conservar +

---

## 7. Gobernanza
- **Nivel:** Medio
- **Implicancias:**
  - Validaciones de datos en frontend y backend
  - Logs de ejecución (quién creó/modificó cada registro)
  - Control de acceso básico (3 roles: admin, médico, recepcionista)
  - Soft deletes en todas las entidades
  - Columnas de auditoría: `created_at`, `updated_at`, `deleted_at`
