"""
🌡️ TEMP.PY - Temperature Trading Dashboard
SHARK: Find LOCKED settlements → Show CHEAPEST winning bracket → Run GUARDS → BUY or BLOCK
TOM: Tomorrow's NWS forecast → Match brackets → Guards → Opportunities

OWNER MODE: ?owner=true
"""
import streamlit as st
import requests
from datetime import datetime, timedelta
import pytz
import re
from bs4 import BeautifulSoup

st.set_page_config(page_title="🌡️ Temp Trading", page_icon="🌡️", layout="wide")

try:
    OWNER_MODE = "owner" in st.query_params and st.query_params["owner"] == "true"
except:
    OWNER_MODE = False

CITIES = {
    "New York City": {"nws": "KNYC", "kalshi_low": "KXLOWTNYC", "kalshi_high": "KXHIGHNY", "tz": "US/Eastern", "lat": 40.78, "lon": -73.97},
    "Philadelphia": {"nws": "KPHL", "kalshi_low": "KXLOWTPHL", "kalshi_high": "KXHIGHPHIL", "tz": "US/Eastern", "lat": 39.87, "lon": -75.23},
    "Miami": {"nws": "KMIA", "kalshi_low": "KXLOWTMIA", "kalshi_high": "KXHIGHMIA", "tz": "US/Eastern", "lat": 25.80, "lon": -80.29},
    "Los Angeles": {"nws": "KLAX", "kalshi_low": "KXLOWTLAX", "kalshi_high": "KXHIGHLAX", "tz": "US/Pacific", "lat": 33.94, "lon": -118.41},
    "Austin": {"nws": "KAUS", "kalshi_low": "KXLOWTAUS", "kalshi_high": "KXHIGHAUS", "tz": "US/Central", "lat": 30.19, "lon": -97.67},
    "Chicago": {"nws": "KMDW", "kalshi_low": "KXLOWTCHI", "kalshi_high": "KXHIGHCHI", "tz": "US/Central", "lat": 41.79, "lon": -87.75},
    "Denver": {"nws": "KDEN", "kalshi_low": "KXLOWTDEN", "kalshi_high": "KXHIGHDEN", "tz": "US/Mountain", "lat": 39.86, "lon": -104.67},
}

WEATHER_DANGER = ["cold front", "warm front", "frontal passage", "freeze", "hard freeze", "frost", "winter storm", "ice storm", "blizzard", "arctic", "polar vortex", "heat wave", "excessive heat", "heat advisory", "severe thunderstorm", "tornado", "hurricane", "record high", "record low", "rapidly falling", "rapidly rising", "sharply colder", "sharply warmer", "plunging", "soaring"]

PRICE_FLOOR = 20
PRICE_WARN = 40
FORECAST_GAP = 3

if "default_city" not in st.session_state:
    st.session_state.default_city = "New York City"

@st.cache_data(ttl=300)
def fetch_full_nws_recording(station, city_tz_str):
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
                        "min_6hr": cells[9].text.strip()
                    })
            except:
                continue
        
        return readings
    except:
        return []

@st.cache_data(ttl=300)
def fetch_nws_observations(station, city_tz_str):
    url = f"https://api.weather.gov/stations/{station}/observations?limit=500"
    try:
        city_tz = pytz.timezone(city_tz_str)
        resp = requests.get(url, headers={"User-Agent": "Temp/1.0", "Cache-Control": "no-cache"}, timeout=15)
        if resp.status_code != 200:
            return None, None, None, [], None, None, None
        observations = resp.json().get("features", [])
        if not observations:
            return None, None, None, [], None, None, None
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
            return None, None, None, [], None, None, None
        readings.sort(key=lambda x: x["time"], reverse=True)
        current = readings[0]["temp"]
        low = min(r["temp"] for r in readings)
        high = max(r["temp"] for r in readings)
        oldest_time = sorted(readings, key=lambda x: x["time"])[0]["time"] if readings else None
        newest_time = sorted(readings, key=lambda x: x["time"])[-1]["time"] if readings else None
        display_readings = [{"time": r["time"].strftime("%H:%M"), "temp": r["temp"]} for r in readings]
        return current, low, high, display_readings, oldest_time, newest_time, len(readings)
    except:
        return None, None, None, [], None, None, None

