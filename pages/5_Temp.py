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
    "Austin": {"high": "KXHIGHAUS", "low": "KXLOWTAUS", "station": "KAUS", "lat": 30.19, "lon": -97.67, "tz": "US/Central"},
    "Chicago": {"high": "KXHIGHCHI", "low": "KXLOWTCHI", "station": "KMDW", "lat": 41.79, "lon": -87.75, "tz": "US/Central"},
    "Denver": {"high": "KXHIGHDEN", "low": "KXLOWTDEN", "station": "KDEN", "lat": 39.86, "lon": -104.67, "tz": "US/Mountain"},
    "Los Angeles": {"high": "KXHIGHLAX", "low": "KXLOWTLAX", "station": "KLAX", "lat": 33.94, "lon": -118.41, "tz": "US/Pacific"},
    "Miami": {"high": "KXHIGHMIA", "low": "KXLOWTMIA", "station": "KMIA", "lat": 25.80, "lon": -80.29, "tz": "US/Eastern"},
    "New York City": {"high": "KXHIGHNY", "low": "KXLOWTNYC", "station": "KNYC", "lat": 40.78, "lon": -73.97, "tz": "US/Eastern"},
    "Philadelphia": {"high": "KXHIGHPHL", "low": "KXLOWTPHL", "station": "KPHL", "lat": 39.87, "lon": -75.23, "tz": "US/Eastern"},
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

st.title("🌡️ LOW TEMP EDGE FINDER")
st.caption(f"Live NWS Observations + Kalshi | {now.strftime('%b %d, %Y %I:%M %p ET')}")

query_params = st.query_params
default_city = query_params.get("city", "New York City")
if default_city not in CITY_LIST:
    default_city = "New York City"
is_owner = query_params.get("mode") == "owner"

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
            <div style="color:#f59e0b;font-weight:700;margin-bottom:8px">🗽 NYC TRADER SCHEDULE</div>
            <div style="color:#c9d1d9;font-size:0.8em;line-height:1.6">
                <b>6-7 AM ET</b> → NYC, Philly, Miami<br>
                <b>7-8 AM ET</b> → Chicago, Austin<br>
                <b>8-9 AM ET</b> → Denver<br>
                <b>9-10 AM ET</b> → Los Angeles<br><br>
                <span style="color:#9ca3af">All LOWs locked by 10 AM ET</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

# Public sidebar - visible to everyone
with st.sidebar:
    st.markdown("""
    <div style="background:#1a1a2e;border:1px solid #3b82f6;border-radius:8px;padding:12px;margin-bottom:15px">
        <div style="color:#3b82f6;font-weight:700;margin-bottom:8px">⏰ LOW LOCK-IN TIMES (Local)</div>
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
extremes_6hr = fetch_nws_6hr_extremes(cfg.get("station", "KNYC"), cfg.get("tz", "US/Eastern")) if is_owner else {}

# OWNER BOX
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

# Current temp display
if current_temp:
    st.markdown(f"""
    <div style="background:#161b22;border:1px solid #30363d;border-radius:8px;padding:15px;margin:10px 0">
        <div style="text-align:center;margin-bottom:10px">
            <span style="color:#6b7280;font-size:0.75em">Data from NWS Station: <strong style="color:#22c55e">{cfg.get('station', 'N/A')}</strong></span>
        </div>
        <div style="display:flex;justify-content:space-around;text-align:center;flex-wrap:wrap;gap:15px">
            <div><div style="color:#6b7280;font-size:0.8em">CURRENT</div><div style="color:#fff;font-size:1.5em;font-weight:700">{current_temp}°F</div></div>
            <div><div style="color:#3b82f6;font-size:0.8em">TODAY'S LOW</div><div style="color:#3b82f6;font-size:1.5em;font-weight:700">{obs_low}°F</div></div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    if readings:
        with st.expander("📊 Recent NWS Observations", expanded=True):
            if oldest_time and newest_time:
                st.markdown(f"<div style='color:#6b7280;font-size:0.8em;margin-bottom:10px;text-align:center'>📅 Data: {oldest_time.strftime('%H:%M')} to {newest_time.strftime('%H:%M')} local</div>", unsafe_allow_html=True)
            
            display_list = readings if is_owner else readings[:8]
            
            # Use actual obs_low, not min of display_list
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
st.markdown('<div style="background:linear-gradient(90deg,#d97706,#f59e0b);padding:10px 15px;border-radius:8px;margin-bottom:20px;text-align:center"><b style="color:#000">🧪 FREE TOOL</b> <span style="color:#000">— LOW Temperature Edge Finder v5.3</span></div>', unsafe_allow_html=True)

st.markdown('<div style="color:#6b7280;font-size:0.75em;text-align:center;margin-top:30px">⚠️ For entertainment purposes only. Not financial advice. Verify on Kalshi before trading.</div>', unsafe_allow_html=True)
