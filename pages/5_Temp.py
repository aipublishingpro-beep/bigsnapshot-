"""
🌡️ TEMP.PY - Temperature Trading Dashboard
SHARK: Find LOCKED settlements → Show CHEAPEST winning bracket → Run GUARDS → BUY or BLOCK
TOM: Tomorrow's NWS forecast → Match brackets → Guards → Opportunities

OWNER MODE: ?owner=true
"""
import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta
import pytz
import re
from bs4 import BeautifulSoup

st.set_page_config(page_title="🌡️ Temp Trading", page_icon="🌡️", layout="wide")

try:
    OWNER_MODE = st.experimental_get_query_params().get("owner", [""])[0] == "true"
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

@st.cache_data(ttl=300)
def fetch_full_nws_recording(station, city_tz_str):
    """Fetch complete NWS observation history with ALL columns"""
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
                time_val = cells[1].text.strip()
                
                if date_val and int(date_val) != today:
                    continue
                
                wind = cells[2].text.strip()
                vis = cells[3].text.strip()
                weather = cells[4].text.strip()
                sky = cells[5].text.strip() if len(cells) > 5 else ""
                air_temp = cells[6].text.strip() if len(cells) > 6 else ""
                dwpt = cells[7].text.strip() if len(cells) > 7 else ""
                max_6hr = cells[8].text.strip() if len(cells) > 8 else ""
                min_6hr = cells[9].text.strip() if len(cells) > 9 else ""
                
                readings.append({
                    "date": date_val if date_val else today,
                    "time": time_val,
                    "wind": wind,
                    "vis": vis,
                    "weather": weather,
                    "sky": sky,
                    "air_temp": air_temp,
                    "dwpt": dwpt,
                    "max_6hr": max_6hr,
                    "min_6hr": min_6hr
                })
            except:
                continue
        
        return readings
    except:
        return []

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

@st.cache_data(ttl=300)
def fetch_current_temp(station):
    try:
        url = f"https://api.weather.gov/stations/{station}/observations/latest"
        resp = requests.get(url, headers={"User-Agent": "Temp/1.0"}, timeout=10)
        if resp.status_code != 200:
            return None
        temp_c = resp.json().get("properties", {}).get("temperature", {}).get("value")
        return round(temp_c * 9/5 + 32, 1) if temp_c else None
    except:
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
    mode = st.radio("Mode", ["🦈 SHARK (Today)", "🦅 TOM (Tomorrow)", "📊 Both"])
    st.divider()
    selected_cities = st.multiselect("Cities", list(CITIES.keys()), default=["New York City", "Miami", "Los Angeles", "Austin", "Chicago", "Philadelphia", "Denver"])
    st.divider()
    if st.button("🔄 Refresh"):
        st.cache_data.clear()
        st.rerun()

if not selected_cities:
    st.warning("Select cities")
    st.stop()

