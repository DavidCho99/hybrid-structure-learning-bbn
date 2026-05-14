from __future__ import annotations

from typing import Iterable

import networkx as nx
import numpy as np
import pandas as pd
from pgmpy.estimators import BayesianEstimator, MaximumLikelihoodEstimator
from pgmpy.inference import VariableElimination
from sklearn.metrics import balanced_accuracy_score, f1_score, log_loss, roc_auc_score
try:
    from pgmpy.models import DiscreteBayesianNetwork as BayesianNetwork  # pgmpy>=1.0.0
except ImportError:  # pragma: no cover
    from pgmpy.models import BayesianNetwork  # pgmpy<1.0.0

try:
    from pgmpy.estimators import BIC as _BICScorer  # pgmpy>=1.0.0
except ImportError:  # pragma: no cover
    from pgmpy.estimators import BicScore as _BICScorer  # pgmpy<1.0.0


def normalize_edges(edges: Iterable[tuple[str, str]]) -> list[tuple[str, str]]:
    normalized: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for source, target in edges:
        edge = (str(source), str(target))
        if edge not in seen:
            seen.add(edge)
            normalized.append(edge)
    return normalized


def build_bayesian_network(edges: Iterable[tuple[str, str]], nodes: Iterable[str]) -> BayesianNetwork:
    edges = normalize_edges(edges)
    graph = nx.DiGraph()
    graph.add_nodes_from(nodes)
    graph.add_edges_from(edges)

    if not nx.is_directed_acyclic_graph(graph):
        raise ValueError("Learned structure is not a DAG.")

    model = BayesianNetwork()
    model.add_nodes_from(nodes)
    model.add_edges_from(edges)
    return model


def fit_bayesian_network(model: BayesianNetwork, train_df: pd.DataFrame) -> BayesianNetwork:
    try:
        fitted = model.fit(
            train_df,
            estimator=BayesianEstimator,
            prior_type="BDeu",
            equivalent_sample_size=10,
        )
        fitted.check_model()
        return fitted
    except Exception:
        fitted = model.fit(
            train_df,
            estimator=MaximumLikelihoodEstimator,
        )
        fitted.check_model()
        return fitted


def compute_bic_score(model: BayesianNetwork, df: pd.DataFrame) -> float:
    scorer = _BICScorer(df)
    return float(scorer.score(model))


def compute_prediction_accuracy(
    model: BayesianNetwork,
    test_df: pd.DataFrame,
    target_column: str,
) -> tuple[float | None, int]:
    if target_column not in model.nodes():
        return None, len(test_df)

    infer = VariableElimination(model)
    correct = 0
    failed_queries = 0

    for _, row in test_df.iterrows():
        evidence = row.drop(target_column).to_dict()
        truth = row[target_column]

        try:
            result = infer.query(variables=[target_column], evidence=evidence, show_progress=False)
            prediction_index = int(np.argmax(result.values))
            predicted_value = result.state_names[target_column][prediction_index]
        except Exception:
            failed_queries += 1
            continue

        if predicted_value == truth:
            correct += 1

    successful_queries = len(test_df) - failed_queries
    if successful_queries <= 0:
        return None, failed_queries

    return correct / successful_queries, failed_queries


