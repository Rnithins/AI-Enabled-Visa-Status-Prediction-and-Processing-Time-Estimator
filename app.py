import os
from datetime import datetime

import pandas as pd
from flask import Flask, jsonify, render_template, request

from visapredict.inference_adapter import build_feature_vector, load_model_and_metadata

BASE_DIR = os.path.dirname(__file__)
MODEL_DIR = os.path.join(BASE_DIR, "model")
DATA_PATH = os.path.join(BASE_DIR, "visapredict", "visa_eda_features.csv")

app = Flask(__name__, template_folder="templates", static_folder="static")

_MODEL = None
_METADATA = None


def _get_model_bundle():
    global _MODEL, _METADATA
    if _MODEL is None or _METADATA is None:
        _MODEL, _METADATA = load_model_and_metadata(MODEL_DIR)
    return _MODEL, _METADATA


def _load_trends_data():
    df = pd.read_csv(DATA_PATH)
    df["application_date"] = pd.to_datetime(df["application_date"], errors="coerce")
    df = df.dropna(subset=["application_date"])
    df["month"] = df["application_date"].dt.strftime("%b")
    month_order = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

    monthly = (
        df.groupby("month")
        .agg(avg_days=("processing_days", "mean"), applications=("processing_days", "size"))
        .reset_index()
    )
    monthly["month"] = pd.Categorical(monthly["month"], categories=month_order, ordered=True)
    monthly = monthly.sort_values("month")

    by_visa_type = (
        df.groupby("visa_type")["processing_days"]
        .mean()
        .reset_index()
        .sort_values("processing_days", ascending=False)
    )

    return {
        "monthly": [
            {
                "month": row["month"],
                "avg_days": round(row["avg_days"], 1),
                "applications": int(row["applications"]),
            }
            for _, row in monthly.iterrows()
        ],
        "by_visa_type": [
            {"visa_type": row["visa_type"], "avg_days": round(row["processing_days"], 1)}
            for _, row in by_visa_type.iterrows()
        ],
    }


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/estimator")
def estimator():
    return render_template("estimator.html")


@app.route("/results")
def results():
    return render_template("results.html")


@app.route("/trends")
def trends():
    return render_template("trends.html")


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


@app.route("/predict", methods=["POST"])
def predict():
    required_fields = [
        "visa_type",
        "applicant_country",
        "destination_country",
        "processing_office",
        "submission_date",
    ]
    payload = request.get_json(silent=True) or {}
    missing = [field for field in required_fields if not payload.get(field)]
    if missing:
        return jsonify({"error": f"Missing required fields: {', '.join(missing)}"}), 400

    try:
        datetime.strptime(payload["submission_date"], "%Y-%m-%d")
    except ValueError:
        return jsonify({"error": "submission_date must be in YYYY-MM-DD format."}), 400

    model, metadata = _get_model_bundle()
    try:
        features = build_feature_vector(payload, metadata)
        prediction = float(model.predict(features)[0])
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500

    prediction = max(prediction, 1.0)
    predicted_days = round(prediction)
    range_min = round(predicted_days * 0.9)
    range_max = round(predicted_days * 1.1)

    return jsonify(
        {
            "predicted_days": predicted_days,
            "range_min": range_min,
            "range_max": range_max,
            "model_name": metadata.get("model_name", "Model"),
            "note": "Estimate based on historical patterns",
        }
    )


@app.route("/trends-data")
def trends_data():
    return jsonify(_load_trends_data())


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
