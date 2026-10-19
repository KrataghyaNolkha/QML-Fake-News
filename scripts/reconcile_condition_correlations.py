"""Reproduce the historical and deduplicated condition-number correlations."""

from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "outputs" / "tables" / "kernel_geometry_performance.csv"
OUTPUT = ROOT / "outputs" / "tables" / "condition_correlation_reconciliation.csv"


def correlation_row(label: str, data: pd.DataFrame, outlier_rule: str) -> dict:
    x = data["log10_condition_number"].astype(float)
    y = data["accuracy"].astype(float)
    return {
        "analysis": label,
        "transformation": "log10(condition_number)",
        "outlier_rule": outlier_rule,
        "n": len(data),
        "pearson_r": np.corrcoef(x, y)[0, 1],
        "spearman_rho": np.corrcoef(x.rank(method="average"), y.rank(method="average"))[0, 1],
    }


def main() -> None:
    frame = pd.read_csv(INPUT)
    required = {"condition_number", "accuracy", "correlation_included"}
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    frame = frame.replace([np.inf, -np.inf], np.nan).dropna(subset=["condition_number", "accuracy"]).copy()
    frame["log10_condition_number"] = np.log10(frame["condition_number"].astype(float))
    unique = frame[frame["correlation_included"].astype(bool)].copy()
    analyses = [
        ("Prior draft: all 25 sweep rows, duplicate retained", frame),
        ("Corrected: 24 distinct model settings", unique),
    ]

    rows = []
    for label, subset in analyses:
        rows.append(correlation_row(label, subset, "none"))
        z_scores = (subset["log10_condition_number"] - subset["log10_condition_number"].mean()) / subset[
            "log10_condition_number"
        ].std()
        retained = subset[z_scores.abs() <= 2.0]
        rows.append(correlation_row(label, retained, "exclude abs(z) > 2 on log10(condition_number)"))

    result = pd.DataFrame(rows)
    expected = [(-0.5210689779, -0.5174395987, 25), (-0.6715583726, -0.5999469000, 23),
                (-0.5163638012, -0.5191038316, 24), (-0.6670180091, -0.6061081789, 22)]
    for row, (pearson, spearman, n) in zip(result.to_dict("records"), expected):
        if row["n"] != n or not np.isclose(row["pearson_r"], pearson, atol=1e-9) or not np.isclose(
            row["spearman_rho"], spearman, atol=1e-9
        ):
            raise AssertionError(f"Correlation reconciliation changed unexpectedly: {row}")

    result.to_csv(OUTPUT, index=False)
    print(result.to_string(index=False))
    print(f"Saved reconciliation to {OUTPUT}")


if __name__ == "__main__":
    main()
