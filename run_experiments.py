from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from arges import run_arges_like
from evaluation import edges_to_frame
from h2pc import run_h2pc
from mmhc import run_mmhc
from preprocessing import DEFAULT_DATASET_PATH


ROOT = Path(__file__).resolve().parent


def save_edges(edges: list[tuple[str, str]], path: Path) -> None:
    edges_to_frame(edges).to_csv(path, index=False)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run all Bayesian network structure-learning experiments.")
    parser.add_argument("--file-path", default=str(DEFAULT_DATASET_PATH))
    parser.add_argument("--sample-size", type=int, default=None)
    parser.add_argument("--output-dir", default=str(ROOT))
    args = parser.parse_args()

    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    outcomes = [
        run_mmhc(file_path=args.file_path, sample_size=args.sample_size),
        run_h2pc(file_path=args.file_path, sample_size=args.sample_size),
        run_arges_like(file_path=args.file_path, sample_size=args.sample_size),
    ]

    summary = pd.DataFrame([outcome["result"] for outcome in outcomes])
    summary_path = output_dir / "results_summary.csv"
    summary.to_csv(summary_path, index=False)

    save_edges(outcomes[0]["edges"], output_dir / "mmhc_edges.csv")
    save_edges(outcomes[1]["edges"], output_dir / "h2pc_edges.csv")
    save_edges(outcomes[2]["edges"], output_dir / "arges_edges.csv")

    print(summary.to_string(index=False))
    print(f"\nSaved results to {summary_path}")


if __name__ == "__main__":
    main()
