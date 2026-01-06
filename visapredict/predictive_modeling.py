import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import warnings
warnings.filterwarnings('ignore')

# Load the cleaned and feature-engineered dataset
df = pd.read_csv('visapredict/visa_eda_features.csv')

# Target column
target_column = 'processing_days'

# Separate features and target
# Select only numeric columns for features
numeric_cols = df.select_dtypes(include=[np.number]).columns
X = df[numeric_cols].drop(columns=[target_column])
y = df[target_column]

# Split the dataset into training and testing sets (80-20 split)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Impute missing values
imputer = SimpleImputer(strategy='mean')
X_train = imputer.fit_transform(X_train)
X_test = imputer.transform(X_test)

# Initialize models
models = {
    'Linear Regression': LinearRegression(),
    'Random Forest Regressor': RandomForestRegressor(random_state=42),
    'Gradient Boosting Regressor': GradientBoostingRegressor(random_state=42)
}

# Dictionary to store evaluation results
results = {}

# Train and evaluate each model
for name, model in models.items():
    # Train the model
    model.fit(X_train, y_train)
    
    # Make predictions
    y_pred = model.predict(X_test)
    
    # Calculate metrics
    mae = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    r2 = r2_score(y_test, y_pred)
    
    # Store results
    results[name] = {'MAE': mae, 'RMSE': rmse, 'R²': r2}

# Display evaluation results in a table
print("Model Evaluation Results:")
print("-" * 50)
print(f"{'Model':<25} {'MAE':<10} {'RMSE':<10} {'R²':<10}")
print("-" * 50)
for model, metrics in results.items():
    print(f"{model:<25} {metrics['MAE']:<10.4f} {metrics['RMSE']:<10.4f} {metrics['R²']:<10.4f}")
print("-" * 50)

# Select the best-performing model based on lowest MAE and RMSE
# We'll use MAE as the primary metric for selection
best_model_name = min(results, key=lambda x: results[x]['MAE'])
best_model = models[best_model_name]
print(f"\nBest model selected: {best_model_name}")

# Perform hyperparameter tuning on the selected model using GridSearchCV
if best_model_name == 'Linear Regression':
    # Linear Regression has no hyperparameters to tune, skip tuning
    tuned_model = best_model
    print("Linear Regression has no hyperparameters to tune.")
else:
    if best_model_name == 'Random Forest Regressor':
        param_grid = {
            'n_estimators': [100, 200, 300],
            'max_depth': [None, 10, 20],
            'min_samples_split': [2, 5, 10]
        }
    elif best_model_name == 'Gradient Boosting Regressor':
        param_grid = {
            'n_estimators': [100, 200, 300],
            'learning_rate': [0.01, 0.1, 0.2],
            'max_depth': [3, 5, 7]
        }
    
    grid_search = GridSearchCV(estimator=best_model, param_grid=param_grid, cv=5, scoring='neg_mean_absolute_error', n_jobs=-1)
    grid_search.fit(X_train, y_train)
    tuned_model = grid_search.best_estimator_
    print(f"Best parameters for {best_model_name}: {grid_search.best_params_}")

# Re-evaluate the tuned model
tuned_model.fit(X_train, y_train)
y_pred_tuned = tuned_model.predict(X_test)

mae_tuned = mean_absolute_error(y_test, y_pred_tuned)
rmse_tuned = np.sqrt(mean_squared_error(y_test, y_pred_tuned))
r2_tuned = r2_score(y_test, y_pred_tuned)

print("\nTuned Model Final Metrics:")
print("-" * 30)
print(f"MAE: {mae_tuned:.4f}")
print(f"RMSE: {rmse_tuned:.4f}")
print(f"R²: {r2_tuned:.4f}")
