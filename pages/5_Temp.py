import streamlit as st
import requests
from datetime import datetime, timedelta
import pytz
import math

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

/* Mobile responsive */
@media (max-width: 768px) {
    .stApp {padding: 0.5rem !important;}
    div[data-testid="stHorizontalBlock"] {flex-direction: column !important; gap: 0.5rem !important;}
    div[data-testid="stColumn"] {width: 100% !important; min-width: 100% !important;}
    h1 {font-size: 1.5rem !important;}
    h2, h3 {font-size: 1.2rem !important;}
    div[data-testid="stNumberInput"] {min-width: 80px !important;}
    div[data-testid="stSelectbox"] {min-width: 100% !important;}
}

/* General improvements */
div[data-testid="stExpander"] {background: #0f172a; border-radius: 8px;}
div[data-testid="stMetric"] {background: #1a1a2e; padding: 12px; border-radius: 8px;}
div[data-testid="stMetric"] label {color: #888 !important;}
div[data-testid="stMetric"] div[data-testid="stMetricValue"] {color: #38bdf8 !important;}

/* Compact inputs */
div[data-testid="stNumberInput"] input {background: #1a1a2e !important; color: #fff !important; border: 1px solid #333 !important;}
div[data-testid="stSelectbox"] > div {background: #1a1a2e !important;}

/* Buy buttons */
.buy-yes {background:#00c853;color:#000;padding:4px 8px;border-radius:4px;text-decoration:none;font-weight:bold;font-size:0.75em;margin-right:4px;}
.buy-no {background:#ff4444;color:#fff;padding:4px 8px;border-radius:4px;text-decoration:none;font-weight:bold;font-size:0.75em;}
.buy-yes:hover, .buy-no:hover {opacity:0.8;}
</style>
""", unsafe_allow_html=True)

# ========== EXPERIMENTAL BANNER ==========
st.markdown("""
<div style="background:linear-gradient(90deg,#ff6b00,#ff9500);padding:10px 15px;border-radius:8px;margin-bottom:20px;text-align:center">
<b style="color:#000">🧪 EXPERIMENTAL</b> <span style="color:#000">— Temperature Edge Finder v1.2</span>
</div>
""", unsafe_allow_html=True)

eastern = pytz.timezone("US/Eastern")
now = datetime.now(eastern)

# ========== CITY CONFIG WITH KALSHI CODES ==========
CITY_CONFIG = {
    "New York City": {"grid": "OKX/33,37", "kalshi": "NYC"},
    "Chicago": {"grid": "LOT/76,73", "kalshi": "CHI"},
    "Los Angeles": {"grid": "LOX/154,44", "kalshi": "LA"},
    "Miami": {"grid": "MFL/109,50", "kalshi": "MIA"},
    "Denver": {"grid": "BOU/62,60", "kalshi": "DEN"},
    "Phoenix": {"grid": "PSR/160,59", "kalshi": "PHX"},
    "Seattle": {"grid": "SEW/124,67", "kalshi": "SEA"},
    "Boston": {"grid": "BOX/71,90", "kalshi": "BOS"},
    "Atlanta": {"grid": "FFC/52,88", "kalshi": "ATL"},
    "Dallas": {"grid": "FWD/83,108", "kalshi": "DAL"},
}

# ========== KALSHI URL BUILDER ==========
def build_kalshi_url(city, market_type, temp_low, temp_high):
    """Build Kalshi market URL for temperature bucket"""
    city_code = CITY_CONFIG.get(city, {}).get("kalshi", "NYC")
    date_str = now.strftime("%y%b%d").upper()
    market_code = "L" if "Low" in market_type else "H"
    
    # Handle edge buckets
    if temp_low == -999:
        bucket_code = f"T{int(temp_high)}U"  # Under
    elif temp_high == 999:
        bucket_code = f"T{int(temp_low)}O"  # Over
    else:
        bucket_code = f"T{int(temp_low)}"
    
    ticker = f"KXTEMP-{date_str}-{city_code}-{market_code}-{bucket_code}"
    return f"https://kalshi.com/markets/kxtemp/{ticker}"

# ========== NORMAL DISTRIBUTION FUNCTIONS ==========
def normal_cdf(x, mu, sigma):
    """Cumulative distribution function for normal distribution"""
    return 0.5 * (1 + math.erf((x - mu) / (sigma * math.sqrt(2))))

def calc_bucket_probability(forecast_temp, bucket_low, bucket_high, sigma=2.5):
    """Calculate probability that actual temp falls in bucket"""
    p_below_high = normal_cdf(bucket_high, forecast_temp, sigma)
    p_below_low = normal_cdf(bucket_low, forecast_temp, sigma)
    return p_below_high - p_below_low

# ========== DYNAMIC BUCKET GENERATION ==========
def generate_temp_buckets(center_temp, bucket_size=2, num_buckets=10):
    """Generate temperature buckets centered around forecast"""
    buckets = []
    start_temp = int(center_temp - (num_buckets // 2) * bucket_size)
    
    # First bucket: "X° or below"
    buckets.append({
        "label": f"{start_temp}° or below",
        "low": -999,
        "high": start_temp + 0.5,
        "temp_low": start_temp,
        "temp_high": start_temp
    })
    
    # Middle buckets
    for i in range(num_buckets - 2):
        low_temp = start_temp + i * bucket_size
        high_temp = low_temp + bucket_size - 1
        buckets.append({
            "label": f"{low_temp}° to {high_temp}°",
            "low": low_temp - 0.5,
            "high": high_temp + 0.5,
            "temp_low": low_temp,
            "temp_high": high_temp
        })
    
    # Last bucket: "X° or above"
    end_temp = start_temp + (num_buckets - 2) * bucket_size
    buckets.append({
        "label": f"{end_temp}° or above",
        "low": end_temp - 0.5,
        "high": 999,
        "temp_low": end_temp,
        "temp_high": end_temp
    })
    
    return buckets

# ========== FETCH NWS FORECAST ==========
@st.cache_data(ttl=1800)
def fetch_nws_forecast(city):
    """Fetch forecast from National Weather Service"""
    try:
        grid = CITY_CONFIG.get(city, {}).get("grid", "OKX/33,37")
        office, gridpoint = grid.split("/")
        
        url = f"https://api.weather.gov/gridpoints/{office}/{gridpoint}/forecast"
        headers = {"User-Agent": "TempEdgeFinder/1.2"}
        resp = requests.get(url, headers=headers, timeout=10)
        data = resp.json()
        
        periods = data.get("properties", {}).get("periods", [])
        
        forecast_data = {"periods": []}
        for p in periods[:8]:
            forecast_data["periods"].append({
                "name": p.get("name", ""),
                "temp": p.get("temperature", 0),
                "is_daytime": p.get("isDaytime", True),
                "short": p.get("shortForecast", ""),
            })
        
        return forecast_data
    except:
        return None

def get_forecast_low_high(forecast_data):
    """Extract forecast low and high"""
    if not forecast_data:
        return None, None
    
    periods = forecast_data.get("periods", [])
    today_high = None
    tonight_low = None
    
    for p in periods[:6]:
        name = p.get("name", "").lower()
        temp = p.get("temp", 0)
        
        if "tonight" in name or "night" in name:
            if tonight_low is None:
                tonight_low = temp
        elif p.get("is_daytime"):
            if today_high is None:
                today_high = temp
    
    return tonight_low, today_high

# ========== MAIN APP ==========
st.title("🌡️ TEMP EDGE FINDER")
st.caption(f"Model probabilities vs Kalshi prices | {now.strftime('%b %d, %Y %I:%M %p ET')}")

# ========== CITY & MARKET SELECTION ==========
col1, col2 = st.columns(2)
with col1:
    city = st.selectbox("📍 City", list(CITY_CONFIG.keys()), index=0)
with col2:
    market_type = st.radio("📊 Market", ["🌙 Low Temp", "☀️ High Temp"], horizontal=True)

is_low_market = "Low" in market_type

# Fetch forecast
forecast_data = fetch_nws_forecast(city)
tonight_low, today_high = get_forecast_low_high(forecast_data) if forecast_data else (None, None)

# ========== FORECAST DISPLAY ==========
st.markdown("---")
st.subheader("📡 NWS FORECAST")

fc1, fc2 = st.columns(2)
with fc1:
    low_display = tonight_low if tonight_low else "—"
    highlight_low = "border: 2px solid #ff9500; box-shadow: 0 0 15px rgba(255,149,0,0.3);" if is_low_market else ""
    st.markdown(f"""<div style="background:#1a1a2e;padding:15px;border-radius:8px;text-align:center;{highlight_low}">
        <div style="color:#888;font-size:0.85em">🌙 Tonight's Low</div>
        <div style="color:#38bdf8;font-size:2em;font-weight:bold">{low_display}°F</div>
    </div>""", unsafe_allow_html=True)

with fc2:
    high_display = today_high if today_high else "—"
    highlight_high = "border: 2px solid #ff9500; box-shadow: 0 0 15px rgba(255,149,0,0.3);" if not is_low_market else ""
    st.markdown(f"""<div style="background:#1a1a2e;padding:15px;border-radius:8px;text-align:center;{highlight_high}">
        <div style="color:#888;font-size:0.85em">☀️ Today's High</div>
        <div style="color:#ff9500;font-size:2em;font-weight:bold">{high_display}°F</div>
    </div>""", unsafe_allow_html=True)

if forecast_data:
    with st.expander("📋 Full Forecast"):
        for p in forecast_data.get("periods", [])[:6]:
            st.markdown(f"**{p['name']}**: {p['temp']}°F — {p['short']}")

st.markdown("---")

# ========== MODEL PARAMETERS ==========
st.subheader("⚙️ MODEL SETTINGS")

pc1, pc2, pc3 = st.columns(3)

with pc1:
    default_temp = tonight_low if is_low_market else today_high
    default_temp = default_temp if default_temp else (32 if is_low_market else 45)
    forecast_temp = st.number_input(
        "🎯 Forecast (°F)", 
        value=default_temp, 
        min_value=-20, 
        max_value=120
    )

with pc2:
    sigma = st.slider("📊 Uncertainty (σ)", 1.0, 5.0, 2.5, 0.25)

with pc3:
    hours_out = st.slider("⏱️ Hours to Settle", 1, 48, 12)

time_adjusted_sigma = sigma * (1 + max(0, (hours_out - 12)) * 0.015)
st.caption(f"⚡ Time-adjusted σ: **{time_adjusted_sigma:.2f}°F**")

st.markdown("---")

# ========== PROBABILITY CALCULATIONS ==========
market_label = "LOW" if is_low_market else "HIGH"

st.subheader(f"📊 {market_label} TEMP PROBABILITIES")

buckets = generate_temp_buckets(forecast_temp, bucket_size=2, num_buckets=10)

# Calculate probabilities
results = []
for b in buckets:
    prob = calc_bucket_probability(forecast_temp, b["low"], b["high"], time_adjusted_sigma)
    kalshi_url = build_kalshi_url(city, market_type, b["temp_low"], b["temp_high"])
    results.append({
        "label": b["label"],
        "model_prob": prob,
        "model_cents": round(prob * 100),
        "kalshi_url": kalshi_url,
        "temp_low": b["temp_low"],
        "temp_high": b["temp_high"]
    })

# Find recommended bucket (highest probability)
max_prob = max(r['model_prob'] for r in results)
recommended_idx = next(i for i, r in enumerate(results) if r['model_prob'] == max_prob)

# Filter relevant buckets
relevant = [(i, r) for i, r in enumerate(results) if r["model_prob"] > 0.005]

st.markdown("**Enter Kalshi prices → Find edges → Click to trade**")

# ========== EDGE TABLE WITH BUY BUTTONS ==========
for idx, r in relevant:
    prob_pct = r['model_prob'] * 100
    is_recommended = (idx == recommended_idx)
    
    # Highlight recommended bucket with orange
    if is_recommended:
        row_style = "background:linear-gradient(90deg,#3d2800,#1a1200);border:2px solid #ff9500;border-radius:8px;padding:10px;margin:8px 0;box-shadow:0 0 20px rgba(255,149,0,0.3);"
        rec_badge = '<span style="background:#ff9500;color:#000;padding:2px 8px;border-radius:4px;font-size:0.7em;font-weight:bold;margin-left:8px;">⭐ RECOMMENDED</span>'
    else:
        row_style = "background:#0f172a;border:1px solid #333;border-radius:6px;padding:8px;margin:4px 0;"
        rec_badge = ""
    
    st.markdown(f'<div style="{row_style}">', unsafe_allow_html=True)
    
    c1, c2, c3, c4, c5 = st.columns([2.5, 1.2, 1.2, 2, 2.1])
    
    with c1:
        label_color = "#ff9500" if is_recommended else "#fff"
        st.markdown(f"<b style='color:{label_color};font-size:1.05em'>{r['label']}</b>{rec_badge}", unsafe_allow_html=True)
    
    with c2:
        prob_color = "#ff9500" if is_recommended else "#38bdf8"
        st.markdown(f"<div style='color:{prob_color};font-weight:bold;padding-top:5px'>{prob_pct:.1f}%</div>", unsafe_allow_html=True)
    
    with c3:
        market_price = st.number_input(
            "¢", 
            min_value=1, 
            max_value=99, 
            value=max(1, r['model_cents']),
            key=f"mkt_{market_type}_{idx}",
            label_visibility="collapsed"
        )
    
    with c4:
        model_cents = r['model_prob'] * 100
        edge = model_cents - market_price
        
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
        # BUY YES and BUY NO buttons
        kalshi_url = r['kalshi_url']
        st.markdown(f"""
        <div style="display:flex;gap:4px;padding-top:2px">
            <a href="{kalshi_url}" target="_blank" class="buy-yes">YES</a>
            <a href="{kalshi_url}" target="_blank" class="buy-no">NO</a>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("---")

# ========== RECOMMENDED SUMMARY ==========
rec = results[recommended_idx]
rec_url = rec['kalshi_url']

st.markdown(f"""
<div style="background:linear-gradient(135deg,#3d2800,#1a1200);border:2px solid #ff9500;border-radius:12px;padding:20px;text-align:center;margin:15px 0;box-shadow:0 0 30px rgba(255,149,0,0.3)">
    <div style="color:#ff9500;font-size:0.9em;margin-bottom:8px">⭐ TOP RECOMMENDATION</div>
    <div style="color:#fff;font-size:1.8em;font-weight:bold;margin-bottom:5px">{rec['label']}</div>
    <div style="color:#ff9500;font-size:1.3em;font-weight:bold;margin-bottom:15px">{rec['model_prob']*100:.1f}% Model Probability</div>
    <div style="display:flex;justify-content:center;gap:15px">
        <a href="{rec_url}" target="_blank" style="background:#00c853;color:#000;padding:12px 30px;border-radius:8px;text-decoration:none;font-weight:bold;font-size:1.1em">BUY YES</a>
        <a href="{rec_url}" target="_blank" style="background:#ff4444;color:#fff;padding:12px 30px;border-radius:8px;text-decoration:none;font-weight:bold;font-size:1.1em">BUY NO</a>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# ========== DISTRIBUTION VISUAL ==========
st.subheader("📈 DISTRIBUTION")

max_prob_visual = max(r['model_prob'] for r in results)

for idx, r in enumerate(results):
    if r['model_prob'] < 0.005:
        continue
        
    bar_width = int((r['model_prob'] / max_prob_visual) * 100)
    prob_pct = r['model_prob'] * 100
    is_rec = (idx == recommended_idx)
    
    if is_rec:
        bar_color = "#ff9500"
        label_style = "color:#ff9500;font-weight:bold"
    elif prob_pct >= 15:
        bar_color = "#38bdf8"
        label_style = "color:#fff"
    else:
        bar_color = "#666"
        label_style = "color:#888"
    
    rec_marker = " ⭐" if is_rec else ""
    
    st.markdown(f"""
    <div style="display:flex;align-items:center;margin-bottom:6px;flex-wrap:wrap;gap:4px">
        <span style="min-width:90px;{label_style};font-size:0.8em">{r['label']}{rec_marker}</span>
        <div style="flex:1;min-width:100px;background:#1a1a2e;border-radius:4px;height:20px">
            <div style="width:{bar_width}%;background:{bar_color};height:100%;border-radius:4px"></div>
        </div>
        <span style="min-width:50px;color:{bar_color};font-weight:bold;font-size:0.85em;text-align:right">{prob_pct:.1f}%</span>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# ========== QUICK LINKS ==========
st.subheader("🔗 QUICK LINKS")

lc1, lc2 = st.columns(2)
with lc1:
    st.markdown("""
    <a href="https://kalshi.com/markets/kxtemp" target="_blank" style="display:block;background:#00c853;color:#000;padding:12px;border-radius:8px;text-align:center;text-decoration:none;font-weight:bold">
    🌡️ Kalshi Temp Markets
    </a>
    """, unsafe_allow_html=True)

with lc2:
    st.markdown("""
    <a href="https://forecast.weather.gov" target="_blank" style="display:block;background:#38bdf8;color:#000;padding:12px;border-radius:8px;text-align:center;text-decoration:none;font-weight:bold">
    📡 NWS Forecast
    </a>
    """, unsafe_allow_html=True)

st.markdown("---")

# ========== HOW TO USE (COLLAPSED) ==========
with st.expander("📖 HOW TO USE THIS APP", expanded=False):
    st.markdown("""
### 🎯 Getting Started

**Temperature Edge Finder** calculates model-based probabilities for Kalshi temperature markets and compares them to live prices to find mispricings.

---

### 📊 Step-by-Step

1. **Select city** — Choose from 10 major US cities
2. **Pick market** — Low (overnight) or High (daytime)
3. **Check forecast** — App pulls live NWS data
4. **Adjust σ** — Default 2.5°F for normal conditions
5. **Enter Kalshi prices** — Type current YES prices
6. **Find edges** — Look for ±5¢+ differences
7. **Click YES/NO** — Trade directly on Kalshi

---

### ⭐ Orange = Recommended

The **orange highlighted bracket** is the model's top pick (highest probability). This is where the actual temperature is most likely to land.

---

### 🧠 The Model

Forecasts have uncertainty. We model this as a **normal distribution**:
- **Mean** = Forecast temperature
- **Std Dev (σ)** = Forecast error (~2.5°F typical)

---

### 📈 Signal Guide

| Signal | Edge | Action |
|--------|------|--------|
| 🎯 **Strong** | ±8¢+ | High confidence |
| 🟢🔴 **Good** | ±5-7¢ | Consider trade |
| 🟡 **Lean** | ±3-5¢ | Small edge |
| ⚪ **Fair** | <±3¢ | No trade |

---

### ⚙️ Uncertainty (σ) Guide

| Condition | σ |
|-----------|---|
| Clear, stable | 1.5-2.0°F |
| Normal | 2.5°F |
| Fronts/variable | 3.0-3.5°F |
| Storms | 4.0-5.0°F |

---

### 💡 Pro Tips

- **Calibrate σ** until model ≈ matches market, then find outliers
- **Trade early** — edges close near settlement
- **Check multiple sources** — NWS, Weather.com, AccuWeather
- **Start small** — test before sizing up

---

*Built for Kalshi. v1.2*
""")

st.markdown("---")
st.caption("⚠️ Experimental tool. Not financial advice. v1.2")
