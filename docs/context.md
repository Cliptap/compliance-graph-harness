# Base de Conocimiento: Proyecto 3 - Repositorio de Procesamiento de Datos con Vibe Coding

## 1. Definición de Conceptos Clave

### Vibe Coding
Uso de asistentes de programación (LLMs) para generar código de forma rápida. Para evitar soluciones sin estructura o calidad, se utiliza un pipeline de interacción orientado por *skills* y *prompts* definidos.

### Skill (Habilidad del Sistema)
Texto que se carga en el prompt de forma persistente. No es solo un generador de código; representa una capacidad específica dentro del pipeline. 
**Componentes de una Skill:**
- Contexto del problema.
- Objetivo.
- Información requerida del usuario.
- Formato de salida esperado.
- Criterios de calidad y coherencia.

---

## 2. Objetivos del Proyecto

**Objetivo General:**
Construir un repositorio simple de procesamiento de datos utilizando Vibe Coding, definiendo explícitamente el uso de *skills* y *prompts*.

**Tareas Concretas:**
- Carga de datos.
- Limpieza y validación.
- Generación de reportes.
- Estructuración de un pipeline de interacción claro.

---

## 3. Grafo de Dependencias entre Skills

```
01_prd ────────────► 02_db ──────────► 08_orm ──────► 03_api ──────► 05_frontend
   │                    │                  │               │               │
   │                    │                  │               ├──► 07_auth ───┤
   │                    │                  │               │               │
   │                    ├──► 04_etl ───────┘               │               │
   │                    │                                  │               │
   │                    └──► 06_reports                    │               │
   │                                                       │               │
   └───────────────────────────────────────────────────────┴───────────────┘
                                                           │
                    09_docker ◄────────────────────────────┘
                    10_testing ◄────── 03_api + 07_auth + 08_orm

Cross-cutting: 09_docker (post-frontend), 10_testing (post-api+auth), 11_contexto (always first)
```

## 4. Pipeline de Desarrollo Propuesto (5 Etapas)

### Etapa 1: Definición del PRD (Product Requirements Document)
Conversación inicial con la IA para definir el propósito, usuarios, casos de uso y tipo de datos.
- **Gobernanza de Datos:** Se debe elegir un nivel:
    - **Baja:** Validaciones mínimas, sin control de acceso ni auditoría.
    - **Media:** Validaciones, logs de ejecución y control básico de acceso.
    - **Alta:** Control por roles, auditoría completa (quién, cuándo, qué) y trazabilidad total.
- **Skill Clave:** Generación de PRD y configuración del repositorio.

### Etapa 2: Modelamiento de Datos
Definiciones técnicas a partir del PRD.
- **Contenido:** Entidades, tablas, atributos, relaciones y campos de auditoría según la gobernanza.
- **Skill Clave:** Definición de modelo relacional (esquemas y tipos de datos).

### Etapa 3: Implementación Backend
- **Acciones:** Creación de DB, pipeline ETL (Carga, Transformación, Validación), reglas de negocio y endpoints.
- **Skills Propuestas:** - Esquema SQL.
    - Construcción de ETL.
    - Definición de validaciones.
    - Implementación de gobernanza (logs, auditoría).
    - Definición de Endpoints.
    - Generación de pruebas.

### Etapa 4: Implementación Frontend
Interfaz para interactuar con el sistema (carga, consulta y visualización).
- **Skills Propuestas:** - Definición de vistas.
    - Interacción con backend.
    - Estructuración de navegación.

### Etapa 5: Reportería
Mecanismos para extraer valor de los datos procesados.
- **Skills Propuestas:** - Definición de métricas/indicadores.
    - Generación de consultas SQL complejas.
    - Estructuración de reportes (deben reflejar la gobernanza).

---

## 4. Resultados Esperados y Métricas

- **Entregables:** Repositorio funcional modular, conjunto de skills .md, pipeline documentado, registro de pruebas.
- **Evaluación de Calidad:**
    - **Etapas iniciales:** Calidad, completitud y coherencia de las definiciones (PRD).
    - **Etapas de implementación:** Cumplimiento de requerimientos funcionales y no funcionales.

---

## 5. Recomendaciones del Profesor
1. **Enfoque Iterativo:** Partir con un caso muy sencillo (ej. Consultorio médico con pocas tablas y gobernanza baja).
2. **Evolución:** Una vez que el pipeline completo funcione, integrar mayor complejidad (niveles de gobernanza media/alta).
3. **Rol del Usuario:** Si el usuario no tiene claridad, la *skill* debe ser capaz de ayudar a completar la información mediante preguntas guiadas.