import streamlit as st

st.set_page_config(page_title="LOW Temp Edge Finder", page_icon="🌡️", layout="wide")

import uuid
import requests as req_ga

def send_ga4_event(page_title, page_path):
    try:
        url = f"https://www.google-analytics.com/mp/collect?measurement_id=G-NQKY5VQ376&api_secret=n4oBJjH7RXi3dA7aQo2CZA"
        payload = {"client_id": str(uuid.uuid4()), "events": [{"name": "page_view", "params": {"page_title": page_title, "page_location": f"https://bigsnapshot.streamlit.app{page_path}"}}]}
        req_ga.post(url, json=payload, timeout=2)
    except: pass

send_ga4_event("Temp Edge Finder", "/Temp")

import extra_streamlit_components as stx
cookie_manager = stx.CookieManager()
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
saved_auth = cookie_manager.get("authenticated")
if saved_auth == "true":
    st.session_state.authenticated = True

import requests
from datetime import datetime
import pytz
import math
import re

st.markdown("""
<style>
.stApp {background-color: #0d1117;}
div[data-testid="stMarkdownContainer"] p {color: #c9d1d9;}
</style>
""", unsafe_allow_html=True)

eastern = pytz.timezone("US/Eastern")
now = datetime.now(eastern)

CITY_CONFIG = {
    "Austin": {"low": "KXLOWTAUS", "station": "KAUS", "lat": 30.19, "lon": -97.67, "tz": "US/Central", "slug": "lowest-temperature-in-austin"},
    "Chicago": {"low": "KXLOWTCHI", "station": "KMDW", "lat": 41.79, "lon": -87.75, "tz": "US/Central", "slug": "lowest-temperature-in-chicago"},
    "Denver": {"low": "KXLOWTDEN", "station": "KDEN", "lat": 39.86, "lon": -104.67, "tz": "US/Mountain", "slug": "lowest-temperature-in-denver"},
    "Los Angeles": {"low": "KXLOWTLAX", "station": "KLAX", "lat": 33.94, "lon": -118.41, "tz": "US/Pacific", "slug": "lowest-temperature-in-los-angeles"},
    "Miami": {"low": "KXLOWTMIA", "station": "KMIA", "lat": 25.80, "lon": -80.29, "tz": "US/Eastern", "slug": "lowest-temperature-in-miami"},
    "New York City": {"low": "KXLOWTNYC", "station": "KNYC", "lat": 40.78, "lon": -73.97, "tz": "US/Eastern", "slug": "lowest-temperature-in-nyc"},
    "Philadelphia": {"low": "KXLOWTPHL", "station": "KPHL", "lat": 39.87, "lon": -75.23, "tz": "US/Eastern", "slug": "lowest-temperature-in-philadelphia"},
}
CITY_LIST = sorted(CITY_CONFIG.keys())

@st.cache_data(ttl=60)
def fetch_kalshi_brackets(series_ticker, slug):
    """Fetch REAL Kalshi brackets from API"""
    url = f"https://api.elections.kalshi.com/trade-api/v2/markets?series_ticker={series_ticker}&status=open"
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code != 200:
            return []
        markets = resp.json().get("markets", [])
        if not markets:
            return []
        
        # Get today's markets
        today = datetime.now(eastern)
        today_str = today.strftime('%y%b%d').upper()
        today_markets = [m for m in markets if today_str in m.get("event_ticker", "").upper()]
        if not today_markets:
            first_event = markets[0].get("event_ticker", "")
            today_markets = [m for m in markets if m.get("event_ticker") == first_event]
        
        brackets = []
        for m in today_markets:
            title = m.get("title", "")
            ticker = m.get("ticker", "")
            
            # Parse the title to extract bracket info
            # Examples: "Will the minimum temperature be 9-10° on Jan 28, 2026?"
            #           "Will the minimum temperature be >10° on Jan 28, 2026?"
            #           "Will the minimum temperature be <3° on Jan 28, 2026?"
            
            # Extract the temperature part
            match = re.search(r'be\s+([<>]?\d+[-–]?\d*)[°]', title)
            if not match:
                continue
            
            temp_part = match.group(1)
            
            # Determine bracket type and bounds
            if temp_part.startswith('>'):
                # ">10" means "11° or above" (greater than 10)
                threshold = int(temp_part[1:])
                bracket_name = f"{threshold + 1}° or above"
                low_bound = threshold + 0.5
                high_bound = 999
            elif temp_part.startswith('<'):
                # "<3" means "2° or below" (less than 3)
                threshold = int(temp_part[1:])
                bracket_name = f"{threshold - 1}° or below"
                low_bound = -999
                high_bound = threshold - 0.5
            elif '-' in temp_part or '–' in temp_part:
                # "9-10" means 9° to 10°
                parts = re.split(r'[-–]', temp_part)
                low_num = int(parts[0])
                high_num = int(parts[1])
                bracket_name = f"{low_num}° to {high_num}°"
                low_bound = low_num - 0.5
                high_bound = high_num + 0.5
            else:
                continue
            
            # Get price
            yb = m.get("yes_bid", 0)
            ya = m.get("yes_ask", 0)
            yes_price = ((yb + ya) / 2) if (yb and ya) else (ya or yb or 0)
            
            # Build URL
            kalshi_url = f"https://kalshi.com/markets/{series_ticker.lower()}/{slug}/{ticker.lower()}"
            
            brackets.append({
                "name": bracket_name,
                "low": low_bound,
                "high": high_bound,
                "price": yes_price,
                "url": kalshi_url,
                "ticker": ticker
            })
        
        # Sort by low bound
        brackets.sort(key=lambda x: x['low'])
        return brackets
    except:
        return []

