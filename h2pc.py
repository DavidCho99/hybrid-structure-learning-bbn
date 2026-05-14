from __future__ import annotations

import argparse
import time

from bnlearn_adapter import learn_h2pc_edges
from evaluation import (
    build_bayesian_network,
    compute_bic_score,
    compute_prediction_metrics,
    fit_bayesian_network,
    summarize_result,
)
from preprocessing import DEFAULT_DATASET_PATH, TARGET_COLUMN, prepare_data


def run_h2pc(file_path: str = str(DEFAULT_DATASET_PATH), sample_size: int | None = None) -> dict[str, object]:
    total_start = time.time()
    prepared = prepare_data(file_path=file_path, sample_size=sample_size)

    structure_start = time.time()
    edges = learn_h2pc_edges(prepared.train_df)
    structure_runtime = time.time() - structure_start

    model = build_bayesian_network(edges=edges, nodes=prepared.train_df.columns)
    model = fit_bayesian_network(model, prepared.train_df)

    bic_score = compute_bic_score(model, prepared.train_df)
    metrics = compute_prediction_metrics(model, prepared.test_df, TARGET_COLUMN)
    total_runtime = time.time() - total_start

    notes = "BIC computed on train split."
    failed_queries = int(metrics.get("Failed Queries") or 0)
    if failed_queries:
        notes = f"{notes} Prediction queries failed for {failed_queries} rows."

    result = summarize_result(
        algorithm="H2PC (bnlearn)",
        dataset=prepared.dataset_path.name,
        train_df=prepared.train_df,
        test_df=prepared.test_df,
        bic_score=bic_score,
        structure_runtime=structure_runtime,
        total_runtime=total_runtime,
        edge_count=len(edges),
        prediction_accuracy=metrics.get("Prediction Accuracy"),
        balanced_accuracy=metrics.get("Balanced Accuracy"),
        macro_f1=metrics.get("Macro F1"),
        auc=metrics.get("AUC"),
        log_loss_value=metrics.get("Log Loss"),
        brier_score=metrics.get("Brier Score"),
        inference_success_rate=metrics.get("Inference Success Rate"),
        failed_queries=metrics.get("Failed Queries"),
        notes=notes,
    )

    return {
        "model": model,
        "edges": edges,
        "result": result,
        "prepared": prepared,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run H2PC with bnlearn.")
    parser.add_argument("--file-path", default=str(DEFAULT_DATASET_PATH))
    parser.add_argument("--sample-size", type=int, default=None)
    args = parser.parse_args()

    outcome = run_h2pc(file_path=args.file_path, sample_size=args.sample_size)
    print(outcome["result"])


if __name__ == "__main__":
    main()
