import streamlit as st
import requests
import pandas as pd
import altair as alt

# -------------------------
# Streamlit page config
# -------------------------
st.set_page_config(page_title="Crypto Live Dashboard", layout="wide")

st.title("🚀 Crypto Live Prediction Dashboard")
st.markdown("Real-time predictions coming from your Kubernetes API.")

# -------------------------
# API Endpoint
# -------------------------
API_URL = "http://localhost:30000/predict"

# -------------------------
# Sidebar settings
# -------------------------
st.sidebar.header("Settings")
refresh_rate = st.sidebar.slider("Refresh every (seconds)", 0.5, 10.0, 2.0, 0.5)

# Automatically refresh page
st_autorefresh = st.experimental_rerun

st.experimental_set_query_params(updated="true")
st_autorefresh = st.autorefresh(interval=int(refresh_rate * 1000), key="data_refresh")

# -------------------------
# Session State Init
# -------------------------
if "history" not in st.session_state:
    st.session_state.history = []

# -------------------------
# Fetch latest prediction
# -------------------------
def fetch_latest():
    try:
        response = requests.get(API_URL, timeout=5)
        data = response.json()
        return data
    except Exception as e:
        return {"error": str(e)}

data = fetch_latest()

# -------------------------
# Display Latest Prediction
# -------------------------
latest_box = st.container()
with latest_box:
    st.subheader("📌 Latest Prediction")

    if "error" in data:
        st.error(f"API Error: {data['error']}")
    else:
        st.write(f"**Price:** {data.get('price')}")
        st.write(f"**Prediction:** {data.get('prediction_label')}")
        st.write(f"**Probability:** {data.get('probability')}")
        st.write(f"**Timestamp:** {data.get('timestamp')}")

        # Append to history
        st.session_state.history.append({
            "timestamp": pd.Timestamp.now(),
            "price": data.get("price"),
            "prediction": 1 if data.get("prediction_label") == "UP" else 0,
            "probability": data.get("probability")
        })

# -------------------------
# Convert to DataFrame
# -------------------------
df = pd.DataFrame(st.session_state.history)

# -------------------------
# Display History Table
# -------------------------
st.subheader("📋 Prediction History")
st.dataframe(df.tail(50), use_container_width=True)

# -------------------------
# Line Chart: Prediction over Time
# -------------------------
if len(df) > 2:
    st.subheader("📈 Prediction Trend")

    chart_pred = (
        alt.Chart(df)
        .mark_line(point=True)
        .encode(
            x="timestamp:T",
            y="prediction:Q",
            tooltip=["timestamp:T", "prediction:Q"]
        )
        .properties(height=300)
    )

    st.altair_chart(chart_pred, use_container_width=True)

# -------------------------
# Line Chart: Price over Time
# -------------------------
if len(df) > 2:
    st.subheader("💰 Price Trend")

    chart_price = (
        alt.Chart(df)
        .mark_line(point=True)
        .encode(
            x="timestamp:T",
            y="price:Q",
            tooltip=["timestamp:T", "price:Q"]
        )
        .properties(height=300)
    )

    st.altair_chart(chart_price, use_container_width=True)
