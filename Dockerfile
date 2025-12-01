# Dockerfile (Prometheus + FastAPI + Kafka + ML libs)
FROM python:3.11-slim

# Set environment
ENV PYTHONUNBUFFERED=1
WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y build-essential curl gcc --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt /app/requirements.txt
RUN pip install --default-timeout=100 --no-cache-dir -r /app/requirements.txt

# Install ML libraries
RUN pip install --no-cache-dir lightgbm xgboost catboost

# Install Prometheus client
RUN pip install --no-cache-dir prometheus_client

# Copy application code
COPY src /app/src

# Copy models and data
COPY models /models
COPY data /data

# Expose port
EXPOSE 8000

# Environment variables
ENV MODELS_DIR=/models
ENV PARQUET_PATH=/data/processed/BTCUSDT_live.parquet
ENV KAFKA_BOOTSTRAP_SERVERS=host.docker.internal:9092

# Run FastAPI app
CMD ["uvicorn", "src.api.app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