@st.cache_data(ttl=300)
def fetch_6hr_settlement(station, city_tz_str):
    url = f"https://forecast.weather.gov/data/obhistory/{station}.html"
    try:
        city_tz = pytz.timezone(city_tz_str)
        today = datetime.now(city_tz).day
        resp = requests.get(url, headers={"User-Agent": "Temp/1.0"}, timeout=15)
        if resp.status_code != 200:
            return None, None, None, None, False, False
        
        soup = BeautifulSoup(resp.text, 'html.parser')
        table = soup.find('table')
        if not table:
            return None, None, None, None, False, False
        
        rows = table.find_all('tr')
        all_6hr_mins, all_6hr_maxs = [], []
        
        for row in rows[3:]:
            cells = row.find_all('td')
            if len(cells) < 10:
                continue
            try:
                date_val = cells[0].text.strip()
                time_val = cells[1].text.strip()
                if date_val and int(date_val) != today:
                    continue
                
                max_6hr = cells[8].text.strip()
                min_6hr = cells[9].text.strip()
                
                if max_6hr:
                    max_val = int(float(max_6hr))
                    hour = int(time_val.replace(":", "")[:2])
                    if hour >= 12:
                        all_6hr_maxs.append((time_val, max_val))
                
                if min_6hr:
                    min_val = int(float(min_6hr))
                    all_6hr_mins.append((time_val, min_val))
            except:
                continue
        
        settlement_low = min(all_6hr_mins, key=lambda x: x[1])[1] if all_6hr_mins else None
        low_time = min(all_6hr_mins, key=lambda x: x[1])[0] if all_6hr_mins else None
        settlement_high = max(all_6hr_maxs, key=lambda x: x[1])[1] if all_6hr_maxs else None
        high_time = max(all_6hr_maxs, key=lambda x: x[1])[0] if all_6hr_maxs else None
        
        is_low_locked = any(int(t.replace(":", "")[:2]) >= 6 for t, _ in all_6hr_mins)
        is_high_locked = any(int(t.replace(":", "")[:2]) >= 18 for t, _ in all_6hr_maxs)
        
        return settlement_low, settlement_high, low_time, high_time, is_low_locked, is_high_locked
    except:
        return None, None, None, None, False, False

@st.cache_data(ttl=300)
def fetch_kalshi_brackets(series_ticker, city_tz_str, is_tomorrow=False):
    url = f"https://api.elections.kalshi.com/trade-api/v2/markets?series_ticker={series_ticker}&status=open"
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code != 200:
            return []
        
        markets = resp.json().get("markets", [])
        if not markets:
            return []
        
        city_tz = pytz.timezone(city_tz_str)
        target_date = datetime.now(city_tz) + (timedelta(days=1) if is_tomorrow else timedelta(days=0))
        date_str = target_date.strftime('%y%b%d').upper()
        
        target_markets = [m for m in markets if date_str in m.get("event_ticker", "").upper()]
        if not target_markets:
            target_markets = [m for m in markets if m.get("event_ticker") == markets[0].get("event_ticker")]
        
        brackets = []
        for m in target_markets:
            title = m.get("title", "")
            ticker = m.get("ticker", "")
            yes_ask = m.get("yes_ask", 0) or 0
            
            low, high, name = None, None, ""
            
            gt_match = re.search(r'>\s*(-?\d+)', title)
            if gt_match:
                threshold = int(gt_match.group(1))
                low = threshold + 1
                high = 999
                name = f">{threshold} ({low}+)"
            
            if low is None:
                lt_match = re.search(r'<\s*(-?\d+)', title)
                if lt_match:
                    threshold = int(lt_match.group(1))
                    high = threshold - 1
                    low = -999
                    name = f"<{threshold} (≤{high})"
            
            if low is None:
                range_match = re.search(r'(-?\d+)\s*to\s*(-?\d+)', title, re.I)
                if range_match:
                    low = int(range_match.group(1))
                    high = int(range_match.group(2))
                    name = f"{low} to {high}"
            
            if low is not None:
                brackets.append({"name": name, "low": low, "high": high, "ask": yes_ask, "ticker": ticker})
        
        return sorted(brackets, key=lambda x: x['ask'])
    except:
        return []

