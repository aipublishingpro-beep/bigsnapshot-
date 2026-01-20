import streamlit as st
import requests
from datetime import datetime, timedelta
import pytz
import uuid

# ============================================================
# TEMP EDGE FINDER v1.3
# NWS vs Kalshi Temperature Market Edge Detection
# ============================================================

st.set_page_config(page_title="Temp Edge Finder", page_icon="🌡️", layout="wide")

# ============================================================
# GA4 TRACKING
# ============================================================
st.markdown("""
<script async src="https://www.googletagmanager.com/gtag/js?id=G-NQKY5VQ376"></script>
<script>window.dataLayer = window.dataLayer || [];function gtag(){dataLayer.push(arguments);}gtag('js', new Date());gtag('config', 'G-NQKY5VQ376');</script>
""", unsafe_allow_html=True)

if "sid" not in st.session_state:
    st.session_state["sid"] = str(uuid.uuid4())

# ============================================================
# AUTH CHECK
# ============================================================
if 'authenticated' not in st.session_state or not st.session_state.authenticated:
    st.warning("⚠️ Please log in from the Home page first.")
    st.page_link("Home.py", label="🏠 Go to Home", use_container_width=True)
    st.stop()

VERSION = "1.3"

# ============================================================
# STYLING
# ============================================================
st.markdown("""
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
.stDeployButton {display: none;}
.edge-structural { background: #166534; color: white; padding: 0.5rem 1rem; border-radius: 8px; }
.edge-marginal { background: #ca8a04; color: white; padding: 0.5rem 1rem; border-radius: 8px; }
.edge-noise { background: #525252; color: white; padding: 0.5rem 1rem; border-radius: 8px; }
</style>
""", unsafe_allow_html=True)

