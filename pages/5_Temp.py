"""
🌡️ TEMP.PY - City View with NWS Observations
OWNER ONLY - Uses 6hr aggregate MIN for settlement (cells[9])
"""
import streamlit as st
import requests
from datetime import datetime
import pytz
from bs4 import BeautifulSoup
import re

st.set_page_config(page_title="🌡️ Temp Trading", page_icon="🌡️", layout="wide")

try:
    OWNER_MODE = "owner" in st.query_params and st.query_params["owner"] == "true"
except:
    OWNER_MODE = False

if not OWNER_MODE:
    st.error("🔒 This page is private.")
    st.stop()

CITIES = {
    "Austin": {"nws": "KAUS", "tz": "US/Central", "kalshi_low": "KXLOWTAUS"},
    "Chicago": {"nws": "KMDW", "tz": "US/Central", "kalshi_low": "KXLOWTCHI"},
    "Denver": {"nws": "KDEN", "tz": "US/Mountain", "kalshi_low": "KXLOWTDEN"},
    "Los Angeles": {"nws": "KLAX", "tz": "US/Pacific", "kalshi_low": "KXLOWTLAX"},
    "Miami": {"nws": "KMIA", "tz": "US/Eastern", "kalshi_low": "KXLOWTMIA"},
    "New York City": {"nws": "KNYC", "tz": "US/Eastern", "kalshi_low": "KXLOWTNYC"},
    "Philadelphia": {"nws": "KPHL", "tz": "US/Eastern", "kalshi_low": "KXLOWTPHL"},
}

if "default_city" not in st.session_state:
    st.session_state.default_city = "New York City"

@st.cache_data(ttl=300)
def fetch_kalshi_brackets(series_ticker):
    """Fetch Kalshi brackets for LOW market"""
    url = f"https://api.elections.kalshi.com/trade-api/v2/markets?series_ticker={series_ticker}&status=open&limit=100"
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code != 200:
            return []
        
        markets = resp.json().get("markets", [])
        brackets = []
        
        for m in markets:
            subtitle = m.get("subtitle", "") or m.get("sub_title", "") or m.get("yes_sub_title", "")
            match = re.search(r'(\d+)°?\s*to\s*(\d+)°?', subtitle)
            if match:
                low = int(match.group(1))
                high = int(match.group(2))
                brackets.append({
                    "low": low,
                    "high": high,
                    "range": f"{low}-{high}°F",
                    "ticker": m.get("ticker", "")
                })
        
        return brackets
    except:
        return []

@st.cache_data(ttl=300)
def fetch_full_nws_recording(station, city_tz_str):
    """Fetch NWS obhistory - CRITICAL: cells[9] = 6hr MIN for LOW settlement"""
    url = f"https://forecast.weather.gov/data/obhistory/{station}.html"
    try:
        city_tz = pytz.timezone(city_tz_str)
        today = datetime.now(city_tz).day
        
        resp = requests.get(url, headers={"User-Agent": "Temp/1.0"}, timeout=15)
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
                date_val = cells[0].text.strip()
                if date_val and int(date_val) == today:
                    readings.append({
                        "date": date_val,
                        "time": cells[1].text.strip(),
                        "wind": cells[2].text.strip(),
                        "vis": cells[3].text.strip(),
                        "weather": cells[4].text.strip(),
                        "sky": cells[5].text.strip(),
                        "air": cells[6].text.strip(),
                        "dwpt": cells[7].text.strip(),
                        "max_6hr": cells[8].text.strip(),
                        "min_6hr": cells[9].text.strip()  # CRITICAL: 6hr MIN for LOW
                    })
            except:
                continue
        
        return readings
    except:
        return []

@st.cache_data(ttl=300)
def fetch_nws_observations(station, city_tz_str):
    """Fetch observations from JSON API"""
    url = f"https://api.weather.gov/stations/{station}/observations?limit=500"
    try:
        city_tz = pytz.timezone(city_tz_str)
        resp = requests.get(url, headers={"User-Agent": "Temp/1.0"}, timeout=15)
        if resp.status_code != 200:
            return None, None, None, []
        
        observations = resp.json().get("features", [])
        if not observations:
            return None, None, None, []
        
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
                    readings.append({"time": ts_local.strftime("%H:%M"), "temp": temp_f})
            except:
                continue
        
        if not readings:
            return None, None, None, []
        
        temps = [r["temp"] for r in readings]
        current = temps[0]
        low = min(temps)
        high = max(temps)
        
        return current, low, high, readings
    except:
        return None, None, None, []

st.title("🌡️ Temperature Trading Dashboard")
st.caption("⚠️ OWNER ONLY - EDUCATIONAL PURPOSES")

