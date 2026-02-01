"""
🌡️ TEMP.PY - City View with NWS Observations + SHARK Mode
Shows hourly readings + 6hr extremes for selected city + automated trading signals
"""
import streamlit as st
import requests
from datetime import datetime
import pytz
from bs4 import BeautifulSoup
import json
import hashlib
import base64
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding as asym_padding
from cryptography.hazmat.backends import default_backend

st.set_page_config(page_title="🌡️ Temp Trading", page_icon="🌡️", layout="wide")

try:
    OWNER_MODE = "owner" in st.query_params and st.query_params["owner"] == "true"
except:
    OWNER_MODE = False

CITIES = {
    "Austin": {"nws": "KAUS", "tz": "US/Central", "lat": 30.19, "lon": -97.67},
    "Chicago": {"nws": "KMDW", "tz": "US/Central", "lat": 41.79, "lon": -87.75},
    "Denver": {"nws": "KDEN", "tz": "US/Mountain", "lat": 39.86, "lon": -104.67},
    "Los Angeles": {"nws": "KLAX", "tz": "US/Pacific", "lat": 33.94, "lon": -118.41},
    "Miami": {"nws": "KMIA", "tz": "US/Eastern", "lat": 25.80, "lon": -80.29},
    "New York City": {"nws": "KNYC", "tz": "US/Eastern", "lat": 40.78, "lon": -73.97},
    "Philadelphia": {"nws": "KPHL", "tz": "US/Eastern", "lat": 39.87, "lon": -75.23},
}

if "default_city" not in st.session_state:
    st.session_state.default_city = "New York City"

