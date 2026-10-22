---
name: compliance-patch
version: 1.0.0
description: Parcheo supervisado de hallazgos de cumplimiento normativo (Ley 21.719, Ley 20.584, CWE-532). Usar para corregir hallazgos confirmados de una auditoria con el cambio minimo, verificando que no se rompa comportamiento existente.
---

# Compliance: modo parche

## Cuando usar
- Existe un hallazgo `confirmed_violation` de `compliance-audit` o de `compliance_check`, y se pidio corregirlo.
- No uses esta skill para `potential_risk` ni `insufficient_evidence` sin confirmacion del usuario.

## Procedimiento
1. Reproduce: identifica archivo y linea del hallazgo y confirma que sigue presente. Si ya no existe, informalo y termina.
2. Lee el control en `.harness/packs/cl-ley-21719.json` (`remediation.mitigations`, `applicability`, `requirement_type`). Elige la mitigacion mas pequena que lo resuelva.
3. Aplica el cambio minimo en el sitio del hallazgo. No refactorices codigo vecino ni cambies contratos publicos sin pedirlo.
4. Escribe o ajusta una prueba que falle antes del parche y pase despues, cuando haya un test runner aplicable.
5. Ejecuta las pruebas existentes y, si esta disponible, `compliance_check` sobre los archivos tocados.
6. Informa: control, cambio aplicado, prueba agregada, resultado de las verificaciones.

## Reglas
- Respeta el alcance: modifica solo los archivos necesarios para el hallazgo.
- Patrones tipicos: enmascarar o redactar antes de registrar; quitar campos sensibles o credenciales del esquema de respuesta; sustituir borrado fisico de fichas clinicas por bloqueo logico o archivado.
- Si la correccion cambia una API usada por otros (campos de respuesta eliminados), senalalo como cambio de contrato y pide confirmacion antes de aplicarlo.
- Si la unica mitigacion posible es una decision juridica o de producto (base de licitud, plazo de conservacion), no la inventes: devuelve la pregunta concreta.

## Limites
No marques un hallazgo como resuelto sin haber visto la verificacion pasar. Un control con `legal_review: pending` se parchea por criterio tecnico; indica que la validacion juridica sigue pendiente.