def find_winning_bracket(low_temp, brackets):
    """Find which REAL Kalshi bracket the low temp falls into"""
    for b in brackets:
        if b['low'] < low_temp <= b['high']:
            return b
    # Fallback to highest bracket if temp is very high
    if brackets and low_temp > brackets[-1]['high']:
        return brackets[-1]
    return None

@st.cache_data(ttl=120)
def fetch_nws_observations(station, city_tz_str):
    url = f"https://api.weather.gov/stations/{station}/observations?limit=100"
    try:
        city_tz = pytz.timezone(city_tz_str)
        resp = requests.get(url, headers={"User-Agent": "TempEdge/3.0"}, timeout=15)
        if resp.status_code != 200:
            return None, None, None, None
        observations = resp.json().get("features", [])
        if not observations:
            return None, None, None, None
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
            return None, None, None, None
        readings.sort(key=lambda x: x["time"], reverse=True)
        current = readings[0]["temp"]
        low = min(r["temp"] for r in readings)
        
        # Find when low was confirmed (first reading AFTER the low that's higher)
        readings_chrono = sorted(readings, key=lambda x: x["time"])
        low_time = None
        confirm_time = None
        for i, r in enumerate(readings_chrono):
            if r["temp"] == low:
                low_time = r["time"]
            elif low_time and r["temp"] > low:
                confirm_time = r["time"]
                break
        
        return current, low, low_time, confirm_time
    except:
        return None, None, None, None

# ========== HEADER ==========
st.title("🌡️ LOW TEMP EDGE FINDER")
st.caption(f"{now.strftime('%b %d, %Y %I:%M %p ET')}")

query_params = st.query_params
default_city = query_params.get("city", "New York City")
if default_city not in CITY_LIST:
    default_city = "New York City"

city = st.selectbox("📍 Select City", CITY_LIST, index=CITY_LIST.index(default_city))

cfg = CITY_CONFIG.get(city, {})
city_tz_str = cfg.get("tz", "US/Eastern")
city_tz = pytz.timezone(city_tz_str)
city_now = datetime.now(city_tz)
hour = city_now.hour

current_temp, obs_low, low_time, confirm_time = fetch_nws_observations(cfg.get("station", "KNYC"), city_tz_str)

# Fetch REAL Kalshi brackets
brackets = fetch_kalshi_brackets(cfg.get("low", "KXLOWTNYC"), cfg.get("slug", "lowest-temperature-in-nyc"))