# Kalshi authentication
def create_kalshi_signature(timestamp, method, path, body=""):
    """Generate Kalshi API signature with PSS padding"""
    try:
        api_key = st.secrets.get("KALSHI_API_KEY", "")
        private_key_str = st.secrets.get("KALSHI_PRIVATE_KEY", "")
        
        if not api_key or not private_key_str:
            return None, None
        
        msg_string = f"{timestamp}{method}{path}{body}"
        
        private_key = serialization.load_pem_private_key(
            private_key_str.encode(),
            password=None,
            backend=default_backend()
        )
        
        signature = private_key.sign(
            msg_string.encode('utf-8'),
            asym_padding.PSS(
                mgf=asym_padding.MGF1(hashes.SHA256()),
                salt_length=asym_padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        
        return api_key, base64.b64encode(signature).decode('utf-8')
    except:
        return None, None

@st.cache_data(ttl=300)
def fetch_full_nws_recording(station, city_tz_str):
    """Fetch complete NWS observation table with 6hr extremes"""
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
    """Fetch hourly observations from NWS API"""
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
        
        readings.reverse()
        
        return current, low, high, readings
    except:
        return None, None, None, []

def check_settlement_lock(full_readings, city_tz_str):
    """Check if LOW or HIGH settlement is locked based on 6hr data appearance"""
    try:
        city_tz = pytz.timezone(city_tz_str)
        now = datetime.now(city_tz)
        
        low_locked = False
        high_locked = False
        low_settlement = None
        high_settlement = None
        
        for r in full_readings:
            time_str = r['time']
            hour, minute = map(int, time_str.split(':'))
            
            # LOW locks at 06:53+ when 6hr min appears
            if hour == 6 and minute >= 53 and r['min_6hr']:
                low_locked = True
                try:
                    low_settlement = int(r['min_6hr'])
                except:
                    pass
            
            # HIGH locks at 18:53+ when 6hr max appears
            if hour == 18 and minute >= 53 and r['max_6hr']:
                high_locked = True
                try:
                    high_settlement = int(r['max_6hr'])
                except:
                    pass
        
        return low_locked, high_locked, low_settlement, high_settlement
    except:
        return False, False, None, None

@st.cache_data(ttl=300)
def fetch_kalshi_markets(city_name):
    """Fetch today's temperature markets for a city"""
    try:
        timestamp = str(int(datetime.now().timestamp() * 1000))
        path = "/trade-api/v2/markets"
        method = "GET"
        
        api_key, signature = create_kalshi_signature(timestamp, method, path)
        if not api_key or not signature:
            return []
        
        headers = {
            "KALSHI-ACCESS-KEY": api_key,
            "KALSHI-ACCESS-SIGNATURE": signature,
            "KALSHI-ACCESS-TIMESTAMP": timestamp,
            "Content-Type": "application/json"
        }
        
        today_str = datetime.now().strftime("%Y-%m-%d")
        city_search = city_name.upper().replace(" ", "")
        
        params = {
            "event_ticker": f"HIGHTEMP-{city_search}-{today_str}",
            "limit": 200,
            "status": "open"
        }
        
        resp = requests.get(
            "https://api.elections.kalshi.com/trade-api/v2/markets",
            headers=headers,
            params=params,
            timeout=15
        )
        
        if resp.status_code != 200:
            return []
        
        markets = resp.json().get("markets", [])
        return markets
    except:
        return []

def parse_bracket(ticker):
    """Extract temperature range from ticker like HIGHTEMP-NYC-24-01-31-T60.5"""
    try:
        parts = ticker.split("-T")
        if len(parts) != 2:
            return None, None
        temp_str = parts[1]
        temp = float(temp_str)
        return temp, temp + 1
    except:
        return None, None

def find_winning_bracket(markets, settlement_temp):
    """Find the cheapest bracket that contains settlement temp"""
    winning_brackets = []
    
    for m in markets:
        ticker = m.get("ticker", "")
        yes_ask = m.get("yes_ask")
        
        if yes_ask is None:
            continue
        
        low, high = parse_bracket(ticker)
        if low is not None and low <= settlement_temp < high:
            winning_brackets.append({
                "ticker": ticker,
                "ask": yes_ask / 100,
                "low": low,
                "high": high
            })
    
    if not winning_brackets:
        return None
    
    return min(winning_brackets, key=lambda x: x["ask"])

@st.cache_data(ttl=600)
def fetch_nws_forecast(lat, lon):
    """Fetch NWS forecast for today's high/low"""
    try:
        point_url = f"https://api.weather.gov/points/{lat},{lon}"
        resp = requests.get(point_url, headers={"User-Agent": "Temp/1.0"}, timeout=10)
        if resp.status_code != 200:
            return None, None, []
        
        forecast_url = resp.json()["properties"]["forecast"]
        resp2 = requests.get(forecast_url, headers={"User-Agent": "Temp/1.0"}, timeout=10)
        if resp2.status_code != 200:
            return None, None, []
        
        periods = resp2.json()["properties"]["periods"]
        today_high = None
        today_low = None
        warnings = []
        
        for p in periods[:3]:
            name = p.get("name", "")
            temp = p.get("temperature")
            forecast = p.get("detailedForecast", "").lower()
            
            if "today" in name.lower() or "this afternoon" in name.lower():
                today_high = temp
            if "tonight" in name.lower():
                today_low = temp
            
            # Check for weather warnings
            warning_keywords = ["cold front", "warm front", "storm", "severe", "warning", "advisory"]
            for keyword in warning_keywords:
                if keyword in forecast:
                    warnings.append(keyword)
        
        return today_high, today_low, warnings
    except:
        return None, None, []

def run_shark_guards(settlement_temp, bracket, forecast_temp, warnings):
    """Run 3 guardrails: weather warnings, price floor, forecast gap"""
    guards = {
        "weather_warnings": {"pass": True, "reason": ""},
        "price_floor": {"pass": True, "reason": ""},
        "forecast_gap": {"pass": True, "reason": ""}
    }
    
    # Guard 1: Weather warnings
    if warnings:
        guards["weather_warnings"]["pass"] = False
        guards["weather_warnings"]["reason"] = f"Active warnings: {', '.join(set(warnings))}"
    
    # Guard 2: Price floor (≤20¢ = market knows something)
    if bracket["ask"] <= 0.20:
        guards["price_floor"]["pass"] = False
        guards["price_floor"]["reason"] = f"Ask price {bracket['ask']:.0%} ≤ 20¢ - market may know something"
    
    # Guard 3: Forecast gap (≥3° difference)
    if forecast_temp and abs(forecast_temp - settlement_temp) >= 3:
        guards["forecast_gap"]["pass"] = False
        guards["forecast_gap"]["reason"] = f"Forecast {forecast_temp}°F differs by {abs(forecast_temp - settlement_temp)}° from settlement"
    
    all_pass = all(g["pass"] for g in guards.values())
    return all_pass, guards

st.title("🌡️ Temperature Trading Dashboard")
st.caption("⚠️ EXPERIMENTAL - EDUCATIONAL PURPOSES ONLY")

# Mode selector
mode = st.radio("Mode", ["📊 City View", "🦈 SHARK Mode"], horizontal=True)

col1, col2 = st.columns([3, 1])
with col1:
    city_selection = st.selectbox("📍 Select City", list(CITIES.keys()), index=list(CITIES.keys()).index(st.session_state.default_city))
with col2:
    if st.button("⭐ Set as Default", use_container_width=True):
        st.session_state.default_city = city_selection
        st.success(f"✅ {city_selection} saved!")

st.divider()

cfg = CITIES[city_selection]

# Fetch data
current_temp, obs_low, obs_high, readings = fetch_nws_observations(cfg["nws"], cfg["tz"])
full_readings = fetch_full_nws_recording(cfg["nws"], cfg["tz"])

if mode == "🦈 SHARK Mode":
    st.header("🦈 SHARK Mode - Automated Trading Signals")
    
    if not full_readings:
        st.error("⚠️ No NWS data available for SHARK analysis")
    else:
        low_locked, high_locked, low_settlement, high_settlement = check_settlement_lock(full_readings, cfg["tz"])
        
        if not low_locked and not high_locked:
            st.info("⏳ Waiting for settlement lock... (LOW at 06:53+, HIGH at 18:53+)")
        else:
            # Determine which settlement is locked
            if low_locked and low_settlement:
                settlement_type = "LOW"
                settlement_temp = low_settlement
                market_search = f"LOWTEMP-{city_selection.upper().replace(' ', '')}"
            elif high_locked and high_settlement:
                settlement_type = "HIGH"
                settlement_temp = high_settlement
                market_search = f"HIGHTEMP-{city_selection.upper().replace(' ', '')}"
            else:
                st.warning("Settlement detected but no valid temperature")
                st.stop()
            
            st.success(f"🔒 {settlement_type} Settlement Locked: {settlement_temp}°F")
            
            # Fetch Kalshi markets
            with st.spinner("Fetching Kalshi markets..."):
                markets = fetch_kalshi_markets(city_selection)
            
            if not markets:
                st.error("❌ No Kalshi markets found")
            else:
                # Find winning bracket
                winning = find_winning_bracket(markets, settlement_temp)
                
                if not winning:
                    st.error("❌ No winning bracket found")
                else:
                    # Fetch forecast and check guards
                    forecast_high, forecast_low, warnings = fetch_nws_forecast(cfg["lat"], cfg["lon"])
                    forecast_temp = forecast_high if settlement_type == "HIGH" else forecast_low
                    
                    all_pass, guards = run_shark_guards(settlement_temp, winning, forecast_temp, warnings)
                    
                    # Display decision
                    if all_pass:
                        st.markdown(f"""
                        <div style="background:#064e3b;border:2px solid #10b981;border-radius:8px;padding:20px;margin:20px 0">
                            <div style="color:#10b981;font-size:2em;font-weight:700;text-align:center">✅ BUY SIGNAL</div>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown(f"""
                        <div style="background:#7f1d1d;border:2px solid #ef4444;border-radius:8px;padding:20px;margin:20px 0">
                            <div style="color:#ef4444;font-size:2em;font-weight:700;text-align:center">🚫 BLOCKED</div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    # Trade details
                    st.subheader("📊 Trade Details")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Settlement Temp", f"{settlement_temp}°F")
                    with col2:
                        st.metric("Winning Bracket", f"{winning['low']}-{winning['high']}°F")
                    with col3:
                        edge = (1 - winning['ask']) * 100
                        st.metric("Edge", f"{edge:.0f}%", f"Ask: {winning['ask']:.0%}")
                    
                    st.caption(f"Ticker: {winning['ticker']}")
                    
                    # Guards status
                    st.subheader("🛡️ Guardrails")
                    for guard_name, guard_data in guards.items():
                        if guard_data["pass"]:
                            st.success(f"✅ {guard_name.replace('_', ' ').title()}")
                        else:
                            st.error(f"🚫 {guard_name.replace('_', ' ').title()}: {guard_data['reason']}")

else:  # City View mode
    st.header(f"📍 {city_selection}")
    
    if current_temp:
        st.markdown(f"""
        <div style="background:#161b22;border:1px solid #30363d;border-radius:8px;padding:15px;margin:10px 0">
            <div style="display:flex;justify-content:space-around;text-align:center">
                <div><div style="color:#6b7280;font-size:0.8em">CURRENT</div><div style="color:#fff;font-size:1.8em;font-weight:700">{current_temp}°F</div></div>
                <div><div style="color:#6b7280;font-size:0.8em">LOW</div><div style="color:#3b82f6;font-size:1.8em;font-weight:700">{obs_low}°F</div></div>
                <div><div style="color:#6b7280;font-size:0.8em">HIGH</div><div style="color:#ef4444;font-size:1.8em;font-weight:700">{obs_high}°F</div></div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    st.subheader("📊 NWS Observations + 6hr Extremes")
    if city_selection == "New York City":
        st.caption(f"Station: {cfg['nws']} | Today's hourly readings from midnight to now")
    else:
        st.caption(f"Station: {cfg['nws']} | Today's readings (5-min intervals) from midnight to now")
    
    if readings and full_readings:
        six_hr_map = {}
        for r in full_readings:
            time_key = r['time']
            six_hr_map[time_key] = {
                'max_6hr': r['max_6hr'],
                'min_6hr': r['min_6hr']
            }
        
        low_idx = next((i for i, r in enumerate(readings) if r['temp'] == obs_low), None)
        
        st.info(f"📊 Showing {len(readings)} readings")
        
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
    else:
        st.warning("⚠️ No data available")
    
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
st.caption("⚠️ **DISCLAIMER:** This application is for EDUCATIONAL and EXPERIMENTAL purposes ONLY. This is NOT financial advice. This is NOT betting advice.")

st.divider()
eastern = pytz.timezone("US/Eastern")
st.caption(f"Last updated: {datetime.now(eastern).strftime('%I:%M:%S %p ET')}")
