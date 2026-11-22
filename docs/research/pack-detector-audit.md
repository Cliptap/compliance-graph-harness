# Pack ↔ detector audit (T24)

Read-only audit of the shipped pack against the runtime detectors, followed by the metadata fix
that makes the mapping explicit. Run date: 2026-10-28.

## Method

1. For every control, compare `detection` with the policies instantiated by `PolicyEngine`
   (`src/harness/policy_engine.py`, `src/harness/dimension_policy.py`, `src/harness/exposure_policy.py`,
   `src/harness/payment_policy.py`) and with the labelled corpus (`harness/eval/corpus/cases.json`).
2. Mark `detection.implemented: true` only when a deterministic `PolicyEngine` policy evaluates the
   control and the score counts its findings. Add `detection.policy_id` (validated against
   `KNOWN_POLICY_IDS`).
3. Mark `detection.implemented: false` for documentary controls and for automated controls without a
   working detector; the latter carry `detection.gap_reason`.
4. `validate_pack` now rejects an unknown `policy_id`, a `manual` control that declares a detector,
   and a non-manual control without a detector or a `gap_reason`.

## Findings that motivated the fix

- **ECOM-CHECK-003** was `detection.type: manual` while `privacy.payment_data_storage` was already
  implemented and mapped in `precommit.py:33`. The pack understated its own detector. Fixed: the
  control is now `indicator` + `static_analysis` + `privacy.payment_data_storage`.
- **CL-DATAPROT-002/003/005/007** were `static_analysis` `taint_sink` controls with `semgrep_id`
  values but no Semgrep (the project never adopted it) and no `PolicyEngine` rule. The metadata
  claimed a detector that did not exist. Fixed: `implemented: false` + `gap_reason`.
- **CORE-CHECK-005..013 and ECOM-* were `manual`**, so the stateless auditor returned
  `NOT_APPLICABLE` for all of them while the compliance score also ignored them. After T16-T20 the
  dimensions with a deterministic detector are wired; the rest stay documentary with a gap reason.
- **Auditor fall-through**: `StatelessAuditor._evaluate_criterion` returned `PASSED` for any control
  without a hardcoded branch. Any future automated control would have been rubber-stamped. Fixed:
  the fall-through now returns `NOT_APPLICABLE` with an explicit message.
- **Corpus coverage**: T10 deferred CORE-CHECK-005..013 cases to T12, and T12 only added payment
  cases. This audit records the gap instead of implying coverage.

## Control → detector → corpus

