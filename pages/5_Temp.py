import streamlit as st
import requests
from datetime import datetime, timedelta
import pytz
import math
import json
import os

st.set_page_config(page_title="Temp Edge Finder", page_icon="🌡️", layout="wide")

# ========== GOOGLE ANALYTICS G4 ==========
st.markdown("""
<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-XXXXXXXXXX"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'G-XXXXXXXXXX');
</script>
""", unsafe_allow_html=True)

# ========== CSS ==========
st.markdown("""
<style>
.stApp {background-color: #0a0a0f;}
div[data-testid="stMarkdownContainer"] p {color: #fff;}
@media (max-width: 768px) {
    .stApp {padding: 0.5rem !important;}
    div[data-testid="stHorizontalBlock"] {flex-direction: column !important;}
    div[data-testid="stColumn"] {width: 100% !important;}
}
div[data-testid="stExpander"] {background: #0f172a; border-radius: 8px;}
div[data-testid="stNumberInput"] input {background: #1a1a2e !important; color: #fff !important;}
</style>
""", unsafe_allow_html=True)

# ========== BANNER ==========
st.markdown("""
<div style="background:linear-gradient(90deg,#ff6b00,#ff9500);padding:10px 15px;border-radius:8px;margin-bottom:20px;text-align:center">
<b style="color:#000">🧪 EXPERIMENTAL</b> <span style="color:#000">— Temperature Edge Finder v2.0</span>
</div>
""", unsafe_allow_html=True)

eastern = pytz.timezone("US/Eastern")
now = datetime.now(eastern)

# ========== CITY CONFIG ==========
CITY_CONFIG = {
    "Austin": {"grid": "EWX/156,91", "kalshi_high": "kxhighaus", "kalshi_low": "kxlowtaus", "slug_high": "highest-temperature-in-austin", "slug_low": "lowest-temperature-in-austin", "tz": "US/Central", "station": "Austin-Bergstrom (KAUS)", "lat": 30.1945, "lon": -97.6699},
    "Chicago": {"grid": "LOT/76,73", "kalshi_high": "kxhighchi", "kalshi_low": "kxlowtchi", "slug_high": "highest-temperature-in-chicago", "slug_low": "lowest-temperature-in-chicago", "tz": "US/Central", "station": "Midway (KMDW)", "lat": 41.7868, "lon": -87.7522},
    "Denver": {"grid": "BOU/62,60", "kalshi_high": "kxhighden", "kalshi_low": "kxlowtden", "slug_high": "highest-temperature-in-denver", "slug_low": "lowest-temperature-in-denver", "tz": "US/Mountain", "station": "Denver Intl (KDEN)", "lat": 39.8561, "lon": -104.6737},
    "Los Angeles": {"grid": "LOX/154,44", "kalshi_high": "kxhighlax", "kalshi_low": "kxlowtlax", "slug_high": "highest-temperature-in-los-angeles", "slug_low": "lowest-temperature-in-los-angeles", "tz": "US/Pacific", "station": "LAX (KLAX)", "lat": 33.9425, "lon": -118.4081},
    "Miami": {"grid": "MFL/109,50", "kalshi_high": "kxhighmia", "kalshi_low": "kxlowtmia", "slug_high": "highest-temperature-in-miami", "slug_low": "lowest-temperature-in-miami", "tz": "US/Eastern", "station": "Miami Intl (KMIA)", "lat": 25.7959, "lon": -80.2870},
    "New York City": {"grid": "OKX/33,37", "kalshi_high": "kxhighny", "kalshi_low": "kxlowtnyc", "slug_high": "highest-temperature-in-nyc", "slug_low": "lowest-temperature-in-nyc", "tz": "US/Eastern", "station": "Central Park (KNYC)", "lat": 40.7829, "lon": -73.9654},
    "Philadelphia": {"grid": "PHI/49,75", "kalshi_high": "kxhighphl", "kalshi_low": "kxlowtphl", "slug_high": "highest-temperature-in-philadelphia", "slug_low": "lowest-temperature-in-philadelphia", "tz": "US/Eastern", "station": "PHL Airport (KPHL)", "lat": 39.8721, "lon": -75.2311},
}

CITY_LIST = sorted(CITY_CONFIG.keys())

# ========== PREFERENCES ==========
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

