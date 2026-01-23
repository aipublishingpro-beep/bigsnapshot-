import streamlit as st
import requests
from datetime import datetime, timedelta
import pytz
import re
from bs4 import BeautifulSoup

st.set_page_config(page_title="Temp Edge Finder", page_icon="🌡️", layout="wide")

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
    "Austin": {"high": "KXHIGHAUS", "low": "KXLOWTAUS", "station": "KAUS", "lat": 30.19, "lon": -97.67},
    "Chicago": {"high": "KXHIGHCHI", "low": "KXLOWTCHI", "station": "KMDW", "lat": 41.79, "lon": -87.75},
    "Denver": {"high": "KXHIGHDEN", "low": "KXLOWTDEN", "station": "KDEN", "lat": 39.86, "lon": -104.67},
    "Los Angeles": {"high": "KXHIGHLAX", "low": "KXLOWTLAX", "station": "KLAX", "lat": 33.94, "lon": -118.41},
    "Miami": {"high": "KXHIGHMIA", "low": "KXLOWTMIA", "station": "KMIA", "lat": 25.80, "lon": -80.29},
    "New York City": {"high": "KXHIGHNY", "low": "KXLOWTNYC", "station": "KNYC", "lat": 40.78, "lon": -73.97},
    "Philadelphia": {"high": "KXHIGHPHL", "low": "KXLOWTPHL", "station": "KPHL", "lat": 39.87, "lon": -75.23},
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
            brackets.append({"range": range_txt, "mid": mid, "yes": yes_price, "ticker": ticker,
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
            return {}, None, None
        soup = BeautifulSoup(resp.text, 'html.parser')
        table = soup.find('table')
        if not table:
            return {}, None, None
        rows = table.find_all('tr')
        extremes = {}
        today = datetime.now(eastern).day
        all_6hr_maxes = []
        all_6hr_mins = []
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
                        if max_val is not None:
                            all_6hr_maxes.append(max_val)
                        if min_val is not None:
                            all_6hr_mins.append(min_val)
                        time_key = time_val.replace(":", "")[:4]
                        time_key = time_key[:2] + ":" + time_key[2:]
                        extremes[time_key] = {"max": max_val, "min": min_val}
                except:
                    continue
        official_high = max(all_6hr_maxes) if all_6hr_maxes else None
        official_low = min(all_6hr_mins) if all_6hr_mins else None
        return extremes, official_high, official_low
    except:
        return {}, None, None

@st.cache_data(ttl=120)
def fetch_nws_observations(station):
    url = f"https://api.weather.gov/stations/{station}/observations"
    try:
        resp = requests.get(url, headers={"User-Agent": "TempEdge/3.0"}, timeout=15)
        if resp.status_code != 200:
            return None, None, None, []
        observations = resp.json().get("features", [])
        if not observations:
            return None, None, None, []
        today = datetime.now(eastern).date()
        readings = []
        for obs in observations:
            props = obs.get("properties", {})
            timestamp_str = props.get("timestamp", "")
            temp_c = props.get("temperature", {}).get("value")
            if not timestamp_str or temp_c is None:
                continue
            try:
                ts = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
                ts_local = ts.astimezone(eastern)
                if ts_local.date() == today:
                    temp_f = round(temp_c * 9/5 + 32, 1)
                    readings.append({"time": ts_local, "temp": temp_f})
            except:
                continue
        if not readings:
            return None, None, None, []
        readings.sort(key=lambda x: x["time"], reverse=True)
        current = readings[0]["temp"]
        low = min(r["temp"] for r in readings)
        high = max(r["temp"] for r in readings)
        display_readings = [{"time": r["time"].strftime("%H:%M"), "temp": r["temp"]} for r in readings]
        return current, low, high, display_readings
    except:
        return None, None, None, []

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

def render_brackets_with_actual(brackets, actual_temp, temp_type):
    if not brackets:
        st.error("Could not load brackets")
        return
    winning_bracket = None
    winner_data = None
    for b in brackets:
        if temp_in_bracket(actual_temp, b['range']):
            winning_bracket = b['range']
            winner_data = b
            break
    market_fav = max(brackets, key=lambda b: b['yes'])
    st.caption(f"Market favorite: {market_fav['range']} @ {market_fav['yes']:.0f}¢")
    edge_cents = market_fav['yes'] - winner_data['yes'] if winner_data else 0
    for b in brackets:
        is_winner = b['range'] == winning_bracket
        is_market_fav = b['range'] == market_fav['range']
        if is_winner:
            if edge_cents >= 50:
                box_style = "background:linear-gradient(135deg,#4a1010,#2d1f0a);border:2px solid #dc2626;box-shadow:0 0 20px rgba(220,38,38,0.5);border-radius:6px;padding:12px 14px;margin:8px 0"
                name_style = "color:#f87171;font-weight:700;font-size:1.05em"
                icon = " 🚨🚨"
            elif edge_cents >= 30:
                box_style = "background:linear-gradient(135deg,#451a03,#2d1f0a);border:2px solid #f59e0b;box-shadow:0 0 18px rgba(245,158,11,0.5);border-radius:6px;padding:12px 14px;margin:8px 0"
                name_style = "color:#fbbf24;font-weight:700;font-size:1.05em"
                icon = " 🚨"
            elif edge_cents >= 15:
                box_style = "background:linear-gradient(135deg,#3d3510,#1a1408);border:2px solid #ca8a04;box-shadow:0 0 12px rgba(202,138,4,0.4);border-radius:6px;padding:12px 14px;margin:8px 0"
                name_style = "color:#eab308;font-weight:700;font-size:1.05em"
                icon = " ⚠️"
            else:
                box_style = "background:linear-gradient(135deg,#2d1f0a,#1a1408);border:2px solid #f59e0b;box-shadow:0 0 15px rgba(245,158,11,0.4);border-radius:6px;padding:12px 14px;margin:8px 0"
                name_style = "color:#fbbf24;font-weight:700;font-size:1.05em"
                icon = " 🎯"
            model_txt = "ACTUAL"
        else:
            if is_market_fav:
                box_style = "background:#1a1a2e;border:1px solid #4a4a6a;border-radius:6px;padding:10px 12px;margin:5px 0"
                icon = " ⭐"
            else:
                box_style = "background:#161b22;border:1px solid #30363d;border-radius:6px;padding:10px 12px;margin:5px 0"
                icon = ""
            name_style = "color:#e5e7eb;font-weight:500"
            model_txt = "—"
        html = f'''<div style="{box_style}"><div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px">
            <span style="{name_style}">{b['range']}{icon}</span>
            <div style="display:flex;gap:12px;align-items:center">
                <span style="color:#f59e0b">Kalshi {b['yes']:.0f}¢</span>
                <span style="color:#9ca3af">{model_txt}</span>
            </div></div></div>'''
        st.markdown(html, unsafe_allow_html=True)
    if winner_data:
        if winner_data['yes'] >= 99:
            card = f'<div style="background:#1a2e1a;border:2px solid #22c55e;border-radius:10px;padding:18px;text-align:center;margin-top:12px"><div style="color:#22c55e;font-size:1.1em;font-weight:700">✅ Market settled — outcome confirmed</div><div style="color:#fff;font-size:1.2em;margin-top:8px">{winning_bracket}</div></div>'
        else:
            potential_profit = 100 - winner_data['yes']
            edge_score_line = ""
            if edge_cents >= 50:
                edge_score_line = f'<div style="color:#f87171;font-size:1em;font-weight:700;margin-top:6px">EDGE SCORE: +{edge_cents:.0f} (Market broken)</div>'
            elif edge_cents >= 30:
                edge_score_line = f'<div style="color:#fbbf24;font-size:1em;font-weight:700;margin-top:6px">EDGE SCORE: +{edge_cents:.0f} (Major mispricing)</div>'
            elif edge_cents >= 15:
                edge_score_line = f'<div style="color:#eab308;font-size:1em;font-weight:700;margin-top:6px">EDGE SCORE: +{edge_cents:.0f} (Edge present)</div>'
            if edge_cents >= 50:
                card_style = "background:linear-gradient(135deg,#4a1010,#2d0a0a);border:2px solid #dc2626;box-shadow:0 0 25px rgba(220,38,38,0.6)"
            elif edge_cents >= 30:
                card_style = "background:linear-gradient(135deg,#451a03,#2d1f0a);border:2px solid #f59e0b;box-shadow:0 0 22px rgba(245,158,11,0.5)"
            elif edge_cents >= 15:
                card_style = "background:linear-gradient(135deg,#3d3510,#1a1408);border:2px solid #ca8a04;box-shadow:0 0 18px rgba(202,138,4,0.4)"
            else:
                card_style = "background:linear-gradient(135deg,#2d1f0a,#1a1408);border:2px solid #f59e0b;box-shadow:0 0 20px rgba(245,158,11,0.5)"
            card = f'<div style="{card_style};border-radius:10px;padding:18px;text-align:center;margin-top:12px"><div style="color:#fbbf24;font-size:0.9em;font-weight:600">🌡️ ACTUAL {temp_type}: {actual_temp}°F</div>{edge_score_line}<div style="color:#fff;font-size:1.3em;font-weight:700;margin:10px 0">{winning_bracket}</div><div style="color:#4ade80;font-size:0.9em">Potential profit: +{potential_profit:.0f}¢ per contract</div><a href="{winner_data["url"]}" target="_blank" style="background:linear-gradient(135deg,#f59e0b,#d97706);color:#000;padding:12px 28px;border-radius:6px;text-decoration:none;font-weight:700;display:inline-block;margin-top:10px;box-shadow:0 4px 12px rgba(245,158,11,0.4)">BUY YES</a></div>'
        st.markdown(card, unsafe_allow_html=True)

# ========== HEADER ==========
st.title("🌡️ TEMP EDGE FINDER")
st.caption(f"Live NWS Observations + Kalshi | {now.strftime('%b %d, %Y %I:%M %p ET')}")

query_params = st.query_params
default_city = query_params.get("city", "New York City")
if default_city not in CITY_LIST:
    default_city = "New York City"

# Owner check
OWNER_KEY = "edge2026"
is_owner = query_params.get("key") == OWNER_KEY

# Owner sidebar tips
if is_owner:
    with st.sidebar:
        st.markdown("""
        <div style="background:#1a2e1a;border:1px solid #22c55e;border-radius:8px;padding:12px;margin-bottom:15px">
            <div style="color:#22c55e;font-weight:700;margin-bottom:8px">🔒 EDGE TIPS</div>
            <div style="color:#c9d1d9;font-size:0.85em;line-height:1.5">
                <b>LOW (Safer):</b><br>
                • Wait for ✅ CONFIRMED bar<br>
                • Shows after 1 rising reading<br>
                • Sun up = no going back<br><br>
                <b>HIGH (Riskier):</b><br>
                • Wait for ✅ CONFIRMED bar<br>
                • Or wait for 18:51 6hr confirm<br><br>
                <b>6hr Extremes:</b><br>
                • 06:51 & 12:51 bracket LOW<br>
                • 12:51 & 18:51 bracket HIGH<br>
                • Official NWS confirmation
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

if st.button("⭐ Set as Default City", use_container_width=False):
    st.query_params["city"] = city
    st.success(f"✓ Bookmark this page to save {city} as default!")

current_temp, obs_low, obs_high, readings = fetch_nws_observations(cfg.get("station", "KNYC"))
extremes_6hr, official_high, official_low = fetch_nws_6hr_extremes(cfg.get("station", "KNYC")) if is_owner else ({}, None, None)

if current_temp:
    # Build display with official extremes for owner
    if is_owner and (official_high or official_low):
        st.markdown(f"""
        <div style="background:#161b22;border:1px solid #30363d;border-radius:8px;padding:15px;margin:10px 0">
            <div style="text-align:center;margin-bottom:10px">
                <span style="color:#6b7280;font-size:0.75em">Data from NWS Station: <strong style="color:#22c55e">{cfg.get('station', 'N/A')}</strong></span>
            </div>
            <div style="display:flex;justify-content:space-around;text-align:center;flex-wrap:wrap;gap:15px">
                <div><div style="color:#6b7280;font-size:0.8em">CURRENT</div><div style="color:#fff;font-size:1.5em;font-weight:700">{current_temp}°F</div></div>
                <div><div style="color:#3b82f6;font-size:0.8em">TODAY'S LOW</div><div style="color:#3b82f6;font-size:1.5em;font-weight:700">{obs_low}°F</div>{f'<div style="color:#22c55e;font-size:0.7em">6hr Official: {official_low:.0f}°F</div>' if official_low else ''}</div>
                <div><div style="color:#ef4444;font-size:0.8em">{"TODAY'S HIGH" if now.hour >= 15 else "TODAY'S HIGH SO FAR"}</div><div style="color:#ef4444;font-size:1.5em;font-weight:700">{obs_high}°F</div>{f'<div style="color:#22c55e;font-size:0.7em">6hr Official: {official_high:.0f}°F</div>' if official_high else ''}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style="background:#161b22;border:1px solid #30363d;border-radius:8px;padding:15px;margin:10px 0">
            <div style="text-align:center;margin-bottom:10px">
                <span style="color:#6b7280;font-size:0.75em">Data from NWS Station: <strong style="color:#22c55e">{cfg.get('station', 'N/A')}</strong></span>
            </div>
            <div style="display:flex;justify-content:space-around;text-align:center;flex-wrap:wrap;gap:15px">
                <div><div style="color:#6b7280;font-size:0.8em">CURRENT</div><div style="color:#fff;font-size:1.5em;font-weight:700">{current_temp}°F</div></div>
                <div><div style="color:#3b82f6;font-size:0.8em">TODAY'S LOW</div><div style="color:#3b82f6;font-size:1.5em;font-weight:700">{obs_low}°F</div></div>
                <div><div style="color:#ef4444;font-size:0.8em">{"TODAY'S HIGH" if now.hour >= 15 else "TODAY'S HIGH SO FAR"}</div><div style="color:#ef4444;font-size:1.5em;font-weight:700">{obs_high}°F</div></div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    if readings:
        with st.expander("📊 Recent NWS Observations", expanded=True):
            display_list = readings if is_owner else readings[:8]
            
            # Find reversal indices
            min_temp = min(r['temp'] for r in display_list)
            low_reversal_idx = None
            for i, r in enumerate(display_list):
                if r['temp'] == min_temp:
                    low_reversal_idx = i
                    break
            
            max_temp = max(r['temp'] for r in display_list)
            high_reversal_idx = None
            if now.hour >= 12:
                for i, r in enumerate(display_list):
                    reading_hour = int(r['time'].split(':')[0])
                    if r['temp'] == max_temp and reading_hour >= 12:
                        high_reversal_idx = i
                        break
            
            # Confirmation: first reading AFTER reversal that proves trend reversed (OWNER ONLY)
            low_confirm_idx = None
            if is_owner and low_reversal_idx is not None and low_reversal_idx >= 1:
                if display_list[low_reversal_idx - 1]['temp'] > min_temp:
                    low_confirm_idx = low_reversal_idx - 1
            
            high_confirm_idx = None
            if is_owner and high_reversal_idx is not None and high_reversal_idx >= 1:
                if display_list[high_reversal_idx - 1]['temp'] < max_temp:
                    high_confirm_idx = high_reversal_idx - 1
            
            for i, r in enumerate(display_list):
                time_key = r['time']
                six_hr_display = ""
                if is_owner:
                    six_hr_max = extremes_6hr.get(time_key, {}).get('max')
                    six_hr_min = extremes_6hr.get(time_key, {}).get('min')
                    if six_hr_max is not None or six_hr_min is not None:
                        parts = []
                        if six_hr_max is not None:
                            parts.append(f"<span style='color:#ef4444'>6hr↑{six_hr_max:.0f}°</span>")
                        if six_hr_min is not None:
                            parts.append(f"<span style='color:#3b82f6'>6hr↓{six_hr_min:.0f}°</span>")
                        six_hr_display = " ".join(parts)
                
                # Show CONFIRMED LOW bar (OWNER ONLY)
                if is_owner and low_confirm_idx is not None and i == low_confirm_idx:
                    st.markdown('<div style="display:flex;justify-content:center;align-items:center;padding:8px;border-radius:4px;background:linear-gradient(135deg,#166534,#14532d);border:2px solid #22c55e;margin:4px 0"><span style="color:#4ade80;font-weight:700">✅ CONFIRMED LOW — BUY NOW</span></div>', unsafe_allow_html=True)
                
                # Show CONFIRMED HIGH bar (OWNER ONLY)
                if is_owner and high_confirm_idx is not None and i == high_confirm_idx:
                    st.markdown('<div style="display:flex;justify-content:center;align-items:center;padding:8px;border-radius:4px;background:linear-gradient(135deg,#166534,#14532d);border:2px solid #22c55e;margin:4px 0"><span style="color:#4ade80;font-weight:700">✅ CONFIRMED HIGH — BUY NOW</span></div>', unsafe_allow_html=True)
                
                # Row styling
                if i == low_reversal_idx:
                    row_style = "display:flex;justify-content:space-between;align-items:center;padding:6px 8px;border-radius:4px;background:linear-gradient(135deg,#2d1f0a,#1a1408);border:1px solid #f59e0b;margin:2px 0"
                    time_style = "color:#fbbf24;font-weight:600"
                    temp_style = "color:#fbbf24;font-weight:700"
                    label = " ↩️ LOW"
                elif i == high_reversal_idx:
                    row_style = "display:flex;justify-content:space-between;align-items:center;padding:6px 8px;border-radius:4px;background:linear-gradient(135deg,#2d0a0a,#1a0808);border:1px solid #ef4444;margin:2px 0"
                    time_style = "color:#f87171;font-weight:600"
                    temp_style = "color:#f87171;font-weight:700"
                    label = " ↩️ HIGH"
                else:
                    row_style = "display:flex;justify-content:space-between;align-items:center;padding:4px 8px;border-bottom:1px solid #30363d"
                    time_style = "color:#9ca3af"
                    temp_style = "color:#fff;font-weight:600"
                    label = ""
                
                st.markdown(f"<div style='{row_style}'><span style='{time_style};min-width:50px'>{r['time']}</span><span style='flex:1;text-align:center;font-size:0.85em'>{six_hr_display}</span><span style='{temp_style}'>{r['temp']}°F{label}</span></div>", unsafe_allow_html=True)
else:
    st.warning("⚠️ Could not fetch NWS observations")

st.markdown("---")
col_high, col_low = st.columns(2)

with col_high:
    st.subheader("☀️ HIGH TEMP")
    hour = now.hour
    if obs_high:
        st.metric("📈 High So Far", f"{obs_high}°F")
        brackets_high = fetch_kalshi_brackets(cfg.get("high", "KXHIGHNY"))
        if hour >= 15:
            st.caption("✅ High likely locked in (after 3 PM)")
            render_brackets_with_actual(brackets_high, obs_high, "HIGH")
        else:
            st.caption(f"⏳ Too early — HIGH peaks 12-5 PM. Check back later.")
            if brackets_high:
                market_fav = max(brackets_high, key=lambda b: b['yes'])
                st.caption(f"Market favorite: {market_fav['range']} @ {market_fav['yes']:.0f}¢")
                for b in brackets_high:
                    is_fav = b['range'] == market_fav['range']
                    box_style = "background:#1a1a2e;border:1px solid #f59e0b;border-radius:6px;padding:10px 12px;margin:5px 0" if is_fav else "background:#161b22;border:1px solid #30363d;border-radius:6px;padding:10px 12px;margin:5px 0"
                    icon = " ⭐" if is_fav else ""
                    st.markdown(f'<div style="{box_style}"><div style="display:flex;justify-content:space-between;align-items:center"><span style="color:#e5e7eb">{b["range"]}{icon}</span><span style="color:#f59e0b">Kalshi {b["yes"]:.0f}¢</span></div></div>', unsafe_allow_html=True)
                st.markdown(f'<div style="text-align:center;margin-top:12px"><a href="{market_fav["url"]}" target="_blank" style="background:linear-gradient(135deg,#f59e0b,#d97706);color:#000;padding:12px 28px;border-radius:6px;text-decoration:none;font-weight:700;display:inline-block;box-shadow:0 4px 12px rgba(245,158,11,0.4)">BUY MARKET FAVORITE</a></div>', unsafe_allow_html=True)
    else:
        st.error("Could not fetch observations")

with col_low:
    st.subheader("🌙 LOW TEMP")
    hour = now.hour
    if obs_low:
        st.metric("📉 Today's Low", f"{obs_low}°F")
        brackets_low = fetch_kalshi_brackets(cfg.get("low", "KXLOWTNYC"))
        if hour >= 6:
            st.caption("✅ Low locked in (after 6 AM)")
            render_brackets_with_actual(brackets_low, obs_low, "LOW")
        else:
            st.caption(f"⏳ Low may still drop (before 6 AM)")
            if brackets_low:
                market_fav = max(brackets_low, key=lambda b: b['yes'])
                st.caption(f"Market favorite: {market_fav['range']} @ {market_fav['yes']:.0f}¢")
                for b in brackets_low:
                    is_fav = b['range'] == market_fav['range']
                    box_style = "background:#1a1a2e;border:1px solid #f59e0b;border-radius:6px;padding:10px 12px;margin:5px 0" if is_fav else "background:#161b22;border:1px solid #30363d;border-radius:6px;padding:10px 12px;margin:5px 0"
                    icon = " ⭐" if is_fav else ""
                    st.markdown(f'<div style="{box_style}"><div style="display:flex;justify-content:space-between;align-items:center"><span style="color:#e5e7eb">{b["range"]}{icon}</span><span style="color:#f59e0b">Kalshi {b["yes"]:.0f}¢</span></div></div>', unsafe_allow_html=True)
                st.markdown(f'<div style="text-align:center;margin-top:12px"><a href="{market_fav["url"]}" target="_blank" style="background:linear-gradient(135deg,#f59e0b,#d97706);color:#000;padding:12px 28px;border-radius:6px;text-decoration:none;font-weight:700;display:inline-block;box-shadow:0 4px 12px rgba(245,158,11,0.4)">BUY MARKET FAVORITE</a></div>', unsafe_allow_html=True)
    else:
        st.error("Could not fetch observations")

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
            bg = "#1a1a2e" if "night" in name.lower() or "tonight" in name.lower() else "#1f2937"
            temp_color = "#3b82f6" if "night" in name.lower() or "tonight" in name.lower() else "#ef4444"
            st.markdown(f'<div style="background:{bg};border:1px solid #30363d;border-radius:8px;padding:12px;text-align:center"><div style="color:#9ca3af;font-size:0.8em;font-weight:600">{name}</div><div style="color:{temp_color};font-size:1.8em;font-weight:700">{temp}°{unit}</div><div style="color:#6b7280;font-size:0.75em;margin-top:5px">{short}</div></div>', unsafe_allow_html=True)
else:
    st.caption("Could not load NWS forecast")

st.markdown("---")
st.markdown('<div style="background:linear-gradient(90deg,#d97706,#f59e0b);padding:10px 15px;border-radius:8px;margin-bottom:20px;text-align:center"><b style="color:#000">🧪 EXPERIMENTAL</b> <span style="color:#000">— Temperature Edge Finder v3.5</span></div>', unsafe_allow_html=True)

with st.expander("❓ How to Use This App"):
    docs = """
**🌡️ What This App Does**

Compares actual NWS temperature observations against Kalshi prediction market prices to find edge opportunities.

**⏰ When to Check**

• **LOW Temperature**: Usually bottoms out between 4-7 AM. Look for the ↩️ REVERSAL in observations — that confirms the low is set.
• **HIGH Temperature**: Usually peaks between 12-5 PM. Once you see temps dropping after the peak, the high is locked.

**🚨 Severity Indicators**

• 🚨🚨 **EXTREME** (50+ cents) — Red glow, "Market broken"
• 🚨 **BIG** (30-49 cents) — Amber glow, "Major mispricing"  
• ⚠️ **MODERATE** (15-29 cents) — Gold highlight, "Edge present"
• 🎯 **NONE** (<15 cents) — Standard display

**⚠️ Important Notes**

• This is NOT financial advice
• Weather can change — especially HIGH temps before 3 PM
• Always verify on Kalshi before trading
"""
    if is_owner:
        docs += """

**📊 6-Hour Extremes (Owner Only)**

The observations show **6hr↑** (6-hour max) and **6hr↓** (6-hour min) from official NWS METAR reports at synoptic times (00Z, 06Z, 12Z, 18Z). These bracket the true daily high/low.

**✅ Confirmation Bars (Owner Only)**

Green CONFIRMED bars appear immediately after the first reading that proves reversal:
• LOW confirmed = next reading is HIGHER than the low
• HIGH confirmed = next reading is LOWER than the high

This is the safest earliest signal to trade.
"""
    st.markdown(docs)

st.markdown('<div style="color:#6b7280;font-size:0.75em;text-align:center;margin-top:30px;padding:0 20px">⚠️ For entertainment and educational purposes only. This tool displays observed temperature data alongside Kalshi market prices. It does not constitute financial advice. Kalshi settles markets using official weather stations, which may differ slightly from NWS observations shown here. Always verify market details on Kalshi before trading.</div>', unsafe_allow_html=True)
st.markdown('<div style="color:#6b7280;font-size:0.75em;text-align:center;margin-top:10px;padding:0 20px">Questions or feedback? DM me on X: @AIPublishingPro</div>', unsafe_allow_html=True)
