# Bayesian Belief Network Project
# File-by-File Implementation Checklist

## Objective

Build a consistent experiment pipeline for comparing:

- `MMHC` from `bnlearn`
- `H2PC` from `bnlearn`
- an `ARGES-like (adaptive triples)` pipeline using `HPC` from `bnlearn` and adaptive restricted `GES` from `pcalg`

on the lung cancer dataset in this repository.

Official dataset:
- [`/Users/seong/Desktop/Programming/BBN/Recategorized_Cleaned_Lung_Cancer_dataset.csv`](/Users/seong/Desktop/Programming/BBN/Recategorized_Cleaned_Lung_Cancer_dataset.csv)

Target variable:
- `Cause of Death`

Core rules:
- every algorithm must use the exact same preprocessing, train/test split, and evaluation logic
- `MMHC` and `H2PC` must come from `bnlearn`
- the `ARGES-like (adaptive triples)` experiment must start from an `HPC` skeleton learned in `bnlearn`
- the adaptive score-based search step must use `pcalg::ges(..., adaptive = "triples")`

## Repository Checklist

### 1. Add shared preprocessing module

File to create:
- [`/Users/seong/Desktop/Programming/BBN/preprocessing.py`](/Users/seong/Desktop/Programming/BBN/preprocessing.py)

Checklist:
- [ ] Add `load_dataset(file_path)` to read the recategorized CSV
- [ ] Add `clean_dataset(df)` to fill missing `Cancer Cell Type` with `Unknown`
- [ ] Add logic to cast every column to categorical/string-safe format
- [ ] Add `encode_dataset(df)` to convert categories to integer codes consistently
- [ ] Add `split_dataset(df, test_size=0.2, random_state=42)` for a fixed train/test split
- [ ] Return category mappings or encoders if needed for reproducibility
- [ ] Keep preprocessing method identical for MMHC, H2PC, and ARGES-like adaptive triples

Definition of done:
- [ ] no missing values remain after preprocessing
- [ ] output is reproducible across runs
- [ ] all experiment scripts can import this file

### 2. Add shared evaluation module

File to create:
- [`/Users/seong/Desktop/Programming/BBN/evaluation.py`](/Users/seong/Desktop/Programming/BBN/evaluation.py)

Checklist:
- [ ] Add helper to measure structure-learning runtime
- [ ] Add helper to measure total runtime
- [ ] Add helper to count learned edges
- [ ] Add helper to compute BIC with one standard definition
- [ ] Add optional helper for prediction accuracy on `Cause of Death`
- [ ] Add helper to package results into one dictionary with standard keys
- [ ] Add optional SHD helper only if a reference graph is later provided

Standard output fields:
- [ ] `Algorithm`
- [ ] `Dataset`
- [ ] `Train Size`
- [ ] `Test Size`
- [ ] `BIC`
- [ ] `Structure Runtime (s)`
- [ ] `Total Runtime (s)`
- [ ] `Edge Count`
- [ ] `Prediction Accuracy`
- [ ] `Notes`

Definition of done:
- [ ] all algorithms produce the same result schema
- [ ] evaluation can be reused without method-specific edits

### 3. Refactor MMHC experiment

File to update:
- [`/Users/seong/Desktop/Programming/BBN/mmhc.py`](/Users/seong/Desktop/Programming/BBN/mmhc.py)

Checklist:
- [ ] Remove duplicated preprocessing logic from the script
- [ ] Import shared functions from [`/Users/seong/Desktop/Programming/BBN/preprocessing.py`](/Users/seong/Desktop/Programming/BBN/preprocessing.py)
- [ ] Import shared evaluation helpers from [`/Users/seong/Desktop/Programming/BBN/evaluation.py`](/Users/seong/Desktop/Programming/BBN/evaluation.py)
- [ ] Replace the current non-`bnlearn` MMHC path with a `bnlearn`-backed MMHC path
- [ ] Keep MMHC-specific logic limited to calling `bnlearn`, parsing learned edges, and BN construction
- [ ] Remove debug prints like `print("here")`
- [ ] Make result output match the standard schema
- [ ] Ensure the script can run as a standalone experiment entry point