col1, col2 = st.columns([3, 1])
with col1:
    city_selection = st.selectbox("📍 Select City", list(CITIES.keys()), index=list(CITIES.keys()).index(st.session_state.default_city))
with col2:
    if st.button("⭐ Set as Default", use_container_width=True):
        st.session_state.default_city = city_selection
        st.success(f"✅ {city_selection} saved!")

st.divider()

cfg = CITIES[city_selection]
st.header(f"📍 {city_selection}")

current_temp, obs_low, obs_high, readings = fetch_nws_observations(cfg["nws"], cfg["tz"])
full_readings = fetch_full_nws_recording(cfg["nws"], cfg["tz"])

# FALLBACK: If JSON API fails, use HTML
if not readings and full_readings:
    st.warning("⚠️ JSON API unavailable - using HTML fallback")
    readings = []
    for r in full_readings:
        try:
            air_temp = float(r['air']) if r['air'] else None
            if air_temp is not None:
                readings.append({"time": r['time'], "temp": air_temp})
        except:
            continue
    
    if readings:
        readings.reverse()
        temps = [r['temp'] for r in readings]
        current_temp = temps[0]
        obs_low = min(temps)
        obs_high = max(temps)

if current_temp:
    settlement_info = ""
    if full_readings:
        # Calculate 6hr MIN (LOWEST value in cells[9])
        raw_6hr_min = None
        for r in full_readings:
            if r['min_6hr']:
                try:
                    min_val = float(r['min_6hr'])
                    if raw_6hr_min is None or min_val < raw_6hr_min:
                        raw_6hr_min = min_val
                except:
                    pass
        
        if raw_6hr_min:
            settlement_temp = round(raw_6hr_min)
            kalshi_series = cfg.get("kalshi_low", "")
            if kalshi_series:
                brackets = fetch_kalshi_brackets(kalshi_series)
                winning_bracket = None
                for b in brackets:
                    if b['low'] <= settlement_temp < b['high']:
                        winning_bracket = b['range']
                        break
                
                if winning_bracket:
                    settlement_info = f"<div style='color:#22c55e;font-size:1.2em;margin-top:8px;font-weight:700'>6hr MIN: {raw_6hr_min}°F → BUY: {winning_bracket}</div>"
                else:
                    settlement_info = f"<div style='color:#22c55e;font-size:1.2em;margin-top:8px;font-weight:700'>6hr MIN: {raw_6hr_min}°F (Settlement: {settlement_temp}°F)</div>"
    
    st.markdown(f"""
    <div style="background:#161b22;border:1px solid #30363d;border-radius:8px;padding:15px;margin:10px 0">
        <div style="display:flex;justify-content:space-around;text-align:center">
            <div><div style="color:#ef4444;font-size:0.9em;font-weight:700;margin-bottom:8px">CURRENT</div><div style="color:#fff;font-size:1.8em;font-weight:700">{current_temp}°F</div></div>
            <div><div style="color:#f59e0b;font-size:0.9em;font-weight:700;margin-bottom:8px">LOW SETTLEMENT</div>{settlement_info}</div>
            <div><div style="color:#ef4444;font-size:0.9em;font-weight:700;margin-bottom:8px">HIGH</div><div style="color:#ef4444;font-size:1.8em;font-weight:700">{obs_high}°F</div></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

st.subheader("📊 NWS Observations + 6hr Extremes")
if city_selection == "New York City":
    st.caption(f"Station: {cfg['nws']} | Hourly readings")
else:
    st.caption(f"Station: {cfg['nws']} | 5-minute intervals - ONLY 6hr MIN used for settlement")

if readings and full_readings:
    six_hr_map = {}
    for r in full_readings:
        six_hr_map[r['time']] = {'max_6hr': r['max_6hr'], 'min_6hr': r['min_6hr']}
    
    raw_6hr_min = None
    settlement_low = None
    for r in full_readings:
        if r['min_6hr']:
            try:
                min_val = float(r['min_6hr'])
                if raw_6hr_min is None or min_val < raw_6hr_min:
                    raw_6hr_min = min_val
                    settlement_low = round(min_val)
            except:
                pass
    
    low_idx = None
    if city_selection == "New York City":
        low_idx = next((i for i, r in enumerate(readings) if r['temp'] == obs_low), None)
    
    if settlement_low:
        kalshi_series = cfg.get("kalshi_low", "")
        brackets = fetch_kalshi_brackets(kalshi_series) if kalshi_series else []
        winning_bracket = None
        for b in brackets:
            if b['low'] <= settlement_low < b['high']:
                winning_bracket = b['range']
                break
        
        if winning_bracket:
            st.info(f"📊 {len(readings)} readings | 6hr MIN: **{raw_6hr_min}°F** → **BUY: {winning_bracket}**")
        else:
            st.info(f"📊 {len(readings)} readings | 6hr MIN: **{raw_6hr_min}°F** → Settlement: **{settlement_low}°F**")
    else:
        st.info(f"📊 {len(readings)} readings")
    
    for i, r in enumerate(readings):
        time_key = r['time']
        temp = r['temp']
        
        six_hr_data = six_hr_map.get(time_key, {})
        six_hr_max = six_hr_data.get('max_6hr', '')
        six_hr_min = six_hr_data.get('min_6hr', '')
        
        six_hr_display = ""
        if six_hr_max:
            six_hr_display += f"<span style='color:#ef4444;font-weight:700'>6hr↑{six_hr_max}</span> "
        if six_hr_min:
            six_hr_display += f"<span style='color:#22c55e;font-weight:700'>6hr↓{six_hr_min}</span>"
        
        if i == low_idx and city_selection == "New York City":
            row_style = "display:flex;justify-content:space-between;padding:8px;border-radius:4px;background:#2d1f0a;border:2px solid #f59e0b;margin:2px 0"
            temp_style = "color:#fbbf24;font-weight:700;font-size:1.1em"
            label = " ⬅️ HOURLY LOW"
        else:
            row_style = "display:flex;justify-content:space-between;padding:6px 8px;border-bottom:1px solid #30363d"
            temp_style = "color:#fff;font-weight:600"
            label = ""
        
        st.markdown(f"<div style='{row_style}'><span style='color:#9ca3af;min-width:60px;font-weight:600'>{time_key}</span><span style='flex:1;text-align:center;font-size:0.9em'>{six_hr_display}</span><span style='{temp_style}'>{temp}°F{label}</span></div>", unsafe_allow_html=True)
elif readings:
    st.info(f"📊 {len(readings)} readings (6hr data unavailable)")
    low_idx = None
    if city_selection == "New York City":
        low_idx = next((i for i, r in enumerate(readings) if r['temp'] == obs_low), None)
    
    for i, r in enumerate(readings):
        time_key = r['time']
        temp = r['temp']
        
        if i == low_idx and city_selection == "New York City":
            row_style = "display:flex;justify-content:space-between;padding:8px;border-radius:4px;background:#2d1f0a;border:2px solid #f59e0b;margin:2px 0"
            temp_style = "color:#fbbf24;font-weight:700;font-size:1.1em"
            label = " ⬅️ HOURLY LOW"
        else:
            row_style = "display:flex;justify-content:space-between;padding:6px 8px;border-bottom:1px solid #30363d"
            temp_style = "color:#fff;font-weight:600"
            label = ""
        
        st.markdown(f"<div style='{row_style}'><span style='color:#9ca3af;min-width:60px;font-weight:600'>{time_key}</span><span style='{temp_style}'>{temp}°F{label}</span></div>", unsafe_allow_html=True)
else:
    st.warning("⚠️ No data available")

st.divider()

with st.expander("📋 Full NWS Table", expanded=True):
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
        <th rowspan="3">Relative<br/>Humidity</th>
        <th rowspan="3">Wind<br/>Chill<br/>(°F)</th>
        <th rowspan="3">Heat<br/>Index<br/>(°F)</th>
        <th colspan="3" class="temp-header">Pressure</th>
        <th colspan="3" class="temp-header">Precipitation<br/>(in)</th>
        </tr>
        <tr>
        <th rowspan="2">Air</th>
        <th rowspan="2">Dwpt</th>
        <th colspan="2">6 hour</th>
        <th rowspan="2">altimeter<br/>(in)</th>
        <th rowspan="2">sea<br/>level<br/>(mb)</th>
        <th rowspan="2">1 hr</th>
        <th rowspan="2">3 hr</th>
        <th rowspan="2">6 hr</th>
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
            <td colspan="7"></td>
            </tr>"""
        
        table_html += "</tbody></table></div>"
        st.markdown(table_html, unsafe_allow_html=True)
        st.caption(f"Source: https://forecast.weather.gov/data/obhistory/{cfg['nws']}.html")

st.divider()
st.caption("⚠️ **DISCLAIMER:** EDUCATIONAL and EXPERIMENTAL purposes ONLY. NOT financial advice. NOT betting advice.")

st.divider()
eastern = pytz.timezone("US/Eastern")
st.caption(f"Last updated: {datetime.now(eastern).strftime('%I:%M:%S %p ET')}")
