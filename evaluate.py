import joblib
import os

MODEL_PATH = "models/final_model.pkl"

if not os.path.exists(MODEL_PATH):
    raise FileNotFoundError("Final model not found")

model_bundle = joblib.load(MODEL_PATH)

print("Evaluation OK – model loaded successfully")
