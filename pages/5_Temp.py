"""
🌡️ TEMP.PY - City View with NWS Observations
OWNER ONLY - Tomorrow's Forecast + NWS Table Only
"""
import streamlit as st
import requests
from datetime import datetime
import pytz
from bs4 import BeautifulSoup
import time

st.set_page_config(page_title="🌡️ Temp Trading", page_icon="🌡️", layout="wide")

try:
    OWNER_MODE = "owner" in st.query_params and st.query_params["owner"] == "true"
except:
    OWNER_MODE = False

if not OWNER_MODE:
    st.error("🔒 This page is private.")
    st.stop()

CITIES = {
    "Austin": {"nws": "KAUS", "tz": "US/Central", "lat": 30.1944, "lon": -97.6700},
    "Chicago": {"nws": "KMDW", "tz": "US/Central", "lat": 41.7868, "lon": -87.7522},
    "Denver": {"nws": "KDEN", "tz": "US/Mountain", "lat": 39.8561, "lon": -104.6737},
    "Los Angeles": {"nws": "KLAX", "tz": "US/Pacific", "lat": 33.9425, "lon": -118.4081},
    "Miami": {"nws": "KMIA", "tz": "US/Eastern", "lat": 25.7959, "lon": -80.2870},
    "New York City": {"nws": "KNYC", "tz": "US/Eastern", "lat": 40.7789, "lon": -73.9692},
    "Philadelphia": {"nws": "KPHL", "tz": "US/Eastern", "lat": 39.8721, "lon": -75.2408},
}

if "default_city" not in st.session_state:
    st.session_state.default_city = "New York City"

def fetch_nws_forecast(lat, lon):
    """Fetch tomorrow's forecast LOW from NWS"""
    try:
        points_url = f"https://api.weather.gov/points/{lat},{lon}"
        resp = requests.get(points_url, headers={"User-Agent": "Temp/1.0"}, timeout=10)
        if resp.status_code != 200:
            return None
        
        data = resp.json()
        forecast_url = data.get("properties", {}).get("forecast", "")
        if not forecast_url:
            return None
        
        forecast_resp = requests.get(forecast_url, headers={"User-Agent": "Temp/1.0"}, timeout=10)
        if forecast_resp.status_code != 200:
            return None
        
        periods = forecast_resp.json().get("properties", {}).get("periods", [])
        
        for period in periods:
            name = period.get("name", "")
            if "Tonight" in name or "Night" in name:
                temp = period.get("temperature")
                if temp:
                    return temp
        
        return None
    except:
        return None

def fetch_full_nws_recording(station):
    """Fetch NWS obhistory - CRITICAL: cells[9] = 6hr MIN for LOW settlement"""
    timestamp = int(time.time())
    url = f"https://forecast.weather.gov/data/obhistory/{station}.html?_={timestamp}"
    try:
        headers = {
            "User-Agent": "Temp/1.0",
            "Cache-Control": "no-cache, no-store, must-revalidate, max-age=0",
            "Pragma": "no-cache",
            "Expires": "0"
        }
        
        resp = requests.get(url, headers=headers, timeout=15)
        if resp.status_code != 200:
            return []
        
        soup = BeautifulSoup(resp.text, 'html.parser')
        table = soup.find('table')
        if not table:
            return []
        
        rows = table.find_all('tr')
        readings = []
        
        for row in rows[3:]:
            cells = row.find_all('td')
            if len(cells) < 10:
                continue
            
            try:
                readings.append({
                    "date": cells[0].text.strip(),
                    "time": cells[1].text.strip(),
                    "wind": cells[2].text.strip(),
                    "vis": cells[3].text.strip(),
                    "weather": cells[4].text.strip(),
                    "sky": cells[5].text.strip(),
                    "air": cells[6].text.strip(),
                    "dwpt": cells[7].text.strip(),
                    "max_6hr": cells[8].text.strip(),
                    "min_6hr": cells[9].text.strip()
                })
            except:
                continue
        
        return readings
    except:
        return []

