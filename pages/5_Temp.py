import streamlit as st
import requests
from datetime import datetime, timedelta
import pytz
import re
from bs4 import BeautifulSoup

st.set_page_config(page_title="LOW Temp Edge Finder", page_icon="🌡️", layout="wide")

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
    "Austin": {"high": "KXHIGHAUS", "low": "KXLOWTAUS", "station": "KAUS", "lat": 30.19, "lon": -97.67, "tz": "US/Central", "slug": "lowest-temperature-in-austin"},
    "Chicago": {"high": "KXHIGHCHI", "low": "KXLOWTCHI", "station": "KMDW", "lat": 41.79, "lon": -87.75, "tz": "US/Central", "slug": "lowest-temperature-in-chicago"},
    "Denver": {"high": "KXHIGHDEN", "low": "KXLOWTDEN", "station": "KDEN", "lat": 39.86, "lon": -104.67, "tz": "US/Mountain", "slug": "lowest-temperature-in-denver"},
    "Los Angeles": {"high": "KXHIGHLAX", "low": "KXLOWTLAX", "station": "KLAX", "lat": 33.94, "lon": -118.41, "tz": "US/Pacific", "slug": "lowest-temperature-in-los-angeles"},
    "Miami": {"high": "KXHIGHMIA", "low": "KXLOWTMIA", "station": "KMIA", "lat": 25.80, "lon": -80.29, "tz": "US/Eastern", "slug": "lowest-temperature-in-miami"},
    "New York City": {"high": "KXHIGHNY", "low": "KXLOWTNYC", "station": "KNYC", "lat": 40.78, "lon": -73.97, "tz": "US/Eastern", "slug": "lowest-temperature-in-nyc"},
    "Philadelphia": {"high": "KXHIGHPHL", "low": "KXLOWTPHL", "station": "KPHL", "lat": 39.87, "lon": -75.23, "tz": "US/Eastern", "slug": "lowest-temperature-in-philadelphia"},
}
CITY_LIST = sorted(CITY_CONFIG.keys())

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

def temp_in_bracket(temp, range_str):
    low, high = get_bracket_bounds(range_str)
    return low < temp <= high

@st.cache_data(ttl=60)
def fetch_kalshi_brackets(series_ticker):
    url = f"https://api.elections.kalshi.com/trade-api/v2/markets?series_ticker={series_ticker}&status=open"
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code != 200:
            return None
        markets = resp.json().get("markets", [])
        if not markets:
            return None
        today = datetime.now(eastern)
        today_str = today.strftime('%y%b%d').upper()
        today_markets = [m for m in markets if today_str in m.get("event_ticker", "").upper()]
        if not today_markets:
            first_event = markets[0].get("event_ticker", "")
            today_markets = [m for m in markets if m.get("event_ticker") == first_event]
        brackets = []
        for m in today_markets:
            range_txt = m.get("subtitle", "") or m.get("title", "")
            ticker = m.get("ticker", "")
            low, high = get_bracket_bounds(range_txt)
            if low == -999:
                mid = high - 1
            elif high == 999:
                mid = low + 1
            else:
                mid = (low + high) / 2
            yb = m.get("yes_bid", 0)
            ya = m.get("yes_ask", 0)
            if yb and ya:
                yes_price = (yb + ya) / 2
            else:
                yes_price = ya or yb or 0
            brackets.append({"range": range_txt, "mid": mid, "yes": yes_price, "ticker": ticker, "low": low, "high": high,
                "url": f"https://kalshi.com/markets/{series_ticker.lower()}/{ticker.lower()}" if ticker else "#"})
        brackets.sort(key=lambda x: x['mid'] or 0)
        return brackets
    except:
        return None

@st.cache_data(ttl=120)
def fetch_nws_6hr_extremes(station):
    url = f"https://forecast.weather.gov/data/obhistory/{station}.html"
    try:
        resp = requests.get(url, headers={"User-Agent": "TempEdge/3.0"}, timeout=15)
        if resp.status_code != 200:
            return {}
        soup = BeautifulSoup(resp.text, 'html.parser')
        table = soup.find('table')
        if not table:
            return {}
        rows = table.find_all('tr')
        extremes = {}
        today = datetime.now(eastern).day
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
        # Find confirm time for LOW - must be WITHIN available readings
        readings_chrono = sorted(readings, key=lambda x: x["time"])
        confirm_time = None
        low_found = False
        for r in readings_chrono:
            if r["temp"] == low:
                low_found = True
            elif low_found and r["temp"] > low:
                confirm_time = r["time"]
                break
        # Get time range of available data
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