def find_winning_bracket(temp, brackets):
    if temp is None or not brackets:
        return None
    for b in brackets:
        if (b["high"] == 999 and temp >= b["low"]) or (b["low"] == -999 and temp <= b["high"]) or (b["low"] <= temp <= b["high"]):
            return b
    return None

@st.cache_data(ttl=900)
def fetch_nws_forecast(lat, lon):
    try:
        points_resp = requests.get(f"https://api.weather.gov/points/{lat},{lon}", headers={"User-Agent": "Temp/1.0"}, timeout=10)
        if points_resp.status_code != 200:
            return None, []
        
        forecast_url = points_resp.json().get("properties", {}).get("forecast")
        if not forecast_url:
            return None, []
        
        forecast_resp = requests.get(forecast_url, headers={"User-Agent": "Temp/1.0"}, timeout=10)
        if forecast_resp.status_code != 200:
            return None, []
        
        periods = forecast_resp.json().get("properties", {}).get("periods", [])[:4]
        
        tonight_low = None
        for p in periods:
            if not p.get("isDaytime", True):
                tonight_low = p.get("temperature")
                break
        
        warnings = []
        for p in periods:
            text = (p.get("detailedForecast", "") + " " + p.get("shortForecast", "")).lower()
            for word in WEATHER_DANGER:
                if word in text and word not in [w.split("'")[1] for w in warnings if "'" in w]:
                    warnings.append(f"⛈️ '{word.upper()}' in {p.get('name')}")
        
        return tonight_low, warnings
    except:
        return None, []

def run_guards(settlement, market_type, ask, nws_forecast, weather_warnings):
    guards = []
    blocked = False
    
    if weather_warnings:
        for w in weather_warnings:
            guards.append(w)
            blocked = True
    
    if ask <= PRICE_FLOOR:
        guards.append(f"💰 PRICE BLOCK: {ask}¢ TOO CHEAP - market knows something!")
        blocked = True
    elif ask <= PRICE_WARN:
        guards.append(f"💰 PRICE WARN: {ask}¢ suspiciously cheap")
    
    if nws_forecast and settlement:
        gap = abs(settlement - nws_forecast)
        if gap >= FORECAST_GAP:
            guards.append(f"🌡️ FORECAST: NWS {nws_forecast}°F vs settlement {settlement}°F - {gap}° gap!")
            blocked = True
        else:
            guards.append(f"✅ FORECAST: NWS {nws_forecast}°F within {FORECAST_GAP}° of settlement")
    
    return guards, blocked

@st.cache_data(ttl=1800)
def fetch_tomorrow_forecast(lat, lon):
    try:
        points_resp = requests.get(f"https://api.weather.gov/points/{lat},{lon}", headers={"User-Agent": "Temp/1.0"}, timeout=10)
        forecast_url = points_resp.json().get("properties", {}).get("forecast")
        forecast_resp = requests.get(forecast_url, headers={"User-Agent": "Temp/1.0"}, timeout=10)
        periods = forecast_resp.json().get("properties", {}).get("periods", [])
        
        tomorrow_low, tomorrow_high = None, None
        for p in periods:
            if not any(day in p.get("name", "").lower() for day in ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]):
                continue
            temp = p.get("temperature")
            if temp is None:
                continue
            if not p.get("isDaytime", True) and tomorrow_low is None:
                tomorrow_low = round(temp)
            elif p.get("isDaytime", True) and tomorrow_high is None:
                tomorrow_high = round(temp)
            if tomorrow_low and tomorrow_high:
                break
        return tomorrow_low, tomorrow_high
    except:
        return None, None

st.title("🌡️ Temperature Trading Dashboard")
st.caption("⚠️ EXPERIMENTAL - EDUCATIONAL PURPOSES ONLY - NOT FINANCIAL OR BETTING ADVICE")
if OWNER_MODE:
    st.caption("🔑 OWNER MODE")
else:
    st.caption("Public View")

