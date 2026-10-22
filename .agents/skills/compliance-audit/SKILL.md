---
name: compliance-audit
version: 1.0.0
description: Auditoria de cumplimiento normativo sobre codigo existente (Ley 21.719, Ley 20.584, CWE-532). Usar para revisar un repositorio o diff y emitir hallazgos con resultado tipificado y evidencia, sin modificar codigo.
---

# Compliance: modo auditoria

## Cuando usar
- Revisar un repositorio, modulo o diff por tratamiento de datos personales o de salud.
- Preparar un informe de hallazgos. Esta skill es de solo lectura: no edita codigo.

## Procedimiento
1. Lee `.harness/packs/cl-ley-21719.json` y selecciona los controles cuyo `applicability.when` se cumpla en el codigo auditado. Lista los controles descartados y por que.
2. Para cada control aplicable, usa su `validation_mode`:
   - `static_analysis`: busca en el codigo y, si existe, ejecuta `compliance_check` o el escaner del harness.
   - `integration_test`: busca pruebas que lo cubran; si no hay, no concluyas.
   - `document_review` / `manual_assessment`: pide o senala la evidencia faltante.
3. Emite un resultado por control, usando solo este vocabulario:
   - `confirmed_violation`: hay evidencia directa en el codigo (archivo y linea).
   - `potential_risk`: hay indicios, pero depende de contexto o de una decision juridica.
   - `not_applicable`: la condicion de aplicabilidad no se cumple.
   - `insufficient_evidence`: el control no puede verificarse con el material disponible.

## Formato de hallazgo
`<control_id> | <resultado> | <requirement_type> | <archivo>:<linea> | <evidencia en una linea> | <remediacion sugerida>`

## Reglas
- Un `internal_standard` incumplido nunca se reporta como violacion legal; se reporta como desviacion del estandar del proyecto.
- Ausencia de una funcion o patron no es `confirmed_violation`; es `insufficient_evidence` salvo que el patron prohibido este presente.
- Si el control tiene `legal_review: pending`, indicalo al final del informe: los hallazgos son tecnicos, no dictamen juridico.
- No reportes el mismo hallazgo con dos controles distintos; elige el mas especifico.
- Termina con conteos por resultado y la lista de controles no verificables.

## Limites
Los deberes de licitud, derechos del titular, transparencia, incidentes, EIPD y transferencias se evaluan por evidencia documental. Sin esa evidencia, el resultado es `insufficient_evidence`.
