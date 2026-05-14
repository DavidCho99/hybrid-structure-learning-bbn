# Bayesian Belief Network Hybrid Structure Learning:
# Project Discussion Summary and Experimental Planning Note

## Abstract

This paper summarizes the project discussion around hybrid structure learning for Bayesian Belief Networks (BBNs), with a focus on comparing three specific experiment paths: MMHC from `bnlearn`, H2PC from `bnlearn`, and an `ARGES-like (adaptive triples)` pipeline that uses `HPC` from `bnlearn` to define the initial restriction and `pcalg::ges(..., adaptive = "triples")` for adaptive score-based search. The conversation began with a task breakdown for data preparation, MMHC implementation, H2PC setup, ARGES setup, poster preparation, and result analysis. A review of the current workspace showed that prototype scripts for MMHC and ARGES already exist, but the experimental pipeline is not yet standardized across methods and does not yet fully reflect the intended library choices. The main concern identified was inconsistent preprocessing, which would make direct comparison unreliable. The discussion then shifted to the possible use of the UCI Heart Disease dataset, followed by a return to the currently available lung cancer dataset. Based on the current data and scripts, this note recommends using the recategorized lung cancer dataset for the weekend experiments because it is already discretized and much closer to the input format required by structure-learning methods.

## 1. Project Context

The project goal is to compare hybrid structure-learning approaches for Bayesian Belief Networks. The initial task outline included the following components:

- data cleaning and discretization
- MMHC implementation and evaluation
- H2PC implementation and evaluation
- ARGES implementation and evaluation
- poster and infographic preparation
- result analysis and short report writing

At the time of discussion, MMHC was assigned to Gwangseong Cho, while the remaining roles had not yet been assigned.

## 2. Current Workspace Status

Inspection of the project workspace showed the following relevant files:

- [`/Users/seong/Desktop/Programming/BBN/mmhc.py`](/Users/seong/Desktop/Programming/BBN/mmhc.py)
- [`/Users/seong/Desktop/Programming/BBN/arges.py`](/Users/seong/Desktop/Programming/BBN/arges.py)
- [`/Users/seong/Desktop/Programming/BBN/Cleaned_Lung_Cancer_dataset.csv`](/Users/seong/Desktop/Programming/BBN/Cleaned_Lung_Cancer_dataset.csv)
- [`/Users/seong/Desktop/Programming/BBN/Recategorized_Cleaned_Lung_Cancer_dataset.csv`](/Users/seong/Desktop/Programming/BBN/Recategorized_Cleaned_Lung_Cancer_dataset.csv)

The inspection suggested the following:

- the current MMHC prototype does not yet reflect the intended `bnlearn`-based implementation
- the current ARGES prototype originally looked closer to a `PC + GES` workflow than the intended adaptive restricted design
- H2PC does not yet appear to have a dedicated experiment script
- preprocessing is inconsistent between the current scripts

This inconsistency is the main barrier to fair comparison across algorithms.

## 3. Initial Methodological Concern: Inconsistent Preprocessing

The conversation identified preprocessing inconsistency as the most immediate issue. In the current codebase:

- one script keeps variables as categorical strings
- another script label-encodes all columns
- missing-value handling differs across scripts
- discretization is not standardized

Because BIC, runtime, and structural outputs are all sensitive to representation choices, inconsistent preprocessing would weaken any comparison between MMHC, H2PC, and the ARGES-like adaptive method.

The discussion therefore emphasized that all algorithms should share:

- the same dataset
- the same preprocessing function
- the same train/test split
- the same evaluation conventions

## 4. Consideration of the UCI Heart Disease Dataset

The UCI Heart Disease dataset was proposed as a possible alternative. The discussion clarified several facts:

- the UCI Heart Disease collection contains 4 source databases: Cleveland, Hungary, Switzerland, and VA Long Beach
- the standard benchmark most commonly used in published work is the Cleveland subset
- the standard Cleveland benchmark contains 303 patients
- all four source databases together are often described as having roughly 920 total patient records

This option was attractive because it is smaller and better standardized. However, the current workspace already contains a much larger lung cancer dataset that is closer to being experiment-ready.

## 5. Characteristics of the Current Lung Cancer Dataset

The existing dataset in the workspace was compared against the UCI Heart Disease benchmark.

### 5.1 Raw cleaned dataset

[`/Users/seong/Desktop/Programming/BBN/Cleaned_Lung_Cancer_dataset.csv`](/Users/seong/Desktop/Programming/BBN/Cleaned_Lung_Cancer_dataset.csv)

- 193,219 rows
- 11 columns
- no missing values in most fields
- 54,113 missing values in `Days from Diagnosis to Treatment`
- `Days from Diagnosis to Treatment` contains 519 unique values

### 5.2 Recategorized dataset

[`/Users/seong/Desktop/Programming/BBN/Recategorized_Cleaned_Lung_Cancer_dataset.csv`](/Users/seong/Desktop/Programming/BBN/Recategorized_Cleaned_Lung_Cancer_dataset.csv)

- 191,993 rows
- 11 columns
- `Cancer Cell Type` contains 20,128 missing values
- most columns are already grouped into a small number of clinically interpretable categories
- `Cause of Death` is already binary
- `Days from Diagnosis to Treatment` is already discretized into a few bins

