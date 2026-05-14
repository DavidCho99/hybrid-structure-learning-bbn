from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict

import pandas as pd
from sklearn.model_selection import train_test_split


ROOT = Path(__file__).resolve().parent
DEFAULT_DATASET_PATH = ROOT / "Recategorized_Cleaned_Lung_Cancer_dataset.csv"
TARGET_COLUMN = "Cause of Death"
DEFAULT_TEST_SIZE = 0.2
DEFAULT_RANDOM_STATE = 42
UNKNOWN_CATEGORY = "Unknown"


@dataclass
class PreparedData:
    dataset_path: Path
    cleaned_df: pd.DataFrame
    encoded_df: pd.DataFrame
    train_df: pd.DataFrame
    test_df: pd.DataFrame
    train_encoded_df: pd.DataFrame
    test_encoded_df: pd.DataFrame
    mappings: Dict[str, Dict[str, int]]


def load_dataset(file_path: str | Path = DEFAULT_DATASET_PATH) -> pd.DataFrame:
    return pd.read_csv(Path(file_path))


def clean_dataset(df: pd.DataFrame) -> pd.DataFrame:
    cleaned = df.copy()
    cleaned["Cancer Cell Type"] = cleaned["Cancer Cell Type"].fillna(UNKNOWN_CATEGORY)

    for column in cleaned.columns:
        # Keep data as plain Python objects (not NumPy string dtype) so downstream
        # libraries (e.g., pgmpy) can reliably infer categorical types.
        cleaned[column] = cleaned[column].fillna(UNKNOWN_CATEGORY).astype(str).astype("object")

    return cleaned


def fit_category_mappings(df: pd.DataFrame) -> Dict[str, Dict[str, int]]:
    mappings: Dict[str, Dict[str, int]] = {}
    for column in df.columns:
        categories = sorted(df[column].astype(str).unique().tolist())
        mappings[column] = {value: idx for idx, value in enumerate(categories)}
    return mappings


def encode_dataset(df: pd.DataFrame, mappings: Dict[str, Dict[str, int]] | None = None) -> tuple[pd.DataFrame, Dict[str, Dict[str, int]]]:
    if mappings is None:
        mappings = fit_category_mappings(df)

    encoded = df.copy()
    for column, mapping in mappings.items():
        encoded[column] = encoded[column].map(mapping)
        if encoded[column].isna().any():
            missing_values = df.loc[encoded[column].isna(), column].unique().tolist()
            raise ValueError(f"Unknown category values in column {column}: {missing_values}")
        encoded[column] = encoded[column].astype(int)

    return encoded, mappings


def split_dataset(
    cleaned_df: pd.DataFrame,
    encoded_df: pd.DataFrame,
    test_size: float = DEFAULT_TEST_SIZE,
    random_state: int = DEFAULT_RANDOM_STATE,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    indices = cleaned_df.index.to_series()
    train_idx, test_idx = train_test_split(
        indices,
        test_size=test_size,
        random_state=random_state,
        shuffle=True,
    )

    train_df = cleaned_df.loc[train_idx].reset_index(drop=True)
    test_df = cleaned_df.loc[test_idx].reset_index(drop=True)
    train_encoded_df = encoded_df.loc[train_idx].reset_index(drop=True)
    test_encoded_df = encoded_df.loc[test_idx].reset_index(drop=True)

    return train_df, test_df, train_encoded_df, test_encoded_df


def prepare_data(
    file_path: str | Path = DEFAULT_DATASET_PATH,
    test_size: float = DEFAULT_TEST_SIZE,
    random_state: int = DEFAULT_RANDOM_STATE,
    sample_size: int | None = None,
) -> PreparedData:
    dataset_path = Path(file_path).resolve()
    cleaned_df = clean_dataset(load_dataset(dataset_path))

    if sample_size is not None and sample_size < len(cleaned_df):
        cleaned_df = cleaned_df.sample(n=sample_size, random_state=random_state).reset_index(drop=True)

    encoded_df, mappings = encode_dataset(cleaned_df)
    train_df, test_df, train_encoded_df, test_encoded_df = split_dataset(
        cleaned_df=cleaned_df,
        encoded_df=encoded_df,
        test_size=test_size,
        random_state=random_state,
    )

    return PreparedData(
        dataset_path=dataset_path,
        cleaned_df=cleaned_df,
        encoded_df=encoded_df,
        train_df=train_df,
        test_df=test_df,
        train_encoded_df=train_encoded_df,
        test_encoded_df=test_encoded_df,
        mappings=mappings,
    )
