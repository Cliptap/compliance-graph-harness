# Cobertura de la Ley 21.719: 30 aristas, 3 modos

El pack `cl-ley-21719.json` enumera 30 controles derivados de la ley. Este documento responde una
pregunta por control: **¿se detecta, se exige evidencia, o lo decide una persona?**

La distinción no es una excusa: un detector solo puede afirmar lo que una prueba en el código
sostiene. Las aristas documentales (EIPD, registro de incidentes, contratos, PCI) no se detectan; se
bloquean hasta que la evidencia exista. Las semánticas (licitud, proporcionalidad, intervención
humana) las firma una persona.

## Matriz

| Control | Arista | Modo | Detector | Estado |
|---|---|---|---|---|
| `CL-DATAPROT-001` | fuga de datos clínicos o RUT a logs | detectar | `privacy.cwe_532` (comparte con `CORE-CHECK-002`) | cubierto, no registrado como implementado |
| `CL-DATAPROT-002` | caché de salud sin cifrado en reposo | detectar | `code_hygiene: cache_unencrypted` | implementado (T31) |
| `CL-DATAPROT-003` | campo ORM de salud sin cifrado | detectar | `code_hygiene: orm_unencrypted` | implementado (T31) |
| `CL-DATAPROT-004` | borrado físico prematuro de ficha clínica | detectar | `domain.prohibited_deletion` | implementado |
| `CL-DATAPROT-005` | endpoint clínico sin control de acceso | detectar | `code_hygiene: route_auth` | implementado (T31) |
| `CL-DATAPROT-006` | decisión clínica automatizada sin intervención humana | manual | — | documental |
| `CL-DATAPROT-007` | portabilidad de ficha en formato no estructurado | detectar | `code_hygiene: export_format` | implementado (T31) |
| `CORE-CHECK-001` | privacidad desde el diseño y minimización | manual | — | semántico |
| `CORE-CHECK-002` | deber de secreto: fugas en logs y consolas | detectar | `privacy.cwe_532` | implementado |
| `CORE-CHECK-003` | derechos del titular y control de acceso | detectar | `code_hygiene: personal_route_auth` | implementado (T31) |
| `CORE-CHECK-004` | decisiones automatizadas: oposición e intervención humana | manual | — | documental |
| `CORE-CHECK-005` | licitud y consentimiento | detectar | `privacy.consent_transparency` | implementado |
| `CORE-CHECK-006` | derechos del titular: procedimiento y plazos | detectar | `privacy.rights_reachability` | implementado: VIOLATION en escaneo completo, WARNING en diff (T32) |
| `CORE-CHECK-007` | deber de información y transparencia | detectar (WARNING) | `privacy.consent_transparency` | implementado, sin violación confirmada |
| `CORE-CHECK-008` | registro y comunicación de vulneraciones | evidencia | — | documental |
| `CORE-CHECK-009` | evaluación de impacto | evidencia | — | documental |
| `CORE-CHECK-010` | encargados del tratamiento y cesión | detectar (WARNING) | `privacy.third_party_transfers` | implementado, sin violación confirmada |
| `CORE-CHECK-011` | transferencias internacionales | detectar (WARNING) | `privacy.third_party_transfers` | implementado, sin violación confirmada |
| `CORE-CHECK-012` | datos de niños, niñas y adolescentes | detectar | `privacy.minors_and_sensitive` | implementado |
| `CORE-CHECK-013` | conservación, supresión y limitación | detectar (WARNING) | `privacy.retention_minimization` | implementado, sin violación confirmada |
| `HEALTH-CHECK-001` | conservación de 15 años de la ficha clínica | detectar | `domain.prohibited_deletion` | implementado |
| `HEALTH-CHECK-002` | interoperabilidad FHIR R4 | evidencia | — | documental |
| `HEALTH-CHECK-003` | protección reforzada de datos de salud | evidencia | — | documental |
| `ECOM-CHECK-001` | marketing directo y oposición | detectar | `privacy.consent_transparency` | implementado |
| `ECOM-CHECK-002` | perfilamiento y recomendaciones | manual | — | documental |
| `ECOM-CHECK-003` | datos de tarjetas de pago | detectar | `privacy.payment_data_storage` | implementado |
| `ECOM-CHECK-004` | PCI DSS | evidencia | — | contractual |
| `ECOM-CHECK-005` | pasarelas y operadores logísticos | detectar (WARNING) | `privacy.third_party_transfers` | implementado, sin violación confirmada |
| `ECOM-CHECK-006` | retención de documentos tributarios | evidencia | — | documental (solapa `v2.billing_retention`) |
| `ECOM-CHECK-007` | situación socioeconómica y puntajes | detectar | `privacy.minors_and_sensitive` | implementado |

## Resumen

| Modo | Controles |
|---|---:|
| Detectar | 19 |
| Detectar solo como riesgo (WARNING) | 5 |
| Exigir evidencia | 6 |
| Manual | 4 |

## Qué significa cada modo en el gate

- **Detectar**: finding con archivo y línea; si la severidad es HIGH/CRITICAL y el estado es
  VIOLATION, el commit se bloquea.
- **Detectar (WARNING)**: el finding se reporta pero no bloquea. Es deliberado: un índice parcial no
  puede probar una violación de retención. La excepción es `privacy.rights_reachability`, que sube a
  VIOLATION solo cuando el `ChangeSet` declara ser completo.
- **Evidencia**: el merge se bloquea si falta el artefacto (EIPD, registro de incidentes, contrato,
  atestación PCI). No hay detector; hay un requisito.
- **Manual**: checklist firmado por una persona con el artículo citado.

## Deriva conocida

- `CL-DATAPROT-001` figura como `implemented: false` en el pack, pero el detector genérico
  `CORE-CHECK-002` evalúa la misma fuga. La matriz lo marca como cubierto, no como implementado,
  hasta que el pack lo declare.
- El audit `pack-detector-audit.md` decía que el pre-commit solo evaluaba tres políticas legacy. El
  código actual corre las cinco políticas legacy y el `CatalogEngine` v2 completo; el audit quedó
  corregido.

## Próximos pasos

1. ~~**Promover a VIOLATION** los WARNING demostrables por código~~ (T32). El consentimiento
   pre-tildado ya era `HIGH`/`VIOLATION`; la ausencia de ruta de derechos ahora es `HIGH`/`VIOLATION`
   cuando el `ChangeSet` es completo (`complete=True`) y sigue `MEDIUM`/`WARNING` en un diff, porque
   un diff no puede probar que una ruta no existe. Lo no demostrable (retención mínima, contratos)
   queda como WARNING a propósito.
2. **Evidence-gate** para las 6 aristas documentales: bloquear el merge si falta el artefacto, con
   el artículo citado en el mensaje.
3. **Ampliar la familia `code_hygiene`** con los tokens de cada proyecto (nombres de rutas clínicas,
   modelos de salud) para que el modo detectar no dependa de una lista fija.