The discussion established that the recategorized dataset is much better suited to weekend structure-learning experiments.

## 6. Recommended Preprocessing for the Lung Cancer Dataset

Based on inspection of the current files, the recommended preprocessing plan for the lung cancer experiments is as follows.

### 6.1 Dataset choice

Use [`/Users/seong/Desktop/Programming/BBN/Recategorized_Cleaned_Lung_Cancer_dataset.csv`](/Users/seong/Desktop/Programming/BBN/Recategorized_Cleaned_Lung_Cancer_dataset.csv) as the official experiment dataset.

This choice avoids unnecessary re-discretization work and creates a more level comparison across methods.

### 6.2 Missing-value handling

Only one major missing-value issue remains in the recategorized file:

- fill missing `Cancer Cell Type` with `Unknown`

No additional imputation should be introduced unless later inspection reveals hidden formatting issues.

### 6.3 Variable treatment

Treat all columns as categorical variables. In particular:

- keep grouped category labels as they are
- do not re-bin variables that are already recategorized
- keep `Cause of Death` as the target variable

### 6.4 Encoding strategy

For methods that require numerical input:

- convert categories to integer codes only after preprocessing is complete
- use one shared encoding pipeline for all algorithms
- ensure that train/test encoding is consistent

### 6.5 Data split

Use one fixed split across all experiments, for example:

- `train_test_split(..., test_size=0.2, random_state=42)`

This makes runtime and score comparisons reproducible.

## 7. Implications for MMHC, H2PC, and ARGES-like Adaptive Search

The discussion highlighted that all three methods should be run under the same experimental protocol.

### 7.1 MMHC

MMHC should be implemented using `bnlearn`. The existing [`/Users/seong/Desktop/Programming/BBN/mmhc.py`](/Users/seong/Desktop/Programming/BBN/mmhc.py) script should therefore be updated so that it both uses the shared preprocessing function and replaces any non-`bnlearn` structure-learning path with the intended `bnlearn`-based MMHC path.

### 7.2 H2PC

H2PC should also be implemented using `bnlearn`. It has not yet been clearly implemented in the workspace and should be added with the same input/output structure as the MMHC and ARGES-like experiments.

### 7.3 ARGES

The intended adaptive experiment in this project is not simply a fixed `HPC -> GES` handoff. A closer-to-true ARGES implementation should use adaptive restricted GES:

- phase 1: run `HPC` in `bnlearn` to estimate a skeleton
- phase 2: convert the skeleton complement into `fixedGaps`
- phase 3: run `pcalg::ges(..., adaptive = "triples")`

This is more faithful to ARGES because the restriction is not fixed forever. During the forward search, `pcalg` can reopen some edge candidates when new unshielded triples appear. For that reason, the safest project label is `ARGES-like (adaptive triples)` unless the implementation is validated as a strict reproduction of a published ARGES variant.

## 8. Evaluation Metrics

The conversation identified the following candidate metrics:

- BIC
- SHD
- runtime
- edge count
- prediction accuracy

However, an important methodological caution was raised regarding SHD:

- SHD requires a reference or gold-standard graph
- if no reference graph exists, SHD should not be reported as if it were ground truth

If no expert-defined or simulated reference DAG is available, the most defensible comparison would use:

- BIC
- structure-learning runtime
- total runtime
- number of learned edges
- optional predictive accuracy

## 9. Practical Team Recommendation

To keep the weekend work manageable, the discussion implicitly suggested the following division of labor:

- one person finalizes the shared preprocessing function
- one person runs MMHC
- one person implements and runs H2PC
- one person finalizes the ARGES-like adaptive-triples pipeline
- one person consolidates results into tables and figures

The most important coordination step before parallel work begins is agreeing on one official dataset and one preprocessing routine.

## 10. Summary of Final Recommendation

The final recommendation from the discussion is:

1. Do not mix preprocessing styles across scripts.
2. Use the recategorized lung cancer dataset already present in the workspace.
3. Fill missing `Cancer Cell Type` values with `Unknown`.
4. Treat all variables as categorical.
5. Use one shared encoding and train/test split for all methods.
6. Implement MMHC and H2PC through `bnlearn`, and implement the adaptive path as `ARGES-like (adaptive triples)` using `HPC` from `bnlearn` and `pcalg::ges(..., adaptive = "triples")`.
7. Report SHD only if a true reference graph is available.

In short, although the UCI Heart Disease dataset is a valid benchmark and easier to explain academically, the current lung cancer dataset is much larger and already closer to a usable hybrid structure-learning benchmark. For this project timeline, the recategorized lung cancer dataset is the more practical and efficient choice.

## Conclusion

The conversation moved from task planning to a deeper methodological concern: fair comparison requires shared preprocessing. That issue remains more important than the choice of algorithm itself. The present workspace already contains enough data and code to support a useful weekend experiment, but only if MMHC, H2PC, and the ARGES-like adaptive method are evaluated under a common pipeline. The strongest immediate next step is therefore to implement one canonical preprocessing function and make all experiment scripts depend on it.
