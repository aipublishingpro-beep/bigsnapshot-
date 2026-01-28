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
# CITY CONFIG - WITH METAR STATIONS
# ============================================================
CITY_CONFIG = {
    "Chicago": {"low": "KXLOWTCHI", "station": "KMDW", "metar": "KMDW", "lat": 41.79, "lon": -87.75, "tz": "US/Central", "pattern": "midnight", "sunrise_hour": 7},
    "Denver": {"low": "KXLOWTDEN", "station": "KDEN", "metar": "KDEN", "lat": 39.86, "lon": -104.67, "tz": "US/Mountain", "pattern": "midnight", "sunrise_hour": 7},
    "Los Angeles": {"low": "KXLOWTLAX", "station": "KLAX", "metar": "KLAX", "lat": 33.94, "lon": -118.41, "tz": "US/Pacific", "pattern": "sunrise", "sunrise_hour": 7},
    "Miami": {"low": "KXLOWTMIA", "station": "KMIA", "metar": "KMIA", "lat": 25.80, "lon": -80.29, "tz": "US/Eastern", "pattern": "sunrise", "sunrise_hour": 7},
    "New York City": {"low": "KXLOWTNYC", "station": "KNYC", "metar": "KNYC", "lat": 40.78, "lon": -73.97, "tz": "US/Eastern", "pattern": "sunrise", "sunrise_hour": 7},
    "Philadelphia": {"low": "KXLOWTPHIL", "station": "KPHL", "metar": "KPHL", "lat": 39.87, "lon": -75.23, "tz": "US/Eastern", "pattern": "sunrise", "sunrise_hour": 7},
}
CITY_LIST = sorted(CITY_CONFIG.keys())

CHECK_TIMES_ET = {
    "Chicago": "8-9 AM ET (post-sunrise)",
    "Denver": "9-10 AM ET (post-sunrise)", 
    "Los Angeles": "10-11 AM ET",
    "Miami": "8-9 AM ET",
    "New York City": "8-9 AM ET",
    "Philadelphia": "8-9 AM ET",
}

SHARK_CITIES = ["New York City", "Philadelphia", "Miami", "Chicago", "Denver"]

query_params = st.query_params
default_city = query_params.get("city", "New York City")
if default_city not in CITY_LIST:
    default_city = "New York City"
is_owner = query_params.get("mode") == "owner"

# DEBUG: Show what we're reading from URL
# st.write(f"DEBUG URL params: {dict(query_params)}")

# VIEW MODE: Read from URL FIRST, ALWAYS
# This runs on EVERY page load before anything else
url_view = str(query_params.get("view", "")).lower().strip()

if url_view in ["city", "today", "tomorrow", "shark", "night"]:
    # URL has valid view - USE IT (this is the source of truth)
    st.session_state.view_mode = url_view
elif "view_mode" not in st.session_state:
    # No URL param and no session - default to city
    st.session_state.view_mode = "city"
# else: keep existing session_state.view_mode

# DEBUG: Show what we ended up with
# st.write(f"DEBUG view_mode: {st.session_state.view_mode}")
if "night_scan_on" not in st.session_state:
    st.session_state.night_scan_on = False
if "night_locked_city" not in st.session_state:
    st.session_state.night_locked_city = None
if "shark_mode_on" not in st.session_state:
    st.session_state.shark_mode_on = False
if "metar_history" not in st.session_state:
    st.session_state.metar_history = {}

# ============================================================
# METAR FUNCTIONS - RAW AIRPORT DATA (FASTER!)
# ============================================================
@st.cache_data(ttl=60)
def fetch_raw_metar(station):
    """Fetch raw METAR data - updates every ~5 min at airports"""
    url = f"https://aviationweather.gov/api/data/metar?ids={station}&format=json"
    try:
        resp = requests.get(url, timeout=10, headers={"User-Agent": "TempEdge/8.1"})
        if resp.status_code != 200:
            return None
        data = resp.json()
        if not data or len(data) == 0:
            return None
        metar = data[0]
        return {
            "raw": metar.get("rawOb", ""),
            "temp_c": metar.get("temp"),
            "temp_f": round(metar.get("temp", 0) * 9/5 + 32, 1) if metar.get("temp") is not None else None,
            "dewpoint_c": metar.get("dewp"),
            "wind_speed_kt": metar.get("wspd", 0),
            "wind_gust_kt": metar.get("wgst"),
            "wind_dir": metar.get("wdir"),
            "visibility_mi": metar.get("visib"),
            "sky_cover": metar.get("cover", ""),
            "clouds": metar.get("clouds", []),
            "obs_time": metar.get("obsTime"),
            "station": station
        }
    except Exception as e:
        return None

def parse_sky_condition(metar_data):
    """Parse sky cover for early lock probability"""
    if not metar_data:
        return "unknown", 0
    
    clouds = metar_data.get("clouds", [])
    cover = metar_data.get("sky_cover", "")
    
    # Check cloud layers
    if clouds:
        lowest_cover = clouds[0].get("cover", "") if clouds else ""
        if lowest_cover in ["OVC", "BKN"]:
            return "cloudy", 80  # High chance of early lock
        elif lowest_cover in ["SCT"]:
            return "partly_cloudy", 50
        elif lowest_cover in ["FEW"]:
            return "few_clouds", 30
    
    if "CLR" in str(cover) or "SKC" in str(cover):
        return "clear", 10  # Low chance - expect sunrise lock
    
    return "unknown", 40

def parse_wind_condition(metar_data):
    """Parse wind for early lock probability"""
    if not metar_data:
        return "unknown", 0
    
    wind_speed = metar_data.get("wind_speed_kt", 0) or 0
    wind_gust = metar_data.get("wind_gust_kt", 0) or 0
    
    max_wind = max(wind_speed, wind_gust)
    
    if max_wind >= 15:
        return "windy", 70  # Mixing = early stabilization
    elif max_wind >= 8:
        return "breezy", 50
    elif max_wind >= 3:
        return "light_wind", 30
    else:
        return "calm", 10  # Radiative cooling continues

def calculate_early_lock_probability(metar_data, forecast_low, current_temp):
    """Calculate probability of early lock (before sunrise)"""
    if not metar_data:
        return 0, "No METAR data"
    
    sky_cond, sky_prob = parse_sky_condition(metar_data)
    wind_cond, wind_prob = parse_wind_condition(metar_data)
    
    # Base probability from conditions
    base_prob = (sky_prob + wind_prob) / 2
    
    # Adjust for temp proximity to forecast low
    if forecast_low and current_temp:
        temp_diff = current_temp - forecast_low
        if temp_diff <= 1:  # Already at or below forecast low
            base_prob += 30
        elif temp_diff <= 3:
            base_prob += 15
        elif temp_diff >= 10:
            base_prob -= 20
    
    prob = max(5, min(95, base_prob))
    
    reasons = []
    if sky_prob >= 70:
        reasons.append(f"☁️ {sky_cond.replace('_', ' ').title()}")
    elif sky_prob <= 20:
        reasons.append(f"🌙 {sky_cond.replace('_', ' ').title()}")
    
    if wind_prob >= 50:
        reasons.append(f"💨 {wind_cond.replace('_', ' ').title()}")
    elif wind_prob <= 20:
        reasons.append(f"🍃 {wind_cond.replace('_', ' ').title()}")
    
    reason_str = " | ".join(reasons) if reasons else "Mixed conditions"
    
    return prob, reason_str

