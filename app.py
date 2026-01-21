import os
from datetime import datetime
from typing import Optional

import pandas as pd
from flask import Flask, jsonify, render_template, request

from visapredict.inference_adapter import build_feature_vector, load_model_and_metadata

BASE_DIR = os.path.dirname(__file__)
MODEL_DIR = os.path.join(BASE_DIR, "model")
DATA_PATH = os.path.join(BASE_DIR, "visapredict", "visa_eda_features.csv")
FORM_DATA_PATH = os.environ.get(
    "FORM_DATA_PATH",
    os.path.join(
        BASE_DIR, "visapredict", "data", "visa_processing_dataset_upgraded_50k.csv"
    ),
)
TRENDS_DATA_PATH = os.environ.get("TRENDS_DATA_PATH")

app = Flask(__name__, template_folder="templates", static_folder="static")

_MODEL = None
_METADATA = None
_FORM_DATA_CACHE = {"df": None, "mtime": None}
_TRENDS_DATA_CACHE = {"df": None, "mtime": None, "path": None}


def _get_model_bundle():
    global _MODEL, _METADATA
    if _MODEL is None or _METADATA is None:
        _MODEL, _METADATA = load_model_and_metadata(MODEL_DIR)
    return _MODEL, _METADATA


def _resolve_trends_data_path() -> str:
    candidates = []
    if TRENDS_DATA_PATH:
        candidates.append(TRENDS_DATA_PATH)
    candidates.extend(
        [
            os.path.join(BASE_DIR, "backend", "data", "visa_data.csv"),
            os.path.join(BASE_DIR, "backend", "data", "visa_data.xlsx"),
            os.path.join(BASE_DIR, "visapredict", "data", "visa_processing_dataset_upgraded_50k.csv"),
            os.path.join(BASE_DIR, "visapredict", "visa_eda_features.csv"),
        ]
    )
    for path in candidates:
        if path and os.path.exists(path):
            return path
    raise FileNotFoundError(
        "Trends data not found. Set TRENDS_DATA_PATH or add backend/data/visa_data.csv."
    )


def _read_tabular_file(path: str) -> pd.DataFrame:
    _, ext = os.path.splitext(path.lower())
    if ext in {".xlsx", ".xls"}:
        return pd.read_excel(path)
    return pd.read_csv(path)


def _normalize_month_value(value) -> Optional[int]:
    if pd.isna(value):
        return None
    if isinstance(value, (int, float)):
        month_num = int(value)
        if 1 <= month_num <= 12:
            return month_num
        return None
    value_str = str(value).strip()
    if not value_str:
        return None
    month_lookup = {
        "jan": 1,
        "january": 1,
        "feb": 2,
        "february": 2,
        "mar": 3,
        "march": 3,
        "apr": 4,
        "april": 4,
        "may": 5,
        "jun": 6,
        "june": 6,
        "jul": 7,
        "july": 7,
        "aug": 8,
        "august": 8,
        "sep": 9,
        "sept": 9,
        "september": 9,
        "oct": 10,
        "october": 10,
        "nov": 11,
        "november": 11,
        "dec": 12,
        "december": 12,
    }
    return month_lookup.get(value_str.lower())


def _normalize_trends_df(df: pd.DataFrame) -> pd.DataFrame:
    if "processing_days" not in df.columns:
        if "avg_processing_days" in df.columns:
            df["processing_days"] = df["avg_processing_days"]
        else:
            raise ValueError("processing_days or avg_processing_days column is required.")

    if "year" not in df.columns or "month" not in df.columns:
        if "application_date" in df.columns:
            df["application_date"] = pd.to_datetime(df["application_date"], errors="coerce")
            df = df.dropna(subset=["application_date"])
            if "year" not in df.columns:
                df["year"] = df["application_date"].dt.year
            if "month" not in df.columns:
                df["month"] = df["application_date"].dt.month
        else:
            raise ValueError("year/month or application_date column is required.")

    df["month_index"] = df["month"].apply(_normalize_month_value)
    df = df.dropna(subset=["month_index"])
    df["month_index"] = df["month_index"].astype(int)
    df["year"] = df["year"].astype(int)
    return df


def _load_trends_df() -> pd.DataFrame:
    path = _resolve_trends_data_path()
    current_mtime = os.path.getmtime(path)
    cached_df = _TRENDS_DATA_CACHE["df"]
    cached_mtime = _TRENDS_DATA_CACHE["mtime"]
    cached_path = _TRENDS_DATA_CACHE["path"]
    if cached_df is not None and cached_mtime == current_mtime and cached_path == path:
        return cached_df

    df = _read_tabular_file(path)
    df = _normalize_trends_df(df)

    _TRENDS_DATA_CACHE["df"] = df
    _TRENDS_DATA_CACHE["mtime"] = current_mtime
    _TRENDS_DATA_CACHE["path"] = path
    return df


def _load_trends_options(df: pd.DataFrame):
    years = sorted(df["year"].dropna().astype(int).unique().tolist())
    applicant_countries = (
        _unique_sorted(df["applicant_country"])
        if "applicant_country" in df.columns
        else []
    )
    visa_types = _unique_sorted(df["visa_type"]) if "visa_type" in df.columns else []
    return {
        "countries": applicant_countries,
        "visa_types": visa_types,
        "years": years,
    }


