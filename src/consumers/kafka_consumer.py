import json
import pandas as pd
from kafka import KafkaConsumer
import os
from src.processing.transforms import add_features_realtime

# --- CONFIG ---
KAFKA_TOPIC = "btc_klines"
KAFKA_BOOTSTRAP = "localhost:9092"
HISTORICAL_FILE = "data/raw/BTCUSDT_1m.csv"
OUTPUT_FILE = "data/processed/BTCUSDT_live.parquet"

os.makedirs("data/processed", exist_ok=True)

# --- Load historical data ---
if os.path.exists(HISTORICAL_FILE):
    df = pd.read_csv(HISTORICAL_FILE)
else:
    df = pd.DataFrame(columns=[
        "symbol", "start_time", "open", "high", "low", "close", "volume", "close_time"
    ])

# Assure correct types
float_cols = ["open","high","low","close","volume"]
for col in float_cols:
    df[col] = pd.to_numeric(df[col], errors="coerce")

# --- Kafka Consumer ---
consumer = KafkaConsumer(
    KAFKA_TOPIC,
    bootstrap_servers=KAFKA_BOOTSTRAP,
    auto_offset_reset="latest",
    enable_auto_commit=True,
    value_deserializer=lambda m: json.loads(m.decode("utf-8"))
)

print("Listening to Kafka topic...")

for message in consumer:
    record = message.value
    new_df = pd.DataFrame([record])

    # Convert types
    for col in float_cols:
        new_df[col] = pd.to_numeric(new_df[col], errors="coerce")

    # Append to main df and drop duplicates
    df = pd.concat([df, new_df], ignore_index=True)
    df.drop_duplicates(subset=["start_time"], keep="last", inplace=True)

    # Apply real-time feature engineering
    df = add_features_realtime(df)

    # Save parquet every update
    df.to_parquet(OUTPUT_FILE, index=False, compression="snappy")
    print(f"Updated → {OUTPUT_FILE} ({len(df)} rows)")
