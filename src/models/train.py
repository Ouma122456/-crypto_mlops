# =====================================
# train.py - Crypto OHLCV Time-Series
# =====================================

import os
import pandas as pd
import numpy as np
from datetime import datetime
from sklearn.model_selection import RandomizedSearchCV
from sklearn.ensemble import RandomForestClassifier, StackingClassifier, VotingClassifier
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier
from catboost import CatBoostClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import precision_score
import mlflow
from dotenv import load_dotenv
from scipy.stats import randint, uniform
from mlflow.models.signature import infer_signature

from src.processing.transforms import add_features  # feature engineering

# --------------------------
# Load .env
# --------------------------
load_dotenv()
DAGSHUB_USERNAME = os.getenv("DAGSHUB_USERNAME")
DAGSHUB_REPO = os.getenv("DAGSHUB_REPO_NAME")
DAGSHUB_TOKEN = os.getenv("DAGSHUB_TOKEN")

EXPERIMENT_NAME = "crypto_candle_prediction"

# --------------------------
# MLflow Tracking Setup
# --------------------------
def setup_mlflow():
    if DAGSHUB_USERNAME and DAGSHUB_REPO:
        remote_uri = f"https://dagshub.com/{DAGSHUB_USERNAME}/{DAGSHUB_REPO}.mlflow"

        try:
            os.environ["MLFLOW_TRACKING_USERNAME"] = DAGSHUB_USERNAME
            os.environ["MLFLOW_TRACKING_PASSWORD"] = DAGSHUB_TOKEN

            mlflow.set_tracking_uri(remote_uri)

            try:
                mlflow.set_experiment(EXPERIMENT_NAME)
            except Exception:
                mlflow.create_experiment(EXPERIMENT_NAME)
                mlflow.set_experiment(EXPERIMENT_NAME)

            print("✅ Connected to DagsHub MLflow")
            print("Tracking URI:", remote_uri)
            return

        except Exception as e:
            print("⚠️ Failed to connect to DagsHub:", e)

    # Local fallback
    local_uri = os.path.abspath("mlruns").replace("\\", "/")
    mlflow.set_tracking_uri(f"file:///{local_uri}")

    try:
        mlflow.set_experiment(EXPERIMENT_NAME)
    except Exception:
        mlflow.create_experiment(EXPERIMENT_NAME)

    print("⚠️ Using local MLflow tracking instead")
    print("Local URI:", f"file:///{local_uri}")

setup_mlflow()

# --------------------------
# Helper Metrics
# --------------------------
def calculate_time_series_metrics(y_true, y_pred, df_returns):
    DA = np.mean(y_true == y_pred)
    precision_up = precision_score(y_true, y_pred, pos_label=1)
    precision_down = precision_score(y_true, y_pred, pos_label=0)
    returns_shifted = df_returns.shift(-1).fillna(0)
    pnl = np.sum(returns_shifted * (2 * y_pred - 1))
    return {
        "DA": DA,
        "Precision_Up": precision_up,
        "Precision_Down": precision_down,
        "PnL": pnl
    }

# --------------------------
# MLflow Model Logger
# --------------------------
def log_model_mlflow(model, name, stage, metrics, duration, params=None):
    with mlflow.start_run(run_name=f"{name}_{stage}"):

        mlflow.log_params(params or {})
        mlflow.log_metrics(metrics)
        mlflow.log_metric("duration_s", duration)

        input_example = X_test.iloc[:1]

        try:
            pred = model.predict(X_test.iloc[:1])
            signature = infer_signature(X_test, pred)
        except:
            signature = None

        mlflow.sklearn.log_model(
            model,
            artifact_path=name,
            input_example=input_example,
            signature=signature
        )

# --------------------------
# Load Dataset
# --------------------------
df = pd.read_csv("data/processed/BTCUSDT_live.csv")

# Apply feature engineering
df = add_features(df)

# Define target
df["target"] = np.where(df["close"].shift(-1) > df["close"], 1, 0)  # 1 = up, 0 = down

# Features
features = [
    "HL_range", "OC_change", "OC_pct_change", "candle_body",
    "candle_direction", "upper_shadow", "lower_shadow",
    "volume_ratio", "price_change_5", "MA_5", "MA_10", "EMA_10", "VWAP"
]

X = df[features].astype(float)
y = df["target"]

