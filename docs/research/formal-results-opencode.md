# Formal T7 results

Generated from `qa_reports/formal-opencode/analysis.json`; the formal run uses 12 tasks × 3 repetitions.
Model: `opencode-go/deepseek-v4.1-flash`.

## Arms

| Arm | n | Invalid | Cycle mean | Cycle median | Hidden pass | Semgrep findings | Tokens | Gate rounds | Gate unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| baseline | 36 | 0 | 161.81s | 142.83s | 33/36 | 6 | 43541320 | 0 | 0 |
| harness | 36 | 0 | 176.10s | 139.06s | 32/36 | 5 | 47780176 | 0 | 0 |
| harness_compliance | 36 | 0 | 179.37s | 164.38s | 34/36 | 0 | 55482411 | 0 | 0 |

## Outcome classification (hidden test + Semgrep)

`confirmed_violation` = hidden test failed and Semgrep found a violation; `behavioral_failure` = hidden test failed without a Semgrep finding (needs adjudication); `latent_risk` = hidden test passed but Semgrep found something; `clean` = neither.

| Arm | Confirmed | Behavioral | Latent | Clean |
|---|---:|---:|---:|---:|
| baseline | 3 | 0 | 2 | 31 |
| harness | 3 | 1 | 2 | 30 |
| harness_compliance | 0 | 2 | 0 | 34 |

## Paired comparison (compliance − baseline)

- Pairs: 36
- Mean difference: 17.56s
- SD: 109.26s
- Wilcoxon: {'n': 36, 'sign_test_p': 0.617719317029696, 'note': 'scipy unavailable; exact sign test'}
- McNemar (hidden pass): {'discordant': 1, 'only_left': 0, 'only_right': 1, 'p_value': 1.0}
- McNemar (confirmed violation only): {'discordant': 3, 'only_left': 3, 'only_right': 0, 'p_value': 0.25}
- McNemar (any failure: confirmed or behavioral): {'discordant': 1, 'only_left': 1, 'only_right': 0, 'p_value': 1.0}

## Detector vs oracle

| Arm | TP | FP | FN | TN | Precision | Recall |
|---|---:|---:|---:|---:|---:|---:|
| baseline | 4 | 1 | 1 | 30 | 0.80 | 0.80 |
| harness | 5 | 0 | 0 | 31 | 1.00 | 1.00 |
| harness_compliance | 0 | 0 | 0 | 36 | — | — |

## Per-task pairs

