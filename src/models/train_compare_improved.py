# src/models/train_compare_improved.py

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression, Ridge
from xgboost import XGBRegressor
from math import sqrt
import joblib
import mlflow
import mlflow.sklearn

DATA_FILE = "data/processed/BTCUSDT_live.parquet"
MODEL_DIR = "models"

def load_data():
    df = pd.read_parquet(DATA_FILE)
    df['target'] = df['close'].shift(-1)
    df = df.dropna()
    X = df.drop(columns=['target', 'start_time', 'symbol', 'close_time'])
    y = df['target']
    return train_test_split(X, y, test_size=0.2, shuffle=False)

def evaluate_model(name, model, X_test, y_test):
    preds = model.predict(X_test)
    mse = mean_squared_error(y_test, preds)
    rmse = sqrt(mse)
    mae = mean_absolute_error(y_test, preds)
    r2 = r2_score(y_test, preds)
    print(f"✅ {name} done: RMSE={rmse:.4f}, R2={r2:.4f}, MAE={mae:.4f}")
    return rmse, r2, mae

def main():
    X_train, X_test, y_train, y_test = load_data()

    mlflow.set_experiment("BTC_price_models_improved")

    models = {
        "XGBoost": XGBRegressor(n_estimators=100, learning_rate=0.1, random_state=42),
        "RandomForest": RandomForestRegressor(n_estimators=100, random_state=42),
        "GradientBoosting": GradientBoostingRegressor(n_estimators=100, learning_rate=0.1, random_state=42),
        "LinearRegression": LinearRegression(),
        "Ridge": Ridge(alpha=1.0)
    }

    # Hyperparameter grids for tuning
    param_grids = {
        "XGBoost": {
            "n_estimators": [50, 100, 200],
            "learning_rate": [0.01, 0.05, 0.1],
            "max_depth": [3, 5, 7]
        },
        "RandomForest": {
            "n_estimators": [50, 100, 200],
            "max_depth": [None, 5, 10]
        },
        "GradientBoosting": {
            "n_estimators": [50, 100, 200],
            "learning_rate": [0.01, 0.05, 0.1],
            "max_depth": [3, 5, 7]
        },
        # LinearRegression and Ridge usually don't need grid search
    }

    for name, model in models.items():
        print(f"\nTraining {name}...")
        with mlflow.start_run(run_name=name):
            # Hyperparameter tuning if grid defined
            if name in param_grids:
                grid = GridSearchCV(model, param_grids[name], cv=3, scoring='neg_mean_squared_error', n_jobs=-1)
                grid.fit(X_train, y_train)
                best_model = grid.best_estimator_
            else:
                model.fit(X_train, y_train)
                best_model = model

            rmse, r2, mae = evaluate_model(name, best_model, X_test, y_test)

            # Save the model
            model_path = f"{MODEL_DIR}/{name}.pkl"
            joblib.dump(best_model, model_path)
            print(f"💾 Model saved → {model_path}")

            # Log to MLflow
            mlflow.log_param("model_name", name)
            mlflow.log_metrics({"RMSE": rmse, "R2": r2, "MAE": mae})
            mlflow.sklearn.log_model(best_model, artifact_path="model")

    print("\n🎉 Training completed! Run `mlflow ui` to visualize results.")

if __name__ == "__main__":
    main()