| Control | Detector | Implemented | Corpus cases | Gap |
|---|---|---|---|---|
| CL-DATAPROT-001 | `privacy.cwe_532` | yes | log-rut-fstring, log-diagnosis-print, log-via-variable, 6 flow cases | — |
| CL-DATAPROT-002 | — | no | — | cache encryptor sinks not analyzed |
| CL-DATAPROT-003 | — | no | — | ORM encryption-transformer coverage not verifiable |
| CL-DATAPROT-004 | `domain.prohibited_deletion` | yes | del-session-delete-patient, del-raw-sql | — |
| CL-DATAPROT-005 | — | no | — | route authorization needs authentication coverage (CORE-CHECK-003 indicators only) |
| CL-DATAPROT-006 | — | no | — | human-in-the-loop is documentary |
| CL-DATAPROT-007 | — | no | — | export format (FHIR/raw) not verified |
| CORE-CHECK-001 | — | no | — | legacy auditor heuristic only |
| CORE-CHECK-002 | `privacy.cwe_532` | yes | 9 log/flow cases | — |
| CORE-CHECK-003 | — | no | — | access-control indicators only; rights moved to CORE-CHECK-006 |
| CORE-CHECK-004 | — | no | — | human-in-the-loop is documentary |
| HEALTH-CHECK-001 | `domain.prohibited_deletion` | yes | del-session-delete-patient, del-raw-sql | — |
| HEALTH-CHECK-002 | — | no | — | FHIR format is documentary |
| HEALTH-CHECK-003 | — | no | — | health isolation is documentary |
| CORE-CHECK-005 | `privacy.consent_transparency` | yes | consent-preticked-default, consent-optin-default-false | record completeness only WARNING |
| CORE-CHECK-006 | `privacy.rights_reachability` | yes | rights-seeded-missing, rights-clean-routes (WARNING tier) | no VIOLATION rule by design |
| CORE-CHECK-007 | `privacy.consent_transparency` | yes | consent-preticked-default | policy route only WARNING |
| CORE-CHECK-008 | — | no | — | documentary (incident register) |
| CORE-CHECK-009 | — | no | — | documentary (EIPD) |
| CORE-CHECK-010 | `privacy.third_party_transfers` | yes | transfers-seeded-host, transfers-clean-local (WARNING tier) | inventory is partial evidence; contracts documentary |
| CORE-CHECK-011 | `privacy.third_party_transfers` | yes | — | transfer basis documentary |
| CORE-CHECK-012 | `privacy.minors_and_sensitive` | yes | sensitive-biometric-raw, sensitive-biometric-token | age/geolocation only WARNING |
| CORE-CHECK-013 | `privacy.retention_minimization` | yes | retention-seeded-missing, retention-clean-field (WARNING tier) | no VIOLATION rule by design |
| ECOM-CHECK-001 | `privacy.consent_transparency` | yes | consent-preticked-default | unsubscribe only WARNING |
| ECOM-CHECK-002 | — | no | — | profiling notices documentary |
| ECOM-CHECK-003 | `privacy.payment_data_storage` | yes | pay-orm-card-number, pay-orm-cvv-mapped, pay-json-blob (known miss) | JSON column miss published |
| ECOM-CHECK-004 | — | no | — | PCI DSS is contractual |
| ECOM-CHECK-005 | `privacy.third_party_transfers` | yes | transfers-seeded-host, transfers-clean-local (WARNING tier) | contracts documentary |
| ECOM-CHECK-006 | — | no | — | billing retention documentary |
| ECOM-CHECK-007 | `privacy.minors_and_sensitive` | yes | sensitive-biometric-raw | socioeconomic fields not in the detector yet |

## Remaining gaps (registered, not hidden)

1. `privacy.rights_reachability`, `privacy.consent_transparency`, `privacy.minors_and_sensitive`,
   `privacy.retention_minimization` and `privacy.third_party_transfers` are `WARNING`-first. Their
   potential-risk precision/recall is now measured on targeted cases (`expected_warnings` /
   `warning_clean`, 1 seeded + 1 clean each, 1.0/1.0 on 2026-10-28) instead of being unmeasured.
   The sample is minimal and written by the detector's author, so it is not a blind benchmark.
2. `privacy.retention_minimization`, `privacy.rights_reachability` and
   `privacy.third_party_transfers` have no `VIOLATION` rule at all: they cannot produce a confirmed
   violation, only potential risk. T7 must seed potential-risk traps for them and report them in the
   secondary outcome, not in `oracle_violations`. A code-only check cannot prove that data was kept
   longer than needed.
3. `CL-DATAPROT-002/003/005/007` still have no detector. They are `implemented: false` with a
   `gap_reason` so no report can claim coverage.
4. The pre-commit gate evaluates only `privacy.cwe_532`, `privacy.api_exposure` and
   `privacy.payment_data_storage`. The dimension policies run in `compliance_check`, the validation
   engine and the experiment metrics, not in the hook (blocking a commit on a missing right would be
   a false positive on a partial index).
5. Layer C (agent review with the pack as a checklist) produces `potential_risk` and is not counted
   by `compliance_score`.
6. Layer B is Python-only (AST). The route/SQL/Prisma/template artifacts are language-neutral, but
   field and flow analysis for JS/TS/Go/Java is not implemented; registered as T28.
7. Cookies and the Agency instructions remain open in T21; no control depends on them yet.