# ============================================================
# CITY CONFIGURATIONS - EXPANDED (17 CITIES)
# ============================================================
CITIES = {
    "NYC": {
        "name": "New York City",
        "nws_station": "KNYC",
        "nws_gridpoint": "OKX/33,37",
        "kalshi_high": "KXHIGHNY",
        "kalshi_low": "KXLOWNY",
        "lat": 40.7128,
        "lon": -74.0060,
    },
    "CHI": {
        "name": "Chicago",
        "nws_station": "KORD",
        "nws_gridpoint": "LOT/76,73",
        "kalshi_high": "KXHIGHCHI",
        "kalshi_low": "KXLOWCHI",
        "lat": 41.8781,
        "lon": -87.6298,
    },
    "MIA": {
        "name": "Miami",
        "nws_station": "KMIA",
        "nws_gridpoint": "MFL/109,50",
        "kalshi_high": "KXHIGHMIA",
        "kalshi_low": "KXLOWMIA",
        "lat": 25.7617,
        "lon": -80.1918,
    },
    "DEN": {
        "name": "Denver",
        "nws_station": "KDEN",
        "nws_gridpoint": "BOU/62,60",
        "kalshi_high": "KXHIGHDEN",
        "kalshi_low": "KXLOWDEN",
        "lat": 39.7392,
        "lon": -104.9903,
    },
    "LAX": {
        "name": "Los Angeles",
        "nws_station": "KLAX",
        "nws_gridpoint": "LOX/154,44",
        "kalshi_high": "KXHIGHLA",
        "kalshi_low": "KXLOWLA",
        "lat": 34.0522,
        "lon": -118.2437,
    },
    "PHX": {
        "name": "Phoenix",
        "nws_station": "KPHX",
        "nws_gridpoint": "PSR/159,59",
        "kalshi_high": "KXHIGHPHX",
        "kalshi_low": "KXLOWPHX",
        "lat": 33.4484,
        "lon": -112.0740,
    },
    "DFW": {
        "name": "Dallas",
        "nws_station": "KDFW",
        "nws_gridpoint": "FWD/80,108",
        "kalshi_high": "KXHIGHDFW",
        "kalshi_low": "KXLOWDFW",
        "lat": 32.7767,
        "lon": -96.7970,
    },
    "HOU": {
        "name": "Houston",
        "nws_station": "KIAH",
        "nws_gridpoint": "HGX/65,97",
        "kalshi_high": "KXHIGHHOU",
        "kalshi_low": "KXLOWHOU",
        "lat": 29.7604,
        "lon": -95.3698,
    },
    "ATL": {
        "name": "Atlanta",
        "nws_station": "KATL",
        "nws_gridpoint": "FFC/51,88",
        "kalshi_high": "KXHIGHATL",
        "kalshi_low": "KXLOWATL",
        "lat": 33.7490,
        "lon": -84.3880,
    },
    "BOS": {
        "name": "Boston",
        "nws_station": "KBOS",
        "nws_gridpoint": "BOX/71,90",
        "kalshi_high": "KXHIGHBOS",
        "kalshi_low": "KXLOWBOS",
        "lat": 42.3601,
        "lon": -71.0589,
    },
    "SEA": {
        "name": "Seattle",
        "nws_station": "KSEA",
        "nws_gridpoint": "SEW/124,67",
        "kalshi_high": "KXHIGHSEA",
        "kalshi_low": "KXLOWSEA",
        "lat": 47.6062,
        "lon": -122.3321,
    },
    "LAS": {
        "name": "Las Vegas",
        "nws_station": "KLAS",
        "nws_gridpoint": "VEF/126,97",
        "kalshi_high": "KXHIGHLAS",
        "kalshi_low": "KXLOWLAS",
        "lat": 36.1699,
        "lon": -115.1398,
    },
    "MSP": {
        "name": "Minneapolis",
        "nws_station": "KMSP",
        "nws_gridpoint": "MPX/107,71",
        "kalshi_high": "KXHIGHMSP",
        "kalshi_low": "KXLOWMSP",
        "lat": 44.9778,
        "lon": -93.2650,
    },
    "DET": {
        "name": "Detroit",
        "nws_station": "KDTW",
        "nws_gridpoint": "DTX/65,33",
        "kalshi_high": "KXHIGHDET",
        "kalshi_low": "KXLOWDET",
        "lat": 42.3314,
        "lon": -83.0458,
    },
    "PHL": {
        "name": "Philadelphia",
        "nws_station": "KPHL",
        "nws_gridpoint": "PHI/57,97",
        "kalshi_high": "KXHIGHPHL",
        "kalshi_low": "KXLOWPHL",
        "lat": 39.9526,
        "lon": -75.1652,
    },
    "SFO": {
        "name": "San Francisco",
        "nws_station": "KSFO",
        "nws_gridpoint": "MTR/84,105",
        "kalshi_high": "KXHIGHSF",
        "kalshi_low": "KXLOWSF",
        "lat": 37.7749,
        "lon": -122.4194,
    },
    "DCA": {
        "name": "Washington DC",
        "nws_station": "KDCA",
        "nws_gridpoint": "LWX/96,70",
        "kalshi_high": "KXHIGHDC",
        "kalshi_low": "KXLOWDC",
        "lat": 38.9072,
        "lon": -77.0369,
    },
}

# ============================================================
# API FUNCTIONS WITH CACHING
# ============================================================
@st.cache_data(ttl=300)
def fetch_nws_forecast(gridpoint):
    url = f"https://api.weather.gov/gridpoints/{gridpoint}/forecast"
    headers = {"User-Agent": "TempEdgeFinder/1.3 (contact@bigsnapshot.com)"}
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        return {
            "success": True,
            "data": data,
            "fetched_at": datetime.now(pytz.timezone("US/Eastern")).strftime("%I:%M %p ET"),
        }
    except Exception as e:
        return {"success": False, "error": str(e), "fetched_at": None}

@st.cache_data(ttl=300)
def fetch_nws_current(lat, lon):
    url = f"https://api.weather.gov/points/{lat},{lon}/observations/latest"
    headers = {"User-Agent": "TempEdgeFinder/1.3 (contact@bigsnapshot.com)"}
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        props = data.get("properties", {})
        temp_c = props.get("temperature", {}).get("value")
        if temp_c is not None:
            temp_f = round(temp_c * 9/5 + 32)
            return {"success": True, "temp_f": temp_f}
        return {"success": False, "temp_f": None}
    except:
        return {"success": False, "temp_f": None}