with st.sidebar:
    st.header("⚙️ Settings")
    
    city_selection = st.selectbox("Default City for NWS Table", list(CITIES.keys()), index=list(CITIES.keys()).index(st.session_state.default_city))
    
    if st.button("Set as Default"):
        st.session_state.default_city = city_selection
        st.success(f"✅ {city_selection} set as default!")
    
    st.divider()
    mode = st.radio("Mode", ["🦈 SHARK (Today)", "🦅 TOM (Tomorrow)", "📊 Both"])
    st.divider()
    
    show_all_cities = st.checkbox("Show All Cities", value=True)
    
    st.divider()
    if st.button("🔄 Refresh"):
        st.cache_data.clear()
        st.rerun()

selected_cities = list(CITIES.keys()) if show_all_cities else [city_selection]

if mode in ["🦈 SHARK (Today)", "📊 Both"]:
    st.header("🦈 SHARK - Locked Settlement Scanner")
    
    if OWNER_MODE:
        st.subheader(f"📊 Recent NWS Observations + 6hr Extremes - {city_selection}")
        
        cfg = CITIES[city_selection]
        current_temp, obs_low, obs_high, readings, oldest_time, newest_time, reading_count = fetch_nws_observations(cfg["nws"], cfg["tz"])
        full_readings = fetch_full_nws_recording(cfg["nws"], cfg["tz"])
        settlement_low, settlement_high, low_time, high_time, is_low_locked, is_high_locked = fetch_6hr_settlement(cfg["nws"], cfg["tz"])
        
        if oldest_time and newest_time:
            st.caption(f"📅 Data: {oldest_time.strftime('%H:%M')} to {newest_time.strftime('%H:%M')} local | {reading_count} readings")
        
        if settlement_low is not None:
            lock_status = "🔒 LOCKED" if is_low_locked else "⏳ WAITING"
            st.markdown(f"<div style='background:#1a2e1a;border:2px solid #22c55e;border-radius:8px;padding:12px;margin-bottom:15px;text-align:center'><span style='color:#22c55e;font-weight:700;font-size:1.1em'>📍 SETTLEMENT LOW: {settlement_low}°F @ {low_time} {lock_status}</span></div>", unsafe_allow_html=True)
        
        if current_temp:
            st.markdown(f"""
            <div style="background:#161b22;border:1px solid #30363d;border-radius:8px;padding:15px;margin:10px 0">
                <div style="display:flex;justify-content:space-around;text-align:center">
                    <div><div style="color:#6b7280;font-size:0.8em">CURRENT</div><div style="color:#fff;font-size:1.8em;font-weight:700">{current_temp}°F</div></div>
                    <div><div style="color:#6b7280;font-size:0.8em">HIGH</div><div style="color:#ef4444;font-size:1.8em;font-weight:700">{obs_high}°F</div></div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        with st.expander("📊 Recent NWS Observations", expanded=True):
            if readings and full_readings:
                six_hr_map = {}
                for r in full_readings:
                    time_key = r['time']
                    six_hr_map[time_key] = {
                        'max_6hr': r['max_6hr'],
                        'min_6hr': r['min_6hr']
                    }
                
                low_idx = next((i for i, r in enumerate(readings) if r['temp'] == obs_low), None)
                
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
                    
                    if i == low_idx:
                        row_style = "display:flex;justify-content:space-between;padding:8px;border-radius:4px;background:#2d1f0a;border:2px solid #f59e0b;margin:2px 0"
                        temp_style = "color:#fbbf24;font-weight:700;font-size:1.1em"
                        label = " ⬅️ HOURLY LOW"
                    else:
                        row_style = "display:flex;justify-content:space-between;padding:6px 8px;border-bottom:1px solid #30363d"
                        temp_style = "color:#fff;font-weight:600"
                        label = ""
                    
                    st.markdown(f"<div style='{row_style}'><span style='color:#9ca3af;min-width:60px;font-weight:600'>{time_key}</span><span style='flex:1;text-align:center;font-size:0.9em'>{six_hr_display}</span><span style='{temp_style}'>{temp}°F{label}</span></div>", unsafe_allow_html=True)
        
        st.divider()
        with st.expander("📋 Full NWS Table", expanded=False):
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
            <th rowspan="3">Time<br/>(est)</th>
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
    
    for city in selected_cities:
        cfg = CITIES[city]
        low_6hr, high_6hr, low_time, high_time, low_locked, high_locked = fetch_6hr_settlement(cfg["nws"], cfg["tz"])
        current_temp, obs_low, obs_high, _, _, _, _ = fetch_nws_observations(cfg["nws"], cfg["tz"])
        nws_forecast, weather_warnings = fetch_nws_forecast(cfg["lat"], cfg["lon"])
        
        if cfg["kalshi_low"] and low_6hr and low_locked:
            brackets = fetch_kalshi_brackets(cfg["kalshi_low"], cfg["tz"])
            winner = find_winning_bracket(low_6hr, brackets)
            
            if winner:
                guards, blocked = run_guards(low_6hr, "LOW", winner["ask"], nws_forecast, weather_warnings)
                
                with st.expander(f"🔒 {city} LOW: {low_6hr}°F @ {low_time} → {winner['name']} @ {winner['ask']}¢", expanded=not blocked):
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Settlement", f"{low_6hr}°F @ {low_time}")
                        st.metric("Current", f"{current_temp}°F" if current_temp else "—")
                    with col2:
                        st.metric("Bracket", winner["name"])
                        st.metric("Ask", f"{winner['ask']}¢")
                    with col3:
                        edge = 100 - winner["ask"]
                        st.metric("Edge", f"{edge}¢")
                        profit = (edge / 100) * 20
                        st.metric("Profit (20x)", f"${profit:.2f}")
                    
                    st.divider()
                    if blocked:
                        st.error("🛡️ GUARDS BLOCKED - DO NOT BUY")
                    else:
                        st.success("✅ GUARDS PASSED - SAFE TO BUY")
                    
                    for g in guards:
                        st.write(g)
        
        if cfg["kalshi_high"] and high_6hr and high_locked:
            brackets = fetch_kalshi_brackets(cfg["kalshi_high"], cfg["tz"])
            winner = find_winning_bracket(high_6hr, brackets)
            
            if winner:
                guards, blocked = run_guards(high_6hr, "HIGH", winner["ask"], None, weather_warnings)
                
                with st.expander(f"🔒 {city} HIGH: {high_6hr}°F @ {high_time} → {winner['name']} @ {winner['ask']}¢", expanded=not blocked):
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Settlement", f"{high_6hr}°F @ {high_time}")
                        st.metric("Current", f"{current_temp}°F" if current_temp else "—")
                    with col2:
                        st.metric("Bracket", winner["name"])
                        st.metric("Ask", f"{winner['ask']}¢")
                    with col3:
                        edge = 100 - winner["ask"]
                        st.metric("Edge", f"{edge}¢")
                        profit = (edge / 100) * 20
                        st.metric("Profit (20x)", f"${profit:.2f}")
                    
                    st.divider()
                    if blocked:
                        st.error("🛡️ GUARDS BLOCKED - DO NOT BUY")
                    else:
                        st.success("✅ GUARDS PASSED - SAFE TO BUY")
                    
                    for g in guards:
                        st.write(g)

if mode in ["🦅 TOM (Tomorrow)", "📊 Both"]:
    st.header("🦅 TOM - Tomorrow Scanner")
    
    for city in selected_cities:
        cfg = CITIES[city]
        forecast_low, forecast_high = fetch_tomorrow_forecast(cfg["lat"], cfg["lon"])
        _, weather_warnings = fetch_nws_forecast(cfg["lat"], cfg["lon"])
        
        if cfg["kalshi_low"] and forecast_low:
            brackets = fetch_kalshi_brackets(cfg["kalshi_low"], cfg["tz"], is_tomorrow=True)
            match = find_winning_bracket(forecast_low, brackets)
            
            if match and match["ask"] <= 20:
                guards, blocked = run_guards(None, "LOW", match["ask"], None, weather_warnings)
                
                with st.expander(f"🦅 {city} LOW: Forecast {forecast_low}°F → {match['name']} @ {match['ask']}¢", expanded=not blocked):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("NWS Forecast", f"{forecast_low}°F")
                        st.metric("Bracket", match["name"])
                    with col2:
                        st.metric("Ask", f"{match['ask']}¢")
                        edge = 100 - match["ask"]
                        st.metric("Edge", f"{edge}¢")
                    
                    if blocked:
                        st.error("⚠️ BLOCKED")
                    else:
                        st.success("✅ SAFE")
                    for g in guards:
                        st.write(g)
        
        if cfg["kalshi_high"] and forecast_high:
            brackets = fetch_kalshi_brackets(cfg["kalshi_high"], cfg["tz"], is_tomorrow=True)
            match = find_winning_bracket(forecast_high, brackets)
            
            if match and match["ask"] <= 20:
                guards, blocked = run_guards(None, "HIGH", match["ask"], None, weather_warnings)
                
                with st.expander(f"🦅 {city} HIGH: Forecast {forecast_high}°F → {match['name']} @ {match['ask']}¢", expanded=not blocked):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("NWS Forecast", f"{forecast_high}°F")
                        st.metric("Bracket", match["name"])
                    with col2:
                        st.metric("Ask", f"{match['ask']}¢")
                        edge = 100 - match["ask"]
                        st.metric("Edge", f"{edge}¢")
                    
                    if blocked:
                        st.error("⚠️ BLOCKED")
                    else:
                        st.success("✅ SAFE")
                    for g in guards:
                        st.write(g)

st.divider()

st.caption("⚠️ **DISCLAIMER:** This application is for EDUCATIONAL and EXPERIMENTAL purposes ONLY. This is NOT financial advice. This is NOT betting advice. Always verify data independently before making any decisions. Past performance does not guarantee future results. Weather is inherently unpredictable. Use at your own risk.")

st.divider()

with st.expander("📖 How to Use This App", expanded=False):
    st.markdown("""
    ### 🦈 SHARK Mode (Today)
    **Purpose:** Find locked settlement temperatures and matching Kalshi brackets
    
    **How it works:**
    1. App pulls 6-hour aggregate data from NWS obhistory
    2. LOW locks after 06:53 local time (overnight minimum captured)
    3. HIGH locks after 18:53 local time (afternoon maximum captured)
    4. App finds the cheapest winning bracket based on locked settlement
    5. Guards check for weather warnings, suspicious pricing, and forecast alignment
    
    **What the metrics mean:**
    - **Settlement**: The locked 6hr Min/Max temperature from NWS
    - **Bracket**: The Kalshi market range that contains the settlement temp
    - **Ask**: Current price to buy YES contract (pays $1 if correct)
    - **Edge**: Profit potential (100¢ - Ask price)
    - **Profit (20x)**: Estimated profit on 20 contracts
    
    ### 🦅 TOM Mode (Tomorrow)
    **Purpose:** Find tomorrow's NWS forecast and match to cheap brackets
    
    **How it works:**
    1. Fetches tomorrow's forecast from NWS
    2. Finds brackets ≤20¢ that match the forecast
    3. Runs guards for weather warnings and pricing
    
    ### 🛡️ Guards System
    **BLOCKED** means do NOT trade - something is wrong:
    - **Weather warnings**: Fronts, storms, extreme events make temps unpredictable
    - **Price too cheap** (≤20¢): Market knows something you don't
    - **Forecast gap** (≥3°): NWS forecast disagrees with settlement
    
    **PASSED** means guards found no red flags (but still do your own research)
    
    ### 📊 Full NWS Recording (Owner Mode)
    Shows complete observation history since midnight with:
    - **Date**: Day of month
    - **Time (est)**: Local observation time
    - **Air Temp (°F)**: Hourly temperature reading
    - **6hr Max**: Maximum temp in last 6 hours (red, what Kalshi uses for HIGH)
    - **6hr Min**: Minimum temp in last 6 hours (blue, what Kalshi uses for LOW)
    
    ### ⚠️ Important Notes
    - This app is for **educational and experimental purposes only**
    - NOT financial advice, NOT betting advice
    - Always verify data independently before making decisions
    - Past performance does not guarantee future results
    - Weather is inherently unpredictable
    """)

st.divider()
eastern = pytz.timezone("US/Eastern")
st.caption(f"Last updated: {datetime.now(eastern).strftime('%I:%M:%S %p ET')}")
