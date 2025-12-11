"""
Visa Status Prediction - Milestone 1: Data Collection & Preprocessing
"""

import argparse
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional


def load_data(input_path: Optional[str] = None, sample: bool = False) -> pd.DataFrame:
    """Load data from CSV file or sample data."""
    if sample:
        sample_data = {
            "application_date": ["2024-01-01", None, "2024-03-10"],
            "decision_date": ["2024-02-01", "2024-03-20", None],
            "country": ["India", None, "UK"],
            "visa_type": ["Student", "Tourist", "Work"],
            "processing_office": ["Delhi", "New York", None],
            "fee_paid": [200.0, None, 150.0]
        }
        df = pd.DataFrame(sample_data)
        print("[INFO] Loaded sample data:", df.shape)
    else:
        df = pd.read_csv(input_path)
        print("[INFO] Loaded data from", input_path, "shape:", df.shape)
    return df


def parse_dates(df: pd.DataFrame, date_cols: List[str]) -> pd.DataFrame:
    """Parse date columns."""
    for col in date_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], format='%d-%m-%Y', errors='coerce')
    return df


def fill_missing(df: pd.DataFrame, date_strategy: str = "mode", numeric_strategy: str = "median",
                 categorical_strategy: str = "mode", custom_values: Optional[Dict[str, Any]] = None) -> pd.DataFrame:
    """Fill missing values in date, numeric & categorical columns."""
    df = df.copy()
    if custom_values:
        for col, val in custom_values.items():
            if col in df.columns:
                df[col] = df[col].fillna(val)

    for col in df.columns:
        if df[col].isna().any():
            if custom_values and col in custom_values:
                continue
            if pd.api.types.is_datetime64_any_dtype(df[col]):
                continue
            elif pd.api.types.is_numeric_dtype(df[col]):
                if isinstance(numeric_strategy, (int, float)):
                    df[col] = df[col].fillna(numeric_strategy)
                elif numeric_strategy == "median":
                    df[col] = df[col].fillna(df[col].median())
                elif numeric_strategy == "mean":
                    df[col] = df[col].fillna(df[col].mean())
            else:
                if categorical_strategy == "mode":
                    mode_val = df[col].mode()
                    if not mode_val.empty:
                        df[col] = df[col].fillna(mode_val[0])
                else:
                    df[col] = df[col].fillna(categorical_strategy)
    return df


def compute_processing_days(df: pd.DataFrame, app_date_col: str = "application_date",
                            dec_date_col: str = "decision_date", drop_na: bool = False) -> pd.DataFrame:
    """Compute processing days."""
    if 'processing_days' not in df.columns:
        df['processing_days'] = (df[dec_date_col] - df[app_date_col]).dt.days
        if drop_na:
            df = df.dropna(subset=['processing_days'])
    return df


def encode_categorical(df: pd.DataFrame, cat_cols: List[str], drop_first: bool = False) -> pd.DataFrame:
    """One-hot encode categorical columns."""
    for col in cat_cols:
        if col in df.columns:
            dummies = pd.get_dummies(df[col], prefix=col, drop_first=drop_first)
            df = pd.concat([df, dummies], axis=1)
            df.drop(col, axis=1, inplace=True)
    return df


def prepare_dataset(input_path: Optional[str], output_path: str, sample: bool, date_cols: List[str],
                    cat_cols: List[str], drop_na_target: bool) -> None:
    """Main preprocessing pipeline."""
    df = load_data(input_path, sample)
    df = parse_dates(df, date_cols)
    df = fill_missing(df)
    df = compute_processing_days(df, date_cols[0], date_cols[1], drop_na_target)
    df = encode_categorical(df, cat_cols)
    df.to_csv(output_path, index=False)
    print(f"[INFO] Saved processed data to {output_path}", df.shape)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Preprocess visa data.")
    parser.add_argument("--input", type=str, help="Path to raw CSV file")
    parser.add_argument("--output", type=str, required=True, help="Path to save processed CSV")
    parser.add_argument("--sample", action="store_true", help="Use sample data")
    parser.add_argument("--date-cols", nargs=2, default=["application_date", "decision_date"])
    parser.add_argument("--cat-cols", nargs="*", default=["applicant_country", "visa_type"])
    parser.add_argument("--drop-na-target", action="store_true")

    args = parser.parse_args()

    if not args.sample and not args.input:
        parser.error("--input is required unless --sample is used")

    prepare_dataset(args.input, args.output, args.sample, args.date_cols, args.cat_cols, args.drop_na_target)