@st.cache_data(ttl=60)
def fetch_kalshi_brackets(series_ticker):
    url = "https://trading-api.kalshi.com/trade-api/v2/markets"
    params = {"series_ticker": series_ticker, "status": "open", "limit": 50}
    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        markets = data.get("markets", [])
        brackets = []
        for m in markets:
            ticker = m.get("ticker", "")
            title = m.get("title", "")
            yes_ask = m.get("yes_ask", 50)
            yes_bid = m.get("yes_bid", 50)
            no_ask = m.get("no_ask", 50)
            if yes_bid and yes_ask:
                mid_price = (yes_bid + yes_ask) / 2
            else:
                mid_price = yes_ask
            spread = abs(yes_ask - yes_bid) if yes_bid else 0
            temp_range = parse_temp_range(title)
            brackets.append({
                "ticker": ticker,
                "title": title,
                "range": temp_range,
                "yes_ask": yes_ask,
                "yes_bid": yes_bid,
                "mid_price": mid_price,
                "spread": spread,
                "no_ask": no_ask,
            })
        return {"success": True, "brackets": brackets}
    except Exception as e:
        return {"success": False, "brackets": [], "error": str(e)}

def parse_temp_range(title):
    import re
    if "or below" in title.lower():
        match = re.search(r'(\d+)', title)
        if match:
            return f"≤{match.group(1)}°F"
    elif "or above" in title.lower():
        match = re.search(r'(\d+)', title)
        if match:
            return f"≥{match.group(1)}°F"
    else:
        matches = re.findall(r'(\d+)', title)
        if len(matches) >= 2:
            return f"{matches[0]}-{matches[1]}°F"
    return title[:30]

# ============================================================
# EDGE CALCULATION ENGINE
# ============================================================
def extract_nws_temps(forecast_data, target_date):
    periods = forecast_data.get("properties", {}).get("periods", [])
    high = None
    low = None
    high_uncertainty = 0
    low_uncertainty = 0
    for period in periods:
        name = period.get("name", "").lower()
        temp = period.get("temperature")
        start_time = period.get("startTime", "")
        if target_date.strftime("%Y-%m-%d") in start_time:
            if "night" in name or "tonight" in name:
                low = temp
            elif temp:
                if high is None or temp > high:
                    high = temp
                if "day" in name or "today" in name or "afternoon" in name:
                    high = temp
    for period in periods:
        text = period.get("detailedForecast", "").lower()
        if "uncertain" in text or "variable" in text or "changing" in text:
            high_uncertainty = 3
            low_uncertainty = 3
    return {"high": high, "low": low, "high_uncertainty": high_uncertainty, "low_uncertainty": low_uncertainty}

def calc_market_implied(brackets):
    if not brackets:
        return None, None, None
    total_prob = 0
    weighted_temp = 0
    for b in brackets:
        prob = b["mid_price"] / 100
        total_prob += prob
        range_str = b["range"]
        import re
        nums = re.findall(r'\d+', range_str)
        if len(nums) >= 2:
            midpoint = (int(nums[0]) + int(nums[1])) / 2
        elif len(nums) == 1:
            midpoint = int(nums[0])
        else:
            continue
        weighted_temp += midpoint * prob
    if total_prob > 0:
        implied_temp = weighted_temp / total_prob
    else:
        implied_temp = None
    vig_warning = None
    if total_prob > 1.05:
        vig_warning = f"High vig detected ({total_prob:.0%})"
    elif total_prob < 0.95:
        vig_warning = f"Low liquidity ({total_prob:.0%})"
    return round(implied_temp, 1) if implied_temp else None, total_prob, vig_warning

def classify_edge(diff):
    abs_diff = abs(diff) if diff else 0
    if abs_diff >= 3:
        return "STRUCTURAL", "edge-structural", "High-confidence edge"
    elif abs_diff >= 2:
        return "MARGINAL", "edge-marginal", "Possible edge - caution"
    else:
        return "NOISE", "edge-noise", "No actionable edge"

def check_volatility(nws_temps):
    uncertainty = max(nws_temps.get("high_uncertainty", 0), nws_temps.get("low_uncertainty", 0))
    return uncertainty >= 3

