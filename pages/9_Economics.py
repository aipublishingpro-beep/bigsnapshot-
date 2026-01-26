# FILE: pages/9_Economics.py
# v2.0 - Added data-driven edge signals
import streamlit as st

st.set_page_config(
    page_title="Economics Edge Finder | BigSnapshot",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ============================================================
# GA4 ANALYTICS - SERVER SIDE
# ============================================================
import uuid
import requests as req_ga

def send_ga4_event(page_title, page_path):
    try:
        url = f"https://www.google-analytics.com/mp/collect?measurement_id=G-NQKY5VQ376&api_secret=n4oBJjH7RXi3dA7aQo2CZA"
        payload = {"client_id": str(uuid.uuid4()), "events": [{"name": "page_view", "params": {"page_title": page_title, "page_location": f"https://bigsnapshot.streamlit.app{page_path}"}}]}
        req_ga.post(url, json=payload, timeout=2)
    except: pass

send_ga4_event("Economics Edge Finder", "/Economics")

# ============================================================
# COOKIE AUTH CHECK
# ============================================================
from auth import require_auth
require_auth()

import requests
from datetime import datetime, timedelta
import pytz
from fred_data import (
    get_fed_rate, get_unemployment, get_gdp_growth, 
    get_cpi_yoy, get_treasury_spread, get_indicator_color,
    generate_edge_signals, get_jobless_claims_trend, get_cpi_momentum,
    THRESHOLDS
)

# ============================================================
# STYLES
# ============================================================
def apply_styles():
    st.markdown('<style>@import url("https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap"); html, body, [class*="css"] { font-family: "Inter", sans-serif; } .stApp { background: linear-gradient(135deg, #0a1628 0%, #1a2a4a 50%, #0d1a2d 100%); } .signal-card-strong { background: linear-gradient(135deg, #3d1a1a 0%, #5a2d2d 100%); border: 2px solid #ff6b35; border-radius: 16px; padding: 24px; margin: 16px 0; box-shadow: 0 8px 32px rgba(255, 107, 53, 0.3); } .signal-card-moderate { background: linear-gradient(135deg, #3d3d1a 0%, #5a5a2d 100%); border: 2px solid #ffcc00; border-radius: 16px; padding: 24px; margin: 16px 0; box-shadow: 0 4px 20px rgba(255, 204, 0, 0.2); } .signal-card-watch { background: linear-gradient(135deg, #1a2a4a 0%, #2a3a5a 100%); border: 1px solid #4a9eff; border-radius: 16px; padding: 24px; margin: 16px 0; } .signal-badge-strong { background: linear-gradient(135deg, #ff6b35 0%, #ff8c42 100%); color: white; padding: 6px 14px; border-radius: 20px; font-size: 0.85rem; font-weight: 700; } .signal-badge-moderate { background: linear-gradient(135deg, #ffcc00 0%, #ffd93d 100%); color: black; padding: 6px 14px; border-radius: 20px; font-size: 0.85rem; font-weight: 700; } .signal-badge-watch { background: linear-gradient(135deg, #4a9eff 0%, #2d7dd2 100%); color: white; padding: 6px 14px; border-radius: 20px; font-size: 0.85rem; font-weight: 700; } .data-point { background: rgba(0, 0, 0, 0.3); border-radius: 8px; padding: 8px 12px; margin: 4px 0; font-family: monospace; color: #ccc; } .event-card { background: linear-gradient(135deg, #1a2a4a 0%, #2a3a5a 100%); border: 1px solid #3a4a6a; border-radius: 16px; padding: 24px; margin: 16px 0; } .event-card-hot { background: linear-gradient(135deg, #1e3a5f 0%, #2d5a87 100%); border: 2px solid #ff6b35; box-shadow: 0 8px 32px rgba(255, 107, 53, 0.3); } .countdown-badge { background: linear-gradient(135deg, #ff6b35 0%, #ff8c42 100%); color: white; padding: 6px 14px; border-radius: 20px; font-size: 0.85rem; font-weight: 600; } .indicator-box { background: rgba(26, 42, 74, 0.8); border: 1px solid #3a4a6a; border-radius: 12px; padding: 20px; text-align: center; } .calendar-row { background: rgba(26, 42, 74, 0.6); border-radius: 8px; padding: 12px 16px; margin: 8px 0; display: flex; justify-content: space-between; align-items: center; } .calendar-row-next { background: linear-gradient(135deg, #1e3a5f 0%, #2d4a6f 100%); border: 1px solid #ff6b35; } .legend-box { background: rgba(26, 42, 74, 0.8); border: 1px solid #3a4a6a; border-radius: 10px; padding: 16px; margin: 16px 0; } .live-badge { background: #22c55e; color: white; padding: 2px 8px; border-radius: 4px; font-size: 0.7rem; font-weight: 600; margin-left: 8px; animation: pulse 2s infinite; } @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.7; } } .market-link { display: inline-block; background: linear-gradient(135deg, #4a9eff 0%, #2d7dd2 100%); color: white !important; padding: 10px 20px; border-radius: 8px; font-weight: 600; text-decoration: none; margin-top: 12px; } a { color: #4a9eff !important; text-decoration: none !important; } a:hover { color: #6bb3ff !important; }</style>', unsafe_allow_html=True)

apply_styles()

# ============================================================
# MOBILE CSS
# ============================================================
st.markdown('<style>@media (max-width: 768px) { .stColumns > div { flex: 1 1 100% !important; min-width: 100% !important; } [data-testid="stMetricValue"] { font-size: 1.2rem !important; } h1 { font-size: 1.5rem !important; } h2 { font-size: 1.2rem !important; } }</style>', unsafe_allow_html=True)

# ============================================================
# CONSTANTS
# ============================================================
eastern = pytz.timezone('US/Eastern')

FOMC_MEETINGS_2026 = [
    {"dates": "January 27-28", "decision_date": datetime(2026, 1, 28, 14, 0), "has_projections": False},
    {"dates": "March 17-18", "decision_date": datetime(2026, 3, 18, 14, 0), "has_projections": True},
    {"dates": "May 5-6", "decision_date": datetime(2026, 5, 6, 14, 0), "has_projections": False},
    {"dates": "June 16-17", "decision_date": datetime(2026, 6, 17, 14, 0), "has_projections": True},
    {"dates": "July 28-29", "decision_date": datetime(2026, 7, 29, 14, 0), "has_projections": False},
    {"dates": "September 15-16", "decision_date": datetime(2026, 9, 16, 14, 0), "has_projections": True},
    {"dates": "October 27-28", "decision_date": datetime(2026, 10, 28, 14, 0), "has_projections": False},
    {"dates": "December 8-9", "decision_date": datetime(2026, 12, 9, 14, 0), "has_projections": True},
]

CPI_RELEASES_2026 = [
    {"month": "January", "release_date": datetime(2026, 1, 14, 8, 30), "for_month": "December 2025"},
    {"month": "February", "release_date": datetime(2026, 2, 12, 8, 30), "for_month": "January 2026"},
    {"month": "March", "release_date": datetime(2026, 3, 11, 8, 30), "for_month": "February 2026"},
    {"month": "April", "release_date": datetime(2026, 4, 10, 8, 30), "for_month": "March 2026"},
    {"month": "May", "release_date": datetime(2026, 5, 13, 8, 30), "for_month": "April 2026"},
    {"month": "June", "release_date": datetime(2026, 6, 10, 8, 30), "for_month": "May 2026"},
    {"month": "July", "release_date": datetime(2026, 7, 14, 8, 30), "for_month": "June 2026"},
    {"month": "August", "release_date": datetime(2026, 8, 12, 8, 30), "for_month": "July 2026"},
    {"month": "September", "release_date": datetime(2026, 9, 11, 8, 30), "for_month": "August 2026"},
    {"month": "October", "release_date": datetime(2026, 10, 13, 8, 30), "for_month": "September 2026"},
    {"month": "November", "release_date": datetime(2026, 11, 12, 8, 30), "for_month": "October 2026"},
    {"month": "December", "release_date": datetime(2026, 12, 10, 8, 30), "for_month": "November 2026"},
]

KALSHI_MARKETS = {
    "fed_rate": "https://kalshi.com/markets/kxfed/fed-funds-rate",
    "fed_decision": "https://kalshi.com/markets/kxfeddecision/fed-meeting",
    "cpi": "https://kalshi.com/markets/kxcpi/cpi",
    "cpi_yoy": "https://kalshi.com/markets/kxcpiyoy/inflation",
    "unemployment": "https://kalshi.com/markets/kxunemployment",
    "economics": "https://kalshi.com/events/economics",
}

# ============================================================
# HELPER FUNCTIONS
# ============================================================
def get_time_until(target_date):
    now = datetime.now(eastern)
    target = eastern.localize(target_date) if target_date.tzinfo is None else target_date
    delta = target - now
    if delta.total_seconds() < 0:
        return "PASSED", 0
    days = delta.days
    hours = delta.seconds // 3600
    minutes = (delta.seconds % 3600) // 60
    if days > 0:
        return f"{days}d {hours}h", days
    elif hours > 0:
        return f"{hours}h {minutes}m", 0
    else:
        return f"{minutes}m", 0

def get_next_fomc():
    now = datetime.now(eastern)
    for meeting in FOMC_MEETINGS_2026:
        meeting_dt = eastern.localize(meeting['decision_date'])
        if meeting_dt > now:
            return meeting
    return FOMC_MEETINGS_2026[0]

def get_next_cpi():
    now = datetime.now(eastern)
    for release in CPI_RELEASES_2026:
        release_dt = eastern.localize(release['release_date'])
        if release_dt > now:
            return release
    return CPI_RELEASES_2026[0]

# ============================================================
# FETCH LIVE DATA
# ============================================================
fed_rate = get_fed_rate()
unemployment = get_unemployment()
gdp = get_gdp_growth()
cpi_yoy = get_cpi_yoy()
spread = get_treasury_spread()

# ============================================================
# MAIN CONTENT
# ============================================================
st.markdown("# 📈 Economics Edge Finder")
st.markdown("*Data-driven signals for Kalshi economics markets*")

now = datetime.now(eastern)
st.markdown(f"**Last Updated:** {now.strftime('%B %d, %Y at %I:%M %p ET')} <span class='live-badge'>LIVE</span>", unsafe_allow_html=True)

# ============================================================
# 🔥 EDGE SIGNALS SECTION (NEW)
# ============================================================
st.markdown("---")
st.markdown("### 🔥 Edge Signals <span class='live-badge'>FROM FRED DATA</span>", unsafe_allow_html=True)
st.caption("Data-driven observations — NOT predictions. Always verify with your own research.")

signals = generate_edge_signals()

if signals:
    for signal in signals:
        if signal['strength'] == "STRONG":
            badge_color = "#ff6b35"
            border_color = "#ff6b35"
        elif signal['strength'] == "MODERATE":
            badge_color = "#ffcc00"
            border_color = "#ffcc00"
        else:
            badge_color = "#4a9eff"
            border_color = "#4a9eff"
        kalshi_link = KALSHI_MARKETS.get(signal['kalshi_market'], KALSHI_MARKETS['economics'])
        data_points_text = "\n".join([f"📊 {dp}" for dp in signal['data_points']])
        st.markdown(f'<div style="background: linear-gradient(135deg, #1a2a4a 0%, #2a3a5a 100%); border: 2px solid {border_color}; border-radius: 16px; padding: 24px; margin: 16px 0;"><span style="background: {badge_color}; color: {"black" if signal["strength"] == "MODERATE" else "white"}; padding: 6px 14px; border-radius: 20px; font-size: 0.85rem; font-weight: 700;">{signal["strength"]} SIGNAL</span><h3 style="color: white; margin: 12px 0 4px 0;">{signal["title"]}</h3><p style="color: {signal["color"]}; margin: 4px 0 0 0; font-size: 0.95rem; font-weight: 600;">→ {signal.get("subtitle", "")}</p><p style="color: #888; margin: 8px 0 16px 0; font-size: 0.85rem;">Market: <strong style="color: #fff;">{signal["market"]}</strong> | Latest: <strong style="color: #fff;">{signal["latest_data"]}</strong><span style="color: #666; font-size: 0.75rem;"> (as of {signal["data_date"]})</span></p><div style="background: rgba(0,0,0,0.3); border-radius: 8px; padding: 12px; margin: 12px 0; font-family: monospace; font-size: 0.85rem; color: #ccc; white-space: pre-line;">{data_points_text}</div><p style="color: #aaa; font-size: 0.9rem; margin: 12px 0; padding: 12px; background: rgba(0,0,0,0.2); border-radius: 8px; border-left: 3px solid {signal["color"]};">💡 <strong>Implication:</strong> {signal["implication"]}</p></div>', unsafe_allow_html=True)
        st.link_button(f"📈 TRADE {signal['market'].upper()} ON KALSHI", kalshi_link, use_container_width=True)
        st.markdown("")
else:
    st.info("📊 No strong signals detected currently. Markets may be efficiently priced or trends unclear.")

# ============================================================
# SIGNAL LEGEND
# ============================================================
with st.expander("📖 Understanding Edge Signals"):
    st.markdown("""
### Signal Strength Levels

| Badge | Meaning | Requirements |
|-------|---------|--------------|
| 🟠 **STRONG** | Clear trend + confirming level | 4+ consecutive data points OR 3+ weeks with elevated/concerning level |
| 🟡 **MODERATE** | Trend emerging with context | 3 consecutive data points with supporting level |
| 🔵 **WATCH** | Early signal | Initial divergence, needs more confirmation |

### Signal Logic (What We Check)

**Jobless Claims:**
- Track consecutive weekly increases/decreases (need 3+ for signal)
- Compare level to historical norms (200K = tight, 260K+ = softening)
- STRONG requires both trend direction AND concerning level

**CPI Momentum:**
- Look at 4 months of MoM data, not just latest
- Compare to Fed's 2% target (~0.17% monthly)
- Check if trend is accelerating OR decelerating
- STRONG requires consistent direction + hot/cool level

**Yield Curve:**
- 10Y-2Y spread: negative = inverted = recession warning
- Deep inversion (<-0.50%) = STRONG signal
- Historical lead time: 12-18 months before recession

**Unemployment:**
- Track 3-month change in rate
- Rising 0.3%+ over 3 months = significant softening
- Supports Fed cut narrative

### What These Signals Are NOT

❌ **Predictions** — We don't know what CPI will print  
❌ **"Locks"** — Markets can stay irrational  
❌ **Financial advice** — Always do your own research  

### Data Sources

All data from **FRED** (Federal Reserve Economic Data):
- Initial Claims: ICSA (weekly)
- CPI: CPIAUCSL (monthly)
- Unemployment: UNRATE (monthly)
- Treasuries: DGS10, DGS2 (daily)
- GDP: A191RL1Q225SBEA (quarterly)
""")

# ============================================================
# CURRENT ECONOMIC SNAPSHOT
# ============================================================
st.markdown("---")
st.markdown("### 📊 Current Economic Snapshot", unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f'<div class="indicator-box"><p style="color: #888; margin: 0;">Fed Funds Rate</p><p style="font-size: 2rem; font-weight: 700; color: #4ade80;">{fed_rate["value"]}</p><p style="color: #888; font-size: 0.8rem;">Target Range</p></div>', unsafe_allow_html=True)

with col2:
    cpi_color = get_indicator_color("cpi_yoy", cpi_yoy.get('raw', 2.7))
    st.markdown(f'<div class="indicator-box"><p style="color: #888; margin: 0;">CPI (YoY)</p><p style="font-size: 2rem; font-weight: 700; color: {cpi_color};">{cpi_yoy["value"]}</p><p style="color: #888; font-size: 0.8rem;">As of {cpi_yoy.get("date", "N/A")}</p></div>', unsafe_allow_html=True)

with col3:
    unemp_color = get_indicator_color("unemployment", unemployment.get('raw', 4.2))
    st.markdown(f'<div class="indicator-box"><p style="color: #888; margin: 0;">Unemployment</p><p style="font-size: 2rem; font-weight: 700; color: {unemp_color};">{unemployment["value"]}</p><p style="color: #888; font-size: 0.8rem;">As of {unemployment.get("date", "N/A")}</p></div>', unsafe_allow_html=True)

with col4:
    gdp_color = get_indicator_color("gdp_growth", gdp.get('raw', 2.5))
    st.markdown(f'<div class="indicator-box"><p style="color: #888; margin: 0;">GDP Growth</p><p style="font-size: 2rem; font-weight: 700; color: {gdp_color};">{gdp["value"]}</p><p style="color: #888; font-size: 0.8rem;">Annualized Q/Q</p></div>', unsafe_allow_html=True)

st.markdown('<div style="background: rgba(26, 42, 74, 0.5); border-radius: 8px; padding: 12px 16px; margin-top: 16px;"><p style="color: #888; margin: 0 0 8px 0; font-size: 0.8rem; font-weight: 600;">📊 COLOR GUIDE</p><div style="display: flex; flex-wrap: wrap; gap: 20px; font-size: 0.75rem; color: #aaa;"><span><span style="color: #4ade80;">●</span> Healthy / On Target</span><span><span style="color: #ffcc00;">●</span> Caution / Elevated</span><span><span style="color: #ff6b6b;">●</span> Concern / Off Target</span></div></div>', unsafe_allow_html=True)

if spread:
    spread_color = "#ff6b6b" if spread['inverted'] else "#4ade80"
    spread_label = "⚠️ INVERTED YIELD CURVE" if spread['inverted'] else "10Y-2Y Treasury Spread"
    st.markdown(f'<div class="indicator-box" style="margin-top: 16px;"><p style="color: #888; margin: 0;">{spread_label}</p><p style="font-size: 1.5rem; font-weight: 700; color: {spread_color};">{spread["spread"]}</p><p style="color: #888; font-size: 0.8rem;">10Y: {spread["t10"]:.2f}% | 2Y: {spread["t2"]:.2f}%</p></div>', unsafe_allow_html=True)

# ============================================================
# NEXT FOMC MEETING
# ============================================================
st.markdown("---")
st.markdown("### 🏛️ Next FOMC Meeting")

next_fomc = get_next_fomc()
countdown, days_until = get_time_until(next_fomc['decision_date'])
is_soon = days_until <= 7
card_class = "event-card event-card-hot" if is_soon else "event-card"
proj_badge = "📊 Includes Projections & Dot Plot" if next_fomc['has_projections'] else ""

st.markdown(f'<div class="{card_class}"><div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;"><div><h2 style="margin: 0; color: white;">FOMC Meeting</h2><p style="font-size: 1.3rem; color: #a0d2ff; margin: 8px 0;">{next_fomc["dates"]}, 2026</p><p style="color: #888;">{proj_badge}</p></div><div style="text-align: right;"><span class="countdown-badge">⏱️ {countdown}</span><p style="color: #888; margin-top: 8px;">Decision at 2:00 PM ET</p></div></div><div style="margin-top: 20px;"><p style="color: #ccc;"><strong>Current Rate:</strong> {fed_rate["value"]}</p><a href="{KALSHI_MARKETS["fed_decision"]}" target="_blank" class="market-link">📈 Trade Fed Decision</a><a href="{KALSHI_MARKETS["fed_rate"]}" target="_blank" class="market-link" style="margin-left: 10px;">📊 Fed Rate Markets</a></div></div>', unsafe_allow_html=True)

# ============================================================
# NEXT CPI RELEASE
# ============================================================
st.markdown("### 📊 Next CPI Release")

next_cpi = get_next_cpi()
cpi_countdown, cpi_days = get_time_until(next_cpi['release_date'])
cpi_card_class = "event-card event-card-hot" if cpi_days <= 3 else "event-card"

st.markdown(f'<div class="{cpi_card_class}"><div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;"><div><h2 style="margin: 0; color: white;">CPI Inflation Data</h2><p style="font-size: 1.3rem; color: #a0d2ff; margin: 8px 0;">{next_cpi["release_date"].strftime("%B %d, %Y")}</p><p style="color: #888;">For: {next_cpi["for_month"]}</p></div><div style="text-align: right;"><span class="countdown-badge">⏱️ {cpi_countdown}</span><p style="color: #888; margin-top: 8px;">Released at 8:30 AM ET</p></div></div><div style="margin-top: 20px;"><p style="color: #ccc;"><strong>Latest CPI YoY:</strong> {cpi_yoy["value"]}</p><a href="{KALSHI_MARKETS["cpi"]}" target="_blank" class="market-link">📈 Trade CPI</a><a href="{KALSHI_MARKETS["cpi_yoy"]}" target="_blank" class="market-link" style="margin-left: 10px;">📊 CPI YoY Markets</a></div></div>', unsafe_allow_html=True)

# ============================================================
# 2026 FOMC CALENDAR
# ============================================================
st.markdown("---")
st.markdown("### 📅 2026 FOMC Calendar")

for meeting in FOMC_MEETINGS_2026:
    countdown_str, days = get_time_until(meeting['decision_date'])
    is_next = meeting == next_fomc
    is_past = countdown_str == "PASSED"
    row_class = "calendar-row-next" if is_next else "calendar-row"
    status_badge = "🔥 NEXT" if is_next else ("✅" if is_past else "")
    proj_badge = "📊" if meeting['has_projections'] else ""
    opacity = "0.5" if is_past else "1"
    st.markdown(f'<div class="{row_class}" style="opacity: {opacity};"><div><strong style="color: white;">{meeting["dates"]}</strong><span style="margin-left: 10px; color: #888;">{proj_badge}</span></div><div><span style="color: #888; margin-right: 15px;">{"Done" if is_past else countdown_str}</span><span style="color: #ff6b35; font-weight: 600;">{status_badge}</span></div></div>', unsafe_allow_html=True)

st.caption("📊 = Includes Summary of Economic Projections (SEP) and Dot Plot")

# ============================================================
# ALL MARKETS
# ============================================================
st.markdown("---")
st.markdown("### 🎯 All Economics Markets")

col1, col2 = st.columns(2)

with col1:
    st.markdown(f'<div class="event-card"><h3 style="color: white; margin-top: 0;">🏛️ Federal Reserve</h3><ul style="color: #ccc;"><li>Fed Funds Rate Target</li><li>FOMC Decision (Cut/Hold/Hike)</li><li>Number of Rate Cuts in 2026</li></ul><a href="{KALSHI_MARKETS["fed_rate"]}" target="_blank" class="market-link">Browse Fed Markets</a></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="event-card"><h3 style="color: white; margin-top: 0;">📊 Inflation</h3><ul style="color: #ccc;"><li>CPI Month-over-Month</li><li>CPI Year-over-Year</li><li>Core CPI (ex food & energy)</li></ul><a href="{KALSHI_MARKETS["cpi_yoy"]}" target="_blank" class="market-link">Browse CPI Markets</a></div>', unsafe_allow_html=True)

with col2:
    st.markdown(f'<div class="event-card"><h3 style="color: white; margin-top: 0;">💼 Employment</h3><ul style="color: #ccc;"><li>Nonfarm Payrolls</li><li>Unemployment Rate</li><li>Jobless Claims</li></ul><a href="{KALSHI_MARKETS["economics"]}" target="_blank" class="market-link">Browse Jobs Markets</a></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="event-card"><h3 style="color: white; margin-top: 0;">📈 Growth</h3><ul style="color: #ccc;"><li>GDP Growth Rate</li><li>Recession Probability</li></ul><a href="{KALSHI_MARKETS["economics"]}" target="_blank" class="market-link">Browse GDP Markets</a></div>', unsafe_allow_html=True)

# ============================================================
# DISCLAIMER
# ============================================================
st.markdown("---")
st.markdown('<div class="legend-box"><strong>⚠️ Important:</strong> Edge signals are data observations, NOT predictions or financial advice. Economic data releases have institutional participation and binary outcomes. Always do your own research. Event contracts can lose 100% of value.</div>', unsafe_allow_html=True)

# ============================================================
# HOW TO USE THIS APP
# ============================================================
with st.expander("📖 How to Use This App"):
    st.markdown("""
## Economics Edge Finder — Quick Start

### Step 1: Check the Edge Signals

The 🔥 **Edge Signals** section shows data-driven observations from FRED:

| Badge | What It Means | Your Action |
|-------|---------------|-------------|
| 🟠 STRONG | Clear trend with confirming data | Worth investigating on Kalshi |
| 🟡 MODERATE | Trend emerging | Monitor, may strengthen |
| 🔵 WATCH | Early signal | Too early to act, keep watching |

**Signals tell you WHERE to look, not WHAT to buy.**

---

### Step 2: Check the Calendar

Economics markets are **event-driven**. Key dates:

| Event | Frequency | Why It Matters |
|-------|-----------|----------------|
| FOMC Meeting | 8x/year | Fed rate decisions move markets |
| CPI Release | Monthly | Inflation data, high volatility |
| Jobs Report | Monthly | Unemployment, payrolls |
| GDP Release | Quarterly | Growth data |

**Best time to trade:** 1-3 days BEFORE release (when signals suggest mispricing)

---

### Step 3: Compare Signal to Market

1. Click **"View on Kalshi"** link on any signal
2. Check the current market price
3. Ask: Does the market already reflect this data trend?

**Example:**
- Signal says: "Claims rising 4 weeks → Unemployment ABOVE may have value"
- Kalshi shows: Unemployment ABOVE 4.2% priced at 35¢
- Your job: Decide if 35¢ is too cheap given the claims trend

---

### Step 4: Size Your Risk

Economics markets have **unique risks:**

- ⚠️ Binary outcomes (contracts go to $0 or $1)
- ⚠️ Institutional traders with better models
- ⚠️ Data revisions can flip outcomes
- ⚠️ "Whisper numbers" on Wall Street

**Rule of thumb:** Never bet more than you'd lose on a coin flip

---

### What This App Does NOT Do

❌ Predict exact CPI/unemployment numbers  
❌ Tell you to "BUY" or "SELL"  
❌ Guarantee any edge exists  
❌ Replace your own research  

---

### Workflow Summary

```
1. Check signals → See what FRED data suggests
2. Check calendar → Know when data releases
3. Check Kalshi → See current market prices
4. Compare → Is market ignoring the trend?
5. Decide → Your call, your risk
```

**This app compresses your research time. The decision is still yours.**
""")

# ============================================================
# FOOTER
# ============================================================

st.markdown('<div style="text-align: center; color: #666; font-size: 0.75rem; padding: 20px;"><p>Economic data from <strong>FRED®</strong>, Federal Reserve Bank of St. Louis</p><p><a href="https://fred.stlouisfed.org/">https://fred.stlouisfed.org/</a></p><p style="margin-top: 10px;">© 2026 BigSnapshot | <a href="https://bigsnapshot.com">bigsnapshot.com</a></p></div>', unsafe_allow_html=True)

st.caption("⚠️ Educational only. Not financial advice. v2.1")
