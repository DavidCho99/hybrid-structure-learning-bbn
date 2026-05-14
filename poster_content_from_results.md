# Poster Template Analysis and Content Draft

## 1. What the poster template is doing well

The sample poster uses a very clear visual hierarchy:

- a large title across the top
- author names and affiliation directly under the title
- a wide center area reserved for visuals
- a narrow right column broken into short rounded boxes
- very little paragraph text, with most ideas expressed as 2 to 4 bullets

This means your version should avoid dense prose. The strongest fit for this layout is:

- one strong title
- one short subtitle or affiliation line
- one central workflow or network figure
- one compact results table or bar chart
- six to seven short content boxes on the right

For your project, the template can be adapted like this:

- center-left visual area: workflow figure plus learned-network figure or bar charts
- right column boxes: Introduction, Background, Dataset, Preprocessing, Hybrid Methods, Results, Limitations / Next Steps

## 2. Recommended title block

### Title

**Comparing Hybrid Bayesian Belief Network Structure Learning Methods on a Lung Cancer Dataset**

### Authors

**Name Here, Name Here, Name Here**

### Affiliation

**Department of Mathematics and Statistics, Texas Tech University**

## 3. Poster-ready content matched to the template

### Introduction

- Bayesian Belief Networks (BBNs) model probabilistic relationships among clinical variables.
- Structure learning identifies the network directly from observed data.
- This project compares three hybrid structure-learning methods on a recategorized lung cancer dataset.
- Goal: determine which method gives the best balance of model fit, runtime, graph size, and prediction accuracy.

### Background

- Hybrid methods combine constraint-based search with score-based optimization.
- `MMHC` and `H2PC` are standard hybrid algorithms available in `bnlearn`.
- An `ARGES-like` pipeline was also tested using an `HPC` restriction graph followed by adaptive restricted `GES`.
- A fair comparison required shared preprocessing, one train/test split, and common evaluation metrics.

### Dataset Structure

- Dataset: `Recategorized_Cleaned_Lung_Cancer_dataset.csv`
- Total records: `191,993`
- Variables: `11` categorical variables
- Target variable: `Cause of Death`
- Train/test split: `153,594 / 38,399` (`80/20`)

**Variables used**

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

### Data Processing

- Missing values in `Cancer Cell Type` were filled with `Unknown`.
- All variables were treated as categorical to keep preprocessing consistent.
- The same cleaned dataset and split were used for all three methods.
- Evaluation focused on `BIC`, structure-learning runtime, total runtime, learned edge count, and prediction accuracy.

### Hybrid Methods

**MMHC**

- Constraint phase: `MMPC`
- Score phase: hill-climbing search
- Implementation: `bnlearn`

**H2PC**

- Constraint phase: `HPC`
- Score phase: hill-climbing search
- Implementation: `bnlearn`

**ARGES-like**

- Phase 1: `HPC` skeleton from `bnlearn`
- Phase 2: adaptive restricted `GES` with `adaptive = "triples"`
- Implementation: `bnlearn` + `pcalg`

### Results

| Method | BIC | Structure Runtime (s) | Total Runtime (s) | Edge Count | Accuracy |
|---|---:|---:|---:|---:|---:|
| MMHC | -1,528,163.0048 | 3.4886 | 16.9972 | 7 | 0.7044 |
| H2PC | -1,380,635.0229 | 8.2177 | 23.9098 | 25 | 0.7226 |
| ARGES-like | -1,703,922.1521 | 8.7062 | 21.4393 | 0 | 0.5595 |

**Result highlights**

- `H2PC` achieved the best `BIC` and the highest prediction accuracy.
- `MMHC` was the fastest method and learned the smallest non-empty graph.
- `ARGES-like` returned `0` final edges on the full dataset.
- The adaptive restricted search did not perform well in this categorical-data setting.

### Interpretation

- `H2PC` gave the best overall balance of structure quality and predictive performance.
- `MMHC` may be useful when runtime is more important than maximum accuracy.
- `ARGES-like` was less suitable under the current scoring and data assumptions.
- These results suggest that `H2PC` is the strongest hybrid method among the three tested pipelines for this dataset.

### Limitations and Next Steps

- All variables in the working dataset were categorical.
- No gold-standard graph was available, so `SHD` was not reported.
- The `ARGES-like` pipeline may be less aligned with this data type than the `bnlearn` methods.
- Future work: test additional datasets, compare learned structures with domain knowledge, and add clearer graph visualizations.

## 4. Short version for the right-side boxes

If you want the text to match the sample poster's short-box style, use the following compact version.

### Box 1: Introduction

- BBNs model probabilistic dependencies between clinical variables.
- We compare hybrid structure-learning methods on a lung cancer dataset.
- Main question: which method best balances fit, runtime, and predictive performance?

### Box 2: Background

- Hybrid learning combines constraint-based and score-based search.
- Compared methods: `MMHC`, `H2PC`, and `ARGES-like`.
- All methods used the same preprocessing and train/test split.

### Box 3: Dataset

- `191,993` records
- `11` categorical variables
- Target: `Cause of Death`
- Split: `80/20`

### Box 4: Data Processing

- Filled missing `Cancer Cell Type` with `Unknown`
- Treated all variables as categorical
- Used one shared preprocessing pipeline
- Evaluated BIC, runtime, edge count, and accuracy

### Box 5: Hybrid Methods

- `MMHC`: MMPC + hill climbing
- `H2PC`: HPC + hill climbing
- `ARGES-like`: HPC restriction + adaptive GES
- Implemented with `bnlearn` and `pcalg`

### Box 6: Results

- Best `BIC`: `H2PC`
- Best accuracy: `H2PC = 0.7226`
- Fastest runtime: `MMHC = 16.9972 s`
- `ARGES-like` produced an empty final graph

### Box 7: Next Steps

- Test more datasets
- Compare against domain knowledge
- Add network visualizations
- Investigate better settings for ARGES-like search

## 5. Suggested captions for center visuals

### Workflow figure caption

**Shared experimental pipeline used for all three hybrid structure-learning methods.**

### Results chart caption

**H2PC achieved the strongest overall performance, while MMHC provided the fastest runtime.**

### Network figure caption

**Learned structures from MMHC and H2PC showed meaningful clinical dependencies, whereas ARGES-like returned an empty final graph.**
