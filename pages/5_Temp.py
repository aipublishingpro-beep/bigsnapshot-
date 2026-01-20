import streamlit as st
import requests
from datetime import datetime
import pytz

st.set_page_config(page_title="Temp Edge Finder", page_icon="🌡️", layout="wide")

# --- GOOGLE ANALYTICS G4 ---
st.markdown("""
<script async src="https://www.googletagmanager.com/gtag/js?id=G-NQKY5VQ376"></script>
<script>window.dataLayer = window.dataLayer || [];function gtag(){dataLayer.push(arguments);}gtag('js', new Date());gtag('config', 'G-NQKY5VQ376');</script>
""", unsafe_allow_html=True)

# --- CITY CONFIG ---
# Each city: NWS grid point + Kalshi series tickers
CITIES = {
    "New York City": {
        "nws_office": "OKX",
        "nws_grid": "33,37",
        "high_series": "KXHIGHNY",
        "low_series": "KXLOWTNYC"
    },
    "Los Angeles": {
        "nws_office": "LOX",
        "nws_grid": "154,44",
        "high_series": "KXHIGHLA",
        "low_series": "KXLOWTLA"
    },
    "Chicago": {
        "nws_office": "LOT",
        "nws_grid": "65,76",
        "high_series": "KXHIGHCHI",
        "low_series": "KXLOWTCHI"
    },
    "Miami": {
        "nws_office": "MFL",
        "nws_grid": "109,50",
        "high_series": "KXHIGHMIA",
        "low_series": "KXLOWTMIA"
    },
    "Austin": {
        "nws_office": "EWX",
        "nws_grid": "156,91",
        "high_series": "KXHIGHAUS",
        "low_series": "KXLOWTAUS"
    }
}

def get_date_suffix(target_date):
    return target_date.strftime("%y%b%d").lower()

def get_nws_forecast(office, grid):
    """Fetch forecast from NWS API"""
    try:
        url = f"https://api.weather.gov/gridpoints/{office}/{grid}/forecast"
        response = requests.get(url, headers={"User-Agent": "BigSnapshot Weather App"}, timeout=10)
        if response.status_code == 200:
            data = response.json()
            periods = data.get("properties", {}).get("periods", [])
            update_time = data.get("properties", {}).get("updateTime", "")
            return periods, update_time, None
        return [], None, f"NWS API {response.status_code}"
    except Exception as e:
        return [], None, str(e)

def fetch_series_markets(series_ticker):
    """Fetch all markets in a Kalshi series"""
    try:
        url = "https://api.elections.kalshi.com/trade-api/v2/markets"
        response = requests.get(url, params={"series_ticker": series_ticker, "limit": 100}, timeout=10)
        if response.status_code == 200:
            return response.json().get("markets", []), None
        return [], f"API {response.status_code}"
    except Exception as e:
        return [], str(e)

def find_todays_market(markets, series_ticker, date_suffix):
    """Find specific day's market from series"""
    target = f"{series_ticker.lower()}-{date_suffix}"
    for m in markets:
        if m.get("ticker", "").lower() == target:
            return m
    return None

def parse_today_forecast(periods):
    """Extract today's high and low from NWS periods"""
    high, low = None, None
    for p in periods[:4]:
        name = p.get("name", "").lower()
        temp = p.get("temperature")
        if "night" in name or "tonight" in name:
            low = temp
        elif high is None and temp:
            high = temp
    return high, low

def calculate_market_implied(markets):
    """Calculate probability-weighted temperature from bracket markets"""
    if not markets:
        return None
    # This would need bracket parsing - simplified for now
    return None

# --- HEADER ---
st.title("🌡️ Temperature Edge Finder")
st.caption("NWS Forecast vs Kalshi Markets | BigSnapshot.com")

# --- TIME CHECK ---
et = pytz.timezone("America/New_York")
now_et = datetime.now(et)
hour = now_et.hour

if hour < 8:
    st.success("🟢 **PRE-MARKET** — Edge window active. NWS data available, markets opening soon.")
    locked = False
elif hour < 12:
    st.info("🟡 **TRADING WINDOW** — 8 AM - 12 PM ET. Execute positions now.")
    locked = False
else:
    st.error("🔴 **LOCKED** — After noon ET. Read-only mode. Edge has decayed.")
    locked = True

st.caption(f"Current time: {now_et.strftime('%I:%M %p ET')} | Today: {now_et.strftime('%A, %B %d, %Y')}")

# --- CITY SELECTOR ---
st.subheader("Select City")
city = st.selectbox("City", list(CITIES.keys()), label_visibility="collapsed")
config = CITIES[city]

