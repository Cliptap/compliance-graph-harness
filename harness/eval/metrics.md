# Metricas de Evaluacion del Harness

## Objetivo
Medir la calidad del output de un LLM usando el harness de VibeCoding (con skills)
vs usando un prompt libre (sin skills), para cuantificar el valor agregado.

## Metricas

### 1. Tasa de Alucinaciones (HA — Hallucination Rate)

**Definicion:** Porcentaje de imports, llamadas a API, nombres de librerias o comandos
que no existen en la realidad.

**Medicion:**
```
HA = (items inventados / total de items de codigo) * 100
```

**Ejemplos de items inventados:**
- `import { useQuantumState } from 'react'` — no existe
- `app.useFingerprintAuth()` — metodo inventado
- `pip install superfastapi` — paquete inexistente
- `docker compose hyperbuild` — comando inventado

**Target:** Con harness < 2%. Sin harness: tipicamente 8-15%.

### 2. Indice de Goldplating (GI — Goldplating Index)

**Definicion:** Porcentaje de features, endpoints, componentes o configuraciones
generados que NO estaban en el PRD ni fueron solicitados.

**Medicion:**
```
GI = (features no solicitadas / total de features implementadas) * 100
```

**Ejemplos de goldplating:**
- Agregar panel de admin sin que este en el PRD
- Implementar dark mode sin solicitarlo
- Agregar i18n con 3 idiomas
- Crear CI/CD sin que se pida
- Agregar health checks sin solicitarlos
- Implementar paginacion en endpoints que no la necesitan

**Target:** Con harness < 5%. Sin harness: tipicamente 20-40%.

### 3. Desviacion del MVP (MD — MVP Deviation)

**Definicion:** Porcentaje de lineas de codigo que implementan funcionalidad
fuera del alcance del PRD.

**Medicion:**
```
MD = (lineas fuera de scope / total de lineas) * 100
```

**Target:** Con harness < 10%. Sin harness: tipicamente 25-50%.

### 4. Tasa de Decisiones No Consultadas (UD — Unconsulted Decisions)

**Definicion:** Numero de decisiones tecnicas (stack, arquitectura, librerias,
patrones) que el modelo tomo sin preguntar al desarrollador.

**Medicion:**
```
UD = count(decisiones_no_consultadas)
```

**Ejemplos:**
- Eligio PostgreSQL sin preguntar SQL vs NoSQL
- Uso TypeScript sin preguntar
- Agrego Docker sin preguntar
- Eligio JWT sin preguntar metodo de auth
- Uso bcrypt sin preguntar algoritmo de hashing

**Target:** Con harness < 2 decisiones. Sin harness: tipicamente 5-15.

---

## Metodologia de Evaluacion

### Caso Base (Sin Harness)

Prompt: "Crea una API REST para gestionar productos con CRUD basico."

Se evalua el output sin ninguna regla ni skill cargada.

### Caso con Harness (Con Skills)

Se carga el harness completo (reglas always-on + skills) y se hace el mismo prompt.

La skill 01_prd deberia activarse y empezar a preguntar en vez de generar codigo.

### Proceso

1. Ejecutar el caso base → medir las 4 metricas
2. Ejecutar el caso con harness → medir las 4 metricas
3. Comparar y generar reporte

### Reporte Esperado

| Metrica | Sin Harness | Con Harness | Mejora |
|---------|-------------|-------------|--------|
| Alucinaciones (HA) | X% | Y% | Δ% |
| Goldplating (GI) | X% | Y% | Δ% |
| Desviacion MVP (MD) | X% | Y% | Δ% |
| Decisiones no consultadas (UD) | N | N | Δ |

---

## Interpretacion

- **HA > 5% con harness:** Las skills no estan previniendo alucinaciones. Revisar regla 03.
- **GI > 10% con harness:** Las skills no estan previniendo goldplating. Revisar regla 02.
- **MD > 15% con harness:** El modelo esta generando codigo sin preguntar. Revisar regla 01.
- **UD > 3 con harness:** Las skills no estan forzando el patron pregunta-respuesta.
  Revisar que las skills tengan preguntas obligatorias que bloqueen el avance.

## Mejora Continua

Cada vez que se detecte una metrica fuera de target, se debe:
1. Identificar la skill o regla que fallo
2. Agregar preguntas o restricciones adicionales
3. Re-evaluar para verificar la mejora
