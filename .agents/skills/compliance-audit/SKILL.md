---
name: compliance-audit
version: 1.1.0
description: Auditoria de cumplimiento normativo sobre codigo existente (Ley 21.719, Ley 20.584, CWE-532). Usar para revisar un repositorio o diff y emitir hallazgos con resultado tipificado y evidencia, sin modificar codigo.
---

# Compliance: modo auditoria

## Cuando usar
- Revisar un repositorio, modulo o diff por tratamiento de datos personales o de salud.
- Preparar un informe de hallazgos. Esta skill es de solo lectura: no edita codigo.

## Procedimiento
1. Lee `.harness/packs/cl-ley-21719.json` y selecciona los controles cuyo `applicability.when` se cumpla en el codigo auditado. Lista los controles descartados y por que. El plugin `ecommerce_retail` aplica solo si el sistema auditado es un comercio electronico; el plugin `health_clinical`, solo si trata fichas clinicas.
2. Para cada control aplicable, usa su `validation_mode`:
   - `static_analysis`: busca en el codigo y, si existe, ejecuta `compliance_check` o el escaner del harness (`python -m src.harness.precommit` sobre el indice de git, o el motor de politicas sobre los archivos).
   - `integration_test`: busca pruebas que lo cubran; si no hay, no concluyas.
   - `document_review` / `manual_assessment`: pide o senala la evidencia faltante (tabla siguiente). El codigo no prueba estos deberes: el resultado es `insufficient_evidence` mientras no exista esa evidencia.
3. Emite un resultado por control, usando solo este vocabulario:
   - `confirmed_violation`: hay evidencia directa en el codigo (archivo y linea).
   - `potential_risk`: hay indicios, pero depende de contexto o del criterio del equipo.
   - `not_applicable`: la condicion de aplicabilidad no se cumple.
   - `insufficient_evidence`: el control no puede verificarse con el material disponible.

## Detectores en codigo (evidencia directa)
| Politica | Que detecta | Control |
|---|---|---|
| `privacy.cwe_532` | RUT o datos de salud hacia logs o consola, directo o por flujo de datos (variables, contenedores, valores de retorno y llamadas entre los archivos evaluados) | CORE-CHECK-002 |
| `privacy.api_exposure` | respuestas de API con credenciales o identificadores sin enmascarar | CORE-CHECK-002 |
| `privacy.payment_data_storage` | CVV o numero de tarjeta sin cifrar persistido en un modelo ORM | ECOM-CHECK-003 |
| `domain.prohibited_deletion` | borrado fisico de fichas clinicas | HEALTH-CHECK-001 |

Limites conocidos y publicados en el corpus (`harness/eval/corpus/cases.json`): no se detectan modelos de respuesta importados de otro archivo, SQL crudo ni datos de tarjeta dentro de una columna JSON. El flujo hacia logs solo resuelve funciones de los archivos evaluados (en la compuerta, los del indice de git); una llamada no resuelta solo propaga el dato desde su receptor o si es una funcion que conserva el valor (`str`, `json.dumps`, `format`), y un diccionario con un RUT queda marcado completo.

## Evidencia documental que debes pedir
| Control | Evidencia a solicitar |
|---|---|
| CORE-CHECK-005 | base de licitud documentada y texto del consentimiento (libre, informado, especifico, previo e inequivoco) con mecanismo de revocacion equivalente |
| CORE-CHECK-006 | procedimiento para atender derechos del titular: 30 dias corridos prorrogables una vez por 30; bloqueo temporal respondido en 2 dias habiles |
| CORE-CHECK-007 | politica de tratamiento publica y accesible |
| CORE-CHECK-008 | registro de vulneraciones y procedimiento de reporte a la Agencia "sin dilaciones indebidas" (la ley no fija horas); aviso a titulares si hay datos sensibles, de menores de 14 anos o economicos |
| CORE-CHECK-009 | evaluacion de impacto en el tratamiento de alto riesgo (perfilamiento con efectos significativos, datos sensibles a gran escala) |
| CORE-CHECK-010 | contrato con cada encargado del tratamiento y registro de cesiones |
| CORE-CHECK-011 | base de cada transferencia internacional (pais adecuado o garantias) |
| CORE-CHECK-012 | tratamiento de datos de menores: menores de 14 anos (ninos y ninas) y 14 a 17 (adolescentes); consentimiento de los padres donde corresponda (detalle pendiente de reverificar contra el texto) |
| CORE-CHECK-013 | plazos de conservacion por finalidad y procedimiento de supresion |
| ECOM-CHECK-001 | baja de comunicaciones promocionales (opt-out) y oposicion al marketing directo |
| ECOM-CHECK-002 | informacion y oposicion al perfilamiento; evaluacion de impacto si hay efectos significativos |
| ECOM-CHECK-003 | procedimiento de seguridad y de comunicacion de vulneraciones para datos de tarjeta |
| ECOM-CHECK-004 | evidencia de cumplimiento PCI DSS (estandar contractual, no ley) |
| ECOM-CHECK-005 | contratos con pasarelas de pago y operadores logisticos |
| ECOM-CHECK-006 | politica de conservacion de documentos tributarios (6 anos) y rechazo de supresion cuando aplica |
| ECOM-CHECK-007 | tratamiento de situacion socioeconomica y puntajes de credito como datos sensibles |

## Formato de hallazgo
`<control_id> | <resultado> | <requirement_type> | <archivo>:<linea> | <evidencia en una linea> | <remediacion sugerida>`

## Reglas
- Un `internal_standard` incumplido nunca se reporta como violacion legal; se reporta como desviacion del estandar del proyecto (por ejemplo PCI DSS o HL7 FHIR).
- Ausencia de una funcion o patron no es `confirmed_violation`; es `insufficient_evidence` salvo que el patron prohibido este presente.
- Todo control del pack lleva `legal_review: validated` y una `validation_note`: significa autovalidacion contra el texto oficial (BCN LeyChile, Diario Oficial) por los autores del harness. Indicalo al final del informe: los hallazgos son tecnicos y contrastados con la ley, no asesoria legal.
- No reportes el mismo hallazgo con dos controles distintos; elige el mas especifico.
- Termina con conteos por resultado y la lista de controles no verificables.

## Limites
Los deberes de licitud, derechos del titular, transparencia, incidentes, evaluacion de impacto, encargados, transferencias, menores y conservacion se evaluan por evidencia documental. Sin esa evidencia, el resultado es `insufficient_evidence`; nunca `confirmed_violation`.
