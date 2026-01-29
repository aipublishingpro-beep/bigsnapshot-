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
    "Austin": {"high": "KXHIGHAUS", "low": "KXLOWTAUS", "station": "KAUS", "lat": 30.19, "lon": -97.67, "tz": "US/Central"},
    "Chicago": {"high": "KXHIGHCHI", "low": "KXLOWTCHI", "station": "KMDW", "lat": 41.79, "lon": -87.75, "tz": "US/Central"},
    "Denver": {"high": "KXHIGHDEN", "low": "KXLOWTDEN", "station": "KDEN", "lat": 39.86, "lon": -104.67, "tz": "US/Mountain"},
    "Los Angeles": {"high": "KXHIGHLAX", "low": "KXLOWTLAX", "station": "KLAX", "lat": 33.94, "lon": -118.41, "tz": "US/Pacific"},
    "Miami": {"high": "KXHIGHMIA", "low": "KXLOWTMIA", "station": "KMIA", "lat": 25.80, "lon": -80.29, "tz": "US/Eastern"},
    "New York City": {"high": "KXHIGHNY", "low": "KXLOWTNYC", "station": "KNYC", "lat": 40.78, "lon": -73.97, "tz": "US/Eastern"},
    "Philadelphia": {"high": "KXHIGHPHL", "low": "KXLOWTPHL", "station": "KPHL", "lat": 39.87, "lon": -75.23, "tz": "US/Eastern"},
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
# HELPER: FORMAT TIME AGO (FIXED!)
# ============================================================
def format_time_ago(mins):
    """Convert minutes to human-readable format"""
    if mins is None:
        return None
    if mins < 60:
        return f"{mins}m"
    hours = mins // 60
    remaining_mins = mins % 60
    if remaining_mins == 0:
        return f"{hours}h"
    return f"{hours}h {remaining_mins}m"

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

@st.cache_data(ttl=60)
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

@st.cache_data(ttl=60)
def fetch_nws_observations(station, city_tz_str):
    url = f"https://api.weather.gov/stations/{station}/observations?limit=500"
    try:
        city_tz = pytz.timezone(city_tz_str)
        resp = requests.get(url, headers={"User-Agent": "TempEdge/3.0", "Cache-Control": "no-cache"}, timeout=15)
        if resp.status_code != 200:
            return None, None, None, [], None, None, None, None
        observations = resp.json().get("features", [])
        if not observations:
            return None, None, None, [], None, None, None, None
        
        now_local = datetime.now(city_tz)
        today_midnight = now_local.replace(hour=0, minute=0, second=0, microsecond=0)
        
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
                if ts_local >= today_midnight and ts_local <= now_local:
                    temp_f = round(temp_c * 9/5 + 32, 1)
                    readings.append({"time": ts_local, "temp": temp_f})
            except:
                continue
        if not readings:
            return None, None, None, [], None, None, None, None
        readings.sort(key=lambda x: x["time"], reverse=True)
        current = readings[0]["temp"]
        low = min(r["temp"] for r in readings)
        high = max(r["temp"] for r in readings)
        readings_chrono = sorted(readings, key=lambda x: x["time"])
        confirm_time = None
        mins_since_confirm = None
        low_found = False
        for r in readings_chrono:
            if r["temp"] == low:
                low_found = True
            elif low_found and r["temp"] > low:
                confirm_time = r["time"]
                mins_since_confirm = int((datetime.now(city_tz) - confirm_time).total_seconds() / 60)
                break
        oldest_time = readings_chrono[0]["time"] if readings_chrono else None
        newest_time = readings_chrono[-1]["time"] if readings_chrono else None
        display_readings = [{"time": r["time"].strftime("%H:%M"), "temp": r["temp"]} for r in readings]
        return current, low, high, display_readings, confirm_time, oldest_time, newest_time, mins_since_confirm
    except:
        return None, None, None, [], None, None, None, None

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
                        short_forecast = p.get("shortForecast", "")
                        return temp, short_forecast
                except:
                    continue
        return None, None
    except:
        return None, None

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
                kalshi_url = f"https://kalshi.com/markets/{series_ticker.lower()}" if series_ticker else f"https://kalshi.com/markets/{m.get('event_ticker', '')}"
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

