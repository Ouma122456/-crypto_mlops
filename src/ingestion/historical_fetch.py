# src/ingestion/historical_fetch.py

from binance.client import Client
import pandas as pd

API_KEY = ''  # optional
API_SECRET = ''
SYMBOL = 'BTCUSDT'
INTERVAL = '1m'  # 1-minute candles
LIMIT = 1000    # number of candles per request

client = Client(API_KEY, API_SECRET)

# Fetch historical klines
klines = client.get_klines(symbol=SYMBOL, interval=INTERVAL, limit=LIMIT)

# Convert to DataFrame
df = pd.DataFrame(klines, columns=[
    'open_time', 'open', 'high', 'low', 'close', 'volume',
    'close_time', 'quote_asset_volume', 'number_of_trades',
    'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
])

# Keep only relevant columns
df = df[['open_time', 'open', 'high', 'low', 'close', 'volume', 'close_time']]
df[['open','high','low','close','volume']] = df[['open','high','low','close','volume']].astype(float)

# Save locally
df.to_csv('data/raw/BTCUSDT_1m.csv', index=False)
print("Historical data saved to data/raw/BTCUSDT_1m.csv")
