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
import joblib

from src.processing.transforms import add_features

# -------------------------- Config --------------------------
load_dotenv()
DAGSHUB_USERNAME = os.getenv("DAGSHUB_USERNAME")
DAGSHUB_REPO = os.getenv("DAGSHUB_REPO_NAME")
DAGSHUB_TOKEN = os.getenv("DAGSHUB_TOKEN")
EXPERIMENT_NAME = "crypto_candle_prediction"

DATA_FILE = "data/processed/BTCUSDT_live.csv"
MODELS_DIR = "models"
os.makedirs(MODELS_DIR, exist_ok=True)

# -------------------------- MLflow setup --------------------------
def setup_mlflow():
    if DAGSHUB_USERNAME and DAGSHUB_REPO:
        uri = f"https://dagshub.com/{DAGSHUB_USERNAME}/{DAGSHUB_REPO}.mlflow"
        os.environ["MLFLOW_TRACKING_USERNAME"] = DAGSHUB_USERNAME
        os.environ["MLFLOW_TRACKING_PASSWORD"] = DAGSHUB_TOKEN
        mlflow.set_tracking_uri(uri)
        mlflow.set_experiment(EXPERIMENT_NAME)
    else:
        mlflow.set_tracking_uri("file:///mlruns")
        mlflow.set_experiment(EXPERIMENT_NAME)

setup_mlflow()

# -------------------------- Load & preprocess --------------------------
df = pd.read_csv(DATA_FILE)
df = add_features(df)
df["target"] = np.where(df["close"].shift(-1) > df["close"], 1, 0)

features = [
    "HL_range","OC_change","OC_pct_change","candle_body","candle_direction",
    "upper_shadow","lower_shadow","volume_ratio","price_change_5",
    "MA_5","MA_10","EMA_10","VWAP"
]

X = df[features].astype(float)
y = df["target"]
returns = df["OC_pct_change"] / 100

split = int(0.8 * len(df))
X_train, X_test = X.iloc[:split], X.iloc[split:]
y_train, y_test = y.iloc[:split], y.iloc[split:]
returns_test = returns.iloc[split:]

# -------------------------- Helpers --------------------------
def calculate_metrics(y_true, y_pred, returns):
    return {
        "DA": np.mean(y_true == y_pred),
        "Precision_Up": precision_score(y_true, y_pred, pos_label=1),
        "Precision_Down": precision_score(y_true, y_pred, pos_label=0),
        "PnL": np.sum(returns.shift(-1).fillna(0) * (2 * y_pred - 1))
    }

def log_model_mlflow(model, name, stage, metrics, duration, params=None):
    with mlflow.start_run(run_name=f"{name}_{stage}"):
        mlflow.log_params(params or {})
        mlflow.log_metrics(metrics)
        mlflow.log_metric("duration_s", duration)
    joblib.dump(model, f"{MODELS_DIR}/{name}_{stage}.pkl")

def print_results(name, stage, metrics):
    print(
        f"{name} ({stage}) | "
        f"DA={metrics['DA']:.4f} | "
        f"PnL={metrics['PnL']:.2f} | "
        f"Precision_Up={metrics['Precision_Up']:.4f} | "
        f"Precision_Down={metrics['Precision_Down']:.4f}"
    )

# -------------------------- Baseline models --------------------------
baseline_models = {
    "RandomForest": RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1),
    "XGBoost": XGBClassifier(n_estimators=100, random_state=42, n_jobs=-1, eval_metric="logloss"),
    "LightGBM": LGBMClassifier(n_estimators=100, random_state=42, n_jobs=-1, verbose=-1),
    "CatBoost": CatBoostClassifier(iterations=100, random_state=42, verbose=0)
}

trained = {}

for name, model in baseline_models.items():
    start = datetime.now()
    model.fit(X_train, y_train)
    pred = model.predict(X_test)
    metrics = calculate_metrics(y_test, pred, returns_test)
    duration = (datetime.now() - start).total_seconds()
    log_model_mlflow(model, name, "baseline", metrics, duration)
    print_results(name, "baseline", metrics)
    trained[name] = model

# -------------------------- Hyperparameter tuning --------------------------
param_space = {
    "RandomForest": {"n_estimators": randint(100, 300), "max_depth": randint(10, 25)},
    "XGBoost": {"n_estimators": randint(100, 300), "max_depth": randint(3, 8), "learning_rate": uniform(0.01, 0.2)},
    "LightGBM": {"n_estimators": randint(80, 150), "max_depth": randint(3, 6), "learning_rate": uniform(0.02, 0.1)}
}

for name in ["RandomForest", "XGBoost", "LightGBM"]:
    search = RandomizedSearchCV(
        baseline_models[name], param_space[name], n_iter=5, cv=3, n_jobs=-1
    )
    start = datetime.now()
    search.fit(X_train, y_train)
    best = search.best_estimator_
    pred = best.predict(X_test)
    metrics = calculate_metrics(y_test, pred, returns_test)
    duration = (datetime.now() - start).total_seconds()
    log_model_mlflow(best, name, "tuned", metrics, duration, search.best_params_)
    print_results(name, "tuned", metrics)
    trained[f"{name}_tuned"] = best

# -------------------------- CatBoost tuned --------------------------
start = datetime.now()
cat = CatBoostClassifier(iterations=150, depth=6, learning_rate=0.05, verbose=0, random_state=42)
cat.fit(X_train, y_train)
pred = cat.predict(X_test)
metrics = calculate_metrics(y_test, pred, returns_test)
duration = (datetime.now() - start).total_seconds()
log_model_mlflow(cat, "CatBoost", "tuned", metrics, duration)
print_results("CatBoost", "tuned", metrics)
trained["CatBoost_tuned"] = cat

# -------------------------- Ensembles --------------------------
estimators = [
    ("rf", trained["RandomForest_tuned"]),
    ("xgb", trained["XGBoost_tuned"]),
    ("lgb", trained["LightGBM_tuned"])
]

# Stacking
stacker = StackingClassifier(estimators=estimators, final_estimator=LogisticRegression(), n_jobs=-1)
stacker.fit(X_train, y_train)
pred = stacker.predict(X_test)
metrics = calculate_metrics(y_test, pred, returns_test)
log_model_mlflow(stacker, "Stacking", "ensemble", metrics, 0)
print_results("Stacking", "ensemble", metrics)

# Voting
voter = VotingClassifier(
    estimators=estimators + [("cat", trained["CatBoost_tuned"])],
    voting="soft",
    n_jobs=-1
)
voter.fit(X_train, y_train)
pred = voter.predict(X_test)
metrics = calculate_metrics(y_test, pred, returns_test)
log_model_mlflow(voter, "Voting", "ensemble", metrics, 0)
print_results("Voting", "ensemble", metrics)

joblib.dump(voter, f"{MODELS_DIR}/final_model.pkl")
print("Final ensemble model saved")