Definition of done:
- [ ] MMHC runs end-to-end on the official dataset
- [ ] results can be merged directly into the shared summary table

### 4. Implement H2PC experiment

File to create:
- [`/Users/seong/Desktop/Programming/BBN/h2pc.py`](/Users/seong/Desktop/Programming/BBN/h2pc.py)

Checklist:
- [ ] Use the shared preprocessing pipeline
- [ ] Implement `H2PC` using `bnlearn`
- [ ] Parse the learned `bnlearn` structure into a standard edge list
- [ ] Build a Bayesian network from learned edges
- [ ] Fit the BN parameters on the train split
- [ ] Evaluate using the shared evaluation module
- [ ] Match the same return format used by MMHC and ARGES-like adaptive triples

Definition of done:
- [ ] H2PC runs on the same dataset and split as the other methods
- [ ] result row is directly comparable with MMHC and ARGES-like adaptive triples

### 5. Refactor ARGES-like adaptive experiment

File to update:
- [`/Users/seong/Desktop/Programming/BBN/arges.py`](/Users/seong/Desktop/Programming/BBN/arges.py)

Checklist:
- [ ] Remove duplicated preprocessing code
- [ ] Import the shared preprocessing module
- [ ] Import the shared evaluation module
- [ ] Replace the current `PC + GES` prototype with an `ARGES-like` adaptive restricted search
- [ ] Use the `bnlearn` `HPC` result as the phase-1 skeleton
- [ ] Convert the skeleton complement into `fixedGaps`
- [ ] Run `pcalg::ges(..., adaptive = "triples")` as the adaptive score-based refinement step
- [ ] Export both the learned CPDAG and one representative DAG for downstream BN fitting
- [ ] Document clearly that this repo implements an `ARGES-like (adaptive triples)` pipeline rather than a plain `HPC -> GES` handoff
- [ ] Keep cycle removal only if necessary and document why
- [ ] Standardize the output to match MMHC and H2PC

Definition of done:
- [ ] ARGES-like adaptive-triples pipeline is clearly defined
- [ ] output is directly comparable with the other methods

### 6. Add bnlearn integration layer

File to create:
- [`/Users/seong/Desktop/Programming/BBN/bnlearn_adapter.py`](/Users/seong/Desktop/Programming/BBN/bnlearn_adapter.py)

Checklist:
- [ ] Add one adapter function for `MMHC`
- [ ] Add one adapter function for `H2PC`
- [ ] Standardize the returned edge-list format for both methods
- [ ] Keep all `bnlearn`-specific calling and parsing logic in this file
- [ ] Make the rest of the repo independent of `bnlearn` call details

Definition of done:
- [ ] `mmhc.py`, `h2pc.py`, and `arges.py` can all reuse the same `bnlearn` adapter
- [ ] changes to `bnlearn` invocation only need to be made in one place

### 7. Add experiment runner

File to create:
- [`/Users/seong/Desktop/Programming/BBN/run_experiments.py`](/Users/seong/Desktop/Programming/BBN/run_experiments.py)

Checklist:
- [ ] Run MMHC
- [ ] Run H2PC
- [ ] Run ARGES-like adaptive triples
- [ ] Collect each method's result dictionary
- [ ] Combine them into one table
- [ ] Save a summary CSV
- [ ] Print a compact console summary

Output files:
- [ ] [`/Users/seong/Desktop/Programming/BBN/results_summary.csv`](/Users/seong/Desktop/Programming/BBN/results_summary.csv)
- [ ] optional learned-edge files for each method

Definition of done:
- [ ] one command runs the full comparison pipeline
- [ ] all results are saved in a report-ready format

### 8. Save learned structures

Files to create during runs:
- [`/Users/seong/Desktop/Programming/BBN/mmhc_edges.csv`](/Users/seong/Desktop/Programming/BBN/mmhc_edges.csv)
- [`/Users/seong/Desktop/Programming/BBN/h2pc_edges.csv`](/Users/seong/Desktop/Programming/BBN/h2pc_edges.csv)
- [`/Users/seong/Desktop/Programming/BBN/arges_edges.csv`](/Users/seong/Desktop/Programming/BBN/arges_edges.csv)

