from app import app


def test_predict_endpoint():
    client = app.test_client()
    payload = {
        "visa_type": "Student",
        "applicant_country": "India",
        "destination_country": "USA",
        "processing_office": "New Delhi",
        "submission_date": "2025-12-15",
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == 200
    data = response.get_json()
    for key in ["predicted_days", "range_min", "range_max", "model_name", "note"]:
        assert key in data
    assert isinstance(data["predicted_days"], (int, float))
    assert isinstance(data["range_min"], (int, float))
    assert isinstance(data["range_max"], (int, float))
    assert data["range_min"] <= data["predicted_days"] <= data["range_max"]
