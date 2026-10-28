# Experiment A variants

Mutated copies of `experiments/supermercado`, each with exactly one seeded defect, plus clean
controls. The manifest (`manifest.json`) is the known truth of the audit experiment and must never
be copied into an audit workspace: the auditor sees only the built variant.

## Build and self-check

```powershell
python experiments/variants/build.py --list
python experiments/variants/build.py            # verify every variant against the detectors
python experiments/variants/build.py --write    # keep the copies under generated/ (gitignored)
python experiments/variants/build.py --only V01-log-rut-direct --write
```

The self-check uses the harness `PolicyEngine` as a sanity check of the mutation, not as the
experiment oracle. Experiment A is judged by the auditor's findings against the manifest.

## Manifest shape

```json
{
  "id": "V01-log-rut-direct",
  "kind": "seeded | clean",
  "description": "one line",
  "mutations": [{"op": "replace | add_file | delete_file", "...": "..."}],
  "expected": [{
    "control": "CORE-CHECK-002",
    "policy": "privacy.cwe_532",
    "detector_status": "VIOLATION | WARNING",
    "audit_outcome": "confirmed_violation | potential_risk"
  }]
}
```

The detector status is the deterministic policy result; the audit outcome is the expected verdict
in the pack vocabulary. A clean variant expects no finding.

## Rules

- One conceptual defect per variant. Two edits are allowed only when both are needed to express
  the same defect (for example, a route and its registration).
- The base copy comes from `experiments/supermercado`; variants are never edited by hand.
- The auditor workspace excludes `manifest.json`, `build.py` and `generated/`.
- Do not add a variant that requires a detector which does not exist; if the expected outcome is a
  known detector gap, record it as such in the manifest and report it as a harness false negative.

## Current batch

Seeded: V01 direct RUT log, V02 RUT through a call, V03 card number stored, V04 CVV stored,
V05 pre-checked consent, V06 API exposes RUT, V07 API exposes credentials, V08 raw biometric
template, V09 erasure route missing, V10 privacy route missing.

Clean: C01 base, C02 harmless helper, C03 masked JSON response.
