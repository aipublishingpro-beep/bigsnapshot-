import streamlit as st
import pandas as pd
import numpy as np
import requests
from datetime import datetime, timedelta
import plotly.graph_objects as go

# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title="Politics Edge Finder | BigSnapshot",
    page_icon="🗳️",
    layout="wide"
)

# ============================================================
# CUSTOM CSS
# ============================================================
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stApp {background: linear-gradient(180deg, #0a0a0f 0%, #1a1a2e 100%);}
</style>
""", unsafe_allow_html=True)

# ============================================================
# KALSHI API
# ============================================================
KALSHI_BASE = "https://api.elections.kalshi.com/trade-api/v2"

def fetch_all_markets():
    """Fetch ALL markets from Kalshi and filter for politics"""
    all_markets = []
    cursor = None
    
    # Paginate through all markets
    for page in range(5):  # Max 5 pages = 1000 markets
        try:
            url = f"{KALSHI_BASE}/markets"
            params = {"status": "open", "limit": 200}
            if cursor:
                params["cursor"] = cursor
            
            response = requests.get(url, params=params, timeout=20)
            
            if response.status_code != 200:
                st.error(f"API Error: {response.status_code}")
                break
            
            data = response.json()
            markets = data.get("markets", [])
            all_markets.extend(markets)
            
            cursor = data.get("cursor")
            if not cursor:
                break
                
        except Exception as e:
            st.error(f"Request failed: {e}")
            break
    
    return all_markets

def filter_political_markets(markets):
    """Filter markets for political content"""
    keywords = [
        "congress", "senate", "house", "president", "governor", "election",
        "trump", "biden", "vance", "republican", "democrat", "shutdown",
        "impeach", "party", "primary", "midterm", "control", "majority",
        "gop", "dem", "ballot", "vote", "winner", "nominee"
    ]
    
    political = []
    for m in markets:
        title = m.get("title", "").lower()
        ticker = m.get("ticker", "").lower()
        
        if any(kw in title or kw in ticker for kw in keywords):
            # Normalize price
            m["yes_price"] = m.get("yes_bid") or m.get("yes_ask") or m.get("last_price") or 50
            political.append(m)
    
    # Sort by volume
    political.sort(key=lambda x: x.get("volume") or 0, reverse=True)
    return political[:20]

# ============================================================
# HEADER
# ============================================================
st.markdown("""
<div style="text-align: center; padding: 30px 0;">
    <h1 style="font-size: 42px; font-weight: 800; color: #fff; margin-bottom: 10px;">
        🗳️ Politics Edge Finder
    </h1>
    <p style="color: #888; font-size: 18px;">
        Live Kalshi Political Markets • Structural Analysis
    </p>
</div>
""", unsafe_allow_html=True)

# ============================================================
# HOW TO USE
# ============================================================
with st.expander("📖 How to Use This Tool", expanded=False):
    st.markdown("""
    **This is NOT a prediction tool.** Politics Edge Finder identifies when structural constraints have resolved outcomes before markets fully adjust.
    
    **🔒 Constraint Status**
    - **Locked (85%+):** Market strongly pricing one outcome. Limited paths remain.
    - **Leaning (70-84%):** Clear direction but uncertainty remains.
    - **Active (31-69%):** Multiple viable paths. High uncertainty.
    
    **📊 What to Look For**
    - Volume spikes after news events = market catching up
    - Price movement toward extremes = paths collapsing
    - Stale prices despite structural changes = opportunity
    
    **✅ How to Trade**
    1. Identify markets where structure has resolved but price lags
    2. Confirm with volume trend (rising = confirmation)
    3. Check chart for recent movement direction
    4. Enter before price fully adjusts to structural reality
    """)

# ============================================================
# FETCH DATA
# ============================================================
st.markdown("---")

# Show loading status
status_container = st.empty()
status_container.info("🔄 Fetching markets from Kalshi API...")

all_markets = fetch_all_markets()
status_container.empty()

# Debug info
with st.expander(f"🔧 Debug: {len(all_markets)} total markets fetched", expanded=False):
    if all_markets:
        st.write("Sample market keys:", list(all_markets[0].keys()))
        st.write("Sample titles:")
        for m in all_markets[:10]:
            st.write(f"- {m.get('title', 'N/A')}")

# Filter for political
markets = filter_political_markets(all_markets)

st.success(f"✅ Found {len(markets)} political markets")

if not markets:
    st.warning("No political markets found. This could mean:")
    st.write("- Kalshi has no open political markets right now")
    st.write("- The API is temporarily unavailable")
    st.write("- Keywords didn't match any titles")
    
    # Show demo data
    st.markdown("### 📊 Demo Data (for testing)")
    markets = [
        {"ticker": "DEMO-SENATE", "title": "Demo: Senate Control 2026", "yes_price": 58, "volume": 45000},
        {"ticker": "DEMO-HOUSE", "title": "Demo: House Control 2026", "yes_price": 75, "volume": 89000},
        {"ticker": "DEMO-SHUTDOWN", "title": "Demo: Government Shutdown Jan 2026", "yes_price": 24, "volume": 12000},
    ]

# ============================================================
# DISPLAY MARKETS
# ============================================================
st.markdown("### 🗳️ Political Markets")

for market in markets:
    ticker = market.get("ticker", "N/A")
    title = market.get("title", "Unknown")
    yes_price = market.get("yes_price", 50)
    no_price = 100 - yes_price
    volume = market.get("volume") or 0
    
    # Status
    if yes_price >= 85 or yes_price <= 15:
        status = "🔒 Locked"
        status_color = "#00c853"
    elif yes_price >= 70 or yes_price <= 30:
        status = "📊 Leaning"
        status_color = "#ffc107"
    else:
        status = "🔓 Active"
        status_color = "#888"
    
    # Edge calculation
    distance = abs(yes_price - 50) / 100
    edge = min(5.5, max(0.3, distance * 4 + np.log1p(volume) * 0.1))
    
    # Signal
    if edge >= 3.5:
        signal = "🟢 STRONG"
    elif edge >= 2.0:
        signal = "🟡 MODERATE"
    else:
        signal = "⚪ WEAK"
    
    # Card
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #1e1e2e 0%, #2a2a3e 100%); border-radius: 12px; padding: 20px; margin-bottom: 15px; border-left: 4px solid {status_color};">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px;">
            <span style="font-size: 16px; font-weight: 700; color: #fff;">{title}</span>
            <span style="background: #333; padding: 4px 12px; border-radius: 12px; font-size: 12px; color: #fff;">{signal}</span>
        </div>
        <div style="display: flex; gap: 30px; margin-top: 15px; flex-wrap: wrap;">
            <div>
                <p style="color: #888; font-size: 11px; margin: 0;">YES</p>
                <p style="color: #00c853; font-size: 18px; font-weight: 700; margin: 0;">{yes_price}¢</p>
            </div>
            <div>
                <p style="color: #888; font-size: 11px; margin: 0;">NO</p>
                <p style="color: #ff5252; font-size: 18px; font-weight: 700; margin: 0;">{no_price}¢</p>
            </div>
            <div>
                <p style="color: #888; font-size: 11px; margin: 0;">STATUS</p>
                <p style="color: #fff; font-size: 14px; margin: 0;">{status}</p>
            </div>
            <div>
                <p style="color: #888; font-size: 11px; margin: 0;">VOLUME</p>
                <p style="color: #fff; font-size: 14px; margin: 0;">${volume:,}</p>
            </div>
            <div>
                <p style="color: #888; font-size: 11px; margin: 0;">EDGE</p>
                <p style="color: #00c853; font-size: 14px; margin: 0;">+{edge:.1f}%</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Kalshi link (real markets only)
    if not ticker.startswith("DEMO"):
        st.markdown(f"[View on Kalshi →](https://kalshi.com/markets?search={ticker})")

# ============================================================
# REFRESH
# ============================================================
st.markdown("---")
col1, col2, col3 = st.columns([1, 1, 1])
with col2:
    if st.button("🔄 Refresh Markets", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# ============================================================
# FOOTER
# ============================================================
st.markdown("""
<div style="text-align: center; padding: 30px; color: #666;">
    <p style="font-size: 12px;">
        ⚠️ Structural analysis only. Not financial advice.
    </p>
    <p style="font-size: 11px; color: #555;">
        BigSnapshot © 2026 | Data from Kalshi Public API
    </p>
</div>
""", unsafe_allow_html=True)
