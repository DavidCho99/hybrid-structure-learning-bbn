# BBN Source Code Organization

BBN is an experiment workspace for comparing hybrid Bayesian Belief Network
structure-learning methods on a recategorized lung cancer dataset. The project
keeps data preparation, R-backed structure learning, Bayesian-network fitting,
evaluation, and reporting in separate files so that each algorithm is compared
under the same experimental protocol.

The main comparison currently covers:

- `MMHC` from `bnlearn`
- `H2PC` from `bnlearn`
- `ARGES-like (adaptive triples)` using an `HPC` restriction graph from
  `bnlearn` and adaptive restricted `GES` from `pcalg`

## Layers

The repository is organized as a small layered pipeline:

- **Data layer**: stores the recategorized lung cancer dataset and generated
  experiment artifacts.
- **Preprocessing layer**: provides one canonical cleaning, encoding, and
  train/test split path shared by every method.
- **R bridge layer**: isolates calls into `bnlearn` and `pcalg`, then converts
  learned structures into Python-readable edge lists.
- **Algorithm layer**: keeps one Python entry point per structure-learning
  method.
- **Evaluation layer**: builds and fits Bayesian networks, computes scores and
  predictive metrics, and standardizes result rows.
- **Orchestration layer**: runs all methods, saves summary tables, exports edge
  lists, and supports repeated validation runs.
- **Presentation/API layer**: renders report-ready visuals and exposes a local
  HTTP API for running experiments.

## Target Environments

The project uses both Python and R.

- **Python**: shared preprocessing, experiment orchestration, Bayesian-network
  fitting, scoring, prediction metrics, image rendering, and the local API.
- **R**: structure learning through `bnlearn` and `pcalg`.
- **Generated artifacts**: CSV summaries, learned-edge files, PNG tables, and
  Markdown report/poster drafts.

Environment-specific rule:

- Python modules should not duplicate preprocessing logic.
- R-specific package calls should stay in the R driver files or the Python
  adapter that invokes them.
- New evaluation metrics should be added to `evaluation.py`, not repeated in
  individual algorithm scripts.

## Experiment Pipeline

The full experiment flow is:

1. `preprocessing.py` loads `Recategorized_Cleaned_Lung_Cancer_dataset.csv`.
2. Missing `Cancer Cell Type` values are filled with `Unknown`.
3. All columns are treated as categorical values.
4. Data is encoded consistently and split into train/test sets with a fixed
   random seed.
5. `mmhc.py`, `h2pc.py`, and `arges.py` learn candidate structures.
6. `evaluation.py` builds a `pgmpy` Bayesian network, fits parameters, and
   computes BIC, runtime, edge count, and predictive metrics.
7. `run_experiments.py` writes `results_summary.csv` and one edge-list CSV per
   method.
8. `make_head_to_head_results.py` can render a report-ready comparison table.

All methods should use the same dataset, preprocessing function, train/test
split, and result schema.

## Repository Map

```text
.
├── README.md
├── preprocessing.py              # canonical dataset loading, cleaning, encoding, split
├── evaluation.py                 # BN construction, fitting, scoring, metrics
├── bnlearn_adapter.py            # Python wrapper around the bnlearn R driver
├── r_bnlearn_driver.R            # MMHC, H2PC, and HPC calls through bnlearn
├── r_arges_driver.R              # ARGES-like adaptive restricted GES through pcalg
├── mmhc.py                       # MMHC experiment entry point
├── h2pc.py                       # H2PC experiment entry point
├── arges.py                      # ARGES-like adaptive triples entry point
├── run_experiments.py            # runs all three methods and saves summaries
├── validate_experiments.py       # repeated validation runs and aggregate metrics
├── make_head_to_head_results.py  # renders a PNG comparison table
├── bbn_api.py                    # local HTTP API for async experiment jobs
├── results_summary.csv           # latest summary table
├── mmhc_edges.csv                # latest MMHC learned edge list
├── h2pc_edges.csv                # latest H2PC learned edge list
├── arges_edges.csv               # latest ARGES-like learned edge list
├── head_to_head_results.png      # rendered result table
└── *.md                          # project notes, poster drafts, and discussion summaries
```

Local-only folders such as `venv/`, `r_libs/`, and `__pycache__/` are not part
of the source layout and should not be uploaded.

## Core Files

### `preprocessing.py`

Defines the shared preprocessing contract:

- default dataset path
- target column: `Cause of Death`
- missing-value handling
- category mapping
- categorical integer encoding
- fixed train/test split
- `PreparedData` container used by the experiment scripts

