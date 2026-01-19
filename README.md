# AI Enabled Visa Status Prediction and Processing Time Estimator (VisaPredictAI)

## 1. Project Overview
Visa applicants often face long waiting times with limited visibility into how long their applications may take. This project addresses that uncertainty by applying machine learning to historical visa processing data. The system analyzes applicant country, visa type, processing office, and seasonal factors to estimate processing times and present them through a web-based dashboard. The result is a transparent, data-driven estimator that improves planning for applicants and stakeholders.

## 2. Features
- AI-based visa processing time prediction
- Estimated time range with confidence framing
- Trend analysis by visa type, country, and season
- User-friendly web interface for inputs and results
- Data-driven transparency based on historical patterns

## 3. System Architecture
End-to-end flow: User submits inputs in the web UI, the frontend sends the request to the Flask backend API, input data is validated and preprocessed, features are prepared and passed to the ML model, the prediction is generated, and the UI renders the estimated days and ranges. Technologies: HTML/CSS templates for the frontend, Flask for API routing and server rendering, pandas and NumPy for data preparation, scikit-learn for model inference, and joblib for model artifact loading.

## 4. Milestones & Timeline (8 Weeks)
Milestone 1 (Weeks 1�2): Data Collection & Preprocessing
- Objective: Build a reliable dataset for modeling visa processing times.
- Dataset collection: Gather public or create synthetic visa processing records with country, visa type, office, and timelines.
- Data cleaning steps: Remove duplicates, normalize country and visa labels, and standardize date fields.
- Handling missing values: Impute numeric features using mean/median and apply consistent defaults for categorical fields.
- Encoding categorical variables: Use target averages or encoded features suitable for regression models.
- Generating target variable: Compute processing time in days as the modeling target.

Milestone 2 (Weeks 3�4): Exploratory Data Analysis & Feature Engineering
- Exploratory analysis with visualizations: Inspect distributions and identify outliers.
- Identifying seasonal and regional trends: Analyze month-by-month and country-level differences.
- Correlation analysis: Evaluate relationships between features and processing time.
- Feature engineering: Create month and season features, and aggregate country-level averages.

Milestone 3 (Weeks 5�6): Predictive Modeling
- Models used: Linear Regression, Random Forest, Gradient Boosting.
- Model training and evaluation: Train on historical data with consistent splits.
- Performance metrics: MAE, RMSE, R^2 to compare accuracy and stability.
- Best model selection and tuning: Choose the model with the best trade-off between accuracy and interpretability.

Milestone 4 (Weeks 7�8): Web App Development & Deployment
- Frontend implementation: Flask templates with responsive HTML/CSS.
- Backend API development using Flask: Input validation, prediction endpoint, and trends endpoint.
- ML model integration: Load model artifacts and run predictions on demand.
- End-to-end testing with sample inputs: Validate UI, API, and prediction consistency.
- Deployment readiness: Containerization or deployment on AWS, Azure, or Heroku.

## 5. Technology Stack
- Programming Language: Python
- Libraries and frameworks: Flask, pandas, NumPy
- ML tools: scikit-learn, joblib
- Visualization tools: HTML/CSS-based dashboards with computed trend data
- Deployment tools: Local Flask server with cloud deployment readiness

## 6. Installation & Setup
- Prerequisites: Python 3.10 or later, pip
- Virtual environment setup: `python -m venv venv`
- Activate environment (Windows): `venv\Scripts\activate`
- Activate environment (macOS/Linux): `source venv/bin/activate`
- Dependency installation: `pip install -r requirements.txt`
- Dataset and model setup: Ensure `visapredict/visa_eda_features.csv` exists; model artifacts are generated on first run and saved in `model/`.

## 7. Running the Application
- Start backend server: `python app.py`
- Access the web app: `http://127.0.0.1:5000/`
- Available routes/pages: `/`, `/estimator`, `/results`, `/trends`, `/health`

## 8. API Endpoints
- POST `/predict`: Returns a processing time estimate and range.
- Request format: JSON with `visa_type`, `applicant_country`, `destination_country`, `processing_office`, `submission_date` (YYYY-MM-DD).
- Response format: JSON with `predicted_days`, `range_min`, `range_max`, `model_name`, and `note`.
- Example payload: `{ "visa_type": "Student", "applicant_country": "India", "destination_country": "USA", "processing_office": "New Del![1768826451793](image/README/1768826451793.png)![1768826455043](image/README/1768826455043.png)![1768826456318](image/README/1768826456318.png)![1768826459091](image/README/1768826459091.png)![1768826468507](image/README/1768826468507.png)![1768826469782](image/README/1768826469782.png)![1768826488474](image/README/1768826488474.png)![1768826599192](image/README/1768826599192.png)hi", "submission_date": "2024-07-12" }`.

## 9. Testing
- End-to-end testing approach: Validate API responses, UI rendering, and prediction outputs using sample inputs.
- Sample test cases: Missing required fields, invalid date format, and valid prediction request.
- Validation of predictions and UI: Confirm returned ranges and UI presentation align with expectations.

## 10. Future Enhancements
- Real-time data integration from official visa processing feeds
- Explainable AI improvements for decision transparency
- Mobile app version for applicants on the go
- Expanded coverage for more visa categories and countries

## 11. Conclusion
VisaPredictAI demonstrates how AI and machine learning can reduce uncertainty in visa processing by delivering structured, data-driven estimates. The project combines predictive modeling with a practical web interface to improve planning and transparency for applicants and decision makers.
