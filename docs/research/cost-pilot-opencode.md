# Cost pilot — T7 / OpenCode Go

Date: 2026-10-31. Model: `opencode-go/deepseek-v4.1-flash` (fixed). Runtime: OpenCode headless
CLI 1.17.18. Tasks: T01 payment method, T03 order tracking, T04 newsletter, T05 account deletion,
T07 profile edit. One run per cell (5 tasks × 3 arms = 15 runs), all finished.

Each run was evaluated with the hidden acceptance test and the independent Semgrep oracle. `P/F` is
the hidden test result; the number after it is the oracle finding count.

| Task | Baseline | Harness | Compliance |
|---|---:|---:|---:|
| T01-payment-method | 192.0s P/1* | 211.3s P/1* | 247.4s P/1* |
| T03-order-tracking | 136.6s P/0 | 87.7s P/0 | 232.2s P/0 |
| T04-newsletter | 82.4s P/0 | 116.6s P/0 | 118.1s P/0 |
| T05-account-delete | 138.7s F/1 | 91.7s F/1 | 237.1s F/0 |
| T07-profile-edit | 407.6s P/0 | 66.7s P/0 | 117.0s P/0 |
| **Mean** | **191.5s** | **114.8s** | **190.4s** |

\* T01 oracle=1 is a **known false positive** of a first draft oracle rule (`dumbo.unmasked-rut-payload`)
that flagged the legitimate self-service RUT export in the base app. The rule was replaced before the
formal run (see `compliance-failure-diagnosis.md`). It does not affect the timing used for N.

## N

Paired difference (compliance − baseline): `[55.43, 95.60, 35.65, 98.39, −290.59]`, mean `−1.10s`,
SD `164.01s`. With the preregistered formula
`N = ceil((z_0.975 + z_0.80)^2 * sd^2 / delta^2)`, `delta = 0.5 * sd`, **N = 32 pairs**. The formula
yields 32 for any positive SD under this effect-size rule; the measured SD is reported for the power
discussion, not to change N.

The formal run uses 12 tasks × 3 repetitions (36 pairs), above N = 32. Mean cycle time is 165.5s, so
108 runs ≈ 5.0 hours of agent time plus evaluation. This exceeds the Cursor estimate (80–90 min);
the formal run is launched in the background and monitored with `formal_status.py`.

## Observations

- **The compliance arm is much more expensive.** It made 1–3 real gate calls, loaded skills, and used
  2.1M tokens on T05 (29 steps). The harness arm was the fastest on average (114.8s). One baseline
  cell (T03) also matched the `compliance_check.py` string because the agent wrote its own script;
  the counter now only records gate calls when the compliance gate is part of the arm, so the formal
  run will not attribute that to the baseline.
- **T07 baseline was an outlier** (407.6s, 30+ steps); it dominates the paired SD. The T07 compliance
  run was 117.0s, producing the only negative difference.
- **T05 remains the hard task.** Baseline and harness hard-deleted the customer (hidden fail, oracle
  hard-delete). The compliance arm registered an erasure request and anonymised the row, which the
  hidden test rejects because it requires the original email to be retained. The gate's remediation
  text was corrected after this pilot to say "retain until the retention period; do not anonymise
  before it", so the formal run reflects the fixed advice.
- **The gate is not free.** Gate calls add rounds and tokens; whether that buys fewer violations is
  the formal question.
- **No T12 cell** in the pilot (the 12-task pack is used in the formal run), so the exposure fix is
  covered by unit tests and the base-app cleanliness check, not by this pilot.

## What this does not say

It does not compare quality between arms. The hidden pass counts are descriptive and the sample is
five tasks once. The formal run is the source of the T7 result. The Cursor pilot and formal run are
not pooled.

## What can and cannot be concluded

Valid from the pilot (methodology and design):

- The OpenCode runner works end to end: isolated workspace, JSON events parsed, tokens and cost
  recorded, hidden test and Semgrep oracle executed, split-minute gate calls visible.
- N = 32 pairs and the ~5 h estimate for 108 runs.
- The customer-deletion policy fires where the old gate was silent: the compliance arm avoided the
  hard delete (oracle 1 in baseline/harness vs 0 in compliance, excluding the T01 false positive).
- The compliance arm pays for the gate: 9.7M tokens and $0.137 vs 3.7M and $0.078 for the harness
  arm, and it is slower than baseline on 4 of 5 tasks (+35s to +98s).

Not valid from the pilot:

- No time effect. The mean paired difference is −1.10s, but the SD is 164s and the sign flips when
  the T07 baseline outlier (407.6s) is excluded (+71s for compliance on the other four tasks).
- No hidden-test effect. All three arms pass 4/5; all fail T05. There is no discordant pair, so
  McNemar is not applicable.
- No violation effect that can be generalised. The only oracle difference after removing the T01
  false positive is one task (T05), and the compliance behaviour there was a design choice
  (anonymise) under the old remediation text, not the fixed one.
- The T01 oracle count is contaminated by the rejected first-draft rule; it must be read as zero.

Conclusion: the pilot freezes N and caught two defects before the formal run (the T01 oracle false
positive and the T05 remediation text). It is not evidence of no effect; it is evidence that five
single runs cannot resolve an effect with this variance.
