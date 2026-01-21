# FILE: pages/9_Economics.py
import streamlit as st
import requests
from datetime import datetime, timedelta
import pytz
import extra_streamlit_components as stx
from fred_data import (
    get_fed_rate, get_unemployment, get_gdp_growth, 
    get_cpi_yoy, get_treasury_spread, get_indicator_color
)

# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title="Economics Edge Finder | BigSnapshot",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ============================================================
# STYLES
# ============================================================
def apply_styles():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    .stApp {
        background: linear-gradient(135deg, #0a1628 0%, #1a2a4a 50%, #0d1a2d 100%);
    }
    
    .event-card {
        background: linear-gradient(135deg, #1a2a4a 0%, #2a3a5a 100%);
        border: 1px solid #3a4a6a;
        border-radius: 16px;
        padding: 24px;
        margin: 16px 0;
        transition: all 0.3s ease;
    }
    
    .event-card:hover {
        border-color: #4a9eff;
        box-shadow: 0 4px 20px rgba(74, 158, 255, 0.2);
    }
    
    .event-card-hot {
        background: linear-gradient(135deg, #1e3a5f 0%, #2d5a87 100%);
        border: 2px solid #ff6b35;
        box-shadow: 0 8px 32px rgba(255, 107, 53, 0.3);
    }
    
    .countdown-badge {
        background: linear-gradient(135deg, #ff6b35 0%, #ff8c42 100%);
        color: white;
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
    }
    
    .rate-display {
        font-size: 2.5rem;
        font-weight: 700;
        color: #4ade80;
    }
    
    .market-link {
        display: inline-block;
        background: linear-gradient(135deg, #4a9eff 0%, #2d7dd2 100%);
        color: white !important;
        padding: 10px 20px;
        border-radius: 8px;
        font-weight: 600;
        text-decoration: none;
        margin-top: 12px;
    }
    
    .market-link:hover {
        background: linear-gradient(135deg, #6bb3ff 0%, #4a9eff 100%);
    }
    
    .indicator-box {
        background: rgba(26, 42, 74, 0.8);
        border: 1px solid #3a4a6a;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
    }
    
    .calendar-row {
        background: rgba(26, 42, 74, 0.6);
        border-radius: 8px;
        padding: 12px 16px;
        margin: 8px 0;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    .calendar-row-next {
        background: linear-gradient(135deg, #1e3a5f 0%, #2d4a6f 100%);
        border: 1px solid #ff6b35;
    }
    
    .legend-box {
        background: rgba(26, 42, 74, 0.8);
        border: 1px solid #3a4a6a;
        border-radius: 10px;
        padding: 16px;
        margin: 16px 0;
    }
    
    .live-badge {
        background: #22c55e;
        color: white;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 0.7rem;
        font-weight: 600;
        margin-left: 8px;
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.7; }
    }
    
    a { color: #4a9eff !important; text-decoration: none !important; }
    a:hover { color: #6bb3ff !important; }
    
    .stButton > button {
        background: linear-gradient(135deg, #4a9eff 0%, #2d7dd2 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 8px 24px;
        font-weight: 600;
    }
    </style>
    """, unsafe_allow_html=True)

apply_styles()

# ============================================================
# COOKIE MANAGER AUTH
# ============================================================
cookie_manager = stx.CookieManager()

if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'user_type' not in st.session_state:
    st.session_state.user_type = None

auth_cookie = cookie_manager.get("bigsnapshot_auth")
if auth_cookie and not st.session_state.authenticated:
    st.session_state.authenticated = True
    st.session_state.user_type = auth_cookie

if not st.session_state.authenticated:
    st.warning("⚠️ Please log in from the Home page first.")
    st.page_link("Home.py", label="🏠 Go to Home", use_container_width=True)
    st.stop()

# ============================================================
# GA4 TRACKING
# ============================================================
st.markdown("""
<script async src="https://www.googletagmanager.com/gtag/js?id=G-NQKY5VQ376"></script>
<script>window.dataLayer = window.dataLayer || [];function gtag(){dataLayer.push(arguments);}gtag('js', new Date());gtag('config', 'G-NQKY5VQ376');</script>
""", unsafe_allow_html=True)

# ============================================================
# MOBILE CSS
# ============================================================
st.markdown("""
<style>
@media (max-width: 768px) {
    .stColumns > div { flex: 1 1 100% !important; min-width: 100% !important; }
    [data-testid="stMetricValue"] { font-size: 1.2rem !important; }
    [data-testid="stMetricLabel"] { font-size: 0.8rem !important; }
    h1 { font-size: 1.5rem !important; }
    h2 { font-size: 1.2rem !important; }
    h3 { font-size: 1rem !important; }
    button { padding: 8px 12px !important; font-size: 0.85em !important; }
}
</style>
""", unsafe_allow_html=True)

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
    "core_cpi": "https://kalshi.com/markets/kxcpicoreyoy/core-inflation",
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
# SIDEBAR
# ============================================================
with st.sidebar:
    st.markdown("### 📈 Economics Edge Finder")
    st.markdown("---")
    
    st.markdown("#### 🎯 Key Markets")
    st.markdown("""
    - **Fed Rate** - FOMC decisions
    - **CPI** - Inflation data
    - **Core CPI** - Ex food & energy
    - **GDP** - Growth data
    - **Jobs** - Employment reports
    """)
    
    st.markdown("---")
    st.markdown("#### 📅 Key Dates")
    next_fomc = get_next_fomc()
    next_cpi = get_next_cpi()
    st.markdown(f"**Next FOMC:** {next_fomc['dates']}")
    st.markdown(f"**Next CPI:** {next_cpi['month']}")
    
    st.markdown("---")
    st.markdown("#### 📊 Live Data")
    st.markdown(f"**Fed Rate:** {fed_rate['value']}")
    st.markdown(f"**Unemployment:** {unemployment['value']}")
    st.markdown(f"**CPI YoY:** {cpi_yoy['value']}")

# ============================================================
# MAIN CONTENT
# ============================================================
st.markdown("# 📈 Economics Edge Finder")
st.markdown("*Fed decisions, inflation data, and economic indicators for Kalshi markets*")

now = datetime.now(eastern)
st.markdown(f"**Last Updated:** {now.strftime('%B %d, %Y at %I:%M %p ET')} <span class='live-badge'>LIVE</span>", unsafe_allow_html=True)

# ============================================================
# CURRENT ECONOMIC SNAPSHOT - LIVE DATA
# ============================================================
st.markdown("---")
st.markdown("### 📊 Current Economic Snapshot <span class='live-badge'>LIVE FROM FRED</span>", unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)

with col1:
    fed_color = "#4ade80"
    st.markdown(f"""
    <div class="indicator-box">
        <p style="color: #888; margin: 0;">Fed Funds Rate</p>
        <p style="font-size: 2rem; font-weight: 700; color: {fed_color};">{fed_rate['value']}</p>
        <p style="color: #888; font-size: 0.8rem;">Target Range</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    cpi_color = get_indicator_color("cpi_yoy", cpi_yoy.get('raw', 2.7))
    st.markdown(f"""
    <div class="indicator-box">
        <p style="color: #888; margin: 0;">CPI (YoY)</p>
        <p style="font-size: 2rem; font-weight: 700; color: {cpi_color};">{cpi_yoy['value']}</p>
        <p style="color: #888; font-size: 0.8rem;">As of {cpi_yoy.get('date', 'N/A')}</p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    unemp_color = get_indicator_color("unemployment", unemployment.get('raw', 4.2))
    st.markdown(f"""
    <div class="indicator-box">
        <p style="color: #888; margin: 0;">Unemployment</p>
        <p style="font-size: 2rem; font-weight: 700; color: {unemp_color};">{unemployment['value']}</p>
        <p style="color: #888; font-size: 0.8rem;">As of {unemployment.get('date', 'N/A')}</p>
    </div>
    """, unsafe_allow_html=True)

with col4:
    gdp_color = get_indicator_color("gdp_growth", gdp.get('raw', 2.5))
    st.markdown(f"""
    <div class="indicator-box">
        <p style="color: #888; margin: 0;">GDP Growth</p>
        <p style="font-size: 2rem; font-weight: 700; color: {gdp_color};">{gdp['value']}</p>
        <p style="color: #888; font-size: 0.8rem;">Annualized Q/Q</p>
    </div>
    """, unsafe_allow_html=True)

# Treasury Spread Row
if spread:
    spread_color = "#ff6b6b" if spread['inverted'] else "#4ade80"
    spread_label = "⚠️ INVERTED YIELD CURVE" if spread['inverted'] else "10Y-2Y Treasury Spread"
    st.markdown(f"""
    <div class="indicator-box" style="margin-top: 16px;">
        <p style="color: #888; margin: 0;">{spread_label}</p>
        <p style="font-size: 1.5rem; font-weight: 700; color: {spread_color};">{spread['spread']}</p>
        <p style="color: #888; font-size: 0.8rem;">10Y: {spread['t10']:.2f}% | 2Y: {spread['t2']:.2f}%</p>
    </div>
    """, unsafe_allow_html=True)

# ============================================================
# NEXT FOMC MEETING - HERO SECTION
# ============================================================
st.markdown("---")
st.markdown("### 🏛️ Next FOMC Meeting")

next_fomc = get_next_fomc()
countdown, days_until = get_time_until(next_fomc['decision_date'])

is_soon = days_until <= 7
card_class = "event-card event-card-hot" if is_soon else "event-card"

projections_badge = "📊 Includes Projections & Dot Plot" if next_fomc['has_projections'] else ""

st.markdown(f"""
<div class="{card_class}">
    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
        <div>
            <h2 style="margin: 0; color: white;">FOMC Meeting</h2>
            <p style="font-size: 1.3rem; color: #a0d2ff; margin: 8px 0;">{next_fomc['dates']}, 2026</p>
            <p style="color: #888;">{projections_badge}</p>
        </div>
        <div style="text-align: right;">
            <span class="countdown-badge">⏱️ {countdown}</span>
            <p style="color: #888; margin-top: 8px;">Decision at 2:00 PM ET</p>
        </div>
    </div>
    <div style="margin-top: 20px;">
        <p style="color: #ccc;">
            <strong>Current Rate:</strong> {fed_rate['value']} | Check Kalshi for live odds on rate decision.
        </p>
        <a href="{KALSHI_MARKETS['fed_decision']}" target="_blank" class="market-link">📈 Trade Fed Decision on Kalshi</a>
        <a href="{KALSHI_MARKETS['fed_rate']}" target="_blank" class="market-link" style="margin-left: 10px;">📊 Fed Rate Markets</a>
    </div>
</div>
""", unsafe_allow_html=True)

# ============================================================
# NEXT CPI RELEASE
# ============================================================
st.markdown("### 📊 Next CPI Release")

next_cpi = get_next_cpi()
cpi_countdown, cpi_days = get_time_until(next_cpi['release_date'])
cpi_card_class = "event-card event-card-hot" if cpi_days <= 3 else "event-card"

st.markdown(f"""
<div class="{cpi_card_class}">
    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
        <div>
            <h2 style="margin: 0; color: white;">CPI Inflation Data</h2>
            <p style="font-size: 1.3rem; color: #a0d2ff; margin: 8px 0;">{next_cpi['release_date'].strftime('%B %d, %Y')}</p>
            <p style="color: #888;">For: {next_cpi['for_month']}</p>
        </div>
        <div style="text-align: right;">
            <span class="countdown-badge">⏱️ {cpi_countdown}</span>
            <p style="color: #888; margin-top: 8px;">Released at 8:30 AM ET</p>
        </div>
    </div>
    <div style="margin-top: 20px;">
        <p style="color: #ccc;">
            <strong>Latest CPI YoY:</strong> {cpi_yoy['value']} | Key Markets: CPI MoM, CPI YoY, Core CPI
        </p>
        <a href="{KALSHI_MARKETS['cpi']}" target="_blank" class="market-link">📈 Trade CPI on Kalshi</a>
        <a href="{KALSHI_MARKETS['cpi_yoy']}" target="_blank" class="market-link" style="margin-left: 10px;">📊 CPI YoY Markets</a>
    </div>
</div>
""", unsafe_allow_html=True)

# ============================================================
# 2026 FOMC CALENDAR
# ============================================================
st.markdown("---")
st.markdown("### 📅 2026 FOMC Meeting Calendar")

for meeting in FOMC_MEETINGS_2026:
    countdown_str, days = get_time_until(meeting['decision_date'])
    is_next = meeting == next_fomc
    is_past = countdown_str == "PASSED"
    
    row_class = "calendar-row-next" if is_next else "calendar-row"
    status_badge = "🔥 NEXT" if is_next else ("✅ DONE" if is_past else "")
    proj_badge = "📊" if meeting['has_projections'] else ""
    
    opacity = "0.5" if is_past else "1"
    
    st.markdown(f"""
    <div class="{row_class}" style="opacity: {opacity};">
        <div>
            <strong style="color: white;">{meeting['dates']}</strong>
            <span style="margin-left: 10px; color: #888;">{proj_badge}</span>
        </div>
        <div>
            <span style="color: #888; margin-right: 15px;">{countdown_str if not is_past else "Completed"}</span>
            <span style="color: #ff6b35; font-weight: 600;">{status_badge}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

st.caption("📊 = Includes Summary of Economic Projections (SEP) and Dot Plot")

# ============================================================
# ALL ECONOMICS MARKETS
# ============================================================
st.markdown("---")
st.markdown("### 🎯 All Economics Markets on Kalshi")

col1, col2 = st.columns(2)

with col1:
    st.markdown(f"""
    <div class="event-card">
        <h3 style="color: white; margin-top: 0;">🏛️ Federal Reserve</h3>
        <ul style="color: #ccc;">
            <li>Fed Funds Rate Target</li>
            <li>FOMC Decision (Cut/Hold/Hike)</li>
            <li>Number of Rate Cuts in 2026</li>
            <li>Next Rate Hike Timing</li>
        </ul>
        <a href="{KALSHI_MARKETS['fed_rate']}" target="_blank" class="market-link">Browse Fed Markets</a>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown(f"""
    <div class="event-card">
        <h3 style="color: white; margin-top: 0;">📊 Inflation</h3>
        <ul style="color: #ccc;">
            <li>CPI Month-over-Month</li>
            <li>CPI Year-over-Year</li>
            <li>Core CPI (ex food & energy)</li>
            <li>Inflation Surge Markets</li>
        </ul>
        <a href="{KALSHI_MARKETS['cpi_yoy']}" target="_blank" class="market-link">Browse CPI Markets</a>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="event-card">
        <h3 style="color: white; margin-top: 0;">💼 Employment</h3>
        <ul style="color: #ccc;">
            <li>Nonfarm Payrolls</li>
            <li>Unemployment Rate</li>
            <li>Jobless Claims</li>
        </ul>
        <a href="{KALSHI_MARKETS['economics']}" target="_blank" class="market-link">Browse Jobs Markets</a>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown(f"""
    <div class="event-card">
        <h3 style="color: white; margin-top: 0;">📈 Growth</h3>
        <ul style="color: #ccc;">
            <li>GDP Growth Rate</li>
            <li>Recession Probability</li>
            <li>Economic State</li>
        </ul>
        <a href="{KALSHI_MARKETS['economics']}" target="_blank" class="market-link">Browse GDP Markets</a>
    </div>
    """, unsafe_allow_html=True)

# ============================================================
# TRADING EDGE FRAMEWORK
# ============================================================
st.markdown("---")
with st.expander("📖 How to Trade Economics Markets"):
    st.markdown("""
    ## Economics Markets on Kalshi
    
    Economics markets are **event-driven** — they resolve based on official government data releases.
    
    ### Key Differences from Sports
    
    | Factor | Sports | Economics |
    |--------|--------|-----------|
    | Timing | Daily | Monthly/Quarterly |
    | Data Source | Live scores | Government releases |
    | Volatility | During games | Around release times |
    | Edge Source | Real-time signals | Forecasts vs consensus |
    
    ### Where Edge Exists
    
    **1. Consensus vs Reality**
    - Bloomberg/Reuters publish "consensus" forecasts
    - If Kalshi prices differ significantly from consensus, potential edge exists
    - But remember: markets aggregate information too
    
    **2. Timing Around Releases**
    - Prices volatile in hours before CPI/Jobs reports
    - Sharp moves possible on unexpected data
    - Liquidity can be thin near release
    
    **3. Fed Communication**
    - FOMC statement language matters
    - Press conference can move markets
    - Dot plot changes signal future path
    
    ### Risk Factors
    
    ⚠️ **Economics markets have unique risks:**
    - Government data can be revised later
    - "Whisper numbers" exist on Wall Street
    - Institutional traders have more resources
    - Binary outcomes (exact number matters)
    
    ### Decision Framework
    
    Before trading economics markets, ask:
    
    1. **Do I have an edge?** (Not just an opinion)
    2. **What's the consensus?** (Check Bloomberg, WSJ)
    3. **What's priced in?** (Check Kalshi odds)
    4. **What's my risk?** (Binary = can go to $0)
    
    ### This Tool's Purpose
    
    Economics Edge Finder provides:
    - ✅ Calendar of key dates
    - ✅ Links to relevant Kalshi markets
    - ✅ Live economic data from FRED
    - ✅ Framework for thinking about trades
    
    It does **NOT** provide:
    - ❌ Predictions of economic data
    - ❌ "Buy/Sell" signals
    - ❌ Guaranteed edges
    
    **Economics markets require more research than sports. This tool helps you know WHEN to look, not WHAT to trade.**
    """)

# ============================================================
# DISCLAIMER
# ============================================================
st.markdown("---")
st.markdown("""
<div class="legend-box">
<strong>⚠️ Important Notice:</strong> 
Economic data releases are high-stakes events with institutional participation. 
This tool provides calendar information and market links only — NOT trading recommendations.
Always do your own research. Event contracts can lose 100% of value.
</div>
""", unsafe_allow_html=True)

# ============================================================
# FOOTER WITH FRED ATTRIBUTION
# ============================================================
st.markdown("""
<div style="text-align: center; color: #666; font-size: 0.75rem; padding: 20px;">
    <p>Economic data provided by <strong>FRED®</strong>, Federal Reserve Bank of St. Louis</p>
    <p><a href="https://fred.stlouisfed.org/" target="_blank">https://fred.stlouisfed.org/</a></p>
    <p style="margin-top: 10px;">© 2025 BigSnapshot | <a href="https://bigsnapshot.com">bigsnapshot.com</a></p>
</div>
""", unsafe_allow_html=True)
