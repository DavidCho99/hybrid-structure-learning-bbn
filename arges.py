from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

from evaluation import (
    build_bayesian_network,
    compute_bic_score,
    compute_prediction_metrics,
    fit_bayesian_network,
    summarize_result,
)
from preprocessing import DEFAULT_DATASET_PATH, TARGET_COLUMN, prepare_data

ROOT = Path(__file__).resolve().parent
R_ARGES_DRIVER_PATH = ROOT / "r_arges_driver.R"
LOCAL_R_LIBS_PATH = ROOT / "r_libs"
FALLBACK_RSCRIPT_PATHS = [
    Path("/opt/anaconda3/bin/Rscript"),
]

def _require_rscript() -> str:
    rscript_path = shutil.which("Rscript")
    if rscript_path is not None:
        return rscript_path

    for candidate in FALLBACK_RSCRIPT_PATHS:
        if candidate.exists():
            return str(candidate)

    raise RuntimeError("Rscript is not installed or not on PATH.")


def _read_edge_csv(path: Path) -> list[tuple[str, str]]:
    import pandas as pd

    if not path.exists() or path.stat().st_size == 0:
        return []

    df = pd.read_csv(path)
    if df.empty:
        return []

    if not {"source", "target"}.issubset(df.columns):
        raise RuntimeError(f"Unexpected ARGES edge format: {df.columns.tolist()}")

    return [(str(row["source"]), str(row["target"])) for _, row in df.iterrows()]


def run_true_arges(train_df) -> tuple[list[tuple[str, str]], list[tuple[str, str]], list[tuple[str, str]]]:
    rscript_path = _require_rscript()

    with tempfile.TemporaryDirectory(prefix="bbn_arges_") as temp_dir_name:
        temp_dir = Path(temp_dir_name)
        input_path = temp_dir / "train_data.csv"
        cpdag_path = temp_dir / "cpdag_edges.csv"
        repr_path = temp_dir / "repr_edges.csv"
        skeleton_path = temp_dir / "skeleton_edges.csv"
        train_df.to_csv(input_path, index=False)

        result = subprocess.run(
            [rscript_path, str(R_ARGES_DRIVER_PATH), str(input_path), str(cpdag_path), str(repr_path), str(skeleton_path)],
            capture_output=True,
            text=True,
            check=False,
            env={
                **os.environ,
                "R_LIBS_USER": str(LOCAL_R_LIBS_PATH),
            },
        )
        if result.returncode != 0:
            stderr = result.stderr.strip() or "No stderr captured."
            raise RuntimeError(f"ARGES driver failed: {stderr}")

        cpdag_edges = _read_edge_csv(cpdag_path)
        repr_edges = _read_edge_csv(repr_path)
        skeleton_edges = _read_edge_csv(skeleton_path)
        return cpdag_edges, repr_edges, skeleton_edges


def run_arges_like(file_path: str = str(DEFAULT_DATASET_PATH), sample_size: int | None = None) -> dict[str, object]:
    total_start = time.time()
    prepared = prepare_data(file_path=file_path, sample_size=sample_size)
    columns = prepared.train_df.columns.tolist()

    structure_start = time.time()
    cpdag_edges, repr_edges, hpc_skeleton_edges = run_true_arges(prepared.train_df)
    structure_runtime = time.time() - structure_start

    model = build_bayesian_network(edges=repr_edges, nodes=columns)
    model = fit_bayesian_network(model, prepared.train_df)

    bic_score = compute_bic_score(model, prepared.train_df)
    metrics = compute_prediction_metrics(model, prepared.test_df, TARGET_COLUMN)
    total_runtime = time.time() - total_start

    notes = "Adaptive restricted GES ran in pcalg with fixedGaps from an HPC skeleton and adaptive='triples'. BIC computed on train split."
    failed_queries = int(metrics.get("Failed Queries") or 0)
    if failed_queries:
        notes = f"{notes} Prediction queries failed for {failed_queries} rows."

    result = summarize_result(
        algorithm="ARGES-like (adaptive triples)",
        dataset=prepared.dataset_path.name,
        train_df=prepared.train_df,
        test_df=prepared.test_df,
        bic_score=bic_score,
        structure_runtime=structure_runtime,
        total_runtime=total_runtime,
        edge_count=len(repr_edges),
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
        "edges": repr_edges,
        "cpdag_edges": cpdag_edges,
        "phase1_edges": hpc_skeleton_edges,
        "result": result,
        "prepared": prepared,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run ARGES-like adaptive restricted GES with adaptive='triples'.")
    parser.add_argument("--file-path", default=str(DEFAULT_DATASET_PATH))
    parser.add_argument("--sample-size", type=int, default=None)
    args = parser.parse_args()

    outcome = run_arges_like(file_path=args.file_path, sample_size=args.sample_size)
    print(outcome["result"])


def run_arges_style(file_path: str = str(DEFAULT_DATASET_PATH), sample_size: int | None = None) -> dict[str, object]:
    return run_arges_like(file_path=file_path, sample_size=sample_size)


if __name__ == "__main__":
    main()