returns = df["OC_pct_change"] / 100

split_idx = int(0.8 * len(df))
X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]
returns_test = returns.iloc[split_idx:]

print(f"Data split: {len(X_train)} train / {len(X_test)} test")

# --------------------------
# Baseline Models
# --------------------------
baseline_models = {
    "RandomForest": RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1),
    "XGBoost": XGBClassifier(n_estimators=100, random_state=42, n_jobs=-1, eval_metric="logloss"),
    "LightGBM": LGBMClassifier(n_estimators=100, random_state=42, n_jobs=-1, verbose=-1),
    "CatBoost": CatBoostClassifier(iterations=100, random_state=42, verbose=0)
}

trained_models = {}

print("\n🚀 Training baseline models...\n")
for name, model in baseline_models.items():
    start = datetime.now()
    model.fit(X_train, y_train)
    pred = model.predict(X_test)
    metrics = calculate_time_series_metrics(y_test, pred, returns_test)
    duration = (datetime.now() - start).total_seconds()
    log_model_mlflow(model, name, "baseline", metrics, duration)
    trained_models[name] = model
    print(f"{name}: DA={metrics['DA']:.4f}, PnL={metrics['PnL']:.2f}, {duration:.1f}s")

# --------------------------
# Hyperparameter Tuning
# --------------------------
param_space = {
    "RandomForest": {"n_estimators": randint(100, 300), "max_depth": randint(10, 25)},
    "XGBoost": {"n_estimators": randint(100, 300), "max_depth": randint(3, 8), "learning_rate": uniform(0.01, 0.2)},
    "LightGBM": {"n_estimators": randint(80,150), "max_depth": randint(3,6), "learning_rate": uniform(0.02, 0.1)},
    "CatBoost": {"iterations": randint(100, 200), "depth": randint(4, 7), "learning_rate": uniform(0.01, 0.1)}
}

print("\n🔍 Hyperparameter tuning...\n")

for name in baseline_models.keys():
    print(f"Tuning {name}...")
    search = RandomizedSearchCV(
        baseline_models[name],
        param_space[name],
        n_iter=5,
        cv=3,
        n_jobs=-1,
        random_state=42,
        verbose=0
    )
    start = datetime.now()
    search.fit(X_train, y_train)
    best_model = search.best_estimator_
    trained_models[name + "_tuned"] = best_model
    pred = best_model.predict(X_test)
    metrics = calculate_time_series_metrics(y_test, pred, returns_test)
    duration = (datetime.now() - start).total_seconds()
    log_model_mlflow(best_model, name, "tuned", metrics, duration, search.best_params_)
    print(f"→ {name}_tuned: DA={metrics['DA']:.4f}  PnL={metrics['PnL']:.2f}")

# --------------------------
# Ensembles
# --------------------------
estimators = [
    ("rf", trained_models["RandomForest_tuned"]),
    ("xgb", trained_models["XGBoost_tuned"]),
    ("lgbm", trained_models["LightGBM_tuned"]),
    ("cat", trained_models["CatBoost_tuned"])
]

print("\n📊 Stacking...")
stacker = StackingClassifier(
    estimators, final_estimator=LogisticRegression(), n_jobs=-1
)
start = datetime.now()
stacker.fit(X_train, y_train)
pred = stacker.predict(X_test)
metrics = calculate_time_series_metrics(y_test, pred, returns_test)
duration = (datetime.now() - start).total_seconds()
log_model_mlflow(stacker, "Stacking", "ensemble", metrics, duration)
print(f"Stacking: DA={metrics['DA']:.4f}, PnL={metrics['PnL']:.2f}")

print("\n📊 Voting...")
voter = VotingClassifier(estimators, voting="soft", n_jobs=-1)
start = datetime.now()
voter.fit(X_train, y_train)
pred = voter.predict(X_test)
metrics = calculate_time_series_metrics(y_test, pred, returns_test)
duration = (datetime.now() - start).total_seconds()
log_model_mlflow(voter, "Voting", "ensemble", metrics, duration)
print(f"Voting: DA={metrics['DA']:.4f}, PnL={metrics['PnL']:.2f}")

# --------------------------
# Save final model for streaming
# --------------------------
import joblib
os.makedirs("models", exist_ok=True)
joblib.dump(voter, "models/final_model.pkl")
print("\n✅ Training finished and model saved to models/final_model.pkl")
