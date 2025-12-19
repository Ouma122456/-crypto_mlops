# =====================================
# kafka_consumer_stream.py (FINAL FIXED + SAFE HEARTBEAT)
# =====================================

import os
import json
import pandas as pd
import numpy as np
from kafka import KafkaConsumer
from src.processing.transforms import add_features_realtime
import joblib
from sklearn.metrics import precision_score
import mlflow
from dotenv import load_dotenv
from datetime import datetime   # ✅ SAFE ADDITION

# --------------------------
# Config
# --------------------------
KAFKA_TOPIC = "btc_klines"
KAFKA_BOOTSTRAP = "localhost:9092"
HISTORICAL_FILE = "data/raw/BTCUSDT_1m.csv"
OUTPUT_FILE = "data/processed/BTCUSDT_live.parquet"
MODELS_DIR = "models"
os.makedirs("data/processed", exist_ok=True)

MIN_ROWS_FOR_PREDICTION = 20
LOG_BATCH_SIZE = 10

# ✅ SAFE ADDITION (heartbeat file)
STREAM_HEARTBEAT_FILE = "data/stream_heartbeat.txt"

# --------------------------
# Load historical data
# --------------------------
if os.path.exists(HISTORICAL_FILE):
    df = pd.read_csv(HISTORICAL_FILE)
    print(f"Loaded historical data → {len(df)} rows")
else:
    print("⚠️ No historical CSV found, starting empty.")
    df = pd.DataFrame(columns=[
        "symbol","start_time","open","high","low","close","volume","close_time"
    ])

float_cols = ["open","high","low","close","volume"]
for col in float_cols:
    df[col] = pd.to_numeric(df[col], errors="coerce")

# =====================================
# Load ONLY the final model
# =====================================
MODEL_PATH = os.path.join(MODELS_DIR, "final_model.pkl")

print(f"Loading final model from {MODEL_PATH} ...")
model = joblib.load(MODEL_PATH)

models = {"final_model": model}

# Expected features
if hasattr(model, "feature_names_in_"):
    model_features = {"final_model": list(model.feature_names_in_)}
else:
    model_features = {
        "final_model": [
            "HL_range","OC_change","OC_pct_change","candle_body","candle_direction",
            "upper_shadow","lower_shadow","volume_ratio","price_change_5",
            "MA_5","MA_10","EMA_10","VWAP"
        ]
    }

print("✅ Loaded final model successfully.")

# =====================================
# MLflow setup
# =====================================
load_dotenv()
USER = os.getenv("DAGSHUB_USERNAME")
REPO = os.getenv("DAGSHUB_REPO_NAME")
TOKEN = os.getenv("DAGSHUB_TOKEN")
EXPERIMENT_NAME = "crypto_candle_prediction"

if USER and REPO:
    remote_uri = f"https://dagshub.com/{USER}/{REPO}.mlflow"
    os.environ["MLFLOW_TRACKING_USERNAME"] = USER
    os.environ["MLFLOW_TRACKING_PASSWORD"] = TOKEN
    mlflow.set_tracking_uri(remote_uri)
else:
    local_uri = os.path.abspath("mlruns").replace("\\", "/")
    mlflow.set_tracking_uri(f"file:///{local_uri}")

mlflow.set_experiment(EXPERIMENT_NAME)

# =====================================
# Kafka consumer
# =====================================
consumer = KafkaConsumer(
    KAFKA_TOPIC,
    bootstrap_servers=KAFKA_BOOTSTRAP,
    auto_offset_reset="latest",
    enable_auto_commit=True,
    value_deserializer=lambda m: json.loads(m.decode("utf-8"))
)
print("📡 Listening to Kafka topic...")

# =====================================
# Metric logging
# =====================================
def log_streaming_metrics(y_true, y_pred, df_returns, model_name):
    df_returns = pd.Series(df_returns)
    y_true = np.array(y_true)
    y_pred = np.array(y_pred)

    DA = np.mean(y_true == y_pred)
    precision_up = precision_score(y_true, y_pred, pos_label=1, zero_division=0)
    precision_down = precision_score(y_true, y_pred, pos_label=0, zero_division=0)

    pnl = np.sum(df_returns.shift(-1).fillna(0) * (2*y_pred - 1))

    mlflow.log_metrics({
        f"{model_name}_DA": DA,
        f"{model_name}_PnL": pnl,
        f"{model_name}_Precision_Up": precision_up,
        f"{model_name}_Precision_Down": precision_down
    })

    print(f"📊 {model_name} → DA={DA:.4f}, PnL={pnl:.2f}")
    print("Prediction distribution:", np.bincount(y_pred))

# =====================================
# Buffers
# =====================================
predictions_buffers = {"final_model": []}
y_trues = []
returns_list = []

# =====================================
# Main Streaming Loop
# =====================================
with mlflow.start_run(run_name="streaming_session"):
    for message in consumer:
        record = message.value

        # Process only final ticks
        if not record.get("is_final", False):
            continue

        # ✅ SAFE HEARTBEAT (proves streaming, no logic impact)
        with open(STREAM_HEARTBEAT_FILE, "w") as f:
            f.write(f"Last streamed event at: {datetime.utcnow().isoformat()}\n")

        # Convert to DF
        new_df = pd.DataFrame([record])
        for col in float_cols:
            new_df[col] = pd.to_numeric(new_df[col], errors="coerce")

        # Append
        df = pd.concat([df, new_df], ignore_index=True)
        df.drop_duplicates(subset=["start_time"], keep="last", inplace=True)

        # Recompute features
        df = add_features_realtime(df)

        # Save latest parquet
        df.to_parquet(OUTPUT_FILE, index=False, compression="snappy")
        print(f"Updated → {OUTPUT_FILE} ({len(df)} rows)")

        # Wait for enough data
        if len(df) < MIN_ROWS_FOR_PREDICTION:
            print(f"⌛ Waiting for at least {MIN_ROWS_FOR_PREDICTION} rows...")
            continue

        # True label
        y_true = 1 if df["close"].iloc[-1] > df["close"].iloc[-2] else 0
        y_trues.append(y_true)

        # Returns
        returns_list.append(df["OC_pct_change"].iloc[-1] / 100)

        # =====================================
        # Prediction
        # =====================================
        expected = model_features["final_model"]
        X_live = df[expected].iloc[-1:].astype(float)

        y_pred = model.predict(X_live)

        if not np.array_equal(np.unique(y_pred), [0, 1]):
            y_pred = (y_pred > 0.5).astype(int)

        predictions_buffers["final_model"].append(y_pred[0])

        # =====================================
        # Batch logging
        # =====================================
        if len(predictions_buffers["final_model"]) >= LOG_BATCH_SIZE:
            log_streaming_metrics(
                y_trues,
                predictions_buffers["final_model"],
                returns_list,
                "final_model"
            )
            predictions_buffers["final_model"].clear()

        if len(y_trues) >= LOG_BATCH_SIZE:
            y_trues.clear()
            returns_list.clear()
