import streamlit as st
import requests
from datetime import datetime
import pytz
import math
import json
import os

st.set_page_config(page_title="Temp Edge Finder", page_icon="🌡️", layout="wide")

st.markdown("""
<style>
.stApp {background-color: #0a0a0f;}
div[data-testid="stMarkdownContainer"] p {color: #fff;}
@media (max-width: 768px) {
    div[data-testid="stHorizontalBlock"] {flex-direction: column !important;}
    div[data-testid="stColumn"] {width: 100% !important;}
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div style="background:linear-gradient(90deg,#ff6b00,#ff9500);padding:10px 15px;border-radius:8px;margin-bottom:20px;text-align:center">
<b style="color:#000">🧪 EXPERIMENTAL</b> <span style="color:#000">— Temperature Edge Finder v2.2</span>
</div>
""", unsafe_allow_html=True)

eastern = pytz.timezone("US/Eastern")
now = datetime.now(eastern)

CITY_CONFIG = {
    "Austin": {"high": "KXHIGHAUS", "low": "KXLOWTAUS", "tz": "US/Central", "station": "KAUS", "lat": 30.19, "lon": -97.67},
    "Chicago": {"high": "KXHIGHCHI", "low": "KXLOWTCHI", "tz": "US/Central", "station": "KMDW", "lat": 41.79, "lon": -87.75},
    "Denver": {"high": "KXHIGHDEN", "low": "KXLOWTDEN", "tz": "US/Mountain", "station": "KDEN", "lat": 39.86, "lon": -104.67},
    "Los Angeles": {"high": "KXHIGHLAX", "low": "KXLOWTLAX", "tz": "US/Pacific", "station": "KLAX", "lat": 33.94, "lon": -118.41},
    "Miami": {"high": "KXHIGHMIA", "low": "KXLOWTMIA", "tz": "US/Eastern", "station": "KMIA", "lat": 25.80, "lon": -80.29},
    "New York City": {"high": "KXHIGHNY", "low": "KXLOWTNYC", "tz": "US/Eastern", "station": "KNYC", "lat": 40.78, "lon": -73.97},
    "Philadelphia": {"high": "KXHIGHPHL", "low": "KXLOWTPHL", "tz": "US/Eastern", "station": "KPHL", "lat": 39.87, "lon": -75.23},
}

CITY_LIST = sorted(CITY_CONFIG.keys())

PREFS_FILE = "temp_prefs.json"
def load_prefs():
    try:
        if os.path.exists(PREFS_FILE):
            with open(PREFS_FILE, 'r') as f:
                return json.load(f)
    except: pass
    return {"default_city": "New York City"}

def save_prefs(prefs):
    try:
        with open(PREFS_FILE, 'w') as f:
            json.dump(prefs, f)
    except: pass

if "prefs" not in st.session_state:
    st.session_state.prefs = load_prefs()

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
            txt = m.get("subtitle", "") or m.get("title", "")
            ticker = m.get("ticker", "")
            mid = None
            tl = txt.lower()
            
            if "below" in tl:
                try: mid = int(''.join(filter(str.isdigit, txt.split('°')[0]))) - 1
                except: mid = 30
            elif "above" in tl:
                try: mid = int(''.join(filter(str.isdigit, txt.split('°')[0]))) + 1
                except: mid = 60
            elif "to" in tl:
                try:
                    p = txt.replace('°','').lower().split('to')
                    mid = (int(''.join(filter(str.isdigit, p[0]))) + int(''.join(filter(str.isdigit, p[1])))) / 2
                except: mid = 45
            
            yb, ya = m.get("yes_bid", 0), m.get("yes_ask", 0)
            yes_price = (yb + ya) / 2 if yb and ya else ya or yb or 0
            
            brackets.append({
                "range": txt,
                "mid": mid,
                "yes": yes_price,
                "no": 100 - yes_price,
                "ticker": ticker,
                "url": f"https://kalshi.com/markets/{series_ticker.lower()}/{ticker.lower()}" if ticker else "#"
            })
        
        brackets.sort(key=lambda x: x['mid'] or 0)
        return brackets
    except:
        return None

@st.cache_data(ttl=300)
def fetch_nws_temp(station):
    url = f"https://api.weather.gov/stations/{station}/observations/latest"
    try:
        resp = requests.get(url, headers={"User-Agent": "TempEdge/2.2"}, timeout=10)
        if resp.status_code == 200:
            tc = resp.json().get("properties", {}).get("temperature", {}).get("value")
            if tc is not None:
                return round(tc * 9/5 + 32, 1)
    except:
        pass
    return None