### `bnlearn_adapter.py` and `r_bnlearn_driver.R`

Provide the bridge between Python and `bnlearn`.

Python writes the train split to a temporary CSV, calls `Rscript`, and reads the
learned edge list back into a standard `list[tuple[str, str]]` format.

Supported `bnlearn` methods:

- `mmhc`
- `h2pc`
- `hpc`

### `arges.py` and `r_arges_driver.R`

Run the ARGES-like path:

- learn an `HPC` skeleton with `bnlearn`
- convert the skeleton complement into `fixedGaps`
- run `pcalg::ges(..., adaptive = "triples")`
- export the CPDAG, representative DAG, and skeleton edge lists

This project intentionally labels the method as `ARGES-like (adaptive triples)`
rather than claiming a strict reproduction of every ARGES variant.

### `evaluation.py`

Centralizes evaluation behavior:

- duplicate-edge normalization
- DAG validation
- Bayesian-network construction with `pgmpy`
- parameter fitting with Bayesian estimation and MLE fallback
- BIC scoring
- prediction metrics for `Cause of Death`
- standard result-row formatting

### `run_experiments.py`

Runs all three algorithms using the same input data and writes:

- `results_summary.csv`
- `mmhc_edges.csv`
- `h2pc_edges.csv`
- `arges_edges.csv`

## Setup

Create and activate a Python environment:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Install the required R packages:

```bash
Rscript -e "install.packages('bnlearn', repos='https://cloud.r-project.org')"
Rscript -e "install.packages('BiocManager', repos='https://cloud.r-project.org'); BiocManager::install('pcalg')"
```

If R packages are installed into a project-local library, set `R_LIBS_USER` to
that folder before running experiments.

## Running Experiments

Run the full comparison on the default dataset:

```bash
python run_experiments.py
```

Run a smaller smoke test:

```bash
python run_experiments.py --sample-size 5000 --output-dir runs/smoke
```

Render the head-to-head result table:

```bash
python make_head_to_head_results.py \
  --summary-csv results_summary.csv \
  --output head_to_head_results.png
```

Run repeated validation:

```bash
python validate_experiments.py --repeats 5 --output-dir runs/validation
```

## Local API

Start the API server:

```bash
python bbn_api.py --host 127.0.0.1 --port 8000
```

Useful endpoints:

- `GET /health`
- `POST /run`
- `GET /jobs/<job_id>`
- `GET /jobs/<job_id>/summary`
- `GET /jobs/<job_id>/results_summary.csv`
- `GET /jobs/<job_id>/head_to_head.png`

Example request:

```bash
curl -X POST http://127.0.0.1:8000/run \
  -H "Content-Type: application/json" \
  -d '{"sample_size": 5000}'
```

## Current Result Snapshot

The latest saved summary compares all three methods on the recategorized lung
cancer dataset.

| Method | BIC | Total Runtime (s) | Edge Count | Prediction Accuracy |
|---|---:|---:|---:|---:|
| MMHC | -1,528,163.0048 | 16.9972 | 7 | 0.7044 |
| H2PC | -1,380,635.0229 | 23.9098 | 25 | 0.7226 |
| ARGES-like | -1,703,922.1521 | 21.4393 | 0 | 0.5595 |

In this run, `H2PC` produced the best BIC and prediction accuracy, while `MMHC`
was the fastest method. The ARGES-like run produced an empty final graph under
the current categorical-data setup.

## Upload Notes

Before uploading the repository:

- Keep source files, result summaries, report drafts, and presentation-ready
  images if they are needed for the project submission.
- Do not upload `venv/`, `r_libs/`, `__pycache__/`, `.DS_Store`, or temporary
  run folders.
- Include the dataset only if its license, class policy, and privacy rules allow
  redistribution. Otherwise, keep the CSV outside the repository and pass it
  with `--file-path`.
- Re-run `python run_experiments.py` after any change to preprocessing,
  algorithm logic, or evaluation metrics.

## Contribution Rules

When adding new code:

- Shared data-cleaning changes belong in `preprocessing.py`.
- Shared scoring or metric changes belong in `evaluation.py`.
- New R method calls should be isolated behind a small Python adapter and an R
  driver script.
- New algorithms should expose a `run_<method>()` function and return the same
  result structure used by `mmhc.py`, `h2pc.py`, and `arges.py`.
- Generated experiment outputs should use clear names and should not overwrite
  source files.
