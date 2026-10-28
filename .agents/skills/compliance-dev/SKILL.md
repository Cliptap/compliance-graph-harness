---
name: compliance-dev
version: 1.1.0
description: Desarrollo con cumplimiento normativo (Ley 21.719, Ley 20.584, CWE-532). Usar al crear o modificar codigo que trate datos personales o de salud. Aplica los controles del pack normativo distinguiendo obligacion legal, medida segun riesgo y estandar interno.
---

# Compliance: modo desarrollo

## Cuando usar
- Antes de escribir codigo que reciba, almacene, registre, exponga, exporte o elimine datos personales o de salud.
- Al agregar endpoints, modelos, logs, caches, exportaciones, comunicaciones promocionales, perfilamiento, pagos o llamadas a servicios externos con datos de personas.

## Fuente normativa
Lee `.harness/packs/cl-ley-21719.json`. Cada control declara `requirement_type`, `applicability.when`, `validation_mode` y `legal_review`. `legal_review: validated` significa autovalidado contra el texto oficial por los autores del harness; nunca es asesoria legal. Cada fuente lleva su `source_check` (articulo, URL de BCN, fecha).

## Como razonar (obligatorio)
1. **Aplicabilidad primero.** Activa un control solo si se cumple su `applicability.when`. No apliques controles de salud a codigo que no trata datos de salud, ni los de `ecommerce_retail` a un sistema que no vende.
2. **Respeta el tipo de requisito.**
   - `legal_obligation`: cumplir; si hay duda, preguntar.
   - `risk_based_measure`: elegir una medida adecuada al riesgo y justificarla en una linea.
   - `internal_standard`: seguirlo, pero nunca lo presentes como exigencia de la ley.
3. **No inventes infracciones.** Si no encuentras una funcion concreta (por ejemplo `encryptAesGcm`), eso no prueba incumplimiento legal; reporta "evidencia insuficiente".

## Reglas de implementacion
- No emitir RUT, diagnosticos ni datos de salud a logs, consola, cache o telemetria; si hay que registrar, redactar o enmascarar por defecto.
- Las respuestas de API devuelven solo los campos necesarios para la finalidad; nunca credenciales (`password`, `hashed_password`, `secret`, `api_key`) ni identificadores sin enmascarar.
- Datos de tarjeta: persistir solo el token de la pasarela y los ultimos cuatro digitos; nunca el codigo de seguridad (CVV/CVC). El detector `privacy.payment_data_storage` bloquea el resto. PCI DSS es un estandar contractual, no ley.
- No borrar fisicamente fichas clinicas (conservacion minima de 15 anos, Ley 20.584 Art. 13); usar bloqueo logico o archivado. El soft delete es una implementacion posible, no la unica.
- Decisiones automatizadas o perfilamiento con efectos significativos para la persona: no bloquear toda automatizacion; documentar excepciones y garantizar informacion, intervencion humana y revision.
- Comunicaciones promocionales: incluir baja inmediata (opt-out) y respetar la oposicion al marketing directo.
- Brechas de seguridad: registrar la vulneracion; el reporte a la Agencia es "sin dilaciones indebidas" (la ley no fija horas).
- Datos de menores de 14 anos o sensibles (incluida la situacion socioeconomica): tratarlos con las medidas mas estrictas y preguntar antes de decidir una base de licitud.
- Minimizar: no pedir ni guardar campos que la finalidad no necesita.

## Cierre de tarea
Antes de terminar, si existe la herramienta `compliance_check`, ejecutala con los archivos cambiados y corrige las infracciones. Si el repositorio tiene instalada la compuerta previa al commit (`python -m src.harness.precommit --install`), el commit se bloqueara con el control y el articulo citados si queda una fuga; la compuerta no impide `git commit --no-verify`. Informa en una linea que controles aplicaste y cuales quedaron fuera por no aplicar.

## Limites
Esta skill no sustituye la asesoria legal. Los deberes de licitud, transparencia, incidentes, evaluacion de impacto, encargados, transferencias y menores requieren evidencia documental fuera del codigo: marcalos como "evidencia insuficiente", no como violacion.
