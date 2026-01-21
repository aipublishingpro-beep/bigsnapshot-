import streamlit as st
import requests
from datetime import datetime, timedelta
import pytz
import re

st.set_page_config(page_title="Temp Edge Finder", page_icon="🌡️", layout="wide")

st.markdown("""
<style>
.stApp {background-color: #0d1117;}
div[data-testid="stMarkdownContainer"] p {color: #c9d1d9;}
</style>
""", unsafe_allow_html=True)

eastern = pytz.timezone("US/Eastern")
now = datetime.now(eastern)

CITY_CONFIG = {
    "Austin": {"high": "KXHIGHAUS", "low": "KXLOWTAUS", "station": "KAUS", "lat": 30.19, "lon": -97.67},
    "Chicago": {"high": "KXHIGHCHI", "low": "KXLOWTCHI", "station": "KORD", "lat": 41.79, "lon": -87.75},
    "Denver": {"high": "KXHIGHDEN", "low": "KXLOWTDEN", "station": "KDEN", "lat": 39.86, "lon": -104.67},
    "Los Angeles": {"high": "KXHIGHLAX", "low": "KXLOWTLAX", "station": "KLAX", "lat": 33.94, "lon": -118.41},
    "Miami": {"high": "KXHIGHMIA", "low": "KXLOWTMIA", "station": "KMIA", "lat": 25.80, "lon": -80.29},
    "New York City": {"high": "KXHIGHNY", "low": "KXLOWTNYC", "station": "KNYC", "lat": 40.78, "lon": -73.97},
    "Philadelphia": {"high": "KXHIGHPHL", "low": "KXLOWTPHL", "station": "KPHL", "lat": 39.87, "lon": -75.23},
}

CITY_LIST = sorted(CITY_CONFIG.keys())

def extract_range_text(market):
    subtitle = market.get("subtitle", "")
    title = market.get("title", "")
    txt = title + " " + subtitle
    
    range_hyphen = re.search(r'(\d+)\s*-\s*(\d+)', txt)
    range_to = re.search(r'(\d+)\s*to\s*(\d+)', txt, re.IGNORECASE)
    
    if range_hyphen:
        return f"{range_hyphen.group(1)}° to {range_hyphen.group(2)}°"
    if range_to:
        return f"{range_to.group(1)}° to {range_to.group(2)}°"
    
    below_pattern = re.search(r'[<≤]\s*(\d+)|(\d+)\s*or\s*below|below\s*(\d+)', txt, re.IGNORECASE)
    if below_pattern:
        num = below_pattern.group(1) or below_pattern.group(2) or below_pattern.group(3)
        return f"{num}° or below"
    
    above_pattern = re.search(r'[>≥]\s*(\d+)|(\d+)\s*or\s*above|above\s*(\d+)', txt, re.IGNORECASE)
    if above_pattern:
        num = above_pattern.group(1) or above_pattern.group(2) or above_pattern.group(3)
        return f"{num}° or above"
    
    nums = re.findall(r'(\d+)', txt)
    if len(nums) >= 2:
        return f"{nums[0]}° to {nums[1]}°"
    elif len(nums) == 1:
        if any(w in txt.lower() for w in ['below', 'under', 'less', '<']):
            return f"{nums[0]}° or below"
        else:
            return f"{nums[0]}° or above"
    
    return subtitle if subtitle else "Unknown"

def get_bracket_bounds(range_str):
    tl = range_str.lower()
    nums = re.findall(r'(\d+)', range_str)
    
    if not nums:
        return 0, 100
    
    if "below" in tl or "under" in tl:
        return -999, int(nums[0]) + 0.5
    elif "above" in tl or "over" in tl:
        return int(nums[0]) - 0.5, 999
    elif len(nums) >= 2:
        return int(nums[0]) - 0.5, int(nums[1]) + 0.5
    else:
        return int(nums[0]) - 0.5, int(nums[0]) + 0.5

def temp_in_bracket(temp, range_str):
    """Check if temperature falls within bracket"""
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
            range_txt = extract_range_text(m)
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
            
            brackets.append({
                "range": range_txt,
                "mid": mid,
                "yes": yes_price,
                "ticker": ticker,
                "url": f"https://kalshi.com/markets/{series_ticker.lower()}/{ticker.lower()}" if ticker else "#"
            })
        
        brackets.sort(key=lambda x: x['mid'] or 0)
        return brackets
    except:
        return None