# ============================================================
# TIME LOGIC
# ============================================================
def get_trading_window_status(now_et):
    hour = now_et.hour
    if hour < 8:
        return "PRE_WINDOW", "Markets typically open ~8 AM ET", "info"
    elif hour >= 8 and hour < 10:
        return "PRIME_WINDOW", "PRIME WINDOW (8-10 AM ET)", "success"
    elif hour >= 10 and hour < 12:
        return "LATE_WINDOW", "Late window - check spreads carefully", "warning"
    elif hour >= 12:
        return "POST_NOON", "Post-noon - most edges arbitraged", "info"
    else:
        return "ACTIVE", "Active trading window", "info"

# ============================================================
# UI COMPONENTS
# ============================================================
def render_bracket_table(brackets, nws_temp, temp_type):
    if not brackets:
        st.warning("No brackets available")
        return
    st.markdown(f"**{temp_type} Brackets:**")
    for b in sorted(brackets, key=lambda x: x.get("mid_price", 0), reverse=True):
        prob = b["mid_price"]
        spread = b["spread"]
        range_str = b["range"]
        if prob >= 70:
            color = "#22c55e"
        elif prob >= 40:
            color = "#f59e0b"
        else:
            color = "#ef4444"
        spread_icon = "⚠️" if spread >= 10 else ""
        nws_highlight = ""
        if nws_temp:
            import re
            nums = re.findall(r'\d+', range_str)
            if len(nums) >= 2:
                if int(nums[0]) <= nws_temp <= int(nums[1]):
                    nws_highlight = "← NWS"
            elif len(nums) == 1:
                temp_val = int(nums[0])
                if "≤" in range_str and nws_temp <= temp_val:
                    nws_highlight = "← NWS"
                elif "≥" in range_str and nws_temp >= temp_val:
                    nws_highlight = "← NWS"
        st.markdown(f"""
        <div style='margin-bottom: 0.5rem;'>
            <div style='display: flex; justify-content: space-between; font-size: 0.85rem;'>
                <span>{range_str} {spread_icon}</span>
                <span style='color: {color};'>{prob:.0f}¢ {nws_highlight}</span>
            </div>
            <div style='background: #333; border-radius: 4px; height: 8px; overflow: hidden;'>
                <div style='background: {color}; width: {prob}%; height: 100%;'></div>
            </div>
            <div style='font-size: 0.7rem; color: #666;'>Spread: {spread:.0f}¢ | Bid: {b['yes_bid']}¢ | Ask: {b['yes_ask']}¢</div>
        </div>
        """, unsafe_allow_html=True)

def render_edge_signal(nws_temp, market_temp, temp_type, volatility_flag):
    if nws_temp is None or market_temp is None:
        st.info(f"Insufficient data for {temp_type} edge")
        return
    diff = nws_temp - market_temp
    label, css_class, description = classify_edge(diff)
    if volatility_flag:
        st.warning(f"⚠️ Forecast volatility detected")
        label = "VOLATILE"
        css_class = "edge-noise"
        description = "Wait for convergence"
    direction = "WARM" if diff > 0 else "COLD" if diff < 0 else "NEUTRAL"
    st.markdown(f"""
    <div class='{css_class}'>
        <strong>{temp_type} EDGE: {label}</strong><br>
        <span style='font-size: 0.9rem;'>NWS: {nws_temp}°F | Market: {market_temp}°F | Diff: {diff:+.1f}°F {direction}</span><br>
        <span style='font-size: 0.8rem; opacity: 0.8;'>{description}</span>
    </div>
    """, unsafe_allow_html=True)

# ============================================================
# MAIN APP
# ============================================================
eastern = pytz.timezone("US/Eastern")
now_et = datetime.now(eastern)

st.markdown(f"""
<div style='text-align: center; padding: 1rem 0;'>
    <h1>🌡️ Temp Edge Finder</h1>
    <p style='color: #888; font-size: 0.9rem;'>NWS vs Kalshi Temperature Market Edge Detection | v{VERSION}</p>
</div>
""", unsafe_allow_html=True)

