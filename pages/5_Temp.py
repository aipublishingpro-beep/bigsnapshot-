import streamlit as st
import requests
from datetime import datetime, timedelta
import pytz
import re

st.set_page_config(page_title="LOW Temp Edge Finder", page_icon="🌡️", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
.stApp {background-color: #0d1117;}
div[data-testid="stMarkdownContainer"] p {color: #c9d1d9;}
</style>
""", unsafe_allow_html=True)

eastern = pytz.timezone("US/Eastern")
now = datetime.now(eastern)

# ============================================================
# CITY CONFIG - 29 CITIES
# ============================================================
CITY_CONFIG = {
    "Atlanta": {"low": "KXLOWTATL", "station": "KATL", "lat": 33.63, "lon": -84.44, "tz": "US/Eastern", "pattern": "sunrise"},
    "Austin": {"low": "KXLOWTAUS", "station": "KAUS", "lat": 30.19, "lon": -97.67, "tz": "US/Central", "pattern": "sunrise"},
    "Boston": {"low": "KXLOWTBOS", "station": "KBOS", "lat": 42.36, "lon": -71.01, "tz": "US/Eastern", "pattern": "sunrise"},
    "Charlotte": {"low": "KXLOWTCLT", "station": "KCLT", "lat": 35.21, "lon": -80.94, "tz": "US/Eastern", "pattern": "sunrise"},
    "Chicago": {"low": "KXLOWTCHI", "station": "KMDW", "lat": 41.79, "lon": -87.75, "tz": "US/Central", "pattern": "midnight"},
    "Cincinnati": {"low": "KXLOWTCVG", "station": "KCVG", "lat": 39.05, "lon": -84.67, "tz": "US/Eastern", "pattern": "sunrise"},
    "Columbus": {"low": "KXLOWTCMH", "station": "KCMH", "lat": 40.00, "lon": -82.88, "tz": "US/Eastern", "pattern": "sunrise"},
    "Dallas": {"low": "KXLOWTDFW", "station": "KDFW", "lat": 32.90, "lon": -97.04, "tz": "US/Central", "pattern": "sunrise"},
    "Denver": {"low": "KXLOWTDEN", "station": "KDEN", "lat": 39.86, "lon": -104.67, "tz": "US/Mountain", "pattern": "midnight"},
    "Detroit": {"low": "KXLOWTDTW", "station": "KDTW", "lat": 42.21, "lon": -83.35, "tz": "US/Eastern", "pattern": "sunrise"},
    "Houston": {"low": "KXLOWTHOU", "station": "KHOU", "lat": 29.65, "lon": -95.28, "tz": "US/Central", "pattern": "sunrise"},
    "Indianapolis": {"low": "KXLOWTIND", "station": "KIND", "lat": 39.73, "lon": -86.27, "tz": "US/Eastern", "pattern": "sunrise"},
    "Kansas City": {"low": "KXLOWTMCI", "station": "KMCI", "lat": 39.30, "lon": -94.71, "tz": "US/Central", "pattern": "midnight"},
    "Las Vegas": {"low": "KXLOWTLAS", "station": "KLAS", "lat": 36.08, "lon": -115.15, "tz": "US/Pacific", "pattern": "sunrise"},
    "Los Angeles": {"low": "KXLOWTLAX", "station": "KLAX", "lat": 33.94, "lon": -118.41, "tz": "US/Pacific", "pattern": "sunrise"},
    "Louisville": {"low": "KXLOWTSDF", "station": "KSDF", "lat": 38.17, "lon": -85.74, "tz": "US/Eastern", "pattern": "sunrise"},
    "Memphis": {"low": "KXLOWTMEM", "station": "KMEM", "lat": 35.05, "lon": -89.98, "tz": "US/Central", "pattern": "sunrise"},
    "Miami": {"low": "KXLOWTMIA", "station": "KMIA", "lat": 25.80, "lon": -80.29, "tz": "US/Eastern", "pattern": "sunrise"},
    "Milwaukee": {"low": "KXLOWTMKE", "station": "KMKE", "lat": 42.95, "lon": -87.90, "tz": "US/Central", "pattern": "midnight"},
    "Minneapolis": {"low": "KXLOWTMSP", "station": "KMSP", "lat": 44.88, "lon": -93.22, "tz": "US/Central", "pattern": "midnight"},
    "Nashville": {"low": "KXLOWTBNA", "station": "KBNA", "lat": 36.12, "lon": -86.69, "tz": "US/Central", "pattern": "sunrise"},
    "New York City": {"low": "KXLOWTNYC", "station": "KNYC", "lat": 40.78, "lon": -73.97, "tz": "US/Eastern", "pattern": "sunrise"},
    "Oklahoma City": {"low": "KXLOWTOKC", "station": "KOKC", "lat": 35.39, "lon": -97.60, "tz": "US/Central", "pattern": "midnight"},
    "Philadelphia": {"low": "KXLOWTPHL", "station": "KPHL", "lat": 39.87, "lon": -75.23, "tz": "US/Eastern", "pattern": "sunrise"},
    "Phoenix": {"low": "KXLOWTPHX", "station": "KPHX", "lat": 33.43, "lon": -112.02, "tz": "US/Arizona", "pattern": "sunrise"},
    "Portland": {"low": "KXLOWTPDX", "station": "KPDX", "lat": 45.59, "lon": -122.60, "tz": "US/Pacific", "pattern": "sunrise"},
    "Salt Lake City": {"low": "KXLOWTSLC", "station": "KSLC", "lat": 40.79, "lon": -111.98, "tz": "US/Mountain", "pattern": "midnight"},
    "San Antonio": {"low": "KXLOWTSAT", "station": "KSAT", "lat": 29.53, "lon": -98.47, "tz": "US/Central", "pattern": "sunrise"},
    "Seattle": {"low": "KXLOWTSEA", "station": "KSEA", "lat": 47.45, "lon": -122.31, "tz": "US/Pacific", "pattern": "sunrise"},
    "St. Louis": {"low": "KXLOWTSTL", "station": "KSTL", "lat": 38.75, "lon": -90.37, "tz": "US/Central", "pattern": "midnight"},
    "Tucson": {"low": "KXLOWTTUS", "station": "KTUS", "lat": 32.13, "lon": -110.95, "tz": "US/Arizona", "pattern": "sunrise"},
    "Tulsa": {"low": "KXLOWTTUL", "station": "KTUL", "lat": 36.20, "lon": -95.89, "tz": "US/Central", "pattern": "midnight"},
}
CITY_LIST = sorted(CITY_CONFIG.keys())

# Check times in ET for owner view
CHECK_TIMES_ET = {
    "Atlanta": "7-8 AM ET",
    "Austin": "7-8 AM ET",
    "Boston": "7-8 AM ET",
    "Charlotte": "7-8 AM ET",
    "Chicago": "1-2 AM ET",
    "Cincinnati": "7-8 AM ET",
    "Columbus": "7-8 AM ET",
    "Dallas": "7-8 AM ET",
    "Denver": "2-3 AM ET",
    "Detroit": "7-8 AM ET",
    "Houston": "7-8 AM ET",
    "Indianapolis": "7-8 AM ET",
    "Kansas City": "2-3 AM ET",
    "Las Vegas": "9-10 AM ET",
    "Los Angeles": "9-10 AM ET",
    "Louisville": "7-8 AM ET",
    "Memphis": "7-8 AM ET",
    "Miami": "7-8 AM ET",
    "Milwaukee": "1-2 AM ET",
    "Minneapolis": "1-2 AM ET",
    "Nashville": "7-8 AM ET",
    "New York City": "7-8 AM ET",
    "Oklahoma City": "2-3 AM ET",
    "Philadelphia": "7-8 AM ET",
    "Phoenix": "8-9 AM ET",
    "Portland": "9-10 AM ET",
    "Salt Lake City": "3-4 AM ET",
    "San Antonio": "7-8 AM ET",
    "Seattle": "9-10 AM ET",
    "St. Louis": "2-3 AM ET",
    "Tucson": "8-9 AM ET",
    "Tulsa": "2-3 AM ET",
}

query_params = st.query_params
default_city = query_params.get("city", "New York City")
if default_city not in CITY_LIST:
    default_city = "New York City"
is_owner = query_params.get("mode") == "owner"

if "view_mode" not in st.session_state:
    st.session_state.view_mode = "city"
if "night_scan_on" not in st.session_state:
    st.session_state.night_scan_on = False
if "night_locked_city" not in st.session_state:
    st.session_state.night_locked_city = None
if "hold_list" not in st.session_state:
    st.session_state.hold_list = []

NIGHT_SCAN_CITIES = ["Phoenix", "Denver", "Chicago", "Houston", "Dallas", "Atlanta", "Detroit"]

# ============================================================
# FUNCTIONS
# ============================================================
@st.cache_data(ttl=120)
def fetch_nws_observations(station, city_tz_str):
    url = f"https://api.weather.gov/stations/{station}/observations"
    try:
        city_tz = pytz.timezone(city_tz_str)
        resp = requests.get(url, headers={"User-Agent": "TempEdge/7.0"}, timeout=15)
        if resp.status_code != 200:
            return None, None, None, [], None, None, None
        observations = resp.json().get("features", [])
        if not observations:
            return None, None, None, [], None, None, None
        today = datetime.now(city_tz).date()
        readings = []
        for obs in observations:
            props = obs.get("properties", {})
            timestamp_str = props.get("timestamp", "")
            temp_c = props.get("temperature", {}).get("value")
            if not timestamp_str or temp_c is None:
                continue
            try:
                ts = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
                ts_local = ts.astimezone(city_tz)
                if ts_local.date() == today:
                    temp_f = round(temp_c * 9/5 + 32, 1)
                    readings.append({"time": ts_local, "temp": temp_f})
            except:
                continue
        if not readings:
            return None, None, None, [], None, None, None
        readings.sort(key=lambda x: x["time"], reverse=True)
        current = readings[0]["temp"]
        obs_low = min(r["temp"] for r in readings)
        obs_high = max(r["temp"] for r in readings)
        readings_chrono = sorted(readings, key=lambda x: x["time"])
        confirm_time = None
        low_found = False
        for r in readings_chrono:
            if r["temp"] == obs_low:
                low_found = True
            elif low_found and r["temp"] > obs_low:
                confirm_time = r["time"]
                break
        oldest_time = readings_chrono[0]["time"] if readings_chrono else None
        newest_time = readings_chrono[-1]["time"] if readings_chrono else None
        display_readings = [{"time": r["time"].strftime("%H:%M"), "temp": r["temp"]} for r in readings]
        return current, obs_low, obs_high, display_readings, confirm_time, oldest_time, newest_time
    except:
        return None, None, None, [], None, None, None

@st.cache_data(ttl=300)
def fetch_nws_forecast(lat, lon):
    try:
        points_url = f"https://api.weather.gov/points/{lat},{lon}"
        resp = requests.get(points_url, headers={"User-Agent": "TempEdge/7.0"}, timeout=10)
        if resp.status_code != 200:
            return None
        forecast_url = resp.json().get("properties", {}).get("forecast")
        if not forecast_url:
            return None
        resp = requests.get(forecast_url, headers={"User-Agent": "TempEdge/7.0"}, timeout=10)
        if resp.status_code != 200:
            return None
        periods = resp.json().get("properties", {}).get("periods", [])
        return periods[:4] if periods else None
    except:
        return None

@st.cache_data(ttl=300)
def fetch_nws_tomorrow_low(lat, lon):
    try:
        points_url = f"https://api.weather.gov/points/{lat},{lon}"
        resp = requests.get(points_url, headers={"User-Agent": "TempEdge/7.0"}, timeout=10)
        if resp.status_code != 200:
            return None
        forecast_url = resp.json().get("properties", {}).get("forecast")
        if not forecast_url:
            return None
        resp = requests.get(forecast_url, headers={"User-Agent": "TempEdge/7.0"}, timeout=10)
        if resp.status_code != 200:
            return None
        periods = resp.json().get("properties", {}).get("periods", [])
        tomorrow = (datetime.now(eastern) + timedelta(days=1)).date()
        for p in periods:
            start_time = p.get("startTime", "")
            is_day = p.get("isDaytime", True)
            temp = p.get("temperature")
            if start_time and not is_day:
                try:
                    period_date = datetime.fromisoformat(start_time.replace("Z", "+00:00")).date()
                    if period_date == tomorrow:
                        return temp
                except:
                    continue
        return None
    except:
        return None

@st.cache_data(ttl=60)
def fetch_kalshi_brackets(series_ticker):
    url = f"https://api.elections.kalshi.com/trade-api/v2/markets?series_ticker={series_ticker}&status=open"
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code != 200:
            return []
        markets = resp.json().get("markets", [])
        if not markets:
            return []
        today_str = datetime.now(eastern).strftime('%y%b%d').upper()
        today_markets = [m for m in markets if today_str in m.get("event_ticker", "").upper()]
        if not today_markets:
            first_event = markets[0].get("event_ticker", "")
            today_markets = [m for m in markets if m.get("event_ticker") == first_event]
        brackets = []
        for m in today_markets:
            title = m.get("title", "")
            yes_bid = m.get("yes_bid", 0) or 0
            yes_ask = m.get("yes_ask", 0) or 0
            low_bound, high_bound, bracket_name = None, None, ""
            range_match = re.search(r'(\d+)\s*[-–to]+\s*(\d+)°', title)
            if range_match:
                low_bound = int(range_match.group(1))
                high_bound = int(range_match.group(2))
                bracket_name = f"{low_bound}-{high_bound}°"
            above_match = re.search(r'(\d+)°?\s*(or above|or more|at least|\+)', title, re.IGNORECASE)
            if above_match and not range_match:
                low_bound = int(above_match.group(1))
                high_bound = 999
                bracket_name = f"{low_bound}°+"
            below_match = re.search(r'(below|under|less than)\s*(\d+)°', title, re.IGNORECASE)
            if below_match and not range_match:
                high_bound = int(below_match.group(2))
                low_bound = -999
                bracket_name = f"<{high_bound}°"
            if low_bound is not None and high_bound is not None:
                kalshi_url = f"https://kalshi.com/markets/{series_ticker.lower()}"
                brackets.append({"name": bracket_name, "low": low_bound, "high": high_bound, "bid": yes_bid, "ask": yes_ask, "url": kalshi_url})
        brackets.sort(key=lambda x: x['low'])
        return brackets
    except:
        return []

@st.cache_data(ttl=60)
def fetch_kalshi_tomorrow_brackets(series_ticker):
    url = f"https://api.elections.kalshi.com/trade-api/v2/markets?series_ticker={series_ticker}&status=open"
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code != 200:
            return []
        markets = resp.json().get("markets", [])
        if not markets:
            return []
        tomorrow = datetime.now(eastern) + timedelta(days=1)
        tomorrow_str = tomorrow.strftime('%y%b%d').upper()
        tomorrow_markets = [m for m in markets if tomorrow_str in m.get("event_ticker", "").upper()]
        if not tomorrow_markets:
            return []
        brackets = []
        for m in tomorrow_markets:
            title = m.get("title", "")
            yes_bid = m.get("yes_bid", 0) or 0
            yes_ask = m.get("yes_ask", 0) or 0
            low_bound, high_bound, bracket_name = None, None, ""
            range_match = re.search(r'(\d+)\s*[-–to]+\s*(\d+)°', title)
            if range_match:
                low_bound = int(range_match.group(1))
                high_bound = int(range_match.group(2))
                bracket_name = f"{low_bound}-{high_bound}°"
            above_match = re.search(r'(\d+)°?\s*(or above|or more|at least|\+)', title, re.IGNORECASE)
            if above_match and not range_match:
                low_bound = int(above_match.group(1))
                high_bound = 999
                bracket_name = f"{low_bound}°+"
            below_match = re.search(r'(below|under|less than)\s*(\d+)°', title, re.IGNORECASE)
            if below_match and not range_match:
                high_bound = int(below_match.group(2))
                low_bound = -999
                bracket_name = f"<{high_bound}°"
            if low_bound is not None and high_bound is not None:
                kalshi_url = f"https://kalshi.com/markets/{series_ticker.lower()}"
                brackets.append({"name": bracket_name, "low": low_bound, "high": high_bound, "bid": yes_bid, "ask": yes_ask, "url": kalshi_url})
        brackets.sort(key=lambda x: x['low'])
        return brackets
    except:
        return []

def find_winning_bracket(temp, brackets):
    if temp is None or not brackets:
        return None
    rounded_temp = round(temp)
    for b in brackets:
        if b['high'] == 999 and rounded_temp >= b['low']:
            return b
        if b['low'] == -999 and rounded_temp < b['high']:
            return b
        if b['low'] <= rounded_temp <= b['high']:
            return b
    return None

def get_lock_status(cfg, confirm_time, obs_low, readings):
    if obs_low is None or not readings:
        return "no_data", "❌ NO DATA", 0
    rising_count = 0
    found_low = False
    for r in readings:
        if r["temp"] == obs_low:
            found_low = True
        elif found_low and r["temp"] > obs_low:
            rising_count += 1
            if rising_count >= 5:
                break
    if confirm_time and rising_count >= 2:
        return "locked", "🔒 LOCKED", 95
    elif confirm_time or rising_count >= 2:
        return "likely", "🔒 LIKELY", 80
    elif rising_count >= 1:
        return "watching", "👀 RISING", 60
    else:
        return "waiting", "⏳ WAITING", 30

# ============================================================
# SIDEBAR
# ============================================================
if is_owner:
    with st.sidebar:
        st.markdown("""
        <div style="background:#1a2e1a;border:1px solid #22c55e;border-radius:8px;padding:12px;margin-bottom:15px">
            <div style="color:#22c55e;font-weight:700;margin-bottom:8px">🎯 CONFIRMATION SIGNALS</div>
            <div style="color:#c9d1d9;font-size:0.85em;line-height:1.5">
                <b>🔒 LOCKED (95%):</b> Confirmed + 2 rising<br>
                <b>🔒 LIKELY (80%):</b> Confirmation OR 2+ rising<br>
                <b>👀 RISING (60%):</b> 1 rising reading<br>
                <b>⏳ WAITING:</b> No rising yet
            </div>
        </div>
        <div style="background:#2d1f0a;border:1px solid #f59e0b;border-radius:8px;padding:12px;margin-bottom:15px">
            <div style="color:#f59e0b;font-weight:700;margin-bottom:8px">🗽 YOUR TRADING SCHEDULE (ET)</div>
            <div style="color:#c9d1d9;font-size:0.75em;line-height:1.5">
                <b>🌙 1-2 AM</b> → Chicago, Milwaukee, Minneapolis<br>
                <b>🌙 2-3 AM</b> → Denver, KC, OKC, STL, Tulsa<br>
                <b>🌙 3-4 AM</b> → Salt Lake City<br>
                <b>☀️ 7-8 AM</b> → ATL, Austin, Boston, Charlotte, Cincy, Columbus, Dallas, Detroit, Houston, Indy, Louisville, Memphis, Miami, Nashville, NYC, Philly, San Antonio<br>
                <b>☀️ 8-9 AM</b> → Phoenix, Tucson<br>
                <b>☀️ 9-10 AM</b> → LA, Las Vegas, Portland, Seattle
            </div>
        </div>
        <div style="background:#1a1a2e;border:1px solid #3b82f6;border-radius:8px;padding:12px;margin-bottom:15px">
            <div style="color:#3b82f6;font-weight:700;margin-bottom:8px">📅 SEASONAL LOCK-IN TIMES</div>
            <div style="color:#c9d1d9;font-size:0.8em;line-height:1.6">
                <b>❄️ Winter</b> (Nov-Feb): 6-7 AM local<br>
                <b>🌸 Spring</b> (Mar-Apr): 5-6 AM local<br>
                <b>☀️ Summer</b> (May-Aug): 5-6 AM local<br>
                <b>🍂 Fall</b> (Sep-Oct): 6-7 AM local<br>
                <span style="color:#6b7280;font-size:0.85em">LOW locks around sunrise ±30 min</span>
            </div>
        </div>
        <div style="background:#1a1a2e;border:1px solid #22c55e;border-radius:8px;padding:12px;margin-bottom:15px">
            <div style="color:#22c55e;font-weight:700;margin-bottom:8px">💰 ENTRY THRESHOLDS (Ask)</div>
            <div style="color:#c9d1d9;font-size:0.8em;line-height:1.6">
                <b>🔥 &lt;85¢</b> = JUMP IN (+15¢)<br>
                <b>✅ 85-90¢</b> = Good (+10-15¢)<br>
                <b>⚠️ 90-95¢</b> = Small edge (+5-10¢)<br>
                <b>❌ 95¢+</b> = Skip it
            </div>
        </div>
        """, unsafe_allow_html=True)
else:
    with st.sidebar:
        st.markdown("""
        <div style="background:#1a1a2e;border:1px solid #3b82f6;border-radius:8px;padding:12px;margin-bottom:15px">
            <div style="color:#3b82f6;font-weight:700;margin-bottom:8px">⏰ LOW WINDOWS</div>
            <div style="color:#c9d1d9;font-size:0.8em;line-height:1.6">
                <b>🌙 Midnight:</b> Chicago, Denver, KC, Milwaukee, Minneapolis, OKC, SLC, STL, Tulsa<br>
                <b>☀️ Sunrise:</b> All other cities
            </div>
        </div>
        """, unsafe_allow_html=True)

# ============================================================
# HEADER
# ============================================================
st.title("🌡️ LOW TEMP EDGE FINDER")
st.caption(f"Live NWS + Kalshi | {now.strftime('%b %d, %Y %I:%M %p ET')} | 32 Cities")

if is_owner:
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        if st.button("📍 City View", use_container_width=True, type="primary" if st.session_state.view_mode == "city" else "secondary"):
            st.session_state.view_mode = "city"
            st.rerun()
    with c2:
        if st.button("🔍 Today Scanner", use_container_width=True, type="primary" if st.session_state.view_mode == "today" else "secondary"):
            st.session_state.view_mode = "today"
            st.rerun()
    with c3:
        if st.button("🎰 Tomorrow Lottery", use_container_width=True, type="primary" if st.session_state.view_mode == "tomorrow" else "secondary"):
            st.session_state.view_mode = "tomorrow"
            st.rerun()
    with c4:
        if st.button("🦈 Night Scan", use_container_width=True, type="primary" if st.session_state.view_mode == "night" else "secondary"):
            st.session_state.view_mode = "night"
            st.rerun()
    st.markdown("---")

# ============================================================
# TODAY'S SCANNER (OWNER ONLY)
# ============================================================
if is_owner and st.session_state.view_mode == "today":
    st.subheader("🔍 TODAY'S MISPRICING SCANNER")
    if st.button("🔄 Refresh All", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    
    results = []
    progress = st.progress(0)
    city_items = list(CITY_CONFIG.items())
    for idx, (city_name, cfg) in enumerate(city_items):
        progress.progress((idx + 1) / len(city_items))
        current_temp, obs_low, obs_high, readings, confirm_time, oldest_time, newest_time = fetch_nws_observations(cfg["station"], cfg["tz"])
        brackets = fetch_kalshi_brackets(cfg["low"])
        pattern_icon = "🌙" if cfg.get("pattern") == "midnight" else "☀️"
        
        if obs_low is None:
            results.append({"city": city_name, "pattern": pattern_icon, "status": "NO DATA"})
            continue
        
        status_code, lock_status, confidence = get_lock_status(cfg, confirm_time, obs_low, readings)
        winning = find_winning_bracket(obs_low, brackets)
        
        if winning:
            edge = (100 - winning["ask"]) if status_code in ["locked", "likely"] else 0
            results.append({
                "city": city_name, 
                "pattern": pattern_icon, 
                "obs_low": obs_low, 
                "bracket": winning["name"], 
                "ask": winning["ask"], 
                "edge": edge, 
                "lock_status": lock_status, 
                "status_code": status_code,
                "url": winning["url"]
            })
        else:
            results.append({
                "city": city_name, 
                "pattern": pattern_icon, 
                "obs_low": obs_low, 
                "bracket": "NO MATCH", 
                "ask": 0, 
                "edge": 0, 
                "lock_status": lock_status,
                "status_code": status_code
            })
    progress.empty()
    
    opps = [r for r in results if r.get("edge", 0) >= 5]
    if opps:
        st.markdown("### 🔥 OPPORTUNITIES (Edge ≥ 5¢)")
        for o in sorted(opps, key=lambda x: x["edge"], reverse=True):
            color = "#22c55e" if o["edge"] >= 15 else "#fbbf24"
            st.markdown(f"""
            <div style="background:#0d1117;border:2px solid {color};border-radius:8px;padding:15px;margin:10px 0">
                <b style="color:{color}">{o['pattern']} {o['city']}</b> | {o['lock_status']} | 
                Low: {o['obs_low']}°F → <b>{o['bracket']}</b> | Ask: {o['ask']}¢ | 
                <b style="color:#22c55e">+{o['edge']}¢ edge</b> | 
                <a href="{o.get('url', '#')}" target="_blank" style="color:#fbbf24">BUY →</a>
            </div>
            """, unsafe_allow_html=True)
    else:
        if now.hour >= 10:
            st.warning("⏰ TODAY'S MARKETS LIKELY DONE - Check Tomorrow's Lottery!")
        else:
            st.info("No mispricing found yet. Markets may already be priced efficiently.")
    
    st.markdown("### 📊 ALL CITIES STATUS")
    for r in results:
        if r.get("status") == "NO DATA":
            st.write(f"{r['pattern']} **{r['city']}** — ❌ No data")
        else:
            status_color = "🟢" if r.get("status_code") == "locked" else "🟡" if r.get("status_code") == "likely" else "⚪"
            st.write(f"{r['pattern']} **{r['city']}** | {r['lock_status']} | {r['obs_low']}°F → {r.get('bracket', 'N/A')} | Ask: {r.get('ask', 0)}¢")

# ============================================================
# TOMORROW'S LOTTERY (OWNER ONLY)
# ============================================================
elif is_owner and st.session_state.view_mode == "tomorrow":
    tomorrow_str = (datetime.now(eastern) + timedelta(days=1)).strftime('%A, %b %d')
    st.subheader(f"🎰 TOMORROW'S LOTTERY ({tomorrow_str})")
    st.caption("Scout targets now → Wait for LOW to lock → Buy confirmed winners")
    
    if st.button("🔄 Refresh All", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    
    st.markdown("""
    <div style="background:#1a2e1a;border:1px solid #22c55e;border-radius:8px;padding:15px;margin-bottom:20px">
        <div style="color:#22c55e;font-weight:700">💡 TOMORROW'S TARGETS</div>
        <div style="color:#c9d1d9;font-size:0.9em">
            Scout cheap brackets now → Check back at lock time → Buy only after LOW confirmed
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    tickets = []
    all_cities = []
    progress = st.progress(0)
    city_items = list(CITY_CONFIG.items())
    for idx, (city_name, cfg) in enumerate(city_items):
        progress.progress((idx + 1) / len(city_items))
        pattern_icon = "🌙" if cfg.get("pattern") == "midnight" else "☀️"
        forecast_low = fetch_nws_tomorrow_low(cfg["lat"], cfg["lon"])
        brackets = fetch_kalshi_tomorrow_brackets(cfg["low"])
        
        if forecast_low is None:
            all_cities.append({"city": city_name, "pattern": pattern_icon, "status": "NO FORECAST"})
            continue
        if not brackets:
            all_cities.append({"city": city_name, "pattern": pattern_icon, "status": "NO MARKET", "forecast": forecast_low})
            continue
        
        winning = find_winning_bracket(forecast_low, brackets)
        if winning:
            data = {
                "city": city_name, 
                "pattern": pattern_icon, 
                "forecast": forecast_low, 
                "bracket": winning["name"], 
                "ask": winning["ask"], 
                "url": winning["url"]
            }
            all_cities.append(data)
            if winning["ask"] < 60:
                tickets.append(data)
        else:
            all_cities.append({"city": city_name, "pattern": pattern_icon, "status": "NO BRACKET", "forecast": forecast_low})
    progress.empty()
    
    if tickets:
        st.markdown("### 🎰 CHEAP ENTRIES (<60¢)")
        for t in sorted(tickets, key=lambda x: x["ask"]):
            color = "#fbbf24" if t["ask"] < 40 else "#22c55e"
            check_time = CHECK_TIMES_ET.get(t['city'], "7-10 AM ET")
            st.markdown(f"""
            <div style="background:#0d1117;border:2px solid {color};border-radius:8px;padding:15px;margin:10px 0">
                <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:10px">
                    <div>
                        <b style="color:{color}">{t['pattern']} {t['city']}</b> | NWS: {t['forecast']}°F → <b>{t['bracket']}</b> | 
                        Ask: <b style="color:#22c55e">{t['ask']}¢</b>
                    </div>
                    <a href="{t['url']}" target="_blank" style="color:#fbbf24;text-decoration:none">Preview Market →</a>
                </div>
                <div style="margin-top:10px;padding:8px;background:#1a1a2e;border-radius:6px;text-align:center">
                    <span style="color:#9ca3af">⏰ LOW locks:</span> <b style="color:#3b82f6">{check_time}</b>
                    <span style="color:#6b7280;margin-left:10px">— Check back then to confirm winner</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No cheap entries found. All brackets priced above 60¢.")
    
    st.markdown(f"### 📋 ALL CITIES - {tomorrow_str}")
    for c in all_cities:
        check_time = CHECK_TIMES_ET.get(c['city'], "7-10 AM ET")
        if c.get("status") == "NO FORECAST":
            st.write(f"{c['pattern']} **{c['city']}** — ❌ No forecast available")
        elif c.get("status") == "NO MARKET":
            st.write(f"{c['pattern']} **{c['city']}** — NWS: {c['forecast']}°F — Market not open yet | ⏰ {check_time}")
        elif c.get("status") == "NO BRACKET":
            st.write(f"{c['pattern']} **{c['city']}** — NWS: {c['forecast']}°F — No matching bracket")
        else:
            st.write(f"{c['pattern']} **{c['city']}** | NWS: {c['forecast']}°F → {c['bracket']} | Ask: {c['ask']}¢ | ⏰ {check_time}")

# ============================================================
# NIGHT SCAN (OWNER ONLY)
# ============================================================
elif is_owner and st.session_state.view_mode == "night":
    st.subheader("🦈 NIGHT SCAN")
    
    # Toggle button
    if st.session_state.night_scan_on:
        if st.button("🦈 Night Scan ON", use_container_width=True, type="primary"):
            st.session_state.night_scan_on = False
            st.session_state.night_locked_city = None
            st.rerun()
        st.markdown('<div style="background:#166534;border:2px solid #22c55e;border-radius:8px;padding:10px;text-align:center;margin:10px 0"><b style="color:#4ade80">● SCANNING ACTIVE</b></div>', unsafe_allow_html=True)
    else:
        if st.button("🦈 Night Scan OFF", use_container_width=True, type="secondary"):
            st.session_state.night_scan_on = True
            st.session_state.night_locked_city = None
            st.session_state.hold_list = []
            st.rerun()
        st.markdown('<div style="background:#7f1d1d;border:2px solid #ef4444;border-radius:8px;padding:10px;text-align:center;margin:10px 0"><b style="color:#fca5a5">● SCAN OFF</b></div>', unsafe_allow_html=True)
    
    st.caption(f"Watching: {', '.join(NIGHT_SCAN_CITIES)} | Auto-refresh: 5 min")
    
    # If already locked, show hold list
    if st.session_state.night_locked_city:
        locked = st.session_state.night_locked_city
        cfg = CITY_CONFIG.get(locked["city"], {})
        brackets = fetch_kalshi_brackets(cfg["low"])
        winning = find_winning_bracket(locked["obs_low"], brackets)
        current_bid = winning["bid"] if winning else locked["bid"]
        current_ask = winning["ask"] if winning else locked["ask"]
        
        st.markdown(f"""
        <div style="background:#0d1117;border:4px solid #22c55e;border-radius:16px;padding:30px;margin:20px 0;text-align:center;animation:pulse 2s infinite;box-shadow:0 0 40px rgba(34,197,94,0.5)">
            <div style="color:#22c55e;font-size:2em;font-weight:800;margin-bottom:10px">🔒 LOW LOCKED</div>
            <div style="color:#fff;font-size:3em;font-weight:800">{locked['city']}</div>
            <div style="color:#fbbf24;font-size:1.5em;margin:15px 0">{locked['obs_low']}°F → {locked['bracket']}</div>
            <div style="color:#9ca3af;font-size:1.2em">Bid: <b style="color:#3b82f6">{current_bid}¢</b> | Ask: <b style="color:#22c55e">{current_ask}¢</b></div>
        </div>
        <style>@keyframes pulse{{0%,100%{{box-shadow:0 0 20px rgba(34,197,94,0.3)}}50%{{box-shadow:0 0 60px rgba(34,197,94,0.8)}}}}</style>
        <script>
        (function(){{
            const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
            const duration = 5;
            const freq = 800;
            const osc = audioCtx.createOscillator();
            const gain = audioCtx.createGain();
            osc.connect(gain);
            gain.connect(audioCtx.destination);
            osc.frequency.value = freq;
            osc.type = 'sine';
            gain.gain.value = 0.3;
            osc.start();
            osc.stop(audioCtx.currentTime + duration);
        }})();
        </script>
        """, unsafe_allow_html=True)
        
        st.markdown(f'<a href="{locked["url"]}" target="_blank"><div style="background:#22c55e;color:#000;font-size:1.5em;font-weight:800;padding:20px;border-radius:12px;text-align:center;margin:20px 0;cursor:pointer">🚀 BUY NOW →</div></a>', unsafe_allow_html=True)
        
        if st.button("🔄 Refresh Prices", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        
        st.markdown("### 📋 Hold List")
        st.markdown(f"""
        <div style="background:#161b22;border:1px solid #30363d;border-radius:8px;padding:15px">
            <div style="display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid #30363d">
                <span style="color:#9ca3af">City</span>
                <span style="color:#9ca3af">Low</span>
                <span style="color:#9ca3af">Bracket</span>
                <span style="color:#9ca3af">Bid/Ask</span>
            </div>
            <div style="display:flex;justify-content:space-between;padding:8px 0">
                <span style="color:#22c55e;font-weight:700">{locked['city']}</span>
                <span style="color:#fff">{locked['obs_low']}°F</span>
                <span style="color:#fbbf24">{locked['bracket']}</span>
                <span style="color:#fff">{current_bid}¢/{current_ask}¢</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Active scanning
    elif st.session_state.night_scan_on:
        st.markdown("### 🔍 Scanning...")
        
        for city_name in NIGHT_SCAN_CITIES:
            cfg = CITY_CONFIG.get(city_name, {})
            current_temp, obs_low, obs_high, readings, confirm_time, oldest_time, newest_time = fetch_nws_observations(cfg["station"], cfg["tz"])
            brackets = fetch_kalshi_brackets(cfg["low"])
            
            if obs_low is None:
                st.write(f"⚪ **{city_name}** — No data")
                continue
            
            rising_count = 0
            found_low = False
            for r in readings:
                if r["temp"] == obs_low:
                    found_low = True
                elif found_low and r["temp"] > obs_low:
                    rising_count += 1
            
            winning = find_winning_bracket(obs_low, brackets)
            
            if rising_count >= 2 and winning:
                # LOCKED - First city wins
                st.session_state.night_locked_city = {
                    "city": city_name,
                    "obs_low": obs_low,
                    "bracket": winning["name"],
                    "bid": winning["bid"],
                    "ask": winning["ask"],
                    "url": winning["url"]
                }
                st.session_state.hold_list.append(st.session_state.night_locked_city)
                st.rerun()
            elif rising_count >= 1:
                st.write(f"👀 **{city_name}** | {obs_low}°F | Rising: {rising_count}")
            else:
                st.write(f"⏳ **{city_name}** | {obs_low}°F | Waiting...")
        
        # Auto-refresh every 5 minutes
        import time
        time.sleep(0.1)
        st.markdown(f"<div style='color:#6b7280;font-size:0.8em;text-align:center;margin-top:20px'>Next refresh in 5 min | {now.strftime('%I:%M:%S %p ET')}</div>", unsafe_allow_html=True)
        st_autorefresh = st.empty()
        st.markdown("""<meta http-equiv="refresh" content="300">""", unsafe_allow_html=True)
    
    else:
        st.info("Toggle Night Scan ON to start watching for locks.")

# ============================================================
# CITY VIEW (DEFAULT)
# ============================================================
else:
    c1, c2 = st.columns([4, 1])
    with c1:
        city = st.selectbox("📍 Select City", CITY_LIST, index=CITY_LIST.index(default_city))
    with c2:
        if st.button("🔄", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    
    cfg = CITY_CONFIG.get(city, {})
    current_temp, obs_low, obs_high, readings, confirm_time, oldest_time, newest_time = fetch_nws_observations(cfg.get("station", "KNYC"), cfg.get("tz", "US/Eastern"))
    
    if obs_low is not None and current_temp is not None:
        status_code, lock_status, confidence = get_lock_status(cfg, confirm_time, obs_low, readings)
        
        if is_owner:
            city_tz = pytz.timezone(cfg.get("tz", "US/Eastern"))
            hour = datetime.now(city_tz).hour
            if confirm_time:
                mins_ago = int((datetime.now(city_tz) - confirm_time).total_seconds() / 60)
                time_ago_text = f"Confirmed {mins_ago} minutes ago" if 0 <= mins_ago < 1440 else "Check readings below"
            else:
                time_ago_text = "Awaiting rise after low..."
            data_warning = ""
            if oldest_time and oldest_time.hour >= 7:
                data_warning = f"⚠️ Data only from {oldest_time.strftime('%H:%M')} - early low may be missing!"
            if status_code == "locked":
                box_status, lock_color, box_bg = "✅ LOCKED IN", "#22c55e", "linear-gradient(135deg,#1a2e1a,#0d1117)"
            elif status_code == "likely":
                box_status, lock_color, box_bg = "🔒 LIKELY LOCKED", "#3b82f6", "linear-gradient(135deg,#1a1a2e,#0d1117)"
            else:
                box_status, lock_color, box_bg = "⏳ MAY STILL DROP", "#f59e0b", "linear-gradient(135deg,#2d1f0a,#0d1117)"
            st.markdown(f"""
            <div style="background:{box_bg};border:3px solid {lock_color};border-radius:16px;padding:30px;margin:20px 0;text-align:center">
                <div style="color:{lock_color};font-size:1.2em;font-weight:700;margin-bottom:10px">{box_status}</div>
                <div style="color:#6b7280;font-size:0.9em">Today's Low (from available data)</div>
                <div style="color:#fff;font-size:4em;font-weight:800;margin:10px 0">{obs_low}°F</div>
                <div style="color:#9ca3af;font-size:0.9em">{time_ago_text}</div>
                <div style="color:#f59e0b;font-size:0.85em;margin-top:10px">{data_warning}</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            lock_color = "#22c55e" if status_code == "locked" else "#3b82f6" if status_code == "likely" else "#fbbf24" if status_code == "watching" else "#6b7280"
            st.markdown(f"""
            <div style="background:linear-gradient(135deg,#1a1a2e,#0d1117);border:3px solid {lock_color};border-radius:16px;padding:25px;margin:20px 0;text-align:center;box-shadow:0 0 20px rgba(59,130,246,0.3)">
                <div style="color:#6b7280;font-size:1em;margin-bottom:5px">📊 Today's Recorded Low</div>
                <div style="color:{lock_color};font-size:4.5em;font-weight:800;margin:10px 0;text-shadow:0 0 20px rgba(59,130,246,0.5)">{obs_low}°F</div>
                <div style="color:#9ca3af;font-size:0.9em">From NWS Station: <span style="color:#22c55e;font-weight:600">{cfg.get('station', 'N/A')}</span></div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <div style="background:#161b22;border:1px solid #30363d;border-radius:8px;padding:15px;margin:10px 0">
            <div style="display:flex;justify-content:space-around;text-align:center;flex-wrap:wrap;gap:15px">
                <div><div style="color:#6b7280;font-size:0.8em">CURRENT TEMP</div><div style="color:#fff;font-size:1.8em;font-weight:700">{current_temp}°F</div></div>
                <div><div style="color:#6b7280;font-size:0.8em">TODAY'S HIGH</div><div style="color:#ef4444;font-size:1.8em;font-weight:700">{obs_high}°F</div></div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        brackets = fetch_kalshi_brackets(cfg["low"])
        winning = find_winning_bracket(obs_low, brackets)
        
        if winning:
            st.markdown("### 🎯 Kalshi Market")
            edge = (100 - winning["ask"]) if status_code in ["locked", "likely"] else 0
            edge_text = f" | **+{edge}¢ edge**" if edge > 0 else ""
            st.markdown(f"""
            <div style="background:#1a2e1a;border:1px solid #22c55e;border-radius:8px;padding:15px;margin:10px 0">
                <b style="color:#22c55e">Winning Bracket: {winning['name']}</b><br>
                Bid: {winning['bid']}¢ | Ask: {winning['ask']}¢{edge_text}<br>
                <a href="{winning['url']}" target="_blank" style="color:#fbbf24">View on Kalshi →</a>
            </div>
            """, unsafe_allow_html=True)
        
        if readings:
            with st.expander("📊 Recent NWS Observations", expanded=True):
                if oldest_time and newest_time:
                    st.markdown(f"<div style='color:#6b7280;font-size:0.8em;margin-bottom:10px;text-align:center'>📅 Data: {oldest_time.strftime('%H:%M')} to {newest_time.strftime('%H:%M')} local</div>", unsafe_allow_html=True)
                display_list = readings if is_owner else readings[:8]
                low_idx = next((i for i, r in enumerate(display_list) if r['temp'] == obs_low), None)
                confirm_idx = (low_idx - 2) if (low_idx is not None and low_idx >= 2) else None
                for i, r in enumerate(display_list):
                    if is_owner and confirm_idx is not None and i == confirm_idx:
                        st.markdown(f'<div style="display:flex;justify-content:center;padding:8px;border-radius:4px;background:#166534;border:2px solid #22c55e;margin:4px 0"><span style="color:#4ade80;font-weight:700">✅ CONFIRMED LOW</span></div>', unsafe_allow_html=True)
                    if i == low_idx:
                        row_style = "display:flex;justify-content:space-between;padding:6px 8px;border-radius:4px;background:#2d1f0a;border:1px solid #f59e0b;margin:2px 0"
                        temp_style = "color:#fbbf24;font-weight:700"
                        label = " ↩️ LOW"
                    else:
                        row_style = "display:flex;justify-content:space-between;padding:4px 8px;border-bottom:1px solid #30363d"
                        temp_style = "color:#fff;font-weight:600"
                        label = ""
                    st.markdown(f"<div style='{row_style}'><span style='color:#9ca3af;min-width:50px'>{r['time']}</span><span style='{temp_style}'>{r['temp']}°F{label}</span></div>", unsafe_allow_html=True)
    else:
        st.warning("⚠️ Could not fetch NWS data for this city")
    
    st.markdown("---")
    st.subheader("📡 NWS Forecast")
    forecast = fetch_nws_forecast(cfg.get("lat", 40.78), cfg.get("lon", -73.97))
    if forecast:
        fcols = st.columns(len(forecast))
        for i, period in enumerate(forecast):
            with fcols[i]:
                name = period.get("name", "")
                temp = period.get("temperature", "")
                unit = period.get("temperatureUnit", "F")
                short = period.get("shortForecast", "")
                bg = "#1a1a2e" if "night" in name.lower() else "#1f2937"
                temp_color = "#3b82f6" if "night" in name.lower() else "#ef4444"
                st.markdown(f'<div style="background:{bg};border:1px solid #30363d;border-radius:8px;padding:12px;text-align:center"><div style="color:#9ca3af;font-size:0.8em">{name}</div><div style="color:{temp_color};font-size:1.8em;font-weight:700">{temp}°{unit}</div><div style="color:#6b7280;font-size:0.75em">{short}</div></div>', unsafe_allow_html=True)

# ============================================================
# FOOTER
# ============================================================
st.markdown("---")
st.markdown('<div style="background:linear-gradient(90deg,#d97706,#f59e0b);padding:10px 15px;border-radius:8px;margin-bottom:20px;text-align:center"><b style="color:#000">🧪 FREE TOOL</b> <span style="color:#000">— LOW Temperature Edge Finder v7.3</span></div>', unsafe_allow_html=True)
st.markdown('<div style="color:#6b7280;font-size:0.75em;text-align:center;margin-top:30px">⚠️ For entertainment purposes only. Not financial advice. Verify on Kalshi before trading.</div>', unsafe_allow_html=True)
