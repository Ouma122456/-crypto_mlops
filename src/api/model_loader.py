# src/api/model_loader.py
import os
import time
import joblib
import pandas as pd
import numpy as np

MODELS_DIR = os.environ.get("MODELS_DIR", "models")
MODEL_FILENAME = os.environ.get("MODEL_FILENAME", "final_model.pkl")
FEATURES_FILENAME = os.environ.get("FEATURES_FILENAME", "features_list.pkl")
PARQUET_PATH = os.environ.get("PARQUET_PATH", "data/processed/BTCUSDT_live.parquet")

_model = None
_features = None

def load_model():
    global _model, _features
    if _model is None:
        model_path = os.path.join(MODELS_DIR, MODEL_FILENAME)
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model not found at {model_path}")
        _model = joblib.load(model_path)

    if _features is None:
        features_path = os.path.join(MODELS_DIR, FEATURES_FILENAME)
        if not os.path.exists(features_path):
            # fallback feature list
            _features = [
                "HL_range","OC_change","OC_pct_change","candle_body","candle_direction",
                "upper_shadow","lower_shadow","volume_ratio","price_change_5",
                "MA_5","MA_10","EMA_10","VWAP"
            ]
        else:
            _features = joblib.load(features_path)
    return _model, _features

def read_latest_parquet(parquet_path=None):
    path = parquet_path or PARQUET_PATH
    if not os.path.exists(path):
        raise FileNotFoundError(f"Parquet file not found: {path}")
    # read parquet and return as DataFrame
    df = pd.read_parquet(path)
    return df

def make_prediction_from_df(df, model=None, features=None):
    """
    df: full dataframe (must contain feature columns and close)
    returns dict: {price, prediction, proba (if available), timestamp}
    """
    if df is None or len(df) == 0:
        raise ValueError("Empty dataframe provided")

    model, features = load_model() if (model is None or features is None) else (model, features)

    # ensure features available
    missing = [f for f in features if f not in df.columns]
    if missing:
        # try to compute missing columns gracefully by filling with 0
        for c in missing:
            df[c] = 0.0

    latest = df.iloc[-1:].copy()
    # ensure numeric conversion
    for col in features:
        latest[col] = pd.to_numeric(latest[col], errors="coerce").fillna(0.0)

    X = latest[features].astype(float)

    # If model is a pipeline wrapped with scaler etc, predict directly
    y_pred = model.predict(X)

    # prediction to int 0/1
    try:
        # if it's continuous (regressor or numeric float array)
        if getattr(y_pred, "dtype", None) is not None and y_pred.dtype.kind in "fc":
            y_pred_bin = int((y_pred > 0.5).astype(int).ravel()[0])
        else:
            y_pred_bin = int(np.array(y_pred).ravel()[0])
    except Exception:
        y_pred_bin = int(np.array(y_pred).ravel()[0])

    proba = None
    # try predict_proba if available
    try:
        if hasattr(model, "predict_proba"):
            proba_arr = model.predict_proba(X)
            # probability for class 1
            proba = float(proba_arr.ravel()[-1])
    except Exception:
        proba = None

    result = {
        "price": float(latest["close"].iloc[0]) if "close" in latest.columns else None,
        "prediction": int(y_pred_bin),
        "prediction_label": "UP" if y_pred_bin == 1 else "DOWN",
        "probability": proba,
        "timestamp": str(latest["start_time"].iloc[0]) if "start_time" in latest.columns else str(pd.Timestamp.now())
    }
    return result

def predict_latest(parquet_path=None):
    model, features = load_model()
    df = read_latest_parquet(parquet_path)
    return make_prediction_from_df(df, model=model, features=features)