def detect_upticks(city, current_temp):
    """Detect consecutive temperature upticks - potential early lock signal
    Uses 0.3°F minimum threshold to filter noise (Grok suggested 0.5, but 0.3 catches real moves faster)
    """
    UPTICK_THRESHOLD = 0.3  # Minimum rise to count as real uptick
    
    if city not in st.session_state.metar_history:
        st.session_state.metar_history[city] = []
    
    history = st.session_state.metar_history[city]
    
    # Add current reading with timestamp
    now_ts = datetime.now(eastern)
    history.append({"temp": current_temp, "time": now_ts})
    
    # Keep only last 60 min of readings (extended for better tracking)
    cutoff = now_ts - timedelta(minutes=60)
    history = [h for h in history if h["time"] > cutoff]
    st.session_state.metar_history[city] = history
    
    if len(history) < 3:
        return 0, "Need more readings", 0
    
    # Find the lowest temp in history (the floor)
    temps = [h["temp"] for h in history]
    floor_temp = min(temps)
    current_rise = current_temp - floor_temp
    
    # Check last 3 readings for consecutive upticks above threshold
    recent = history[-3:]
    real_upticks = 0
    for i in range(1, len(recent)):
        rise = recent[i]["temp"] - recent[i-1]["temp"]
        if rise >= UPTICK_THRESHOLD:
            real_upticks += 1
    
    if real_upticks >= 2:
        return 2, f"🔥 {real_upticks} REAL UPTICKS! (+{current_rise:.1f}° from floor)", current_rise
    elif real_upticks == 1:
        return 1, f"⬆️ 1 uptick (+{current_rise:.1f}° from floor)", current_rise
    elif current_rise >= 0.5:
        return 1, f"📈 Rising +{current_rise:.1f}° from floor {floor_temp}°F", current_rise
    else:
        return 0, f"Flat/dropping (floor: {floor_temp}°F)", current_rise

# ============================================================
# NWS FUNCTIONS (EXISTING)
# ============================================================
@st.cache_data(ttl=120)
def fetch_nws_observations(station, city_tz_str):
    url = f"https://api.weather.gov/stations/{station}/observations"
    try:
        city_tz = pytz.timezone(city_tz_str)
        resp = requests.get(url, headers={"User-Agent": "TempEdge/8.1"}, timeout=15)
        if resp.status_code != 200:
            return None, None, None, [], None, None, None, None
        observations = resp.json().get("features", [])
        if not observations:
            return None, None, None, [], None, None, None, None
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
            return None, None, None, [], None, None, None, None
        readings.sort(key=lambda x: x["time"], reverse=True)
        current = readings[0]["temp"]
        obs_low = min(r["temp"] for r in readings)
        obs_high = max(r["temp"] for r in readings)
        readings_chrono = sorted(readings, key=lambda x: x["time"])
        low_time = None
        for r in readings_chrono:
            if r["temp"] == obs_low:
                low_time = r["time"]
                break
        oldest_time = readings_chrono[0]["time"] if readings_chrono else None
        newest_time = readings_chrono[-1]["time"] if readings_chrono else None
        display_readings = [{"time": r["time"].strftime("%H:%M"), "temp": r["temp"], "full_time": r["time"]} for r in readings]
        return current, obs_low, obs_high, display_readings, low_time, oldest_time, newest_time, city_tz
    except:
        return None, None, None, [], None, None, None, None

@st.cache_data(ttl=300)
def fetch_nws_forecast(lat, lon):
    try:
        points_url = f"https://api.weather.gov/points/{lat},{lon}"
        resp = requests.get(points_url, headers={"User-Agent": "TempEdge/8.1"}, timeout=10)
        if resp.status_code != 200:
            return None
        forecast_url = resp.json().get("properties", {}).get("forecast")
        if not forecast_url:
            return None
        resp = requests.get(forecast_url, headers={"User-Agent": "TempEdge/8.1"}, timeout=10)
        if resp.status_code != 200:
            return None
        periods = resp.json().get("properties", {}).get("periods", [])
        return periods[:4] if periods else None
    except:
        return None

@st.cache_data(ttl=300)
def fetch_nws_tonight_low(lat, lon):
    """Get tonight's forecast low"""
    try:
        points_url = f"https://api.weather.gov/points/{lat},{lon}"
        resp = requests.get(points_url, headers={"User-Agent": "TempEdge/8.1"}, timeout=10)
        if resp.status_code != 200:
            return None
        forecast_url = resp.json().get("properties", {}).get("forecast")
        if not forecast_url:
            return None
        resp = requests.get(forecast_url, headers={"User-Agent": "TempEdge/8.1"}, timeout=10)
        if resp.status_code != 200:
            return None
        periods = resp.json().get("properties", {}).get("periods", [])
        for p in periods:
            name = p.get("name", "").lower()
            if "tonight" in name or "night" in name:
                return p.get("temperature")
        return None
    except:
        return None

@st.cache_data(ttl=300)
def fetch_nws_tomorrow_low(lat, lon):
    try:
        points_url = f"https://api.weather.gov/points/{lat},{lon}"
        resp = requests.get(points_url, headers={"User-Agent": "TempEdge/8.1"}, timeout=10)
        if resp.status_code != 200:
            return None
        forecast_url = resp.json().get("properties", {}).get("forecast")
        if not forecast_url:
            return None
        resp = requests.get(forecast_url, headers={"User-Agent": "TempEdge/8.1"}, timeout=10)
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

@st.cache_data(ttl=300)
def fetch_nws_today_low(lat, lon):
    try:
        points_url = f"https://api.weather.gov/points/{lat},{lon}"
        resp = requests.get(points_url, headers={"User-Agent": "TempEdge/8.1"}, timeout=10)
        if resp.status_code != 200:
            return None
        forecast_url = resp.json().get("properties", {}).get("forecast")
        if not forecast_url:
            return None
        resp = requests.get(forecast_url, headers={"User-Agent": "TempEdge/8.1"}, timeout=10)
        if resp.status_code != 200:
            return None
        periods = resp.json().get("properties", {}).get("periods", [])
        today = datetime.now(eastern).date()
        for p in periods:
            start_time = p.get("startTime", "")
            is_day = p.get("isDaytime", True)
            temp = p.get("temperature")
            if start_time and not is_day:
                try:
                    period_date = datetime.fromisoformat(start_time.replace("Z", "+00:00")).date()
                    if period_date == today:
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

