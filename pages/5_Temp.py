import streamlit as st
import requests
from datetime import datetime

st.set_page_config(page_title="NYC Temp Markets", page_icon="🌡️", layout="wide")

st.title("🌡️ NYC Temperature Markets")
st.caption("Kalshi Weather Markets | BigSnapshot.com")

# --- CONFIG ---
# Kalshi ticker format: kxhighny-26jan20 (YYmmmDD lowercase)
# LOW ticker has T: kxlowtnyc
HIGH_SERIES = "kxhighny"
LOW_SERIES = "kxlowtnyc"

def get_date_suffix(target_date):
    """Convert date to Kalshi format: 26jan20 (YYmmmDD lowercase)"""
    return target_date.strftime("%y%b%d").lower()

def fetch_markets(series_ticker, date_suffix):
    """Fetch specific market from Kalshi API"""
    url = "https://api.elections.kalshi.com/trade-api/v2/markets"
    full_ticker = f"{series_ticker}-{date_suffix}"
    
    try:
        response = requests.get(url, params={"ticker": full_ticker}, timeout=10)
        if response.status_code == 200:
            return response.json().get("markets", []), None
        return [], f"API {response.status_code}"
    except Exception as e:
        return [], str(e)

def fetch_series(series_ticker):
    """Fetch all markets in series (for debugging)"""
    url = "https://api.elections.kalshi.com/trade-api/v2/markets"
    
    try:
        response = requests.get(url, params={"series_ticker": series_ticker, "limit": 50}, timeout=10)
        if response.status_code == 200:
            return response.json().get("markets", []), None
        return [], f"API {response.status_code}"
    except Exception as e:
        return [], str(e)

def get_nws_forecast():
    """Fetch NYC forecast from NWS API"""
    try:
        # NYC Central Park grid point
        response = requests.get(
            "https://api.weather.gov/gridpoints/OKX/33,37/forecast",
            headers={"User-Agent": "BigSnapshot Weather App"},
            timeout=10
        )
        if response.status_code == 200:
            periods = response.json().get("properties", {}).get("periods", [])
            return periods, None
        return [], f"NWS API {response.status_code}"
    except Exception as e:
        return [], str(e)

# --- TODAY'S DATE ---
today = datetime.now().date()
date_suffix = get_date_suffix(today)

st.info(f"**Today:** {today.strftime('%A, %B %d, %Y')} | **Ticker suffix:** `{date_suffix}`")

# --- NWS FORECAST ---
st.subheader("📡 NWS Forecast")

periods, nws_err = get_nws_forecast()
if nws_err:
    st.error(f"NWS Error: {nws_err}")
elif periods:
    # Find today's high and tonight's low
    today_high = None
    today_low = None
    
    for p in periods[:4]:
        name = p.get("name", "").lower()
        temp = p.get("temperature")
        
        if "night" in name or "tonight" in name:
            today_low = temp
        elif today_high is None and temp:
            today_high = temp
    
    col1, col2 = st.columns(2)
    with col1:
        if today_high:
            st.metric("🔥 NWS High", f"{today_high}°F")
    with col2:
        if today_low:
            st.metric("❄️ NWS Low", f"{today_low}°F")

# --- KALSHI MARKETS ---
st.subheader("📊 Kalshi Markets")

col_high, col_low = st.columns(2)

with col_high:
    st.write("**HIGH Temp Market**")
    st.caption(f"`{HIGH_SERIES}-{date_suffix}`")
    
    markets, err = fetch_markets(HIGH_SERIES, date_suffix)
    if err:
        st.error(err)
    elif markets:
        for m in markets:
            title = m.get("title", "")
            yes_bid = m.get("yes_bid", 0)
            yes_ask = m.get("yes_ask", 0)
            if yes_bid and yes_ask:
                mid = (yes_bid + yes_ask) / 2
                st.metric(title[:40], f"{mid:.0f}¢")
            else:
                st.write(title)
    else:
        st.warning("No market found")

with col_low:
    st.write("**LOW Temp Market**")
    st.caption(f"`{LOW_SERIES}-{date_suffix}`")
    
    markets, err = fetch_markets(LOW_SERIES, date_suffix)
    if err:
        st.error(err)
    elif markets:
        for m in markets:
            title = m.get("title", "")
            yes_bid = m.get("yes_bid", 0)
            yes_ask = m.get("yes_ask", 0)
            if yes_bid and yes_ask:
                mid = (yes_bid + yes_ask) / 2
                st.metric(title[:40], f"{mid:.0f}¢")
            else:
                st.write(title)
    else:
        st.warning("No market found")

# --- DEBUG ---
with st.expander("🔧 Debug"):
    if st.button("Show All Series Tickers"):
        st.write("**HIGH Series:**")
        markets, _ = fetch_series(HIGH_SERIES)
        for m in markets[:10]:
            st.code(m.get("ticker"))
        
        st.write("**LOW Series:**")
        markets, _ = fetch_series(LOW_SERIES)
        for m in markets[:10]:
            st.code(m.get("ticker"))

st.divider()
st.caption("BigSnapshot.com | Temp Markets v1.0")