if obs_low:
    # Find the REAL winning bracket
    winning = find_winning_bracket(obs_low, brackets)
    
    if winning:
        buy_bracket = winning['name']
        buy_price = f"@ {winning['price']:.0f}¢" if winning['price'] else ""
        buy_url = winning['url']
    else:
        buy_bracket = "Could not load brackets"
        buy_price = ""
        buy_url = "#"
    
    # Calculate minutes ago
    if confirm_time:
        mins_ago = int((city_now - confirm_time).total_seconds() / 60)
        time_ago_text = f"Confirmed {mins_ago} minutes ago"
    elif low_time:
        mins_ago = int((city_now - low_time).total_seconds() / 60)
        time_ago_text = f"Low hit {mins_ago} minutes ago"
    else:
        time_ago_text = ""
    
    # Determine lock status
    if hour >= 6:
        lock_status = "✅ LOCKED IN"
        lock_color = "#22c55e"
    else:
        lock_status = "⏳ MAY STILL DROP"
        lock_color = "#f59e0b"
    
    # ONE BIG BOX
    st.markdown(f"""
    <div style="background:linear-gradient(135deg,#1a2e1a,#0d1117);border:3px solid {lock_color};border-radius:16px;padding:30px;margin:20px 0;text-align:center;box-shadow:0 0 30px rgba(34,197,94,0.3)">
        <div style="color:{lock_color};font-size:1.2em;font-weight:700;margin-bottom:10px">{lock_status}</div>
        <div style="color:#6b7280;font-size:0.9em;margin-bottom:5px">Today's Low</div>
        <div style="color:#fff;font-size:4em;font-weight:800;margin:10px 0">{obs_low}°F</div>
        <div style="color:#9ca3af;font-size:0.9em;margin-bottom:20px">{time_ago_text}</div>
        <div style="background:#161b22;border-radius:10px;padding:20px;margin-top:15px">
            <div style="color:#f59e0b;font-size:1em;margin-bottom:8px">BUY ON KALSHI {buy_price}:</div>
            <div style="color:#fbbf24;font-size:2em;font-weight:700">{buy_bracket}</div>
            <a href="{buy_url}" target="_blank" style="background:linear-gradient(135deg,#f59e0b,#d97706);color:#000;padding:12px 28px;border-radius:6px;text-decoration:none;font-weight:700;display:inline-block;margin-top:15px;box-shadow:0 4px 12px rgba(245,158,11,0.4)">BUY YES →</a>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Current temp small display
    st.markdown(f"""
    <div style="text-align:center;color:#6b7280;margin-top:20px">
        Current: <span style="color:#fff;font-weight:600">{current_temp}°F</span> | 
        Station: <span style="color:#22c55e">{cfg.get('station')}</span> | 
        {city_now.strftime('%I:%M %p')} {city_now.strftime('%Z')}
    </div>
    """, unsafe_allow_html=True)

else:
    st.error("⚠️ Could not fetch NWS observations")

st.markdown("---")
st.subheader("📡 NWS Forecast")

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

forecast = fetch_nws_forecast(cfg.get("lat", 40.78), cfg.get("lon", -73.97))
if forecast:
    fcols = st.columns(len(forecast))
    for i, period in enumerate(forecast):
        with fcols[i]:
            name = period.get("name", "")
            temp = period.get("temperature", "")
            unit = period.get("temperatureUnit", "F")
            short = period.get("shortForecast", "")
            bg = "#1a1a2e" if "night" in name.lower() or "tonight" in name.lower() else "#1f2937"
            temp_color = "#3b82f6" if "night" in name.lower() or "tonight" in name.lower() else "#ef4444"
            st.markdown(f'<div style="background:{bg};border:1px solid #30363d;border-radius:8px;padding:12px;text-align:center"><div style="color:#9ca3af;font-size:0.8em;font-weight:600">{name}</div><div style="color:{temp_color};font-size:1.8em;font-weight:700">{temp}°{unit}</div><div style="color:#6b7280;font-size:0.75em;margin-top:5px">{short}</div></div>', unsafe_allow_html=True)
else:
    st.caption("Could not load NWS forecast")

st.markdown("---")
st.markdown('<div style="background:linear-gradient(90deg,#d97706,#f59e0b);padding:10px 15px;border-radius:8px;text-align:center"><b style="color:#000">🧪 FREE TOOL</b> <span style="color:#000">— LOW Temperature Edge Finder v5.0</span></div>', unsafe_allow_html=True)

st.markdown('<div style="color:#6b7280;font-size:0.75em;text-align:center;margin-top:20px">⚠️ For educational purposes only. Not financial advice. Verify on Kalshi before trading.</div>', unsafe_allow_html=True)
