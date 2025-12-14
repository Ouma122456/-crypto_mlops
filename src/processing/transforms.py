import pandas as pd
import numpy as np

# ===========================
# 1) Training feature engineering
# ===========================
def add_features(df: pd.DataFrame) -> pd.DataFrame:

    df = df.copy()

    df["HL_range"] = df["high"] - df["low"]
    df["OC_change"] = df["close"] - df["open"]
    df["OC_pct_change"] = (df["close"] - df["open"]) / df["open"] * 100
    df["candle_body"] = df["OC_change"].abs()
    df["candle_direction"] = df["OC_change"].apply(lambda x: 1 if x > 0 else -1)

    df["upper_shadow"] = df["high"] - df[["open","close"]].max(axis=1)
    df["lower_shadow"] = df[["open","close"]].min(axis=1) - df["low"]

    df["volume_ratio"] = df["volume"] / df["volume"].rolling(5).mean()

    df["price_change_5"] = df["close"] - df["close"].shift(5)

    df["MA_5"] = df["close"].rolling(5).mean()
    df["MA_10"] = df["close"].rolling(10).mean()
    df["EMA_10"] = df["close"].ewm(span=10, adjust=False).mean()

    vwap_window = df["volume"].rolling(5).mean()
    df["VWAP"] = ((df["high"] + df["low"] + df["close"]) / 3) * df["volume"] / vwap_window

    df.fillna(method="bfill", inplace=True)
    df.fillna(method="ffill", inplace=True)

    return df



# ===========================
# 2) REAL-TIME feature engineering (Kafka)
# ===========================
def add_features_realtime(df: pd.DataFrame) -> pd.DataFrame:
    df = df.sort_values("start_time").copy()

    df["HL_range"] = df["high"] - df["low"]
    df["OC_change"] = df["close"] - df["open"]
    df["OC_pct_change"] = (df["close"] - df["open"]) / df["open"] * 100
    df["candle_body"] = df["OC_change"].abs()
    df["candle_direction"] = (df["close"] > df["open"]).astype(int) * 2 - 1

    df["upper_shadow"] = df["high"] - df[["open","close"]].max(axis=1)
    df["lower_shadow"] = df[["open","close"]].min(axis=1) - df["low"]

    # Safe rolling
    df["volume_ratio"] = df["volume"] / df["volume"].rolling(5, min_periods=1).mean()
    df["price_change_5"] = df["close"] - df["close"].shift(1)  # safer for first rows
    df["MA_5"] = df["close"].rolling(5, min_periods=1).mean()
    df["MA_10"] = df["close"].rolling(10, min_periods=1).mean()
    df["EMA_10"] = df["close"].ewm(span=10, adjust=False).mean()

    vol_roll = df["volume"].rolling(5, min_periods=1).mean()
    df["VWAP"] = ((df["high"] + df["low"] + df["close"]) / 3) * df["volume"] / vol_roll

    # Fill missing values instead of dropping rows
    df.bfill(inplace=True)
    df.ffill(inplace=True)


    return df

