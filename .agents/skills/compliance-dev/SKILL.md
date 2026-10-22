---
name: compliance-dev
version: 1.0.0
description: Desarrollo con cumplimiento normativo (Ley 21.719, Ley 20.584, CWE-532). Usar al crear o modificar codigo que trate datos personales o de salud. Aplica los controles del pack normativo distinguiendo obligacion legal, medida segun riesgo y estandar interno.
---

# Compliance: modo desarrollo

## Cuando usar
- Antes de escribir codigo que reciba, almacene, registre, exponga, exporte o elimine datos personales o de salud.
- Al agregar endpoints, modelos, logs, caches, exportaciones o llamadas a servicios externos con datos de personas.

## Fuente normativa
Lee `.harness/packs/cl-ley-21719.json`. Cada control declara `requirement_type`, `applicability.when`, `validation_mode` y `legal_review`. Todo control con `legal_review: pending` es una guia de ingenieria, no un dictamen juridico.

## Como razonar (obligatorio)
1. **Aplicabilidad primero.** Activa un control solo si se cumple su `applicability.when`. No apliques controles de salud a codigo que no trata datos de salud.
2. **Respeta el tipo de requisito.**
   - `legal_obligation`: cumplir; si hay duda, preguntar.
   - `risk_based_measure`: elegir una medida adecuada al riesgo y justificarla en una linea.
   - `internal_standard`: seguirlo, pero nunca lo presentes como exigencia de la ley.
3. **No inventes infracciones.** Si no encuentras una funcion concreta (por ejemplo `encryptAesGcm`), eso no prueba incumplimiento legal; reporta "evidencia insuficiente".

## Reglas de implementacion
- No emitir RUT, diagnosticos ni datos de salud a logs, consola, cache o telemetria; si hay que registrar, redactar o enmascarar por defecto.
- Las respuestas de API devuelven solo los campos necesarios para la finalidad; nunca credenciales (`password`, `hashed_password`, `secret`, `api_key`) ni identificadores sin enmascarar.
- No borrar fisicamente fichas clinicas (conservacion minima de 15 anos, Ley 20.584 Art. 13); usar bloqueo logico o archivado. El soft delete es una implementacion posible, no la unica.
- Decisiones automatizadas con efectos significativos para la persona: no bloquear toda automatizacion; documentar excepciones y garantizar informacion, intervencion humana y revision.
- Minimizar: no pedir ni guardar campos que la finalidad no necesita.

## Cierre de tarea
Antes de terminar, si existe la herramienta `compliance_check`, ejecutala con los archivos cambiados y corrige las infracciones. Informa en una linea que controles aplicaste y cuales quedaron fuera por no aplicar.

## Limites
Esta skill no sustituye la validacion juridica. Los deberes de licitud, transparencia, incidentes, EIPD y encargados requieren evidencia documental fuera del codigo: marcalos como "evidencia insuficiente", no como violacion.
