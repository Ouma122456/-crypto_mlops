# src/api/app.py
import time
import random
import asyncio
from fastapi import FastAPI, HTTPException, Request, Query
from fastapi.responses import JSONResponse, StreamingResponse
from prometheus_client import Counter, Histogram, make_asgi_app

app = FastAPI(title="Crypto Live Prediction API", version="1.1")

# Prometheus metrics
REQUEST_COUNT = Counter("api_requests_total", "Total API Requests", ["endpoint", "status"])
REQUEST_LATENCY = Histogram("api_request_latency_seconds", "Request latency in seconds", ["endpoint"], buckets=[0.01, 0.05, 0.1, 0.5, 1, 2])
PRED_UP = Counter("crypto_predictions_up_total", "Total UP predictions")
PRED_DOWN = Counter("crypto_predictions_down_total", "Total DOWN predictions")

# Middleware for metrics
@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    if request.url.path.startswith("/metrics"):
        return await call_next(request)
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    REQUEST_COUNT.labels(endpoint=request.url.path, status=response.status_code).inc()
    REQUEST_LATENCY.labels(endpoint=request.url.path).observe(duration)
    return response

# Simulated prediction
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
        "timestamp": int(time.time() * 1000)  # milliseconds
    }

# Endpoints
@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/predict")
async def predict():
    try:
        return JSONResponse(predict_latest())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Streaming predictions (SSE)
async def event_generator(interval_seconds: float = 1.0, max_events: int = None):
    count = 0
    while True:
        yield f"data: {predict_latest()}\n\n"
        count += 1
        if max_events and count >= max_events:
            break
        await asyncio.sleep(interval_seconds)

@app.get("/stream")
async def stream(interval: float = 1.0, max_events: int = Query(None, ge=1)):
    return StreamingResponse(event_generator(interval, max_events), media_type="text/event-stream")

# Prometheus /metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# Background task for demo metrics
async def generate_metrics_periodically():
    while True:
        predict_latest()
        await asyncio.sleep(1)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(generate_metrics_periodically())

# Run
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.api.app:app", host="0.0.0.0", port=8000, reload=True)