def _empty_trends_payload():
    return {
        "months": [],
        "seasonal_avg_days": [],
        "country_labels": [],
        "country_avg_days": [],
        "visa_type_labels": [],
        "visa_type_avg_days": [],
        "monthly_volume": [],
        "kpis": {
            "this_month_days": 0,
            "avg_wait_days": 0,
            "peak_season_label": "",
            "peak_delta_pct": 0,
        },
    }


def _load_trends_data(
    country: Optional[str] = None,
    visa_type: Optional[str] = None,
    year: Optional[str] = None,
):
    df = _load_trends_df()
    if country and country != "all" and "applicant_country" in df.columns:
        df = df[df["applicant_country"] == country]
    if visa_type and visa_type != "all" and "visa_type" in df.columns:
        df = df[df["visa_type"] == visa_type]
    if year and year != "all":
        try:
            df = df[df["year"] == int(year)]
        except ValueError:
            df = df.iloc[0:0]

    if df.empty:
        return _empty_trends_payload()

    month_order = [
        "Jan",
        "Feb",
        "Mar",
        "Apr",
        "May",
        "Jun",
        "Jul",
        "Aug",
        "Sep",
        "Oct",
        "Nov",
        "Dec",
    ]
    month_lookup = {index + 1: label for index, label in enumerate(month_order)}

    volume_col = "application_volume" if "application_volume" in df.columns else None
    volume_agg = ("sum" if volume_col else "size")
    volume_col = volume_col or "processing_days"

    monthly = (
        df.groupby("month_index")
        .agg(avg_days=("processing_days", "mean"), volume=(volume_col, volume_agg))
        .reset_index()
    )
    monthly["month_label"] = monthly["month_index"].map(month_lookup)

    if "applicant_country" in df.columns:
        by_country = (
            df.groupby("applicant_country")
            .agg(avg_days=("processing_days", "mean"), volume=(volume_col, volume_agg))
            .reset_index()
            .sort_values(["volume", "avg_days"], ascending=False)
            .head(8)
        )
    else:
        by_country = pd.DataFrame(columns=["applicant_country", "avg_days", "volume"])

    if "visa_type" in df.columns:
        by_visa_type = (
            df.groupby("visa_type")["processing_days"]
            .mean()
            .reset_index()
            .sort_values("processing_days", ascending=False)
        )
    else:
        by_visa_type = pd.DataFrame(columns=["visa_type", "processing_days"])

    monthly_lookup = {row["month_label"]: row for _, row in monthly.iterrows()}
    months = month_order
    seasonal_avg_days = [
        round(float(monthly_lookup[label]["avg_days"]), 1) if label in monthly_lookup else None
        for label in months
    ]
    monthly_volume = [
        int(monthly_lookup[label]["volume"]) if label in monthly_lookup else 0
        for label in months
    ]

    latest_month_index = int(monthly["month_index"].max()) if not monthly.empty else None
    this_month_days = 0
    if latest_month_index is not None:
        latest_row = monthly.loc[monthly["month_index"] == latest_month_index]
        if not latest_row.empty:
            this_month_days = round(float(latest_row["avg_days"].iloc[0]), 1)

    avg_wait_days = round(float(df["processing_days"].mean()), 1) if not df.empty else 0

    peak_season_label = ""
    peak_delta_pct = 0
    monthly_avg_days = [
        monthly_lookup[label]["avg_days"] if label in monthly_lookup else None for label in months
    ]
    available_months = [
        (index, value)
        for index, value in enumerate(monthly_avg_days)
        if value is not None
    ]
    if available_months:
        if len(available_months) >= 2:
            best_pair = None
            best_value = None
            for index, value in available_months:
                next_index = index + 1
                if next_index < len(monthly_avg_days) and monthly_avg_days[next_index] is not None:
                    pair_value = (value + monthly_avg_days[next_index]) / 2
                    if best_value is None or pair_value > best_value:
                        best_value = pair_value
                        best_pair = (index, next_index)
            if best_pair:
                peak_season_label = f"{months[best_pair[0]]}-{months[best_pair[1]]}"
                if avg_wait_days:
                    peak_delta_pct = round(((best_value - avg_wait_days) / avg_wait_days) * 100)
        if not peak_season_label:
            peak_month_index, peak_value = max(available_months, key=lambda item: item[1])
            peak_season_label = months[peak_month_index]
            if avg_wait_days:
                peak_delta_pct = round(((peak_value - avg_wait_days) / avg_wait_days) * 100)

    return {
        "months": months,
        "seasonal_avg_days": seasonal_avg_days,
        "country_labels": by_country["applicant_country"].tolist(),
        "country_avg_days": [round(float(value), 1) for value in by_country["avg_days"].tolist()],
        "visa_type_labels": by_visa_type["visa_type"].astype(str).tolist(),
        "visa_type_avg_days": [round(float(value), 1) for value in by_visa_type["processing_days"].tolist()],
        "monthly_volume": monthly_volume,
        "kpis": {
            "this_month_days": this_month_days,
            "avg_wait_days": avg_wait_days,
            "peak_season_label": peak_season_label,
            "peak_delta_pct": peak_delta_pct,
        },
    }


