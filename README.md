# Benford's Law and Anomaly Detection in Financial Data

A Python project that tests how well Benford's Law, business rules, and statistical outlier methods can flag suspicious transactions in a financial ledger. The ledger is synthetic and contains deliberately planted anomalies, so every method is scored against known ground truth. Results were then replicated on an independently generated ledger.

## Summary (plain English)

Auditors screen large ledgers for transactions worth a closer look. I built a fake ledger of 5,040 payments with 130 hidden problems and tested several screening methods on it.

- Simple behaviour-based rules (round amounts, amounts just under an approval limit, duplicate payments) together caught **100 of the 130** problems, and caught the same 100 on a second, independently generated ledger.
- Standard statistical outlier tests (Z-scores) caught **none**, because the planted problems were not unusually large or small.
- Benford's Law could tell that something was wrong when it examined a suspect group of fabricated amounts, but it was a weak detector across the whole ledger and across individual vendors.
- All 30 fabricated transactions were missed by every rule, which shows the limit of rules aimed at specific patterns.
- The takeaway is that screening tools produce candidates for investigation, not proof of fraud, and that combining methods works better than relying on one.

## Data

`src/generate_ledger.py` creates a ledger with 5,040 transactions across 50 vendors and 5 categories, amounts in BND, and an approval limit of BND 5,000. Clean amounts are drawn from a log-normal distribution, so they follow Benford's Law approximately. The original ledger uses seed 42, and the independent test ledger uses seed 123.

Planted anomalies (130 per ledger):

| Type | Count | How it was planted |
|---|---|---|
| Round-number | 30 | Amounts of 1,000, 2,000, 3,000, 8,000 or 10,000 |
| Below-threshold | 30 | Amounts between 95% and 99.9% of the approval limit |
| Fabricated | 30 | First digits chosen roughly uniformly instead of following Benford |
| Duplicate | 40 | Copies of clean transactions with the date shifted by 0 to 3 days |

## Methods

1. First-digit analysis against Benford's expected distribution, with a chi-square goodness-of-fit test and Mean Absolute Deviation (MAD)
2. Benford analysis on the clean transactions, on the fabricated group, and per vendor
3. Rule-based screens: round numbers, just below the approval limit, and duplicates (same vendor, category and amount)
4. Z-score outliers on raw and log-transformed amounts (threshold |Z| > 3)
5. A combined anomaly score (sum of the rule flags), evaluated with precision and recall
6. Sensitivity analysis: a grouped 80/20 split (matching transactions kept together) repeated over five seeds
7. Replication: the same rules, with unchanged definitions, applied to a newly generated ledger

## Results

Precision and recall are both measured against all 130 planted anomalies, so the methods can be compared directly.

**Original ledger (seed 42)**

| Method | Flagged | Precision | Recall |
|---|---|---|---|
| Round-number rule | 30 | 100.0% | 23.1% |
| Below-threshold rule | 57 | 52.6% | 23.1% |
| Duplicate detection | 80 | 50.0% | 30.8% |
| Raw Z-score | 37 | 0.0% | 0.0% |
| Log Z-score | 15 | 0.0% | 0.0% |
| **Combined rules** | 167 | 59.9% | **76.9%** |

**Independent ledger (seed 123, rules unchanged)**

| Method | Flagged | Precision | Recall |
|---|---|---|---|
| Round-number rule | 30 | 100.0% | 23.1% |
| Below-threshold rule | 60 | 50.0% | 23.1% |
| Duplicate detection | 84 | 47.6% | 30.8% |
| **Combined rules** | 174 | 57.5% | **76.9%** |

The combined rules caught 100 of 130 anomalies on both ledgers. On the independent ledger they flagged 74 clean transactions, and by anomaly type they missed every fabricated transaction (30 of 30) and none of the others.

**Stability across five grouped splits of the original ledger** (test sets of about 1,000 rows)

| Method | Mean precision | Mean recall |
|---|---|---|
| Round-number rule | 100.0% | 22.0% |
| Below-threshold rule | 49.5% | 19.8% |
| Duplicate detection | 50.0% | 37.2% |
| **Combined rules** | 58.3% | **79.1%** (SD 5.6 points) |

**Benford results**

| Data | Chi-square (8 df) | p-value | MAD |
|---|---|---|---|
| Original ledger, full | 20.09 | 0.010 | 0.0059 |
| Original ledger, clean only | 12.54 | 0.129 | 0.0052 |
| Original ledger, fabricated only (n = 30) | 33.56 | < 0.001 | 0.0826 |
| Independent ledger, full | 17.34 | 0.027 | 0.0052 |
| Independent ledger, clean only | 13.72 | 0.089 | 0.0045 |
| Independent ledger, fabricated only (n = 30) | 40.45 | < 0.001 | 0.0987 |

Key findings:

- **Ledger-wide Benford testing is weak.** 130 anomalies among 5,040 rows barely shift the overall digit distribution. Chi-square rejects Benford for the full ledgers but not for the clean rows, while MAD stays in the "close conformity" range throughout.
- **Benford is powerful on a concentrated group.** The fabricated transactions deviate strongly (under-represented digits 1 and 2, over-represented digits 5, 7 and 8), but only once they are isolated.
- **Vendor-level Benford screening did not work.** Each vendor has only 71 to 119 transactions, so sampling noise dominates. Every vendor's MAD (0.014 to 0.035) is above the usual conformity thresholds, and the correlation between vendor MAD and anomaly count is about 0.03.
- **Z-scores found nothing.** The flagged transactions were all legitimate large or small amounts, because the planted anomalies are behavioural rather than extreme.
- **Combining rules more than doubles the coverage of the best single rule**, and the result was stable across splits and on a new ledger, but the 30 fabricated transactions are missed entirely, since none of the rules target them.

## Limitations

- The data is synthetic and the rules were written knowing how the anomalies were planted, so the near-perfect recall of each rule on its own anomaly type is partly circular.
- The independent ledger comes from the same generator, so it shows the results are reproducible across random samples, not that the rules would work on real financial records.
- The rules have no fitted parameters, so the repeated splits measure sampling variability on this dataset, not generalisation to unseen data.
- The round-number rule's perfect precision is an artefact of this dataset. Real ledgers contain many legitimate round amounts (rent, salaries, fixed fees).
- The duplicate rule flags both members of each pair, so row-level precision is capped at about 50%. At pair level, all 40 planted duplicates were found in the original ledger.
- A Benford-based rule built from the fabricated group's digits would leak label information, so it is kept as exploratory analysis and left out of the combined score. The fabricated group is also small (n = 30), so the chi-square approximation is rough there.
- A flag means "worth investigating", not "fraud".

## Repository structure

```
data/           synthetic_ledger.csv (generated)
notebooks/      01_benford_analysis.ipynb
src/            generate_ledger.py
requirements.txt
README.md
```

## How to run

```bash
pip install -r requirements.txt
python src/generate_ledger.py      # writes data/synthetic_ledger.csv
jupyter notebook notebooks/01_benford_analysis.ipynb
```

Requirements: pandas, numpy, scipy, matplotlib, scikit-learn, jupyter.

## Possible extensions

- Isolation Forest on engineered features (distance to the approval limit, vendor frequency, day of week)
- Benford second-digit and first-two-digit tests
- A rule or test aimed at the fabricated transactions that does not use their labels
- Repeating the independent-ledger test over many seeds and reporting mean and standard deviation