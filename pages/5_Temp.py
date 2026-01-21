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

def get_bracket_bounds(range_str):
    """Parse temperature bracket from Kalshi subtitle - only match temp numbers with °"""
    tl = range_str.lower()
    
    # Pattern: "<12°" or "be <12°"
    below_match = re.search(r'<\s*(\d+)°', range_str)
    if below_match:
        return -999, int(below_match.group(1)) - 0.5
    
    # Pattern: ">19°" or "be >19°"  
    above_match = re.search(r'>\s*(\d+)°', range_str)
    if above_match:
        return int(above_match.group(1)) + 0.5, 999
    
    # Pattern: "16-17°" or "16° to 17°" or "16 to 17°"
    range_match = re.search(r'(\d+)[-–]\s*(\d+)°|(\d+)°?\s*to\s*(\d+)°', range_str)
    if range_match:
        if range_match.group(1) and range_match.group(2):
            low, high = int(range_match.group(1)), int(range_match.group(2))
        else:
            low, high = int(range_match.group(3)), int(range_match.group(4))
        return low - 0.5, high + 0.5
    
    # Pattern: "32° or below" or "41° or above"
    if "or below" in tl or "below" in tl:
        nums = re.findall(r'(\d+)°', range_str)
        if nums:
            return -999, int(nums[0]) + 0.5
    if "or above" in tl or "above" in tl:
        nums = re.findall(r'(\d+)°', range_str)
        if nums:
            return int(nums[0]) - 0.5, 999
    
    # Fallback: only numbers with degree symbol
    nums = re.findall(r'(\d+)°', range_str)
    if len(nums) >= 2:
        return int(nums[0]) - 0.5, int(nums[1]) + 0.5
    elif nums:
        return int(nums[0]) - 0.5, int(nums[0]) + 0.5
    
    return 0, 100

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
        
        today = datetime.now(eastern).date()
        temps = []
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
                    temps.append(temp_f)
                    readings.append({"time": ts_local.strftime("%H:%M"), "temp": temp_f})
            except:
                continue
        
        if not temps:
            return None, None, None, []
        
        current = temps[0] if temps else None
        low = min(temps)
        high = max(temps)
        
        return current, low, high, readings[:12]
        
    except:
        return None, None, None, []

@st.cache_data(ttl=300)
def fetch_nws_forecast(lat, lon):
    """Fetch NWS forecast for display"""
    try:
        # First get the forecast URL from points endpoint
        points_url = f"https://api.weather.gov/points/{lat},{lon}"
        resp = requests.get(points_url, headers={"User-Agent": "TempEdge/3.0"}, timeout=10)
        if resp.status_code != 200:
            return None
        
        forecast_url = resp.json().get("properties", {}).get("forecast")
        if not forecast_url:
            return None
        
        # Fetch the actual forecast
        resp = requests.get(forecast_url, headers={"User-Agent": "TempEdge/3.0"}, timeout=10)
        if resp.status_code != 200:
            return None
        
        periods = resp.json().get("properties", {}).get("periods", [])
        if not periods:
            return None
        
        # Return first 4 periods (today/tonight/tomorrow/tomorrow night)
        return periods[:4]
    except:
        return None

def render_brackets_with_actual(brackets, actual_temp, temp_type):
    """Render brackets highlighting the actual winning bracket"""
    if not brackets:
        st.error("Could not load brackets")
        return
    
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
        
        if is_winner:
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
    
    if readings:
        with st.expander("📊 Recent NWS Observations"):
            # Find reversal point (LOW: temp lower than both neighbors)
            reversal_idx = None
            for i in range(1, len(readings) - 1):
                # readings are newest first, so check if this is lower than both neighbors
                if readings[i]['temp'] < readings[i-1]['temp'] and readings[i]['temp'] < readings[i+1]['temp']:
                    reversal_idx = i
                    break
            
            for i, r in enumerate(readings[:8]):
                # Highlight the reversal point in orange
                if i == reversal_idx:
                    row_style = "display:flex;justify-content:space-between;padding:6px 8px;border-radius:4px;background:linear-gradient(135deg,#2d1f0a,#1a1408);border:1px solid #f59e0b;margin:2px 0"
                    time_style = "color:#fbbf24;font-weight:600"
                    temp_style = "color:#fbbf24;font-weight:700"
                    label = " ↩️ REVERSAL"
                else:
                    row_style = "display:flex;justify-content:space-between;padding:4px 0;border-bottom:1px solid #30363d"
                    time_style = "color:#9ca3af"
                    temp_style = "color:#fff;font-weight:600"
                    label = ""
                st.markdown(f"<div style='{row_style}'><span style='{time_style}'>{r['time']}</span><span style='{temp_style}'>{r['temp']}°F{label}</span></div>", unsafe_allow_html=True)
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
                    if is_fav:
                        box_style = "background:#1a1a2e;border:1px solid #f59e0b;border-radius:6px;padding:10px 12px;margin:5px 0"
                        icon = " ⭐"
                    else:
                        box_style = "background:#161b22;border:1px solid #30363d;border-radius:6px;padding:10px 12px;margin:5px 0"
                        icon = ""
                    html = f'''<div style="{box_style}">
                        <div style="display:flex;justify-content:space-between;align-items:center">
                            <span style="color:#e5e7eb">{b['range']}{icon}</span>
                            <span style="color:#f59e0b">Kalshi {b['yes']:.0f}¢</span>
                        </div>
                    </div>'''
                    st.markdown(html, unsafe_allow_html=True)
                
                # Add BUY button for market favorite
                st.markdown(f'''
                <div style="text-align:center;margin-top:12px">
                    <a href="{market_fav['url']}" target="_blank" style="background:linear-gradient(135deg,#f59e0b,#d97706);color:#000;padding:12px 28px;border-radius:6px;text-decoration:none;font-weight:700;display:inline-block;box-shadow:0 4px 12px rgba(245,158,11,0.4)">BUY MARKET FAVORITE</a>
                </div>
                ''', unsafe_allow_html=True)
    else:
        st.error("Could not fetch observations")

