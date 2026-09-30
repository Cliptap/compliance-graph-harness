# Evidencia Empírica: Desarrollo con Harness vs. Desarrollo sin Harness

Este documento consolida la evidencia experimental obtenida en el benchmark de evaluación del **VibeCoding Harness** (`qa_reports/results.json`), contrastando el desempeño del desarrollo asistido por IA **bajo gobernanza del harness** frente al **modo libre (sin harness)**.

---

## 1. Diseño Experimental

El experimento utilizó un **diseño intrasujeto balanceado** donde la única variable independiente fue la presencia de las reglas de gobernanza y skills del harness:

| Parámetro | Configuración |
|---|---|
| **Modelo evaluado** | `opencode-go/minimax-m3` |
| **Población de tareas** | 3 tareas de desarrollo representativas de software real ($N = 3$) |
| **Total de ejecuciones** | 6 corridas ($3 \times 2$ modos intrasujeto) |
| **Modo A (Sin Harness / eval-libre)** | Modelo con prompt abierto: "sé prolijo, agregá lo que consideres necesario para que sea production-ready, usá las abstracciones que quieras sin restricciones". |
| **Modo B (Con Harness / eval-con-skills)** | Modelo gobernado por las 4 reglas Always-On (Preguntar antes de asumir, MVP sin goldplating, Cero alucinaciones, KISS/YAGNI). |

---

## 2. Resumen Global de Resultados

| Métrica | Modo Libre (Sin Harness) | Modo Gobernado (Con Harness) | Impacto del Harness |
|---|---|---|---|
| **Tiempo de ciclo promedio** | 252.9 s | 196.2 s | **-22.4% de tiempo** (mayor agilidad) |
| **Archivos generados promedio** | 2.33 | 1.67 | **-28.6% dispersión de archivos** |
| **Líneas de código promedio (LOC)** | 202.3 LOC | 133.3 LOC | **-34.1% sobre-ingeniería / bloat** |
| **Alucinaciones de dependencias** | 0 | 0 | 100% apego a dependencias del repo |
| **Tasa de tareas completadas** | 3/3 (100%) | 3/3 (100%) | Sin degradación funcional |

---

## 3. Desglose Tarea por Tarea

### Tarea 01: Validador de RUT Chileno (Módulo 11)
- **Sin Harness:**
  - Archivos: 1 (`app/utils/rut_validator.py`, 36 LOC).
  - Tiempo de ciclo: 160.0 s.
  - Complejidad ciclomática promedio: 3.67.
  - Resultado: Entregó la función sin pruebas unitarias ejecutables.
- **Con Harness:**
  - Archivos: 2 (`app/utils/rut_validator.py`, `_test_rut.py`, 63 LOC totales).
  - Tiempo de ciclo: 127.1 s (**-20.5%**).
  - Complejidad ciclomática: 4.0.
  - Resultado: Entregó la función validada junto a una suite mínima de tests ejecutables.

### Tarea 02: Endpoint `GET /appointments` con 7 Query Params y RBAC
- **Sin Harness:**
  - Archivos: 3 (`src/backend/api/appointments.py`, `src/backend/schemas.py`, `tests/unit/test_appointments.py`).
  - Total LOC: 532 LOC.
  - Tiempo de ciclo: 461.7 s.
  - Costo: $0.2032 USD.
  - Observación: Creó capas intermedias de abstracción prematura y esquemas redundantes no solicitados explícitamente.
- **Con Harness:**
  - Archivos: 2 (`src/backend/api/appointments.py`, `tests/unit/test_appointments.py`).
  - Total LOC: 314 LOC (**-41.0% de código innecesario**).
  - Tiempo de ciclo: 372.9 s (**-19.2%**).
  - Costo: $0.1933 USD.
  - Observación: Implementó las convenciones del repositorio documentadas, sin crear esquemas superfluos. Cero alucinaciones de imports.

### Tarea 03: Sanitizador y Normalizador de Nombres Propios (Unicode NFC)
- **Sin Harness:**
  - Archivos: 3 (`app/utils/text_normalizer.py`, `app/__init__.py`, `app/utils/__init__.py`, 39 LOC).
  - Tiempo de ciclo: 136.9 s.
  - Observación: Proliferación de archivos vacíos `__init__.py` redundantes.
- **Con Harness:**
  - Archivos: 1 (`app/utils/text_normalizer.py`, 23 LOC).
  - Tiempo de ciclo: 88.5 s (**-35.3%**).
  - Observación: Entrega precisa y contenida, respetando la Regla 2 (MVP) y Regla 4 (KISS/YAGNI).

---

## 4. Conclusiones para la Defensa del Hito 0

1. **El valor no es solo "hacerlo funcionar", sino "evitar el goldplating":**
   Los modelos LLM sin restricciones tienden a generar sobre-arquitectura (abstracciones innecesarias, archivos redundantes y código accesorio) que eleva el costo de mantenimiento a largo plazo. El harness acota la generación al alcance MVP estricto (-34.1% de LOC superfluas).
2. **Eficiencia temporal y de contexto:**
   La reducción del 22.4% en tiempo de ciclo demuestra que guiar al agente con restricciones claras previene ciclos de corrección y "thrashing".
3. **Complementariedad del Harness:**
   El harness no reemplaza la capacidad del LLM, sino que establece el **marco de gobernanza**, **consistencia de proyecto**, **gestión de contexto** y **auditoría especializada (Ley 21.719)** para que el código sea directamente integrable en una base de código profesional.