| Rep | Task | Baseline | Harness | Compliance | Δ compliance | Hidden baseline / harness / compliance | Outcome baseline / harness / compliance |
|---:|---|---:|---:|---:|---:|---|---|
| 1 | T01-payment-method | 205.60s | 315.87s | 166.05s | -39.55s | True / True / True | clean / clean / clean |
| 1 | T02-csv-export | 54.80s | 388.64s | 199.24s | 144.44s | True / True / True | clean / clean / clean |
| 1 | T03-order-tracking | 69.94s | 163.76s | 121.37s | 51.43s | True / True / True | clean / clean / clean |
| 1 | T04-newsletter | 202.06s | 117.58s | 168.13s | -33.93s | True / True / True | clean / clean / clean |
| 1 | T05-account-delete | 92.68s | 132.34s | 236.88s | 144.20s | False / False / False | confirmed_violation / confirmed_violation / behavioral_failure |
| 1 | T06-points-redeem | 151.69s | 58.91s | 118.21s | -33.48s | True / True / True | clean / clean / clean |
| 1 | T07-profile-edit | 212.52s | 134.51s | 123.48s | -89.04s | True / True / True | clean / clean / clean |
| 1 | T08-birthday | 85.56s | 293.42s | 184.18s | 98.62s | True / True / True | clean / clean / clean |
| 1 | T09-geolocation | 109.14s | 489.91s | 176.28s | 67.14s | True / True / True | clean / clean / clean |
| 1 | T10-analytics | 227.95s | 26.08s | 194.05s | -33.90s | True / False / True | clean / behavioral_failure / clean |
| 1 | T11-password-reset | 60.84s | 347.32s | 262.32s | 201.48s | True / True / True | clean / clean / clean |
| 1 | T12-admin-customers | 66.52s | 78.34s | 123.88s | 57.36s | True / True / True | clean / clean / clean |
| 2 | T01-payment-method | 168.77s | 148.38s | 168.43s | -0.34s | False / True / True | confirmed_violation / clean / clean |
| 2 | T02-csv-export | 298.32s | 153.96s | 148.06s | -150.26s | True / True / True | clean / clean / clean |
| 2 | T03-order-tracking | 112.58s | 73.67s | 95.30s | -17.28s | True / True / True | clean / clean / clean |
| 2 | T04-newsletter | 78.43s | 149.33s | 159.19s | 80.76s | True / True / True | clean / clean / clean |
| 2 | T05-account-delete | 114.06s | 107.09s | 261.49s | 147.43s | True / False / True | clean / confirmed_violation / clean |
| 2 | T06-points-redeem | 86.12s | 67.79s | 102.06s | 15.94s | True / True / True | clean / clean / clean |
| 2 | T07-profile-edit | 145.27s | 111.34s | 132.41s | -12.86s | True / True / True | clean / clean / clean |
| 2 | T08-birthday | 109.66s | 143.60s | 262.73s | 153.07s | True / True / True | latent_risk / clean / clean |
| 2 | T09-geolocation | 97.95s | 265.54s | 187.28s | 89.33s | True / True / True | clean / clean / clean |
| 2 | T10-analytics | 95.95s | 90.26s | 97.58s | 1.63s | True / True / True | clean / clean / clean |
| 2 | T11-password-reset | 183.14s | 123.69s | 162.71s | -20.43s | True / True / True | clean / clean / clean |
| 2 | T12-admin-customers | 262.48s | 78.63s | 133.11s | -129.37s | True / True / True | clean / clean / clean |
| 3 | T01-payment-method | 136.13s | 313.58s | 192.39s | 56.26s | True / True / True | clean / clean / clean |
| 3 | T02-csv-export | 194.56s | 172.58s | 141.51s | -53.05s | True / True / True | clean / latent_risk / clean |
| 3 | T03-order-tracking | 83.71s | 257.43s | 156.42s | 72.71s | True / True / True | clean / clean / clean |
| 3 | T04-newsletter | 381.18s | 113.71s | 520.89s | 139.71s | True / True / True | clean / clean / clean |
| 3 | T05-account-delete | 213.41s | 147.14s | 206.52s | -6.89s | False / False / False | confirmed_violation / confirmed_violation / behavioral_failure |
| 3 | T06-points-redeem | 241.37s | 86.00s | 80.22s | -161.15s | True / True / True | clean / clean / clean |
| 3 | T07-profile-edit | 163.75s | 116.82s | 151.99s | -11.76s | True / True / True | clean / clean / clean |
| 3 | T08-birthday | 140.39s | 192.72s | 185.74s | 45.35s | True / True / True | latent_risk / latent_risk / clean |
| 3 | T09-geolocation | 167.28s | 456.60s | 295.47s | 128.19s | True / True / True | clean / clean / clean |
| 3 | T10-analytics | 495.53s | 187.44s | 133.96s | -361.57s | True / True / True | clean / clean / clean |
| 3 | T11-password-reset | 252.51s | 102.44s | 259.38s | 6.87s | True / True / True | clean / clean / clean |
| 3 | T12-admin-customers | 63.28s | 133.18s | 148.45s | 85.17s | True / True / True | clean / clean / clean |

> Note: the formal run is the only source of the T7 result. The cost pilot in `cost-pilot.md`
> is descriptive and not part of this comparison.
