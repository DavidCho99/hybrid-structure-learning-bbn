from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parent
R_DRIVER_PATH = ROOT / "r_bnlearn_driver.R"
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

    raise RuntimeError(
        "Rscript is not installed or not on PATH. Install R and the bnlearn package first."
    )


def _read_edges(edge_csv_path: Path) -> list[tuple[str, str]]:
    if edge_csv_path.stat().st_size == 0:
        return []

    edges_df = pd.read_csv(edge_csv_path)
    if edges_df.empty:
        return []

    if not {"from", "to"}.issubset(edges_df.columns):
        raise RuntimeError(f"Unexpected bnlearn edge format: {edges_df.columns.tolist()}")

    return [(str(row["from"]), str(row["to"])) for _, row in edges_df.iterrows()]


def run_bnlearn_structure(train_df: pd.DataFrame, method: str) -> list[tuple[str, str]]:
    rscript_path = _require_rscript()

    with tempfile.TemporaryDirectory(prefix="bbn_bnlearn_") as temp_dir_name:
        temp_dir = Path(temp_dir_name)
        input_path = temp_dir / "train_data.csv"
        output_path = temp_dir / "edges.csv"
        train_df.to_csv(input_path, index=False)

        result = subprocess.run(
            [rscript_path, str(R_DRIVER_PATH), str(input_path), method, str(output_path)],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            stderr = result.stderr.strip() or "No stderr captured."
            raise RuntimeError(f"bnlearn {method} failed: {stderr}")

        return _read_edges(output_path)


def learn_mmhc_edges(train_df: pd.DataFrame) -> list[tuple[str, str]]:
    return run_bnlearn_structure(train_df=train_df, method="mmhc")


def learn_h2pc_edges(train_df: pd.DataFrame) -> list[tuple[str, str]]:
    return run_bnlearn_structure(train_df=train_df, method="h2pc")


def learn_hpc_edges(train_df: pd.DataFrame) -> list[tuple[str, str]]:
    return run_bnlearn_structure(train_df=train_df, method="hpc")
