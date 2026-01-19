# VisaPredictAI
AI-powered system that predicts visa processing time using ML and a Flask API, with a modern frontend dashboard.

## Setup
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

## Run
```bash
python app.py
```

App routes:
- http://127.0.0.1:5000/
- http://127.0.0.1:5000/estimator
- http://127.0.0.1:5000/results
- http://127.0.0.1:5000/trends

## Tests
```bash
pytest -q
```

## Notes
- Model artifacts are created on first run and saved to the `model/` directory.
- The prediction API is available at `POST /predict`.
