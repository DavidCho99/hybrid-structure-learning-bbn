# BBN Hybrid Learner

BBN Hybrid Learner compares hybrid Bayesian Belief Network structure-learning
methods on a recategorized lung cancer dataset. The repository is organized so
that source code, R drivers, data, saved results, and project writeups each live
in their own folder.

The current comparison includes:

- `MMHC` from `bnlearn`
- `H2PC` from `bnlearn`
- `ARGES-like (adaptive triples)` using an `HPC` restriction graph from
  `bnlearn` and adaptive restricted `GES` from `pcalg`

## Project Summary

This project asks which hybrid structure-learning algorithm provides the best
balance of model fit, computational efficiency, structural interpretability,
and predictive performance for a large-scale categorical lung cancer dataset.

The working dataset contains `191,993` records and `11` categorical variables.
The target variable is `Cause of Death`, and all methods use the same `80/20`
train/test split.

The poster analysis found that `H2PC` performed best overall. It produced the
strongest model fit, the highest prediction accuracy, and a richer learned
network than `MMHC`. `MMHC` was faster, but it produced a sparse graph.
`ARGES-like` did not learn meaningful dependencies in the current categorical
setting, suggesting that this pipeline may be better suited to continuous or
differently encoded data.

The broader goal is to improve the reliability of interpretable Bayesian
network models for clinical decision support in lung cancer analysis.

## Folder Layout

```text
.
├── README.md
├── requirements.txt
├── bbn_hybrid_learner/
│   ├── __init__.py
│   ├── preprocessing.py
│   ├── evaluation.py
│   ├── bnlearn_adapter.py
│   ├── mmhc.py
│   ├── h2pc.py
│   ├── arges.py
│   ├── run_experiments.py
│   ├── validate_experiments.py
│   ├── make_head_to_head_results.py
│   └── bbn_api.py
├── data/
│   └── Recategorized_Cleaned_Lung_Cancer_dataset.csv
├── r/
│   ├── r_bnlearn_driver.R
│   └── r_arges_driver.R
├── results/
│   ├── results_summary.csv
│   ├── edges/
│   │   ├── mmhc_edges.csv
│   │   ├── h2pc_edges.csv
│   │   └── arges_edges.csv
│   └── figures/
│       └── head_to_head_results.png
└── docs/
    ├── discussion_summary_paper.md
    ├── implementation_checklist.md
    ├── poster_content_from_results.md
    └── poster_draft.md
```

Local-only folders such as `venv/`, `r_libs/`, and `__pycache__/` are ignored
and should not be uploaded.

## Layers

- **Data layer**: `data/` contains the working dataset.
- **Python package layer**: `bbn_hybrid_learner/` contains preprocessing,
  algorithm runners, evaluation logic, visualization, and the local API.
- **R bridge layer**: `r/` contains the R scripts that call `bnlearn` and
  `pcalg`.
- **Results layer**: `results/` contains generated CSV summaries, edge lists,
  and rendered figures.
- **Documentation layer**: `docs/` contains planning notes, poster drafts, and
  writeups.

## Pipeline

1. `bbn_hybrid_learner/preprocessing.py` loads the dataset from `data/`.
2. Missing `Cancer Cell Type` values are filled with `Unknown`.
3. All variables are treated as categorical.
4. A fixed train/test split is shared by every method.
5. `mmhc.py`, `h2pc.py`, and `arges.py` learn candidate structures.
6. `evaluation.py` builds and fits `pgmpy` Bayesian networks.
7. `run_experiments.py` saves the summary table and learned edges under
   `results/`.
8. `make_head_to_head_results.py` renders a PNG comparison table.

## Core Modules

### `bbn_hybrid_learner/preprocessing.py`

Defines the shared dataset path, target column, missing-value handling,
categorical encoding, and train/test split.

### `bbn_hybrid_learner/evaluation.py`

Builds Bayesian networks, validates DAGs, fits parameters, computes BIC, and
reports prediction metrics for `Cause of Death`.