if mode in ["🦈 SHARK (Today)", "📊 Both"]:
    st.header("🦈 SHARK - Locked Settlement Scanner")
    
    if OWNER_MODE:
        st.subheader("📊 Full NWS Recording (All Cities)")
        city_choice = st.selectbox("Select City for Full Recording", selected_cities)
        
        if city_choice:
            cfg = CITIES[city_choice]
            full_readings = fetch_full_nws_recording(cfg["nws"], cfg["tz"])
            if full_readings:
                table_html = """
                <style>
                .nws-full-table { width: 100%; border-collapse: collapse; font-family: 'Courier New', monospace; font-size: 11px; }
                .nws-full-table th { background: #2d3748; color: #fff; padding: 8px 6px; text-align: center; border: 1px solid #4a5568; font-weight: 600; font-size: 10px; }
                .nws-full-table td { padding: 6px 4px; text-align: center; border: 1px solid #4a5568; background: #1a202c; }
                .nws-full-table tr:hover td { background: #2d3748; }
                .max-6hr-cell { color: #fc8181; font-weight: 700; }
                .min-6hr-cell { color: #63b3ed; font-weight: 700; }
                .temp-cell { color: #fff; font-weight: 600; }
                </style>
                <table class='nws-full-table'>
                <thead><tr>
                <th>Date</th><th>Time<br/>(est)</th><th>Wind<br/>(mph)</th><th>Vis.<br/>(mi.)</th><th>Weather</th><th>Sky<br/>Cond.</th>
                <th>Air<br/>Temp</th><th>Dwpt</th><th>6 hour<br/>Max.</th><th>6 hour<br/>Min.</th>
                </tr></thead><tbody>
                """
                
                for r in readings:
                    max_display = f"<span class='max-6hr-cell'>{r['max_6hr']}</span>" if r['max_6hr'] else ""
                    min_display = f"<span class='min-6hr-cell'>{r['min_6hr']}</span>" if r['min_6hr'] else ""
                    air_display = f"<span class='temp-cell'>{r['air_temp']}</span>" if r['air_temp'] else ""
                    
                    table_html += f"""<tr>
                    <td>{r['date']}</td><td>{r['time']}</td><td>{r['wind']}</td><td>{r['vis']}</td>
                    <td>{r['weather']}</td><td>{r['sky']}</td><td>{air_display}</td><td>{r['dwpt']}</td>
                    <td>{max_display}</td><td>{min_display}</td>
                    </tr>"""
                
                table_html += "</tbody></table>"
                st.markdown(table_html, unsafe_allow_html=True)
                st.caption(f"Source: https://forecast.weather.gov/data/obhistory/{cfg['nws']}.html")
        
        st.divider()
    
    for city in selected_cities:
        cfg = CITIES[city]
        low_6hr, high_6hr, low_time, high_time, low_locked, high_locked = fetch_6hr_settlement(cfg["nws"], cfg["tz"])
        current = fetch_current_temp(cfg["nws"])
        nws_forecast, weather_warnings = fetch_nws_forecast(cfg["lat"], cfg["lon"])
        
        if OWNER_MODE:
            full_readings = fetch_full_nws_recording(cfg["nws"], cfg["tz"])
            if full_readings:
                with st.expander(f"📊 {city} - Full NWS Recording (Since Midnight)", expanded=True):
                    city_tz = pytz.timezone(cfg["tz"])
                    today = datetime.now(city_tz).day
                    
                    table_html = """
                    <style>
                    .nws-table { width: 100%; border-collapse: collapse; font-family: 'Courier New', monospace; font-size: 12px; }
                    .nws-table th { background: #2d3748; color: #fff; padding: 10px 8px; text-align: center; border: 1px solid #4a5568; font-weight: 600; }
                    .nws-table td { padding: 8px; text-align: center; border: 1px solid #4a5568; background: #1a202c; }
                    .nws-table tr:hover td { background: #2d3748; }
                    .time-col { color: #a0aec0; font-weight: 600; }
                    .temp-col { color: #fff; font-weight: 700; font-size: 14px; }
                    .max-6hr { color: #fc8181; font-weight: 700; }
                    .min-6hr { color: #63b3ed; font-weight: 700; }
                    </style>
                    <table class='nws-table'><thead><tr><th>Date</th><th>Time (est)</th><th>Air Temp (°F)</th><th>6hr Max</th><th>6hr Min</th></tr></thead><tbody>
                    """
                    
                    for r in full_readings:
                        max_display = f"<span class='max-6hr'>{r['max_6hr']}</span>" if r['max_6hr'] else ""
                        min_display = f"<span class='min-6hr'>{r['min_6hr']}</span>" if r['min_6hr'] else ""
                        table_html += f"<tr><td class='time-col'>{today}</td><td class='time-col'>{r['time']}</td><td class='temp-col'>{r['temp']}</td><td>{max_display}</td><td>{min_display}</td></tr>"
                    
                    table_html += "</tbody></table>"
                    st.markdown(table_html, unsafe_allow_html=True)
                    st.caption(f"Source: https://forecast.weather.gov/data/obhistory/{cfg['nws']}.html")
        
        if cfg["kalshi_low"] and low_6hr and low_locked:
            brackets = fetch_kalshi_brackets(cfg["kalshi_low"], cfg["tz"])
            winner = find_winning_bracket(low_6hr, brackets)
            
            if winner:
                guards, blocked = run_guards(low_6hr, "LOW", winner["ask"], nws_forecast, weather_warnings)
                
                with st.expander(f"🔒 {city} LOW: {low_6hr}°F @ {low_time} → {winner['name']} @ {winner['ask']}¢", expanded=not blocked):
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Settlement", f"{low_6hr}°F @ {low_time}")
                        st.metric("Current", f"{current}°F" if current else "—")
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
        
        if high_6hr and high_locked:
            brackets = fetch_kalshi_brackets(cfg["kalshi_high"], cfg["tz"])
            winner = find_winning_bracket(high_6hr, brackets)
            
            if winner:
                guards, blocked = run_guards(high_6hr, "HIGH", winner["ask"], None, weather_warnings)
                
                with st.expander(f"🔒 {city} HIGH: {high_6hr}°F @ {high_time} → {winner['name']} @ {winner['ask']}¢", expanded=not blocked):
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Settlement", f"{high_6hr}°F @ {high_time}")
                        st.metric("Current", f"{current}°F" if current else "—")
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
        
        if forecast_high:
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