with col_low:
    st.subheader("🌙 LOW TEMP")
    hour = now.hour
    
    if obs_low:
        st.metric("📉 Today's Low", f"{obs_low}°F")
        brackets_low = fetch_kalshi_brackets(cfg.get("low", "KXLOWTNYC"))
        
        if hour >= 6:  # LOW locks in by 6 AM
            st.caption("✅ Low locked in (after 6 AM)")
            render_brackets_with_actual(brackets_low, obs_low, "LOW")
        else:
            st.caption(f"⏳ Low may still drop (before 6 AM)")
            if brackets_low:
                market_fav = max(brackets_low, key=lambda b: b['yes'])
                st.caption(f"Market favorite: {market_fav['range']} @ {market_fav['yes']:.0f}¢")
                for b in brackets_low:
                    is_fav = b['range'] == market_fav['range']
                    if is_fav:
                        box_style = "background:#1a1a2e;border:1px solid #f59e0b;border-radius:6px;padding:10px 12px;margin:5px 0"
                        icon = " ⭐"
                    else:
                        box_style = "background:#161b22;border:1px solid #30363d;border-radius:6px;padding:10px 12px;margin:5px 0"
                        icon = ""
                    html = f'''<div style="{box_style}">
                        <div style="display:flex;justify-content:space-between;align-items:center">
                            <span style="color:#e5e7eb">{b['range']}{icon}</span>
                            <span style="color:#f59e0b">Kalshi {b['yes']:.0f}¢</span>
                        </div>
                    </div>'''
                    st.markdown(html, unsafe_allow_html=True)
                
                # Add BUY button for market favorite
                st.markdown(f'''
                <div style="text-align:center;margin-top:12px">
                    <a href="{market_fav['url']}" target="_blank" style="background:linear-gradient(135deg,#f59e0b,#d97706);color:#000;padding:12px 28px;border-radius:6px;text-decoration:none;font-weight:700;display:inline-block;box-shadow:0 4px 12px rgba(245,158,11,0.4)">BUY MARKET FAVORITE</a>
                </div>
                ''', unsafe_allow_html=True)
    else:
        st.error("Could not fetch observations")

# ========== NWS FORECAST SECTION ==========
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
            
            # Color based on day/night
            if "night" in name.lower() or "tonight" in name.lower():
                bg = "#1a1a2e"
                temp_color = "#3b82f6"
            else:
                bg = "#1f2937"
                temp_color = "#ef4444"
            
            st.markdown(f"""
            <div style="background:{bg};border:1px solid #30363d;border-radius:8px;padding:12px;text-align:center">
                <div style="color:#9ca3af;font-size:0.8em;font-weight:600">{name}</div>
                <div style="color:{temp_color};font-size:1.8em;font-weight:700">{temp}°{unit}</div>
                <div style="color:#6b7280;font-size:0.75em;margin-top:5px">{short}</div>
            </div>
            """, unsafe_allow_html=True)
else:
    st.caption("Could not load NWS forecast")

st.markdown("---")
st.markdown("""
<div style="background:linear-gradient(90deg,#d97706,#f59e0b);padding:10px 15px;border-radius:8px;margin-bottom:20px;text-align:center">
<b style="color:#000">🧪 EXPERIMENTAL</b> <span style="color:#000">— Temperature Edge Finder v3.1</span>
</div>
""", unsafe_allow_html=True)

with st.expander("❓ How to Use This App"):
    st.markdown("""
    **🌡️ What This App Does**
    
    Compares actual NWS temperature observations against Kalshi prediction market prices to find edge opportunities.
    
    **⏰ Timing Windows**
    
    • **LOW Temperature**: Locks in by ~6 AM. The overnight low is set — it only warms up from there.
    • **HIGH Temperature**: Locks in by ~3 PM. Peak heat typically occurs 12-5 PM.
    
    **↩️ Reversal Point (Orange Highlight)**
    
    In "Recent NWS Observations", we highlight the **reversal point** — the exact moment temps bottomed out and started climbing back up. Example:
    
    • 07:51 → 19.0°F (warming up)
    • 06:51 → 17.1°F ↩️ REVERSAL (lowest point)
    • 05:51 → 18.0°F (was cooling down)
    
    When you see a reversal, it confirms the LOW is locked in. The temperature hit bottom and reversed direction — it's not going lower.
    
    **🎯 Reading the Display**
    
    • **⭐ Star** = Market favorite (highest Kalshi price)
    • **🎯 ACTUAL** = The bracket where the observed temperature actually falls
    • **Kalshi price** = What the market thinks the probability is (e.g., 40¢ = 40% chance)
    
    **💰 Finding Edge**
    
    When ACTUAL bracket ≠ Market favorite, there may be edge:
    • If actual temp falls in a bracket priced at 1¢, buying YES pays +99¢ profit
    • If actual temp falls in a bracket priced at 50¢, buying YES pays +50¢ profit
    
    **📊 Data Sources**
    
    • **Observations**: Live hourly readings from NWS weather stations
    • **Brackets**: Real-time prices from Kalshi API
    • **Forecast**: NWS official forecast for reference
    
    **⚠️ Important Notes**
    
    • This is NOT financial advice
    • Weather can change — especially HIGH temps before 3 PM
    • Always verify on Kalshi before trading
    • Kalshi uses specific weather stations — slight differences possible
    """)

st.caption("⚠️ Based on actual NWS observations. Not financial advice. v3.1")
