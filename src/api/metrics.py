# src/api/metrics.py
from fastapi import FastAPI, Request
from fastapi.responses import Response
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST, CollectorRegistry

app = FastAPI(title="Crypto Metrics API")

# ----------------------------
# Prometheus registry and metrics
# ----------------------------
registry = CollectorRegistry()

REQUEST_COUNT = Counter(
    'crypto_api_requests_total',
    'Total API requests',
    ['endpoint', 'method', 'status'],
    registry=registry
)

REQUEST_LATENCY = Histogram(
    'crypto_api_request_latency_seconds',
    'Request latency in seconds',
    ['endpoint', 'method'],
    registry=registry,
    buckets=[0.01, 0.05, 0.1, 0.5, 1, 2]
)

PRED_UP = Counter(
    'crypto_predictions_up_total',
    'Total UP predictions',
    registry=registry
)

PRED_DOWN = Counter(
    'crypto_predictions_down_total',
    'Total DOWN predictions',
    registry=registry
)

# ----------------------------
# Middleware for metrics
# ----------------------------
@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    # Skip metrics endpoint itself
    if request.url.path.startswith("/metrics"):
        return await call_next(request)

    import time
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time

    REQUEST_COUNT.labels(
        endpoint=request.url.path,
        method=request.method,
        status=response.status_code
    ).inc()

    REQUEST_LATENCY.labels(
        endpoint=request.url.path,
        method=request.method
    ).observe(duration)

    return response

# ----------------------------
# Metrics endpoint
# ----------------------------
@app.get("/metrics")
def metrics():
    return Response(generate_latest(registry), media_type=CONTENT_TYPE_LATEST)

# ----------------------------
# Example endpoint: /crypto
# ----------------------------
import random
import time as t

@app.get("/crypto")
def get_crypto():
    start_time = t.time()
    # Simulated crypto prediction
    price = 87000 + random.uniform(-500, 500)
    probability = random.uniform(0.3, 0.9)
    label = "UP" if probability > 0.5 else "DOWN"
    if label == "UP":
        PRED_UP.inc()
    else:
        PRED_DOWN.inc()

    latency = t.time() - start_time
    REQUEST_LATENCY.labels(endpoint="/crypto", method="GET").observe(latency)
    REQUEST_COUNT.labels(endpoint="/crypto", method="GET", status="200").inc()

    return {
        "price": round(price, 2),
        "prediction_label": label,
        "probability": round(probability, 2),
        "timestamp": int(t.time())
    }