### `bbn_hybrid_learner/bnlearn_adapter.py`

Writes Python data frames to temporary CSV files, calls `Rscript`, and returns
learned structures as Python edge lists.

### `bbn_hybrid_learner/mmhc.py`, `h2pc.py`, and `arges.py`

Each file owns one structure-learning method and returns the same result schema
so the methods can be compared directly.

### `r/`

Contains the R-only structure-learning calls:

- `r_bnlearn_driver.R`: `mmhc`, `h2pc`, and `hpc`
- `r_arges_driver.R`: adaptive restricted `GES` with `adaptive = "triples"`

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

Run the full comparison:

```bash
python -m bbn_hybrid_learner.run_experiments
```

Run a smaller smoke test:

```bash
python -m bbn_hybrid_learner.run_experiments \
  --sample-size 5000 \
  --output-dir results/smoke
```

Render the head-to-head result table:

```bash
python -m bbn_hybrid_learner.make_head_to_head_results
```

Run repeated validation:

```bash
python -m bbn_hybrid_learner.validate_experiments \
  --repeats 5 \
  --output-dir results/validation
```

## Local API

Start the API server:

```bash
python -m bbn_hybrid_learner.bbn_api --host 127.0.0.1 --port 8000
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

The latest saved summary is in `results/results_summary.csv`.

| Method | BIC | Total Runtime (s) | Edge Count | Prediction Accuracy | AUC |
|---|---:|---:|---:|---:|---:|
| MMHC | -1,528,163.0048 | 16.9972 | 7 | 0.7044 | 0.7047 |
| H2PC | -1,380,635.0229 | 23.9098 | 25 | 0.7226 | 0.7922 |
| ARGES-like | -1,703,922.1521 | 21.4393 | 0 | 0.5595 | 0.5000 |

In this run, `H2PC` produced the best BIC and prediction accuracy, while `MMHC`
was the fastest method. The ARGES-like run produced an empty final graph under
the current categorical-data setup.

## Follow-Up Research

The next research step is to use the same lung cancer dataset with additional
machine-learning models and compare those results against the Bayesian network
methods in this repository.

The follow-up comparison should keep the same preprocessing, target variable,
and train/test split, then evaluate models such as logistic regression, random
forest, gradient boosting or XGBoost, support vector machines, and neural
network classifiers.

The purpose of this follow-up work is to compare:

- predictive performance, using accuracy, balanced accuracy, macro F1, AUC, and
  log loss
- runtime and scalability on the same large categorical dataset
- interpretability, especially BBN graph structure versus feature-importance or
  black-box model explanations
- clinical usefulness for understanding lung cancer progression and treatment
  outcomes

This would turn the project from a comparison of hybrid Bayesian network
structure learners into a broader study of interpretable probabilistic models
versus standard machine-learning baselines on the same medical dataset.

## Upload Notes

- Keep source files, result summaries, report drafts, and presentation-ready
  images if they are needed for submission.
- Do not upload `venv/`, `r_libs/`, `__pycache__/`, `.DS_Store`, or temporary
  run folders.
- Include the dataset only if its license, class policy, and privacy rules allow
  redistribution. Otherwise, keep the CSV outside the repository and pass it
  with `--file-path`.
- Re-run `python -m bbn_hybrid_learner.run_experiments` after changes to
  preprocessing, algorithm logic, or evaluation metrics.

## Contribution Rules

- Shared data-cleaning changes belong in `bbn_hybrid_learner/preprocessing.py`.
- Shared scoring or metric changes belong in `bbn_hybrid_learner/evaluation.py`.
- New R method calls should stay behind a Python adapter and an R driver script.
- New algorithms should expose a `run_<method>()` function and return the same
  result structure used by the current method files.
- Generated experiment outputs should go under `results/`.

## Poster PDF

The final project poster is available here:

[Gwangseong Cho - TRUE Poster](docs/gwangseong-cho-true-poster.pdf)
