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
# CITY CONFIG
# ============================================================
CITY_CONFIG = {
    "Austin": {"low": "KXLOWTAUS", "station": "KAUS", "lat": 30.19, "lon": -97.67, "tz": "US/Central", "pattern": "sunrise"},
    "Chicago": {"low": "KXLOWTCHI", "station": "KMDW", "lat": 41.79, "lon": -87.75, "tz": "US/Central", "pattern": "midnight"},
    "Denver": {"low": "KXLOWTDEN", "station": "KDEN", "lat": 39.86, "lon": -104.67, "tz": "US/Mountain", "pattern": "midnight"},
    "Los Angeles": {"low": "KXLOWTLAX", "station": "KLAX", "lat": 33.94, "lon": -118.41, "tz": "US/Pacific", "pattern": "sunrise"},
    "Miami": {"low": "KXLOWTMIA", "station": "KMIA", "lat": 25.80, "lon": -80.29, "tz": "US/Eastern", "pattern": "sunrise"},
    "New York City": {"low": "KXLOWTNYC", "station": "KNYC", "lat": 40.78, "lon": -73.97, "tz": "US/Eastern", "pattern": "sunrise"},
    "Philadelphia": {"low": "KXLOWTPHL", "station": "KPHL", "lat": 39.87, "lon": -75.23, "tz": "US/Eastern", "pattern": "sunrise"},
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
        resp = requests.get(url, headers={"User-Agent": "TempEdge/7.0"}, timeout=15)
        if resp.status_code != 200:
            return None, None, None, [], None
        observations = resp.json().get("features", [])
        if not observations:
            return None, None, None, [], None
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
            return None, None, None, [], None
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
        display_readings = [{"time": r["time"].strftime("%H:%M"), "temp": r["temp"]} for r in readings]
        return current, obs_low, obs_high, display_readings, confirm_time
    except:
        return None, None, None, [], None

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
            <div style="color:#f59e0b;font-weight:700;margin-bottom:8px">🗽 LOW PATTERNS</div>
            <div style="color:#c9d1d9;font-size:0.8em;line-height:1.6">
                <b>🌙 Midnight:</b> Chicago, Denver<br>
                <b>☀️ Sunrise:</b> Austin, LA, Miami, NYC, Philly
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
                <b>☀️ Sunrise:</b> Austin, LA, Miami, NYC, Philly
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
# TODAY'S SCANNER (OWNER ONLY)
# ============================================================
if is_owner and st.session_state.view_mode == "today":
    st.subheader("🔍 TODAY'S MISPRICING SCANNER")
    if st.button("🔄 Refresh All", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    
    results = []
    for city_name, cfg in CITY_CONFIG.items():
        current_temp, obs_low, obs_high, readings, confirm_time = fetch_nws_observations(cfg["station"], cfg["tz"])
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
    st.caption("Buy now while market is dead → Sell tomorrow when LOW locks")
    
    if st.button("🔄 Refresh All", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    
    st.markdown("""
    <div style="background:#1a2e1a;border:1px solid #22c55e;border-radius:8px;padding:15px;margin-bottom:20px">
        <div style="color:#22c55e;font-weight:700">💡 THE PLAY</div>
        <div style="color:#c9d1d9;font-size:0.9em">
            Buy winning bracket at 15-30¢ tonight → Sell tomorrow AM at 35-50¢ → Pocket 10-25¢
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    tickets = []
    all_cities = []
    for city_name, cfg in CITY_CONFIG.items():
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
    
    if tickets:
        st.markdown("### 🎰 CHEAP ENTRIES (<60¢)")
        for t in sorted(tickets, key=lambda x: x["ask"]):
            color = "#fbbf24" if t["ask"] < 40 else "#22c55e"
            st.markdown(f"""
            <div style="background:#0d1117;border:2px solid {color};border-radius:8px;padding:15px;margin:10px 0">
                <b style="color:{color}">{t['pattern']} {t['city']}</b> | NWS: {t['forecast']}°F → <b>{t['bracket']}</b> | 
                Ask: <b style="color:#22c55e">{t['ask']}¢</b> | 
                <a href="{t['url']}" target="_blank" style="color:#fbbf24">BUY NOW →</a>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No cheap entries found. All brackets priced above 60¢.")
    
    st.markdown(f"### 📋 ALL CITIES - {tomorrow_str}")
    for c in all_cities:
        if c.get("status") == "NO FORECAST":
            st.write(f"{c['pattern']} **{c['city']}** — ❌ No forecast available")
        elif c.get("status") == "NO MARKET":
            st.write(f"{c['pattern']} **{c['city']}** — NWS: {c['forecast']}°F — Market not open yet")
        elif c.get("status") == "NO BRACKET":
            st.write(f"{c['pattern']} **{c['city']}** — NWS: {c['forecast']}°F — No matching bracket")
        else:
            st.write(f"{c['pattern']} **{c['city']}** | NWS: {c['forecast']}°F → {c['bracket']} | Ask: {c['ask']}¢")

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
    current_temp, obs_low, obs_high, readings, confirm_time = fetch_nws_observations(cfg.get("station", "KNYC"), cfg.get("tz", "US/Eastern"))
    
    if obs_low is not None and current_temp is not None:
        status_code, lock_status, confidence = get_lock_status(cfg, confirm_time, obs_low, readings)
        lock_color = "#22c55e" if status_code == "locked" else "#3b82f6" if status_code == "likely" else "#fbbf24" if status_code == "watching" else "#6b7280"
        
        st.markdown(f"""
        <div style="background:#0d1117;border:3px solid {lock_color};border-radius:16px;padding:25px;margin:20px 0;text-align:center">
            <div style="color:{lock_color};font-size:1.2em;font-weight:700">{lock_status}</div>
            <div style="color:#6b7280">Today's Low</div>
            <div style="color:#fff;font-size:4em;font-weight:800">{obs_low}°F</div>
            <div style="color:#6b7280;font-size:0.9em">Rounds to {round(obs_low)}°F</div>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        col1.metric("🌡️ Current", f"{current_temp}°F")
        col2.metric("📈 High", f"{obs_high}°F")
        col3.metric("📉 Low", f"{obs_low}°F")
        
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
            with st.expander("📊 Recent Readings", expanded=False):
                display_count = len(readings) if is_owner else min(12, len(readings))
                for i, r in enumerate(readings[:display_count]):
                    marker = " ← **LOW**" if r['temp'] == obs_low else ""
                    st.write(f"{r['time']} → {r['temp']}°F{marker}")
    else:
        st.warning("⚠️ Could not fetch NWS data for this city")
    
    st.markdown("---")
    forecast = fetch_nws_forecast(cfg.get("lat", 40.78), cfg.get("lon", -73.97))
    if forecast:
        st.subheader("📡 NWS Forecast")
        cols = st.columns(len(forecast))
        for i, p in enumerate(forecast):
            with cols[i]:
                icon = "☀️" if p.get("isDaytime", True) else "🌙"
                st.metric(f"{icon} {p.get('name', '')[:8]}", f"{p.get('temperature', '')}°F")

# ============================================================
# FOOTER
# ============================================================
st.markdown("---")
st.markdown('<div style="background:#f59e0b;padding:8px;border-radius:6px;text-align:center"><b style="color:#000">LOW Temp Edge Finder v7.1</b></div>', unsafe_allow_html=True)