@st.cache_data(ttl=120)
def fetch_nws_observations(station):
    """Fetch today's hourly observations from NWS"""
    url = f"https://api.weather.gov/stations/{station}/observations"
    try:
        resp = requests.get(url, headers={"User-Agent": "TempEdge/3.0"}, timeout=15)
        if resp.status_code != 200:
            return None, None, None, []
        
        observations = resp.json().get("features", [])
        if not observations:
            return None, None, None, []
        
        # Get today's date in local timezone
        today = datetime.now(eastern).date()
        
        temps = []
        readings = []
        
        for obs in observations:
            props = obs.get("properties", {})
            timestamp_str = props.get("timestamp", "")
            temp_c = props.get("temperature", {}).get("value")
            
            if not timestamp_str or temp_c is None:
                continue
            
            # Parse timestamp
            try:
                ts = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
                ts_local = ts.astimezone(eastern)
                
                # Only include today's readings
                if ts_local.date() == today:
                    temp_f = round(temp_c * 9/5 + 32, 1)
                    temps.append(temp_f)
                    readings.append({
                        "time": ts_local.strftime("%H:%M"),
                        "temp": temp_f
                    })
            except:
                continue
        
        if not temps:
            return None, None, None, []
        
        current = temps[0] if temps else None
        low = min(temps)
        high = max(temps)
        
        return current, low, high, readings[:12]  # Last 12 readings
        
    except Exception as e:
        return None, None, None, []

def render_brackets_with_actual(brackets, actual_temp, temp_type):
    """Render brackets highlighting the actual winning bracket"""
    if not brackets:
        st.error("Could not load brackets")
        return
    
    # Find which bracket the actual temp falls into
    winning_bracket = None
    for b in brackets:
        if temp_in_bracket(actual_temp, b['range']):
            winning_bracket = b['range']
            break
    
    market_fav = max(brackets, key=lambda b: b['yes'])
    st.caption(f"Market favorite: {market_fav['range']} @ {market_fav['yes']:.0f}¢")
    
    for b in brackets:
        is_winner = b['range'] == winning_bracket
        is_market_fav = b['range'] == market_fav['range']
        
        # Calculate edge: if this is the actual winner, edge = 100 - kalshi price
        if is_winner:
            edge = 100 - b['yes']
            box_style = "background:linear-gradient(135deg,#2d1f0a,#1a1408);border:2px solid #f59e0b;box-shadow:0 0 15px rgba(245,158,11,0.4);border-radius:6px;padding:12px 14px;margin:8px 0"
            name_style = "color:#fbbf24;font-weight:700;font-size:1.05em"
            edge_color = "#fbbf24"
            icon = " 🎯"
            model_txt = "ACTUAL"
        else:
            edge = 0 - b['yes']  # Would lose full amount
            if is_market_fav:
                box_style = "background:#1a1a2e;border:1px solid #4a4a6a;border-radius:6px;padding:10px 12px;margin:5px 0"
                icon = " ⭐"
            else:
                box_style = "background:#161b22;border:1px solid #30363d;border-radius:6px;padding:10px 12px;margin:5px 0"
                icon = ""
            name_style = "color:#e5e7eb;font-weight:500"
            edge_color = "#6b7280"
            model_txt = "—"
        
        html = f'''<div style="{box_style}">
            <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px">
                <span style="{name_style}">{b['range']}{icon}</span>
                <div style="display:flex;gap:12px;align-items:center">
                    <span style="color:#f59e0b">Kalshi {b['yes']:.0f}¢</span>
                    <span style="color:#9ca3af">{model_txt}</span>
                </div>
            </div>
        </div>'''
        st.markdown(html, unsafe_allow_html=True)
    
    # Show actual temp and winning bracket
    if winning_bracket:
        winner_data = next((b for b in brackets if b['range'] == winning_bracket), None)
        if winner_data:
            potential_profit = 100 - winner_data['yes']
            card = f'''
            <div style="background:linear-gradient(135deg,#2d1f0a,#1a1408);border:2px solid #f59e0b;border-radius:10px;padding:18px;text-align:center;margin-top:12px;box-shadow:0 0 20px rgba(245,158,11,0.5)">
                <div style="color:#fbbf24;font-size:0.9em;font-weight:600">🌡️ ACTUAL {temp_type}: {actual_temp}°F</div>
                <div style="color:#fff;font-size:1.3em;font-weight:700;margin:10px 0">{winning_bracket}</div>
                <div style="color:#4ade80;font-size:0.9em">Potential profit: +{potential_profit:.0f}¢ per contract</div>
                <a href="{winner_data['url']}" target="_blank" style="background:linear-gradient(135deg,#f59e0b,#d97706);color:#000;padding:12px 28px;border-radius:6px;text-decoration:none;font-weight:700;display:inline-block;margin-top:10px;box-shadow:0 4px 12px rgba(245,158,11,0.4)">BUY YES</a>
            </div>'''
            st.markdown(card, unsafe_allow_html=True)

