# src/api/metrics.py
from prometheus_client import start_http_server, Counter, Histogram
import time
from fastapi import FastAPI

app = FastAPI()

# Metrics
REQUEST_COUNT = Counter(
    'crypto_api_requests_total', 'Total API requests', ['endpoint', 'method', 'status']
)
REQUEST_LATENCY = Histogram(
    'crypto_api_request_latency_seconds', 'Request latency', ['endpoint', 'method']
)

@app.get("/metrics")
def metrics():
    # Prometheus scrape endpoint
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
    from fastapi.responses import Response
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.get("/crypto")
def get_crypto():
    start_time = time.time()
    # your API logic here
    data = {"BTC": 30000, "ETH": 2000}
    latency = time.time() - start_time
    REQUEST_COUNT.labels(endpoint="/crypto", method="GET", status="200").inc()
    REQUEST_LATENCY.labels(endpoint="/crypto", method="GET").observe(latency)
    return data