def compute_prediction_metrics(
    model: BayesianNetwork,
    test_df: pd.DataFrame,
    target_column: str,
) -> dict[str, object]:
    """
    Validation metrics for predicting `target_column` from the remaining columns.

    Notes:
    - Metrics are computed only on rows where inference succeeds.
    - When the model doesn't contain the target, metrics are returned as None.
    """
    if target_column not in model.nodes():
        return {
            "Prediction Accuracy": None,
            "Balanced Accuracy": None,
            "Macro F1": None,
            "AUC": None,
            "Log Loss": None,
            "Brier Score": None,
            "Inference Success Rate": 0.0,
            "Failed Queries": int(len(test_df)),
        }

    infer = VariableElimination(model)
    y_true: list[str] = []
    y_pred: list[str] = []
    y_prob: list[np.ndarray] = []
    classes: list[str] | None = None
    failed_queries = 0

    for _, row in test_df.iterrows():
        evidence = row.drop(target_column).to_dict()
        truth = str(row[target_column])

        try:
            result = infer.query(variables=[target_column], evidence=evidence, show_progress=False)
            state_names = [str(x) for x in result.state_names[target_column]]
            if classes is None:
                classes = state_names
            elif classes != state_names:
                # If state ordering changes between queries, align to the first seen ordering.
                # (This shouldn't normally happen, but it's safer than silently mixing.)
                index_map = {name: idx for idx, name in enumerate(state_names)}
                aligned = np.zeros((len(classes),), dtype=float)
                for aligned_idx, name in enumerate(classes):
                    if name in index_map:
                        aligned[aligned_idx] = float(result.values[index_map[name]])
                probs = aligned
            else:
                probs = np.asarray(result.values, dtype=float)

            prediction_index = int(np.argmax(probs))
            predicted_value = classes[prediction_index] if classes is not None else state_names[prediction_index]
        except Exception:
            failed_queries += 1
            continue

        if classes is None:
            failed_queries += 1
            continue
        if truth not in classes:
            failed_queries += 1
            continue

        y_true.append(truth)
        y_pred.append(str(predicted_value))
        y_prob.append(probs)

    n_success = len(y_true)
    n_total = len(test_df)
    success_rate = 0.0 if n_total == 0 else n_success / n_total

    if n_success == 0 or classes is None:
        return {
            "Prediction Accuracy": None,
            "Balanced Accuracy": None,
            "Macro F1": None,
            "AUC": None,
            "Log Loss": None,
            "Brier Score": None,
            "Inference Success Rate": round(success_rate, 6),
            "Failed Queries": int(n_total - n_success),
        }

    y_prob_arr = np.vstack(y_prob)

    accuracy = float(np.mean(np.array(y_true) == np.array(y_pred)))
    bal_acc = float(balanced_accuracy_score(y_true, y_pred))
    macro_f1 = float(f1_score(y_true, y_pred, average="macro"))

    auc: float | None = None
    try:
        present_labels = [label for label in classes if label in set(y_true)]
        if len(present_labels) >= 2:
            if len(classes) == 2:
                # Binary ROC AUC: use the second class in `classes` as the positive label
                # to make the metric deterministic.
                positive_label = classes[1]
                positive_index = 1
                y_true_bin = np.asarray([1 if t == positive_label else 0 for t in y_true], dtype=int)
                y_score = y_prob_arr[:, positive_index]
                auc = float(roc_auc_score(y_true_bin, y_score))
            else:
                # Multiclass macro AUC (one-vs-rest) on labels observed in the successful queries.
                indices = [classes.index(label) for label in present_labels]
                auc = float(
                    roc_auc_score(
                        y_true,
                        y_prob_arr[:, indices],
                        labels=present_labels,
                        multi_class="ovr",
                        average="macro",
                    )
                )
    except Exception:
        auc = None

    # log_loss expects probabilities for all classes in a stable order.
    ll = float(log_loss(y_true, y_prob_arr, labels=classes))
    # Multi-class Brier: mean sum_k (p_k - y_k)^2.
    y_onehot = np.zeros_like(y_prob_arr)
    class_to_idx = {name: idx for idx, name in enumerate(classes)}
    for i, truth in enumerate(y_true):
        y_onehot[i, class_to_idx[truth]] = 1.0
    brier = float(np.mean(np.sum((y_prob_arr - y_onehot) ** 2, axis=1)))

    return {
        "Prediction Accuracy": round(accuracy, 6),
        "Balanced Accuracy": round(bal_acc, 6),
        "Macro F1": round(macro_f1, 6),
        "AUC": None if auc is None else round(auc, 6),
        "Log Loss": round(ll, 6),
        "Brier Score": round(brier, 6),
        "Inference Success Rate": round(success_rate, 6),
        "Failed Queries": int(n_total - n_success),
    }


def edges_to_frame(edges: Iterable[tuple[str, str]]) -> pd.DataFrame:
    return pd.DataFrame(normalize_edges(edges), columns=["source", "target"])


def summarize_result(
    algorithm: str,
    dataset: str,
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
    bic_score: float | None,
    structure_runtime: float,
    total_runtime: float,
    edge_count: int,
    prediction_accuracy: float | None,
    balanced_accuracy: float | None = None,
    macro_f1: float | None = None,
    auc: float | None = None,
    log_loss_value: float | None = None,
    brier_score: float | None = None,
    inference_success_rate: float | None = None,
    failed_queries: int | None = None,
    notes: str = "",
) -> dict[str, object]:
    return {
        "Algorithm": algorithm,
        "Dataset": dataset,
        "Train Size": len(train_df),
        "Test Size": len(test_df),
        "BIC": None if bic_score is None else round(bic_score, 4),
        "Structure Runtime (s)": round(structure_runtime, 4),
        "Total Runtime (s)": round(total_runtime, 4),
        "Edge Count": int(edge_count),
        "Prediction Accuracy": None if prediction_accuracy is None else round(prediction_accuracy, 4),
        "Balanced Accuracy": None if balanced_accuracy is None else round(balanced_accuracy, 4),
        "Macro F1": None if macro_f1 is None else round(macro_f1, 4),
        "AUC": None if auc is None else round(auc, 4),
        "Log Loss": None if log_loss_value is None else round(log_loss_value, 4),
        "Brier Score": None if brier_score is None else round(brier_score, 4),
        "Inference Success Rate": None if inference_success_rate is None else round(inference_success_rate, 4),
        "Failed Queries": None if failed_queries is None else int(failed_queries),
        "Notes": notes,
    }