# ============================================================
# SIDEBAR LEGENDS
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
                <span style="color:#6b7280;font-size:0.85em;margin-left:12px">Midnight LOWs</span><br>
                <b>☀️ 7-8 AM</b> → Austin, Miami, NYC, Philly<br>
                <span style="color:#6b7280;font-size:0.85em;margin-left:12px">Sunrise LOWs</span><br>
                <b>☀️ 9-10 AM</b> → Los Angeles<br>
                <span style="color:#6b7280;font-size:0.85em;margin-left:12px">West coast</span>
            </div>
        </div>
        <div style="background:#1a2e1a;border:2px solid #22c55e;border-radius:8px;padding:12px;margin-bottom:15px">
            <div style="color:#22c55e;font-weight:700;margin-bottom:8px">🎨 ROW COLORS</div>
            <div style="color:#c9d1d9;font-size:0.8em;line-height:1.6">
                <span style="color:#22c55e">🟢 GREEN</span> = LOCKED + Confirmed<br>
                <span style="color:#f59e0b">🟡 AMBER</span> = Waiting / Pre-peak<br>
                <span style="color:#6b7280">⬛ GRAY</span> = No data
            </div>
        </div>
        <div style="background:#1a1a2e;border:1px solid #22c55e;border-radius:8px;padding:12px;margin-bottom:15px">
            <div style="color:#22c55e;font-weight:700;margin-bottom:8px">💰 ENTRY THRESHOLDS</div>
            <div style="color:#c9d1d9;font-size:0.8em;line-height:1.6">
                <b>🔥 &lt;85¢</b> = JUMP IN (+15¢)<br>
                <b>✅ 85-90¢</b> = Good (+10-15¢)<br>
                <b>⚠️ 90-95¢</b> = Small edge<br>
                <b>❌ 95¢+</b> = Skip it
            </div>
        </div>
        """, unsafe_allow_html=True)
else:
    with st.sidebar:
        st.markdown("""
        <div style="background:#1a1a2e;border:1px solid #3b82f6;border-radius:8px;padding:12px;margin-bottom:15px">
            <div style="color:#3b82f6;font-weight:700;margin-bottom:8px">⏰ LOW LOCK-IN TIMES (ET)</div>
            <div style="color:#c9d1d9;font-size:0.8em;line-height:1.6">
                <b>🌙 MIDNIGHT:</b> Chicago ~1:15 AM, Denver ~2:40 AM<br>
                <b>☀️ SUNRISE:</b> Austin/Miami ~7:40 AM, NYC ~7:51 AM, Philly ~7:54 AM, LA ~9:00 AM
            </div>
        </div>
        """, unsafe_allow_html=True)

# ============================================================
# HEADER
# ============================================================
st.title("🌡️ LOW TEMP EDGE FINDER")
st.caption(f"Live NWS Observations + Kalshi | {now.strftime('%b %d, %Y %I:%M %p ET')}")

if is_owner:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
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
    st.subheader("🔍 All Cities Scanner")
    
    if st.button("🔄 Refresh Scan", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    
    results = []
    with st.spinner("Scanning all 7 cities..."):
        for city_name, cfg in CITY_CONFIG.items():
            current_temp, obs_low, obs_high, readings, confirm_time, oldest_time, newest_time, mins_since_confirm = fetch_nws_observations(cfg["station"], cfg["tz"])
            brackets = fetch_kalshi_brackets(cfg["low"])
            
            if obs_low is None:
                results.append({"city": city_name, "status": "❌ NO DATA", "obs_low": None, "bracket": None, "bid": 0, "ask": 100, "edge": 0, "url": None, "locked": False, "confirm_time": None, "mins_since_confirm": None})
                continue
            
            winning = find_winning_bracket(obs_low, brackets)
            is_locked = check_low_locked(cfg["tz"])
            
            if winning:
                bid = winning["bid"]
                ask = winning["ask"]
                edge = (100 - ask) if is_locked and ask < 95 else 0
                if ask < 85:
                    rating = "🔥"
                elif ask < 90:
                    rating = "✅"
                elif ask < 95:
                    rating = "⚠️"
                else:
                    rating = "❌"
                results.append({"city": city_name, "status": "✅", "obs_low": obs_low, "bracket": winning["name"], "bid": bid, "ask": ask, "edge": edge, "rating": rating, "url": winning["url"], "locked": is_locked, "confirm_time": confirm_time, "mins_since_confirm": mins_since_confirm})
            else:
                results.append({"city": city_name, "status": "⚠️ NO BRACKET", "obs_low": obs_low, "bracket": None, "bid": 0, "ask": 100, "edge": 0, "url": None, "locked": is_locked, "confirm_time": confirm_time, "mins_since_confirm": mins_since_confirm})
    
    results_with_edge = sorted([r for r in results if r.get("edge") and r["edge"] >= 10], key=lambda x: x["edge"], reverse=True)
    
    st.markdown("### 🔥 OPPORTUNITIES")
    if results_with_edge:
        for r in results_with_edge:
            lock_icon = "🔒" if r["locked"] else "⏳"
            time_ago_str = format_time_ago(r.get('mins_since_confirm'))
            confirm_text = f"✅ {time_ago_str} ago" if time_ago_str else "⏳ Awaiting..."
            rating_color = "#22c55e" if r["rating"] == "🔥" else "#3b82f6" if r["rating"] == "✅" else "#f59e0b"
            st.markdown(f"""
            <div style="background:linear-gradient(135deg,#1a2e1a,#0d1117);border:2px solid {rating_color};border-radius:12px;padding:20px;margin:10px 0">
                <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:10px">
                    <div>
                        <span style="color:{rating_color};font-size:1.5em;font-weight:700">{r['rating']} {r['city']}</span>
                        <span style="color:#6b7280;margin-left:10px">{lock_icon}</span>
                        <span style="color:#22c55e;margin-left:10px">{confirm_text}</span>
                    </div>
                    <div style="text-align:right">
                        <div style="color:#fbbf24;font-size:1.8em;font-weight:800">+{r['edge']:.0f}¢ EDGE</div>
                    </div>
                </div>
                <div style="display:flex;justify-content:space-between;align-items:center;margin-top:15px;flex-wrap:wrap;gap:10px">
                    <div><span style="color:#9ca3af">Low:</span><span style="color:#3b82f6;font-weight:700;margin-left:5px">{r['obs_low']}°F</span></div>
                    <div><span style="color:#9ca3af">Winner:</span><span style="color:#fbbf24;font-weight:700;margin-left:5px">{r['bracket']}</span></div>
                </div>
                <div style="display:flex;justify-content:center;gap:20px;margin-top:15px;padding:10px;background:#161b22;border-radius:8px">
                    <div style="text-align:center"><div style="color:#6b7280;font-size:0.75em">BID</div><div style="color:#22c55e;font-size:1.2em;font-weight:700">{r['bid']:.0f}¢</div></div>
                    <div style="text-align:center"><div style="color:#6b7280;font-size:0.75em">ASK</div><div style="color:#ef4444;font-size:1.2em;font-weight:700">{r['ask']:.0f}¢</div></div>
                    <div style="text-align:center"><div style="color:#6b7280;font-size:0.75em">SPREAD</div><div style="color:#fbbf24;font-size:1.2em;font-weight:700">{r['ask'] - r['bid']:.0f}¢</div></div>
                </div>
                <a href="{r['url']}" target="_blank" style="text-decoration:none;display:block;margin-top:15px">
                    <div style="background:linear-gradient(135deg,#22c55e,#16a34a);padding:12px 20px;border-radius:8px;text-align:center;cursor:pointer">
                        <span style="color:#000;font-weight:800;font-size:1.1em">🛒 BUY YES → {r['bracket']}</span>
                    </div>
                </a>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No opportunities with 10¢+ edge found.")
    
    st.markdown("### 📊 ALL CITIES")
    for r in results:
        if r["status"] == "❌ NO DATA":
            st.markdown(f"<div style='background:#1a1a2e;border:1px solid #30363d;border-radius:8px;padding:12px;margin:5px 0'><span style='color:#ef4444'>{r['city']}</span><span style='color:#6b7280;margin-left:10px'>— No NWS data</span></div>", unsafe_allow_html=True)
        elif r["status"] == "⚠️ NO BRACKET":
            lock_icon = "🔒" if r["locked"] else "⏳"
            row_bg = "#1a2e1a" if r["locked"] and r.get("confirm_time") else "#2d1f0a" if not r["locked"] else "#1a1a2e"
            row_border = "#22c55e" if r["locked"] and r.get("confirm_time") else "#f59e0b" if not r["locked"] else "#30363d"
            time_ago_str = format_time_ago(r.get('mins_since_confirm'))
            confirm_display = f"<span style='color:#22c55e;font-weight:700'>✅ {time_ago_str}</span>" if time_ago_str else ""
            st.markdown(f"<div style='background:{row_bg};border:2px solid {row_border};border-radius:8px;padding:12px;margin:5px 0'><span style='color:#f59e0b'>{r['city']}</span><span style='color:#6b7280;margin-left:8px'>{lock_icon}</span><span style='margin-left:8px'>{confirm_display}</span><span style='color:#6b7280;margin-left:10px'>— Low: {r['obs_low']}°F — No bracket</span></div>", unsafe_allow_html=True)
        else:
            lock_icon = "🔒" if r["locked"] else "⏳"
            row_bg = "#1a2e1a" if r["locked"] and r.get("confirm_time") else "#2d1f0a" if not r["locked"] else "#0d1117"
            row_border = "#22c55e" if r["locked"] and r.get("confirm_time") else "#f59e0b" if not r["locked"] else "#30363d"
            edge_display = f"<span style='color:#22c55e;font-weight:700'>{r.get('rating','')} +{r['edge']:.0f}¢</span>" if r.get("edge") and r["edge"] >= 10 else "<span style='color:#6b7280'>—</span>"
            ask_color = "#22c55e" if r["ask"] < 85 else "#3b82f6" if r["ask"] < 90 else "#f59e0b" if r["ask"] < 95 else "#9ca3af"
            time_ago_str = format_time_ago(r.get('mins_since_confirm'))
            confirm_display = f"<span style='color:#22c55e;font-weight:700'>✅ {time_ago_str}</span>" if time_ago_str else "<span style='color:#f59e0b'>⏳</span>" if r["locked"] else ""
            st.markdown(f"<div style='background:{row_bg};border:2px solid {row_border};border-radius:8px;padding:12px;margin:5px 0;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:10px'><div><span style='color:#fff;font-weight:600'>{r['city']}</span><span style='color:#6b7280;margin-left:8px'>{lock_icon}</span><span style='margin-left:8px'>{confirm_display}</span></div><div><span style='color:#3b82f6'>{r['obs_low']}°F</span><span style='color:#6b7280;margin:0 8px'>→</span><span style='color:#fbbf24'>{r['bracket']}</span><span style='color:#6b7280;margin:0 5px'>|</span><span style='color:#9ca3af'>Bid:</span><span style='color:#22c55e;margin:0 3px'>{r['bid']:.0f}¢</span><span style='color:#9ca3af'>Ask:</span><span style='color:{ask_color};margin:0 3px'>{r['ask']:.0f}¢</span><span style='color:#6b7280;margin:0 5px'>|</span>{edge_display}</div></div>", unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown(f"<div style='text-align:center;color:#6b7280;font-size:0.8em'>Last scan: {now.strftime('%I:%M %p ET')} | 🟢 = LOCKED + Confirmed | 🟡 = Waiting</div>", unsafe_allow_html=True)

    # TOMORROW'S LOW SECTION
    st.markdown("---")
    tomorrow_date = (datetime.now(eastern) + timedelta(days=1)).strftime('%A, %b %d')
    st.subheader(f"🔮 TOMORROW'S LOW ({tomorrow_date})")
    
    tomorrow_results = []
    with st.spinner("Scanning tomorrow's markets..."):
        for city_name, cfg in CITY_CONFIG.items():
            forecast_low, forecast_desc = fetch_nws_tomorrow_low(cfg["lat"], cfg["lon"])
            brackets = fetch_kalshi_tomorrow_brackets(cfg["low"])
            if forecast_low is None:
                tomorrow_results.append({"city": city_name, "status": "❌", "forecast_low": None, "bracket": None, "ask": None, "url": None})
                continue
            if not brackets:
                tomorrow_results.append({"city": city_name, "status": "⚠️", "forecast_low": forecast_low, "bracket": None, "ask": None, "url": None})
                continue
            winning = find_winning_bracket(forecast_low, brackets)
            if winning:
                tomorrow_results.append({"city": city_name, "status": "✅", "forecast_low": forecast_low, "bracket": winning["name"], "bid": winning["bid"], "ask": winning["ask"], "url": winning["url"]})
            else:
                tomorrow_results.append({"city": city_name, "status": "⚠️", "forecast_low": forecast_low, "bracket": None, "ask": None, "url": None})
    
    cheap_opps = [r for r in tomorrow_results if r.get("ask") and r["ask"] < 40]
    cheap_opps.sort(key=lambda x: x["ask"])
    
    if cheap_opps:
        st.markdown("### 💰 CHEAP ENTRIES (Ask < 40¢)")
        for r in cheap_opps:
            potential = 100 - r["ask"]
            st.markdown(f"""
            <div style="background:linear-gradient(135deg,#1a1a2e,#0d1117);border:2px solid #3b82f6;border-radius:12px;padding:20px;margin:10px 0">
                <div style="display:flex;justify-content:space-between;align-items:center">
                    <span style="color:#3b82f6;font-size:1.4em;font-weight:700">{r['city']}</span>
                    <span style="color:#22c55e;font-size:1.8em;font-weight:800">{r['ask']:.0f}¢</span>
                </div>
                <div style="margin-top:10px"><span style="color:#9ca3af">NWS:</span><span style="color:#fbbf24;font-weight:700;margin-left:5px">{r['forecast_low']}°F</span><span style="color:#6b7280;margin:0 10px">→</span><span style="color:#22c55e;font-weight:700">{r['bracket']}</span></div>
                <div style="margin-top:10px;color:#9ca3af">Potential: <span style="color:#22c55e;font-weight:700">+{potential:.0f}¢</span></div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No cheap entries (all > 40¢)")
    
    st.markdown("### 📋 ALL CITIES - TOMORROW")
    for r in tomorrow_results:
        if r["status"] == "❌":
            st.markdown(f"<div style='background:#1a1a2e;border:1px solid #30363d;border-radius:8px;padding:10px;margin:5px 0'><span style='color:#ef4444'>{r['city']}</span><span style='color:#6b7280;margin-left:10px'>— No forecast</span></div>", unsafe_allow_html=True)
        elif r["status"] == "⚠️":
            st.markdown(f"<div style='background:#1a1a2e;border:1px solid #30363d;border-radius:8px;padding:10px;margin:5px 0'><span style='color:#f59e0b'>{r['city']}</span><span style='color:#6b7280;margin-left:10px'>— {r.get('forecast_low', '?')}°F — No bracket</span></div>", unsafe_allow_html=True)
        else:
            ask_color = "#22c55e" if r["ask"] < 30 else "#3b82f6" if r["ask"] < 40 else "#f59e0b" if r["ask"] < 50 else "#9ca3af"
            st.markdown(f"<div style='background:#0d1117;border:1px solid #30363d;border-radius:8px;padding:10px;margin:5px 0;display:flex;justify-content:space-between;align-items:center'><span style='color:#fff;font-weight:600'>{r['city']}</span><div><span style='color:#fbbf24'>{r['forecast_low']}°F</span><span style='color:#6b7280;margin:0 8px'>→</span><span style='color:#22c55e'>{r['bracket']}</span><span style='color:#6b7280;margin:0 5px'>|</span><span style='color:{ask_color};font-weight:700'>{r['ask']:.0f}¢</span></div></div>", unsafe_allow_html=True)

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
        st.success(f"✓ Bookmark to save {city} as default!")

    current_temp, obs_low, obs_high, readings, confirm_time, oldest_time, newest_time, mins_since_confirm = fetch_nws_observations(cfg.get("station", "KNYC"), cfg.get("tz", "US/Eastern"))
    extremes_6hr = fetch_nws_6hr_extremes(cfg.get("station", "KNYC"), cfg.get("tz", "US/Eastern")) if is_owner else {}

    if is_owner and obs_low and current_temp:
        city_tz = pytz.timezone(cfg.get("tz", "US/Eastern"))
        hour = datetime.now(city_tz).hour
        time_ago_str = format_time_ago(mins_since_confirm)
        if time_ago_str:
            time_ago_text = f"✅ Confirmed {time_ago_str} ago"
        else:
            time_ago_text = "⏳ Awaiting rise after low..."
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
            <div style="color:#6b7280;font-size:0.9em">Today's Low</div>
            <div style="color:#fff;font-size:4em;font-weight:800;margin:10px 0">{obs_low}°F</div>
            <div style="color:#9ca3af;font-size:0.9em">{time_ago_text}</div>
            <div style="color:#f59e0b;font-size:0.85em;margin-top:10px">{data_warning}</div>
        </div>
        """, unsafe_allow_html=True)

    if not is_owner and obs_low and current_temp:
        st.markdown(f"""
        <div style="background:linear-gradient(135deg,#1a1a2e,#0d1117);border:3px solid #3b82f6;border-radius:16px;padding:25px;margin:20px 0;text-align:center">
            <div style="color:#6b7280;font-size:1em;margin-bottom:5px">📊 Today's Recorded Low</div>
            <div style="color:#3b82f6;font-size:4.5em;font-weight:800;margin:10px 0">{obs_low}°F</div>
            <div style="color:#9ca3af;font-size:0.9em">From NWS Station: <span style="color:#22c55e;font-weight:600">{cfg.get('station', 'N/A')}</span></div>
        </div>
        """, unsafe_allow_html=True)

    if current_temp:
        st.markdown(f"""
        <div style="background:#161b22;border:1px solid #30363d;border-radius:8px;padding:15px;margin:10px 0">
            <div style="display:flex;justify-content:space-around;text-align:center">
                <div><div style="color:#6b7280;font-size:0.8em">CURRENT</div><div style="color:#fff;font-size:1.8em;font-weight:700">{current_temp}°F</div></div>
                <div><div style="color:#6b7280;font-size:0.8em">HIGH</div><div style="color:#ef4444;font-size:1.8em;font-weight:700">{obs_high}°F</div></div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if readings:
            with st.expander("📊 Recent NWS Observations", expanded=True):
                if oldest_time and newest_time:
                    st.markdown(f"<div style='color:#6b7280;font-size:0.8em;margin-bottom:10px;text-align:center'>📅 Data: {oldest_time.strftime('%H:%M')} to {newest_time.strftime('%H:%M')} local | {len(readings)} readings</div>", unsafe_allow_html=True)
                display_list = readings if is_owner else readings[:12]
                low_idx = next((i for i, r in enumerate(display_list) if r['temp'] == obs_low), None)
                confirm_idx = low_idx if (low_idx is not None and low_idx > 0 and confirm_time) else None
                for i, r in enumerate(display_list):
                    time_key = r['time']
                    six_hr = extremes_6hr.get(time_key, {})
                    six_hr_display = ""
                    if six_hr.get('max') is not None:
                        six_hr_display += f"<span style='color:#ef4444'>6hr↑{six_hr['max']:.0f}°</span> "
                    if six_hr.get('min') is not None:
                        six_hr_display += f"<span style='color:#3b82f6'>6hr↓{six_hr['min']:.0f}°</span>"
                    if is_owner and confirm_idx is not None and i == confirm_idx:
                        confirm_time_ago = format_time_ago(mins_since_confirm)
                        confirm_mins_text = f" — {confirm_time_ago} ago" if confirm_time_ago else ""
                        st.markdown(f'<div style="display:flex;justify-content:center;padding:8px;border-radius:4px;background:#166534;border:2px solid #22c55e;margin:4px 0"><span style="color:#4ade80;font-weight:700">✅ CONFIRMED LOW{confirm_mins_text}</span></div>', unsafe_allow_html=True)
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
st.markdown('<div style="background:linear-gradient(90deg,#d97706,#f59e0b);padding:10px 15px;border-radius:8px;margin-bottom:20px;text-align:center"><b style="color:#000">🧪 FREE TOOL</b> <span style="color:#000">— LOW Temperature Edge Finder v6.3</span></div>', unsafe_allow_html=True)
st.markdown('<div style="color:#6b7280;font-size:0.75em;text-align:center;margin-top:30px">⚠️ For entertainment only. Not financial advice.</div>', unsafe_allow_html=True)