# SIDEBAR
with st.sidebar:
    st.page_link("Home.py", label="🏠 Home", use_container_width=True)
    st.divider()
    st.markdown("### Settings")
    city_code = st.selectbox(
        "Select City",
        options=list(CITIES.keys()),
        format_func=lambda x: f"{CITIES[x]['name']} ({x})"
    )
    target_date = st.date_input("Target Date", value=now_et.date() + timedelta(days=1))
    if st.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.rerun()
    st.divider()
    st.markdown("### 📖 Legend")
    st.caption("🟢 STRUCTURAL: ≥3°F diff")
    st.caption("🟡 MARGINAL: 2-3°F diff")
    st.caption("⚫ NOISE: <2°F diff")
    st.divider()
    st.caption(f"v{VERSION}")

city = CITIES[city_code]

# Trading window status
status, message, status_type = get_trading_window_status(now_et)
if status_type == "success":
    st.success(f"🟢 {message}")
elif status_type == "warning":
    st.warning(f"🟡 {message}")
else:
    st.info(f"ℹ️ {message}")

# Main columns
col1, col2 = st.columns(2)

with col1:
    st.markdown("## 🔥 High Temperature")
    nws_result = fetch_nws_forecast(city["nws_gridpoint"])
    if nws_result["success"]:
        nws_temps = extract_nws_temps(nws_result["data"], target_date)
        nws_high = nws_temps.get("high")
        volatility_high = check_volatility(nws_temps)
        st.caption(f"Last NWS update: {nws_result['fetched_at']}")
        if nws_high:
            st.metric("NWS Forecast High", f"{nws_high}°F")
        else:
            st.warning("NWS high not available for this date")
    else:
        st.error(f"NWS API error: {nws_result.get('error', 'Unknown')}")
        nws_high = None
        volatility_high = False
    
    kalshi_result = fetch_kalshi_brackets(city["kalshi_high"])
    if kalshi_result["success"] and kalshi_result["brackets"]:
        market_high, total_prob, vig_warning = calc_market_implied(kalshi_result["brackets"])
        if market_high:
            st.metric("Market Implied High", f"{market_high}°F")
        if vig_warning:
            st.caption(f"⚠️ {vig_warning}")
        if status != "LOCKED":
            render_edge_signal(nws_high, market_high, "HIGH", volatility_high)
        with st.expander("📊 Bracket Details"):
            render_bracket_table(kalshi_result["brackets"], nws_high, "High")
    else:
        st.warning("No Kalshi high temp markets found")

with col2:
    st.markdown("## ❄️ Low Temperature")
    if nws_result["success"]:
        nws_low = nws_temps.get("low")
        volatility_low = check_volatility(nws_temps)
        st.caption(f"Last NWS update: {nws_result['fetched_at']}")
        if nws_low:
            st.metric("NWS Forecast Low", f"{nws_low}°F")
        else:
            st.warning("NWS low not available for this date")
    else:
        nws_low = None
        volatility_low = False
    
    kalshi_low_result = fetch_kalshi_brackets(city["kalshi_low"])
    if kalshi_low_result["success"] and kalshi_low_result["brackets"]:
        market_low, total_prob_low, vig_warning_low = calc_market_implied(kalshi_low_result["brackets"])
        if market_low:
            st.metric("Market Implied Low", f"{market_low}°F")
        if vig_warning_low:
            st.caption(f"⚠️ {vig_warning_low}")
        if status != "LOCKED":
            render_edge_signal(nws_low, market_low, "LOW", volatility_low)
        with st.expander("📊 Bracket Details"):
            render_bracket_table(kalshi_low_result["brackets"], nws_low, "Low")
    else:
        st.warning("No Kalshi low temp markets found")

# Current temp
st.markdown("---")
current = fetch_nws_current(city["lat"], city["lon"])
if current["success"] and current["temp_f"]:
    st.markdown(f"**Current Temperature in {city['name']}:** {current['temp_f']}°F")

st.markdown("---")
st.caption(f"⚠️ For entertainment only. Not financial advice. | 🕐 {now_et.strftime('%I:%M %p ET')}")
