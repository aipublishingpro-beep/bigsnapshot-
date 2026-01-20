import streamlit as st
import requests
from datetime import datetime, timedelta
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
    "Atlanta": {
        "nws_office": "FFC",
        "nws_grid": "52,88",
        "high_series": "KXHIGHATL",
        "low_series": "KXLOWTATL"
    },
    "Austin": {
        "nws_office": "EWX",
        "nws_grid": "156,91",
        "high_series": "KXHIGHAUS",
        "low_series": "KXLOWTAUS"
    },
    "Boston": {
        "nws_office": "BOX",
        "nws_grid": "71,90",
        "high_series": "KXHIGHBOS",
        "low_series": "KXLOWTBOS"
    },
    "Chicago": {
        "nws_office": "LOT",
        "nws_grid": "65,76",
        "high_series": "KXHIGHCHI",
        "low_series": "KXLOWTCHI"
    },
    "Dallas": {
        "nws_office": "FWD",
        "nws_grid": "79,108",
        "high_series": "KXHIGHDAL",
        "low_series": "KXLOWTDAL"
    },
    "Denver": {
        "nws_office": "BOU",
        "nws_grid": "62,60",
        "high_series": "KXHIGHDEN",
        "low_series": "KXLOWTDEN"
    },
    "Houston": {
        "nws_office": "HGX",
        "nws_grid": "65,97",
        "high_series": "KXHIGHHOU",
        "low_series": "KXLOWTHOU"
    },
    "Los Angeles": {
        "nws_office": "LOX",
        "nws_grid": "154,44",
        "high_series": "KXHIGHLA",
        "low_series": "KXLOWTLA"
    },
    "Miami": {
        "nws_office": "MFL",
        "nws_grid": "109,50",
        "high_series": "KXHIGHMIA",
        "low_series": "KXLOWTMIA"
    },
    "New York City": {
        "nws_office": "OKX",
        "nws_grid": "33,37",
        "high_series": "KXHIGHNY",
        "low_series": "KXLOWTNYC"
    },
    "Philadelphia": {
        "nws_office": "PHI",
        "nws_grid": "49,75",
        "high_series": "KXHIGHPHL",
        "low_series": "KXLOWTPHL"
    },
    "Phoenix": {
        "nws_office": "PSR",
        "nws_grid": "161,58",
        "high_series": "KXHIGHPHX",
        "low_series": "KXLOWTPHX"
    },
    "San Francisco": {
        "nws_office": "MTR",
        "nws_grid": "85,105",
        "high_series": "KXHIGHSF",
        "low_series": "KXLOWTSF"
    },
    "Seattle": {
        "nws_office": "SEW",
        "nws_grid": "124,67",
        "high_series": "KXHIGHSEA",
        "low_series": "KXLOWTSEA"
    },
    "Washington DC": {
        "nws_office": "LWX",
        "nws_grid": "97,71",
        "high_series": "KXHIGHDC",
        "low_series": "KXLOWTDC"
    }
}

def get_date_suffix(target_date):
    return target_date.strftime("%y%b%d").upper()

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

def find_todays_markets(markets, series_ticker, date_suffix):
    """Find all bracket markets for a specific day"""
    prefix = f"{series_ticker}-{date_suffix}".upper()
    found = []
    for m in markets:
        ticker = m.get("ticker", "").upper()
        if ticker.startswith(prefix):
            found.append(m)
    return found

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

# --- TIME ---
et = pytz.timezone("America/New_York")
now_et = datetime.now(et)

st.caption(f"Current time: {now_et.strftime('%I:%M %p ET')} | Today: {now_et.strftime('%A, %B %d, %Y')}")

# --- CITY SELECTOR ---
st.subheader("Select City")
city = st.selectbox("City", list(CITIES.keys()), label_visibility="collapsed")
config = CITIES[city]

# --- DATE SELECTION ---
today = now_et.date()
tomorrow = today + timedelta(days=1)

date_option = st.radio("Select Date", ["Today", "Tomorrow"], horizontal=True)
target_date = today if date_option == "Today" else tomorrow
date_suffix = get_date_suffix(target_date)

st.caption(f"Looking for: {target_date.strftime('%A, %B %d')} | Suffix: `{date_suffix}`")

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

col_high, col_low = st.columns(2)

with col_high:
    st.write("**HIGH Temp Market**")
    st.caption(f"`{config['high_series']}-{date_suffix}-T##`")
    
    high_markets, err = fetch_series_markets(config["high_series"])
    if err:
        st.error(err)
    else:
        day_markets = find_todays_markets(high_markets, config["high_series"], date_suffix)
        if day_markets:
            st.success(f"✅ Found {len(day_markets)} brackets")
            for market in sorted(day_markets, key=lambda x: x.get("ticker", "")):
                ticker = market.get("ticker", "")
                title = market.get("title", "")
                yes_bid = market.get("yes_bid", 0)
                yes_ask = market.get("yes_ask", 0)
                
                # Extract threshold from ticker (e.g., -T40 means 40°F)
                threshold = ticker.split("-T")[-1] if "-T" in ticker else ""
                
                if yes_bid and yes_ask:
                    mid = (yes_bid + yes_ask) / 2
                    spread = yes_ask - yes_bid
                    col_a, col_b = st.columns([2, 1])
                    with col_a:
                        st.write(f"**{threshold}°F+**")
                    with col_b:
                        st.write(f"{mid:.0f}¢ (spread {spread}¢)")
                else:
                    st.write(f"**{threshold}°F+** — no bid/ask")
        else:
            st.warning("No markets for this date")
            if high_markets:
                st.caption("Available dates:")
                shown = set()
                for m in high_markets[:10]:
                    t = m.get("ticker", "")
                    # Extract date portion
                    parts = t.split("-")
                    if len(parts) >= 2:
                        date_part = parts[1]
                        if date_part not in shown:
                            st.code(date_part)
                            shown.add(date_part)

with col_low:
    st.write("**LOW Temp Market**")
    st.caption(f"`{config['low_series']}-{date_suffix}-T##`")
    
    low_markets, err = fetch_series_markets(config["low_series"])
    if err:
        st.error(err)
    else:
        day_markets = find_todays_markets(low_markets, config["low_series"], date_suffix)
        if day_markets:
            st.success(f"✅ Found {len(day_markets)} brackets")
            for market in sorted(day_markets, key=lambda x: x.get("ticker", "")):
                ticker = market.get("ticker", "")
                title = market.get("title", "")
                yes_bid = market.get("yes_bid", 0)
                yes_ask = market.get("yes_ask", 0)
                
                # Extract threshold from ticker
                threshold = ticker.split("-T")[-1] if "-T" in ticker else ""
                
                if yes_bid and yes_ask:
                    mid = (yes_bid + yes_ask) / 2
                    spread = yes_ask - yes_bid
                    col_a, col_b = st.columns([2, 1])
                    with col_a:
                        st.write(f"**{threshold}°F or less**")
                    with col_b:
                        st.write(f"{mid:.0f}¢ (spread {spread}¢)")
                else:
                    st.write(f"**{threshold}°F or less** — no bid/ask")
        else:
            st.warning("No markets for this date")
            if low_markets:
                st.caption("Available dates:")
                shown = set()
                for m in low_markets[:10]:
                    t = m.get("ticker", "")
                    parts = t.split("-")
                    if len(parts) >= 2:
                        date_part = parts[1]
                        if date_part not in shown:
                            st.code(date_part)
                            shown.add(date_part)

# --- EDGE ANALYSIS ---
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
