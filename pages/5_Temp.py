import streamlit as st
import requests
from datetime import datetime
import pytz
import math
import re

st.set_page_config(page_title="Temp Edge Finder", page_icon="🌡️", layout="wide")

st.markdown("""
<style>
.stApp {background-color: #0d1117;}
div[data-testid="stMarkdownContainer"] p {color: #c9d1d9;}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div style="background:linear-gradient(90deg,#d97706,#f59e0b);padding:10px 15px;border-radius:8px;margin-bottom:20px;text-align:center">
<b style="color:#000">🧪 EXPERIMENTAL</b> <span style="color:#000">— Temperature Edge Finder v2.4</span>
</div>
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

@st.cache_data(ttl=300)
def fetch_nws_temp(station):
    url = f"https://api.weather.gov/stations/{station}/observations/latest"
    try:
        resp = requests.get(url, headers={"User-Agent": "TempEdge/2.4"}, timeout=10)
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
        lat = cfg.get("lat", 40.78)
        lon = cfg.get("lon", -73.97)
        
        point_url = f"https://api.weather.gov/points/{lat},{lon}"
        resp = requests.get(point_url, headers={"User-Agent": "TempEdge/2.4"}, timeout=10)
        props = resp.json().get("properties", {})
        forecast_url = props.get("forecast", "")
        
        if not forecast_url:
            return None, None
        
        resp = requests.get(forecast_url, headers={"User-Agent": "TempEdge/2.4"}, timeout=10)
        periods = resp.json().get("properties", {}).get("periods", [])
        
        high_temp = None
        low_temp = None
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

def render_brackets(brackets, forecast, sigma):
    if not brackets:
        st.error("Could not load brackets")
        return
    
    # Find best edge
    best = max(brackets, key=lambda b: calc_model_prob(forecast, *get_bracket_bounds(b['range']), sigma) * 100 - b['yes'])
    best_edge = calc_model_prob(forecast, *get_bracket_bounds(best['range']), sigma) * 100 - best['yes']
    
    market_fav = max(brackets, key=lambda b: b['yes'])
    st.caption(f"Market favorite: {market_fav['range']} @ {market_fav['yes']:.0f}¢")
    
    for b in brackets:
        low, high = get_bracket_bounds(b['range'])
        model_prob = calc_model_prob(forecast, low, high, sigma) * 100
        market_prob = b['yes']
        edge = model_prob - market_prob
        is_best = (b['range'] == best['range']) and (best_edge >= 5)
        
        # Build styles
        if is_best:
            box_style = "background:linear-gradient(135deg,#2d1f0a,#1a1408);border:2px solid #f59e0b;box-shadow:0 0 15px rgba(245,158,11,0.4);border-radius:6px;padding:12px 14px;margin:8px 0"
            name_style = "color:#fbbf24;font-weight:700;font-size:1.05em"
            edge_color = "#fbbf24"
            icon = " 🎯"
        elif edge >= 5:
            box_style = "background:#0f1f0f;border:1px solid #2d5a2d;border-radius:6px;padding:10px 12px;margin:5px 0"
            name_style = "color:#e5e7eb;font-weight:500"
            edge_color = "#4ade80"
            icon = " 🟢"
        elif edge <= -5:
            box_style = "background:#1f0f0f;border:1px solid #5a2d2d;border-radius:6px;padding:10px 12px;margin:5px 0"
            name_style = "color:#e5e7eb;font-weight:500"
            edge_color = "#f87171"
            icon = " 🔴"
        else:
            box_style = "background:#161b22;border:1px solid #30363d;border-radius:6px;padding:10px 12px;margin:5px 0"
            name_style = "color:#e5e7eb;font-weight:500"
            edge_color = "#6b7280"
            icon = ""
        
        html = f'''<div style="{box_style}">
            <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px">
                <span style="{name_style}">{b['range']}{icon}</span>
                <div style="display:flex;gap:12px;align-items:center">
                    <span style="color:#f59e0b">Kalshi {b['yes']:.0f}¢</span>
                    <span style="color:#9ca3af">Model {model_prob:.0f}%</span>
                    <span style="color:{edge_color};font-weight:bold">{edge:+.0f}¢</span>
                </div>
            </div>
        </div>'''
        st.markdown(html, unsafe_allow_html=True)
    
    # BUY YES card
    if best_edge >= 5:
        card = f'''
        <div style="background:linear-gradient(135deg,#2d1f0a,#1a1408);border:2px solid #f59e0b;border-radius:10px;padding:18px;text-align:center;margin-top:12px;box-shadow:0 0 20px rgba(245,158,11,0.5)">
            <div style="color:#fbbf24;font-size:0.9em;font-weight:600">🎯 BEST EDGE: +{best_edge:.0f}¢</div>
            <div style="color:#fff;font-size:1.3em;font-weight:700;margin:10px 0">{best['range']}</div>
            <a href="{best['url']}" target="_blank" style="background:linear-gradient(135deg,#f59e0b,#d97706);color:#000;padding:12px 28px;border-radius:6px;text-decoration:none;font-weight:700;display:inline-block;box-shadow:0 4px 12px rgba(245,158,11,0.4)">BUY YES</a>
        </div>'''
        st.markdown(card, unsafe_allow_html=True)
    else:
        card = f'''
        <div style="background:#161b22;border:1px solid #30363d;border-radius:10px;padding:15px;text-align:center;margin-top:12px">
            <div style="color:#6b7280">No strong edge found</div>
            <div style="color:#9ca3af;margin:5px 0">{market_fav['range']} @ {market_fav['yes']:.0f}¢</div>
            <a href="{market_fav['url']}" target="_blank" style="background:#30363d;color:#c9d1d9;padding:8px 20px;border-radius:6px;text-decoration:none;display:inline-block">VIEW MARKET</a>
        </div>'''
        st.markdown(card, unsafe_allow_html=True)

# ========== HEADER ==========
st.title("🌡️ TEMP EDGE FINDER")
st.caption(f"Live Kalshi Data | {now.strftime('%b %d, %Y %I:%M %p ET')}")

c1, c2 = st.columns([4, 1])
with c1:
    city = st.selectbox("📍 Select City", CITY_LIST, index=CITY_LIST.index("New York City"))
with c2:
    cfg = CITY_CONFIG.get(city, {})
    nws_url = f"https://forecast.weather.gov/MapClick.php?lat={cfg.get('lat', 40.78)}&lon={cfg.get('lon', -73.97)}"
    st.markdown(f"<a href='{nws_url}' target='_blank' style='display:block;background:#3b82f6;color:#fff;padding:8px;border-radius:6px;text-align:center;text-decoration:none;font-weight:500;margin-top:25px'>📡 NWS</a>", unsafe_allow_html=True)

nws_temp = fetch_nws_temp(cfg.get("station", "KNYC"))
nws_high, nws_low = fetch_nws_forecast(city)

curr = f"{nws_temp}°F" if nws_temp else "?"
hi = f"{nws_high}°F" if nws_high else "?"
lo = f"{nws_low}°F" if nws_low else "?"
st.caption(f"📡 Current: **{curr}** | NWS High: **{hi}** | NWS Low: **{lo}**")

st.markdown("---")

col_high, col_low = st.columns(2)

with col_high:
    st.subheader("☀️ HIGH TEMP")
    h1, h2 = st.columns(2)
    with h1:
        if nws_high:
            default_high = int(nws_high)
        elif nws_temp:
            default_high = int(nws_temp)
        else:
            default_high = 40
        high_forecast = st.number_input("🎯 Your forecast", value=default_high, min_value=-20, max_value=120, key="high_fc")
    with h2:
        high_sigma = st.slider("σ uncertainty", 0.0, 3.0, 1.8, 0.1, key="high_sig")
    
    brackets_high = fetch_kalshi_brackets(cfg.get("high", "KXHIGHNY"))
    render_brackets(brackets_high, high_forecast, high_sigma)

with col_low:
    st.subheader("🌙 LOW TEMP")
    l1, l2 = st.columns(2)
    with l1:
        if nws_low:
            default_low = int(nws_low)
        else:
            default_low = 25
        low_forecast = st.number_input("🎯 Your forecast", value=default_low, min_value=-20, max_value=120, key="low_fc")
    with l2:
        low_sigma = st.slider("σ uncertainty", 0.0, 3.0, 1.8, 0.1, key="low_sig")
    
    brackets_low = fetch_kalshi_brackets(cfg.get("low", "KXLOWTNYC"))
    render_brackets(brackets_low, low_forecast, low_sigma)

st.markdown("---")
st.caption("⚠️ Experimental. Not financial advice. v2.4")