@st.cache_data(ttl=1800)
def fetch_nws_forecast(city):
    try:
        cfg = CITY_CONFIG.get(city, {})
        lat, lon = cfg.get("lat", 40.78), cfg.get("lon", -73.97)
        
        point_url = f"https://api.weather.gov/points/{lat},{lon}"
        resp = requests.get(point_url, headers={"User-Agent": "TempEdge/2.2"}, timeout=10)
        props = resp.json().get("properties", {})
        forecast_url = props.get("forecast", "")
        
        if not forecast_url:
            return None, None
        
        resp = requests.get(forecast_url, headers={"User-Agent": "TempEdge/2.2"}, timeout=10)
        periods = resp.json().get("properties", {}).get("periods", [])
        
        high_temp, low_temp = None, None
        for p in periods[:6]:
            name = p.get("name", "").lower()
            temp = p.get("temperature", 0)
            if ("tonight" in name or "night" in name) and low_temp is None:
                low_temp = temp
            elif p.get("isDaytime", True) and high_temp is None:
                high_temp = temp
        
        return high_temp, low_temp
    except:
        return None, None

def normal_cdf(x, mu, sigma):
    return 0.5 * (1 + math.erf((x - mu) / (sigma * math.sqrt(2))))

def calc_model_prob(forecast, low, high, sigma):
    if low == -999:
        return normal_cdf(high, forecast, sigma)
    elif high == 999:
        return 1 - normal_cdf(low, forecast, sigma)
    else:
        return normal_cdf(high, forecast, sigma) - normal_cdf(low, forecast, sigma)

def get_bracket_bounds(range_str):
    tl = range_str.lower()
    if "below" in tl:
        try:
            num = int(''.join(filter(str.isdigit, range_str.split('°')[0])))
            return -999, num + 0.5
        except:
            return -999, 30.5
    elif "above" in tl:
        try:
            num = int(''.join(filter(str.isdigit, range_str.split('°')[0])))
            return num - 0.5, 999
        except:
            return 59.5, 999
    elif "to" in tl:
        try:
            parts = range_str.replace('°','').lower().split('to')
            lo = int(''.join(filter(str.isdigit, parts[0])))
            hi = int(''.join(filter(str.isdigit, parts[1])))
            return lo - 0.5, hi + 0.5
        except:
            return 40, 50
    return 0, 100

st.title("🌡️ TEMP EDGE FINDER")
st.caption(f"Live Kalshi Data | {now.strftime('%b %d, %Y %I:%M %p ET')}")

c1, c2, c3 = st.columns([3, 1, 1])
with c1:
    default_idx = CITY_LIST.index(st.session_state.prefs.get("default_city", "New York City")) if st.session_state.prefs.get("default_city") in CITY_LIST else 5
    city = st.selectbox("📍 Select City", CITY_LIST, index=default_idx)
with c2:
    if st.button("⭐ Default", use_container_width=True):
        st.session_state.prefs["default_city"] = city
        save_prefs(st.session_state.prefs)
        st.success("✅")
with c3:
    cfg = CITY_CONFIG.get(city, {})
    nws_url = f"https://forecast.weather.gov/MapClick.php?lat={cfg.get('lat', 40.78)}&lon={cfg.get('lon', -73.97)}"
    st.markdown(f"<a href='{nws_url}' target='_blank' style='display:block;background:#38bdf8;color:#000;padding:8px;border-radius:6px;text-align:center;text-decoration:none;font-weight:bold;margin-top:25px'>📡 NWS</a>", unsafe_allow_html=True)

nws_temp = fetch_nws_temp(cfg.get("station", "KNYC"))
nws_high, nws_low = fetch_nws_forecast(city)

if nws_temp:
    st.caption(f"📡 Current: **{nws_temp}°F** | NWS High: **{nws_high or '?'}°F** | NWS Low: **{nws_low or '?'}°F**")
else:
    st.caption(f"📡 NWS High: **{nws_high or '?'}°F** | NWS Low: **{nws_low or '?'}°F**")

st.markdown("---")

col_high, col_low = st.columns(2)

