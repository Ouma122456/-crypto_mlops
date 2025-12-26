import os
import sys
import mlflow
from mlflow.tracking import MlflowClient
from dotenv import load_dotenv

# --------------------------
# MLflow setup (MUST match training)
# --------------------------
load_dotenv()

DAGSHUB_USERNAME = os.getenv("DAGSHUB_USERNAME")
DAGSHUB_REPO = os.getenv("DAGSHUB_REPO_NAME")
DAGSHUB_TOKEN = os.getenv("DAGSHUB_TOKEN")

EXPERIMENT_NAME = "crypto_candle_prediction"
METRIC_NAME = "DA"

if DAGSHUB_USERNAME and DAGSHUB_REPO:
    remote_uri = f"https://dagshub.com/{DAGSHUB_USERNAME}/{DAGSHUB_REPO}.mlflow"
    os.environ["MLFLOW_TRACKING_USERNAME"] = DAGSHUB_USERNAME
    os.environ["MLFLOW_TRACKING_PASSWORD"] = DAGSHUB_TOKEN
    mlflow.set_tracking_uri(remote_uri)
else:
    print("MLflow credentials missing")
    sys.exit(0)

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
    sys.exit(1)
else:
    print("Model performance improved or stable")
    sys.exit(0)
