"""Generate a synthetic ledger with known, planted anomalies.

Because we plant the anomalies ourselves, every detection method can later
be scored against ground truth (precision, recall, false-positive rate).
"""
import numpy as np
import pandas as pd


def generate_ledger(n=5000, approval_limit=5000, seed=42):
    rng = np.random.default_rng(seed)

    vendors = [f"V{i:03d}" for i in range(1, 51)]
    categories = ["Supplies", "Utilities", "Travel", "Maintenance", "Consulting"]

    df = pd.DataFrame({
        "date": pd.to_datetime("2025-01-01")
                + pd.to_timedelta(rng.integers(0, 365, n), unit="D"),
        "vendor": rng.choice(vendors, n),
        "category": rng.choice(categories, n),
        # Log-normal with a wide spread gives roughly Benford-like first digits
        "amount": np.round(rng.lognormal(mean=6.5, sigma=1.5, size=n), 2),
    })
    df["is_anomaly"] = False
    df["anomaly_type"] = ""

    # Pick non-overlapping rows to corrupt (30 of each type)
    pool = rng.choice(n, size=90, replace=False)
    round_idx, below_idx, fake_idx = pool[:30], pool[30:60], pool[60:90]

    # 1. Suspiciously round amounts
    df.loc[round_idx, "amount"] = rng.choice([1000, 2000, 3000, 8000, 10000], 30)
    df.loc[round_idx, ["is_anomaly", "anomaly_type"]] = [True, "round_number"]

    # 2. Amounts just under the approval limit
    df.loc[below_idx, "amount"] = np.round(
        rng.uniform(0.95, 0.999, 30) * approval_limit, 2)
    df.loc[below_idx, ["is_anomaly", "anomaly_type"]] = [True, "below_threshold"]

    # 3. Fabricated amounts: people tend to pick first digits ~uniformly
    digit = rng.integers(1, 10, 30)
    magnitude = 10 ** rng.integers(2, 4, 30)
    df.loc[fake_idx, "amount"] = (
        digit * magnitude + rng.integers(0, magnitude) + rng.integers(0, 100, 30) / 100)
    df.loc[fake_idx, ["is_anomaly", "anomaly_type"]] = [True, "fabricated"]

    # 4. Duplicate payments: copy clean rows, shift the date by 0-3 days
    dups = df[~df["is_anomaly"]].sample(40, random_state=seed).copy()
    dups["date"] += pd.to_timedelta(rng.integers(0, 4, len(dups)), unit="D")
    dups["is_anomaly"] = True
    dups["anomaly_type"] = "duplicate"
    df = pd.concat([df, dups], ignore_index=True)

    return df.sort_values("date").reset_index(drop=True)


def first_digit(x):
    return int(f"{x:.2f}".lstrip("0.")[0])


if __name__ == "__main__":
    ledger = generate_ledger()
    ledger.to_csv("data/synthetic_ledger.csv", index=False)

    print(f"Rows: {len(ledger)}")
    print(ledger["anomaly_type"].replace("", "clean").value_counts())

    # Sanity check: clean rows should look roughly Benford (30.1% start with 1)
    clean = ledger[~ledger["is_anomaly"]]
    share_one = (clean["amount"].map(first_digit) == 1).mean()
    print(f"Clean rows starting with digit 1: {share_one:.1%} (Benford: 30.1%)")