# ========== HIGH TEMPERATURE ==========
with col_high:
    st.subheader("☀️ HIGH TEMP")
    
    h1, h2 = st.columns(2)
    with h1:
        default_high = int(nws_high) if nws_high else (int(nws_temp) if nws_temp else 45)
        high_forecast = st.number_input("🎯 High forecast", value=default_high, min_value=-20, max_value=120, key="high_fc")
    with h2:
        high_sigma = st.slider("σ (High)", 1.0, 3.0, 1.8, 0.1, key="high_sig")
    
    brackets_high = fetch_kalshi_brackets(cfg.get("high", "KXHIGHNY"))
    
    if brackets_high:
        market_fav = max(brackets_high, key=lambda b: b['yes'])
        st.caption(f"Market favorite: **{market_fav['range']}** @ {market_fav['yes']:.0f}¢")
        
        for b in brackets_high:
            is_fav = b['range'] == market_fav['range']
            low, high = get_bracket_bounds(b['range'])
            model_prob = calc_model_prob(high_forecast, low, high, high_sigma) * 100
            market_prob = b['yes']
            edge = model_prob - market_prob
            
            if is_fav:
                bg, border, icon = "linear-gradient(90deg,#3d2800,#1a1200)", "2px solid #ff9500", " ⭐"
            elif edge >= 5:
                bg, border, icon = "#0a2e0a", "1px solid #00ff00", " 🟢"
            elif edge <= -5:
                bg, border, icon = "#2e0a0a", "1px solid #ff4444", " 🔴"
            else:
                bg, border, icon = "#0f172a", "1px solid #333", ""
            
            edge_txt = f"<span style='color:{'#00ff00' if edge > 0 else '#ff4444'};font-weight:bold'>{edge:+.0f}¢</span>" if abs(edge) >= 5 else f"<span style='color:#666'>{edge:+.0f}¢</span>"
            
            st.markdown(f"""<div style="background:{bg};border:{border};border-radius:6px;padding:8px 10px;margin:4px 0">
                <div style="display:flex;justify-content:space-between;align-items:center">
                    <span style="color:#fff">{b['range']}{icon}</span>
                    <div>
                        <span style="color:#ff9500;margin-right:10px">Kalshi {b['yes']:.0f}¢</span>
                        <span style="color:#38bdf8;margin-right:10px">Model {model_prob:.0f}%</span>
                        {edge_txt}
                    </div>
                </div>
            </div>""", unsafe_allow_html=True)
        
        best_yes = max(brackets_high, key=lambda b: calc_model_prob(high_forecast, *get_bracket_bounds(b['range']), high_sigma) * 100 - b['yes'])
        best_edge = calc_model_prob(high_forecast, *get_bracket_bounds(best_yes['range']), high_sigma) * 100 - best_yes['yes']
        
        if best_edge >= 5:
            st.markdown(f"""
            <div style="background:linear-gradient(135deg,#0a2e0a,#001a00);border:2px solid #00ff00;border-radius:10px;padding:15px;text-align:center;margin-top:10px">
                <div style="color:#00ff00;font-size:0.8em">🎯 BEST EDGE: +{best_edge:.0f}¢</div>
                <div style="color:#fff;font-size:1.3em;font-weight:bold">{best_yes['range']}</div>
                <a href="{best_yes['url']}" target="_blank" style="background:#00c853;color:#000;padding:10px 25px;border-radius:6px;text-decoration:none;font-weight:bold;display:inline-block;margin-top:10px">BUY YES</a>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="background:#1a1a2e;border:1px solid #666;border-radius:10px;padding:15px;text-align:center;margin-top:10px">
                <div style="color:#888">No strong edge found</div>
                <div style="color:#fff;font-size:1.1em">{market_fav['range']} @ {market_fav['yes']:.0f}¢</div>
                <a href="{market_fav['url']}" target="_blank" style="background:#666;color:#fff;padding:8px 20px;border-radius:6px;text-decoration:none;display:inline-block;margin-top:10px">VIEW MARKET</a>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.error("❌ Could not load HIGH temp brackets")

# ========== LOW TEMPERATURE ==========
with col_low:
    st.subheader("🌙 LOW TEMP")
    
    l1, l2 = st.columns(2)
    with l1:
        default_low = int(nws_low) if nws_low else 30
        low_forecast = st.number_input("🎯 Low forecast", value=default_low, min_value=-20, max_value=120, key="low_fc")
    with l2:
        low_sigma = st.slider("σ (Low)", 1.0, 3.0, 1.8, 0.1, key="low_sig")
    
    brackets_low = fetch_kalshi_brackets(cfg.get("low", "KXLOWTNYC"))
    
    if brackets_low:
        market_fav = max(brackets_low, key=lambda b: b['yes'])
        st.caption(f"Market favorite: **{market_fav['range']}** @ {market_fav['yes']:.0f}¢")
        
        for b in brackets_low:
            is_fav = b['range'] == market_fav['range']
            low, high = get_bracket_bounds(b['range'])
            model_prob = calc_model_prob(low_forecast, low, high, low_sigma) * 100
            market_prob = b['yes']
            edge = model_prob - market_prob
            
            if is_fav:
                bg, border, icon = "linear-gradient(90deg,#002a3d,#001a20)", "2px solid #38bdf8", " ⭐"
            elif edge >= 5:
                bg, border, icon = "#0a2e0a", "1px solid #00ff00", " 🟢"
            elif edge <= -5:
                bg, border, icon = "#2e0a0a", "1px solid #ff4444", " 🔴"
            else:
                bg, border, icon = "#0f172a", "1px solid #333", ""
            
            edge_txt = f"<span style='color:{'#00ff00' if edge > 0 else '#ff4444'};font-weight:bold'>{edge:+.0f}¢</span>" if abs(edge) >= 5 else f"<span style='color:#666'>{edge:+.0f}¢</span>"
            
            st.markdown(f"""<div style="background:{bg};border:{border};border-radius:6px;padding:8px 10px;margin:4px 0">
                <div style="display:flex;justify-content:space-between;align-items:center">
                    <span style="color:#fff">{b['range']}{icon}</span>
                    <div>
                        <span style="color:#38bdf8;margin-right:10px">Kalshi {b['yes']:.0f}¢</span>
                        <span style="color:#ff9500;margin-right:10px">Model {model_prob:.0f}%</span>
                        {edge_txt}
                    </div>
                </div>
            </div>""", unsafe_allow_html=True)
        
        best_yes = max(brackets_low, key=lambda b: calc_model_prob(low_forecast, *get_bracket_bounds(b['range']), low_sigma) * 100 - b['yes'])
        best_edge = calc_model_prob(low_forecast, *get_bracket_bounds(best_yes['range']), low_sigma) * 100 - best_yes['yes']
        
        if best_edge >= 5:
            st.markdown(f"""
            <div style="background:linear-gradient(135deg,#0a2e0a,#001a00);border:2px solid #00ff00;border-radius:10px;padding:15px;text-align:center;margin-top:10px">
                <div style="color:#00ff00;font-size:0.8em">🎯 BEST EDGE: +{best_edge:.0f}¢</div>
                <div style="color:#fff;font-size:1.3em;font-weight:bold">{best_yes['range']}</div>
                <a href="{best_yes['url']}" target="_blank" style="background:#00c853;color:#000;padding:10px 25px;border-radius:6px;text-decoration:none;font-weight:bold;display:inline-block;margin-top:10px">BUY YES</a>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="background:#1a1a2e;border:1px solid #666;border-radius:10px;padding:15px;text-align:center;margin-top:10px">
                <div style="color:#888">No strong edge found</div>
                <div style="color:#fff;font-size:1.1em">{market_fav['range']} @ {market_fav['yes']:.0f}¢</div>
                <a href="{market_fav['url']}" target="_blank" style="background:#666;color:#fff;padding:8px 20px;border-radius:6px;text-decoration:none;display:inline-block;margin-top:10px">VIEW MARKET</a>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.error("❌ Could not load LOW temp brackets")

st.markdown("---")

with st.expander("📖 HOW TO USE", expanded=False):
    st.markdown("""
### 🎯 Finding Edge

1. **Set your forecast** — HIGH and LOW have separate inputs now!
2. **Adjust σ** — Lower = more confident, Higher = more uncertainty
3. **Compare** — Your model % vs Kalshi's market %
4. **Find edge** — Green 🟢 = BUY YES, Red 🔴 = BUY NO

### 📊 Edge Guide

| Edge | Meaning | Action |
|------|---------|--------|
| 🟢 **+5¢ or more** | Model higher than market | BUY YES |
| 🔴 **-5¢ or more** | Model lower than market | BUY NO |
| ⚪ **Within ±5¢** | No clear edge | Skip |

### ⏰ Best Time to Trade

- **8-10 AM** — Best! Forecast stable, prices cheap
- **10 AM-12 PM** — Good, prices rising
- **After 12 PM** — Late, prices already reflect outcome

*v2.2 — Separate HIGH/LOW forecasts*
""")

st.caption("⚠️ Experimental. Not financial advice. v2.2")
