# crypto_dashboard.py
import streamlit as st
import requests
import pandas as pd
import time

st.set_page_config(page_title="Crypto Live Dashboard", layout="wide")
st.title("🚀 Crypto Live Prediction Dashboard")

# Correct API endpoint
API_PREDICT = "http://api:8000/predict"

# Sidebar settings
update_interval = st.sidebar.slider("Update interval (seconds)", 1, 10, 2)
show_graph = st.sidebar.checkbox("Show live chart", value=True)

# Placeholders
latest_placeholder = st.empty()
chart_placeholder = st.empty()

# Initialize session state for history
if "history" not in st.session_state:
    st.session_state.history = []

# Main loop
while True:
    try:
        resp = requests.get(API_PREDICT, timeout=5)
        data = resp.json()

        # Convert timestamp properly
        timestamp = pd.to_datetime(float(data["timestamp"]), unit="ms")

        # Add to history
        st.session_state.history.append({
            "timestamp": timestamp,
            "price": data["price"],
            "prediction": 1 if data["prediction_label"] == "UP" else 0,
            "probability": data["probability"]
        })

        # Display latest prediction
        latest_placeholder.markdown(
            f"**Price:** {data['price']}\n\n"
            f"**Prediction:** {data['prediction_label']}\n\n"
            f"**Probability:** {data['probability']:.2f}\n\n"
            f"**Timestamp:** {timestamp}"
        )

        # Plot history chart
        if show_graph and len(st.session_state.history) > 1:
            df = pd.DataFrame(st.session_state.history).set_index("timestamp")
            chart_placeholder.line_chart(df[["price", "probability"]])

        time.sleep(update_interval)

    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching prediction: {e}")
        time.sleep(update_interval)
