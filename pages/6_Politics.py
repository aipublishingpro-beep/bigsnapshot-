import streamlit as st
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go

# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title="Politics Super Edge | BigSnapshot",
    page_icon="🗳️",
    layout="wide"
)

# ============================================================
# HEADER
# ============================================================
st.markdown("""
# 🗳️ Politics Super Edge
Structural market pressure — **not predictions**
""")

st.caption("Public beta • Free live data • No login")

# ============================================================
# KALSHI PUBLIC API (NO AUTH)
# ============================================================
BASE = "https://api.elections.kalshi.com/trade-api/v2"

@st.cache_data(ttl=300)
def get_markets():
    r = requests.get(
        f"{BASE}/markets",
        params={"status": "open", "limit": 200},
        timeout=10
    )
    if r.status_code != 200:
        return []

    markets = r.json().get("markets", [])

    keywords = [
        "election", "senate", "president", "congress",
        "governor", "supreme", "fed", "vote", "primary"
    ]

    filtered = []
    for m in markets:
        title = m.get("title", "").lower()
        if any(k in title for k in keywords):
            filtered.append(m)

    return filtered[:25]

@st.cache_data(ttl=600)
def get_history(ticker):
    end_ts = int(datetime.utcnow().timestamp())
    start_ts = int((datetime.utcnow() - timedelta(days=21)).timestamp())

    r = requests.get(
        f"{BASE}/markets/{ticker}/candlesticks",
        params={
            "start_ts": start_ts,
            "end_ts": end_ts,
            "period_interval": 1440
        },
        timeout=10
    )

    if r.status_code != 200:
        return []

    return r.json().get("candlesticks", [])

# ============================================================
# SUPER EDGE LOGIC (INTERNAL)
# ============================================================
def super_edge(market):
    yes_price = market.get("yes_price", 50) / 100
    volume = market.get("volume", 0)

    structural = abs(yes_price - 0.5) * 5
    attention = np.log1p(volume) * 0.08

    edge = structural + attention
    edge = min(max(edge, 0.5), 6.0)

    return round(edge, 1)

def constraint_label(price):
    if price >= 85 or price <= 15:
        return "LOCKED"
    if price >= 70 or price <= 30:
        return "LEANING"
    return "ACTIVE"

# ============================================================
# LOAD MARKETS
# ============================================================
with st.spinner("Loading live political markets…"):
    markets = get_markets()

if not markets:
    st.warning("No political markets available right now.")
    st.stop()

# ============================================================
# MARKET CARDS
# ============================================================
for m in markets:
    ticker = m["ticker"]
    title = m.get("title", "Unknown Market")
    yes = m.get("yes_price", 50)
    no = 100 - yes
    volume = m.get("volume", 0)

    edge = super_edge(m)
    status = constraint_label(yes)

    st.markdown("---")
    st.subheader(title)

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("YES", f"{yes}¢")
    col2.metric("NO", f"{no}¢")
    col3.metric("Volume", f"${volume:,}")
    col4.metric("Constraint", status)
    col5.metric("Super Edge", f"+{edge}%")

    with st.expander("📈 Price history"):
        history = get_history(ticker)
        if history:
            df = pd.DataFrame(history)
            df["date"] = pd.to_datetime(df["end_period_ts"], unit="s")
            df["price"] = df["close_price"]

            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=df["date"],
                y=df["price"],
                mode="lines",
                line=dict(width=2)
            ))

            fig.update_layout(
                height=260,
                margin=dict(l=0, r=0, t=20, b=0),
                yaxis_title="YES price (¢)",
                xaxis_title=""
            )

            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No historical data available.")

    st.markdown(f"[View on Kalshi →](https://kalshi.com/markets/{ticker})")

# ============================================================
# FOOTER
# ============================================================
st.markdown("---")
st.caption(
    "BigSnapshot © 2026 • Structural analysis only • "
    "Not financial or political advice"
)
