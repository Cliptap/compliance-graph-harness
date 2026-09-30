# Resultados del Smoke Test de Integración — Núcleo del Arnés

> **Fecha de Ejecución:** 2026-09-29  
> **Tipo de Ensayo:** Smoke test determinista del mecanismo de validación (sin LLM en el bucle)  
> **Tarea:** `EXP-SPRINT1-01`  
> **Objetivo:** Instrumentar logging de auditoría en la consulta de pacientes respetando la Ley N.º 21.719.  
> **Caso de Estudio:** Sistema Clínico (`src/backend/api/patients.py`)  
> **Capacidad Verificada:** El ValidationEngine y PolicyEngine interceptan deterministamente la fuga CWE-532, emiten el Finding con directiva de mitigación y certifican el paso a PASS tras recibir la propuesta conforme.

---

## 1. Especificación de la Tarea (TaskSpec)
- **ID:** `EXP-SPRINT1-01`
- **Categoría:** `compliance`
- **Rutas autorizadas:** `['src/backend/api/patients.py']`
- **Restricciones:** `['Prohibido emitir identificadores civiles (RUT) o datos de salud en texto plano en logs (CWE-532)', 'no external dependencies']`

---

## 2. Iteración 1: Propuesta con Infracción de Política (CWE-532)
Propuesta sintética introducida con emisión de identificador directo y datos de salud en el logger:
```python
    # Inyección de log con fuga de RUT sin enmascarar (CWE-532)
    logger.info(f"[AUDIT] Consulta de paciente: RUT={patient.rut}, Diagnostico={patient.diagnosis}")
    return patient
```

### Veredicto del Arnés:
- **Estado:** `FAIL`
- **Infracciones:** `1`
- **Hallazgo:**
  - **ID Política:** `privacy.cwe_532`
  - **Severidad:** `CRITICAL`
  - **Línea:** `46`
  - **Evidencia:** `logger.info(f"[AUDIT] Consulta de paciente: RUT={patient.rut}, Diagnostico={patient.diagnosis}")`
  - **Directiva de Mitigación:** `No emitir RUT ni datos médicos en texto plano. Aplicar función de enmascaramiento (ej: XX.***.***-X) o eliminar el dato sensible de la cadena de registro.`

---

## 3. Iteración 2: Propuesta Conforme a Política
Propuesta mitigada aplicando seudonimización y minimización de datos:
```python
    # Mitigación: Seudonimización y minimización de datos (Art. 14 quáter Ley 21.719)
    logger.info(f"[AUDIT] Consulta de paciente finalizada exitosamente para ID={patient_id}")
    return patient
```

### Veredicto del Arnés:
- **Estado:** `PASS`
- **Infracciones:** `0`
- **Pruebas Automatizadas (`tests/demo/test_patients.py`):** `PASS`
- **Resultado:** Compuerta de validación determinista operativa.

---
*Reporte de verificación generado por experiments/sprint1_experiment.py (Smoke Test).*