st.title("🌡️ Temperature Trading Dashboard")
st.caption("⚠️ OWNER ONLY - EDUCATIONAL PURPOSES")

# Sidebar: City Selector
with st.sidebar:
    st.header("📍 Select City")
    city_selection = st.selectbox(
        "Choose a city to view:",
        list(CITIES.keys()),
        index=list(CITIES.keys()).index(st.session_state.default_city),
        label_visibility="collapsed"
    )
    
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("⭐ Set Default", use_container_width=True):
            st.session_state.default_city = city_selection
            st.success(f"✅ Saved!")
    with col_b:
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()

st.divider()

cfg = CITIES[city_selection]
st.header(f"📍 {city_selection}")

# Tomorrow's Forecast
st.subheader("📅 Tomorrow's Forecast")

lat = cfg.get("lat")
lon = cfg.get("lon")

if lat and lon:
    forecast_low = fetch_nws_forecast(lat, lon)
    
    if forecast_low:
        forecast_settlement = round(forecast_low)
        st.success(f"🎯 NWS Forecast LOW: **{forecast_low}°F** → Settlement: **{forecast_settlement}°F**")
    else:
        st.info("⏳ Tomorrow's forecast not yet available from NWS")
else:
    st.error("⚠️ Missing lat/lon coordinates for this city")

st.divider()

# Full NWS Table
st.subheader("📋 Full NWS Table")

full_readings = fetch_full_nws_recording(cfg["nws"])

if full_readings:
    table_html = """
    <style>
    .nws-full { width: 100%; border-collapse: collapse; font-family: Arial, sans-serif; font-size: 12px; }
    .nws-full th { background: #b8cce4; color: #000; padding: 6px 4px; text-align: center; border: 1px solid #7f7f7f; font-weight: 600; font-size: 11px; }
    .nws-full td { padding: 5px 3px; text-align: center; border: 1px solid #d0d0d0; background: #fff; color: #000; font-size: 11px; }
    .nws-full tr:nth-child(even) td { background: #f0f0f0; }
    .temp-header { background: #dae8f5 !important; }
    </style>
    <div style="overflow-x: auto;">
    <table class='nws-full'>
    <thead>
    <tr>
    <th rowspan="3">Date</th>
    <th rowspan="3">Time<br/>(local)</th>
    <th rowspan="3">Wind<br/>(mph)</th>
    <th rowspan="3">Vis.<br/>(mi.)</th>
    <th rowspan="3">Weather</th>
    <th rowspan="3">Sky<br/>Cond.</th>
    <th colspan="4" class="temp-header">Temperature (°F)</th>
    </tr>
    <tr>
    <th rowspan="2">Air</th>
    <th rowspan="2">Dwpt</th>
    <th colspan="2">6 hour</th>
    </tr>
    <tr>
    <th>Max</th>
    <th>Min</th>
    </tr>
    </thead>
    <tbody>
    """
    
    for r in full_readings:
        table_html += f"""<tr>
        <td>{r['date']}</td>
        <td>{r['time']}</td>
        <td>{r['wind']}</td>
        <td>{r['vis']}</td>
        <td>{r['weather']}</td>
        <td>{r['sky']}</td>
        <td><b>{r['air']}</b></td>
        <td>{r['dwpt']}</td>
        <td><b style="color:#d00">{r['max_6hr']}</b></td>
        <td><b style="color:#00d">{r['min_6hr']}</b></td>
        </tr>"""
    
    table_html += "</tbody></table></div>"
    st.markdown(table_html, unsafe_allow_html=True)
    st.caption(f"Source: https://forecast.weather.gov/data/obhistory/{cfg['nws']}.html")
else:
    st.warning("⚠️ No NWS data available")

st.divider()
st.caption("⚠️ **DISCLAIMER:** EDUCATIONAL and EXPERIMENTAL purposes ONLY. NOT financial advice. NOT betting advice.")

st.divider()
eastern = pytz.timezone("US/Eastern")
st.caption(f"Last updated: {datetime.now(eastern).strftime('%I:%M:%S %p ET')}")
