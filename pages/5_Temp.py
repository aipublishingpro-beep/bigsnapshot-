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
# CITY CONFIG - 6 VERIFIED KALSHI LOW TEMP MARKETS ONLY
# ============================================================
CITY_CONFIG = {
    "Chicago": {"low": "KXLOWTCHI", "station": "KMDW", "lat": 41.79, "lon": -87.75, "tz": "US/Central", "pattern": "midnight", "sunrise_hour": 7},
    "Denver": {"low": "KXLOWTDEN", "station": "KDEN", "lat": 39.86, "lon": -104.67, "tz": "US/Mountain", "pattern": "midnight", "sunrise_hour": 7},
    "Los Angeles": {"low": "KXLOWTLAX", "station": "KLAX", "lat": 33.94, "lon": -118.41, "tz": "US/Pacific", "pattern": "sunrise", "sunrise_hour": 7},
    "Miami": {"low": "KXLOWTMIA", "station": "KMIA", "lat": 25.80, "lon": -80.29, "tz": "US/Eastern", "pattern": "sunrise", "sunrise_hour": 7},
    "New York City": {"low": "KXLOWTNYC", "station": "KNYC", "lat": 40.78, "lon": -73.97, "tz": "US/Eastern", "pattern": "sunrise", "sunrise_hour": 7},
    "Philadelphia": {"low": "KXLOWTPHIL", "station": "KPHL", "lat": 39.87, "lon": -75.23, "tz": "US/Eastern", "pattern": "sunrise", "sunrise_hour": 7},
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

NIGHT_SCAN_CITIES = ["Chicago", "Denver"]

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

# ============================================================
# FUNCTIONS
# ============================================================
@st.cache_data(ttl=120)
def fetch_nws_observations(station, city_tz_str):
    url = f"https://api.weather.gov/stations/{station}/observations"
    try:
        city_tz = pytz.timezone(city_tz_str)
        resp = requests.get(url, headers={"User-Agent": "TempEdge/8.0"}, timeout=15)
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
        resp = requests.get(points_url, headers={"User-Agent": "TempEdge/8.0"}, timeout=10)
        if resp.status_code != 200:
            return None
        forecast_url = resp.json().get("properties", {}).get("forecast")
        if not forecast_url:
            return None
        resp = requests.get(forecast_url, headers={"User-Agent": "TempEdge/8.0"}, timeout=10)
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
        resp = requests.get(points_url, headers={"User-Agent": "TempEdge/8.0"}, timeout=10)
        if resp.status_code != 200:
            return None
        forecast_url = resp.json().get("properties", {}).get("forecast")
        if not forecast_url:
            return None
        resp = requests.get(forecast_url, headers={"User-Agent": "TempEdge/8.0"}, timeout=10)
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
        resp = requests.get(points_url, headers={"User-Agent": "TempEdge/8.0"}, timeout=10)
        if resp.status_code != 200:
            return None
        forecast_url = resp.json().get("properties", {}).get("forecast")
        if not forecast_url:
            return None
        resp = requests.get(forecast_url, headers={"User-Agent": "TempEdge/8.0"}, timeout=10)
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
    """
    SUNRISE-BASED CONFIRMATION:
    - LOCKED: Post-sunrise + temp rising for 60min+
    - DANGER: Midnight cities pre-sunrise
    - WAITING: Pre-sunrise or temp not confirmed rising
    """
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
        <div style="background:#7f1d1d;border:2px solid #ef4444;border-radius:8px;padding:12px;margin-bottom:15px">
            <div style="color:#ef4444;font-weight:700;margin-bottom:8px">🎰 MIDNIGHT CITIES = DANGER</div>
            <div style="color:#fca5a5;font-size:0.85em;line-height:1.5">
                Chicago & Denver can drop<br>
                HOURS after "rising" signals.<br>
                <b>$85 lost Jan 27.</b><br>
                <b>WAIT FOR SUNRISE!</b>
            </div>
        </div>
        <div style="background:#1a2e1a;border:1px solid #22c55e;border-radius:8px;padding:12px;margin-bottom:15px">
            <div style="color:#22c55e;font-weight:700;margin-bottom:8px">🌅 SUNRISE CONFIRMATION</div>
            <div style="color:#c9d1d9;font-size:0.85em;line-height:1.5">
                <b>🔒 LOCKED:</b> Post-sunrise + rising<br>
                <b>🎰 DANGER:</b> Pre-sunrise (NO BUY)<br>
                <b>⏳ WAITING:</b> Too early
            </div>
        </div>
        <div style="background:#2d1f0a;border:1px solid #f59e0b;border-radius:8px;padding:12px;margin-bottom:15px">
            <div style="color:#f59e0b;font-weight:700;margin-bottom:8px">🗽 SAFE TRADING (ET)</div>
            <div style="color:#c9d1d9;font-size:0.8em;line-height:1.6">
                <b>☀️ 8-9 AM</b> → Miami, NYC, Philly<br>
                <b>☀️ 10-11 AM</b> → LA<br>
                <span style="color:#ef4444">🌙 Chicago/Denver = Casino</span>
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
                <b>🌙 Midnight:</b> Chicago, Denver<br>
                <b>☀️ Sunrise:</b> LA, Miami, NYC, Philly
            </div>
        </div>
        """, unsafe_allow_html=True)

# ============================================================
# HEADER
# ============================================================
st.title("🌡️ LOW TEMP EDGE FINDER")
st.caption(f"Live NWS + Kalshi | {now.strftime('%b %d, %Y %I:%M %p ET')} | 6 Cities | Sunrise Confirmation")

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
    st.subheader("🦈 NIGHT SCAN (Sunrise Confirmation)")
    
    st.markdown('<div style="background:#7f1d1d;border:3px solid #ef4444;border-radius:12px;padding:20px;margin:10px 0;text-align:center"><div style="color:#ef4444;font-size:1.5em;font-weight:800">🎰 EXTREME RISK MODE 🎰</div><div style="color:#fca5a5;font-size:1em;margin-top:10px">Midnight cities (Chicago/Denver) can drop HOURS after seeming to rise.<br><b>$85 LOST on Jan 27</b> buying "rising" signals that kept falling.<br><b>WAIT FOR ACTUAL SUNRISE before buying!</b></div></div>', unsafe_allow_html=True)
    
    current_hour = now.hour
    current_min = now.minute
    in_window = (current_hour == 23 and current_min >= 50) or (0 <= current_hour < 10)
    
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
            st.rerun()
        st.markdown('<div style="background:#7f1d1d;border:2px solid #ef4444;border-radius:8px;padding:10px;text-align:center;margin:10px 0"><b style="color:#fca5a5">● SCAN OFF</b></div>', unsafe_allow_html=True)
    
    st.caption(f"Watching: Chicago, Denver | SUNRISE LOCK REQUIRED (not just 2hr!)")
    st.markdown('<div style="background:#7f1d1d;border:1px solid #ef4444;border-radius:8px;padding:10px;margin:10px 0;text-align:center"><b style="color:#ef4444">⚠️ WAIT FOR 🔒 POST-SUNRISE LOCKED BEFORE BUYING!</b></div>', unsafe_allow_html=True)
    
    if not in_window:
        st.markdown(f'<div style="background:#7f1d1d;border:2px solid #ef4444;border-radius:8px;padding:15px;text-align:center;margin:10px 0"><div style="color:#fca5a5;font-weight:700">⏰ OUTSIDE SCAN WINDOW</div><div style="color:#9ca3af;font-size:0.9em">Current: {now.strftime("%I:%M %p ET")} | Window: 11:50 PM - 10:00 AM ET</div></div>', unsafe_allow_html=True)
        st.markdown('<div style="background:#1a1a2e;border:1px solid #3b82f6;border-radius:8px;padding:15px;margin-top:15px"><div style="color:#3b82f6;font-weight:700;margin-bottom:8px">🌅 SUNRISE LOCK TIMES (ET)</div><div style="color:#c9d1d9;font-size:0.85em;line-height:1.6"><b>8-9 AM ET</b> → Chicago (7 AM CT sunrise)<br><b>9-10 AM ET</b> → Denver (7 AM MT sunrise)<br><span style="color:#ef4444">DO NOT BUY before these times!</span></div></div>', unsafe_allow_html=True)
    
    if st.session_state.night_locked_city:
        locked = st.session_state.night_locked_city
        cfg = CITY_CONFIG.get(locked["city"], {})
        brackets = fetch_kalshi_brackets(cfg["low"])
        winning = find_winning_bracket(locked["obs_low"], brackets)
        current_bid = winning["bid"] if winning else locked["bid"]
        current_ask = winning["ask"] if winning else locked["ask"]
        
        st.markdown(f'<div style="background:#0d1117;border:4px solid #22c55e;border-radius:16px;padding:30px;margin:20px 0;text-align:center;box-shadow:0 0 40px rgba(34,197,94,0.5)"><div style="color:#22c55e;font-size:2em;font-weight:800">🔒 POST-SUNRISE LOCKED</div><div style="color:#fff;font-size:3em;font-weight:800">{locked["city"]}</div><div style="color:#fbbf24;font-size:1.5em;margin:15px 0">{locked["obs_low"]}°F → {locked["bracket"]}</div><div style="color:#9ca3af;font-size:1.2em">Bid: <b style="color:#3b82f6">{current_bid}¢</b> | Ask: <b style="color:#22c55e">{current_ask}¢</b></div><div style="color:#22c55e;font-size:1.8em;font-weight:800;margin-top:15px">+{100 - current_ask}¢ EDGE</div></div>', unsafe_allow_html=True)
        
        if st.button("🔊 TEST BEEP", use_container_width=True):
            st.toast("🔔 BEEP! POST-SUNRISE LOCKED!", icon="🚨")
        
        st.markdown(f'<a href="{locked["url"]}" target="_blank"><div style="background:#22c55e;color:#000;font-size:1.5em;font-weight:800;padding:20px;border-radius:12px;text-align:center;margin:20px 0;cursor:pointer">🚀 BUY NOW →</div></a>', unsafe_allow_html=True)
        
        if st.button("🔄 Refresh Prices", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        
        if st.button("❌ Clear Lock", use_container_width=True):
            st.session_state.night_locked_city = None
            st.rerun()
    
    elif st.session_state.night_scan_on and in_window:
        st.markdown("### 🔍 Scanning (Sunrise Confirmation)...")
        
        if now.hour >= 23:
            target_date = (now + timedelta(days=1)).date()
        else:
            target_date = now.date()
        
        st.caption(f"📅 Trading Date: {target_date.strftime('%b %d, %Y')}")
        
        for city_name in NIGHT_SCAN_CITIES:
            cfg = CITY_CONFIG.get(city_name, {})
            if not cfg:
                continue
            
            city_tz = pytz.timezone(cfg["tz"])
            city_now = datetime.now(city_tz)
            city_date = city_now.date()
            
            if city_date < target_date:
                midnight_city = datetime.combine(target_date, datetime.min.time())
                midnight_city = city_tz.localize(midnight_city)
                city_now_aware = city_now if city_now.tzinfo else city_tz.localize(city_now)
                diff = (midnight_city - city_now_aware).total_seconds()
                mins_until = max(0, int(diff / 60))
                st.write(f"🕐 **{city_name}** — Waiting for midnight ({city_now.strftime('%I:%M %p')} local, ~{mins_until} min)")
                continue
            
            current_temp, obs_low, obs_high, readings, low_time, oldest_time, newest_time, tz = fetch_nws_observations(cfg["station"], cfg["tz"])
            brackets = fetch_kalshi_brackets(cfg["low"])
            forecast_low = fetch_nws_today_low(cfg["lat"], cfg["lon"])
            
            if obs_low is None:
                st.write(f"⚪ **{city_name}** — No data yet for {target_date.strftime('%b %d')}")
                continue
            
            status_code, lock_status, confidence, mins_info, is_danger = get_lock_status_sunrise(obs_low, low_time, current_temp, city_tz, cfg.get("sunrise_hour", 7), cfg.get("pattern", "midnight"))
            forecast_warn_level, forecast_warn_text = get_forecast_warning(obs_low, forecast_low)
            winning = find_winning_bracket(obs_low, brackets)
            
            warn_display = f" | {forecast_warn_text}" if forecast_warn_text else ""
            
            if status_code == "locked" and winning and winning["ask"] < 90:
                st.session_state.night_locked_city = {"city": city_name, "obs_low": obs_low, "bracket": winning["name"], "bid": winning["bid"], "ask": winning["ask"], "url": winning["url"]}
                st.rerun()
            elif status_code == "locked" and winning and winning["ask"] >= 90:
                st.write(f"🔒 **{city_name}** | {obs_low}°F | POST-SUNRISE LOCKED but NO EDGE (Ask {winning['ask']}¢)")
            elif status_code == "locked":
                st.write(f"🔒 **{city_name}** | {obs_low}°F | POST-SUNRISE LOCKED ✅")
            elif status_code == "danger":
                low_time_str = low_time.strftime('%H:%M') if low_time else "?"
                st.markdown(f'<div style="background:#7f1d1d;border:1px solid #ef4444;border-radius:6px;padding:8px;margin:5px 0"><b style="color:#ef4444">🎰 {city_name}</b> | {obs_low}°F @ {low_time_str} | <span style="color:#fca5a5">{lock_status} - DO NOT BUY</span>{warn_display}</div>', unsafe_allow_html=True)
            else:
                low_time_str = low_time.strftime('%H:%M') if low_time else "?"
                st.write(f"⏳ **{city_name}** | {obs_low}°F @ {low_time_str} | {lock_status}{warn_display}")
        
        st.markdown(f"<div style='color:#6b7280;font-size:0.8em;text-align:center;margin-top:20px'>Auto-refresh: 5 min | {now.strftime('%I:%M:%S %p ET')}</div>", unsafe_allow_html=True)
        st.markdown('<meta http-equiv="refresh" content="300">', unsafe_allow_html=True)
    else:
        if st.session_state.night_scan_on and not in_window:
            st.warning("⏰ Scan ON but outside window. Will auto-scan when window opens.")
        else:
            st.info("Toggle Night Scan ON to start watching.")

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
st.markdown('<div style="background:linear-gradient(90deg,#d97706,#f59e0b);padding:10px 15px;border-radius:8px;margin-bottom:20px;text-align:center"><b style="color:#000">🧪 FREE TOOL</b> <span style="color:#000">— LOW Temperature Edge Finder v8.0 (Sunrise Gate)</span></div>', unsafe_allow_html=True)
