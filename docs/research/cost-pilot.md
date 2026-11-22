# Cost pilot — T7 / Fase 5

Date: 2026-10-30. Model: `composer-2.5` (fixed). Runtime: Cursor SDK local bridge. Tasks:
T01 payment method, T03 order tracking, T04 newsletter, T05 account deletion, T07 profile edit.
One run per cell (5 tasks × 3 arms = 15 runs).

Each run was evaluated with the hidden acceptance test and the independent Semgrep oracle.
`P/F` is the hidden test result; the number after it is the oracle finding count.

| Task | Baseline | Harness | Compliance |
|---|---:|---:|---:|
| T01-payment-method | 97.8s P/0 | 60.0s P/0 | 53.7s P/0 |
| T03-order-tracking | 47.6s P/0 | 50.9s P/0 | 40.6s P/0 |
| T04-newsletter | 56.7s P/0 | 38.5s F/1 | 47.0s P/0 |
| T05-account-delete | 47.2s P/0 | 60.3s P/0 | 53.5s P/0 |
| T07-profile-edit | 29.5s P/0 | 43.5s P/0 | 52.7s P/0 |
| **Mean** | **55.8s** | **50.7s** | **49.5s** |
| SD | 25.5s | 9.7s | 5.7s |
| Hidden pass | 5/5 | 4/5 | 5/5 |
| Oracle findings | 0 | 1 | 0 |

## N

Paired difference (compliance − baseline): `[-44.08, -7.00, -9.61, 6.20, 23.15]`, mean `-6.27s`,
SD `24.81s`. With the preregistered formula
`N = ceil((z_0.975 + z_0.80)^2 * sd^2 / delta^2)`, `delta = 0.5 * sd`, `N = 32` pairs.
At ~52s per run, 32 pairs × 3 arms ≈ 96 runs ≈ 80–90 minutes of agent time, plus evaluation.

The formal run will use the 12 tasks with 3 repetitions (36 pairs), above the frozen minimum of 32.
N is frozen at 32; the extra repetitions are reported as achieved power, not as a new target.

## Observations

- **Variance dominates this pilot.** One run per cell is not an efficacy result. Earlier runs had
  T01 failing in baseline and in the compliance arm; this rerun had baseline and compliance passing
  and the harness arm failing T04 with one oracle finding. The formal run needs repetitions.
- **The oracle caught T04** (pre-ticked newsletter consent) while the hidden test failed; the
  Semgrep rule added independent evidence.
- **No clear time penalty** for the harness arms in this sample: compliance was slightly faster than
  baseline on average, with a wide paired SD. The earlier pilot had the opposite sign on T05. This
  is exactly why N was derived from measured variance.
- **Rounds were 1 in every run**; the compliance gate produced no extra feedback rounds here. The
  gate’s cost may appear on tasks where it reports a violation; T01’s earlier failure was a detector
  miss, not a gate round.
- **Base tests** were green in the workspaces after the photo test was skipped when photo assets are
  not copied; the previous pilot’s `tests: 1 failed` was the missing photo fixture, not the agent.

## What this does not say

It does not compare quality between arms. The hidden pass counts are descriptive and the sample is
five tasks once. The formal run (Fase 6) is the source of the T7 results.
