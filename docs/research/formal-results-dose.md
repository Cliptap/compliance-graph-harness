# Formal T7 results

Generated from `qa_reports/formal-dose/analysis.json`.
Model: `opencode-go/deepseek-v4.1-flash`.

## Arms

| Arm | n | Invalid | Cycle mean | Cycle median | Hidden pass | Semgrep findings | Tokens | Gate rounds | Gate unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| baseline | 20 | 0 | 87.21s | 80.43s | 6/20 | 11 | 15616182 | 0 | 0 |
| rules | 20 | 0 | 65.45s | 54.33s | 7/20 | 8 | 8018926 | 0 | 0 |
| rules_skills | 20 | 0 | 94.30s | 74.88s | 9/20 | 3 | 12839933 | 0 | 0 |
| rules_skills_gate | 20 | 0 | 133.56s | 116.88s | 18/20 | 4 | 35808267 | 0 | 0 |
| rules_skills_gate_enforced | 20 | 0 | 154.96s | 120.61s | 14/20 | 0 | 35343560 | 0 | 0 |

## Outcome classification (hidden test + Semgrep)

`confirmed_violation` = hidden test failed and Semgrep found a violation; `behavioral_failure` = hidden test failed without a Semgrep finding (needs adjudication); `latent_risk` = hidden test passed but Semgrep found something; `clean` = neither.

| Arm | Confirmed | Behavioral | Latent | Clean |
|---|---:|---:|---:|---:|
| baseline | 8 | 6 | 2 | 4 |
| rules | 7 | 6 | 1 | 6 |
| rules_skills | 3 | 8 | 0 | 9 |
| rules_skills_gate | 0 | 2 | 3 | 15 |
| rules_skills_gate_enforced | 0 | 6 | 0 | 14 |

## Behavioral failure split

| Arm | Task completion | Test artifact | Privacy behavioral |
|---|---:|---:|---:|
| baseline | 0 | 5 | 1 |
| rules | 3 | 3 | 0 |
| rules_skills | 4 | 4 | 0 |
| rules_skills_gate | 0 | 2 | 0 |
| rules_skills_gate_enforced | 2 | 4 | 0 |

## Paired comparison (compliance − baseline)

- Pairs: 0
- Mean difference: —s
- SD: —s
- Wilcoxon: {'n': 0, 'note': 'no pairs'}
- McNemar (hidden pass): {'discordant': 0, 'only_left': 0, 'only_right': 0, 'p_value': 1.0}
- McNemar (confirmed violation only): {'discordant': 0, 'only_left': 0, 'only_right': 0, 'p_value': 1.0}
- McNemar (any failure: confirmed or behavioral): {'discordant': 0, 'only_left': 0, 'only_right': 0, 'p_value': 1.0}

## Dose contrasts (each arm vs baseline)

| Arm | n | Δ mean | Δ SD | McNemar confirmed | McNemar any failure |
|---|---:|---:|---:|---|---|
| rules | 20 | -21.76s | 41.72s | {'discordant': 5, 'only_left': 3, 'only_right': 2, 'p_value': 1.0} | {'discordant': 3, 'only_left': 2, 'only_right': 1, 'p_value': 1.0} |
| rules_skills | 20 | 7.09s | 95.44s | {'discordant': 7, 'only_left': 6, 'only_right': 1, 'p_value': 0.125} | {'discordant': 5, 'only_left': 4, 'only_right': 1, 'p_value': 0.375} |
| rules_skills_gate | 20 | 46.35s | 55.03s | {'discordant': 8, 'only_left': 8, 'only_right': 0, 'p_value': 0.0078125} | {'discordant': 12, 'only_left': 12, 'only_right': 0, 'p_value': 0.00048828125} |
| rules_skills_gate_enforced | 20 | 67.75s | 121.80s | {'discordant': 8, 'only_left': 8, 'only_right': 0, 'p_value': 0.0078125} | {'discordant': 10, 'only_left': 9, 'only_right': 1, 'p_value': 0.021484375} |

## Detector vs oracle

| Arm | TP | FP | FN | TN | Precision | Recall |
|---|---:|---:|---:|---:|---:|---:|
| baseline | 9 | 2 | 1 | 8 | 0.82 | 0.90 |
| rules | 7 | 1 | 1 | 11 | 0.88 | 0.88 |
| rules_skills | 3 | 1 | 0 | 16 | 0.75 | 1.00 |
| rules_skills_gate | 0 | 0 | 3 | 17 | — | 0.00 |
| rules_skills_gate_enforced | 0 | 0 | 0 | 20 | — | — |

> Note: the formal run is the only source of the T7 result. The cost pilot in `cost-pilot.md`
> is descriptive and not part of this comparison.
