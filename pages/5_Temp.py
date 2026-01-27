import streamlit as st
import requests
from datetime import datetime, timedelta
import pytz
import re
import math
from bs4 import BeautifulSoup

st.set_page_config(page_title="LOW Temp Edge Finder", page_icon="🌡️", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<script async src="https://www.googletagmanager.com/gtag/js?id=G-NQKY5VQ376"></script>
<script>window.dataLayer = window.dataLayer || [];function gtag(){dataLayer.push(arguments);}gtag('js', new Date());gtag('config', 'G-NQKY5VQ376');</script>
""", unsafe_allow_html=True)

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

if "scanner_view" not in st.session_state:
    st.session_state.scanner_view = False

# ============================================================
# SHARED FUNCTIONS
# ============================================================
def get_bracket_bounds(range_str):
    tl = range_str.lower()
    below_match = re.search(r'<\s*(\d+)°', range_str)
    if below_match:
        return -999, int(below_match.group(1)) - 0.5
    above_match = re.search(r'>\s*(\d+)°', range_str)
    if above_match:
        return int(above_match.group(1)) + 0.5, 999
    range_match = re.search(r'(\d+)[-–]\s*(\d+)°|(\d+)°?\s*to\s*(\d+)°', range_str)
    if range_match:
        if range_match.group(1) and range_match.group(2):
            low, high = int(range_match.group(1)), int(range_match.group(2))
        else:
            low, high = int(range_match.group(3)), int(range_match.group(4))
        return low - 0.5, high + 0.5
    if "or below" in tl or "below" in tl:
        nums = re.findall(r'(\d+)°', range_str)
        if nums:
            return -999, int(nums[0]) + 0.5
    if "or above" in tl or "above" in tl:
        nums = re.findall(r'(\d+)°', range_str)
        if nums:
            return int(nums[0]) - 0.5, 999
    nums = re.findall(r'(\d+)°', range_str)
    if len(nums) >= 2:
        return int(nums[0]) - 0.5, int(nums[1]) + 0.5
    elif nums:
        return int(nums[0]) - 0.5, int(nums[0]) + 0.5
    return 0, 100

@st.cache_data(ttl=120)
def fetch_nws_6hr_extremes(station, city_tz_str):
    url = f"https://forecast.weather.gov/data/obhistory/{station}.html"
    try:
        city_tz = pytz.timezone(city_tz_str)
        resp = requests.get(url, headers={"User-Agent": "TempEdge/3.0"}, timeout=15)
        if resp.status_code != 200:
            return {}
        soup = BeautifulSoup(resp.text, 'html.parser')
        table = soup.find('table')
        if not table:
            return {}
        rows = table.find_all('tr')
        extremes = {}
        today = datetime.now(city_tz).day
        for row in rows[3:]:
            cells = row.find_all('td')
            if len(cells) >= 10:
                try:
                    date_val = cells[0].text.strip()
                    time_val = cells[1].text.strip()
                    if date_val and int(date_val) != today:
                        continue
                    max_6hr_text = cells[8].text.strip() if len(cells) > 8 else ""
                    min_6hr_text = cells[9].text.strip() if len(cells) > 9 else ""
                    if max_6hr_text or min_6hr_text:
                        max_val = float(max_6hr_text) if max_6hr_text else None
                        min_val = float(min_6hr_text) if min_6hr_text else None
                        if max_val is not None or min_val is not None:
                            time_key = time_val.replace(":", "")[:4]
                            time_key = time_key[:2] + ":" + time_key[2:]
                            extremes[time_key] = {"max": max_val, "min": min_val}
                except:
                    continue
        return extremes
    except:
        return {}

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
    """Get tomorrow's forecasted low from NWS 7-day forecast"""
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
                    # Tomorrow night = tomorrow's low
                    if period_date == tomorrow:
                        short_forecast = p.get("shortForecast", "")
                        return temp, short_forecast
                except:
                    continue
        return None, None
    except:
        return None, None

@st.cache_data(ttl=60)
def fetch_kalshi_tomorrow_brackets(series_ticker):
    """Fetch tomorrow's Kalshi brackets"""
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
            ticker = m.get("ticker", "")
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
                bracket_name = f"{low_bound}° or above"
            below_match = re.search(r'(below|under|less than)\s*(\d+)°', title, re.IGNORECASE)
            if below_match and not range_match:
                high_bound = int(below_match.group(2))
                low_bound = -999
                bracket_name = f"below {high_bound}°"
            
            if low_bound is not None and high_bound is not None:
                event_ticker = m.get("event_ticker", "")
                kalshi_url = f"https://kalshi.com/markets/{series_ticker.lower()}"
                brackets.append({"name": bracket_name, "low": low_bound, "high": high_bound, "bid": yes_bid, "ask": yes_ask, "url": kalshi_url, "ticker": ticker})
        
        brackets.sort(key=lambda x: x['low'])
        return brackets
    except:
        return []

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
            ticker = m.get("ticker", "")
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
                bracket_name = f"{low_bound}° or above"
            below_match = re.search(r'(below|under|less than)\s*(\d+)°', title, re.IGNORECASE)
            if below_match and not range_match:
                high_bound = int(below_match.group(2))
                low_bound = -999
                bracket_name = f"below {high_bound}°"
            if low_bound is not None and high_bound is not None:
                event_ticker = m.get("event_ticker", "")
                kalshi_url = f"https://kalshi.com/markets/{series_ticker.lower()}" if series_ticker else f"https://kalshi.com/markets/{event_ticker}"
                brackets.append({"name": bracket_name, "low": low_bound, "high": high_bound, "bid": yes_bid, "ask": yes_ask, "url": kalshi_url, "ticker": ticker})
        brackets.sort(key=lambda x: x['low'])
        return brackets
    except:
        return []

def find_winning_bracket(low_temp, brackets):
    for b in brackets:
        if b['high'] == 999 and low_temp >= b['low']:
            return b
        if b['low'] == -999 and low_temp < b['high']:
            return b
        if b['low'] <= low_temp <= b['high']:
            return b
        if b['low'] < low_temp <= b['high']:
            return b
    return None

def check_low_locked(city_tz_str):
    city_tz = pytz.timezone(city_tz_str)
    city_now = datetime.now(city_tz)
    return city_now.hour >= 7

def get_lock_status(cfg, confirm_time, obs_low, readings):
    """
    Determine lock status based on:
    1. Time window (when LOW typically occurs)
    2. Confirmation (temps rising after low point)
    
    Returns: (status_code, status_text, confidence)
    - status_code: "locked", "likely", "watching", "waiting"
    - status_text: Display text
    - confidence: 0-100
    """
    city_tz = pytz.timezone(cfg["tz"])
    city_now = datetime.now(city_tz)
    current_hour = city_now.hour
    
    window_start = cfg.get("window_start", 6)
    window_end = cfg.get("window_end", 9)
    pattern = cfg.get("pattern", "sunrise")
    
    # Count rising readings after the low
    rising_count = 0
    if readings and obs_low is not None:
        found_low = False
        for r in readings:  # readings are newest first
            if r["temp"] == obs_low:
                found_low = True
            elif found_low and r["temp"] > obs_low:
                rising_count += 1
    
    # For midnight cities, handle the 0-2 AM window specially
    if pattern == "midnight":
        in_window = current_hour >= window_start and current_hour <= window_end
        past_window = current_hour > window_end and current_hour < 12  # Before noon
        
        if confirm_time and rising_count >= 2:
            return "locked", "🔒 LOCKED", 95
        elif confirm_time or rising_count >= 2:
            return "likely", "🔒 LIKELY", 80
        elif past_window:
            # Past the window but no confirmation - still likely locked
            if rising_count >= 1:
                return "likely", "🔒 LIKELY", 75
            else:
                return "watching", "👀 WATCHING", 60
        elif in_window:
            return "watching", "👀 IN WINDOW", 40
        else:
            return "waiting", "⏳ WAITING", 20
    
    # For sunrise cities
    else:
        in_window = current_hour >= window_start and current_hour <= window_end
        past_window = current_hour > window_end
        
        if confirm_time and rising_count >= 2:
            return "locked", "🔒 LOCKED", 95
        elif confirm_time or rising_count >= 2:
            return "likely", "🔒 LIKELY", 80
        elif past_window:
            # Past the typical window
            if rising_count >= 1:
                return "likely", "🔒 LIKELY", 75
            else:
                return "watching", "👀 CHECK DATA", 50
        elif in_window:
            if rising_count >= 1:
                return "watching", "👀 RISING", 55
            else:
                return "watching", "👀 IN WINDOW", 40
        else:
            return "waiting", "⏳ WAITING", 20

def get_lottery_status(cfg, obs_low, ask_price, confirm_time, readings):
    """Determine if this is a lottery ticket opportunity"""
    status_code, status_text, confidence = get_lock_status(cfg, confirm_time, obs_low, readings)
    
    if status_code not in ["locked", "likely"]:
        return None, None, None, None
    
    if obs_low is None or ask_price is None:
        return None, None, None, None
    
    # LOW is locked/likely - check if market is stale
    edge = 100 - ask_price
    
    if ask_price < 50 and confidence >= 75:
        return "🎰 LOTTERY TICKET", f"LOW {status_text} at {obs_low}°F, market still at {ask_price}¢!", edge, confidence
    elif ask_price < 65 and confidence >= 75:
        return "💰 BIG EDGE", f"LOW {status_text}, market catching up ({ask_price}¢)", edge, confidence
    elif ask_price < 80 and confidence >= 70:
        return "✅ GOOD EDGE", f"LOW {status_text}, decent price ({ask_price}¢)", edge, confidence
    elif ask_price < 90 and confidence >= 80:
        return "📈 SMALL EDGE", f"LOW {status_text}, thin margin ({ask_price}¢)", edge, confidence
    else:
        return None, None, None, None

# ============================================================
# SIDEBAR LEGENDS (OWNER ONLY - BOTH VIEWS)
# ============================================================
if is_owner:
    with st.sidebar:
        st.markdown("""
        <div style="background:#1a2e1a;border:1px solid #22c55e;border-radius:8px;padding:12px;margin-bottom:15px">
            <div style="color:#22c55e;font-weight:700;margin-bottom:8px">🔒 EDGE TIPS</div>
            <div style="color:#c9d1d9;font-size:0.85em;line-height:1.5">
                <b>LOW (Safer):</b><br>
                • Wait 1hr after reversal<br>
                • 2+ rising readings = locked<br>
                • Sun up = no going back<br><br>
                <b>6hr Extremes:</b><br>
                • 06:51 & 12:51 bracket LOW<br>
                • Official NWS confirmation
            </div>
        </div>
        <div style="background:#2d1f0a;border:1px solid #f59e0b;border-radius:8px;padding:12px;margin-bottom:15px">
            <div style="color:#f59e0b;font-weight:700;margin-bottom:8px">🗽 YOUR TRADING SCHEDULE (ET)</div>
            <div style="color:#c9d1d9;font-size:0.8em;line-height:1.6">
                <b>🌙 1-2 AM</b> → Chicago, Denver<br>
                <span style="color:#6b7280;font-size:0.85em;margin-left:12px">Midnight LOWs - trade while they sleep!</span><br>
                <b>☀️ 7-8 AM</b> → Austin, Miami, NYC, Philly<br>
                <span style="color:#6b7280;font-size:0.85em;margin-left:12px">Sunrise LOWs - Eastern cities</span><br>
                <b>☀️ 9-10 AM</b> → Los Angeles<br>
                <span style="color:#6b7280;font-size:0.85em;margin-left:12px">West coast sunrise</span>
            </div>
        </div>
        <div style="background:#1a1a2e;border:1px solid #3b82f6;border-radius:8px;padding:12px;margin-bottom:15px">
            <div style="color:#3b82f6;font-weight:700;margin-bottom:8px">⏰ LOW LOCK-IN TIMES</div>
            <div style="color:#c9d1d9;font-size:0.8em;line-height:1.6">
                <b>🌙 MIDNIGHT CITIES:</b><br>
                • Chicago ~00:15 CT (1:15 AM ET)<br>
                • Denver ~00:40 MT (2:40 AM ET)<br><br>
                <b>☀️ SUNRISE CITIES:</b><br>
                • Austin ~06:40 CT (7:40 AM ET)<br>
                • Miami ~07:40 ET<br>
                • NYC ~07:51 ET<br>
                • Philly ~07:54 ET<br>
                • LA ~06:00 PT (9:00 AM ET)
            </div>
        </div>
        <div style="background:#1a1a2e;border:1px solid #22c55e;border-radius:8px;padding:12px;margin-bottom:15px">
            <div style="color:#22c55e;font-weight:700;margin-bottom:8px">💰 ENTRY THRESHOLDS (Ask)</div>
            <div style="color:#c9d1d9;font-size:0.8em;line-height:1.6">
                <b>🔥 &lt;85¢</b> = JUMP IN (+15¢)<br>
                <b>✅ 85-90¢</b> = Good (+10-15¢)<br>
                <b>⚠️ 90-95¢</b> = Small edge (+5-10¢)<br>
                <b>❌ 95¢+</b> = Skip it<br><br>
                <span style="color:#9ca3af">Only showing 10¢+ edge opps</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
else:
    with st.sidebar:
        st.markdown("""
        <div style="background:#1a1a2e;border:1px solid #3b82f6;border-radius:8px;padding:12px;margin-bottom:15px">
            <div style="color:#3b82f6;font-weight:700;margin-bottom:8px">⏰ LOW LOCK-IN TIMES (ET)</div>
            <div style="color:#c9d1d9;font-size:0.8em;line-height:1.6">
                <b>🌙 MIDNIGHT CITIES:</b><br>
                • Chicago ~1:15 AM ET<br>
                • Denver ~2:40 AM ET<br><br>
                <b>☀️ SUNRISE CITIES:</b><br>
                • Austin ~7:40 AM ET<br>
                • Miami ~7:40 AM ET<br>
                • NYC ~7:51 AM ET<br>
                • Philly ~7:54 AM ET<br>
                • LA ~9:00 AM ET
            </div>
        </div>
        """, unsafe_allow_html=True)

# ============================================================
# HEADER + OWNER TOGGLE
# ============================================================
st.title("🌡️ LOW TEMP EDGE FINDER")
st.caption(f"Live NWS Observations + Kalshi | {now.strftime('%b %d, %Y %I:%M %p ET')}")

if is_owner:
    col_toggle1, col_toggle2, col_toggle3 = st.columns([1, 2, 1])
    with col_toggle2:
        view_label = "🔍 SCANNER VIEW" if st.session_state.scanner_view else "📍 CITY VIEW"
        if st.button(f"Switch to {'📍 City View' if st.session_state.scanner_view else '🔍 Scanner View'}", use_container_width=True):
            st.session_state.scanner_view = not st.session_state.scanner_view
            st.rerun()
        st.markdown(f"<div style='text-align:center;color:#22c55e;font-size:0.9em;margin-top:5px'>Current: {view_label}</div>", unsafe_allow_html=True)
    st.markdown("---")

# ============================================================
# SCANNER VIEW (OWNER ONLY)
# ============================================================
if is_owner and st.session_state.scanner_view:
    st.subheader("🎰 LOTTERY TICKET SCANNER")
    st.caption("Find locked LOWs where market hasn't caught up yet")
    
    if st.button("🔄 Refresh Scan", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    
    # Show current time context
    st.markdown(f"""
    <div style="background:#1a1a2e;border:1px solid #3b82f6;border-radius:8px;padding:15px;margin-bottom:20px">
        <div style="display:flex;justify-content:space-around;flex-wrap:wrap;gap:15px;text-align:center">
            <div>
                <div style="color:#6b7280;font-size:0.8em">YOUR TIME (ET)</div>
                <div style="color:#3b82f6;font-size:1.5em;font-weight:700">{now.strftime('%I:%M %p')}</div>
            </div>
            <div>
                <div style="color:#6b7280;font-size:0.8em">CHICAGO (CT)</div>
                <div style="color:#fbbf24;font-size:1.5em;font-weight:700">{datetime.now(pytz.timezone('US/Central')).strftime('%I:%M %p')}</div>
            </div>
            <div>
                <div style="color:#6b7280;font-size:0.8em">DENVER (MT)</div>
                <div style="color:#fbbf24;font-size:1.5em;font-weight:700">{datetime.now(pytz.timezone('US/Mountain')).strftime('%I:%M %p')}</div>
            </div>
            <div>
                <div style="color:#6b7280;font-size:0.8em">LA (PT)</div>
                <div style="color:#22c55e;font-size:1.5em;font-weight:700">{datetime.now(pytz.timezone('US/Pacific')).strftime('%I:%M %p')}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    results = []
    lottery_tickets = []
    
    with st.spinner("Scanning all 7 cities..."):
        for city_name, cfg in CITY_CONFIG.items():
            current_temp, obs_low, obs_high, readings, confirm_time, oldest_time, newest_time = fetch_nws_observations(cfg["station"], cfg["tz"])
            brackets = fetch_kalshi_brackets(cfg["low"])
            
            is_locked, lock_status = check_low_locked_precise(cfg)
            pattern = cfg.get("pattern", "sunrise")
            pattern_icon = "🌙" if pattern == "midnight" else "☀️"
            
            city_tz = pytz.timezone(cfg["tz"])
            local_time = datetime.now(city_tz).strftime('%H:%M')
            lock_time = f"{cfg.get('low_hour', 7):02d}:{cfg.get('low_min', 0):02d}"
            
            if obs_low is None:
                results.append({
                    "city": city_name, "status": "❌ NO DATA", "obs_low": None, "bracket": None, 
                    "price": None, "edge": None, "url": None, "locked": False, "confirm_time": None,
                    "lock_status": lock_status, "pattern": pattern_icon, "local_time": local_time, "lock_time": lock_time
                })
                continue
            
            winning = find_winning_bracket(obs_low, brackets)
            
            if winning:
                bid = winning["bid"]
                ask = winning["ask"]
                
                # Check for lottery ticket opportunity
                lottery_type, lottery_msg, lottery_edge = get_lottery_status(cfg, obs_low, ask, confirm_time)
                
                if lottery_type:
                    lottery_tickets.append({
                        "city": city_name, "obs_low": obs_low, "bracket": winning["name"],
                        "bid": bid, "ask": ask, "edge": lottery_edge, "url": winning["url"],
                        "lottery_type": lottery_type, "lottery_msg": lottery_msg,
                        "pattern": pattern_icon, "lock_status": lock_status, "confirm_time": confirm_time
                    })
                
                # Rating based on ask price
                if ask < 85:
                    rating = "🔥"
                elif ask < 90:
                    rating = "✅"
                elif ask < 95:
                    rating = "⚠️"
                else:
                    rating = "❌"
                
                edge = (100 - ask) if is_locked and ask < 95 else 0
                
                results.append({
                    "city": city_name, "status": "✅", "obs_low": obs_low, "bracket": winning["name"],
                    "bid": bid, "ask": ask, "edge": edge, "rating": rating, "url": winning["url"],
                    "locked": is_locked, "confirm_time": confirm_time, "lock_status": lock_status,
                    "pattern": pattern_icon, "local_time": local_time, "lock_time": lock_time
                })
            else:
                results.append({
                    "city": city_name, "status": "⚠️ NO BRACKET", "obs_low": obs_low, "bracket": None,
                    "price": None, "edge": None, "url": None, "locked": is_locked, "confirm_time": confirm_time,
                    "lock_status": lock_status, "pattern": pattern_icon, "local_time": local_time, "lock_time": lock_time
                })
    
    # LOTTERY TICKETS SECTION
    if lottery_tickets:
        st.markdown("### 🎰 LOTTERY TICKETS - ACT NOW!")
        st.markdown("<div style='color:#22c55e;font-size:0.9em;margin-bottom:15px'>LOW is LOCKED but market hasn't caught up. This is free money.</div>", unsafe_allow_html=True)
        
        lottery_tickets.sort(key=lambda x: x["edge"], reverse=True)
        
        for t in lottery_tickets:
            confirm_text = "✓ Confirmed" if t.get("confirm_time") else "Observed"
            ticket_color = "#fbbf24" if t["lottery_type"] == "🎰 LOTTERY TICKET" else "#22c55e" if t["lottery_type"] == "💰 BIG EDGE" else "#3b82f6"
            
            st.markdown(f"""
            <div style="background:linear-gradient(135deg,#1a2e1a,#0d1117);border:3px solid {ticket_color};border-radius:16px;padding:25px;margin:15px 0;box-shadow:0 0 30px rgba(251,191,36,0.3)">
                <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:10px">
                    <div>
                        <span style="color:{ticket_color};font-size:2em;font-weight:800">{t['lottery_type']}</span>
                        <span style="color:#6b7280;margin-left:15px;font-size:1.2em">{t['pattern']} {t['city']}</span>
                    </div>
                    <div style="text-align:right">
                        <div style="color:#22c55e;font-size:2.5em;font-weight:800">+{t['edge']:.0f}¢</div>
                        <div style="color:#6b7280;font-size:0.9em">potential profit</div>
                    </div>
                </div>
                <div style="margin-top:20px;padding:15px;background:#161b22;border-radius:8px">
                    <div style="color:#fbbf24;font-size:1.1em;margin-bottom:10px">{t['lottery_msg']}</div>
                    <div style="display:flex;justify-content:space-around;flex-wrap:wrap;gap:15px;margin-top:15px">
                        <div style="text-align:center">
                            <div style="color:#6b7280;font-size:0.8em">ACTUAL LOW</div>
                            <div style="color:#3b82f6;font-size:1.8em;font-weight:700">{t['obs_low']}°F</div>
                            <div style="color:#6b7280;font-size:0.75em">{confirm_text}</div>
                        </div>
                        <div style="text-align:center">
                            <div style="color:#6b7280;font-size:0.8em">WINNING BRACKET</div>
                            <div style="color:#fbbf24;font-size:1.8em;font-weight:700">{t['bracket']}</div>
                        </div>
                        <div style="text-align:center">
                            <div style="color:#6b7280;font-size:0.8em">CURRENT ASK</div>
                            <div style="color:#ef4444;font-size:1.8em;font-weight:700">{t['ask']:.0f}¢</div>
                        </div>
                        <div style="text-align:center">
                            <div style="color:#6b7280;font-size:0.8em">SETTLES AT</div>
                            <div style="color:#22c55e;font-size:1.8em;font-weight:700">100¢</div>
                        </div>
                    </div>
                </div>
                <a href="{t['url']}" target="_blank" style="text-decoration:none;display:block;margin-top:20px">
                    <div style="background:linear-gradient(135deg,#fbbf24,#f59e0b);padding:15px 25px;border-radius:8px;text-align:center;cursor:pointer">
                        <span style="color:#000;font-weight:800;font-size:1.3em">🎰 BUY {t['bracket']} NOW → GUARANTEED +{t['edge']:.0f}¢</span>
                    </div>
                </a>
            </div>
            """, unsafe_allow_html=True)
    else:
        # Check what's coming up
        upcoming = []
        for city_name, cfg in CITY_CONFIG.items():
            is_locked, lock_status = check_low_locked_precise(cfg)
            if not is_locked:
                city_tz = pytz.timezone(cfg["tz"])
                lock_time_local = f"{cfg.get('low_hour', 7):02d}:{cfg.get('low_min', 0):02d}"
                pattern = "🌙" if cfg.get("pattern") == "midnight" else "☀️"
                upcoming.append(f"{pattern} {city_name} locks ~{lock_time_local} local")
        
        if upcoming:
            st.markdown("### ⏳ NO LOTTERY TICKETS RIGHT NOW")
            st.info(f"**Upcoming locks:**\n" + "\n".join(upcoming))
        else:
            st.success("All cities locked! Check ALL CITIES below for edge opportunities.")
    
    # ALL CITIES STATUS
    st.markdown("### 📊 ALL CITIES STATUS")
    
    for r in results:
        if r["status"] == "❌ NO DATA":
            st.markdown(f"""
            <div style='background:#1a1a2e;border:1px solid #30363d;border-radius:8px;padding:12px;margin:5px 0'>
                <span style='color:#ef4444;font-weight:600'>{r['pattern']} {r['city']}</span>
                <span style='color:#6b7280;margin-left:10px'>— No NWS data</span>
            </div>""", unsafe_allow_html=True)
        elif r["status"] == "⚠️ NO BRACKET":
            st.markdown(f"""
            <div style='background:#1a1a2e;border:1px solid #30363d;border-radius:8px;padding:12px;margin:5px 0'>
                <span style='color:#f59e0b;font-weight:600'>{r['pattern']} {r['city']}</span>
                <span style='color:#6b7280;margin-left:8px'>{r['lock_status']}</span>
                <span style='color:#6b7280;margin-left:10px'>— Low: {r['obs_low']}°F — No matching Kalshi bracket</span>
            </div>""", unsafe_allow_html=True)
        else:
            lock_color = "#22c55e" if "LOCKED" in r["lock_status"] else "#f59e0b"
            edge_display = f"<span style='color:#22c55e;font-weight:700'>+{r['edge']:.0f}¢</span>" if r["edge"] and r["edge"] >= 10 else "<span style='color:#6b7280'>—</span>"
            ask_color = "#22c55e" if r["ask"] and r["ask"] < 50 else "#3b82f6" if r["ask"] and r["ask"] < 75 else "#f59e0b" if r["ask"] and r["ask"] < 90 else "#9ca3af"
            
            st.markdown(f"""
            <div style='background:#0d1117;border:1px solid #30363d;border-radius:8px;padding:12px;margin:5px 0'>
                <div style='display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:10px'>
                    <div>
                        <span style='color:#fff;font-weight:600'>{r['pattern']} {r['city']}</span>
                        <span style='color:{lock_color};margin-left:8px;font-size:0.85em'>{r['lock_status']}</span>
                        <span style='color:#6b7280;margin-left:8px;font-size:0.8em'>({r['local_time']} local, locks ~{r['lock_time']})</span>
                    </div>
                    <div>
                        <span style='color:#3b82f6;font-weight:600'>{r['obs_low']}°F</span>
                        <span style='color:#6b7280;margin:0 8px'>→</span>
                        <span style='color:#fbbf24'>{r['bracket']}</span>
                        <span style='color:#6b7280;margin:0 5px'>|</span>
                        <span style='color:#9ca3af'>Ask:</span>
                        <span style='color:{ask_color};margin:0 3px;font-weight:700'>{r['ask']:.0f}¢</span>
                        <span style='color:#6b7280;margin:0 5px'>|</span>
                        {edge_display}
                    </div>
                </div>
            </div>""", unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown(f"<div style='text-align:center;color:#6b7280;font-size:0.8em'>Last scan: {now.strftime('%I:%M %p ET')} | 🌙 = Midnight LOW | ☀️ = Sunrise LOW</div>", unsafe_allow_html=True)

    # ============================================================
    # TOMORROW'S LOW SECTION (OWNER ONLY)
    # ============================================================
    st.markdown("---")
    tomorrow_date = (datetime.now(eastern) + timedelta(days=1)).strftime('%A, %b %d')
    st.subheader(f"🔮 TOMORROW'S LOW ({tomorrow_date})")
    st.caption("Buy now, sell tomorrow 7 AM when LOW locks in")
    
    tomorrow_results = []
    with st.spinner("Scanning tomorrow's markets..."):
        for city_name, cfg in CITY_CONFIG.items():
            forecast_low, forecast_desc = fetch_nws_tomorrow_low(cfg["lat"], cfg["lon"])
            brackets = fetch_kalshi_tomorrow_brackets(cfg["low"])
            
            if forecast_low is None:
                tomorrow_results.append({"city": city_name, "status": "❌ NO FORECAST", "forecast_low": None, "bracket": None, "ask": None, "url": None, "desc": None})
                continue
            
            if not brackets:
                tomorrow_results.append({"city": city_name, "status": "⚠️ NO MARKET", "forecast_low": forecast_low, "bracket": None, "ask": None, "url": None, "desc": forecast_desc})
                continue
            
            winning = find_winning_bracket(forecast_low, brackets)
            if winning:
                tomorrow_results.append({
                    "city": city_name, 
                    "status": "✅", 
                    "forecast_low": forecast_low, 
                    "bracket": winning["name"], 
                    "bid": winning["bid"],
                    "ask": winning["ask"], 
                    "url": winning["url"],
                    "desc": forecast_desc
                })
            else:
                tomorrow_results.append({"city": city_name, "status": "⚠️ NO BRACKET", "forecast_low": forecast_low, "bracket": None, "ask": None, "url": None, "desc": forecast_desc})
    
    # Show cheap opportunities (ask < 40¢)
    cheap_opps = [r for r in tomorrow_results if r.get("ask") and r["ask"] < 40]
    cheap_opps.sort(key=lambda x: x["ask"])
    
    if cheap_opps:
        st.markdown("### 💰 CHEAP ENTRIES (Ask < 40¢)")
        for r in cheap_opps:
            potential = 100 - r["ask"]
            # Check if forecast is in middle of bracket (safer)
            bracket_low, bracket_high = 0, 100
            range_match = re.search(r'(\d+)-(\d+)', r["bracket"])
            if range_match:
                bracket_low, bracket_high = int(range_match.group(1)), int(range_match.group(2))
            mid = (bracket_low + bracket_high) / 2
            buffer = abs(r["forecast_low"] - mid)
            safety = "🎯 CENTERED" if buffer <= 1 else "⚠️ EDGE" if buffer <= 2 else "🔴 RISKY"
            
            st.markdown(f"""
            <div style="background:linear-gradient(135deg,#1a1a2e,#0d1117);border:2px solid #3b82f6;border-radius:12px;padding:20px;margin:10px 0">
                <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:10px">
                    <div>
                        <span style="color:#3b82f6;font-size:1.4em;font-weight:700">{r['city']}</span>
                    </div>
                    <div style="text-align:right">
                        <span style="color:#9ca3af;font-size:0.9em">Ask:</span>
                        <span style="color:#22c55e;font-size:1.8em;font-weight:800;margin-left:5px">{r['ask']:.0f}¢</span>
                    </div>
                </div>
                <div style="display:flex;justify-content:space-between;align-items:center;margin-top:15px;flex-wrap:wrap;gap:10px">
                    <div>
                        <span style="color:#9ca3af">NWS Forecast:</span>
                        <span style="color:#fbbf24;font-weight:700;margin-left:5px">{r['forecast_low']}°F</span>
                        <span style="color:#6b7280;margin-left:8px;font-size:0.85em">{r.get('desc', '')}</span>
                    </div>
                    <div>
                        <span style="color:#9ca3af">Winner:</span>
                        <span style="color:#22c55e;font-weight:700;margin-left:5px">{r['bracket']}</span>
                        <span style="margin-left:8px">{safety}</span>
                    </div>
                </div>
                <div style="margin-top:15px;padding:10px;background:#161b22;border-radius:8px;text-align:center">
                    <span style="color:#9ca3af">Potential profit:</span>
                    <span style="color:#22c55e;font-weight:700;margin-left:5px">+{potential:.0f}¢</span>
                    <span style="color:#6b7280;margin-left:10px">|</span>
                    <span style="color:#9ca3af;margin-left:10px">Sell at 35-40¢ = </span>
                    <span style="color:#fbbf24;font-weight:700">+{35 - r['ask']:.0f}¢ to +{40 - r['ask']:.0f}¢</span>
                </div>
                <a href="{r['url']}" target="_blank" style="text-decoration:none;display:block;margin-top:15px">
                    <div style="background:linear-gradient(135deg,#3b82f6,#2563eb);padding:12px 20px;border-radius:8px;text-align:center;cursor:pointer">
                        <span style="color:#fff;font-weight:800;font-size:1.1em">🛒 BUY TOMORROW'S {r['bracket']} → {r['ask']:.0f}¢</span>
                    </div>
                </a>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No cheap entries found (all brackets > 40¢). Check back later or prices may already be efficient.")
    
    st.markdown("### 📋 ALL CITIES - TOMORROW")
    for r in tomorrow_results:
        if r["status"] == "❌ NO FORECAST":
            st.markdown(f"<div style='background:#1a1a2e;border:1px solid #30363d;border-radius:8px;padding:10px;margin:5px 0'><span style='color:#ef4444'>{r['city']}</span><span style='color:#6b7280;margin-left:10px'>— No NWS forecast</span></div>", unsafe_allow_html=True)
        elif r["status"] == "⚠️ NO MARKET":
            st.markdown(f"<div style='background:#1a1a2e;border:1px solid #30363d;border-radius:8px;padding:10px;margin:5px 0'><span style='color:#f59e0b'>{r['city']}</span><span style='color:#6b7280;margin-left:10px'>— Forecast: {r['forecast_low']}°F — Market not open yet</span></div>", unsafe_allow_html=True)
        elif r["status"] == "⚠️ NO BRACKET":
            st.markdown(f"<div style='background:#1a1a2e;border:1px solid #30363d;border-radius:8px;padding:10px;margin:5px 0'><span style='color:#f59e0b'>{r['city']}</span><span style='color:#6b7280;margin-left:10px'>— Forecast: {r['forecast_low']}°F — No matching bracket</span></div>", unsafe_allow_html=True)
        else:
            ask_color = "#22c55e" if r["ask"] < 30 else "#3b82f6" if r["ask"] < 40 else "#f59e0b" if r["ask"] < 50 else "#9ca3af"
            st.markdown(f"<div style='background:#0d1117;border:1px solid #30363d;border-radius:8px;padding:10px;margin:5px 0;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:10px'><div><span style='color:#fff;font-weight:600'>{r['city']}</span></div><div><span style='color:#fbbf24'>NWS: {r['forecast_low']}°F</span><span style='color:#6b7280;margin:0 8px'>→</span><span style='color:#22c55e'>{r['bracket']}</span><span style='color:#6b7280;margin:0 5px'>|</span><span style='color:#9ca3af'>Ask:</span><span style='color:{ask_color};margin-left:3px;font-weight:700'>{r['ask']:.0f}¢</span></div></div>", unsafe_allow_html=True)

# ============================================================
# CITY VIEW (DEFAULT)
# ============================================================
else:
    c1, c2 = st.columns([4, 1])
    with c1:
        city = st.selectbox("📍 Select City", CITY_LIST, index=CITY_LIST.index(default_city))
    with c2:
        cfg = CITY_CONFIG.get(city, {})
        nws_url = f"https://forecast.weather.gov/MapClick.php?lat={cfg.get('lat', 40.78)}&lon={cfg.get('lon', -73.97)}"
        st.markdown(f"<a href='{nws_url}' target='_blank' style='display:block;background:#3b82f6;color:#fff;padding:8px;border-radius:6px;text-align:center;text-decoration:none;font-weight:500;margin-top:25px'>📡 NWS</a>", unsafe_allow_html=True)

    cfg = CITY_CONFIG.get(city, {})

    if st.button("⭐ Set as Default City", use_container_width=False):
        st.query_params["city"] = city
        st.success(f"✓ Bookmark this page to save {city} as default!")

    current_temp, obs_low, obs_high, readings, confirm_time, oldest_time, newest_time = fetch_nws_observations(cfg.get("station", "KNYC"), cfg.get("tz", "US/Eastern"))
    extremes_6hr = fetch_nws_6hr_extremes(cfg.get("station", "KNYC"), cfg.get("tz", "US/Eastern")) if is_owner else {}

    if is_owner and obs_low and current_temp:
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
        if hour >= 6 and confirm_time:
            lock_status, lock_color, box_bg = "✅ LOCKED IN", "#22c55e", "linear-gradient(135deg,#1a2e1a,#0d1117)"
        elif hour >= 6:
            lock_status, lock_color, box_bg = "⏳ LIKELY LOCKED", "#3b82f6", "linear-gradient(135deg,#1a1a2e,#0d1117)"
        else:
            lock_status, lock_color, box_bg = "⏳ MAY STILL DROP", "#f59e0b", "linear-gradient(135deg,#2d1f0a,#0d1117)"
        st.markdown(f"""
        <div style="background:{box_bg};border:3px solid {lock_color};border-radius:16px;padding:30px;margin:20px 0;text-align:center">
            <div style="color:{lock_color};font-size:1.2em;font-weight:700;margin-bottom:10px">{lock_status}</div>
            <div style="color:#6b7280;font-size:0.9em">Today's Low (from available data)</div>
            <div style="color:#fff;font-size:4em;font-weight:800;margin:10px 0">{obs_low}°F</div>
            <div style="color:#9ca3af;font-size:0.9em">{time_ago_text}</div>
            <div style="color:#f59e0b;font-size:0.85em;margin-top:10px">{data_warning}</div>
        </div>
        """, unsafe_allow_html=True)

    if not is_owner and obs_low and current_temp:
        st.markdown(f"""
        <div style="background:linear-gradient(135deg,#1a1a2e,#0d1117);border:3px solid #3b82f6;border-radius:16px;padding:25px;margin:20px 0;text-align:center;box-shadow:0 0 20px rgba(59,130,246,0.3)">
            <div style="color:#6b7280;font-size:1em;margin-bottom:5px">📊 Today's Recorded Low</div>
            <div style="color:#3b82f6;font-size:4.5em;font-weight:800;margin:10px 0;text-shadow:0 0 20px rgba(59,130,246,0.5)">{obs_low}°F</div>
            <div style="color:#9ca3af;font-size:0.9em">From NWS Station: <span style="color:#22c55e;font-weight:600">{cfg.get('station', 'N/A')}</span></div>
        </div>
        """, unsafe_allow_html=True)

    if current_temp:
        st.markdown(f"""
        <div style="background:#161b22;border:1px solid #30363d;border-radius:8px;padding:15px;margin:10px 0">
            <div style="display:flex;justify-content:space-around;text-align:center;flex-wrap:wrap;gap:15px">
                <div><div style="color:#6b7280;font-size:0.8em">CURRENT TEMP</div><div style="color:#fff;font-size:1.8em;font-weight:700">{current_temp}°F</div></div>
                <div><div style="color:#6b7280;font-size:0.8em">TODAY'S HIGH</div><div style="color:#ef4444;font-size:1.8em;font-weight:700">{obs_high}°F</div></div>
            </div>
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
                    time_key = r['time']
                    six_hr = extremes_6hr.get(time_key, {})
                    six_hr_display = ""
                    if six_hr.get('max') is not None:
                        six_hr_display += f"<span style='color:#ef4444'>6hr↑{six_hr['max']:.0f}°</span> "
                    if six_hr.get('min') is not None:
                        six_hr_display += f"<span style='color:#3b82f6'>6hr↓{six_hr['min']:.0f}°</span>"
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
                    st.markdown(f"<div style='{row_style}'><span style='color:#9ca3af;min-width:50px'>{r['time']}</span><span style='flex:1;text-align:center;font-size:0.85em'>{six_hr_display}</span><span style='{temp_style}'>{r['temp']}°F{label}</span></div>", unsafe_allow_html=True)
    else:
        st.warning("⚠️ Could not fetch NWS observations")

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

st.markdown("---")
st.markdown('<div style="background:linear-gradient(90deg,#d97706,#f59e0b);padding:10px 15px;border-radius:8px;margin-bottom:20px;text-align:center"><b style="color:#000">🧪 FREE TOOL</b> <span style="color:#000">— LOW Temperature Edge Finder v6.0</span></div>', unsafe_allow_html=True)
st.markdown('<div style="color:#6b7280;font-size:0.75em;text-align:center;margin-top:30px">⚠️ For entertainment purposes only. Not financial advice. Verify on Kalshi before trading.</div>', unsafe_allow_html=True)
