import app as app_module


def test_api_trends_empty_filters(monkeypatch, tmp_path):
    csv_path = tmp_path / "trends.csv"
    csv_path.write_text(
        "applicant_country,visa_type,year,month,processing_days\n"
        "United States,Work,2024,1,30\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(app_module, "TRENDS_DATA_PATH", str(csv_path))
    app_module._TRENDS_DATA_CACHE["df"] = None
    app_module._TRENDS_DATA_CACHE["mtime"] = None
    app_module._TRENDS_DATA_CACHE["path"] = None

    client = app_module.app.test_client()
    response = client.get("/api/trends?country=Canada")
    assert response.status_code == 200
    payload = response.get_json()

    assert payload["months"] == []
    assert payload["seasonal_avg_days"] == []
    assert payload["monthly_volume"] == []
    assert payload["country_labels"] == []
    assert payload["visa_type_labels"] == []
    assert payload["kpis"]["this_month_days"] == 0
    assert payload["kpis"]["avg_wait_days"] == 0
    assert payload["kpis"]["peak_season_label"] == ""
    assert payload["kpis"]["peak_delta_pct"] == 0