def get_forecast_warning(obs_low, forecast_low):
    if obs_low is None or forecast_low is None:
        return None, ""
    diff = obs_low - forecast_low
    if abs(diff) >= 5:
        return "danger", f"⚠️ FORECAST MISMATCH: Observed {obs_low}°F vs Forecast {forecast_low}°F (diff: {diff:+.0f}°)"
    elif abs(diff) >= 3:
        return "warning", f"⚠️ Forecast said {forecast_low}°F, observing {obs_low}°F (diff: {diff:+.0f}°)"
    return None, ""

def get_lock_status_sunrise(obs_low, low_time, current_temp, city_tz, sunrise_hour, pattern):
    if obs_low is None or low_time is None or city_tz is None:
        return "no_data", "❌ NO DATA", 0, 0, False
    now_local = datetime.now(city_tz)
    current_hour = now_local.hour
    minutes_since_low = (now_local - low_time).total_seconds() / 60
    past_sunrise = current_hour >= sunrise_hour
    is_danger_zone = (pattern == "midnight" and not past_sunrise)
    if past_sunrise and current_temp > obs_low and minutes_since_low >= 60:
        return "locked", "🔒 LOCKED (post-sunrise)", 95, int(minutes_since_low), is_danger_zone
    elif past_sunrise and current_temp > obs_low:
        mins_to_1hr = max(0, 60 - int(minutes_since_low))
        return "likely", f"⏳ {mins_to_1hr}min to lock", 70, mins_to_1hr, is_danger_zone
    elif not past_sunrise and pattern == "midnight":
        mins_to_sunrise = (sunrise_hour - current_hour) * 60 - now_local.minute
        if mins_to_sunrise < 0:
            mins_to_sunrise = 0
        return "danger", f"🎰 DANGER ({mins_to_sunrise}min to sunrise)", 20, mins_to_sunrise, True
    elif not past_sunrise:
        mins_to_sunrise = (sunrise_hour - current_hour) * 60 - now_local.minute
        if mins_to_sunrise < 0:
            mins_to_sunrise = 0
        return "waiting", f"⏳ {mins_to_sunrise}min to sunrise", 40, mins_to_sunrise, is_danger_zone
    else:
        return "waiting", "⏳ WAITING (at low)", 30, 0, is_danger_zone

# ============================================================
# SIDEBAR
# ============================================================
if is_owner:
    with st.sidebar:
        st.markdown("""
        <div style="background:#1a1a2e;border:2px solid #8b5cf6;border-radius:8px;padding:12px;margin-bottom:15px">
            <div style="color:#8b5cf6;font-weight:700;margin-bottom:8px">🦈 SHARK SIGNALS</div>
            <div style="color:#c9d1d9;font-size:0.85em;line-height:1.5">
                <b>☁️ Cloudy + 💨 Windy</b> = Early lock likely<br>
                <b>🌙 Clear + 🍃 Calm</b> = Sunrise lock<br>
                <b>🔥 2+ Upticks</b> = POUNCE!
            </div>
        </div>
        <div style="background:#7f1d1d;border:2px solid #ef4444;border-radius:8px;padding:12px;margin-bottom:15px">
            <div style="color:#ef4444;font-weight:700;margin-bottom:8px">🎰 MIDNIGHT CITIES = DANGER</div>
            <div style="color:#fca5a5;font-size:0.85em;line-height:1.5">
                Chicago & Denver can drop<br>
                HOURS after "rising" signals.<br>
                <b>$85 lost Jan 27.</b>
            </div>
        </div>
        <div style="background:#1a2e1a;border:1px solid #22c55e;border-radius:8px;padding:12px;margin-bottom:15px">
            <div style="color:#22c55e;font-weight:700;margin-bottom:8px">💰 SHARK ENTRY</div>
            <div style="color:#c9d1d9;font-size:0.8em;line-height:1.6">
                <b>🦈 &lt;30¢</b> = SHARK ZONE (early)<br>
                <b>🔥 30-50¢</b> = Still good<br>
                <b>⚠️ 50-70¢</b> = Crowd arriving<br>
                <b>❌ 70¢+</b> = Too late
            </div>
        </div>
        """, unsafe_allow_html=True)
else:
    with st.sidebar:
        st.markdown("""
        <div style="background:#1a1a2e;border:1px solid #3b82f6;border-radius:8px;padding:12px;margin-bottom:15px">
            <div style="color:#3b82f6;font-weight:700;margin-bottom:8px">⏰ LOW WINDOWS</div>
            <div style="color:#c9d1d9;font-size:0.8em;line-height:1.6">
                <b>🌙 Midnight:</b> Chicago, Denver<br>
                <b>☀️ Sunrise:</b> LA, Miami, NYC, Philly
            </div>
        </div>
        """, unsafe_allow_html=True)

# ============================================================
# HEADER
# ============================================================
st.title("🌡️ LOW TEMP EDGE FINDER")
st.caption(f"Live NWS + METAR | {now.strftime('%b %d, %Y %I:%M %p ET')} | Shark Mode")

if is_owner:
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        if st.button("📍 City", use_container_width=True, type="primary" if st.session_state.view_mode == "city" else "secondary"):
            st.session_state.view_mode = "city"
            st.query_params.update({"mode": "owner", "view": "city"})
            st.rerun()
    with c2:
        if st.button("🔍 Today", use_container_width=True, type="primary" if st.session_state.view_mode == "today" else "secondary"):
            st.session_state.view_mode = "today"
            st.query_params.update({"mode": "owner", "view": "today"})
            st.rerun()
    with c3:
        if st.button("🎰 Tomorrow", use_container_width=True, type="primary" if st.session_state.view_mode == "tomorrow" else "secondary"):
            st.session_state.view_mode = "tomorrow"
            st.query_params.update({"mode": "owner", "view": "tomorrow"})
            st.rerun()
    with c4:
        if st.button("🦈 SHARK", use_container_width=True, type="primary" if st.session_state.view_mode == "shark" else "secondary"):
            st.session_state.view_mode = "shark"
            st.query_params.update({"mode": "owner", "view": "shark"})
            st.rerun()
    with c5:
        if st.button("🌙 Night", use_container_width=True, type="primary" if st.session_state.view_mode == "night" else "secondary"):
            st.session_state.view_mode = "night"
            st.query_params.update({"mode": "owner", "view": "night"})
            st.rerun()
    st.markdown("---")

