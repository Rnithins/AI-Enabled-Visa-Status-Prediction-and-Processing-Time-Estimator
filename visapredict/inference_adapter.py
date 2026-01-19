import json
import os
from typing import Dict, Tuple

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor

TARGET_COLUMN = "processing_days"
MODEL_NAME = "RandomForestRegressor"


def _load_dataset() -> pd.DataFrame:
    base_dir = os.path.dirname(__file__)
    data_path = os.path.join(base_dir, "visa_eda_features.csv")
    return pd.read_csv(data_path)


def _build_metadata(df: pd.DataFrame) -> Dict:
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    feature_cols = [col for col in numeric_cols if col != TARGET_COLUMN]
    defaults = {col: float(df[col].mean()) for col in feature_cols}
    country_avg = (
        df.groupby("applicant_country")[TARGET_COLUMN].mean().dropna().to_dict()
    )
    visa_avg = df.groupby("visa_type")[TARGET_COLUMN].mean().dropna().to_dict()
    overall_mean = float(df[TARGET_COLUMN].mean())
    return {
        "feature_order": feature_cols,
        "defaults": defaults,
        "country_avg_processing": country_avg,
        "visa_type_avg_processing": visa_avg,
        "overall_processing_mean": overall_mean,
        "model_name": MODEL_NAME,
    }


def _train_model(df: pd.DataFrame, feature_cols) -> RandomForestRegressor:
    X = df[feature_cols].fillna(df[feature_cols].mean())
    y = df[TARGET_COLUMN]
    model = RandomForestRegressor(
        n_estimators=120,
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X, y)
    return model


def ensure_artifacts(model_dir: str) -> Tuple[str, str]:
    model_path = os.path.join(model_dir, "visa_model.pkl")
    metadata_path = os.path.join(model_dir, "metadata.json")

    if os.path.exists(model_path) and os.path.exists(metadata_path):
        return model_path, metadata_path

    os.makedirs(model_dir, exist_ok=True)
    df = _load_dataset()
    metadata = _build_metadata(df)
    model = _train_model(df, metadata["feature_order"])

    joblib.dump(model, model_path)
    with open(metadata_path, "w", encoding="utf-8") as handle:
        json.dump(metadata, handle, indent=2)

    return model_path, metadata_path


def load_model_and_metadata(model_dir: str):
    model_path, metadata_path = ensure_artifacts(model_dir)
    model = joblib.load(model_path)
    with open(metadata_path, "r", encoding="utf-8") as handle:
        metadata = json.load(handle)
    return model, metadata


def build_feature_vector(payload: Dict, metadata: Dict) -> pd.DataFrame:
    submission_date = pd.to_datetime(payload["submission_date"], errors="coerce")
    if pd.isna(submission_date):
        raise ValueError("submission_date must be in YYYY-MM-DD format.")

    defaults = metadata["defaults"]
    country_map = metadata["country_avg_processing"]
    visa_map = metadata["visa_type_avg_processing"]
    overall_mean = metadata["overall_processing_mean"]
    visa_aliases = {
        "Student": "Student (Other)",
        "Work": "Work (Other)",
    }
    normalized_visa = visa_aliases.get(payload["visa_type"], payload["visa_type"])

    feature_values = {
        "biometrics_delay_days": defaults["biometrics_delay_days"],
        "document_verification_delay": defaults["document_verification_delay"],
        "employer_size": defaults["employer_size"],
        "salary_usd": defaults["salary_usd"],
        "applicant_age": defaults["applicant_age"],
        "fraud_risk_score": defaults["fraud_risk_score"],
        "application_month": float(submission_date.month),
        "country_avg_processing": float(
            country_map.get(payload["applicant_country"], overall_mean)
        ),
        "visa_type_avg_processing": float(visa_map.get(normalized_visa, overall_mean)),
    }

    ordered_features = [feature_values[name] for name in metadata["feature_order"]]
    return pd.DataFrame([ordered_features], columns=metadata["feature_order"])