Checklist:
- [ ] Save parent-child edge list for each algorithm
- [ ] Use one consistent CSV schema such as `source,target`
- [ ] Save edge counts in the summary table

Definition of done:
- [ ] learned graphs can be inspected and compared independently of the scripts

### 9. Add results analysis notebook or script

File to create:
- [`/Users/seong/Desktop/Programming/BBN/analyze_results.py`](/Users/seong/Desktop/Programming/BBN/analyze_results.py)

Checklist:
- [ ] Read `results_summary.csv`
- [ ] Produce a compact comparison table
- [ ] Generate simple plots for runtime and BIC
- [ ] Optionally summarize edge counts and accuracy
- [ ] Export plots for poster/report use

Suggested outputs:
- [ ] `bic_comparison.png`
- [ ] `runtime_comparison.png`
- [ ] `results_table.png` or a markdown table for the report

Definition of done:
- [ ] outputs are ready to drop into the poster and internal report

### 10. Write short methods/results summary

File to create:
- [`/Users/seong/Desktop/Programming/BBN/internal_report.md`](/Users/seong/Desktop/Programming/BBN/internal_report.md)

Checklist:
- [ ] Describe dataset choice
- [ ] Describe preprocessing
- [ ] Describe each algorithm briefly
- [ ] Present the result table
- [ ] Interpret BIC, runtime, and graph-size differences
- [ ] State that the ARGES-like path uses `adaptive = "triples"` in `pcalg`
- [ ] Note limitations such as missing SHD reference graph if applicable

Definition of done:
- [ ] a teammate can understand the full experiment without reading the source code

## Suggested Work Order

### Day 1
- [ ] Create `preprocessing.py`
- [ ] Create `evaluation.py`
- [ ] Create `bnlearn_adapter.py`
- [ ] Refactor `mmhc.py`

### Day 2
- [ ] Implement `h2pc.py`
- [ ] Refactor `arges.py`
- [ ] Run smoke tests for all methods

### Day 3
- [ ] Run full experiments
- [ ] Save `results_summary.csv`
- [ ] Save learned edge lists
- [ ] Generate plots and report content

## Team Split Suggestion

- Shared pipeline owner:
  [`/Users/seong/Desktop/Programming/BBN/preprocessing.py`](/Users/seong/Desktop/Programming/BBN/preprocessing.py),
  [`/Users/seong/Desktop/Programming/BBN/evaluation.py`](/Users/seong/Desktop/Programming/BBN/evaluation.py),
  [`/Users/seong/Desktop/Programming/BBN/bnlearn_adapter.py`](/Users/seong/Desktop/Programming/BBN/bnlearn_adapter.py),
  [`/Users/seong/Desktop/Programming/BBN/run_experiments.py`](/Users/seong/Desktop/Programming/BBN/run_experiments.py)

- MMHC owner:
  [`/Users/seong/Desktop/Programming/BBN/mmhc.py`](/Users/seong/Desktop/Programming/BBN/mmhc.py)

- H2PC owner:
  [`/Users/seong/Desktop/Programming/BBN/h2pc.py`](/Users/seong/Desktop/Programming/BBN/h2pc.py)

- ARGES-like owner:
  [`/Users/seong/Desktop/Programming/BBN/arges.py`](/Users/seong/Desktop/Programming/BBN/arges.py)

- Analysis/report owner:
  [`/Users/seong/Desktop/Programming/BBN/analyze_results.py`](/Users/seong/Desktop/Programming/BBN/analyze_results.py),
  [`/Users/seong/Desktop/Programming/BBN/internal_report.md`](/Users/seong/Desktop/Programming/BBN/internal_report.md)

## Final Success Criteria

- [ ] all three algorithms run on the same preprocessed dataset
- [ ] all three produce standardized outputs
- [ ] results are collected in one summary file
- [ ] plots/tables are ready for the poster
- [ ] methods and limitations are documented clearly
