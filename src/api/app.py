import os
import time
import asyncio
from fastapi import FastAPI, HTTPException, Request, Query
from fastapi.responses import JSONResponse, StreamingResponse
import uvicorn
from prometheus_client import Counter, Histogram, make_asgi_app
import random

app = FastAPI(title="Crypto Live Prediction API", version="1.1")

# ----------------------------
# Prometheus metrics
# ----------------------------

REQUEST_COUNT = Counter(
    "api_requests_total",
    "Total API Requests",
    ["endpoint", "status"]
)

REQUEST_LATENCY = Histogram(
    "api_request_latency_seconds",
    "Request latency in seconds",
    ["endpoint"],
    buckets=[0.01, 0.05, 0.1, 0.5, 1, 2]
)

PRED_UP = Counter("crypto_predictions_up_total", "Total UP predictions")
PRED_DOWN = Counter("crypto_predictions_down_total", "Total DOWN predictions")

@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    status = response.status_code
    REQUEST_COUNT.labels(endpoint=request.url.path, status=status).inc()
    REQUEST_LATENCY.labels(endpoint=request.url.path).observe(duration)
    return response

# ----------------------------
# Simulated model
# ----------------------------
def predict_latest():
    price = 87000 + random.uniform(-500, 500)
    probability = random.uniform(0.3, 0.9)
    label = "UP" if probability > 0.5 else "DOWN"
    if label == "UP":
        PRED_UP.inc()
    else:
        PRED_DOWN.inc()
    return {
        "price": round(price, 2),
        "prediction": 1 if label == "UP" else 0,
        "prediction_label": label,
        "probability": round(probability, 2),
        "timestamp": int(time.time())
    }

# ----------------------------
# Endpoints
# ----------------------------
@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/predict")
async def predict():
    try:
        result = predict_latest()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return JSONResponse(result)

# Streaming predictions (SSE) with optional max_events for testing
async def event_generator(interval_seconds: float = 1.0, max_events: int = None):
    count = 0
    while True:
        try:
            result = predict_latest()
            yield f"data: {result}\n\n"
        except Exception as e:
            yield f"data: {{'error':'{str(e)}'}}\n\n"
        count += 1
        if max_events is not None and count >= max_events:
            break
        await asyncio.sleep(interval_seconds)

@app.get("/stream")
async def stream(interval: float = 1.0, max_events: int = Query(None, ge=1)):
    return StreamingResponse(event_generator(interval, max_events), media_type="text/event-stream")

# ----------------------------
# Prometheus /metrics endpoint
# ----------------------------
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# ----------------------------
# Run
# ----------------------------
if __name__ == "__main__":
    uvicorn.run(
        "src.api.app:app",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8000)),
        reload=True
    )
