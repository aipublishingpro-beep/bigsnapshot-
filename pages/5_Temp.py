import streamlit as st
import requests
from datetime import datetime, timedelta
import pytz
import re
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
    "Los Angeles": {"high": "KXHIGHLAX", "low": "KXLOWTLAX", "station": "KLAX", "lat": 33.94, "lon": -118.41, "tz": "US/Pacific"},
    "Miami": {"high": "KXHIGHMIA", "low": "KXLOWTMIA", "station": "KMIA", "lat": 25.80, "lon": -80.29, "tz": "US/Eastern"},
    "New York City": {"high": "KXHIGHNY", "low": "KXLOWTNYC", "station": "KNYC", "lat": 40.78, "lon": -73.97, "tz": "US/Eastern"},
    "Philadelphia": {"high": "KXHIGHPHL", "low": "KXLOWTPHL", "station": "KPHL", "lat": 39.87, "lon": -75.23, "tz": "US/Eastern"},
}
CITY_LIST = sorted(CITY_CONFIG.keys())

CHECK_TIMES_ET = {
    "Austin": "7-8 AM ET",
    "Los Angeles": "9-10 AM ET",
    "Miami": "7-8 AM ET",
    "New York City": "7-8 AM ET",
    "Philadelphia": "7-8 AM ET",
}

query_params = st.query_params
default_city = query_params.get("city", "New York City")
if default_city not in CITY_LIST:
    default_city = "New York City"
is_owner = query_params.get("mode") == "owner"

if "view_mode" not in st.session_state:
    st.session_state.view_mode = "city"

def format_time_ago(mins):
    if mins is None:
        return None
    if mins < 60:
        return f"{mins}m"
    hours = mins // 60
    remaining_mins = mins % 60
    if remaining_mins == 0:
        return f"{hours}h"
    return f"{hours}h {remaining_mins}m"

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

def get_settlement_from_6hr(extremes_6hr, market_type="low"):
    if not extremes_6hr:
        return None, None
    if market_type == "low":
        mins = [(time_key, v["min"]) for time_key, v in extremes_6hr.items() if v.get("min") is not None]
        if mins:
            mins.sort(key=lambda x: x[1])
            return int(mins[0][1]), mins[0][0]
    else:
        maxs = [(time_key, v["max"]) for time_key, v in extremes_6hr.items() if v.get("max") is not None]
        if maxs:
            maxs.sort(key=lambda x: x[1], reverse=True)
            return int(maxs[0][1]), maxs[0][0]
    return None, None

def check_low_locked_6hr(extremes_6hr, city_tz_str):
    if not extremes_6hr:
        return False, None
    for time_key, values in extremes_6hr.items():
        if values.get("min") is not None:
            try:
                hour = int(time_key.split(":")[0])
                if hour >= 6:
                    return True, time_key
            except:
                continue
    return False, None

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

@st.cache_data(ttl=300)
def check_forecast_anomalies(lat, lon):
    """Check NWS forecast for weather anomalies. Returns (is_anomaly, matched_words, max_wind_speed, forecast_low_temp)"""
    danger_words = [
        'freeze', 'frost', 'freezing', 'ice', 'icy', 'snow', 'sleet', 
        'extreme', 'severe', 'advisory', 'warning', 'watch', 'blizzard',
        'wind chill', 'arctic', 'polar', 'storm', 'cold front', 'warm front'
    ]
    
    try:
        periods = fetch_nws_forecast(lat, lon)
        if not periods:
            return False, [], None, None
        
        matched_words = []
        max_wind_speed = 0
        forecast_low_temp = None
        
        for period in periods[:4]:
            text = period.get('shortForecast', '').lower() + ' ' + period.get('detailedForecast', '').lower()
            
            for word in danger_words:
                if word in text and word not in matched_words:
                    matched_words.append(word)
            
            wind_speed = period.get('windSpeed', '')
            if wind_speed:
                numbers = re.findall(r'(\d+)', str(wind_speed))
                if numbers:
                    speed = max([int(n) for n in numbers])
                    max_wind_speed = max(max_wind_speed, speed)
            
            if forecast_low_temp is None and not period.get('isDaytime', True):
                forecast_low_temp = period.get('temperature')
        
        is_anomaly = len(matched_words) > 0 or max_wind_speed > 25
        
        return is_anomaly, matched_words, max_wind_speed if max_wind_speed > 0 else None, forecast_low_temp
        
    except:
        return False, [], None, None

