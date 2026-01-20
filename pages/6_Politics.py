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
# BASIC PASSWORD GATE (BETA ONLY)
# ============================================================
def gate():
    if "ok" not in st.session_state:
        st.session_state.ok = False
    if st.session_state.ok:
        return True

    st.markdown("## 🗳️ Politics Super Edge")
    pw = st.text_input("Beta access", type="password")
    if st.button("Enter"):
        if pw == "beta":
            st.session_state.ok = True
            st.rerun()
        else:
            st.error("Invalid")
    return False

if not gate():
    st.stop()

# ============================================================
# KALSHI PUBLIC API
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

    out = []
    for m in markets:
        title = m.get("title", "").lower()
        if any(k in title for k in keywords):
            out.append(m)
    return out[:25]

@st.cache_data(ttl=600)
def get_history(ticker):
    end = int(datetime.utcnow().timestamp())
    start = int((datetime.utcnow() - timedelta(days=21)).timestamp())
    r = requests.get(
        f"{BASE}/markets/{ticker}/candlesticks",
        params={"start_ts": start, "end_ts": end, "period_interval": 1440},
        timeout=10
    )
    if r.status_code != 200:
        return []
    return r.json().get("candlesticks", [])

# ============================================================
# SUPER EDGE LOGIC (HIDDEN MECHANICS)
# ============================================================
def super_edge(market):
    yes = market.get("yes_price", 50) / 100
    vol = market.get("volume", 0)

    # Layer 1: Structural distance
    structural = abs(yes - 0.5) * 5

    # Layer 2: Attention pressure
    attention = np.log1p(vol) * 0.08

    edge = structural + attention
    return round(min(max(edge, 0.5), 6.0), 1)

def constraint_label(price):
    if price >= 85 or price <= 15:
        return "LOCKED"
    if price >= 70 or price <= 30:
        return "LEANING"
    return "ACTIVE"

# ============================================================
# UI HEADER
# ============================================================
st.markdown("""
# 🗳️ Politics Super Edge  
**Structural market pressure • not predictions**
""")

# ============================================================
# LOAD MARKETS
# ============================================================
with st.spinner("Loading live markets…"):
    markets = get_markets()

if not markets:
    st.warning("No markets available.")
    st.stop()

# ============================================================
# MARKET CARDS
# ============================================================
for m in markets:
    ticker = m["ticker"]
    title = m.get("title", "Unknown")
    yes = m.get("yes_price", 50)
    no = 100 - yes
    vol = m.get("volume", 0)

    edge = super_edge(m)
    status = constraint_label(yes)

    st.markdown(f"""
    ---
    ### {title}
    **YES:** {yes}¢ | **NO:** {no}¢  
    **Volume:** ${vol:,}  
    **Constraint:** {status}  
    **Super Edge:** +{edge}%
    """)

    with st.expander("📈 Price history"):
        hist = get_history(ticker)
        if hist:
            df = pd.DataFrame(hist)
            df["t"] = pd.to_datetime(df["end_period_ts"], unit="s")
            df["p"] = df["close_price"]

            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=df["t"],
                y=df["p"],
                mode="lines",
                line=dict(width=2)
            ))
            fig.update_layout(
                height=250,
                margin=dict(l=0, r=0, t=20, b=0),
                yaxis_title="YES price (¢)",
                xaxis_title=""
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No history available.")

    st.markdown(f"[View on Kalshi →](https://kalshi.com/markets/{ticker})")

# ============================================================
# FOOTER
# ============================================================
st.caption(
    "BigSnapshot © 2026 — Structural market analysis only. "
    "No predictions. No political messaging."
)