today = now_et.date()
date_suffix = get_date_suffix(today)

# --- NWS FORECAST ---
st.subheader(f"📡 NWS Forecast — {city}")

periods, update_time, nws_err = get_nws_forecast(config["nws_office"], config["nws_grid"])

if nws_err:
    st.error(f"NWS Error: {nws_err}")
    nws_high, nws_low = None, None
else:
    nws_high, nws_low = parse_today_forecast(periods)
    
    # Show last update time
    if update_time:
        try:
            update_dt = datetime.fromisoformat(update_time.replace("Z", "+00:00"))
            update_et = update_dt.astimezone(et)
            st.caption(f"Last NWS update: {update_et.strftime('%I:%M %p ET')}")
        except:
            pass
    
    col1, col2 = st.columns(2)
    with col1:
        if nws_high:
            st.metric("🔥 NWS High", f"{nws_high}°F")
        else:
            st.metric("🔥 NWS High", "—")
    with col2:
        if nws_low:
            st.metric("❄️ NWS Low", f"{nws_low}°F")
        else:
            st.metric("❄️ NWS Low", "—")

# --- KALSHI MARKETS ---
st.subheader("📊 Kalshi Markets")

target_high = f"{config['high_series'].lower()}-{date_suffix}"
target_low = f"{config['low_series'].lower()}-{date_suffix}"

col_high, col_low = st.columns(2)

with col_high:
    st.write("**HIGH Temp Market**")
    st.caption(f"`{target_high}`")
    
    high_markets, err = fetch_series_markets(config["high_series"])
    if err:
        st.error(err)
    else:
        market = find_todays_market(high_markets, config["high_series"], date_suffix)
        if market:
            title = market.get("title", "")
            yes_bid = market.get("yes_bid", 0)
            yes_ask = market.get("yes_ask", 0)
            
            st.write(f"**{title}**")
            
            if yes_bid and yes_ask:
                mid = (yes_bid + yes_ask) / 2
                spread = yes_ask - yes_bid
                st.metric("Market Price", f"{mid:.0f}¢", delta=f"Spread: {spread}¢")
                
                if spread > 15:
                    st.warning("⚠️ Wide spread — reduce size or wait")
            else:
                st.caption("No bid/ask")
        else:
            st.warning("Market not found for today")
            if high_markets:
                st.caption("Available:")
                for m in high_markets[:3]:
                    st.code(m.get("ticker", ""))

with col_low:
    st.write("**LOW Temp Market**")
    st.caption(f"`{target_low}`")
    
    low_markets, err = fetch_series_markets(config["low_series"])
    if err:
        st.error(err)
    else:
        market = find_todays_market(low_markets, config["low_series"], date_suffix)
        if market:
            title = market.get("title", "")
            yes_bid = market.get("yes_bid", 0)
            yes_ask = market.get("yes_ask", 0)
            
            st.write(f"**{title}**")
            
            if yes_bid and yes_ask:
                mid = (yes_bid + yes_ask) / 2
                spread = yes_ask - yes_bid
                st.metric("Market Price", f"{mid:.0f}¢", delta=f"Spread: {spread}¢")
                
                if spread > 15:
                    st.warning("⚠️ Wide spread — reduce size or wait")
            else:
                st.caption("No bid/ask")
        else:
            st.warning("Market not found for today")
            if low_markets:
                st.caption("Available:")
                for m in low_markets[:3]:
                    st.code(m.get("ticker", ""))

# --- EDGE ANALYSIS ---
if not locked:
    st.subheader("🎯 Edge Analysis")
    st.caption("Kalshi settlements reference NWS Daily Climate Report. Other sources are informational only.")
    
    # Placeholder for edge calculation
    # Would compare NWS forecast to market-implied temperature
    st.info("Edge calculation requires bracket-level market data. Use debug below to verify tickers.")

# --- DEBUG ---
with st.expander("🔧 Debug"):
    st.write(f"**City Config:**")
    st.json(config)
    st.write(f"**Date Suffix:** `{date_suffix}`")
    
    if st.button("Show HIGH Series Tickers"):
        markets, _ = fetch_series_markets(config["high_series"])
        for m in markets[:10]:
            st.code(f"{m.get('ticker')} — {m.get('title', '')[:50]}")
    
    if st.button("Show LOW Series Tickers"):
        markets, _ = fetch_series_markets(config["low_series"])
        for m in markets[:10]:
            st.code(f"{m.get('ticker')} — {m.get('title', '')[:50]}")

st.divider()
st.caption("BigSnapshot.com | Temp Edge Finder v3.0")