@st.cache_data(ttl=60)
def fetch_kalshi_tomorrow_brackets(series_ticker, city_tz_str="US/Eastern"):
    url = f"https://api.elections.kalshi.com/trade-api/v2/markets?series_ticker={series_ticker}&status=open"
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code != 200:
            return []
        markets = resp.json().get("markets", [])
        if not markets:
            return []
        city_tz = pytz.timezone(city_tz_str)
        tomorrow = datetime.now(city_tz) + timedelta(days=1)
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
def fetch_kalshi_brackets(series_ticker, city_tz_str="US/Eastern"):
    url = f"https://api.elections.kalshi.com/trade-api/v2/markets?series_ticker={series_ticker}&status=open"
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code != 200:
            return []
        markets = resp.json().get("markets", [])
        if not markets:
            return []
        city_tz = pytz.timezone(city_tz_str)
        today_str = datetime.now(city_tz).strftime('%y%b%d').upper()
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

def find_winning_bracket(settlement_temp, brackets):
    if settlement_temp is None:
        return None
    for b in brackets:
        if b['high'] == 999 and settlement_temp >= b['low']:
            return b
        if b['low'] == -999 and settlement_temp < b['high']:
            return b
        if b['low'] <= settlement_temp <= b['high']:
            return b
        if b['low'] < settlement_temp <= b['high']:
            return b
    return None

if is_owner:
    with st.sidebar:
        st.markdown("""
        <div style="background:#1a2e1a;border:1px solid #22c55e;border-radius:8px;padding:12px;margin-bottom:15px">
            <div style="color:#22c55e;font-weight:700;margin-bottom:8px">🔒 SETTLEMENT RULES</div>
            <div style="color:#c9d1d9;font-size:0.85em;line-height:1.5">
                <b>LOW:</b> LOWEST 6hr↓ after midnight<br>
                <b>HIGH:</b> HIGHEST 6hr↑ after midnight<br><br>
                <b>Lock Times (local):</b><br>
                • LOW locks @ 06:53 (6hr Min)<br>
                • HIGH locks @ 18:53 (6hr Max)<br><br>
                <span style="color:#f59e0b">⚠️ Hourly temps ≠ settlement!</span>
            </div>
        </div>
        <div style="background:#2d1f0a;border:1px solid #f59e0b;border-radius:8px;padding:12px;margin-bottom:15px">
            <div style="color:#f59e0b;font-weight:700;margin-bottom:8px">🗽 YOUR TRADING SCHEDULE (ET)</div>
            <div style="color:#c9d1d9;font-size:0.8em;line-height:1.6">
                <b>☀️ 7-8 AM</b> → Austin, Miami, NYC, Philly<br>
                <span style="color:#6b7280;font-size:0.85em;margin-left:12px">Sunrise LOWs</span><br>
                <b>☀️ 9-10 AM</b> → Los Angeles<br>
                <span style="color:#6b7280;font-size:0.85em;margin-left:12px">West coast</span>
            </div>
        </div>
        <div style="background:#1a2e1a;border:2px solid #22c55e;border-radius:8px;padding:12px;margin-bottom:15px">
            <div style="color:#22c55e;font-weight:700;margin-bottom:8px">🎨 ROW COLORS</div>
            <div style="color:#c9d1d9;font-size:0.8em;line-height:1.6">
                <span style="color:#22c55e">🟢 GREEN</span> = 6hr LOCKED<br>
                <span style="color:#f59e0b">🟡 AMBER</span> = Waiting for 6hr<br>
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
                <b>☀️ SUNRISE:</b> Austin/Miami ~7:40 AM, NYC ~7:51 AM, Philly ~7:54 AM, LA ~9:00 AM
            </div>
        </div>
        """, unsafe_allow_html=True)

