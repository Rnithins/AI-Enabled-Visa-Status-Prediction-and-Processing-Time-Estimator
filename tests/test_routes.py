from app import app


def test_routes():
    client = app.test_client()
    for path in ["/", "/estimator", "/trends"]:
        response = client.get(path)
        assert response.status_code == 200