def _load_form_dataset() -> pd.DataFrame:
    if not os.path.exists(FORM_DATA_PATH):
        raise FileNotFoundError(f"Form data not found at {FORM_DATA_PATH}")

    current_mtime = os.path.getmtime(FORM_DATA_PATH)
    cached_df = _FORM_DATA_CACHE["df"]
    cached_mtime = _FORM_DATA_CACHE["mtime"]
    if cached_df is not None and cached_mtime == current_mtime:
        return cached_df

    _, ext = os.path.splitext(FORM_DATA_PATH.lower())
    if ext in {".xlsx", ".xls"}:
        df = pd.read_excel(FORM_DATA_PATH)
    else:
        df = pd.read_csv(FORM_DATA_PATH)

    _FORM_DATA_CACHE["df"] = df
    _FORM_DATA_CACHE["mtime"] = current_mtime
    return df


def _unique_sorted(series: pd.Series):
    values = series.dropna().astype(str).str.strip()
    values = [value for value in values if value]
    return sorted(set(values))


def _build_form_options(
    df: pd.DataFrame,
    destination_country: Optional[str] = None,
    visa_type: Optional[str] = None,
):
    destination_col = "destination_country"
    if destination_col not in df.columns and "sponsor_country" in df.columns:
        destination_col = "sponsor_country"

    applicant_countries = (
        _unique_sorted(df["applicant_country"]) if "applicant_country" in df.columns else []
    )
    destination_countries = (
        _unique_sorted(df[destination_col]) if destination_col in df.columns else []
    )
    processing_offices = (
        _unique_sorted(df["processing_center"]) if "processing_center" in df.columns else []
    )

    filtered = df
    if destination_country and destination_col in df.columns:
        filtered = filtered[filtered[destination_col] == destination_country]

    visa_types = (
        _unique_sorted(filtered["visa_type"]) if "visa_type" in filtered.columns else []
    )

    return {
        "applicant_countries": applicant_countries,
        "destination_countries": destination_countries,
        "visa_types": visa_types,
        "processing_offices": processing_offices,
    }


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/estimator")
def estimator():
    form_options = {
        "applicant_countries": [],
        "destination_countries": [],
        "visa_types": [],
        "processing_offices": [],
    }
    try:
        df = _load_form_dataset()
        base_options = _build_form_options(df)
        form_options.update(base_options)
    except FileNotFoundError:
        pass
    return render_template("estimator.html", form_options=form_options)


@app.route("/results")
def results():
    return render_template("results.html")


@app.route("/trends")
def trends():
    options = {"countries": [], "visa_types": [], "years": []}
    initial_data = _empty_trends_payload()
    try:
        df = _load_trends_df()
        options = _load_trends_options(df)
        initial_data = _load_trends_data()
    except (FileNotFoundError, ValueError):
        pass
    return render_template(
        "trends.html",
        trends_options=options,
        trends_data=initial_data,
    )


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


@app.route("/form-options")
def form_options():
    destination_country = request.args.get("destination_country")
    visa_type = request.args.get("visa_type")

    try:
        df = _load_form_dataset()
    except FileNotFoundError as exc:
        return jsonify({"error": str(exc)}), 500

    options = _build_form_options(
        df,
        destination_country=destination_country,
        visa_type=visa_type,
    )
    warnings = []
    if destination_country and not options["visa_types"]:
        warnings.append("No visa types available for the selected destination country.")
    return jsonify(
        {
            "options": {
                "applicant_countries": options["applicant_countries"],
                "destination_countries": options["destination_countries"],
                "visa_types": options["visa_types"],
                "processing_offices": options["processing_offices"],
            },
            "warnings": warnings,
        }
    )


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

    try:
        model, metadata = _get_model_bundle()
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
    return jsonify(
        _load_trends_data(
            country=request.args.get("country"),
            visa_type=request.args.get("visa_type"),
            year=request.args.get("year"),
        )
    )


@app.route("/api/trends")
def api_trends():
    try:
        payload = _load_trends_data(
            country=request.args.get("country"),
            visa_type=request.args.get("visa_type"),
            year=request.args.get("year"),
        )
    except (FileNotFoundError, ValueError) as exc:
        return jsonify({"error": str(exc)}), 500
    return jsonify(payload)


@app.route("/api/trends/options")
def api_trends_options():
    try:
        df = _load_trends_df()
        options = _load_trends_options(df)
    except (FileNotFoundError, ValueError) as exc:
        return jsonify({"error": str(exc)}), 500
    return jsonify({"options": options})


@app.route("/api/trends/meta")
def api_trends_meta():
    try:
        df = _load_trends_df()
        options = _load_trends_options(df)
    except (FileNotFoundError, ValueError) as exc:
        return jsonify({"error": str(exc)}), 500
    return jsonify(options)


@app.route("/trends-options")
def trends_options():
    return api_trends_options()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