# ========== HEADER ==========
st.markdown("""
<div style="background:linear-gradient(90deg,#d97706,#f59e0b);padding:10px 15px;border-radius:8px;margin-bottom:20px;text-align:center">
<b style="color:#000">🧪 EXPERIMENTAL</b> <span style="color:#000">— Temperature Edge Finder v3.0 (Actual Observations)</span>
</div>
""", unsafe_allow_html=True)

st.title("🌡️ TEMP EDGE FINDER")
st.caption(f"Live NWS Observations + Kalshi | {now.strftime('%b %d, %Y %I:%M %p ET')}")

c1, c2 = st.columns([4, 1])
with c1:
    city = st.selectbox("📍 Select City", CITY_LIST, index=CITY_LIST.index("New York City"))
with c2:
    cfg = CITY_CONFIG.get(city, {})
    nws_url = f"https://forecast.weather.gov/MapClick.php?lat={cfg.get('lat', 40.78)}&lon={cfg.get('lon', -73.97)}"
    st.markdown(f"<a href='{nws_url}' target='_blank' style='display:block;background:#3b82f6;color:#fff;padding:8px;border-radius:6px;text-align:center;text-decoration:none;font-weight:500;margin-top:25px'>📡 NWS</a>", unsafe_allow_html=True)

# Fetch actual observations
current_temp, obs_low, obs_high, readings = fetch_nws_observations(cfg.get("station", "KNYC"))

# Display current conditions
if current_temp:
    st.markdown(f"""
    <div style="background:#161b22;border:1px solid #30363d;border-radius:8px;padding:15px;margin:10px 0">
        <div style="display:flex;justify-content:space-around;text-align:center;flex-wrap:wrap;gap:15px">
            <div>
                <div style="color:#6b7280;font-size:0.8em">CURRENT</div>
                <div style="color:#fff;font-size:1.5em;font-weight:700">{current_temp}°F</div>
            </div>
            <div>
                <div style="color:#3b82f6;font-size:0.8em">TODAY'S LOW</div>
                <div style="color:#3b82f6;font-size:1.5em;font-weight:700">{obs_low}°F</div>
            </div>
            <div>
                <div style="color:#ef4444;font-size:0.8em">TODAY'S HIGH</div>
                <div style="color:#ef4444;font-size:1.5em;font-weight:700">{obs_high}°F</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Show recent readings
    if readings:
        with st.expander("📊 Recent Readings"):
            reading_text = " | ".join([f"{r['time']}: {r['temp']}°F" for r in readings[:8]])
            st.caption(reading_text)
else:
    st.warning("⚠️ Could not fetch NWS observations")

st.markdown("---")

col_high, col_low = st.columns(2)

with col_high:
    st.subheader("☀️ HIGH TEMP")
    
    if obs_high:
        st.metric("📈 Today's High So Far", f"{obs_high}°F")
        hour = now.hour
        if hour < 15:
            st.caption("⏳ High may still increase (before 3 PM)")
        else:
            st.caption("✅ High likely locked in (after 3 PM)")
        
        brackets_high = fetch_kalshi_brackets(cfg.get("high", "KXHIGHNY"))
        render_brackets_with_actual(brackets_high, obs_high, "HIGH")
    else:
        st.error("Could not fetch observations")

with col_low:
    st.subheader("🌙 LOW TEMP")
    
    if obs_low:
        st.metric("📉 Today's Low So Far", f"{obs_low}°F")
        hour = now.hour
        if hour < 8:
            st.caption("⏳ Low may still drop (before 8 AM)")
        else:
            st.caption("✅ Low likely locked in (after 8 AM)")
        
        brackets_low = fetch_kalshi_brackets(cfg.get("low", "KXLOWTNYC"))
        render_brackets_with_actual(brackets_low, obs_low, "LOW")
    else:
        st.error("Could not fetch observations")

st.markdown("---")
st.caption("⚠️ Based on actual NWS observations. Not financial advice. v3.0")
