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

# ========== MOBILE-FRIENDLY CSS ==========
st.markdown("""
<style>
.stApp {background-color: #0a0a0f;}
div[data-testid="stMarkdownContainer"] p {color: #fff;}
@media (max-width: 768px) {
    .stApp {padding: 0.5rem !important;}
    div[data-testid="stHorizontalBlock"] {flex-direction: column !important; gap: 0.5rem !important;}
    div[data-testid="stColumn"] {width: 100% !important; min-width: 100% !important;}
    h1 {font-size: 1.5rem !important;}
    h2, h3 {font-size: 1.2rem !important;}
}
div[data-testid="stExpander"] {background: #0f172a; border-radius: 8px;}
div[data-testid="stNumberInput"] input {background: #1a1a2e !important; color: #fff !important; border: 1px solid #333 !important;}
.buy-yes {background:#00c853;color:#000;padding:4px 8px;border-radius:4px;text-decoration:none;font-weight:bold;font-size:0.75em;margin-right:4px;}
.buy-no {background:#ff4444;color:#fff;padding:4px 8px;border-radius:4px;text-decoration:none;font-weight:bold;font-size:0.75em;}
</style>
""", unsafe_allow_html=True)

# ========== EXPERIMENTAL BANNER ==========
st.markdown("""
<div style="background:linear-gradient(90deg,#ff6b00,#ff9500);padding:10px 15px;border-radius:8px;margin-bottom:20px;text-align:center">
<b style="color:#000">🧪 EXPERIMENTAL</b> <span style="color:#000">— Temperature Edge Finder v1.3</span>
</div>
""", unsafe_allow_html=True)

eastern = pytz.timezone("US/Eastern")
now = datetime.now(eastern)

# ========== ALL KALSHI TEMPERATURE CITIES (ALPHABETICAL) ==========
CITY_CONFIG = {
    "Austin": {
        "grid": "EWX/156,91",
        "kalshi_high": "KXHIGHAUS",
        "kalshi_low": "KXLOWAUS",
        "kalshi_slug_high": "highest-temperature-in-austin",
        "kalshi_slug_low": "lowest-temperature-in-austin",
        "tz": "US/Central",
        "station": "Austin-Bergstrom Airport (KAUS)"
    },
    "Chicago": {
        "grid": "LOT/76,73",
        "kalshi_high": "KXHIGHCHI",
        "kalshi_low": "KXLOWCHI",
        "kalshi_slug_high": "highest-temperature-in-chicago",
        "kalshi_slug_low": "lowest-temperature-in-chicago",
        "tz": "US/Central",
        "station": "Midway Airport (KMDW)"
    },
    "Denver": {
        "grid": "BOU/62,60",
        "kalshi_high": "KXHIGHDEN",
        "kalshi_low": "KXLOWDEN",
        "kalshi_slug_high": "highest-temperature-in-denver",
        "kalshi_slug_low": "lowest-temperature-in-denver",
        "tz": "US/Mountain",
        "station": "Denver Intl Airport (KDEN)"
    },
    "Los Angeles": {
        "grid": "LOX/154,44",
        "kalshi_high": "KXHIGHLAX",
        "kalshi_low": "KXLOWLAX",
        "kalshi_slug_high": "highest-temperature-in-los-angeles",
        "kalshi_slug_low": "lowest-temperature-in-los-angeles",
        "tz": "US/Pacific",
        "station": "LAX Airport (KLAX)"
    },
    "Miami": {
        "grid": "MFL/109,50",
        "kalshi_high": "KXHIGHMIA",
        "kalshi_low": "KXLOWMIA",
        "kalshi_slug_high": "highest-temperature-in-miami",
        "kalshi_slug_low": "lowest-temperature-in-miami",
        "tz": "US/Eastern",
        "station": "Miami Intl Airport (KMIA)"
    },
    "New York City": {
        "grid": "OKX/33,37",
        "kalshi_high": "KXHIGHNY",
        "kalshi_low": "KXLOWNY",
        "kalshi_slug_high": "highest-temperature-in-nyc",
        "kalshi_slug_low": "lowest-temperature-in-nyc-today",
        "tz": "US/Eastern",
        "station": "Central Park (KNYC)"
    },
    "Philadelphia": {
        "grid": "PHI/49,75",
        "kalshi_high": "KXHIGHPHL",
        "kalshi_low": "KXLOWPHL",
        "kalshi_slug_high": "highest-temperature-in-philadelphia",
        "kalshi_slug_low": "lowest-temperature-in-philadelphia",
        "tz": "US/Eastern",
        "station": "PHL Airport (KPHL)"
    },
}

