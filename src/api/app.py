# src/api/app.py
import os
import time
import asyncio
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse
import uvicorn
from prometheus_client import Counter, Histogram, make_asgi_app
import random

app = FastAPI(title="Crypto Live Prediction API", version="1.0")

# ----------------------------
# Prometheus metrics
# ----------------------------
REQUEST_COUNT = Counter("api_requests_total", "Total API Requests", ["endpoint"])
REQUEST_LATENCY = Histogram("api_request_latency_seconds", "Request latency in seconds", ["endpoint"])

@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    import time
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    REQUEST_COUNT.labels(endpoint=request.url.path).inc()
    REQUEST_LATENCY.labels(endpoint=request.url.path).observe(duration)
    return response

# ----------------------------
# Simulated model
# ----------------------------
def predict_latest():
    """
    Simulate a dynamic prediction.
    Replace this with your actual model inference later.
    """
    price = 87000 + random.uniform(-500, 500)  # dynamic price
    probability = random.uniform(0.3, 0.9)
    label = "UP" if probability > 0.5 else "DOWN"

    return {
        "price": round(price, 2),
        "prediction": 1 if label == "UP" else 0,
        "prediction_label": label,
        "probability": round(probability, 2),
        "timestamp": int(time.time())  # UNIX timestamp in seconds
    }

# ----------------------------
# Health endpoint
# ----------------------------
@app.get("/health")
async def health():
    return {"status": "ok"}

# ----------------------------
# Single prediction
# ----------------------------
@app.get("/predict")
async def predict():
    """
    Return a single, immediate prediction (latest candle)
    """
    try:
        result = predict_latest()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return JSONResponse(result)

# ----------------------------
# Streaming predictions (SSE)
# ----------------------------
async def event_generator(interval_seconds: float = 1.0):
    """
    Async generator for Server-Sent Events.
    Yields a JSON line every `interval_seconds`.
    """
    while True:
        try:
            result = predict_latest()
            yield f"data: {result}\n\n"
        except Exception as e:
            yield f"data: {{'error':'{str(e)}'}}\n\n"
        await asyncio.sleep(interval_seconds)

@app.get("/stream")
async def stream(interval: float = 1.0):
    """
    Stream live predictions as Server-Sent Events (SSE).
    Example: /stream?interval=1.0
    """
    return StreamingResponse(event_generator(interval), media_type="text/event-stream")

# ----------------------------
# Prometheus /metrics endpoint
# ----------------------------
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# ----------------------------
# Run the app
# ----------------------------
if __name__ == "__main__":
    uvicorn.run(
        "src.api.app:app",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8000, )),
        reload=True
    )