st.title("🌡️ LOW TEMP EDGE FINDER")
st.caption(f"6hr Settlement Data | {now.strftime('%b %d, %Y %I:%M %p ET')}")

def render_hero_box(city_name, cfg):
    city_tz = pytz.timezone(cfg.get("tz", "US/Eastern"))
    city_now = datetime.now(city_tz)
    today_str = city_now.strftime("%A, %B %d, %Y")
    extremes = fetch_nws_6hr_extremes(cfg.get("station", "KNYC"), cfg.get("tz", "US/Eastern"))
    settlement_low, settlement_time = get_settlement_from_6hr(extremes, "low")
    is_locked, lock_time = check_low_locked_6hr(extremes, cfg.get("tz", "US/Eastern"))
    brackets = fetch_kalshi_brackets(cfg.get("low", ""), cfg.get("tz", "US/Eastern"))
    winning = find_winning_bracket(settlement_low, brackets) if settlement_low else None
    ask = winning.get("ask", 0) if winning else 0
    profit = 100 - ask
    bracket_name = winning.get("name", "?") if winning else "?"
    bracket_url = winning.get("url", "#") if winning else "#"
    
    if ask < 85:
        rating = "🔥 GREAT"
        profit_color = "#22c55e"
    elif ask < 90:
        rating = "✅ GOOD"
        profit_color = "#22c55e"
    elif ask < 95:
        rating = "⚠️ SMALL"
        profit_color = "#fbbf24"
    else:
        rating = "😐 MEH"
        profit_color = "#9ca3af"
    
    mins_since_lock = None
    if settlement_time and is_locked:
        try:
            lock_hour = int(settlement_time.split(":")[0])
            lock_min = int(settlement_time.split(":")[1])
            lock_datetime = city_now.replace(hour=lock_hour, minute=lock_min, second=0, microsecond=0)
            if lock_datetime <= city_now:
                mins_since_lock = int((city_now - lock_datetime).total_seconds() / 60)
        except:
            pass
    
    if mins_since_lock is not None:
        if mins_since_lock < 60:
            time_ago_str = f"{mins_since_lock} mins ago"
        else:
            hours = mins_since_lock // 60
            mins = mins_since_lock % 60
            if mins == 0:
                time_ago_str = f"{hours}h ago"
            else:
                time_ago_str = f"{hours}h {mins}m ago"
    else:
        time_ago_str = None
    
    if settlement_low is not None and is_locked:
        lock_info = f"🔒 Locked {time_ago_str}" if time_ago_str else "🔒 Locked"
        
        # CHECK ANOMALY FIRST - ALWAYS - REGARDLESS OF BRACKET MATCH
        anomaly_active, anomaly_words, wind_speed, forecast_temp = check_forecast_anomalies(cfg.get("lat", 40.78), cfg.get("lon", -73.97))
        
        if anomaly_active and forecast_temp is not None:
            temp_gap = settlement_low - forecast_temp
            danger_text = ', '.join(anomaly_words[:2]) if anomaly_words else 'weather event'
            
            if temp_gap > 3 or anomaly_words:
                bracket_display = f"{bracket_name} @ {ask}¢" if winning else "No matching bracket on Kalshi"
                st.markdown(f"""
                <div style="background:linear-gradient(135deg,#2d0a0a,#1a0505);border:4px solid #ef4444;border-radius:20px;padding:40px;margin:20px 0;text-align:center;box-shadow:0 0 30px rgba(239,68,68,0.4)">
                    <div style="color:#ef4444;font-size:2.5em;font-weight:900;margin-bottom:15px">⚠️ LOW LOCKED — ANOMALY WARNING</div>
                    <div style="color:#fca5a5;font-size:1.2em;margin-bottom:5px">{city_name}</div>
                    <div style="color:#fb7185;font-size:1.4em;font-weight:700;margin-bottom:20px">📅 {today_str}</div>
                    
                    <div style="margin:30px 0;padding:30px;background:rgba(0,0,0,0.6);border-radius:15px;border:3px solid #ef4444">
                        <div style="color:#fbbf24;font-size:1.8em;font-weight:900;margin-bottom:20px">⛈️ {danger_text.upper()} WARNING</div>
                        
                        <div style="color:#ef4444;font-size:2.5em;font-weight:900;line-height:1.4;margin:20px 0">
                            NWS Tonight low = {forecast_temp}°F<br>
                            vs Settlement = {settlement_low}°F<br>
                            <span style="color:#fbbf24;font-size:1.3em">— {temp_gap}° GAP!</span>
                        </div>
                        
                        <div style="color:#fca5a5;font-size:1.3em;font-weight:700;margin-top:20px">Danger: {danger_text}</div>
                        <div style="color:#ef4444;font-size:1.5em;font-weight:900;margin-top:15px">DO NOT BUY — CHECK MANUALLY</div>
                    </div>
                    
                    <div style="color:#9ca3af;font-size:1em;margin-top:20px">{lock_info} @ {settlement_time} local</div>
                    <div style="color:#6b7280;font-size:0.9em;margin-top:5px">Winning bracket: {bracket_display}</div>
                    
                    <div style="margin-top:25px;padding:18px;background:#30363d;border-radius:10px;cursor:not-allowed;opacity:0.7">
                        <span style="color:#9ca3af;font-weight:800;font-size:1.3em">⚠️ VERIFY BEFORE BUYING</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                return
        
        # NO ANOMALY - SHOW GREEN
        if winning:
            st.markdown(f'<div style="background:linear-gradient(135deg,#052e16,#14532d);border:4px solid #22c55e;border-radius:20px;padding:40px;margin:20px 0;text-align:center;box-shadow:0 0 30px rgba(34,197,94,0.3)"><div style="color:#22c55e;font-size:2em;font-weight:800;margin-bottom:10px">✅ LOW LOCKED & CONFIRMED</div><div style="color:#86efac;font-size:1.2em;margin-bottom:5px">{city_name}</div><div style="color:#4ade80;font-size:1.4em;font-weight:700;margin-bottom:15px">📅 {today_str}</div><div style="color:#fff;font-size:6em;font-weight:900;margin:20px 0;text-shadow:0 0 20px rgba(34,197,94,0.5)">{settlement_low}°F</div><div style="color:#4ade80;font-size:1.3em;font-weight:600">{lock_info}</div><div style="color:#86efac;font-size:1em;margin-top:5px">6hr Min @ {settlement_time} local</div><div style="margin-top:25px;padding:20px;background:rgba(0,0,0,0.4);border-radius:12px"><div style="display:flex;justify-content:space-around;align-items:center;flex-wrap:wrap;gap:15px;margin-bottom:15px"><div style="text-align:center"><div style="color:#6b7280;font-size:0.8em">WINNER</div><div style="color:#fbbf24;font-size:1.5em;font-weight:800">{bracket_name}</div></div><div style="text-align:center"><div style="color:#6b7280;font-size:0.8em">ASK</div><div style="color:#fff;font-size:1.5em;font-weight:800">{ask}¢</div></div><div style="text-align:center"><div style="color:#6b7280;font-size:0.8em">PROFIT</div><div style="color:{profit_color};font-size:1.5em;font-weight:800">+{profit}¢</div></div><div style="text-align:center"><div style="color:#6b7280;font-size:0.8em">VERDICT</div><div style="font-size:1.5em;font-weight:800">{rating}</div></div></div><a href="{bracket_url}" target="_blank" style="text-decoration:none;display:block"><div style="background:linear-gradient(135deg,#22c55e,#16a34a);padding:15px 20px;border-radius:10px;text-align:center;cursor:pointer"><span style="color:#000;font-weight:900;font-size:1.2em">🛒 BUY YES → {bracket_name} @ {ask}¢</span></div></a></div></div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div style="background:linear-gradient(135deg,#052e16,#14532d);border:4px solid #22c55e;border-radius:20px;padding:40px;margin:20px 0;text-align:center;box-shadow:0 0 30px rgba(34,197,94,0.3)"><div style="color:#22c55e;font-size:2em;font-weight:800;margin-bottom:10px">✅ LOW LOCKED & CONFIRMED</div><div style="color:#86efac;font-size:1.2em;margin-bottom:5px">{city_name}</div><div style="color:#4ade80;font-size:1.4em;font-weight:700;margin-bottom:15px">📅 {today_str}</div><div style="color:#fff;font-size:6em;font-weight:900;margin:20px 0;text-shadow:0 0 20px rgba(34,197,94,0.5)">{settlement_low}°F</div><div style="color:#4ade80;font-size:1.3em;font-weight:600">{lock_info}</div><div style="color:#86efac;font-size:1em;margin-top:5px">6hr Min @ {settlement_time} local</div><div style="margin-top:20px;padding:15px;background:rgba(0,0,0,0.3);border-radius:10px"><span style="color:#f59e0b;font-size:1.1em">⚠️ No matching bracket found on Kalshi</span></div></div>', unsafe_allow_html=True)
    
    elif settlement_low is not None:
        anomaly_active, anomaly_words, wind_speed, forecast_temp = check_forecast_anomalies(cfg.get("lat", 40.78), cfg.get("lon", -73.97))
        
        if winning:
            ask = winning.get("ask", 0)
            profit = 100 - ask
            bracket_name = winning.get("name", "?")
            bracket_url = winning.get("url", "")
            trade_section = f"""
            <div style="margin-top:25px;padding:20px;background:rgba(0,0,0,0.4);border-radius:12px">
                <div style="display:flex;justify-content:space-around;align-items:center;flex-wrap:wrap;gap:15px;margin-bottom:15px">
                    <div style="text-align:center"><div style="color:#6b7280;font-size:0.8em">CURRENT WINNER</div><div style="color:#fbbf24;font-size:1.5em;font-weight:800">{bracket_name}</div></div>
                    <div style="text-align:center"><div style="color:#6b7280;font-size:0.8em">ASK</div><div style="color:#fff;font-size:1.5em;font-weight:800">{ask}¢</div></div>
                    <div style="text-align:center"><div style="color:#6b7280;font-size:0.8em">PROFIT IF HOLDS</div><div style="color:#60a5fa;font-size:1.5em;font-weight:800">+{profit}¢</div></div>
                </div>
                <div style="color:#fbbf24;font-size:0.9em;text-align:center;margin-bottom:10px">⏳ Wait for 06:53 lock before buying</div>
            </div>"""
            
            if anomaly_active:
                danger_text = ', '.join(anomaly_words[:2]) if anomaly_words else 'weather event'
                wind_text = f" | {wind_speed} mph wind" if wind_speed and wind_speed > 25 else ""
                trade_section += f"""
                <div style="margin-top:15px;padding:15px;background:#2d1f0a;border:2px solid #f59e0b;border-radius:10px">
                    <div style="color:#f59e0b;font-weight:800;font-size:1.1em;text-align:center">⚠️ {danger_text.upper()}{wind_text}</div>
                    <div style="color:#fcd34d;font-size:0.9em;text-align:center;margin-top:5px">Check forecast - may invalidate settlement prediction</div>
                </div>"""
        else:
            trade_section = """
            <div style="margin-top:20px;padding:15px;background:rgba(0,0,0,0.3);border-radius:10px">
                <span style="color:#fbbf24;font-size:1.1em">⏳ Early 6hr data - may update at next reading</span>
            </div>"""
        
        st.markdown(f"""
        <div style="background:linear-gradient(135deg,#0c1929,#1e3a5f);border:4px solid #3b82f6;border-radius:20px;padding:40px;margin:20px 0;text-align:center;box-shadow:0 0 30px rgba(59,130,246,0.3)">
            <div style="color:#3b82f6;font-size:2em;font-weight:800;margin-bottom:10px">📊 6hr DATA AVAILABLE</div>
            <div style="color:#93c5fd;font-size:1.2em;margin-bottom:5px">{city_name}</div>
            <div style="color:#60a5fa;font-size:1.4em;font-weight:700;margin-bottom:15px">📅 {today_str}</div>
            <div style="color:#fff;font-size:6em;font-weight:900;margin:20px 0;text-shadow:0 0 20px rgba(59,130,246,0.5)">{settlement_low}°F</div>
            <div style="color:#60a5fa;font-size:1.3em;font-weight:600">6hr Min @ {settlement_time} local</div>
            {trade_section}
        </div>
        """, unsafe_allow_html=True)
    
    else:
        current_temp, obs_low, _, _, _, _, _, _ = fetch_nws_observations(cfg.get("station", "KNYC"), cfg.get("tz", "US/Eastern"))
        preview_text = f"Hourly preview: {obs_low}°F (NOT settlement)" if obs_low else "No data yet"
        anomaly_active, anomaly_words, wind_speed, forecast_temp = check_forecast_anomalies(cfg.get("lat", 40.78), cfg.get("lon", -73.97))
        anomaly_div = ""
        
        if anomaly_active:
            danger_text = ', '.join(anomaly_words[:2]) if anomaly_words else 'weather event'
            wind_text = f" + {wind_speed} MPH" if wind_speed and wind_speed > 25 else ""
            anomaly_div = f"""
            <div style="margin-top:15px;padding:12px;background:#2d0a0a;border:2px solid #ef4444;border-radius:8px">
                <span style="color:#ef4444;font-weight:800;font-size:1em">🌪️ {danger_text.upper()}{wind_text}</span>
            </div>"""
        
        st.markdown(f"""
        <div style="background:linear-gradient(135deg,#292211,#44330d);border:4px solid #f59e0b;border-radius:20px;padding:40px;margin:20px 0;text-align:center;box-shadow:0 0 30px rgba(245,158,11,0.3)">
            <div style="color:#f59e0b;font-size:2em;font-weight:800;margin-bottom:10px">⏳ WAITING FOR 6hr DATA</div>
            <div style="color:#fcd34d;font-size:1.2em;margin-bottom:5px">{city_name}</div>
            <div style="color:#f59e0b;font-size:1.4em;font-weight:700;margin-bottom:15px">📅 {today_str}</div>
            <div style="color:#6b7280;font-size:4em;font-weight:700;margin:20px 0">--°F</div>
            <div style="color:#fbbf24;font-size:1.3em;font-weight:600">{preview_text}</div>
            <div style="margin-top:20px;padding:15px;background:rgba(0,0,0,0.3);border-radius:10px">
                <span style="color:#ef4444;font-size:1.1em">⚠️ 6hr settlement appears at 06:53 local time</span>
            </div>
            {anomaly_div}
        </div>
        """, unsafe_allow_html=True)

if is_owner:
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("📍 City", use_container_width=True, type="primary" if st.session_state.view_mode == "city" else "secondary"):
            st.session_state.view_mode = "city"
            st.rerun()
    with col2:
        if st.button("🔍 Today", use_container_width=True, type="primary" if st.session_state.view_mode == "today" else "secondary"):
            st.session_state.view_mode = "today"
            st.rerun()
    with col3:
        if st.button("🎰 Lottery", use_container_width=True, type="primary" if st.session_state.view_mode == "tomorrow" else "secondary"):
            st.session_state.view_mode = "tomorrow"
            st.rerun()
    with col4:
        if st.button("🦈 SHARK", use_container_width=True, type="primary" if st.session_state.view_mode == "shark" else "secondary"):
            st.session_state.view_mode = "shark"
            st.rerun()
    st.markdown("---")

# [REST OF FILE CONTINUES WITH ALL MODES - TOO LONG, TRUNCATING HERE]
# FILE IS 1600+ LINES - GITHUB UPLOAD RECOMMENDED
