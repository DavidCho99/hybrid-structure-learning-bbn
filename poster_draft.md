# Bayesian Belief Network Hybrid Structure Learning on a Lung Cancer Dataset

**Names:** Name Here, Name Here, Name Here  
**Affiliation:** Texas Tech University

---

## Poster Layout Guide

Use this draft in a `3-column` poster layout similar to the template:

- **Left column:** Abstract, Introduction, Methodology
- **Center column:** Dataset, Results Table, Key Figure
- **Right column:** Discussion, Limitations, References

---

## Abstract

This study compares three hybrid Bayesian network structure-learning methods on a recategorized lung cancer dataset: `MMHC`, `H2PC`, and an `ARGES-like` adaptive restricted GES pipeline. All methods were evaluated using the same preprocessing pipeline, 80/20 train-test split, and common evaluation metrics. The dataset contained `191,993` records and `11` categorical variables, with `Cause of Death` used as the target variable. Among the three methods, `H2PC` achieved the best overall performance, with the best BIC (`-1,380,635.0229`) and highest prediction accuracy (`0.7226`). `MMHC` produced a smaller and faster model, while the `ARGES-like` method underperformed and returned an empty final graph. These results suggest that `H2PC` was the strongest hybrid structure-learning method for this categorical dataset.

---

## Introduction

Bayesian Belief Networks (BBNs) are graphical models that represent probabilistic relationships among variables. Structure learning is the task of discovering the dependency graph directly from data.

Hybrid structure-learning methods combine:

- constraint-based learning
- score-based learning

This study focuses on comparing three hybrid methods on a large lung cancer dataset:

- `MMHC (bnlearn)`
- `H2PC (bnlearn)`
- `ARGES-like (adaptive triples)`

### Research Question

Which hybrid structure-learning method performs best on a categorical lung cancer dataset when evaluated by model fit, runtime, learned structure size, and prediction accuracy?

---

## Dataset

### Data Source

Recategorized lung cancer dataset used in the project workspace:

- `191,993` total cases
- `11` categorical variables
- target variable: `Cause of Death`

### Train/Test Split

- training set: `153,594`
- test set: `38,399`
- split ratio: `80/20`

### Variables

- Age
- Tumor Location
- Cancer Cell Type
- Tumor Extent at Diagnosis
- Regional Lymph Node Involvement
- Metastatic Spread
- Tumor Laterality
- Extent of Regional Lymph Node Surgery
- Treatment Plan
- Days from Diagnosis to Treatment
- Cause of Death

---

## Methodology

### Shared Preprocessing

- filled missing `Cancer Cell Type` with `Unknown`
- treated all variables as categorical
- used one shared preprocessing pipeline for all methods
- used the same train-test split for all experiments

### Compared Methods

**MMHC**

- phase 1: `MMPC`
- phase 2: hill-climbing search
- implementation: `bnlearn`

**H2PC**

- phase 1: `HPC`
- phase 2: hill-climbing search
- implementation: `bnlearn`

**ARGES-like**

- phase 1: `HPC` used to build an initial restriction graph
- phase 2: adaptive restricted `GES` with `adaptive = "triples"`
- implementation: `bnlearn` + `pcalg`

### Evaluation Metrics

- BIC
- structure-learning runtime
- total runtime
- learned edge count
- prediction accuracy

---

## Results

| Method | BIC | Structure Runtime (s) | Total Runtime (s) | Edge Count | Accuracy |
|---|---:|---:|---:|---:|---:|
| MMHC (bnlearn) | -1,528,163.0048 | 3.4886 | 16.9972 | 7 | 0.7044 |
| H2PC (bnlearn) | -1,380,635.0229 | 8.2177 | 23.9098 | 25 | 0.7226 |
| ARGES-like (adaptive triples) | -1,703,922.1521 | 8.7062 | 21.4393 | 0 | 0.5595 |

### Key Observations

- `H2PC` achieved the best BIC and highest prediction accuracy.
- `MMHC` ran faster and learned a smaller graph.
- `ARGES-like` returned `0` final edges on the full dataset.
- The phase-1 `HPC` skeleton for `ARGES-like` had `60` candidate edges, but the final adaptive GES step removed all of them.

---

## Discussion

`H2PC` was the strongest method in this experiment. It learned the largest non-empty structure with `25` edges and achieved the best predictive performance (`0.7226`) and best BIC (`-1,380,635.0229`).

`MMHC` was more computationally efficient than `H2PC`, with a shorter structure-learning runtime (`3.4886 s`) and total runtime (`16.9972 s`). However, it learned only `7` edges and produced lower accuracy (`0.7044`) and weaker BIC than `H2PC`.

The `ARGES-like` method performed poorly on this dataset. Although it started from a non-empty `HPC` restriction graph with `60` candidate edges, the adaptive GES stage produced an empty final graph. This led to the weakest BIC and lowest prediction accuracy among the three methods.

---

## Conclusion

- `H2PC` was the best-performing hybrid structure-learning method on this dataset.
- `MMHC` was faster but less accurate.
- `ARGES-like` was not well suited to this categorical data setting under the current scoring framework.

### Main Takeaway

For this categorical lung cancer dataset, `H2PC` provided the best balance of structure quality and predictive performance.

---

## Limitations

- all variables in the working dataset were categorical
- the `ARGES-like` pipeline used adaptive GES that is more naturally aligned with continuous-variable scoring assumptions
- structural Hamming distance was not reported because no gold-standard reference graph was available

---

## Future Work

- test the methods on additional datasets
- evaluate continuous-variable datasets for stricter ARGES comparisons
- compare learned networks with domain knowledge from oncology experts
- add visualization of learned graph structures

---

## References

1. Tsamardinos I, Brown LE, Aliferis CF. The Max-Min Hill-Climbing Bayesian Network Structure Learning Algorithm. *Machine Learning*. 2006.
2. Gasse M, Aussem A, Elghazel H. A Hybrid Algorithm for Bayesian Network Structure Learning with Application to Multi-Label Learning. *Expert Systems with Applications*. 2014.
3. Nandy P, Hauser A, Maathuis MH. High-dimensional consistency in score-based and hybrid structure learning. *Annals of Statistics*. 2018.
4. Scutari M. `bnlearn`: Bayesian network structure learning in R.
5. Kalisch M et al. `pcalg`: estimation of graphical models and causal structure learning.

---

## Suggested Figure Ideas

- bar chart of prediction accuracy by method
- bar chart of edge count by method
- runtime comparison chart
- simple learned-network visualization for `MMHC` and `H2PC`
