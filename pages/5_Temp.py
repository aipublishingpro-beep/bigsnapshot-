import streamlit as st
import requests
from datetime import datetime, timedelta
import pytz
import re
from bs4 import BeautifulSoup

st.set_page_config(page_title="LOW Temp Edge Finder", page_icon="🌡️", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
.stApp {background-color: #0d1117;}
div[data-testid="stMarkdownContainer"] p {color: #c9d1d9;}
</style>
""", unsafe_allow_html=True)

eastern = pytz.timezone("US/Eastern")
now = datetime.now(eastern)

CITY_CONFIG = {
    "Austin": {"high": "KXHIGHAUS", "low": "KXLOWTAUS", "station": "KAUS", "lat": 30.19, "lon": -97.67, "tz": "US/Central", "window_start": 5, "window_end": 8, "pattern": "sunrise"},
    "Chicago": {"high": "KXHIGHCHI", "low": "KXLOWTCHI", "station": "KMDW", "lat": 41.79, "lon": -87.75, "tz": "US/Central", "window_start": 0, "window_end": 2, "pattern": "midnight"},
    "Denver": {"high": "KXHIGHDEN", "low": "KXLOWTDEN", "station": "KDEN", "lat": 39.86, "lon": -104.67, "tz": "US/Mountain", "window_start": 0, "window_end": 2, "pattern": "midnight"},
    "Los Angeles": {"high": "KXHIGHLAX", "low": "KXLOWTLAX", "station": "KLAX", "lat": 33.94, "lon": -118.41, "tz": "US/Pacific", "window_start": 5, "window_end": 8, "pattern": "sunrise"},
    "Miami": {"high": "KXHIGHMIA", "low": "KXLOWTMIA", "station": "KMIA", "lat": 25.80, "lon": -80.29, "tz": "US/Eastern", "window_start": 6, "window_end": 9, "pattern": "sunrise"},
    "New York City": {"high": "KXHIGHNY", "low": "KXLOWTNYC", "station": "KNYC", "lat": 40.78, "lon": -73.97, "tz": "US/Eastern", "window_start": 6, "window_end": 9, "pattern": "sunrise"},
    "Philadelphia": {"high": "KXHIGHPHL", "low": "KXLOWTPHL", "station": "KPHL", "lat": 39.87, "lon": -75.23, "tz": "US/Eastern", "window_start": 6, "window_end": 9, "pattern": "sunrise"},
}
CITY_LIST = sorted(CITY_CONFIG.keys())

query_params = st.query_params
default_city = query_params.get("city", "New York City")
if default_city not in CITY_LIST:
    default_city = "New York City"
is_owner = query_params.get("mode") == "owner"

if "view_mode" not in st.session_state:
    st.session_state.view_mode = "city"

# ============================================================
# FUNCTIONS
# ============================================================
@st.cache_data(ttl=120)
def fetch_nws_observations(station, city_tz_str):
    url = f"https://api.weather.gov/stations/{station}/observations"
    try:
        city_tz = pytz.timezone(city_tz_str)
        resp = requests.get(url, headers={"User-Agent": "TempEdge/3.0"}, timeout=15)
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
        low = min(r["temp"] for r in readings)
        high = max(r["temp"] for r in readings)
        readings_chrono = sorted(readings, key=lambda x: x["time"])
        confirm_time = None
        low_found = False
        for r in readings_chrono:
            if r["temp"] == low:
                low_found = True
            elif low_found and r["temp"] > low:
                confirm_time = r["time"]
                break
        oldest_time = readings_chrono[0]["time"] if readings_chrono else None
        newest_time = readings_chrono[-1]["time"] if readings_chrono else None
        display_readings = [{"time": r["time"].strftime("%H:%M"), "temp": r["temp"]} for r in readings]
        return current, low, high, display_readings, confirm_time, oldest_time, newest_time
    except:
        return None, None, None, [], None, None, None

@st.cache_data(ttl=300)
def fetch_nws_forecast(lat, lon):
    try:
        points_url = f"https://api.weather.gov/points/{lat},{lon}"
        resp = requests.get(points_url, headers={"User-Agent": "TempEdge/3.0"}, timeout=10)
        if resp.status_code != 200:
            return None
        forecast_url = resp.json().get("properties", {}).get("forecast")
        if not forecast_url:
            return None
        resp = requests.get(forecast_url, headers={"User-Agent": "TempEdge/3.0"}, timeout=10)
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
        resp = requests.get(points_url, headers={"User-Agent": "TempEdge/3.0"}, timeout=10)
        if resp.status_code != 200:
            return None, None
        forecast_url = resp.json().get("properties", {}).get("forecast")
        if not forecast_url:
            return None, None
        resp = requests.get(forecast_url, headers={"User-Agent": "TempEdge/3.0"}, timeout=10)
        if resp.status_code != 200:
            return None, None
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
                        return temp, p.get("shortForecast", "")
                except:
                    continue
        return None, None
    except:
        return None, None

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
    for b in brackets:
        if b['high'] == 999 and temp >= b['low']:
            return b
        if b['low'] == -999 and temp < b['high']:
            return b
        if b['low'] <= temp <= b['high']:
            return b
    return None

def get_lock_status(cfg, confirm_time, obs_low, readings):
    city_tz = pytz.timezone(cfg["tz"])
    city_now = datetime.now(city_tz)
    current_hour = city_now.hour
    window_start = cfg.get("window_start", 6)
    window_end = cfg.get("window_end", 9)
    pattern = cfg.get("pattern", "sunrise")
    
    rising_count = 0
    if readings and obs_low is not None:
        found_low = False
        for r in readings:
            if r["temp"] == obs_low:
                found_low = True
            elif found_low and r["temp"] > obs_low:
                rising_count += 1
                if rising_count >= 5:
                    break
    
    if pattern == "midnight":
        in_window = current_hour >= window_start and current_hour <= window_end
        past_window = current_hour > window_end and current_hour < 12
        if confirm_time and rising_count >= 2:
            return "locked", "🔒 LOCKED", 95
        elif confirm_time or rising_count >= 2:
            return "likely", "🔒 LIKELY", 80
        elif past_window and rising_count >= 1:
            return "likely", "🔒 LIKELY", 75
        elif in_window:
            return "watching", "👀 IN WINDOW", 40
        else:
            return "waiting", "⏳ WAITING", 20
    else:
        in_window = current_hour >= window_start and current_hour <= window_end
        past_window = current_hour > window_end
        if confirm_time and rising_count >= 2:
            return "locked", "🔒 LOCKED", 95
        elif confirm_time or rising_count >= 2:
            return "likely", "🔒 LIKELY", 80
        elif past_window and rising_count >= 1:
            return "likely", "🔒 LIKELY", 75
        elif in_window:
            return "watching", "👀 IN WINDOW", 40
        else:
            return "waiting", "⏳ WAITING", 20

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
                <b>🔒 LIKELY (75-80%):</b> Confirmation OR 2+ rising<br>
                <b>👀 WATCHING (40%):</b> In window<br>
                <b>⏳ WAITING:</b> Before window
            </div>
        </div>
        <div style="background:#2d1f0a;border:1px solid #f59e0b;border-radius:8px;padding:12px;margin-bottom:15px">
            <div style="color:#f59e0b;font-weight:700;margin-bottom:8px">🗽 TRADING WINDOWS (ET)</div>
            <div style="color:#c9d1d9;font-size:0.8em;line-height:1.6">
                <b>🌙 1-3 AM:</b> Chicago, Denver<br>
                <b>☀️ 6-10 AM:</b> Austin, Miami, NYC, Philly, LA
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
                <b>☀️ Sunrise:</b> Austin, Miami, NYC, Philly, LA
            </div>
        </div>
        """, unsafe_allow_html=True)

# ============================================================
# HEADER
# ============================================================
st.title("🌡️ LOW TEMP EDGE FINDER")
st.caption(f"Live NWS + Kalshi | {now.strftime('%b %d, %Y %I:%M %p ET')}")

if is_owner:
    c1, c2, c3 = st.columns(3)
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
    st.markdown("---")

# ============================================================
# TODAY'S SCANNER
# ============================================================
if is_owner and st.session_state.view_mode == "today":
    st.subheader("🔍 TODAY'S MISPRICING SCANNER")
    if st.button("🔄 Refresh", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    
    results = []
    for city_name, cfg in CITY_CONFIG.items():
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
            results.append({"city": city_name, "pattern": pattern_icon, "obs_low": obs_low, "bracket": winning["name"], "ask": winning["ask"], "edge": edge, "lock_status": lock_status, "url": winning["url"]})
        else:
            results.append({"city": city_name, "pattern": pattern_icon, "obs_low": obs_low, "bracket": "NO MATCH", "ask": 0, "edge": 0, "lock_status": lock_status})
    
    opps = [r for r in results if r.get("edge", 0) >= 5]
    if opps:
        st.markdown("### 🔥 OPPORTUNITIES")
        for o in sorted(opps, key=lambda x: x["edge"], reverse=True):
            st.markdown(f"**{o['pattern']} {o['city']}** | {o['lock_status']} | Low: {o['obs_low']}°F → {o['bracket']} | Ask: {o['ask']}¢ | **+{o['edge']}¢ edge** | [BUY]({o.get('url', '#')})")
    else:
        if now.hour >= 10:
            st.warning("⏰ TODAY'S MARKETS DONE - Check Tomorrow's Lottery!")
        else:
            st.info("No mispricing found yet.")
    
    st.markdown("### 📊 ALL CITIES")
    for r in results:
        if r.get("status") == "NO DATA":
            st.write(f"{r['pattern']} {r['city']} — No data")
        else:
            st.write(f"{r['pattern']} {r['city']} | {r['lock_status']} | {r['obs_low']}°F → {r.get('bracket', 'N/A')} | Ask: {r.get('ask', 0)}¢")

# ============================================================
# TOMORROW'S LOTTERY
# ============================================================
elif is_owner and st.session_state.view_mode == "tomorrow":
    tomorrow_str = (datetime.now(eastern) + timedelta(days=1)).strftime('%A, %b %d')
    st.subheader(f"🎰 TOMORROW'S LOTTERY ({tomorrow_str})")
    st.caption("Buy now while market is dead → Sell tomorrow when LOW locks")
    
    if st.button("🔄 Refresh", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    
    st.markdown("""
    <div style="background:#1a2e1a;border:1px solid #22c55e;border-radius:8px;padding:15px;margin-bottom:20px">
        <div style="color:#22c55e;font-weight:700">💡 THE PLAY</div>
        <div style="color:#c9d1d9;font-size:0.9em">
            Buy winning bracket at 15-30¢ → Sell tomorrow at 35-50¢ → Pocket 10-25¢
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    tickets = []
    all_cities = []
    for city_name, cfg in CITY_CONFIG.items():
        pattern_icon = "🌙" if cfg.get("pattern") == "midnight" else "☀️"
        forecast_low, desc = fetch_nws_tomorrow_low(cfg["lat"], cfg["lon"])
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
        st.markdown("### 🎰 CHEAP ENTRIES")
        for t in sorted(tickets, key=lambda x: x["ask"]):
            color = "#fbbf24" if t["ask"] < 40 else "#22c55e"
            st.markdown(f"""
            <div style="background:#0d1117;border:2px solid {color};border-radius:8px;padding:15px;margin:10px 0">
                <b style="color:{color}">{t['pattern']} {t['city']}</b> | NWS: {t['forecast']}°F → <b>{t['bracket']}</b> | Ask: <b style="color:#22c55e">{t['ask']}¢</b> | 
                <a href="{t['url']}" target="_blank" style="color:#fbbf24">BUY NOW →</a>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No cheap entries found. Prices may already be high.")
    
    st.markdown(f"### 📋 ALL CITIES - {tomorrow_str}")
    for c in all_cities:
        if c.get("status") == "NO FORECAST":
            st.write(f"{c['pattern']} {c['city']} — No forecast")
        elif c.get("status") == "NO MARKET":
            st.write(f"{c['pattern']} {c['city']} — NWS: {c['forecast']}°F — Market not open")
        elif c.get("status") == "NO BRACKET":
            st.write(f"{c['pattern']} {c['city']} — NWS: {c['forecast']}°F — No matching bracket")
        else:
            st.write(f"{c['pattern']} {c['city']} | NWS: {c['forecast']}°F → {c['bracket']} | Ask: {c['ask']}¢")

# ============================================================
# CITY VIEW
# ============================================================
else:
    c1, c2 = st.columns([4, 1])
    with c1:
        city = st.selectbox("📍 Select City", CITY_LIST, index=CITY_LIST.index(default_city))
    cfg = CITY_CONFIG.get(city, {})
    
    current_temp, obs_low, obs_high, readings, confirm_time, oldest_time, newest_time = fetch_nws_observations(cfg.get("station", "KNYC"), cfg.get("tz", "US/Eastern"))
    
    if obs_low and current_temp:
        status_code, lock_status, confidence = get_lock_status(cfg, confirm_time, obs_low, readings)
        lock_color = "#22c55e" if "LOCKED" in lock_status else "#3b82f6" if "LIKELY" in lock_status else "#fbbf24"
        
        st.markdown(f"""
        <div style="background:#0d1117;border:3px solid {lock_color};border-radius:16px;padding:25px;margin:20px 0;text-align:center">
            <div style="color:{lock_color};font-size:1.2em;font-weight:700">{lock_status}</div>
            <div style="color:#6b7280">Today's Low</div>
            <div style="color:#fff;font-size:4em;font-weight:800">{obs_low}°F</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"**Current:** {current_temp}°F | **High:** {obs_high}°F")
        
        if readings:
            with st.expander("📊 Recent Readings", expanded=True):
                for i, r in enumerate(readings[:12]):
                    marker = " ← LOW" if r['temp'] == obs_low else ""
                    st.write(f"{r['time']} → {r['temp']}°F{marker}")
    else:
        st.warning("⚠️ Could not fetch NWS data")
    
    st.markdown("---")
    forecast = fetch_nws_forecast(cfg.get("lat", 40.78), cfg.get("lon", -73.97))
    if forecast:
        st.subheader("📡 NWS Forecast")
        cols = st.columns(len(forecast))
        for i, p in enumerate(forecast):
            with cols[i]:
                st.metric(p.get("name", ""), f"{p.get('temperature', '')}°F")

st.markdown("---")
st.markdown('<div style="background:#f59e0b;padding:8px;border-radius:6px;text-align:center"><b style="color:#000">LOW Temp Edge Finder v7.0</b></div>', unsafe_allow_html=Tru
