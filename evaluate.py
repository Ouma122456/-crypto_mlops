import mlflow
from mlflow.tracking import MlflowClient
import os
import sys

EXPERIMENT_NAME = "crypto_candle_prediction"
METRIC_NAME = "DA"

client = MlflowClient()

experiment = client.get_experiment_by_name(EXPERIMENT_NAME)
if experiment is None:
    print("Experiment not found")
    sys.exit(0)

runs = client.search_runs(
    experiment_ids=[experiment.experiment_id],
    order_by=["attributes.start_time DESC"],
    max_results=2
)

if len(runs) < 2:
    print("Not enough runs to compare")
    sys.exit(0)

latest = runs[0].data.metrics.get(METRIC_NAME)
previous = runs[1].data.metrics.get(METRIC_NAME)

print(f"Latest DA: {latest}")
print(f"Previous DA: {previous}")

if latest < previous:
    print("Performance regression detected")
    sys.exit(1)   # IMPORTANT
else:
    print("Model performance improved or stable")
    sys.exit(0)
