# Dose conclusions — which harness component reduces violations?

Status: final for the dose run (2026-11-02). Model `opencode-go/deepseek-v4.1-flash`.
Data: `qa_reports/formal-dose/` (100 runs, 100 finished, 0 invalid), generated report
`docs/research/formal-results-dose.md`.

## Design

Five arms, same 4 held-out tasks (T31, T33, T34, T35), 5 repetitions:

| Arm | `AGENTS.md` | Skills | Gate CLI + instruction | External enforcement |
|---|---|---|---|---|
| `baseline` | no | no | no | no |
| `rules` | yes | no | no | no |
| `rules_skills` | yes | 12 pipeline | no | no |
| `rules_skills_gate` | yes | 12 + 3 compliance | yes | no |
| `rules_skills_gate_enforced` | yes | 12 + 3 compliance | yes | yes |

## Results

| Arm | Confirmed | Behavioral | Latent | Clean | Hidden (raw) | Semgrep | Gate calls | Tokens |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| baseline | 8 | 6 | 2 | 4 | 6/20 | 11 | 0 | 15.6M |
| rules | 7 | 6 | 1 | 6 | 7/20 | 8 | 0 | 8.0M |
| rules_skills | 3 | 8 | 0 | 9 | 9/20 | 3 | 0 | 12.8M |
| rules_skills_gate | **0** | 2 | 3 | 15 | **18/20** | 4 | 25 | 35.8M |
| rules_skills_gate_enforced | **0** | 6 | 0 | 14 | 14/20 | 0 | 25 | 35.3M |

> Hidden counts are raw. After the T34 test fix, the corrected hidden counts are baseline 11/20,
> rules 10/20, rules_skills 13/20, rules_skills_gate 20/20 and rules_skills_gate_enforced 18/20.
> The confirmed column is unchanged.

### Behavioral failure split

A hidden-test failure without a Semgrep finding is not necessarily a privacy failure. The analysis
now separates it:

| Arm | Task completion | Test artifact | Privacy behavioral |
|---|---:|---:|---:|
| baseline | 0 | 5 | 1 |
| rules | 3 | 3 | 0 |
| rules_skills | 4 | 4 | 0 |
| rules_skills_gate | 0 | 2 | 0 |
| rules_skills_gate_enforced | 2 | 4 | 0 |

- **Task completion** = the endpoint was not implemented (`404`).
- **Test artifact** = the old T34 test rejected the field name `api_key` even when its value was
  empty/masked; the test is now fixed to reject only a non-empty value.
- **Privacy behavioral** = a hidden failure without Semgrep that is not a completion or test issue.

Contrasts against baseline (paired, 20 pairs):

| Arm | Δ time | McNemar confirmed | McNemar any failure |
|---|---:|---|---|
| rules | −21.8s | 3/2, **p=1.0** | 2/1, p=1.0 |
| rules_skills | +7.1s | 6/1, **p=0.125** | 4/1, p=0.375 |
| rules_skills_gate | +46.3s | **8/0, p=0.0078** | **12/0, p=0.0005** |
| rules_skills_gate_enforced | +67.8s | **8/0, p=0.0078** | 9/1, p=0.021 |

## What the dose attributes

1. **The rules alone do nothing.** `rules` vs baseline is a coin flip on confirmed violations
   (3/2, p=1.0). Writing the rules into `AGENTS.md` is not sufficient.
2. **The skills help, but not enough.** `rules_skills` reduces confirmed violations from 8 to 3
   (6/1 discordant, p=0.125) and Semgrep findings from 11 to 3, but it adds behavioral failures
   (8/20 raw; 4 remain as task completion after the T34 test fix) and does not reach significance with 20 pairs.
3. **The gate is the decisive component.** `rules_skills_gate` eliminates confirmed violations
   (8/0, p=0.0078) and improves hidden passes from 6/20 to 20/20 after the T34 test fix (18/20 raw). The effect survives the
   conservative "any failure" outcome (12/0, p=0.0005).
4. **External enforcement adds nothing here.** Both gate arms made 25 gate CLI calls and the
   external feedback loop never fired (0 rounds). The gate arms are effectively the same treatment;
   the advisory gate is simpler and has fewer adjudicated failures after the T34 test fix (0 vs 2 task-completion failures; 2 vs 6 raw) in this sample.
   The enforcement contrast is not a clean test because the loop never triggered.
5. **The gate costs about 2.3× tokens** (35.8M vs 15.6M) and some time (+46s to +68s, large SD).
   The primary outcome is violations; the cost is the price of the effect.

## Mechanism and caveats

- The gate's effect is the **instruction + local CLI + the agent's self-correction before finishing**:
  25 gate calls per gate arm, final code clean of confirmed violations. The external feedback loop
  was not the mechanism.
- The detector-vs-oracle table shows TP=0 in the gate arms because the final code was already fixed;
  the detector's value is the in-run feedback, not the post-hoc finding.
- The 3 latent risks in the advisory gate are Semgrep findings with a passing hidden test, most likely
  the known `hard-delete-orders` false positive on a retention-aware delete.
- The two `behavioral_failure` cells in the advisory gate are **T34 rep1 and rep5** (`test artifact`):
  the agent returned a safe config with empty or masked `api_key` fields (`{"api_key": "",
  "configured": false}`, `{"api_key_configured": false, "api_key_masked": ""}`), but the old hidden
  test rejected the field name itself. The test now rejects only a non-empty value; the gate's
  silence was correct, not a miss.
- The three `latent_risk` cells in the advisory gate are **oracle false positives**: T31 rep1/rep3
  (`hard-delete-orders` on a retention-aware delete; the hidden test passes) and T33 rep5
  (`log-sensitive` matched "print" inside `_token_fingerprint`; the token was SHA-256 hashed, not
  logged). The Semgrep rule now uses word boundaries; the T31 retention-aware case remains a declared
  oracle limitation.
- The two extra T31 failures in the enforced arm (rep2/rep3) are 404 endpoints not implemented
  (`task completion`), not privacy violations. The external feedback loop never fired. The advisory
  gate implemented the endpoint in all 5 repetitions; the enforced arm missed it in 2 of 5.
- **Privacy vs completion.** With the split, the privacy result is **40/40 gate cells without a
  confirmed violation** (0 confirmed in both 20-cell gate arms). Task completion is **20/20 for the
  advisory gate** and **18/20 for the enforced gate**; the 2 misses are T31 404s, not privacy. This
  is the design alignment: the primary outcome is the confirmed privacy violation; task completion is
  reported separately and is not charged to the gate.
- The current run did **not** include a completion checklist in the gate instruction. For the next
  run the instruction adds a definition-of-done (implement the route in `TASK.md`, run
  `python -m pytest tests -q`), so completion is nudged without touching the hidden acceptance tests.
- The formal is **not re-scored**. The adjudication above is the interpretation; future runs use the
  corrected T34 test and the corrected Semgrep regex. The primary conclusion is unchanged: the gate
  eliminated the confirmed violations, and the residual gate-arm counts were test/oracle artifacts.
- 20 pairs per contrast, 4 tasks, one model. The gate contrasts are significant; the skills contrast
  is not. Do not pool with the 12-task formal or the Cursor run.

## Recommendation

Adopt the **advisory gate** (`rules_skills_gate`) as the effective configuration: it eliminates
confirmed violations at a lower complexity than the enforced arm, and the enforcement loop did not
fire. Keep the skills (they contribute to the direction), but do not rely on the rules alone. If the
gate is removed, the confirmed-violation rate returns to the baseline level.
