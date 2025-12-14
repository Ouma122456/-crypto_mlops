# src/ingestion/binance_producer_ws.py
import json
import websocket
from kafka import KafkaProducer

SYMBOL = "btcusdt"
INTERVAL = "1m"
KAFKA_TOPIC = "btc_klines"
KAFKA_BOOTSTRAP = "localhost:9092"

producer = KafkaProducer(
    bootstrap_servers=KAFKA_BOOTSTRAP,
    value_serializer=lambda v: json.dumps(v).encode("utf-8")
)

def on_message(ws, message):
    data = json.loads(message)
    kline = data['k']
    record = {
        'symbol': SYMBOL.upper(),
        'start_time': kline['t'],
        'open': float(kline['o']),
        'high': float(kline['h']),
        'low': float(kline['l']),
        'close': float(kline['c']),
        'volume': float(kline['v']),
        'close_time': kline['T'],
        'is_final': kline['x']
    }
    producer.send(KAFKA_TOPIC, value=record)
    print(f"Sent: {record}")

def on_error(ws, error):
    print("Error:", error)

def on_close(ws, close_status_code, close_msg):
    print("Connection closed")

def on_open(ws):
    print("WebSocket connection opened")

# WebSocket endpoint for 1m Klines
url = f"wss://stream.binance.com:9443/ws/{SYMBOL}@kline_{INTERVAL}"

ws = websocket.WebSocketApp(url, on_open=on_open, on_message=on_message, on_error=on_error, on_close=on_close)
ws.run_forever()
