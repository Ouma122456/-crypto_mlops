import pytest
from fastapi import status
from httpx import AsyncClient, ASGITransport
from src.api.app import app, predict_latest

# ----------------------------
# Test /health
# ----------------------------
@pytest.mark.asyncio
async def test_health_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        response = await ac.get("/health")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"status": "ok"}

# ----------------------------
# Test /predict
# ----------------------------
@pytest.mark.asyncio
async def test_predict_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        response = await ac.get("/predict")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    expected_keys = {"price", "prediction", "prediction_label", "probability", "timestamp"}
    assert expected_keys.issubset(data.keys())
    assert data["prediction"] in [0, 1]
    assert data["prediction_label"] in ["UP", "DOWN"]
    assert 0.0 <= data["probability"] <= 1.0

# ----------------------------
# Test /stream (SSE) with max_events
# ----------------------------
@pytest.mark.asyncio
async def test_stream_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        response = await ac.get("/stream", params={"interval": 0.01, "max_events": 3})
        content = await response.aread()
        lines = content.decode().splitlines()
    assert any(line.startswith("data: ") for line in lines)

# ----------------------------
# Test predict_latest function
# ----------------------------
def test_predict_latest_function():
    result = predict_latest()
    expected_keys = {"price", "prediction", "prediction_label", "probability", "timestamp"}
    assert expected_keys.issubset(result.keys())
    assert result["prediction"] in [0, 1]
    assert result["prediction_label"] in ["UP", "DOWN"]
    assert 0.0 <= result["probability"] <= 1.0