# ========== HEADER ==========
st.title("🌡️ LOW TEMP EDGE FINDER")
st.caption(f"Live NWS Observations + Kalshi | {now.strftime('%b %d, %Y %I:%M %p ET')}")

query_params = st.query_params
default_city = query_params.get("city", "New York City")
if default_city not in CITY_LIST:
    default_city = "New York City"

# Owner check
is_owner = query_params.get("mode") == "owner"

# Owner sidebar tips
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
        <div style="background:#1a1a2e;border:1px solid #3b82f6;border-radius:8px;padding:12px;margin-bottom:15px">
            <div style="color:#3b82f6;font-weight:700;margin-bottom:8px">⏰ LOW LOCK-IN TIMES</div>
            <div style="color:#c9d1d9;font-size:0.8em;line-height:1.6">
                <b>Winter</b> (Nov-Feb): 6-7 AM<br>
                <b>Spring</b> (Mar-Apr): 5-6 AM<br>
                <b>Summer</b> (May-Aug): 5-6 AM<br>
                <b>Fall</b> (Sep-Oct): 6-7 AM<br><br>
                <span style="color:#9ca3af">LOW locks around sunrise ±30min</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

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
extremes_6hr = fetch_nws_6hr_extremes(cfg.get("station", "KNYC")) if is_owner else {}

# ============================================================
# OWNER ONLY: BIG GREEN/AMBER BOX WITH BUY RECOMMENDATION
# ============================================================
if is_owner and obs_low and current_temp:
    city_tz = pytz.timezone(cfg.get("tz", "US/Eastern"))
    hour = datetime.now(city_tz).hour
    
    # Calculate time ago - ONLY if confirm_time exists and is valid
    if confirm_time:
        mins_ago = int((datetime.now(city_tz) - confirm_time).total_seconds() / 60)
        if mins_ago >= 0 and mins_ago < 1440:  # Sanity check: within 24 hours
            time_ago_text = f"Confirmed {mins_ago} minutes ago"
        else:
            time_ago_text = "Confirmation time invalid"
    else:
        time_ago_text = "Waiting for confirmation (need rise after low)..."
    
    # Show data range warning if oldest reading is recent (data may be incomplete)
    data_warning = ""
    if oldest_time:
        oldest_hour = oldest_time.hour
        if oldest_hour >= 7:  # If data only goes back to 7 AM or later, might miss the real low
            data_warning = f"<div style='color:#f59e0b;font-size:0.85em;margin-top:10px'>⚠️ NWS data only from {oldest_time.strftime('%H:%M')} - early morning low may be missing!</div>"
    
    # Lock status
    if hour >= 6 and confirm_time:
        lock_status = "✅ LOCKED IN"
        lock_color = "#22c55e"
        box_bg = "linear-gradient(135deg,#1a2e1a,#0d1117)"
    elif hour >= 6:
        lock_status = "⏳ LIKELY LOCKED (awaiting rise)"
        lock_color = "#3b82f6"
        box_bg = "linear-gradient(135deg,#1a1a2e,#0d1117)"
    else:
        lock_status = "⏳ NOT LOCKED - MAY STILL DROP"
        lock_color = "#f59e0b"
        box_bg = "linear-gradient(135deg,#2d1f0a,#0d1117)"
    
    st.markdown(f"""
    <div style="background:{box_bg};border:3px solid {lock_color};border-radius:16px;padding:30px;margin:20px 0;text-align:center;box-shadow:0 0 30px rgba(34,197,94,0.3)">
        <div style="color:{lock_color};font-size:1.2em;font-weight:700;margin-bottom:10px">{lock_status}</div>
        <div style="color:#6b7280;font-size:0.9em;margin-bottom:5px">Today's Low (from available data)</div>
        <div style="color:#fff;font-size:4em;font-weight:800;margin:10px 0">{obs_low}°F</div>
        <div style="color:#9ca3af;font-size:0.9em;margin-bottom:10px