# ========== FUNCTIONS ==========
def build_kalshi_url(city, is_high):
    cfg = CITY_CONFIG.get(city, {})
    series = cfg.get("kalshi_high" if is_high else "kalshi_low", "kxhighny")
    slug = cfg.get("slug_high" if is_high else "slug_low", "highest-temperature-in-nyc")
    return f"https://kalshi.com/markets/{series}/{slug}"

def normal_cdf(x, mu, sigma):
    return 0.5 * (1 + math.erf((x - mu) / (sigma * math.sqrt(2))))

def calc_bucket_prob(forecast, low, high, sigma):
    return normal_cdf(high, forecast, sigma) - normal_cdf(low, forecast, sigma)

def generate_buckets(center, size=2, count=8):
    buckets = []
    start = int(center - (count // 2) * size)
    buckets.append({"label": f"{start}° or below", "low": -999, "high": start + 0.5})
    for i in range(count - 2):
        lo = start + i * size
        hi = lo + size - 1
        buckets.append({"label": f"{lo}° to {hi}°", "low": lo - 0.5, "high": hi + 0.5})
    end = start + (count - 2) * size
    buckets.append({"label": f"{end}° or above", "low": end - 0.5, "high": 999})
    return buckets

@st.cache_data(ttl=1800)
def fetch_nws_forecast(city):
    try:
        grid = CITY_CONFIG.get(city, {}).get("grid", "OKX/33,37")
        office, gp = grid.split("/")
        url = f"https://api.weather.gov/gridpoints/{office}/{gp}/forecast"
        resp = requests.get(url, headers={"User-Agent": "TempEdge/2.0"}, timeout=10)
        data = resp.json()
        periods = data.get("properties", {}).get("periods", [])
        return [{"name": p.get("name", ""), "temp": p.get("temperature", 0), "is_day": p.get("isDaytime", True), "short": p.get("shortForecast", "")} for p in periods[:8]]
    except:
        return []

def get_forecasts(periods):
    high, low = None, None
    for p in periods[:6]:
        name = p.get("name", "").lower()
        temp = p.get("temp", 0)
        if ("tonight" in name or "night" in name) and low is None:
            low = temp
        elif p.get("is_day") and high is None:
            high = temp
    return high, low

def get_city_time(city):
    tz = pytz.timezone(CITY_CONFIG.get(city, {}).get("tz", "US/Eastern"))
    return datetime.now(tz)

def calc_hours_to_settle(city, is_high):
    city_now = get_city_time(city)
    if is_high:
        # High settles around 5-6 PM local
        target = city_now.replace(hour=17, minute=0, second=0)
        if city_now.hour >= 17:
            return 1
    else:
        # Low settles at midnight local
        target = city_now.replace(hour=23, minute=59, second=59)
        if city_now.hour >= 23:
            return 1
    return max(1, int((target - city_now).total_seconds() / 3600))

def auto_sigma(periods):
    if not periods:
        return 2.5
    text = " ".join([p.get("short", "").lower() for p in periods[:4]])
    if any(w in text for w in ["storm", "thunder", "severe"]):
        return 4.5
    elif any(w in text for w in ["front", "variable", "scattered", "chance"]):
        return 3.5
    elif any(w in text for w in ["partly", "showers"]):
        return 3.0
    elif any(w in text for w in ["clear", "sunny", "fair"]):
        return 2.0
    return 2.5

# ========== HEADER ==========
st.title("🌡️ TEMP EDGE FINDER")
st.caption(f"HIGH & LOW Temperature Markets | {now.strftime('%b %d, %Y %I:%M %p ET')}")

# ========== CITY SELECTION ==========
c1, c2, c3 = st.columns([3, 1, 1])
with c1:
    default_idx = CITY_LIST.index(st.session_state.prefs.get("default_city", "New York City")) if st.session_state.prefs.get("default_city") in CITY_LIST else 5
    city = st.selectbox("📍 Select City", CITY_LIST, index=default_idx)
with c2:
    if st.button("⭐ Set Default", use_container_width=True):
        st.session_state.prefs["default_city"] = city
        save_prefs(st.session_state.prefs)
        st.success("✅ Saved!")
with c3:
    cfg = CITY_CONFIG.get(city, {})
    nws_url = f"https://forecast.weather.gov/MapClick.php?lat={cfg.get('lat', 40.78)}&lon={cfg.get('lon', -73.97)}"
    st.markdown(f"<a href='{nws_url}' target='_blank' style='display:block;background:#38bdf8;color:#000;padding:8px;border-radius:6px;text-align:center;text-decoration:none;font-weight:bold;margin-top:25px'>📡 NWS</a>", unsafe_allow_html=True)

st.caption(f"📡 Station: **{cfg.get('station', 'N/A')}** | ⭐ Default: {st.session_state.prefs.get('default_city')}")

# Fetch forecast
periods = fetch_nws_forecast(city)
forecast_high, forecast_low = get_forecasts(periods)
city_now = get_city_time(city)
base_sigma = auto_sigma(periods)

st.markdown("---")

# ========== SIDE BY SIDE: HIGH (LEFT) | LOW (RIGHT) ==========
col_high, col_low = st.columns(2)

# ========== HIGH TEMPERATURE (LEFT) ==========
with col_high:
    st.subheader("☀️ HIGH TEMP")
    
    # Forecast & Settings
    h1, h2 = st.columns(2)
    with h1:
        high_forecast = st.number_input("Forecast High °F", value=forecast_high or 45, min_value=-20, max_value=120, key="high_f")
    with h2:
        high_sigma = st.slider("σ (uncertainty)", 1.0, 5.0, base_sigma, 0.25, key="high_s")
    
    hours_high = calc_hours_to_settle(city, is_high=True)
    adj_sigma_high = high_sigma * (1 + max(0, (hours_high - 6)) * 0.02)
    st.caption(f"🕐 Settles ~5 PM {city_now.strftime('%Z')} ({hours_high}h) | σ: {adj_sigma_high:.2f}°F")
    
    # Calculate probabilities
    buckets_high = generate_buckets(high_forecast)
    results_high = []
    for b in buckets_high:
        prob = calc_bucket_prob(high_forecast, b["low"], b["high"], adj_sigma_high)
        results_high.append({"label": b["label"], "prob": prob, "cents": round(prob * 100)})
    
    max_prob_high = max(r["prob"] for r in results_high)
    rec_idx_high = next(i for i, r in enumerate(results_high) if r["prob"] == max_prob_high)
    kalshi_url_high = build_kalshi_url(city, is_high=True)
    
    # Show brackets
    for i, r in enumerate(results_high):
        if r["prob"] < 0.01:
            continue
        is_rec = (i == rec_idx_high)
        bg = "linear-gradient(90deg,#3d2800,#1a1200)" if is_rec else "#0f172a"
        border = "2px solid #ff9500" if is_rec else "1px solid #333"
        lbl_clr = "#ff9500" if is_rec else "#fff"
        badge = " ⭐" if is_rec else ""
        
        st.markdown(f"""<div style="background:{bg};border:{border};border-radius:6px;padding:8px 10px;margin:4px 0;display:flex;justify-content:space-between;align-items:center">
            <span style="color:{lbl_clr};font-weight:{'bold' if is_rec else 'normal'}">{r['label']}{badge}</span>
            <span style="color:#ff9500;font-weight:bold">{r['prob']*100:.1f}%</span>
        </div>""", unsafe_allow_html=True)
    
    # Recommendation
    rec_high = results_high[rec_idx_high]
    st.markdown(f"""
    <div style="background:linear-gradient(135deg,#3d2800,#1a1200);border:2px solid #ff9500;border-radius:10px;padding:15px;text-align:center;margin-top:10px">
        <div style="color:#ff9500;font-size:0.8em">⭐ RECOMMENDED HIGH</div>
        <div style="color:#fff;font-size:1.4em;font-weight:bold">{rec_high['label']}</div>
        <div style="color:#ff9500;margin-bottom:10px">{rec_high['prob']*100:.1f}%</div>
        <a href="{kalshi_url_high}" target="_blank" style="background:#00c853;color:#000;padding:10px 30px;border-radius:6px;text-decoration:none;font-weight:bold;display:inline-block">🎯 BUY YES</a>
    </div>
    """, unsafe_allow_html=True)

# ========== LOW TEMPERATURE (RIGHT) ==========
with col_low:
    st.subheader("🌙 LOW TEMP")
    
    # Forecast & Settings
    l1, l2 = st.columns(2)
    with l1:
        low_forecast = st.number_input("Forecast Low °F", value=forecast_low or 32, min_value=-20, max_value=120, key="low_f")
    with l2:
        low_sigma = st.slider("σ (uncertainty)", 1.0, 5.0, base_sigma, 0.25, key="low_s")
    
    hours_low = calc_hours_to_settle(city, is_high=False)
    adj_sigma_low = low_sigma * (1 + max(0, (hours_low - 6)) * 0.02)
    st.caption(f"🕐 Settles midnight {city_now.strftime('%Z')} ({hours_low}h) | σ: {adj_sigma_low:.2f}°F")
    
    # Calculate probabilities
    buckets_low = generate_buckets(low_forecast)
    results_low = []
    for b in buckets_low:
        prob = calc_bucket_prob(low_forecast, b["low"], b["high"], adj_sigma_low)
        results_low.append({"label": b["label"], "prob": prob, "cents": round(prob * 100)})
    
    max_prob_low = max(r["prob"] for r in results_low)
    rec_idx_low = next(i for i, r in enumerate(results_low) if r["prob"] == max_prob_low)
    kalshi_url_low = build_kalshi_url(city, is_high=False)
    
    # Show brackets
    for i, r in enumerate(results_low):
        if r["prob"] < 0.01:
            continue
        is_rec = (i == rec_idx_low)
        bg = "linear-gradient(90deg,#002a3d,#001a12)" if is_rec else "#0f172a"
        border = "2px solid #38bdf8" if is_rec else "1px solid #333"
        lbl_clr = "#38bdf8" if is_rec else "#fff"
        badge = " ⭐" if is_rec else ""
        
        st.markdown(f"""<div style="background:{bg};border:{border};border-radius:6px;padding:8px 10px;margin:4px 0;display:flex;justify-content:space-between;align-items:center">
            <span style="color:{lbl_clr};font-weight:{'bold' if is_rec else 'normal'}">{r['label']}{badge}</span>
            <span style="color:#38bdf8;font-weight:bold">{r['prob']*100:.1f}%</span>
        </div>""", unsafe_allow_html=True)
    
    # Recommendation
    rec_low = results_low[rec_idx_low]
    st.markdown(f"""
    <div style="background:linear-gradient(135deg,#002a3d,#001a12);border:2px solid #38bdf8;border-radius:10px;padding:15px;text-align:center;margin-top:10px">
        <div style="color:#38bdf8;font-size:0.8em">⭐ RECOMMENDED LOW</div>
        <div style="color:#fff;font-size:1.4em;font-weight:bold">{rec_low['label']}</div>
        <div style="color:#38bdf8;margin-bottom:10px">{rec_low['prob']*100:.1f}%</div>
        <a href="{kalshi_url_low}" target="_blank" style="background:#00c853;color:#000;padding:10px 30px;border-radius:6px;text-decoration:none;font-weight:bold;display:inline-block">🎯 BUY YES</a>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# ========== QUICK LINKS ==========
st.subheader("🔗 TRADE ON KALSHI")
lk1, lk2 = st.columns(2)
with lk1:
    st.markdown(f"""<a href="{kalshi_url_high}" target="_blank" style="display:block;background:#ff9500;color:#000;padding:12px;border-radius:8px;text-align:center;text-decoration:none;font-weight:bold">
    ☀️ {city} HIGH Market
    </a>""", unsafe_allow_html=True)
with lk2:
    st.markdown(f"""<a href="{kalshi_url_low}" target="_blank" style="display:block;background:#38bdf8;color:#000;padding:12px;border-radius:8px;text-align:center;text-decoration:none;font-weight:bold">
    🌙 {city} LOW Market
    </a>""", unsafe_allow_html=True)

st.markdown("---")

# ========== HOW TO USE ==========
with st.expander("📖 HOW TO USE", expanded=False):
    st.markdown("""
### 🎯 Quick Start

1. **Select city** from dropdown
2. **View both markets** side-by-side
3. **Orange/Blue highlighted** = Model's top pick
4. **Click BUY YES** to trade on Kalshi

### 📊 The Model

Uses normal distribution around NWS forecast:
- **σ (sigma)** = forecast uncertainty
- **Higher σ** = more spread across brackets
- **Lower σ** = concentrated around forecast

### ⏰ Settlement Times

- **HIGH temp**: Settles ~5 PM local time
- **LOW temp**: Settles midnight local time

### 🌍 Cities (Kalshi Markets)

Austin, Chicago, Denver, Los Angeles, Miami, NYC, Philadelphia

*v2.0 — Built for Kalshi*
""")

st.caption("⚠️ Experimental. Not financial advice. v2.0")
