import pandas as pd
df = pd.read_parquet("data/processed/BTCUSDT_live.parquet")
print(df.tail())
