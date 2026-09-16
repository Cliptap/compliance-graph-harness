---
name: project-type-data-pipeline
version: 2.0.0
depends_on: [prd-generation, architecture-design, data-modeling]
stage: cross-cutting
project_types: [data_pipeline]
governance: all
description: Especificaciones adicionales para proyectos de procesamiento de datos. Cubre ETL, fuentes de datos, validacion, transformaciones y reporteria.
---

# Skill: Data Pipeline (ETL / Procesamiento de Datos)

## Objetivo
Refinar la arquitectura y el desarrollo para proyectos de procesamiento de datos,
cubriendo ETL, validacion, transformaciones y reporteria.

## Instrucciones
- Esta skill **complementa** las skills base, no las reemplaza.
- Activar solo si el tipo de proyecto es `data_pipeline`.
- Hacer preguntas adicionales especificas de pipelines de datos.

---

## Flujo de Interaccion

### 1. Fuentes de Datos

```
? De donde provienen los datos?

a) Carga manual — el usuario sube archivos (CSV, Excel, JSON)

b) APIs externas — consumir datos de servicios de terceros
   ?Que APIs? ?Autenticacion? ?Rate limits?

c) Bases de datos externas — conectar a otras BD y extraer datos

d) Sensores / IoT / streaming — datos en tiempo real

e) Web scraping — extraer datos de paginas web

f) Multiples fuentes — combinacion de varias de las anteriores

⏳ Describi cada fuente.
```

### 2. Frecuencia de Carga

```
? Cada cuanto se cargan/actualizan los datos?

a) Una sola vez — carga inicial, sin actualizaciones

b) Bajo demanda — el usuario dispara la carga manualmente

c) Programado — cada X tiempo (diario, semanal, mensual)
   Tool: cron, schedule de GitHub Actions, Airflow, Prefect

d) Tiempo real / streaming — los datos llegan continuamente
   Tool: Kafka, Kinesis, WebSocket

⏳ Esperando tu respuesta.
```

### 3. Volumen y Performance de Datos

```
? Que volumen de datos manejamos?

a) Pequeno — menos de 10k registros, cabe en memoria
   Procesamiento simple, CSV/Excel suficiente

b) Mediano — 10k a 1M de registros
   Base de datos necesaria, procesamiento en batches

c) Grande — 1M+ registros
   [PREGUNTAR] Optimizaciones necesarias: indices, particionamiento, procesamiento paralelo

? Hay restricciones de tiempo para el procesamiento?
  Ej: "la carga diaria no puede tomar mas de 30 minutos"
```

### 4. Pipeline ETL/ELT

```
? Como es el flujo de datos?

a) ETL (Extract → Transform → Load):
   Extraer de fuente, transformar (limpiar, validar, enriquecer), cargar a destino
   Mejor para: datos que necesitan limpieza antes de guardar

b) ELT (Extract → Load → Transform):
   Extraer, cargar raw a destino, transformar con queries
   Mejor para: datos masivos, transformaciones complejas en SQL

? Que transformaciones necesitas?
  - Limpieza: quitar duplicados, normalizar formatos, manejar nulos
  - Validacion: verificar tipos, rangos, formatos
  - Enriquecimiento: agregar columnas calculadas, joins con otras tablas
  - Agregacion: sumarizar, agrupar, calcular metricas
```

### 5. Validacion de Datos

```
? Que nivel de validacion necesitas para los datos de entrada?

Para cada campo del esquema de datos, responder:

1. FORMATO: ?Como debe verse el dato?
2. AUTO-FORMATO: ?El sistema inserta separadores automaticamente o el usuario los digita?
3. CARACTERES PERMITIDOS: ?Solo digitos, alfanumerico, formato libre?
4. LONGITUD Y RANGO: ?Minimo y maximo de caracteres o valor?
5. VALIDACION SEMANTICA: ?Solo formato o tambien integridad (digito verificador, checksum)?
6. NORMALIZACION: ?Se convierte a un formato canonico? (mayusculas, sin espacios, etc.)
7. OBLIGATORIEDAD: ?El campo es obligatorio, opcional o condicional?

⏳ Vamos campo por campo. Empecemos por {primer campo}.
```

### 6. Destino de los Datos

```
? Donde se almacenan los datos procesados?

a) Base de datos SQL (PostgreSQL) — [RECOMENDADO para datos estructurados]
   Con esquema definido, relaciones, integridad referencial

b) Data Warehouse (BigQuery, Redshift, Snowflake)
   Mejor para: analytics, grandes volumenes, queries complejas

c) Data Lake (S3 + Parquet/Delta/Iceberg)
   Mejor para: datos raw, data science, ML

d) Archivos (CSV, Parquet, Excel) — output final para descargar

e) API — exponer los datos procesados via endpoints

⏳ Esperando tu respuesta.
```

### 7. Reporteria y Visualizacion

```
? Necesitas reporteria o dashboards?

a) No — solo necesito almacenar/procesar los datos

b) Reportes estaticos — queries SQL predefinidas que generan tablas/graficos
   Formato: CSV, Excel, PDF, HTML

c) Dashboard interactivo — filtros, drill-down, actualizacion en vivo
   Herramientas: Metabase, Superset, Grafana, Streamlit

d) Jupyter Notebooks — analisis exploratorio, prototipos de reportes

? Que metricas/KPIs necesitas visualizar?
? Cada cuanto se actualizan los reportes?
```

### 8. Idempotencia y Reintentos

```
? Como manejar fallos en el pipeline?

a) Reintentos automaticos — si una carga falla, reintentar N veces
   con exponential backoff

b) Idempotencia — si se ejecuta el mismo pipeline 2 veces,
   el resultado es el mismo (no duplica datos)

c) Dead Letter Queue — datos que fallan van a una cola de revision manual

d) Sin manejo de fallos — MVP simple, si falla se corrige manualmente

⏳ Esperando tu respuesta.
```

---

## Verificacion Post-Generacion

- [ ] Todas las fuentes de datos estan identificadas y configuradas
- [ ] El pipeline ETL/ELT esta implementado con las transformaciones definidas
- [ ] Las validaciones de datos estan implementadas para cada campo
- [ ] El destino de datos esta configurado y recibe datos correctamente
- [ ] El schedule (si aplica) esta configurado
- [ ] Los reintentos y manejo de errores estan implementados
- [ ] La reporteria (si aplica) genera los KPIs definidos

## Condicion de Cierre

```
Voy a generar el pipeline de datos completo.
¿Confirmas que el flujo ETL y las validaciones son correctos?

⏳ Esperando tu confirmacion.
```