CITY_LIST = sorted(CITY_CONFIG.keys())  # Alphabetical

# ========== USER PREFERENCES ==========
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

# ========== KALSHI URL BUILDER ==========
def build_kalshi_url(city, is_low_market):
    """Build Kalshi market URL - goes directly to the correct market page"""
    config = CITY_CONFIG.get(city, {})
    series = config.get("kalshi_low" if is_low_market else "kalshi_high", "KXHIGHNY")
    slug = config.get("kalshi_slug_low" if is_low_market else "kalshi_slug_high", "lowest-temperature-in-nyc")
    return f"https://kalshi.com/markets/{series.lower()}/{slug}"

# ========== NORMAL DISTRIBUTION ==========
def normal_cdf(x, mu, sigma):
    return 0.5 * (1 + math.erf((x - mu) / (sigma * math.sqrt(2))))

def calc_bucket_probability(forecast_temp, bucket_low, bucket_high, sigma=2.5):
    p_below_high = normal_cdf(bucket_high, forecast_temp, sigma)
    p_below_low = normal_cdf(bucket_low, forecast_temp, sigma)
    return p_below_high - p_below_low

# ========== DYNAMIC BUCKETS ==========
def generate_temp_buckets(center_temp, bucket_size=2, num_buckets=10):
    buckets = []
    start_temp = int(center_temp - (num_buckets // 2) * bucket_size)
    
    buckets.append({
        "label": f"{start_temp}° or below",
        "low": -999, "high": start_temp + 0.5
    })
    
    for i in range(num_buckets - 2):
        low_temp = start_temp + i * bucket_size
        high_temp = low_temp + bucket_size - 1
        buckets.append({
            "label": f"{low_temp}° to {high_temp}°",
            "low": low_temp - 0.5, "high": high_temp + 0.5
        })
    
    end_temp = start_temp + (num_buckets - 2) * bucket_size
    buckets.append({
        "label": f"{end_temp}° or above",
        "low": end_temp - 0.5, "high": 999
    })
    
    return buckets

# ========== FETCH NWS FORECAST ==========
@st.cache_data(ttl=1800)
def fetch_nws_forecast(city):
    try:
        grid = CITY_CONFIG.get(city, {}).get("grid", "OKX/33,37")
        office, gridpoint = grid.split("/")
        url = f"https://api.weather.gov/gridpoints/{office}/{gridpoint}/forecast"
        headers = {"User-Agent": "TempEdgeFinder/1.3"}
        resp = requests.get(url, headers=headers, timeout=10)
        data = resp.json()
        periods = data.get("properties", {}).get("periods", [])
        return {"periods": [{"name": p.get("name", ""), "temp": p.get("temperature", 0), 
                           "is_daytime": p.get("isDaytime", True), "short": p.get("shortForecast", "")} 
                          for p in periods[:8]]}
    except:
        return None

def get_forecast_low_high(forecast_data):
    if not forecast_data:
        return None, None
    tonight_low, today_high = None, None
    for p in forecast_data.get("periods", [])[:6]:
        name = p.get("name", "").lower()
        temp = p.get("temp", 0)
        if "tonight" in name or "night" in name:
            if tonight_low is None: tonight_low = temp
        elif p.get("is_daytime"):
            if today_high is None: today_high = temp
    return tonight_low, today_high

# ========== TIME FUNCTIONS ==========
def calc_hours_to_midnight(city):
    city_tz_str = CITY_CONFIG.get(city, {}).get("tz", "US/Eastern")
    city_tz = pytz.timezone(city_tz_str)
    now_local = datetime.now(city_tz)
    midnight = now_local.replace(hour=23, minute=59, second=59)
    if now_local.hour >= 23:
        return 1
    return max(1, int((midnight - now_local).total_seconds() / 3600))

def get_city_time(city):
    city_tz_str = CITY_CONFIG.get(city, {}).get("tz", "US/Eastern")
    return datetime.now(pytz.timezone(city_tz_str))

def auto_detect_sigma(forecast_data):
    if not forecast_data:
        return 2.5
    all_text = " ".join([p.get("short", "").lower() for p in forecast_data.get("periods", [])[:4]])
    if any(w in all_text for w in ["storm", "thunder", "severe"]):
        return 4.5
    elif any(w in all_text for w in ["front", "variable", "scattered", "chance"]):
        return 3.5
    elif any(w in all_text for w in ["partly", "showers"]):
        return 3.0
    elif any(w in all_text for w in ["clear", "sunny", "fair"]):
        return 2.0
    return 2.5

# ========== MAIN APP ==========
st.title("🌡️ TEMP EDGE FINDER")
st.caption(f"Kalshi Temperature Markets | {now.strftime('%b %d, %Y %I:%M %p ET')}")

# ========== CITY & MARKET SELECTION ==========
col1, col2, col3 = st.columns([2, 2, 1])

with col1:
    default_idx = CITY_LIST.index(st.session_state.prefs.get("default_city", "New York City")) if st.session_state.prefs.get("default_city") in CITY_LIST else 5
    city = st.selectbox("📍 City", CITY_LIST, index=default_idx)

with col2:
    market_type = st.radio("📊 Market", ["🌙 Low Temp", "☀️ High Temp"], horizontal=True)

with col3:
    if st.button("⭐ Set Default", use_container_width=True):
        st.session_state.prefs["default_city"] = city
        save_prefs(st.session_state.prefs)
        st.success(f"✅ {city}")

is_low_market = "Low" in market_type

# Show city info
city_config = CITY_CONFIG.get(city, {})
st.caption(f"📡 NWS Station: **{city_config.get('station', 'N/A')}** | ⭐ Default: {st.session_state.prefs.get('default_city', 'None')}")

# Fetch forecast
forecast_data = fetch_nws_forecast(city)
tonight_low, today_high = get_forecast_low_high(forecast_data) if forecast_data else (None, None)

# ========== FORECAST DISPLAY ==========
st.markdown("---")
st.subheader("📡 NWS FORECAST")

fc1, fc2 = st.columns(2)
with fc1:
    low_display = tonight_low if tonight_low else "—"
    hl = "border:2px solid #ff9500;box-shadow:0 0 15px rgba(255,149,0,0.3);" if is_low_market else ""
    st.markdown(f"""<div style="background:#1a1a2e;padding:15px;border-radius:8px;text-align:center;{hl}">
        <div style="color:#888;font-size:0.85em">🌙 Tonight's Low</div>
        <div style="color:#38bdf8;font-size:2em;font-weight:bold">{low_display}°F</div>
    </div>""", unsafe_allow_html=True)

with fc2:
    high_display = today_high if today_high else "—"
    hh = "border:2px solid #ff9500;box-shadow:0 0 15px rgba(255,149,0,0.3);" if not is_low_market else ""
    st.markdown(f"""<div style="background:#1a1a2e;padding:15px;border-radius:8px;text-align:center;{hh}">
        <div style="color:#888;font-size:0.85em">☀️ Today's High</div>
        <div style="color:#ff9500;font-size:2em;font-weight:bold">{high_display}°F</div>
    </div>""", unsafe_allow_html=True)

if forecast_data:
    with st.expander("📋 Full Forecast"):
        for p in forecast_data.get("periods", [])[:6]:
            st.markdown(f"**{p['name']}**: {p['temp']}°F — {p['short']}")

st.markdown("---")

# ========== MODEL PARAMETERS ==========
auto_hours = calc_hours_to_midnight(city)
auto_sigma = auto_detect_sigma(forecast_data)
city_now = get_city_time(city)
city_tz_abbr = city_now.strftime("%Z")

st.subheader("⚙️ MODEL SETTINGS")

pc1, pc2, pc3 = st.columns(3)

with pc1:
    default_temp = tonight_low if is_low_market else today_high
    default_temp = default_temp if default_temp else (32 if is_low_market else 45)
    forecast_temp = st.number_input("🎯 Forecast (°F)", value=default_temp, min_value=-20, max_value=120)

with pc2:
    sigma = st.slider("📊 Uncertainty (σ)", 1.0, 5.0, auto_sigma, 0.25)

with pc3:
    hours_out = st.slider("⏱️ Hrs to Midnight", 1, 24, auto_hours)

time_adjusted_sigma = sigma * (1 + max(0, (hours_out - 6)) * 0.02)
st.caption(f"🕐 **{city}**: {city_now.strftime('%I:%M %p %Z')} | Settles midnight ({hours_out}h) | σ: **{time_adjusted_sigma:.2f}°F**")

st.markdown("---")

# ========== PROBABILITY CALCULATIONS ==========
market_label = "LOW" if is_low_market else "HIGH"
st.subheader(f"📊 {market_label} TEMP PROBABILITIES")

buckets = generate_temp_buckets(forecast_temp, bucket_size=2, num_buckets=10)

results = []
kalshi_url = build_kalshi_url(city, is_low_market)  # One URL for all buckets
for b in buckets:
    prob = calc_bucket_probability(forecast_temp, b["low"], b["high"], time_adjusted_sigma)
    results.append({"label": b["label"], "model_prob": prob, "model_cents": round(prob * 100), "kalshi_url": kalshi_url})

max_prob = max(r['model_prob'] for r in results)
recommended_idx = next(i for i, r in enumerate(results) if r['model_prob'] == max_prob)

relevant = [(i, r) for i, r in enumerate(results) if r["model_prob"] > 0.005]

st.markdown("**Enter Kalshi prices → Find edges → Trade**")

# ========== EDGE TABLE ==========
for idx, r in relevant:
    prob_pct = r['model_prob'] * 100
    is_rec = (idx == recommended_idx)
    
    if is_rec:
        row_style = "background:linear-gradient(90deg,#3d2800,#1a1200);border:2px solid #ff9500;border-radius:8px;padding:10px;margin:8px 0;box-shadow:0 0 20px rgba(255,149,0,0.3);"
        rec_badge = '<span style="background:#ff9500;color:#000;padding:2px 6px;border-radius:4px;font-size:0.65em;font-weight:bold;margin-left:6px;">⭐ REC</span>'
    else:
        row_style = "background:#0f172a;border:1px solid #333;border-radius:6px;padding:8px;margin:4px 0;"
        rec_badge = ""
    
    st.markdown(f'<div style="{row_style}">', unsafe_allow_html=True)
    
    c1, c2, c3, c4, c5 = st.columns([2.5, 1.2, 1.2, 1.8, 2.3])
    
    with c1:
        lbl_clr = "#ff9500" if is_rec else "#fff"
        st.markdown(f"<b style='color:{lbl_clr}'>{r['label']}</b>{rec_badge}", unsafe_allow_html=True)
    
    with c2:
        p_clr = "#ff9500" if is_rec else "#38bdf8"
        st.markdown(f"<div style='color:{p_clr};font-weight:bold;padding-top:5px'>{prob_pct:.1f}%</div>", unsafe_allow_html=True)
    
    with c3:
        market_price = st.number_input("¢", 1, 99, max(1, r['model_cents']), key=f"m_{market_type}_{idx}", label_visibility="collapsed")
    
    with c4:
        edge = r['model_prob'] * 100 - market_price
        if abs(edge) < 3:
            st.markdown("<span style='color:#888'>⚪ FAIR</span>", unsafe_allow_html=True)
        elif edge >= 8:
            st.markdown(f"<span style='background:#00ff00;color:#000;padding:3px 8px;border-radius:4px;font-weight:bold'>🎯 +{edge:.0f}¢</span>", unsafe_allow_html=True)
        elif edge >= 5:
            st.markdown(f"<span style='color:#00ff00;font-weight:bold'>🟢 +{edge:.0f}¢</span>", unsafe_allow_html=True)
        elif edge <= -8:
            st.markdown(f"<span style='background:#ff4444;color:#fff;padding:3px 8px;border-radius:4px;font-weight:bold'>🎯 {edge:.0f}¢</span>", unsafe_allow_html=True)
        elif edge <= -5:
            st.markdown(f"<span style='color:#ff4444;font-weight:bold'>🔴 {edge:.0f}¢</span>", unsafe_allow_html=True)
        else:
            st.markdown(f"<span style='color:#ffaa00'>🟡 {edge:+.0f}¢</span>", unsafe_allow_html=True)
    
    with c5:
        st.markdown(f"""<div style="display:flex;gap:4px;padding-top:2px">
            <a href="{r['kalshi_url']}" target="_blank" class="buy-yes">BUY YES</a>
            <a href="{r['kalshi_url']}" target="_blank" class="buy-no">BUY NO</a>
        </div>""", unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("---")

# ========== RECOMMENDED SUMMARY ==========
rec = results[recommended_idx]
st.markdown(f"""
<div style="background:linear-gradient(135deg,#3d2800,#1a1200);border:2px solid #ff9500;border-radius:12px;padding:20px;text-align:center;margin:15px 0;box-shadow:0 0 30px rgba(255,149,0,0.3)">
    <div style="color:#ff9500;font-size:0.9em;margin-bottom:8px">⭐ TOP PICK — {city.upper()}</div>
    <div style="color:#fff;font-size:1.8em;font-weight:bold;margin-bottom:5px">{rec['label']}</div>
    <div style="color:#ff9500;font-size:1.3em;font-weight:bold;margin-bottom:15px">{rec['model_prob']*100:.1f}% Probability</div>
    <div style="display:flex;justify-content:center;gap:15px">
        <a href="{rec['kalshi_url']}" target="_blank" style="background:#00c853;color:#000;padding:12px 30px;border-radius:8px;text-decoration:none;font-weight:bold;font-size:1.1em">BUY YES</a>
        <a href="{rec['kalshi_url']}" target="_blank" style="background:#ff4444;color:#fff;padding:12px 30px;border-radius:8px;text-decoration:none;font-weight:bold;font-size:1.1em">BUY NO</a>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# ========== DISTRIBUTION VISUAL ==========
st.subheader("📈 DISTRIBUTION")

for idx, r in enumerate(results):
    if r['model_prob'] < 0.005:
        continue
    bar_width = int((r['model_prob'] / max_prob) * 100)
    prob_pct = r['model_prob'] * 100
    is_rec = (idx == recommended_idx)
    bar_color = "#ff9500" if is_rec else ("#38bdf8" if prob_pct >= 15 else "#666")
    rec_mark = " ⭐" if is_rec else ""
    st.markdown(f"""<div style="display:flex;align-items:center;margin-bottom:6px">
        <span style="min-width:90px;color:{'#ff9500' if is_rec else '#fff'};font-size:0.8em">{r['label']}{rec_mark}</span>
        <div style="flex:1;background:#1a1a2e;border-radius:4px;height:18px;margin:0 8px">
            <div style="width:{bar_width}%;background:{bar_color};height:100%;border-radius:4px"></div>
        </div>
        <span style="min-width:45px;color:{bar_color};font-weight:bold;font-size:0.85em">{prob_pct:.1f}%</span>
    </div>""", unsafe_allow_html=True)

st.markdown("---")

# ========== QUICK LINKS ==========
st.subheader("🔗 QUICK LINKS")

market_url = build_kalshi_url(city, is_low_market)
market_label = "Low" if is_low_market else "High"

lc1, lc2 = st.columns(2)
with lc1:
    st.markdown(f"""<a href="{market_url}" target="_blank" style="display:block;background:#00c853;color:#000;padding:12px;border-radius:8px;text-align:center;text-decoration:none;font-weight:bold">
    🌡️ Kalshi {city} {market_label}
    </a>""", unsafe_allow_html=True)
with lc2:
    st.markdown("""<a href="https://forecast.weather.gov" target="_blank" style="display:block;background:#38bdf8;color:#000;padding:12px;border-radius:8px;text-align:center;text-decoration:none;font-weight:bold">
    📡 NWS Forecast
    </a>""", unsafe_allow_html=True)

st.markdown("---")

# ========== HOW TO USE ==========
with st.expander("📖 HOW TO USE THIS APP", expanded=False):
    st.markdown(f"""
### 🎯 Getting Started

**Temperature Edge Finder** calculates probabilities for Kalshi temperature markets.

---

### 🌍 Available Cities (Kalshi Markets)

| City | NWS Station | Timezone |
|------|-------------|----------|
| Austin | Austin-Bergstrom (KAUS) | Central |
| Chicago | Midway Airport (KMDW) | Central |
| Denver | Denver Intl (KDEN) | Mountain |
| Los Angeles | LAX Airport (KLAX) | Pacific |
| Miami | Miami Intl (KMIA) | Eastern |
| New York City | Central Park (KNYC) | Eastern |
| Philadelphia | PHL Airport (KPHL) | Eastern |

**⭐ Set Default City**: Click the "Set Default" button to save your preferred city.

---

### 📊 How It Works

1. **Select city** from the dropdown (alphabetical)
2. **Pick market** — Low (overnight) or High (daytime)
3. **Review forecast** — Auto-pulled from NWS
4. **Adjust σ** if needed (auto-detected from conditions)
5. **Enter Kalshi prices** — Type current YES prices
6. **Find edges** — Look for ±5¢+ differences
7. **Click YES/NO** — Trade directly on Kalshi

---

### ⭐ Orange = Recommended

The **orange highlighted bracket** is the model's top pick (highest probability).

---

### 📈 Signal Guide

| Signal | Edge | Action |
|--------|------|--------|
| 🎯 | ±8¢+ | Strong signal |
| 🟢🔴 | ±5-7¢ | Good edge |
| 🟡 | ±3-5¢ | Small edge |
| ⚪ | <±3¢ | No trade |

---

### ⏰ Settlement Time

All markets settle at **midnight local time** based on the NWS Daily Climate Report.

---

*Built for Kalshi. v1.3*
""")

st.markdown("---")
st.caption("⚠️ Experimental tool. Not financial advice. v1.3")
