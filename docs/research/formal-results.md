# Formal T7 results

Generated from `qa_reports/formal/analysis.json`; the formal run uses 12 tasks × 3 repetitions.

> **PROVISIONAL**: 79/108 runs finished; 29 invalid. Rerun the invalid cells before using these results.
> Invalid runs failed with the Cursor SDK message: `You're out of usage. Switch to Auto, or ask your admin to increase your limit.`

## Arms

| Arm | n | Invalid | Cycle mean | Cycle median | Hidden pass | Oracle findings | Tokens |
|---|---:|---:|---:|---:|---:|---:|---:|
| baseline | 31 | 5 | 61.50s | 42.47s | 29/31 | 2 | 25260443 |
| harness | 24 | 12 | 45.98s | 43.20s | 23/24 | 0 | 18302856 |
| harness_compliance | 24 | 12 | 44.28s | 43.70s | 19/24 | 2 | 19365539 |

## Paired comparison (compliance − baseline)

- Pairs: 24
- Mean difference: -23.16s
- SD: 44.46s
- Wilcoxon: {'n': 24, 'sign_test_p': 0.5412561893463135, 'note': 'scipy unavailable; exact sign test'}
- McNemar (hidden pass): {'discordant': 5, 'only_left': 4, 'only_right': 1, 'p_value': 0.375}

## Detector vs oracle

| Arm | TP | FP | FN | TN | Precision | Recall |
|---|---:|---:|---:|---:|---:|---:|
| baseline | 1 | 0 | 1 | 29 | 1.00 | 0.50 |
| harness | 0 | 0 | 0 | 24 | — | — |
| harness_compliance | 0 | 0 | 2 | 22 | — | 0.00 |

## Per-task pairs

| Rep | Task | Baseline | Harness | Compliance | Δ compliance | Hidden baseline / harness / compliance |
|---:|---|---:|---:|---:|---:|---|
| 1 | T01-payment-method | 98.54s | 83.76s | 42.73s | -55.81s | True / False / False |
| 1 | T02-csv-export | 158.74s | 70.22s | 38.03s | -120.71s | True / True / True |
| 1 | T03-order-tracking | 188.18s | 51.97s | 40.89s | -147.29s | True / True / True |
| 1 | T04-newsletter | 133.34s | 48.94s | 43.73s | -89.61s | True / True / True |
| 1 | T05-account-delete | 92.36s | 54.09s | 47.63s | -44.73s | True / True / False |
| 1 | T06-points-redeem | 82.48s | 44.42s | 36.84s | -45.64s | True / True / True |
| 1 | T07-profile-edit | 41.39s | 42.41s | 47.39s | 6.00s | True / True / True |
| 1 | T08-birthday | 44.45s | 51.47s | 49.88s | 5.43s | True / True / True |
| 1 | T09-geolocation | 79.27s | 37.85s | 48.70s | -30.57s | True / True / True |
| 1 | T10-analytics | 100.92s | 37.39s | 39.91s | -61.01s | True / True / True |
| 1 | T11-password-reset | 66.63s | 47.51s | 45.60s | -21.03s | True / True / True |
| 1 | T12-admin-customers | 45.92s | 34.36s | 51.20s | 5.28s | True / True / True |
| 2 | T01-payment-method | 58.12s | 59.07s | 39.33s | -18.79s | True / True / False |
| 2 | T02-csv-export | 36.38s | 34.86s | 43.55s | 7.17s | True / True / True |
| 2 | T03-order-tracking | 42.47s | 40.44s | 38.96s | -3.51s | True / True / True |
| 2 | T04-newsletter | 35.88s | 43.44s | 54.90s | 19.02s | False / True / True |
| 2 | T05-account-delete | 40.39s | 42.95s | 58.39s | 18.00s | False / True / False |
| 2 | T06-points-redeem | 35.03s | 35.36s | 51.70s | 16.67s | True / True / True |
| 2 | T07-profile-edit | 38.00s | 31.84s | 29.78s | -8.22s | True / True / True |
| 2 | T08-birthday | 36.88s | 44.96s | 45.32s | 8.44s | True / True / True |
| 2 | T09-geolocation | 42.44s | 38.91s | 37.26s | -5.18s | True / True / True |
| 2 | T10-analytics | 28.85s | 35.37s | 39.00s | 10.15s | True / True / True |
| 2 | T11-password-reset | 48.04s | 50.53s | 48.44s | 0.40s | True / True / True |
| 2 | T12-admin-customers | 43.97s | 41.43s | 43.68s | -0.29s | True / True / False |

> Note: the formal run is the only source of the T7 result. The cost pilot in `cost-pilot.md`
> is descriptive and not part of this comparison.
