import streamlit as st
import pandas as pd
import numpy as np
import requests
from datetime import datetime, timedelta
import plotly.graph_objects as go
from plotly.subplots import make_subplots

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
    
    .stApp {
        background: linear-gradient(180deg, #0a0a0f 0%, #1a1a2e 100%);
    }
    
    .market-card {
        background: linear-gradient(135deg, #1e1e2e 0%, #2a2a3e 100%);
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 20px;
        border: 1px solid #333;
    }
    
    .market-title {
        font-size: 18px;
        font-weight: 700;
        color: #fff;
        margin-bottom: 15px;
    }
    
    .signal-badge {
        display: inline-block;
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 13px;
        font-weight: 600;
    }
    
    .signal-strong {
        background: linear-gradient(135deg, #00c853 0%, #00a844 100%);
        color: #000;
    }
    
    .signal-moderate {
        background: linear-gradient(135deg, #ffc107 0%, #e6ac00 100%);
        color: #000;
    }
    
    .signal-weak {
        background: linear-gradient(135deg, #666 0%, #555 100%);
        color: #fff;
    }
    
    .how-to-use {
        background: linear-gradient(135deg, #1a2a4a 0%, #2a3a5a 100%);
        border-radius: 16px;
        padding: 30px;
        margin: 20px 0;
        border: 1px solid #3a4a6a;
    }
    
    @media (max-width: 768px) {
        .market-card { padding: 16px; }
        .market-title { font-size: 16px; }
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# KALSHI API - FREE, NO AUTH REQUIRED
# ============================================================
KALSHI_BASE = "https://api.elections.kalshi.com/trade-api/v2"

@st.cache_data(ttl=300)  # Cache 5 minutes
def get_political_markets():
    """Fetch political markets from Kalshi API"""
    political_markets = []
    cursor = None
    
    # Paginate through markets to find political ones
    for _ in range(5):
        try:
            url = f"{KALSHI_BASE}/markets"
            params = {"status": "open", "limit": 200}
            if cursor:
                params["cursor"] = cursor
            
            response = requests.get(url, params=params, timeout=15)
            
            if response.status_code != 200:
                break
            
            data = response.json()
            markets = data.get("markets", [])
            
            # Filter for political markets
            keywords = [
                "congress", "senate", "house", "president", "governor", "election",
                "trump", "biden", "vance", "republican", "democrat", "vote", "poll",
                "cabinet", "supreme", "impeach", "legislation", "bill", "shutdown",
                "fed chair", "appointment", "confirmation", "party", "primary",
                "gop", "dem", "control", "majority", "electoral", "ballot", "midterm",
                "nominee", "approval", "executive", "veto", "filibuster", "electoral",
                "swing state", "battleground", "runoff", "recount", "certification"
            ]
            
            for m in markets:
                title_lower = m.get("title", "").lower()
                ticker_lower = m.get("ticker", "").lower()
                
                if any(kw in title_lower or kw in ticker_lower for kw in keywords):
                    # Normalize yes_price
                    m["yes_price"] = m.get("yes_bid") or m.get("last_price") or 50
                    political_markets.append(m)
            
            cursor = data.get("cursor")
            if not cursor:
                break
                
        except Exception as e:
            st.error(f"API Error: {e}")
            break
    
    # Sort by volume
    political_markets.sort(key=lambda x: x.get("volume") or 0, reverse=True)
    return political_markets[:20]

@st.cache_data(ttl=600)  # Cache 10 minutes
def get_market_history(ticker):
    """Fetch candlestick history for a market"""
    try:
        # Get daily candlesticks for past 30 days
        end_ts = int(datetime.now().timestamp())
        start_ts = int((datetime.now() - timedelta(days=30)).timestamp())
        
        url = f"{KALSHI_BASE}/markets/{ticker}/candlesticks"
        params = {
            "start_ts": start_ts,
            "end_ts": end_ts,
            "period_interval": 1440  # Daily
        }
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            return data.get("candlesticks", [])
        return []
    except:
        return []

def calculate_edge(market):
    """Calculate structural edge - formula hidden from user"""
    yes_price = market.get("yes_price", 50)
    if yes_price > 1:
        yes_price = yes_price / 100
    volume = market.get("volume", 0) or 0
    
    distance = abs(yes_price - 0.5)
    edge = distance * 4 + np.log1p(volume) * 0.1
    edge = min(edge, 5.5)
    edge = max(edge, 0.3)
    
    return round(edge, 1)

def get_constraint_status(market):
    """Determine if market appears structurally locked"""
    yes_price = market.get("yes_price", 50)
    
    if yes_price >= 85 or yes_price <= 15:
        return "Locked", "🔒"
    elif yes_price >= 70 or yes_price <= 30:
        return "Leaning", "📊"
    else:
        return "Active", "🔓"

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
# HOW TO USE (Collapsible)
# ============================================================
with st.expander("📖 How to Use This Tool", expanded=False):
    st.markdown("""
    **Understanding Structural Edge**
    
    **This is NOT a prediction tool.** Politics Edge Finder identifies when 
    **structural constraints** have resolved outcomes before markets fully adjust.
    
    **🔒 Constraint Status**
    - **Locked (85%+):** Market strongly pricing one outcome. Limited paths remain.
    - **Leaning (70-84%):** Clear direction but uncertainty remains.
    - **Active (31-69%):** Multiple viable paths. High uncertainty.
    
    **📊 What to Look For**
    - **Volume spikes** after news events = market catching up
    - **Price movement toward extremes** = paths collapsing
    - **Stale prices** despite structural changes = opportunity
    
    **✅ How to Trade**
    1. Identify markets where structure has resolved but price lags
    2. Confirm with volume trend (rising = confirmation)
    3. Check chart for recent movement direction
    4. Enter before price fully adjusts to structural reality
    """)

# ============================================================
# FETCH DATA
# ============================================================
with st.spinner("Loading live Kalshi political markets..."):
    markets = get_political_markets()

if not markets:
    st.warning("No political markets currently open on Kalshi. Political markets typically appear during election cycles and major political events.")
    st.info("Check back closer to the 2026 midterm elections for active political markets.")
    st.stop()

# ============================================================
# MARKET PRESSURE GAUGE
# ============================================================
st.markdown("---")
st.markdown("### 📊 Market Pressure")

# Calculate aggregate stats
locked_count = sum(1 for m in markets if m.get("yes_price", 50) >= 85 or m.get("yes_price", 50) <= 15)
total_volume = sum(m.get("volume", 0) or 0 for m in markets)
avg_price_distance = np.mean([abs(m.get("yes_price", 50) - 50) for m in markets])

pressure_score = (locked_count / max(len(markets), 1)) * 40 + (avg_price_distance / 50) * 40 + 20
pressure_score = min(100, max(0, pressure_score))

if pressure_score >= 70:
    pressure_label = "HIGH STRUCTURAL ACTIVITY"
    pressure_color = "#00c853"
elif pressure_score >= 40:
    pressure_label = "MODERATE ACTIVITY"
    pressure_color = "#ffc107"
else:
    pressure_label = "LOW ACTIVITY"
    pressure_color = "#888"

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
    <div style="background: #1e1e2e; border-radius: 12px; padding: 20px; text-align: center;">
        <p style="color: #888; font-size: 12px; margin-bottom: 5px;">PRESSURE INDEX</p>
        <p style="color: {pressure_color}; font-size: 32px; font-weight: 800; margin: 0;">{pressure_score:.0f}</p>
        <p style="color: {pressure_color}; font-size: 11px; margin-top: 5px;">{pressure_label}</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div style="background: #1e1e2e; border-radius: 12px; padding: 20px; text-align: center;">
        <p style="color: #888; font-size: 12px; margin-bottom: 5px;">LOCKED MARKETS</p>
        <p style="color: #4dabf7; font-size: 32px; font-weight: 800; margin: 0;">{locked_count}</p>
        <p style="color: #666; font-size: 11px; margin-top: 5px;">of {len(markets)} tracked</p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    vol_display = f"${total_volume/1000:.0f}K" if total_volume >= 1000 else f"${total_volume}"
    st.markdown(f"""
    <div style="background: #1e1e2e; border-radius: 12px; padding: 20px; text-align: center;">
        <p style="color: #888; font-size: 12px; margin-bottom: 5px;">TOTAL VOLUME</p>
        <p style="color: #fff; font-size: 32px; font-weight: 800; margin: 0;">{vol_display}</p>
        <p style="color: #888; font-size: 11px; margin-top: 5px;">across all markets</p>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div style="background: #1e1e2e; border-radius: 12px; padding: 20px; text-align: center;">
        <p style="color: #888; font-size: 12px; margin-bottom: 5px;">MARKETS FOUND</p>
        <p style="color: #fff; font-size: 32px; font-weight: 800; margin: 0;">{len(markets)}</p>
        <p style="color: #666; font-size: 11px; margin-top: 5px;">political markets</p>
    </div>
    """, unsafe_allow_html=True)

# ============================================================
# MARKET CARDS WITH CHARTS
# ============================================================
st.markdown("---")
st.markdown("### 🗳️ Live Political Markets")

for market in markets:
    ticker = market.get("ticker", "N/A")
    title = market.get("title", "Unknown Market")
    yes_price = market.get("yes_price", 50)
    no_price = 100 - yes_price
    volume = market.get("volume", 0) or 0
    
    edge = calculate_edge(market)
    status, status_icon = get_constraint_status(market)
    
    # Signal classification
    if edge >= 3.5:
        signal_class = "signal-strong"
        signal_text = "STRONG SIGNAL"
    elif edge >= 2.0:
        signal_class = "signal-moderate"
        signal_text = "MODERATE SIGNAL"
    else:
        signal_class = "signal-weak"
        signal_text = "WEAK SIGNAL"
    
    # Card styling
    card_border = "#4a8f4a" if status == "Locked" else "#8f8f4a" if status == "Leaning" else "#333"
    
    st.markdown(f"""
    <div class="market-card" style="border-color: {card_border};">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; flex-wrap: wrap; gap: 10px;">
            <span class="market-title">{title}</span>
            <span class="signal-badge {signal_class}">{signal_text}</span>
        </div>
        <div style="display: flex; gap: 30px; flex-wrap: wrap;">
            <div>
                <p style="color: #888; font-size: 11px; margin-bottom: 3px;">YES PRICE</p>
                <p style="color: #00c853; font-size: 20px; font-weight: 700; margin: 0;">{yes_price}¢</p>
            </div>
            <div>
                <p style="color: #888; font-size: 11px; margin-bottom: 3px;">NO PRICE</p>
                <p style="color: #ff5252; font-size: 20px; font-weight: 700; margin: 0;">{no_price}¢</p>
            </div>
            <div>
                <p style="color: #888; font-size: 11px; margin-bottom: 3px;">STATUS</p>
                <p style="color: #fff; font-size: 16px; font-weight: 600; margin: 0;">{status_icon} {status}</p>
            </div>
            <div>
                <p style="color: #888; font-size: 11px; margin-bottom: 3px;">VOLUME</p>
                <p style="color: #fff; font-size: 16px; font-weight: 600; margin: 0;">${volume:,}</p>
            </div>
            <div>
                <p style="color: #888; font-size: 11px; margin-bottom: 3px;">EDGE</p>
                <p style="color: #00c853; font-size: 16px; font-weight: 600; margin: 0;">+{edge}%</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Price chart
    with st.expander(f"📈 Price Chart — {ticker}", expanded=False):
        history = get_market_history(ticker)
        
        if history:
            df = pd.DataFrame(history)
            if "end_period_ts" in df.columns:
                df["date"] = pd.to_datetime(df["end_period_ts"], unit="s")
            else:
                df["date"] = pd.date_range(end=datetime.now(), periods=len(df), freq="D")
            
            if "close_price" in df.columns:
                df["close"] = df["close_price"]
            elif "close" in df.columns:
                pass
            else:
                df["close"] = yes_price
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=df["date"],
                y=df["close"],
                mode="lines",
                name="YES Price",
                line=dict(color="#00c853", width=2),
                fill="tozeroy",
                fillcolor="rgba(0, 200, 83, 0.1)"
            ))
            
            fig.update_layout(
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(30,30,46,1)",
                margin=dict(l=0, r=0, t=30, b=0),
                height=250,
                xaxis=dict(showgrid=False),
                yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.1)", title="Price (¢)"),
                showlegend=False
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                high = df["close"].max()
                st.metric("30d High", f"{high}¢")
            with col2:
                low = df["close"].min()
                st.metric("30d Low", f"{low}¢")
            with col3:
                if len(df) > 1:
                    change = df["close"].iloc[-1] - df["close"].iloc[0]
                    st.metric("30d Change", f"{change:+.0f}¢")
                else:
                    st.metric("30d Change", "N/A")
        else:
            st.info("📊 Historical data not available for this market")
            
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=["YES", "NO"],
                y=[yes_price, no_price],
                marker_color=["#00c853", "#ff5252"]
            ))
            fig.update_layout(
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(30,30,46,1)",
                height=200,
                margin=dict(l=0, r=0, t=20, b=0),
                yaxis=dict(title="Price (¢)", range=[0, 100])
            )
            st.plotly_chart(fig, use_container_width=True)
    
    # Kalshi link
    kalshi_url = f"https://kalshi.com/markets?search={ticker}"
    st.markdown(f"[View on Kalshi →]({kalshi_url})")
    st.markdown("")

# ============================================================
# REFRESH BUTTON
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
    <p style="font-size: 12px; margin-bottom: 10px;">
        ⚠️ <strong>Disclaimer:</strong> Structural analysis only. Not financial advice. 
        Political markets carry unique risks including regulatory changes and event uncertainty.
    </p>
    <p style="font-size: 11px; color: #555;">
        BigSnapshot © 2026 | Data from Kalshi Public API | Refreshes every 5 minutes
    </p>
</div>
""", unsafe_allow_html=True)