# ============================================================
# 🦈 SHARK MODE - BE FIRST!
# ============================================================
if is_owner and st.session_state.view_mode == "shark":
    st.subheader("🦈 SHARK MODE - Hunt Early Locks")
    
    st.markdown("""
    <div style="background:linear-gradient(135deg,#1a1a2e,#2d1f5e);border:2px solid #8b5cf6;border-radius:12px;padding:20px;margin:10px 0">
        <div style="color:#8b5cf6;font-size:1.3em;font-weight:800;text-align:center">BE THE SHARK, NOT THE PREY</div>
        <div style="color:#c9d1d9;font-size:0.9em;margin-top:10px;text-align:center">
            Raw METAR data • Early lock detection • Uptick alerts<br>
            <b>Buy at 10-30¢ while others sleep. Sell at 80-90¢ when they wake up.</b>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 1])
    with col1:
        shark_city = st.selectbox("🎯 Target City", SHARK_CITIES, index=0)
    with col2:
        if st.button("🔄 REFRESH METAR (every 5 min ideal)", use_container_width=True, type="primary"):
            st.cache_data.clear()
            st.rerun()
    
    cfg = CITY_CONFIG.get(shark_city, {})
    city_tz = pytz.timezone(cfg["tz"])
    
    # Fetch all data
    metar = fetch_raw_metar(cfg["metar"])
    forecast_low = fetch_nws_tonight_low(cfg["lat"], cfg["lon"])
    current_temp, obs_low, obs_high, readings, low_time, oldest_time, newest_time, tz = fetch_nws_observations(cfg["station"], cfg["tz"])
    brackets = fetch_kalshi_brackets(cfg["low"])
    
    # METAR Status
    st.markdown("### 📡 RAW METAR (Live Airport Data)")
    if metar:
        metar_temp = metar.get("temp_f")
        wind_speed = metar.get("wind_speed_kt", 0) or 0
        wind_dir = metar.get("wind_dir", "---")
        
        # Calculate early lock probability
        early_prob, prob_reason = calculate_early_lock_probability(metar, forecast_low, metar_temp)
        
        # Detect upticks (returns 3 values: count, message, rise_amount)
        if metar_temp:
            uptick_count, uptick_msg, rise_amount = detect_upticks(shark_city, metar_temp)
        else:
            uptick_count, uptick_msg, rise_amount = 0, "No temp", 0
        
        # Sky condition
        sky_cond, sky_prob = parse_sky_condition(metar)
        wind_cond, wind_prob = parse_wind_condition(metar)
        
        # Color based on probability
        if early_prob >= 60:
            prob_color = "#22c55e"
            prob_label = "HIGH"
        elif early_prob >= 40:
            prob_color = "#f59e0b"
            prob_label = "MEDIUM"
        else:
            prob_color = "#ef4444"
            prob_label = "LOW"
        
        # NIGHT TYPE LABEL
        if sky_prob <= 20 and wind_prob <= 20:
            night_type = "🌙 CLEAR + CALM"
            night_advice = "Low locks at SUNRISE. Sleep or wait until 6 AM."
            night_color = "#ef4444"
        elif sky_prob >= 60 or wind_prob >= 60:
            night_type = "☁️💨 CLOUDY/WINDY"
            night_advice = "Early lock POSSIBLE. Stay sharp, watch for upticks!"
            night_color = "#22c55e"
        else:
            night_type = "🌤️ MIXED"
            night_advice = "Could go either way. Watch the data."
            night_color = "#f59e0b"
        
        st.markdown(f"""
        <div style="background:{night_color}20;border:2px solid {night_color};border-radius:10px;padding:15px;margin:10px 0;text-align:center">
            <div style="color:{night_color};font-size:1.5em;font-weight:800">{night_type}</div>
            <div style="color:#c9d1d9;font-size:0.95em;margin-top:5px">{night_advice}</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <div style="background:#161b22;border:1px solid #30363d;border-radius:12px;padding:20px;margin:10px 0">
            <div style="display:flex;justify-content:space-between;flex-wrap:wrap;gap:15px">
                <div style="text-align:center;flex:1;min-width:100px">
                    <div style="color:#6b7280;font-size:0.8em">METAR TEMP</div>
                    <div style="color:#fff;font-size:2.5em;font-weight:800">{metar_temp}°F</div>
                </div>
                <div style="text-align:center;flex:1;min-width:100px">
                    <div style="color:#6b7280;font-size:0.8em">FORECAST LOW</div>
                    <div style="color:#3b82f6;font-size:2.5em;font-weight:800">{forecast_low or '?'}°F</div>
                </div>
                <div style="text-align:center;flex:1;min-width:100px">
                    <div style="color:#6b7280;font-size:0.8em">WIND</div>
                    <div style="color:#fff;font-size:1.5em;font-weight:700">{wind_dir}° @ {wind_speed}kt</div>
                </div>
                <div style="text-align:center;flex:1;min-width:100px">
                    <div style="color:#6b7280;font-size:0.8em">SKY</div>
                    <div style="color:#fff;font-size:1.2em;font-weight:700">{sky_cond.replace('_', ' ').title()}</div>
                </div>
            </div>
            <div style="margin-top:15px;padding:10px;background:#0d1117;border-radius:8px;text-align:center">
                <span style="color:#6b7280">Raw: </span><code style="color:#8b5cf6;font-size:0.8em">{metar.get('raw', 'N/A')[:80]}...</code>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Early Lock Probability Box
        st.markdown(f"""
        <div style="background:linear-gradient(135deg,#0d1117,#1a1a2e);border:3px solid {prob_color};border-radius:12px;padding:20px;margin:15px 0;text-align:center">
            <div style="color:{prob_color};font-size:1.2em;font-weight:700">EARLY LOCK PROBABILITY</div>
            <div style="color:#fff;font-size:4em;font-weight:800;margin:10px 0">{early_prob}%</div>
            <div style="color:{prob_color};font-size:1.2em;font-weight:700">{prob_label}</div>
            <div style="color:#9ca3af;font-size:0.9em;margin-top:10px">{prob_reason}</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Uptick Alert
        if uptick_count >= 2:
            st.markdown(f"""
            <div style="background:#166534;border:3px solid #22c55e;border-radius:12px;padding:20px;margin:15px 0;text-align:center;animation:pulse 1s infinite">
                <div style="color:#22c55e;font-size:2em;font-weight:800">🔥 UPTICK ALERT!</div>
                <div style="color:#fff;font-size:1.2em;margin-top:10px">{uptick_msg}</div>
                <div style="color:#4ade80;font-size:1em;margin-top:5px">Potential early lock - CHECK KALSHI NOW!</div>
            </div>
            """, unsafe_allow_html=True)
        elif uptick_count == 1:
            st.markdown(f"""
            <div style="background:#2d1f0a;border:2px solid #f59e0b;border-radius:8px;padding:15px;margin:10px 0;text-align:center">
                <div style="color:#f59e0b;font-size:1.2em;font-weight:700">⬆️ First Uptick Detected</div>
                <div style="color:#9ca3af;font-size:0.9em">Watching for confirmation...</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="background:#1a1a2e;border:1px solid #6b7280;border-radius:8px;padding:15px;margin:10px 0;text-align:center">
                <div style="color:#6b7280;font-size:1em">{uptick_msg}</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.warning("⚠️ Could not fetch METAR data")
    
    # Kalshi Market Status
    st.markdown("### 💰 Kalshi Market")
    if brackets and metar:
        winning = find_winning_bracket(metar.get("temp_f"), brackets)
        if winning:
            ask = winning["ask"]
            if ask < 30:
                edge_color, edge_label = "#8b5cf6", "🦈 SHARK ZONE"
            elif ask < 50:
                edge_color, edge_label = "#22c55e", "🔥 GOOD ENTRY"
            elif ask < 70:
                edge_color, edge_label = "#f59e0b", "⚠️ CROWD ARRIVING"
            else:
                edge_color, edge_label = "#ef4444", "❌ TOO LATE"
            
            # 🚨 SHARK ALERT COMBO: prob >70% + upticks + ask <30¢
            shark_alert = False
            if early_prob >= 70 and uptick_count >= 1 and ask < 30:
                shark_alert = True
                st.markdown(f"""
                <div style="background:linear-gradient(135deg,#166534,#22c55e);border:4px solid #4ade80;border-radius:16px;padding:30px;margin:15px 0;text-align:center;box-shadow:0 0 60px rgba(34,197,94,0.6);animation:pulse 0.5s infinite alternate">
                    <div style="color:#fff;font-size:2.5em;font-weight:900">🦈🚨 SHARK ALERT 🚨🦈</div>
                    <div style="color:#fff;font-size:1.3em;margin:15px 0">ALL CONDITIONS MET!</div>
                    <div style="display:flex;justify-content:center;gap:20px;flex-wrap:wrap;margin:15px 0">
                        <div style="background:#0d1117;padding:10px 20px;border-radius:8px">
                            <div style="color:#4ade80;font-size:0.9em">PROBABILITY</div>
                            <div style="color:#fff;font-size:1.5em;font-weight:800">{early_prob}%</div>
                        </div>
                        <div style="background:#0d1117;padding:10px 20px;border-radius:8px">
                            <div style="color:#4ade80;font-size:0.9em">UPTICKS</div>
                            <div style="color:#fff;font-size:1.5em;font-weight:800">✓ YES</div>
                        </div>
                        <div style="background:#0d1117;padding:10px 20px;border-radius:8px">
                            <div style="color:#4ade80;font-size:0.9em">ASK PRICE</div>
                            <div style="color:#fff;font-size:1.5em;font-weight:800">{ask}¢</div>
                        </div>
                    </div>
                    <a href="{winning['url']}" target="_blank">
                        <div style="background:#fff;color:#166534;font-size:1.8em;font-weight:900;padding:20px;border-radius:12px;margin-top:15px;cursor:pointer">
                            🎯 POUNCE NOW → BUY {winning['name']}
                        </div>
                    </a>
                </div>
                """, unsafe_allow_html=True)
                st.balloons()
            elif early_prob >= 50 and uptick_count >= 1 and ask < 50:
                # Near-shark alert
                st.markdown(f"""
                <div style="background:#2d1f0a;border:3px solid #f59e0b;border-radius:12px;padding:20px;margin:15px 0;text-align:center">
                    <div style="color:#f59e0b;font-size:1.5em;font-weight:800">⚠️ SHARK WARMING UP</div>
                    <div style="color:#c9d1d9;font-size:1em;margin-top:10px">
                        Prob: {early_prob}% | Upticks: {uptick_count} | Ask: {ask}¢<br>
                        <b>Getting close! Watch for prob >70% or ask drop.</b>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown(f"""
            <div style="background:#0d1117;border:2px solid {edge_color};border-radius:12px;padding:20px;margin:10px 0">
                <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap">
                    <div>
                        <div style="color:#6b7280;font-size:0.8em">WINNING BRACKET</div>
                        <div style="color:#fff;font-size:1.8em;font-weight:800">{winning['name']}</div>
                    </div>
                    <div style="text-align:right">
                        <div style="color:{edge_color};font-size:0.9em;font-weight:700">{edge_label}</div>
                        <div style="color:#fff;font-size:2em;font-weight:800">Ask: {ask}¢</div>
                        <div style="color:#9ca3af;font-size:0.9em">Bid: {winning['bid']}¢</div>
                    </div>
                </div>
                <a href="{winning['url']}" target="_blank">
                    <div style="background:{edge_color};color:#000;font-weight:700;padding:12px;border-radius:8px;text-align:center;margin-top:15px;cursor:pointer">
                        🎯 OPEN KALSHI →
                    </div>
                </a>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info("No bracket match for current temp")
    else:
        st.info("Fetching market data...")
    
    # Decision Guide
    st.markdown("### 🧠 Shark Decision Guide")
    
    guide_items = []
    if metar:
        # Re-calculate for guide (these may have been calculated above but let's be explicit)
        early_prob_guide, _ = calculate_early_lock_probability(metar, forecast_low, metar.get("temp_f"))
        
        # Detect upticks - returns 3 values
        if metar.get("temp_f"):
            uptick_count_guide, _, rise_amt = detect_upticks(shark_city, metar.get("temp_f"))
        else:
            uptick_count_guide, rise_amt = 0, 0
        ask_price = 100
        if brackets:
            winning_guide = find_winning_bracket(metar.get("temp_f"), brackets)
            if winning_guide:
                ask_price = winning_guide["ask"]
        
        # Sky/wind for night type assessment
        sky_cond_guide, sky_prob_guide = parse_sky_condition(metar)
        wind_cond_guide, wind_prob_guide = parse_wind_condition(metar)
        
        # SHARK ALERT CONDITIONS
        if early_prob_guide >= 70 and uptick_count_guide >= 1 and ask_price < 30:
            guide_items.append(("🦈 POUNCE NOW!", "#22c55e", f"ALL CONDITIONS MET: {early_prob_guide}% prob + upticks + {ask_price}¢ ask. BUY IMMEDIATELY!"))
        elif early_prob_guide >= 60 and uptick_count_guide >= 2:
            guide_items.append(("🔥 STRONG SIGNAL", "#22c55e", f"High probability + confirmed upticks. Check ask - if <50¢, consider buying."))
        elif early_prob_guide >= 60:
            guide_items.append(("👀 WATCH CLOSELY", "#f59e0b", "High probability but waiting for uptick confirmation."))
        elif early_prob_guide >= 40 and uptick_count_guide >= 1:
            guide_items.append(("📊 DEVELOPING", "#3b82f6", "Medium probability with early signs. Keep watching."))
        elif early_prob_guide >= 40:
            guide_items.append(("⏳ PATIENCE", "#3b82f6", "Medium probability. Could go either way."))
        else:
            guide_items.append(("😴 WAIT FOR SUNRISE", "#6b7280", "Clear/calm night = low locks at sunrise. Consider sleeping."))
        
        # Add specific condition notes
        if sky_prob_guide <= 20 and wind_prob_guide <= 20:
            guide_items.append(("🌙 CLEAR + CALM NIGHT", "#ef4444", "Radiative cooling continues until dawn. Early lock unlikely."))
        
        if cfg.get("pattern") == "midnight":
            guide_items.append(("⚠️ MIDNIGHT CITY", "#ef4444", "Extra caution - can drop for hours after 'rising'. Consider safer cities."))
    
    for label, color, desc in guide_items:
        st.markdown(f"""
        <div style="background:#161b22;border-left:4px solid {color};padding:12px 15px;margin:8px 0;border-radius:0 8px 8px 0">
            <b style="color:{color}">{label}</b>
            <div style="color:#9ca3af;font-size:0.9em">{desc}</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Manual refresh (auto-refresh removed to preserve session_state)
    st.markdown(f"<div style='color:#6b7280;font-size:0.8em;text-align:center;margin-top:20px'>Last updated: {now.strftime('%I:%M:%S %p ET')} | Click refresh every 60s for fresh METAR</div>", unsafe_allow_html=True)
    
    if st.button("🔄 REFRESH METAR DATA", use_container_width=True, type="primary", key="bottom_refresh"):
        st.cache_data.clear()
        st.rerun()
    
    # METAR History (for manual verification)
    if shark_city in st.session_state.metar_history and len(st.session_state.metar_history[shark_city]) > 1:
        with st.expander("📊 METAR Temperature History (Last 60 min)", expanded=False):
            history = st.session_state.metar_history[shark_city]
            st.markdown("<div style='font-size:0.85em'>", unsafe_allow_html=True)
            for i, h in enumerate(reversed(history[-10:])):  # Last 10 readings
                time_str = h["time"].strftime("%H:%M:%S")
                temp = h["temp"]
                if i == 0:
                    st.markdown(f"<div style='padding:4px 8px;background:#1a2e1a;border-radius:4px;margin:2px 0'><b style='color:#22c55e'>{time_str}</b> → <b style='color:#fff'>{temp}°F</b> (latest)</div>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<div style='padding:4px 8px;border-bottom:1px solid #30363d'><span style='color:#6b7280'>{time_str}</span> → <span style='color:#9ca3af'>{temp}°F</span></div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

# ============================================================
# TODAY'S SCANNER (OWNER ONLY)
# ============================================================
elif is_owner and st.session_state.view_mode == "today":
    st.subheader("🔍 TODAY'S MISPRICING SCANNER")
    if st.button("🔄 Refresh All", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    
    results = []
    for city_name, cfg in CITY_CONFIG.items():
        current_temp, obs_low, obs_high, readings, low_time, oldest_time, newest_time, city_tz = fetch_nws_observations(cfg["station"], cfg["tz"])
        brackets = fetch_kalshi_brackets(cfg["low"])
        forecast_low = fetch_nws_today_low(cfg["lat"], cfg["lon"])
        pattern_icon = "🌙" if cfg.get("pattern") == "midnight" else "☀️"
        if obs_low is None:
            results.append({"city": city_name, "pattern": pattern_icon, "status": "NO DATA"})
            continue
        status_code, lock_status, confidence, mins_info, is_danger = get_lock_status_sunrise(obs_low, low_time, current_temp, city_tz, cfg.get("sunrise_hour", 7), cfg.get("pattern", "sunrise"))
        forecast_warn_level, forecast_warn_text = get_forecast_warning(obs_low, forecast_low)
        winning = find_winning_bracket(obs_low, brackets)
        if winning:
            edge = (100 - winning["ask"]) if status_code == "locked" else 0
            results.append({"city": city_name, "pattern": pattern_icon, "obs_low": obs_low, "bracket": winning["name"], "ask": winning["ask"], "edge": edge, "lock_status": lock_status, "status_code": status_code, "url": winning["url"], "is_danger": is_danger, "forecast_warn": forecast_warn_text})
        else:
            results.append({"city": city_name, "pattern": pattern_icon, "obs_low": obs_low, "bracket": "NO MATCH", "ask": 0, "edge": 0, "lock_status": lock_status, "status_code": status_code, "is_danger": is_danger, "forecast_warn": forecast_warn_text})
    
    danger_opps = [r for r in results if r.get("is_danger", False)]
    if danger_opps:
        st.markdown("### 🎰 DANGER ZONE (Midnight Cities Pre-Sunrise)")
        st.markdown('<div style="background:#7f1d1d;border:2px solid #ef4444;border-radius:8px;padding:10px;margin:10px 0"><b style="color:#fca5a5">⚠️ DO NOT BUY - Low can still drop until sunrise!</b></div>', unsafe_allow_html=True)
        for d in danger_opps:
            warn_text = f'<div style="color:#fca5a5;font-size:0.85em">{d.get("forecast_warn", "")}</div>' if d.get("forecast_warn") else ""
            st.markdown(f'<div style="background:#0d1117;border:2px solid #ef4444;border-radius:8px;padding:15px;margin:10px 0"><b style="color:#ef4444">{d["pattern"]} {d["city"]}</b> | {d["lock_status"]} | Low: {d["obs_low"]}°F → <b>{d.get("bracket", "N/A")}</b> | Ask: {d.get("ask", 0)}¢{warn_text}</div>', unsafe_allow_html=True)
    
    opps = [r for r in results if r.get("edge", 0) >= 5 and r.get("status_code") == "locked" and not r.get("is_danger", False)]
    if opps:
        st.markdown("### 🔥 LOCKED OPPORTUNITIES (Edge ≥ 5¢)")
        for o in sorted(opps, key=lambda x: x["edge"], reverse=True):
            color = "#22c55e" if o["edge"] >= 15 else "#fbbf24"
            warn_text = f'<div style="color:#f59e0b;font-size:0.85em">{o.get("forecast_warn", "")}</div>' if o.get("forecast_warn") else ""
            st.markdown(f'<div style="background:#0d1117;border:2px solid {color};border-radius:8px;padding:15px;margin:10px 0"><b style="color:{color}">{o["pattern"]} {o["city"]}</b> | {o["lock_status"]} | Low: {o["obs_low"]}°F → <b>{o["bracket"]}</b> | Ask: {o["ask"]}¢ | <b style="color:#22c55e">+{o["edge"]}¢ edge</b> | <a href="{o.get("url", "#")}" target="_blank" style="color:#fbbf24">BUY →</a>{warn_text}</div>', unsafe_allow_html=True)
    else:
        if now.hour >= 10:
            st.warning("⏰ TODAY'S MARKETS LIKELY DONE - Check Tomorrow's Lottery!")
        else:
            st.info("No LOCKED opportunities found yet. Wait for post-sunrise confirmation.")
    
    st.markdown("### 📊 ALL CITIES STATUS")
    for r in results:
        if r.get("status") == "NO DATA":
            st.write(f"{r['pattern']} **{r['city']}** — ❌ No data")
        else:
            st.write(f"{r['pattern']} **{r['city']}** | {r['lock_status']} | {r['obs_low']}°F → {r.get('bracket', 'N/A')} | Ask: {r.get('ask', 0)}¢")

# ============================================================
# TOMORROW'S LOTTERY (OWNER ONLY)
# ============================================================
elif is_owner and st.session_state.view_mode == "tomorrow":
    if now.hour < 5:
        target_date = now.date()
        lottery_label = "TODAY'S"
    else:
        target_date = (now + timedelta(days=1)).date()
        lottery_label = "TOMORROW'S"
    target_str = target_date.strftime('%A, %b %d')
    st.subheader(f"🎰 {lottery_label} LOTTERY ({target_str})")
    st.caption("Scout targets now → Wait for SUNRISE lock → Buy confirmed winners")
    if st.button("🔄 Refresh All", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    
    tickets = []
    all_cities = []
    for city_name, cfg in CITY_CONFIG.items():
        pattern_icon = "🌙" if cfg.get("pattern") == "midnight" else "☀️"
        if now.hour < 5:
            forecast_low = fetch_nws_today_low(cfg["lat"], cfg["lon"])
            brackets = fetch_kalshi_brackets(cfg["low"])
        else:
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
            data = {"city": city_name, "pattern": pattern_icon, "forecast": forecast_low, "bracket": winning["name"], "ask": winning["ask"], "url": winning["url"]}
            all_cities.append(data)
            if winning["ask"] < 60:
                tickets.append(data)
        else:
            all_cities.append({"city": city_name, "pattern": pattern_icon, "status": "NO BRACKET", "forecast": forecast_low})
    
    if tickets:
        st.markdown("### 🎰 CHEAP ENTRIES (<60¢)")
        for t in sorted(tickets, key=lambda x: x["ask"]):
            color = "#fbbf24" if t["ask"] < 40 else "#22c55e"
            check_time = CHECK_TIMES_ET.get(t['city'], "8-9 AM ET")
            st.markdown(f'<div style="background:#0d1117;border:2px solid {color};border-radius:8px;padding:15px;margin:10px 0"><b style="color:{color}">{t["pattern"]} {t["city"]}</b> | NWS: {t["forecast"]}°F → <b>{t["bracket"]}</b> | Ask: <b style="color:#22c55e">{t["ask"]}¢</b> | <a href="{t["url"]}" target="_blank" style="color:#fbbf24">Preview →</a><div style="margin-top:10px;padding:8px;background:#1a1a2e;border-radius:6px;text-align:center"><span style="color:#9ca3af">⏰ Sunrise Lock:</span> <b style="color:#3b82f6">{check_time}</b></div></div>', unsafe_allow_html=True)
    else:
        st.info("No cheap entries found. All brackets priced above 60¢.")
    
    st.markdown(f"### 📋 ALL CITIES - {target_str}")
    for c in all_cities:
        check_time = CHECK_TIMES_ET.get(c['city'], "8-9 AM ET")
        if c.get("status") == "NO FORECAST":
            st.write(f"{c['pattern']} **{c['city']}** — ❌ No forecast")
        elif c.get("status") == "NO MARKET":
            st.write(f"{c['pattern']} **{c['city']}** — NWS: {c['forecast']}°F — Market not open | ⏰ {check_time}")
        elif c.get("status") == "NO BRACKET":
            st.write(f"{c['pattern']} **{c['city']}** — NWS: {c['forecast']}°F — No bracket match")
        else:
            st.write(f"{c['pattern']} **{c['city']}** | NWS: {c['forecast']}°F → {c['bracket']} | Ask: {c['ask']}¢ | ⏰ {check_time}")

# ============================================================
# NIGHT SCAN (OWNER ONLY)
# ============================================================
elif is_owner and st.session_state.view_mode == "night":
    st.subheader("🌙 NIGHT SCAN (Sunrise Confirmation)")
    
    st.markdown('<div style="background:#7f1d1d;border:3px solid #ef4444;border-radius:12px;padding:20px;margin:10px 0;text-align:center"><div style="color:#ef4444;font-size:1.5em;font-weight:800">🎰 USE SHARK MODE INSTEAD 🦈</div><div style="color:#fca5a5;font-size:1em;margin-top:10px">Night Scan is for post-sunrise confirmation only.<br>For early hunting, use <b>🦈 SHARK MODE</b> with METAR + uptick detection.</div></div>', unsafe_allow_html=True)
    
    current_hour = now.hour
    in_window = (current_hour >= 6 and current_hour < 12)
    
    if not in_window:
        st.info(f"⏰ Night Scan active 6 AM - 12 PM ET. Current: {now.strftime('%I:%M %p ET')}")
        st.markdown("**For overnight hunting (11 PM - 6 AM), use 🦈 SHARK MODE**")
    else:
        for city_name in ["New York City", "Philadelphia", "Miami", "Chicago", "Denver"]:
            cfg = CITY_CONFIG.get(city_name, {})
            current_temp, obs_low, obs_high, readings, low_time, oldest_time, newest_time, city_tz = fetch_nws_observations(cfg["station"], cfg["tz"])
            brackets = fetch_kalshi_brackets(cfg["low"])
            
            if obs_low is None:
                st.write(f"⚪ **{city_name}** — No data")
                continue
            
            status_code, lock_status, confidence, mins_info, is_danger = get_lock_status_sunrise(obs_low, low_time, current_temp, city_tz, cfg.get("sunrise_hour", 7), cfg.get("pattern", "sunrise"))
            winning = find_winning_bracket(obs_low, brackets)
            
            if status_code == "locked" and winning:
                edge = 100 - winning["ask"]
                st.markdown(f'<div style="background:#1a2e1a;border:2px solid #22c55e;border-radius:8px;padding:12px;margin:8px 0"><b style="color:#22c55e">🔒 {city_name}</b> | {obs_low}°F → {winning["name"]} | Ask: {winning["ask"]}¢ | <b>+{edge}¢</b> | <a href="{winning["url"]}" target="_blank" style="color:#fbbf24">BUY →</a></div>', unsafe_allow_html=True)
            elif is_danger:
                st.markdown(f'<div style="background:#7f1d1d;border:1px solid #ef4444;border-radius:8px;padding:10px;margin:5px 0"><b style="color:#ef4444">🎰 {city_name}</b> | {obs_low}°F | {lock_status}</div>', unsafe_allow_html=True)
            else:
                st.write(f"⏳ **{city_name}** | {obs_low}°F | {lock_status}")

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
    current_temp, obs_low, obs_high, readings, low_time, oldest_time, newest_time, city_tz = fetch_nws_observations(cfg.get("station", "KNYC"), cfg.get("tz", "US/Eastern"))
    
    if obs_low is not None and current_temp is not None:
        status_code, lock_status, confidence, mins_info, is_danger = get_lock_status_sunrise(obs_low, low_time, current_temp, city_tz, cfg.get("sunrise_hour", 7), cfg.get("pattern", "sunrise"))
        forecast_low = fetch_nws_today_low(cfg.get("lat", 40.78), cfg.get("lon", -73.97))
        forecast_warn_level, forecast_warn_text = get_forecast_warning(obs_low, forecast_low)
        
        if cfg.get("pattern") == "midnight" and is_owner:
            st.markdown('<div style="background:#7f1d1d;border:2px solid #ef4444;border-radius:8px;padding:12px;margin:10px 0;text-align:center"><b style="color:#ef4444">🎰 MIDNIGHT PATTERN CITY</b><br><span style="color:#fca5a5">Low can drop until sunrise! Wait for post-sunrise lock.</span></div>', unsafe_allow_html=True)
        
        if is_owner:
            if low_time:
                low_time_str = low_time.strftime('%H:%M')
                mins_since = int((datetime.now(city_tz) - low_time).total_seconds() / 60)
                if status_code == "locked":
                    time_ago_text = f"Low at {low_time_str} ({mins_since} min ago) - POST-SUNRISE ✅"
                elif status_code == "danger":
                    time_ago_text = f"Low at {low_time_str} ({mins_since} min ago) - ⚠️ PRE-SUNRISE DANGER"
                else:
                    time_ago_text = f"Low at {low_time_str} ({mins_since} min ago) - waiting for sunrise"
            else:
                time_ago_text = "Low time unknown"
            
            data_warning = ""
            if oldest_time and oldest_time.hour >= 7:
                data_warning = f"⚠️ Data only from {oldest_time.strftime('%H:%M')} - early low may be missing!"
            
            if status_code == "locked":
                box_status, lock_color, box_bg = "🔒 POST-SUNRISE LOCKED", "#22c55e", "linear-gradient(135deg,#1a2e1a,#0d1117)"
            elif status_code == "danger":
                box_status, lock_color, box_bg = "🎰 DANGER - PRE-SUNRISE", "#ef4444", "linear-gradient(135deg,#7f1d1d,#0d1117)"
            elif status_code == "likely":
                box_status, lock_color, box_bg = f"⏳ {mins_info}min to lock", "#3b82f6", "linear-gradient(135deg,#1a1a2e,#0d1117)"
            else:
                box_status, lock_color, box_bg = "⏳ WAITING", "#6b7280", "linear-gradient(135deg,#1a1a1a,#0d1117)"
            
            forecast_display = f'<div style="color:#f59e0b;font-size:0.85em;margin-top:10px;padding:8px;background:#2d1f0a;border-radius:6px">{forecast_warn_text}</div>' if forecast_warn_text else ""
            
            st.markdown(f'<div style="background:{box_bg};border:3px solid {lock_color};border-radius:16px;padding:30px;margin:20px 0;text-align:center"><div style="color:{lock_color};font-size:1.2em;font-weight:700;margin-bottom:10px">{box_status}</div><div style="color:#6b7280;font-size:0.9em">Today\'s Low</div><div style="color:#fff;font-size:4em;font-weight:800;margin:10px 0">{obs_low}°F</div><div style="color:#9ca3af;font-size:0.9em">{time_ago_text}</div><div style="color:#f59e0b;font-size:0.85em;margin-top:10px">{data_warning}</div>{forecast_display}</div>', unsafe_allow_html=True)
        else:
            lock_color = "#22c55e" if status_code == "locked" else "#3b82f6" if status_code == "likely" else "#6b7280"
            st.markdown(f'<div style="background:linear-gradient(135deg,#1a1a2e,#0d1117);border:3px solid {lock_color};border-radius:16px;padding:25px;margin:20px 0;text-align:center"><div style="color:#6b7280;font-size:1em;margin-bottom:5px">📊 Today\'s Recorded Low</div><div style="color:{lock_color};font-size:4.5em;font-weight:800;margin:10px 0">{obs_low}°F</div><div style="color:#9ca3af;font-size:0.9em">From NWS Station: <span style="color:#22c55e;font-weight:600">{cfg.get("station", "N/A")}</span></div></div>', unsafe_allow_html=True)
        
        st.markdown(f'<div style="background:#161b22;border:1px solid #30363d;border-radius:8px;padding:15px;margin:10px 0"><div style="display:flex;justify-content:space-around;text-align:center"><div><div style="color:#6b7280;font-size:0.8em">CURRENT TEMP</div><div style="color:#fff;font-size:1.8em;font-weight:700">{current_temp}°F</div></div><div><div style="color:#6b7280;font-size:0.8em">TODAY\'S HIGH</div><div style="color:#ef4444;font-size:1.8em;font-weight:700">{obs_high}°F</div></div></div></div>', unsafe_allow_html=True)
        
        brackets = fetch_kalshi_brackets(cfg["low"])
        winning = find_winning_bracket(obs_low, brackets)
        if winning:
            st.markdown("### 🎯 Kalshi Market")
            edge = (100 - winning["ask"]) if status_code == "locked" else 0
            if status_code == "locked":
                edge_text = f" | **+{edge}¢ edge**"
            elif status_code == "danger":
                edge_text = " | 🎰 DANGER - Wait for sunrise!"
            else:
                edge_text = " | ⚠️ Wait for post-sunrise lock"
            st.markdown(f'<div style="background:#1a2e1a;border:1px solid #22c55e;border-radius:8px;padding:15px;margin:10px 0"><b style="color:#22c55e">Winning Bracket: {winning["name"]}</b><br>Bid: {winning["bid"]}¢ | Ask: {winning["ask"]}¢{edge_text}<br><a href="{winning["url"]}" target="_blank" style="color:#fbbf24">View on Kalshi →</a></div>', unsafe_allow_html=True)
        
        if readings:
            with st.expander("📊 Recent NWS Observations", expanded=True):
                if oldest_time and newest_time:
                    st.markdown(f"<div style='color:#6b7280;font-size:0.8em;margin-bottom:10px;text-align:center'>📅 Data: {oldest_time.strftime('%H:%M')} to {newest_time.strftime('%H:%M')} local</div>", unsafe_allow_html=True)
                
                display_list = readings if is_owner else readings[:8]
                
                for i, r in enumerate(display_list):
                    is_low = r['temp'] == obs_low
                    if is_low:
                        st.markdown(f'<div style="display:flex;justify-content:space-between;padding:6px 8px;border-radius:4px;background:#2d1f0a;border:1px solid #f59e0b;margin:2px 0"><span style="color:#9ca3af">{r["time"]}</span><span style="color:#fbbf24;font-weight:700">{r["temp"]}°F ↩️ LOW</span></div>', unsafe_allow_html=True)
                    else:
                        st.markdown(f'<div style="display:flex;justify-content:space-between;padding:4px 8px;border-bottom:1px solid #30363d"><span style="color:#9ca3af">{r["time"]}</span><span style="color:#fff;font-weight:600">{r["temp"]}°F</span></div>', unsafe_allow_html=True)
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
st.markdown('<div style="background:linear-gradient(90deg,#8b5cf6,#6366f1);padding:10px 15px;border-radius:8px;margin-bottom:20px;text-align:center"><b style="color:#fff">🦈 SHARK EDITION</b> <span style="color:#e0e0e0">— LOW Temperature Edge Finder v8.7</span></div>', unsafe_allow_html=True)
