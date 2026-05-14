from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from arges import run_arges_like
from h2pc import run_h2pc
from mmhc import run_mmhc
from preprocessing import DEFAULT_DATASET_PATH


ROOT = Path(__file__).resolve().parent


METRIC_COLUMNS = [
    "Prediction Accuracy",
    "Balanced Accuracy",
    "Macro F1",
    "AUC",
    "Log Loss",
    "Brier Score",
    "Inference Success Rate",
    "Failed Queries",
]


def _aggregate(df: pd.DataFrame, group_col: str, metric_cols: list[str]) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for key, group in df.groupby(group_col, dropna=False):
        record: dict[str, object] = {group_col: key}
        for col in metric_cols:
            values = pd.to_numeric(group[col], errors="coerce").dropna().to_numpy(dtype=float)
            if values.size == 0:
                record[f"{col} Mean"] = None
                record[f"{col} Std"] = None
                continue
            record[f"{col} Mean"] = float(np.mean(values))
            record[f"{col} Std"] = float(np.std(values, ddof=1)) if values.size > 1 else 0.0
        rows.append(record)

    return pd.DataFrame(rows)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run repeated train/test validations and summarize predictive metrics."
    )
    parser.add_argument("--file-path", default=str(DEFAULT_DATASET_PATH))
    parser.add_argument("--sample-size", type=int, default=None)
    parser.add_argument("--output-dir", default=str(ROOT))
    parser.add_argument("--repeats", type=int, default=5)
    args = parser.parse_args()

    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    runs: list[dict[str, object]] = []
    for repeat in range(args.repeats):
        outcomes = [
            run_mmhc(file_path=args.file_path, sample_size=args.sample_size),
            run_h2pc(file_path=args.file_path, sample_size=args.sample_size),
            run_arges_like(file_path=args.file_path, sample_size=args.sample_size),
        ]

        for outcome in outcomes:
            row = dict(outcome["result"])
            row["Repeat"] = repeat
            runs.append(row)

    runs_df = pd.DataFrame(runs)
    runs_path = output_dir / "validation_runs.csv"
    runs_df.to_csv(runs_path, index=False)

    summary_df = _aggregate(runs_df, group_col="Algorithm", metric_cols=METRIC_COLUMNS)
    summary_path = output_dir / "validation_summary.csv"
    summary_df.to_csv(summary_path, index=False)

    display_cols = ["Algorithm"] + [f"{c} Mean" for c in METRIC_COLUMNS]
    print(summary_df[display_cols].to_string(index=False))
    print(f"\nSaved per-run results to {runs_path}")
    print(f"Saved aggregated summary to {summary_path}")


if __name__ == "__main__":
    main()
